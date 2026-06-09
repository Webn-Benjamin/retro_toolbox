"""os_bridge/mac.py — Implémentations macOS : Quartz + notifications système."""
from __future__ import annotations
import re, subprocess, threading, time, os, glob
from dataclasses import dataclass
from typing import Callable

_PTN_SESSION = re.compile(r"^(.+?)\s*[-–]\s*Dofus", re.IGNORECASE)
_PTN_LOADING = re.compile(r"^Dofus\s*Retro\b",       re.IGNORECASE)
_PTN_ALERT   = re.compile(r"^\[!\]",                   re.IGNORECASE)


@dataclass
class GameWindow:
    hwnd: int; pseudo: str; loading: bool = False


# ─── Quartz helpers ──────────────────────────────────────────────────
def _quartz_wins() -> list[dict]:
    try:
        import Quartz
        wins = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly |
            Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID)
        return list(wins) if wins else []
    except Exception:
        return []


def has_screen_permission() -> bool:
    try:
        import Quartz
        wins = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        if wins:
            for w in wins:
                if w.get("kCGWindowName") is not None:
                    return True
            return False
        return True
    except Exception:
        return False


def list_windows() -> list[GameWindow]:
    result = []
    seen_ids = set()
    idx = 1

    try:
        import Quartz as _Q
        all_wins = _Q.CGWindowListCopyWindowInfo(
            _Q.kCGWindowListOptionAll | _Q.kCGWindowListExcludeDesktopElements,
            _Q.kCGNullWindowID) or []
    except Exception:
        all_wins = _quartz_wins()

    for w in all_wins:
        owner  = (w.get("kCGWindowOwnerName") or "").lower()
        wid    = w.get("kCGWindowNumber", 0)
        layer  = w.get("kCGWindowLayer", 0)
        bounds = w.get("kCGWindowBounds", {})
        alpha  = w.get("kCGWindowAlpha", 1.0)

        if wid in seen_ids: continue
        if "dofus" not in owner: continue
        if layer not in (0, -1): continue
        if bounds.get("Width", 0) < 500: continue
        if bounds.get("Height", 0) < 400: continue
        if alpha < 0.5: continue

        seen_ids.add(wid)
        title = (w.get("kCGWindowName") or "").strip()
        clean = re.sub(r"^\[!\]\s*", "", title)
        m     = _PTN_SESSION.match(clean)
        if m:
            name = m.group(1).strip()
        elif title and len(title) > 3:
            name = title
        else:
            name = f"Fenêtre {idx}"
        idx += 1
        result.append(GameWindow(hwnd=wid, pseudo=name))
    return result


def focus_window(wid: int) -> bool:
    for w in _quartz_wins():
        if w.get("kCGWindowNumber") == wid:
            pname = w.get("kCGWindowOwnerName", "")
            if not pname: continue
            try:
                # Désminimiser si besoin + mettre au premier plan
                script = f'''
tell application "{pname}"
    activate
    try
        set miniaturized of window 1 to false
    end try
end tell
tell application "System Events"
    tell process "{pname}"
        set frontmost to true
    end tell
end tell'''
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
    except Exception:
        return (0, 0)


def get_rbutton_state() -> bool:
    return False


def window_at(x: int, y: int) -> tuple[int, str]:
    for w in _quartz_wins():
        b = w.get("kCGWindowBounds", {})
        if (b.get("X", 0) <= x <= b.get("X", 0) + b.get("Width", 0) and
                b.get("Y", 0) <= y <= b.get("Y", 0) + b.get("Height", 0)):
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
    """Raccourcis globaux Mac via NSEvent global monitor."""
    try:
        from AppKit import NSEvent
        import threading

        parts   = combo.lower().replace("ctrl","control").split("+")
        mod_map = {
            "control": 1 << 18,  # NSControlKeyMask
            "cmd":     1 << 20,  # NSCommandKeyMask
            "alt":     1 << 19,  # NSAlternateKeyMask
            "shift":   1 << 17,  # NSShiftKeyMask
        }
        mods_needed = 0
        char_key    = None
        for p in parts:
            if p in mod_map: mods_needed |= mod_map[p]
            else:            char_key = p

        if char_key is None: return False

        NSKeyDownMask = 1 << 10

        def _handler(event):
            try:
                chars = (event.charactersIgnoringModifiers() or "").lower()
                flags = event.modifierFlags() & 0xFFFF0000
                if chars == char_key and (flags & mods_needed) == mods_needed:
                    fn()
            except Exception: pass

        monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSKeyDownMask, _handler)
        return monitor is not None
    except Exception as e:
        print(f"[Mac] Raccourci {combo} non disponible: {e}")
        return False


