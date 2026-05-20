# =============================================================
# tools/get_workspace_usage.py
# =============================================================
# Tool MCP : récupère les données d'usage du workspace Dust
#
# ⚠️  DEPRECATION NOTICE :
#     Cet endpoint sera supprimé après le 01/06/2026.
#     Le endpoint de remplacement sera :
#     GET /api/v1/w/{wId}/analytics/export
#     → Mettre à jour ce tool dès que Dust publiera la nouvelle doc.
#
# Endpoint : GET /api/v1/w/{wId}/workspace-usage
# =============================================================

import json
import requests                          # Utilisé directement (pas dust_get)
                                         # car la réponse peut être JSON ou CSV
from config import DUST_API_KEY, DUST_WORKSPACE_ID

BASE_URL = "https://dust.tt/api/v1"     # Identique à utils/dust.py


def register(mcp):
    """
    Enregistre le tool 'get_workspace_usage' dans le serveur MCP.
    Appelé par server.py au démarrage via tools.get_workspace_usage.register(mcp).

    Note : on n'utilise pas dust_get() de utils/dust.py car cet endpoint
    peut retourner du JSON, du CSV ou un ZIP selon les paramètres.
    On fait donc la requête HTTP directement pour garder le contrôle.
    """

    @mcp.tool()
    def get_workspace_usage(
        start           : str,
        table           : str,
        mode            : str  = "month",
        end             : str  = None,
        include_inactive: bool = False
    ) -> str:
        """
        Récupère les données d'usage du workspace Dust pour une période donnée.

        ⚠️  DEPRECATION : cet endpoint sera supprimé après le 01/06/2026.
            Futur endpoint de remplacement : GET /api/v1/w/{wId}/analytics/export

        Cas d'usage typiques :
          - Quels agents sont les plus utilisés ?       → table="assistants"
          - Combien de messages ont été envoyés ?       → table="assistant_messages"
          - Qui utilise le plus Dust ?                  → table="users"
          - Qui crée le plus d'agents ?                 → table="builders"
          - Quels feedbacks ont été donnés ?            → table="feedback"

        Args:
            start            : Date de début — format YYYY-MM ou YYYY-MM-DD.
                               Exemples : "2026-05" (mai 2026), "2026-05-01".

            table            : Type de données à récupérer :
                               - "users"             : utilisateurs et niveau d'activité
                               - "assistant_messages": messages envoyés avec agents mentionnés
                               - "builders"          : créateurs d'agents et leur activité
                               - "assistants"        : agents du workspace et leur usage
                               - "feedback"          : feedbacks sur les réponses d'agents
                               ⚠️ "all" non supporté (retourne un ZIP binaire non lisible)

            mode             : Mode de sélection de période :
                               - "month" (défaut) : analyse le mois indiqué dans 'start'
                               - "range"          : analyse sur la plage start → end

            end              : Date de fin — OBLIGATOIRE si mode="range".
                               Format YYYY-MM ou YYYY-MM-DD.

            include_inactive : Si True, inclut les utilisateurs/agents avec 0 messages.
                               Défaut : False.

        Returns:
            JSON contenant les données d'usage selon la table demandée.
        """
        try:
            # ── Validation de 'table' ──────────────────────────────────────
            # "all" est exclu : il retourne un ZIP binaire illisible par un LLM
            valid_tables = ["users", "assistant_messages", "builders", "assistants", "feedback"]
            if table not in valid_tables:
                return json.dumps({
                    "error": f"Table invalide : '{table}'. Valeurs acceptées : {valid_tables}.",
                    "note" : "'all' n'est pas supporté car il retourne un fichier ZIP binaire. "
                             "Appelez le tool plusieurs fois avec chaque table si besoin."
                }, ensure_ascii=False)

            # ── Validation de 'mode' ───────────────────────────────────────
            if mode not in ["month", "range"]:
                return json.dumps({
                    "error": f"Mode invalide : '{mode}'. Valeurs acceptées : ['month', 'range']."
                }, ensure_ascii=False)

            # ── Validation de 'end' si mode=range ─────────────────────────
            if mode == "range" and not end:
                return json.dumps({
                    "error": "Le paramètre 'end' est obligatoire quand mode='range'. "
                             "Exemple : start='2026-01', end='2026-05', mode='range'."
                }, ensure_ascii=False)

            # ── Construction des paramètres de requête ────────────────────
            params = {
                "start"          : start,
                "mode"           : mode,
                "table"          : table,
                "format"         : "json",                        # On force JSON pour lisibilité
                "includeInactive": str(include_inactive).lower(), # "true" ou "false"
            }
            # 'end' ajouté seulement en mode range
            if end and mode == "range":
                params["end"] = end

            # ── Headers d'authentification ─────────────────────────────────
            headers = {
                "Authorization": f"Bearer {DUST_API_KEY}",
                "Accept"       : "application/json",
            }

            # ── Appel HTTP ─────────────────────────────────────────────────
            r = requests.get(
                f"{BASE_URL}/w/{DUST_WORKSPACE_ID}/workspace-usage",
                headers=headers,
                params=params,
                timeout=30,   # 30s max — les données d'usage peuvent être volumineuses
            )

            # ── Gestion des erreurs HTTP ───────────────────────────────────
            if not r.ok:
                # Hints spécifiques aux codes d'erreur documentés par l'API Dust
                hints = {
                    400: "Paramètres invalides. Vérifiez le format de 'start'/'end' (YYYY-MM ou YYYY-MM-DD).",
                    403: "Ce workspace n'a pas accès à l'API d'usage (plan insuffisant).",
                    404: "Workspace introuvable. Vérifiez DUST_WORKSPACE_ID.",
                    405: "Méthode non supportée.",
                }
                return json.dumps({
                    "error": f"HTTP {r.status_code}: {r.text[:400]}",
                    "hint" : hints.get(r.status_code, ""),
                }, ensure_ascii=False)

            # ── Parsing de la réponse ──────────────────────────────────────
            # Avec format=json la réponse devrait être du JSON valide.
            # En cas d'échec (CSV retourné malgré format=json), on renvoie le texte brut.
            try:
                data = r.json()
                return json.dumps(data, ensure_ascii=False, indent=2)
            except ValueError:
                return json.dumps({
                    "warning" : "La réponse reçue n'est pas du JSON — voici le texte brut :",
                    "raw_data": r.text[:5000],  # Limité à 5000 chars
                }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "table": table,
                "start": start,
            }, ensure_ascii=False)
