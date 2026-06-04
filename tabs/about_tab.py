"""tabs/about_tab.py — Détails et session."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime
import theme

T = theme

class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._session_start = datetime.now()
        self._build()
        t = QTimer(self); t.timeout.connect(self._tick); t.start(1000)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 14, 12, 14)
        lay.setSpacing(10)

        # ── Hero card ─────────────────────────────────────
        hero = QFrame()
        hero.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"border-radius:12px;border:none;}}"
            f"QLabel{{background:transparent;color:white;}}")
        hl = QVBoxLayout(hero); hl.setContentsMargins(20,20,20,20); hl.setSpacing(4)
        icon = QLabel("🎮")
        icon.setStyleSheet("font-size:28pt;background:transparent;color:white;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(icon)
        title = QLabel("Retro Toolbox")
        title.setStyleSheet("font-size:15pt;font-weight:bold;background:transparent;color:white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(title)
        from updater import CURRENT_VERSION
        ver = QLabel(f"v{CURRENT_VERSION}")
        ver.setStyleSheet("font-size:9pt;background:transparent;color:white;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(ver)
        by = QLabel("par Steal")
        by.setStyleSheet("font-size:9pt;background:transparent;color:rgba(255,255,255,204);font-style:italic;")
        by.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(by)
        lay.addWidget(hero)

        # ── Session ───────────────────────────────────────
        sess_card = QFrame()
        sess_card.setStyleSheet(
            f"QFrame{{background:{T.SURFACE};border:1px solid {T.BORDER};"
            f"border-radius:10px;}}"
            f"QLabel{{background:transparent;}}")
        sc = QVBoxLayout(sess_card); sc.setContentsMargins(14,12,14,12); sc.setSpacing(8)
        hdr = QLabel("📊  SESSION EN COURS")
        hdr.setStyleSheet(f"font-size:8pt;font-weight:700;color:{T.HINT};")
        sc.addWidget(hdr)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{T.BORDER};max-height:1px;")
        sc.addWidget(sep)

        self._rows = {}
        for key, label, default in [
            ("kills",    "⚔️  Kills",          "0"),
            ("rares",    "💎  Drops rares",     "0"),
            ("duration", "⏱  Durée",           "00:00:00"),
            ("avg",      "📈  Moy. kills/heure","—"),
        ]:
            row = QHBoxLayout(); row.setSpacing(8)
            l = QLabel(label)
            l.setStyleSheet(f"font-size:9pt;color:{T.SUBTEXT};font-weight:600;")
            v = QLabel(default)
            v.setStyleSheet(
                f"font-size:9pt;font-weight:700;color:{T.ORANGE};"
                f"background:{T.SURFACE2};padding:2px 8px;border-radius:4px;")
            v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(l, 1); row.addWidget(v)
            sc.addLayout(row)
            self._rows[key] = v
        lay.addWidget(sess_card)

        # ── Bouton Discord ────────────────────────────────
        btn_discord = QPushButton("💬  Rejoindre le Discord")
        btn_discord.setFixedHeight(36)
        btn_discord.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:8px;"
            f"font-size:10pt;font-weight:700;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        btn_discord.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_discord.clicked.connect(lambda: __import__('webbrowser').open(
            "https://discord.com/invite/Md8RJXdtQZ"))
        lay.addWidget(btn_discord)
        lay.addStretch()

    def _tick(self):
        delta = datetime.now() - self._session_start
        h, r  = divmod(int(delta.total_seconds()), 3600)
        m, s  = divmod(r, 60)
        self._rows["duration"].setText(f"{h:02d}:{m:02d}:{s:02d}")
        kills = int(self._rows["kills"].text() or 0)
        hours = delta.total_seconds() / 3600
        avg = f"{kills/hours:.1f}" if hours > 0 else "—"
        self._rows["avg"].setText(avg)

    def add_kill(self): self._rows["kills"].setText(str(int(self._rows["kills"].text())+1))
    def add_rare(self): self._rows["rares"].setText(str(int(self._rows["rares"].text())+1))

    def update_session_stats(self, maps):
        total_kills = 0
        total_rares = 0
        for md in maps.values():
            for gd in md.get('groups', {}).values():
                total_kills += len(gd.get('deaths', []))
                total_rares += len(gd.get('bambouto_times', []))
        self._rows["kills"].setText(str(total_kills))
        self._rows["rares"].setText(str(total_rares))
