# =============================================================
# tools/list_agents.py
# =============================================================
# Tool MCP : liste tous les agents du workspace Dust
# avec leurs capacités complètes ET leurs derniers auteurs.
#
# Fusionne les anciennes versions :
#   - list_agents        (capacités enrichies : mcp_tools, sub_agents, etc.)
#   - list_agents_with_authors (paramètre withAuthors=true)
#
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations
#            ?view=all&variant=full&withAuthors=true
# =============================================================

import json
from utils.dust import dust_get        # Client HTTP centralisé du projet
from config import DUST_WORKSPACE_ID   # ID du workspace, lu depuis les variables d'env


# =============================================================
# FONCTION UTILITAIRE PRIVÉE
# =============================================================

def _extract_capabilities(agent: dict) -> dict:
    """
    Parse le tableau 'actions' d'un agent (disponible uniquement en variant=full)
    et classe chaque action en 4 catégories selon son type.

    Catégories :
      - mcp_tools      : outils MCP (serveurs externes connectés à l'agent)
      - sub_agents     : sous-agents que cet agent peut appeler
      - knowledge_bases: bases de connaissance connectées (retrieval/search)
      - other_actions  : tout le reste (tables, apps Dust, etc.)

    Les skills sont dans un tableau séparé à la racine de l'agent
    (pas dans 'actions') — traités indépendamment.

    Args:
        agent : dictionnaire d'un agent tel que retourné par l'API Dust

    Returns:
        dict avec 5 clés : mcp_tools, sub_agents, knowledge_bases, skills, other_actions
    """
    mcp_tools      = []
    sub_agents     = []
    knowledge_bases = []
    other_actions  = []

    for action in agent.get("actions", []):
        # On lit le type en minuscules pour faciliter les comparaisons
        action_type = action.get("type", "").lower()
        name        = action.get("name", "")

        # ── CAS 1 : Tool MCP ──────────────────────────────────────────────
        # Types : "mcp_server_tool_configuration", "mcp_configuration", etc.
        if "mcp" in action_type:
            mcp_tools.append({
                "name"           : name,
                "description"    : action.get("description"),
                # L'ID du serveur MCP peut avoir deux noms selon la version de l'API
                "server_view_id" : (
                    action.get("mcpServerViewId") or
                    action.get("serverViewId")
                ),
                "type"           : action.get("type"),
            })

        # ── CAS 2 : Sous-agent ────────────────────────────────────────────
        # Un sous-agent = action qui appelle un autre agent Dust
        elif "agent" in action_type:
            sub_agents.append({
                "name"                    : name,
                # L'ID de l'agent cible peut avoir deux noms différents
                "agent_configuration_id"  : (
                    action.get("agentConfigurationId") or
                    action.get("configuration_id")
                ),
                "type"                    : action.get("type"),
            })

        # ── CAS 3 : Knowledge base ────────────────────────────────────────
        # Types : "retrieval_configuration", "search_configuration"
        elif "retrieval" in action_type or "search" in action_type:
            data_sources = action.get("dataSources", [])
            if data_sources:
                # Une action peut pointer vers plusieurs sources → on itère
                for ds in data_sources:
                    knowledge_bases.append({
                        "name"           : ds.get("name") or ds.get("dataSourceId"),
                        "data_source_id" : ds.get("dataSourceId"),
                        "workspace_id"   : ds.get("workspaceId"),
                    })
            else:
                # Pas de détail de source → on note l'action quand même
                knowledge_bases.append({
                    "name" : name,
                    "type" : action.get("type"),
                })

        # ── CAS 4 : Autre action ──────────────────────────────────────────
        # Tables, apps Dust, etc.
        else:
            if name or action.get("type"):
                other_actions.append({
                    "name" : name,
                    "type" : action.get("type"),
                })

    # ── Skills ────────────────────────────────────────────────────────────
    # Tableau séparé à la racine de l'agent (pas dans 'actions')
    skills = [
        {"name": skill.get("name"), "sId": skill.get("sId")}
        for skill in agent.get("skills", [])
    ]

    return {
        "mcp_tools"      : mcp_tools,
        "sub_agents"     : sub_agents,
        "knowledge_bases": knowledge_bases,
        "skills"         : skills,
        "other_actions"  : other_actions,
    }


# =============================================================
# ENREGISTREMENT DU TOOL MCP
# =============================================================

