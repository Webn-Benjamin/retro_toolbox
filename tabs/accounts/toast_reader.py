"""toast_reader.py - Lecture notifications Toast Dofus via winsdk."""
from __future__ import annotations
import asyncio, ctypes, re, threading
from dataclasses import dataclass
from typing import Callable

try:
    import winsdk.windows.ui.notifications.management as _mgmt
    import winsdk.windows.ui.notifications as _notif
    SDK_OK = True
except ImportError:
    SDK_OK = False

from tabs.accounts.window_manager import _PTN_SESSION

_RULES = [
    ("combat",  "⚔️", [re.compile(r"de jouer|turn to play|Le toca jugar", re.I)]),
    ("echange", "🔄", [re.compile(r"propose.+échange|offers.+trade|propone.+intercambio", re.I)]),
    ("groupe",  "👥", [re.compile(r"invite.+rejoindre|invited.+join|invita.+unirte", re.I)]),
    ("mp",      "💬", [re.compile(r"^de |^from |^desde ", re.I)]),
    ("defi",    "🏆", [re.compile(r"te défie|challenges you|te desafía", re.I)]),
    ("craft",   "🔨", [re.compile(r"talents|atelier|fabriqués|skills|workshop|created|artesano|taller", re.I)]),
    ("pvp",     "🛡️", [re.compile(r"percepteur.+attaqué|perceptor.+attacked|recaudador.+atacado", re.I)]),
]

def _categorize(body):
    for ntype, emoji, patterns in _RULES:
        if any(p.search(body) for p in patterns):
            return ntype, emoji
    return "other", "🔔"

@dataclass
class AlertEvent:
    ntype: str; emoji: str; pseudo: str; body: str

class AlertWatcher:
    def __init__(self, callback: Callable[[AlertEvent], None],
                 remove_after_read=True, on_status=None):
        self._cb = callback
        self._remove = remove_after_read
        self._on_status = on_status
        self._running = False
        self._loop = None
        self._thread = None

    def set_dismiss(self, v): self._remove = v

    def start(self):
        if not SDK_OK:
            return False
        self._running = True
        self._thread = threading.Thread(
            target=self._event_loop, daemon=True, name="AlertWatcher")
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _event_loop(self):
        ctypes.windll.ole32.CoInitializeEx(None, 0x2)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._subscribe())
        except Exception:
            pass
        finally:
            self._loop.close()
            ctypes.windll.ole32.CoUninitialize()

    async def _subscribe(self):
        listener = _mgmt.UserNotificationListener.current
        access   = await listener.request_access_async()
        if access != _mgmt.UserNotificationListenerAccessStatus.ALLOWED:
            if self._on_status:
                self._on_status("denied")
            return
        if self._on_status:
            self._on_status("ok")

        seen: set[int] = set()
        event = asyncio.Event()
        token = None
        use_events = False

        def on_changed(sender, args):
            try:
                if self._loop and self._loop.is_running():
                    self._loop.call_soon_threadsafe(event.set)
            except Exception:
                pass

        try:
            token = listener.add_notification_changed(on_changed)
            use_events = True
        except Exception:
            pass

        try:
            existing = await listener.get_notifications_async(
                _notif.NotificationKinds.TOAST)
            for n in existing:
                seen.add(n.id)

            while self._running:
                if use_events:
                    try:
                        await asyncio.wait_for(event.wait(), timeout=30.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                    event.clear()
                else:
                    try:
                        await asyncio.sleep(0.3)
                    except asyncio.CancelledError:
                        break

                toasts = await listener.get_notifications_async(
                    _notif.NotificationKinds.TOAST)
                new = [n for n in toasts if n.id not in seen]
                for n in new:
                    seen.add(n.id)
                    if self._remove:
                        try:
                            listener.remove_notification(n.id)
                        except Exception:
                            pass
                    parsed = self._decode(n)
                    if parsed:
                        threading.Thread(
                            target=self._cb, args=(parsed,),
                            daemon=True).start()
                if len(seen) > 2000:
                    seen.clear()
        finally:
            if token:
                try:
                    listener.remove_notification_changed(token)
                except Exception:
                    pass

    def _decode(self, raw):
        try:
            binding = raw.notification.visual.get_binding(
                _notif.KnownNotificationBindings.toast_generic)
            if not binding:
                return None
            texts = [e.text for e in binding.get_text_elements()]
            if not texts:
                return None
            title = texts[0]
            body  = texts[1] if len(texts) > 1 else ""
            m = _PTN_SESSION.match(title)
            if not m:
                return None
            pseudo = m.group(1).strip()
            ntype, emoji = _categorize(body)
            if ntype == "other":
                return None
            return AlertEvent(ntype=ntype, emoji=emoji, pseudo=pseudo, body=body)
        except Exception:
            return None


class _MockWatcher:
    def __init__(self, cb, remove=True, on_status=None):
        self._cb = cb; self._t = None
    def set_dismiss(self, v): pass
    def start(self) -> bool:
        from PySide6.QtCore import QTimer
        import random
        self._t = QTimer()
        self._t.timeout.connect(lambda: self._cb(random.choice([
            AlertEvent("combat","⚔️","St-Arc","C est a toi de jouer"),
            AlertEvent("echange","🔄","St-Enu","te propose de faire un echange"),
        ])))
        self._t.start(15000)
        return True
    def stop(self):
        if self._t: self._t.stop()


def make_watcher(callback, remove=True, mock=False, on_status=None):
    if mock:
        return _MockWatcher(callback, remove, on_status)
    return AlertWatcher(callback, remove, on_status=on_status)
