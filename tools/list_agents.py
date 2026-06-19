# =============================================================
# tools/list_agents.py
# =============================================================
# Tool MCP : liste tous les agents du workspace Dust
# avec leurs capacités complètes ET leurs derniers auteurs.
#
# Endpoint : GET /api/v1/w/{wId}/assistant/agent_configurations
#            ?view=all&variant=full&withAuthors=truee
# =============================================================

import json
from utils.dust import dust_get       # Client HTTP centralisé du projet
from config import DUST_WORKSPACE_ID  # ID du workspace, lu depuis les variables d'env

# =============================================================
# FONCTION UTILITAIRE PRIVÉE
# =============================================================

def _extract_capabilities(agent: dict) -> dict:
    """
    Parse le tableau 'actions' d'un agent (disponible uniquement en variant=full)
    et classe chaque action en 4 catégories selon son type.

    Catégories :
    - mcp_tools       : outils MCP (serveurs externes connectés à l'agent)
    - sub_agents      : sous-agents que cet agent peut appeler
    - knowledge_bases : bases de connaissance connectées (retrieval/search)
    - other_actions   : tout le reste (tables, apps Dust, etc.)

    Les skills sont dans un tableau séparé à la racine de l'agent
    (pas dans 'actions') — traités indépendamment.
    """
    mcp_tools      = []
    sub_agents     = []
    knowledge_bases = []
    other_actions  = []

    for action in agent.get("actions", []):
        action_type = action.get("type", "").lower()
        name = action.get("name", "")

        # ── CAS 1 : Tool MCP ─────────────────────────────────────────
        if "mcp" in action_type:
            mcp_tools.append({
                "name"           : name,
                "description"    : action.get("description"),
                "server_view_id" : (
                    action.get("mcpServerViewId") or
                    action.get("serverViewId")
                ),
                "type"           : action.get("type"),
            })

        # ── CAS 2 : Sous-agent ────────────────────────────────────────
        elif "agent" in action_type:
            sub_agents.append({
                "name"                    : name,
                "agent_configuration_id"  : (
                    action.get("agentConfigurationId") or
                    action.get("configuration_id")
                ),
                "type"                    : action.get("type"),
            })

        # ── CAS 3 : Knowledge base ────────────────────────────────────
        elif "retrieval" in action_type or "search" in action_type:
            data_sources = action.get("dataSources", [])
            if data_sources:
                for ds in data_sources:
                    knowledge_bases.append({
                        "name"          : ds.get("name") or ds.get("dataSourceId"),
                        "data_source_id": ds.get("dataSourceId"),
                        "workspace_id"  : ds.get("workspaceId"),
                    })
            else:
                knowledge_bases.append({
                    "name": name,
                    "type": action.get("type"),
                })

        # ── CAS 4 : Autre action ──────────────────────────────────────
        else:
            if name or action.get("type"):
                other_actions.append({
                    "name": name,
                    "type": action.get("type"),
                })

    # ── Skills ────────────────────────────────────────────────────────
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
        view           : str  = "all",
        with_authors   : bool = False,
        include_inactive: bool = False
    ) -> str:
        """
        Retourne la liste complète des agents du workspace Dust
        avec leurs capacités enrichies et, optionnellement, leurs derniers auteurs.

        Args:
            view : "all" (défaut) · "workspace" · "published" · "global"
                   ⚠️ "list" et "favorites" requièrent OAuth (incompatible clé API)
            with_authors    : Si True, inclut le champ 'lastAuthors' sur chaque agent.
            include_inactive: Si True, inclut les agents inactifs/archivés.

        Returns:
            JSON avec :
            - total  : nombre d'agents retournés
            - agents : tableau d'agents enrichis
        """
        try:
            # ── Validation de la vue ─────────────────────────────────
            valid_views = ["all", "workspace", "published", "global"]
            if view not in valid_views:
                return json.dumps({
                    "error": f"Vue '{view}' non supportée avec une clé API.",
                    "hint" : f"Vues disponibles : {valid_views}. "
                             f"'list' et 'favorites' requièrent OAuth."
                }, ensure_ascii=False)

            path = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations"

            # ── Construction des paramètres ──────────────────────────
            params = {
                "view"   : view,
                "variant": "full",  # OBLIGATOIRE pour obtenir 'actions'
            }

            # withAuthors est ajouté seulement si demandé
            # (l'API attend la string "true", pas un booléen Python)
            if with_authors:
                params["withAuthors"] = "true"

            # ── Appel API ────────────────────────────────────────────
            # dust_get lève une RuntimeError si la réponse n'est pas un dict
            # (fix appliqué dans utils/dust.py)
            data = dust_get(path, params=params)

            # ✅ FIX : garde de sécurité supplémentaire au niveau du tool
            # Au cas où dust_get retournerait quand même autre chose qu'un dict
            if not isinstance(data, dict):
                return json.dumps({
                    "error"    : "Réponse inattendue de l'API Dust",
                    "type_reçu": type(data).__name__,
                    "aperçu"   : str(data)[:300],
                    "hint"     : "Vérifie ta DUST_API_KEY et ton DUST_WORKSPACE_ID sur Railway"
                }, ensure_ascii=False)

            agents_raw = data.get("agentConfigurations", [])

            # ── Filtrage des inactifs ────────────────────────────────
            if not include_inactive:
                agents_raw = [a for a in agents_raw if a.get("status") == "active"]

            # ── Enrichissement de chaque agent ───────────────────────
            agents = []
            for agent in agents_raw:
                model_raw = agent.get("model", {})

                enriched = {
                    "sId"        : agent.get("sId", ""),
                    "name"       : agent.get("name", ""),
                    "description": agent.get("description", ""),
                    "status"     : agent.get("status", ""),
                    "scope"      : agent.get("scope", ""),
                    "model"      : {
                        "model_id"   : model_raw.get("modelId")    or model_raw.get("model_id"),
                        "provider_id": model_raw.get("providerId") or model_raw.get("provider_id"),
                        "temperature": model_raw.get("temperature"),
                    } if model_raw else None,
                }

                # Ajout des capacités enrichies (mcp_tools, sub_agents, etc.)
                enriched.update(_extract_capabilities(agent))

                # Ajout des auteurs si demandé
                if with_authors:
                    enriched["lastAuthors"] = agent.get("lastAuthors", [])

                agents.append(enriched)

            # ── Retour final ─────────────────────────────────────────
            return json.dumps({
                "total" : len(agents),
                "agents": agents,
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
