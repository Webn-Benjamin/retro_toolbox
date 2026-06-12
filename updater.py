import sys as _sys
if _sys.platform == "darwin":
    import ssl as _ssl
    try:
        import certifi as _certifi
        _ssl._create_default_https_context = lambda: _ssl.create_default_context(
            cafile=_certifi.where())
    except ImportError:
        _ssl._create_default_https_context = _ssl._create_unverified_context

"""updater.py - Mise a jour automatique."""

import sys
import os
import threading
import urllib.request
import json
import subprocess
from pathlib import Path

CURRENT_VERSION = "1.1.4"
VERSION_URL     = "https://retro-toolbox.fr/version.json"

# User-Agent navigateur pour eviter les blocages serveur
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def check_update_qt(parent=None):
    threading.Thread(target=lambda: _check(parent), daemon=True).start()


def _check(parent):
    try:
        req  = urllib.request.Request(VERSION_URL, headers=_HEADERS)
        resp = urllib.request.urlopen(req, timeout=6)
        data = json.loads(resp.read().decode())

        latest = data.get("version", CURRENT_VERSION)
        url    = data.get("url", "")
        notes  = data.get("notes", "")

        if _is_newer(latest, CURRENT_VERSION) and url:
            parent._update_info = (latest, url, notes)
            parent._trigger_update.emit()

    except Exception as e:
        print(f"[Updater] Erreur : {e}")


def _is_newer(remote, local):
    """Compare deux versions x.y[.z] — supporte 1.10, 1.0.9, etc."""
    try:
        r = tuple(int(x) for x in remote.strip().split("."))
        l = tuple(int(x) for x in local.strip().split("."))
        # Normaliser a la meme longueur
        length = max(len(r), len(l))
        r = r + (0,) * (length - len(r))
        l = l + (0,) * (length - len(l))
        return r > l
    except Exception:
        return False


def download_and_restart(url: str, version: str, on_progress=None):
    """Telecharge le nouvel exe et remplace via .bat."""
    if getattr(sys, "frozen", False):
        current_exe = Path(sys.executable)
    else:
        current_exe = Path(sys.argv[0])

    exe_dir = current_exe.parent
    new_exe = exe_dir / f"_update_{version}.exe"

    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=120) as r:
            total      = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            with open(new_exe, "wb") as f:
                while True:
                    chunk = r.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress and total:
                        on_progress(downloaded / total)
    except Exception as e:
        if new_exe.exists():
            new_exe.unlink()
        raise e

    bat_path    = exe_dir / "_retro_update.bat"
    pid = os.getpid() if hasattr(os, "getpid") else None
    exe_name = current_exe.name
    bat_content = (
        "@echo off\n"
        "chcp 65001 >nul\n"
        # Attendre que le process parent se ferme TOUT SEUL (pas de kill brutal).
        # QTimer.singleShot ferme l'app proprement -> PyInstaller nettoie son _MEI.
        + (f"echo Attente de la fermeture de Retro Toolbox...\n" )
        + ":waitclose\n"
        + (f"tasklist /FI \"PID eq {pid}\" 2>nul | find \"{pid}\" >nul\n" if pid else "")
        + (f"if not errorlevel 1 (\n"
           f"  timeout /t 1 /nobreak >nul\n"
           f"  goto waitclose\n"
           f")\n" if pid else "")
        # Marge supplementaire pour laisser Windows liberer les fichiers du _MEI
        + "timeout /t 2 /nobreak >nul\n"
        # Boucle retry sur le move jusqu'a ce que l'ancien exe soit libere
        + ":retry\n"
        + f"move /y \"{new_exe}\" \"{current_exe}\" >nul 2>&1\n"
        + "if errorlevel 1 (\n"
        + "  timeout /t 1 /nobreak >nul\n"
        + "  goto retry\n"
        + ")\n"
        # Relancer depuis le bon dossier de travail
        + f"cd /d \"{exe_dir}\"\n"
        + f"start \"\" \"{current_exe}\"\n"
        + "del \"%~f0\"\n"
    )
    bat_path.write_text(bat_content, encoding="utf-8")

    subprocess.Popen(
        ["cmd.exe", "/c", str(bat_path)],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    QTimer.singleShot(500, QApplication.instance().quit)
