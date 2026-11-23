# Tasks: Filtres de période par défaut sur 12 mois glissants

## 1. Fonction utilitaire de calcul

- [x] 1.1 Ajouter `_periode_par_defaut(_aujourdhui: date | None = None) -> tuple[int, int, int, int]` dans `src/kpi/web/routes.py` — retourne `(année_début, mois_début, année_fin, mois_fin)` pour les 12 derniers mois glissants — verify: `python -c "from kpi.web.routes import _periode_par_defaut; print(_periode_par_defaut(date(2026, 11, 15)))"` affiche `(2025, 12, 2026, 11)`
- [x] 1.2 Gérer le passage d'année : janvier 2026 → début février 2025 — verify: `_periode_par_defaut(date(2026, 1, 10))` retourne `(2025, 2, 2026, 1)`

## 2. Application dans page_kpi

- [x] 2.1 Dans `page_kpi`, après lecture des query_params, si aucun des 4 paramètres de période n'est présent, appeler `_periode_par_defaut()` et remplir `_annee_debut`, `_mois_debut`, `_annee_fin`, `_mois_fin` — verify: ouvrir `/kpi` sans paramètre affiche les sélecteurs sur les 12 derniers mois
- [x] 2.2 S'assurer que les années de la période par défaut sont dans `annees_disponibles` même si la base est vide — verify: les sélecteurs d'année affichent 2025 et 2026 même sans événements

## 3. Application dans _page_ghosting_detail

- [x] 3.1 Appliquer la même logique dans `_page_ghosting_detail` — verify: `/kpi/TauxGhosting` sans paramètre pré-remplit les 12 derniers mois

## 4. Tests unitaires

- [x] 4.1 Ajouter `TestPeriodeParDefaut` dans `tests/test_web.py` : tester `_periode_par_defaut` avec plusieurs dates (milieu d'année, janvier, décembre, 1er du mois, 31 du mois) — verify: `python -m unittest tests.test_web.TestPeriodeParDefaut` passe
- [x] 4.2 Tester que `page_kpi` sans paramètre applique les filtres par défaut (vérifier le contexte passé au template) — verify: test passe
- [x] 4.3 Tester que `page_kpi` avec un seul paramètre de période ne modifie pas les autres — verify: test passe
- [x] 4.4 Vérifier l'absence de régression : `python -m unittest discover -s tests` — tous les tests passent

## 5. Vérification manuelle et style

- [x] 5.1 Lancer l'application et ouvrir `/kpi` dans le navigateur : vérifier que les filtres affichent les 12 derniers mois — verify: sélecteurs pré-remplis correctement
- [x] 5.2 Cliquer sur « Effacer les filtres » : vérifier le retour aux 12 derniers mois — verify: comportement identique à l'ouverture initiale
- [x] 5.3 Ouvrir `/kpi?annee_debut=2024` : vérifier qu'aucun filtre par défaut n'est appliqué sur la fin — verify: seule l'année de début est filtrée
- [x] 5.4 `pycodestyle src/ tests/` sans erreur — verify: style PEP 8 respecté
