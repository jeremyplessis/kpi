# Design: Affichage complet du commentaire dans la liste des événements

## Context

Le tableau « Derniers événements » dans `saisie.html` affiche 8 colonnes dans un conteneur avec `overflow-x: auto`. La colonne commentaire a actuellement `max-width: 18rem` dans `base.html`, ce qui tronque visuellement les commentaires longs. Le problème est signalé dans `documentation/00_analyse_kpi_xlsx.md` (TODO).

## Goals / Non-Goals

**Goals:**
- Le commentaire complet est visible sans modifier l'événement
- Le tableau reste lisible (pas de colonne commentaire qui écrase tout)
- Pas de scroll horizontal forcé à cause du commentaire

**Non-Goals:**
- Un éditeur de commentaire inline dans le tableau
- La pagination du tableau
- Modifier le formulaire de saisie du commentaire

## Decisions

### Decision 1: Infobulle `title` + largeur adaptative

Deux mécanismes complémentaires :
1. **Attribut `title`** sur la cellule `<td>` : au survol, le navigateur affiche le commentaire complet dans une infobulle native. Aucun JS nécessaire.
2. **CSS assoupli** : supprimer `max-width: 18rem`, garder `min-width: 4rem` et laisser le navigateur répartir l'espace. Le commentaire revient à la ligne (`white-space: normal`) mais n'est plus coupé arbitrairement à droite.

### Decision 2: Pas de troncature avec ellipsis

Éviter `text-overflow: ellipsis` qui couperait le texte avec « … ». L'infobulle `title` + retour à la ligne suffisent.

### Decision 3: Le tableau garde son `overflow-x: auto`\n
Si le tableau dépasse la largeur, le scroll horizontal reste disponible, mais la colonne commentaire ne force plus ce scroll à elle seule.

## Data Flow

Aucun changement de data flow : le commentaire est déjà présent dans `_evenement.commentaire`, il suffit de l'afficher complètement.

```
_evenement.commentaire (déjà chargé)
  → cellule <td class="commentaire" title="...">texte complet</td>
  → CSS : min-width: 4rem, pas de max-width
```