def register(mcp):
    """
    Enregistre le tool 'list_agents' dans le serveur MCP.
    Appelé par server.py au démarrage via tools.list_agents.register(mcp).
    """

    @mcp.tool()
    def list_agents(
        view          : str  = "all",
        with_authors  : bool = False,
        include_inactive: bool = False
    ) -> str:
        """
        Retourne la liste complète des agents du workspace Dust
        avec leurs capacités enrichies et, optionnellement, leurs derniers auteurs.

        Pour chaque agent, retourne :
          - sId et name      : identifiants de l'agent
          - description      : description de l'agent
          - status           : statut (active, etc.)
          - scope            : portée (workspace, published, global...)
          - model            : modèle LLM utilisé (id + provider + température)
          - mcp_tools        : outils MCP (serveurs externes) configurés sur l'agent
          - sub_agents       : sous-agents que cet agent peut appeler
          - knowledge_bases  : bases de connaissance connectées
          - skills           : skills activées sur cet agent
          - other_actions    : autres actions (tables, apps Dust, etc.)
          - lastAuthors      : (si with_authors=True) utilisateurs ayant récemment édité l'agent

        Args:
            view            : Filtre de vue :
                              - "all"       (défaut) : tous les agents non-privés
                              - "workspace" : agents dont le scope est 'workspace'
                              - "published" : agents publiés publiquement
                              - "global"    : agents globaux Dust (@dust, @gpt4, etc.)
                              ⚠️ "list" et "favorites" requièrent OAuth (incompatible clé API)

            with_authors    : Si True, inclut le champ 'lastAuthors' sur chaque agent
                              avec les infos des utilisateurs ayant récemment édité l'agent.
                              Défaut : False.

            include_inactive: Si True, inclut les agents inactifs/archivés.
                              Défaut : False.

        Returns:
            JSON avec :
              - total   : nombre d'agents retournés
              - agents  : tableau d'agents enrichis
        """
        try:
            # ── Validation de la vue ──────────────────────────────────────
            # "list" et "favorites" ne fonctionnent qu'en OAuth, pas avec une clé API
            valid_views = ["all", "workspace", "published", "global"]
            if view not in valid_views:
                return json.dumps({
                    "error" : f"Vue '{view}' non supportée avec une clé API.",
                    "hint"  : f"Vues disponibles : {valid_views}. "
                              f"'list' et 'favorites' requièrent OAuth."
                }, ensure_ascii=False)

            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"

            # ── Construction des paramètres ───────────────────────────────
            params = {
                "view"    : view,
                "variant" : "full",   # OBLIGATOIRE pour obtenir 'actions'
                                      # (nécessaire pour _extract_capabilities)
            }

            # withAuthors est ajouté seulement si demandé
            # (l'API attend la string "true", pas un booléen Python)
            if with_authors:
                params["withAuthors"] = "true"

            # ── Appel API ─────────────────────────────────────────────────
            data = dust_get(path, params=params)

            agents_raw = data.get("agentConfigurations", [])

            # ── Filtrage des inactifs (si demandé) ────────────────────────
            if not include_inactive:
                # On garde uniquement les agents dont le status est "active"
                agents_raw = [a for a in agents_raw if a.get("status") == "active"]

            # ── Enrichissement de chaque agent ────────────────────────────
            agents = []
            for agent in agents_raw:
                model_raw = agent.get("model", {})

                enriched = {
                    "sId"        : agent.get("sId", ""),
                    "name"       : agent.get("name", ""),
                    "description": agent.get("description", ""),
                    "status"     : agent.get("status", ""),
                    "scope"      : agent.get("scope", ""),
                    # Le modèle peut avoir des noms de clés différents selon la version de l'API
                    "model"      : {
                        "model_id"   : model_raw.get("modelId")    or model_raw.get("model_id"),
                        "provider_id": model_raw.get("providerId") or model_raw.get("provider_id"),
                        "temperature": model_raw.get("temperature"),
                    } if model_raw else None,
                }

                # Ajout des capacités enrichies (mcp_tools, sub_agents, etc.)
                enriched.update(_extract_capabilities(agent))

                # Ajout des auteurs récents si withAuthors=true a été demandé
                # lastAuthors est un tableau retourné directement par l'API Dust
                if with_authors:
                    enriched["lastAuthors"] = agent.get("lastAuthors", [])

                agents.append(enriched)

            return json.dumps({
                "total"       : len(agents),
                "view"        : view,
                "with_authors": with_authors,
                "agents"      : agents,
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
