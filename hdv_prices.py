"""hdv_prices.py — Client des prix HDV communautaires (Supabase).

Identité sans compte : un UUID aléatoire est généré à la première utilisation
et stocké localement. Le pseudo est figé côté serveur après la première
soumission (impossible à usurper).

Sécurité côté serveur (voir schema.sql) :
  - rate-limit en cascade (UUID + IP + global/item)
  - validation statistique (rejet des prix aberrants)
  - pondération par ancienneté de l'installation
  - signalement communautaire avec seuil de masquage

Le client n'écrit jamais en direct : tout passe par les RPC / Edge Functions.
"""

import json
import uuid as _uuid
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

# ─── Configuration (à remplir avec tes valeurs Supabase) ──────────────
SUPABASE_URL  = "https://nexuircefbgjtjckcskx.supabase.co"
SUPABASE_ANON = "sb_publishable_TAyjavYcUc4IwJEw9lN1tQ_l5q7AZcB"

# Endpoint REST auto-généré + Edge Function pour la soumission
_REST = f"{SUPABASE_URL}/rest/v1"
_RPC  = f"{SUPABASE_URL}/rest/v1/rpc"
_EDGE = f"{SUPABASE_URL}/functions/v1/submit-price"

SERVERS = ("boune", "allisteria", "fallanster")

_HEADERS = {
    "apikey": SUPABASE_ANON,
    "Authorization": f"Bearer {SUPABASE_ANON}",
    "Content-Type": "application/json",
}


# ─── Identité locale (UUID persistant) ────────────────────────────────
def _id_file() -> Path:
    base = Path.home() / ".retro_toolbox"
    base.mkdir(exist_ok=True)
    return base / "install_id.json"


def get_install_id() -> str:
    """Retourne l'UUID de cette installation, le crée si absent."""
    f = _id_file()
    if f.exists():
        try:
            return json.loads(f.read_text())["uuid"]
        except Exception:
            pass
    new_id = str(_uuid.uuid4())
    f.write_text(json.dumps({"uuid": new_id}))
    return new_id


# ─── Appels HTTP ──────────────────────────────────────────────────────
def _post(url: str, payload: dict, timeout: int = 10) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"ok": False, "error": f"http_{e.code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _get(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers=_HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


# ─── API publique ─────────────────────────────────────────────────────
def register(pseudo: str, server: str) -> dict:
    """Enregistre l'installation, ou change le pseudo (1x / 15 jours).

    Retourne {ok, pseudo, changed} ou {ok: False, error: 'pseudo_cooldown',
    retry_after_days: N}.
    """
    if server not in SERVERS:
        return {"ok": False, "error": "server_invalid"}
    return _post(f"{_RPC}/register_install", {
        "p_uuid": get_install_id(),
        "p_pseudo": pseudo,
        "p_server": server,
    })


def change_pseudo(new_pseudo: str, server: str) -> dict:
    """Alias clair pour changer de pseudo (même endpoint que register)."""
    return register(new_pseudo, server)


def get_my_pseudo() -> dict:
    """Récupère le pseudo actuel de cette installation.

    Retourne {ok, pseudo, can_change, days_left} ou {ok: False, error: ...}.
    """
    return _post(f"{_RPC}/get_my_pseudo", {"p_uuid": get_install_id()})


def price_history(server: str, item_id: int, days: int = 30) -> list:
    """Historique des prix : dernier prix par jour sur N jours (7, 15 ou 30).

    Retourne une liste de points : [{jour, x1, x10, x100}, ...].
    """
    if server not in SERVERS:
        return []
    res = _post(f"{_RPC}/price_history", {
        "p_server": server,
        "p_item_id": item_id,
        "p_days": days,
    })
    if isinstance(res, dict) and res.get("ok"):
        return res.get("points", [])
    return []


def price_history(server: str, item_id: int, days: int = 30) -> list:
    """Historique des prix (dernier prix par jour) sur N jours.

    Retourne une liste de {jour, x1, x10, x100} triée par date.
    """
    if server not in SERVERS:
        return []
    res = _post(f"{_RPC}/price_history", {
        "p_server": server,
        "p_item_id": item_id,
        "p_days": days,
    })
    return res if isinstance(res, list) else []


# Mets True si tu as déployé l'Edge Function submit-price (IP réelle, plus sûr).
# Mets False pour appeler directement la RPC (marche sans Edge Function).
USE_EDGE_FUNCTION = False


