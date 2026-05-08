# =============================================================
# tools/list_agents.py
# =============================================================
# Tool MCP : liste tous les agents du workspace Dust
# avec leurs tools MCP, sous-agents, knowledge bases et skills
#
# AVANT : retournait uniquement sId + name (variant=light)
# APRÈS : retourne les capacités complètes de chaque agent (variant=full)
#
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations
#            ?view=all&variant=full
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


# =============================================================
# FONCTION UTILITAIRE PRIVÉE
# =============================================================

def _extract_capabilities(agent: dict) -> dict:
    """
    Parse les 'actions' d'un agent et les classe en 4 catégories.

    Dans l'API Dust avec variant=full, chaque agent expose un tableau
    'actions' qui liste tous ses outils/capacités configurés.
    Chaque action a un champ 'type' qui indique sa nature.

    On classe selon ces règles :
      - type contient "mcp"                     → mcp_tools
      - type contient "agent"                   → sub_agents
      - type contient "retrieval" ou "search"   → knowledge_bases
      - tout le reste                           → other_actions

    Les skills sont un tableau SÉPARÉ au niveau racine de l'agent
    (pas dans 'actions') — traités à part.

    Args:
        agent : dictionnaire d'un agent tel que retourné par l'API Dust

    Returns:
        dict avec les 5 clés : mcp_tools, sub_agents, knowledge_bases,
        skills, other_actions
    """
    mcp_tools      = []
    sub_agents     = []
    knowledge_bases = []
    other_actions  = []

    for action in agent.get("actions", []):

        # On lit le type en minuscules pour faciliter la comparaison
        action_type = action.get("type", "").lower()
        name        = action.get("name", "")

        # ── CAS 1 : Tool MCP ──────────────────────────────────
        # Exemples de types : "mcp_server_tool_configuration", "mcp_configuration"
        if "mcp" in action_type:
            mcp_tools.append({
                "name":           name,
                "description":    action.get("description"),
                # L'ID du serveur MCP peut être sous deux noms selon la version de l'API
                "server_view_id": (
                    action.get("mcpServerViewId") or
                    action.get("serverViewId")
                ),
                "type": action.get("type"),
            })

        # ── CAS 2 : Sous-agent ────────────────────────────────
        # Un sous-agent = action qui appelle un autre agent Dust
        # Type contient "agent" mais pas "mcp" (déjà capturé ci-dessus)
        elif "agent" in action_type:
            sub_agents.append({
                "name": name,
                # L'ID de l'agent cible peut être sous deux noms différents
                "agent_configuration_id": (
                    action.get("agentConfigurationId") or
                    action.get("configuration_id")
                ),
                "type": action.get("type"),
            })

        # ── CAS 3 : Knowledge base ────────────────────────────
        # Bases de connaissance : "retrieval_configuration", "search_configuration"
        elif "retrieval" in action_type or "search" in action_type:
            data_sources = action.get("dataSources", [])

            if data_sources:
                # Une action peut pointer vers plusieurs sources
                for ds in data_sources:
                    knowledge_bases.append({
                        "name":           ds.get("name") or ds.get("dataSourceId"),
                        "data_source_id": ds.get("dataSourceId"),
                        "workspace_id":   ds.get("workspaceId"),
                    })
            else:
                # Pas de détail de source → on note quand même l'action
                knowledge_bases.append({
                    "name": name,
                    "type": action.get("type"),
                })

        # ── CAS 4 : Autre action ──────────────────────────────
        # Tables, apps Dust, etc. On garde une trace pour ne rien perdre
        else:
            if name or action.get("type"):
                other_actions.append({
                    "name": name,
                    "type": action.get("type"),
                })

    # ── Skills ────────────────────────────────────────────────
    # Les skills sont dans un tableau séparé à la racine de l'agent
    # (pas dans 'actions') — on les traite donc indépendamment
    skills = [
        {
            "name": skill.get("name"),
            "sId":  skill.get("sId"),
        }
        for skill in agent.get("skills", [])
    ]

    return {
        "mcp_tools":       mcp_tools,
        "sub_agents":      sub_agents,
        "knowledge_bases": knowledge_bases,
        "skills":          skills,
        "other_actions":   other_actions,
    }


# =============================================================
# ENREGISTREMENT DU TOOL MCP
# =============================================================

def register(mcp):

    @mcp.tool()
    def list_agents() -> str:
        """
        Retourne la liste de tous les agents du workspace Dust
        avec leurs capacités complètes.

        Pour chaque agent, retourne :
          - sId et name       : identifiants de l'agent
          - description       : description de l'agent
          - status            : statut (active, etc.)
          - scope             : portée (workspace, published, global...)
          - model             : modèle LLM utilisé (id + provider)
          - mcp_tools         : tools MCP (serveurs externes) configurés
          - sub_agents        : sous-agents que cet agent peut appeler
          - knowledge_bases   : bases de connaissance connectées
          - skills            : skills activés sur cet agent
          - other_actions     : autres actions (tables, apps Dust, etc.)

        Returns:
            JSON avec total (nombre d'agents) et agents (tableau enrichi).
        """
        try:
            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"

            # variant=full est OBLIGATOIRE pour obtenir le tableau 'actions'
            # Sans lui, 'actions' est absent et on ne peut pas extraire
            # les tools MCP, sous-agents ni les knowledge bases.
            # view=all → tous les agents non-privés, compatible clé API
            data = dust_get(path, params={"view": "all", "variant": "full"})

            agents_raw = data.get("agentConfigurations", [])
            agents = []

            for agent in agents_raw:

                # ── Infos de base ──────────────────────────────
                model_raw = agent.get("model", {})

                enriched = {
                    "sId":         agent.get("sId", ""),
                    "name":        agent.get("name", ""),
                    "description": agent.get("description", ""),
                    "status":      agent.get("status", ""),
                    "scope":       agent.get("scope", ""),

                    # Le modèle peut avoir des noms de clés différents
                    # selon la version de l'API — on gère les deux
                    "model": {
                        "model_id":    model_raw.get("modelId")    or model_raw.get("model_id"),
                        "provider_id": model_raw.get("providerId") or model_raw.get("provider_id"),
                    } if model_raw else None,
                }

                # ── Ajout des capacités enrichies ──────────────
                # _extract_capabilities() parse 'actions' + 'skills'
                # et retourne les 5 catégories prêtes à l'emploi
                enriched.update(_extract_capabilities(agent))

                agents.append(enriched)

            return json.dumps({
                "total":  len(agents),
                "agents": agents,
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)