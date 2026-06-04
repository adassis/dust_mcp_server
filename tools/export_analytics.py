# =============================================================
# tools/export_analytics.py
# =============================================================
# Tool MCP : exporte les données analytiques du workspace Dust
# Endpoint : GET /api/v1/w/{wId}/analytics/export
# Doc : https://docs.dust.tt/reference/get_api-v1-w-wid-analytics-export
#
# ⚠️  PRÉREQUIS : ta clé API Dust doit avoir le scope "admin"
#     (une clé normale retourne HTTP 403)
#     → Dust > Settings > API Keys > créer une clé avec scope admin
# =============================================================

import json                        # Pour formater la réponse en texte JSON lisible
from typing import Optional        # Pour déclarer des paramètres optionnels avec type hint
from utils.dust import dust_get    # Client HTTP centralisé (gère auth + erreurs)
from config import DUST_WORKSPACE_ID  # ID du workspace, lu depuis les variables d'environnement

def register(mcp):
    """
    Enregistre le tool 'export_analytics' dans le serveur MCP.
    Cette fonction est appelée une seule fois au démarrage, dans server.py.
    """

    @mcp.tool()
    def export_analytics(
        table: str,
        start_date: str,
        end_date: str,
        timezone: Optional[str] = None,
    ) -> str:
        """
        Exporte les données analytiques du workspace Dust pour une période donnée.

        Utilise cet outil pour analyser l'usage de Dust sur ton workspace :
        nombre de messages, utilisateurs actifs, agents les plus utilisés,
        détail des conversations, etc.

        ⚠️  Nécessite une clé API Dust avec le scope "admin".

        Args:
            table : Le type de données à exporter. Valeurs possibles :
                - "usage_metrics"  : Messages, conversations et utilisateurs actifs dans le temps
                - "active_users"   : Compteurs d'utilisateurs actifs (jour / semaine / mois)
                - "source"         : Volume de messages par origine (web, Slack, API, etc.)
                - "agents"         : Top agents classés par nombre de messages reçus
                - "users"          : Top utilisateurs classés par nombre de messages envoyés
                - "skill_usage"    : Exécutions de skills et utilisateurs uniques dans le temps
                - "tool_usage"     : Exécutions de tools et utilisateurs uniques dans le temps
                - "messages"       : Logs détaillés message par message

            start_date : Date de début au format YYYY-MM-DD (ex: "2025-01-01")

            end_date : Date de fin au format YYYY-MM-DD (ex: "2025-12-31")

            timezone : (optionnel) Nom de timezone IANA pour interpréter les dates.
                       Ex: "Europe/Brussels", "America/New_York"
                       Si non fourni, UTC est utilisé par défaut.

        Returns:
            JSON contenant les données analytiques demandées.
            La structure varie selon la table choisie.
        """

        # ── Validation du paramètre 'table' ──────────────────────────────────
        # L'API Dust retournerait une erreur 400 si la valeur est invalide.
        # On préfère donner un message clair à l'agent plutôt qu'une erreur HTTP cryptique.
        VALID_TABLES = [
            "usage_metrics",
            "active_users",
            "source",
            "agents",
            "users",
            "skill_usage",
            "tool_usage",
            "messages",
        ]
        if table not in VALID_TABLES:
            return json.dumps({
                "error": f"Table invalide : '{table}'.",
                "tables_disponibles": VALID_TABLES
            }, ensure_ascii=False, indent=2)

        # ── Validation du format de date ──────────────────────────────────────
        # On vérifie que les dates respectent bien le format YYYY-MM-DD
        # pour éviter une erreur 400 de l'API Dust.
        import re
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        if not date_pattern.match(start_date) or not date_pattern.match(end_date):
            return json.dumps({
                "error": "Les dates doivent être au format YYYY-MM-DD (ex: '2025-01-01').",
                "start_date_recu": start_date,
                "end_date_recu": end_date
            }, ensure_ascii=False, indent=2)

        try:
            # ── Construction du chemin de l'endpoint ──────────────────────────
            # DUST_WORKSPACE_ID est lu depuis les variables d'environnement de Railway
            path = f"/w/{DUST_WORKSPACE_ID}/analytics/export"

            # ── Construction des paramètres de requête (query string) ─────────
            # On passe obligatoirement : table, startDate, endDate, format
            # On ajoute timezone uniquement s'il a été fourni
            params = {
                "table": table,              # Quel type de données exporter
                "startDate": start_date,     # Format attendu par l'API : YYYY-MM-DD
                "endDate": end_date,         # Format attendu par l'API : YYYY-MM-DD
                "format": "json",            # On force JSON pour rester compatible avec dust_get()
                                             # (dust_get appelle r.json() en fin de chaîne)
            }

            # On ajoute timezone seulement s'il a été fourni (sinon l'API utilise UTC)
            if timezone is not None:
                params["timezone"] = timezone

            # ── Appel à l'API Dust ─────────────────────────────────────────────
            # dust_get() va :
            #   1. Vérifier que DUST_API_KEY et DUST_WORKSPACE_ID sont bien définis
            #   2. Ajouter le header "Authorization: Bearer DUST_API_KEY"
            #   3. Faire le GET https://dust.tt/api/v1/w/{wId}/analytics/export?...
            #   4. Vérifier que la réponse HTTP est 2xx (sinon lever une RuntimeError)
            #   5. Retourner le corps JSON converti en dict Python
            data = dust_get(path, params=params)

            # ── Enrichissement de la réponse ───────────────────────────────────
            # On ajoute les paramètres utilisés pour faciliter la lecture du résultat
            result = {
                "table": table,
                "start_date": start_date,
                "end_date": end_date,
                "timezone": timezone or "UTC",
                "data": data  # Les données brutes retournées par l'API Dust
            }

            # Conversion en texte JSON formaté et lisible par l'agent
            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            # En cas d'erreur (403 = clé pas admin, 400 = params invalides, réseau…)
            # On retourne un JSON d'erreur propre plutôt que de faire planter le serveur
            error_msg = str(e)

            # Message d'aide spécifique si l'erreur est un 403 (cas fréquent)
            aide = None
            if "403" in error_msg:
                aide = (
                    "HTTP 403 = ta clé API n'a pas le scope 'admin'. "
                    "Va dans Dust > Settings > API Keys et crée une clé avec les droits admin."
                )

            return json.dumps({
                "error": error_msg,
                "aide": aide,
                "parametres_utilises": {
                    "table": table,
                    "start_date": start_date,
                    "end_date": end_date,
                    "timezone": timezone
                }
            }, ensure_ascii=False, indent=2)
