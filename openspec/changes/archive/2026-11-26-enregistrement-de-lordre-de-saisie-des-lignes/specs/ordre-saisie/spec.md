# Spec Delta: Ordre de saisie des lignes

## ADDED Requirements

### Requirement: Colonne `ordre_saisie` persistée sur chaque événement

La table `suivi_activite` comporte une colonne `ordre_saisie` (entier, non nul) donnant le rang chronologique de saisie de la ligne. Les bases existantes sont migrées à l'ouverture : les lignes reçoivent un `ordre_saisie` croissant selon leur `id` (ordre d'insertion constaté).

#### Scenario: Nouvelle saisie

- **WHEN** un événement est enregistré (via le formulaire web ou l'import)
- **THEN** son `ordre_saisie` vaut `MAX(ordre_saisie) + 1` sur l'ensemble des lignes existantes (ou 1 si la table est vide)

#### Scenario: Saisies successives

- **WHEN** trois événements sont saisis successivement
- **THEN** leurs `ordre_saisie` valent respectivement n, n+1, n+2 pour un n strictement croissant

#### Scenario: Suppression puis nouvelle saisie

- **WHEN** une ligne est supprimée puis qu'une nouvelle ligne est saisie
- **THEN** la nouvelle ligne reçoit un `ordre_saisie` supérieur à tous les existants (aucun réemploi du rang supprimé)

#### Scenario: Migration d'une base existante

- **WHEN** la base est ouverte et ne possède pas encore la colonne `ordre_saisie`
- **THEN** la colonne est ajoutée et chaque ligne existante reçoit un `ordre_saisie` unique, croissant selon l'`id` de la ligne
- **AND** la migration est idempotente (réouverture de la base ne change rien)

#### Scenario: Modification d'un événement

- **WHEN** un événement existant est modifié
- **THEN** son `ordre_saisie` est conservé inchangé

### Requirement: Import initial depuis le classeur

Lors de l'import initial, l'`ordre_saisie` de chaque événement importé correspond à la position de sa ligne dans l'onglet « Suivi » du classeur (1 pour la première ligne de données, etc.).

#### Scenario: Import d'un classeur

- **WHEN** le classeur contient N lignes de suivi dans son onglet « Suivi »
- **THEN** les événements importés ont pour `ordre_saisie` 1 à N, dans l'ordre des lignes du classeur

#### Scenario: Réimport avec --force

- **WHEN** un réimport `--force` est effectué
- **THEN** les `ordre_saisie` sont recalculés depuis l'ordre des lignes du classeur, sans trou ni doublon

### Requirement: Non-affichage de l'ordre de saisie dans le tableau des résultats

Le tableau des résultats de l'écran de saisie n'affiche pas l'`ordre_saisie` : aucune colonne « N° » n'apparaît et aucun en-tête ne permet de trier sur ce critère. L'ordre de saisie reste une donnée interne, utilisée uniquement comme critère de départage (voir requirement suivant).

#### Scenario: Absence de la colonne

- **WHEN** la page de saisie affiche le tableau des résultats
- **THEN** aucune colonne « N° » ni aucun en-tête d'ordre de saisie n'est présent dans le tableau

### Requirement: Ordre de saisie comme dernier critère de tri (descendant)

Quel que soit le tri principal demandé sur le tableau des résultats, les égalités sont départagées par `ordre_saisie` décroissant : à colonne principale égale, la saisie la plus récente apparaît en premier.

#### Scenario: Tri par date avec départage

- **WHEN** le tableau est trié par date (quel que soit le sens)
- **AND** plusieurs événements share la même date
- **THEN** ceux de même date sont ordonnés par `ordre_saisie` décroissant

#### Scenario: Tri par une autre colonne avec départage

- **WHEN** le tableau est trié par personne, statut, action, canal, action photographe ou commentaire
- **AND** plusieurs lignes ont la même valeur pour cette colonne
- **THEN** celles de même valeur sont ordonnées par `ordre_saisie` décroissant
