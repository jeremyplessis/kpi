# Tasks: Affichage complet du commentaire

## 1. CSS

- [x] 1.1 Dans `base.html`, revenir en `table-layout: auto`, `min-width: 42rem` sur le tableau, `white-space: nowrap` sur les cellules standard, et contraindre le commentaire via un div interne (`max-width: 22rem`, `overflow-wrap: break-word`) — verify: `grep "td.commentaire" base.html`
- [x] 1.2 Agrandir la zone liste : grille `minmax(300px, 4fr) minmax(0, 10fr)` + `.sans-formulaire` en `1fr` quand le formulaire est masqué — verify: `grep "sans-formulaire" base.html`
- [x] 1.3 Style `.pagination` et `.bouton-ajouter` — verify: `grep "bouton-ajouter" base.html`

## 2. Template

- [x] 2.1 Dans `saisie.html`, ajouter `title="{{ _evenement.commentaire }}"` sur la cellule `<td class="commentaire">` quand le commentaire existe
- [x] 2.2 Dans `saisie.html`, envelopper le commentaire dans `<div>` et ajouter la barre de pagination (Précédent/Suivant)
- [x] 2.3 Dans `saisie.html`, masquer le formulaire par défaut (`{% if afficher_formulaire %}`) et afficher le lien « + Ajouter un événement » avec `url_afficher_formulaire`
- [x] 2.4 Dans `saisie.html`, ajouter un lien « Fermer » (`url_masquer_formulaire`) dans les actions du formulaire, et supprimer le lien « Gérer les listes »

## 3. Pagination et formulaire conditionnel (routes)

- [x] 3.0 Dans `routes.py`, `EVENEMENTS_PAR_PAGE = 10`, paginer `_contexte_page` avec `page`, `total_pages`, `total_evenements`, URLs de pagination
- [x] 3.1 Dans `routes.py`, lire `afficher_formulaire` depuis l'URL, forcer à True dans `page_modifier` et `_reafficher_formulaire`, conserver dans `_rediriger_vers_saisie`, construire `url_afficher_formulaire` et `url_masquer_formulaire`

## 4. Tests

- [x] 4.1 Test : un commentaire long est présent en entier dans le HTML de la liste — `test_commentaire_complet_dans_liste`
- [x] 4.2 Test : la cellule a un attribut `title` avec le commentaire complet — `test_commentaire_title`
- [x] 4.3 Test : pas de `title` quand le commentaire est vide — `test_commentaire_sans_title_si_vide`
- [x] 4.4 Test : le CSS contient `max-width: 22rem` et `overflow-wrap: break-word` — `test_commentaire_css_sans_troncature`
- [x] 4.5 Tests pagination : 10/page, page 1 + lien Suivant, dernière page + lien Précédent, page invalide, filtres conservés, pas de barre si <= 10 — classe `TestPagination` (5 tests)
- [x] 4.6 Tests formulaire conditionnel : masqué par défaut avec lien Ajouter, affiché avec `?afficher_formulaire=1`, lien conserve filtres/page, redirection conserve le paramètre — 3 tests
- [x] 4.7 Tests bouton Fermer et lien Gérer les listes supprimé — 2 tests

## 5. Documentation

- [x] 5.1 Mettre à jour `documentation/03_ecran_saisie.md` : pagination 10/page, formulaire masqué par défaut, lien « Ajouter », infobulle au survol

## 6. Intégration

- [x] 6.1 Tous les tests passent — `.venv/bin/python -m unittest discover -s tests` (87 tests OK)
- [x] 6.2 Pas de régression visuelle — `white-space: nowrap` sur les cellules, `min-width: 42rem` sur le tableau
