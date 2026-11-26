# Proposal: Accès au CHANGELOG depuis l'en-tête

## Why

L'utilisatrice veut savoir ce qui a changé dans la version qu'elle utilise sans quitter l'application. Un lien discret dans l'en-tête, à côté du numéro de version, lui permet d'ouvrir le `CHANGELOG.md` de la branche courante sur GitHub dans un nouvel onglet du navigateur.

## What Changes

- L'en-tête affiche désormais « Suivi d'activité (vX.Y.Z - changements) » où « changements » est un lien ouvrant le `CHANGELOG.md` de la branche courante sur GitHub **dans une nouvelle fenêtre** (`target="_blank"`)
- L'URL pointée est `https://github.com/jeremyplessis/kpi/blob/<branche-courante>/CHANGELOG.md`
- Aucun rendu interne : pas de route `/changelog`, pas de template dédié — le navigateur affiche directement le fichier publié sur GitHub

## Capabilities

### New Capabilities
- `acces-changelog/lien-changelog`: Lien « changements » dans l'en-tête de toutes les pages, ouvrant le `CHANGELOG.md` de la branche courante sur GitHub dans un nouvel onglet

## Impact

- `src/kpi/web/gabarits/base.html` : le numéro de version devient `(v{{ version }} - <a href="{{ url_changelog }}" target="_blank" rel="noopener">changements</a>)`
- `src/kpi/web/routes.py` : calcul de l'URL GitHub (branche courante via `git rev-parse --abbrev-ref HEAD`, repli `main`) exposé comme variable globale Jinja2 `url_changelog`
- `tests/test_web.py` : tests de la présence du lien `target="_blank"` et de l'URL GitHub dans l'en-tête
