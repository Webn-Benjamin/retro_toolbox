"""updater.py — Vérification mise à jour PySide6."""

import threading, urllib.request, json, webbrowser

CURRENT_VERSION = "1.0.0"
VERSION_URL     = "https://monsite.com/version.json"  # ← à modifier


def check_update_qt(parent=None):
    threading.Thread(target=lambda: _check(parent), daemon=True).start()


def _check(parent):
    try:
        req  = urllib.request.urlopen(VERSION_URL, timeout=4)
        data = json.loads(req.read().decode())
        latest = data.get("version", CURRENT_VERSION)
        url    = data.get("url", "")
        notes  = data.get("notes", "")
        if _is_newer(latest, CURRENT_VERSION):
            from PySide6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                parent, "_show_update",
                Qt.ConnectionType.QueuedConnection,
            )
            parent._update_info = (latest, url, notes)
    except Exception:
        pass


def _is_newer(remote, local):
    try:
        return tuple(int(x) for x in remote.split(".")) > \
               tuple(int(x) for x in local.split("."))
    except Exception:
        return False
