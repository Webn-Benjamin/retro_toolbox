"""farmsadi_panel.py — Mode Farm Sadi : ignore les tours d'autofocus combat
pour les Sadidas pendant N tours configurables."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QSpinBox,
    QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QKeySequence
import theme as T
from tabs.accounts.hotkey_manager import FarmSadiManager

_KEY_NAMES = {
    Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right",
    Qt.Key.Key_Up: "up",     Qt.Key.Key_Down:  "down",
    Qt.Key.Key_Home: "home", Qt.Key.Key_End:   "end",
    **{getattr(Qt.Key, f"Key_F{i}", None): f"f{i}" for i in range(1, 13)},
}


def _lbl(txt, color=None, sz="8.5pt", bold=False, italic=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{sz};"
    if color:  ss += f"color:{color};"
    if bold:   ss += "font-weight:bold;"
    if italic: ss += "font-style:italic;"
    l.setStyleSheet(ss)
    return l


class FarmSadiPanel(QWidget):
    """
    Panneau de configuration du mode Farm Sadi.
    Affiché comme 4ème sous-onglet dans AccountsTab.
    """

    def __init__(self, cfg: dict, mgr: FarmSadiManager,
                 on_save, on_register_shortcut, parent=None):
        super().__init__(parent)
        self._cfg          = cfg
        self._mgr          = mgr
        self._on_save      = on_save
        self._reg_shortcut = on_register_shortcut
        self._char_rows:   list[QWidget] = []
        self._capture:     QObject | None = None
        self._build()

    # ── Build ──────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{T.BG_DARK};border-bottom:1px solid {T.BORDER};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(10, 6, 10, 6); hl.setSpacing(6)
        icon = QLabel("🌿"); icon.setStyleSheet("background:transparent;font-size:12pt;")
        hl.addWidget(icon)
        hl.addWidget(_lbl("Mode Farm Sadi", T.TEXT, "9pt", bold=True), 1)

        # Indicateur actif
        self._active_badge = QLabel()
        self._active_badge.setFixedHeight(20)
        self._active_badge.setStyleSheet(
            f"background:transparent;font-size:8pt;font-weight:bold;")
        hl.addWidget(self._active_badge)
        root.addWidget(hdr)

        # Description
        desc = QLabel(
            "Ignore automatiquement l'autofocus combat de tes Sadidas\n"
            "pendant N tours — utile quand ils farm avec leurs poupées.")
        desc.setStyleSheet(
            f"background:{T.SURFACE2};color:{T.HINT};font-size:9pt;"
            f"font-style:italic;padding:8px 10px;"
            f"border-bottom:1px solid {T.BORDER};")
        desc.setWordWrap(True)
        root.addWidget(desc)

        # Scroll
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setStyleSheet(
            f"QScrollArea{{background:{T.BG};border:none;}}"
            f"QScrollBar:vertical{{background:{T.BG_DARK};width:4px;}}"
            f"QScrollBar::handle:vertical{{background:{T.BORDER2};min-height:20px;}}"
            f"QScrollBar::handle:vertical:hover{{background:{T.ORANGE};}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        inner = QWidget(); inner.setStyleSheet(f"background:{T.BG};")
        self._lay = QVBoxLayout(inner)
        self._lay.setContentsMargins(0, 0, 0, 8); self._lay.setSpacing(0)
        sc.setWidget(inner)
        root.addWidget(sc)

        self._rebuild()

    def _rebuild(self):
        # Vider
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        fs = self._cfg.get("farmsadi", {})
        enabled  = fs.get("enabled", False)
        turns    = fs.get("turns", 3)
        shortcut = fs.get("shortcut", "")
        sadis    = set(fs.get("sadis", []))

        # ── Section Activation ─────────────────────────────
        self._lay.addWidget(self._section("Activation"))

        toggle_row = self._toggle_row(
            "enabled", "🌿  Activer le mode Farm Sadi", enabled)
        self._lay.addWidget(toggle_row)

        # ── Section Raccourci ──────────────────────────────
        self._lay.addWidget(self._section("Raccourci clavier"))

        sc_card = QFrame()
        sc_card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}")
        scl = QVBoxLayout(sc_card)
        scl.setContentsMargins(10, 8, 10, 8); scl.setSpacing(6)

        scl.addWidget(_lbl(
            "Appuie sur ce raccourci quand c'est au tour de ton Sadida\n"
            "pour démarrer le compteur.", T.HINT, "9pt", italic=True))
        scl.addWidget(_lbl("Le raccourci fonctionne uniquement si Dofus est actif.", T.HINT, "8.5pt", italic=True))

        sc_row = QHBoxLayout(); sc_row.setSpacing(5)
        self._sc_inp = QLineEdit(shortcut or "Aucun")
        self._sc_inp.setFixedHeight(28)
        self._sc_inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sc_inp.setReadOnly(True)
        self._sc_inp.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sc_inp.setStyleSheet(
            f"QLineEdit{{background:{T.BG_DARK};"
            f"color:{T.ORANGE if shortcut else T.HINT};"
            f"border:none;padding:4px;font-family:Consolas;font-size:9pt;}}")
        self._sc_inp.mousePressEvent = lambda e: self._begin_capture(self._sc_inp)
        sc_row.addWidget(self._sc_inp, 1)

        btn_clr = QPushButton("✕")
        btn_clr.setFixedSize(28, 28)
        btn_clr.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:none;font-size:9pt;}}"
            f"QPushButton:hover{{color:{T.RED};}}")
        btn_clr.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clr.clicked.connect(self._clear_shortcut)
        sc_row.addWidget(btn_clr)
        scl.addLayout(sc_row)
        self._lay.addWidget(sc_card)

        # ── Section Nombre de tours ────────────────────────
        self._lay.addWidget(self._section("Nombre de tours à ignorer"))

        turns_card = QFrame()
        turns_card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}")
        tl = QHBoxLayout(turns_card)
        tl.setContentsMargins(12, 10, 12, 10); tl.setSpacing(10)
        tl.addWidget(_lbl("Ignorer", T.TEXT, "8.5pt"), 1)

        spin = QSpinBox()
        spin.setRange(1, 20)
        spin.setValue(turns)
        spin.setFixedWidth(60)
        spin.setFixedHeight(28)
        spin.setStyleSheet(
            f"QSpinBox{{background:{T.BG_DARK};color:{T.ORANGE};"
            f"border:none;padding:3px 6px;font-size:9pt;font-weight:bold;}}"
            f"QSpinBox::up-button,QSpinBox::down-button{{"
            f"background:{T.BG_DARK};border:none;width:14px;}}")
        spin.valueChanged.connect(self._on_turns_change)
        tl.addWidget(spin)
        tl.addWidget(_lbl("tours de combat", T.TEXT, "8.5pt"))
        self._lay.addWidget(turns_card)

        # ── Section Personnages Sadida ─────────────────────
        self._lay.addWidget(self._section("Personnages Sadida"))

        info_card = QFrame()
        info_card.setStyleSheet(f"background:{T.SURFACE};")
        il = QVBoxLayout(info_card)
        il.setContentsMargins(10, 6, 10, 6); il.setSpacing(4)
        il.addWidget(_lbl(
            "Coche les personnages qui jouent en mode poupées.",
            T.HINT, "9pt", italic=True))
        self._lay.addWidget(info_card)

        # Liste des fenêtres Dofus détectées
        from tabs.accounts.window_manager import scan_windows
        windows = scan_windows()
        if not windows:
            no = _lbl("Aucune fenêtre Dofus détectée. Ouvre Dofus et relance.",
                      T.HINT, "9.5pt", italic=True)
            no.setContentsMargins(12, 8, 12, 8)
            self._lay.addWidget(no)
        else:
            for win in windows:
                row = self._char_toggle(win.pseudo, win.pseudo in sadis)
                self._lay.addWidget(row)

        # Bouton refresh
        btn_r = QPushButton("🔄 Actualiser la liste")
        btn_r.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:none;"
            f"padding:6px 12px;font-size:8pt;}}"
            f"QPushButton:hover{{color:{T.ORANGE};}}")
        btn_r.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_r.clicked.connect(self._rebuild)
        self._lay.addWidget(btn_r)

        # ── Contrôles manuels ─────────────────────────────
        self._lay.addWidget(self._section("Contrôles"))

        ctrl_card = QFrame()
        ctrl_card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}")
        cl = QHBoxLayout(ctrl_card)
        cl.setContentsMargins(10, 8, 10, 8); cl.setSpacing(6)

        btn_cancel = QPushButton("✕ Annuler tous les compteurs")
        btn_cancel.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};border:none;"
            f"padding:5px 10px;font-size:9pt;font-weight:bold;}}"
            f"QPushButton:hover{{color:{T.RED};}}")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self._cancel_all)
        cl.addWidget(btn_cancel, 1)

        self._status_lbl = _lbl("", T.GREEN, "9pt")
        cl.addWidget(self._status_lbl)
        self._lay.addWidget(ctrl_card)
        self._lay.addStretch()

        self._update_badge()

    # ── Helpers ────────────────────────────────────────────

    def _section(self, title: str) -> QLabel:
        l = QLabel(f"  {title}")
        l.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.HINT};"
            f"font-size:8pt;font-weight:bold;letter-spacing:1px;"
            f"padding:4px 0;border-top:1px solid {T.BORDER};"
            f"border-bottom:1px solid {T.BORDER};")
        l.setFixedHeight(24)
        return l

    def _toggle_row(self, key: str, label: str, checked: bool) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}"
            f"QFrame:hover{{background:{T.SURFACE2};}}")
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setFixedHeight(40)
        rl = QHBoxLayout(row); rl.setContentsMargins(12, 0, 12, 0); rl.setSpacing(10)
        lbl = _lbl(label, T.TEXT, "8.5pt"); rl.addWidget(lbl, 1)
        sw  = QLabel("ON  ●" if checked else "●  OFF")
        sw.setFixedWidth(54); sw.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sw.setStyleSheet(
            f"background:{T.GREEN if checked else T.BG_DARK};"
            f"color:{'white' if checked else T.HINT};"
            f"font-size:9pt;font-weight:bold;padding:2px;")
        rl.addWidget(sw)
        state = [checked]
        def _flip(e=None):
            state[0] = not state[0]
            v = state[0]
            sw.setText("ON  ●" if v else "●  OFF")
            sw.setStyleSheet(
                f"background:{T.GREEN if v else T.BG_DARK};"
                f"color:{'white' if v else T.HINT};"
                f"font-size:9pt;font-weight:bold;padding:2px;")
            self._cfg.setdefault("farmsadi", {})[key] = v
            self._on_save()
        for w in (row, lbl, sw): w.mousePressEvent = _flip
        return row

    def _char_toggle(self, pseudo: str, checked: bool) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}"
            f"QFrame:hover{{background:{T.SURFACE2};}}")
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setFixedHeight(40)
        rl = QHBoxLayout(row); rl.setContentsMargins(12, 0, 12, 0); rl.setSpacing(10)

        cb = QLabel("🌿 ☑" if checked else "🌿 ☐")
        cb.setFixedWidth(36)
        cb.setStyleSheet(
            f"background:transparent;font-size:12pt;"
            f"color:{T.GREEN if checked else T.HINT};")

        lbl = _lbl(pseudo, T.TEXT, "9pt", bold=True)
        rl.addWidget(cb); rl.addWidget(lbl, 1)

        # Compteur restant
        rem = self._mgr.remaining(pseudo)
        self._ctr = _lbl(f"⏳ {rem} tours restants" if rem else "", T.ORANGE, "9pt")
        rl.addWidget(self._ctr)

        state = [checked]
        def _flip(e=None):
            state[0] = not state[0]
            v = state[0]
            cb.setText("🌿 ☑" if v else "🌿 ☐")
            cb.setStyleSheet(
                f"background:transparent;font-size:12pt;"
                f"color:{T.GREEN if v else T.HINT};")
            sadis = set(self._cfg.get("farmsadi", {}).get("sadis", []))
            if v: sadis.add(pseudo)
            else: sadis.discard(pseudo); self._mgr.cancel(pseudo)
            self._cfg.setdefault("farmsadi", {})["sadis"] = list(sadis)
            self._mgr.set_sadis(sadis)
            self._on_save()
        for w in (row, cb, lbl): w.mousePressEvent = _flip
        return row

    # ── Capture raccourci ──────────────────────────────────

    def _begin_capture(self, inp: QLineEdit):
        inp.setText("Appuyez sur un raccourci…")
        inp.setStyleSheet(inp.styleSheet().replace(T.ORANGE, T.HINT))
        if self._capture:
            inp.removeEventFilter(self._capture)

        class _Cap(QObject):
            def __init__(self_, fn): super().__init__(); self_._fn = fn
            def eventFilter(self_, obj, evt):
                if evt.type() == QEvent.Type.KeyPress:
                    self_._fn(evt); return True
                return False

        def on_key(event):
            MODS = {Qt.Key.Key_Control, Qt.Key.Key_Shift,
                    Qt.Key.Key_Alt, Qt.Key.Key_Meta}
            k = event.key()
            if k in MODS: return
            parts = []
            mod = event.modifiers()
            if mod & Qt.KeyboardModifier.ControlModifier: parts.append("ctrl")
            if mod & Qt.KeyboardModifier.ShiftModifier:   parts.append("shift")
            if mod & Qt.KeyboardModifier.AltModifier:     parts.append("alt")
            name = _KEY_NAMES.get(k) or QKeySequence(k).toString().lower()
            if not name: return
            combo = "+".join(parts + [name])
            inp.setText(combo)
            inp.setStyleSheet(inp.styleSheet().replace(T.HINT, T.ORANGE))
            inp.removeEventFilter(self._capture)
            self._capture = None
            self.window().setFocus()
            self._cfg.setdefault("farmsadi", {})["shortcut"] = combo
            self._on_save()
            self._reg_shortcut(combo)

        self._capture = _Cap(on_key)
        inp.installEventFilter(self._capture)

    def _clear_shortcut(self):
        self._cfg.setdefault("farmsadi", {})["shortcut"] = ""
        self._sc_inp.setText("Aucun")
        self._sc_inp.setStyleSheet(
            self._sc_inp.styleSheet().replace(T.ORANGE, T.HINT))
        self._reg_shortcut("")
        self._on_save()

    # ── Callbacks ──────────────────────────────────────────

    def _on_turns_change(self, val: int):
        self._mgr.turns = val
        self._cfg.setdefault("farmsadi", {})["turns"] = val
        self._on_save()

    def _cancel_all(self):
        self._mgr.cancel_all()
        self._status_lbl.setText("✅ Compteurs annulés")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._status_lbl.setText(""))
        self._update_badge()

    def _update_badge(self):
        if self._mgr.is_active():
            self._active_badge.setText("● Actif")
            self._active_badge.setStyleSheet(
                f"background:transparent;color:{T.GREEN};"
                f"font-size:8pt;font-weight:bold;")
        else:
            self._active_badge.setText("")

    def refresh_counts(self):
        """Appelé après chaque check() pour mettre à jour l'affichage."""
        self._update_badge()
