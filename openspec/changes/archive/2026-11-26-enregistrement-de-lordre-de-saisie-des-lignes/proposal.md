# Proposal: Enregistrement de l'ordre de saisie des lignes

## Why

Aujourd'hui, la seule trace chronologique d'une ligne du suivi est sa `date`, qui est la date métier de l'événement (interaction avec le prospect/client), pas la date de saisie. Or plusieurs événements peuvent partager la même date, et des événements passés peuvent être saisis rétroactivement : la date seule ne permet pas de reconstituer dans quel ordre les lignes ont réellement été saisies. L'identifiant `id` (AUTOINCREMENT) reflète cet ordre, mais de façon implicite, invisible pour l'utilisatrice, et remis à zéro à chaque réimport `--force`.

L'objectif est de pouvoir reconstituer l'ordre chronologique des saisies dans la correspondance entre la photographe et ses prospects/clients, y compris pour les données déjà présentes dans la base.

## What Changes

- Nouvelle colonne `ordre_saisie INTEGER NOT NULL` sur la table `suivi_activite`, avec migration explicite (ALTER TABLE + backfill) pour les bases existantes conformément à la règle « jamais de modification de schéma sans migration »
- À chaque nouvelle saisie (web ou import), `ordre_saisie` vaut `MAX(ordre_saisie) + 1` : compteur monotone, jamais réutilisé même après suppression
- Le script d'import initial renseigne `ordre_saisie` selon l'ordre des lignes de l'onglet « Suivi » du classeur (backfill des données existantes)
- Le modèle `EvenementSuivi` gagne un champ `ordre_saisie`
- Le tableau des résultats de l'écran de saisie n'affiche pas la colonne « N° » (ordre de saisie), celle-ci n'est pas triable comme les autres colonnes, elle est toujours masquée
- Quel que soit le tri choisi, l'ordre de saisie descendant est toujours appliqué comme dernier critère de départage
- La modification d'un événement ne change jamais son `ordre_saisie`

## Capabilities

### New Capabilities
- `ordre-saisie/stockage`: Colonne `ordre_saisie` persistée, incrémentée à chaque saisie, backfillée à l'import
- `ordre-saisie/affichage`: Colonne « N° » non affichée dans le tableau des résultats et utilisée comme dernier critère de tri (descendant)

### Modified Capabilities
- `bdd/suivi-activite`: Schéma de `suivi_activite` (nouvelle colonne + migration), `SuiviRepository.ajouter()` calcule le prochain `ordre_saisie`, la requête de lecture le sélectionne
- `web/saisie`: Affichage de la colonne et tri secondaire par `ordre_saisie` décroissant
- `import/import-initial`: L'ordre des lignes du classeur devient l'`ordre_saisie` importé

## Impact

- `src/kpi/bdd/connexion.py` : ajout de la colonne dans le schéma + migration des bases existantes (backfill par ordre de `id`)
- `src/kpi/bdd/modeles.py` : `SuiviRepository.ajouter()` calcule `MAX(ordre_saisie)+1`, `REQUETE_LECTURE` sélectionne la colonne, `mettre_a_jour()` ne la modifie pas
- `src/kpi/suivi.py` : champ `ordre_saisie: int | None` sur `EvenementSuivi`
- `outils/import_initial.py` : l'ordre des lignes de l'onglet « Suivi » est passé comme `ordre_saisie`
- `src/kpi/web/routes.py` : `ordre_saisie` ajouté à `COLONNES_TRI`, tri secondaire toujours appliqué (descendant)
- `tests/test_bdd.py`, `tests/test_import_excel.py`, `tests/test_web.py` : tests de la colonne, du backfill, de l'affichage et du tri
