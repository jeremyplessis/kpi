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

## 7. Correction du rendu JS des indicateurs (bug écran vide)

- [x] 7.1 Remplacer `join('", "')` par `|tojson` dans `kpi.html` pour `lignesIndicateur` (ligne ~454) — verify: le JS généré contient `["2026","1","formulaire de contact"]` sans `&#34;`
- [x] 7.2 Remplacer `join('", "')` par `|tojson` pour `dimensionNames` (ligne ~462) — verify: `dimensionNames` est un tableau JS valide
- [x] 7.3 Ajouter un test de non-régression : le HTML rendu ne contient pas `&#34;` dans les blocs `<script>` — verify: `test_kpi_web.py`
- [x] 7.4 Vérifier que tous les tests existants passent encore — verify: 88 tests OK
- [x] 7.5 Corriger l'appel `generateTableHTML(hierarchy, ...)` → `generateTableHTML(hierarchy.children || {}, ...)` dans `kpi.html` — verify: le JS ne plante plus avec TypeError toFixed sur un objet, le tbody est peuplé
- [x] 7.6 Ajouter un test de non-régression pour 7.5 — verify: `test_kpi_tableau_appel_hierarchy_children` dans `test_kpi_web.py`
- [x] 7.7 Tous les tests passent — verify: 89 tests OK
- [x] 7.8 Envelopper le contenu récursif du tableau dépliable dans un `<table>` dans le `<td>` — verify: le navigateur ne remonte plus les `<tr>` imbriqués hors du conteneur masqué, les sous-niveaux sont repliés par défaut
- [x] 7.9 Rendre les `data-key`/`data-parent` uniques par chemin (`2025/1` au lieu de `1`) — verify: le clic sur un mois ne bascule plus les conteneurs des autres années
- [x] 7.10 Afficher le tableau en arborescence : libellé toujours dans la première colonne avec `padding-left` proportionnel à la profondeur — verify: 2025 → 1 → canal visuellement indentés
- [x] 7.11 Ajouter un zebra striping (`feuille-pair`/`feuille-impair`) sur les lignes finales sans enfants — verify: alternance de fond sur les feuilles
- [x] 7.12 Supprimer les en-têtes de colonnes du tableau dépliable — verify: plus de `<thead>` dans `tableau-kpi`
- [x] 7.13 Envelopper chaque `<canvas>` Chart.js dans un `<div style="height: Npx;">` — verify: les graphiques ont une hauteur visible (5 canvases dans kpi.html + 1 dans kpi_ghosting.html)
- [x] 7.14 Servir Chart.js en local (`/static/chart.umd.min.js`) au lieu du CDN — verify: `GET /static/chart.umd.min.js` → 200, `base.html` ne référence plus jsdelivr
