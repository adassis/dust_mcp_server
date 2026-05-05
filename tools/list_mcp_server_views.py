# =============================================================
# tools/list_mcp_server_views.py
# =============================================================
# Tool MCP : retourne les vues disponibles pour interroger les agents
# Mis à jour : clarification sur les agents privés par vue
# Source : https://docs.dust.tt/reference/get_api-v1-w-wid-assistant-agent-configurations
# =============================================================

import json


def register(mcp):

    @mcp.tool()
    def list_mcp_server_views() -> str:
        """
        Retourne la liste complète des vues (views) disponibles pour interroger
        les agents Dust, avec indication explicite du comportement vis-à-vis
        des agents privés (scope=private).

        ⚠️ Point clé sur les agents privés :
        Seule la vue "list" inclut les agents privés accessibles à l'utilisateur.
        La vue "all" les exclut explicitement selon la documentation officielle Dust.

        Returns:
            JSON avec les vues disponibles, leur description et leur compatibilité
            avec les agents privés.
        """
        views = [
            {
                "view": "list",
                "description": (
                    "Retourne TOUS les agents actifs accessibles à l'utilisateur authentifié, "
                    "y compris les agents privés (scope=private) dont il est propriétaire."
                ),
                "includes_private_agents": True,   # ✅ agents privés inclus
                "requires_auth": True,
                "use_case": "Vue recommandée par défaut — ne rate aucun agent.",
                "recommended": True
            },
            {
                "view": "all",
                "description": (
                    "Retourne tous les agents NON-PRIVÉS du workspace. "
                    "Les agents privés (scope=private) sont explicitement exclus "
                    "selon la documentation officielle de l'API Dust."
                ),
                "includes_private_agents": False,  # ❌ agents privés exclus
                "requires_auth": False,
                "use_case": "Inventaire public du workspace, sans les agents privés.",
                "recommended": False
            },
            {
                "view": "workspace",
                "description": "Retourne uniquement les agents dont le scope est 'workspace'.",
                "includes_private_agents": False,  # ❌ scope=private != scope=workspace
                "requires_auth": True,
                "use_case": "Agents créés et partagés à l'échelle du workspace.",
                "recommended": False
            },
            {
                "view": "published",
                "description": "Retourne les agents dont le scope est 'published'.",
                "includes_private_agents": False,  # ❌
                "requires_auth": False,
                "use_case": "Agents publiés publiquement en dehors du workspace.",
                "recommended": False
            },
            {
                "view": "global",
                "description": "Retourne les agents globaux fournis par Dust (@dust, @gpt4, etc.).",
                "includes_private_agents": False,  # ❌
                "requires_auth": False,
                "use_case": "Agents système disponibles dans tous les workspaces Dust.",
                "recommended": False
            },
            {
                "view": "favorites",
                "description": "Retourne uniquement les agents marqués comme favoris par l'utilisateur.",
                "includes_private_agents": True,   # ✅ peut inclure des favoris privés
                "requires_auth": True,
                "use_case": "Accès rapide aux agents préférés d'un utilisateur.",
                "recommended": False
            }
        ]

        result = {
            "total_views": len(views),
            "private_agents_warning": (
                "⚠️ Pour inclure les agents privés, utilisez obligatoirement view='list'. "
                "La vue 'all' exclut explicitement les agents privés (source : doc API Dust)."
            ),
            "usage": "Passez la valeur 'view' comme paramètre à list_agent_configurations(view=...)",
            "available_views": views
        }

        return json.dumps(result, ensure_ascii=False, indent=2)