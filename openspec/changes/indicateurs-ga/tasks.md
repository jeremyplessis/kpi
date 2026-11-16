# Tasks: Indicateurs GA

## 0. Validation des règles avec l'utilisatrice

- [ ] 0.1 Valider la règle "Visiteurs GA" (somme des visiteurs mensuels) — verify: règle notée dans la proposal
- [ ] 0.2 Définir la règle "Conversions" (GA4, suivi, ou croisé) — verify: règle choisie et documentée
- [ ] 0.3 Décider si un taux de conversion est pertinent — verify: décision notée

## 1. Classes d'indicateurs

- [ ] 1.1 Créer la classe `VisiteursGA(Indicateur)` dans `indicateurs.py` — verify: hérite de Indicateur, a libelle/description/dimensions
- [ ] 1.2 Implémenter `VisiteursGA.calculer(releves, periode)` — verify: retourne les bonnes lignes (tests unitaires)
- [ ] 1.3 Créer la classe `Conversions(Indicateur)` selon la règle validée — verify: calcul conforme à la règle
- [ ] 1.4 Enregistrer les nouvelles classes dans `REGISTRE_INDICATEURS` — verify: elles apparaissent dans le sélecteur `/kpi`

## 2. Adaptation de la route KPI

- [ ] 2.1 Modifier `page_kpi` pour charger aussi les données GA via `GoogleAnalyticsRepository` quand l'indicateur sélectionné est un indicateur GA — verify: pas de requête GA inutile pour les indicateurs suivi
- [ ] 2.2 Passer les relevés GA à l'indicateur (paramètre additionnel ou contexte) — verify: l'indicateur reçoit les bonnes données

## 3. Template

- [ ] 3.1 Vérifier que `kpi.html` affiche correctement les nouveaux indicateurs (tableau + graphique) — verify: les graphiques se rendent sans erreur JS
- [ ] 3.2 Ajouter les cartes GA dans le tableau de bord (si change 1 déjà fait) — verify: 6 cartes au total

## 4. Tests

- [ ] 4.1 Tests unitaires `VisiteursGA` dans `test_calculs_kpi.py` — verify: valeurs calculées à la main
- [ ] 4.2 Tests unitaires `Conversions` — verify: selon la règle choisie
- [ ] 4.3 Test web : `/kpi?indicateur=VisiteursGA` affiche les données — verify: `test_kpi_visiteurs_ga`
- [ ] 4.4 Test web : filtres de période appliqués aux indicateurs GA — verify: `test_kpi_ga_filtre_periode`
- [ ] 4.5 Test : les nouveaux indicateurs apparaissent dans le sélecteur — verify: `test_selecteur_indicateurs_ga`

## 5. Documentation

- [ ] 5.1 Créer `documentation/06_indicateurs_ga.md` avec les règles de calcul validées — verify: doc claire
- [ ] 5.2 Mettre à jour README.md (étape 6 terminée) — verify: tableau à jour
- [ ] 5.3 Mettre à jour CHANGELOG.md — verify: entrée pour les indicateurs GA

## 6. Intégration

- [ ] 6.1 Tous les tests passent — verify: `.venv/bin/python -m unittest discover -s tests`
- [ ] 6.2 Style PEP 8 — verify: `.venv/bin/pycodestyle src/ tests/`
