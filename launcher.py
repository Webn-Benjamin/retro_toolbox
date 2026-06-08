"""
launcher.py — Launcher automatique Retro Toolbox.

Ce fichier est compilé séparément en "Retro Toolbox Launcher.exe".
Il est le seul exe que l'utilisateur lance.
Il vérifie les mises à jour, télécharge si besoin, puis lance l'app.

Build :
    python -m PyInstaller --onefile --windowed
        --icon=retro_toolbox.ico
        --name "Retro Toolbox"
        --add-data "retro_toolbox.ico;."
        launcher.py
"""

import sys
import os
import json
import subprocess
import urllib.request
import urllib.error
import tempfile
import shutil
import threading
from pathlib import Path

# ── Config ─────────────────────────────────────────────────
VERSION_URL  = "https://retro-toolbox.fr/version.json"
APP_FILENAME = "Retro Toolbox App.exe"   # l'exe de l'app (mis à jour automatiquement)
TIMEOUT      = 5                          # secondes max pour la vérification

# ── Chemins ────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

APP_PATH     = BASE_DIR / APP_FILENAME
VERSION_FILE = BASE_DIR / "current_version.txt"


def get_current_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


def save_current_version(version: str):
    VERSION_FILE.write_text(version, encoding="utf-8")


def fetch_remote_info() -> dict | None:
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def version_tuple(v: str):
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0, 0, 0)


def download_app(url: str, dest: Path, on_progress=None) -> bool:
    try:
        tmp = Path(tempfile.mktemp(suffix=".exe", dir=dest.parent))
        with urllib.request.urlopen(url, timeout=60) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 8192
            with open(tmp, "wb") as f:
                while True:
                    data = r.read(chunk)
                    if not data:
                        break
                    f.write(data)
                    downloaded += len(data)
                    if on_progress and total:
                        on_progress(downloaded / total)
        # Remplacer l'ancienne version
        if dest.exists():
            dest.unlink()
        shutil.move(str(tmp), str(dest))
        return True
    except Exception as e:
        if tmp.exists():
            tmp.unlink()
        return False


def launch_app():
    if not APP_PATH.exists():
        _show_error(
            f"Application introuvable :\n{APP_PATH}\n\n"
            "Télécharge Retro Toolbox depuis retro-toolbox.fr")
        return
    try:
        subprocess.Popen([str(APP_PATH)], cwd=str(BASE_DIR))
    except Exception as e:
        _show_error(f"Impossible de lancer l'application :\n{e}")


def _show_error(msg: str):
    """Affiche une erreur via une fenêtre Qt minimale."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Retro Toolbox", msg)
    except Exception:
        pass


def _show_update_ui(remote_version: str, notes: str, url: str):
    """Fenêtre de progression du téléchargement."""
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QLabel,
        QProgressBar, QPushButton, QHBoxLayout
    )
    from PySide6.QtCore import Qt, QThread, Signal

    app = QApplication.instance() or QApplication(sys.argv)

    win = QWidget()
    win.setWindowTitle("Retro Toolbox — Mise à jour")
    win.setFixedSize(360, 180)
    win.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
    win.setStyleSheet("""
        QWidget { background: #e8dcc8; font-family: 'Segoe UI'; color: #2d241b; }
        QLabel  { background: transparent; }
        QPushButton {
            background: #d9791f; color: white; border: none;
            border-radius: 6px; padding: 6px 14px; font-weight: bold;
        }
        QPushButton:hover { background: #e8883a; }
        QPushButton:disabled { background: #c9b99a; color: #7a6a56; }
        QProgressBar {
            background: #d6c9b0; border: 1px solid #c9b99a;
            border-radius: 6px; text-align: center;
        }
        QProgressBar::chunk { background: #d9791f; border-radius: 4px; }
    """)

    lay = QVBoxLayout(win)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(10)

    title = QLabel(f"🎮 Mise à jour disponible — v{remote_version}")
    title.setStyleSheet("font-size:11pt;font-weight:bold;")
    lay.addWidget(title)

    if notes:
        note_lbl = QLabel(notes)
        note_lbl.setStyleSheet("font-size:9pt;color:#7a6a56;font-style:italic;")
        note_lbl.setWordWrap(True)
        lay.addWidget(note_lbl)

    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(0)
    bar.setFixedHeight(18)
    bar.setVisible(False)
    lay.addWidget(bar)

    status = QLabel("")
    status.setStyleSheet("font-size:8pt;color:#7a6a56;")
    lay.addWidget(status)

    btn_row = QHBoxLayout()
    btn_update = QPushButton("⬇  Mettre à jour maintenant")
    btn_skip   = QPushButton("Plus tard")
    btn_skip.setStyleSheet(
        "QPushButton{background:#d6c9b0;color:#7a6a56;border:1px solid #c9b99a;"
        "border-radius:6px;padding:6px 14px;font-weight:bold;}"
        "QPushButton:hover{background:#c9b99a;}")
    btn_row.addWidget(btn_update)
    btn_row.addWidget(btn_skip)
    lay.addLayout(btn_row)

    result = {"action": "skip"}

    class DownloadThread(QThread):
        progress = Signal(float)
        done     = Signal(bool)

        def run(self):
            ok = download_app(url, APP_PATH, lambda p: self.progress.emit(p))
            self.done.emit(ok)

    dl_thread = DownloadThread()

    def start_download():
        btn_update.setEnabled(False)
        btn_skip.setEnabled(False)
        bar.setVisible(True)
        status.setText("Téléchargement en cours…")
        dl_thread.start()

    def on_progress(p):
        bar.setValue(int(p * 100))

    def on_done(ok):
        if ok:
            save_current_version(remote_version)
            status.setText("✅ Mise à jour installée !")
            result["action"] = "updated"
        else:
            status.setText("❌ Erreur — vérifiez votre connexion.")
            btn_skip.setEnabled(True)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1200, win.close)

    dl_thread.progress.connect(on_progress)
    dl_thread.done.connect(on_done)
    btn_update.clicked.connect(start_download)
    btn_skip.clicked.connect(win.close)

    win.show()
    app.exec()
    return result["action"]


def main():
    current = get_current_version()
    remote  = fetch_remote_info()

    if remote and version_tuple(remote.get("version","0")) > version_tuple(current):
        # Nouvelle version disponible
        action = _show_update_ui(
            remote["version"],
            remote.get("notes", ""),
            remote["url"]
        )
        # Lancer l'app dans tous les cas (mise à jour ou skip)

    elif not APP_PATH.exists() and remote:
        # Premier lancement : télécharger l'app
        _show_update_ui(
            remote.get("version","?"),
            "Premier téléchargement de l'application.",
            remote["url"]
        )

    launch_app()


if __name__ == "__main__":
    main()
