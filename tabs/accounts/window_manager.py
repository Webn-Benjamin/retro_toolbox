"""window_manager.py — Détection et contrôle des fenêtres Dofus Rétro."""
from __future__ import annotations
import re
from dataclasses import dataclass

try:
    import win32gui, win32con, win32api, win32process
    WIN32_OK = True
except ImportError:
    WIN32_OK = False

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

_RE_TITLE = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_RE_LOAD  = re.compile(r"^Dofus\s*Retro\b", re.IGNORECASE)
_short_map: dict[int, str] = {}   # hwnd → titre original avant raccourcissement


@dataclass
class DofusWin:
    hwnd:   int
    pseudo: str
    loading: bool = False


def _check_pid(pid: int) -> bool:
    if not PSUTIL_OK: return True
    try:
        return "dofus" in psutil.Process(pid).name().lower()
    except Exception:
        return False


def scan_windows() -> list[DofusWin]:
    """Retourne toutes les fenêtres Dofus Rétro visibles."""
    if not WIN32_OK:
        return [DofusWin(1001,"Perso1"), DofusWin(1002,"Perso2"), DofusWin(1003,"Perso3")]
    result = []
    def _cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd): return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not _check_pid(pid): return
        except Exception: return
        raw = win32gui.GetWindowText(hwnd)
        # Fenêtre avec titre raccourci — utiliser l'original sauvegardé
        if hwnd in _short_map:
            original = _short_map[hwnd]
            m2 = _RE_TITLE.match(original)
            if m2:
                result.append(DofusWin(hwnd=hwnd, pseudo=m2.group(1).strip()))
            return True
        m = _RE_TITLE.match(raw)
        if m:
            result.append(DofusWin(hwnd=hwnd, pseudo=m.group(1).strip()))
        elif _RE_LOAD.match(raw):
            result.append(DofusWin(hwnd=hwnd, pseudo="Chargement…", loading=True))
    win32gui.EnumWindows(_cb, None)
    return result


def get_pseudo(hwnd: int) -> str | None:
    if not WIN32_OK: return None
    if hwnd in _short_map: return win32gui.GetWindowText(hwnd) or None
    raw = win32gui.GetWindowText(hwnd)
    m = _RE_TITLE.match(raw)
    return m.group(1).strip() if m else None


def bring_to_front(hwnd: int) -> bool:
    if not WIN32_OK: return False
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        # Trick ALT pour contourner SetForegroundWindow restrictions
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        try:
            win32gui.SetForegroundWindow(hwnd)
        finally:
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False


def bring_to_front_by_pseudo(pseudo: str) -> bool:
    for w in scan_windows():
        if w.pseudo.lower() == pseudo.lower():
            return bring_to_front(w.hwnd)
    return False


def current_foreground_hwnd() -> int | None:
    if not WIN32_OK: return None
    try: return win32gui.GetForegroundWindow()
    except: return None


def is_dofus_active() -> bool:
    if not WIN32_OK: return False
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd in _short_map: return True
        raw = win32gui.GetWindowText(hwnd)
        return bool(_RE_TITLE.match(raw) or _RE_LOAD.match(raw))
    except: return False


def apply_short_titles(enabled: bool):
    if not WIN32_OK: return
    def _cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd): return
        raw = win32gui.GetWindowText(hwnd)
        if enabled:
            m = _RE_TITLE.match(raw)
            if not m: return
            _short_map[hwnd] = raw  # sauvegarder le titre complet
            try: win32gui.SetWindowText(hwnd, m.group(1).strip())
            except: pass
        else:
            # Restaurer depuis la map — fonctionne même si titre déjà raccourci
            if hwnd in _short_map:
                original = _short_map.pop(hwnd)
                try: win32gui.SetWindowText(hwnd, original)
                except: pass
    win32gui.EnumWindows(_cb, None)
