# =============================================================
# tools/list_agent_configurations.py
# =============================================================
# Tool MCP : liste toutes les configurations d'agents du workspace
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations
# Doc : https://docs.dust.tt/reference/get_api-v1-w-wid-assistant-agent-configurations
# =============================================================

import json
from typing import Optional
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):
    """
    Enregistre le tool 'list_agent_configurations' dans le serveur MCP.
    Cette fonction est appelée une seule fois au démarrage, dans server.py.
    """

    @mcp.tool()
    def list_agent_configurations(
        view: Optional[str] = "all",
        with_authors: Optional[bool] = False,
    ) -> str:
        """
        Liste toutes les configurations d'agents du workspace Dust.

        Utilise cet outil pour obtenir la liste complète des agents disponibles
        avec leurs métadonnées (nom, description, scope, modèle, statut...).

        Args:
            view : Filtre sur la visibilité des agents. Valeurs possibles :
                - "all"        : Tous les agents non-privés (défaut)
                - "list"       : Agents actifs accessibles à l'utilisateur
                - "workspace"  : Agents de scope workspace uniquement
                - "published"  : Agents publiés uniquement
                - "global"     : Agents globaux uniquement
                - "favorites"  : Agents marqués comme favoris par l'utilisateur

            with_authors : Si True, inclut les informations sur les auteurs récents
                           de chaque agent (champ lastAuthors).

        Returns:
            JSON contenant :
            - total        : nombre total d'agents retournés
            - view         : le filtre utilisé
            - agentConfigurations : tableau des configurations d'agents
        """

        VALID_VIEWS = ["all", "list", "workspace", "published", "global", "favorites"]

        if view not in VALID_VIEWS:
            return json.dumps({
                "error": f"Vue invalide : '{view}'.",
                "views_disponibles": VALID_VIEWS
            }, ensure_ascii=False, indent=2)

        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"

            params = {
                "view": view,
                "withAuthors": "true" if with_authors else "false",
            }

            data = dust_get(path, params=params)

            agents = data.get("agentConfigurations", [])

            result = {
                "total": len(agents),
                "view": view,
                "agentConfigurations": agents,
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "view": view
            }, ensure_ascii=False)
