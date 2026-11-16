# Proposal: Export PDF des écrans KPI

## Why

L'utilisatrice a besoin de partager ses indicateurs avec des tiers (comptable, banque, associés) ou de les imprimer pour des réunions. L'export PDF permettra de figer une période et ses indicateurs dans un document partageable, produit à partir des mêmes données que l'écran (aucune divergence possible).

## What Changes

- Ajout de la dépendance `weasyprint` dans `pyproject.toml`
- Nouvelle route `GET /kpi/export-pdf` qui génère un PDF à partir des filtres courants
- Le PDF reprend : la période filtrée, les 4 indicateurs avec tableaux et graphiques (rendu serveur via WeasyPrint)
- Bouton "Exporter en PDF" sur la page `/kpi` et sur la page détaillée ghosting
- Le PDF inclut l'en-tête avec le nom de l'application, la version, et la date de génération

## Capabilities

### New Capabilities
- `export-pdf/rapport-kpi`: Génération d'un PDF à partir des données KPI affichées

### Modified Capabilities
- `consultation-kpi/page-kpi`: Ajout d'un bouton "Exporter en PDF" conservant les filtres actifs

## Impact

- `pyproject.toml` : ajouter `weasyprint>=62` dans les dépendances
- `src/kpi/web/routes.py` : nouvelle route `page_export_pdf` qui rend un template HTML puis le convertit en PDF via WeasyPrint
- `src/kpi/web/gabarits/rapport_kpi.html` : nouveau template dédié au PDF (mise en page print, sans navigation)
- `src/kpi/web/gabarits/kpi.html` et `kpi_ghosting.html` : ajouter le bouton d'export
- `tests/test_kpi_web.py` : tests de la route PDF (statut 200, content-type `application/pdf`, contenu non vide)
- `documentation/04_ecran_consultation.md` : documenter l'export PDF
