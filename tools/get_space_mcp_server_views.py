# =============================================================
# tools/get_space_mcp_server_views.py
# =============================================================
# Tool MCP : liste les serveurs MCP connectés à un espace Dust
# Endpoint  : GET /api/v1/w/{wId}/spaces/{spaceId}/mcp_server_views
#
# Ce tool permet de savoir quels serveurs MCP (remote ou internal)
# sont activés dans un espace Dust donné, avec leurs détails :
# nom, description, type, outils disponibles, etc.
# =============================================================

import json                          # Pour formater la réponse en JSON lisible
from utils.dust import dust_get      # Le client HTTP centralisé du projet
from config import DUST_WORKSPACE_ID # L'ID du workspace, lu depuis Railway

def register(mcp):
    """
    Appelée par server.py au démarrage.
    Enregistre le tool 'get_space_mcp_server_views' dans l'instance FastMCP.
    """

    @mcp.tool()
    def get_space_mcp_server_views(space_id: str) -> str:
        """
        Récupère la liste des serveurs MCP (vues MCP) connectés à un espace Dust.

        Utilise cet outil pour savoir quels outils MCP sont disponibles
        dans un espace Dust spécifique : serveurs remote, serveurs internes,
        leurs outils exposés, leur type d'autorisation OAuth, etc.

        Args:
            space_id : Identifiant de l'espace Dust (ex: "spc_xyz789").
                       Visible dans l'URL Dust :
                       dust.tt/w/WORKSPACE/spaces/SPACE_ID
                       ou récupérable via l'API /spaces.

        Returns:
            JSON contenant un tableau 'spaces' avec pour chaque vue MCP :
            - id          : identifiant numérique interne
            - sId         : identifiant unique de la vue (ex: "mcp_sv_abc123")
            - name        : nom personnalisé de la vue (ou null)
            - description : description personnalisée (ou null)
            - createdAt   : timestamp Unix de création
            - updatedAt   : timestamp Unix de dernière modification
            - spaceId     : ID de l'espace auquel appartient cette vue
            - serverType  : type du serveur — "remote" ou "internal"
            - server      : objet détaillant le serveur MCP (nom, outils, etc.)
            - oAuthUseCase: cas d'usage OAuth — "platform_actions",
                           "personal_actions", ou null
            - editedByUser: infos sur le dernier éditeur (ou null)
        """
        try:
            # Construction du chemin de l'endpoint
            # DUST_WORKSPACE_ID vient de la variable d'environnement Railway
            # space_id est fourni par l'agent qui appelle ce tool
            path = f"/w/{DUST_WORKSPACE_ID}/spaces/{space_id}/mcp_server_views"

            # Appel GET via le client centralisé (gère auth + erreurs HTTP)
            data = dust_get(path)

            # Mise en forme : on enrichit la réponse avec un comptage rapide
            spaces = data.get("spaces", [])

            result = {
                "space_id": space_id,          # On rappelle l'espace interrogé
                "total_mcp_views": len(spaces), # Nombre total de vues MCP
                "mcp_server_views": spaces      # La liste brute retournée par l'API
            }

            # Conversion en JSON formaté (indent=2 = lisible, ensure_ascii=False = accents OK)
            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            # En cas d'erreur (space_id invalide, pas de droits, réseau, etc.)
            # On retourne un JSON d'erreur structuré plutôt que de crasher
            return json.dumps(
                {
                    "error": str(e),         # Message d'erreur explicite
                    "space_id": space_id     # L'ID qui a causé l'erreur
                },
                ensure_ascii=False
            )
