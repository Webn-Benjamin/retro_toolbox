"""tabs/about_tab.py — À propos de Retro Toolbox."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
import webbrowser
import theme

T = theme

class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 14, 12, 14)
        lay.setSpacing(12)
        lay.addStretch()

        # Icône
        icon = QLabel("🎮")
        icon.setStyleSheet("font-size:36pt;background:transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)

        # Nom
        title = QLabel("Retro Toolbox")
        title.setStyleSheet(
            f"font-size:16pt;font-weight:bold;color:{T.ORANGE};"
            f"background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        # Version
        try:
            from updater import CURRENT_VERSION
            ver_txt = f"v{CURRENT_VERSION}"
        except Exception:
            ver_txt = ""
        ver = QLabel(ver_txt)
        ver.setStyleSheet(f"font-size:9pt;color:{T.HINT};background:transparent;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ver)

        # Auteur
        by = QLabel("par Steal")
        by.setStyleSheet(
            f"font-size:10pt;color:{T.SUBTEXT};font-style:italic;"
            f"background:transparent;")
        by.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(by)

        lay.addSpacing(16)

        # Bouton Discord
        btn = QPushButton("💬  Rejoindre le Discord")
        btn.setFixedHeight(36)
        btn.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});"
            f"color:white;border:none;border-radius:8px;"
            f"font-size:10pt;font-weight:700;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});}}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: webbrowser.open("https://discord.com/invite/Md8RJXdtQZ"))
        lay.addWidget(btn)
        lay.addStretch()

    # Garder les méthodes appelées depuis main_window
    def update_session_stats(self, maps): pass
    def add_kill(self): pass
    def add_rare(self): pass
