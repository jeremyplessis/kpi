# Proposal: Connecteur Google Analytics 4

## Why

Les relevés Google Analytics sont aujourd'hui saisis manuellement dans le classeur Excel puis importés. Un connecteur automatique vers l'API GA4 permettra de récupérer les visiteurs mensuels, la répartition par canal et les requêtes de recherche directement depuis GA4, sans saisie manuelle. Les tables `ga_visiteurs`, `ga_canaux`, `ga_requetes` et le `GoogleAnalyticsRepository` existent déjà : il ne reste qu'à brancher l'API.

## What Changes

- Ajout de la dépendance `google-analytics-data` dans `pyproject.toml`
- Nouveau module `src/kpi/ga4.py` : client GA4 encapsulant l'appel API (compte de service, property ID, récupération mensuelle)
- Nouvelle page web `/ga4` : bouton "Récupérer les données GA4", affichage de la date du dernier relevé, sélection de la période à récupérer
- Route POST `/ga4/recuperer` qui appelle le connecteur et enregistre dans les tables GA existantes (idempotent)
- Documentation de la procédure de création du compte de service Google (Cloud Console, clé JSON, accès GA4)
- Gestion des erreurs : clé manquante, property invalide, quota dépassé → message clair à l'utilisatrice

## Capabilities

### New Capabilities
- `connecteur-ga4/client-api`: Client Python pour l'API GA4 (authentification compte de service, requêtes mensuelles)
- `connecteur-ga4/ecran-ga4`: Page web de lancement manuel et suivi des relevés

### Modified Capabilities
- `bdd/google-analytics`: Le `GoogleAnalyticsRepository` est réutilisé tel quel (méthodes `enregistrer_*` déjà idempotentes), aucune modification nécessaire

## Impact

- `pyproject.toml` : ajouter `google-analytics-data>=0.18`
- `src/kpi/ga4.py` : nouveau module (client GA4)
- `src/kpi/web/routes.py` : routes `GET /ga4` et `POST /ga4/recuperer`
- `src/kpi/web/gabarits/ga4.html` : nouveau template
- `src/kpi/web/gabarits/base.html` : ajouter le lien "GA4" dans la navigation
- `tests/test_ga4.py` : tests du client (mock de l'API) et de la route web
- `documentation/05_connecteur_ga4.md` : procédure compte de service + guide d'utilisation
- `.gitignore` : ajouter le fichier de clé JSON (`*.json` de compte de service, ou nom explicite)
