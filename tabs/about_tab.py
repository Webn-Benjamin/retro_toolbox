"""tabs/about_tab.py — Détails PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime
import theme


class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._session_start = datetime.now()
        self._build()
        t = QTimer(self); t.timeout.connect(self._tick); t.start(1000)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        # Titre
        card1 = QFrame(); card1.setObjectName("card")
        c1 = QVBoxLayout(card1); c1.setContentsMargins(12,16,12,16); c1.setSpacing(6)

        title = QLabel("Retro Toolbox")
        title.setStyleSheet(f"font-size:14pt;font-weight:bold;color:{theme.TEXT};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c1.addWidget(title)

        ver = QLabel("Version 1.0.0")
        ver.setStyleSheet(f"color:{theme.HINT};font-size:8pt;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c1.addWidget(ver)
        c1.addWidget(theme.sep(card1))

        QLabel("Powered by").setParent(None)
        by = QLabel("Powered by")
        by.setStyleSheet(f"color:{theme.HINT};font-size:8pt;")
        by.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c1.addWidget(by)

        steal = QLabel("Steal")
        steal.setStyleSheet(f"color:{theme.ORANGE};font-size:18pt;font-weight:bold;")
        steal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c1.addWidget(steal)
        lay.addWidget(card1)

        # Session
        card2 = QFrame(); card2.setObjectName("card")
        c2 = QVBoxLayout(card2); c2.setContentsMargins(12,10,12,10); c2.setSpacing(4)

        lbl_sess = QLabel("SESSION EN COURS")
        lbl_sess.setStyleSheet(f"color:{theme.HINT};font-size:7pt;font-weight:bold;letter-spacing:1px;")
        c2.addWidget(lbl_sess)
        c2.addWidget(theme.sep(card2))

        self._rows = {}
        for key, label, default, orange in [
            ("start","Début",self._session_start.strftime("%H:%M  —  %d/%m/%Y"), False),
            ("dur","Durée","00:00:00", True),
            ("kills","Kills totaux","0", False),
            ("rares","Rares totaux","0", False),
            ("avg_kill","Moy. kills","—", False),
            ("avg_rare","Moy. rares","—", False),
        ]:
            row = QHBoxLayout()
            k = QLabel(label)
            k.setStyleSheet(f"color:{theme.HINT};font-size:8pt;")
            k.setFixedWidth(100)
            v = QLabel(default)
            v.setStyleSheet(f"color:{theme.ORANGE if orange else theme.TEXT};font-weight:bold;font-size:8pt;")
            row.addWidget(k); row.addWidget(v); row.addStretch()
            c2.addLayout(row)
            self._rows[key] = v
        lay.addWidget(card2)
        lay.addStretch()

    def _tick(self):
        elapsed = datetime.now() - self._session_start
        total = int(elapsed.total_seconds())
        h, rem = divmod(total, 3600); m, s = divmod(rem, 60)
        self._rows["dur"].setText(f"{h:02d}:{m:02d}:{s:02d}")

    def update_session_stats(self, maps):
        all_kills, all_rares = [], []
        for md in maps.values():
            for gd in md['groups'].values():
                all_kills.extend(gd.get('deaths', []))
                all_rares.extend(gd.get('bambouto_times', []))
        def fmt(t):
            if not t: return "—"
            avg = sum(t)/len(t); m,s = divmod(int(avg),60)
            return f"{m:02d}:{s:02d}"
        self._rows["kills"].setText(str(len(all_kills)))
        self._rows["rares"].setText(str(len(all_rares)))
        self._rows["avg_kill"].setText(fmt(all_kills))
        self._rows["avg_rare"].setText(fmt(all_rares))