# ─── Surveillance notifications macOS via bannière Quartz ────────────
def _find_notif_db() -> str | None:
    """Trouve la DB notifications — essaie tous les chemins connus."""
    import sqlite3
    patterns = [
        os.path.expanduser("~/Library/Application Support/NotificationCenter/*.db"),
        os.path.expanduser("~/Library/Application Support/NotificationCenter/db2"),
        os.path.expanduser("~/Library/Application Support/NotificationCenter/db"),
        "/private/var/folders/*/*/C/com.apple.notificationcenter/db2/db",
    ]
    for p in patterns:
        for match in glob.glob(p):
            try:
                conn = sqlite3.connect(f"file:{match}?mode=ro", uri=True)
                cur  = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cur.fetchall()]
                conn.close()
                if tables:
                    return match
            except Exception:
                pass
    return None


def _get_db_schema(db_path: str) -> tuple[str, str, str] | None:
    """Retourne (table, id_col, data_col) selon le schéma détecté."""
    import sqlite3
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        conn.close()
        if "record" in tables:
            return ("record", "record_id", "data")
        if "presented_notifications" in tables:
            return ("presented_notifications", "rowid", "encoded_data")
    except Exception:
        pass
    return None


def _read_last_notif_id(db_path: str) -> int:
    schema = _get_db_schema(db_path)
    if not schema: return 0
    table, id_col, _ = schema
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        cur.execute(f"SELECT MAX({id_col}) FROM {table}")
        row = cur.fetchone(); conn.close()
        return row[0] or 0
    except Exception:
        return 0


def _read_new_notifs(db_path: str, since_id: int) -> list[dict]:
    schema = _get_db_schema(db_path)
    if not schema: return []
    table, id_col, data_col = schema
    results = []
    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        cur.execute(f"SELECT {id_col}, {data_col} FROM {table} WHERE {id_col} > ?",
                    (since_id,))
        for row in cur.fetchall():
            results.append({"id": row[0], "raw": row[1]})
        conn.close()
    except Exception:
        pass
    return results


# ─── Surveillance bannière notification via Quartz ───────────────────
def _watch_notif_banner(callback):
    """
    Surveille TOUTES les nouvelles fenêtres — détecte les bannières de
    notification par leur contenu (pas par leur owner).
    """
    _DOFUS_KW = ["jouer","tour","trade","échange","exchange","combat",
                 "groupe","group","message"," mp ","défi","challenge",
                 "craft","pvp","percepteur","dofus"]
    seen: set[int] = set()
    known: set[int] = set()

    while True:
        try:
            current_wins = _quartz_wins()
            current_ids  = {w.get("kCGWindowNumber",0) for w in current_wins}

            # Détecter les NOUVELLES fenêtres
            new_ids = current_ids - known
            known   = current_ids

            for w in current_wins:
                wid   = w.get("kCGWindowNumber", 0)
                if wid not in new_ids or wid in seen: continue

                owner = (w.get("kCGWindowOwnerName") or "").lower()
                title = (w.get("kCGWindowName") or "").strip().lower()
                layer = w.get("kCGWindowLayer", 0)

                # Ignorer nos propres fenêtres et Dofus lui-même
                if "python" in owner or "retro toolbox" in owner: continue
                if "dofus" in owner: continue

                # Chercher une bannière contenant du contenu Dofus
                content = f"{owner} {title}"
                if any(kw in content for kw in _DOFUS_KW):
                    seen.add(wid)
                    wins   = list_windows()
                    pseudo = wins[0].pseudo if wins else ""
                    if pseudo:
                        try:
                            from tabs.accounts.toast_reader import _categorize
                            ntype, _ = _categorize(title)
                            if ntype == "other": ntype = "combat"
                        except Exception:
                            ntype = "combat"
                        print(f"[Mac Banner] {owner} | {title} → {ntype}: {pseudo}")
                        callback(pseudo, ntype)

            # Nettoyer
            seen &= current_ids
        except Exception:
            pass
        time.sleep(0.15)


