# Lanceur macOS Specification

## Purpose

Le lanceur `KPI.command` met automatiquement à jour le code (git pull) et les dépendances (pip install) avant de démarrer l'application, tout en restant un lanceur macOS classique (double-clic Finder, fenêtre Terminal).

## Requirements

### Requirement: Mise à jour du code depuis le dépôt distant

Au lancement de `KPI.command`, si le dossier du projet est un dépôt git ayant un remote `origin`, le script vérifie si la branche courante est en retard et exécute `git pull --ff-only` avant de lancer l'application, puis se ré-exécute une fois.

#### Scenario: La branche courante est en retard

- **WHEN** `git fetch origin` indique que la branche amont contient des commits absents de `HEAD`
- **THEN** `git pull --ff-only` est exécuté, le script se ré-exécute, et l'application démarre avec le nouveau code

#### Scenario: Le code local est à jour

- **THEN** aucun `git pull` ni ré-exécution n'a lieu, l'application démarre directement

#### Scenario: Pas d'upstream configuré

- **THEN** le script utilise `origin/<branche-courante>` ; si inexistante, la vérification est ignorée sans erreur

#### Scenario: Hors ligne ou remote injoignable

- **THEN** un avertissement est affiché et le script poursuit avec le code local

#### Scenario: Arbre de travail sale

- **THEN** un avertissement est affiché et le script poursuit sans ré-exécution

#### Scenario: Dossier hors dépôt git

- **THEN** la vérification git est ignorée silencieusement

### Requirement: Mise à jour des dépendances de l'environnement virtuel

Si le hash SHA-256 de `pyproject.toml` diffère du stamp `.venv/kpi-pyproject.sha256`, le script exécute `.venv/bin/pip install -e . --quiet` puis réécrit le stamp.

#### Scenario: pyproject.toml a changé

- **THEN** `pip install -e .` est exécuté, le stamp réécrit, l'application démarre après

#### Scenario: Dépendances déjà à jour

- **THEN** aucune commande pip n'est exécutée

#### Scenario: Environnement virtuel absent

- **THEN** le venv est créé, les dépendances installées, le stamp écrit

#### Scenario: Échec de l'installation pip

- **THEN** un avertissement est affiché et le script poursuit

### Requirement: Ordre des opérations

Mise à jour git → mise à jour dépendances → lancement de l'application.

### Requirement: Échappatoire à la mise à jour automatique

La variable d'environnement `KPI_SANS_MISE_A_JOUR=1` désactive git pull et pip install ; la création du venv a toujours lieu.

### Requirement: Protection contre les boucles de ré-exécution

Un garde-fou (`_KPI_MAJ_REEXEC`) bloque toute ré-exécution récursive au-delà d'une seule fois.

### Requirement: Comportement de lancement inchangé

Double-clic Finder, `cd` dans le dossier du projet, lancement de `.venv/bin/kpi`, fenêtre Terminal maintenue ouverte. La commande `kpi` (code Python) n'est pas modifiée.
