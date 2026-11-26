# Design: Enregistrement de l'ordre de saisie des lignes

## Context

La table `suivi_activite` possède un `id INTEGER PRIMARY KEY AUTOINCREMENT` qui reflète déjà l'ordre d'insertion, mais de façon implicite : non affiché, non triable comme tel, et remis à zéro lors d'un réimport `--force`. La `date` de la ligne est la date métier de l'événement, insuffisante pour distinguer deux saisies du même jour ou des saisies rétroactives. Le tableau des résultats de l'écran de saisie (`saisie.html`) est trié via `COLONNES_TRI` avec un tri par défaut `date` décroissante, sans critère de départage explicite.

## Goals / Non-Goals

**Goals:**
- Stocker un ordre de saisie explicite, monotone et persistant (`ordre_saisie`) sur chaque ligne de `suivi_activite`
- Backfill des données existantes : à l'import initial, l'ordre des lignes du classeur ; pour une base déjà existante, migration par ordre de `id` (qui reflète l'ordre d'insertion)
- Ne pas afficher l'ordre de saisie dans le tableau des résultats et l'utiliser comme dernier critère de tri, toujours descendant
- Ne jamais modifier l'ordre de saisie d'une ligne existante (la modification d'un événement conserve son rang)

**Non-Goals:**
- Réordonner manuellement les lignes (pas de déplacement « Monter/Descendre » dans l'UI) — l'ordre est figé à la saisie
- Utiliser un horodatage de saisie (`date_saisie`) — la précision à la seconde n'apporte rien pour un usage humain
- Rendre l'ordre de saisie modifiable à la modification d'un événement

## Decisions

### Decision 1: Colonne dédiée `ordre_saisie INTEGER NOT NULL`

Plutôt que de s'appuyer sur `id` (implicite, réinitialisé au réimport), une colonne explicite `ordre_saisie` est ajoutée. C'est un rang entier, pas un timestamp : plus simple, lisible comme « N° de saisie », et suffisant pour ordonner.

### Decision 2: Migration explicite des bases existantes

Conformément à la règle du projet (« ne jamais modifier le schéma sans migration »), la colonne est ajoutée par `ALTER TABLE suivi_activite ADD COLUMN ordre_saisie INTEGER`, puis backfillée avec `ROW_NUMBER() OVER (ORDER BY id)` : l'`id` AUTOINCREMENT reflète fidèlement l'ordre de saisie des lignes existantes. La colonne est ensuite passée en `NOT NULL` via une table temporaire si l'on veut la contrainte forte (SQLite ne permet pas d'ajouter directement une colonne NOT NULL avec valeur par défaut non constante ; une valeur par défaut `0` puis backfill, ou recréation de table, selon le choix d'implémentation retenu dans les tâches).

### Decision 3: Incrément à la saisie (`MAX(ordre_saisie) + 1`)

Dans `SuiviRepository.ajouter()`, le prochain `ordre_saisie` est calculé comme `COALESCE(MAX(ordre_saisie), 0) + 1` avant l'INSERT. Les suppressions ne provoquent pas de réutilisation (les trous dans la séquence sont normaux et sans conséquence). La modification (`mettre_a_jour`) ne touche pas la colonne.

### Decision 4: Import initial = ordre des lignes du classeur

L'onglet « Suivi » du classeur est parcouru dans l'ordre de ses lignes ; chaque événement importé reçoit `ordre_saisie = 1, 2, 3…` selon sa position. Ainsi, le réimport `--force` reconstruit un ordre de saisie déterministe et cohérent avec le classeur source.

### Decision 5: Affichage et tri dans le tableau des résultats

- `EvenementSuivi` gagne un champ `ordre_saisie: int | None = None`, renseigné à la lecture.
- `ordre_saisie` est ajouté à `COLONNES_TRI` : la colonne « N° » ne devient pas triable comme les autres (cliquer inverse le sens) puisqu'elle n'est pas affichée.
- Quel que soit le tri demandé, un tri final par `ordre_saisie` **descendant** est toujours appliqué en dernier critère de départage (les saisies les plus récentes d'abord en cas d'égalité), conformément à la demande de l'utilisatrice.

## Risks / Mitigations

- **Concurrence** : application mono-utilisateur locale, une seule connexion par requête ; le `MAX+1` est donc sûr. Mitigation : calcul dans la même transaction que l'INSERT.
- **Bases existantes sans migration** : la migration est exécutée à l'ouverture de la base (`BaseDonnees`), idempotente (vérification de l'existence de la colonne via `PRAGMA table_info`).
- **Classeur non ordonné** : l'ordre des lignes Excel est pris comme source de vérité ; documenté dans le guide d'import.
