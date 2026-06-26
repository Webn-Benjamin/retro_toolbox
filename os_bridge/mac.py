"""os_bridge/mac.py — Implémentations macOS : même interface que Windows."""
from __future__ import annotations
import re, subprocess, threading, time, os
from dataclasses import dataclass
from typing import Callable

_PTN_SESSION = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_PTN_LOADING = re.compile(r"^Dofus\s*Retro\b",       re.IGNORECASE)

@dataclass
class GameWindow:
    hwnd: int; pseudo: str; loading: bool = False


# ─── Quartz helpers ──────────────────────────────────────────────────
def _quartz_wins() -> list[dict]:
    try:
        import Quartz
        wins = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionAll |
            Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID)
        return list(wins) if wins else []
    except Exception:
        return []


def list_windows() -> list[GameWindow]:
    result = []
    seen_ids = set()
    idx = 1
    for w in _quartz_wins():
        owner  = (w.get("kCGWindowOwnerName") or "").lower()
        wid    = w.get("kCGWindowNumber", 0)
        layer  = w.get("kCGWindowLayer", 0)
        bounds = w.get("kCGWindowBounds", {})
        if wid in seen_ids: continue
        if "dofus" not in owner: continue
        if layer not in (0, -1): continue
        if bounds.get("Width", 0) < 500 or bounds.get("Height", 0) < 400: continue
        if (w.get("kCGWindowAlpha", 1.0) or 0) < 0.5: continue
        seen_ids.add(wid)
        title = (w.get("kCGWindowName") or "").strip()
        clean = re.sub(r"^\[!\]\s*", "", title)
        m     = _PTN_SESSION.match(clean)
        name  = m.group(1).strip() if m else (title if len(title) > 3 else f"Fenêtre {idx}")
        idx  += 1
        result.append(GameWindow(hwnd=wid, pseudo=name))
    return result


def focus_window(wid: int) -> bool:
    for w in _quartz_wins():
        if w.get("kCGWindowNumber") == wid:
            pname = w.get("kCGWindowOwnerName", "")
            if not pname: continue
            try:
                script = f'''tell application "{pname}" to activate
tell application "System Events" to tell process "{pname}" to set frontmost to true'''
                subprocess.run(["osascript", "-e", script],
                               capture_output=True, timeout=3)
                return True
            except Exception: pass
    return False


def focus_by_name(name: str) -> bool:
    for w in list_windows():
        if w.pseudo.lower() == name.lower(): return focus_window(w.hwnd)
    return False


def foreground_hwnd() -> int | None:
    wins = _quartz_wins()
    return wins[0].get("kCGWindowNumber") if wins else None


def is_game_active() -> bool:
    wins = _quartz_wins()
    return bool(wins and "dofus" in (wins[0].get("kCGWindowOwnerName") or "").lower())


def compact_titles(_enabled: bool): pass


def get_cursor_pos() -> tuple[int, int]:
    try:
        import Quartz
        loc = Quartz.NSEvent.mouseLocation()
        h   = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID()).size.height
        return int(loc.x), int(h - loc.y)
    except Exception: return (0, 0)


def get_rbutton_state() -> bool: return False


def window_at(x: int, y: int) -> tuple[int, str]:
    for w in _quartz_wins():
        b = w.get("kCGWindowBounds", {})
        if (b.get("X",0) <= x <= b.get("X",0)+b.get("Width",0) and
                b.get("Y",0) <= y <= b.get("Y",0)+b.get("Height",0)):
            owner = (w.get("kCGWindowOwnerName") or "").lower()
            title = (w.get("kCGWindowName") or "").lower()
            return w.get("kCGWindowNumber", 0), f"{owner} {title}"
    return 0, ""


def simulate_ctrl_shift(key: str):
    try:
        subprocess.run(["osascript", "-e",
            f'tell application "System Events" to keystroke "{key}" '
            f'using {{control down, shift down}}'],
            capture_output=True, timeout=2)
    except Exception: pass


