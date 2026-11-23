# Spec Delta: Lanceur macOS (KPI.command) avec mise à jour automatique

## ADDED Requirements

### Requirement: Mise à jour du code depuis le dépôt distant

Au lancement de `KPI.command`, si le dossier du projet est un dépôt git ayant un remote `origin`, le script vérifie si la branche courante est en retard sur sa branche amont et, le cas échéant, exécute `git pull --ff-only` avant de lancer l'application. Si le pull a mis à jour le code, le script se ré-exécute une fois pour poursuivre avec le nouveau code.

#### Scenario: La branche courante est en retard

- **WHEN** `KPI.command` est exécuté
- **AND** `git fetch origin` indique que la branche amont contient des commits absents de `HEAD`
- **THEN** `git pull --ff-only` est exécuté
- **AND** le script se ré-exécute (`exec bash "$0"`) pour relire le code nouvellement tiré
- **AND** l'application `.venv/bin/kpi` démarre ensuite avec le nouveau code

#### Scenario: Le code local est à jour

- **WHEN** `KPI.command` est exécuté
- **AND** aucun commit n'est en retard sur la branche amont
- **THEN** aucun `git pull` n'est exécuté
- **AND** aucune ré-exécution du script n'a lieu
- **AND** l'application démarre directement

#### Scenario: Pas d'upstream configuré pour la branche

- **WHEN** la branche courante n'a pas d'upstream (`@{upstream}` introuvable)
- **THEN** le script utilise `origin/<nom-de-la-branche-courante>` comme branche amont
- **AND** si cette branche n'existe pas sur le remote, la vérification git est ignorée sans erreur

#### Scenario: Hors ligne ou remote injoignable

- **WHEN** `git fetch origin` échoue ou est interrompu (pas de réseau, transfert bloqué au-delà du délai basse vitesse)
- **THEN** un avertissement est affiché
- **AND** le script poursuit et lance l'application avec le code local actuel

#### Scenario: Arbre de travail sale rendant le pull impossible

- **WHEN** des commits sont en retard
- **AND** `git pull --ff-only` échoue (modifications locales conflictuelles, divergence)
- **THEN** un avertissement est affiché
- **AND** le script poursuit sans ré-exécution et lance l'application avec le code local actuel

#### Scenario: Dossier hors dépôt git

- **WHEN** `KPI.command` est exécuté depuis un dossier sans `.git` (installation copiée hors du clone)
- **THEN** la vérification git est ignorée silencieusement
- **AND** l'application démarre normalement

### Requirement: Mise à jour des dépendances de l'environnement virtuel

Au lancement de `KPI.command`, si le hash SHA-256 de `pyproject.toml` diffère du stamp `.venv/kpi-pyproject.sha256`, le script exécute `.venv/bin/pip install -e . --quiet` puis réécrit le stamp. La création du venv si absent reste inchangée et produit aussi un stamp à jour.

#### Scenario: pyproject.toml a changé depuis la dernière installation

- **WHEN** `KPI.command` est exécuté
- **AND** le hash de `pyproject.toml` diffère du stamp (ou le stamp est absent)
- **THEN** `.venv/bin/pip install -e . --quiet` est exécuté
- **AND** le stamp est réécrit avec le nouveau hash
- **AND** l'application démarre après l'installation

#### Scenario: Dépendances déjà à jour

- **WHEN** `KPI.command` est exécuté
- **AND** le hash de `pyproject.toml` correspond au stamp
- **THEN** aucune commande pip n'est exécutée
- **AND** le lancement reste rapide

#### Scenario: Environnement virtuel absent

- **WHEN** le dossier `.venv` n'existe pas
- **THEN** le venv est créé (`python3 -m venv .venv`, `pip install --upgrade pip`) comme aujourd'hui
- **AND** les dépendances sont installées et le stamp est écrit

#### Scenario: Échec de l'installation pip

- **WHEN** `.venv/bin/pip install -e .` échoue
- **THEN** un avertissement est affiché
- **AND** le script poursuit et lance l'application avec les dépendances actuelles

### Requirement: Ordre des opérations dans le script

La mise à jour du code git (avec ré-exécution éventuelle) précède la mise à jour des dépendances, qui précède le lancement de l'application.

#### Scenario: Code et dépendances ont tous deux bougé

- **WHEN** `KPI.command` est exécuté
- **AND** des commits sont en retard
- **AND** `pyproject.toml` a changé dans ces commits
- **THEN** `git pull --ff-only` est exécuté en premier
- **AND** le script se ré-exécute
- **AND** la seconde exécution constate le code à jour, exécute `pip install -e .` avec le nouveau `pyproject.toml`, réécrit le stamp
- **AND** l'application démarre ensuite, une seule fois

### Requirement: Échappatoire à la mise à jour automatique

La mise à jour automatique peut être désactivée par variable d'environnement ; la création du venv si absent, elle, a toujours lieu.

#### Scenario: Variable KPI_SANS_MISE_A_JOUR définie

- **WHEN** `KPI.command` est exécuté avec `KPI_SANS_MISE_A_JOUR=1` dans l'environnement
- **THEN** ni `git fetch`/`git pull` ni la réinstallation pip ne sont exécutés
- **AND** le venv est toujours créé s'il est absent
- **AND** l'application démarre directement

### Requirement: Protection contre les boucles de ré-exécution

La ré-exécution du script après un `git pull` réussi ne doit pas provoquer de boucle infinie, y compris si le pull a modifié `KPI.command` lui-même.

#### Scenario: Ré-exécution après pull

- **WHEN** le script se ré-exécute après un `git pull --ff-only` réussi
- **THEN** la seconde exécution détecte que le code est à jour
- **AND** aucun nouveau pull ni ré-exécution n'a lieu
- **AND** un garde-fou (variable d'environnement interne `_KPI_MAJ_REEXEC`) bloque toute ré-exécution récursive au-delà d'une seule fois

### Requirement: Comportement de lancement inchangé

Le script reste un lanceur macOS classique : double-clic depuis le Finder, lancement de `.venv/bin/kpi`, fenêtre Terminal maintenue ouverte en fin d'exécution.

#### Scenario: Lancement standard

- **WHEN** `KPI.command` est exécuté
- **THEN** le répertoire courant du script devient le dossier du projet (`cd "$(dirname "$0")"`)
- **AND** `.venv/bin/kpi` est lancé après les éventuelles mises à jour
- **AND** le message « Appuyez sur Entrée pour fermer cette fenêtre... » est affiché en fin d'exécution
- **AND** la commande `kpi` elle-même (code Python) n'est pas modifiée
