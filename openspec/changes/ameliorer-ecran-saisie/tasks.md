# Tasks: Affichage complet du commentaire

## 1. CSS

- [ ] 1.1 Dans `base.html`, modifier `td.commentaire` : supprimer `max-width: 18rem`, garder `min-width: 4rem` et `white-space: normal` — verify: `grep "td.commentaire" base.html` ne montre plus de max-width

## 2. Template

- [ ] 2.1 Dans `saisie.html`, ajouter `title="{{ _evenement.commentaire }}"` sur la cellule `<td class="commentaire">` quand le commentaire existe — verify: le HTML généré contient `title="..."` pour un commentaire long

## 3. Tests

- [ ] 3.1 Test dans `test_web.py` : un commentaire long est présent en entier dans le HTML de la liste — verify: `test_commentaire_complet_dans_liste`
- [ ] 3.2 Test : la cellule a un attribut `title` avec le commentaire complet — verify: `test_commentaire_title`
- [ ] 3.3 Test : pas de `title` quand le commentaire est vide — verify: `test_commentaire_sans_title_si_vide`

## 4. Documentation

- [ ] 4.1 Mettre à jour `documentation/03_ecran_saisie.md` : mentionner que le commentaire complet est visible (infobulle au survol) — verify: la doc reflète le nouveau comportement

## 5. Intégration

- [ ] 5.1 Tous les tests passent — verify: `.venv/bin/python -m unittest discover -s tests`
- [ ] 5.2 Pas de régression visuelle sur le reste du tableau — verify: les autres colonnes gardent leur largeur
