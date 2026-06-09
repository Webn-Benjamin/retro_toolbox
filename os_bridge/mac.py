"""os_bridge/mac.py — Implémentations macOS : même interface que Windows."""
from __future__ import annotations
import re, subprocess, threading, time, os
from dataclasses import dataclass
from typing import Callable

_PTN_SESSION = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_PTN_LOADING = re.compile(r"^Dofus\s*Retro\b",       re.IGNORECASE)

@dataclass
class GameWindow:
    hwnd: int; pseudo: str; loading: bool = False


# ─── Quartz helpers ──────────────────────────────────────────────────
def _quartz_wins() -> list[dict]:
    try:
        import Quartz
        wins = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionAll |
            Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID)
        return list(wins) if wins else []
    except Exception:
        return []


def list_windows() -> list[GameWindow]:
    result = []
    seen_ids = set()
    idx = 1
    for w in _quartz_wins():
        owner  = (w.get("kCGWindowOwnerName") or "").lower()
        wid    = w.get("kCGWindowNumber", 0)
        layer  = w.get("kCGWindowLayer", 0)
        bounds = w.get("kCGWindowBounds", {})
        if wid in seen_ids: continue
        if "dofus" not in owner: continue
        if layer not in (0, -1): continue
        if bounds.get("Width", 0) < 500 or bounds.get("Height", 0) < 400: continue
        if (w.get("kCGWindowAlpha", 1.0) or 0) < 0.5: continue
        seen_ids.add(wid)
        title = (w.get("kCGWindowName") or "").strip()
        clean = re.sub(r"^\[!\]\s*", "", title)
        m     = _PTN_SESSION.match(clean)
        name  = m.group(1).strip() if m else (title if len(title) > 3 else f"Fenêtre {idx}")
        idx  += 1
        result.append(GameWindow(hwnd=wid, pseudo=name))
    return result


def focus_window(wid: int) -> bool:
    for w in _quartz_wins():
        if w.get("kCGWindowNumber") == wid:
            pname = w.get("kCGWindowOwnerName", "")
            if not pname: continue
            try:
                script = f'''tell application "{pname}" to activate
tell application "System Events" to tell process "{pname}" to set frontmost to true'''
                subprocess.run(["osascript", "-e", script],
                               capture_output=True, timeout=3)
                return True
            except Exception: pass
    return False


def focus_by_name(name: str) -> bool:
    for w in list_windows():
        if w.pseudo.lower() == name.lower(): return focus_window(w.hwnd)
    return False


def foreground_hwnd() -> int | None:
    wins = _quartz_wins()
    return wins[0].get("kCGWindowNumber") if wins else None


def is_game_active() -> bool:
    wins = _quartz_wins()
    return bool(wins and "dofus" in (wins[0].get("kCGWindowOwnerName") or "").lower())


def compact_titles(_enabled: bool): pass


def get_cursor_pos() -> tuple[int, int]:
    try:
        import Quartz
        loc = Quartz.NSEvent.mouseLocation()
        h   = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID()).size.height
        return int(loc.x), int(h - loc.y)
    except Exception: return (0, 0)


def get_rbutton_state() -> bool: return False


def window_at(x: int, y: int) -> tuple[int, str]:
    for w in _quartz_wins():
        b = w.get("kCGWindowBounds", {})
        if (b.get("X",0) <= x <= b.get("X",0)+b.get("Width",0) and
                b.get("Y",0) <= y <= b.get("Y",0)+b.get("Height",0)):
            owner = (w.get("kCGWindowOwnerName") or "").lower()
            title = (w.get("kCGWindowName") or "").lower()
            return w.get("kCGWindowNumber", 0), f"{owner} {title}"
    return 0, ""


def simulate_ctrl_shift(key: str):
    try:
        subprocess.run(["osascript", "-e",
            f'tell application "System Events" to keystroke "{key}" '
            f'using {{control down, shift down}}'],
            capture_output=True, timeout=2)
    except Exception: pass


def register_hotkey(combo: str, fn: Callable) -> bool:
    try:
        from AppKit import NSEvent
        parts    = combo.lower().replace("ctrl","control").split("+")
        mod_map  = {"control":1<<18,"cmd":1<<20,"alt":1<<19,"shift":1<<17}
        mods     = 0
        char_key = None
        for p in parts:
            if p in mod_map: mods |= mod_map[p]
            else: char_key = p
        if char_key is None: return False
        NSKeyDownMask = 1 << 10
        def _handler(event):
            try:
                chars = (event.charactersIgnoringModifiers() or "").lower()
                flags = event.modifierFlags() & 0xFFFF0000
                if chars == char_key and (flags & mods) == mods: fn()
            except Exception: pass
        monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSKeyDownMask, _handler)
        return monitor is not None
    except Exception as e:
        print(f"[Mac] Raccourci {combo}: {e}")
        return False


