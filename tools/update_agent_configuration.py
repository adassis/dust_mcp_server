# =============================================================
# tools/update_agent_configuration.py
# =============================================================
# Tool MCP : modifie la configuration d'un agent Dust existant.
#
# Endpoint : PATCH /api/v1/w/{wId}/assistant/agent_configurations/{sId}
# Body     : JSON partiel — seuls les champs envoyés sont modifiés.
# Retourne : la configuration complète mise à jour de l'agent.
#
# ⚠️  COMPORTEMENT PATCH (partiel) :
#     Seuls les champs que tu inclus dans le body seront modifiés.
#     Les champs absents du body restent INCHANGÉS.
#     EXCEPTION : skills et toolset sont des remplacements complets
#     (si tu les envoies, ils écrasent toute la liste existante).
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

        PRINCIPE FONDAMENTAL (PATCH) :
        --------------------------------
        Seuls les paramètres que tu fournis seront modifiés.
        Tout paramètre laissé à None reste INCHANGÉ côté Dust.
        Ne modifie QUE ce que l'utilisateur demande explicitement.

        WORKFLOW OBLIGATOIRE AVANT TOUTE MODIFICATION :
        -------------------------------------------------
        1. Utilise get_agent_yaml(agent_sid) pour voir la config actuelle.
        2. Identifie précisément ce qui doit changer.
        3. N'envoie QUE les champs à modifier.
        4. Reconfirme le résultat avec get_agent_yaml après la mise à jour.

        PARAMÈTRES :
        -------------
        agent_sid (str, OBLIGATOIRE) :
            Identifiant unique de l'agent à modifier (ex: "7f3a9c2b1e").
            Récupérable via list_agent_configurations ou search_agent_by_name.

        instructions (str, optionnel) :
            Nouvelles instructions système de l'agent (le "system prompt").
            Remplace intégralement les instructions existantes.
            ⚠️  Envoie le texte complet des nouvelles instructions,
            pas juste la partie modifiée.
            Exemple : "Tu es un assistant RH. Réponds toujours en français."

        model_provider_id (str, optionnel) :
            Fournisseur du modèle LLM à utiliser.
            Valeurs possibles : "anthropic", "openai", "google_ai_studio",
                                "mistral", "togetherai"
            ⚠️  Doit être cohérent avec model_id.
            Exemple : "anthropic"

        model_id (str, optionnel) :
            Identifiant du modèle LLM spécifique.
            ⚠️  Doit correspondre au model_provider_id fourni.
            Exemples par provider :
              - anthropic  → "claude-opus-4-5", "claude-sonnet-4-5",
                             "claude-haiku-3-5"
              - openai     → "gpt-4o", "gpt-4o-mini", "o1", "o3-mini"
              - google     → "gemini-2.0-flash-001", "gemini-1.5-pro"
              - mistral    → "mistral-large-latest", "mistral-small-latest"

        temperature (float, optionnel) :
            Niveau de créativité/aléatoire du modèle.
            Valeur entre 0.0 (déterministe, réponses consistantes)
            et 1.0 (créatif, réponses variées).
            Recommandations :
              - 0.0 à 0.3 : tâches factuelles, analyse, code
              - 0.4 à 0.7 : usage général, Q&A, résumés
              - 0.7 à 1.0 : créativité, brainstorming, rédaction
            Exemple : 0.5

        user_favorite (bool, optionnel) :
            Ajoute (True) ou retire (False) l'agent des favoris
            de l'utilisateur courant.
            N'affecte PAS la configuration de l'agent lui-même.
            Exemple : True

        skills_json (str, optionnel) :
            Liste JSON des skills à activer sur l'agent.
            ⚠️  REMPLACE INTÉGRALEMENT la liste actuelle des skills.
            Si tu envoies une liste vide [], tous les skills sont supprimés.
            Utilise get_agent_yaml avant pour voir les skills actuels.
            Format attendu (JSON stringifié) :
              '[{"sId": "skill_id_1"}, {"sId": "skill_id_2"}]'
            Exemple pour activer 2 skills :
              '[{"sId": "abc123"}, {"sId": "def456"}]'
            Exemple pour supprimer tous les skills :
              '[]'

        toolset_json (str, optionnel) :
            Liste JSON des outils/actions à configurer sur l'agent.
            ⚠️  REMPLACE INTÉGRALEMENT le toolset actuel.
            Utilise get_agent_yaml avant pour voir le toolset actuel.
            Format attendu (JSON stringifié) :
              '[{"type": "tool_type", "sId": "tool_id"}]'

        tags_json (str, optionnel) :
            Liste JSON des tags à appliquer à l'agent.
            Format attendu (JSON stringifié) :
              '[{"sId": "tag_id_1"}, {"sId": "tag_id_2"}]'

        RETOURNE :
        ----------
        JSON contenant agentConfiguration avec la config complète
        de l'agent après modification, incluant : id, sId, version,
        name, description, instructions, model, actions, status, scope.

        EXEMPLES D'USAGE :
        -------------------
        # Modifier uniquement les instructions :
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            instructions="Tu es un assistant RH expert."
        )

        # Changer le modèle vers Claude Opus :
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            model_provider_id="anthropic",
            model_id="claude-opus-4-5"
        )

        # Modifier instructions + température en même temps :
        update_agent_configuration(
            agent_sid="7f3a9c2b1e",
            instructions="Réponds toujours de façon concise.",
            temperature=0.3
        )
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
            # On ne construit que les parties du body qui sont demandées.
            # Les champs None ne sont jamais envoyés à l'API.

            body = {}

            # userFavorite est au niveau racine (pas dans "agent")
            if user_favorite is not None:
                body["userFavorite"] = user_favorite

            # Tout le reste va dans l'objet "agent"
            agent_payload = {}

            if instructions is not None:
                agent_payload["instructions"] = instructions

            # generation_settings regroupe provider, model et temperature
            # On ne l'envoie que si au moins un des 3 est fourni
            generation_settings = {}
            if model_provider_id is not None:
                generation_settings["providerId"] = model_provider_id
            if model_id is not None:
                generation_settings["modelId"] = model_id
            if temperature is not None:
                if not (0.0 <= temperature <= 1.0):
                    return json.dumps({
                        "error": f"temperature doit être entre 0.0 et 1.0 "
                                 f"(reçu : {temperature})"
                    }, ensure_ascii=False)
                generation_settings["temperature"] = temperature

            if generation_settings:
                agent_payload["generation_settings"] = generation_settings

            # skills : parse le JSON string → liste Python
            if skills_json is not None:
                try:
                    parsed_skills = json.loads(skills_json)
                    if not isinstance(parsed_skills, list):
                        raise ValueError("skills_json doit être un tableau JSON.")
                    agent_payload["skills"] = parsed_skills
                except (json.JSONDecodeError, ValueError) as e:
                    return json.dumps({
                        "error": f"skills_json invalide : {e}",
                        "hint" : "Format attendu : '[{\"sId\": \"abc123\"}]'"
                    }, ensure_ascii=False)

            # toolset : parse le JSON string → liste Python
            if toolset_json is not None:
                try:
                    parsed_toolset = json.loads(toolset_json)
                    if not isinstance(parsed_toolset, list):
                        raise ValueError("toolset_json doit être un tableau JSON.")
                    agent_payload["toolset"] = parsed_toolset
                except (json.JSONDecodeError, ValueError) as e:
                    return json.dumps({
                        "error": f"toolset_json invalide : {e}",
                        "hint" : "Format attendu : '[{\"type\": \"tool_type\"}]'"
                    }, ensure_ascii=False)

            # tags : parse le JSON string → liste Python
            if tags_json is not None:
                try:
                    parsed_tags = json.loads(tags_json)
                    if not isinstance(parsed_tags, list):
                        raise ValueError("tags_json doit être un tableau JSON.")
                    agent_payload["tags"] = parsed_tags
                except (json.JSONDecodeError, ValueError) as e:
                    return json.dumps({
                        "error": f"tags_json invalide : {e}",
                        "hint" : "Format attendu : '[{\"sId\": \"tag_id\"}]'"
                    }, ensure_ascii=False)

            if agent_payload:
                body["agent"] = agent_payload

            # Sécurité : si body est vide, rien à faire
            if not body:
                return json.dumps({
                    "error": "Aucun champ à modifier fourni.",
                    "hint" : "Fournis au moins un paramètre parmi : "
                             "instructions, model_provider_id, model_id, "
                             "temperature, user_favorite, skills_json, "
                             "toolset_json, tags_json."
                }, ensure_ascii=False)

            # ── Appel API ──────────────────────────────────────────
            path = (
                f"/w/{DUST_WORKSPACE_ID}"
                f"/assistant/agent_configurations/{agent_sid.strip()}"
            )

            result = dust_patch(path, body)

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                "error"    : str(e),
                "agent_sid": agent_sid
            }, ensure_ascii=False)
