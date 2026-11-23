# Tasks: Indicateurs de conversion (nombre et taux)

## 1. Moteur de calcul — fonction utilitaire demandes/conversions

- [ ] 1.1 Ajouter `_detecter_demandes_et_conversions(_evenements) -> tuple[set[str], dict[str, str], set[str]]` dans `src/kpi/kpi/indicateurs.py` — retourne (personnes_avec_demande, statut_par_personne, personnes_converties) — verify: `python -m unittest tests.test_calculs_kpi` passe
- [ ] 1.2 La fonction identifie les demandes (`action_public ∈ {"Demande", "Réservation"}`) et les confirmations (`action_photographe == "Confirmation"`), une personne = 1 demandeur et 1 conversion max sur la période

## 2. Moteur de calcul — classe NbConversions

- [ ] 2.1 Créer `NbConversions(Indicateur)` avec `libelle = "Nombre de conversions"`, `dimensions = ("statut",)` — verify: import OK
- [ ] 2.2 Implémenter `calculer()` : retourner les lignes `("Tous", total)`, `("client", nb)`, `("prospect", nb)` — verify: retourne des `LigneIndicateur`
- [ ] 2.3 Ajouter `NbConversions` à `REGISTRE_INDICATEURS` — verify: apparaît dans la liste de `/kpi`

## 3. Moteur de calcul — classe TauxConversion

- [ ] 3.1 Créer `TauxConversion(Indicateur)` avec `libelle = "Taux de conversion"`, `dimensions = ("statut",)` — verify: import OK
- [ ] 3.2 Implémenter `calculer()` : taux global + composantes client/prospect en pourcentage (0-100), `None` si division par zéro — verify: pas de division par zéro
- [ ] 3.3 Ajouter `TauxConversion` à `REGISTRE_INDICATEURS` — verify: apparaît dans la liste de `/kpi`

## 4. Tests unitaires

- [ ] 4.1 Ajouter `TestNbConversions` dans `tests/test_calculs_kpi.py` : demande+confirmation = conversion, demande seule ≠ conversion, confirmation seule ≠ conversion, plusieurs demandes = 1 conversion, dépliement par statut — verify: `python -m unittest tests.test_calculs_kpi.TestNbConversions` passe
- [ ] 4.2 Ajouter `TestTauxConversion` dans `tests/test_calculs_kpi.py` : taux global, composantes client/prospect, 0 demande → None, statut sans demande → None, taux borné 0-100 — verify: `python -m unittest tests.test_calculs_kpi.TestTauxConversion` passe
- [ ] 4.3 Vérifier l'absence de régression — verify: `python -m unittest discover -s tests` sans régression

## 5. Intégration web — tableau de bord et page indicateur

- [ ] 5.1 Modifier `_construire_tableau_de_bord` dans `src/kpi/web/routes.py` pour que `TauxConversion` affiche le taux global (ligne « Tous ») en % — verify: carte cohérente
- [ ] 5.2 Vérifier que le tableau dépliable de `/kpi` gère une dimension `("statut",)` avec dépliement « Tous » → client/prospect — verify: le clic déplie correctement
- [ ] 5.3 Adapter le graphique Chart.js pour 1 dimension avec 3 barres (Tous, Clients, Prospects) — verify: rendu correct

## 6. Vérification manuelle et style

- [ ] 6.1 Lancer l'application et vérifier `/kpi` : 6 cartes, tableau dépliable pour les 2 nouveaux indicateurs, graphique 3 barres — verify: rendu correct dans le navigateur
- [ ] 6.2 `pycodestyle src/ tests/` sans erreur — verify: style PEP 8 respecté
- [ ] 6.3 `python -m unittest discover -s tests` — tous les tests passent
