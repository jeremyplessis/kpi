# Design: Export PDF KPI

## Context

WeasyPrint est le choix acté dans la proposition d'architecture (documentation/01) car il permet de réutiliser les mêmes gabarits HTML/Jinja2 pour l'écran et le PDF, avec un rendu serveur fidèle. Les graphiques Chart.js étant en JavaScript, ils ne seront pas dans le PDF : on les remplace par des tableaux clairs, ou on génère des graphiques statiques côté serveur.

## Goals / Non-Goals

**Goals:**
- PDF téléchargeable depuis `/kpi` avec les filtres actifs
- Contenu identique aux données affichées à l'écran (mêmes calculs, même période)
- Mise en page propre pour impression A4

**Non-Goals:**
- Graphiques interactifs dans le PDF (Chart.js est client-side)
- Export PDF de l'écran de saisie (hors scope)
- Génération automatique périodique (hors scope)

## Decisions

### Decision 1: WeasyPrint pour le rendu PDF

WeasyPrint transforme du HTML/CSS en PDF côté serveur. Il supporte les polices, les tableaux, les mises en page CSS print (`@media print`). Ajouté comme dépendance standard.

### Decision 2: Template dédié au PDF

Un gabarit `rapport_kpi.html` séparé des templates d'écran, avec :
- Une mise en page A4 (`@page { size: A4; margin: 2cm; }`)
- Pas de navigation, pas de JavaScript
- Les tableaux de données complets (pas de dépliage)
- Les sparklines remplacés par des tableaux mensuels
- En-tête avec "KPI — Cécile Plessis Photographe", version, date de génération, période

### Decision 3: Route dédiée avec les mêmes filtres

`GET /kpi/export-pdf?indicateur=...&annee_debut=...` reçoit les mêmes paramètres que `/kpi`, recalcule les mêmes données, rend `rapport_kpi.html`, et retourne un `Response` avec `media_type="application/pdf"` et `Content-Disposition: attachment; filename="kpi_2026-01_2026-06.pdf"`.

### Decision 4: Un seul PDF pour tous les indicateurs (v1)

Le PDF contient les 4 indicateurs sur la période filtrée, pas un seul. Si un indicateur spécifique est sélectionné, le PDF ne contient que celui-là. Cela évite d'avoir à choisir.

### Decision 5: Nom de fichier explicite

Le nom du fichier PDF inclut la période : `kpi_2026-01_2026-06.pdf` ou `kpi_tout.pdf` si aucune période.

## Data Flow

```
GET /kpi/export-pdf?indicateur=NbDemandes&annee_debut=2026&...
  → page_export_pdf lit les mêmes query params que page_kpi
  → filtre les événements (même méthode _filtrer_par_periode)
  → calcule tous les indicateurs (ou un seul si sélectionné)
  → rend rapport_kpi.html avec le contexte complet
  → weasyprint.HTML(string=html).write_pdf() → bytes
  → Response(content=pdf_bytes, media_type="application/pdf")
```