# ─── Catégorisation (même logique que Windows) ───────────────────────
_RULES = [
    ("combat",  "⚔️",  [re.compile(r"de jouer|turn to play|Le toca jugar", re.I)]),
    ("echange", "🔄",  [re.compile(r"propose.+échange|offers.+trade", re.I)]),
    ("groupe",  "👥",  [re.compile(r"invite.+rejoindre|invited.+join", re.I)]),
    ("mp",      "💬",  [re.compile(r"^de |^from ", re.I)]),
    ("defi",    "🏆",  [re.compile(r"te défie|challenges you", re.I)]),
    ("craft",   "🔨",  [re.compile(r"talents|atelier|fabriqués|skills|workshop", re.I)]),
    ("pvp",     "🛡️",  [re.compile(r"percepteur.+attaqué|perceptor.+attacked", re.I)]),
]

def _categorize(body: str) -> tuple[str, str]:
    for ntype, emoji, patterns in _RULES:
        if any(p.search(body) for p in patterns):
            return ntype, emoji
    return "other", "🔔"


# ─── AlertWatcher Mac — screencapture + tesseract ────────────────────
from dataclasses import dataclass as _dc

@_dc
class AlertEvent:
    ntype: str; emoji: str; pseudo: str; body: str


class AlertWatcher:
    """
    Équivalent Mac de AlertWatcher Windows.
    Utilise screencapture (natif macOS) + tesseract pour lire
    les bannières de notification Dofus.
    Interface identique à la version Windows.
    """

    def __init__(self, callback: Callable):
        self._cb      = callback
        self._running = False

    def set_dismiss(self, v): pass

    def start(self) -> bool:
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True, name="MacAlertWatcher")
        t.start()
        print("[Mac] AlertWatcher démarré")
        return True

    def stop(self):
        self._running = False

    def _get_screen_width(self) -> int:
        try:
            import Quartz
            b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
            return int(b.size.width)
        except Exception:
            return 1920

    def _capture_notif_area(self, sw: int) -> str | None:
        """Capture le coin notification et retourne le texte OCR."""
        tmp = "/tmp/rt_notif_cap.png"
        x   = max(0, sw - 440)
        try:
            # screencapture -x = sans son, -R = région
            r = subprocess.run(
                ["screencapture", "-x", "-R", f"{x},0,440,200", tmp],
                capture_output=True, timeout=2)
            if not os.path.exists(tmp): return None
            import pytesseract
            from PIL import Image
            img  = Image.open(tmp).convert("L")  # niveaux de gris
            text = pytesseract.image_to_string(img, config="--psm 6").strip()
            try: os.unlink(tmp)
            except Exception: pass
            return text if len(text) > 3 else None
        except Exception as e:
            print(f"[Mac] Capture erreur: {e}")
            return None

    def _decode(self, text: str) -> AlertEvent | None:
        """
        Parse le texte OCR pour extraire pseudo + type.
        Format attendu :
          ligne 1 : "Pseudo - Dofus Retro v1.x"
          ligne 2 : "C'est à votre tour de jouer"
        """
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines: return None

        pseudo = ""
        body   = ""

        # Chercher le pseudo dans chaque ligne
        for line in lines:
            m = _PTN_SESSION.match(line)
            if m:
                pseudo = m.group(1).strip()
                break

        # Si pas trouvé via regex, chercher dans les fenêtres connues
        if not pseudo:
            text_low = text.lower()
            for win in list_windows():
                if win.pseudo.lower() in text_low:
                    pseudo = win.pseudo
                    break

        if not pseudo: return None

        # Corps = lignes qui ne sont pas le titre
        body_lines = [l for l in lines if not _PTN_SESSION.match(l)
                      and "Dofus" not in l and len(l) > 3]
        body = " ".join(body_lines)

        ntype, emoji = _categorize(body or text)
        if ntype == "other": return None

        return AlertEvent(ntype=ntype, emoji=emoji, pseudo=pseudo, body=body)

    def _loop(self):
        sw        = self._get_screen_width()
        last_text = ""
        seen: set[str] = set()

        print(f"[Mac] Surveillance notifications (largeur écran: {sw}px)")

        while self._running:
            try:
                text = self._capture_notif_area(sw)
                if text and text != last_text:
                    print(f"[Mac] OCR: {repr(text[:80])}")
                    last_text = text
                    ev = self._decode(text)
                    if ev and ev.pseudo not in seen:
                        seen.add(ev.pseudo)
                        if len(seen) > 20: seen.pop()
                        print(f"[Mac] → {ev.ntype}: {ev.pseudo}")
                        threading.Thread(
                            target=self._cb, args=(ev,),
                            daemon=True).start()
                elif not text:
                    last_text = ""  # reset quand zone vide
            except Exception as e:
                print(f"[Mac] Boucle erreur: {e}")
            time.sleep(0.35)
