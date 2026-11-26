# Tasks: Accès au CHANGELOG

## 1. Template de la page changelog

- [ ] 1.1 Créer `src/kpi/web/gabarits/changelog.html` héritant de `base.html`, avec un bloc `contenu` affichant `{{ contenu_changelog }}` dans un `<pre>` stylisé à l'intérieur d'une `.carte`, plus une ligne facultative `{{ source_changelog }}` — verify: le template se rend sans erreur Jinja2

## 2. Helpers de lecture du CHANGELOG (GitHub + repli disque)

- [ ] 2.1 Implémenter `_branche_courante()` dans `routes.py` : `subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"])`, repli `"main"` en cas d'échec — verify: retourne le nom de la branche courante
- [ ] 2.2 Implémenter `_telecharger_changelog()` : GET `https://raw.githubusercontent.com/jeremyplessis/kpi/<branche>/CHANGELOG.md` via `urllib.request.urlopen` (timeout 5 s), retourne le texte ou `None` — verify: mock de `urlopen` retourne le contenu en test
- [ ] 2.3 Implémenter le repli : si `_telecharger_changelog()` retourne `None`, lire `CHANGELOG.md` sur le disque avec la mention « (copie locale — la branche n'est pas publiée sur GitHub) » ; sinon « Aucun historique disponible. » — verify: les trois cas renvoient un contenu et une source

## 3. Route /changelog

- [ ] 3.1 Ajouter `_app.get("/changelog")(self.page_changelog)` dans `_configurer_routes` — verify: la route apparaît dans la liste des routes FastAPI
- [ ] 3.2 Implémenter `page_changelog` : appeler les helpers, rendre `changelog.html` avec `contenu_changelog` et `source_changelog` dans le contexte — verify: `GET /changelog` répond 200

## 4. Lien dans l'en-tête

- [ ] 4.1 Modifier `base.html:226` : remplacer `(v{{ version }})` par `(v{{ version }} - <a href="/changelog" style="color: inherit;">changements</a>)` — verify: le HTML rendu contient `href="/changelog"` et le mot « changements »

## 5. Tests

- [ ] 5.1 Test : `GET /changelog` avec mock `urlopen` réussi retourne 200 et le contenu téléchargé — verify: `test_page_changelog_depuis_github`
- [ ] 5.2 Test : `GET /changelog` avec mock `urlopen` en échec et fichier local présent → repli disque + mention « copie locale » — verify: `test_page_changelog_repli_disque`
- [ ] 5.3 Test : `GET /changelog` avec les deux sources indisponibles → « Aucun historique disponible. » — verify: `test_page_changelog_indisponible`
- [ ] 5.4 Test : le lien `/changelog` est présent dans le HTML de la page d'accueil — verify: `test_lien_changelog_dans_entete`

## 6. Vérification globale

- [ ] 6.1 Lancer la suite complète : `.venv/bin/python -m unittest discover -s tests` — verify: tous les tests passent
