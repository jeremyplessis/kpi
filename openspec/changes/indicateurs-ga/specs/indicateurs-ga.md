# Spec Delta: Indicateurs GA

## ADDED Requirements

### Requirement: Indicateur "Visiteurs GA"

Un nouvel indicateur "Nombre de visiteurs GA" calcule le nombre total de visiteurs du site sur la période, à partir des relevés `ga_visiteurs`.

#### Scenario: Calcul mensuel

- **WHEN** l'indicateur VisiteursGA est calculé sur une période
- **THEN** il retourne une ligne par (année, mois) avec le nombre de visiteurs
- **AND** les mois sans relevé GA sont absents (pas de valeur 0)

#### Scenario: Total sur la période

- **WHEN** le tableau de bord affiche la carte "Visiteurs GA"
- **THEN** le total affiché est la somme des visiteurs de tous les mois de la période

### Requirement: Indicateur "Conversions" (règle à définir)

Un nouvel indicateur "Nombre de conversions" est implémenté selon la règle validée avec l'utilisatrice (voir proposal — pistes A, B ou C).

#### Scenario: Calcul selon la règle choisie

- **WHEN** l'indicateur Conversions est calculé sur une période
- **THEN** il retourne des lignes conformes à la règle de calcul validée
- **AND** la règle est documentée dans la docstring de la classe

### Requirement: Intégration dans le registre

Les nouveaux indicateurs sont enregistrés dans `REGISTRE_INDICATEURS` et apparaissent dans le sélecteur de `/kpi`.

#### Scenario: Sélecteur d'indicateurs

- **WHEN** la page `/kpi` est affichée
- **THEN** le sélecteur contient "Nombre de visiteurs GA" et "Nombre de conversions" en plus des 4 existants

#### Scenario: Tableau de bord

- **WHEN** aucun indicateur n'est sélectionné sur `/kpi`
- **THEN** le tableau de bord affiche une carte par nouvel indicateur GA

### Requirement: Filtrage par période

Les indicateurs GA respectent les mêmes filtres de période (année/mois début/fin) que les autres indicateurs.

#### Scenario: Filtre appliqué

- **WHEN** l'utilisatrice filtre sur janvier 2026 uniquement et sélectionne VisiteursGA
- **THEN** seules les données de janvier 2026 sont affichées
