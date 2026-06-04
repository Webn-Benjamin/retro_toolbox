"""tabs/settings_tab.py — Paramètres."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSlider, QFileDialog
)
from PySide6.QtCore import Qt
import model, theme

T = theme

def _section(title):
    l = QLabel(title)
    l.setStyleSheet(
        f"background:transparent;color:{T.HINT};font-size:8pt;"
        f"font-weight:700;")
    return l

def _card():
    f = QFrame()
    f.setStyleSheet(
        f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:10px;}}"
        f"QLabel{{background:transparent;border:none;}}")
    return f

def _row(label, widget, lay):
    r = QHBoxLayout(); r.setSpacing(10)
    l = QLabel(label)
    l.setStyleSheet(f"font-size:10pt;color:{T.TEXT};font-weight:600;")
    r.addWidget(l, 1); r.addWidget(widget)
    lay.addLayout(r)

class _ThemeSwitch(QWidget):
    def __init__(self, dark, on_toggle, parent=None):
        super().__init__(parent)
        self._dark = dark; self._on_toggle = on_toggle
        self.setFixedSize(180, 28)
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(4)
        self._sun  = QPushButton("☀️  Clair")
        self._moon = QPushButton("🌙  Sombre")
        self._sun.setFixedHeight(28); self._moon.setFixedHeight(28)
        self._sun.setFixedWidth(78);  self._moon.setFixedWidth(96)
        self._sun.setCursor(Qt.CursorShape.PointingHandCursor)
        self._moon.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self._sun); lay.addWidget(self._moon)
        self._sun.clicked.connect(lambda: self._set(False))
        self._moon.clicked.connect(lambda: self._set(True))
        self._refresh()

    def _set(self, dark):
        if self._dark == dark: return
        self._dark = dark; self._refresh(); self._on_toggle(dark)

    def _refresh(self):
        on  = (f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
               f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
               f"border-radius:6px;font-size:8pt;font-weight:700;}}")
        off = (f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
               f"border:1px solid {T.BORDER};border-radius:6px;"
               f"font-size:8pt;font-weight:600;}}"
               f"QPushButton:hover{{color:{T.TEXT};}}")
        self._sun.setStyleSheet(on if not self._dark else off)
        self._moon.setStyleSheet(on if self._dark else off)


class SettingsTab(QWidget):
    def __init__(self, data_file_path, on_change_folder, parent=None):
        super().__init__(parent)
        self._path = data_file_path
        self._on_change = on_change_folder
        self._build(data_file_path)

    def _build(self, path):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 14, 12, 14); lay.setSpacing(10)

        # ── Dossier données ───────────────────────────────
        lay.addWidget(_section("📁  DOSSIER DES DONNÉES"))
        card1 = _card()
        c1 = QVBoxLayout(card1); c1.setContentsMargins(14,12,14,12); c1.setSpacing(8)
        self._path_lbl = QLabel(path)
        self._path_lbl.setStyleSheet(
            f"font-size:8pt;color:{T.SUBTEXT};"
            f"background:{T.SURFACE2};padding:6px 10px;"
            f"border-radius:6px;")
        self._path_lbl.setWordWrap(True)
        c1.addWidget(self._path_lbl)
        btn_folder = QPushButton("📂  Changer de dossier")
        btn_folder.setFixedHeight(32)
        btn_folder.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:8px;"
            f"font-size:9pt;font-weight:700;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_folder.clicked.connect(self._on_change)
        c1.addWidget(btn_folder)
        lay.addWidget(card1)

        # ── Alerte Timer ──────────────────────────────────
        lay.addWidget(_section("⏱  ALERTE TIMER"))
        card2 = _card()
        c2 = QVBoxLayout(card2); c2.setContentsMargins(14,12,14,12); c2.setSpacing(8)
        cfg = model.load_config()
        val = cfg.get("timer_alert_pct", 80)
        pct_lbl = QLabel(f"{val}%")
        pct_lbl.setStyleSheet(
            f"font-size:11pt;font-weight:700;color:{T.ORANGE};"
            f"background:{T.SURFACE2};padding:2px 10px;border-radius:6px;")
        pct_lbl.setFixedWidth(52)
        pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(50, 100); sl.setValue(val)
        sl.setStyleSheet(
            f"QSlider::groove:horizontal{{background:{T.BG_DARK};height:4px;border-radius:2px;}}"
            f"QSlider::handle:horizontal{{background:white;border:2px solid {T.ORANGE};"
            f"width:14px;height:14px;border-radius:7px;margin:-5px 0;}}"
            f"QSlider::sub-page:horizontal{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border-radius:2px;}}")
        def on_sl(v): pct_lbl.setText(f"{v}%"); cfg2=model.load_config(); cfg2["timer_alert_pct"]=v; model.save_config(cfg2)
        sl.valueChanged.connect(on_sl)
        row = QHBoxLayout(); row.setSpacing(10)
        row.addWidget(sl, 1); row.addWidget(pct_lbl)
        c2.addLayout(row)
        hint = QLabel("Alerte rouge quand le timer dépasse ce seuil")
        hint.setStyleSheet(f"font-size:8pt;color:{T.HINT};font-style:italic;background:transparent;")
        c2.addWidget(hint)
        lay.addWidget(card2)

        # ── Apparence ─────────────────────────────────────
        lay.addWidget(_section("🎨  APPARENCE"))
        card3 = _card()
        c3 = QVBoxLayout(card3); c3.setContentsMargins(14,12,14,12); c3.setSpacing(6)
        dark = cfg.get("dark_theme", False)
        sw = _ThemeSwitch(dark, self._toggle_theme)
        _row("Thème", sw, c3)
        lay.addWidget(card3)
        lay.addStretch()

    def _toggle_theme(self, dark):
        cfg = model.load_config()
        cfg["dark_theme"] = dark
        model.save_config(cfg)
        from PySide6.QtWidgets import QApplication, QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Thème")
        msg.setText("Relance l'application pour appliquer le thème.")
        msg.setStyleSheet(f"background:{T.BG};color:{T.TEXT};")
        msg.exec()

    def update_path(self, p):
        self._path_lbl.setText(p)
