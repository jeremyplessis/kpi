# Spécification: Filtres de période par défaut sur /kpi

## Scénario: Ouverture de /kpi sans paramètre de période

- **WHEN** l'utilisatrice ouvre `/kpi` sans aucun paramètre `annee_debut`, `mois_debut`, `annee_fin`, `mois_fin` dans l'URL
- **THEN** les filtres de période sont automatiquement pré-remplis sur les 12 derniers mois glissants (mois en cours inclus)
- **AND** les sélecteurs HTML affichent ces valeurs comme sélectionnées
- **AND** les indicateurs (tableau de bord ou indicateur sélectionné) sont calculés sur cette période

## Scénario: Calcul des 12 mois glissants — cas général

- **WHEN** la date du jour est le 15 novembre 2026
- **THEN** la période par défaut est : année_début=2025, mois_début=12, année_fin=2026, mois_fin=11

## Scénario: Calcul des 12 mois glissants — passage d'année (janvier)

- **WHEN** la date du jour est le 10 janvier 2026
- **THEN** la période par défaut est : année_début=2025, mois_début=2, année_fin=2026, mois_fin=1

## Scénario: Calcul des 12 mois glissants — février (année non bissextile vs bissextile)

- **WHEN** la date du jour est en février 2026 (non bissextile) ou février 2028 (bissextile)
- **THEN** la période par défaut fait toujours exactement 12 mois (le calcul est basé sur les mois, pas sur les jours)

## Scénario: L'utilisateur fournit au moins un paramètre de période

- **WHEN** l'utilisatrice ouvre `/kpi?annee_debut=2025` (un seul paramètre de période)
- **THEN** AUCUN filtre par défaut n'est appliqué : seul `annee_debut=2025` est pris en compte, les autres filtres restent vides (« Toutes les années » / « Tous les mois » pour la fin)
- **AND** les sélecteurs reflètent exactement ce qui est dans l'URL

## Scénario: L'utilisateur fournit tous les paramètres de période

- **WHEN** l'utilisatrice ouvre `/kpi?annee_debut=2024&mois_debut=6&annee_fin=2025&mois_fin=3`
- **THEN** la période affichée est exactement 2024-06 à 2025-03, sans modification

## Scénario: Lien « Effacer les filtres »

- **WHEN** l'utilisatrice clique sur « Effacer les filtres » (lien vers `/kpi` sans paramètre)
- **THEN** la page retombe sur les 12 derniers mois glissants (comportement par défaut)
- **AND** les sélecteurs affichent cette période

## Scénario: Page de détail du ghosting (/kpi/TauxGhosting)

- **WHEN** l'utilisatrice ouvre `/kpi/TauxGhosting` sans paramètre de période
- **THEN** les filtres sont pré-remplis sur les 12 derniers mois glissants, comme sur `/kpi`

## Scénario: Base de données vide (aucun événement)

- **WHEN** la base ne contient aucun événement et que l'utilisatrice ouvre `/kpi`
- **THEN** les filtres par défaut sont quand même appliqués et affichés dans les sélecteurs
- **AND** les années de la période par défaut (ex: 2025 et 2026) apparaissent dans les options des sélecteurs d'année

## Scénario: Tableau de bord avec période par défaut

- **WHEN** l'utilisatrice ouvre `/kpi` sans paramètre et sans indicateur sélectionné
- **THEN** le tableau de bord (cartes de synthèse) est calculé sur les 12 derniers mois glissants
- **AND** les sparklines couvrent cette même période
