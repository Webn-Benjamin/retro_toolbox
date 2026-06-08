"""move_mode.py - Mode deplacement : clic gauche sur Dofus = personnage suivant."""
from __future__ import annotations
import ctypes
import ctypes.wintypes as wt
import threading
import time
from typing import Callable

WH_MOUSE_LL    = 14
WM_LBUTTONDOWN = 0x0201
LLMHF_INJECTED = 0x00000001


class MouseHookData(ctypes.Structure):
    _fields_ = [
        ("pt",          wt.POINT),
        ("mouseData",   wt.DWORD),
        ("flags",       wt.DWORD),
        ("time",        wt.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class SwitchModeCtrl:
    """
    Mode deplacement : hook souris bas niveau (WH_MOUSE_LL).
    A chaque clic gauche sur une fenetre Dofus, appelle cycle_fn
    apres un court delai.
    """
    CYCLE_DELAY_MS = 95
    COOLDOWN_MS    = 96

    def __init__(self, cycle_fn: Callable,
                 on_state_change: Callable[[bool], None] | None = None):
        self._cycle_fn        = cycle_fn
        self._on_state_change = on_state_change
        self._active          = False
        self._last_ts         = 0.0
        self._hook            = None
        self._proc            = None
        self._thread          = threading.Thread(
            target=self._monitor_loop, daemon=True, name="MoveModeHook")
        self._thread.start()

    def toggle(self) -> bool:
        self._active = not self._active
        if self._on_state_change:
            self._on_state_change(self._active)
        return self._active

    @property
    def is_active(self) -> bool:
        return self._active

    def _is_game_hwnd(self, hwnd: int) -> bool:
        try:
            from tabs.accounts.window_manager import _PTN_SESSION, _PTN_LOADING
            title_buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, title_buf, 256)
            title = title_buf.value
            return bool(_PTN_SESSION.match(title) or _PTN_LOADING.match(title))
        except Exception:
            return False

    def _monitor_loop(self):
        LowLevelMouseProc = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_int, wt.WPARAM,
            ctypes.POINTER(MouseHookData),
        )

        def _callback(nCode, wParam, lParam):
            if nCode >= 0 and wParam == WM_LBUTTONDOWN:
                if not (lParam.contents.flags & LLMHF_INJECTED):
                    if self._active:
                        try:
                            pt = lParam.contents.pt
                            hwnd_under = ctypes.windll.user32.WindowFromPoint(pt)
                            # Remonter a la fenetre racine
                            hwnd_root = ctypes.windll.user32.GetAncestor(hwnd_under, 2)
                            if self._is_game_hwnd(hwnd_root):
                                now = time.monotonic()
                                if now - self._last_ts >= (self.COOLDOWN_MS / 1000.0):
                                    self._last_ts = now
                                    threading.Timer(
                                        self.CYCLE_DELAY_MS / 1000.0,
                                        self._cycle_fn
                                    ).start()
                        except Exception:
                            pass
            return ctypes.windll.user32.CallNextHookEx(
                self._hook, nCode, wParam, lParam)

        self._proc = LowLevelMouseProc(_callback)
        self._hook = ctypes.windll.user32.SetWindowsHookExW(
            WH_MOUSE_LL, self._proc, None, 0)

        msg = wt.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook:
            ctypes.windll.user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
