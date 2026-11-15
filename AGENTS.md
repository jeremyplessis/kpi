# AGENTS.md - Projet KPI

Ce fichier décrit les conventions, l'architecture et les règles spécifiques à respecter lorsque tu travailles sur ce projet.

## Présentation du projet

**KPI** est un outil de saisie d'activité et de restitution des indicateurs clés (KPI) destiné aux entrepreneurs individuels, spécifiquement développé pour Cécile Plessis Photographe.

### État actuel (15 novembre 2026)

| Étape | Contenu | État |
|---|---|---|
| 1 | Base SQLite, référentiels, import du classeur | ✅ Terminé |
| 2 | Moteur de calcul des indicateurs existants | ✅ Terminé |
| 3 | Écran de saisie du suivi | ✅ Terminé |
| 4 | Écrans de consultation KPI + export PDF | ⏳ À venir |
| 5 | Connecteur Google Analytics 4 | ⏳ À venir |

### Feuille de route

- **Étape 4** : Implémenter les écrans de consultation des KPI avec graphiques (Chart.js) et export PDF (WeasyPrint)
- **Étape 5** : Connecteur GA4 pour récupérer automatiquement les données Google Analytics
- **Étape 6** : Indicateurs reportés (visiteurs GA, conversions) et documentation complète

## Architecture technique

### Stack technique

| Composant | Technologie | Rôle |
|---|---|---|
| Langage | Python 3.13+ | Langage principal |
| Base de données | SQLite | Base de données embarquée, fichier unique |
| Framework web | FastAPI | Serveur web local |
| Templates | Jinja2 | Génération HTML |
| CSS/JS | HTMX + Chart.js | Interactivité côté client |
| PDF | WeasyPrint | Génération de PDF à partir de HTML |
| Tests | unittest | Tests automatisés |
| GA4 | google-analytics-data | API Google Analytics 4 (futur) |

### Structure du projet

```
kpi/
├── src/
│   └── kpi/
│       ├── __init__.py          # Module principal, version
│       ├── app.py                # Point d'entrée CLI : démarre le serveur
│       ├── bdd/
│       │   ├── __init__.py
│       │   ├── connexion.py      # Connexion SQLite, création du schéma
│       │   └── modeles.py        # Repository pattern (accès aux données)
│       ├── suivi.py              # Modèle métier EvenementSuivi
│       ├── kpi/
│       │   ├── __init__.py
│       │   └── indicateurs.py    # Moteur de calcul des KPI
│       └── web/
│           ├── __init__.py
│           ├── routes.py         # Toutes les routes FastAPI
│           └── gabarits/         # Templates Jinja2
├── outils/
│   └── import_initial.py        # Import du classeur Excel vers SQLite
├── tests/
│   ├── test_bdd.py              # Tests de la base de données
│   ├── test_calculs_kpi.py      # Tests des indicateurs
│   ├── test_import_excel.py     # Tests de l'import initial
│   └── test_web.py              # Tests de l'application web
├── documentation/
│   ├── 00_analyse_kpi_xlsx.md   # Analyse du classeur Excel
│   ├── 01_proposition_architecture.md  # Architecture validée
│   ├── 02_import_initial.md     # Guide de l'import
│   └── 03_ecran_saisie.md        # Guide de l'écran de saisie
├── pyproject.toml               # Dépendances et configuration
├── README.md                    # Documentation utilisateur
└── kpi.sqlite3                  # Base de données (fichier unique)
```

### Modèle de données

#### Tables de référence (éditables)
- `canal` : formulaire de contact, instagram, mail, téléphone, etc.
- `provenance` : Google, Instagram, Bouche à oreille, etc.
- `statut_contact` : prospect, client
- `prestation` : Mariage, Séances, Carte cadeau, etc.
- `detail_prestation` : Famille, Grossesse, Portrait, etc.
- `action` : Demande, Paiement, RDV, Relance, Refus, Réservation, Réponse, etc.
- `personne` : Personnes suivies (créées automatiquement)

#### Table principale
- `suivi_activite` : Un événement = une ligne du suivi

#### Tables Google Analytics
- `ga_visiteurs` : Visiteurs mensuels
- `ga_canaux` : Visiteurs par canal mensuel
- `ga_requetes` : Requêtes de recherche mensuelles

