# Design: Indicateurs de conversion (nombre et taux)

## Context

Le moteur d'indicateurs fonctionne sur `calculer(_evenements) -> list[LigneIndicateur]`.
Les indicateurs classiques reçoivent les événements de la période filtrée.

**Problème** : les indicateurs de conversion ont besoin de connaître les demandes antérieures à la période pour détecter celles qui sont encore ouvertes. Ils doivent donc recevoir **tous les événements** + les bornes de la période.

## Architecture

### Nouvelle méthode `calculer_periode`

Les indicateurs de conversion implémentent une méthode supplémentaire :

```python
def calculer_periode(
    self,
    _tous_evenements: Sequence[EvenementSuivi],
    _debut: tuple[int, int] | None,  # (année, mois) ou None = début des données
    _fin: tuple[int, int] | None,    # (année, mois) ou None = fin des données
) -> list[LigneIndicateur]:
```

### Adaptation de `page_kpi` dans `routes.py`

```python
if hasattr(_indicateur, "calculer_periode"):
    _a_debut = int(_annee_debut) if _annee_debut else None
    _m_debut = int(_mois_debut) if _mois_debut else None
    _a_fin = int(_annee_fin) if _annee_fin else None
    _m_fin = int(_mois_fin) if _mois_fin else None
    _debut = (_a_debut, _m_debut) if _a_debut else None
    _fin = (_a_fin, _m_fin) if _a_fin else None
    _lignes_indicateur = _indicateur.calculer_periode(_evenements, _debut, _fin)
else:
    _lignes_indicateur = _indicateur.calculer(_evenements_filtres)
```

Idem dans `_construire_tableau_de_bord`.

### Fonction utilitaire `_calculer_demandeurs_ouverts`

```python
def _calculer_demandeurs_ouverts(
    _tous_evenements: Sequence[EvenementSuivi],
    _debut: tuple[int, int] | None,
    _fin: tuple[int, int] | None,
) -> tuple[set[str], dict[str, str]]:
    """Retourne (demandeurs_ouverts, statut_par_personne).

    - demandeurs_ouverts : personnes avec au moins une demande dans P
      OU (demande avant P ET sans Confirmation dans P).
    - statut_par_personne : statut de la première demande de chaque personne.
    """
```

Algorithme :
1. Trier tous les événements par date.
2. Pour chaque personne, mémoriser sa première demande (date + statut).
3. `demandes_dans_P` = personnes avec au moins une demande dans P.
4. `confirmations_dans_P` = personnes avec au moins une Confirmation dans P.
5. `demandes_avant_P` = personnes avec au moins une demande avant P.
6. `demandeurs_ouverts` = `demandes_dans_P` ∪ (`demandes_avant_P` − `confirmations_dans_P`).

### NbConversions

```
class NbConversions(Indicateur):
    libelle = "Nombre de conversions"
    dimensions = ("statut",)
```

`calculer_periode` :
1. Compter les Confirmations dans P, par statut de la personne (statut de sa première demande, ou "(vide)" si pas de demande).
2. Lignes : `("Tous", total)`, puis par statut trié.

`calculer(_evenements)` (pour compatibilité) : délègue à `calculer_periode(_evenements, None, None)`.

### TauxConversion

```
class TauxConversion(Indicateur):
    libelle = "Taux de conversion"
    dimensions = ("statut",)
```

`calculer_periode` :
1. `demandeurs, statut` = `_calculer_demandeurs_ouverts(...)`.
2. `confirmations` = personnes avec Confirmation dans P.
3. `taux_global = len(confirmations) / len(demandeurs) × 100` si demandeurs > 0, sinon 0.
4. Par statut S : `taux_S = len(confirmations ∩ statut=S) / len(demandeurs ∩ statut=S) × 100`.
5. Lignes : `("Tous", taux_global)`, puis par statut.

## Fichiers impactés

| Fichier | Changement |
|---|---|
| `src/kpi/kpi/indicateurs.py` | +`_calculer_demandeurs_ouverts()`, +`NbConversions`, +`TauxConversion` avec `calculer_periode` |
| `src/kpi/web/routes.py` | `page_kpi` et `_construire_tableau_de_bord` : détecter `calculer_periode` et passer tous les événements + bornes |
| `tests/test_calculs_kpi.py` | tests avec demandes antérieures, demandes dans P, confirmations |
