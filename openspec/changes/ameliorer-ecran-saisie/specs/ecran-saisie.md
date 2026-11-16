# Spec Delta: Affichage du commentaire dans la liste des événements

## MODIFIED Requirements

### Requirement: Colonne commentaire non tronquée

La cellule commentaire du tableau « Derniers événements » affiche le texte complet, sans troncature à droite.

#### Scenario: Commentaire long dans la liste

- **WHEN** un événement a un commentaire long
- **THEN** le texte complet est présent dans le HTML de la cellule (pas de coupure)
- **AND** la cellule a un attribut `title` contenant le commentaire complet (infobulle au survol)
- **AND** le contenu de la cellule est enveloppé dans un `<div>` avec `max-width: 22rem` et `overflow-wrap: break-word`, pour que le texte revienne à la ligne sans être tronqué

#### Scenario: Commentaire court

- **WHEN** un événement a un commentaire court (moins d'une ligne)
- **THEN** il s'affiche normalement, sur une seule ligne

#### Scenario: Commentaire vide

- **WHEN** un événement n'a pas de commentaire
- **THEN** la cellule est vide (pas de `title` vide inutile)

### Requirement: Tableau toujours lisible

Le tableau reste lisible malgré la colonne commentaire : les autres colonnes ne sont pas écrasées, et un défilement horizontal est disponible si nécessaire.

#### Scenario: Largeur du tableau

- **WHEN** le tableau des événements est affiché
- **THEN** il utilise `table-layout: auto` (comportement naturel) avec `min-width: 42rem`
- **AND** le conteneur `.defilement` conserve son `overflow-x: auto` (barre de défilement horizontale en cas de dépassement)
- **AND** les cellules standard ont `white-space: nowrap` (dates, liens, en-têtes restent sur une ligne)
- **AND** la zone liste occupe plus d'espace que le formulaire (grille `minmax(300px, 4fr) minmax(0, 10fr)`)

### Requirement: Pagination de la liste

La liste des événements est paginée pour alléger l'affichage.

#### Scenario: Plus de 10 événements

- **WHEN** le nombre d'événements dépasse 10
- **THEN** seuls les 10 premiers (selon le tri actif) sont affichés
- **AND** une barre de pagination affiche « Page N / M (X événements) » avec les liens Précédent / Suivant
- **AND** les liens de pagination conservent les filtres et le tri actifs

#### Scenario: 10 événements ou moins

- **WHEN** le nombre d'événements filtrés est inférieur ou égal à 10
- **THEN** tous sont affichés sur une seule page, sans barre de pagination

### Requirement: Formulaire masqué par défaut

Le formulaire de saisie n'est affiché que sur demande, pour laisser
toute la largeur à la liste des événements.

#### Scenario: Page par défaut

- **WHEN** la page de saisie est ouverte sans paramètre
- **THEN** le formulaire « Nouvel événement » est masqué
- **AND** un lien « + Ajouter un événement » est visible au-dessus de la liste
- **AND** la liste occupe toute la largeur de l'écran

#### Scenario: Affichage du formulaire

- **WHEN** l'utilisateur clique sur « Ajouter un événement » (paramètre `afficher_formulaire=1`)
- **THEN** le formulaire s'affiche à gauche et la liste à droite
- **AND** le lien « Ajouter » conserve les filtres, le tri et la page actifs
- **AND** après un enregistrement ou une modification, le formulaire reste visible
- **AND** un lien « Fermer » dans le formulaire permet de le masquer (retire `afficher_formulaire` de l'URL, conserve filtres, tri et page)
- **AND** le formulaire ne contient pas de lien « Gérer les listes » (accessible via la barre de navigation)
