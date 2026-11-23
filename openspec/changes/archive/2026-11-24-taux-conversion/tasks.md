# Tasks: Indicateurs de conversion (nombre et taux)

## 1. Moteur de calcul — demandes ouvertes et confirmations

- [x] 1.1 Ajouter `_calculer_demandeurs_ouverts()` et `_compter_confirmations_dans_periode()` dans `src/kpi/kpi/indicateurs.py` — demandeurs = demandes dans P ∪ (demandes avant P sans Confirmation dans P) — verify: tests passent
- [x] 1.2 Ajouter `_dans_periode()` et `_avant_periode()` pour comparer (année, mois)

## 2. Moteur de calcul — classe NbConversions

- [x] 2.1 Créer `NbConversions(Indicateur)` avec `calculer_periode()` — compte les Confirmations dans P par statut — verify: import OK
- [x] 2.2 Ajouter `NbConversions` à `REGISTRE_INDICATEURS`

## 3. Moteur de calcul — classe TauxConversion

- [x] 3.1 Créer `TauxConversion(Indicateur)` avec `calculer_periode()` — taux = Confirmations / demandeurs ouverts × 100 — verify: tests passent
- [x] 3.2 Ajouter `TauxConversion` à `REGISTRE_INDICATEURS`

## 4. Tests unitaires

- [x] 4.1 `TestNbConversions` : 3 tests (total, par statut, hors période)
- [x] 4.2 `TestTauxConversion` : 7 tests (global, demande avant P ouverte/fermée, composantes, 0 demande, bornes, statut 1ère demande)
- [x] 4.3 `python -m unittest discover -s tests` — 116 tests OK

## 5. Intégration web

- [x] 5.1 `page_kpi` : détecter `calculer_periode` et passer tous les événements + bornes
- [x] 5.2 `_construire_tableau_de_bord` : idem, reçoit tous les événements
- [x] 5.3 Template `kpi.html` : affichage % pour TauxConversion (déjà fait)

## 6. Vérification

- [x] 6.1 Tous les tests passent (116)
- [x] 6.2 `pycodestyle` — pas de nouvelle violation
