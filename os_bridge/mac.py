"""os_bridge/mac.py — Implémentations macOS : Quartz + notifications système."""
from __future__ import annotations
import re, subprocess, threading, time, os, glob
from dataclasses import dataclass
from typing import Callable

_PTN_SESSION = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_PTN_LOADING = re.compile(r"^Dofus\s*Retro\b",       re.IGNORECASE)
_PTN_ALERT   = re.compile(r"^\[!\]",                   re.IGNORECASE)


@dataclass
class GameWindow:
    hwnd: int; pseudo: str; loading: bool = False


# ─── Quartz helpers ──────────────────────────────────────────────────
def _quartz_wins() -> list[dict]:
    try:
        import Quartz
        wins = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly |
            Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID)
        return list(wins) if wins else []
    except Exception:
        return []


def has_screen_permission() -> bool:
    try:
        import Quartz
        wins = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        if wins:
            for w in wins:
                if w.get("kCGWindowName") is not None:
                    return True
            return False
        return True
    except Exception:
        return False


def list_windows() -> list[GameWindow]:
    result = []
    seen_ids = set()
    idx = 1
    for w in _quartz_wins():
        owner = (w.get("kCGWindowOwnerName") or "").lower()
        wid   = w.get("kCGWindowNumber", 0)
        layer = w.get("kCGWindowLayer", 0)
        if layer != 0 or wid in seen_ids: continue
        if "dofus" not in owner: continue
        seen_ids.add(wid)
        title = (w.get("kCGWindowName") or "").strip()
        clean = re.sub(r"^\[!\]\s*", "", title)
        m     = _PTN_SESSION.match(clean)
        if m:
            name = m.group(1).strip()
        elif title and len(title) > 2:
            name = title
        else:
            name = f"Fenêtre {idx}"
        idx += 1
        result.append(GameWindow(hwnd=wid, pseudo=name))
    return result


def focus_window(wid: int) -> bool:
    for w in _quartz_wins():
        if w.get("kCGWindowNumber") == wid:
            pname = w.get("kCGWindowOwnerName", "")
            if not pname: continue
            try:
                # Désminimiser si besoin + mettre au premier plan
                script = f'''
tell application "{pname}"
    activate
    try
        set miniaturized of window 1 to false
    end try
end tell
tell application "System Events"
    tell process "{pname}"
        set frontmost to true
    end tell
end tell'''
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
    except Exception:
        return (0, 0)


def get_rbutton_state() -> bool:
    return False


def window_at(x: int, y: int) -> tuple[int, str]:
    for w in _quartz_wins():
        b = w.get("kCGWindowBounds", {})
        if (b.get("X", 0) <= x <= b.get("X", 0) + b.get("Width", 0) and
                b.get("Y", 0) <= y <= b.get("Y", 0) + b.get("Height", 0)):
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


def register_hotkey(combo: str, fn: Callable) -> bool:
    """Raccourcis globaux Mac via NSEvent global monitor."""
    try:
        from AppKit import NSEvent
        import threading

        parts   = combo.lower().replace("ctrl","control").split("+")
        mod_map = {
            "control": 1 << 18,  # NSControlKeyMask
            "cmd":     1 << 20,  # NSCommandKeyMask
            "alt":     1 << 19,  # NSAlternateKeyMask
            "shift":   1 << 17,  # NSShiftKeyMask
        }
        mods_needed = 0
        char_key    = None
        for p in parts:
            if p in mod_map: mods_needed |= mod_map[p]
            else:            char_key = p

        if char_key is None: return False

        NSKeyDownMask = 1 << 10

        def _handler(event):
            try:
                chars = (event.charactersIgnoringModifiers() or "").lower()
                flags = event.modifierFlags() & 0xFFFF0000
                if chars == char_key and (flags & mods_needed) == mods_needed:
                    fn()
            except Exception: pass

        monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSKeyDownMask, _handler)
        return monitor is not None
    except Exception as e:
        print(f"[Mac] Raccourci {combo} non disponible: {e}")
        return False


# ─── Surveillance notifications macOS via bannière Quartz ────────────
def _find_notif_db() -> str | None:
    """Trouve la DB notifications — essaie tous les chemins connus."""
    import sqlite3
    patterns = [
        os.path.expanduser("~/Library/Application Support/NotificationCenter/*.db"),
        os.path.expanduser("~/Library/Application Support/NotificationCenter/db2"),
        os.path.expanduser("~/Library/Application Support/NotificationCenter/db"),
        "/private/var/folders/*/*/C/com.apple.notificationcenter/db2/db",
    ]
    for p in patterns:
        for match in glob.glob(p):
            try:
                conn = sqlite3.connect(f"file:{match}?mode=ro", uri=True)
                cur  = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cur.fetchall()]
                conn.close()
                if tables:
                    return match
            except Exception:
                pass
    return None


def _get_db_schema(db_path: str) -> tuple[str, str, str] | None:
    """Retourne (table, id_col, data_col) selon le schéma détecté."""
    import sqlite3
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        conn.close()
        if "record" in tables:
            return ("record", "record_id", "data")
        if "presented_notifications" in tables:
            return ("presented_notifications", "rowid", "encoded_data")
    except Exception:
        pass
    return None


def _read_last_notif_id(db_path: str) -> int:
    schema = _get_db_schema(db_path)
    if not schema: return 0
    table, id_col, _ = schema
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        cur.execute(f"SELECT MAX({id_col}) FROM {table}")
        row = cur.fetchone(); conn.close()
        return row[0] or 0
    except Exception:
        return 0


