# Proposal: Filtres de période par défaut sur 12 mois glissants

## Why

Aujourd'hui, quand Cécile ouvre `/kpi` sans aucun paramètre d'URL, les filtres de période sont vides : toutes les années et tous les mois sont sélectionnés (« Toutes les années » / « Tous les mois »). Les indicateurs affichent alors l'intégralité de l'historique, ce qui noie les tendances récentes dans des données anciennes peu actionnables.

Or l'usage courant est de consulter **l'activité récente** : Cécile veut voir d'un coup ce qui s'est passé sur les 12 derniers mois, sans avoir à régler manuellement les dates à chaque visite.

## What Changes

- **Modifié** : `src/kpi/web/routes.py` — dans `page_kpi` et `_page_ghosting_detail`, quand aucun des paramètres `annee_debut`, `mois_debut`, `annee_fin`, `mois_fin` n'est présent dans l'URL, pré-remplir automatiquement les filtres sur les **12 derniers mois glissants** (du mois en cours − 11 jusqu'au mois en cours).
- **Modifié** : `src/kpi/web/gabarits/kpi.html` — les sélecteurs de période reflètent ces valeurs par défaut (option sélectionnée).
- **Modifié** : `src/kpi/web/gabarits/kpi_ghosting.html` — idem pour la page de détail du ghosting.
- **Nouveau** : tests dans `tests/test_web.py` (ou `tests/test_kpi_web.py`) pour vérifier le calcul des 12 mois glissants et le pré-remplissage.

### Règles de calcul des 12 mois glissants

Soit `(A, M)` le couple (année, mois) de la date du jour :

- **Début** = le mois situé 11 mois avant `(A, M)` (ex: si on est en novembre 2026, le début est décembre 2025).
- **Fin** = `(A, M)` (mois en cours).
- Si l'utilisateur fournit **au moins un** des 4 paramètres de période dans l'URL, aucun filtre par défaut n'est appliqué : on respecte intégralement ce qu'il a demandé (même partiel).
- Le lien « Effacer les filtres » (`/kpi` sans paramètre) retombe sur les 12 mois glissants, pas sur « toutes les années ».

### Hors périmètre

- Pas de mémorisation des filtres personnalisés (ce serait un autre change).
- Pas de changement du schéma SQLite.
- Pas de filtre par défaut sur la page de saisie (`/`).
- Le tableau de bord (quand aucun indicateur n'est sélectionné) bénéficie aussi de cette période par défaut.

## Hypothèses enregistrées

- « 12 mois glissants » inclut le mois en cours (12 mois au total, mois courant compris).
- Le calcul se fait à chaque chargement de page, basé sur la date du jour : les filtres « par défaut » évoluent automatiquement avec le temps.
- Si la base ne contient aucun événement, les filtres par défaut s'appliquent quand même (les sélecteurs affichent la période calculée).
