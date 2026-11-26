# Tasks: Enregistrement de l'ordre de saisie des lignes

## 1. Schéma et migration

- [x] 1.1 Ajouter `ordre_saisie INTEGER NOT NULL DEFAULT 0` à la table `suivi_activite` dans `SCHEMA` (`src/kpi/bdd/connexion.py`) — verify: nouvelle base créée avec la colonne
- [x] 1.2 Implémenter la migration idempotente dans `BaseDonnees` : si la colonne manque (`PRAGMA table_info`), `ALTER TABLE` puis backfill `UPDATE ... SET ordre_saisie = ROW_NUMBER() OVER (ORDER BY id)` — verify: une base ancienne ouverte reçoit des `ordre_saisie` uniques croissants selon `id`
- [x] 1.3 Ajouter un index `idx_suivi_ordre ON suivi_activite(ordre_saisie)` — verify: présent dans le schéma

## 2. Modèle métier et repository

- [x] 2.1 Ajouter le champ `ordre_saisie: int | None = None` à `EvenementSuivi` (`src/kpi/suivi.py`) — verify: le dataclass accepte le champ
- [x] 2.2 Dans `SuiviRepository.ajouter()` (`src/kpi/bdd/modeles.py`), calculer `COALESCE(MAX(ordre_saisie), 0) + 1` dans la même transaction et l'insérer — verify: deux ajouts successifs reçoivent n puis n+1
- [x] 2.3 Ajouter `s.ordre_saisie` à `REQUETE_LECTURE` et le lire dans `_vers_evenement()` — verify: `lister()` et `obtenir()` retournent l'`ordre_saisie`
- [x] 2.4 Vérifier que `mettre_a_jour()` ne modifie pas `ordre_saisie` — verify: modification d'un événement, son rang est conservé

## 3. Import initial (backfill des données existantes)

- [x] 3.1 Dans `outils/import_initial.py`, passer `ordre_saisie=<position de la ligne>` (1..N) à chaque `EvenementSuivi` créé dans `_importer_suivi()` — verify: l'import de N lignes produit des `ordre_saisie` 1 à N dans l'ordre du classeur
- [x] 3.2 Vérifier le réimport `--force` : les `ordre_saisie` sont recalculés sans trou — verify: test avec double import

## 4. Tri web (sans affichage de l'ordre de saisie)

- [x] 4.1 Ne rien ajouter à l'écran de saisie : aucune colonne « N° » dans le tableau de `saisie.html` et aucun en-tête cliquable sur l'ordre de saisie (la colonne reste masquée) — verify: le rendu HTML du tableau ne contient aucune cellule ni aucun en-tête d'ordre de saisie
- [x] 4.2 Modifier `_trier_evenements()` (`src/kpi/web/routes.py`) pour appliquer systématiquement `ordre_saisie` décroissant comme dernier critère de départage, quel que soit le tri demandé — verify: deux événements de même date apparaissent, le plus récemment saisi en premier
- [x] 4.3 Vérifier qu'aucun en-tête du tableau ne propose de lien de tri sur l'ordre de saisie — verify: le HTML rendu ne contient aucun lien `tri=ordre_saisie`

## 5. Tests

- [x] 5.1 `tests/test_bdd.py` : test de la migration (base sans colonne → backfill selon `id`), test `ajouter()` incrémente `MAX+1`, test suppression puis ajout ne réutilise pas le rang, test `mettre_a_jour()` conserve le rang — verify: `python -m unittest tests.test_bdd` passe
- [x] 5.2 `tests/test_import_excel.py` : test que l'import attribue `ordre_saisie` 1..N selon l'ordre des lignes du classeur, et que `--force` recalcule proprement — verify: `python -m unittest tests.test_import_excel` passe
- [x] 5.3 `tests/test_web.py` : test d'absence de toute colonne « N° » dans le tableau rendu, test du départage par `ordre_saisie` descendant sur égalité de date (et sur égalité d'une autre colonne triée) — verify: `python -m unittest tests.test_web` passe
- [x] 5.4 Lancer la suite complète — verify: `python -m unittest discover -s tests` passe sans régression

## 6. Documentation

- [x] 6.1 Mettre à jour `documentation/02_import_initial.md` : l'ordre des lignes du classeur définit l'ordre de saisie — verify: doc à jour
- [x] 6.2 Mettre à jour `CHANGELOG.md` (format du skill changelog-kpi) — verify: entrée ajoutée
