# Proposal: Indicateurs de conversion (nombre et taux)

## Why

Aujourd'hui, l'application calcule 4 indicateurs (prospects, demandes, taux de ghosting, RDV par canal) mais aucun ne mesure la **conversion** : le pourcentage de demandes qui aboutissent réellement à une séance (prestation réalisée). Cécile ne peut pas voir combien de ses demandes se concrétisent, ni si le taux diffère entre clients et prospects. Ces deux indicateurs figuraient pourtant dans le classeur Excel d'origine (documentés comme « Nombre de conversions » reportés faute de définition validée).

La demande couvre 2 indicateurs :

1. **Nombre de conversions** : nombre de demandes converties en séances sur la période filtrée, avec dépliement par statut du demandeur (client / prospect).
2. **Taux de conversion** : pourcentage global de demandes converties en séances sur la période filtrée, avec dépliement en 2 composantes :
   - **Composante clients** : demandes de clients converties / demandes de clients × 100
   - **Composante prospects** : demandes de prospects converties / demandes de prospects × 100

## What Changes

- **Nouveau** : classe `NbConversions` dans `src/kpi/kpi/indicateurs.py` — compte les demandes converties en séances sur la période, par statut du demandeur.
- **Nouveau** : classe `TauxConversion` dans `src/kpi/kpi/indicateurs.py` — calcule le taux global (conversions / demandes × 100) avec dépliement clients / prospects.
- **Modifié** : `REGISTRE_INDICATEURS` — ajout des deux nouvelles classes.
- **Nouveau** : tests dans `tests/test_calculs_kpi.py` pour les deux indicateurs.
- **Modifié** : `src/kpi/web/routes.py` — ajustement du tableau de bord pour afficher le taux global en pourcentage.
- Aucun changement de schéma de base de données.

## Règles métier

### Qu'est-ce qu'une demande ?

Une **demande** est un événement avec `action_public ∈ {"Demande", "Réservation"}`, dédoublonné par (personne, mois) conformément à la règle validée du 28/10/2026. Sur une période de plusieurs mois, une même personne peut compter plusieurs fois (une par mois où elle a fait une demande).

### Qu'est-ce qu'une conversion en séance ?

Une **conversion en séance** est une personne qui a :

- au moins une **demande** (`action_public ∈ {"Demande", "Réservation"}`) dans la période filtrée, ET
- au moins un événement avec `action_photographe = "Confirmation"` dans la même période filtrée.

- La conversion est comptée **une seule fois par personne sur toute la période** (pas de dédoublonnage par mois pour les conversions : si une personne a 3 demandes sur 3 mois et une confirmation, elle compte pour 1 conversion).
- Le **statut** (client / prospect) attribué à la conversion est celui du **premier événement de demande** de la personne dans la période.

### Qu'est-ce que le taux de conversion ?

Le taux de conversion se calcule **sur la période filtrée par les dates de l'écran KPI** :

```
taux_global = (nb_personnes_converties) / (nb_personnes_avec_demande) × 100
```

- Le dénominateur est le nombre de **personnes distinctes** ayant fait au moins une demande dans la période (pas le nombre d'événements de demande, pour éviter qu'une personne avec 5 demandes le même mois ne pèse 5 fois — même si le dédoublonnage par mois s'applique, sur plusieurs mois une personne peut apparaître plusieurs fois ; ici on compte la personne une seule fois sur toute la période).
- Le numérateur est le nombre de **personnes distinctes** parmi ces demandeurs qui ont aussi une `Confirmation` dans la période.
- Si aucune personne n'a fait de demande dans la période, le taux est `None` (pas de division par zéro) — affiche « — ».

### Décomposition en composantes

En dépliant le résultat, on affiche 2 composantes :

```
taux_clients    = (clients convertis)    / (clients avec demande)    × 100
taux_prospects  = (prospects convertis)  / (prospects avec demande)  × 100
```

- Le statut (client/prospect) est celui porté par le **premier événement de demande** de la personne dans la période.
- Si une composante a 0 demande, son taux est `None` (« — »).

## Hors périmètre

- Pas de suivi de cohorte (une confirmation peut venir d'une demande du mois précédent hors période).
- Pas de calcul de valeur moyenne du contrat (CA) — un indicateur séparé.
- Pas de modification du schéma SQLite.
- Pas de connecteur GA4 (les « conversions » GA sont un indicateur séparé, étape 6).
- Pas de détail par canal d'acquisition (remplacé par le détail par statut client/prospect).

## Hypothèses enregistrées

- Une « Confirmation » (`action_photographe = "Confirmation"`) matérialise la réalisation d'une séance pour une personne.
- La période de calcul est celle filtrée par les dates de début/fin de l'écran `/kpi`.
- Une personne est comptée une fois dans le dénominateur (demandes) et une fois dans le numérateur (conversions), même si elle a plusieurs demandes ou plusieurs confirmations sur la période.
- Le statut retenu est celui du premier événement de demande de la personne dans la période.
