# Guide : l'écran de consultation des KPI

Ce document décrit l'écran web de consultation des indicateurs clés
(« KPI »), accessible depuis le lien **KPI** dans la barre de navigation.

## Le tableau de bord

Quand aucun indicateur n'est sélectionné, la page `/kpi` affiche un
**tableau de bord** synthétique : une carte par indicateur, avec :

- le **libellé** de l'indicateur ;
- la **valeur agrégée** sur la période filtrée (total pour les
  comptages, moyenne pour le taux de ghosting affiché en pourcentage) ;
- un **sparkline** (mini-graphique de tendance mensuelle) quand la
  période couvre au moins deux mois.

Chaque carte est **cliquable** : elle renvoie vers le détail de
l'indicateur concerné, en conservant les filtres de période actifs.

| Carte | Valeur affichée |
|---|---|
| Nombre de prospects | Total de prospects sur la période |
| Nombre de demandes | Total de demandes (dédoublonnées) sur la période |
| Taux de ghosting | Moyenne des taux mensuels, en % |
| RDV par canal | Total de RDV sur la période |

## Filtrer par période

Le formulaire en haut de la page permet de restreindre l'affichage à
une période :

- **Du** : année et mois de début (vide = depuis le début) ;
- **au** : année et mois de fin (vide = jusqu'à aujourd'hui).

Le bouton **Appliquer les filtres** recharge la page avec la période
choisie. Le lien **Effacer les filtres** revient à la période complète.

Les filtres s'appliquent à la fois au tableau de bord et aux pages
détaillées des indicateurs.

## Consulter le détail d'un indicateur

Sélectionnez un indicateur dans la liste déroulante puis cliquez sur
**Appliquer les filtres** (ou cliquez directement sur une carte du
tableau de bord). La page affiche alors :

- le **tableau des données** (regroupées selon les dimensions de
  l'indicateur, avec dépliage pour les tableaux multi-niveaux) ;
- un **graphique** Chart.js adapté au nombre de dimensions.

### Taux de ghosting

L'indicateur « Taux de ghosting » dispose d'une page dédiée
(`/kpi/TauxGhosting`) avec le détail mensuel : nombre de demandes,
nombre de réponses et taux pour chaque mois, plus un graphique combiné
(barres demandes/réponses + courbe du taux).

## Navigation

| Lien | Page |
|---|---|
| Saisie | `/` — formulaire de saisie du suivi |
| KPI | `/kpi` — tableau de bord et consultation |
| Listes | `/listes` — gestion des valeurs des listes déroulantes |

## Tests associés

Les tests automatisés (`tests/test_kpi_web.py`) couvrent l'affichage du
tableau de bord (cartes, totaux, filtres de période), la navigation
entre cartes et détail, et la cohérence entre les totaux du tableau de
bord et les tableaux détaillés.
