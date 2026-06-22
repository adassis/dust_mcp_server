# =============================================================
# tools/get_space_mcp_server_views.py
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID, DUST_SPACE_ID

def register(mcp):

    @mcp.tool()
    def get_space_mcp_server_views() -> str:
        """
        Récupère la liste des serveurs MCP connectés à l'espace Dust du workspace.

        Aucun paramètre requis : l'espace est configuré dans config.py
        (variable d'environnement DUST_SPACE_ID).

        QUAND UTILISER CE TOOL :
        - Découvrir quels serveurs MCP sont disponibles dans le workspace
        - Récupérer le "sId" (mcpServerViewId) d'un outil Dust natif
          (ex: web_search_&_browse, file browsing, etc.)
        - Vérifier si un serveur MCP est bien connecté à l'espace

        WORKFLOW TYPIQUE :
        1. get_space_mcp_server_views()
           → repère le serveur MCP voulu dans la liste
           → copie son "sId" (ex: "msv_JyagEzGFORBF")
        2. Utilise ce sId pour configurer un agent via
           update_agent_configuration ou create_agent_from_yaml

        Returns:
            JSON contenant un tableau 'mcp_server_views' avec pour
            chaque vue MCP :
            - sId         : identifiant unique de la vue MCP
                            (c'est le mcpServerViewId à utiliser
                            pour connecter l'outil à un agent)
            - name        : nom de la vue (ou null)
            - description : description (ou null)
            - serverType  : "remote" (URL externe) ou "internal" (Dust natif)
            - server      : détails du serveur (nom, outils exposés, URL...)
            - oAuthUseCase: "platform_actions", "personal_actions", ou null
            - createdAt   : timestamp de création
            - updatedAt   : timestamp de dernière modification
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/spaces/{DUST_SPACE_ID}/mcp_server_views"
            data = dust_get(path)

            server_views = data.get("serverViews", [])   # ✅ CORRIGÉ (était "spaces")

            result = {
                "space_id"         : DUST_SPACE_ID,
                "total_mcp_views"  : len(server_views),
                "mcp_server_views" : server_views
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                "error"   : str(e),
                "space_id": DUST_SPACE_ID
            }, ensure_ascii=False)
