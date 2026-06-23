# =============================================================
# utils/dust.py — Client HTTP Dust centralisé
# =============================================================
# Toutes les fonctions d'appel à l'API Dust passent ici.
# Gère automatiquement :
# - l'URL de base
# - l'authentification via Bearer token (clé API Dust)
# - les erreurs HTTP
# =============================================================

import requests  # Pour faire des requêtes HTTP

# On importe les credentials depuis config.py
from config import DUST_API_KEY, DUST_WORKSPACE_ID

# L'URL de base de l'API Dust — toutes les requêtes partent de là
BASE_URL = "https://dust.tt/api/v1"

def _check_credentials():
    """
    Vérifie que la clé API et le workspace ID sont bien configurés.
    Si ce n'est pas le cas, on lève une erreur claire plutôt que
    d'avoir un message cryptique plus tard.
    """
    if not DUST_API_KEY or not DUST_WORKSPACE_ID:
        raise RuntimeError(
            "DUST_API_KEY ou DUST_WORKSPACE_ID non configurés. "
            "Vérifiez vos variables d'environnement sur Railway."
        )

# ✅ FIX : le type de retour passe de "-> dict" à "-> dict | list"
# car l'API Dust retourne une liste [] pour certains endpoints
# (ex: /analytics/export?table=messages retourne un tableau de messages)
def dust_get(path: str, params: dict = None) -> dict | list:
    """
    Effectue un GET authentifié vers l'API Dust.

    Args:
        path   : chemin de l'endpoint, ex: "/w/abc123/assistant/agent_configurations/xyz"
        params : paramètres query string optionnels, ex: {"variant": "light"}

    Returns:
        dict ou list : le corps JSON complet de la réponse Dust
        (dict pour la majorité des endpoints, list pour analytics/export?table=messages)

    Raises:
        RuntimeError : si credentials manquants, si l'API retourne une erreur HTTP,
                       ou si la réponse n'est ni un dict ni une list
    """
    # On vérifie d'abord que les credentials sont bien présents
    _check_credentials()

    headers = {
        "Authorization": f"Bearer {DUST_API_KEY}",  # Format obligatoire : "Bearer VOTRE_CLE"
        "Accept": "application/json"                 # On dit qu'on veut du JSON en retour
    }

    r = requests.get(
        BASE_URL + path,
        headers=headers,
        params=params or {},  # Si params est None, on passe un dict vide
        timeout=30
    )

    # r.ok = True si le code HTTP est entre 200 et 299 (succès)
    if not r.ok:
        raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")

    # On convertit la réponse JSON en dict ou list Python
    result = r.json()

    # ✅ FIX : guard de type étendu — on accepte maintenant dict {} ET list []
    # Avant : isinstance(result, dict)  → rejetait les listes (ex: table=messages)
    # Après : isinstance(result, (dict, list)) → accepte les deux formats
    # On rejette uniquement les types vraiment inattendus (str, int, None, etc.)
    if not isinstance(result, (dict, list)):
        raise RuntimeError(
            f"GET {path} → Réponse JSON inattendue "
            f"(type reçu : {type(result).__name__}) : {str(result)[:200]}"
        )

    return result

def dust_get_text(path: str, accept: str = "text/plain", params: dict = None) -> str:
    """
    GET authentifié → retourne le contenu brut en texte.

    Utilisé pour les endpoints qui ne retournent PAS du JSON,
    comme /export/yaml qui retourne un fichier YAML en texte brut.

    Args:
        path   : chemin de l'endpoint
        accept : type MIME attendu ("text/yaml", "text/plain", etc.)
        params : paramètres query string optionnels

    Returns:
        str : le contenu texte brut de la réponse

    Raises:
        RuntimeError : si credentials manquants ou erreur HTTP
    """
    _check_credentials()

    headers = {
        "Authorization": f"Bearer {DUST_API_KEY}",
        "Accept": accept  # "text/yaml" pour l'export YAML
    }

    r = requests.get(
        BASE_URL + path,
        headers=headers,
        params=params or {},
        timeout=30
    )

    if not r.ok:
        raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")

    # On retourne le texte brut — pas r.json() !
    return r.text

def dust_patch(path: str, body: dict) -> dict:
    """
    PATCH authentifié → envoie un body JSON partiel et retourne un dict JSON.

    Utilisé pour les mises à jour partielles (seuls les champs envoyés
    sont modifiés, les autres restent inchangés).

    Args:
        path : chemin de l'endpoint
        body : dict Python représentant le body JSON à envoyer

    Returns:
        dict : la réponse JSON de l'API Dust

    Raises:
        RuntimeError : si credentials manquants, erreur HTTP ou réponse non-dict
    """
    _check_credentials()

    headers = {
        "Authorization": f"Bearer {DUST_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    r = requests.patch(
        BASE_URL + path,
        headers=headers,
        json=body,  # requests sérialise automatiquement le dict en JSON
        timeout=30
    )

    if not r.ok:
        raise RuntimeError(f"PATCH {path} → HTTP {r.status_code}: {r.text[:400]}")

    result = r.json()

    if not isinstance(result, dict):
        raise RuntimeError(
            f"PATCH {path} → Réponse inattendue "
            f"(type: {type(result).__name__}) : {str(result)[:200]}"
        )

    return result

def dust_post(path: str, body: dict) -> dict:
    """
    POST authentifié → envoie un body JSON complet et retourne un dict JSON.

    Utilisé pour la création de ressources (nouveaux agents, etc.).
    Contrairement à PATCH, POST crée une nouvelle ressource.

    Args:
        path : chemin de l'endpoint, ex: "/w/abc123/assistant/agent_configurations/import"
        body : dict Python représentant le body JSON complet à envoyer

    Returns:
        dict : la réponse JSON de l'API Dust

    Raises:
        RuntimeError : si credentials manquants, erreur HTTP ou réponse non-dict
    """
    _check_credentials()

    headers = {
        "Authorization": f"Bearer {DUST_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    r = requests.post(
        BASE_URL + path,
        headers=headers,
        json=body,  # requests sérialise automatiquement le dict en JSON
        timeout=30
    )

    if not r.ok:
        raise RuntimeError(f"POST {path} → HTTP {r.status_code}: {r.text[:400]}")

    result = r.json()

    if not isinstance(result, dict):
        raise RuntimeError(
            f"POST {path} → Réponse inattendue "
            f"(type: {type(result).__name__}) : {str(result)[:200]}"
        )

    return result
