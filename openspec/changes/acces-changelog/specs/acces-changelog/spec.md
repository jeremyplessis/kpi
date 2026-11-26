# acces-changelog Specification

## Purpose

Permettre à l'utilisatrice de consulter le fichier `CHANGELOG.md` de la branche courante tel que publié sur GitHub, directement depuis l'interface web, via un lien « changements » placé dans l'en-tête à côté du numéro de version.

## Requirements

### Requirement: Lien « changements » dans l'en-tête

L'en-tête de toutes les pages affiche le numéro de version suivi d'un lien « changements » pointant vers `/changelog`.

#### Scenario: Affichage de l'en-tête

- **WHEN** l'utilisatrice ouvre n'importe quelle page de l'application
- **THEN** l'en-tête affiche « Suivi d'activité (vX.Y.Z - changements) »
- **AND** le mot « changements » est un lien cliquable vers `/changelog`
- **AND** le lien hérite de la couleur de l'en-tête (lisible mais discret)

#### Scenario: Version absente

- **WHEN** la variable `version` n'est pas définie (valeurs de test)
- **THEN** seul « Suivi d'activité » est affiché, sans parenthèse ni lien

### Requirement: Page /changelog lit le CHANGELOG depuis GitHub

La route `GET /changelog` télécharge le contenu du fichier `CHANGELOG.md` depuis `raw.githubusercontent.com` pour la branche git courante du projet et l'affiche.

#### Scenario: Téléchargement réussi

- **WHEN** l'utilisatrice ouvre `/changelog`
- **THEN** la page répond 200 avec le contenu textuel du fichier `CHANGELOG.md` téléchargé depuis `https://raw.githubusercontent.com/jeremyplessis/kpi/<branche-courante>/CHANGELOG.md`
- **AND** la branche courante est déterminée par `git rev-parse --abbrev-ref HEAD`
- **AND** le contenu est affiché dans une carte lisible, avec le titre « Historique des changements (vX.Y.Z) »
- **AND** la page utilise le gabarit commun (`base.html`) avec la navigation habituelle

#### Scenario: Repli sur le fichier local

- **WHEN** le téléchargement depuis GitHub échoue (pas de réseau, branche non poussée, dépôt distant injoignable)
- **THEN** la page tente de lire `CHANGELOG.md` sur le disque local
- **AND** si le fichier local existe, son contenu est affiché avec une mention « (copie locale — la branche n'est pas publiée sur GitHub) »
- **AND** la page répond toujours 200

#### Scenario: Aucun CHANGELOG disponible

- **WHEN** ni GitHub ni le disque local ne fournissent de `CHANGELOG.md`
- **THEN** la page affiche « Aucun historique disponible. » sans erreur

### Requirement: Re-téléchargement à chaque requête

Le contenu du CHANGELOG est téléchargé depuis GitHub à chaque appel de `/changelog` (pas de cache).

#### Scenario: Mise à jour du CHANGELOG sur GitHub

- **WHEN** le fichier `CHANGELOG.md` est modifié et poussé sur la branche courante sur GitHub
- **THEN** la prochaine visite de `/changelog` reflète la modification sans redémarrage du serveur
