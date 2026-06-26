"""tabs/xp_metier_tab.py — Calculateur d'XP métier Dofus Rétro."""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QScrollArea, QSpinBox, QSlider
)
from PySide6.QtCore import Qt
import theme

T = theme

# ─── Données XP métier Dofus Rétro ────────────────────────────────────
# (niveau_debut, niveau_fin, xp_totale_du_palier, cases_requises)
PALIERS_XP = [
    (1,   10,     1_911,    2),
    (10,  20,     6_186,    3),
    (20,  30,    11_145,    4),
    (30,  40,    17_399,    4),
    (40,  50,    25_850,    5),
    (50,  60,    37_930,    5),
    (60,  70,    56_060,    6),
    (70,  80,    84_483,    6),
    (80,  90,   130_906,    7),
    (90,  100,  209_817,    7),
    (100, 110,  315_000,    8),
    (110, 120,  450_000,    8),
    (120, 130,  620_000,    9),
    (130, 140,  830_000,    9),
    (140, 150, 1_100_000,  10),
    (150, 160, 1_420_000,  10),
    (160, 170, 1_800_000,  11),
    (170, 180, 2_250_000,  11),
    (180, 190, 2_800_000,  12),
    (190, 200, 3_450_000,  12),
]

# XP par craft selon le nombre de cases (mult=1)
XP_CRAFT_TABLE = {
    2: 10, 3: 25, 4: 50, 5: 100, 6: 250, 7: 500,
    8: 1_000, 9: 2_000, 10: 4_000, 11: 8_000, 12: 16_000,
}


def _xp_min_for_level(level: int) -> int:
    """XP totale cumulée minimale pour atteindre ce niveau."""
    if level <= 1:
        return 0
    xp = 0
    for (lvl_start, lvl_end, xp_palier, _) in PALIERS_XP:
        if lvl_start >= level:
            break
        if lvl_end <= level:
            xp += xp_palier
        else:
            nb = lvl_end - lvl_start
            xp += round(xp_palier * (level - lvl_start) / nb)
            break
    return xp


# ─── Helpers UI ───────────────────────────────────────────────────────

def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER};max-height:1px;")
    return f

def _lbl(txt, color=None, size="9pt", bold=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{size};"
    if color: ss += f"color:{color};"
    if bold:  ss += "font-weight:bold;"
    l.setStyleSheet(ss)
    return l

def _card():
    f = QFrame()
    f.setStyleSheet(
        f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:10px;}}"
        f"QLabel{{background:transparent;border:none;}}")
    return f

def _spinbox(max_v=200, val=None):
    s = QSpinBox()
    s.setRange(0, max_v)
    s.setSpecialValueText(" ")
    s.setValue(val if val is not None else 0)
    s.setFixedHeight(32)
    s.setStyleSheet(
        f"QSpinBox{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:6px;padding:2px 8px;color:{T.TEXT};font-size:10pt;}}"
        f"QSpinBox:focus{{border:1px solid {T.ORANGE};}}"
        f"QSpinBox::up-button{{width:0;border:none;}}"
        f"QSpinBox::down-button{{width:0;border:none;}}")
    return s

def _fmt(v):
    return f"{int(v):,}".replace(",", ".")


