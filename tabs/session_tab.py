"""tabs/session_tab.py — Chrono de farm + compteur de donjons."""
import time
from datetime import timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
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

def _card(radius=12):
    f = QFrame()
    f.setStyleSheet(
        f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
        f"border-radius:{radius}px;}}"
        f"QLabel{{background:transparent;border:none;}}")
    return f

def _icon_btn(txt, bg, fg="white", size=36):
    b = QPushButton(txt); b.setFixedSize(size, size)
    b.setStyleSheet(
        f"QPushButton{{background:{bg};color:{fg};border:none;"
        f"border-radius:{size//2}px;font-size:{size//2}pt;font-weight:bold;padding:0;}}"
        f"QPushButton:hover{{opacity:0.85;}}")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

def _outline_btn(txt, h=32):
    b = QPushButton(txt); b.setFixedHeight(h)
    b.setStyleSheet(
        f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
        f"border:1px solid {T.BORDER};border-radius:8px;"
        f"font-size:8pt;font-weight:bold;padding:0 12px;}}"
        f"QPushButton:hover{{color:{T.TEXT};border-color:{T.TEXT};}}")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class SessionTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed   = 0      # secondes
        self._running   = False
        self._last_tick = 0.0
        self._donjons   = 0

        # Charger depuis la config
        cfg = model.load_config()
        self._donjons = cfg.get("session_donjons", 0)

        self._build()
        self._load_elapsed()

        # Timer Qt toutes les secondes
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(1000)

    # ─── Build UI ─────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        # Header gradient
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14, 0, 12, 0)
        t = QLabel("⏱  Session")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t); hl.addStretch()
        lay.addWidget(hdr)

        # Contenu scrollable
        body = QWidget(); body.setStyleSheet(f"background:{T.BG};")
        bl = QVBoxLayout(body); bl.setContentsMargins(14, 14, 14, 14); bl.setSpacing(12)
        lay.addWidget(body, 1)

        # ── Carte Chrono ─────────────────────────────────────────────
        chrono_card = _card()
        cl = QVBoxLayout(chrono_card); cl.setContentsMargins(16, 14, 16, 14); cl.setSpacing(10)

        # Titre
        ct = QHBoxLayout()
        ct.addWidget(_lbl("🌾", size="12pt"))
        ct.addWidget(_lbl("Chrono de farm", T.TEXT, "10pt", bold=True))
        ct.addStretch()
        self._status_lbl = QLabel("En pause")
        self._status_lbl.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.HINT};font-size:8pt;"
            f"border-radius:8px;padding:2px 8px;")
        ct.addWidget(self._status_lbl)
        cl.addLayout(ct)

        # Affichage temps
        self._time_lbl = QLabel("00:00:00")
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_lbl.setStyleSheet(
            f"font-size:38pt;font-weight:bold;color:{T.ORANGE};"
            f"letter-spacing:2px;background:transparent;")
        cl.addWidget(self._time_lbl)

        # Boutons contrôle
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.addStretch()

        self._btn_start = QPushButton("▶  Démarrer")
        self._btn_start.setFixedHeight(38)
        self._btn_start.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:10px;"
            f"font-size:10pt;font-weight:bold;padding:0 20px;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_start.clicked.connect(self._toggle_chrono)
        btn_row.addWidget(self._btn_start)

        btn_reset_c = _outline_btn("↺  Reset", 38)
        btn_reset_c.clicked.connect(self._reset_chrono)
        btn_row.addWidget(btn_reset_c)
        btn_row.addStretch()
        cl.addLayout(btn_row)
        bl.addWidget(chrono_card)

        # ── Carte Donjons ─────────────────────────────────────────────
        don_card = _card()
        dl = QVBoxLayout(don_card); dl.setContentsMargins(16, 14, 16, 14); dl.setSpacing(10)

        # Titre
        dt_row = QHBoxLayout()
        dt_row.addWidget(_lbl("🏰", size="12pt"))
        dt_row.addWidget(_lbl("Compteur de donjons", T.TEXT, "10pt", bold=True))
        dt_row.addStretch()
        dl.addLayout(dt_row)

        # Contrôles sur une ligne : [−] [compteur] [+] [Reset]
        don_ctrl = QHBoxLayout(); don_ctrl.setSpacing(8)
        don_ctrl.addStretch()

        H = 42  # hauteur commune

        btn_don_m = QPushButton("−"); btn_don_m.setFixedSize(H, H)
        btn_don_m.setStyleSheet(
            f"QPushButton{{background:#c0392b;color:white;border:none;"
            f"border-radius:10px;font-size:18pt;font-weight:bold;padding:0;}}"
            f"QPushButton:hover{{background:#e74c3c;}}")
        btn_don_m.setCursor(Qt.CursorShape.PointingHandCursor)

        self._don_lbl = QLabel(str(self._donjons))
        self._don_lbl.setFixedSize(80, H)
        self._don_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._don_lbl.setStyleSheet(
            f"font-size:20pt;font-weight:bold;color:{T.BLUE};"
            f"background:{T.BG_DARK};border-radius:10px;padding:0;")

        btn_don_p = QPushButton("+"); btn_don_p.setFixedSize(H, H)
        btn_don_p.setStyleSheet(
            f"QPushButton{{background:{T.GRAD1};color:white;border:none;"
            f"border-radius:10px;font-size:18pt;font-weight:bold;padding:0;}}"
            f"QPushButton:hover{{background:{T.GRAD2};}}")
        btn_don_p.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_don_r = QPushButton("↺ Reset"); btn_don_r.setFixedHeight(H)
        btn_don_r.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.HINT};"
            f"border:1px solid {T.BORDER};border-radius:10px;"
            f"font-size:9pt;font-weight:bold;padding:0 14px;}}"
            f"QPushButton:hover{{color:{T.RED};border-color:{T.RED};}}")
        btn_don_r.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_don_m.clicked.connect(lambda: self._change_donjons(-1))
        btn_don_p.clicked.connect(lambda: self._change_donjons(+1))
        btn_don_r.clicked.connect(self._reset_donjons)

        don_ctrl.addWidget(btn_don_m)
        don_ctrl.addWidget(self._don_lbl)
        don_ctrl.addWidget(btn_don_p)
        don_ctrl.addSpacing(6)
        don_ctrl.addWidget(btn_don_r)
        don_ctrl.addStretch()
        dl.addLayout(don_ctrl)
        bl.addWidget(don_card)

        # ── Carte Récap ───────────────────────────────────────────────
        recap_card = _card()
        rl = QVBoxLayout(recap_card); rl.setContentsMargins(16, 12, 16, 12); rl.setSpacing(6)
        rl.addWidget(_lbl("📊  Récapitulatif de session", T.HINT, "8pt", bold=True))
        rl.addWidget(_sep())

        self._recap_rows: dict[str, QLabel] = {}
        for key, label in [
            ("moy_don", "Donjons / heure"),
            ("tps_don",  "Temps moyen / donjon"),
        ]:
            row = QHBoxLayout()
            row.addWidget(_lbl(label, T.SUBTEXT, "9pt"))
            row.addStretch()
            val = QLabel("—")
            val.setStyleSheet(
                f"font-size:9pt;font-weight:bold;color:{T.TEXT};background:transparent;")
            self._recap_rows[key] = val
            row.addWidget(val)
            rl.addLayout(row)

        bl.addWidget(recap_card)
        bl.addStretch()

    # ─── Chrono ───────────────────────────────────────────────────────
    def _toggle_chrono(self):
        if self._running:
            self._running = False
            self._timer.stop()
            self._btn_start.setText("▶  Reprendre")
            self._status_lbl.setText("En pause")
            self._status_lbl.setStyleSheet(
                f"background:{T.BG_DARK};color:{T.HINT};font-size:8pt;"
                f"border-radius:8px;padding:2px 8px;")
        else:
            self._running = True
            self._last_tick = time.time()
            self._timer.start()
            self._btn_start.setText("⏸  Pause")
            self._status_lbl.setText("En cours")
            self._status_lbl.setStyleSheet(
                f"background:#e8f5e9;color:#2e7d32;font-size:8pt;font-weight:bold;"
                f"border-radius:8px;padding:2px 8px;")
        self._save_elapsed()

    def _tick(self):
        now  = time.time()
        self._elapsed += int(now - self._last_tick)
        self._last_tick = now
        self._update_time_display()
        self._update_recap()
        self._save_elapsed()

    def _reset_chrono(self):
        self._running = False
        self._timer.stop()
        self._elapsed = 0
        self._btn_start.setText("▶  Démarrer")
        self._status_lbl.setText("En pause")
        self._status_lbl.setStyleSheet(
            f"background:{T.BG_DARK};color:{T.HINT};font-size:8pt;"
            f"border-radius:8px;padding:2px 8px;")
        self._update_time_display()
        self._update_recap()
        self._save_elapsed()

    def _update_time_display(self):
        td = timedelta(seconds=self._elapsed)
        h  = int(td.total_seconds() // 3600)
        m  = int((td.total_seconds() % 3600) // 60)
        s  = int(td.total_seconds() % 60)
        self._time_lbl.setText(f"{h:02d}:{m:02d}:{s:02d}")

    # ─── Donjons ──────────────────────────────────────────────────────
    def _change_donjons(self, delta: int):
        self._donjons = max(0, self._donjons + delta)
        self._don_lbl.setText(str(self._donjons))
        self._update_recap()
        self._save_donjons()

    def _reset_donjons(self):
        self._donjons = 0
        self._don_lbl.setText("0")
        self._update_recap()
        self._save_donjons()

    # ─── Récap ────────────────────────────────────────────────────────
    def _update_recap(self):
        hours = self._elapsed / 3600
        if hours > 0 and self._donjons > 0:
            moy = self._donjons / hours
            self._recap_rows["moy_don"].setText(f"{moy:.1f}")
            tps = self._elapsed / self._donjons
            td  = timedelta(seconds=int(tps))
            m   = int(td.total_seconds() // 60)
            s   = int(td.total_seconds() % 60)
            self._recap_rows["tps_don"].setText(f"{m:02d}:{s:02d}")
        else:
            self._recap_rows["moy_don"].setText("—")
            self._recap_rows["tps_don"].setText("—")

    # ─── Persistance ──────────────────────────────────────────────────
    def _save_elapsed(self):
        cfg = model.load_config()
        cfg["session_elapsed"]  = self._elapsed
        cfg["session_running"]  = self._running
        model.save_config(cfg)

    def _save_donjons(self):
        cfg = model.load_config()
        cfg["session_donjons"] = self._donjons
        model.save_config(cfg)

    def _load_elapsed(self):
        cfg = model.load_config()
        self._elapsed  = cfg.get("session_elapsed", 0)
        self._running  = False   # on ne reprend jamais auto au démarrage
        self._update_time_display()
        self._update_recap()

    def reset_session(self):
        """Reset complet — appelable depuis l'extérieur."""
        self._reset_chrono()
        self._reset_donjons()
