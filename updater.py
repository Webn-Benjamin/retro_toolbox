"""updater.py — Mise à jour automatique (un seul exe, auto-remplacement via .bat)."""

import sys
import os
import threading
import urllib.request
import json
import tempfile
import subprocess
from pathlib import Path

CURRENT_VERSION = "1.0.8"
VERSION_URL     = "https://retro-toolbox.fr/version.json"


def check_update_qt(parent=None):
    threading.Thread(target=lambda: _check(parent), daemon=True).start()


def _check(parent):
    try:
        req  = urllib.request.urlopen(VERSION_URL, timeout=4)
        data = json.loads(req.read().decode())
        latest = data.get("version", CURRENT_VERSION)
        url    = data.get("url", "")
        notes  = data.get("notes", "")
        if _is_newer(latest, CURRENT_VERSION) and url:
            from PySide6.QtCore import QMetaObject, Qt
            parent._update_info = (latest, url, notes)
            QMetaObject.invokeMethod(
                parent, "_show_update",
                Qt.ConnectionType.QueuedConnection)
    except Exception:
        pass


def _is_newer(remote, local):
    try:
        return tuple(int(x) for x in remote.split(".")) > \
               tuple(int(x) for x in local.split("."))
    except Exception:
        return False


def download_and_restart(url: str, version: str, on_progress=None):
    """
    Télécharge le nouvel exe, crée un .bat qui remplace et relance,
    puis ferme l'app.
    Appeler depuis un thread secondaire.
    """
    # Chemin de l'exe actuel
    if getattr(sys, 'frozen', False):
        current_exe = Path(sys.executable)
    else:
        # En dev : simuler
        current_exe = Path(sys.argv[0])

    exe_dir = current_exe.parent
    new_exe = exe_dir / f"_update_{version}.exe"

    # 1. Télécharger
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            with open(new_exe, "wb") as f:
                while True:
                    chunk = r.read(8192)
                    if not chunk: break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress and total:
                        on_progress(downloaded / total)
    except Exception as e:
        if new_exe.exists(): new_exe.unlink()
        raise e

    # 2. Créer le script bat qui remplace l'exe et relance
    bat_path = exe_dir / "_retro_update.bat"
    bat_content = f"""@echo off
ping 127.0.0.1 -n 3 > nul
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
    bat_path.write_text(bat_content, encoding="utf-8")

    # 3. Lancer le bat en arrière-plan et quitter l'app
    subprocess.Popen(
        ["cmd.exe", "/c", str(bat_path)],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True
    )

    # 4. Fermer l'app proprement
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    QTimer.singleShot(200, QApplication.instance().quit)
