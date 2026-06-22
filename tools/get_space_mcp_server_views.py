# =============================================================
# tools/get_space_mcp_server_views.py
# =============================================================
# Tool MCP : liste les serveurs MCP connectés à l'espace Dust
# principal du workspace.
#
# Endpoint : GET /api/v1/w/{wId}/spaces/{spaceId}/mcp_server_views
#
# Le spaceId est lu depuis config.DUST_SPACE_ID (variable
# d'environnement Railway DUST_SPACE_ID, ou valeur par défaut
# définie dans config.py).
#
# Ce tool permet de savoir quels serveurs MCP (remote ou internal)
# sont activés dans l'espace, avec leurs détails :
# nom, description, type, outils disponibles, sId, etc.
#
# Cas d'usage principal : récupérer le mcpServerViewId d'un outil
# Dust natif (web search, etc.) pour l'ajouter à un agent via
# update_agent_configuration ou create_agent_from_yaml.
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID, DUST_SPACE_ID   # ← DUST_SPACE_ID importé

def register(mcp):

    @mcp.tool()
    def get_space_mcp_server_views() -> str:             # ← plus de paramètre space_id
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
            # DUST_SPACE_ID vient de config.py (variable d'environnement Railway
            # ou valeur par défaut "vlt_VZXFm4VFUdvh")
            path = f"/w/{DUST_WORKSPACE_ID}/spaces/{DUST_SPACE_ID}/mcp_server_views"

            data   = dust_get(path)
            spaces = data.get("spaces", [])

            result = {
                "space_id"         : DUST_SPACE_ID,   # rappel de l'espace interrogé
                "total_mcp_views"  : len(spaces),
                "mcp_server_views" : spaces
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                "error"   : str(e),
                "space_id": DUST_SPACE_ID
            }, ensure_ascii=False)
