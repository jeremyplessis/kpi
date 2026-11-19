# Proposal: Améliorer l'écran de consultation KPI (tableau de bord)

## Why

L'écran `/kpi` actuel permet de sélectionner un indicateur et une période, mais il manque une vue d'ensemble synthétique. L'utilisatrice (Cécile) doit aujourd'hui naviguer indicateur par indicateur pour avoir une vision globale de son activité. Un tableau de bord avec des cartes de synthèse permettrait de voir d'un coup les tendances clés.

## What Changes

- Ajout d'une vue "Tableau de bord" sur `/kpi` (par défaut quand aucun indicateur n'est sélectionné)
- Cartes de synthèse affichant les 4 indicateurs sur la période filtrée :
  - Nombre total de prospects sur la période
  - Nombre total de demandes sur la période
  - Taux de ghosting moyen sur la période
  - Nombre total de RDV sur la période
- Mini-graphiques sparkline dans chaque carte (tendance mensuelle)
- Liens vers le détail de chaque indicateur
- Amélioration de la navigation entre le tableau de bord et les indicateurs détaillés
- Correction du bug "écran vide" à la sélection d'un indicateur : les données
  JavaScript étaient sérialisées avec `join()` manuel, produisant des entités
  HTML `&#34;` invalides en JS. Remplacement par le filtre `|tojson`.

## Capabilities

### New Capabilities
- `consultation-kpi/tableau-bord`: Vue d'ensemble synthétique des 4 indicateurs avec cartes et tendances

### Modified Capabilities
- `consultation-kpi/page-kpi`: La page `/kpi` sans indicateur sélectionné affiche désormais le tableau de bord au lieu d'un message vide

## Impact

- `src/kpi/web/routes.py` : modifier `page_kpi` pour calculer les synthèses quand aucun indicateur n'est sélectionné
- `src/kpi/web/gabarits/kpi.html` : ajouter le bloc tableau de bord avec cartes et sparklines
- `src/kpi/kpi/indicateurs.py` : ajouter éventuellement des méthodes de synthèse (total sur période) si nécessaire
- `tests/test_kpi_web.py` : nouveaux tests pour le tableau de bord
- `documentation/04_ecran_consultation.md` : nouveau guide utilisateur
