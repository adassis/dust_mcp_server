# =============================================================
# server.py — Point d'entrée du serveur MCP Dust
# =============================================================
# Pour ajouter un nouvel outil :
#   1. Créer tools/mon_outil.py avec une fonction register(mcp)
#   2. Ajouter import + register() ci-dessous
# =============================================================

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config import PORT, MCP_BEARER_TOKEN

# ── Import de chaque tool (1 fichier = 1 tool) ────────────────
import tools.get_agent_configuration
import tools.list_agent_configurations
import tools.search_agent_by_name
import tools.list_mcp_server_views
import tools.list_skills
import tools.list_agents     


# ── Initialisation ─────────────────────────────────────────────

mcp = FastMCP(
    name="dust-agent-configurations-server",
    host="0.0.0.0",
    port=PORT,
    instructions=(
        "Serveur MCP pour interroger l'API Dust. "
        "TOOLS DISPONIBLES : "
        "1. get_agent_configuration(agent_sid, variant) : détails d'un agent par sId. "
        "2. list_agent_configurations(view, variant) : liste tous les agents. "
        "3. search_agent_by_name(query) : recherche des agents par nom. "
        "4. list_mcp_server_views() : liste les vues de filtrage disponibles. "
        "5. list_skills(status) : liste les skills du workspace. "
        "WORKFLOW : search_agent_by_name ou list_agent_configurations "
        "→ puis get_agent_configuration avec le sId pour les détails."
    )
)


# ── Enregistrement des outils ──────────────────────────────────
# Chaque register(mcp) enregistre le @mcp.tool() de son fichier

tools.get_agent_configuration.register(mcp)
tools.list_agent_configurations.register(mcp)
tools.search_agent_by_name.register(mcp)
tools.list_mcp_server_views.register(mcp)
tools.list_skills.register(mcp)
tools.list_agents.register(mcp)    


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