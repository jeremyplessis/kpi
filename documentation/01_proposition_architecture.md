# Proposition d'architecture de l'application KPI

Proposition soumise à validation avant tout développement. L'objectif : une application
autonome, simple, qui remplace le classeur `KPI.xlsx` pour l'activité
Cécile Plessis Photographe.

## Choix techniques proposés

| Composant | Choix proposé | Pourquoi |
|---|---|---|
| Langage | Python 3.14 | Conforme au projet |
| Base de données | SQLite (fichier unique `kpi.sqlite3`) | Aucun serveur, sauvegarde = copie de fichier, embarquée dans Python |
| Interface | Application web locale (FastAPI + Jinja2 + HTMX) | Interface conviviale et moderne, aucune installation côté utilisatrice, PDF et graphiques faciles |
| PDF | WeasyPrint (rendu HTML vers PDF) | Les écrans et les PDF partagent les mêmes gabarits ; mise en page riche |
| Graphiques | Chart.js (écrans) | Interactif, léger |
| Google Analytics | API GA4 (bibliothèque `google-analytics-data`) | Standard, relevés mensuels automatisables |
| Tests | unittest (bibliothèque standard) | Conforme aux habitudes du projet |

### Pourquoi une application web locale plutôt qu'une application de bureau

Deux options étaient envisageables :

1. **Application de bureau** (PySide6/Qt ou Tkinter) : fenêtre native, mais interfaces
   moins souples pour des tableaux de bord, PDF et graphiques plus laborieux, look daté
   avec Tkinter.
2. **Application web locale** : l'application démarre un petit serveur sur l'ordinateur
   et s'utilise dans le navigateur (aucune connexion internet nécessaire). C'est le choix
   recommandé car la convivialité de la saisie et la richesse des écrans KPI
   (tableaux, graphiques, filtres, export PDF) y sont bien plus simples à obtenir.
   C'est aussi le plus évolutif si un jour l'outil doit devenir multi-entreprises ou
   accessible à distance.

Pour l'utilisatrice, le résultat concret : une icône « KPI » sur le bureau qui ouvre le
navigateur sur l'application. Un script de lancement (et éventuellement un service
système) masque totalement le serveur.

## Arborescence du projet

```
kpi/
├── documentation/               # Documentation utilisateur (au fil du développement)
│   ├── 00_analyse_kpi_xlsx.md
│   ├── 01_proposition_architecture.md   # ce document
│   └── …
├── src/
│   └── kpi/
│       ├── __init__.py
│       ├── app.py               # Point d'entrée : démarre le serveur et ouvre le navigateur
│       ├── bdd/
│       │   ├── __init__.py
│       │   ├── connexion.py     # Ouverture/initialisation de la base SQLite
│       │   └── modeles.py       # Classes d'accès aux données (pattern repository)
│       ├── referentiels.py      # Gestion des listes déroulantes
│       ├── suivi.py             # Saisie et consultation du suivi d'activité
│       ├── ga.py                # Import et relevés Google Analytics
│       ├── kpi/
│       │   ├── __init__.py
│       │   ├── base.py          # Classe de base des indicateurs
│       │   └── indicateurs.py    # Les indicateurs existants
│       ├── rapports.py          # Génération des PDF
│       └── web/
│           ├── __init__.py
│           ├── routes.py        # Définition des pages
│           └── gabarits/        # Templates HTML (Jinja2)
│               ├── base.html
│               ├── suivi_*.html
│               └── kpi_*.html
├── tests/
│   ├── test_import_excel.py    # Reprise des données du classeur
│   ├── test_calculs_kpi.py     # Fidélité aux valeurs du classeur
│   └── test_suivi.py           # Règles de saisie
├── outils/
│   └── import_initial.py       # Import du classeur KPI.xlsx (une fois)
├── README.md
└── pyproject.toml
```

## Modèle de données SQLite

### Tables de référence (issues de l'onglet `Listes`)

Chaque référentiel est éditable dans l'application (écran de paramétrage), avec une
colonne `actif` pour désactiver une valeur sans perdre l'historique.

| Table | Contenu |
|---|---|
| `canal` | formulaire de contact, instagram, mail, téléphone, whatsapp, sms, calendly, mariages.net, studio, réservation site, réservation en ligne, formulaire + insta, autre |
| `provenance` | Google, Instagram, FB, Bouche à oreille, Prestataires, photographe, Galerie/Expo, exposition, Crèche ?, fourmillart, autre |
| `statut_contact` | prospect, client |
| `prestation` | Mariage, Séances, Carte cadeau, Identité, Fêtes, EVJF, autre |
| `detail_prestation` | Famille, Grossesse, Nouveau-né, Portrait, EVJF, Couple, Baptême, Duo, Mariage, autre |
| `action_public` | Demande, Paiement, RDV, Relance, Refus, Réservation, … |
| `action_photographe` | Réponse, Relance, RDV, Devis, Confirmation, … |
| `personne` | Personnes créées automatiquement à la saisie (nom, téléphone éventuel, note) |

### Table principale

`suivi_activite` : un enregistrement = un événement du parcours d'une personne.

