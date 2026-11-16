# Tasks: Connecteur GA4

## 1. Dépendance et configuration

- [ ] 1.1 Ajouter `google-analytics-data>=0.18` dans `pyproject.toml` — verify: `.venv/bin/pip install -e .` installe la lib
- [ ] 1.2 Ajouter `ga4-credentials.json` (et `*-credentials.json`) dans `.gitignore` — verify: `git status` ne montre pas le fichier de clé

## 2. Module client GA4

- [ ] 2.1 Créer `src/kpi/ga4.py` avec une classe `ConnecteurGA4` — verify: importable sans erreur
- [ ] 2.2 Implémenter l'authentification par compte de service (fichier JSON) — verify: la méthode d'init charge les credentials
- [ ] 2.3 Implémenter `recuperer_visiteurs(property_id, annee, mois)` → int — verify: retourne le nombre de visiteurs du mois (mock API dans les tests)
- [ ] 2.4 Implémenter `recuperer_canaux(property_id, annee, mois)` → dict[canal, int] — verify: retourne la répartition par canal
- [ ] 2.5 Implémenter `recuperer_requetes(property_id, annee, mois)` → dict[requete, int] — verify: retourne les requêtes (ou vide si non disponible)
- [ ] 2.6 Implémenter `recuperer_periode(...)` qui boucle sur les mois et retourne un rapport — verify: le rapport contient le nombre de mois traités

## 3. Page web et routes

- [ ] 3.1 Créer la route `GET /ga4` dans `routes.py` — verify: la page s'affiche avec le formulaire
- [ ] 3.2 Créer le template `ga4.html` (formulaire période + bouton + dernier relevé) — verify: rendu correct
- [ ] 3.3 Créer la route `POST /ga4/recuperer` avec vérification Origin — verify: POST sans Origin valide → 403
- [ ] 3.4 La route appelle `ConnecteurGA4.recuperer_periode` puis enregistre via `GoogleAnalyticsRepository` avec `origine="api"` — verify: données enregistrées en base
- [ ] 3.5 Gérer les erreurs (clé manquante, API inaccessible) avec message clair — verify: message affiché, pas de crash
- [ ] 3.6 Ajouter le lien "GA4" dans `base.html` navigation — verify: lien présent sur toutes les pages

## 4. Tests

- [ ] 4.1 Créer `tests/test_ga4.py` — verify: fichier de tests créé
- [ ] 4.2 Test : `ConnecteurGA4` avec credentials mockés retourne les bonnes valeurs — verify: `test_recuperer_visiteurs_mock`
- [ ] 4.3 Test : `recuperer_periode` boucle correctement sur la période — verify: `test_recuperer_periode`
- [ ] 4.4 Test : `GET /ga4` affiche le formulaire — verify: `test_page_ga4`
- [ ] 4.5 Test : `POST /ga4/recuperer` enregistre en base (avec mock du connecteur) — verify: `test_recuperer_enregistre`
- [ ] 4.6 Test : `POST /ga4/recuperer` sans clé → message d'erreur — verify: `test_recuperer_sans_cle`
- [ ] 4.7 Test : idempotence (double récupération = pas de doublon) — verify: `test_recuperer_idempotent`
- [ ] 4.8 Test : POST depuis autre site → 403 — verify: `test_ga4_origine_externe`

## 5. Documentation

- [ ] 5.1 Créer `documentation/05_connecteur_ga4.md` avec la procédure complète compte de service — verify: doc claire, étapes numérotées
- [ ] 5.2 Mettre à jour README.md (état étape 5) — verify: tableau à jour
- [ ] 5.3 Mettre à jour CHANGELOG.md — verify: entrée pour le connecteur GA4

## 6. Intégration

- [ ] 6.1 Tous les tests passent — verify: `.venv/bin/python -m unittest discover -s tests`
- [ ] 6.2 Style PEP 8 — verify: `.venv/bin/pycodestyle src/ tests/`
