import sys as _sys
if _sys.platform == "darwin":
    import ssl as _ssl
    try:
        import certifi as _certifi
        _ssl._create_default_https_context = lambda: _ssl.create_default_context(
            cafile=_certifi.where())
    except ImportError:
        _ssl._create_default_https_context = _ssl._create_unverified_context

"""updater.py — Mise à jour automatique via retro_launcher.exe.

Architecture :
  - retro_launcher.exe  : launcher permanent, fait le remplacement au démarrage
  - retro_toolbox.exe   : la vraie app, télécharge juste le nouvel exe et quitte

  1. retro_toolbox.exe télécharge _retro_toolbox_new.exe dans INSTALL_DIR
  2. retro_toolbox.exe quitte (QApplication.quit())
  3. retro_launcher.exe détecte _retro_toolbox_new.exe au prochain lancement
  4. retro_launcher.exe fait le remplacement et lance le nouvel exe

Aucun --apply-update, aucun _MEI conflit, aucun bricolage.
"""

import sys
import os
import hashlib
import threading
import subprocess
import urllib.request
import json
from pathlib import Path

CURRENT_VERSION = "2.1"
VERSION_URL     = "https://retro-toolbox.fr/version.json"
NEW_EXE_NAME    = "_retro_toolbox_new.exe"  # installé par le launcher sous retro_toolbox_app.exe

# Dossier d'installation (même que le launcher)
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "RetroToolbox"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Vérifier s'il existe une nouvelle version ──────────────────────────

def check_update_qt(parent=None):
    threading.Thread(target=lambda: _check(parent), daemon=True).start()


def _check(parent):
    try:
        req  = urllib.request.Request(VERSION_URL, headers=_HEADERS)
        data = json.loads(urllib.request.urlopen(req, timeout=6).read().decode())
        latest = data.get("version", CURRENT_VERSION)
        url    = data.get("url", "")
        notes  = data.get("notes", "")
        sha256 = data.get("sha256", "")
        if _is_newer(latest, CURRENT_VERSION) and url:
            parent._update_info = (latest, url, notes, sha256)
            parent._trigger_update.emit()
    except Exception as e:
        print(f"[Updater] Erreur : {e}")


def _is_newer(remote, local):
    try:
        r = tuple(int(x) for x in remote.strip().split("."))
        l = tuple(int(x) for x in local.strip().split("."))
        n = max(len(r), len(l))
        return r + (0,) * (n - len(r)) > l + (0,) * (n - len(l))
    except Exception:
        return False


# ── Téléchargement ─────────────────────────────────────────────────────

def download_update(url: str, sha256: str = "", on_progress=None) -> Path:
    """Télécharge le nouvel exe dans INSTALL_DIR."""
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    new_exe = INSTALL_DIR / NEW_EXE_NAME
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=120) as r:
            total, done = int(r.headers.get("Content-Length", 0)), 0
            hasher = hashlib.sha256() if sha256 else None
            with open(new_exe, "wb") as f:
                while chunk := r.read(8192):
                    f.write(chunk)
                    if hasher:
                        hasher.update(chunk)
                    done += len(chunk)
                    if on_progress:
                        if total:
                            on_progress(done / total)
                        else:
                            on_progress(min(0.95, done / (5 * 1024 * 1024)))

        if on_progress:
            on_progress(1.0)

        size = new_exe.stat().st_size
        if size == 0 or (total and size != total):
            raise IOError("Téléchargement incomplet — réessaie.")
        if size < 1_000_000:
            raise IOError("Fichier téléchargé invalide.")
        if sha256 and hasher and hasher.hexdigest().lower() != sha256.lower():
            raise IOError("Fichier corrompu (signature invalide) — mise à jour annulée.")

    except Exception:
        new_exe.unlink(missing_ok=True)
        raise

    return new_exe


# ── Déclenchement du redémarrage ───────────────────────────────────────

def apply_pending_update() -> bool:
    """Quitter proprement — le launcher fera le remplacement au prochain lancement."""
    new_exe = INSTALL_DIR / NEW_EXE_NAME
    if not new_exe.exists():
        return False

    # Relancer via le launcher qui s'occupera du remplacement
    launcher = INSTALL_DIR / "retro_toolbox.exe"
    if launcher.exists():
        subprocess.Popen(
            [str(launcher)],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
            cwd=str(INSTALL_DIR),
        )
    return True
