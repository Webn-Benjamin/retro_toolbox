"""tabs/runes_tab.py — Runes + Calculateur de Puit inline PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QComboBox, QScrollArea,
    QLineEdit, QSpinBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QScreen
import theme

T = theme

RUNE_DATA = [
    ("PA",100,None,None,100),("PM",90,None,None,90),("PO",51,None,None,51),
    ("Invocation",30,None,None,30),("Critique",30,None,None,30),("Soin",20,None,None,20),
    None,
    ("Renvoie Do",30,None,None,30),("Do",20,None,None,20),("% Do",2,6,20,2),
    ("Do pi",15,None,None,15),("% Do pi",2,6,20,2),
    None,
    ("% Res",4,None,None,4),("Ré fixe",5,None,None,5),
    None,
    ("Sagesse",3,9,30,3),("Prospection",3,9,None,3),
    None,
    ("Ine/Fo/Age/Cha",1,3,10,1),("Initiative",1,3,10,0.1),("Vitalité",1,3,8,0.25),
    None,
    ("Pods",3,8,25,0.25),("Chasse",5,None,None,5),
]

RUNE_WEIGHTS = {}
for _r in RUNE_DATA:
    if _r:
        _n,_s,_p,_ra,_u = _r
        RUNE_WEIGHTS[_n] = {'Simple':float(_s or 0),'Pa':float(_p or 0),'Ra':float(_ra or 0)}

RUNE_NAMES = [r[0] for r in RUNE_DATA if r]

def _fmt(v):
    if v is None: return "—"
    return f"{v:g}" if isinstance(v, float) else str(v)

def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER};max-height:1px;")
    return f

def _lbl(txt, color=None, size="9pt", bold=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{size};"
    if color: ss += f"color:{color};"
    if bold:  ss += "font-weight:bold;"
    l.setStyleSheet(ss); return l

def _combo(items):
    c = QComboBox(); c.addItems(items)
    c.setStyleSheet(
        f"QComboBox{{background:{T.SURFACE2};border:1px solid {T.BORDER};border-radius:6px;"
        f"padding:4px 8px;color:{T.TEXT};font-size:9pt;}}"
        f"QComboBox QAbstractItemView{{background:{T.SURFACE};color:{T.TEXT};"
        f"selection-background-color:{T.ORANGE};selection-color:white;}}")
    return c


# ── Calculateur de Puit inline ─────────────────────────────

class PuitPanel(QFrame):
    """Panneau inline du calculateur de puit."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame#puit_panel{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:4px;}}")
        self.setObjectName("puit_panel")
        self._puit = 0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 8, 10, 8); lay.setSpacing(5)

        # Puit restant + boutons sur même ligne
        top = QHBoxLayout(); top.setSpacing(6)
        lbl = QLabel("Puit :")
        lbl.setStyleSheet(f"color:{T.HINT};font-size:9pt;font-weight:bold;background:transparent;")
        self._puit_lbl = QLabel("0")
        self._puit_lbl.setStyleSheet(f"font-size:24pt;font-weight:bold;color:{T.ORANGE};background:transparent;")
        self._puit_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(lbl); top.addWidget(self._puit_lbl, 1)
        lay.addLayout(top)

        # Boutons rapides basés sur les poids du tableau des runes
        # Valeurs utiles : 1,2,3,5,8,9,10,20,25,30
        def _make_btn(d):
            label = str(d) if d < 0 else f"+{d}"
            b = QPushButton(label)
            bg  = T.RED     if d < 0 else T.GREEN
            hov = "#9e4840" if d < 0 else "#6e9428"
            b.setStyleSheet(
                f"QPushButton{{background:{bg};color:white;border:none;border-radius:6px;"
                f"padding:4px 0;font-weight:bold;font-size:8pt;}}"
                f"QPushButton:hover{{background:{hov};}}")
            b.clicked.connect(lambda _, delta=d: self._adjust(delta))
            return b

        # Ligne négative : valeurs courantes en forgemagie
        neg_row = QHBoxLayout(); neg_row.setSpacing(3)
        for d in [-30, -25, -10, -9, -5, -3, -2, -1]:
            neg_row.addWidget(_make_btn(d))
        lay.addLayout(neg_row)

        # Ligne positive + reset
        pos_row = QHBoxLayout(); pos_row.setSpacing(3)
        for d in [1, 2, 3, 5, 9, 10, 25, 30]:
            pos_row.addWidget(_make_btn(d))
        reset = QPushButton("↺")
        reset.setFixedWidth(30)
        reset.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {T.BORDER};color:{T.SUBTEXT};"
            f"border-radius:6px;padding:4px;font-size:9pt;}}"
            f"QPushButton:hover{{border-color:{T.RED};color:{T.RED};}}")
        reset.clicked.connect(self._reset)
        pos_row.addWidget(reset)
        lay.addLayout(pos_row)
        lay.addWidget(_sep())

        # Sélecteurs compacts
        for attr, label in [('_saute','Rune sautée'),('_cause','Rune cause')]:
            row = QHBoxLayout(); row.setSpacing(6)
            lbl2 = QLabel(label)
            lbl2.setStyleSheet(f"color:{T.HINT};font-size:8pt;font-weight:bold;background:transparent;")
            lbl2.setFixedWidth(80)
            combo = _combo(RUNE_NAMES)
            tcombo = _combo(['Simple','Pa','Ra']); tcombo.setFixedWidth(72)
            row.addWidget(lbl2); row.addWidget(combo); row.addWidget(tcombo)
            lay.addLayout(row)
            setattr(self, f'{attr}_combo', combo)
            setattr(self, f'{attr}_type', tcombo)

        # Calculer + résultat sur même ligne
        calc_row = QHBoxLayout(); calc_row.setSpacing(6)
        calc = QPushButton("Calculer PUIT")
        calc.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;border-radius:6px;"
            f"padding:6px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        calc.clicked.connect(self._calculer)
        self._result_lbl = QLabel("")
        self._result_lbl.setStyleSheet(f"font-size:8pt;font-weight:bold;background:transparent;")
        self._result_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        calc_row.addWidget(calc); calc_row.addWidget(self._result_lbl, 1)
        lay.addLayout(calc_row)
        lay.addWidget(_sep())

        # Historique avec scroll fixe
        h_hdr = QHBoxLayout()
        h_lbl = QLabel("Historique")
        h_lbl.setStyleSheet(f"color:{T.HINT};font-size:9pt;font-weight:bold;background:transparent;")
        clr = QPushButton("Effacer")
        clr.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{T.HINT};"
            f"font-size:8pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.RED};}}")
        clr.clicked.connect(self._clear_hist)
        h_hdr.addWidget(h_lbl); h_hdr.addStretch(); h_hdr.addWidget(clr)
        lay.addLayout(h_hdr)

        # Zone scrollable fixe — ne grandit pas avec l'historique
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setFixedHeight(40)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea{{background:transparent;border:none;}}"
            f"QScrollBar:vertical{{background:{T.BG_DARK};width:5px;border-radius:4px;}}"
            f"QScrollBar::handle:vertical{{background:{T.BORDER};border-radius:4px;min-height:15px;}}"
            f"QScrollBar::handle:vertical:hover{{background:{T.ORANGE};}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")

        self._hist_widget = QWidget()
        self._hist_widget.setStyleSheet("background:transparent;")
        self._hist_lay = QVBoxLayout(self._hist_widget)
        self._hist_lay.setSpacing(2)
        self._hist_lay.setContentsMargins(0,0,0,0)
        self._hist_lay.addStretch()
        scroll.setWidget(self._hist_widget)
        lay.addWidget(scroll)
        self._hist_scroll = scroll

    def _adjust(self, d):
        self._puit = max(0, self._puit + d)
        self._add_hist(f"{'Ajout +' if d>0 else 'Retrait '}{d if d<0 else d} puit")
        self._refresh()

    def _reset(self):
        self._puit = 0; self._add_hist("Reset"); self._refresh()

    def _calculer(self):
        ws = RUNE_WEIGHTS.get(self._saute_combo.currentText(),{}).get(self._saute_type.currentText(),0)
        wc = RUNE_WEIGHTS.get(self._cause_combo.currentText(),{}).get(self._cause_type.currentText(),0)
        if not wc:
            self._result_lbl.setText("⚠ Rune cause invalide (poids 0)")
            self._result_lbl.setStyleSheet(f"font-size:9pt;font-weight:bold;color:{T.RED};background:transparent;")
            return
        net = ws - wc
        self._puit = max(0, self._puit + int(net))
        color = T.GREEN if net > 0 else T.RED if net < 0 else T.HINT
        txt = f"{net:.0f} puit {'gagné' if net>0 else 'perdu' if net<0 else 'neutre'}"
        self._result_lbl.setText(txt)
        self._result_lbl.setStyleSheet(f"font-size:9pt;font-weight:bold;color:{color};background:transparent;")
        self._add_hist(f"{self._saute_combo.currentText()} {ws:.0f} − "
                       f"{self._cause_combo.currentText()} {wc:.0f} = {net:.0f}")
        self._refresh()

    def _refresh(self):
        col = T.HINT if self._puit == 0 else T.ORANGE
        self._puit_lbl.setText(str(self._puit))
        self._puit_lbl.setStyleSheet(f"font-size:24pt;font-weight:bold;color:{col};background:transparent;")

    def _add_hist(self, msg):
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        row_w = QWidget(); row_w.setStyleSheet("background:transparent;")
        row = QHBoxLayout(row_w); row.setContentsMargins(0,1,0,1); row.setSpacing(4)
        m = QLabel(msg); m.setStyleSheet(f"color:{T.SUBTEXT};font-size:8pt;background:transparent;")
        t = QLabel(f"{now}  T:{self._puit}")
        t.setStyleSheet(f"color:{T.ORANGE};font-size:8pt;font-weight:bold;background:transparent;")
        row.addWidget(m); row.addStretch(); row.addWidget(t)
        # Insérer avant le stretch final (dernière position - 1)
        count = self._hist_lay.count()
        self._hist_lay.insertWidget(count - 1, row_w)
        if self._hist_lay.count() > 11:  # 10 entrées + 1 stretch
            item = self._hist_lay.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()
        # Scroll vers le bas
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, lambda: self._hist_scroll.verticalScrollBar().setValue(
            self._hist_scroll.verticalScrollBar().maximum()))

    def _clear_hist(self):
        while self._hist_lay.count() > 1:  # garder le stretch
            item = self._hist_lay.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()