_hotkey_monitors = []  # garder les références vivantes (évite garbage collection)

def register_hotkey(combo: str, fn: Callable) -> bool:
    try:
        from AppKit import NSEvent
        parts    = combo.lower().replace("ctrl","control").split("+")
        mod_map  = {"control":1<<18,"cmd":1<<20,"alt":1<<19,"shift":1<<17}
        mods     = 0
        char_key = None
        for p in parts:
            p = p.strip()
            if p in mod_map: mods |= mod_map[p]
            elif p: char_key = p
        if char_key is None:
            print(f"[Mac] Raccourci {combo}: pas de touche")
            return False
        NSKeyDownMask = 1 << 10
        def _handler(event):
            try:
                chars = (event.charactersIgnoringModifiers() or "").lower()
                flags = event.modifierFlags() & 0xFFFF0000
                if chars == char_key and (flags & mods) == mods:
                    fn()
            except Exception: pass
        monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSKeyDownMask, _handler)
        if monitor is not None:
            _hotkey_monitors.append(monitor)
            print(f"[Mac] Raccourci enregistré: {combo}")
            return True
        print(f"[Mac] Raccourci {combo}: monitor None (permission Accessibilité ?)")
        return False
    except Exception as e:
        print(f"[Mac] Raccourci {combo}: {e}")
        return False


# ─── Catégorisation — tous types comme Windows (FR + EN + ES) ────────
_RULES = [
    ("combat",  "⚔️",  [re.compile(r"de jouer|turn to play|toca jugar|your turn|'s turn to play", re.I)]),
    ("echange", "🔄",  [re.compile(r"propose.+échange|offers?.+trade|veut échanger|wants to trade|échange|exchange|propone.+intercambio", re.I)]),
    ("groupe",  "👥",  [re.compile(r"invite.+rejoindre|invit.+groupe|invited.+join|invites you|invita.+unirte|rejoindre le groupe|join.+group", re.I)]),
    ("mp",      "💬",  [re.compile(r"vous murmure|whispers|murmure|message privé|private message|^de\s|^from\s|susurra|te dice", re.I)]),
    ("defi",    "🏆",  [re.compile(r"te défie|vous défie|défie|challenges you|challenge|desafía|provoca", re.I)]),
    ("craft",   "🔨",  [re.compile(r"talents|atelier|fabriqués|fabrication|skills|workshop|created|crafted|artesano|taller", re.I)]),
    ("pvp",     "🛡️",  [re.compile(r"percepteur.+attaqué|votre percepteur|perceptor.+attacked|recaudador|collector.+attack|tax collector", re.I)]),
]

def _categorize(body: str) -> tuple[str, str]:
    for ntype, emoji, patterns in _RULES:
        if any(p.search(body) for p in patterns):
            return ntype, emoji
    return "other", "🔔"


# ─── AlertWatcher Mac — screencapture + tesseract ────────────────────
from dataclasses import dataclass as _dc

@_dc
class AlertEvent:
    ntype: str; emoji: str; pseudo: str; body: str


