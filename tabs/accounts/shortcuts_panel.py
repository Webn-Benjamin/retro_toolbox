"""shortcuts_panel.py — Configuration des raccourcis clavier globaux."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QKeySequence
import theme as T
from tabs.accounts.hotkey_manager import HotkeyRegistry

# Définition des raccourcis disponibles
_SHORTCUTS = [
    ("next",        "▶",  "Personnage suivant",      "ctrl+right"),
    ("prev",        "◀",  "Personnage précédent",    "ctrl+left"),
    ("main",        "★",  "Revenir au principal",    "ctrl+home"),
    ("back",        "↩",  "Fenêtre précédente",      ""),
    ("ctrl_shift",  "⇧",  "Ctrl+Shift simulé",       ""),
    ("move_mode",   "👟", "Mode Déplacement",         ""),
]

_KEY_NAMES = {
    Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right",
    Qt.Key.Key_Up:   "up",   Qt.Key.Key_Down:  "down",
    Qt.Key.Key_Home: "home", Qt.Key.Key_End:   "end",
    Qt.Key.Key_PageUp: "page up", Qt.Key.Key_PageDown: "page down",
    Qt.Key.Key_Insert: "insert", Qt.Key.Key_Delete: "delete",
    Qt.Key.Key_Escape: "escape", Qt.Key.Key_Tab: "tab",
    **{getattr(Qt.Key, f"Key_F{i}", None): f"f{i}" for i in range(1, 13)},
}


def _lbl(txt, color=None, sz="9pt", bold=False, italic=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{sz};"
    if color:  ss += f"color:{color};"
    if bold:   ss += "font-weight:bold;"
    if italic: ss += "font-style:italic;"
    l.setStyleSheet(ss)
    return l


class ShortcutsPanel(QWidget):

    def __init__(self, cfg: dict, registry: HotkeyRegistry, on_save,
                 on_next, on_prev, on_main, on_back, on_ctrl_shift,
                 parent=None):
        super().__init__(parent)
        self._cfg      = cfg
        self._reg      = registry
        self._on_save  = on_save
        self._actions  = {
            "next": on_next, "prev": on_prev, "main": on_main,
            "back": on_back, "ctrl_shift": on_ctrl_shift,
        }
        self._inputs:  dict[str, QLineEdit] = {}
        self._badges:  dict[str, QLabel]    = {}
        self._capture: QObject | None       = None
        self._build()
        self._load_and_apply()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(10, 6, 10, 6)
        lbl_h = _lbl("Raccourcis clavier", "white", "9pt", bold=True)
        lbl_h.setStyleSheet("background:transparent;color:white;font-size:9pt;font-weight:bold;")
        hl.addWidget(lbl_h)
        root.addWidget(hdr)

        # Notice
        notice = QLabel("Actifs même si l'app est en arrière-plan.")
        notice.setStyleSheet(
            f"background:{T.SURFACE2};color:{T.HINT};font-size:9pt;"
            f"font-style:italic;padding:5px 10px;"
            f"border-bottom:1px solid {T.BORDER};")
        root.addWidget(notice)

        # Chaque raccourci
        saved = self._cfg.get("shortcuts", {})
        for key, icon, label, default in _SHORTCUTS:
            current = saved.get(key) or default
            root.addWidget(self._make_row(key, icon, label, current))

        # Indicateur Ctrl+Shift
        root.addWidget(self._make_cs_bar())
        root.addStretch()

    def _make_row(self, key: str, icon: str, label: str, current: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(5)

        # Titre + badge statut
        r1 = QHBoxLayout(); r1.setSpacing(6)
        r1.addWidget(_lbl(f"{icon}  {label}", T.TEXT, "9pt", bold=True))
        badge = _lbl("", T.GREEN, "9pt")
        self._badges[key] = badge
        r1.addWidget(badge); r1.addStretch()
        lay.addLayout(r1)

        # Champ + bouton effacer
        r2 = QHBoxLayout(); r2.setSpacing(5)
        inp = QLineEdit(current or "Aucun")
        inp.setFixedHeight(28)
        inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inp.setReadOnly(True)
        inp.setStyleSheet(
            f"QLineEdit{{background:{T.BG_DARK};"
            f"color:{T.ORANGE if current else T.HINT};"
            f"border:none;padding:4px;font-family:Consolas;font-size:9pt;}}")
        inp.mousePressEvent = lambda e, k=key, i=inp: self._begin_capture(i, k)
        inp.setCursor(Qt.CursorShape.PointingHandCursor)
        self._inputs[key] = inp
        r2.addWidget(inp, 1)

        btn_clr = QPushButton("✕")
        btn_clr.setFixedSize(28, 28)
        btn_clr.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:1px solid {T.BORDER};"
            f"border-radius:6px;font-size:9pt;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        btn_clr.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clr.clicked.connect(lambda _, k=key: self._clear(k))
        r2.addWidget(btn_clr)
        lay.addLayout(r2)
        return card

    def _make_cs_bar(self) -> QFrame:
        bar = QFrame()
        bar.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-top:1px solid {T.BORDER};}}")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 8, 10, 8); bl.setSpacing(8)
        self._cs_indicator = _lbl("⇧  Ctrl+Shift : OFF", T.HINT, "9pt", bold=True)
        bl.addWidget(self._cs_indicator, 1)
        btn = QPushButton("Activer / Désactiver")
        btn.setFixedHeight(26)
        btn.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};border:none;"
            f"padding:3px 10px;font-size:9pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.ORANGE};}}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._actions["ctrl_shift"])
        bl.addWidget(btn)
        return bar

    # ── Capture clavier ────────────────────────────────────

    def _begin_capture(self, inp: QLineEdit, key: str):
        inp.setText("Appuyez sur un raccourci…")
        inp.setStyleSheet(inp.styleSheet().replace(T.ORANGE, T.HINT))
        if self._capture:
            inp.removeEventFilter(self._capture)

        class _Cap(QObject):
            def __init__(self_, fn):
                super().__init__()
                self_._fn = fn
            def eventFilter(self_, obj, evt):
                if evt.type() == QEvent.Type.KeyPress:
                    self_._fn(evt)
                    return True
                return False

        def on_key(event):
            MODS = {Qt.Key.Key_Control, Qt.Key.Key_Shift,
                    Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_CapsLock}
            k = event.key()
            if k in MODS:
                return
            parts = []
            mod = event.modifiers()
            if mod & Qt.KeyboardModifier.ControlModifier: parts.append("ctrl")
            if mod & Qt.KeyboardModifier.ShiftModifier:   parts.append("shift")
            if mod & Qt.KeyboardModifier.AltModifier:     parts.append("alt")
            name = _KEY_NAMES.get(k) or QKeySequence(k).toString().lower()
            if not name:
                return
            combo = "+".join(parts + [name])
            inp.setText(combo)
            inp.setStyleSheet(inp.styleSheet().replace(T.HINT, T.ORANGE))
            inp.removeEventFilter(self._capture)
            self._capture = None
            self.window().setFocus()
            self._apply(key, combo)

        self._capture = _Cap(on_key)
        inp.installEventFilter(self._capture)

    # ── Application ────────────────────────────────────────

    def _apply(self, key: str, combo: str):
        self._cfg.setdefault("shortcuts", {})[key] = combo
        ok = self._reg.add(key, combo, self._actions[key])
        self._badges[key].setText("✅ Actif" if ok else "❌ Invalide")
        self._on_save()

    def _clear(self, key: str):
        self._reg.remove(key)
        self._cfg.setdefault("shortcuts", {})[key] = ""
        inp = self._inputs[key]
        inp.setText("Aucun")
        inp.setStyleSheet(inp.styleSheet().replace(T.ORANGE, T.HINT))
        self._badges[key].setText("")
        self._on_save()

    def _load_and_apply(self):
        saved = self._cfg.get("shortcuts", {})
        for key, _, _, default in _SHORTCUTS:
            combo = saved.get(key) or default
            if combo and key not in ("ctrl_shift",):
                ok = self._reg.add(key, combo, self._actions[key])
                if key in self._badges:
                    self._badges[key].setText("✅ Actif" if ok else "❌")

    def update_cs_indicator(self, active: bool):
        txt   = "⇧  Ctrl+Shift : ON " if active else "⇧  Ctrl+Shift : OFF"
        color = T.ORANGE if active else T.HINT
        self._cs_indicator.setText(txt)
        self._cs_indicator.setStyleSheet(
            f"background:transparent;font-size:9pt;font-weight:bold;color:{color};")
