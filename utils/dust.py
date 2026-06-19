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

def dust_get(path: str, params: dict = None) -> dict:
    """
    Effectue un GET authentifié vers l'API Dust.

    Args:
        path   : chemin de l'endpoint, ex: "/w/abc123/assistant/agent_configurations/xyz"
        params : paramètres query string optionnels, ex: {"variant": "light"}

    Returns:
        dict : le corps JSON complet de la réponse Dust

    Raises:
        RuntimeError : si credentials manquants, si l'API retourne une erreur HTTP,
                       ou si la réponse n'est pas un dictionnaire JSON
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

    # On convertit la réponse JSON en dict Python
    result = r.json()

    # ✅ FIX : guard de type — l'API Dust doit toujours retourner un objet JSON {}
    # Si on reçoit une string, une liste ou autre chose, on lève une erreur lisible
    # au lieu de laisser crasher avec "'str' object has no attribute 'get'"
    if not isinstance(result, dict):
        raise RuntimeError(
            f"GET {path} → Réponse JSON inattendue "
            f"(type reçu : {type(result).__name__}) : {str(result)[:200]}"
        )

    return result
