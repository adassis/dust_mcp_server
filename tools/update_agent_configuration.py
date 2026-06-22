# =============================================================
# tools/update_agent_configuration.py
# =============================================================
# Tool MCP : modifie la configuration d'un agent Dust existant.
#
# Endpoint : PATCH /api/v1/w/{wId}/assistant/agent_configurations/{sId}
# Body : JSON partiel — seuls les champs envoyés sont modifiés.
# Retourne : la configuration complète mise à jour de l'agent.
#
# ⚠️ COMPORTEMENT PATCH (partiel) :
# Seuls les champs que tu inclus dans le body seront modifiés.
# Les champs absents du body restent INCHANGÉS.
# EXCEPTION : skills et toolset sont des remplacements complets
# (si tu les envoies, ils écrasent toute la liste existante).
# =============================================================

import json
from utils.dust import dust_patch
from config import DUST_WORKSPACE_ID

def register(mcp):

    @mcp.tool()
    def update_agent_configuration(
        agent_sid: str,
        instructions: str = None,
        model_provider_id: str = None,
        model_id: str = None,
        temperature: float = None,
        user_favorite: bool = None,
        skills_json: str = None,
        toolset_json: str = None,
        tags_json: str = None,
    ) -> str:
        """
        Modifie la configuration d'un agent Dust existant.

        ════════════════════════════════════════════════════════
        PRINCIPE FONDAMENTAL (PATCH)
        ════════════════════════════════════════════════════════
        Seuls les paramètres que tu fournis seront modifiés.
        Tout paramètre laissé à None reste INCHANGÉ côté Dust.
        Ne modifie QUE ce que l'utilisateur demande explicitement.

        ════════════════════════════════════════════════════════
        WORKFLOW OBLIGATOIRE AVANT TOUTE MODIFICATION
        ════════════════════════════════════════════════════════
        1. Utilise get_agent_yaml(agent_sid) pour lire la config actuelle.
        2. Identifie précisément ce qui doit changer.
        3. Pour skills/toolset : récupère la liste complète existante,
           car tu vas écraser l'intégralité de la liste.
        4. N'envoie QUE les champs à modifier.
        5. Reconfirme le résultat avec get_agent_yaml après la mise à jour.

        ════════════════════════════════════════════════════════
        STRUCTURE DU BODY API (à connaître absolument)
        ════════════════════════════════════════════════════════
        Les champs sont au NIVEAU RACINE du body, PAS imbriqués :

        {
          "userFavorite": bool,
          "agent": { handle, description, scope, avatar_url,
                     max_steps_per_run, visualization_enabled },
          "instructions": "string",
          "generation_settings": { provider_id, model_id,
                                   temperature, reasoning_effort },
          "tags": [...],
          "skills": [...],
          "toolset": [...]
        }

        ════════════════════════════════════════════════════════
        PARAMÈTRES
        ════════════════════════════════════════════════════════

        agent_sid (str, OBLIGATOIRE)
            Identifiant unique de l'agent à modifier (ex: "7f3a9c2b1e").
            Récupérable via list_agent_configurations ou search_agent_by_name.

        ────────────────────────────────────────────────────────
        instructions (str, optionnel)
        ────────────────────────────────────────────────────────
            Nouvelles instructions système de l'agent (le "system prompt").
            ⚠️ Remplace INTÉGRALEMENT les instructions existantes.
            Envoie toujours le texte complet, pas juste la partie modifiée.

            QUAND L'UTILISER :
            - L'utilisateur veut changer le comportement de l'agent
            - L'utilisateur veut ajouter/modifier des règles de réponse
            - L'utilisateur veut changer la langue, le ton, le rôle de l'agent

            MARCHE À SUIVRE :
            1. Lire les instructions actuelles via get_agent_yaml
            2. Modifier uniquement ce qui est demandé
            3. Renvoyer le texte complet des nouvelles instructions

            EXEMPLE :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                instructions="Tu es un assistant RH expert. Réponds toujours
                              en français et de façon concise."
            )

        ────────────────────────────────────────────────────────
        model_provider_id + model_id (str, optionnel)
        ────────────────────────────────────────────────────────
            Changent le modèle LLM de l'agent.
            ⚠️ Toujours fournir les DEUX ensemble, ils sont liés.

            PROVIDERS ET MODÈLES DISPONIBLES :
            - "anthropic"        → "claude-opus-4-5"
                                   "claude-sonnet-4-5"
                                   "claude-haiku-3-5"
            - "openai"           → "gpt-4o"
                                   "gpt-4o-mini"
                                   "o1"
                                   "o3-mini"
            - "google_ai_studio" → "gemini-2.0-flash-001"
                                   "gemini-1.5-pro"
            - "mistral"          → "mistral-large-latest"
                                   "mistral-small-latest"
            - "togetherai"       → modèles open-source hébergés

            QUAND L'UTILISER :
            - L'utilisateur veut un modèle plus rapide/moins cher → haiku, gpt-4o-mini
            - L'utilisateur veut plus de capacité → opus, gpt-4o
            - L'utilisateur veut changer de provider

            EXEMPLE :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                model_provider_id="anthropic",
                model_id="claude-opus-4-5"
            )

        ────────────────────────────────────────────────────────
        temperature (float, optionnel)
        ────────────────────────────────────────────────────────
            Niveau de créativité du modèle. Valeur entre 0.0 et 1.0.

            RECOMMANDATIONS :
            - 0.0 → 0.3 : tâches factuelles, analyse, code, SQL
            - 0.4 → 0.6 : usage général, Q&A, résumés
            - 0.7 → 1.0 : créativité, brainstorming, rédaction libre

            EXEMPLE :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                temperature=0.2
            )

        ────────────────────────────────────────────────────────
        user_favorite (bool, optionnel)
        ────────────────────────────────────────────────────────
            Ajoute (True) ou retire (False) l'agent des favoris
            de l'utilisateur courant uniquement.
            N'affecte PAS la configuration de l'agent lui-même.

        ────────────────────────────────────────────────────────
        skills_json (str, optionnel) — JSON stringifié
        ────────────────────────────────────────────────────────
            Liste des skills à activer sur l'agent.
            ⚠️ REMPLACE INTÉGRALEMENT la liste actuelle des skills.
            ⚠️ Chaque skill DOIT avoir "sId" ET "name" (tous deux requis).

            QUAND L'UTILISER :
            - L'utilisateur veut ajouter un skill à l'agent
            - L'utilisateur veut supprimer un skill
            - L'utilisateur veut remplacer tous les skills

            MARCHE À SUIVRE POUR AJOUTER UN SKILL :
            1. get_agent_yaml(agent_sid) → récupère la liste actuelle des skills
            2. Ajoute le nouveau skill à la liste existante (ne pas écraser les autres)
            3. Envoie la liste complète mise à jour

            MARCHE À SUIVRE POUR SUPPRIMER UN SKILL :
            1. get_agent_yaml(agent_sid) → récupère la liste actuelle
            2. Retire le skill concerné de la liste
            3. Envoie la liste complète sans ce skill

            FORMAT ATTENDU (JSON stringifié) :
            '[{"sId": "skill_id_1", "name": "NomDuSkill1"},
              {"sId": "skill_id_2", "name": "NomDuSkill2"}]'

            EXEMPLE — ajouter 2 skills :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                skills_json='[{"sId": "abc123", "name": "Web Search"},
                              {"sId": "def456", "name": "Code Sandbox"}]'
            )

            EXEMPLE — supprimer tous les skills :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                skills_json='[]'
            )

        ────────────────────────────────────────────────────────
        toolset_json (str, optionnel) — JSON stringifié
        ────────────────────────────────────────────────────────
            Liste des outils MCP à connecter à l'agent.
            ⚠️ REMPLACE INTÉGRALEMENT le toolset actuel.

            QUAND L'UTILISER :
            - L'utilisateur veut connecter un serveur MCP à l'agent
            - L'utilisateur veut déconnecter un outil
            - L'utilisateur veut remplacer tous les outils

            MARCHE À SUIVRE POUR AJOUTER UN OUTIL MCP :
            1. get_agent_yaml(agent_sid) → récupère le toolset actuel complet
            2. Ajoute le nouvel outil MCP à la liste (ne pas écraser les autres)
            3. Envoie la liste complète mise à jour

            FORMAT D'UN OUTIL MCP :
            {
              "type": "MCP",
              "name": "Nom affiché de l'outil",
              "description": "Ce que fait cet outil (aide l'agent à décider quand l'utiliser)",
              "configuration": {
                "url": "https://mon-serveur-mcp.railway.app/sse",
                "headers": {}
              }
            }

            EXEMPLE — connecter 1 serveur MCP :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                toolset_json='[{
                  "type": "MCP",
                  "name": "Mon Serveur MCP",
                  "description": "Gère les agents Dust via API",
                  "configuration": {
                    "url": "https://mon-serveur.railway.app/sse",
                    "headers": {}
                  }
                }]'
            )

            EXEMPLE — ajouter un outil à un toolset existant de 2 outils :
            # Supposons que get_agent_yaml retourne déjà 2 outils existants
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                toolset_json='[
                  {"type":"MCP","name":"Outil 1","description":"...","configuration":{"url":"https://outil1.railway.app/sse","headers":{}}},
                  {"type":"MCP","name":"Outil 2","description":"...","configuration":{"url":"https://outil2.railway.app/sse","headers":{}}},
                  {"type":"MCP","name":"Nouvel Outil","description":"...","configuration":{"url":"https://nouvel-outil.railway.app/sse","headers":{}}}
                ]'
            )

            EXEMPLE — supprimer tous les outils :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                toolset_json='[]'
            )

        ────────────────────────────────────────────────────────
        tags_json (str, optionnel) — JSON stringifié
        ────────────────────────────────────────────────────────
            Liste des tags à appliquer à l'agent.
            ⚠️ REMPLACE INTÉGRALEMENT les tags actuels.

            FORMAT ATTENDU (JSON stringifié) :
            '[{"name": "nom-du-tag", "kind": "standard"}]'

            kind peut valoir : "standard" ou "protected"

            EXEMPLE :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                tags_json='[{"name": "rh"}, {"name": "production"}]'
            )

        ════════════════════════════════════════════════════════
        EXEMPLES COMBINÉS
        ════════════════════════════════════════════════════════

        # Changer modèle + température + instructions en une seule fois :
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            instructions="Tu es un assistant factuel. Réponds en moins de 3 phrases.",
            model_provider_id="anthropic",
            model_id="claude-haiku-3-5",
            temperature=0.1
        )

        # Ajouter un serveur MCP sans toucher aux autres paramètres :
        # (récupère d'abord le toolset actuel via get_agent_yaml)
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            toolset_json='[...toolset_existant..., {"type":"MCP",...}]'
        )

        ════════════════════════════════════════════════════════
        RETOURNE
        ════════════════════════════════════════════════════════
        JSON contenant agentConfiguration avec la config complète
        de l'agent après modification, incluant :
        id, sId, version, name, description, instructions,
        model, actions, status, scope, tags, skills.
        """
        try:
            # ── Validation ─────────────────────────────────────────
            if not agent_sid or not agent_sid.strip():
                return json.dumps({
                    "error": "agent_sid est obligatoire.",
                    "hint" : "Utilise list_agent_configurations ou "
                             "search_agent_by_name pour trouver le sId."
                }, ensure_ascii=False)

            # ── Construction du body PATCH ─────────────────────────
            # STRUCTURE CORRECTE : tous les champs sont au niveau RACINE.
            # L'objet "agent" ne contient QUE les métadonnées
            # (handle, description, scope, etc.), PAS instructions ni model.

            body = {}

            # 1. userFavorite → racine
            if user_favorite is not None:
                body["userFavorite"] = user_favorite

            # 2. instructions → racine (PAS dans "agent")
            if instructions is not None:
                body["instructions"] = instructions

            # 3. generation_settings → racine, clés en snake_case
            #    ⚠️ Les clés sont provider_id et model_id (snake_case),
            #    PAS providerId / modelId (camelCase).
            generation_settings = {}
            if model_provider_id is not None:
                generation_settings["provider_id"] = model_provider_id  # snake_case ✅
            if model_id is not None:
                generation_settings["model_id"] = model_id              # snake_case ✅
            if temperature is not None:
                if not (0.0 <= temperature <= 1.0):
                    return json.dumps({
                        "error": f"temperature doit être entre 0.0 et 1.0 "
                                 f"(reçu : {temperature})"
                    }, ensure_ascii=False)
                generation_settings["temperature"] = temperature

            if generation_settings:
                body["generation_settings"] = generation_settings       # racine ✅

            # 4. skills → racine (PAS dans "agent")
            #    Chaque skill requiert "sId" ET "name" (tous deux obligatoires).
            if skills_json is not None:
                try:
                    parsed_skills = json.loads(skills_json)
                    if not isinstance(parsed_skills, list):
                        raise ValueError("skills_json doit être un tableau JSON.")
                    for i, skill in enumerate(parsed_skills):
                        if "sId" not in skill:
                            raise ValueError(
                                f"Le skill à l'index {i} manque du champ 'sId'."
                            )
                        if "name" not in skill:
                            raise ValueError(
                                f"Le skill à l'index {i} manque du champ 'name' "
                                f"(requis par l'API Dust)."
                            )
                    body["skills"] = parsed_skills                       # racine ✅
                except (json.JSONDecodeError, ValueError) as e:
                    return json.dumps({
                        "error": f"skills_json invalide : {e}",
                        "hint" : 'Format attendu : \'[{"sId": "abc123", "name": "NomSkill"}]\''
                    }, ensure_ascii=False)

            # 5. toolset → racine (PAS dans "agent")
            if toolset_json is not None:
                try:
                    parsed_toolset = json.loads(toolset_json)
                    if not isinstance(parsed_toolset, list):
                        raise ValueError("toolset_json doit être un tableau JSON.")
                    body["toolset"] = parsed_toolset                     # racine ✅
                except (json.JSONDecodeError, ValueError) as e:
                    return json.dumps({
                        "error": f"toolset_json invalide : {e}",
                        "hint" : 'Format attendu : \'[{"type": "MCP", "name": "...", '
                                 '"description": "...", "configuration": {"url": "...", "headers": {}}}]\''
                    }, ensure_ascii=False)

            # 6. tags → racine (PAS dans "agent")
            if tags_json is not None:
                try:
                    parsed_tags = json.loads(tags_json)
                    if not isinstance(parsed_tags, list):
                        raise ValueError("tags_json doit être un tableau JSON.")
                    body["tags"] = parsed_tags                           # racine ✅
                except (json.JSONDecodeError, ValueError) as e:
                    return json.dumps({
                        "error": f"tags_json invalide : {e}",
                        "hint" : 'Format attendu : \'[{"name": "mon-tag", "kind": "standard"}]\''
                    }, ensure_ascii=False)

            # 7. Rien à modifier → sortie anticipée
            if not body:
                return json.dumps({
                    "error": "Aucun paramètre fourni. Rien à modifier.",
                    "hint" : "Fournis au moins un paramètre parmi : instructions, "
                             "model_provider_id, model_id, temperature, user_favorite, "
                             "skills_json, toolset_json, tags_json."
                }, ensure_ascii=False)

            # ── Appel API ──────────────────────────────────────────
            endpoint = (
                f"/api/v1/w/{DUST_WORKSPACE_ID}"
                f"/assistant/agent_configurations/{agent_sid.strip()}"
            )
            result = dust_patch(endpoint, body)
            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