def submit_price(server: str, item_id: int,
                 price_x1: int, price_x10: int = None,
                 price_x100: int = None) -> dict:
    """Soumet les prix par lot d'un item.

    price_x1 obligatoire ; price_x10 et price_x100 optionnels (None si absent).
    Validation médiane par lot côté serveur.
    """
    if server not in SERVERS:
        return {"ok": False, "error": "server_invalid"}

    payload_rpc = {
        "p_uuid": get_install_id(),
        "p_server": server,
        "p_item_id": item_id,
        "p_price_x1": price_x1,
        "p_price_x10": price_x10,
        "p_price_x100": price_x100,
    }

    if USE_EDGE_FUNCTION:
        return _post(_EDGE, {
            "uuid": get_install_id(),
            "server": server,
            "item_id": item_id,
            "price_x1": price_x1,
            "price_x10": price_x10,
            "price_x100": price_x100,
        })

    import hashlib
    ip_hash = hashlib.sha256(("local|" + get_install_id()).encode()).hexdigest()
    payload_rpc["p_ip_hash"] = ip_hash
    return _post(f"{_RPC}/submit_price", payload_rpc)


def report_price(submission_id: int) -> dict:
    """Signale une soumission suspecte."""
    return _post(f"{_RPC}/report_price", {
        "p_submission_id": submission_id,
        "p_uuid": get_install_id(),
        "p_ip_hash": "",   # l'IP réelle est gérée côté Edge si tu passes par une
    })


def get_settings() -> dict:
    """Récupère les paramètres publics (délais, seuils) depuis la table settings."""
    url = f"{_REST}/settings?select=key,value"
    res = _get(url)
    if isinstance(res, list):
        return {r["key"]: r["value"] for r in res}
    return {}


def get_prices(server: str) -> list:
    """Récupère les prix actuels (médiane) pour un serveur."""
    if server not in SERVERS:
        return []
    url = (f"{_REST}/current_prices"
           f"?server=eq.{server}&select=*&order=item_name.asc")
    res = _get(url)
    return res if isinstance(res, list) else []


def _strip_accents(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def _query_items(filter_part: str, limit: int) -> list:
    """Interroge la table items. Tente avec category, retombe sans si erreur."""
    # 1) avec category
    url = f"{_REST}/items?{filter_part}&select=id,name,category&order=name.asc&limit={limit}"
    res = _get(url)
    if isinstance(res, list):
        return res
    # 2) sans category (si la colonne n'existe pas / 403 sur category)
    url2 = f"{_REST}/items?{filter_part}&select=id,name&order=name.asc&limit={limit}"
    res2 = _get(url2)
    if isinstance(res2, list):
        # ajouter category par défaut pour cohérence côté UI
        for it in res2:
            it.setdefault("category", "resource")
        return res2
    return []


def search_items(query: str, limit: int = 50) -> list:
    """Autocomplete sur la liste d'items connue.

    Recherche insensible à la casse ET aux accents. Résiliente : si la colonne
    category n'est pas exposée, on retombe sur id,name.
    """
    q = query.strip()
    if not q:
        return _query_items("", limit)

    q_slug = _strip_accents(q).lower()
    enc = urllib.parse.quote(f"*{q_slug}*")
    res = _query_items(f"slug=ilike.{enc}", limit)
    if res:
        return res

    # Fallback : recherche directe sur name
    enc2 = urllib.parse.quote(f"*{q}*")
    return _query_items(f"name=ilike.{enc2}", limit)


# ─── Helper d'affichage des erreurs ───────────────────────────────────
def error_message(res: dict) -> str:
    """Traduit un code d'erreur serveur en message français lisible."""
    err = res.get("error", "")
    mapping = {
        "rate_limit_create":     "Tu viens de proposer un prix. Attends un peu avant le prochain.",
        "rate_limit_update":     "Ce prix a déjà été modifié récemment. Réessaie plus tard.",
        "rate_limit_uuid":       "Tu as déjà modifié un prix récemment. Réessaie plus tard.",
        "rate_limit_ip":         "Trop de modifications depuis ta connexion. Patiente un peu.",
        "rate_limit_item_daily": "Cet item a atteint sa limite de modifications du jour.",
        "price_outlier":         "Un de tes prix est trop éloigné du prix actuel — refusé.",
        "install_unknown":       "Installation non reconnue. Enregistre d'abord ton pseudo.",
        "pseudo_invalid":        "Pseudo invalide (2 à 24 caractères).",
        "pseudo_cooldown":       "Tu as déjà changé ton pseudo récemment.",
        "pseudo_taken":          "Ce pseudo est déjà utilisé par un autre joueur. Choisis-en un autre.",
        "server_invalid":        "Serveur invalide.",
        "price_invalid":         "Prix invalide. Le lot ×1 est obligatoire et doit être un nombre positif.",
    }
    # Si code inconnu, l'afficher pour faciliter le diagnostic
    base = mapping.get(err, f"Erreur : {err}" if err else "Une erreur est survenue.")
    # Délai en jours (changement de pseudo)
    if "retry_after_days" in res:
        d = max(1, int(res["retry_after_days"]))
        base += f" (encore {d} jour{'s' if d > 1 else ''})"
    # Délai en minutes (rate-limit prix)
    elif "retry_after" in res:
        secs = int(res["retry_after"])
        if secs >= 3600:
            base += f" (encore ~{secs // 3600}h{(secs % 3600) // 60:02d})"
        else:
            base += f" (encore ~{max(1, secs // 60)} min)"
    return base
