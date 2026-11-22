# Tasks: Amélioration du lanceur macOS (KPI.command)

## 1. Bloc git dans KPI.command

- [x] 1.1 Ajouter en tête de `KPI.command` (après le `cd`), le garde `[ -z "$KPI_SANS_MISE_A_JOUR" ] && [ -d .git ]` pour le bloc git — verify: `bash -n KPI.command` sans erreur
- [x] 1.2 Implémenter le fetch borné : `git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 fetch --quiet origin 2>/dev/null` ; en échec → avertissement « remote injoignable » et on saute le bloc — verify: sans réseau, le script affiche l'avertissement et poursuit
- [x] 1.3 Implémenter la branche amont : `@{upstream}` via `git rev-parse --abbrev-ref @{upstream}`, repli `origin/$(git rev-parse --abbrev-ref HEAD)` ; si aucune des deux n'existe côté remote → ignorer silencieusement — verify: branche sans upstream → repli sur `origin/<branche>`
- [x] 1.4 Implémenter la détection de retard : `git rev-list --count HEAD..$AMONT` > 0 → `git pull --ff-only` — verify: dépôt en retard → pull exécuté ; à jour → aucun pull
- [x] 1.5 En cas de succès du pull : `_KPI_MAJ_REEXEC=1 exec bash "$0"` (garde-fou anti-boucle, re-lit un script éventuellement modifié par le pull) ; en cas d'échec du pull → avertissement et on poursuit — verify: arbre sale → avertissement, pas de ré-exécution, lancement normal

## 2. Bloc dépendances dans KPI.command

- [x] 2.1 Conserver la création du venv si absent telle quelle, et y ajouter l'écriture du stamp `.venv/kpi-pyproject.sha256` après `pip install -e .` réussi — verify: premier lancement → venv créé + stamp présent
- [x] 2.2 Ajouter le calcul du hash : `_HASH=$(shasum -a 256 pyproject.toml 2>/dev/null | awk '{print $1}')` avec repli `sha256sum` — verify: produit le même hash que `shasum -a 256 pyproject.toml`
- [x] 2.3 Ajouter la comparaison au stamp : si `.venv/kpi-pyproject.sha256` absent ou différent → `.venv/bin/pip install -e . --quiet` puis réécriture du stamp ; échec pip → avertissement et on poursuit — verify: `pyproject.toml` modifié → pip appelé + stamp mis à jour ; second lancement → aucun pip
- [x] 2.4 Placer le bloc dépendances après le bloc git (la ré-exécution ayant déjà replacé le script sur le nouveau code) et avant `.venv/bin/kpi` — verify: code + `pyproject.toml` bougés → pull, ré-exécution, puis pip avec le nouveau hash, lancement unique

## 3. Échappatoire

- [x] 3.1 Vérifier que `KPI_SANS_MISE_A_JOUR=1` désactive le bloc git et la réinstallation pip, tout en conservant la création du venv si absent — verify: `KPI_SANS_MISE_A_JOUR=1 bash KPI.command` dans un clone en retard → aucun fetch/pull/pip, lancement direct

## 4. Tests

- [x] 4.1 Créer `tests/test_lanceur.py` : helper qui construit un dossier temporaire (clone git + remote bare local, faux `pyproject.toml`, faux `.venv/bin/pip` et `.venv/bin/kpi` qui écrivent leurs arguments dans un fichier log, `KPI.command` copié depuis la racine du projet) et exécute `bash KPI.command < /dev/null` via subprocess — verify: le helper isole complètement le vrai dépôt et le vrai venv
- [x] 4.2 Test : branche en retard sur le remote → `git pull` présent dans l'historique git du clone et le script s'est ré-exécuté (garde-fou) — verify: `test_pull_quand_en_retard`
- [x] 4.3 Test : branche à jour → aucun pull, aucune ré-exécution — verify: `test_rien_quand_a_jour`
- [x] 4.4 Test : `pyproject.toml` modifié (hash différent du stamp) → faux pip appelé avec `install -e .` et stamp réécrit ; hash identique → pip non appelé — verify: `test_pip_quand_pyproject_change`, `test_pas_pip_quand_stamp_identique`
- [x] 4.5 Test : `KPI_SANS_MISE_A_JOUR=1` → ni fetch/pull ni pip — verify: `test_env_desactive_mise_a_jour`
- [x] 4.6 Test : dossier sans `.git` → bloc git ignoré silencieusement, lancement normal — verify: `test_hors_depot_git`
- [x] 4.7 Lancer toute la suite : `.venv/bin/python -m unittest discover -s tests` — verify: tous les tests passent, y compris les existants

## 5. Documentation et style

- [x] 5.1 Mettre à jour le bloc de code copiable de `KPI.command` dans `documentation/03_ecran_saisie.md` pour qu'il corresponde exactement au nouveau script — verify: diff entre le bloc de la doc et `KPI.command` = vide (hors commentaires explicatifs)
- [x] 5.2 Vérifier la syntaxe et le style du script : `bash -n KPI.command` et `shellcheck KPI.command` si disponible — verify: aucune erreur ; warnings documentés si shellcheck absent
- [x] 5.3 Mettre à jour le CHANGELOG.md — verify: entrée pour la mise à jour automatique du lanceur `KPI.command`

## 6. Intégration

- [x] 6.1 Vérification manuelle : double-clic (ou `bash KPI.command`) avec un commit en retard sur origin → le Terminal affiche la mise à jour, le script se ré-exécute et l'application démarre — verify: logs du Terminal + application ouverte sur l'écran de saisie
- [x] 6.2 Vérification manuelle hors ligne : avertissement affiché, lancement normal — verify: pas de blocage
- [x] 6.3 Vérification manuelle avec `pyproject.toml` touché : `pip install -e .` relancé, stamp mis à jour — verify: second lancement sans réinstallation
- [ ] 6.4 Commit selon Conventional Commits (`feat(lanceur): ...`) et push de la branche `feat-amelioration-lanceur` — verify: branche poussée sur origin
