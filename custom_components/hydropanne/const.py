"""Constantes pour l'intégration Hydro-Panne."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "hydropanne"

# Valeurs par défaut
DEFAULT_NAME: Final = "Hydro-Panne"
DEFAULT_RADIUS: Final = 1000  # mètres
DEFAULT_SCAN_INTERVAL: Final = 5  # minutes
MIN_SCAN_INTERVAL: Final = 1
MAX_SCAN_INTERVAL: Final = 120
MIN_RADIUS: Final = 100
MAX_RADIUS: Final = 50000

# API « données ouvertes » d'Hydro-Québec (OpenDataSoft Explore v2.1)
# https://donnees.hydroquebec.com/explore/dataset/pannes-interruptions/
API_BASE_URL: Final = (
    "https://donnees.hydroquebec.com/api/explore/v2.1/catalog/datasets/"
    "pannes-interruptions/records"
)
API_PAGE_LIMIT: Final = 100
API_MAX_RECORDS: Final = 2000
API_TIMEOUT: Final = 30

# Le portail de données ouvertes est servi derrière un pare-feu applicatif
# (Akamai) qui refuse (HTTP 403) les requêtes dont l'agent utilisateur trahit un
# client automatisé — ce qui est le cas de l'agent par défaut de Home Assistant
# (« HomeAssistant/… aiohttp/… Python/… »). On envoie donc des en-têtes
# imitant un navigateur afin que l'API accepte la requête.
API_HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8",
}

# Métadonnées de l'appareil
MANUFACTURER: Final = "Hydro-Québec"
MODEL: Final = "Info-pannes (données ouvertes)"
CONFIGURATION_URL: Final = "https://infopannes.solutions.hydroquebec.com/"
ATTRIBUTION: Final = "Données fournies par Hydro-Québec (données ouvertes)"
