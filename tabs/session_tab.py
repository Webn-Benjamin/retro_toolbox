"""tabs/session_tab.py — Session de farm : chrono, compteurs donjons + captures/combats."""
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QProgressBar, QSlider
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
    sl = QSlider(Qt.Orientation.Horizontal)
    sl.setRange(lo, hi); sl.setValue(val)
    sl.setStyleSheet(
        f"QSlider::groove:horizontal{{background:{T.BG_DARK};height:4px;border-radius:2px;}}"
        f"QSlider::handle:horizontal{{background:white;border:2px solid {T.ORANGE};"
        f"width:14px;height:14px;border-radius:7px;margin:-5px 0;}}"
        f"QSlider::sub-page:horizontal{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border-radius:2px;}}")
    return sl

def _counter_btn(text, color, hover):
    b = QPushButton(text); b.setFixedSize(38, 38)
    b.setStyleSheet(
        f"QPushButton{{background:{color};color:white;border:none;"
        f"border-radius:9px;font-size:16pt;font-weight:bold;padding:0;}}"
        f"QPushButton:hover{{background:{hover};}}")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

def _counter_lbl(val="0"):
    l = QLabel(str(val)); l.setFixedSize(66, 38)
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l.setStyleSheet(
        f"font-size:18pt;font-weight:bold;color:{T.TEXT};"
        f"background:{T.BG_DARK};border-radius:9px;")
    return l

