"""os_bridge/focus_assist.py — Détection du mode "Ne pas déranger" / Assistant
de concentration Windows, qui peut empêcher l'app de recevoir les notifications
système (tour de jeu, échange, etc. lues via toast_reader.py).
"""
from __future__ import annotations
import sys

try:
    import winreg
    _OK = sys.platform == "win32"
except ImportError:
    _OK = False


def is_notifications_disabled() -> bool:
    """Retourne True si les notifications Windows sont globalement coupées
    (toggle "Notifications" dans Paramètres > Système)."""
    if not _OK:
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications",
        )
        value, _ = winreg.QueryValueEx(key, "ToastEnabled")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False


def _read_noc_toasts_enabled() -> int | None:
    """Lit la clé NOC_GLOBAL_SETTING_TOASTS_ENABLED, qui reflète l'état du
    mode Ne pas déranger / Assistant de concentration (documentée par
    Microsoft sous Notifications\\Settings). 1 = notifications visibles,
    0 = masquées par le mode Ne pas déranger."""
    if not _OK:
        return None
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings",
        )
        value, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED")
        winreg.CloseKey(key)
        return int(value)
    except Exception:
        return None


# Chemins de registre du blob binaire (méthode héritée, gardée en fallback
# secondaire pour les configurations où la clé NOC ci-dessus serait absente).
_REGISTRY_BLOB_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache"
    r"\DefaultAccount\Current\windows.data.notifications.quiethourssettings\Current",
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache"
    r"\DefaultAccount\Current\windows.data.notifications.quiethourssettings"
    r"\windows.data.notifications.quiethourssettings",
]


def _read_quiet_hours_blob() -> bytes | None:
    if not _OK:
        return None
    for path in _REGISTRY_BLOB_PATHS:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
            raw, _ = winreg.QueryValueEx(key, "Data")
            winreg.CloseKey(key)
            if raw:
                return raw
        except Exception:
            continue
    return None


def _read_quiethours_service_state() -> int | None:
    """Lit QuietHoursServiceState sous Notifications\\QuietHours — clé
    découverte empiriquement qui reflète l'état réel du service Ne pas
    déranger sur cette machine. 0 = inactif, toute autre valeur = actif."""
    if not _OK:
        return None
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\QuietHours",
        )
        value, _ = winreg.QueryValueEx(key, "QuietHoursServiceState")
        winreg.CloseKey(key)
        return int(value)
    except Exception:
        return None


def is_focus_assist_active() -> bool:
    """Détecte si le mode "Ne pas déranger" / Assistant de concentration
    Windows est actif. Priorité à QuietHoursServiceState (clé fiable
    identifiée empiriquement), puis NOC_GLOBAL_SETTING_TOASTS_ENABLED,
    puis le blob binaire en dernier recours."""
    state = _read_quiethours_service_state()
    if state is not None:
        return state != 0

    noc = _read_noc_toasts_enabled()
    if noc is not None:
        return noc == 0

    raw = _read_quiet_hours_blob()
    if not raw or len(raw) < 19:
        return False
    try:
        return raw[18] != 0
    except IndexError:
        return False


def is_dnd_active() -> bool:
    """Vrai si l'une des détections indique que les notifications de l'app
    risquent d'être masquées par Windows."""
    return is_notifications_disabled() or is_focus_assist_active()


def open_notification_settings() -> bool:
    """Ouvre directement le panneau Paramètres Windows des notifications."""
    if sys.platform != "win32":
        return False
    try:
        import os
        os.startfile("ms-settings:notifications")
        return True
    except Exception:
        return False
