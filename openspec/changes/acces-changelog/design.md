# Design: Accès au CHANGELOG

## Contexte

L'en-tête commun (`base.html:226`) affiche déjà le numéro de version via la variable globale Jinja2 `version` (injectée dans `routes.py:131` depuis `kpi.__version__`). Le projet est hébergé sur GitHub (`git@github.com:jeremyplessis/kpi.git`). Le fichier `CHANGELOG.md` est commité à la racine du dépôt.

## Décisions

### D1 — Le lien pointe vers une page web, pas vers le fichier brut

Le navigateur ouvre `/changelog`, une route FastAPI qui rend le contenu du `CHANGELOG.md` dans un template. Cela garde la navigation dans l'application (en-tête, pied de page communs).

### D2 — Le CHANGELOG est téléchargé depuis GitHub (branche courante)

`page_changelog` construit l'URL `https://raw.githubusercontent.com/jeremyplessis/kpi/<branche>/CHANGELOG.md` où `<branche>` est obtenue par `git rev-parse --abbrev-ref HEAD` (via `subprocess`, avec repli sur `"main"` si git échoue). Le téléchargement utilise `urllib.request.urlopen` (bibliothèque standard — aucune dépendance ajoutée ; `httpx` n'est qu'en dépendance dev). Timeout de 5 secondes. Le contenu est téléchargé à chaque requête (pas de cache) pour refléter la branche effectivement déployée.

### D3 — Repli sur le disque local en cas d'échec réseau

Si le téléchargement échoue (pas de réseau, branche non poussée, 404 GitHub), la page tente de lire `CHANGELOG.md` sur le disque local (`Path(__file__).parent.parent.parent.parent / "CHANGELOG.md"`) et affiche une mention « (copie locale — la branche n'est pas publiée sur GitHub) ». Si les deux échouent, message « Aucun historique disponible. ». La page répond toujours 200.

### D4 — Affichage en texte préformaté

Le CHANGELOG est du Markdown. Aucun convertisseur Markdown n'est dans les dépendances du projet ; ajouter une dépendance pour une page consultative serait disproportionné. Le contenu est affiché dans un bloc `<pre>` avec `white-space: pre-wrap`, dans une carte stylisée comme le reste de l'interface.

### D5 — Position du lien dans l'en-tête

Le lien « changements » est placé à l'intérieur du `<span>` existant qui affiche la version, sous la forme `(v{{ version }} - <a href="/changelog">changements</a>)`. Le lien hérite du style du span (`color: inherit`) pour rester discret.

## Fichiers concernés

| Fichier | Modification |
|---|---|
| `src/kpi/web/gabarits/base.html` | Ligne 226 : ajouter le lien dans le span de version |
| `src/kpi/web/routes.py` | Ajouter `_app.get("/changelog")(self.page_changelog)` ; méthode `page_changelog` avec téléchargement GitHub + repli disque ; helpers `_branche_courante()` et `_telecharger_changelog()` |
| `src/kpi/web/gabarits/changelog.html` | Nouveau template héritant de `base.html` |
| `tests/test_web.py` | Tests avec mock de `urllib.request.urlopen` : succès GitHub, repli disque, aucun disponible, lien dans l'en-tête |

## Risques

- **Dépendance à la connectivité réseau** : mitigée par le repli sur le disque local (D3).
- **Branche non poussée** : le 404 GitHub déclenche le repli local avec mention explicite.
- **Appel `git` via subprocess** : le binaire git est requis (déjà le cas pour setuptools-scm). Repli sur `"main"` si indisponible.
- **Temps de réponse** : timeout de 5 s sur le téléchargement ; au-delà, repli local.
