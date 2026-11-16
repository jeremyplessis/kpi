# Spec Delta: Connecteur GA4

## ADDED Requirements

### Requirement: Page de gestion GA4

Une page `/ga4` permet de lancer une récupération manuelle et de voir l'état des relevés.

#### Scenario: Affichage de la page GA4

- **WHEN** l'utilisatrice ouvre `/ga4`
- **THEN** la page affiche un formulaire de sélection de période (année/mois début et fin)
- **AND** un bouton "Récupérer les données GA4"
- **AND** la date du dernier relevé enregistré en base (si disponible)

#### Scenario: Lien dans la navigation

- **WHEN** n'importe quelle page de l'application est affichée
- **THEN** la barre de navigation contient un lien "GA4" vers `/ga4`

### Requirement: Récupération manuelle des données GA4

Un POST sur `/ga4/recuperer` avec une période déclenche l'appel à l'API GA4 et l'enregistrement en base.

#### Scenario: Récupération réussie

- **WHEN** le compte de service est configuré et la propriété GA4 accessible
- **AND** l'utilisatrice soumet une période valide
- **THEN** les visiteurs mensuels sont enregistrés dans `ga_visiteurs` avec `origine="api"`
- **AND** les canaux sont enregistrés dans `ga_canaux`
- **AND** les requêtes de recherche sont enregistrées dans `ga_requetes` (si l'API les expose)
- **AND** la page affiche un message de confirmation avec le nombre de mois récupérés

#### Scenario: Idempotence

- **WHEN** une récupération est relancée sur une période déjà relevée
- **THEN** les valeurs existantes sont remplacées, pas dupliquées
- **AND** le nombre de lignes en base reste identique

#### Scenario: Clé de compte de service manquante

- **WHEN** le fichier de clé JSON est absent ou le chemin invalide
- **THEN** la récupération échoue avec un message clair indiquant comment configurer le compte de service
- **AND** aucune donnée n'est modifiée en base

#### Scenario: Property ID invalide ou inaccessible

- **WHEN** le property ID ne correspond à aucune propriété accessible au compte de service
- **THEN** l'API retourne une erreur, affichée clairement à l'utilisatrice
- **AND** aucune donnée n'est modifiée en base

### Requirement: Module client GA4

Un module `src/kpi/ga4.py` encapsule toute la logique d'appel à l'API GA4.

#### Scenario: Isolation de l'API

- **WHEN** le code web a besoin de données GA4
- **THEN** il passe par le module `kpi.ga4`, jamais directement par `google-analytics-data`
- **AND** le module expose une interface simple : `recuperer_periode(property_id, credentials_path, annee_debut, mois_debut, annee_fin, mois_fin) -> dict`

### Requirement: Sécurité du fichier de clé

Le fichier de clé JSON du compte de service n'est jamais versionné.

#### Scenario: Fichier exclu du git

- **WHEN** le projet est cloné sur une nouvelle machine
- **THEN** le fichier de clé n'est pas présent (dans `.gitignore`)
- **AND** la documentation explique comment le re-télécharger
