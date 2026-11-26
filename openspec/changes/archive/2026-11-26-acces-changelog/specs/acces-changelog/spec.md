# acces-changelog Specification

## Purpose

Permettre à l'utilisatrice d'ouvrir le fichier `CHANGELOG.md` de la branche courante tel que publié sur GitHub, dans une nouvelle fenêtre du navigateur, via un lien « changements » placé dans l'en-tête à côté du numéro de version.

## Requirements

### Requirement: Lien « changements » dans l'en-tête

L'en-tête de toutes les pages affiche le numéro de version suivi d'un lien « changements » pointant vers le CHANGELOG publié sur GitHub.

#### Scenario: Affichage de l'en-tête

- **WHEN** l'utilisatrice ouvre n'importe quelle page de l'application
- **THEN** l'en-tête affiche « Suivi d'activité (vX.Y.Z - changements) »
- **AND** le mot « changements » est un lien cliquable
- **AND** le lien hérite de la couleur de l'en-tête (lisible mais discret)

#### Scenario: Version absente

- **WHEN** la variable `version` n'est pas définie (valeurs de test)
- **THEN** seul « Suivi d'activité » est affiché, sans parenthèse ni lien

### Requirement: Ouverture dans une nouvelle fenêtre

Le lien « changements » ouvre le CHANGELOG dans un nouvel onglet du navigateur, sans quitter l'application.

#### Scenario: Clic sur « changements »

- **WHEN** l'utilisatrice clique sur « changements »
- **THEN** le navigateur ouvre un nouvel onglet
- **AND** ce nouvel onglet affiche le fichier `CHANGELOG.md` hébergé sur GitHub
- **AND** la page de suivi des KPI reste ouverte et inchangée dans l'onglet d'origine

### Requirement: URL pointant vers la branche courante sur GitHub

Le lien pointe vers `https://github.com/jeremyplessis/kpi/blob/<branche-courante>/CHANGELOG.md`.

#### Scenario: Construction de l'URL

- **WHEN** l'application construit le lien
- **THEN** `<branche-courante>` est déterminée par `git rev-parse --abbrev-ref HEAD`
- **AND** si git est indisponible, le repli est la branche `main`

#### Scenario: Attributs du lien

- **WHEN** le lien est rendu dans le HTML
- **THEN** il porte `target="_blank"` et `rel="noopener"`
- **AND** son `href` contient `github.com/jeremyplessis/kpi/blob/` et se termine par `/CHANGELOG.md`
