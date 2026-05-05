import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def list_agent_configurations(
        view: str = "all",
        variant: str = "light"
    ) -> str:
        """
        Liste les agents du workspace Dust accessibles via clé API.

        Args:
            view    : "all" (défaut) · "workspace" · "published" · "global"
                      ⚠️ "list" et "favorites" requièrent OAuth — incompatible clé API
            variant : "light" (défaut) ou "full"

        Returns:
            JSON avec le tableau agentConfigurations.
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"
            data = dust_get(path, params={"view": view, "variant": variant})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)