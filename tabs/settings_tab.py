"""tabs/settings_tab.py — Paramètres PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSlider, QFileDialog
)
from PySide6.QtCore import Qt
import model, theme


class SettingsTab(QWidget):
    def __init__(self, data_file_path, on_change_folder, parent=None):
        super().__init__(parent)
        self._on_change_folder = on_change_folder
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._build(data_file_path)

    def _build(self, data_file_path):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        # Dossier
        card1 = QFrame(); card1.setObjectName("card")
        c1 = QVBoxLayout(card1); c1.setContentsMargins(12,10,12,10); c1.setSpacing(6)
        lbl = QLabel("DOSSIER DES DONNÉES")
        lbl.setStyleSheet(f"color:{theme.HINT};font-size:7pt;font-weight:bold;letter-spacing:1px;")
        c1.addWidget(lbl)
        self._path_lbl = QLabel(data_file_path)
        self._path_lbl.setStyleSheet(f"color:{theme.ORANGE};font-size:8pt;")
        self._path_lbl.setWordWrap(True)
        c1.addWidget(self._path_lbl)
        btn = QPushButton("Changer le dossier"); btn.setObjectName("btn_orange")
        btn.clicked.connect(self._on_change_folder)
        c1.addWidget(btn)
        lay.addWidget(card1)

        # Seuil
        card2 = QFrame(); card2.setObjectName("card")
        c2 = QVBoxLayout(card2); c2.setContentsMargins(12,10,12,10); c2.setSpacing(8)
        lbl2 = QLabel("ALERTE TIMER")
        lbl2.setStyleSheet(f"color:{theme.HINT};font-size:7pt;font-weight:bold;letter-spacing:1px;")
        c2.addWidget(lbl2)
        hint = QLabel("Le timer passe en rouge après ce délai sans kill ni rare.")
        hint.setStyleSheet(f"color:{theme.HINT};font-size:8pt;")
        hint.setWordWrap(True)
        c2.addWidget(hint)

        row = QHBoxLayout()
        lbl_s = QLabel("Seuil"); lbl_s.setStyleSheet(f"color:{theme.TEXT};")
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(1, 60)
        self._slider.setValue(model.get_alert_threshold() // 60)
        self._slider.valueChanged.connect(self._on_slider)
        self._val_lbl = QLabel(f"{self._slider.value()} min")
        self._val_lbl.setStyleSheet(f"color:{theme.ORANGE};font-weight:bold;")
        self._val_lbl.setFixedWidth(45)
        row.addWidget(lbl_s); row.addWidget(self._slider); row.addWidget(self._val_lbl)
        c2.addLayout(row)
        lay.addWidget(card2)

        # Fixer la hauteur exacte après construction
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        total = (lay.contentsMargins().top() + lay.contentsMargins().bottom()
                 + card1.sizeHint().height() + card2.sizeHint().height()
                 + lay.spacing())
        self.setFixedHeight(total)

    def _on_slider(self, val):
        self._val_lbl.setText(f"{val} min")
        model.set_alert_threshold(val * 60)

    def update_path(self, path):
        self._path_lbl.setText(path)
