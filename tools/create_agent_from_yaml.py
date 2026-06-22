# =============================================================
# tools/create_agent_from_yaml.py
# =============================================================
# Tool MCP : crée un nouvel agent Dust à partir d'une
# configuration YAML (texte brut).
#
# Endpoint : POST /api/v1/w/{wId}/assistant/agent_configurations/import
# Body : JSON complet de la configuration agent
# Retourne : la configuration complète du nouvel agent créé.
#
# Sources YAML acceptées :
# - Sortie de get_agent_yaml(agent_sid) → cloner/dupliquer un agent existant
# - YAML rédigé manuellement selon le schéma Dust
#
# ⚠️ Cet endpoint CRÉE toujours un NOUVEL agent (nouveau sId).
#    Pour modifier un agent existant, utiliser update_agent_configuration.
# =============================================================

import json
import yaml          # pip install pyyaml
from utils.dust import dust_post
from config import DUST_WORKSPACE_ID

def register(mcp):

    @mcp.tool()
    def create_agent_from_yaml(yaml_content: str) -> str:
        """
        Crée un nouvel agent Dust à partir d'une configuration YAML.

        ════════════════════════════════════════════════════════
        QUAND UTILISER CE TOOL
        ════════════════════════════════════════════════════════
        - Créer un nouvel agent from scratch via une config YAML
        - Dupliquer/cloner un agent existant :
            1. get_agent_yaml(sId_source) → récupère le YAML de l'agent source
            2. Modifie le champ "name" dans le YAML (nouveau nom obligatoire)
            3. create_agent_from_yaml(yaml_modifié) → crée le clone

        ⚠️ Crée TOUJOURS un NOUVEL agent avec un nouveau sId.
           Pour modifier un agent existant → update_agent_configuration.

        ════════════════════════════════════════════════════════
        SCHÉMA YAML ATTENDU
        ════════════════════════════════════════════════════════

        Champs OBLIGATOIRES :
        ─────────────────────
        name         (str)   : Nom de l'agent (handle). Doit être unique.
                               Ex: "Mon Agent RH"
        instructions (str)   : System prompt complet de l'agent.
                               Supporte le multiline avec le pipe YAML (|)
        model        (dict)  : Configuration du modèle LLM (voir ci-dessous)

        Champs du bloc "model" (tous obligatoires) :
        ─────────────────────────────────────────────
        model.provider_id    (str)   : Provider LLM
                                       Valeurs : "anthropic", "openai",
                                       "google_ai_studio", "mistral", "togetherai"
        model.model_id       (str)   : Identifiant du modèle
                                       Ex: "claude-sonnet-4-5", "gpt-4o",
                                           "gemini-2.5-flash"
        model.temperature    (float) : Créativité du modèle (0.0 → 1.0)
                                       0.0 = factuel, 1.0 = créatif

        Champs OPTIONNELS :
        ────────────────────
        description          (str)   : Description courte de l'agent
        scope                (str)   : Visibilité. Valeurs : "visible" (défaut),
                                       "hidden", "workspace", "published"
        avatar_url           (str)   : URL de l'emoji/image de l'agent
                                       Ex: "https://dust.tt/static/emojis/..."
        max_steps_per_run    (int)   : Nombre max d'étapes par run (défaut: 64)
        visualization_enabled (bool) : Active les visualisations (défaut: false)
        model.reasoning_effort (str) : Raisonnement étendu : "low", "medium", "high"
        tags                 (list)  : Tags de l'agent. Format :
                                       [{name: "tag1"}, {name: "tag2"}]
        editors              (list)  : Éditeurs autorisés. Format :
                                       [{email: "user@example.com"}]
        toolset              (list)  : Outils MCP à connecter. Format :
                                       [{type: "MCP", name: "...",
                                         description: "...",
                                         configuration: {url: "...", headers: {}}}]
        skills               (list)  : Skills à activer. Format :
                                       [{sId: "abc123", name: "NomSkill"}]

        ════════════════════════════════════════════════════════
        EXEMPLES DE YAML
        ════════════════════════════════════════════════════════

        # Exemple minimal (obligatoires uniquement) :
        ---
        name: Mon Assistant RH
        instructions: |
          Tu es un assistant RH expert.
          Réponds toujours en français, de façon concise et professionnelle.
        model:
          provider_id: anthropic
          model_id: claude-sonnet-4-5
          temperature: 0.5

        ────────────────────────────────────────────────────────

        # Exemple complet :
        ---
        name: Assistant Data Analyst
        description: Analyse de données et visualisations
        scope: visible
        max_steps_per_run: 32
        visualization_enabled: true
        instructions: |
          Tu es un data analyst expert en Python, SQL et visualisation.
          Tu expliques chaque étape de ton analyse.
        model:
          provider_id: google_ai_studio
          model_id: gemini-2.5-flash
          temperature: 0.2
          reasoning_effort: high
        tags:
          - name: data
          - name: analyse
        toolset:
          - type: MCP
            name: Mon Serveur MCP
            description: Accès aux données de l'entreprise
            configuration:
              url: https://mon-serveur.railway.app/sse
              headers: {}
        skills:
          - sId: abc123
            name: Web Search

        ────────────────────────────────────────────────────────

        # Cloner un agent existant :
        # 1. yaml_existant = get_agent_yaml("sId_source")
        # 2. Modifie "name:" dans le YAML
        # 3. create_agent_from_yaml(yaml_modifié)

        ════════════════════════════════════════════════════════
        NOTES SUR LES ACTIONS (mcpServerViewId)
        ════════════════════════════════════════════════════════
        Les actions Dust natives (web search, file browsing, etc.)
        utilisent un "mcpServerViewId" propre au workspace.
        Elles ne peuvent PAS être importées via ce endpoint —
        elles apparaîtront dans "skippedActions" dans la réponse.

        Pour ajouter des outils MCP externes → utilise "toolset".
        Pour les outils Dust natifs → configure-les manuellement
        via l'UI Dust après création de l'agent.

        ════════════════════════════════════════════════════════
        RETOURNE
        ════════════════════════════════════════════════════════
        JSON contenant :
        - agentConfiguration : config complète du nouvel agent
          (id, sId, version, name, instructions, model, actions...)
        - skippedActions : liste des actions ignorées (avec raison)

        Args:
            yaml_content (str) : Configuration de l'agent au format YAML
                                 (texte brut, multiline supporté)
        """
        try:
            # ── 1. Parse YAML → dict Python ────────────────────────
            # yaml.safe_load est sûr : il n'exécute pas de code arbitraire
            # contrairement à yaml.load()
            try:
                config = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                return json.dumps({
                    "error": f"YAML invalide : {e}",
                    "hint" : "Vérifie l'indentation (espaces, pas de tabulations) "
                             "et la syntaxe YAML."
                }, ensure_ascii=False)

            if not isinstance(config, dict):
                return json.dumps({
                    "error": "Le YAML doit être un objet (dict), pas une liste ou une valeur.",
                    "hint" : "Le YAML doit commencer par des clés : name:, instructions:, model:, ..."
                }, ensure_ascii=False)

            # ── 2. Validation des champs obligatoires ──────────────
            missing = []
            if not config.get("name"):
                missing.append("name")
            if config.get("instructions") is None:
                missing.append("instructions")
            if not config.get("model"):
                missing.append("model")
            elif not isinstance(config["model"], dict):
                return json.dumps({
                    "error": "'model' doit être un bloc YAML avec provider_id, model_id, temperature.",
                    "hint" : "Exemple :\nmodel:\n  provider_id: anthropic\n  model_id: claude-sonnet-4-5\n  temperature: 0.5"
                }, ensure_ascii=False)
            else:
                if not config["model"].get("provider_id"):
                    missing.append("model.provider_id")
                if not config["model"].get("model_id"):
                    missing.append("model.model_id")
                if config["model"].get("temperature") is None:
                    missing.append("model.temperature")

            if missing:
                return json.dumps({
                    "error": f"Champs obligatoires manquants : {', '.join(missing)}",
                    "hint" : "name, instructions, model.provider_id, model.model_id "
                             "et model.temperature sont requis."
                }, ensure_ascii=False)

            # ── 3. Validation reasoning_effort (si fourni) ─────────
            reasoning_effort = config["model"].get("reasoning_effort")
            VALID_EFFORTS = {"low", "medium", "high"}
            if reasoning_effort is not None and reasoning_effort not in VALID_EFFORTS:
                return json.dumps({
                    "error": f"model.reasoning_effort invalide : '{reasoning_effort}'.",
                    "hint" : "Valeurs acceptées : 'low', 'medium', 'high'."
                }, ensure_ascii=False)

            # ── 4. Validation temperature ──────────────────────────
            temperature = config["model"].get("temperature")
            if temperature is not None and not (0.0 <= float(temperature) <= 1.0):
                return json.dumps({
                    "error": f"model.temperature doit être entre 0.0 et 1.0 (reçu : {temperature})"
                }, ensure_ascii=False)

            # ── 5. Construction du body API ────────────────────────
            # Mapping YAML → structure attendue par l'endpoint /import
            # Référence : POST /api/v1/w/{wId}/assistant/agent_configurations/import

            # -- Bloc "agent" : métadonnées de l'agent ---------------
            agent_block = {
                "handle"     : config["name"],                      # "name" YAML → "handle" API
                "scope"      : config.get("scope", "visible"),      # défaut : visible
            }

            if config.get("description"):
                agent_block["description"] = config["description"]

            if config.get("avatar_url"):
                agent_block["avatar_url"] = config["avatar_url"]

            if config.get("max_steps_per_run") is not None:
                agent_block["max_steps_per_run"] = int(config["max_steps_per_run"])

            if config.get("visualization_enabled") is not None:
                agent_block["visualization_enabled"] = bool(config["visualization_enabled"])

            # -- generation_settings : modèle LLM --------------------
            generation_settings = {
                "provider_id" : config["model"]["provider_id"],   # snake_case ✅
                "model_id"    : config["model"]["model_id"],       # snake_case ✅
                "temperature" : float(config["model"]["temperature"]),
            }
            if reasoning_effort is not None:
                generation_settings["reasoning_effort"] = reasoning_effort

            # -- Listes (défaut : liste vide) ------------------------
            tags    = config.get("tags",    []) or []
            editors = config.get("editors", []) or []
            toolset = config.get("toolset", []) or []
            skills  = config.get("skills",  []) or []

            # -- Assemblage du body final ----------------------------
            body = {
                "agent"              : agent_block,
                "instructions"       : config["instructions"] or "",
                "generation_settings": generation_settings,
                "tags"               : tags,
                "editors"            : editors,
                "toolset"            : toolset,
            }

            # skills n'est pas dans la spec officielle /import mais
            # est supporté de la même façon que sur /patch
            if skills:
                body["skills"] = skills

            # ── 6. Appel API ───────────────────────────────────────
            # ⚠️ BASE_URL = "https://dust.tt/api/v1" (dans utils/dust.py)
            # → path commence par /w/ uniquement
            endpoint = f"/w/{DUST_WORKSPACE_ID}/assistant/agent_configurations/import"
            result   = dust_post(endpoint, body)

            # ── 7. Enrichissement de la réponse ────────────────────
            # On signale les actions ignorées pour que l'agent le sache
            skipped = result.get("skippedActions", [])
            if skipped:
                result["_info"] = (
                    f"{len(skipped)} action(s) ignorée(s) car elles utilisent "
                    f"des mcpServerViewId propres au workspace source et ne peuvent "
                    f"pas être importées automatiquement. "
                    f"Configure-les manuellement via l'UI Dust."
                )

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
