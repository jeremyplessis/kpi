# Proposal: Bornes année/mois min et max pour « Toutes les années » / « Tous les mois »

## Why

Sur l'écran `/kpi`, quand l'utilisatrice sélectionne « Toutes les années » et « Tous les mois » (les 4 sélecteurs de période laissés vides) puis clique sur « Appliquer les filtres », l'URL générée est `/kpi?...&annee_debut=&mois_debut=&annee_fin=&mois_fin=` : les 4 paramètres sont **présents mais vides**.

Or le code actuel de `page_kpi` (et `_page_ghosting_detail`) applique la période par défaut (12 mois glissants) dès que les 4 valeurs sont vides :

```python
if not (_annee_debut or _mois_debut or _annee_fin or _mois_fin):
    _a, _m, _af, _mf = _periode_par_defaut()
    ...
```

Cette condition ne distingue pas « paramètres absents de l'URL » (vrai défaut) de « paramètres présents mais vides » (choix explicite de l'utilisatrice). Résultat : le clic sur « Appliquer les filtres » avec « Toutes les années » / « Tous les mois » ramène silencieusement à la période par défaut, et l'utilisatrice ne peut jamais consulter l'intégralité de l'historique via les filtres.

## What Changes

- **Modifié** : `src/kpi/web/routes.py` — dans `page_kpi` et `_page_ghosting_detail`, la période par défaut (12 mois glissants) ne s'applique que quand **aucun** des 4 paramètres de période n'est présent dans l'URL (`"annee_debut" in _requete.query_params`, etc.). Quand au moins un paramètre est présent, les valeurs vides signifient « borne extrême des données ».
- **Nouveau** : helper `_bornes_annees_mois(_evenements)` qui retourne les couples `(année, mois)` minimum et maximum présents dans les événements, pour résoudre les bornes vides.
- **Modifié** : `_filtrer_par_periode` — utiliser ces bornes min/max quand une borne est vide (au lieu de se rabattre sur une logique par défaut), afin que « Toutes les années » / « Tous les mois » couvre réellement tout l'historique.
- **Modifié** : `page_kpi` et `_construire_tableau_de_bord` — transmettre aux indicateurs avec `calculer_periode` les bornes résolues (min/max des données quand les paramètres sont vides), et non `None`, pour que le recalcul porte bien sur toute la plage des données.
- **Nouveau** : tests dans `tests/test_web.py` couvrant le cas « 4 paramètres présents mais vides ».

### Hors périmètre

- Pas de changement du libellé du lien « Effacer les filtres » (hors sujet).
- Pas de mémorisation des filtres.
- Pas de modification du schéma SQLite ni du moteur de calcul des indicateurs.

## Hypothèses enregistrées

- « Paramètre présent mais vide » = choix explicite « Toutes les années » / « Tous les mois » ; la période couvre alors du couple (année, mois) minimum au couple maximum trouvés dans les événements.
- « Paramètre absent de l'URL » = visite initiale ou lien « Effacer les filtres » → 12 mois glissants (comportement existant, préservé).
- Si la base est vide et que les 4 paramètres sont vides, il n'y a aucune donnée : les indicateurs affichent « Aucune donnée disponible » (pas de calcul de bornes sur liste vide).
