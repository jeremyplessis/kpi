# Spec Delta: Charte graphique

## ADDED Requirements

### Requirement: Palette officielle en variables CSS

Le thème de l'application est défini exclusivement à partir des couleurs de la charte graphique de Cécile Plessis Photographe (novembre 2026) : Jaune #ECD981, Bleu #C1D3CE, Vert clair #D1CF95, Vert #879675, Beige #F4F2ED, Sapin #353F38 et leurs nuances.

#### Scenario: Lecture des variables CSS

- **WHEN** le navigateur charge n'importe quelle page de l'application
- **THEN** les variables CSS `--fond`, `--carte`, `--bord`, `--encre`, `--encre-doux`, `--accent` ont pour valeurs des couleurs de la palette officielle (beige, blanc cassé #FBFBF9, vert clair #D0D3C5, sapin #353F38, sapin moyen #757B74, vert foncé #475836)
- **AND** aucune couleur hors palette n'est utilisée pour les fonds, textes, bordures ou boutons

#### Scenario: Texte sur fonds clairs

- **WHEN** du texte est affiché sur un fond clair
- **THEN** il est composé en vert sapin #353F38 (ou une nuance foncée de la palette), conformément à la règle de la charte

### Requirement: Boutons primaires en vert sapin

Les boutons d'action principale sont remplis en vert sapin #353F38 avec du texte blanc, et passent au sapin très foncé #0B100C au survol.

#### Scenario: Survol d'un bouton primaire

- **WHEN** l'utilisatrice survole le bouton « Enregistrer »
- **THEN** le fond du bouton passe de #353F38 à #0B100C

### Requirement: Typographie conforme à la hiérarchie de la charte

Les titres (h1, h2, legend) utilisent une police serif expressive (substitut de Laviossa), le texte courant une police sans-serif lisible (substitut de Roundo). Des replis système garantissent la lisibilité si les polices ne sont pas chargées.

#### Scenario: Chargement avec connexion

- **WHEN** la page est chargée avec un accès à Google Fonts
- **THEN** les titres sont rendus en Fraunces et le texte en Red Hat Display

#### Scenario: Chargement sans connexion

- **WHEN** la page est chargée sans accès à Google Fonts
- **THEN** les titres utilisent le repli serif (Georgia) et le texte le repli système (system-ui), sans erreur

### Requirement: Motif papier millimétré subtil en arrière-plan

Le fond de page comporte un quadrillage très léger (lignes de la palette à faible opacité), conformément au motif « papier millimétré » de la charte, sans gêner la lecture.

#### Scenario: Affichage du fond

- **WHEN** l'utilisatrice consulte n'importe quelle page
- **THEN** le fond beige #F4F2ED comporte un quadrillage subtil en vert #879675 à faible opacité

### Requirement: Favicon = pictogramme de la marque

Le favicon de l'application est le pictogramme (submark) de la charte, en version monochrome vert sapin.

#### Scenario: Onglet du navigateur

- **WHEN** l'application est ouverte dans un onglet
- **THEN** l'icône de l'onglet est le pictogramme étoile de Cécile en #353F38

### Requirement: Pied de page avec le logo primaire

Toutes les pages affichent un pied de page contenant le logo primaire de la charte en version monochrome sapin, conformément à la recommandation « logo primaire en pied de page du site ».

#### Scenario: Bas de page

- **WHEN** l'utilisatrice fait défiler une page jusqu'en bas
- **THEN** un pied de page affiche le logo « Cécile Plessis — photographie • studio » en sapin #353F38

### Requirement: Graphiques Chart.js dans la palette

Toutes les séries des graphiques des écrans KPI utilisent exclusivement des couleurs de la palette officielle (sapin, vert, bleu, jaune, vert clair et leurs nuances).

#### Scenario: Graphique d'un indicateur

- **WHEN** l'utilisatrice affiche le graphique d'un indicateur KPI
- **THEN** la courbe est tracée en sapin #353F38 (ou une couleur de la palette pour les séries multiples)
- **AND** aucune couleur hors palette (rouge, violet, orange vif…) n'apparaît dans le graphique

#### Scenario: Graphique du taux de ghosting

- **WHEN** l'utilisatrice affiche l'écran ghosting
- **THEN** les demandes sont en bleu #92AFA6, les réponses en vert #475836, la zone de ghosting en jaune foncé #DAB941
