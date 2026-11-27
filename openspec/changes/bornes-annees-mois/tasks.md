# Tasks: Bornes année/mois min et max pour « Toutes les années » / « Tous les mois »

## 1. Helper de calcul des bornes

- [ ] 1.1 Ajouter `_bornes_annees_mois(_evenements) -> tuple[tuple[int, int], tuple[int, int]] | None` dans `src/kpi/web/routes.py` — retourne `((a_min, m_min), (a_max, m_max))`, `None` si liste vide — verify: `python -c "from kpi.web.routes import _bornes_annees_mois; ..."` avec événements fictifs
- [ ] 1.2 Couvrir le cas liste vide (retour `None`, pas d'exception)

## 2. Distinction absent / présent-vide dans page_kpi

- [ ] 2.1 Remplacer `if not (_annee_debut or _mois_debut or _annee_fin or _mois_fin):` par une condition sur la présence des clés dans `_requete.query_params` — verify: `/kpi` sans paramètre applique toujours les 12 mois glissants (test existant non cassé)
- [ ] 2.2 Quand au moins une clé est présente : résoudre les composantes vides via `_bornes_annees_mois` pour obtenir `_debut`/`_fin` effectifs — verify: `/kpi?indicateur=NbDemandes&annee_debut=&mois_debut=&annee_fin=&mois_fin=` retourne toutes les lignes de la base

## 3. Application dans _page_ghosting_detail et _construire_tableau_de_bord

- [ ] 3.1 Appliquer la même logique dans `_page_ghosting_detail` — verify: `/kpi/TauxGhosting?annee_debut=&mois_debut=&annee_fin=&mois_fin=` couvre toute la plage des données
- [ ] 3.2 Appliquer la même résolution des bornes dans `_construire_tableau_de_bord` pour `_debut`/`_fin` passés aux indicateurs `calculer_periode` — verify: carte « Taux de conversion » recalculée sur toute la plage

## 4. Tests unitaires

- [ ] 4.1 Test : `_bornes_annees_mois` avec liste vide → `None` ; avec événements → bons couples min/max
- [ ] 4.2 Test : `page_kpi` avec les 4 paramètres présents mais vides → période = min/max des données (vérifier le contexte passé au template et les événements filtrés)
- [ ] 4.3 Test : `page_kpi` sans aucun paramètre → 12 mois glissants (non-régression du change filtres-par-defaut)
- [ ] 4.4 Test : `page_kpi` avec un seul paramètre (ex. `annee_debut=2025`) → pas de défaut, autres bornes = min/max des données
- [ ] 4.5 Test : base vide + 4 paramètres vides → aucune erreur, « Aucune donnée disponible »
- [ ] 4.6 Non-régression : `python -m unittest discover -s tests` — tous les tests passent

## 5. Vérification manuelle et style

- [ ] 5.1 Lancer l'application, ouvrir `/kpi`, sélectionner « Toutes les années » / « Tous les mois », cliquer sur « Appliquer les filtres » — verify: les indicateurs couvrent l'intégralité de l'historique, pas les 12 derniers mois
- [ ] 5.2 Cliquer sur « Effacer les filtres » — verify: retour aux 12 derniers mois glissants
- [ ] 5.3 `pycodestyle src/ tests/` sans erreur — verify: style PEP 8 respecté
