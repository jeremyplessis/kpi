# Proposal: Amélioration du lanceur macOS (KPI.command)

## Why

L'utilisatrice lance l'application en double-cliquant sur le fichier `KPI.command` à la racine du projet (script bash ouvert dans Terminal). Aujourd'hui, ce script se contente de créer l'environnement virtuel s'il manque, puis de lancer `.venv/bin/kpi`. Or le projet évolue sur GitHub (PR mergées, commits poussés depuis un autre poste) : si le dépôt distant a bougé, le lanceur démarre quand même avec l'ancien code, sans que l'utilisatrice le sache. De même, si `pyproject.toml` a changé (nouvelle dépendance), le venv local n'est pas mis à jour.

Cécile n'est pas développeuse : elle ne doit pas avoir à penser à faire `git pull` et `pip install` avant de double-cliquer. Le lanceur macOS doit se mettre à jour tout seul, de façon sûre et silencieuse.

**Périmètre** : seul le fichier `KPI.command` est modifié. La commande Python `kpi` (`src/kpi/app.py`) reste inchangée.

## What Changes

- `KPI.command` : ajout d'un bloc de mise à jour automatique, exécuté avant le lancement de l'application, désactivable via la variable d'environnement `KPI_SANS_MISE_A_JOUR=1`
- **Mise à jour du code** : si le dossier est un dépôt git avec un remote, `git fetch` puis, si la branche courante est en retard sur sa branche amont (`@{upstream}`, ou `origin/<branche-courante>` à défaut), `git pull --ff-only`. Si le pull a fait avancer le code, le script se ré-exécute (`exec bash "$0"`, avec garde-fou) pour relire un éventuel `KPI.command` mis à jour et poursuivre avec le nouveau code
- **Mise à jour des dépendances** : comparaison du hash SHA-256 de `pyproject.toml` avec un stamp `.venv/kpi-pyproject.sha256` ; si différent (ou absent), `.venv/bin/pip install -e . --quiet` puis réécriture du stamp
- La création du venv si absent est conservée telle quelle (bootstrap, pas une mise à jour)
- Toute erreur (hors ligne, arbre sale, pas de remote, pas un dépôt git, échec pip) affiche un avertissement mais ne bloque jamais le lancement
- `documentation/03_ecran_saisie.md` : le bloc de code copiable de `KPI.command` est mis à jour pour refléter le nouveau script

## Capabilities

### New Capabilities
- `lanceur/mise-a-jour-automatique`: Mise à jour automatique du code (git pull) et des dépendances (pip install) au lancement via `KPI.command`

### Modified Capabilities
- Aucune côté Python : `src/kpi/app.py` et la commande `kpi` ne sont pas modifiés

## Impact

- `KPI.command` : blocs git (fetch/pull `--ff-only`, ré-exécution guardée) et dépendances (stamp de hash, `pip install -e .`) ajoutés avant le lancement de `.venv/bin/kpi`
- `tests/test_lanceur.py` : nouveau fichier de tests (dépôt git temporaire avec remote local, faux `.venv/bin/pip` et `.venv/bin/kpi` qui journalisent leurs appels, exécution du script via `subprocess`)
- `documentation/03_ecran_saisie.md` : bloc copiable de `KPI.command` mis à jour
- Aucun changement de code Python, de schéma de base de données, ni de routes web

## Hypothèses enregistrées

- `git pull --ff-only` uniquement : jamais de merge automatique, jamais d'écrasement des modifications locales (échec propre si l'arbre est sale)
- En cas d'échec de la mise à jour (réseau, conflit, etc.), le script avertit et lance quand même l'application avec le code actuel
- Le stamp `.venv/kpi-pyproject.sha256` vit dans le venv : jamais commité (`.venv/` est ignoré par git)
- macOS n'a pas la commande `timeout` : les appels réseau git sont bornés via les options `http.lowSpeedLimit`/`http.lowSpeedTime` de git
- Le hash est calculé avec `shasum -a 256` (présent par défaut sur macOS), avec repli sur `sha256sum`
- Seule échappatoire : la variable d'environnement `KPI_SANS_MISE_A_JOUR=1` (pas de flag Python, la commande `kpi` n'étant pas modifiée)
