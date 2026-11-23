# Filtres de période par défaut Specification

## Purpose

Sur l'écran `/kpi` (et `/kpi/TauxGhosting`), quand aucun paramètre de période n'est présent dans l'URL, les filtres sont automatiquement pré-remplis sur les 12 derniers mois glissants (mois en cours inclus).

## Requirements

### Requirement: Période par défaut sur 12 mois glissants

- **WHEN** l'utilisatrice ouvre `/kpi` sans aucun paramètre `annee_debut`, `mois_debut`, `annee_fin`, `mois_fin`
- **THEN** les filtres sont pré-remplis sur les 12 derniers mois glissants (mois en cours inclus)
- **AND** les sélecteurs HTML affichent ces valeurs comme sélectionnées
- **AND** les indicateurs sont calculés sur cette période

#### Scenario: Cas général (novembre 2026)

- **WHEN** la date du jour est le 15 novembre 2026
- **THEN** la période par défaut est : année_début=2025, mois_début=12, année_fin=2026, mois_fin=11

#### Scenario: Passage d'année (janvier)

- **WHEN** la date du jour est le 10 janvier 2026
- **THEN** la période par défaut est : année_début=2025, mois_début=2, année_fin=2026, mois_fin=1

#### Scenario: Décembre (12 mois dans la même année)

- **WHEN** la date du jour est le 31 décembre 2026
- **THEN** la période par défaut est : année_début=2026, mois_début=1, année_fin=2026, mois_fin=12

### Requirement: Paramètre de période fourni = pas de défaut

- **WHEN** l'utilisatrice fournit au moins un des 4 paramètres de période dans l'URL
- **THEN** aucun filtre par défaut n'est appliqué
- **AND** seuls les paramètres fournis sont pris en compte

### Requirement: Lien « Effacer les filtres »

- **WHEN** l'utilisatrice clique sur « Effacer les filtres » (lien vers `/kpi` sans paramètre)
- **THEN** la page retombe sur les 12 derniers mois glissants

### Requirement: Années par défaut dans les sélecteurs

- **WHEN** la base ne contient aucun événement (ou aucune année de la période par défaut)
- **THEN** les années de la période par défaut apparaissent quand même dans les sélecteurs d'année
