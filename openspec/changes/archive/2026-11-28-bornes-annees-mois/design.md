# Design: Bornes année/mois min et max pour « Toutes les années » / « Tous les mois »

## Vue d'ensemble

Le changement est limité à la couche web (`src/kpi/web/routes.py`) et aux tests. Aucune modification du moteur de calcul ni du schéma SQLite.

## Décisions techniques

### 1. Distinguer « paramètre absent » de « paramètre présent mais vide »

C'est le cœur du fix. Dans `page_kpi` et `_page_ghosting_detail`, remplacer la condition actuelle :

```python
if not (_annee_debut or _mois_debut or _annee_fin or _mois_fin):
```

par une condition sur la **présence des clés** dans l'URL :

```python
_CLE_PERIODE = ("annee_debut", "mois_debut", "annee_fin", "mois_fin")
_a_aucun_parametre = not any(_c in _requete.query_params for _c in _CLE_PERIODE)
if _a_aucun_parametre:
    # 12 mois glissants (comportement par défaut, inchangé)
    ...
```

Ainsi :
- `/kpi` (aucun paramètre) → 12 mois glissants ;
- `/kpi?annee_debut=&mois_debut=&annee_fin=&mois_fin=` (4 paramètres vides) → bornes min/max des données.

### 2. Helper de calcul des bornes (année, mois) des données

Nouvelle fonction dans `src/kpi/web/routes.py` :

```python
def _bornes_annees_mois(
    _evenements: list[EvenementSuivi],
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Retourne ((année_min, mois_min), (année_max, mois_max)) des événements.

    Retourne None si la liste est vide.
    """
    if not _evenements:
        return None
    _cles = [(_ev.annee, _ev.mois) for _ev in _evenements]
    return min(_cles), max(_cles)
```

### 3. Résolution des bornes de période effectives

Quand au moins un paramètre est présent dans l'URL, les composantes vides sont résolues depuis les données :

- début : `annee_debut`/`mois_debut` vides → couple min des événements ;
- fin : `annee_fin`/`mois_fin` vides → couple max des événements.

Ces bornes résolues servent à la fois :
- au filtrage via `_filtrer_par_periode` (qui reçoit désormais des valeurs non vides, ou bien on lui passe les bornes résolues) ;
- aux indicateurs avec `calculer_periode` (`_debut`, `_fin`), pour que `NbConversions` et `TauxConversion` calculent réellement sur toute la plage des données et pas sur `None`.

Implémentation proposée : calculer `_debut` et `_fin` résolus une seule fois dans `page_kpi` :

```python
_bornes = _bornes_annees_mois(_evenements)
_a_d = int(_annee_debut) if _annee_debut else (_bornes[0][0] if _bornes else None)
_m_d = int(_mois_debut) if _mois_debut else (_bornes[0][1] if _bornes else (1 if _a_d else None))
_a_f = int(_annee_fin) if _annee_fin else (_bornes[1][0] if _bornes else None)
_m_f = int(_mois_fin) if _mois_fin else (_bornes[1][1] if _bornes else (12 if _a_f else None))
_debut = (_a_d, _m_d) if _a_d else None
_fin = (_a_f, _m_f) if _a_f else None
```

et utiliser `_debut`/`_fin` pour `_filtrer_par_periode` (via une variante acceptant des tuples, ou en réinjectant les valeurs résolues dans les chaînes passées à `_filtrer_par_periode`).

### 4. Cohérence `_filtrer_par_periode`

La méthode `_filtrer_par_periode` garde sa signature (4 chaînes). Deux options :
- (retenue) résoudre les vides **avant** l'appel, en passant les valeurs min/max à la place des chaînes vides — la méthode reste inchangée et son comportement « vide = extrême des données » devient un filet de sécurité inutile mais conservé.
- Alternative écartée : modifier `_filtrer_par_periode` pour accepter les bornes résolues — plus invasif, aucun bénéfice.

### 5. Application identique dans `_page_ghosting_detail` et `_construire_tableau_de_bord`

- `_page_ghosting_detail` : même condition sur la présence des clés + mêmes bornes résolues pour le filtre.
- `_construire_tableau_de_bord` : reçoit déjà les 4 paramètres ; appliquer la même résolution des bornes pour `_debut`/`_fin` passés aux indicateurs `calculer_periode`.

### 6. Templates

Aucune modification nécessaire : les sélecteurs affichent « Toutes les années » / « Tous les mois » quand les valeurs sont vides, ce qui correspond au choix explicite de l'utilisatrice.

## Points d'attention

- **Base vide + paramètres vides** : `_bornes_annees_mois` retourne `None`, `_debut`/`_fin` restent `None`, `_filtrer_par_periode` retourne une liste vide → « Aucune donnée disponible ». Aucun crash.
- **Un seul paramètre présent** (ex. `annee_debut=2025`) : comportement existant préservé (pas de défaut), les autres bornes vides se résolvent sur min/max des données.
- **Tests** : injecter des événements avec des couples (année, mois) connus et vérifier que `/kpi?...&annee_debut=&mois_debut=&annee_fin=&mois_fin=` filtre bien sur toute la plage, et que `/kpi` sans paramètre applique toujours les 12 mois glissants.

## Fichiers impactés

| Fichier | Modification |
|---|---|
| `src/kpi/web/routes.py` | Condition sur présence des clés, helper `_bornes_annees_mois`, résolution des bornes dans `page_kpi`, `_page_ghosting_detail`, `_construire_tableau_de_bord` |
| `tests/test_web.py` | Nouveaux tests : paramètres présents mais vides → bornes min/max ; paramètres absents → 12 mois glissants (non-régression) |
