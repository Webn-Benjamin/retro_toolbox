"""notif_help.py - Dialog tutoriel pour activer les notifications Dofus."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt
import subprocess
import theme as T


STEPS = [
    (
        "1",
        "Ouvre les Parametres Windows",
        "Appuie sur Win + I ou cherche Parametres dans le menu Demarrer."
    ),
    (
        "2",
        "Va dans Notifications",
        "Systeme -> Notifications (Windows 10)\nou Confidentialite et securite -> Notifications (Windows 11)"
    ),
    (
        "3",
        "Active l'acces global",
        "Coche : Autoriser les applications a acceder a vos notifications"
    ),
    (
        "4",
        "Autorise Dofus Retro",
        "Dans la liste des applications, trouve Dofus et active son toggle."
    ),
    (
        "5",
        "Relance Retro Toolbox",
        "Ferme et reouvre l'application. Les notifications sont maintenant actives !"
    ),
]


class NotifHelpDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activer les notifications Dofus")
        self.setFixedWidth(420)
        self.setStyleSheet(f"QDialog{{background:{T.BG};}}")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)

        # Titre
        title = QLabel("🔔  Activer les notifications Dofus Retro")
        title.setStyleSheet(
            f"background:transparent;color:{T.TEXT};border:none;"
            f"font-size:11pt;font-weight:bold;")
        title.setWordWrap(True)
        lay.addWidget(title)

        desc = QLabel(
            "Pour que Retro Toolbox detecte les tours de combat, MP et echanges, "
            "Dofus Retro doit etre autorise a envoyer des notifications Windows.")
        desc.setStyleSheet(
            f"background:transparent;color:{T.HINT};border:none;"
            f"font-size:9pt;font-style:italic;")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{T.BORDER};")
        lay.addWidget(sep)

        # Etapes
        for num, titre, detail in STEPS:
            row = QFrame()
            row.setStyleSheet(
                f"QFrame{{background:{T.SURFACE};"
                f"border:none;"
                f"border-left:3px solid {T.ORANGE};}}"
                f"QLabel{{border:none;background:transparent;}}")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)
            rl.setSpacing(10)

            badge = QLabel(num)
            badge.setFixedSize(26, 26)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"background:{T.ORANGE};color:white;"
                f"font-size:9.5pt;font-weight:bold;")

            info_w = QVBoxLayout()
            info_w.setSpacing(2)

            t_lbl = QLabel(titre)
            t_lbl.setStyleSheet(
                f"background:transparent;color:{T.TEXT};border:none;"
                f"font-size:9.5pt;font-weight:bold;")

            d_lbl = QLabel(detail)
            d_lbl.setStyleSheet(
                f"background:transparent;color:{T.HINT};font-size:8.5pt;")
            d_lbl.setWordWrap(True)

            info_w.addWidget(t_lbl)
            info_w.addWidget(d_lbl)
            rl.addWidget(badge)
            rl.addLayout(info_w, 1)
            lay.addWidget(row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{T.BORDER};")
        lay.addWidget(sep2)

        # Boutons
        btns = QHBoxLayout()
        btns.setSpacing(8)

        btn_open = QPushButton("Ouvrir Parametres Windows")
        btn_open.setFixedHeight(34)
        btn_open.setStyleSheet(
            f"QPushButton{{background:{T.ORANGE};color:white;border:none;"
            f"padding:5px 12px;font-size:9.5pt;font-weight:bold;}}"
            f"QPushButton:hover{{background:{T.ORANGE_L};}}")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.clicked.connect(self._open_settings)

        btn_close = QPushButton("Fermer")
        btn_close.setFixedHeight(34)
        btn_close.setStyleSheet(
            f"QPushButton{{background:{T.BG_DARK};color:{T.SUBTEXT};border:none;"
            f"padding:5px 12px;font-size:9pt;}}"
            f"QPushButton:hover{{color:{T.TEXT};}}")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.reject)

        btns.addWidget(btn_open)
        btns.addWidget(btn_close)
        lay.addLayout(btns)

    def _open_settings(self):
        try:
            subprocess.Popen(
                "start ms-settings:privacy-notifications",
                shell=True)
        except Exception:
            pass
