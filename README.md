# kpi

Outil de saisie d'activité et de restitution des KPI, destiné aux
entrepreneurs individuels (en cours de développement : voir
`documentation/01_proposition_architecture.md`).

## État du projet

| Étape | Contenu | État |
|---|---|---|
| 1 | Base SQLite, référentiels, import du classeur | Terminé |
| 2 | Moteur de calcul des indicateurs existants | Terminé |
| 3 | Écran de saisie du suivi | Terminé |
| 4 | Écrans de consultation KPI + export PDF | À venir |
| 5 | Connecteur Google Analytics 4 | À venir |

## Mise en route

Python 3.14 ou plus récent est requis.

```bash
# 1. préparer l'environnement (une seule fois)
python3 -m venv .venv
.venv/bin/pip install -e .

# 2. importer les données du classeur d'origine
.venv/bin/python -m outils.import_initial chemin/vers/KPI.xlsx [chemin/base.sqlite3]

# 3. lancer les tests automatisés
.venv/bin/pip install -e ".[dev]"   # une seule fois : ajoute httpx, requis par les tests web
.venv/bin/python -m unittest discover -s tests

# 4. lancer l'application (le navigateur s'ouvre sur l'écran de saisie)
.venv/bin/kpi
```

Sous Linux, `source .venv/bin/activate` permet ensuite d'utiliser `python`
directement au lieu de `.venv/bin/python`.

## Documentation

La documentation utilisateur est rédigée au fil du développement, dans le
dossier `documentation/` :

- `00_analyse_kpi_xlsx.md` : analyse du classeur d'origine et valeurs
  témoins ;
- `01_proposition_architecture.md` : architecture de l'application et
  décisions actées ;
- `02_import_initial.md` : guide de l'import du classeur et des tests ;
- `03_ecran_saisie.md` : guide de l'écran de saisie du suivi.

## Conventions de code

- Python 3.14, programmation orientée objet, PEP 8 ;
- les variables locales sont préfixées par `_` ;
- chaque classe et méthode est documentée (docstrings) ;
- tests automatisés (unittest) ajoutés au fil du développement.