## Conventions de développement

### Python

- **Version** : Python 3.13 minimum (requis dans pyproject.toml)
- **Style** : PEP 8 strict
- **Typage** : Type hints obligatoires
- **Nommage** :
  - Variables locales préfixées par `_` (ex: `_base`, `_evenement`)
  - Noms de classes en PascalCase
  - Noms de méthodes et fonctions en snake_case
  - Constantes en UPPER_CASE
- **Docstrings** : Obligatoires pour toutes les classes et méthodes publiques
- **Gestion des erreurs** : Exceptions explicites avec messages clairs

### SQL

- **Protection** : Toutes les requêtes SQL sont construites avec des paramètres (pas de string formatting)
- **Tables listées blanche** : Pour les tables de référence, utiliser le tuple `TABLES_REFERENTIELLES` pour valider
- **Transactions** : Toujours valider explicitement avec `base.valider()` ou annuler avec `base.annuler()`

### FastAPI

- **Routes** : Toutes les routes sont définies dans `src/kpi/web/routes.py`
- **Templates** : Utilisation de Jinja2 avec filtres personnalisés
- **Sécurité** : Vérification de l'origine (`Origin` header) pour toutes les écritures
- **Connexion** : Chaque requête ouvre sa propre connexion SQLite (pas de connexion globale)

### Tests

- **Framework** : unittest (bibliothèque standard)
- **Organisation** : Un fichier de test par module fonctionnel
- **Jeu de données** : Données synthétiques et anonymes
- **Valeurs témoins** : Calculées à la main et documentées dans les docstrings

## Règles de développement

### 1. Ne jamais modifier le schéma sans migration

Le schéma est défini dans `src/kpi/bdd/connexion.py` (variable `SCHEMA`).
Toute modification doit être documentée et testée.

### 2. Respecter le pattern Repository

Toutes les requêtes SQL doivent passer par les classes Repository dans `src/kpi/bdd/modeles.py` :
- `ReferentielRepository`
- `PersonneRepository`
- `SuiviRepository`
- `GoogleAnalyticsRepository`

Le reste de l'application ne doit **jamais** exécuter de SQL directement.

### 3. Indicateurs KPI

Les indicateurs sont implémentés comme des classes dans `src/kpi/kpi/indicateurs.py` :
- Chaque indicateur hérite de la classe `Indicateur`
- La méthode `calculer()` retourne une liste de `LigneIndicateur`
- Les règles de calcul sont documentées dans les docstrings
- Les indicateurs sont enregistrés dans `REGISTRE_INDICATEURS`

### 4. Règles métiers validées

- **Demande** : action_public ∈ {"Demande", "Réservation"}
- **Réponse** : action_public ∉ {"-", "Demande", "Réservation", "Relance"}
- **Taux de ghosting** : (demandes - réponses) / demandes, borné à 0
- **Dédoublonnage** : Une personne ne compte qu'une fois par mois pour les demandes

### 5. Sécurité

