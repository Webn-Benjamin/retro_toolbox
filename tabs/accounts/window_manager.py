"""window_manager.py — Gestion des sessions Dofus Rétro actives."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

try:
    import win32gui, win32con, win32api, win32process
    _W32 = True
except ImportError:
    _W32 = False

try:
    import psutil
    _PS = True
except ImportError:
    _PS = False

# Patterns de titre Dofus Rétro
_PTN_SESSION = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_PTN_LOADING = re.compile(r"^Dofus\s*Retro\b",       re.IGNORECASE)

# Registre des titres compactés (hwnd → titre complet)
_title_registry: dict[int, str] = {}


@dataclass
class SessionEntry:
    hwnd:    int
    pseudo:  str
    loading: bool = False


def _pid_alive(pid: int) -> bool:
    """Vérifie que le process Dofus est encore vivant."""
    if not _PS:
        return True
    try:
        return "dofus" in psutil.Process(pid).name().lower()
    except Exception:
        return False


def collect_sessions() -> list[SessionEntry]:
    """Parcourt les fenêtres visibles et retourne les sessions Dofus actives."""
    if not _W32:
        return [SessionEntry(1001, "Alpha"), SessionEntry(1002, "Beta"),
                SessionEntry(1003, "Gamma")]

    sessions: list[SessionEntry] = []

    def _visit(hwnd: int, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not _pid_alive(pid):
                return
        except Exception:
            return

        raw = win32gui.GetWindowText(hwnd)

        if hwnd in _title_registry:
            src = _title_registry[hwnd]
            hit = _PTN_SESSION.match(src)
            if hit:
                sessions.append(SessionEntry(hwnd=hwnd, pseudo=hit.group(1).strip()))
            return

        hit = _PTN_SESSION.match(raw)
        if hit:
            sessions.append(SessionEntry(hwnd=hwnd, pseudo=hit.group(1).strip()))
        elif _PTN_LOADING.match(raw):
            sessions.append(SessionEntry(hwnd=hwnd, pseudo="Chargement…", loading=True))

    win32gui.EnumWindows(_visit, None)
    return sessions


def get_display_name(hwnd: int) -> str | None:
    """Retourne le pseudo associé à une fenêtre, ou None."""
    if not _W32:
        return None
    if hwnd in _title_registry:
        return win32gui.GetWindowText(hwnd) or None
    raw = win32gui.GetWindowText(hwnd)
    hit = _PTN_SESSION.match(raw)
    return hit.group(1).strip() if hit else None


def activate_window(hwnd: int) -> bool:
    """Met la fenêtre au premier plan."""
    if not _W32:
        return False
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        # Contourne la restriction SetForegroundWindow via ALT simulé
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        try:
            win32gui.SetForegroundWindow(hwnd)
        finally:
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False


def activate_by_name(pseudo: str) -> bool:
    """Met au premier plan la session correspondant au pseudo."""
    for session in collect_sessions():
        if session.pseudo.lower() == pseudo.lower():
            return activate_window(session.hwnd)
    return False


def foreground_handle() -> int | None:
    """Retourne le hwnd de la fenêtre en premier plan."""
    if not _W32:
        return None
    try:
        return win32gui.GetForegroundWindow()
    except Exception:
        return None


def is_game_focused() -> bool:
    """Indique si une fenêtre Dofus est actuellement au premier plan."""
    if not _W32:
        return False
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd in _title_registry:
            return True
        raw = win32gui.GetWindowText(hwnd)
        return bool(_PTN_SESSION.match(raw) or _PTN_LOADING.match(raw))
    except Exception:
        return False


def apply_compact_titles(enabled: bool):
    """Active ou désactive les titres courts sur les fenêtres Dofus."""
    if not _W32:
        return

    def _visit(hwnd: int, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        raw = win32gui.GetWindowText(hwnd)
        if enabled:
            hit = _PTN_SESSION.match(raw)
            if not hit:
                return
            _title_registry[hwnd] = raw
            try:
                win32gui.SetWindowText(hwnd, hit.group(1).strip())
            except Exception:
                pass
        elif hwnd in _title_registry:
            saved = _title_registry.pop(hwnd)
            try:
                win32gui.SetWindowText(hwnd, saved)
            except Exception:
                pass

    win32gui.EnumWindows(_visit, None)
