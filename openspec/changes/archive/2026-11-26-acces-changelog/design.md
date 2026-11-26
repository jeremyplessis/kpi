# Design: Accès au CHANGELOG

## Contexte

L'en-tête commun (`base.html:226`) affiche déjà le numéro de version via la variable globale Jinja2 `version`. Le projet est hébergé sur GitHub (`git@github.com:jeremyplessis/kpi.git`). Le fichier `CHANGELOG.md` est commité à la racine du dépôt.

## Décisions

### D1 — Le lien ouvre GitHub dans un nouvel onglet, sans page interne

Contrairement à une première version qui rendait `/changelog` dans l'application, le lien pointe directement vers le fichier publié sur GitHub avec `target="_blank" rel="noopener"`. Avantages : aucun code serveur de téléchargement, le navigateur affiche le Markdown tel que GitHub le rend, et l'application reste ouverte dans l'onglet d'origine. Inconvénient accepté : nécessite une connexion réseau au moment du clic.

### D2 — L'URL GitHub est calculée côté serveur et injectée dans le gabarit

La branche courante est obtenue par `git rev-parse --abbrev-ref HEAD` (via `subprocess`, repli `"main"` si git échoue). L'URL `https://github.com/jeremyplessis/kpi/blob/<branche>/CHANGELOG.md` est exposée comme variable globale Jinja2 `url_changelog` (calculée à l'initialisation de `ApplicationWeb`, comme `version`). Le gabarit reste ainsi déclaratif : `<a href="{{ url_changelog }}" target="_blank" rel="noopener">changements</a>`.

### D3 — Position du lien dans l'en-tête

Le lien « changements » est placé à l'intérieur du `<span>` existant qui affiche la version, sous la forme `(v{{ version }} - <a ...>changements</a>)`. Le lien hérite du style du span (`color: inherit`) pour rester discret.

## Fichiers concernés

| Fichier | Modification |
|---|---|
| `src/kpi/web/gabarits/base.html` | Ligne 226 : lien `target="_blank"` vers `{{ url_changelog }}` |
| `src/kpi/web/routes.py` | Méthode `_branche_courante()` + variable globale `url_changelog` dans `__init__` ; suppression de la route `/changelog` et des helpers de téléchargement |
| `src/kpi/web/gabarits/changelog.html` | Supprimé (plus de rendu interne) |
| `tests/test_web.py` | Tests : lien `target="_blank"` présent, URL GitHub correcte, repli `main` |

## Risques

- **Branche non poussée** : GitHub affichera une page 404 dans le nouvel onglet. Accepté : le lien reflète fidèlement la branche courante.
- **Hors ligne** : le nouvel onglet affiche l'erreur réseau du navigateur. Accepté pour un lien externe.
- **Appel `git` à l'initialisation** : subprocess avec timeout 5 s, repli `"main"`.