# ─── AlertWatcher — double mécanisme : notifications + polling titres ─
class AlertWatcher:
    """
    Autofocus Mac via deux mécanismes combinés :
    1. Surveillance base de données notifications macOS (équivalent Toast Windows)
    2. Polling titres de fenêtres [!] toutes les 200ms (fallback)
    """

    def __init__(self, callback: Callable[[str, str], None]):
        self._cb      = callback
        self._running = False
        self._seen_titles: set[int] = set()

    def start(self):
        self._running = True
        # Interception directe des notifications macOS (équivalent winsdk Windows)
        _start_notification_listeners(self._cb)
        # Polling titres [!] en parallèle
        threading.Thread(target=self._title_loop, daemon=True).start()

    def stop(self):
        self._running = False



    def _process_notif(self, raw):
        """Parse la notification et extrait pseudo + type (combat, echange, mp...)."""
        if not raw: return
        try:
            from tabs.accounts.toast_reader import _categorize
        except Exception:
            _categorize = lambda t: ("combat", "⚔️")

        text = ""
        try:
            import plistlib
            data  = raw if isinstance(raw, bytes) else bytes(raw)
            plist = plistlib.loads(data)
            for key in ["body", "title", "subtitle", "req", "content"]:
                val = plist.get(key, "")
                if isinstance(val, str) and val:
                    text += " " + val
        except Exception:
            pass

        ntype, _ = _categorize(text.strip()) if text.strip() else ("combat", "⚔️")
        if ntype == "other": ntype = "combat"

        m      = _PTN_SESSION.search(text)
        pseudo = m.group(1).strip() if m else ""
        if not pseudo:
            wins   = list_windows()
            pseudo = wins[0].pseudo if wins else ""

        if pseudo:
            self._cb(pseudo, ntype)
        elif not text.strip():
            wins = list_windows()
            if wins: self._cb(wins[0].pseudo, ntype)

    # ── Boucle polling titres [!] ─────────────────────────────────
    def _title_loop(self):
        while self._running:
            try:
                self._check_titles()
            except Exception:
                pass
            time.sleep(0.20)

    def _check_titles(self):
        alerted: set[int] = set()
        for w in _quartz_wins():
            title = (w.get("kCGWindowName") or "").strip()
            wid   = w.get("kCGWindowNumber", 0)
            if not _PTN_ALERT.match(title):
                self._seen_titles.discard(wid); continue
            alerted.add(wid)
            if wid in self._seen_titles: continue
            self._seen_titles.add(wid)
            clean  = re.sub(r"^\[!\]\s*", "", title)
            m      = _PTN_SESSION.match(clean)
            pseudo = m.group(1).strip() if m else clean.strip()
            if pseudo: self._cb(pseudo, "combat")
        self._seen_titles &= alerted# ─── Interception notifications macOS via Darwin + NSDistributed ─────
def _start_notification_listeners(callback: Callable):
    """
    Intercepte les notifications macOS de Dofus via deux mécanismes :
    1. NSDistributedNotificationCenter (notifications inter-processus)
    2. Darwin notify center (notifications système bas niveau)
    Sans base de données, sans OCR — équivalent direct de winsdk Windows.
    """
    import threading

    def _start_ocr_watcher():
        try:
            import Quartz
            from PIL import Image as _PILImage
            import pytesseract

            seen_texts: set[str] = set()
            last_text = ""

            while True:
                try:
                    screen = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
                    sw = int(screen.size.width)
                    # Capture Quartz — capture les bannières système
                    region = Quartz.CGRectMake(sw - 430, 0, 430, 200)
                    cg_img = Quartz.CGWindowListCreateImage(
                        region,
                        Quartz.kCGWindowListOptionOnScreenOnly,
                        Quartz.kCGNullWindowID,
                        Quartz.kCGWindowImageDefault)
                    if cg_img:
                        w_px = Quartz.CGImageGetWidth(cg_img)
                        h_px = Quartz.CGImageGetHeight(cg_img)
                        prov = Quartz.CGImageGetDataProvider(cg_img)
                        raw  = Quartz.CGDataProviderCopyData(prov)
                        img  = _PILImage.frombytes("RGBA", (w_px, h_px), bytes(raw))
                    else:
                        from PIL import ImageGrab
                        img = ImageGrab.grab(bbox=(sw-430, 0, sw, 200))

                    text = pytesseract.image_to_string(img, config="--psm 6").strip()

                    if text and text != last_text and len(text) > 3:
                        last_text = text
                        print(f"[Mac OCR scan] {repr(text[:60])}")
                        tl = text.lower()
                        if any(kw in tl for kw in
                               ["dofus","jouer","play","trade","échange",
                                "exchange","groupe","group","message","défi",
                                "challenge","craft","pvp","percepteur","turn",
                                "arc","pro","vous","your","st-"]):
                            if text not in seen_texts:
                                seen_texts.add(text)
                                if len(seen_texts) > 15: seen_texts.pop()
                                print(f"[Mac OCR MATCH] {text[:80]}")
                                _dispatch_notif(text, callback)
                except Exception:
                    pass
                time.sleep(0.4)
        except Exception as e:
            print(f"[Mac OCR] Erreur: {e}")

    threading.Thread(target=_start_ocr_watcher, daemon=True).start()


