import json


def register(mcp):

    @mcp.tool()
    def list_mcp_server_views() -> str:
        """
        Retourne la liste complète des vues (views) disponibles pour interroger
        les agents Dust via l'API MCP.

        Utilise cet outil pour comprendre quels filtres appliquer lors de l'appel
        à list_agent_configurations. Chaque vue correspond à un sous-ensemble
        différent des agents du workspace selon leur scope et leur visibilité.

        Returns:
            JSON avec la liste des vues disponibles, leur description,
            leur cas d'usage, et si elles nécessitent une authentification.
        """
        views = [
            {
                "view": "all",
                "description": "Retourne TOUS les agents non-privés du workspace.",
                "requires_auth": False,
                "use_case": "Vue complète du workspace, utile pour un inventaire."
            },
            {
                "view": "list",
                "description": "Retourne tous les agents actifs accessibles à l'utilisateur authentifié.",
                "requires_auth": True,
                "use_case": "Vue standard pour un utilisateur connecté."
            },
            {
                "view": "workspace",
                "description": "Retourne uniquement les agents dont le scope est 'workspace'.",
                "requires_auth": True,
                "use_case": "Agents créés et partagés à l'échelle du workspace."
            },
            {
                "view": "published",
                "description": "Retourne les agents dont le scope est 'published'.",
                "requires_auth": False,
                "use_case": "Agents rendus publics en dehors du workspace."
            },
            {
                "view": "global",
                "description": "Retourne les agents globaux fournis par Dust (@dust, @gpt4, etc.).",
                "requires_auth": False,
                "use_case": "Agents système disponibles dans tous les workspaces Dust."
            },
            {
                "view": "favorites",
                "description": "Retourne uniquement les agents marqués comme favoris.",
                "requires_auth": True,
                "use_case": "Accès rapide aux agents préférés d'un utilisateur."
            }
        ]

        result = {
            "total_views": len(views),
            "usage": "Passez la valeur 'view' comme paramètre à list_agent_configurations(view=...)",
            "available_views": views
        }

        return json.dumps(result, ensure_ascii=False, indent=2)