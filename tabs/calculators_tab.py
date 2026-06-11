"""tabs/calculators_tab.py — Onglet Calculateurs avec sous-pages XP Métier et Craft/HDV."""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QDoubleSpinBox, QScrollArea,
    QSizePolicy, QStackedWidget, QSpinBox
)
from PySide6.QtCore import Qt
import theme

T = theme

# ─── Données XP métier Dofus Rétro ────────────────────────────────────
# Format : (niveau_debut, niveau_fin, xp_totale_du_palier, cases_requises)
# Source : validé contre dofuspourlesnoobs.com (tableau de référence)
#
# FORMULE PROUVÉE :
#   XP par craft = XP_CRAFT_TABLE[cases] × multiplicateur
#   crafts_palier = ceil(xp_palier / (XP_CRAFT_TABLE[cases] × mult))
#
# XP_CRAFT_TABLE = {2:10, 3:25, 4:50, 5:100, 6:250, 7:500}
# (validé sur tous les paliers 1→100 ✓)

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

# XP par craft selon le nombre de cases du palier (mult=1, slider=2)
XP_CRAFT_TABLE = {
    2:  10,
    3:  25,
    4:  50,
    5:  100,
    6:  250,
    7:  500,
    8:  1_000,
    9:  2_000,
    10: 4_000,
    11: 8_000,
    12: 16_000,
}


def _xp_min_for_level(level: int) -> int:
    """XP totale cumulée minimale pour atteindre ce niveau (début du niveau)."""
    if level <= 1:
        return 0
    xp = 0
    for (lvl_start, lvl_end, xp_palier, _) in PALIERS_XP:
        if lvl_start >= level:
            break
        if lvl_end <= level:
            xp += xp_palier
        else:
            nb_levels = lvl_end - lvl_start
            xp += round(xp_palier * (level - lvl_start) / nb_levels)
            break
    return xp


def _cases_for_level(level: int) -> int:
    """Nombre de cases requises pour le niveau donné."""
    for (lvl_start, lvl_end, _, cases) in PALIERS_XP:
        if lvl_start <= level < lvl_end:
            return cases
    return PALIERS_XP[-1][3]


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

def _inp(placeholder="", w=None):
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setFixedHeight(32)
    if w: e.setFixedWidth(w)
    e.setStyleSheet(
        f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:6px;padding:2px 10px;color:{T.TEXT};font-size:10pt;}}"
        f"QLineEdit:focus{{border:1px solid {T.ORANGE};}}")
    return e

def _card(parent=None):
    f = QFrame(parent)
    f.setStyleSheet(
        f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:10px;}}"
        f"QLabel{{background:transparent;border:none;}}")
    return f

def _spinbox(min_v=1, max_v=200, val=None):
    s = QSpinBox()
    # 0 = valeur spéciale "vide" affichée comme " "
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

def _fmt_num(v):
    """Formate un entier avec séparateur de milliers (point)."""
    return f"{int(v):,}".replace(",", ".")


# ─── Page XP Métier ───────────────────────────────────────────────────

