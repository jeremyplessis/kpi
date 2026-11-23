# Design: Lanceur macOS (KPI.command) avec mise à jour automatique

## Context

`KPI.command` est un script bash à la racine du projet, lancé par double-clic depuis le Finder (ouverture dans Terminal). Il fait aujourd'hui : `cd "$(dirname "$0")"`, création du venv si absent (`python3 -m venv .venv` + `pip install -e .`), puis `.venv/bin/kpi`, puis un `read` final. Le projet est un clone git avec le remote `origin` (GitHub) ; la branche courante peut ne pas avoir d'upstream configuré (cas observé sur `feat-amelioration-lanceur`).

Contraintes macOS : pas de commande `timeout` (coreutils absent), `shasum` présent par défaut, bash 3.2 (pas de fonctionnalités bash 4+). Le script est suivi par git : un `git pull` peut donc modifier `KPI.command` **pendant que bash le lit** — d'où la ré-exécution systématique après un pull réussi.

**Périmètre** : aucune modification du code Python. La commande `kpi` (`src/kpi/app.py`) reste telle quelle ; toute la logique de mise à jour vit dans `KPI.command`.

## Goals / Non-Goals

**Goals:**
- `KPI.command` lance toujours l'application, même si une mise à jour échoue (réseau, conflit git, pip en échec)
- Remote en avance → `git pull --ff-only` puis ré-exécution du script pour charger le nouveau code
- `pyproject.toml` changé → `.venv/bin/pip install -e . --quiet` dans le venv local
- Lancement rapide quand rien n'a changé (pas de `pip install` systématique)
- Échappatoire par variable d'environnement `KPI_SANS_MISE_A_JOUR=1` (tests, usage hors ligne)

**Non-Goals:**
- Pas de modification de `src/kpi/app.py` ni de la commande `kpi` (ni flag `--sans-mise-a-jour` côté Python)
- Pas de merge automatique (uniquement `--ff-only`)
- Pas de gestion de conflits git (avertissement + lancement avec le code actuel)
- Pas de mise à jour si le dossier n'est pas un clone git
- Pas de notification push ni de planification (mise à jour uniquement au lancement)

## Decisions

### Decision 1: Toute la logique dans `KPI.command`, zéro changement Python

Le bloc de mise à jour est ajouté dans le script bash, avant le lancement de `.venv/bin/kpi`. `src/kpi/app.py` n'est pas touché : la commande `kpi` lancée manuellement depuis un terminal ne fait aucune mise à jour.

### Decision 2: Détection « le projet a bougé » par `git fetch` + `rev-list HEAD..amont`

