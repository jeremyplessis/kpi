# Design: Indicateurs GA

## Context

Les tables `ga_visiteurs`, `ga_canaux`, `ga_requetes` contiennent les relevés GA4 (manuels aujourd'hui, automatiques après l'étape 5). Les indicateurs actuels (`src/kpi/kpi/indicateurs.py`) ne lisent que `SuiviRepository`. Les nouveaux indicateurs devront lire aussi `GoogleAnalyticsRepository`.

## Goals / Non-Goals

**Goals:**
- Indicateur "Visiteurs GA" : total des visiteurs mensuels sur la période
- Indicateur "Conversions" : règle à définir (voir proposal)
- Intégration transparente dans l'écran KPI existant

**Non-Goals:**
- Modification des indicateurs existants
- Graphiques spécifiques GA (les graphiques existants suffisent)
- Croisement complexe suivi × GA (v2 si pertinent)

## Decisions

### Decision 1: Les indicateurs GA lisent directement en base

Contrairement aux indicateurs actuels qui reçoivent une liste d'événements, les indicateurs GA auront besoin d'accéder à `GoogleAnalyticsRepository`. Deux approches :

**Approche retenue** : la route `page_kpi` charge les données GA via `GoogleAnalyticsRepository` et les passe à l'indicateur via un paramètre optionnel, ou l'indicateur reçoit un "contexte de calcul" contenant suivi + GA.

### Decision 2: Règle "Visiteurs GA" (proposée, à valider)

`VisiteursGA` : somme de `ga_visiteurs.visiteurs` sur la période, regroupée par (année, mois). Dimension : (année, mois). Valeur : nombre de visiteurs.

### Decision 3: Règle "Conversions" (à définir avec l'utilisatrice)

Pistes :
- A) Conversions GA4 : événements marqués comme "conversion" dans GA4 (nécessite que Cécile ait configuré des événements de conversion dans GA4)
- B) Conversions suivi : événements du suivi avec `action_photographe = "RDV"` ou `action_public = "Paiement"`, dédoublonnés par mois et par personne
- C) Croisé : visiteurs GA × taux de conversion du suivi

**À valider avant implémentation.** La spec prévoit un mécanisme permettant de brancher la règle choisie sans changer l'interface.

### Decision 4: Affichage dans le tableau de bord

Les nouveaux indicateurs apparaissent comme des cartes supplémentaires dans le tableau de bord, et comme des options dans le sélecteur d'indicateur de `/kpi`.

## Data Flow

```
GET /kpi?indicateur=VisiteursGA
  → page_kpi ouvre la base
  → SuiviRepository(_base).lister() → evenements (pour filtrage période)
  → GoogleAnalyticsRepository(_base).lister_visiteurs() → relevés GA
  → VisiteursGA().calculer(releves_visiteurs, periode) → lignes
  → rend kpi.html avec les lignes
```
