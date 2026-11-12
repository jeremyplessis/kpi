# Guide : import initial du classeur KPI.xlsx

Ce document décrit l'outil qui reprend les données déjà saisies dans le
classeur Excel d'origine, afin que la base de données de l'application ne
soit pas vide lors des tests utilisateurs.

## Ce que fait l'import

L'outil lit le classeur `KPI.xlsx` et alimente la base SQLite :

| Onglet lu | Ce qui est importé |
|---|---|
| `Listes` | les valeurs des listes déroulantes (référentiels) |
| `Suivi` | les événements du suivi d'activité (une ligne = un événement) |
| `Google Analytics` | les relevés mensuels : visiteurs, canaux, requêtes |

Les onglets `Feuil1` et `Données` sont ignorés. L'onglet `Données KPI`
n'est pas importé : ses règles de calcul sont désormais portées par le code
de l'application (voir `01_proposition_architecture.md`).

Points importants :

- les colonnes `Année` et `Mois` du suivi ne sont pas importées : seule la
  date fait foi (l'application les déduit automatiquement) ;
- une valeur absente des listes (par exemple une action saisie librement)
  est ajoutée au référentiel plutôt que perdue ;
- les dates manifestement erronées (par exemple une ligne datée de 2009)
  sont conservées telles quelles et signalées par un avertissement ;
- les relevés GA d'un mois déjà en base sont remplacés, jamais cumulés :
  relancer l'import ne crée pas de doublons.

## Utilisation

Après avoir préparé l'environnement (voir le `README.md` : création d'un
environnement virtuel puis `pip install -e .`), depuis la racine du
projet, avec Python 3.14 ou plus récent :

```bash
python3 -m outils.import_initial chemin/vers/KPI.xlsx [chemin/base.sqlite3]
```

Si le chemin de la base n'est pas précisé, le fichier `kpi.sqlite3` est
créé (ou complété) dans le dossier courant.

L'import affiche un bilan : nombre de référentiels et de personnes créés,
nombre d'événements importés, relevés GA et avertissements éventuels.

### Relancer l'import

Par prudence, l'outil refuse d'importer deux fois dans une base qui
contient déjà un suivi. Pour vider puis réimporter :

```bash
python3 -m outils.import_initial chemin/vers/KPI.xlsx base.sqlite3 --force
```

Attention : `--force` supprime les événements de suivi présents dans la
base avant de réimporter le classeur. À n'utiliser que pour repartir du
classeur d'origine.

## Tests automatisés

Les tests de cette étape se lancent avec la bibliothèque standard :

```bash
python3 -m unittest discover -s tests
```

Trois familles de tests sont couvertes :

- `test_bdd.py` : création de la base, référentiels, suivi, relevés GA ;
- `test_calculs_kpi.py` : règles de calcul des indicateurs sur un jeu de
  données anonyme ;
- `test_import_excel.py` : import complet d'un classeur synthétique,
  protection contre les doublons.

Les tests n'utilisent que des données anonymes : aucune donnée réelle de
clientèle n'est versionnée dans le dépôt.
