# Tasks: Accès au CHANGELOG (lien externe, nouvel onglet)

## 1. Retirer le rendu interne (révision de la spécification)

- [x] 1.1 Supprimer la route `GET /changelog` et la méthode `page_changelog` de `routes.py` — verify: la route n'apparaît plus dans les routes FastAPI
- [x] 1.2 Supprimer les helpers `_telecharger_changelog` et `_lire_changelog` (plus de téléchargement serveur) — verify: plus aucune référence à `urlopen` dans `routes.py`
- [x] 1.3 Supprimer le template `src/kpi/web/gabarits/changelog.html` — verify: le fichier n'existe plus

## 2. URL GitHub de la branche courante

- [x] 2.1 Garder `_branche_courante()` (git rev-parse, repli `main`) — verify: retourne la branche courante
- [x] 2.2 Dans `__init__`, exposer la variable globale Jinja2 `url_changelog = f"https://github.com/jeremyplessis/kpi/blob/{self._branche_courante()}/CHANGELOG.md"` — verify: `app.modeles.env.globals["url_changelog"]` contient l'URL

## 3. Lien dans l'en-tête

- [x] 3.1 Modifier `base.html:226` : `(v{{ version }} - <a href="{{ url_changelog }}" target="_blank" rel="noopener" style="color: inherit;">changements</a>)` — verify: le HTML rendu contient `target="_blank"` et l'URL GitHub

## 4. Tests

- [x] 4.1 Test : le lien `/changelog` interne est retiré (GET /changelog → 404) — verify: `test_route_changelog_supprimee`
- [x] 4.2 Test : l'en-tête contient un lien `target="_blank"` vers `github.com` se terminant par `/CHANGELOG.md` — verify: `test_lien_changelog_nouvel_onglet`
- [x] 4.3 Test : le lien contient le mot « changements » et `rel="noopener"` — verify: `test_lien_changelog_attributs`
- [x] 4.4 Test : repli branche `main` quand git échoue — verify: `test_branche_courante_repli_main`

## 5. Vérification globale

- [x] 5.1 Lancer la suite complète : `.venv/bin/python -m unittest discover -s tests` — verify: tous les tests passent
