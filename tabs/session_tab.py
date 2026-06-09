"""tabs/session_tab.py — Session de farm : chrono farm, compteur donjons + chrono donjon."""
import time
from datetime import timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QSpinBox,
    QProgressBar, QSlider
)
from PySide6.QtCore import Qt, QTimer
import model, theme

T = theme


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{T.BORDER};max-height:1px;"); return f

def _lbl(txt, color=None, size="9pt", bold=False):
    l = QLabel(txt)
    ss = f"background:transparent;font-size:{size};"
    if color: ss += f"color:{color};"
    if bold:  ss += "font-weight:bold;"
    l.setStyleSheet(ss); return l

def _card():
    f = QFrame()
    f.setStyleSheet(
        f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};border-radius:12px;}}"
        f"QLabel{{background:transparent;border:none;}}")
    return f

def _green_slider(val, lo, hi):
    """Réglette verte style settings."""
    sl = QSlider(Qt.Orientation.Horizontal)
    sl.setRange(lo, hi); sl.setValue(val)
    sl.setStyleSheet(
        f"QSlider::groove:horizontal{{background:{T.BG_DARK};height:4px;border-radius:2px;}}"
        f"QSlider::handle:horizontal{{background:white;border:2px solid #27ae60;"
        f"width:14px;height:14px;border-radius:7px;margin:-5px 0;}}"
        f"QSlider::sub-page:horizontal{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 #27ae60,stop:1 #2ecc71);border-radius:2px;}}")
    return sl


class SessionTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        cfg = model.load_config()
        self._farm_elapsed  = 0
        self._farm_running  = False
        self._farm_tick     = 0.0
        self._don_elapsed   = 0
        self._don_running   = False
        self._don_tick      = 0.0
        self._donjons       = cfg.get("session_donjons", 0)
        self._build()
        self._load_state()

        self._farm_timer = QTimer(self); self._farm_timer.timeout.connect(self._farm_tick_fn)
        self._farm_timer.setInterval(1000)
        self._don_timer  = QTimer(self); self._don_timer.timeout.connect(self._don_tick_fn)
        self._don_timer.setInterval(1000)

    # ─── Build UI ─────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14,0,12,0)
        hl.addWidget(_lbl("⏱  Session", bold=True, size="11pt"))
        hl.addStretch()
        lay.addWidget(hdr)

        body = QWidget(); body.setStyleSheet(f"background:{T.BG};")
        bl = QVBoxLayout(body); bl.setContentsMargins(14,14,14,14); bl.setSpacing(10)
        lay.addWidget(body, 1)

        # ── Nom de session ────────────────────────────────────────────
        name_card = _card()
        nl = QHBoxLayout(name_card); nl.setContentsMargins(12,8,12,8); nl.setSpacing(8)
        nl.addWidget(_lbl("🏷", size="11pt"))
        nl.addWidget(_lbl("Nom de la session :", T.TEXT, "9pt", bold=True))
        self._name_edit = QLineEdit()
        self._name_edit.setText(model.load_config().get("session_name",""))
        self._name_edit.setPlaceholderText("ex : Farm Arakne soir…")
        self._name_edit.setFixedHeight(28)
        self._name_edit.setStyleSheet(
            f"QLineEdit{{background:{T.BG_DARK};border:1px solid {T.BORDER};"
            f"border-radius:7px;padding:2px 8px;color:{T.TEXT};font-size:9pt;}}"
            f"QLineEdit:focus{{border-color:{T.ORANGE};}}")
        self._name_edit.textChanged.connect(lambda t: self._save("session_name", t))
        nl.addWidget(self._name_edit, 1)
        bl.addWidget(name_card)

        # ── Chrono de farm ────────────────────────────────────────────
        farm_card = _card()
        fc = QVBoxLayout(farm_card); fc.setContentsMargins(16,14,16,14); fc.setSpacing(10)

        fct = QHBoxLayout()
        fct.addWidget(_lbl("🌾", size="12pt"))
        fct.addWidget(_lbl("Chrono de farm", T.TEXT, "10pt", bold=True))
        fct.addStretch()
        self._farm_status = QLabel("En pause")
        self._farm_status.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.HINT};font-size:8pt;"
            f"border-radius:8px;padding:2px 8px;border:none;")
        fct.addWidget(self._farm_status)
        fc.addLayout(fct)

        self._farm_lbl = QLabel("00:00:00")
        self._farm_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._farm_lbl.setStyleSheet(
            f"font-size:38pt;font-weight:bold;color:{T.ORANGE};"
            f"letter-spacing:2px;background:transparent;")
        fc.addWidget(self._farm_lbl)

        fb = QHBoxLayout(); fb.setSpacing(10); fb.addStretch()
        self._farm_btn = QPushButton("▶  Démarrer"); self._farm_btn.setFixedHeight(38)
        self._farm_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:10px;font-size:10pt;font-weight:bold;padding:0 20px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._farm_btn.clicked.connect(self._toggle_farm)

        farm_rst = QPushButton("↺  Reset"); farm_rst.setFixedHeight(38)
        farm_rst.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:10px;"
            f"font-size:9pt;font-weight:bold;padding:0 16px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        farm_rst.clicked.connect(self._reset_farm)
        fb.addWidget(self._farm_btn); fb.addWidget(farm_rst); fb.addStretch()
        fc.addLayout(fb)
        bl.addWidget(farm_card)

        # ── Compteur de donjons ───────────────────────────────────────
        don_card = _card()
        dc = QVBoxLayout(don_card); dc.setContentsMargins(16,14,16,14); dc.setSpacing(8)

        # Titre + pace
        dt = QHBoxLayout()
        dt.addWidget(_lbl("🏰", size="12pt"))
        dt.addWidget(_lbl("Compteur de donjons", T.TEXT, "10pt", bold=True))
        dt.addStretch()
        dc.addLayout(dt)

        # Barre de progression objectif (donjons/objectif)
        self._obj_bar = QProgressBar(); self._obj_bar.setFixedHeight(10)
        self._obj_bar.setTextVisible(False); self._obj_bar.setRange(0,100); self._obj_bar.setValue(0)
        self._obj_bar.setStyleSheet(
            f"QProgressBar{{background:{T.BG_DARK};border:none;border-radius:5px;}}"
            f"QProgressBar::chunk{{background:{T.BLUE};border-radius:5px;}}")
        dc.addWidget(self._obj_bar)

        dc.addWidget(_sep())

        # Objectif — réglette verte + valeur en dessous
        dc.addWidget(_lbl("🎯 Objectif", T.TEXT, "9pt", bold=True))
        self._obj_sl = _green_slider(model.load_config().get("session_objectif",0), 0, 100)
        def _on_obj(v):
            self._obj_lbl.setText(f"{v} donjons" if v > 0 else "—")
            self._save("session_objectif", v); self._update_recap()
        self._obj_sl.valueChanged.connect(_on_obj)
        dc.addWidget(self._obj_sl)
        self._obj_lbl = QLabel()
        _obj_init = model.load_config().get("session_objectif",0)
        self._obj_lbl.setText(f"{_obj_init} donjons" if _obj_init > 0 else "—")
        self._obj_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._obj_lbl.setStyleSheet(
            f"font-size:16pt;font-weight:bold;color:#27ae60;background:transparent;")
        dc.addWidget(self._obj_lbl)

        # Boutons +/-
        H = 42
        ctrl = QHBoxLayout(); ctrl.setSpacing(8); ctrl.addStretch()
        btn_m = QPushButton("−"); btn_m.setFixedSize(H,H)
        btn_m.setStyleSheet(
            f"QPushButton{{background:#c0392b;color:white;border:none;"
            f"border-radius:10px;font-size:18pt;font-weight:bold;padding:0;}}"
            f"QPushButton:hover{{background:#e74c3c;}}")
        btn_m.setCursor(Qt.CursorShape.PointingHandCursor)

        self._don_lbl = QLabel(str(self._donjons))
        self._don_lbl.setFixedSize(80, H)
        self._don_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._don_lbl.setStyleSheet(
            f"font-size:20pt;font-weight:bold;color:{T.BLUE};"
            f"background:{T.BG_DARK};border-radius:10px;padding:0;")

        btn_p = QPushButton("+"); btn_p.setFixedSize(H,H)
        btn_p.setStyleSheet(
            f"QPushButton{{background:{T.GRAD1};color:white;border:none;"
            f"border-radius:10px;font-size:18pt;font-weight:bold;padding:0;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        btn_p.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_r = QPushButton("↺ Reset"); btn_r.setFixedHeight(H)
        btn_r.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:10px;"
            f"font-size:9pt;font-weight:bold;padding:0 14px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        btn_r.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_m.clicked.connect(lambda: self._change_don(-1))
        btn_p.clicked.connect(lambda: self._change_don(+1))
        btn_r.clicked.connect(self._reset_don)
        ctrl.addWidget(btn_m); ctrl.addWidget(self._don_lbl)
        ctrl.addWidget(btn_p); ctrl.addSpacing(6); ctrl.addWidget(btn_r)
        ctrl.addStretch()
        dc.addLayout(ctrl)

        dc.addWidget(_sep())

        # Chrono de donjon
        dc.addWidget(_lbl("⏱ Chrono donjon", T.TEXT, "9pt", bold=True))
        don_time_row = QHBoxLayout(); don_time_row.setSpacing(10)
        self._don_time_lbl = QLabel("00:00:00")
        self._don_time_lbl.setStyleSheet(
            f"font-size:18pt;font-weight:bold;color:{T.BLUE};"
            f"letter-spacing:1px;background:transparent;")
        don_time_row.addWidget(self._don_time_lbl)
        don_time_row.addStretch()

        self._don_btn = QPushButton("▶  Démarrer"); self._don_btn.setFixedHeight(28)
        self._don_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:7px;font-size:8pt;font-weight:bold;padding:0 12px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._don_btn.clicked.connect(self._toggle_don)

        don_rst = QPushButton("↺  Reset"); don_rst.setFixedHeight(28)
        don_rst.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:9px;"
            f"font-size:9pt;font-weight:bold;padding:0 14px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        don_rst.clicked.connect(self._reset_don_timer)
        don_time_row.addWidget(self._don_btn); don_time_row.addWidget(don_rst)
        dc.addLayout(don_time_row)
        bl.addWidget(don_card)

        # ── Récap ─────────────────────────────────────────────────────
        recap_card = _card()
        rl = QVBoxLayout(recap_card); rl.setContentsMargins(16,12,16,12); rl.setSpacing(6)
        rt = QHBoxLayout()
        rt.addWidget(_lbl("📊  Récapitulatif", T.HINT, "8pt", bold=True))
        rt.addStretch()
        btn_ra = QPushButton("↺ Reset tout"); btn_ra.setFixedHeight(24)
        btn_ra.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:6px;"
            f"font-size:7pt;font-weight:bold;padding:0 8px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        btn_ra.clicked.connect(self._reset_all)
        rt.addWidget(btn_ra)
        rl.addLayout(rt); rl.addWidget(_sep())
        self._recap_rows: dict[str, QLabel] = {}
        for key, label in [("moy_don","Donjons / heure"),("tps_don","Temps moyen / donjon")]:
            row = QHBoxLayout()
            row.addWidget(_lbl(label, T.SUBTEXT, "9pt")); row.addStretch()
            val = QLabel("—")
            val.setStyleSheet(f"font-size:9pt;font-weight:bold;color:{T.TEXT};background:transparent;")
            self._recap_rows[key] = val; row.addWidget(val); rl.addLayout(row)
        bl.addWidget(recap_card)
        bl.addStretch()

    # ─── Chrono farm ──────────────────────────────────────────────────
    def _toggle_farm(self):
        if self._farm_running:
            self._farm_running = False; self._farm_timer.stop()
            self._farm_btn.setText("▶  Reprendre")
            self._farm_status.setText("En pause")
            self._farm_status.setStyleSheet(
                f"background:{T.BG_DARK};color:{T.HINT};font-size:8pt;"
                f"border-radius:8px;padding:2px 8px;border:none;")
        else:
            self._farm_running = True; self._farm_tick = time.time(); self._farm_timer.start()
            self._farm_btn.setText("⏸  Pause")
            self._farm_status.setText("En cours")
            self._farm_status.setStyleSheet(
                f"background:#e8f5e9;color:#2e7d32;font-size:8pt;font-weight:bold;"
                f"border-radius:8px;padding:2px 8px;border:none;")
        self._save("session_farm_elapsed", self._farm_elapsed)

    def _farm_tick_fn(self):
        now = time.time()
        self._farm_elapsed += int(now - self._farm_tick); self._farm_tick = now
        self._farm_lbl.setText(self._fmt(self._farm_elapsed))
        self._update_recap(); self._save("session_farm_elapsed", self._farm_elapsed)

    def _reset_farm(self):
        self._farm_running = False; self._farm_timer.stop(); self._farm_elapsed = 0
        self._farm_btn.setText("▶  Démarrer")
        self._farm_status.setText("En pause")
        self._farm_status.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.HINT};font-size:8pt;"
            f"border-radius:8px;padding:2px 8px;border:none;")
        self._farm_lbl.setText("00:00:00")
        self._update_recap(); self._save("session_farm_elapsed", 0)

    # ─── Chrono donjon ────────────────────────────────────────────────
    def _toggle_don(self):
        if self._don_running:
            self._don_running = False; self._don_timer.stop()
            self._don_btn.setText("▶  Démarrer")
            self._don_btn.setStyleSheet(
                f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
                f"border-radius:7px;font-size:8pt;font-weight:bold;padding:0 12px;}}"
                f"QPushButton:hover{{background:{T.GRAD2};}}")
        else:
            self._don_running = True; self._don_tick = time.time(); self._don_timer.start()
            self._don_btn.setText("⏸  Pause")
            self._don_btn.setStyleSheet(
                f"QPushButton{{background:#e67e22;color:white;border:none;"
                f"border-radius:7px;font-size:8pt;font-weight:bold;padding:0 12px;}}"
                f"QPushButton:hover{{background:#d35400;}}")

    def _don_tick_fn(self):
        now = time.time()
        self._don_elapsed += int(now - self._don_tick); self._don_tick = now
        self._don_time_lbl.setText(self._fmt(self._don_elapsed))

    def _reset_don_timer(self):
        self._don_running = False; self._don_timer.stop(); self._don_elapsed = 0
        self._don_btn.setText("▶  Démarrer")
        self._don_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:7px;font-size:8pt;font-weight:bold;padding:0 12px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._don_time_lbl.setText("00:00:00")

    # ─── Donjons ──────────────────────────────────────────────────────
    def _change_don(self, delta):
        self._donjons = max(0, self._donjons + delta)
        self._don_lbl.setText(str(self._donjons))
        self._update_recap(); self._save("session_donjons", self._donjons)

    def _reset_don(self):
        self._donjons = 0; self._don_lbl.setText("0")
        self._update_recap(); self._save("session_donjons", 0)

    def _reset_all(self):
        self._reset_farm(); self._reset_don(); self._reset_don_timer()

    # ─── Récap ────────────────────────────────────────────────────────
    def _update_recap(self):
        # Guard: widgets pas encore créés pendant _build
        if not hasattr(self, '_recap_rows') or not hasattr(self, '_obj_bar'):
            return

        hours = self._farm_elapsed / 3600 if self._farm_elapsed > 0 else 0
        obj = self._obj_sl.value()

        # Barre objectif donjons
        if obj > 0:
            pct   = min(int(self._donjons / obj * 100), 100)
            done  = self._donjons >= obj
            color = "#27ae60" if done else (T.ORANGE if pct >= 50 else T.BLUE)
            self._obj_bar.setRange(0, obj)
            self._obj_bar.setValue(min(self._donjons, obj))
            self._obj_bar.setStyleSheet(
                f"QProgressBar{{background:{T.BG_DARK};border:none;border-radius:5px;}}"
                f"QProgressBar::chunk{{background:{color};border-radius:5px;}}")
            self._obj_bar.update()
        else:
            self._obj_bar.setValue(0)

        # Récap : nécessite au moins 5s de chrono farm et 1 donjon
        if hours > 0.001 and self._donjons > 0:
            moy  = self._donjons / hours
            tps  = self._farm_elapsed / self._donjons
            m, s = int(tps // 60), int(tps % 60)
            self._recap_rows["moy_don"].setText(f"{moy:.1f}")
            self._recap_rows["tps_don"].setText(f"{m:02d}:{s:02d}")
        else:
            self._recap_rows["moy_don"].setText("—")
            self._recap_rows["tps_don"].setText("—")

    # ─── Utilitaires ──────────────────────────────────────────────────
    @staticmethod
    def _fmt(sec):
        h, r = divmod(sec, 3600); m, s = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _save(self, key, val):
        cfg = model.load_config(); cfg[key] = val; model.save_config(cfg)

    def _load_state(self):
        cfg = model.load_config()
        self._farm_elapsed = cfg.get("session_farm_elapsed", 0)
        self._farm_lbl.setText(self._fmt(self._farm_elapsed))
        self._don_time_lbl.setText("00:00:00")
        self._update_recap()