# ── PuitWindow — fenêtre flottante détachée ──────────────

class PuitWindow(QFrame):
    """Fenêtre flottante contenant le calculateur de puit.
    Déplaçable par l'utilisateur, sans barre de titre Windows.
    """

    def __init__(self, puit_panel: 'PuitPanel', on_reattach, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self._puit_panel = puit_panel
        self._on_reattach = on_reattach
        self._drag_pos = None
        self.setObjectName("puit_window")
        self.setStyleSheet(
            f"QFrame#puit_window{{background:{T.BG};border:2px solid {T.ORANGE};"
            f"border-radius:6px;}}")
        self.setFixedWidth(340)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Barre de titre custom
        titlebar = QFrame()
        titlebar.setStyleSheet(
            f"QFrame{{background:{T.BG_DARK};border-bottom:1px solid {T.BORDER};"
            f"border-radius:4px 4px 0 0;}}")
        titlebar.setFixedHeight(34)
        tb_lay = QHBoxLayout(titlebar)
        tb_lay.setContentsMargins(10, 0, 8, 0); tb_lay.setSpacing(6)

        icon = QLabel("🧮")
        icon.setStyleSheet("background:transparent;font-size:12pt;")
        title = QLabel("Calculateur de Puit")
        title.setStyleSheet(
            f"background:transparent;color:{T.TEXT};font-size:9pt;font-weight:bold;")

        btn_reattach = QPushButton("⊙ Réintégrer")
        btn_reattach.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T.HINT};border:none;"
            f"font-size:8pt;padding:2px 6px;}}"
            f"QPushButton:hover{{color:{T.ORANGE};}}")
        btn_reattach.clicked.connect(self._reattach)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setObjectName("puit_close")
        # Forcer la couleur explicitement — le QSS parent peut écraser
        btn_close.setStyleSheet(
            "QPushButton#puit_close{"
            f"background:#8c4038;color:white;border:none;"
            f"font-size:11pt;font-weight:bold;border-radius:4px;}}"
            "QPushButton#puit_close:hover{"
            f"background:#9e4840;color:white;}}")
        btn_close.clicked.connect(self._reattach)

        tb_lay.addWidget(icon)
        tb_lay.addWidget(title, 1)
        tb_lay.addWidget(btn_reattach)
        tb_lay.addWidget(btn_close)
        lay.addWidget(titlebar)
        lay.addWidget(self._puit_panel)

    def _reattach(self):
        self._on_reattach()

    # ── Drag pour déplacer la fenêtre ─────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


