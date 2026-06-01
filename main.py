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
    # Restaurer la position mémorisée
    import model as _model
    cfg = _model.load_config()
    wx, wy = cfg.get("window_x"), cfg.get("window_y")
    if wx is not None and wy is not None:
        screen = QApplication.primaryScreen().availableGeometry()
        wx = max(0, min(wx, screen.width()  - 100))
        wy = max(0, min(wy, screen.height() - 100))
        window.move(wx, wy)
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
