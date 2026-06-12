"""tabs/craft_hdv_tab.py — Calculateur de craft / marge HDV (vrai calculateur complet).

Réutilise le moteur complet de craft_tab.py (cartes, ressources, OCR clic droit,
marge HDV) et y ajoute un bouton retour vers le menu Calculateurs.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
import theme
from tabs.craft_tab import CraftTab

T = theme


class CraftHdvTab(QWidget):
    """Enveloppe le vrai CraftTab avec un header + bouton retour."""

    def __init__(self, on_back=None, parent=None):
        super().__init__(parent)
        self._on_back = on_back
        self._craft = CraftTab()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header avec bouton retour
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {T.GRAD1},stop:1 {T.GRAD2});border:none;}}"
            f"QLabel{{background:transparent;color:white;border:none;}}")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 12, 0)
        hl.setSpacing(8)
        if self._on_back:
            back = QPushButton("‹  Retour")
            back.setFixedHeight(28)
            back.setCursor(Qt.CursorShape.PointingHandCursor)
            back.setStyleSheet(
                "QPushButton{background:rgba(255,255,255,40);color:white;"
                "border:1px solid rgba(255,255,255,90);border-radius:6px;"
                "font-size:8pt;font-weight:bold;padding:0 10px;}"
                "QPushButton:hover{background:rgba(255,255,255,70);}")
            back.clicked.connect(self._on_back)
            hl.addWidget(back)
        t = QLabel("🔧  Calculateur Craft / HDV")
        t.setStyleSheet("font-size:11pt;font-weight:bold;color:white;background:transparent;")
        hl.addWidget(t)
        hl.addStretch()
        lay.addWidget(hdr)

        # Masquer le header interne du CraftTab (on garde le nôtre)
        inner_lay = self._craft.layout()
        if inner_lay and inner_lay.count() > 0:
            first = inner_lay.itemAt(0).widget()
            if first:
                first.setVisible(False)

        lay.addWidget(self._craft, 1)

    def set_active(self, active: bool):
        """Relaye l'activation du watcher OCR au CraftTab interne."""
        if hasattr(self._craft, "set_active"):
            self._craft.set_active(active)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(350, 600)

    def minimumSizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(350, 100)