def _dispatch_notif(text: str, callback: Callable):
    """Analyse le texte et identifie quel perso a reçu la notification."""
    _DOFUS_KW = ["dofus","jouer","turn to play","trade","échange","exchange",
                 "groupe","group","message","défi","challenge",
                 "craft","pvp","percepteur","turn","play"]
    text_low = text.lower()
    if not any(kw in text_low for kw in _DOFUS_KW):
        return
    try:
        from tabs.accounts.toast_reader import _categorize
        ntype, _ = _categorize(text)
        if ntype == "other": ntype = "combat"
    except Exception:
        ntype = "combat"

    wins = list_windows()
    if not wins: return

    # Chercher quel perso correspond à la notification
    # La notification contient le pseudo : "St-Arc 's turn" ou "St-Arc propose..."
    pseudo = ""

    # 1. Essayer de matcher directement avec les pseudos connus
    for win in wins:
        if win.pseudo.lower() in text_low:
            pseudo = win.pseudo
            break

    # 2. Essayer d'extraire depuis le titre de la notif (format "Pseudo - Dofus")
    if not pseudo:
        m = _PTN_SESSION.search(text)
        if m:
            found = m.group(1).strip()
            # Vérifier si ce pseudo correspond à une fenêtre connue
            for win in wins:
                if win.pseudo.lower() == found.lower():
                    pseudo = win.pseudo
                    break
            if not pseudo:
                pseudo = found  # utiliser quand même

    # 3. Fallback : première fenêtre
    if not pseudo:
        pseudo = wins[0].pseudo

    print(f"[Mac Notif] {ntype}: {pseudo} | {text[:60]}")
    callback(pseudo, ntype)


# ─── AlertWatcher — double mécanisme : notifications + polling titres ─
class AlertWatcher:
    """
    Autofocus Mac via deux mécanismes combinés :
    1. Surveillance base de données notifications macOS (équivalent Toast Windows)
    2. Polling titres de fenêtres [!] toutes les 200ms (fallback)
    """

    def __init__(self, callback: Callable[[str, str], None]):
        self._cb      = callback
        self._running = False
        self._seen_titles: set[int] = set()

    def start(self):
        self._running = True
        # Interception directe des notifications macOS (équivalent winsdk Windows)
        _start_notification_listeners(self._cb)
        # Polling titres [!] en parallèle
        threading.Thread(target=self._title_loop, daemon=True).start()

    def stop(self):
        self._running = False



    def _process_notif(self, raw):
        """Parse la notification et extrait pseudo + type (combat, echange, mp...)."""
        if not raw: return
        try:
            from tabs.accounts.toast_reader import _categorize
        except Exception:
            _categorize = lambda t: ("combat", "⚔️")

        text = ""
        try:
            import plistlib
            data  = raw if isinstance(raw, bytes) else bytes(raw)
            plist = plistlib.loads(data)
            for key in ["body", "title", "subtitle", "req", "content"]:
                val = plist.get(key, "")
                if isinstance(val, str) and val:
                    text += " " + val
        except Exception:
            pass

        ntype, _ = _categorize(text.strip()) if text.strip() else ("combat", "⚔️")
        if ntype == "other": ntype = "combat"

        m      = _PTN_SESSION.search(text)
        pseudo = m.group(1).strip() if m else ""
        if not pseudo:
            wins   = list_windows()
            pseudo = wins[0].pseudo if wins else ""

        if pseudo:
            self._cb(pseudo, ntype)
        elif not text.strip():
            wins = list_windows()
            if wins: self._cb(wins[0].pseudo, ntype)

    # ── Boucle polling titres [!] ─────────────────────────────────
    def _title_loop(self):
        while self._running:
            try:
                self._check_titles()
            except Exception:
                pass
            time.sleep(0.20)

    def _check_titles(self):
        alerted: set[int] = set()
        for w in _quartz_wins():
            title = (w.get("kCGWindowName") or "").strip()
            wid   = w.get("kCGWindowNumber", 0)
            if not _PTN_ALERT.match(title):
                self._seen_titles.discard(wid); continue
            alerted.add(wid)
            if wid in self._seen_titles: continue
            self._seen_titles.add(wid)
            clean  = re.sub(r"^\[!\]\s*", "", title)
            m      = _PTN_SESSION.match(clean)
            pseudo = m.group(1).strip() if m else clean.strip()
            if pseudo: self._cb(pseudo, "combat")
        self._seen_titles &= alerted
