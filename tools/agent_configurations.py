# =============================================================
# tools/agent_configurations.py — Outils MCP : Agents Dust
# =============================================================
# 2 outils exposés :
#   - get_agent_configuration  : récupère la config d'un agent par son sId
#   - list_agent_configurations : liste tous les agents du workspace
#
# API : https://dust.tt/api/v1/w/{wId}/assistant/agent_configurations/{sId}
# =============================================================

import json  # Pour convertir les données Python en texte JSON

# On importe le client HTTP depuis utils/dust.py
from utils.dust import dust_get

# On importe le Workspace ID depuis config.py
# (il est nécessaire pour construire l'URL de l'API)
from config import DUST_WORKSPACE_ID


def register(mcp):
    """
    Fonction appelée depuis server.py pour enregistrer les tools dans FastMCP.
    Le paramètre 'mcp' est l'instance du serveur FastMCP créée dans server.py.
    """

    # ── Tool 1 : Récupérer un agent spécifique ────────────────
    
    @mcp.tool()  # Ce décorateur dit à FastMCP "cette fonction est un tool MCP"
    def get_agent_configuration(
        agent_sid: str,          # Paramètre obligatoire : l'ID de l'agent
        variant: str = "light"   # Paramètre optionnel : "light" ou "full"
    ) -> str:  # Le tool retourne toujours une chaîne de caractères (JSON en string)
        """
        Récupère la configuration complète d'un agent Dust par son identifiant.
        
        Utilise cet outil pour connaître les détails d'un agent spécifique :
        son nom, sa description, ses instructions, le modèle utilisé,
        ses actions/tools configurés, et son statut.
        
        Args:
            agent_sid : Identifiant unique de l'agent Dust (ex: "7f3a9c2b1e").
                        Se trouve dans l'URL de l'agent dans Dust.
            variant   : Niveau de détail de la réponse :
                        - "light" (défaut) : informations basiques sans les actions
                        - "full" : configuration complète avec toutes les actions/tools
        
        Returns:
            JSON avec la configuration de l'agent, incluant :
            - id, sId : identifiants de l'agent
            - name : nom de l'agent
            - description : description de l'agent
            - instructions : le "system prompt" de l'agent
            - model : le modèle LLM utilisé (ex: claude-3-5-sonnet)
            - status : "active" ou inactif
            - actions : les tools configurés (seulement si variant="full")
        """
        try:
            # Construction de l'URL de l'endpoint
            # DUST_WORKSPACE_ID est lu depuis config.py (variable d'environnement Railway)
            # agent_sid est passé par l'agent lors de l'appel au tool
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations/{agent_sid}"
            
            # On passe variant comme paramètre query string
            # L'URL finale sera : .../agent_configurations/xyz?variant=light
            data = dust_get(path, params={"variant": variant})
            
            # On convertit le dict Python en string JSON formatée
            # ensure_ascii=False → conserve les accents et caractères spéciaux
            # indent=2 → indentation pour une meilleure lisibilité
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        except Exception as e:
            # En cas d'erreur, on retourne un JSON d'erreur
            # plutôt que de faire planter le serveur
            return json.dumps(
                {"error": str(e), "agent_sid": agent_sid},
                ensure_ascii=False
            )

    # ── Tool 2 : Lister tous les agents du workspace ──────────
    
    @mcp.tool()
    def list_agent_configurations(variant: str = "light") -> str:
        """
        Liste toutes les configurations d'agents disponibles dans le workspace Dust.
        
        Utilise cet outil pour découvrir quels agents existent dans le workspace
        et obtenir leurs sId (nécessaires pour get_agent_configuration).
        
        Args:
            variant : "light" (défaut) → liste basique de tous les agents
                      "full" → liste complète avec toutes les actions de chaque agent
        
        Returns:
            JSON avec la liste des agents du workspace et leurs informations principales.
        """
        try:
            # URL sans le /{sId} → retourne tous les agents du workspace
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"
            
            data = dust_get(path, params={"variant": variant})
            
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)