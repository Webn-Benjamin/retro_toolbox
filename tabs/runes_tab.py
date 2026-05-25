"""tabs/runes_tab.py — Runes + Calculateur de Puit inline PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
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

def _combo(items):
    c = QComboBox(); c.addItems(items)
    c.setStyleSheet(
        f"QComboBox{{background:{T.SURFACE2};border:1px solid {T.BORDER};border-radius:3px;"
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

        # Boutons rapides + Reset sur une seule ligne
        btns = QHBoxLayout(); btns.setSpacing(3)
        for d in [-5,-3,-2,-1]:
            b = QPushButton(str(d))
            b.setStyleSheet(f"QPushButton{{background:{T.RED};color:white;border:none;border-radius:3px;"
                f"padding:4px 0;font-weight:bold;font-size:8pt;}}"
                f"QPushButton:hover{{background:#9e4840;}}")
            b.clicked.connect(lambda _, delta=d: self._adjust(delta))
            btns.addWidget(b)
        for d in [1,2,3,5]:
            b = QPushButton(f"+{d}")
            b.setStyleSheet(f"QPushButton{{background:{T.GREEN};color:white;border:none;border-radius:3px;"
                f"padding:4px 0;font-weight:bold;font-size:8pt;}}"
                f"QPushButton:hover{{background:#6e9428;}}")
            b.clicked.connect(lambda _, delta=d: self._adjust(delta))
            btns.addWidget(b)
        reset = QPushButton("↺")
        reset.setFixedWidth(30)
        reset.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {T.BORDER};color:{T.SUBTEXT};"
            f"border-radius:3px;padding:4px;font-size:9pt;}}"
            f"QPushButton:hover{{border-color:{T.RED};color:{T.RED};}}")
        reset.clicked.connect(self._reset)
        btns.addWidget(reset)
        lay.addLayout(btns)
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
            f"QPushButton{{background:{T.ORANGE};color:white;border:none;border-radius:3px;"
            f"padding:6px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:{T.ORANGE_L};}}")
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
            f"QScrollBar:vertical{{background:{T.BG_DARK};width:5px;border-radius:2px;}}"
            f"QScrollBar::handle:vertical{{background:{T.BORDER};border-radius:2px;min-height:15px;}}"
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


# ── RunesTab ───────────────────────────────────────────────

class RunesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._puit_visible = False
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(8)

        # Titre + bouton puit
        tr = QHBoxLayout()
        title = QLabel("Poids des Runes")
        title.setStyleSheet(f"font-size:11pt;font-weight:bold;color:{T.TEXT};background:transparent;")
        self._btn_puit = QPushButton("🧮  Calculer PUIT")
        self._btn_puit.setStyleSheet(
            f"QPushButton{{background:{T.ORANGE};color:white;border:none;border-radius:3px;"
            f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:{T.ORANGE_L};}}")
        self._btn_puit.clicked.connect(self._toggle_puit)
        tr.addWidget(title); tr.addStretch(); tr.addWidget(self._btn_puit)
        lay.addLayout(tr)

        # Panneau puit inline (caché par défaut)
        self._puit_panel = PuitPanel()
        self._puit_panel.hide()
        lay.addWidget(self._puit_panel)

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
        lay.addWidget(card)

    def _toggle_puit(self):
        self._puit_visible = not self._puit_visible
        self._puit_panel.setVisible(self._puit_visible)
        self._btn_puit.setText("✕  Fermer Puit" if self._puit_visible else "🧮  Calculer PUIT")
        col = '#8c4038' if self._puit_visible else T.ORANGE
        hov = '#9e4840' if self._puit_visible else T.ORANGE_L
        self._btn_puit.setStyleSheet(
            f"QPushButton{{background:{col};color:white;border:none;border-radius:3px;"
            f"padding:6px 12px;font-weight:bold;font-size:9pt;}}"
            f"QPushButton:hover{{background:{hov};}}")
        self._apply_height()

    def _apply_height(self):
        root = self.window()
        if not root or not hasattr(root, '_adjust_height'): return
        root._adjust_height()
