# Spec Delta: Affichage du commentaire dans la liste des événements

## MODIFIED Requirements

### Requirement: Colonne commentaire non tronquée

La cellule commentaire du tableau « Derniers événements » affiche le texte complet, sans troncature à droite.

#### Scenario: Commentaire long dans la liste

- **WHEN** un événement a un commentaire de plus de 18rem de large
- **THEN** le texte complet est présent dans le HTML de la cellule (pas de coupure)
- **AND** la cellule a un attribut `title` contenant le commentaire complet (infobulle au survol)
- **AND** le CSS de la cellule n'a pas de `max-width` qui tronque

#### Scenario: Commentaire court

- **WHEN** un événement a un commentaire court (moins d'une ligne)
- **THEN** il s'affiche normalement, sur une seule ligne

#### Scenario: Commentaire vide

- **WHEN** un événement n'a pas de commentaire
- **THEN** la cellule est vide (pas de `title` vide inutile)

### Requirement: Tableau toujours lisible

Malgré l'absence de `max-width` sur la colonne commentaire, le tableau reste lisible.

#### Scenario: Largeur du tableau

- **WHEN** le tableau des événements est affiché
- **THEN** il conserve son `min-width: 28rem` et son `overflow-x: auto`
- **AND** les autres colonnes ne sont pas écrasées par la colonne commentaire