class XpMetierPage(QWidget):
    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._build(on_back)

    def _build(self, on_back):
        from PySide6.QtWidgets import QSlider
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 12, 0)
        hl.setSpacing(8)

        back = QPushButton("< Retour")
        back.setFixedHeight(28)
        back.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,40);color:white;"
            "border:1px solid rgba(255,255,255,100);border-radius:6px;"
            "font-size:8pt;font-weight:bold;padding:0 10px;}"
            "QPushButton:hover{background:rgba(255,255,255,70);}")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(on_back)
        hl.addWidget(back)

        t = QLabel("🎓  Calculateur XP Métier")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t)
        hl.addStretch()
        lay.addWidget(hdr)

        # ── Corps (pas de scroll, fit au contenu) ───────────────────
        body = QWidget()
        body.setStyleSheet(f"background:{T.BG};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(8)

        # ── Card inputs ─────────────────────────────────────────────
        inp_card = QFrame()
        inp_card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:10px;}}"
            f"QLabel{{background:transparent;border:none;}}")
        il = QVBoxLayout(inp_card)
        il.setContentsMargins(14, 10, 14, 12)
        il.setSpacing(6)

        # Niveau actuel
        il.addWidget(_lbl("Niveau actuel", T.HINT, "8pt"))
        self._lvl_start = _spinbox(1, 199, val=None)
        self._lvl_start.valueChanged.connect(self._calculate)
        il.addWidget(self._lvl_start)

        # XP actuelle optionnel
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

        # Niveau souhaité
        il.addWidget(_lbl("Niveau souhaité", T.HINT, "8pt"))
        self._lvl_target = _spinbox(2, 200, val=None)
        self._lvl_target.valueChanged.connect(self._calculate)
        il.addWidget(self._lvl_target)

        il.addWidget(_sep())

        # Multiplicateur — réglette style timer
        _mult_steps = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

        mult_row = QHBoxLayout()
        mult_row.setSpacing(8)
        mult_lbl_title = _lbl("Multiplicateur XP", T.HINT, "8pt")
        mult_row.addWidget(mult_lbl_title)
        mult_row.addStretch()
        self._mult_val_lbl = QLabel(f"x{_mult_steps[0]:.1f}".rstrip('0').rstrip('.') if _mult_steps[0] != 1.5 else "x1.5")
        self._mult_val_lbl.setFixedWidth(36)
        self._mult_val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mult_val_lbl.setStyleSheet(
            f"font-size:9pt;font-weight:bold;color:{T.ORANGE};"
            f"background:{T.BG_DARK};border-radius:6px;padding:2px 4px;")
        mult_row.addWidget(self._mult_val_lbl)
        il.addLayout(mult_row)

        self._mult_sl = QSlider(Qt.Orientation.Horizontal)
        self._mult_sl.setRange(0, len(_mult_steps) - 1)
        self._mult_sl.setValue(0)
        self._mult_sl.setTickInterval(1)
        self._mult_sl.setStyleSheet(
            f"QSlider::groove:horizontal{{background:{T.BG_DARK};height:4px;border-radius:2px;}}"
            f"QSlider::handle:horizontal{{background:white;border:2px solid {T.ORANGE};"
            f"width:14px;height:14px;border-radius:7px;margin:-5px 0;}}"
            f"QSlider::sub-page:horizontal{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border-radius:2px;}}")

        self._mult_steps = _mult_steps

        def _on_mult(idx):
            v = self._mult_steps[idx]
            label = f"x{int(v)}" if v % 1 == 0 else f"x{v:.1f}"
            self._mult_val_lbl.setText(label)
            self._calculate()

        self._mult_sl.valueChanged.connect(_on_mult)
        il.addWidget(self._mult_sl)

        # Marqueurs min/max
        marks_row = QHBoxLayout()
        marks_row.setContentsMargins(0, 0, 0, 0)
        marks_row.addWidget(_lbl("x1", T.HINT, "7pt"))
        marks_row.addStretch()
        marks_row.addWidget(_lbl("x4", T.HINT, "7pt"))
        il.addLayout(marks_row)

        bl.addWidget(inp_card)

        # ── Card résultat ────────────────────────────────────────────
        self._res_card = QFrame()
        self._res_card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:10px;}}"
            f"QLabel{{background:transparent;border:none;}}")
        self._res_card.setVisible(False)
        rl = QVBoxLayout(self._res_card)
        rl.setContentsMargins(14, 10, 14, 12)
        rl.setSpacing(6)

        # XP totale + parchemins sur la même ligne
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        xp_box = QFrame()
        xp_box.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border-radius:8px;border:none;}}"
            f"QLabel{{background:transparent;border:none;}}")
        xb = QVBoxLayout(xp_box)
        xb.setContentsMargins(10, 8, 10, 8)
        xb.setSpacing(2)
        xb.addWidget(_lbl("Gain total", T.HINT, "8pt"))
        self._lbl_xp_total = _lbl("—", T.GREEN, "13pt", bold=True)
        xb.addWidget(self._lbl_xp_total)
        top_row.addWidget(xp_box, 1)

        parch_box = QFrame()
        parch_box.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border-radius:8px;border:none;}}"
            f"QLabel{{background:transparent;border:none;}}")
        pb = QVBoxLayout(parch_box)
        pb.setContentsMargins(10, 8, 10, 8)
        pb.setSpacing(2)
        pb.addWidget(_lbl("Parchemins", T.HINT, "8pt"))
        self._lbl_parch = _lbl("—", T.BLUE, "13pt", bold=True)
        pb.addWidget(self._lbl_parch)
        top_row.addWidget(parch_box, 1)

        rl.addLayout(top_row)
        rl.addWidget(_sep())

        # Tableau des paliers
        rl.addWidget(_lbl("Tableau des paliers", T.TEXT, "9pt", bold=True))

        # En-tête tableau
        hrow = QHBoxLayout()
        hrow.setSpacing(4)
        for txt, stretch in [("Palier", 2), ("Cases", 1), ("XP", 2), ("Crafts", 1)]:
            hrow.addWidget(_lbl(txt, T.HINT, "8pt", bold=True), stretch)
        rl.addLayout(hrow)
        rl.addWidget(_sep())

        self._table_lay = QVBoxLayout()
        self._table_lay.setSpacing(2)
        rl.addLayout(self._table_lay)

        bl.addWidget(self._res_card)
        lay.addWidget(body)

    def _calculate(self):
        lvl_start  = self._lvl_start.value()
        lvl_target = self._lvl_target.value()
        mult_idx   = self._mult_sl.value()
        mult       = self._mult_steps[mult_idx]

        # Pas de calcul si les champs sont vides (valeur spéciale = 0 pour spinbox vide)
        if lvl_start <= 0 or lvl_target <= 0 or lvl_target <= lvl_start:
            self._res_card.setVisible(False)
            return

        # XP de départ
        xp_start_txt = self._xp_current.text().strip()
        if xp_start_txt:
            try:
                xp_start = int(xp_start_txt.replace(" ", "").replace(".", "").replace(",", ""))
            except ValueError:
                xp_start = _xp_min_for_level(lvl_start)
        else:
            xp_start = _xp_min_for_level(lvl_start)

        xp_target = _xp_min_for_level(lvl_target)
        xp_needed = max(0, xp_target - xp_start)

        # Total global
        total_crafts = math.ceil(xp_needed / (10 * mult)) if mult > 0 else 0
        nb_parch     = math.ceil(total_crafts / 10)

        # Tableau palier par palier
        palier_rows = []
        for (p_start, p_end, p_xp, p_cases) in PALIERS_XP:
            if p_end   <= lvl_start:  continue
            if p_start >= lvl_target: break

            eff_start    = max(lvl_start,  p_start)
            eff_end      = min(lvl_target, p_end)
            nb_lvl_total = p_end   - p_start
            nb_lvl_eff   = eff_end - eff_start
            xp_palier_eff = round(p_xp * nb_lvl_eff / nb_lvl_total)

            if eff_start == lvl_start:
                xp_deja = max(0, xp_start - _xp_min_for_level(p_start))
                xp_palier_eff = max(0, xp_palier_eff - xp_deja)

            xp_par_craft = XP_CRAFT_TABLE.get(p_cases, p_cases * 10) * mult
            if xp_par_craft <= 0:
                continue

            palier_rows.append({
                "label":  f"{eff_start} → {eff_end}",
                "cases":  p_cases,
                "xp":     xp_palier_eff,
                "crafts": math.ceil(xp_palier_eff / xp_par_craft),
            })

        # Mise à jour UI
        self._lbl_parch.setText(_fmt_num(nb_parch))
        self._lbl_xp_total.setText(f"{_fmt_num(xp_needed)} XP")

        while self._table_lay.count():
            item = self._table_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, row in enumerate(palier_rows):
            bg = T.BG_DARK if i % 2 == 0 else T.SURFACE
            row_frame = QFrame()
            row_frame.setStyleSheet(
                f"QFrame{{background:{bg};border-radius:4px;border:none;}}"
                f"QLabel{{background:transparent;border:none;}}")
            row_lay = QHBoxLayout(row_frame)
            row_lay.setContentsMargins(6, 4, 6, 4)
            row_lay.setSpacing(4)
            row_lay.addWidget(_lbl(row["label"],           T.TEXT,    "8pt"),       2)
            row_lay.addWidget(_lbl(str(row["cases"]),      T.SUBTEXT, "8pt"),       1)
            row_lay.addWidget(_lbl(_fmt_num(row["xp"]),    T.SUBTEXT, "8pt"),       2)
            row_lay.addWidget(_lbl(_fmt_num(row["crafts"]), T.ORANGE, "8pt", True), 1)
            self._table_lay.addWidget(row_frame)

        self._res_card.setVisible(True)


