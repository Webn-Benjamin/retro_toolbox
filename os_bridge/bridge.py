"""os_bridge/bridge.py — Point d'entrée unique multiplateforme."""
import sys

if sys.platform == "win32":
    from os_bridge.windows import (
        GameWindow, list_windows, focus_window, focus_by_name,
        foreground_hwnd, is_game_active, compact_titles,
        register_hotkey, get_cursor_pos, get_rbutton_state,
        window_at, simulate_ctrl_shift, AlertWatcher,
    )
elif sys.platform == "darwin":
    from os_bridge.mac import (
        GameWindow, list_windows, focus_window, focus_by_name,
        foreground_hwnd, is_game_active, compact_titles,
        register_hotkey, get_cursor_pos, get_rbutton_state,
        window_at, simulate_ctrl_shift, AlertWatcher,
    )
else:
    from dataclasses import dataclass
    from typing import Callable

    @dataclass
    class GameWindow:
        hwnd: int; name: str; loading: bool = False

    def list_windows():          return []
    def focus_window(h):         return False
    def focus_by_name(n):        return False
    def foreground_hwnd():       return None
    def is_game_active():        return False
    def compact_titles(e):       pass
    def register_hotkey(c, fn):  return False
    def get_cursor_pos():        return (0, 0)
    def get_rbutton_state():     return False
    def window_at(x, y):         return (0, "")
    def simulate_ctrl_shift(k):  pass

    class AlertWatcher:
        def __init__(self, cb, **kw): pass
        def start(self): pass
        def stop(self):  pass
