# =============================================================
# tools/get_conversation.py
# =============================================================
# Tool MCP : récupère une conversation Dust à partir de son ID
# Endpoint : GET /api/v1/w/{wId}/assistant/conversations/{cId}
# =============================================================

import json                          # Pour convertir les données Python en texte JSON lisible
from utils.dust import dust_get      # Le client HTTP centralisé du projet (gère auth + erreurs)
from config import DUST_WORKSPACE_ID # L'ID du workspace, stocké en variable d'environnement

def register(mcp):
    """
    Cette fonction est appelée par server.py au démarrage.
    Elle enregistre le tool 'get_conversation' dans le serveur MCP
    grâce au décorateur @mcp.tool().
    
    Le paramètre 'mcp' est l'instance FastMCP créée dans server.py.
    """

    @mcp.tool()
    def get_conversation(
        conversation_id: str,
        limit: int = None,
        last_value: str = None
    ) -> str:
        """
        Récupère le contenu complet d'une conversation Dust à partir de son ID.

        Utilise cet outil pour obtenir tous les messages d'une conversation :
        les messages de l'utilisateur, les réponses des agents, les actions
        effectuées, ainsi que les métadonnées de la conversation (titre,
        date de création, participants, etc.).

        Args:
            conversation_id : Identifiant unique de la conversation (ex: "gWQdp70e2T").
                              Visible dans l'URL Dust : dust.tt/w/WORKSPACE/conversations/CONVERSATION_ID
            
            limit : (optionnel) Nombre maximum de messages à retourner.
                    Utile pour les très longues conversations.
                    Si non fourni, tous les messages sont retournés.
            
            last_value : (optionnel) Curseur de pagination — valeur retournée
                         par un appel précédent pour récupérer la page suivante
                         de messages. Laisser vide pour le premier appel.

        Returns:
            JSON contenant l'objet conversation avec :
            - sId : identifiant unique de la conversation
            - title : titre de la conversation
            - created : timestamp de création
            - content : tableau de messages (userMessage, agentMessage, etc.)
              Chaque message contient : role, content, mentions, createdAt...
        """

        try:
            # Construction du chemin de l'endpoint Dust
            # DUST_WORKSPACE_ID est lu depuis les variables d'environnement de Railway
            # conversation_id est passé par l'agent qui appelle ce tool
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/conversations/{conversation_id}"

            # Construction des paramètres de requête (query string)
            # On ne les inclut que s'ils ont été fournis (pour éviter d'envoyer "None")
            params = {}
            if limit is not None:
                params["limit"] = limit          # Ex: ?limit=20
            if last_value is not None:
                params["lastValue"] = last_value  # Ex: ?lastValue=abc123

            # Appel à l'API Dust via le client HTTP centralisé
            # dust_get() gère automatiquement :
            #   - l'ajout du header Authorization: Bearer DUST_API_KEY
            #   - la vérification du code HTTP de la réponse
            #   - la conversion de la réponse en dict Python
            data = dust_get(path, params=params if params else None)

            # Conversion du dict Python en texte JSON formaté
            # ensure_ascii=False → conserve les accents et caractères spéciaux
            # indent=2 → indentation pour lisibilité
            return json.dumps(data, ensure_ascii=False, indent=2)

        except Exception as e:
            # En cas d'erreur (ID invalide, pas de droits, réseau, etc.)
            # On retourne un JSON d'erreur plutôt que de faire planter le serveur
            return json.dumps(
                {
                    "error": str(e),                        # Message d'erreur
                    "conversation_id": conversation_id      # L'ID qui a causé l'erreur
                },
                ensure_ascii=False
            )