| Colonne | Type | Remarque |
|---|---|---|
| id | INTEGER PK | |
| date | DATE | obligatoire |
| personne_id | FK | obligatoire |
| statut_contact_id | FK | |
| action_public_id | FK | peut être vide |
| canal_id | FK | |
| provenance_id | FK | |
| prestation_id | FK | |
| detail_prestation_id | FK | |
| action_photographe_id | FK | |
| canal2_id | FK vers canal | |
| commentaire | TEXT | |

`Année` et `Mois` ne sont pas stockés : déduits de `date` par des vues ou lors des
calculs. Le suivi d'une entreprise est stocké tel quel ; l'ajout d'une colonne
`entreprise_id` plus tard est envisageable si l'outil doit suivre plusieurs activités.

### Tables Google Analytics

| Table | Clé | Contenu |
|---|---|---|
| `ga_visiteurs` | (annee, mois) | nombre de visiteurs du mois |
| `ga_canaux` | (annee, mois, canal) | visiteurs du mois par canal |
| `ga_requetes` | (annee, mois, requete) | occurrences de la requête |

Chaque relevé porte une date de mise à jour et une origine (`manuel` ou `api`), pour
recharger un mois sans créer de doublons.

### Ce qui n'est PAS en base

Les structures de l'onglet `Données KPI` (comptages, taux de ghosting…) ne sont pas des
données : ce sont des règles de calcul, donc du code Python. Elles seront recalculées
à la demande.

## Les indicateurs (KPI)

Chaque indicateur est une classe Python dérivant d'une classe de base commune :

```python
class Indicateur:
    """Classe de base de tous les indicateurs KPI."""

    libelle: str
    description: str

    def calculer(self, _debut: date, _fin: date) -> ResultatIndicateur:
        """Calcule l'indicateur sur la période donnée."""
        raise NotImplementedError
```

Les indicateurs existants (fidèles au classeur) :

| Indicateur | Règle |
|---|---|
| Nombre de prospects | lignes de suivi avec statut `prospect`, groupées par mois et canal |
| Nombre de demandes | lignes avec action public `Demande`, groupées par mois et canal |
| Taux de ghosting | par mois : (demandes − réponses) / demandes, borné à 0 |
| RDV par canal | lignes avec action photographe `RDV`, groupées par canal |
| Nombre de visiteurs GA | relevés de la table `ga_visiteurs` (à finaliser) |
| Nombre de conversions | à définir (voir question ouverte) |

L'ajout d'un nouvel indicateur = une nouvelle classe + un gabarit d'affichage : aucune
modification du reste de l'application. Les tests compareront systématiquement les
résultats aux valeurs témoins du classeur (91 prospects/demandes, taux de ghosting
36,7 %, 28 RDV).

## Parcours de saisie proposé

L'ordre actuel des colonnes Excel est perfectible. Proposition d'un formulaire
organisé en trois groupes logiques, pré-rempli et avec valeurs mémorisées :

1. **Qui et quand** : date (aujourd'hui par défaut), personne (recherche avec
   création à la volée, autocomplétion sur les noms existants), statut
   (prospect/client) ;
2. **La demande** : prestation, détail, action du public, canal entrant, provenance ;
3. **La réponse** : action du photographe, canal utilisé, commentaire.

Confort prévu : les listes déroulantes proposent les valeurs actives en premier,
recherche incrémentale sur les personnes, bouton « nouvelle ligne pour la même
personne » après enregistrement, correction immédiate d'une ligne récente.

## Écrans de restitution et export PDF

- Un écran « Tableau de bord » : sélecteur de période (année, mois, personnalisé),
  cartes de synthèse, tableaux et graphiques, un bloc par indicateur ;
- Un bouton « Exporter en PDF » sur chaque écran : le PDF reprend la période et les
  filtres affichés, avec tableaux et graphiques (rendu serveur) ;
- Le PDF est produit à partir des mêmes données que l'écran : aucune divergence
  possible entre ce qui est affiché et ce qui est exporté.

## Récupération automatique Google Analytics

Prévu dans un second temps, l'architecture le rend simple : les tables GA étant déjà en
base, un connecteur GA4 (compte de service Google, fichier de clé local) viendra
alimenter les mêmes tables via l'API `google-analytics-data`. Un écran permettra de
lancer une récupération manuelle et de voir la date du dernier relevé ; une exécution
mensuelle automatique pourra être ajoutée ensuite. La première année, l'import manuel
du classeur servira de relais.

## Feuille de route de développement

| Étape | Contenu | Tests associés |
|---|---|---|
| 1 | Socle : base SQLite, référentiels, import initial du classeur | import sans doublon, valeurs témoins |
| 2 | Moteur de calcul des KPI existants | fidélité aux valeurs du classeur (91, 36,7 %, 28) |
| 3 | Écran de saisie du suivi | validation des champs, création de personne |
| 4 | Écrans de consultation KPI + export PDF | rendu des périodes, contenu PDF |
| 5 | Connecteur GA4 | mois de test, idempotence des rechargements |
| 6 | Documentation utilisateur complète | revue de la documentation |

## Points à valider avant de démarrer

Voir les questions listées dans la discussion : type d'interface, définition des deux
indicateurs en construction, environnement d'utilisation de Cécile, et accès à la
propriété GA4.
