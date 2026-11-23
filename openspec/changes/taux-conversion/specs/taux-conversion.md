# Spec Delta: Indicateurs de conversion (nombre et taux)

## ADDED Requirements

### Requirement: Indicateur « Nombre de conversions »

L'application calcule le nombre de demandes converties en séances sur la période filtrée de l'écran KPI, avec une ligne « Tous » (total) et un dépliement par statut du demandeur (client / prospect).

Une **conversion en séance** est une personne ayant au moins une demande (`action_public ∈ {"Demande", "Réservation"}`) ET au moins un événement avec `action_photographe = "Confirmation"`, tous deux dans la période filtrée.

#### Scenario: Demande + Confirmation = conversion

- **WHEN** une personne a un événement avec `action_public = "Demande"` et un autre événement avec `action_photographe = "Confirmation"` dans la période
- **THEN** cette personne compte pour 1 conversion
- **AND** le statut retenu est celui de son premier événement de demande dans la période

#### Scenario: Demande sans Confirmation

- **WHEN** une personne a une demande mais aucun événement avec `action_photographe = "Confirmation"` dans la période
- **THEN** elle n'est pas comptée comme conversion
- **AND** elle compte quand même dans les demandes (dénominateur du taux)

#### Scenario: Confirmation sans demande

- **WHEN** une personne a un événement avec `action_photographe = "Confirmation"` mais aucune demande dans la période
- **THEN** elle n'est pas comptée comme conversion
- **AND** elle n'apparaît pas dans les demandeurs

#### Scenario: Plusieurs demandes, une seule conversion

- **WHEN** une personne a 3 demandes sur 3 mois différents et 1 Confirmation dans la période
- **THEN** elle compte pour 1 conversion (pas 3)
- **AND** elle compte pour 1 demandeur (pas 3)

#### Scenario: Dépliement par statut

- **WHEN** l'utilisatrice déplie la ligne « Tous » de l'indicateur NbConversions
- **THEN** deux sous-lignes apparaissent : « client » et « prospect » avec le nombre de conversions pour chaque statut

### Requirement: Indicateur « Taux de conversion »

L'application calcule le taux de conversion global sur la période filtrée : pourcentage de demandeurs ayant abouti à une séance. En dépliant, deux composantes sont affichées : clients et prospects.

```
taux_global    = nb_convertis / nb_demandeurs × 100
taux_clients   = nb_convertis_clients / nb_demandeurs_clients × 100
taux_prospects = nb_convertis_prospects / nb_demandeurs_prospects × 100
```

#### Scenario: Calcul du taux global

- **WHEN** sur la période filtrée, 10 personnes ont fait une demande et 4 ont une Confirmation
- **THEN** le taux global affiché est 40,0 %

#### Scenario: Décomposition clients / prospects

- **WHEN** parmi les 10 demandeurs, 6 sont « client » (dont 3 convertis) et 4 sont « prospect » (dont 1 converti)
- **THEN** la composante clients affiche 50,0 % (3/6)
- **AND** la composante prospects affiche 25,0 % (1/4)

#### Scenario: Aucune demande sur la période

- **WHEN** aucune personne n'a fait de demande dans la période filtrée
- **THEN** le taux global affiche « — » (pas de division par zéro)
- **AND** les composantes clients et prospects affichent aussi « — »

#### Scenario: Composante sans demande

- **WHEN** aucun prospect n'a fait de demande dans la période, mais des clients oui
- **THEN** la composante prospects affiche « — »
- **AND** la composante clients affiche le taux calculé normalement

#### Scenario: Taux borné entre 0 et 100 %

- **WHEN** le taux est calculé
- **THEN** il est toujours compris entre 0 et 100 (inclus)

#### Scenario: Le statut est celui du premier événement de demande

- **WHEN** une personne a un premier événement de demande avec `statut_contact = "prospect"` puis un deuxième avec `statut_contact = "client"` dans la même période
- **THEN** le statut retenu pour cette personne est « prospect » (premier événement de demande)

### Requirement: Intégration dans le registre et l'interface

Les deux nouveaux indicateurs sont enregistrés dans `REGISTRE_INDICATEURS` et apparaissent dans la liste déroulante de la page `/kpi`, dans les cartes du tableau de bord, et dans la page de détail avec tableau dépliable et graphique.

#### Scenario: Tableau de bord

- **WHEN** l'utilisatrice ouvre `/kpi` sans sélectionner d'indicateur
- **THEN** 6 cartes de synthèse sont affichées (les 4 existantes + NbConversions + TauxConversion)
- **AND** la carte « Taux de conversion » affiche le taux global en pourcentage (ligne « Tous »)
- **AND** la carte « Nombre de conversions » affiche le total des conversions (ligne « Tous »)

#### Scenario: Page de détail du taux de conversion

- **WHEN** l'utilisatrice sélectionne « Taux de conversion » dans `/kpi`
- **THEN** le tableau affiche la ligne « Tous » avec le pourcentage global
- **AND** en cliquant sur « Tous », deux sous-lignes se déplient : « client » et « prospect » avec leurs pourcentages respectifs
- **AND** le graphique Chart.js affiche 3 barres (Tous, Clients, Prospects)

#### Scenario: Page de détail du nombre de conversions

- **WHEN** l'utilisatrice sélectionne « Nombre de conversions » dans `/kpi`
- **THEN** le tableau affiche la ligne « Tous » avec le nombre total de conversions
- **AND** en dépliant, les sous-lignes « client » et « prospect » affichent les effectifs