def _reset_btn(text="↺ Reset"):
    b = QPushButton(text); b.setFixedHeight(38)
    b.setStyleSheet(
        f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
        f"border:1px solid {T.BORDER};border-radius:9px;"
        f"font-size:9pt;font-weight:bold;padding:0 12px;}}"
        f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class SessionTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        cfg = model.load_config()
        self._farm_elapsed = 0
        self._farm_running = False
        self._farm_tick    = 0.0
        self._don_elapsed  = 0          # chrono du donjon en cours
        self._don_total    = 0          # temps cumulé de tous les donjons (pour stats)
        self._don_running  = False
        self._don_tick     = 0.0
        self._cap_total    = 0          # temps cumulé chrono captures (pour stats)
        self._cap_running  = False
        self._cap_tick     = 0.0
        self._donjons      = cfg.get("session_donjons", 0)
        self._captures     = cfg.get("session_captures", 0)
        self._build()
        self._load_state()

        self._farm_timer = QTimer(self)
        self._farm_timer.timeout.connect(self._farm_tick_fn)
        self._farm_timer.setInterval(1000)
        self._don_timer = QTimer(self)
        self._don_timer.timeout.connect(self._don_tick_fn)
        self._don_timer.setInterval(1000)
        self._cap_timer = QTimer(self)
        self._cap_timer.timeout.connect(self._cap_tick_fn)
        self._cap_timer.setInterval(1000)

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
        bl = QVBoxLayout(body); bl.setContentsMargins(14,12,14,12); bl.setSpacing(8)
        lay.addWidget(body, 1)

        # ── Nom de session ────────────────────────────────────────────
        name_card = _card()
        nl = QHBoxLayout(name_card); nl.setContentsMargins(12,8,12,8); nl.setSpacing(8)
        nl.addWidget(_lbl("🏷", size="11pt"))
        nl.addWidget(_lbl("Nom :", T.TEXT, "9pt", bold=True))
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
        fc = QVBoxLayout(farm_card); fc.setContentsMargins(14,12,14,12); fc.setSpacing(6)

        fct = QHBoxLayout()
        fct.addWidget(_lbl("🌾", size="11pt"))
        fct.addWidget(_lbl("Chrono de farm", T.TEXT, "10pt", bold=True))
        fct.addStretch()
        self._farm_status = QLabel("En pause")
        self._farm_status.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.HINT};font-size:8pt;"
            f"border-radius:8px;padding:2px 8px;border:none;")
        fct.addWidget(self._farm_status)
        fc.addLayout(fct)

        # Chrono — police réduite (était 38pt → 26pt)
        self._farm_lbl = QLabel("00:00:00")
        self._farm_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._farm_lbl.setStyleSheet(
            f"font-size:26pt;font-weight:bold;color:{T.ORANGE};"
            f"letter-spacing:2px;background:transparent;")
        fc.addWidget(self._farm_lbl)

        fb = QHBoxLayout(); fb.setSpacing(8); fb.addStretch()
        self._farm_btn = QPushButton("▶  Démarrer"); self._farm_btn.setFixedHeight(34)
        self._farm_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:9px;font-size:9pt;font-weight:bold;padding:0 18px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._farm_btn.clicked.connect(self._toggle_farm)
        farm_rst = _reset_btn("↺  Reset"); farm_rst.setFixedHeight(34)
        farm_rst.clicked.connect(self._reset_farm)
        fb.addWidget(self._farm_btn); fb.addWidget(farm_rst); fb.addStretch()
        fc.addLayout(fb)
        bl.addWidget(farm_card)

        # ── Compteur donjons ──────────────────────────────────────────
        don_card = _card()
        dc = QVBoxLayout(don_card); dc.setContentsMargins(14,12,14,12); dc.setSpacing(6)

        dt = QHBoxLayout()
        dt.addWidget(_lbl("🏰", size="11pt"))
        dt.addWidget(_lbl("Compteur de donjons", T.TEXT, "10pt", bold=True))
        dt.addStretch()
        dc.addLayout(dt)

        self._obj_bar = QProgressBar(); self._obj_bar.setFixedHeight(8)
        self._obj_bar.setTextVisible(False); self._obj_bar.setRange(0,100); self._obj_bar.setValue(0)
        self._obj_bar.setStyleSheet(
            f"QProgressBar{{background:{T.BG_DARK};border:none;border-radius:4px;}}"
            f"QProgressBar::chunk{{background:{T.BLUE};border-radius:4px;}}")
        dc.addWidget(self._obj_bar)
        dc.addWidget(_sep())

        dc.addWidget(_lbl("🎯 Objectif", T.TEXT, "9pt", bold=True))
        self._obj_sl = _green_slider(model.load_config().get("session_objectif",0), 0, 100)
        def _on_obj(v):
            self._obj_lbl.setText(f"{v} donjons" if v > 0 else "—")
            self._save("session_objectif", v); self._update_recap()
        self._obj_sl.valueChanged.connect(_on_obj)
        dc.addWidget(self._obj_sl)
        self._obj_lbl = QLabel()
        _obj_init = model.load_config().get("session_objectif", 0)
        self._obj_lbl.setText(f"{_obj_init} donjons" if _obj_init > 0 else "—")
        self._obj_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._obj_lbl.setStyleSheet(
            f"font-size:14pt;font-weight:bold;color:{T.ORANGE};background:transparent;")
        dc.addWidget(self._obj_lbl)

        ctrl = QHBoxLayout(); ctrl.setSpacing(8); ctrl.addStretch()
        btn_dm = _counter_btn("−", "#c0392b", "#e74c3c")
        self._don_lbl = _counter_lbl(self._donjons)
        btn_dp = _counter_btn("+", T.GRAD1, T.GRAD2)
        btn_dr = _reset_btn()
        btn_dm.clicked.connect(lambda: self._change_don(-1))
        btn_dp.clicked.connect(lambda: self._change_don(+1))
        btn_dr.clicked.connect(self._reset_don)
        ctrl.addWidget(btn_dm); ctrl.addWidget(self._don_lbl)
        ctrl.addWidget(btn_dp); ctrl.addSpacing(4); ctrl.addWidget(btn_dr)
        ctrl.addStretch()
        dc.addLayout(ctrl)

        dc.addWidget(_sep())

        # Chrono donjon (en cours)
        don_hdr = QHBoxLayout()
        don_hdr.addWidget(_lbl("⏱ Chrono donjon", T.TEXT, "9pt", bold=True))
        don_hdr.addStretch()
        don_hdr.addWidget(_lbl("Total :", T.HINT, "8pt"))
        self._don_total_lbl = QLabel("00:00:00")
        self._don_total_lbl.setStyleSheet(
            f"font-size:9pt;font-weight:bold;color:{T.ORANGE};background:transparent;")
        don_hdr.addWidget(self._don_total_lbl)
        dc.addLayout(don_hdr)

        don_time_row = QHBoxLayout(); don_time_row.setSpacing(8)
        self._don_time_lbl = QLabel("00:00:00")
        self._don_time_lbl.setStyleSheet(
            f"font-size:16pt;font-weight:bold;color:{T.BLUE};"
            f"letter-spacing:1px;background:transparent;")
        don_time_row.addWidget(self._don_time_lbl)
        don_time_row.addStretch()
        self._don_btn = QPushButton("▶  Démarrer"); self._don_btn.setFixedHeight(26)
        self._don_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._don_btn.clicked.connect(self._toggle_don)
        don_rst = QPushButton("↺  Reset"); don_rst.setFixedHeight(26)
        don_rst.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:6px;"
            f"font-size:8pt;font-weight:bold;padding:0 10px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        don_rst.clicked.connect(self._reset_don_timer)
        don_time_row.addWidget(self._don_btn); don_time_row.addWidget(don_rst)
        dc.addLayout(don_time_row)
        bl.addWidget(don_card)

        # ── Compteur captures / combats ───────────────────────────────
        cap_card = _card()
        cc = QVBoxLayout(cap_card); cc.setContentsMargins(14,12,14,12); cc.setSpacing(6)
        cap_hdr = QHBoxLayout()
        cap_hdr.addWidget(_lbl("⚔  Captures & Combats", T.TEXT, "10pt", bold=True))
        cap_hdr.addStretch()
        cc.addLayout(cap_hdr)
        cc.addWidget(_sep())

        ctrl_cap = QHBoxLayout(); ctrl_cap.setSpacing(8); ctrl_cap.addStretch()
        btn_cm = _counter_btn("−", "#c0392b", "#e74c3c")
        self._captures_lbl = _counter_lbl(self._captures)
        btn_cp = _counter_btn("+", T.GRAD1, T.GRAD2)
        btn_cr = _reset_btn()
        btn_cm.clicked.connect(lambda: self._change_counter("_captures", "session_captures", -1))
        btn_cp.clicked.connect(lambda: self._change_counter("_captures", "session_captures", +1))
        btn_cr.clicked.connect(lambda: self._reset_counter("_captures", "session_captures"))
        ctrl_cap.addWidget(btn_cm); ctrl_cap.addWidget(self._captures_lbl)
        ctrl_cap.addWidget(btn_cp); ctrl_cap.addSpacing(4); ctrl_cap.addWidget(btn_cr)
        ctrl_cap.addStretch()
        cc.addLayout(ctrl_cap)

        cc.addWidget(_sep())

        # Chrono captures (cumulatif)
        cap_chr_hdr = QHBoxLayout()
        cap_chr_hdr.addWidget(_lbl("⏱ Chrono captures", T.TEXT, "9pt", bold=True))
        cap_chr_hdr.addStretch()
        cap_chr_hdr.addWidget(_lbl("Total :", T.HINT, "8pt"))
        self._cap_total_lbl = QLabel("00:00:00")
        self._cap_total_lbl.setStyleSheet(
            f"font-size:9pt;font-weight:bold;color:{T.ORANGE};background:transparent;")
        cap_chr_hdr.addWidget(self._cap_total_lbl)
        cc.addLayout(cap_chr_hdr)

        cap_time_row = QHBoxLayout(); cap_time_row.setSpacing(8)
        self._cap_time_lbl = QLabel("00:00:00")
        self._cap_time_lbl.setStyleSheet(
            f"font-size:16pt;font-weight:bold;color:{T.BLUE};"
            f"letter-spacing:1px;background:transparent;")
        cap_time_row.addWidget(self._cap_time_lbl)
        cap_time_row.addStretch()
        self._cap_btn = QPushButton("▶  Démarrer"); self._cap_btn.setFixedHeight(26)
        self._cap_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._cap_btn.clicked.connect(self._toggle_cap)
        cap_rst = QPushButton("↺  Reset"); cap_rst.setFixedHeight(26)
        cap_rst.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:6px;"
            f"font-size:8pt;font-weight:bold;padding:0 10px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        cap_rst.clicked.connect(self._reset_cap_timer)
        cap_time_row.addWidget(self._cap_btn); cap_time_row.addWidget(cap_rst)
        cc.addLayout(cap_time_row)
        bl.addWidget(cap_card)

        # ── Récapitulatif ─────────────────────────────────────────────
        recap_card = _card()
        rl = QVBoxLayout(recap_card); rl.setContentsMargins(14,10,14,10); rl.setSpacing(5)
        rt = QHBoxLayout()
        rt.addWidget(_lbl("📊  Récapitulatif", T.HINT, "8pt", bold=True))
        rt.addStretch()
        btn_ra = QPushButton("↺ Reset tout"); btn_ra.setFixedHeight(22)
        btn_ra.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:6px;"
            f"font-size:7pt;font-weight:bold;padding:0 8px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        btn_ra.clicked.connect(self._reset_all)
        rt.addWidget(btn_ra)
        rl.addLayout(rt); rl.addWidget(_sep())

        self._recap_rows: dict[str, QLabel] = {}
        for key, label in [
            ("moy_don",  "Donjons / heure"),
            ("tps_don",  "Temps moyen / donjon"),
            ("moy_cap",  "Captures / heure"),
        ]:
            row = QHBoxLayout()
            row.addWidget(_lbl(label, T.SUBTEXT, "9pt")); row.addStretch()
            val = QLabel("—")
            val.setStyleSheet(
                f"font-size:9pt;font-weight:bold;color:{T.TEXT};background:transparent;")
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
            self._farm_running = True; self._farm_tick = time.time()
            self._farm_timer.start()
            self._farm_btn.setText("⏸  Pause")
            self._farm_status.setText("En cours")
            self._farm_status.setStyleSheet(
                f"background:{T.BG_DARK};color:{T.ORANGE};font-size:8pt;font-weight:bold;"
                f"border-radius:8px;padding:2px 8px;border:none;")
        self._save("session_farm_elapsed", self._farm_elapsed)

    def _farm_tick_fn(self):
        now = time.time()
        self._farm_elapsed += int(now - self._farm_tick); self._farm_tick = now
        self._farm_lbl.setText(self._fmt(self._farm_elapsed))
        self._update_recap()
        self._save("session_farm_elapsed", self._farm_elapsed)

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
                f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
                f"QPushButton:hover{{background:{T.GRAD2};}}")
        else:
            self._don_running = True; self._don_tick = time.time(); self._don_timer.start()
            self._don_btn.setText("⏸  Pause")
            self._don_btn.setStyleSheet(
                f"QPushButton{{background:#e67e22;color:white;border:none;"
                f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
                f"QPushButton:hover{{background:#d35400;}}")

    def _don_tick_fn(self):
        now = time.time()
        delta = int(now - self._don_tick); self._don_tick = now
        self._don_elapsed += delta
        self._don_total   += delta
        self._don_time_lbl.setText(self._fmt(self._don_elapsed))
        self._don_total_lbl.setText(self._fmt(self._don_total))
        self._update_recap()
        self._save("session_don_total", self._don_total)

    # ─── Chrono captures ─────────────────────────────────────────────
    def _toggle_cap(self):
        if self._cap_running:
            self._cap_running = False; self._cap_timer.stop()
            self._cap_btn.setText("▶  Démarrer")
            self._cap_btn.setStyleSheet(
                f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
                f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
                f"QPushButton:hover{{background:{T.GRAD2};}}")
        else:
            self._cap_running = True; self._cap_tick = time.time(); self._cap_timer.start()
            self._cap_btn.setText("⏸  Pause")
            self._cap_btn.setStyleSheet(
                f"QPushButton{{background:#e67e22;color:white;border:none;"
                f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
                f"QPushButton:hover{{background:#d35400;}}")

    def _cap_tick_fn(self):
        now = time.time()
        delta = int(now - self._cap_tick); self._cap_tick = now
        self._cap_running_elapsed = getattr(self, '_cap_running_elapsed', 0) + delta
        self._cap_total += delta
        self._cap_time_lbl.setText(self._fmt(getattr(self, '_cap_running_elapsed', 0)))
        self._cap_total_lbl.setText(self._fmt(self._cap_total))
        self._update_recap()
        self._save("session_cap_total", self._cap_total)

    def _reset_cap_timer(self):
        """Reset le chrono captures en cours (garde le total cumulé)."""
        self._cap_running = False; self._cap_timer.stop()
        self._cap_running_elapsed = 0
        self._cap_btn.setText("▶  Démarrer")
        self._cap_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._cap_time_lbl.setText("00:00:00")

    def _reset_don_timer(self):
        """Reset le chrono du donjon en cours (garde le total cumulé)."""
        self._don_running = False; self._don_timer.stop(); self._don_elapsed = 0
        self._don_btn.setText("▶  Démarrer")
        self._don_btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});color:white;border:none;"
            f"border-radius:6px;font-size:8pt;font-weight:bold;padding:0 10px;}}"
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

    # ─── Captures / Combats ───────────────────────────────────────────
    def _change_counter(self, attr, key, delta):
        setattr(self, attr, max(0, getattr(self, attr) + delta))
        getattr(self, f"{attr}_lbl").setText(str(getattr(self, attr)))
        self._update_recap(); self._save(key, getattr(self, attr))

    def _reset_counter(self, attr, key):
        setattr(self, attr, 0)
        getattr(self, f"{attr}_lbl").setText("0")
        self._update_recap(); self._save(key, 0)

    # ─── Récap ────────────────────────────────────────────────────────
    def _update_recap(self):
        if not hasattr(self, '_recap_rows') or not hasattr(self, '_obj_bar'):
            return

        hours = self._farm_elapsed / 3600.0
        obj   = self._obj_sl.value()

        # Barre objectif
        if obj > 0:
            pct   = min(int(self._donjons / obj * 100), 100)
            color = T.ORANGE if self._donjons >= obj else (T.ORANGE if pct >= 50 else T.BLUE)
            color = T.GREEN if self._donjons >= obj else color
            self._obj_bar.setRange(0, obj)
            self._obj_bar.setValue(min(self._donjons, obj))
            self._obj_bar.setStyleSheet(
                f"QProgressBar{{background:{T.BG_DARK};border:none;border-radius:4px;}}"
                f"QProgressBar::chunk{{background:{color};border-radius:4px;}}")
        else:
            self._obj_bar.setRange(0, 100); self._obj_bar.setValue(0)

        # Stats basées sur le chrono donjon cumulé (don_total)
        don_hours = self._don_total / 3600.0
        if don_hours >= 0.001:
            self._recap_rows["moy_don"].setText(f"{self._donjons / don_hours:.1f}" if self._donjons > 0 else "—")
        else:
            self._recap_rows["moy_don"].setText("—")

        cap_hours = self._cap_total / 3600.0
        if cap_hours >= 0.001:
            self._recap_rows["moy_cap"].setText(f"{self._captures / cap_hours:.1f}" if self._captures > 0 else "—")
        else:
            self._recap_rows["moy_cap"].setText("—")

        # Temps moyen / donjon
        if self._donjons > 0 and self._don_total > 0:
            tps = self._don_total / self._donjons
            m, s = int(tps // 60), int(tps % 60)
            self._recap_rows["tps_don"].setText(f"{m:02d}:{s:02d}")
        else:
            self._recap_rows["tps_don"].setText("—")

    def update_session_stats(self, maps):
        """Appelé depuis main_window toutes les secondes — pas utilisé ici."""
        pass

    # ─── Utilitaires ──────────────────────────────────────────────────
    @staticmethod
    def _fmt(sec):
        h, r = divmod(int(sec), 3600); m, s = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _save(self, key, val):
        cfg = model.load_config(); cfg[key] = val; model.save_config(cfg)

    def _load_state(self):
        cfg = model.load_config()
        self._farm_elapsed = cfg.get("session_farm_elapsed", 0)
        self._don_total    = cfg.get("session_don_total", 0)
        self._cap_total    = cfg.get("session_cap_total", 0)
        self._farm_lbl.setText(self._fmt(self._farm_elapsed))
        self._don_lbl.setText(str(self._donjons))
        self._captures_lbl.setText(str(self._captures))
        self._don_time_lbl.setText("00:00:00")
        self._cap_time_lbl.setText("00:00:00")
        self._don_total_lbl.setText(self._fmt(self._don_total))
        self._cap_total_lbl.setText(self._fmt(self._cap_total))
        self._update_recap()

    def _reset_all(self):
        self._reset_farm(); self._reset_don(); self._reset_don_timer()
        self._don_total = 0
        self._don_total_lbl.setText("00:00:00")
        self._save("session_don_total", 0)
        self._reset_cap_timer()
        self._cap_total = 0
        self._cap_total_lbl.setText("00:00:00")
        self._save("session_cap_total", 0)
        self._reset_counter("_captures", "session_captures")
