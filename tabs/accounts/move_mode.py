"""move_mode.py - Mode deplacement : clic gauche sur Dofus = personnage suivant.

Implémentation par polling (GetAsyncKeyState) au lieu d'un hook WH_MOUSE_LL.
Un hook bas niveau global laisse un hook orphelin si le thread est tué à la
fermeture, ce qui freeze la souris pendant plusieurs secondes sous Windows.
Le polling via QTimer évite entièrement ce problème.
"""
from __future__ import annotations
import sys as _move_sys
import threading
import time
from typing import Callable
import re as _mre

_PTN_SESSION = _mre.compile(r'^(.+?)\s*[-\u2013]\s*Dofus', _mre.IGNORECASE)
_PTN_LOADING = _mre.compile(r'^Dofus\s*Retro\b', _mre.IGNORECASE)

# Intervalle de polling en ms — assez court pour être réactif
_POLL_MS = 30
_COOLDOWN_MS = 96


class SwitchModeCtrl:
    """Mode déplacement — polling GetAsyncKeyState, sans hook bas niveau."""

    _SUPPORTED = _move_sys.platform == "win32"

    def __init__(self, cycle_fn: Callable,
                 on_state_change: Callable[[bool], None] | None = None):
        self._cycle_fn        = cycle_fn
        self._on_state_change = on_state_change
        self._active          = False
        self._last_ts         = 0.0
        self._prev_down       = False
        self._timer           = None  # QTimer, créé au premier toggle

    def _ensure_timer(self):
        """Crée le QTimer la première fois (doit être fait dans le thread Qt)."""
        if self._timer is not None:
            return
        if _move_sys.platform != "win32":
            return
        from PySide6.QtCore import QTimer
        self._timer = QTimer()
        self._timer.setInterval(_POLL_MS)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    def stop(self):
        """Arrête le polling proprement — appelé depuis le thread Qt."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def toggle(self) -> bool:
        self._ensure_timer()
        self._active = not self._active
        if self._on_state_change:
            self._on_state_change(self._active)
        return self._active

    @property
    def is_active(self) -> bool:
        return self._active

    def _poll(self):
        """Appelé toutes les 30ms par QTimer depuis le thread Qt principal."""
        if not self._active:
            self._prev_down = False
            return
        try:
            import ctypes
            # VK_LBUTTON = 0x01
            state = ctypes.windll.user32.GetAsyncKeyState(0x01)
            down  = bool(state & 0x8000)

            # Détecter le front montant (appui)
            if down and not self._prev_down:
                self._on_click()

            self._prev_down = down
        except Exception:
            pass

    def _on_click(self):
        """Vérifie si le clic est sur une fenêtre Dofus, puis appelle cycle_fn."""
        try:
            import ctypes
            import ctypes.wintypes as wt

            # Position curseur
            pt = wt.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

            # Fenêtre sous le curseur
            hwnd_under = ctypes.windll.user32.WindowFromPoint(pt)
            hwnd_root  = ctypes.windll.user32.GetAncestor(hwnd_under, 2)

            # Titre de la fenêtre
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd_root, buf, 256)
            title = buf.value

            if not (_PTN_SESSION.match(title) or _PTN_LOADING.match(title)):
                return

            # Cooldown
            now = time.monotonic()
            if now - self._last_ts < _COOLDOWN_MS / 1000.0:
                return
            self._last_ts = now

            # Déclencher après 95ms comme avant
            threading.Timer(0.095, self._cycle_fn).start()

        except Exception:
            pass
