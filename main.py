"""
main.py — Point d'entrée Retro Toolbox PySide6.
"""

import sys
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, qInstallMessageHandler, QtMsgType
from main_window import MainWindow
import theme


def _qt_msg_handler(msg_type, context, message):
    if "Could not parse" in message:
        print(f"\n{'='*60}")
        print(f"[QT CSS ERROR] {message}")
        print(f"  File : {context.file}")
        print(f"  Line : {context.line}")
        print(f"  Func : {context.function}")
        print("  Python traceback:")
        for line in traceback.format_stack()[:-1]:
            print("   ", line.strip())
        print('='*60)
    else:
        if msg_type == QtMsgType.QtWarningMsg:
            print(f"[Qt Warning] {message}")


def main():
    # Mode --apply-update : remplacement de l'exe, sans Qt.
    # On intercepte ici avant tout import Qt pour éviter l'erreur
    # "no Qt platform plugin could be initialized".
    import sys as _sys
    if len(_sys.argv) >= 3 and _sys.argv[1] == "--apply-update":
        try:
            from updater import apply_pending_update
            apply_pending_update()
        except Exception:
            pass
        import os as _os
        _os._exit(0)

    # Nettoyage des fichiers résiduels de la mise à jour précédente
    try:
        import sys as _sys2, time as _time2, threading as _th2
        from pathlib import Path as _Path
        _dir = _Path(_sys2.executable).parent if getattr(_sys2, "frozen", False) else _Path(__file__).parent
        # Supprimer le nouvel exe si la mise à jour a été interrompue
        (_dir / "_retro_toolbox_new.exe").unlink(missing_ok=True)
        # Supprimer le flag de relance si présent
        (_dir / "relaunch.flag").unlink(missing_ok=True)
        # Supprimer le .old en arrière-plan — le sous-process --apply-update
        # peut encore être en train de renommer, on réessaie pendant 30s
        def _cleanup_old():
            _old = _dir / "retro_toolbox.exe.old"
            for _ in range(60):  # 60 x 0.5s = 30s max
                try:
                    if _old.exists():
                        _old.unlink()
                    break
                except Exception:
                    _time2.sleep(0.5)
        _th2.Thread(target=_cleanup_old, daemon=True).start()
    except Exception:
        pass

    qInstallMessageHandler(_qt_msg_handler)
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
