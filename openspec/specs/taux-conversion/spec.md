# Taux de conversion Specification

## Purpose

Deux indicateurs mesurent la conversion des demandes en séances (prestation réalisée) sur la période filtrée de l'écran KPI : le nombre de conversions et le taux de conversion, avec une hiérarchie dépliable Tous → statut → canal.

## Requirements

### Requirement: Indicateur « Nombre de conversions »

L'application compte les événements `action_photographe = "Confirmation"` dans la période filtrée de l'écran KPI, avec une hiérarchie dépliable : **Tous → canal → statut → canal**.

#### Scenario: Hiérarchie Tous → canal → statut → canal

- **WHEN** l'utilisatrice affiche l'indicateur « Nombre de conversions »
- **THEN** la ligne « Tous » affiche le total des Confirmations
- **AND** en dépliant « Tous », les canaux cumulés (tous statuts confondus) apparaissent : mail, téléphone, etc.
- **AND** sous chaque canal, les lignes « client » et « prospect » apparaissent
- **AND** en dépliant un statut, son détail par canal apparaît

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

L'application calcule le taux de conversion sur la période filtrée : pourcentage de demandes ouvertes converties en séances. La hiérarchie dépliable est : **Tous → canal → statut → canal**. Les canaux dont le taux vaut 0 % ne sont pas affichés.

```
taux_global           = nb_confirmations_dans_P / nb_demandeurs_ouverts × 100
taux_statut_S_canal_C = confirmations_{S,C} / demandeurs_{S,C} × 100
```

#### Scenario: Demande dans la période, toujours comptée

- **WHEN** une personne a une demande dans la période P (même avec une Confirmation dans P)
- **THEN** elle est comptée dans les demandeurs ouverts

#### Scenario: Demande antérieure sans Confirmation avant fin de période

- **WHEN** une personne a une demande avant P et aucune Confirmation à une date ≤ fin de P
- **THEN** elle est comptée dans les demandeurs ouverts

#### Scenario: Demande antérieure avec Confirmation avant fin de période

- **WHEN** une personne a une demande avant P et une Confirmation à une date ≤ fin de P (même hors de P)
- **THEN** elle n'est PAS comptée dans les demandeurs ouverts (sa demande est fermée)
- **AND** si la Confirmation est dans P, elle est comptée dans les conversions

#### Scenario: Calcul du taux par canal

- **WHEN** sur la période P, un canal C a 2 demandeurs ouverts et 1 Confirmation
- **THEN** le taux affiché pour ce canal est 50,0 %

#### Scenario: Canaux à 0 % masqués

- **WHEN** un canal a un taux de 0 % (0 Confirmation ou 0 demandeur)
- **THEN** il n'apparaît pas dans le dépliement

#### Scenario: Aucune demande ouverte

- **WHEN** aucune personne n'a de demande ouverte sur la période
- **THEN** aucune ligne n'est produite

#### Scenario: Statut vide = prospect

- **WHEN** une personne a une Demande avec `statut_contact = None` (vide)
- **THEN** son statut est « prospect »
- **AND** elle apparaît dans la composante « prospect » du dépliement

#### Scenario: Taux borné entre 0 et 100 %

- **WHEN** le taux est calculé
- **THEN** il est toujours entre 0 et 100 (inclus)

### Requirement: Intégration dans le registre et l'interface

Les deux indicateurs apparaissent dans la liste de `/kpi`, dans les cartes du tableau de bord, et dans la page de détail avec tableau dépliable et graphique.

#### Scenario: Tableau de bord

- **WHEN** l'utilisatrice ouvre `/kpi` sans indicateur sélectionné
- **THEN** 6 cartes sont affichées (4 existantes + NbConversions + TauxConversion)
- **AND** la carte « Taux de conversion » affiche le taux global en %
- **AND** la carte « Nombre de conversions » affiche le total des Confirmations dans la période

#### Scenario: Page de détail du taux de conversion

- **WHEN** l'utilisatrice sélectionne « Taux de conversion » dans `/kpi`
- **THEN** le tableau dépliable affiche les canaux sous « Tous », puis le détail par statut → canal
- **AND** le graphique Chart.js affiche les taux par canal
