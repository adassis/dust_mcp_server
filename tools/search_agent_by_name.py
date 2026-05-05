# =============================================================
# tools/search_agent_by_name.py
# =============================================================
# Tool MCP : recherche des agents Dust par nom
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations/search?q=...
#
# ⚠️ La recherche porte sur tous les agents accessibles à l'utilisateur
#    authentifié, y compris les agents privés (scope=private).
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def search_agent_by_name(query: str) -> str:
        """
        Recherche des agents Dust dont le nom correspond à la requête donnée.
        La recherche inclut les agents privés (scope=private) accessibles
        à l'utilisateur authentifié.

        Utilise cet outil quand tu connais (partiellement) le nom d'un agent
        mais pas son sId. La recherche est insensible à la casse et supporte
        les correspondances partielles.

        Exemple : search_agent_by_name("support") retournera tous les agents
        dont le nom contient "support", privés inclus.

        Args:
            query : Terme de recherche (ex: "Customer", "Sales", "Internal").
                    Doit contenir au moins 1 caractère.

        Returns:
            JSON avec :
            - query : le terme recherché
            - total_results : nombre d'agents trouvés
            - scope_breakdown : répartition par scope (private/workspace/etc.)
            - agentConfigurations : tableau des agents correspondants
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations/search"
            data = dust_get(path, params={"q": query})

            agents = data.get("agentConfigurations", [])

            # Breakdown par scope pour rendre visible les agents privés trouvés
            scope_breakdown = {}
            for agent in agents:
                scope = agent.get("scope", "unknown")
                scope_breakdown[scope] = scope_breakdown.get(scope, 0) + 1

            result = {
                "query": query,
                "total_results": len(agents),
                "scope_breakdown": scope_breakdown,
                "agentConfigurations": agents
            }

            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "query": query}, ensure_ascii=False)