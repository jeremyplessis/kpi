# Proposal: Améliorer l'affichage de la colonne commentaire dans la liste des événements

## Why

Dans l'écran de saisie, la colonne « Commentaire » du tableau « Derniers événements » est tronquée sur la droite : le CSS limite la cellule à `max-width: 18rem` (`td.commentaire` dans `base.html`), ce qui coupe visuellement les commentaires longs. L'utilisatrice ne voit pas le contenu complet sans modifier l'événement. Ce point était déjà signalé comme TODO dans `documentation/00_analyse_kpi_xlsx.md`.

## What Changes

- Supprimer ou assouplir la contrainte `max-width: 18rem` sur `td.commentaire`
- Permettre au commentaire de s'afficher en entier, soit :
  - en élargissant la colonne (sans max-width, le tableau s'étire) ;
  - ou en ajoutant un mécanisme de dépliage au clic (cliquer sur la cellule déploie le texte complet) ;
  - ou en affichant le commentaire complet dans l'attribut `title` (infobulle au survol) en complément.
- Garder le tableau lisible : éviter que la colonne commentaire n'écrase les autres colonnes
- Option retenue à valider : **infobulle `title` + largeur adaptative** (pas de max-width agressif, `min-width` suffisant)

## Capabilities

### Modified Capabilities
- `ecran-saisie/liste-evenements`: La colonne commentaire du tableau des derniers événements affiche le texte complet (plus de troncature à droite)

## Impact

- `src/kpi/web/gabarits/base.html` : modifier le CSS de `td.commentaire` (supprimer `max-width: 18rem`, ajuster `min-width`)
- `src/kpi/web/gabarits/saisie.html` : ajouter `title="{{ _evenement.commentaire }}"` sur la cellule pour infobulle au survol
- `tests/test_web.py` : test vérifiant que le commentaire complet est présent dans le HTML (attribut title ou cellule non tronquée)
- `documentation/03_ecran_saisie.md` : mettre à jour la section sur le tableau des événements
