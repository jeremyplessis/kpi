# Design: Application de la charte graphique

## Context

La charte graphique (`docs/Charte Graphique.pdf`, novembre 2026) définit :
- **Palette** : 01 Jaune `#ECD981`, 02 Bleu `#C1D3CE`, 03 Vert clair `#D1CF95`, 04 Vert `#879675`, 05 Beige `#F4F2ED`, 06 Sapin `#353F38`, chacune avec 3 nuances (claire, moyenne, foncée)
- **Typographies** : Laviossa (titres), Roundo capitales (sous-titres), Roundo (texte). Substitutions officielles : Canva « Recoleta Alt Semi gras » / « Red hat Display », Insta « Poster » / « Deco »
- **Règles** : sur fonds clairs privilégier le vert sapin ; sur fonds foncés le blanc ; motif papier millimétré en fond subtil ; logo primaire recommandé en pied de page de site ; submark recommandé comme favicon
- **Pictogramme** : étoile/halo de lumière (tatouage de Cécile), déclinable en monochrome

## Goals / Non-Goals

**Goals :**
- Toute l'interface adopte la palette officielle (aucune couleur hors palette hors états fonctionnels)
- Hiérarchie typographique : titres serif expressif, texte courant lisible
- Identité de marque visible : favicon + pied de page avec le logo
- Graphiques lisibles et cohérents avec la charte

**Non-Goals :**
- Utiliser les polices commerciales Laviossa/Roundo (non disponibles librement) → substitutions libres
- Refondre la navigation ou la structure des pages
- Modifier le moteur de calcul ou les données

## Decisions

### Decision 1: Polices de substitution servies par Google Fonts avec replis

Laviossa et Roundo sont commerciales. La charte recommande Red Hat Display comme substitut de Roundo (disponible sur Google Fonts, licence OFL). Pour Laviossa (serif doux et expressif), Fraunces (OFL, Google Fonts) est le substitut libre le plus proche. Les polices sont chargées via `<link>` Google Fonts avec `display=swap` et des piles de repli (`Georgia, serif` / `system-ui, sans-serif`) : l'application reste lisible sans connexion.

### Decision 2: Variables CSS dérivées de la palette

Les 6 couleurs principales et les nuances utiles deviennent des variables CSS nommées d'après la charte (`--sapin`, `--vert`, `--bleu`, `--jaune`, `--vert-clair`, `--beige`, + nuances). Les rôles sémantiques existants (`--encre`, `--fond`, `--accent`…) pointent vers ces variables pour limiter le diff dans les templates.

Mapping :
- `--fond` → `--beige` #F4F2ED ; `--carte` → #FBFBF9 ; `--bord` → #D0D3C5 (vert, nuance claire)
- `--encre` → `--sapin` #353F38 ; `--encre-doux` → #757B74 (sapin, nuance moyenne)
- `--accent` (liens, focus, legend) → `--vert-fonce` #475836 ; boutons primaires fond sapin #353F38, hover #0B100C
- succès → fond #E8E6D0 / bord #ABA857 / texte #475836 ; erreur → fond #EAE6DC / bord #757B74 / texte #0B100C

### Decision 3: Motif papier millimétré en CSS pur

Plutôt qu'une image, le motif est reproduit par deux `linear-gradient` répétés (lignes fines `#879675` à 8 % d'opacité, tous les 24 px) sur le `body`. Subtil, sans asset, conforme à « utilisation subtile ».

### Decision 4: Favicon et logo extraits du PDF, recolorés sapin

Le pictogramme (submark) et le logo primaire sont extraits des images vectorielles du PDF (`pdfimages`), le fond retiré (transparence) et le blanc remplacé par le sapin #353F38 — déclinaison monochrome autorisée par la charte. Fichiers servis depuis `/static/`.

### Decision 5: Graphiques Chart.js en palette

Couleur principale des séries : sapin #353F38. Palettes multi-séries (12 couleurs) construites exclusivement depuis les 6 couleurs + nuances foncées. Ghosting : demandes en bleu #92AFA6, réponses en vert #475836, zone ghosting en jaune foncé #DAB941.

## Data Flow

Aucun changement de données. `GET /*` → `base.html` applique le thème ; les templates KPI consomment les mêmes contextes, seules les couleurs JS changent.
