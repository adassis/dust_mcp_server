# =============================================================
# config.py — Configuration du serveur MCP Dust
# =============================================================

import os  # Librairie standard Python pour accéder aux variables d'environnement

# ── Serveur MCP ───────────────────────────────────────────────

# PORT : le port sur lequel le serveur écoute
# Railway injecte automatiquement la variable PORT
# Si elle n'existe pas (ex: en local), on utilise 8000 par défaut
PORT = int(os.environ.get("PORT", 8000))

# MCP_BEARER_TOKEN : token de sécurité pour protéger ton serveur MCP
# Si ce token est défini, Dust devra l'envoyer dans chaque requête
# pour prouver qu'il est bien autorisé à utiliser le serveur
MCP_BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN", "")

# ── API Dust ──────────────────────────────────────────────────

# DUST_API_KEY : ta clé API Dust personnelle
# À trouver dans : Dust > Settings > API Keys
DUST_API_KEY = os.environ.get("DUST_API_KEY", "")

# DUST_WORKSPACE_ID : l'identifiant de ton workspace Dust
# Visible dans l'URL quand tu es connecté : dust.tt/w/XXXXXXXX
DUST_WORKSPACE_ID = os.environ.get("DUST_WORKSPACE_ID", "")

# DUST_SPACE_ID : l'identifiant de l'espace (Space) principal du workspace
# Visible dans l'URL : dust.tt/w/WORKSPACE/spaces/SPACE_ID
# Utilisé par get_space_mcp_server_views pour lister les serveurs MCP
# disponibles dans cet espace sans avoir à le passer en paramètre
DUST_SPACE_ID = os.environ.get("DUST_SPACE_ID", "vlt_VZXFm4VFUdvh") 
