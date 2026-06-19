# =============================================================
# tools/get_agent_yaml.py
# =============================================================
# Tool MCP : exporte la configuration complète d'un agent Dust
# au format YAML (instructions, actions, modèle, etc.)
#
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations/{sId}/export/yaml
# Header   : Accept: text/yaml
# Retourne : texte YAML brut (pas du JSON)
# =============================================================

import json
from utils.dust import dust_get_text   # Nouvelle fonction pour réponses texte
from config import DUST_WORKSPACE_ID


def register(mcp):
    """
    Enregistre le tool 'get_agent_yaml' dans le serveur MCP.
    Appelé par server.py au démarrage.
    """

    @mcp.tool()
    def get_agent_yaml(agent_sid: str) -> str:
        """
        Retourne la configuration complète d'un agent Dust au format YAML.

        Inclut : nom, description, instructions système, modèle LLM,
        actions/tools configurés, paramètres avancés.

        Utilise cet outil pour inspecter en détail la configuration
        d'un agent spécifique à partir de son identifiant (sId).

        Args:
            agent_sid : Identifiant unique de l'agent (ex: "7f3a9c2b1e").
                        Récupérable via list_agent_configurations
                        ou search_agent_by_name.

        Returns:
            Le contenu YAML complet de la configuration de l'agent,
            ou un JSON d'erreur si l'agent est introuvable.
        """
        try:
            # Validation — agent_sid ne doit pas être vide
            if not agent_sid or not agent_sid.strip():
                return json.dumps({
                    "error": "agent_sid est requis.",
                    "hint" : "Passe l'identifiant sId de l'agent. "
                             "Utilise list_agent_configurations ou "
                             "search_agent_by_name pour le trouver."
                }, ensure_ascii=False)

            # Construction du chemin de l'endpoint YAML
            path = (
                f"/w/{DUST_WORKSPACE_ID}"
                f"/assistant/agent_configurations/{agent_sid.strip()}"
                f"/export/yaml"
            )

            # Appel API — réponse en texte YAML (pas en JSON)
            yaml_content = dust_get_text(path, accept="text/yaml")

            # On retourne le YAML brut directement
            return yaml_content

        except Exception as e:
            return json.dumps({
                "error"    : str(e),
                "agent_sid": agent_sid
            }, ensure_ascii=False)
