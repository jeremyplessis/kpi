# Spec Delta: Filtres de période — bornes min/max des données

## MODIFIED Requirements

### Requirement: Période par défaut sur 12 mois glissants

- **WHEN** l'utilisatrice ouvre `/kpi` (ou `/kpi/TauxGhosting`) sans **aucun** des paramètres `annee_debut`, `mois_debut`, `annee_fin`, `mois_fin` présent dans l'URL
- **THEN** les filtres sont pré-remplis sur les 12 derniers mois glissants (mois en cours inclus)
- **AND** les sélecteurs HTML affichent ces valeurs comme sélectionnées
- **AND** les indicateurs sont calculés sur cette période

#### Scenario: Cas général (novembre 2026)

- **WHEN** la date du jour est le 15 novembre 2026 et l'URL ne contient aucun paramètre de période
- **THEN** la période par défaut est : année_début=2025, mois_début=12, année_fin=2026, mois_fin=11

#### Scenario: Lien « Effacer les filtres »

- **WHEN** l'utilisatrice clique sur « Effacer les filtres » (lien vers `/kpi` sans paramètre)
- **THEN** la page retombe sur les 12 derniers mois glissants

### Requirement: « Toutes les années » / « Tous les mois » explicites = bornes min/max des données

- **WHEN** l'URL contient au moins un des 4 paramètres de période, et les 4 valeurs sont vides (`annee_debut=&mois_debut=&annee_fin=&mois_fin=`)
- **THEN** la période appliquée va du couple (année, mois) **minimum** au couple (année, mois) **maximum** présents dans les événements du suivi
- **AND** les indicateurs sont recalculés sur cette plage complète (tableau de bord et indicateur sélectionné)
- **AND** les sélecteurs affichent « Toutes les années » / « Tous les mois » comme sélectionnés (valeurs vides conservées)
- **AND** la période par défaut des 12 mois glissants n'est PAS appliquée

#### Scenario: Application des filtres avec tous les sélecteurs vides

- **WHEN** l'utilisatrice sélectionne « Toutes les années » et « Tous les mois » dans les 4 sélecteurs puis clique sur « Appliquer les filtres »
- **THEN** l'URL est `/kpi?...&annee_debut=&mois_debut=&annee_fin=&mois_fin=`
- **AND** les événements pris en compte vont du couple (année, mois) le plus ancien au plus récent de la base
- **AND** les valeurs des indicateurs reflètent l'intégralité de l'historique

#### Scenario: Bornes partielles vides

- **WHEN** l'URL contient `annee_debut=2025` mais `mois_debut`, `annee_fin`, `mois_fin` vides
- **THEN** le début est (2025, mois minimum des événements de 2025), la fin est le couple (année, mois) maximum des événements
- **AND** aucune période par défaut n'est appliquée

#### Scenario: Base vide avec sélecteurs vides explicites

- **WHEN** la base ne contient aucun événement et l'URL contient les 4 paramètres vides
- **THEN** les indicateurs affichent « Aucune donnée disponible pour cette période »
- **AND** aucune erreur n'est levée (pas de calcul de min/max sur liste vide)

### Requirement: Cohérence page de détail du ghosting

- **WHEN** l'utilisatrice ouvre `/kpi/TauxGhosting` avec les 4 paramètres de période présents mais vides
- **THEN** le même comportement s'applique : bornes min/max des données, pas de retour aux 12 mois glissants
