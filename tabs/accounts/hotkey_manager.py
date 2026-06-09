"""hotkey_manager.py — Raccourcis clavier globaux et Ctrl+Shift simulé."""
from __future__ import annotations
import sys as _sys
from typing import Callable

# Windows : keyboard (hook direct bas niveau)
# macOS   : pynput via os_bridge
if _sys.platform == "win32":
    try:
        import keyboard
        KEYBOARD_OK = True
    except ImportError:
        KEYBOARD_OK = False
else:
    KEYBOARD_OK = False

try:
    from pynput import keyboard as _pynput_kb
    PYNPUT_OK = True
except ImportError:
    PYNPUT_OK = False


class InputRelay:
    """Maintient Ctrl+Shift enfoncé sur la fenêtre active."""

    def __init__(self):
        self._on = False
        self._ctrl  = None
        self._shift = None

    @property
    def active(self) -> bool:
        return self._on

    def toggle(self, require_dofus_fg=None) -> bool:
        self._on = not self._on
        if _sys.platform == "win32" and KEYBOARD_OK:
            if self._on:
                keyboard.press("ctrl"); keyboard.press("shift")
            else:
                keyboard.release("shift"); keyboard.release("ctrl")
        elif _sys.platform == "darwin" and PYNPUT_OK:
            ctrl  = _pynput_kb.Key.ctrl
            shift = _pynput_kb.Key.shift
            kb    = _pynput_kb.Controller()
            if self._on:
                kb.press(ctrl); kb.press(shift)
            else:
                kb.release(shift); kb.release(ctrl)
        return self._on

    def sync_keys(self):
        if not self._on: return
        if _sys.platform == "win32" and KEYBOARD_OK:
            keyboard.release("shift"); keyboard.release("ctrl")
            keyboard.press("ctrl"); keyboard.press("shift")

    def clear_keys(self):
        if self._on:
            if _sys.platform == "win32" and KEYBOARD_OK:
                try:
                    keyboard.release("shift")
                    keyboard.release("ctrl")
                except Exception: pass
        self._on = False


class ShortcutTable:
    """Registre de raccourcis globaux identifiés par nom."""

    def __init__(self):
        self._registered: dict[str, tuple[str, any]] = {}
        self.ctrl_shift = InputRelay()

    def add(self, name: str, combo: str, fn: Callable) -> bool:
        if not combo.strip(): return False
        self.remove(name)

        if _sys.platform == "darwin":
            try:
                from os_bridge.bridge import register_hotkey
                ok = register_hotkey(combo, fn)
                if ok:
                    self._registered[name] = (combo, None)
                return ok
            except Exception as e:
                print(f"[ShortcutTable Mac] {name}={combo}: {e}")
                return False

        if not KEYBOARD_OK: return False
        if not self._is_valid_win(combo): return False
        try:
            hook = keyboard.add_hotkey(combo, fn, suppress=False)
            self._registered[name] = (combo, hook)
            return True
        except Exception as e:
            print(f"[ShortcutTable] {name}={combo}: {e}")
            return False

    def remove(self, name: str):
        if name in self._registered:
            _, hook = self._registered.pop(name)
            if hook and KEYBOARD_OK:
                try: keyboard.remove_hotkey(hook)
                except: pass

    def clear(self):
        for name in list(self._registered):
            self.remove(name)
        self.ctrl_shift.clear_keys()

    def _is_valid_win(self, combo: str) -> bool:
        try: keyboard.parse_hotkey(combo); return True
        except: return False

    def is_valid(self, combo: str) -> bool:
        if not combo.strip(): return False
        if _sys.platform == "darwin":
            # Valider format pynput : ex "ctrl+tab", "ctrl+shift+a"
            parts = combo.lower().replace("ctrl","control").split("+")
            known_mods = {"control","cmd","alt","shift"}
            has_mod = any(p in known_mods for p in parts)
            has_key = any(p not in known_mods for p in parts)
            return has_mod and has_key
        return self._is_valid_win(combo) if KEYBOARD_OK else False


class CycleEngine:
    """Mode Farm Sadi — ignore N tours de combat pour les Sadidas désignés."""

    def __init__(self, turns: int = 3):
        self._turns:  int            = max(1, int(turns))
        self._sadis:  set[str]       = set()
        self._counts: dict[str, int] = {}

    @property
    def turns(self) -> int: return self._turns
    @turns.setter
    def turns(self, v: int): self._turns = max(1, int(v))

    @property
    def sadis(self) -> set[str]: return set(self._sadis)

    def set_sadis(self, pseudos: set[str]):
        self._sadis = set(pseudos)
        for p in list(self._counts):
            if p not in self._sadis: del self._counts[p]

    def is_sadi(self, pseudo: str) -> bool:
        return pseudo in self._sadis

    def trigger(self, pseudo: str):
        if pseudo in self._sadis:
            self._counts[pseudo] = self._turns

    def check(self, pseudo: str) -> tuple[bool, int]:
        left = self._counts.get(pseudo, 0)
        if left <= 0: return False, 0
        new = left - 1
        if new == 0: del self._counts[pseudo]
        else: self._counts[pseudo] = new
        return True, new

    def remaining(self, pseudo: str) -> int:
        return self._counts.get(pseudo, 0)

    def cancel(self, pseudo: str): self._counts.pop(pseudo, None)
    def cancel_all(self): self._counts.clear()
    def is_active(self) -> bool: return bool(self._counts)
