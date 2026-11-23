# Spec Delta: Indicateurs de conversion (nombre et taux)

## ADDED Requirements

### Requirement: Indicateur « Nombre de conversions »

L'application compte les événements `action_photographe = "Confirmation"` dans la période filtrée de l'écran KPI, avec une ligne « Tous » (total) et un dépliement par statut de la personne (basé sur sa première demande).

#### Scenario: Confirmation dans la période = conversion

- **WHEN** un événement a `action_photographe = "Confirmation"` dans la période
- **THEN** il compte pour 1 conversion
- **AND** aucune vérification de demande préalable n'est faite

#### Scenario: Confirmation hors période ignorée

- **WHEN** un événement a `action_photographe = "Confirmation"` avant ou après la période
- **THEN** il n'est pas compté

#### Scenario: Dépliement par statut

- **WHEN** l'utilisatrice déplie la ligne « Tous »
- **THEN** les sous-lignes par statut (client, prospect) apparaissent avec le nombre de conversions pour chaque statut
- **AND** le statut est celui de la première demande de la personne (chronologiquement)

### Requirement: Indicateur « Taux de conversion »

L'application calcule le taux de conversion global sur la période filtrée : pourcentage de demandes ouvertes converties en séances. En dépliant, deux composantes : clients et prospects.

```
taux_global    = nb_confirmations_dans_P / nb_demandeurs_ouverts × 100
taux_clients   = confirmations_clients / demandeurs_clients × 100
taux_prospects = confirmations_prospects / demandeurs_prospects × 100
```

#### Scenario: Demande dans la période, toujours comptée

- **WHEN** une personne a une demande dans la période P (même avec une Confirmation dans P)
- **THEN** elle est comptée dans les demandeurs ouverts

#### Scenario: Demande antérieure sans Confirmation dans P

- **WHEN** une personne a une demande avant P et aucune Confirmation dans P
- **THEN** elle est comptée dans les demandeurs ouverts

#### Scenario: Demande antérieure AVEC Confirmation avant fin de période

- **WHEN** une personne a une demande avant P et une Confirmation à une date ≤ fin de P (même hors de P)
- **THEN** elle n'est PAS comptée dans les demandeurs ouverts (sa demande est fermée)
- **AND** si la Confirmation est dans P, elle est comptée dans les conversions

#### Scenario: Calcul du taux global

- **WHEN** sur la période P, il y a 10 demandeurs ouverts et 4 Confirmations
- **THEN** le taux global affiché est 40,0 %

#### Scenario: Décomposition clients / prospects

- **WHEN** parmi les demandeurs, 6 sont « client » (dont 3 avec Confirmation) et 4 sont « prospect » (dont 1 avec Confirmation)
- **THEN** la composante clients affiche 50,0 % (3/6)
- **AND** la composante prospects affiche 25,0 % (1/4)

#### Scenario: Aucune demande ouverte

- **WHEN** aucune personne n'a de demande ouverte sur la période
- **THEN** le taux global affiche 0,0 % (pas de division par zéro)

#### Scenario: Composante sans demandeur

- **WHEN** aucun prospect n'a de demande ouverte, mais des clients oui
- **THEN** la composante prospects n'apparaît pas ou affiche « — »

#### Scenario: Demande antérieure convertie avant P

- **WHEN** Alice a une demande en janvier et une Confirmation en février, et P = mars
- **THEN** Alice n'est PAS dans les demandeurs ouverts (Confirmation ≤ fin P)
- **AND** sa Confirmation de février n'est PAS comptée dans les conversions de P (hors P)

#### Scenario: Statut vide = prospect

- **WHEN** une personne a une Demande avec `statut_contact = None` (vide)
- **THEN** son statut est « prospect » (pas « (vide) »)
- **AND** elle apparaît dans la composante « prospect » du dépliement

#### Scenario: Taux borné entre 0 et 100 %

- **WHEN** le taux est calculé
- **THEN** il est toujours entre 0 et 100 (inclus)

### Requirement: Intégration dans le registre et l'interface

Les deux indicateurs apparaissent dans la liste de `/kpi`, dans les cartes du tableau de bord, et dans la page de détail avec tableau et graphique.

#### Scenario: Tableau de bord

- **WHEN** l'utilisatrice ouvre `/kpi` sans indicateur sélectionné
- **THEN** 6 cartes sont affichées (4 existantes + NbConversions + TauxConversion)
- **AND** la carte « Taux de conversion » affiche le taux global en %
- **AND** la carte « Nombre de conversions » affiche le total des Confirmations dans la période

#### Scenario: Page de détail du taux de conversion

- **WHEN** l'utilisatrice sélectionne « Taux de conversion » dans `/kpi`
- **THEN** le tableau affiche la ligne « Tous » avec le % global, dépliable en « client » et « prospect »
- **AND** le graphique affiche 3 barres (Tous, Clients, Prospects)
