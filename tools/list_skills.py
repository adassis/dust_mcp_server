# =============================================================
# tools/list_skills.py
# =============================================================
# Tool MCP : liste les skills du workspace Dust
# Endpoint : GET /api/v1/w/{wId}/skills?status=...
# =============================================================

import json
from utils.dust import dust_get
from config import DUST_WORKSPACE_ID


def register(mcp):

    @mcp.tool()
    def list_skills(status: str = "active") -> str:
        """
        Liste les skills (compétences personnalisées) disponibles dans le workspace Dust.

        Les skills sont des capacités personnalisées créées dans le workspace.
        Elles peuvent être activées sur des agents pour étendre leurs fonctionnalités.
        Par défaut, seules les skills actives sont retournées.

        Utilise cet outil pour :
        - Découvrir quelles skills sont disponibles dans ton workspace
        - Obtenir le sId d'une skill (nécessaire pour l'assigner à un agent)
        - Vérifier l'état des skills (active, archivée, suggérée)

        Args:
            status : Filtre par statut de la skill :
                     - "active" (défaut) : skills en cours d'utilisation
                     - "archived" : skills désactivées / archivées
                     - "suggested" : skills suggérées mais pas encore activées

        Returns:
            JSON avec le tableau skills contenant pour chaque skill :
            son sId, son nom, sa description, et son statut.
        """
        try:
            # Validation du statut avant l'appel API
            # Evite une erreur 400 de l'API Dust avec un message clair
            valid_statuses = ["active", "archived", "suggested"]
            if status not in valid_statuses:
                return json.dumps({
                    "error": f"Statut invalide : '{status}'. Valeurs autorisées : {valid_statuses}"
                }, ensure_ascii=False)

            # Endpoint : GET /api/v1/w/{wId}/skills
            path = f"/w/{DUST_WORKSPACE_ID}/skills"
            data = dust_get(path, params={"status": status})

            # On enrichit la réponse avec le nombre de skills trouvées
            skills = data.get("skills", [])
            result = {
                "status_filter": status,
                "total_skills": len(skills),
                "skills": skills
            }

            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "status_filter": status}, ensure_ascii=False)