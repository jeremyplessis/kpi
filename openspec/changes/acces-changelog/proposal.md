# Proposal: Accès au CHANGELOG depuis l'en-tête

## Why

L'utilisatrice veut savoir ce qui a changé dans la version qu'elle utilise sans quitter l'application. Un lien discret dans l'en-tête, à côté du numéro de version, lui permet de consulter l'historique des changements de la version en cours. Le contenu est lu directement depuis le dépôt GitHub (branche courante), garantissant que le CHANGELOG affiché correspond toujours à la branche effectivement déployée.

## What Changes

- L'en-tête affiche désormais « Suivi d'activité (vX.Y.Z - changements) » où « changements » est un lien vers une nouvelle page `/changelog`
- Nouvelle route `GET /changelog` qui télécharge le fichier `CHANGELOG.md` depuis `raw.githubusercontent.com` sur la branche git courante et l'affiche dans une page dédiée
- Nouveau template `changelog.html` héritant de `base.html`, présentant le contenu du CHANGELOG dans une carte lisible
- En cas d'indisponibilité réseau ou branche introuvable sur GitHub, la page affiche le CHANGELOG local (repli sur le disque) puis un message d'erreur clair

## Capabilities

### New Capabilities
- `acces-changelog/page-changelog`: Page `/changelog` affichant le contenu du fichier `CHANGELOG.md` de la branche courante tel que publié sur GitHub, avec lien depuis l'en-tête de toutes les pages

## Impact

- `src/kpi/web/gabarits/base.html` : le numéro de version devient `(v{{ version }} - <a href="/changelog">changements</a>)`
- `src/kpi/web/routes.py` : nouvelle route `GET /changelog` et méthode `page_changelog` téléchargeant `CHANGELOG.md` depuis GitHub (branche courante) via `urllib.request`
- `src/kpi/web/gabarits/changelog.html` : nouveau template
- `tests/test_web.py` : tests de la route `/changelog` (mock du téléchargement) et de la présence du lien dans l'en-tête
