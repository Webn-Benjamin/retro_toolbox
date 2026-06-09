"""os_bridge/mac.py — Implémentations macOS : Quartz + pynput."""
from __future__ import annotations
import re, subprocess, threading, time
from dataclasses import dataclass
from typing import Callable

_PTN_SESSION = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_PTN_LOADING = re.compile(r"^Dofus\s*Retro\b",       re.IGNORECASE)
_PTN_ALERT   = re.compile(r"^\[!\]",                   re.IGNORECASE)

@dataclass
class GameWindow:
    hwnd: int; name: str; loading: bool = False

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
    """Vérifie si l'app a la permission Enregistrement d'écran (macOS 10.15+)."""
    try:
        import Quartz
        # Tenter de lire les titres : si vide alors qu'il y a des fenêtres, permission manquante
        wins = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        if wins:
            # Vérifier si on peut lire les noms
            for w in wins:
                if w.get("kCGWindowName") is not None:
                    return True
            return False  # fenêtres présentes mais noms masqués = pas de permission
        return True
    except Exception:
        return False

def list_windows() -> list[GameWindow]:
    result = []
    for w in _quartz_wins():
        title = (w.get("kCGWindowName") or "").strip()
        clean = re.sub(r"^\[!\]\s*", "", title)
        wid   = w.get("kCGWindowNumber", 0)
        m = _PTN_SESSION.match(clean)
        if m:
            result.append(GameWindow(hwnd=wid, name=m.group(1).strip()))
        elif _PTN_LOADING.match(clean):
            result.append(GameWindow(hwnd=wid, name="Chargement…", loading=True))
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
        if w.name.lower() == name.lower(): return focus_window(w.hwnd)
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
    return False  # géré via listener pynput dans craft_tab

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
            f'tell application "System Events" to keystroke "{key}" using {{control down, shift down}}'],
            capture_output=True, timeout=2)
    except Exception: pass

def register_hotkey(combo: str, fn: Callable) -> bool:
    try:
        from pynput import keyboard as _kb
        parts   = combo.lower().replace("ctrl","control").split("+")
        mod_map = {"control":_kb.Key.ctrl,"cmd":_kb.Key.cmd,
                   "alt":_kb.Key.alt,"shift":_kb.Key.shift}
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

class AlertWatcher:
    """Autofocus Mac via polling titres [!] toutes les 200ms."""
    def __init__(self, callback: Callable[[str, str], None]):
        self._cb = callback; self._running = False; self._seen: set[int] = set()

    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self): self._running = False

    def _loop(self):
        while self._running:
            try: self._check()
            except Exception: pass
            time.sleep(0.20)

    def _check(self):
        alerted: set[int] = set()
        for w in _quartz_wins():
            title = (w.get("kCGWindowName") or "").strip()
            wid   = w.get("kCGWindowNumber", 0)
            if not _PTN_ALERT.match(title):
                self._seen.discard(wid); continue
            alerted.add(wid)
            if wid in self._seen: continue
            self._seen.add(wid)
            clean  = re.sub(r"^\[!\]\s*", "", title)
            m      = _PTN_SESSION.match(clean)
            pseudo = m.group(1).strip() if m else clean.strip()
            if pseudo: self._cb(pseudo, "combat")
        self._seen &= alerted