# ── Données de probabilité exo PA / PM ────────────────────
_PCT_PA = {31:4.56,32:4.86,33:5.17,34:5.48,35:5.81,36:6.15,37:6.49,38:6.85,39:7.21,40:7.59,41:7.97,42:8.37,43:8.77,44:9.18,45:9.61,46:10.04,47:10.48,48:10.93,49:11.39,50:11.86,51:12.34,52:12.83,53:13.32,54:13.83,55:14.35,56:14.88,57:15.41,58:15.96,59:16.51,60:17.08,61:17.65,62:18.23,63:18.83,64:19.43,65:20.04,66:20.66,67:21.29,68:21.93,69:22.58,70:23.24,71:23.91,72:24.59,73:25.28,74:25.97,75:26.68,76:27.4,77:28.12,78:28.86,79:29.6,80:30.36,81:31.12,82:31.89,83:32.68,84:33.47,85:34.27,86:35.08,87:35.9,88:36.73,89:37.57,90:38.42,91:39.28,92:40.15,93:41.03,94:41.91,95:42.81,96:43.72,97:44.63,98:45.56,99:46.49,100:47.43,101:48.39,102:49.35,103:50.32,104:51.3,105:52.3,106:53.3,107:54.31,108:55.33,109:56.36,110:57.4,111:58.44,112:59.5,113:60.57,114:61.65,115:62.73,116:63.83,117:64.93,118:66.05}
_PCT_PM = {1:0.01,2:0.02,3:0.05,4:0.09,5:0.14,6:0.19,7:0.27,8:0.35,9:0.44,10:0.54,11:0.65,12:0.78,13:0.91,14:1.06,15:1.22,16:1.39,17:1.56,18:1.75,19:1.95,20:2.16,21:2.39,22:2.62,23:2.86,24:3.12,25:3.38,26:3.66,27:3.94,28:4.24,29:4.55,30:4.87,31:5.2,32:5.54,33:5.89,34:6.26,35:6.63,36:7.01,37:7.41,38:7.81,39:8.23,40:8.66,41:9.1,42:9.55,43:10.01,44:10.48,45:10.96,46:11.45,47:11.95,48:12.47,49:12.99,50:13.53,51:14.07,52:14.63,53:15.2,54:15.78,55:16.37,56:16.97,57:17.58,58:18.2,59:18.84,60:19.48,61:20.13,62:20.8,63:21.48,64:22.16,65:22.86,66:23.57,67:24.29,68:25.02,69:25.76,70:26.51,71:27.28,72:28.05,73:28.84,74:29.63,75:30.44,76:31.25,77:32.08,78:32.92,79:33.77,80:34.63,81:35.5,82:36.38,83:37.28,84:38.18,85:39.1,86:40.02,87:40.96,88:41.9,89:42.86,90:43.83,91:44.81,92:45.8,93:46.8,94:47.81,95:48.84,96:49.87,97:50.91,98:51.97,99:53.03,100:54.11,101:55.2,102:56.3,103:57.41,104:58.53,105:59.66,106:60.8,107:61.95,108:63.12,109:64.29,110:65.47}

