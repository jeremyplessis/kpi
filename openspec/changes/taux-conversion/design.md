# Design: Indicateurs de conversion (nombre et taux)

## Context

Le moteur d'indicateurs (`src/kpi/kpi/indicateurs.py`) fonctionne sur le modèle suivant :

- Chaque indicateur hérite de `Indicateur` et implémente `calculer(_evenements) -> list[LigneIndicateur]`.
- `LigneIndicateur` est un `NamedTuple(dimensions: tuple, valeur: float)`.
- Les indicateurs sont enregistrés dans `REGISTRE_INDICATEURS` et consommés par la route `/kpi` (`page_kpi` dans `routes.py`).
- Le tableau de bord (`_construire_tableau_de_bord`) agrège chaque indicateur pour afficher une carte de synthèse avec un total et un sparkline.

Les règles métier validées (28/10/2026) définissent déjà :
- **Demande** : `action_public ∈ {"Demande", "Réservation"}`
- **Dédoublonnage** : une personne = une demande par mois max

## Architecture des nouveaux indicateurs

### NbConversions

```
class NbConversions(Indicateur):
    libelle = "Nombre de conversions"
    dimensions = ("année", "mois", "canal")
```

**Algorithme** :

1. Parcourir les événements triés par date croissante.
2. Pour chaque personne, détecter la première transition prospect → client :
   - Garder en mémoire les personnes vues comme « prospect ».
   - Dès qu'un événement a `statut_contact == "client"` pour une personne connue comme prospect (ou même inconnue — arrivée directe), enregistrer la conversion.
3. La conversion est attribuée à :
   - **année/mois** : ceux du premier événement « client » de la personne.
   - **canal** : celui du **premier événement** de la personne (canal d'acquisition).
4. Agréger par (année, mois, canal) et retourner les `LigneIndicateur`.

**Détection de la première conversion** :

```python
_vus_comme_prospect: set[str] = set()
_premier_canal: dict[str, str] = {}  # personne -> canal du premier événement
_conversion_deja_comptee: set[str] = set()

for _ev in sorted(evenements, key=lambda e: e.date):
    if _ev.personne not in _premier_canal:
        _premier_canal[_ev.personne] = _ev.canal or "(vide)"
    if _ev.statut_contact == "prospect":
        _vus_comme_prospect.add(_ev.personne)
    if (_ev.statut_contact == "client"
        and _ev.personne not in _conversion_deja_comptee
        and (_ev.personne in _vus_comme_prospect or True)):  # arrivée directe = conversion aussi
        _conversion_deja_comptee.add(_ev.personne)
        _cle = (_ev.annee, _ev.mois, _premier_canal[_ev.personne])
        _comptes[_cle] += 1
```

### TauxConversion

```
class TauxConversion(Indicateur):
    libelle = "Taux de conversion"
    dimensions = ("année", "mois", "canal")
```

**Algorithme** :

1. Calculer les conversions par (année, mois, canal) — même logique que `NbConversions`.
2. Calculer les demandes par (année, mois, canal) — même logique que `NbDemandes` (dédoublonnage par personne/mois).
3. Pour chaque clé (année, mois, canal) présente dans les demandes :
   - `taux = conversions[cle] / demandes[cle]` si demandes > 0, sinon la ligne est omise.
4. Retourner les `LigneIndicateur` avec le taux (entre 0 et 1).

**Méthode utilitaire partagée** : extraire la logique de détection des conversions dans une fonction privée `_detecter_conversions(_evenements) -> dict[tuple, int]` réutilisée par les deux indicateurs.

## Intégration web

### Tableau de bord (`_construire_tableau_de_bord`)

Actuellement, le total d'un pourcentage (`TauxGhosting`) est la **moyenne des valeurs mensuelles**. Pour `TauxConversion`, le total doit être le **ratio global** : somme des conversions / somme des demandes sur la période, pas la moyenne des taux mensuels. Cela évite le biais de Simpson.

Modification : détecter `TauxConversion` comme pourcentage spécial avec calcul du ratio global.

### Page indicateur (`/kpi?indicateur=TauxConversion`)

Même affichage que les autres indicateurs à 3 dimensions : tableau dépliable année → mois → canal, plus graphique Chart.js en courbes.

### Page dédiée ?

Pas de page dédiée comme pour le ghosting (qui a un détail demandes/réponses). Le taux de conversion se suffit du tableau + graphique standard.

## Tests

Jeu de données synthétiques couvrant :
- Conversion simple (prospect → client le mois suivant).
- Arrivée directe en client (sans statut prospect préalable).
- Personne jamais convertie (reste prospect).
- Dédoublonnage : une personne = une conversion max.
- Canal d'acquisition = canal du premier contact, pas de la conversion.
- Taux = conversions / demandes par canal.
- Division par zéro (canal avec demandes mais 0 conversion → taux 0 ; canal sans demande → pas de ligne).

## Fichiers impactés

| Fichier | Changement |
|---|---|
| `src/kpi/kpi/indicateurs.py` | +2 classes, +1 fonction utilitaire, registre mis à jour |
| `src/kpi/web/routes.py` | ajustement `_construire_tableau_de_bord` pour le ratio global du taux |
| `tests/test_calculs_kpi.py` | +2 classes de tests |