`git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 fetch --quiet origin` (les options `lowSpeed*` bornent un transfert bloqué à ~30 s, remplaçant l'absente commande `timeout` sur macOS) puis `git rev-list --count HEAD..<amont>`. Si le compte > 0, la branche est en retard. L'amont est `@{upstream}` si configuré, sinon `origin/$(git rev-parse --abbrev-ref HEAD)` ; si cette branche n'existe pas côté remote, la vérification est ignorée silencieusement. Toute erreur (hors ligne, pas un dépôt) → avertissement ou silence selon le cas, jamais de blocage. Le script fait déjà `cd "$(dirname "$0")"` en tête : toutes les commandes git s'exécutent donc à la racine du projet.

### Decision 3: `git pull --ff-only` uniquement, puis ré-exécution du script

Seul le fast-forward est autorisé : jamais de commit de merge, jamais d'écrasement des modifications locales. Si le pull réussit et a fait avancer `HEAD`, le script se ré-exécute via `_KPI_MAJ_REEXEC=1 exec bash "$0"` : ceci est indispensable car bash lit le script incrémentalement et le pull peut avoir modifié `KPI.command` lui-même ; c'est aussi ce qui fait « relire » le nouveau code par le shell. Le garde-fou `_KPI_MAJ_REEXEC` bloque toute boucle (la seconde exécution constate le code à jour). Si le pull échoue (arbre sale, divergence) → avertissement, le script poursuit sans ré-exécution.

### Decision 4: Détection « les dépendances ont bougé » par hash de `pyproject.toml`

Le SHA-256 de `pyproject.toml` (`shasum -a 256 pyproject.toml`, repli `sha256sum` pour Linux) est comparé au stamp `.venv/kpi-pyproject.sha256`. Stamp absent ou différent → `.venv/bin/pip install -e . --quiet` puis réécriture du stamp. Le stamp vit dans `.venv/` (ignoré par git, donc jamais commité) et le pip appelé est celui du venv local du script. La création du venv si absent est conservée telle quelle et écrit aussi le stamp après installation. Échec pip → avertissement, lancement quand même.

### Decision 5: Ordre strict dans le script — git, ré-exécution, puis dépendances, puis lancement

1. Bloc git : fetch, pull `--ff-only` éventuel, ré-exécution guardée si le code a bougé
2. Bloc dépendances : création du venv si absent, sinon vérification du stamp et `pip install -e .` éventuel (la ré-exécution ayant déjà replacé le script sur le nouveau code, c'est bien le nouveau `pyproject.toml` qui est hashé)
3. Lancement de `.venv/bin/kpi` + `read` final inchangés

### Decision 6: Échappatoire unique par variable d'environnement

`KPI_SANS_MISE_A_JOUR=1` dans l'environnement du Terminal désactive le bloc git et la réinstallation pip (la création du venv si absent a toujours lieu). Pas de flag côté Python, la commande `kpi` n'étant pas modifiée.

### Decision 7: Jamais de blocage

Aucune commande du bloc de mise à jour n'utilise `set -e` ; chaque étape en échec est rattrapée (`|| echo "⚠ ..."`) et le script atteint toujours le lancement de `.venv/bin/kpi`.

## Data Flow

```
KPI.command (double-clic Finder → Terminal)
  → cd "$(dirname "$0")"                      # racine du projet
  → [ -z "$KPI_SANS_MISE_A_JOUR" ] && [ -d .git ] ?
    → git fetch origin (lowSpeed 30 s)
      → amont = @{upstream} ou origin/<branche>
      → rev-list --count HEAD..amont > 0 ?
        → oui : git pull --ff-only
          → succès : _KPI_MAJ_REEXEC=1 exec bash "$0"   # re-lit le script éventuellement mis à jour
          → échec  : avertissement, on continue
        → non : rien
    → fetch en échec : avertissement, on continue
  → [ ! -d .venv ] ? → création venv + pip install -e . + stamp
  → sinon : hash pyproject.toml vs .venv/kpi-pyproject.sha256
      → différent/absent : .venv/bin/pip install -e . --quiet + réécrit le stamp
      → pip en échec : avertissement, on continue
  → .venv/bin/kpi                               # inchangé
  → read                                        # inchangé
```

## Risques et mitigations

| Risque | Mitigation |
|---|---|
| `KPI.command` modifié par le pull pendant sa lecture par bash | ré-exécution `exec bash "$0"` après tout pull réussi, guardée par `_KPI_MAJ_REEXEC` |
| Boucle infinie de ré-exécution | garde-fou `_KPI_MAJ_REEXEC=1` + la seconde exécution détecte « à jour » |
| Perte de modifications locales | `--ff-only` uniquement ; échec = avertissement + lancement |
| Blocage réseau au lancement | options git `http.lowSpeedLimit`/`http.lowSpeedTime` (~30 s max) ; toute erreur → avertissement + continue |
| Pas de `timeout` sur macOS | on n'en utilise pas ; les bornes réseau passent par git |
| `shasum` vs `sha256sum` | `shasum -a 256` d'abord (macOS), repli `sha256sum` (Linux) |
| Stamp commité par erreur | il vit dans `.venv/`, déjà ignoré par git (AGENTS.md) |
| Tests qui déclenchent de vrais git pull/pip | tests exécutent le script via subprocess dans un dépôt temporaire avec remote local et faux binaires `.venv/bin/pip` / `.venv/bin/kpi` ; `KPI_SANS_MISE_A_JOUR=1` pour les autres tests |