- L'application n'écoute que sur `127.0.0.1` (pas d'accès externe)
- Vérification systématique de l'en-tête `Origin` pour les requêtes POST
- Pas d'authentification (usage personnel, environnement local)

### 6. Gestion des fichiers

- **Ne pas commiter** :
  - Les bases SQLite (`*.sqlite3`, `*.sqlite3-journal`)
  - Les environnements virtuels (`.venv/`, `venv/`)
  - Les caches Python (`__pycache__/`, `*.pyc`, `*.pyo`)
  - Le classeur source (`KPI.xlsx`) - contient des données réelles
- **Toujours commiter** :
  - Les tests
  - La documentation
  - Les migrations de schéma (si implémentées)

## Commandes utiles

### Développement

```bash
# Installer les dépendances
python3 -m venv .venv
.venv/bin/pip install -e .

# Installer les dépendances de développement
.venv/bin/pip install -e ".[dev]"

# Lancer l'application
.venv/bin/kpi                    # Ouvre le navigateur
.venv/bin/kpi --sans-navigateur  # Sans ouvrir le navigateur
.venv/bin/kpi --base autre.sqlite3 --port 9000

# Lancer les tests
.venv/bin/python -m unittest discover -s tests

# Vérifier le style
.venv/bin/pycodestyle src/ tests/
```

### Import initial

```bash
# Importer le classeur (une seule fois)
.venv/bin/python -m outils.import_initial chemin/vers/KPI.xlsx [chemin/base.sqlite3]

# Réimporter (force la suppression du suivi existant)
.venv/bin/python -m outils.import_initial chemin/vers/KPI.xlsx --force
```

## Conventions de commit

**Utilise Conventional Commits** pour tous les messages de commit.

Format : `<type>([scope]): <description>`

### Types de commits

| Type | Utilisation | Exemple |
|---|---|---|
| `feat` | Nouvelle fonctionnalité | `feat: ajout de l'écran de consultation des KPI` |
| `fix` | Correction de bug | `fix: correction du calcul du taux de ghosting` |
| `docs` | Documentation | `docs: mise à jour du guide d'import initial` |
| `style` | Modifications de style (espaces, formatage) | `style: correction du formatage PEP 8` |
| `refactor` | Refactoring sans changement fonctionnel | `refactor: extraction du Repository pattern` |
| `test` | Ajout ou correction de tests | `test: ajout de tests pour les indicateurs` |
| `chore` | Maintenance, configuration | `chore: mise à jour des dépendances` |
| `perf` | Amélioration de performance | `perf: optimisation des requêtes SQL` |
| `build` | Changements de build (pyproject.toml, etc.) | `build: ajout de la dépendance httpx` |

### Scopes optionnels

- `bdd` : Base de données et repositories
- `kpi` : Moteur de calcul des indicateurs
- `web` : Application web et templates
- `import` : Outil d'import initial
- `tests` : Tests automatisés

### Règles supplémentaires

- **Corps du commit** : Expliquer **pourquoi** le changement, pas **quoi** (le code montre déjà quoi)
- ** Pied de commit** : Référencer les issues ou tickets si applicable
- **Ligne de sujet** : 50-72 caractères maximum
- **Ligne de corps** : 72 caractères maximum par ligne
- **Utiliser l'impératif** : "Ajouter" pas "Ajoute"

### Exemples

```
feat(web): ajouter l'écran de consultation des KPI

Implémente les routes pour afficher les indicateurs avec filtres par
période. Utilise Chart.js pour les graphiques.

Generated by Mistral Vibe.
Co-Authored-By: Mistral Vibe <vibe@mistral.ai>

fix(kpi): corriger le calcul du taux de ghosting

Le taux était calculé avec un dédoublonnage incorrect des réponses.
Maintenant conforme aux règles validées du 28/10/2026.

fixup: correction de typo dans le README
```

## Conventions de Pull Request

### Titre

Même format que les commits : `<type>([scope]): <description>`

### Description

- **Contexte** : Expliquer le problème ou l'objectif
- **Changements** : Résumer les modifications
- **Tests** : Décrire comment les changements ont été testés
- **Documentation** : Mentionner si la documentation a été mise à jour

### Template de PR

```markdown
## Description

[Description des changements]

## Contexte

[Pourquoi ces changements sont nécessaires]

## Changements apportés

- [ ] Nouvelle fonctionnalité
- [ ] Correction de bug
- [ ] Refactoring
- [ ] Documentation
- [ ] Tests

## Tests

- [ ] Tous les tests existants passent
- [ ] Nouveaux tests ajoutés
- [ ] Testé manuellement

## Documentation

- [ ] README.md mis à jour
- [ ] Documentation utilisateur mise à jour
- [ ] Documentation technique mise à jour
```

## Points d'attention

1. **Données réelles** : Ne jamais commiter le fichier `KPI.xlsx` ou les bases SQLite contenant des données réelles
2. **Sécurité** : Toujours vérifier l'origine des requêtes POST
3. **Compatibilité** : Le projet cible Python 3.13+, ne pas utiliser de fonctionnalités de versions ultérieures
4. **Performances** : Les requêtes SQL doivent être optimisées (index, jointures)
5. **Accessibilité** : Les templates HTML doivent être accessibles (balises sémantiques, labels)

## Ressources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
