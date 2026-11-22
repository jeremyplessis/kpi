# Tasks: Indicateurs de conversion (nombre et taux)

## 1. Moteur de calcul — fonction utilitaire de détection des conversions

- [ ] 1.1 Ajouter la fonction `_detecter_conversions(_evenements) -> dict[tuple, int]` dans `src/kpi/kpi/indicateurs.py` — detecte la première transition prospect → client par personne, attribue le canal du premier contact — verify: `python -m unittest tests.test_calculs_kpi` passe
- [ ] 1.2 La fonction retourne un dict `{(année, mois, canal): nb_conversions}`

## 2. Moteur de calcul — classe NbConversions

- [ ] 2.1 Créer la classe `NbConversions(Indicateur)` avec `libelle = "Nombre de conversions"`, `dimensions = ("année", "mois", "canal")` — verify: import OK
- [ ] 2.2 Implémenter `calculer()` en utilisant `_detecter_conversions()` — verify: retourne des `LigneIndicateur` triées
- [ ] 2.3 Ajouter `NbConversions` à `REGISTRE_INDICATEURS` — verify: l'indicateur apparaît dans la liste de `/kpi`

## 3. Moteur de calcul — classe TauxConversion

- [ ] 3.1 Créer la classe `TauxConversion(Indicateur)` avec `libelle = "Taux de conversion"`, `dimensions = ("année", "mois", "canal")` — verify: import OK
- [ ] 3.2 Implémenter `calculer()` : calculer conversions et demandes par (année, mois, canal), retourner `conversions / demandes` pour chaque groupe avec demandes > 0 — verify: pas de division par zéro
- [ ] 3.3 Ajouter `TauxConversion` à `REGISTRE_INDICATEURS` — verify: l'indicateur apparaît dans la liste de `/kpi`

## 4. Tests unitaires

- [ ] 4.1 Ajouter `TestNbConversions` dans `tests/test_calculs_kpi.py` : conversion simple, arrivée directe client, dédoublonnage, canal d'acquisition = premier contact — verify: `python -m unittest tests.test_calculs_kpi.TestNbConversions` passe
- [ ] 4.2 Ajouter `TestTauxConversion` dans `tests/test_calculs_kpi.py` : taux par groupe, 0 conversion → 0 %, pas de demande → pas de ligne, taux borné 0-1 — verify: `python -m unittest tests.test_calculs_kpi.TestTauxConversion` passe
- [ ] 4.3 Vérifier que tous les tests existants passent encore — verify: `python -m unittest discover -s tests` sans régression

## 5. Intégration web — tableau de bord

- [ ] 5.1 Modifier `_construire_tableau_de_bord` dans `src/kpi/web/routes.py` pour que `TauxConversion` affiche le ratio global (somme conversions / somme demandes) et non la moyenne des taux — verify: la carte affiche un pourcentage cohérent
- [ ] 5.2 Vérifier que `NbConversions` affiche la somme dans le tableau de bord — verify: carte avec total entier

## 6. Vérification manuelle et style

- [ ] 6.1 Lancer l'application et vérifier visuellement `/kpi` : 6 cartes, tableau et graphique pour les 2 nouveaux indicateurs — verify: rendu correct dans le navigateur
- [ ] 6.2 `pycodestyle src/ tests/` sans erreur — verify: style PEP 8 respecté
- [ ] 6.3 `python -m unittest discover -s tests` — tous les tests passent
