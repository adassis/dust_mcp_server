# =============================================================
# utils/dust.py — Client HTTP Dust centralisé
# =============================================================
# Toutes les fonctions d'appel à l'API Dust passent ici.
# Gère automatiquement :
#   - l'URL de base
#   - l'authentification via Bearer token (clé API Dust)
#   - les erreurs HTTP
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
    
    Le underscore devant le nom (_check) indique que c'est une 
    fonction "privée" — utilisée uniquement dans ce fichier.
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
        RuntimeError : si credentials manquants ou si l'API retourne une erreur HTTP
    """
    # On vérifie d'abord que les credentials sont bien présents
    _check_credentials()
    
    # L'API Dust utilise un Bearer token dans le header Authorization
    # C'est différent de Pipedrive qui passait le token en query string
    headers = {
        "Authorization": f"Bearer {DUST_API_KEY}",  # Format obligatoire : "Bearer VOTRE_CLE"
        "Accept": "application/json"                  # On dit qu'on veut du JSON en retour
    }
    
    # On fait la requête GET
    # - BASE_URL + path = URL complète
    # - headers = authentification
    # - params = paramètres optionnels (ex: variant=light)
    # - timeout=30 = on abandonne si pas de réponse après 30 secondes
    r = requests.get(
        BASE_URL + path,
        headers=headers,
        params=params or {},  # Si params est None, on passe un dict vide
        timeout=30
    )
    
    # r.ok = True si le code HTTP est entre 200 et 299 (succès)
    # r.ok = False si erreur (400, 401, 404, 500, etc.)
    if not r.ok:
        # On lève une erreur avec le code HTTP et le début du message d'erreur
        # r.text[:400] = les 400 premiers caractères de la réponse (pour éviter les messages trop longs)
        raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")
    
    # On convertit la réponse JSON en dict Python et on la retourne
    return r.json()

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
        "Content-Type" : "application/json",
        "Accept"       : "application/json"
    }

    r = requests.post(
        BASE_URL + path,
        headers=headers,
        json=body,      # requests sérialise automatiquement le dict en JSON
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