class XpMetierTab(QWidget):
    """Calculateur d'XP métier. on_back = callback retour au menu Calculateurs."""

    def __init__(self, on_back=None, parent=None):
        super().__init__(parent)
        self._on_back = on_back
        self._mult_steps = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        self._build()

    # ── Construction UI ──────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 12, 0)
        hl.setSpacing(8)
        if self._on_back:
            back = QPushButton("‹  Retour")
            back.setFixedHeight(28)
            back.setCursor(Qt.CursorShape.PointingHandCursor)
            back.setStyleSheet(
                "QPushButton{background:rgba(255,255,255,40);color:white;"
                "border:1px solid rgba(255,255,255,90);border-radius:6px;"
                "font-size:8pt;font-weight:bold;padding:0 10px;}"
                "QPushButton:hover{background:rgba(255,255,255,70);}")
            back.clicked.connect(self._on_back)
            hl.addWidget(back)
        t = QLabel("🎓  Calculateur XP Métier")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t)
        hl.addStretch()
        lay.addWidget(hdr)

        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea{{background:{T.BG};}}")
        container = QWidget()
        container.setStyleSheet(f"background:{T.BG};")
        cl = QVBoxLayout(container)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(10)

        # ── Carte saisie ─────────────────────────────────────────────
        inp_card = _card()
        il = QVBoxLayout(inp_card)
        il.setContentsMargins(14, 12, 14, 14)
        il.setSpacing(8)

        il.addWidget(_lbl("Niveau actuel", T.HINT, "8pt"))
        self._lvl_start = _spinbox(199)
        self._lvl_start.valueChanged.connect(self._calculate)
        il.addWidget(self._lvl_start)

        il.addWidget(_lbl("XP actuelle (optionnel)", T.HINT, "8pt"))
        self._xp_current = QLineEdit()
        self._xp_current.setPlaceholderText("XP actuelle (optionnel)")
        self._xp_current.setFixedHeight(32)
        self._xp_current.setStyleSheet(
            f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:6px;padding:2px 10px;color:{T.TEXT};font-size:10pt;}}"
            f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
        self._xp_current.textChanged.connect(self._calculate)
        il.addWidget(self._xp_current)

        hint = QLabel("Laissez vide pour utiliser l'XP minimale du niveau en cours.")
        hint.setStyleSheet(f"color:{T.HINT};font-size:7pt;background:transparent;")
        hint.setWordWrap(True)
        il.addWidget(hint)

        il.addWidget(_sep())

        il.addWidget(_lbl("Niveau souhaité", T.HINT, "8pt"))
        self._lvl_target = _spinbox(200)
        self._lvl_target.valueChanged.connect(self._calculate)
        il.addWidget(self._lvl_target)

        il.addWidget(_sep())

        # Multiplicateur — réglette
        mult_row = QHBoxLayout()
        mult_row.addWidget(_lbl("Multiplicateur XP", T.HINT, "8pt"))
        mult_row.addStretch()
        self._mult_val = QLabel("x1")
        self._mult_val.setFixedWidth(40)
        self._mult_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mult_val.setStyleSheet(
            f"font-size:9pt;font-weight:bold;color:{T.ORANGE};"
            f"background:{T.BG_DARK};border-radius:6px;padding:2px 4px;")
        mult_row.addWidget(self._mult_val)
        il.addLayout(mult_row)

        self._mult_sl = QSlider(Qt.Orientation.Horizontal)
        self._mult_sl.setRange(0, len(self._mult_steps) - 1)
        self._mult_sl.setValue(0)
        self._mult_sl.setStyleSheet(
            f"QSlider::groove:horizontal{{background:{T.BG_DARK};height:4px;border-radius:2px;}}"
            f"QSlider::handle:horizontal{{background:white;border:2px solid {T.ORANGE};"
            f"width:14px;height:14px;border-radius:7px;margin:-5px 0;}}"
            f"QSlider::sub-page:horizontal{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border-radius:2px;}}")
        self._mult_sl.valueChanged.connect(self._on_mult)
        il.addWidget(self._mult_sl)

        marks = QHBoxLayout()
        marks.addWidget(_lbl("x1", T.HINT, "7pt"))
        marks.addStretch()
        marks.addWidget(_lbl("x4", T.HINT, "7pt"))
        il.addLayout(marks)

        cl.addWidget(inp_card)

        # ── Carte résultat ───────────────────────────────────────────
        self._res_card = _card()
        self._res_card.setVisible(False)
        rl = QVBoxLayout(self._res_card)
        rl.setContentsMargins(14, 12, 14, 14)
        rl.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)
        xp_box = QFrame()
        xp_box.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border-radius:8px;border:none;}}"
            f"QLabel{{background:transparent;border:none;}}")
        xb = QVBoxLayout(xp_box)
        xb.setContentsMargins(10, 8, 10, 8)
        xb.setSpacing(2)
        xb.addWidget(_lbl("Gain total", T.HINT, "8pt"))
        self._lbl_xp = _lbl("—", T.GREEN, "13pt", bold=True)
        xb.addWidget(self._lbl_xp)
        top.addWidget(xp_box, 1)

        pa_box = QFrame()
        pa_box.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border-radius:8px;border:none;}}"
            f"QLabel{{background:transparent;border:none;}}")
        pb = QVBoxLayout(pa_box)
        pb.setContentsMargins(10, 8, 10, 8)
        pb.setSpacing(2)
        pb.addWidget(_lbl("Parchemins", T.HINT, "8pt"))
        self._lbl_parch = _lbl("—", T.BLUE, "13pt", bold=True)
        pb.addWidget(self._lbl_parch)
        top.addWidget(pa_box, 1)
        rl.addLayout(top)

        rl.addWidget(_sep())
        rl.addWidget(_lbl("Tableau des paliers", T.TEXT, "9pt", bold=True))

        head = QHBoxLayout()
        head.setSpacing(4)
        for txt, stretch in [("Palier", 2), ("Cases", 1), ("XP", 2), ("Crafts", 1)]:
            head.addWidget(_lbl(txt, T.HINT, "8pt", bold=True), stretch)
        rl.addLayout(head)
        rl.addWidget(_sep())

        self._table = QVBoxLayout()
        self._table.setSpacing(2)
        rl.addLayout(self._table)

        cl.addWidget(self._res_card)
        cl.addStretch()
        scroll.setWidget(container)
        self._scroll = scroll
        lay.addWidget(scroll, 1)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        # header(44) + hauteur réelle du contenu (plafonné pour activer le scroll)
        h = 44
        if hasattr(self, '_scroll') and self._scroll.widget():
            h += min(self._scroll.widget().sizeHint().height() + 8, 640)
        return QSize(350, h)

    def minimumSizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(350, 100)

    # ── Logique ──────────────────────────────────────────────────────
    def _on_mult(self, idx):
        v = self._mult_steps[idx]
        self._mult_val.setText(f"x{int(v)}" if v % 1 == 0 else f"x{v:.1f}")
        self._calculate()

    def _calculate(self):
        lvl_start  = self._lvl_start.value()
        lvl_target = self._lvl_target.value()
        mult       = self._mult_steps[self._mult_sl.value()]

        if lvl_start <= 0 or lvl_target <= 0 or lvl_target <= lvl_start:
            self._res_card.setVisible(False)
            return

        txt = self._xp_current.text().strip()
        if txt:
            try:
                xp_start = int(txt.replace(" ", "").replace(".", "").replace(",", ""))
            except ValueError:
                xp_start = _xp_min_for_level(lvl_start)
        else:
            xp_start = _xp_min_for_level(lvl_start)

        xp_target = _xp_min_for_level(lvl_target)
        xp_needed = max(0, xp_target - xp_start)

        total_crafts = math.ceil(xp_needed / (10 * mult)) if mult > 0 else 0
        nb_parch     = math.ceil(total_crafts / 10)

        rows = []
        for (p_start, p_end, p_xp, p_cases) in PALIERS_XP:
            if p_end   <= lvl_start:  continue
            if p_start >= lvl_target: break
            eff_start = max(lvl_start,  p_start)
            eff_end   = min(lvl_target, p_end)
            nb_total  = p_end   - p_start
            nb_eff    = eff_end - eff_start
            xp_eff    = round(p_xp * nb_eff / nb_total)
            if eff_start == lvl_start:
                deja = max(0, xp_start - _xp_min_for_level(p_start))
                xp_eff = max(0, xp_eff - deja)
            xpc = XP_CRAFT_TABLE.get(p_cases, p_cases * 10) * mult
            if xpc <= 0: continue
            rows.append({
                "label":  f"{eff_start} → {eff_end}",
                "cases":  p_cases,
                "xp":     xp_eff,
                "crafts": math.ceil(xp_eff / xpc),
            })

        self._lbl_xp.setText(f"{_fmt(xp_needed)} XP")
        self._lbl_parch.setText(_fmt(nb_parch))

        while self._table.count():
            item = self._table.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, row in enumerate(rows):
            bg = T.BG_DARK if i % 2 == 0 else T.SURFACE
            rf = QFrame()
            rf.setStyleSheet(
                f"QFrame{{background:{bg};border-radius:4px;border:none;}}"
                f"QLabel{{background:transparent;border:none;}}")
            rlay = QHBoxLayout(rf)
            rlay.setContentsMargins(6, 4, 6, 4)
            rlay.setSpacing(4)
            rlay.addWidget(_lbl(row["label"],       T.TEXT,    "8pt"),       2)
            rlay.addWidget(_lbl(str(row["cases"]),  T.SUBTEXT, "8pt"),       1)
            rlay.addWidget(_lbl(_fmt(row["xp"]),    T.SUBTEXT, "8pt"),       2)
            rlay.addWidget(_lbl(_fmt(row["crafts"]), T.ORANGE, "8pt", True), 1)
            self._table.addWidget(rf)

        self._res_card.setVisible(True)
        self._propagate()

    def _propagate(self):
        from PySide6.QtCore import QTimer
        def do():
            w = self
            while w:
                w.updateGeometry()
                w = w.parentWidget()
            root = self.window()
            if not root: return
            root.setMinimumHeight(0)
            root.setMaximumHeight(16777215)
            root.adjustSize()
        QTimer.singleShot(0, do)
