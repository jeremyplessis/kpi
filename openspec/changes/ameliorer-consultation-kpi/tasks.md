# Tasks: Tableau de bord KPI

## 1. Calcul des synthèses côté serveur

- [x] 1.1 Ajouter une méthode `synthetiser(evenements)` ou calculer les totaux dans `page_kpi` pour chaque indicateur du registre — verify: les 4 totaux apparaissent dans le contexte Jinja2
- [x] 1.2 Regrouper les lignes de chaque indicateur par (année, mois) pour construire les séries mensuelles des sparklines — verify: chaque série contient un point par mois de la période
- [x] 1.3 Formater les valeurs : entiers pour les comptages, pourcentage pour le taux de ghosting — verify: le contexte contient les valeurs formatées correctement

## 2. Template du tableau de bord

- [x] 2.1 Modifier `kpi.html` : remplacer le bloc "Sélectionnez un indicateur" par le tableau de bord quand `indicateur_selectionne` est vide — verify: `/kpi` sans paramètre affiche les 4 cartes
- [x] 2.2 Créer le bloc HTML des cartes (une par indicateur) avec libellé, total, et canvas pour le sparkline — verify: le HTML contient 4 `<canvas>` avec les bons IDs
- [x] 2.3 Rendre chaque carte cliquable (lien vers `/kpi?indicateur=...` avec filtres conservés) — verify: clic sur une carte redirige vers le bon indicateur

## 3. Sparklines Chart.js

- [x] 3.1 Ajouter le script JavaScript pour initialiser 4 sparklines (un line chart compact par carte) — verify: chaque carte affiche un mini-graphique de tendance
- [x] 3.2 Gérer le cas période d'un seul mois (sparkline avec un point ou message) — verify: pas d'erreur JS quand un seul mois est filtré

## 4. Tests

- [x] 4.1 Test : `/kpi` sans indicateur affiche les 4 cartes avec les bons libellés — verify: `test_tableau_bord_affiche_cartes`
- [x] 4.2 Test : les totaux des cartes correspondent aux données de test — verify: `test_tableau_bord_totaux`
- [x] 4.3 Test : les filtres de période s'appliquent au tableau de bord — verify: `test_tableau_bord_filtre_periode`
- [x] 4.4 Test : clic sur carte redirige vers l'indicateur avec filtres conservés — verify: `test_carte_cliquable`
- [x] 4.5 Test : cohérence total carte vs somme tableau détaillé — verify: `test_coherence_total_detail`

## 5. Documentation

- [x] 5.1 Créer `documentation/04_ecran_consultation.md` — verify: le guide explique le tableau de bord et la navigation
- [x] 5.2 Mettre à jour le README.md (état étape 4) — verify: le tableau mentionne le tableau de bord

## 6. Intégration

- [x] 6.1 Tous les tests existants passent encore (73 tests) — verify: `.venv/bin/python -m unittest discover -s tests`
- [x] 6.2 Vérifier le style PEP 8 — verify: `.venv/bin/pycodestyle src/ tests/` (warnings préexistants uniquement, pas de régression)
