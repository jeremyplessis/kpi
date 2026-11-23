# Design: Filtres de période par défaut sur 12 mois glissants

## Vue d'ensemble

Le changement est limité à la couche web (routes + templates). Aucune modification du moteur de calcul ni du schéma SQLite.

## Décisions techniques

### 1. Fonction utilitaire de calcul de la période par défaut

Ajouter une fonction dans `src/kpi/web/routes.py` :

```python
def _periode_par_defaut(_aujourdhui: date | None = None) -> tuple[int, int, int, int]:
    """Retourne (année_début, mois_début, année_fin, mois_fin) pour les
    12 derniers mois glissants, mois en cours inclus.

    :param _aujourdhui: date de référence (par défaut ``date.today()``),
        injectable pour les tests.
    """
    _ref = _aujourdhui or date.today()
    _total_mois = _ref.year * 12 + (_ref.month - 1)  # mois écoulés depuis l'an 0
    _debut_total = _total_mois - 11  # 11 mois avant le mois en cours
    _a_debut, _m_debut = divmod(_debut_total, 12)
    return _a_debut, _m_debut + 1, _ref.year, _ref.month
```

### 2. Application des filtres par défaut dans `page_kpi`

Dans `page_kpi` (et `_page_ghosting_detail`), après lecture des paramètres d'URL :

```python
_annee_debut = _requete.query_params.get("annee_debut", "")
_mois_debut = _requete.query_params.get("mois_debut", "")
_annee_fin = _requete.query_params.get("annee_fin", "")
_mois_fin = _requete.query_params.get("mois_fin", "")

# Si AUCUN paramètre de période n'est présent, appliquer les 12 mois glissants
if not (_annee_debut or _mois_debut or _annee_fin or _mois_fin):
    _a_d, _m_d, _a_f, _m_f = _periode_par_defaut()
    _annee_debut = str(_a_d)
    _mois_debut = str(_m_d)
    _annee_fin = str(_a_f)
    _mois_fin = str(_m_f)
```

### 3. Cohérence avec `_filtrer_par_periode`

La méthode `_filtrer_par_periode` existe déjà et gère les filtres partiels (si seule l'année de début est donnée, etc.). En passant les 4 valeurs par défaut, le filtrage se comporte comme une période normale — aucun changement nécessaire dans cette méthode.

### 4. Templates

Aucune modification structurelle des templates `kpi.html` et `kpi_ghosting.html` : les variables `annee_debut`, `mois_debut`, `annee_fin`, `mois_fin` sont déjà utilisées pour pré-sélectionner les `<option selected>`. Il suffit que le route leur passe les bonnes valeurs.

### 5. Lien « Effacer les filtres »

Le lien `<a href="/kpi">Effacer les filtres</a>` pointe vers `/kpi` sans paramètre : il retombe donc naturellement sur les 12 mois glissants. **Ce n'est plus un « effacement » mais un retour au défaut.** Le libellé du lien pourrait être ajusté en « Réinitialiser (12 derniers mois) » pour éviter la confusion, mais ce renommage est optionnel et laissé à l'appréciation.

## Points d'attention

- **Testabilité** : la fonction `_periode_par_defaut` accepte une date en paramètre pour être testée avec des dates fixes (ex: 15 janvier 2026 → début = février 2025).
- **Cas limite janvier** : si on est en janvier 2026, les 12 mois glissants vont de février 2025 à janvier 2026 (divmod gère correctement le passage d'année).
- **Cas limite base vide** : si aucun événement n'existe, `_obtenir_annees` retourne un set vide, les sélecteurs d'année n'ont que l'option « Toutes les années » + les années par défaut calculées. Il faudra s'assurer que les années de la période par défaut apparaissent dans `annees_disponibles` même sans événements, ou que le sélecteur affiche quand même la valeur sélectionnée. **Décision** : ajouter les années de la période par défaut à `annees_disponibles` si elles n'y sont pas déjà.

## Fichiers impactés

| Fichier | Modification |
|---|---|
| `src/kpi/web/routes.py` | Ajout `_periode_par_defaut()`, modification `page_kpi` et `_page_ghosting_detail` |
| `src/kpi/web/gabarits/kpi.html` | Optionnel : libellé du lien « Effacer les filtres » |
| `src/kpi/web/gabarits/kpi_ghosting.html` | Aucun (les variables sont déjà passées) |
| `tests/test_web.py` | Nouveaux tests pour `_periode_par_defaut` et le comportement de `page_kpi` |
