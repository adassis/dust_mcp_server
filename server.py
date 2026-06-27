# =============================================================
# server.py — Point d'entrée du serveur MCP Dust
# =============================================================
# Pour ajouter un nouvel outil :
# 1. Créer tools/mon_outil.py avec une fonction register(mcp)
# 2. Ajouter import + register() ci-dessous
# =============================================================

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config import PORT, MCP_BEARER_TOKEN

# ── Import de chaque tool (1 fichier = 1 tool) ────────────────
import tools.get_agent_yaml
import tools.search_agent_by_name
import tools.list_skills
import tools.get_conversation
import tools.export_analytics
import tools.get_space_mcp_server_views
import tools.update_agent_configuration
import tools.create_agent_from_yaml
import tools.add_mcp_server_to_agent
import tools.list_agent_configurations

# ── Initialisation ─────────────────────────────────────────────
mcp = FastMCP(
    name="dust-agent-configurations-server",
    host="0.0.0.0",
    port=PORT,
    instructions=(
        "Serveur MCP pour interroger et gérer l'API Dust. "
        "TOOLS DISPONIBLES : "
        "1. get_agent_yaml(agent_sid) : exporte la config complète d'un agent au format YAML. "
        "2. search_agent_by_name(query) : recherche des agents par nom. "
        "3. list_mcp_server_views() : liste les vues de filtrage disponibles (all, workspace, published...). "
        "4. list_skills(status) : liste les skills du workspace. "
        "5. export_analytics(table, start_date, end_date, timezone) : exporte les analytiques. "
        "6. get_conversation(conversation_id) : récupère une conversation. "
        "7. get_space_mcp_server_views() : liste les serveurs MCP de l'espace workspace "
        "(aucun paramètre requis — spaceId configuré dans config.py). "
        "Retourne les sId (mcpServerViewId) des outils Dust natifs. "
        "8. update_agent_configuration(agent_sid, ...) : modifie la configuration d'un agent existant "
        "(instructions, modèle, temperature, reasoning_effort, skills, toolset, tags). "
        "LIMITE : toolset_json ne supporte que les serveurs MCP internes. "
        "Pour les serveurs remote, utiliser add_mcp_server_to_agent. "
        "9. create_agent_from_yaml(yaml_content) : crée un nouvel agent Dust depuis un YAML. "
        "Utiliser pour créer from scratch ou cloner un agent existant. "
        "10. add_mcp_server_to_agent(agent_sid, mcp_server_view_id, ...) : "
        "ajoute un serveur MCP remote OU interne à un agent via la route privée Dust. "
        "Utiliser quand update_agent_configuration échoue sur un serveur remote (ex: Aircall). "
        "WORKFLOW RECOMMANDÉ : search_agent_by_name → get_agent_yaml → "
        "update_agent_configuration ou add_mcp_server_to_agent ou create_agent_from_yaml."
        "11. list_agent_configurations(view, with_authors) : liste toutes les configurations d'agents du workspace. "
        "Paramètre view : all (défaut), list, workspace, published, global, favorites. "
    )
)

# ── Enregistrement des outils ──────────────────────────────────
tools.get_agent_yaml.register(mcp)
tools.search_agent_by_name.register(mcp)
tools.list_skills.register(mcp)
tools.get_conversation.register(mcp)
tools.export_analytics.register(mcp)
tools.get_space_mcp_server_views.register(mcp)
tools.update_agent_configuration.register(mcp)
tools.create_agent_from_yaml.register(mcp)
tools.add_mcp_server_to_agent.register(mcp)
tools.list_agent_configurations.register(mcp)

# ── Middleware d'authentification ──────────────────────────────
class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if MCP_BEARER_TOKEN:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or auth[7:].strip() != MCP_BEARER_TOKEN:
                return JSONResponse({"error": "Non autorisé"}, status_code=401)
        return await call_next(request)

# ── Démarrage ──────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Serveur MCP Dust démarré sur le port {PORT}")
    print(f"🔐 Auth : {'Activée' if MCP_BEARER_TOKEN else 'DÉSACTIVÉE'}")
    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
