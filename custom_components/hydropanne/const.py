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

# API temps réel « Info-pannes » d'Hydro-Québec — la source qui alimente la
# carte officielle des pannes. Le jeu de données ouvertes OpenDataSoft
# (donnees.hydroquebec.com/.../pannes-interruptions) est une coquille vide
# (« has_records: false », aucun champ) : il ne renvoie jamais de panne. On
# interroge donc directement le flux temps réel, en deux temps : d'abord le
# numéro de version courant, puis le fichier de marqueurs correspondant qui
# liste toutes les pannes de la province.
API_V3_BASE_URL: Final = "https://pannes.hydroquebec.com/pannes/donnees/v3_0/"
API_VERSION_URL: Final = f"{API_V3_BASE_URL}bisversion.json"
API_TIMEOUT: Final = 30


def markers_url(version: str) -> str:
    """URL du fichier de marqueurs pour un numéro de version donné."""
    return f"{API_V3_BASE_URL}bismarkers{version}.json"


# En-têtes imitant un navigateur : certains chemins d'Hydro-Québec sont servis
# derrière un pare-feu applicatif (Akamai) qui filtre les clients automatisés.
API_HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8",
}

# Métadonnées de l'appareil
MANUFACTURER: Final = "Hydro-Québec"
MODEL: Final = "Info-pannes (temps réel)"
CONFIGURATION_URL: Final = "https://infopannes.solutions.hydroquebec.com/"
ATTRIBUTION: Final = "Données fournies par Hydro-Québec (Info-pannes)"
