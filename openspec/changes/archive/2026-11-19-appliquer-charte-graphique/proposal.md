# Proposal: Appliquer la charte graphique de Cécile Plessis Photographe

## Why

L'application a été développée avec une palette neutre par défaut (beige chaud, accent terracotta) et la police système Segoe UI. Cécile dispose maintenant d'une charte graphique officielle (`docs/Charte Graphique.pdf`, novembre 2026) qui définit une palette de 6 couleurs, deux typographies (Laviossa pour les titres, Roundo pour le texte) et un pictogramme personnel. L'application doit adopter cette identité visuelle pour rester cohérente avec l'ensemble des supports de communication de la marque.

## What Changes

- Remplacement des variables CSS de `base.html` par la palette officielle :
  - fonds beige `#F4F2ED`, cartes `#FBFBF9`, bords `#D0D3C5`
  - texte principal vert sapin `#353F38` (règle charte : vert sapin sur fonds clairs), texte secondaire `#757B74`
  - boutons primaires en sapin `#353F38`, liens et accents en vert `#475836`
- Typographie : titres en substitut Laviossa (Fraunces, police libre proche), texte courant en substitut Roundo (Red Hat Display, recommandé par la charte), avec replis système si les polices ne chargent pas
- Motif « papier millimétré » en arrière-plan subtil (lignes `#879675` à faible opacité), conformément à la charte
- Favicon : pictogramme (submark) extrait de la charte, recoloré sapin
- Pied de page : logo primaire extrait de la charte, version sapin sur transparent (la charte recommande le logo primaire en pied de page de site)
- Graphiques Chart.js (`kpi.html`, `kpi_ghosting.html`) : séries colorées exclusively avec la palette (sapin, vert, bleu, jaune et leurs nuances foncées)
- Bandeaux succès/erreur : teintés avec les nuances de la palette (vert clair pour succès, beige foncé + sapin foncé pour erreur)

## Capabilities

### New Capabilities
- `charte-graphique/palette-css`: Variables CSS de `base.html` conformes à la palette officielle (6 couleurs + nuances)
- `charte-graphique/typographie`: Hiérarchie Laviossa→titres / Roundo→texte via polices de substitution servies avec replis
- `charte-graphique/marque`: Favicon (pictogramme) et pied de page (logo primaire) extraits de la charte
- `charte-graphique/graphiques`: Couleurs des graphiques Chart.js restreintes à la palette

### Modified Capabilities
- `consultation-kpi/page-kpi`: Les écrans KPI héritent automatiquement du nouveau thème via `base.html`

## Impact

- `src/kpi/web/gabarits/base.html` : variables CSS, `@font-face`/lien polices, motif de fond, favicon, pied de page
- `src/kpi/web/gabarits/kpi.html` : couleurs Chart.js
- `src/kpi/web/gabarits/kpi_ghosting.html` : couleurs Chart.js
- `src/kpi/web/static/` : `favicon.png`, `logo-primaire.png` (extraits du PDF de la charte)
- `tests/test_web.py` / `tests/test_kpi_web.py` : tests de non-régression (présence favicon, pied de page, variables palette)
- `CHANGELOG.md` : entrée dans la section « À venir »
