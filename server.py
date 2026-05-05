# =============================================================
# server.py — Point d'entrée du serveur MCP Dust
# =============================================================
# Pour ajouter un nouvel outil à l'avenir :
#   1. Créer tools/mon_outil.py avec une fonction register(mcp)
#   2. Ajouter import + register() ci-dessous
# =============================================================

import uvicorn  # Le serveur web ASGI qui fait tourner l'app

# FastMCP : le framework qui crée le serveur MCP
from mcp.server.fastmcp import FastMCP

# Pour créer le middleware d'authentification
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Les variables de configuration (port, token MCP)
from config import PORT, MCP_BEARER_TOKEN

# Import du module contenant nos tools Dust
import tools.agent_configurations


# ── Initialisation du serveur MCP ─────────────────────────────

# On crée l'instance FastMCP avec :
# - name : le nom du serveur (affiché dans Dust)
# - host : "0.0.0.0" = accessible depuis n'importe quelle IP (requis pour Railway)
# - port : le port d'écoute (lu depuis la variable d'environnement PORT)
# - instructions : description du serveur pour guider l'agent qui l'utilise
mcp = FastMCP(
    name="dust-agent-configurations-server",
    host="0.0.0.0",
    port=PORT,
    instructions=(
        "Serveur MCP pour interroger l'API Dust. "
        "Outils disponibles : "
        "- get_agent_configuration : récupère la configuration détaillée d'un agent Dust spécifique (nom, instructions, modèle, actions...). "
        "- list_agent_configurations : liste tous les agents disponibles dans le workspace Dust. "
        "Utilisez list_agent_configurations d'abord pour trouver le sId d'un agent, "
        "puis get_agent_configuration pour en obtenir les détails complets."
    )
)


# ── Enregistrement des outils ─────────────────────────────────

# On appelle register(mcp) pour chaque module de tools
# Cette fonction enregistre tous les @mcp.tool() définis dans le fichier
tools.agent_configurations.register(mcp)


# ── Middleware d'authentification ─────────────────────────────

# Ce middleware intercepte TOUTES les requêtes entrantes
# avant qu'elles n'atteignent les tools MCP
class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # On vérifie seulement si un token est configuré
        # (si MCP_BEARER_TOKEN est vide, le serveur est ouvert — à éviter en prod)
        if MCP_BEARER_TOKEN:
            # On récupère le header Authorization de la requête
            auth = request.headers.get("Authorization", "")
            
            # Le format attendu est : "Bearer VOTRE_TOKEN"
            # On vérifie :
            # 1. Que le header commence bien par "Bearer "
            # 2. Que le token après "Bearer " correspond à notre token secret
            if not auth.startswith("Bearer ") or auth[7:].strip() != MCP_BEARER_TOKEN:
                # Token absent ou invalide → on retourne une erreur 401
                return JSONResponse({"error": "Non autorisé"}, status_code=401)
        
        # Token valide (ou pas de token configuré) → on laisse passer la requête
        return await call_next(request)


# ── Démarrage du serveur ──────────────────────────────────────

# Ce bloc ne s'exécute que quand on lance directement "python server.py"
if __name__ == "__main__":
    print(f"🚀 Serveur MCP Dust démarré sur le port {PORT}")
    print(f"🔐 Auth : {'Activée' if MCP_BEARER_TOKEN else 'DÉSACTIVÉE'}")
    
    # On crée l'application ASGI (le serveur web)
    # streamable_http_app() = mode HTTP streaming, requis pour Dust
    app = mcp.streamable_http_app()
    
    # On attache le middleware d'auth à l'application
    app.add_middleware(BearerAuthMiddleware)
    
    # On démarre le serveur uvicorn
    # host="0.0.0.0" = accessible depuis l'extérieur (requis pour Railway)
    # port=PORT = port défini dans les variables d'environnement
    uvicorn.run(app, host="0.0.0.0", port=PORT)