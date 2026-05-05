# =============================================================
# tools/get_agent_configuration.py
# =============================================================
# Tool MCP : récupère la configuration d'un agent Dust par sId
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations/{sId}
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def get_agent_configuration(
        agent_sid: str,
        variant: str = "light"
    ) -> str:
        """
        Récupère la configuration complète d'un agent Dust par son identifiant unique (sId).

        Utilise cet outil pour obtenir les détails précis d'un agent :
        son nom, sa description, ses instructions système, le modèle LLM utilisé,
        ses actions/tools configurés, et son statut.

        Args:
            agent_sid : Identifiant unique de l'agent (ex: "7f3a9c2b1e").
                        Récupérable via list_agent_configurations ou search_agent_by_name.
            variant   : Niveau de détail retourné :
                        - "light" (défaut) : infos basiques, sans le détail des actions
                        - "full" : config complète avec toutes les actions/tools de l'agent

        Returns:
            JSON contenant l'objet agentConfiguration avec :
            id, sId, version, name, description, instructions,
            pictureUrl, status, scope, model, actions, maxStepsPerRun.
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations/{agent_sid}"
            data = dust_get(path, params={"variant": variant})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "agent_sid": agent_sid}, ensure_ascii=False)