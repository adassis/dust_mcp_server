# =============================================================
# tools/list_agent_configurations.py
# =============================================================
# Tool MCP : liste tous les agents du workspace Dust
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations
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
        Liste toutes les configurations d'agents disponibles dans le workspace Dust.

        Utilise cet outil pour découvrir quels agents existent et récupérer leurs sId
        (nécessaires pour get_agent_configuration ou search_agent_by_name).

        Args:
            view    : Filtre de visibilité des agents (voir list_mcp_server_views
                      pour la liste complète). Valeurs principales :
                      - "list" (défaut) : tous les agents actifs accessibles
                      - "all" : tous les agents non-privés
                      - "workspace" : agents partagés au niveau workspace
                      - "published" : agents publiés publiquement
                      - "global" : agents système fournis par Dust
                      - "favorites" : agents marqués comme favoris
            variant : "light" (défaut) ou "full" pour inclure les actions détaillées.

        Returns:
            JSON avec le tableau agentConfigurations contenant tous les agents correspondants.
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"
            data = dust_get(path, params={"view": view, "variant": variant})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)