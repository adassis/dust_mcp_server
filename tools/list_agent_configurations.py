# =============================================================
# tools/list_agent_configurations.py
# =============================================================
# Tool MCP : liste tous les agents du workspace Dust
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations
#
# ⚠️ IMPORTANT — vues et agents privés :
#   view=list → inclut les agents privés accessibles à l'utilisateur ✅
#   view=all  → exclut TOUS les agents privés (doc officielle Dust)  ❌
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def list_agent_configurations(
        view: str = "list",
        variant: str = "light"
    ) -> str:
        """
        Liste toutes les configurations d'agents disponibles dans le workspace Dust,
        y compris les agents privés accessibles à l'utilisateur authentifié.

        ⚠️ Choix de la vue et agents privés :
        - "list" (défaut) → retourne TOUS les agents actifs accessibles à l'utilisateur,
          Y COMPRIS les agents privés (scope=private) dont il est propriétaire.
        - "all" → retourne uniquement les agents NON-PRIVÉS (les agents privés
          sont explicitement exclus par l'API Dust avec cette vue).

        Utilise toujours view="list" pour ne rater aucun agent privé.

        Args:
            view    : Filtre de visibilité. Valeurs disponibles :
                      - "list" (défaut) : tous les agents accessibles + privés ✅
                      - "all" : tous les agents non-privés uniquement ❌ privés exclus
                      - "workspace" : agents partagés au niveau workspace
                      - "published" : agents publiés publiquement
                      - "global" : agents système Dust (@dust, @gpt4, etc.)
                      - "favorites" : agents favoris de l'utilisateur
            variant : "light" (défaut) ou "full" pour inclure les actions détaillées.

        Returns:
            JSON avec le tableau agentConfigurations. Chaque agent contient :
            sId, name, description, status, scope (private/workspace/published/global).
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"
            data = dust_get(path, params={"view": view, "variant": variant})

            agents = data.get("agentConfigurations", [])

            # On enrichit la réponse avec le nombre total et un breakdown par scope
            # pour rendre visible la présence d'agents privés
            scope_breakdown = {}
            for agent in agents:
                scope = agent.get("scope", "unknown")
                scope_breakdown[scope] = scope_breakdown.get(scope, 0) + 1

            result = {
                "view_used": view,
                "total_agents": len(agents),
                "scope_breakdown": scope_breakdown,  # ex: {"private": 3, "workspace": 12}
                "agentConfigurations": agents
            }

            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)