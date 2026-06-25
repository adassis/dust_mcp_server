# =============================================================
# tools/add_mcp_server_to_agent.py
# =============================================================
# Ajoute un serveur MCP (interne OU remote) à un agent Dust.
#
# Pourquoi ce tool existe :
# La route publique v1 PATCH (utilisée par update_agent_configuration)
# ne supporte que les serveurs MCP INTERNES via toolset/mcp_server_name.
# Les serveurs REMOTE (ex: Aircall, serveurs custom Railway) sont rejetés
# avec "Invalid internal MCP server name".
#
# Ce tool utilise la route PRIVÉE PATCH /api/w/{wId}/assistant/agent_configurations/{aId}
# qui accepte mcpServerViewId directement, sans passer par le YAML converter.
#
# Endpoint : PATCH /api/w/{wId}/assistant/agent_configurations/{aId}
# (BASE_URL = "https://dust.tt/api" — PAS /api/v1)
# =============================================================

import json
from utils.dust import dust_get_private, dust_patch_private
from config import DUST_WORKSPACE_ID


def _normalize_action(action: dict) -> dict:
    """
    Convertit une action depuis la réponse GET (AgentConfigurationType)
    vers le format attendu par le body PATCH.
    Retire les champs générés par le serveur (id, sId, agentConfigurationId…).
    """
    return {
        "type": action.get("type"),
        "mcpServerViewId": action.get("mcpServerViewId"),
        "name": action.get("name", ""),
        "description": action.get("description"),
        "dataSources": action.get("dataSources"),
        "tables": action.get("tables"),
        "childAgentId": action.get("childAgentId"),
        "timeFrame": action.get("timeFrame"),
        "jsonSchema": action.get("jsonSchema"),
        "additionalConfiguration": action.get("additionalConfiguration") or {},
        "dustAppConfiguration": action.get("dustAppConfiguration"),
        "secretName": action.get("secretName"),
        "dustProject": action.get("dustProject"),
    }


def register(mcp):

    @mcp.tool()
    def add_mcp_server_to_agent(
        agent_sid: str,
        mcp_server_view_id: str,
        action_name: str = None,
        action_description: str = None,
    ) -> str:
        """
        Ajoute un serveur MCP (interne OU remote) à un agent Dust existant.

        Utilise la route privée PATCH /api/w/{wId}/assistant/agent_configurations/{aId}
        qui accepte mcpServerViewId directement — contrairement à update_agent_configuration
        (toolset_json) qui ne supporte que les serveurs internes via YAML.

        QUAND UTILISER CE TOOL :
        - Pour ajouter tout serveur MCP remote (Aircall, webhook custom, etc.)
        - Pour ajouter des serveurs internes également (fonctionne pour les deux)
        - update_agent_configuration (toolset_json) échoue → utiliser ce tool

        WORKFLOW :
        1. get_space_mcp_server_views() → récupère le sId (msv_xxx) du serveur voulu
        2. add_mcp_server_to_agent(agent_sid, mcp_server_view_id)
        3. get_agent_yaml(agent_sid) → vérifie que l'action est bien ajoutée

        Args:
            agent_sid          : sId de l'agent à modifier (ex: "VCcSUHGA1o").
            mcp_server_view_id : sId de la vue MCP à ajouter (ex: "msv_hwB8vD8eCt0Gh0").
                                  Récupérable via get_space_mcp_server_views().
            action_name        : Nom de l'action dans l'agent (optionnel, défaut: "").
            action_description : Description de l'action (optionnel).

        Returns:
            JSON de la configuration d'agent mise à jour.
        """
        path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations/{agent_sid}"

        # 1. Récupère la config complète (variant=full implicite via route privée)
        data = dust_get_private(path)
        agent = data.get("agentConfiguration", {})

        if not agent:
            raise RuntimeError(
                f"Agent '{agent_sid}' introuvable ou accès refusé. "
                f"Vérifiez le sId via search_agent_by_name."
            )

        # 2. Normalise les actions existantes (retire les champs serveur-générés)
        existing_actions = [
            _normalize_action(a) for a in agent.get("actions", [])
        ]

        # 3. Construit la nouvelle action MCP
        new_action = {
            "type": "mcp_server_configuration",
            "mcpServerViewId": mcp_server_view_id,
            "name": action_name or "",
            "description": action_description or None,
            "dataSources": None,
            "tables": None,
            "childAgentId": None,
            "timeFrame": None,
            "jsonSchema": None,
            "additionalConfiguration": {},
            "dustAppConfiguration": None,
            "secretName": None,
            "dustProject": None,
        }

        # 4. Construit le body PATCH complet (createOrUpgradeAgentConfiguration)
        model = agent.get("model", {})

        body = {
            "assistant": {
                "name": agent["name"],
                "description": agent.get("description", ""),
                "instructions": agent.get("instructions", ""),
                "pictureUrl": agent.get("pictureUrl", ""),
                "status": agent.get("status", "active"),
                "scope": agent.get("scope", "visible"),
                "model": {
                    "modelId": model.get("modelId"),
                    "providerId": model.get("providerId"),
                    "temperature": model.get("temperature", 0),
                    "reasoningEffort": model.get("reasoningEffort"),
                    "responseFormat": model.get("responseFormat"),
                },
                "actions": existing_actions + [new_action],
                "templateId": agent.get("templateId"),
                "tags": [{"sId": t["sId"]} for t in agent.get("tags", [])],
                "maxStepsPerRun": agent.get("maxStepsPerRun", 64),
                "visualizationEnabled": agent.get("visualizationEnabled", False),
            }
        }

        # 5. Appelle la route privée PATCH
        result = dust_patch_private(path, body)
        return json.dumps(result, ensure_ascii=False, indent=2)
