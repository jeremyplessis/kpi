# Tasks: Appliquer la charte graphique

## 1. Proposition OpenSpec

- [x] 1.1 Rédiger proposal.md, design.md, specs/charte-graphique.md et tasks.md dans openspec/changes/appliquer-charte-graphique — verify: 4 fichiers présents

## 2. Assets marque extraits de la charte

- [x] 2.1 Extraire le pictogramme du PDF, retirer le fond, recolorer en sapin #353F38, sauver static/favicon.png (64px) — verify: GET /static/favicon.png → 200, image carrée
- [x] 2.2 Extraire le logo primaire du PDF, fond transparent, recoloré sapin, sauver static/logo-primaire.png — verify: GET /static/logo-primaire.png → 200

## 3. Thème CSS dans base.html

- [x] 3.1 Remplacer les variables `--encre`…`--erreur-texte` par les valeurs de la palette charte — verify: grep des codes hex dans base.html
- [x] 3.2 Ajouter le chargement des polices (Fraunces 600, Red Hat Display 400/500/700) avec replis — verify: font-family des titres = Fraunces, Georgia, serif ; body = Red Hat Display, system-ui
- [x] 3.3 Appliquer Fraunces aux h1/h2/legend — verify: règle CSS présente
- [x] 3.4 Ajouter le motif papier millimétré en fond de body (dégradés CSS subtils) — verify: background-image sur body
- [x] 3.5 Boutons primaires : fond #353F38, hover #0B100C — verify: règles button.primaire
- [x] 3.6 Ajouter <link rel="icon"> et le pictogramme en favicon — verify: balise dans le <head>
- [x] 3.7 Ajouter un pied de page avec le logo primaire — verify: <footer> dans base.html avec /static/logo-primaire.png

## 4. Graphiques Chart.js

- [x] 4.1 kpi.html : remplacer les rgba(180, 89, 59, …) par sapin rgba(53, 63, 56, …) — verify: grep sans occurrence de 180, 89, 59
- [x] 4.2 kpi.html : palette 12 couleurs 100 % issue de la charte — verify: grep des couleurs du graphique
- [x] 4.3 kpi_ghosting.html : demandes #92AFA6, réponses #475836, ghosting #DAB941 — verify: grep des couleurs

## 5. Tests

- [x] 5.1 Test : base.html contient le favicon et le pied de page logo — verify: test_web.py
- [x] 5.2 Test : les variables CSS contiennent les codes de la palette (#353F38, #F4F2ED…) — verify: test_web.py
- [x] 5.3 Tous les tests existants passent — verify: .venv/bin/python -m unittest discover -s tests
- [x] 5.4 pycodestyle sans régression — verify: .venv/bin/pycodestyle src/ tests/

## 6. Documentation

- [x] 6.1 Entrée CHANGELOG.md (section « À venir ») — verify: section modifiée
