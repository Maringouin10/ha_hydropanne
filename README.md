# Hydro-Panne

[![HACS Custom][hacs-badge]][hacs-url]
[![GitHub Release][release-badge]][release-url]
[![Validate][validate-badge]][validate-url]

Intégration Home Assistant pour détecter les **pannes d'électricité Hydro-Québec** en temps réel à votre domicile, avec l'heure estimée de rétablissement.

---

## Fonctionnalités

| Entité | Type | Description |
|--------|------|-------------|
| `binary_sensor.panne_d_electricite` | Capteur binaire | `on` = panne en cours à votre domicile |
| `sensor.retablissement_estime` | Horodatage | Heure estimée de rétablissement |
| `sensor.debut_de_la_panne` | Horodatage | Heure de début de la panne |
| `sensor.clients_touches` | Mesure | Nombre de clients sans courant |
| `sensor.pannes_a_proximite` | Mesure | Nombre de pannes dans le rayon |
| `sensor.cause` | Texte | Cause de la panne (si connue) |

Les données proviennent du jeu de données ouvertes officiel d'Hydro-Québec
([pannes-interruptions][hq-open-data]) — aucun compte Hydro-Québec requis.

---

## Installation via HACS

1. Dans HACS, cliquez sur **Dépôts personnalisés** → ajoutez `maringouin10/ha_hydropanne` (catégorie : Intégration).
2. Installez **Hydro-Panne**.
3. Redémarrez Home Assistant.

### Installation manuelle

Copiez le dossier `custom_components/hydropanne/` dans votre répertoire
`<config>/custom_components/` puis redémarrez Home Assistant.

---

## Configuration

1. **Paramètres → Appareils et services → Ajouter une intégration** → cherchez **Hydro-Panne**.
2. Renseignez votre nom, latitude, longitude et le rayon de recherche (défaut : 1 000 m).  
   Les coordonnées reprennent automatiquement l'emplacement de votre instance HA.
3. Cliquez sur **Envoyer** — l'intégration valide la connexion avant de s'enregistrer.

### Options (modifiables après l'installation)

| Option | Défaut | Description |
|--------|--------|-------------|
| Rayon (m) | 1 000 | Zone autour du domicile analysée (100 – 50 000 m) |
| Intervalle (min) | 5 | Fréquence de mise à jour (1 – 120 min) |

---

## Exemples d'automatisation

### Notification lors d'une panne

```yaml
automation:
  - alias: "Alerte panne Hydro-Québec"
    trigger:
      - platform: state
        entity_id: binary_sensor.panne_d_electricite
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "⚡ Panne d'électricité"
          message: >
            Panne détectée.
            {% if states('sensor.retablissement_estime') != 'unavailable' %}
            Rétablissement prévu : {{ states('sensor.retablissement_estime') | as_timestamp | timestamp_local }}.
            {% else %}
            Heure de rétablissement inconnue.
            {% endif %}
```

### Carte Lovelace

```yaml
type: entities
title: Hydro-Panne
entities:
  - entity: binary_sensor.panne_d_electricite
  - entity: sensor.retablissement_estime
  - entity: sensor.debut_de_la_panne
  - entity: sensor.clients_touches
  - entity: sensor.cause
```

---

## Source des données

- **API** : [Données ouvertes Hydro-Québec][hq-open-data] (OpenDataSoft Explore v2.1)
- **Mise à jour** : toutes les 5 minutes (configurable)
- **Méthode de détection** : algorithme point-dans-polygone (ray casting) sur la géométrie GeoJSON de chaque panne — aucune dépendance externe

---

## Licence

[MIT](LICENSE)

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/release/maringouin10/ha_hydropanne.svg
[release-url]: https://github.com/maringouin10/ha_hydropanne/releases
[validate-badge]: https://github.com/maringouin10/ha_hydropanne/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/maringouin10/ha_hydropanne/actions/workflows/validate.yml
[hq-open-data]: https://donnees.hydroquebec.com/explore/dataset/pannes-interruptions/
