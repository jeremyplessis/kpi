# Contexte du projet KPI

## Qu'est-ce que KPI ?

Outil de saisie d'activité et de restitution des indicateurs clés (KPI) destiné aux entrepreneurs individuels, développé pour Cécile Plessis Photographe.

## Stack technique

| Composant | Technologie |
|---|---|
| Langage | Python 3.13+ |
| Base de données | SQLite (fichier unique `kpi.sqlite3`) |
| Framework web | FastAPI + Uvicorn (serveur local 127.0.0.1) |
| Templates | Jinja2 |
| CSS/JS | HTMX + Chart.js |
| PDF | WeasyPrint (à venir) |
| GA4 | google-analytics-data (à venir) |
| Tests | unittest |

## Architecture

```
src/kpi/
├── app.py              # Point d'entrée CLI
├── bdd/
│   ├── connexion.py    # Connexion SQLite, schéma
│   └── modeles.py      # Repository pattern (Referentiel, Personne, Suivi, GA)
├── suivi.py            # Modèle EvenementSuivi
├── kpi/
│   └── indicateurs.py  # Moteur de calcul (4 indicateurs + registre)
└── web/
    ├── routes.py       # Routes FastAPI
    └── gabarits/       # Templates Jinja2
```

## État actuel (novembre 2026)

| Étape | Contenu | État |
|---|---|---|
| 1 | Base SQLite, référentiels, import classeur | ✅ Terminé |
| 2 | Moteur de calcul des indicateurs | ✅ Terminé |
| 3 | Écran de saisie du suivi | ✅ Terminé |
| 4 | Écrans de consultation KPI + export PDF | 🟡 Partiel (écran fait, PDF manquant) |
| 5 | Connecteur Google Analytics 4 | ❌ À venir |
| 6 | Indicateurs GA (visiteurs, conversions) | ❌ À venir |

## Conventions

- Python 3.13+, PEP 8 strict, type hints obligatoires
- Variables locales préfixées par `_`
- Repository pattern obligatoire (pas de SQL direct hors `modeles.py`)
- Chaque requête web ouvre sa propre connexion SQLite
- Vérification `Origin` header pour toutes les écritures POST
- Tests unittest avec données synthétiques anonymes
- Conventional Commits pour les messages git
- Ne jamais commiter `*.sqlite3`, `KPI.xlsx`, `.venv/`

## Règles métier validées

- **Demande** : action_public ∈ {"Demande", "Réservation"}
- **Réponse** : action_public ∉ {"-", "Demande", "Réservation", "Relance"}
- **Taux de ghosting** : (demandes - réponses) / demandes, borné à 0
- **Dédoublonnage** : une personne = une demande par mois max
