import json


def register(mcp):

    @mcp.tool()
    def list_mcp_server_views() -> str:
        """
        Retourne la liste des vues disponibles pour interroger les agents Dust
        via clé API (sans OAuth).

        Returns:
            JSON avec les vues disponibles et leur description.
        """
        views = [
            {
                "view": "all",
                "description": "Tous les agents non-privés du workspace.",
                "use_case": "Vue par défaut recommandée avec une clé API."
            },
            {
                "view": "workspace",
                "description": "Agents dont le scope est 'workspace'.",
                "use_case": "Agents partagés à l'échelle du workspace."
            },
            {
                "view": "published",
                "description": "Agents publiés publiquement.",
                "use_case": "Agents partageables hors workspace."
            },
            {
                "view": "global",
                "description": "Agents globaux Dust (@dust, @gpt4, etc.).",
                "use_case": "Agents système disponibles dans tous les workspaces."
            },
            {
                "view": "list",
                "description": "❌ Requiert OAuth — non compatible clé API.",
                "use_case": "Non disponible avec une clé API."
            },
            {
                "view": "favorites",
                "description": "❌ Requiert OAuth — non compatible clé API.",
                "use_case": "Non disponible avec une clé API."
            }
        ]

        return json.dumps({
            "total_views": len(views),
            "available_views": views
        }, ensure_ascii=False, indent=2)