class AlertWatcher:
    """
    Équivalent Mac de AlertWatcher Windows.
    Lit les notifications via l'API Accessibilité (AXUIElement) —
    pas d'OCR, lit directement le texte. Équivalent direct de winsdk.
    Nécessite la permission Accessibilité accordée à l'app/Terminal.
    """

    def __init__(self, callback: Callable):
        self._cb      = callback
        self._running = False

    def set_dismiss(self, v): pass

    def start(self) -> bool:
        self._running = True
        threading.Thread(target=self._loop, daemon=True,
                         name="MacAlertWatcher").start()
        print("[Mac] AlertWatcher démarré (API Accessibilité)")
        return True

    def stop(self):
        self._running = False

    def _read_all(self, el) -> list[str]:
        """Lit récursivement tout le texte d'un élément AX."""
        from ApplicationServices import AXUIElementCopyAttributeValue
        texts = []
        for attr in ["AXTitle", "AXValue", "AXDescription"]:
            err, val = AXUIElementCopyAttributeValue(el, attr, None)
            if err == 0 and val and str(val).strip():
                texts.append(str(val))
        err, kids = AXUIElementCopyAttributeValue(el, "AXChildren", None)
        if err == 0 and kids:
            for k in kids:
                texts += self._read_all(k)
        return texts

    def _decode(self, texts: list[str]) -> AlertEvent | None:
        """Parse les textes d'une notification → pseudo (le perso concerné) + type."""
        # Ignorer l'entrée "Notification Center" générique
        clean = [t for t in texts if t.strip() and t.strip() != "Notification Center"]
        if not clean:
            return None
        full = " ".join(clean)

        # 1. Le pseudo du PERSO qui reçoit la notif = depuis "Pseudo - Dofus Retro"
        pseudo = ""
        for t in clean:
            m = _PTN_SESSION.match(t.strip())
            if m:
                pseudo = m.group(1).strip()
                break
        # 2. Fallback : matcher avec une fenêtre Dofus connue
        if not pseudo:
            full_low = full.lower()
            for win in list_windows():
                if win.pseudo.lower() in full_low:
                    pseudo = win.pseudo
                    break
        if not pseudo:
            return None

        # Le corps = le message (dernière ligne, sans le titre "Pseudo - Dofus")
        body_lines = [t for t in clean
                      if not _PTN_SESSION.match(t.strip())
                      and t.strip() != "Dofus Retro"]
        body = " ".join(body_lines) if body_lines else full

        ntype, emoji = _categorize(body)
        if ntype == "other":
            # Même si non catégorisé, déclencher en "combat" par défaut
            # (mieux vaut switcher que rater)
            ntype, emoji = "combat", "⚔️"
        return AlertEvent(ntype=ntype, emoji=emoji, pseudo=pseudo, body=body)

    def _loop(self):
        try:
            from ApplicationServices import (
                AXUIElementCreateApplication, AXUIElementCopyAttributeValue,
            )
        except Exception as e:
            print(f"[Mac] API Accessibilité indisponible: {e}")
            return

        # Trouver le PID du NotificationCenter
        def _get_pid():
            try:
                out = subprocess.run(["pgrep", "-x", "NotificationCenter"],
                    capture_output=True, text=True, timeout=2).stdout.strip()
                return int(out.split("\n")[0]) if out else None
            except Exception:
                return None

        pid = _get_pid()
        if not pid:
            print("[Mac] NotificationCenter introuvable")
            return
        app = AXUIElementCreateApplication(pid)
        print(f"[Mac] Surveillance NotificationCenter (PID {pid})")

        # active = notifications actuellement affichées (pour détecter apparition)
        active: set[str] = set()

        while self._running:
            try:
                err, wins = AXUIElementCopyAttributeValue(app, "AXWindows", None)
                current_keys: set[str] = set()
                if err == 0 and wins:
                    for w in wins:
                        texts = self._read_all(w)
                        if len(texts) < 2:  # juste "Notification Center"
                            continue
                        key = " ".join(texts)
                        current_keys.add(key)
                        # Déclencher UNIQUEMENT à l'apparition (pas déjà active)
                        if key in active:
                            continue
                        print(f"[Mac] NOTIF brute: {texts}")
                        ev = self._decode(texts)
                        if ev:
                            print(f"[Mac] → {ev.ntype}: {ev.pseudo} | BODY={repr(ev.body)}")
                            threading.Thread(target=self._cb, args=(ev,),
                                           daemon=True).start()
                # Mettre à jour : les notifs disparues seront re-déclenchables
                active = current_keys
            except Exception as e:
                new_pid = _get_pid()
                if new_pid and new_pid != pid:
                    pid = new_pid
                    app = AXUIElementCreateApplication(pid)
            time.sleep(0.20)
