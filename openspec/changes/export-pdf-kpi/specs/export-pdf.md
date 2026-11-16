# Spec Delta: Export PDF KPI

## ADDED Requirements

### Requirement: Route d'export PDF

Une route `GET /kpi/export-pdf` génère un PDF à partir des filtres de période et d'indicateur passés en paramètres d'URL.

#### Scenario: Export avec tous les indicateurs

- **WHEN** l'utilisatrice clique sur "Exporter en PDF" depuis `/kpi` sans indicateur sélectionné
- **THEN** la réponse est un PDF (`Content-Type: application/pdf`)
- **AND** le PDF contient les 4 indicateurs sur la période filtrée
- **AND** le nom du fichier est `kpi_<periode>.pdf`

#### Scenario: Export d'un indicateur spécifique

- **WHEN** l'utilisatrice exporte depuis `/kpi?indicateur=TauxGhosting`
- **THEN** le PDF ne contient que le détail du taux de ghosting
- **AND** les filtres de période sont respectés

### Requirement: Contenu du PDF

Le PDF reprend fidèlement les données affichées à l'écran pour la même période.

#### Scenario: Cohérence écran/PDF

- **WHEN** un PDF est généré pour une période donnée
- **THEN** les totaux et tableaux du PDF sont identiques à ceux affichés sur `/kpi` pour la même période
- **AND** la période est indiquée dans l'en-tête du PDF

### Requirement: Mise en page imprimable

Le PDF est mis en page pour une impression A4 lisible.

#### Scenario: Format A4

- **WHEN** le PDF est ouvert dans un lecteur PDF
- **THEN** la page est au format A4 portrait
- **AND** les tableaux tiennent dans la largeur de page (pas de défilement horizontal)
- **AND** l'en-tête contient le titre, la version de l'application, et la date de génération

### Requirement: Bouton d'export sur les écrans KPI

Un bouton "Exporter en PDF" est visible sur la page `/kpi` et sur la page détaillée `/kpi/TauxGhosting`.

#### Scenario: Bouton présent

- **WHEN** la page `/kpi` est affichée
- **THEN** un lien ou bouton "Exporter en PDF" est visible
- **AND** il pointe vers `/kpi/export-pdf` avec les paramètres de filtre actuels conservés

### Requirement: PDF non vide et valide

Le PDF généré est un fichier PDF valide et non vide.

#### Scenario: Validité du PDF

- **WHEN** la route `/kpi/export-pdf` est appelée
- **THEN** la réponse a le statut 200
- **AND** le `Content-Type` est `application/pdf`
- **AND** le contenu commence par `%PDF-`
- **AND** la taille du contenu est supérieure à 1 Ko
