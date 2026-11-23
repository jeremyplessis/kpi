# Proposal: Indicateurs de conversion (nombre et taux)

## Why

L'application calcule 4 indicateurs (prospects, demandes, taux de ghosting, RDV par canal) mais aucun ne mesure la **conversion** : le pourcentage de demandes qui aboutissent réellement à une séance (prestation réalisée). Cécile veut voir, sur la période filtrée de l'écran KPI, quel taux de ses demandes se concrétise, et si ce taux diffère entre clients et prospects.

## What Changes

- **Nouveau** : classe `NbConversions` dans `src/kpi/kpi/indicateurs.py` — compte les conversions (Confirmations) dans la période, avec ligne « Tous » et dépliement par statut.
- **Nouveau** : classe `TauxConversion` dans `src/kpi/kpi/indicateurs.py` — calcule le taux global (Confirmations / demandes ouvertes × 100) avec dépliement clients / prospects.
- **Modifié** : `REGISTRE_INDICATEURS` — ajout des deux nouvelles classes.
- **Nouveau** : tests dans `tests/test_calculs_kpi.py`.
- **Modifié** : `src/kpi/web/routes.py` — les indicateurs de conversion reçoivent tous les événements (pas seulement la période filtrée) + les bornes de période, pour détecter les demandes antérieures encore ouvertes.
- Aucun changement de schéma de base de données.

## Règles métier (révisées novembre 2026)

### Période

La période est celle filtrée par les dates de début/fin de l'écran `/kpi`. Soit `P = [début, fin]` cette période (en année/mois).

### Qu'est-ce qu'une conversion ?

Une **conversion** est un événement avec `action_photographe = "Confirmation"` dont la date est dans la période P. **Toute Confirmation compte**, sans vérifier qu'une demande existe.

```
nb_conversions = nombre d'événements Confirmation dans P
```

### Qu'est-ce qu'une demande ouverte (dénominateur) ?

Une demande est un événement avec `action_public ∈ {"Demande", "Réservation"}`. Une personne peut avoir plusieurs demandes.

Le dénominateur compte les **personnes ayant au moins une demande ouverte** à la fin de la période :

1. **Demandes dans la période** : toute personne ayant au moins une demande dont la date est dans P est comptée (même si elle a aussi une Confirmation dans P).
2. **Demandes antérieures encore ouvertes** : toute personne ayant au moins une demande dont la date est antérieure au début de P, ET qui n'a **aucune Confirmation à une date ≤ fin de P** (la demande n'a jamais été convertie), est comptée. Une Confirmation à n'importe quelle date antérieure ou égale à la fin de la période ferme la demande.

```
demandeurs = {personnes avec demande dans P}
           ∪ {personnes avec demande avant P et sans Confirmation dans P}
```

### Qu'est-ce que le taux de conversion ?

```
taux_global = nb_conversions / len(demandeurs) × 100
```

- Si `demandeurs` est vide, le taux est 0 (pas de division par zéro).
- Le taux est borné entre 0 et 100 %.

### Décomposition en composantes

En dépliant le résultat, deux composantes :

```
taux_clients   = conversions_clients / demandeurs_clients × 100
taux_prospects = conversions_prospects / demandeurs_prospects × 100
```

- Le **statut** (client/prospect) d'une personne est celui de sa **première demande** (chronologiquement, avant ou dans P). Un `statut_contact` vide (None) vaut **« prospect »** (règle validée : une demande sans statut est un prospect).
- `conversions_S` = nombre de Confirmations dans P pour des personnes de statut S.
- `demandeurs_S` = nombre de demandeurs de statut S (selon la règle ci-dessus).
- Si `demandeurs_S` = 0, la composante n'apparaît pas.

## Hors périmètre

- Pas de calcul de CA.
- Pas de modification du schéma SQLite.
- Pas de connecteur GA4.

## Hypothèses enregistrées

- Une demande peut courir sur plusieurs mois avant sa conversion : une demande de janvier peut être confirmée en mars.
- Une Confirmation dans la période ferme les demandes antérieures de la même personne (elles ne sont plus comptées comme ouvertes).
- Le statut retenu est celui de la première demande de la personne (chronologiquement).
