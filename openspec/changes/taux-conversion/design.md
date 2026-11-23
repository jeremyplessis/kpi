# Design: Indicateurs de conversion (nombre et taux)

## Context

Le moteur d'indicateurs (`src/kpi/kpi/indicateurs.py`) fonctionne sur le modèle suivant :

- Chaque indicateur hérite de `Indicateur` et implémente `calculer(_evenements) -> list[LigneIndicateur]`.
- `LigneIndicateur` est un `NamedTuple(dimensions: tuple, valeur: float)`.
- Les indicateurs sont enregistrés dans `REGISTRE_INDICATEURS` et consommés par la route `/kpi` (`page_kpi` dans `routes.py`).
- Le tableau de bord (`_construire_tableau_de_bord`) agrège chaque indicateur pour afficher une carte de synthèse avec un total et un sparkline.
- La période est déjà filtrée en amont par `_filtrer_par_periode` dans `routes.py` : les indicateurs reçoivent uniquement les événements de la période sélectionnée.

Les règles métier validées (28/10/2026) définissent déjà :
- **Demande** : `action_public ∈ {"Demande", "Réservation"}`
- **Dédoublonnage demandes** : une personne = une demande par mois max

Nouvelle règle métier (novembre 2026) :
- **Conversion en séance** : `action_photographe = "Confirmation"` pour une personne ayant aussi une demande dans la période

## Architecture des nouveaux indicateurs

### Fonction utilitaire partagée : `_detecter_demandes_et_conversions`

```python
def _detecter_demandes_et_conversions(
    _evenements: list[EvenementSuivi],
) -> tuple[set[str], dict[str, str], set[str]]:
    """Retourne (personnes_avec_demande, statut_par_personne, personnes_converties).

    - personnes_avec_demande : personnes ayant au moins un événement avec
      action_public ∈ {"Demande", "Réservation"} (une seule fois par personne,
      quel que soit le nombre de demandes sur la période).
    - statut_par_personne : statut_contact du premier événement de demande
      de chaque personne (client / prospect / autre).
    - personnes_converties : personnes ayant au moins une demande ET au moins
      un événement avec action_photographe == "Confirmation".
    """
```

### NbConversions

```
class NbConversions(Indicateur):
    libelle = "Nombre de conversions"
    dimensions = ("statut",)
```

**Algorithme** :

1. Appeler `_detecter_demandes_et_conversions(_evenements)`.
2. Pour chaque personne convertie, récupérer son statut.
3. Agréger : `{"Tous": nb_total, "client": nb_clients, "prospect": nb_prospects}` (les statuts autres que client/prospect sont regroupés sous leur libellé propre ou ignorés selon les données).
4. Retourner les `LigneIndicateur` avec `dimensions = (statut,)` et `valeur = nb`.

### TauxConversion

```
class TauxConversion(Indicateur):
    libelle = "Taux de conversion"
    dimensions = ("statut",)
```

**Algorithme** :

1. Appeler `_detecter_demandes_et_conversions(_evenements)`.
2. `taux_global = len(converties) / len(demandeurs) × 100` si demandeurs > 0, sinon `None`.
3. Pour chaque statut S ∈ {"client", "prospect"} :
   - `demandeurs_S` = demandeurs avec statut S
   - `convertis_S` = convertis avec statut S
   - `taux_S = len(convertis_S) / len(demandeurs_S) × 100` si demandeurs_S > 0, sinon `None`
4. Retourner les lignes :
   - `("Tous", taux_global)` — le pourcentage global
   - `("client", taux_client)` — composante clients
   - `("prospect", taux_prospect)` — composante prospects
5. Les valeurs sont des pourcentages (0–100), pas des ratios 0–1.

## Intégration web

### Tableau de bord (`_construire_tableau_de_bord`)

- `TauxConversion` est traité comme un pourcentage : la carte affiche le taux global (ligne « Tous »).
- `NbConversions` affiche la somme (ligne « Tous »).

### Page indicateur (`/kpi?indicateur=TauxConversion`)

- Tableau dépliable à 1 dimension (`statut`) : ligne « Tous » en parent, lignes « client » et « prospect » en enfants (dépliables au clic, comme le tableau existant).
- Graphique Chart.js en barres : 3 barres (Tous, Clients, Prospects) avec les pourcentages.
- Si une composante a `None` (pas de demandes), afficher « — ».

### Page indicateur (`/kpi?indicateur=NbConversions`)

- Idem : tableau avec les 3 lignes, graphique en barres avec les effectifs.

## Tests

Jeu de données synthétiques couvrant :
- Demande + Confirmation même personne → conversion.
- Demande sans Confirmation → pas de conversion.
- Confirmation sans demande préalable → pas de conversion (la personne n'est pas dans les demandeurs).
- Plusieurs demandes même personne → 1 demandeur, 1 conversion max.
- Décomposition client / prospect selon le statut du premier événement de demande.
- Division par zéro : aucune demande → taux `None` ; statut sans demande → composante `None`.
- Période filtrée : seules les demandes et confirmations dans la période comptent.

## Fichiers impactés

| Fichier | Changement |
|---|---|
| `src/kpi/kpi/indicateurs.py` | +2 classes, +1 fonction utilitaire, registre mis à jour |
| `src/kpi/web/routes.py` | ajustement `_construire_tableau_de_bord` pour le taux global en % |
| `src/kpi/web/gabarits/kpi.html` | ajustement affichage tableau 1 dimension avec dépliement + graphique barres 3 catégories |
| `tests/test_calculs_kpi.py` | +2 classes de tests |
