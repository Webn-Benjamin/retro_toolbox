"""focus_guard.py — Empêche les fenêtres exclues du cycle de garder le focus.

Dofus force parfois le focus sur sa fenêtre quand c'est son tour de jeu.
Ce module installe un hook Win32 EVENT_SYSTEM_FOREGROUND qui détecte ça et
re-focus immédiatement la dernière fenêtre active non-exclue.
"""
from __future__ import annotations
import ctypes
import ctypes.wintypes as wt
import threading
from typing import Callable

try:
    import win32gui
    import win32con
    import win32api
    _OK = True
except ImportError:
    _OK = False

# Constantes Win32
_EVENT_SYSTEM_FOREGROUND = 0x0003
_WINEVENT_OUTOFCONTEXT   = 0x0000


class FocusGuard:
    """Surveille les changements de fenêtre active.
    Si la fenêtre qui prend le focus appartient à un pseudo exclu,
    re-focus immédiatement `last_active_hwnd`.
    """

    def __init__(self):
        self._excluded:       set[str]  = set()
        self._hwnd_to_pseudo: dict[int, str] = {}
        self._last_hwnd:      int | None = None
        self._hook            = None
        self._thread:  threading.Thread | None = None
        self._running  = False
        # Référence forte sur le callback pour éviter le GC
        self._hook_proc = None

    # ── API publique ───────────────────────────────────────

    def update(self, excluded: set[str], hwnd_to_pseudo: dict[int, str]):
        """Appelé à chaque refresh AccountPanel."""
        self._excluded       = set(excluded)
        self._hwnd_to_pseudo = dict(hwnd_to_pseudo)

    def set_last_active(self, hwnd: int | None):
        """Mémoriser la dernière fenêtre active non-exclue."""
        if hwnd and self._hwnd_to_pseudo.get(hwnd) not in self._excluded:
            self._last_hwnd = hwnd

    def start(self):
        if not _OK or self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="FocusGuard")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._hook:
            try:
                ctypes.windll.user32.UnhookWinEvent(self._hook)
            except Exception:
                pass
            self._hook = None
        # Poster WM_QUIT dans le thread de la boucle de messages
        if self._thread and self._thread.is_alive():
            ctypes.windll.user32.PostThreadMessageW(
                self._thread.ident, 0x0012, 0, 0)  # WM_QUIT

    # ── Boucle interne ────────────────────────────────────

    def _run(self):
        _WinEventProc = ctypes.WINFUNCTYPE(
            None,
            wt.HANDLE, wt.DWORD, wt.HWND,
            wt.LONG, wt.LONG, wt.DWORD, wt.DWORD,
        )

        def _callback(hWinEventHook, event, hwnd, idObject, idChild,
                      dwEventThread, dwmsEventTime):
            if not hwnd:
                return
            pseudo = self._hwnd_to_pseudo.get(hwnd)
            if pseudo and pseudo in self._excluded:
                # Vérifier si la souris est sur cette fenêtre :
                # si oui → clic volontaire de l'utilisateur, on laisse faire.
                # si non → Dofus a forcé le focus (tour de jeu), on re-focus.
                try:
                    cx, cy = win32api.GetCursorPos()
                    hwnd_under = win32gui.WindowFromPoint((cx, cy))
                    # Remonter au parent top-level
                    while True:
                        p = win32gui.GetParent(hwnd_under)
                        if not p:
                            break
                        hwnd_under = p
                    if hwnd_under == hwnd:
                        # Clic volontaire → mémoriser quand même comme dernière
                        self._last_hwnd = hwnd
                        return
                except Exception:
                    pass
                # Focus forcé par le jeu → re-focus la dernière bonne fenêtre
                target = self._last_hwnd
                if target and target != hwnd:
                    try:
                        if win32gui.IsIconic(target):
                            win32gui.ShowWindow(target, win32con.SW_RESTORE)
                        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                        try:
                            win32gui.SetForegroundWindow(target)
                        finally:
                            win32api.keybd_event(
                                win32con.VK_MENU, 0,
                                win32con.KEYEVENTF_KEYUP, 0)
                    except Exception:
                        pass
            else:
                # Fenêtre normale → mémoriser comme dernière active
                if pseudo:  # c'est bien une fenêtre Dofus connue
                    self._last_hwnd = hwnd

        self._hook_proc = _WinEventProc(_callback)
        self._hook = ctypes.windll.user32.SetWinEventHook(
            _EVENT_SYSTEM_FOREGROUND,
            _EVENT_SYSTEM_FOREGROUND,
            None,
            self._hook_proc,
            0, 0,
            _WINEVENT_OUTOFCONTEXT,
        )

        # Boucle de messages — nécessaire pour que le hook soit dispatché
        msg = wt.MSG()
        while self._running:
            ret = ctypes.windll.user32.GetMessageW(
                ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook:
            ctypes.windll.user32.UnhookWinEvent(self._hook)
            self._hook = None
