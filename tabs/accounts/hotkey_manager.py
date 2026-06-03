"""hotkey_manager.py — Raccourcis clavier globaux et Ctrl+Shift simulé."""
from __future__ import annotations
from typing import Callable

try:
    import keyboard
    KEYBOARD_OK = True
except ImportError:
    KEYBOARD_OK = False


class CtrlShiftSimulator:
    """Maintient Ctrl+Shift enfoncé sur la fenêtre active."""

    def __init__(self):
        self._on = False

    @property
    def active(self) -> bool:
        return self._on

    def toggle(self, require_dofus_fg=None) -> bool:
        self._on = not self._on
        if KEYBOARD_OK:
            if self._on:
                keyboard.press("ctrl")
                keyboard.press("shift")
            else:
                keyboard.release("shift")
                keyboard.release("ctrl")
        return self._on

    def reapply(self):
        """Ré-appuie Ctrl+Shift après un changement de focus."""
        if not self._on or not KEYBOARD_OK: return
        keyboard.release("shift"); keyboard.release("ctrl")
        keyboard.press("ctrl"); keyboard.press("shift")

    def release_all(self):
        if self._on and KEYBOARD_OK:
            try:
                keyboard.release("shift")
                keyboard.release("ctrl")
            except Exception: pass
        self._on = False


class HotkeyRegistry:
    """Registre de raccourcis globaux identifiés par nom."""

    def __init__(self):
        self._registered: dict[str, tuple[str, any]] = {}
        self.ctrl_shift = CtrlShiftSimulator()

    def add(self, name: str, combo: str, fn: Callable) -> bool:
        if not KEYBOARD_OK or not combo.strip(): return False
        self.remove(name)
        if not self._is_valid(combo): return False
        try:
            hook = keyboard.add_hotkey(combo, fn, suppress=False)
            self._registered[name] = (combo, hook)
            return True
        except Exception as e:
            print(f"[HotkeyRegistry] {name}={combo}: {e}")
            return False

    def remove(self, name: str):
        if name in self._registered:
            _, hook = self._registered.pop(name)
            try: keyboard.remove_hotkey(hook)
            except: pass

    def clear(self):
        if not KEYBOARD_OK: return
        for name in list(self._registered):
            self.remove(name)
        self.ctrl_shift.release_all()

    def _is_valid(self, combo: str) -> bool:
        try: keyboard.parse_hotkey(combo); return True
        except: return False

    def is_valid(self, combo: str) -> bool:
        return self._is_valid(combo) if KEYBOARD_OK and combo.strip() else False


class FarmSadiManager:
    """
    Mode Farm Sadi — ignore les notifications de combat pendant N tours
    pour les personnages Sadida désignés.

    Usage :
        mgr = FarmSadiManager(turns=3)
        mgr.set_sadis({"St-Sadi", "St-Sadi2"})

        # Appuie raccourci → déclenche le compteur
        mgr.trigger("St-Sadi")

        # Avant chaque autofocus combat :
        skip, left = mgr.check("St-Sadi")
        if skip: return  # ignorer ce tour
    """

    def __init__(self, turns: int = 3):
        self._turns:   int            = max(1, int(turns))
        self._sadis:   set[str]       = set()
        self._counts:  dict[str, int] = {}

    # ── Config ─────────────────────────────────────────────

    @property
    def turns(self) -> int: return self._turns

    @turns.setter
    def turns(self, v: int): self._turns = max(1, int(v))

    @property
    def sadis(self) -> set[str]: return set(self._sadis)

    def set_sadis(self, pseudos: set[str]):
        self._sadis = set(pseudos)
        for p in list(self._counts):
            if p not in self._sadis:
                del self._counts[p]

    def is_sadi(self, pseudo: str) -> bool:
        return pseudo in self._sadis

    # ── Contrôle ───────────────────────────────────────────

    def trigger(self, pseudo: str):
        """Démarre ou remet à zéro le compteur pour ce Sadida."""
        if pseudo in self._sadis:
            self._counts[pseudo] = self._turns

    def check(self, pseudo: str) -> tuple[bool, int]:
        """
        Appelé avant chaque autofocus combat.
        Retourne (skip, tours_restants).
        Décrémente le compteur à chaque appel positif.
        """
        left = self._counts.get(pseudo, 0)
        if left <= 0:
            return False, 0
        new = left - 1
        if new == 0:
            del self._counts[pseudo]
        else:
            self._counts[pseudo] = new
        return True, new

    def remaining(self, pseudo: str) -> int:
        return self._counts.get(pseudo, 0)

    def cancel(self, pseudo: str):
        self._counts.pop(pseudo, None)

    def cancel_all(self):
        self._counts.clear()

    def is_active(self) -> bool:
        return bool(self._counts)
