"""platform/windows.py — Implémentations Win32."""
from __future__ import annotations
import re, threading, time
from dataclasses import dataclass
from typing import Callable

try:
    import win32gui, win32con, win32api, win32process
    _OK = True
except ImportError:
    _OK = False

try:
    import psutil
    _PS = True
except ImportError:
    _PS = False

_PTN_SESSION = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_PTN_LOADING = re.compile(r"^Dofus\s*Retro\b",      re.IGNORECASE)
_PTN_ALERT   = re.compile(r"^\[!\]",                  re.IGNORECASE)
_title_reg: dict[int, str] = {}

@dataclass
class GameWindow:
    hwnd: int; name: str; loading: bool = False

def _pid_alive(pid):
    if not _PS: return True
    try: return "dofus" in psutil.Process(pid).name().lower()
    except: return False

def list_windows() -> list[GameWindow]:
    if not _OK:
        return []
    result = []
    def _visit(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd): return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not _pid_alive(pid): return
        except: return
        raw = win32gui.GetWindowText(hwnd)
        src = _title_reg.get(hwnd, raw)
        m = _PTN_SESSION.match(src)
        if m: result.append(GameWindow(hwnd=hwnd, name=m.group(1).strip()))
        elif _PTN_LOADING.match(raw):
            result.append(GameWindow(hwnd=hwnd, name="Chargement…", loading=True))
    win32gui.EnumWindows(_visit, None)
    return result

def focus_window(hwnd: int) -> bool:
    if not _OK: return False
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        try: win32gui.SetForegroundWindow(hwnd)
        finally: win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except: return False

def focus_by_name(name: str) -> bool:
    for w in list_windows():
        if w.name.lower() == name.lower(): return focus_window(w.hwnd)
    return False

def foreground_hwnd() -> int | None:
    try: return win32gui.GetForegroundWindow()
    except: return None

def is_game_active() -> bool:
    try:
        hwnd = win32gui.GetForegroundWindow()
        raw = _title_reg.get(hwnd, win32gui.GetWindowText(hwnd))
        return bool(_PTN_SESSION.match(raw) or _PTN_LOADING.match(raw))
    except: return False

def compact_titles(enabled: bool):
    if not _OK: return
    def _v(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd): return
        raw = win32gui.GetWindowText(hwnd)
        if enabled:
            m = _PTN_SESSION.match(raw)
            if not m: return
            _title_reg[hwnd] = raw
            try: win32gui.SetWindowText(hwnd, m.group(1).strip())
            except: pass
        elif hwnd in _title_reg:
            saved = _title_reg.pop(hwnd)
            try: win32gui.SetWindowText(hwnd, saved)
            except: pass
    win32gui.EnumWindows(_v, None)

def register_hotkey(combo: str, fn: Callable) -> bool:
    try:
        import keyboard
        keyboard.add_hotkey(combo, fn, suppress=False)
        return True
    except: return False

def get_cursor_pos() -> tuple[int,int]:
    try: return win32api.GetCursorPos()
    except: return (0,0)

def get_rbutton_state() -> bool:
    try: return bool(win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000)
    except: return False

def window_at(x, y) -> tuple[int, str]:
    """Retourne (hwnd, title) de la fenêtre sous (x,y)."""
    try:
        hwnd = win32gui.WindowFromPoint((x, y))
        top  = hwnd
        while True:
            p = win32gui.GetParent(top)
            if not p: break
            top = p
        return top, win32gui.GetWindowText(top).lower()
    except: return 0, ""

def simulate_ctrl_shift(key: str):
    """Envoie Ctrl+Shift+<key> à la fenêtre active."""
    try:
        VK = ord(key.upper())
        for vk in [win32con.VK_CONTROL, win32con.VK_SHIFT, VK]:
            win32api.keybd_event(vk, 0, 0, 0)
        for vk in [VK, win32con.VK_SHIFT, win32con.VK_CONTROL]:
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
    except: pass


# ── Watcher autofocus — Toast Windows ─────────────────────────────────
class AlertWatcher:
    """Lit les notifications Toast Dofus via winsdk."""
    def __init__(self, callback: Callable[[str, str], None]):
        self._cb = callback
        self._thread = None
        self._running = False

    def start(self):
        from tabs.accounts.toast_reader import AlertWatcher as _TW
        self._inner = _TW(self._cb)
        self._inner.start()

    def stop(self):
        if hasattr(self, "_inner"):
            self._inner.stop()
