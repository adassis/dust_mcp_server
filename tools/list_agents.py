import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def list_agents() -> str:
        """
        Retourne la liste simplifiée de tous les agents du workspace Dust :
        uniquement le nom et le sId de chaque agent.

        Utilise cet outil pour avoir un aperçu rapide des agents disponibles
        ou pour récupérer un sId avant d'appeler get_agent_configuration.

        Returns:
            JSON avec le nombre total d'agents et un tableau contenant
            pour chaque agent : sId et name uniquement.
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"
            data = dust_get(path, params={"view": "all", "variant": "light"})

            agents_raw = data.get("agentConfigurations", [])

            # On extrait uniquement sId et name — rien d'autre
            agents = [
                {
                    "sId":  agent.get("sId", ""),
                    "name": agent.get("name", "")
                }
                for agent in agents_raw
            ]

            return json.dumps({
                "total": len(agents),
                "agents": agents
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)