# ─── Page Craft / HDV ─────────────────────────────────────────────────

class CraftHdvPage(QWidget):
    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._build(on_back)

    def _build(self, on_back):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 12, 0)
        hl.setSpacing(8)

        back = QPushButton("< Retour")
        back.setFixedHeight(28)
        back.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,40);color:white;"
            "border:1px solid rgba(255,255,255,100);border-radius:6px;"
            "font-size:8pt;font-weight:bold;padding:0 10px;}"
            "QPushButton:hover{background:rgba(255,255,255,70);}")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(on_back)
        hl.addWidget(back)

        t = QLabel("🔧  Calculateur Craft / HDV")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t)
        hl.addStretch()
        lay.addWidget(hdr)

        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border-bottom:1px solid {T.BORDER};}}"
            f"QLabel{{background:transparent;border:none;}}")
        il = QHBoxLayout(info_frame)
        il.setContentsMargins(14, 10, 14, 10)
        il.setSpacing(10)
        icon = QLabel("🔧")
        icon.setStyleSheet("font-size:18pt;background:transparent;")
        il.addWidget(icon)
        desc = QLabel(
            "Le calculateur de craft complet est dans l'onglet <b>Craft</b>.\n"
            "Ici : calcul rapide de marge HDV.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{T.SUBTEXT};font-size:9pt;background:transparent;")
        desc.setTextFormat(Qt.TextFormat.RichText)
        il.addWidget(desc, 1)
        lay.addWidget(info_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea{{background:{T.BG};}}")
        container = QWidget()
        container.setStyleSheet(f"background:{T.BG};")
        cl = QVBoxLayout(container)
        cl.setContentsMargins(10, 12, 10, 12)
        cl.setSpacing(10)

        inp_card = _card()
        tl = QVBoxLayout(inp_card)
        tl.setContentsMargins(14, 12, 14, 14)
        tl.setSpacing(8)
        tl.addWidget(_lbl("Calcul rapide de marge", T.TEXT, "10pt", bold=True))
        tl.addWidget(_sep())

        tl.addWidget(_lbl("Prix de vente HDV (kamas)", T.HINT, "8pt"))
        self._price_sell = _inp("Ex: 500000")
        self._price_sell.textChanged.connect(self._update_margin)
        tl.addWidget(self._price_sell)

        tl.addWidget(_lbl("Coût total des ressources (kamas)", T.HINT, "8pt"))
        self._price_cost = _inp("Ex: 320000")
        self._price_cost.textChanged.connect(self._update_margin)
        tl.addWidget(self._price_cost)

        tl.addWidget(_lbl("Taxe HDV (%)", T.HINT, "8pt"))
        self._tax = QDoubleSpinBox()
        self._tax.setRange(0, 100)
        self._tax.setValue(2.0)
        self._tax.setSingleStep(0.5)
        self._tax.setDecimals(1)
        self._tax.setSuffix(" %")
        self._tax.setFixedHeight(32)
        self._tax.setStyleSheet(
            f"QDoubleSpinBox{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:6px;padding:2px 8px;color:{T.TEXT};font-size:10pt;}}"
            f"QDoubleSpinBox:focus{{border:1px solid {T.ORANGE};}}"
            f"QDoubleSpinBox::up-button{{width:0;border:none;}}"
            f"QDoubleSpinBox::down-button{{width:0;border:none;}}")
        self._tax.valueChanged.connect(self._update_margin)
        tl.addWidget(self._tax)
        cl.addWidget(inp_card)

        self._res_card = _card()
        self._res_card.setVisible(False)
        rl = QVBoxLayout(self._res_card)
        rl.setContentsMargins(14, 12, 14, 14)
        rl.setSpacing(8)
        rl.addWidget(_lbl("Résultat", T.TEXT, "10pt", bold=True))
        rl.addWidget(_sep())

        for attr, label, color, size in [
            ("_lbl_net",    "Prix net (après taxe) :", T.BLUE,  "11pt"),
            ("_lbl_margin", "Marge :",                 T.GREEN, "14pt"),
            ("_lbl_pct",    "Rentabilité :",           T.TEXT,  "11pt"),
        ]:
            box = QFrame()
            box.setStyleSheet(
                f"QFrame{{background:{T.BG_DARK};border-radius:8px;border:none;}}"
                f"QLabel{{background:transparent;border:none;}}")
            row = QHBoxLayout(box)
            row.setContentsMargins(12, 8, 12, 8)
            row.addWidget(_lbl(label, T.HINT, "9pt"))
            row.addStretch()
            w = _lbl("—", color, size, bold=True)
            setattr(self, attr, w)
            row.addWidget(w)
            rl.addWidget(box)

        cl.addWidget(self._res_card)
        scroll.setWidget(container)
        lay.addWidget(scroll)

    def _parse(self, text):
        try:
            return int(str(text).replace(" ", "").replace(".", "").replace(",", ""))
        except Exception:
            return 0

    def _update_margin(self):
        sell = self._parse(self._price_sell.text())
        cost = self._parse(self._price_cost.text())
        tax  = self._tax.value() / 100.0

        if sell <= 0 and cost <= 0:
            self._res_card.setVisible(False)
            return

        net    = round(sell * (1 - tax))
        margin = net - cost
        pct    = (margin / cost * 100) if cost > 0 else 0
        color  = T.GREEN if margin >= 0 else T.RED
        sign   = "+" if margin >= 0 else ""

        self._lbl_net.setText(f"{_fmt_num(net)} k")
        self._lbl_margin.setText(f"{sign}{_fmt_num(margin)} k")
        self._lbl_margin.setStyleSheet(
            f"color:{color};font-size:14pt;font-weight:bold;background:transparent;")
        self._lbl_pct.setText(f"{sign}{pct:.1f} %")
        self._lbl_pct.setStyleSheet(
            f"color:{color};font-size:11pt;font-weight:bold;background:transparent;")
        self._res_card.setVisible(True)


# ─── Page d'accueil Calculateurs ──────────────────────────────────────

class CalculatorsHomePanel(QWidget):
    def __init__(self, on_xp, on_craft, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 12, 0)
        t = QLabel("🧮  Calculateurs")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t)
        hl.addStretch()
        lay.addWidget(hdr)

        content = QWidget()
        content.setStyleSheet(f"background:{T.BG};")
        content.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        cl = QVBoxLayout(content)
        cl.setContentsMargins(14, 14, 14, 14)
        cl.setSpacing(10)
        cl.addWidget(_lbl("Choisissez un calculateur :", T.SUBTEXT, "9pt"))

        for icon, title, subtitle, callback in [
            ("🎓", "Calculateur XP Métier",
             "Calcule le nombre de crafts nécessaires\npour monter votre métier du niveau A au niveau B.",
             on_xp),
            ("🔧", "Calculateur Craft / HDV",
             "Calcule rapidement la marge et la rentabilité\nd'un craft en tenant compte de la taxe HDV.",
             on_craft),
        ]:
            btn = QFrame()
            btn.setStyleSheet(
                f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
                f"border-radius:12px;}}"
                f"QLabel{{background:transparent;border:none;}}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_lay = QHBoxLayout(btn)
            btn.setMinimumHeight(72)
            btn_lay.setContentsMargins(14, 12, 14, 12)
            btn_lay.setSpacing(12)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size:20pt;background:transparent;")
            btn_lay.addWidget(icon_lbl)

            texts = QVBoxLayout()
            texts.setSpacing(2)
            texts.addWidget(_lbl(title, T.TEXT, "10pt", bold=True))
            sub_lbl = _lbl(subtitle, T.HINT, "8pt")
            sub_lbl.setWordWrap(True)
            texts.addWidget(sub_lbl)
            btn_lay.addLayout(texts, 1)

            arrow = _lbl("›", T.ORANGE, "18pt", bold=True)
            btn_lay.addWidget(arrow)

            cl.addWidget(btn)
            btn.mousePressEvent = (lambda e, cb=callback: cb())

        lay.addWidget(content)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        h = 44  # header
        if hasattr(self, 'layout') and self.layout():
            lay = self.layout()
            h = lay.sizeHint().height()
        return QSize(350, h)


# ─── CalculatorsTab ────────────────────────────────────────────────────

class _InnerFitStack(QStackedWidget):
    """QStackedWidget interne qui délègue sizeHint au widget actif."""
    def sizeHint(self):
        w = self.currentWidget()
        return w.sizeHint() if w else super().sizeHint()
    def minimumSizeHint(self):
        w = self.currentWidget()
        return w.minimumSizeHint() if w else super().minimumSizeHint()


class CalculatorsTab(QWidget):
    PAGE_HOME  = 0
    PAGE_XP    = 1
    PAGE_CRAFT = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._stack = _InnerFitStack()
        self._stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self._home  = CalculatorsHomePanel(
            on_xp=lambda: self._go(self.PAGE_XP),
            on_craft=lambda: self._go(self.PAGE_CRAFT),
        )
        self._xp    = XpMetierPage(on_back=lambda: self._go(self.PAGE_HOME))
        self._craft = CraftHdvPage(on_back=lambda: self._go(self.PAGE_HOME))

        self._stack.addWidget(self._home)
        self._stack.addWidget(self._xp)
        self._stack.addWidget(self._craft)

        lay.addWidget(self._stack)
        self._go(self.PAGE_HOME)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        w = self._stack.currentWidget()
        if w:
            return w.sizeHint()
        return QSize(350, 200)

    def minimumSizeHint(self):
        return self.sizeHint()

    def _go(self, page: int):
        self._stack.setCurrentIndex(page)
        # Remonter jusqu'à la fenêtre exactement comme TodoTab
        w = self
        while w:
            w.updateGeometry()
            p = w.parentWidget()
            if p is None:
                w.setMinimumHeight(0)
                w.setMaximumHeight(16777215)
                w.adjustSize()
                break
            w = p
