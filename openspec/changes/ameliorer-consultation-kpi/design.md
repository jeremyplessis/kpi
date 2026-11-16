# Design: Tableau de bord KPI

## Context

L'écran `/kpi` existe déjà avec filtres par période et sélecteur d'indicateur. Quand aucun indicateur n'est sélectionné, il affiche un message invitant à choisir. Nous allons remplacer ce message par un tableau de bord synthétique.

## Goals / Non-Goals

**Goals:**
- Vue d'ensemble des 4 indicateurs sur la période filtrée
- Cartes visuelles avec valeur agrégée + tendance (sparkline)
- Navigation fluide vers le détail de chaque indicateur

**Non-Goals:**
- Nouveaux indicateurs (ce sera l'étape 6)
- Export PDF (change séparé)
- Modification du moteur de calcul des indicateurs

## Decisions

### Decision 1: Calcul des synthèses côté serveur

Les valeurs agrégées sont calculées dans `page_kpi` (Python) et passées au template, plutôt que calculées en JavaScript. Cela garantit la cohérence avec les données affichées dans les tableaux détaillés.

### Decision 2: Sparkline via Chart.js

Chaque carte contient un mini-graphique sparkline (line chart sans axes) rendu par Chart.js, déjà chargé dans `base.html`. Pas de nouvelle dépendance.

### Decision 3: Période par défaut = 12 derniers mois

Quand aucun filtre de période n'est appliqué, le tableau de bord affiche les 12 derniers mois glissants pour avoir une tendance significative.

### Decision 4: Carte cliquable

Chaque carte est un lien vers `/kpi?indicateur=<Nom>` avec les filtres de période conservés, pour aller directement au détail.

## Data Flow

```
GET /kpi (sans indicateur)
  → page_kpi calcule :
      - pour chaque indicateur du REGISTRE_INDICATEURS :
          - lignes = indicateur.calculer(evenements_filtres)
          - total = somme des valeurs
          - serie_mensuelle = regroupement par (année, mois) pour le sparkline
  → rend kpi.html avec contexte tableau_de_bord
  → kpi.html affiche 4 cartes + sparklines Chart.js
```

## Structure du contexte ajouté

```python
{
    "tableau_de_bord": [
        {
            "nom": "NbProspects",
            "libelle": "Nombre de prospects",
            "total": 48,
            "unite": "",
            "pourcentage": False,
            "serie": [("2026-01", 5), ("2026-02", 8), ...],  # pour sparkline
            "lien": "/kpi?indicateur=NbProspects&annee_debut=...",
        },
        ...
    ]
}
```
