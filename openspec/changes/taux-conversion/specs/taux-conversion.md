# Spec Delta: Indicateurs de conversion (nombre et taux)

## ADDED Requirements

### Requirement: Indicateur « Nombre de conversions »

L'application calcule le nombre de prospects convertis en clients, regroupés par année, mois et canal d'acquisition, avec dépliement hiérarchique (année → mois → canal).

#### Scenario: Conversion simple prospect → client

- **WHEN** une personne a un événement avec `statut_contact = "prospect"` puis un événement ultérieur avec `statut_contact = "client"`
- **THEN** cette personne compte pour 1 conversion
- **AND** la conversion est attribuée à l'année et au mois du premier événement « client »
- **AND** le canal attribué est celui du premier événement de la personne (canal d'acquisition)

#### Scenario: Arrivée directe en client

- **WHEN** une personne a un premier événement avec `statut_contact = "client"` sans jamais avoir été « prospect »
- **THEN** cette personne compte pour 1 conversion
- **AND** le canal attribué est celui de ce premier événement

#### Scenario: Une personne = une seule conversion

- **WHEN** une personne passe prospect → client plusieurs fois (changement de statut répété)
- **THEN** seule la première transition prospect → client est comptée
- **AND** les transitions ultérieures sont ignorées

#### Scenario: Personne jamais convertie

- **WHEN** une personne reste « prospect » dans tous ses événements
- **THEN** elle n'apparaît dans aucune ligne de l'indicateur

#### Scenario: Agrégation par année, mois, canal

- **WHEN** plusieurs conversions ont lieu le même mois via le même canal d'acquisition
- **THEN** elles sont agrégées en une seule ligne avec la somme

### Requirement: Indicateur « Taux de conversion »

L'application calcule le taux de conversion : pourcentage de conversions par rapport au nombre total de demandes, avec détail par année, mois et canal d'acquisition.

#### Scenario: Calcul du taux par groupe

- **WHEN** un groupe (année, mois, canal) contient 3 demandes et 1 conversion
- **THEN** le taux affiché pour ce groupe est 1/3 ≈ 33,3 %

#### Scenario: Aucune demande dans le groupe

- **WHEN** un groupe (année, mois, canal) contient des conversions mais aucune demande (cas anormal)
- **THEN** aucune ligne de taux n'est produite pour ce groupe (pas de division par zéro)

#### Scenario: Aucune conversion dans le groupe

- **WHEN** un groupe (année, mois, canal) contient des demandes mais 0 conversion
- **THEN** le taux affiché pour ce groupe est 0 %

#### Scenario: Taux borné entre 0 et 100 %

- **WHEN** le taux est calculé
- **THEN** il est toujours compris entre 0 et 1 (0 % et 100 %)

### Requirement: Intégration dans le registre et l'interface

Les deux nouveaux indicateurs sont enregistrés dans `REGISTRE_INDICATEURS` et apparaissent dans la liste déroulante de la page `/kpi`, dans les cartes du tableau de bord, et dans la page de détail avec tableau et graphique.

#### Scenario: Tableau de bord

- **WHEN** l'utilisatrice ouvre `/kpi` sans sélectionner d'indicateur
- **THEN** 6 cartes de synthèse sont affichées (les 4 existantes + NbConversions + TauxConversion)
- **AND** la carte « Taux de conversion » affiche le ratio global (somme conversions / somme demandes) en pourcentage
- **AND** la carte « Nombre de conversions » affiche la somme des conversions

#### Scenario: Page de détail d'un indicateur de conversion

- **WHEN** l'utilisatrice sélectionne « Nombre de conversions » ou « Taux de conversion » dans `/kpi`
- **THEN** le tableau dépliable affiche les données par année → mois → canal
- **AND** le graphique Chart.js affiche l'évolution