def _read_new_notifs(db_path: str, since_id: int) -> list[dict]:
    schema = _get_db_schema(db_path)
    if not schema: return []
    table, id_col, data_col = schema
    results = []
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        cur.execute(f"SELECT {id_col}, {data_col} FROM {table} WHERE {id_col} > ?",
                    (since_id,))
        for row in cur.fetchall():
            results.append({"id": row[0], "raw": row[1]})
        conn.close()
    except Exception:
        pass
    return results


# ─── Surveillance bannière notification via Quartz (fallback) ─────────
def _watch_notif_banner(callback):
    """
    Détecte les bannières de notification Dofus via Quartz.
    Fonctionne même sans accès à la DB.
    """
    seen: set[int] = set()
    while True:
        try:
            for w in _quartz_wins():
                owner = (w.get("kCGWindowOwnerName") or "").lower()
                title = (w.get("kCGWindowName") or "").strip()
                wid   = w.get("kCGWindowNumber", 0)
                # Bannière notification = fenêtre du NotificationCenter
                if "notificationcenter" not in owner and                    "notification center" not in owner: continue
                if wid in seen or not title: continue
                # Vérifier si c'est une notif Dofus
                if "dofus" in title.lower() or any(
                    kw in title.lower() for kw in
                    ["jouer","trade","échange","combat","groupe","message","mp"]):
                    seen.add(wid)
                    wins = list_windows()
                    pseudo = wins[0].pseudo if wins else ""
                    if pseudo:
                        try:
                            from tabs.accounts.toast_reader import _categorize
                            ntype, _ = _categorize(title)
                            if ntype == "other": ntype = "combat"
                        except Exception:
                            ntype = "combat"
                        callback(pseudo, ntype)
            # Nettoyer les bannières disparues
            current = {w.get("kCGWindowNumber",0) for w in _quartz_wins()}
            seen &= current
        except Exception:
            pass
        time.sleep(0.2)


# ─── AlertWatcher — double mécanisme : notifications + polling titres ─
class AlertWatcher:
    """
    Autofocus Mac via deux mécanismes combinés :
    1. Surveillance base de données notifications macOS (équivalent Toast Windows)
    2. Polling titres de fenêtres [!] toutes les 200ms (fallback)
    """

    def __init__(self, callback: Callable[[str, str], None]):
        self._cb      = callback
        self._running = False
        self._seen_titles: set[int] = set()
        self._db_path  = _find_notif_db()
        self._last_id  = 0

    def start(self):
        self._running = True
        # Mécanisme 1 : DB notifications (si accessible)
        if self._db_path:
            self._last_id = _read_last_notif_id(self._db_path)
            threading.Thread(target=self._notif_loop, daemon=True).start()
        # Mécanisme 2 : Bannières notification via Quartz
        threading.Thread(
            target=_watch_notif_banner, args=(self._cb,), daemon=True).start()
        # Mécanisme 3 : Polling titres [!]
        threading.Thread(target=self._title_loop, daemon=True).start()

    def stop(self):
        self._running = False

    # ── Boucle notifications DB ────────────────────────────────────
    def _notif_loop(self):
        while self._running:
            try:
                notifs = _read_new_notifs(self._db_path, self._last_id)
                for n in notifs:
                    self._last_id = max(self._last_id, n["id"])
                    self._process_notif(n["raw"])
            except Exception:
                pass
            time.sleep(0.3)

    def _process_notif(self, raw):
        """Parse la notification et extrait pseudo + type (combat, echange, mp...)."""
        if not raw: return
        try:
            from tabs.accounts.toast_reader import _categorize
        except Exception:
            _categorize = lambda t: ("combat", "⚔️")

        text = ""
        try:
            import plistlib
            data  = raw if isinstance(raw, bytes) else bytes(raw)
            plist = plistlib.loads(data)
            for key in ["body", "title", "subtitle", "req", "content"]:
                val = plist.get(key, "")
                if isinstance(val, str) and val:
                    text += " " + val
        except Exception:
            pass

        ntype, _ = _categorize(text.strip()) if text.strip() else ("combat", "⚔️")
        if ntype == "other": ntype = "combat"

        m      = _PTN_SESSION.search(text)
        pseudo = m.group(1).strip() if m else ""
        if not pseudo:
            wins   = list_windows()
            pseudo = wins[0].pseudo if wins else ""

        if pseudo:
            self._cb(pseudo, ntype)
        elif not text.strip():
            wins = list_windows()
            if wins: self._cb(wins[0].pseudo, ntype)

    # ── Boucle polling titres [!] ─────────────────────────────────
    def _title_loop(self):
        while self._running:
            try:
                self._check_titles()
            except Exception:
                pass
            time.sleep(0.20)

    def _check_titles(self):
        alerted: set[int] = set()
        for w in _quartz_wins():
            title = (w.get("kCGWindowName") or "").strip()
            wid   = w.get("kCGWindowNumber", 0)
            if not _PTN_ALERT.match(title):
                self._seen_titles.discard(wid); continue
            alerted.add(wid)
            if wid in self._seen_titles: continue
            self._seen_titles.add(wid)
            clean  = re.sub(r"^\[!\]\s*", "", title)
            m      = _PTN_SESSION.match(clean)
            pseudo = m.group(1).strip() if m else clean.strip()
            if pseudo: self._cb(pseudo, "combat")
        self._seen_titles &= alerted
