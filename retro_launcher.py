"""retro_launcher.py — Launcher permanent de Retro Toolbox.

Ce fichier ne change JAMAIS après installation.
Il est le seul point d'entrée de l'application (raccourci bureau).

Rôle :
  1. Appliquer une mise à jour en attente (_retro_toolbox_new.exe → retro_toolbox.exe)
  2. Nettoyer les fichiers résiduels (.old, .flag)
  3. Lancer retro_toolbox.exe
"""

import sys
import os
import shutil
import subprocess
import time
from pathlib import Path


# Dossier d'installation : %LocalAppData%\RetroToolbox\
INSTALL_DIR  = Path(os.environ.get("LOCALAPPDATA", "")) / "RetroToolbox"
LAUNCHER_EXE = INSTALL_DIR / "retro_toolbox.exe"
APP_EXE      = INSTALL_DIR / "retro_toolbox_app.exe"
NEW_EXE      = INSTALL_DIR / "_retro_toolbox_new.exe"
OLD_EXE      = INSTALL_DIR / "retro_toolbox_app.exe.old"


def apply_update():
    """Si un nouvel exe est prêt, le substituer à l'ancien. Simple et atomique."""
    if not NEW_EXE.exists():
        return

    # Renommer l'ancien en .old
    try:
        if APP_EXE.exists():
            APP_EXE.rename(OLD_EXE)
    except Exception:
        return  # ne jamais bloquer le lancement

    # Déplacer le nouveau à la place
    try:
        shutil.move(str(NEW_EXE), str(APP_EXE))
    except Exception:
        # Restaurer si le move échoue
        if OLD_EXE.exists() and not APP_EXE.exists():
            OLD_EXE.rename(APP_EXE)
        return

    # Nettoyage du .old (le launcher n'est pas verrouillé, ça marche toujours)
    try:
        OLD_EXE.unlink(missing_ok=True)
    except Exception:
        pass


def cleanup():
    """Supprimer les fichiers résiduels de mises à jour précédentes."""
    for f in (OLD_EXE, NEW_EXE):
        try:
            f.unlink(missing_ok=True)
        except Exception:
            pass


def launch_app():
    """Lancer retro_toolbox_app.exe via ShellExecuteW — contourne les blocages antivirus."""
    if not APP_EXE.exists():
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Fichier introuvable :\n{APP_EXE}\n\nRéinstallez l'application.",
            "Retro Toolbox — Erreur",
            0x10  # MB_ICONERROR
        )
        sys.exit(1)

    import ctypes
    ret = ctypes.windll.shell32.ShellExecuteW(
        None,
        "open",
        str(APP_EXE),
        None,
        str(INSTALL_DIR),
        1,
    )
    if ret <= 32:
        # Bloqué par l'antivirus — afficher un message explicatif
        ctypes.windll.user32.MessageBoxW(
            0,
            'Retro Toolbox a été bloqué par votre antivirus (faux positif).\n\nPour résoudre :\n\n1. Ouvrez Sécurité Windows\n2. Protection contre les virus > Gérer les paramètres\n3. Exclusions > Ajouter une exclusion > Dossier\n4. Collez : %LocalAppData%\\RetroToolbox\n5. Relancez Retro Toolbox\n\nSupport : discord.com/invite/Md8RJXdtQZ',
            "Retro Toolbox - Antivirus",
            0x10
        )
        sys.exit(1)


def main():
    apply_update()
    cleanup()
    launch_app()


if __name__ == "__main__":
    main()
