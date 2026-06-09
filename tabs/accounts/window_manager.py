"""window_manager.py — Re-exporte depuis os_bridge.bridge (cross-platform)."""
from os_bridge.bridge import (
    GameWindow  as SessionEntry,
    list_windows as collect_sessions,
    focus_window as activate_window,
    focus_by_name as activate_by_name,
    foreground_hwnd as foreground_handle,
    is_game_active as is_game_focused,
    compact_titles as apply_compact_titles,
    get_cursor_pos, get_rbutton_state, window_at,
    simulate_ctrl_shift,
)
import re as _re

_PTN_SESSION = _re.compile(r"^(.+?)\s*[-–]\s*Dofus", _re.IGNORECASE)
_PTN_LOADING = _re.compile(r"^Dofus\s*Retro\b",       _re.IGNORECASE)

def get_display_name(hwnd: int) -> str | None:
    for w in collect_sessions():
        if w.hwnd == hwnd: return w.pseudo
    return None
