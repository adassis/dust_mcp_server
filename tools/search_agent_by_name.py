# =============================================================
# tools/search_agent_by_name.py
# =============================================================
# Tool MCP : recherche des agents Dust par nom
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations/search?q=...
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def search_agent_by_name(query: str) -> str:
        """
        Recherche des agents Dust dont le nom correspond à la requête donnée.

        Utilise cet outil quand tu connais (partiellement) le nom d'un agent
        mais pas son sId. La recherche est insensible à la casse et supporte
        les correspondances partielles.

        Exemple : search_agent_by_name("support") retournera tous les agents
        dont le nom contient "support".

        Args:
            query : Terme de recherche pour les noms d'agents (ex: "Customer", "Sales").
                    Doit contenir au moins 1 caractère.

        Returns:
            JSON avec le tableau agentConfigurations des agents correspondants,
            incluant pour chacun : sId, name, description, status, scope.
            Retourne un tableau vide si aucun agent ne correspond.
        """
        try:
            # Le paramètre de recherche s'appelle "q" selon la spec OpenAPI Dust
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations/search"
            data = dust_get(path, params={"q": query})

            # On enrichit la réponse avec le nombre de résultats trouvés
            agent_count = len(data.get("agentConfigurations", []))
            result = {
                "query": query,
                "total_results": agent_count,
                "agentConfigurations": data.get("agentConfigurations", [])
            }

            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "query": query}, ensure_ascii=False)