def _get_pct(rune_type: str, level: int) -> float:
    """Retourne le % d'obtention de rune exo PA ou PM selon le niveau."""
    if rune_type == "PA":
        if level < 31:   return 0.0
        if level >= 119: return 66.66
        return _PCT_PA.get(level, 66.66)
    else:  # PM
        if level < 1:    return 0.0
        if level >= 111: return 66.66
        return _PCT_PM.get(level, 66.66)


class ExoCalcPanel(QFrame):
    """Calculateur Obtention rune PA/PM."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("exo_panel")
        self.setStyleSheet(
            f"QFrame#exo_panel{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:4px;}}"
            f"QLabel{{background:transparent;}}")
        self._build()

    def _build(self):
        from PySide6.QtWidgets import QSpinBox, QRadioButton, QButtonGroup
        lay = QVBoxLayout(self); lay.setContentsMargins(10,10,10,10); lay.setSpacing(8)

        # ── Type PA / PM — toggle pills ──────────────────────
        type_row = QHBoxLayout(); type_row.setSpacing(6)
        type_row.addWidget(_lbl("Type :", T.HINT, "9pt", bold=True))
        self._type_sel = "PA"
        self._type_btns = {}
        for txt in ["PA", "PM"]:
            b = QPushButton(txt); b.setFixedHeight(28); b.setFixedWidth(52)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self._type_btns[txt] = b
            type_row.addWidget(b)
        type_row.addStretch()
        lay.addLayout(type_row)
        self._type_btns["PA"].setChecked(True)
        def _on_type(txt):
            self._type_sel = txt
            for k, b in self._type_btns.items():
                active = (k == txt)
                b.setChecked(active)
                b.setStyleSheet(
                    (f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                     f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
                     f"border-radius:8px;font-size:9pt;font-weight:bold;}}")
                    if active else
                    (f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
                     f"border:1px solid {T.BORDER};border-radius:8px;"
                     f"font-size:9pt;font-weight:bold;}}"
                     f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.ORANGE};}}"))
            self._update_pct()
        for txt in ["PA", "PM"]:
            self._type_btns[txt].clicked.connect(lambda _, t=txt: _on_type(t))

        # ── Niveau de l'item ─────────────────────────────────
        lvl_row = QHBoxLayout(); lvl_row.setSpacing(8)
        lvl_row.addWidget(_lbl("Niveau item :", T.HINT, "9pt", bold=True))
        self._lvl_spin = QSpinBox()
        self._lvl_spin.setRange(1, 200); self._lvl_spin.setValue(100)
        self._lvl_spin.setFixedHeight(28); self._lvl_spin.setFixedWidth(72)
        self._lvl_spin.setStyleSheet(
            f"QSpinBox{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:6px;padding:2px 6px;color:{T.TEXT};font-size:9pt;}}"
            f"QSpinBox::up-button{{width:0;}}QSpinBox::down-button{{width:0;}}")
        lvl_row.addWidget(self._lvl_spin)

        # Badge probabilité
        self._pct_lbl = QLabel("47.43%")
        self._pct_lbl.setFixedHeight(28)
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pct_lbl.setStyleSheet(
            f"background:{T.ORANGE};color:white;font-size:10pt;font-weight:bold;"
            f"border-radius:6px;padding:2px 12px;")
        lvl_row.addWidget(self._pct_lbl)
        lvl_row.addStretch()
        lay.addLayout(lvl_row)

        # ── Quantité + potentiel ──────────────────────────────
        qty_row = QHBoxLayout(); qty_row.setSpacing(8)
        qty_row.addWidget(_lbl("Quantité craftées :", T.HINT, "9pt", bold=True))
        self._qty_forge = QSpinBox()
        self._qty_forge.setRange(1, 99999); self._qty_forge.setValue(100)
        self._qty_forge.setFixedHeight(28); self._qty_forge.setFixedWidth(80)
        self._qty_forge.setStyleSheet(
            f"QSpinBox{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:6px;padding:2px 6px;color:{T.TEXT};font-size:9pt;}}"
            f"QSpinBox::up-button{{width:0;}}QSpinBox::down-button{{width:0;}}")
        qty_row.addWidget(self._qty_forge)
        qty_row.addWidget(_lbl("→", T.HINT, "9pt"))
        self._potential_lbl = QLabel("≈ 47 runes")
        self._potential_lbl.setFixedHeight(28)
        self._potential_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._potential_lbl.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.BLUE};font-size:9pt;font-weight:bold;"
            f"border-radius:6px;padding:2px 10px;")
        qty_row.addWidget(self._potential_lbl)
        qty_row.addStretch()
        lay.addLayout(qty_row)

        self._lvl_spin.valueChanged.connect(self._update_pct)
        self._qty_forge.valueChanged.connect(self._update_pct)
        # Init styles + pct maintenant que _lvl_spin existe
        _on_type("PA")
        lay.addWidget(_sep())

        # ── Champs optionnels ─────────────────────────────────
        lay.addWidget(_lbl("Rentabilité (optionnel)", T.HINT, "8pt", bold=True))

        _inp_ss = (f"QLineEdit{{background:{T.SURFACE};border:1px solid {T.BORDER};"
                   f"border-radius:6px;padding:2px 6px;color:{T.TEXT};font-size:9pt;}}"
                   f"QLineEdit:focus{{border-color:{T.ORANGE};}}")

        def _kamas_field(label):
            row = QHBoxLayout(); row.setSpacing(8)
            row.addWidget(_lbl(label, T.SUBTEXT, "8pt"))
            row.addStretch()
            e = QLineEdit(); e.setFixedHeight(26); e.setFixedWidth(120)
            e.setStyleSheet(_inp_ss)
            e.setAlignment(Qt.AlignmentFlag.AlignRight)
            def _fmt(le=e):
                import re
                txt = re.sub(r'\s', '', le.text())
                try:
                    v = int(txt)
                    le.blockSignals(True)
                    le.setText(f"{v:,}".replace(",", " "))
                    le.blockSignals(False)
                except ValueError:
                    pass
            e.editingFinished.connect(_fmt)
            row.addWidget(e)
            lay.addLayout(row)
            return e

        def _qty_field(label):
            row = QHBoxLayout(); row.setSpacing(8)
            row.addWidget(_lbl(label, T.SUBTEXT, "8pt"))
            row.addStretch()
            e = QLineEdit(); e.setFixedHeight(26); e.setFixedWidth(80)
            e.setStyleSheet(_inp_ss)
            e.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(e)
            lay.addLayout(row)
            return e

        self._e_kamas  = _kamas_field("Kamas dépensés")
        self._e_price  = _kamas_field("Prix rune GA PA (u)")
        self._e_qty    = _qty_field("Quantité obtenue")
        lay.addWidget(_sep())

        # ── Calculer ──────────────────────────────────────────
        calc_row = QHBoxLayout(); calc_row.setSpacing(6)
        btn = QPushButton("Calculer")
        btn.setFixedHeight(30)
        btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:6px;"
            f"font-weight:bold;font-size:9pt;padding:0 14px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        btn.clicked.connect(self._calculer)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._result_lbl = QLabel("")
        self._result_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._result_lbl.setStyleSheet("font-size:9pt;font-weight:bold;background:transparent;")
        calc_row.addWidget(btn); calc_row.addWidget(self._result_lbl, 1)
        lay.addLayout(calc_row)

    def _update_pct(self):
        rtype = self._type_sel
        lvl   = self._lvl_spin.value()
        pct   = _get_pct(rtype, lvl)
        qty   = self._qty_forge.value()

        if pct == 0:
            self._pct_lbl.setText("N/A")
            self._pct_lbl.setStyleSheet(
                f"background:{T.BG_DARK};color:{T.HINT};font-size:10pt;font-weight:bold;"
                f"border-radius:6px;padding:2px 12px;")
            self._potential_lbl.setText("—")
        else:
            self._pct_lbl.setText(f"{pct}%")
            color = T.GREEN if pct >= 50 else T.ORANGE if pct >= 25 else T.RED
            self._pct_lbl.setStyleSheet(
                f"background:{color};color:white;font-size:10pt;font-weight:bold;"
                f"border-radius:6px;padding:2px 12px;")
            # Potentiel : nb runes attendues sur qty forgages
            expected = qty * pct / 100
            self._potential_lbl.setText(f"≈ {expected:.1f} runes")

    def _parse_int(self, e):
        import re
        try: return int(re.sub(r'\s', '', e.text()))
        except: return 0

    def _calculer(self):
        rtype = self._type_sel
        lvl   = self._lvl_spin.value()
        pct   = _get_pct(rtype, lvl)
        kamas = self._parse_int(self._e_kamas)
        price = self._parse_int(self._e_price)
        qty   = self._parse_int(self._e_qty)

        if price and qty:
            gain   = price * qty
            result = gain - kamas if kamas else gain
            sign   = "+" if result >= 0 else ""
            color  = T.GREEN if result >= 0 else T.RED
            label  = "bénéfice" if result >= 0 else "perte"
            txt    = f"{sign}{result:,} k — {label}".replace(",", " ")
        elif pct > 0:
            txt   = f"Probabilité : {pct}% (niv. {lvl})"
            color = T.ORANGE
        else:
            txt   = f"Aucune rune {rtype} sur niv. {lvl}"
            color = T.HINT

        self._result_lbl.setText(txt)
        self._result_lbl.setStyleSheet(
            f"font-size:9pt;font-weight:bold;color:{color};background:transparent;")


class ExoWindow(QFrame):
    """Fenêtre flottante détachable pour le calculateur exo."""

    def __init__(self, panel: ExoCalcPanel, on_reattach, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self._panel      = panel
        self._on_reattach = on_reattach
        self._drag_pos   = None
        self.setObjectName("exo_window")
        self.setStyleSheet(
            f"QFrame#exo_window{{background:{T.BG};border:2px solid {T.ORANGE};"
            f"border-radius:6px;}}")
        self.setFixedWidth(340)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        titlebar = QFrame()
        titlebar.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border-radius:4px 4px 0 0;}}"
            f"QLabel{{background:transparent;color:white;}}")
        tb = QHBoxLayout(titlebar); tb.setContentsMargins(10,6,6,6); tb.setSpacing(6)
        tb.addWidget(_lbl("⚡", size="10pt"))
        tb.addWidget(_lbl("Calculateur Obtention rune PA/PM", bold=True, size="9pt"), 1)
        btn_r = QPushButton("⎋"); btn_r.setFixedSize(24,24)
        btn_r.setObjectName("exo_close")
        btn_r.setStyleSheet(
            "QPushButton#exo_close{background:rgba(255,255,255,40);color:white;"
            "border:none;font-size:11pt;font-weight:bold;border-radius:4px;}"
            "QPushButton#exo_close:hover{background:rgba(255,255,255,80);}")
        btn_r.clicked.connect(self._on_reattach)
        tb.addWidget(btn_r)
        lay.addWidget(titlebar)
        lay.addWidget(self._panel)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


# ── RunesTab ───────────────────────────────────────────────

class RunesTab(QWidget):
    def sizeHint(self):
        lay = self.layout()
        if not lay: return super().sizeHint()
        h = lay.contentsMargins().top() + lay.contentsMargins().bottom()
        for i in range(lay.count()):
            item = lay.itemAt(i)
            if not item: continue
            w = item.widget()
            if w and w.isVisible():
                h += w.sizeHint().height() + lay.spacing()
            elif item.layout():
                h += item.layout().sizeHint().height() + lay.spacing()
        from PySide6.QtCore import QSize
        return QSize(self.width(), h)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._puit_visible  = False
        self._puit_detached = False
        self._puit_window   = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(8)

        # ── Compteur tentatives exo PA / PM ──────────────────────────
        self._exo_count = 0
        exo_card = QFrame()
        exo_card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:10px;}}"
            f"QLabel{{background:transparent;border:none;}}")
        ex = QVBoxLayout(exo_card); ex.setContentsMargins(12, 8, 12, 8); ex.setSpacing(4)

        # Ligne 1 : titre
        title_row = QHBoxLayout(); title_row.setSpacing(6)
        icon = QLabel("⚡"); icon.setStyleSheet("font-size:11pt;background:transparent;")
        title_row.addWidget(icon)
        ex_title = QLabel("Tentatives exo PA / PM")
        ex_title.setStyleSheet(f"font-size:9pt;font-weight:bold;color:{T.TEXT};")
        title_row.addWidget(ex_title); title_row.addStretch()
        ex.addLayout(title_row)

        # Ligne 2 : contrôles
        ctrl_row = QHBoxLayout(); ctrl_row.setSpacing(8)

        def _small_btn(txt, color, hover):
            b = QPushButton(txt); b.setFixedSize(26, 26)
            b.setStyleSheet(
                f"QPushButton{{background:{color};color:white;border:none;"
                f"border-radius:6px;font-size:13pt;font-weight:bold;padding:0;}}"
                f"QPushButton:hover{{background:{hover};}}")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            return b

        btn_minus = _small_btn("−", "#c0392b", "#e74c3c")
        self._exo_lbl = QLabel("0")
        self._exo_lbl.setFixedWidth(52)
        self._exo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._exo_lbl.setStyleSheet(
            f"font-size:14pt;font-weight:bold;color:{T.ORANGE};"
            f"background:{T.BG_DARK};border-radius:6px;padding:1px 6px;")
        btn_plus = _small_btn("+", T.GRAD1, T.GRAD2)

        btn_reset = QPushButton("↺"); btn_reset.setFixedSize(26, 26)
        btn_reset.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:6px;font-size:11pt;padding:0;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setToolTip("Remettre à zéro")

        def _update_exo():
            self._exo_lbl.setText(str(self._exo_count))
            import model; cfg = model.load_config()
            cfg["exo_count"] = self._exo_count; model.save_config(cfg)

        btn_minus.clicked.connect(lambda: [setattr(self, '_exo_count', max(0, self._exo_count - 1)), _update_exo()])
        btn_plus.clicked.connect(lambda: [setattr(self, '_exo_count', self._exo_count + 1), _update_exo()])
        btn_reset.clicked.connect(lambda: [setattr(self, '_exo_count', 0), _update_exo()])

        try:
            import model; self._exo_count = model.load_config().get("exo_count", 0)
            self._exo_lbl.setText(str(self._exo_count))
        except Exception:
            pass

        ctrl_row.addWidget(btn_minus)
        ctrl_row.addWidget(self._exo_lbl)
        ctrl_row.addWidget(btn_plus)
        ctrl_row.addSpacing(4)
        ctrl_row.addWidget(btn_reset)
        ctrl_row.addStretch()
        ex.addLayout(ctrl_row)
        lay.addWidget(exo_card)

        # ── Boutons exo + puit — pleine largeur, 2 colonnes, AU-DESSUS du titre ──
        _btn_ss_active = (f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                          f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
                          f"border-radius:8px;font-weight:bold;font-size:9pt;padding:7px 0;}}"
                          f"QPushButton:hover{{background:{T.GRAD2};}}")
        _btn_ss_idle   = (f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
                          f"border:1px solid {T.BORDER};border-radius:8px;"
                          f"font-weight:bold;font-size:9pt;padding:7px 0;}}"
                          f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.ORANGE};}}")
        _det_ss = (f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
                   f"border:1px solid {T.BORDER};border-radius:8px;font-size:11pt;}}"
                   f"QPushButton:hover{{background:{T.ORANGE};color:white;border-color:{T.ORANGE};}}")

        btn_cols = QHBoxLayout(); btn_cols.setSpacing(6)

        # Colonne Exo
        exo_col = QHBoxLayout(); exo_col.setSpacing(4)
        self._btn_exo = QPushButton("⚡  Calcul rune PA/PM")
        self._btn_exo.setFixedHeight(34); self._btn_exo.setStyleSheet(_btn_ss_idle)
        self._btn_exo.clicked.connect(self._toggle_exo)
        self._btn_exo_detach = QPushButton("⎋")
        self._btn_exo_detach.setFixedSize(34, 34); self._btn_exo_detach.setStyleSheet(_det_ss)
        self._btn_exo_detach.setToolTip("Détacher"); self._btn_exo_detach.clicked.connect(self._detach_exo)
        self._btn_exo_detach.hide()
        exo_col.addWidget(self._btn_exo, 1); exo_col.addWidget(self._btn_exo_detach)

        # Colonne Puit
        puit_col = QHBoxLayout(); puit_col.setSpacing(4)
        self._btn_puit = QPushButton("🧮  Calculer PUIT")
        self._btn_puit.setFixedHeight(34); self._btn_puit.setStyleSheet(_btn_ss_active)
        self._btn_puit.clicked.connect(self._toggle_puit)
        self._btn_detach = QPushButton("⎋")
        self._btn_detach.setFixedSize(34, 34); self._btn_detach.setStyleSheet(_det_ss)
        self._btn_detach.setToolTip("Détacher"); self._btn_detach.clicked.connect(self._detach_puit)
        self._btn_detach.hide()
        puit_col.addWidget(self._btn_puit, 1); puit_col.addWidget(self._btn_detach)

        btn_cols.addLayout(exo_col, 1); btn_cols.addLayout(puit_col, 1)
        lay.addLayout(btn_cols)

        # Titre sous les boutons
        # Panneau exo inline — AU-DESSUS du titre
        self._exo_panel      = ExoCalcPanel()
        self._exo_visible    = False
        self._exo_detached   = False
        self._exo_window     = None
        self._exo_panel.hide()
        lay.addWidget(self._exo_panel)

        # Panneau puit inline — AU-DESSUS du titre
        self._puit_panel = PuitPanel()
        self._puit_panel.hide()
        lay.addWidget(self._puit_panel)

        # Titre "Poids des Runes"
        tr = QHBoxLayout()
        title = QLabel("Poids des Runes")
        title.setStyleSheet(f"font-size:11pt;font-weight:bold;color:{T.TEXT};background:transparent;")
        tr.addWidget(title); tr.addStretch()
        lay.addLayout(tr)

        card = QFrame(); card.setObjectName("card")
        grid = QGridLayout(card); grid.setContentsMargins(0,0,0,0); grid.setSpacing(0)

        for col, h in enumerate(["Stat","Simple","Pa","Ra","Unité"]):
            lbl = QLabel(h)
            lbl.setStyleSheet(f"background:{T.BG_DARK};color:{T.SUBTEXT};font-weight:bold;"
                              f"font-size:8pt;padding:6px 8px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft if col==0 else Qt.AlignmentFlag.AlignRight)
            grid.addWidget(lbl, 0, col)

        row_idx = 1; data_idx = 0
        for entry in RUNE_DATA:
            if entry is None:
                sf = QFrame(); sf.setStyleSheet(f"background:{T.BG_DARK};"); sf.setFixedHeight(4)
                grid.addWidget(sf, row_idx, 0, 1, 5); row_idx += 1; continue
            stat,simple,pa,ra,unite = entry
            bg = T.SURFACE if data_idx%2==0 else T.SURFACE2
            for col,val in enumerate([stat,simple,pa,ra,unite]):
                txt = stat if col==0 else _fmt(val)
                lbl = QLabel(txt)
                lbl.setStyleSheet(
                    f"background:{bg};padding:5px 8px;"
                    + (f"color:{T.ORANGE};font-weight:bold;" if col>0 and txt!="—"
                       else f"color:{T.HINT};" if txt=="—" else f"color:{T.TEXT};"))
                lbl.setAlignment(Qt.AlignmentFlag.AlignLeft if col==0 else Qt.AlignmentFlag.AlignRight)
                grid.addWidget(lbl, row_idx, col)
            row_idx += 1; data_idx += 1

        grid.setColumnStretch(0, 2)
        for c in range(1,5): grid.setColumnStretch(c, 1)
        self._table_card = card
        lay.addWidget(card)

    def _toggle_puit(self):
        if self._puit_detached:
            self._reattach_puit()
            return
        self._puit_visible = not self._puit_visible
        self._puit_panel.setVisible(self._puit_visible)
        self._btn_detach.setVisible(self._puit_visible)
        from PySide6.QtWidgets import QSizePolicy
        sp = self._puit_panel.sizePolicy()
        if self._puit_visible:
            sp.setVerticalPolicy(QSizePolicy.Policy.Preferred)
        else:
            sp.setVerticalPolicy(QSizePolicy.Policy.Fixed)
        self._puit_panel.setSizePolicy(sp)
        self._puit_panel.setMaximumHeight(16777215 if self._puit_visible else 0)
        self._btn_puit.setText("✕  Fermer Puit" if self._puit_visible else "🧮  Calculer PUIT")
        col = 'T.RED' if self._puit_visible else T.ORANGE
        hov = '#9e4840' if self._puit_visible else T.ORANGE_L
        self._btn_puit.setStyleSheet(
            f"QPushButton{{background:{col};color:white;border:none;border-radius:6px;"
            f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:{hov};}}")
        self._apply_height()

    def _detach_puit(self):
        """Extrait le calculateur dans une fenêtre flottante."""
        if self._puit_detached: return

        # Retirer le panel du layout (setParent None le détache sans détruire)
        lay = self.layout()
        lay.removeWidget(self._puit_panel)
        self._puit_panel.setParent(None)

        # Créer la fenêtre flottante — on lui passe le panel comme enfant direct
        self._puit_window = PuitWindow(self._puit_panel, self._reattach_puit)

        # Positionner à côté de la fenêtre principale
        main = self.window()
        if main:
            geo = main.geometry()
            self._puit_window.move(geo.right() + 10, geo.top())
        else:
            self._puit_window.move(200, 200)

        self._puit_window.adjustSize()
        self._puit_window.show()
        self._puit_window.raise_()

        self._puit_detached = True
        self._puit_visible  = False
        self._btn_detach.hide()
        self._btn_puit.setText("✕  Fermer Puit")
        self._btn_puit.setStyleSheet(
            f"QPushButton{{background:#8c4038;color:white;border:none;border-radius:6px;"
            f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:#9e4840;}}")
        self._apply_height()

    def _reattach_puit(self):
        """Réintègre le calculateur dans l'onglet."""
        if not self._puit_detached: return

        # Détacher la fenêtre flottante SANS détruire le panel
        if self._puit_window:
            # Retirer le panel de la fenêtre avant de la fermer
            try:
                self._puit_panel.setParent(None)
            except RuntimeError:
                # Panel déjà détruit — en recréer un
                self._puit_panel = PuitPanel()
            self._puit_window.hide()
            self._puit_window.deleteLater()
            self._puit_window = None

        # Remettre le panel dans le layout inline
        lay = self.layout()
        self._puit_panel.setParent(self)
        lay.insertWidget(1, self._puit_panel)
        self._puit_panel.show()

        self._puit_detached = False
        self._puit_visible  = True
        self._btn_detach.setVisible(True)
        self._btn_puit.setText("✕  Fermer Puit")
        self._btn_puit.setStyleSheet(
            f"QPushButton{{background:#8c4038;color:white;border:none;border-radius:6px;"
            f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:#9e4840;}}")
        self._apply_height()

    def _apply_height(self):
        from PySide6.QtWidgets import QApplication
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

    def _toggle_exo(self):
        if self._exo_detached:
            if self._exo_window:
                self._exo_window.hide() if self._exo_window.isVisible() else self._exo_window.show()
            return
        self._exo_visible = not self._exo_visible
        self._exo_panel.setVisible(self._exo_visible)
        self._btn_exo_detach.setVisible(self._exo_visible)
        self._btn_exo.setText("✕  Fermer" if self._exo_visible else "⚡  Calcul rune PA/PM")
        self._btn_exo.setStyleSheet(
            (f"QPushButton{{background:#8c4038;color:white;border:none;border-radius:6px;"
             f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
             f"QPushButton:hover{{background:#9e4840;}}") if self._exo_visible else
            (f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};"
             f"border:1px solid {T.BORDER};border-radius:6px;"
             f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
             f"QPushButton:hover{{border-color:{T.ORANGE};color:{T.ORANGE};}}"))
        self._apply_height()

    def _detach_exo(self):
        if self._exo_detached: return
        lay = self.layout()
        lay.removeWidget(self._exo_panel)
        self._exo_panel.setParent(None)
        self._exo_window = ExoWindow(self._exo_panel, self._reattach_exo)
        main = self.window()
        if main:
            geo = main.geometry()
            self._exo_window.move(geo.right() + 10, geo.top() + 200)
        else:
            self._exo_window.move(200, 200)
        self._exo_window.adjustSize()
        self._exo_window.show()
        self._exo_window.raise_()
        self._exo_detached = True
        self._exo_visible  = False
        self._btn_exo_detach.hide()
        self._apply_height()

    def _reattach_exo(self):
        if not self._exo_detached: return
        if self._exo_window:
            try: self._exo_panel.setParent(None)
            except RuntimeError: self._exo_panel = ExoCalcPanel()
            self._exo_window.hide()
            self._exo_window.deleteLater()
            self._exo_window = None
        lay = self.layout()
        self._exo_panel.setParent(self)
        # Chercher la position du titre "Poids des Runes" et insérer juste avant
        title_idx = -1
        for i in range(lay.count()):
            item = lay.itemAt(i)
            if item and item.layout():
                inner = item.layout()
                for j in range(inner.count()):
                    w = inner.itemAt(j).widget() if inner.itemAt(j) else None
                    if w and isinstance(w, QLabel) and "Poids des Runes" in (w.text() or ""):
                        title_idx = i
                        break
            if title_idx >= 0: break
        insert_pos = title_idx if title_idx >= 0 else max(0, lay.count() - 1)
        lay.insertWidget(insert_pos, self._exo_panel)
        self._exo_panel.show()
        self._exo_detached = False
        self._exo_visible  = True
        self._btn_exo_detach.setVisible(True)
        # Remettre le bouton en état "ouvert"
        self._btn_exo.setText("✕  Fermer")
        self._btn_exo.setStyleSheet(
            f"QPushButton{{background:#8c4038;color:white;border:none;border-radius:6px;"
            f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:#9e4840;}}")
        self._apply_height()
