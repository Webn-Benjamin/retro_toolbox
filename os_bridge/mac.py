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
            if pname:
                try:
                    subprocess.run(["osascript", "-e",
                        f'tell application "{pname}" to activate'],
                        capture_output=True, timeout=2)
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
    try:
        from pynput import keyboard as _kb
        parts   = combo.lower().replace("ctrl", "control").split("+")
        mod_map = {"control": _kb.Key.ctrl, "cmd": _kb.Key.cmd,
                   "alt": _kb.Key.alt, "shift": _kb.Key.shift}
        mods: set = set(); key = None
        for p in parts:
            if p in mod_map: mods.add(mod_map[p])
            else:
                try:    key = _kb.KeyCode.from_char(p)
                except: key = getattr(_kb.Key, p, None)
        if key is None: return False
        pressed: set = set()
        def on_press(k):
            pressed.add(k)
            if mods <= pressed and key in pressed: fn()
        def on_release(k): pressed.discard(k)
        lst = _kb.Listener(on_press=on_press, on_release=on_release)
        lst.daemon = True; lst.start()
        return True
    except Exception: return False


# ─── Lecture base de données notifications macOS ─────────────────────
def _find_notif_db() -> str | None:
    """Trouve la base de données des notifications macOS."""
    patterns = [
        os.path.expanduser("~/Library/Application Support/NotificationCenter/*.db"),
        "/private/var/folders/*/*/C/com.apple.notificationcenter/db2/db",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def _read_last_notif_id(db_path: str) -> int:
    """Lit le dernier ID de notification dans la DB."""
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        # Essayer différentes versions du schéma macOS
        for query in [
            "SELECT MAX(record_id) FROM record",
            "SELECT MAX(rowid) FROM presented_notifications",
        ]:
            try:
                cur.execute(query)
                row = cur.fetchone()
                conn.close()
                return row[0] or 0
            except Exception:
                pass
        conn.close()
    except Exception:
        pass
    return 0


def _read_new_notifs(db_path: str, since_id: int) -> list[dict]:
    """Lit les nouvelles notifications depuis un ID donné."""
    results = []
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        for query in [
            f"SELECT record_id, data FROM record WHERE record_id > {since_id}",
            f"SELECT rowid, encoded_data FROM presented_notifications WHERE rowid > {since_id}",
        ]:
            try:
                cur.execute(query)
                rows = cur.fetchall()
                if rows:
                    for row in rows:
                        results.append({"id": row[0], "raw": row[1]})
                    break
            except Exception:
                pass
        conn.close()
    except Exception:
        pass
    return results


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
        if self._db_path:
            self._last_id = _read_last_notif_id(self._db_path)
            t = threading.Thread(target=self._notif_loop, daemon=True)
            t.start()
        # Toujours démarrer le polling des titres en parallèle
        t2 = threading.Thread(target=self._title_loop, daemon=True)
        t2.start()

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
        """Parse la notification binaire et extrait le pseudo."""
        if not raw: return
        try:
            # Décoder le plist binaire
            import plistlib
            data = raw if isinstance(raw, bytes) else bytes(raw)
            plist = plistlib.loads(data)
            # Chercher le contenu dans les clés communes
            text = ""
            for key in ["body", "title", "subtitle", "req", "content"]:
                val = plist.get(key, "")
                if isinstance(val, str) and val:
                    text += " " + val
            if not text.strip(): return
            # Chercher un pseudo dans le texte
            m = _PTN_SESSION.search(text)
            pseudo = m.group(1).strip() if m else ""
            if not pseudo:
                # Essayer d'extraire depuis les fenêtres actives
                wins = list_windows()
                if wins: pseudo = wins[0].name
            if pseudo:
                self._cb(pseudo, "combat")
        except Exception:
            # Si le parsing échoue, utiliser la première fenêtre Dofus
            wins = list_windows()
            if wins:
                self._cb(wins[0].name, "combat")

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
