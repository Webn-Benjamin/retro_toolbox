"""
main.py — Point d'entrée Retro Toolbox PySide6.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from main_window import MainWindow
import theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Retro Toolbox")
    app.setStyleSheet(theme.QSS)

    window = MainWindow()
    window.show()

    # Vérification mise à jour (3s après démarrage)
    from PySide6.QtCore import QTimer
    try:
        from updater import check_update_qt
        QTimer.singleShot(3000, lambda: check_update_qt(window))
    except Exception:
        pass

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
