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
#
# ⚠️ BASE_URL dans utils/dust.py = "https://dust.tt/api/v1"
# → Le path ici commence par /w/ (PAS /api/v1/w/)
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
        reasoning_effort: str = None,
        max_steps_per_run: int = None,      # ← AJOUTÉ
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
        Les champs sont au NIVEAU RACINE du body, PAS imbriqués.
        EXCEPTION : max_steps_per_run et visualization_enabled
        sont dans le sous-objet "agent".

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
                                   "gemini-2.5-flash"
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
            Niveau de créativité du modèle.

            VALEURS POSSIBLES : float entre 0.0 et 1.0 (inclus)

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
        reasoning_effort (str, optionnel)
        ────────────────────────────────────────────────────────
            Contrôle le niveau de raisonnement étendu (extended thinking)
            du modèle. Fait partie de generation_settings.

            VALEURS POSSIBLES (enum strict) :
            - "none"   : raisonnement désactivé
            - "light"  : raisonnement minimal, réponses plus rapides
            - "medium" : équilibre vitesse / profondeur (défaut courant)
            - "high"   : raisonnement approfondi, meilleure qualité
                         sur les tâches complexes (plus lent)

            ⚠️ La valeur "low" N'EXISTE PAS dans l'API Dust.
               Utiliser "light" pour le niveau le plus bas.

            COMPATIBILITÉ :
            Tous les modèles ne supportent pas reasoning_effort.
            Modèles compatibles connus :
            - google_ai_studio : gemini-2.5-flash, gemini-2.5-pro
            - anthropic        : claude-opus-4-5 (extended thinking)
            - openai           : o1, o3-mini (effort paramétrable)

            QUAND L'UTILISER :
            - L'utilisateur veut "activer le raisonnement avancé"
            - L'utilisateur veut "plus de réflexion", "extended thinking"
            - L'utilisateur veut accélérer les réponses → "light"
            - L'utilisateur veut plus de qualité sur tâches complexes → "high"

            EXEMPLE — passer le raisonnement à "high" :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                reasoning_effort="high"
            )

            EXEMPLE — combiner changement de modèle + reasoning_effort :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                model_provider_id="google_ai_studio",
                model_id="gemini-2.5-flash",
                reasoning_effort="high"
            )

        ────────────────────────────────────────────────────────
        max_steps_per_run (int, optionnel)
        ────────────────────────────────────────────────────────
            Nombre maximum d'étapes (appels LLM + tools) que l'agent
            peut enchaîner en une seule conversation.
            Envoyé dans le sous-objet "agent" du body PATCH.

            VALEURS POSSIBLES : entier entre 1 et 64 (inclus)

            RECOMMANDATIONS :
            - 1  → 5  : agent ultra-simple, réponse directe sans tool
            - 6  → 15 : workflow linéaire, 3 à 7 outils max
            - 16 → 30 : workflow multi-étapes, boucles légères
            - 31 → 64 : agent complexe / orchestrateur (défaut Dust = 64)

            ⚠️ Une valeur trop haute consomme inutilement des tokens si
               l'agent entre dans une boucle. Préférer une valeur adaptée
               au workflow réel de l'agent.

            QUAND L'UTILISER :
            - L'utilisateur veut limiter les coûts token sur un agent simple
            - L'utilisateur veut éviter les boucles infinies
            - L'agent a un workflow clair en N étapes → max = N * 2 + marge

            EXEMPLE — réduire à 10 pour un agent 3 étapes :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                max_steps_per_run=10
            )

            EXEMPLE — combiner avec reasoning_effort :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                max_steps_per_run=10,
                reasoning_effort="light"
            )

        ────────────────────────────────────────────────────────
        user_favorite (bool, optionnel)
        ────────────────────────────────────────────────────────
            Ajoute (True) ou retire (False) l'agent des favoris
            de l'utilisateur courant uniquement.
            N'affecte PAS la configuration de l'agent lui-même.

            VALEURS POSSIBLES : True | False

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
              "type": "MCP",                          ← seule valeur possible
              "name": "Nom affiché de l'outil",
              "description": "Ce que fait cet outil (aide l'agent à décider quand l'utiliser)",
              "configuration": {
                "mcp_server_name": "nom_du_serveur",  ← nom exact dans Dust
                "additional_configuration": {}        ← objet vide si pas de config spécifique
              }
            }

            EXEMPLE — connecter 1 serveur MCP interne Dust :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                toolset_json='[{
                  "type": "MCP",
                  "name": "Web Search",
                  "description": "Recherche web et navigation",
                  "configuration": {
                    "mcp_server_name": "web_search_&_browse",
                    "additional_configuration": {}
                  }
                }]'
            )

            EXEMPLE — ajouter un outil à un toolset existant de 2 outils :
            # Récupère d'abord le toolset complet via get_agent_yaml, puis :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                toolset_json='[
                  {"type":"MCP","name":"Outil 1","description":"...","configuration":{"mcp_server_name":"search","additional_configuration":{}}},
                  {"type":"MCP","name":"Outil 2","description":"...","configuration":{"mcp_server_name":"web_search_&_browse","additional_configuration":{}}},
                  {"type":"MCP","name":"Nouvel Outil","description":"...","configuration":{"mcp_server_name":"hubspot","additional_configuration":{}}}
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

            VALEURS POSSIBLES pour "kind" : "standard" | "protected"
            - "standard"  : tag normal, modifiable par les builders
            - "protected" : tag verrouillé, non modifiable dans l'UI

            EXEMPLE :
            update_agent_configuration(
                agent_sid="7f3a9c2b1e",
                tags_json='[{"name": "rh", "kind": "standard"},
                            {"name": "production", "kind": "protected"}]'
            )

        ════════════════════════════════════════════════════════
        EXEMPLES COMBINÉS
        ════════════════════════════════════════════════════════

        # Changer modèle + température + reasoning_effort en une seule fois :
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            model_provider_id="google_ai_studio",
            model_id="gemini-2.5-flash",
            temperature=0.7,
            reasoning_effort="high"
        )

        # Optimiser un agent simple (moins cher + plus rapide) :
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            model_provider_id="anthropic",
            model_id="claude-haiku-3-5",
            reasoning_effort="light",
            max_steps_per_run=10
        )

        # Changer uniquement le reasoning_effort sans toucher au reste :
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            reasoning_effort="high"
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
            # ── Validation agent_sid ───────────────────────────────
            if not agent_sid or not agent_sid.strip():
                return json.dumps({
                    "error": "agent_sid est obligatoire.",
                    "hint" : "Utilise list_agent_configurations ou "
                             "search_agent_by_name pour trouver le sId."
                }, ensure_ascii=False)

            # ── Validation reasoning_effort ────────────────────────
            # ⚠️ L'API Dust utilise "light", PAS "low".
            VALID_REASONING_EFFORTS = {"none", "light", "medium", "high"}
            if reasoning_effort is not None:
                if reasoning_effort not in VALID_REASONING_EFFORTS:
                    return json.dumps({
                        "error": f"reasoning_effort invalide : '{reasoning_effort}'.",
                        "hint" : "Valeurs acceptées : 'none', 'light', 'medium', 'high'. "
                                 "⚠️ Utiliser 'light' (et non 'low') pour le niveau minimal."
                    }, ensure_ascii=False)

            # ── Validation temperature ─────────────────────────────
            if temperature is not None:
                if not isinstance(temperature, (int, float)) or not (0.0 <= temperature <= 1.0):
                    return json.dumps({
                        "error": f"temperature doit être un float entre 0.0 et 1.0 "
                                 f"(reçu : {temperature})"
                    }, ensure_ascii=False)

            # ── Validation max_steps_per_run ───────────────────────
            if max_steps_per_run is not None:
                if not isinstance(max_steps_per_run, int) or not (1 <= max_steps_per_run <= 64):
                    return json.dumps({
                        "error": f"max_steps_per_run doit être un entier entre 1 et 64 "
                                 f"(reçu : {max_steps_per_run}).",
                        "hint" : "Valeurs recommandées : 5-10 pour un agent simple, "
                                 "10-30 pour un workflow multi-étapes, 64 = maximum Dust."
                    }, ensure_ascii=False)

            # ── Construction du body PATCH ─────────────────────────
            # STRUCTURE CORRECTE : tous les champs sont au niveau RACINE.
            # EXCEPTION : max_steps_per_run et visualization_enabled
            #             sont dans le sous-objet "agent".

            body = {}

            # 1. userFavorite → racine
            if user_favorite is not None:
                body["userFavorite"] = user_favorite

            # 2. instructions → racine (PAS dans "agent")
            if instructions is not None:
                body["instructions"] = instructions

            # 3. sous-objet "agent" : métadonnées + max_steps_per_run
            agent_patch = {}
            if max_steps_per_run is not None:
                agent_patch["max_steps_per_run"] = max_steps_per_run
            if agent_patch:
                body["agent"] = agent_patch                              # ✅

            # 4. generation_settings → racine, clés en snake_case
            #    Regroupe : provider_id, model_id, temperature, reasoning_effort
            #    ⚠️ Les clés sont snake_case (PAS camelCase).
            generation_settings = {}
            if model_provider_id is not None:
                generation_settings["provider_id"] = model_provider_id  # snake_case ✅
            if model_id is not None:
                generation_settings["model_id"] = model_id              # snake_case ✅
            if temperature is not None:
                generation_settings["temperature"] = temperature
            if reasoning_effort is not None:
                generation_settings["reasoning_effort"] = reasoning_effort

            if generation_settings:
                body["generation_settings"] = generation_settings       # racine ✅

            # 5. skills → racine (PAS dans "agent")
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

            # 6. toolset → racine (PAS dans "agent")
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
                                 '"description": "...", "configuration": '
                                 '{"mcp_server_name": "...", "additional_configuration": {}}}]\''
                    }, ensure_ascii=False)

            # 7. tags → racine (PAS dans "agent")
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
                                 " — kind : \"standard\" | \"protected\""
                    }, ensure_ascii=False)

            # 8. Rien à modifier → sortie anticipée
            if not body:
                return json.dumps({
                    "error": "Aucun paramètre fourni. Rien à modifier.",
                    "hint" : "Fournis au moins un paramètre parmi : instructions, "
                             "model_provider_id, model_id, temperature, reasoning_effort, "
                             "max_steps_per_run, user_favorite, skills_json, toolset_json, "
                             "tags_json."
                }, ensure_ascii=False)

            # ── Appel API ──────────────────────────────────────────
            # ⚠️ BASE_URL = "https://dust.tt/api/v1" (déjà dans utils/dust.py)
            # → Le path commence par /w/ uniquement, PAS /api/v1/w/
            endpoint = (
                f"/w/{DUST_WORKSPACE_ID}"                                # ✅ sans /api/v1
                f"/assistant/agent_configurations/{agent_sid.strip()}"
            )
            result = dust_patch(endpoint, body)
            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
