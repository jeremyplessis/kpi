# Design: Connecteur GA4

## Context

Cécile a un accès administrateur à la propriété GA4 de son site. Les tables GA et le repository existent déjà avec des méthodes idempotentes (`ON CONFLICT DO UPDATE`). L'import manuel du classeur a déjà alimenté ces tables pour les données historiques. Le connecteur vient compléter, pas remplacer.

## Goals / Non-Goals

**Goals:**
- Récupération manuelle (sur clic) des données GA4 pour une période donnée
- Enregistrement dans les tables existantes (idempotent)
- Affichage de la date du dernier relevé
- Procédure documentée pour créer le compte de service

**Non-Goals:**
- Récupération automatique périodique (cron) — v2
- Graphiques GA4 dans l'écran KPI (ce sera l'étape 6)
- Gestion multi-propriétés GA4

## Decisions

### Decision 1: Compte de service Google (fichier JSON)

L'authentification se fait via un compte de service Google Cloud, dont la clé privée est un fichier JSON téléchargé depuis Google Cloud Console. Ce fichier est stocké localement (chemin configurable, par défaut `ga4-credentials.json` à la racine du projet, exclu du git).

Procédure documentée :
1. Google Cloud Console → créer un projet (ou utiliser existant)
2. Activer l'API Google Analytics Data API
3. Créer un compte de service → télécharger la clé JSON
4. Dans GA4 Admin → accès à la propriété → ajouter le compte de service comme "Lecteur"
5. Noter le Property ID (numérique, ex: `123456789`)

### Decision 2: Property ID et chemin de clé en configuration

Lecture depuis des variables d'environnement ou un fichier de config local :
- `KPI_GA4_PROPERTY_ID` (env) ou champ dans la page `/ga4`
- `KPI_GA4_CREDENTIALS` (env) ou `ga4-credentials.json` par défaut

### Decision 3: Requêtes mensuelles par blocs

L'API GA4 est interrogée mois par mois (12 requêtes max par an) pour visiteurs totaux, canaux, et requêtes de recherche. Chaque mois est enregistré via `GoogleAnalyticsRepository` avec `origine="api"`.

Dimensions GA4 utilisées :
- Visiteurs : `date` (YYYYMMDD) + métrique `totalUsers`
- Canaux : `sessionDefaultChannelGroup` + `totalUsers`
- Requêtes : `searchTerm` (si disponible dans l'API) + `totalUsers` — à vérifier car l'API GA4 peut différer du relevé manuel

### Decision 4: Page web dédiée `/ga4`

- Formulaire : période (année + mois début/fin), bouton "Récupérer"
- Affichage : dernier relevé (date + origine), nombre de mois enregistrés
- Messages d'erreur clairs si clé manquante ou API inaccessible

### Decision 5: Pas de modification du schéma

Les tables `ga_visiteurs`, `ga_canaux`, `ga_requetes` sont réutilisées telles quelles. Le champ `origine` distingue `manuel` vs `api`.

## Data Flow

```
POST /ga4/recuperer (form: annee_debut, mois_debut, annee_fin, mois_fin)
  → lit property_id et credentials path
  → client GA4 : pour chaque mois de la période :
      - requête totalUsers → enregistrer_visiteurs(annee, mois, total, origine="api")
      - requête par channelGroup → enregistrer_canal(...)
      - requête par searchTerm → enregistrer_requete(...)
  → base.valider()
  → redirection /ga4?message=... (succès ou erreur)
```
