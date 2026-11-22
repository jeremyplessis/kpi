# Proposal: Indicateurs de conversion (nombre et taux)

## Why

Aujourd'hui, l'application calcule 4 indicateurs (prospects, demandes, taux de ghosting, RDV par canal) mais aucun ne mesure la **conversion** : le passage d'un prospect au statut de client. Cécile ne peut pas voir combien de ses prospects deviennent réellement clients, ni à quel taux, ni par quel canal d'acquisition. Ces deux indicateurs figuraient pourtant dans le classeur Excel d'origine (documentés comme « Nombre de conversions » reportés faute de définition validée).

La demande couvre 2 indicateurs :

1. **Nombre de conversions** : nombre total de prospects convertis en clients, par année et par mois, avec dépliement par canal d'acquisition (année → mois → canal).
2. **Taux de conversion** : pourcentage de conversions par rapport au nombre total de demandes, avec le même détail par année, mois et canal d'acquisition.

## What Changes

- **Nouveau** : classe `NbConversions` dans `src/kpi/kpi/indicateurs.py` — compte les conversions par (année, mois, canal d'acquisition).
- **Nouveau** : classe `TauxConversion` dans `src/kpi/kpi/indicateurs.py` — calcule le taux de conversion par (année, mois, canal) comme ratio conversions / demandes.
- **Modifié** : `REGISTRE_INDICATEURS` — ajout des deux nouvelles classes.
- **Nouveau** : tests dans `tests/test_calculs_kpi.py` pour les deux indicateurs.
- **Modifié** : `src/kpi/web/routes.py` — ajustement du tableau de bord pour gérer le pourcentage du taux de conversion (moyenne pondérée ou ratio global selon les dimensions).
- Aucun changement de schéma de base de données.

## Règles métier proposées

### Qu'est-ce qu'une conversion ?

Une **conversion** est le passage d'une personne du statut « prospect » au statut « client ». Concrètement, dans le suivi, c'est la première fois qu'un événement porte `statut_contact = "client"` pour une personne qui avait zuvor un événement avec `statut_contact = "prospect"`.

- La conversion est comptée **une seule fois par personne** (à la date du premier événement « client »).
- Le **canal d'acquisition** attribué à la conversion est le canal du **premier événement** de la personne (le canal par lequel elle est arrivée), pas celui de l'événement de conversion.
- La conversion est attribuée au **mois/année du premier événement « client »**.

### Qu'est-ce que le taux de conversion ?

Le taux de conversion rapporte le nombre de conversions au nombre de demandes (tel que défini par l'indicateur `NbDemandes`, avec dédoublonnage par personne et par mois) :

```
taux = nb_conversions / nb_demandes
```

- Le taux est calculé par (année, mois, canal) : pour chaque groupe, on rapporte les conversions du groupe aux demandes du même groupe.
- Si aucune demande dans le groupe, le taux est `None` (pas de division par zéro) — la ligne n'apparaît pas ou affiche « — ».
- Le taux est borné entre 0 et 1 (ou affiché en pourcentage entre 0 % et 100 %).

## Hors périmètre

- Pas de suivi de cohorte (une conversion peut venir d'une demande du mois précédent).
- Pas de calcul de valeur moyenne du contrat (CA) — un indicateur séparé.
- Pas de modification du schéma SQLite.
- Pas de connecteur GA4 (les « conversions » GA sont un indicateur séparé, étape 6).

## Hypothèses enregistrées

- Une personne peut passer de « prospect » à « client » et inversement ; seule la **première** transition prospect → client compte comme conversion.
- Le canal d'acquisition est celui du premier contact de la personne, pas celui de l'événement de conversion.
- Le taux de conversion se calcule sur les demandes **du même canal** que la conversion, pas sur l'ensemble des demandes.
- Si une personne n'a jamais eu le statut « prospect » explicite mais passe directement « client », elle compte comme conversion (arrivée directe en client).
