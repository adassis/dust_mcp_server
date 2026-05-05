import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def search_agent_by_name(query: str) -> str:
        """
        Recherche des agents Dust dont le nom correspond à la requête donnée.
        Insensible à la casse, supporte les correspondances partielles.

        Args:
            query : Terme de recherche (ex: "Customer", "Sales").

        Returns:
            JSON avec total_results et le tableau agentConfigurations.
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations/search"
            data = dust_get(path, params={"q": query})

            agents = data.get("agentConfigurations", [])
            result = {
                "query": query,
                "total_results": len(agents),
                "agentConfigurations": agents
            }

            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "query": query}, ensure_ascii=False)