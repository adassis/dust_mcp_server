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
# ❌ Supprimés : list_agents, get_agent_configuration
# ✅ Ajouté    : get_agent_yaml
import tools.get_agent_yaml              
import tools.search_agent_by_name
import tools.list_mcp_server_views
import tools.list_skills
import tools.get_conversation
import tools.export_analytics
import tools.get_space_mcp_server_views

# ── Initialisation ─────────────────────────────────────────────
mcp = FastMCP(
    name="dust-agent-configurations-server",
    host="0.0.0.0",
    port=PORT,
    instructions=(
        "Serveur MCP pour interroger l'API Dust. "
        "TOOLS DISPONIBLES : "
        "1. get_agent_yaml(agent_sid) : exporte la config complète d'un agent au format YAML. "
        "2. list_agent_configurations(view, variant) : liste tous les agents. "
        "3. search_agent_by_name(query) : recherche des agents par nom. "
        "4. list_mcp_server_views() : liste les vues de filtrage disponibles. "
        "5. list_skills(status) : liste les skills du workspace. "
        "6. export_analytics(table, start_date, end_date, timezone) : exporte les analytiques. "
        "7. get_conversation(conversation_id) : récupère une conversation. "
        "8. get_space_mcp_server_views() : liste les vues MCP server par space. "
        "WORKFLOW RECOMMANDÉ : list_agent_configurations ou search_agent_by_name "
        "→ puis get_agent_yaml avec le sId pour la config complète."
    )
)

# ── Enregistrement des outils ──────────────────────────────────
tools.get_agent_yaml.register(mcp)            
tools.search_agent_by_name.register(mcp)
tools.list_mcp_server_views.register(mcp)
tools.list_skills.register(mcp)
tools.get_conversation.register(mcp)
tools.export_analytics.register(mcp)
tools.get_space_mcp_server_views.register(mcp)

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
