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

# Métadonnées de l'appareil
MANUFACTURER: Final = "Hydro-Québec"
MODEL: Final = "Info-pannes (données ouvertes)"
CONFIGURATION_URL: Final = "https://infopannes.solutions.hydroquebec.com/"
ATTRIBUTION: Final = "Données fournies par Hydro-Québec (données ouvertes)"
