# consultation-kpi Specification

## Purpose

L'écran `/kpi` permet de sélectionner un indicateur et une période, mais il manque une vue d'ensemble synthétique. Cette spec définit le tableau de bord affiché par défaut sur `/kpi` quand aucun indicateur n'est sélectionné, avec des cartes de synthèse et des sparklines de tendance, ainsi que les règles de rendu JavaScript sans erreur d'échappement pour les tableaux multi-dimensions.

## Requirements

### Requirement: Vue tableau de bord par défaut

La page `/kpi` sans paramètre `indicateur` affiche un tableau de bord synthétique au lieu d'un message vide.

#### Scenario: Accès direct à /kpi

- **WHEN** l'utilisatrice ouvre `/kpi` sans sélectionner d'indicateur
- **THEN** la page affiche 4 cartes de synthèse (une par indicateur du registre)
- **AND** chaque carte affiche le libellé, la valeur agrégée sur la période, et un sparkline de tendance

#### Scenario: Tableau de bord avec filtres de période

- **WHEN** l'utilisatrice applique des filtres de période puis ouvre `/kpi` sans indicateur
- **THEN** les cartes de synthèse sont calculées sur la période filtrée
- **AND** les sparklines couvrent uniquement la période filtrée

### Requirement: Cartes de synthèse cliquables

Chaque carte du tableau de bord est un lien vers la page détaillée de l'indicateur correspondant.

#### Scenario: Clic sur une carte

- **WHEN** l'utilisatrice clique sur la carte "Taux de ghosting"
- **THEN** elle est redirigée vers `/kpi?indicateur=TauxGhosting` avec les filtres de période conservés
- **AND** l'indicateur TauxGhosting est pré-sélectionné et ses données affichées

### Requirement: Sparkline de tendance mensuelle

Chaque carte affiche un mini-graphique (sparkline) montrant l'évolution mensuelle de l'indicateur sur la période.

#### Scenario: Affichage du sparkline

- **WHEN** la période couvre plusieurs mois
- **THEN** le sparkline affiche un point par mois avec la valeur de l'indicateur ce mois-ci
- **AND** le graphique est un line chart Chart.js sans axes ni légende (mode compact)

#### Scenario: Période d'un seul mois

- **WHEN** la période filtrée ne couvre qu'un seul mois
- **THEN** le sparkline affiche un seul point (ou un message "période trop courte")

### Requirement: Valeurs agrégées cohérentes

Les totaux affichés dans les cartes correspondent exactement à la somme des valeurs affichées dans les tableaux détaillés pour la même période.

#### Scenario: Cohérence total vs détail

- **WHEN** l'utilisatrice consulte le tableau de bord puis clique sur un indicateur
- **THEN** la somme des valeurs du tableau détaillé égale le total affiché dans la carte

### Requirement: Indicateur en pourcentage

La carte "Taux de ghosting" affiche le taux moyen en pourcentage, pas en décimal.

#### Scenario: Affichage du taux de ghosting

- **WHEN** la carte Taux de ghosting est affichée
- **THEN** la valeur est affichée sous forme de pourcentage (ex: "36,7 %")
- **AND** le sparkline utilise la même échelle en pourcentage

### Requirement: Rendu JavaScript des tableaux multi-dimensions sans erreur d'échappement

Les données passées au JavaScript pour le tableau dépliable et les graphiques
sont sérialisées avec le filtre `|tojson` de Jinja2, et non par concaténation
manuelle de chaînes. Aucun caractère n'est échappé en entité HTML (`&#34;`)
dans le code JavaScript généré.

#### Scenario: Sélection d'un indicateur à 3 dimensions

- **WHEN** l'utilisatrice sélectionne un indicateur à 3 dimensions (NbProspects, NbDemandes)
- **THEN** le tableau dépliable affiche les données (pas d'écran vide)
- **AND** la console JavaScript ne contient aucune erreur de syntaxe

#### Scenario: Sélection d'un indicateur à 2 dimensions

- **WHEN** l'utilisatrice sélectionne TauxGhosting ou RdvParCanal
- **THEN** le tableau et le graphique s'affichent correctement
- **AND** `dimensionNames` est un tableau JS valide
