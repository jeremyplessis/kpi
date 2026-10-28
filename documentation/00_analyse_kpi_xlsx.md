# Analyse du classeur KPI.xlsx

Ce document synthétise l'analyse du classeur `KPI.xlsx`, point de départ de l'application.
Il sert de référence pour garantir que l'application restitue fidèlement les indicateurs
actuellement calculés dans Excel.

## Vue d'ensemble des onglets

| Onglet | Rôle | Statut dans l'application |
|---|---|---|
| `Feuil1` | (sans objet) | Ignoré |
| `Listes` | Paramétrage des valeurs des listes déroulantes | À reprendre en tables de référence |
| `Données` | (sans objet) | Ignoré |
| `Google Analytics` | Relevé manuel des données GA (visiteurs, canaux, requêtes) | À reprendre en tables, puis à automatiser |
| `KPI` | Tableaux croisés dynamiques (les indicateurs) | À recalculer en Python |
| `Données KPI` | Structures intermédiaires alimentant les TCD | Devient du code Python (pas des tables) |
| `Suivi` | Saisie du suivi d'activité | À reprendre en table principale |

## Onglet `Listes` : les référentiels

L'onglet contient les listes de valeurs autorisées pour les listes déroulantes de `Suivi` :

| Liste | Valeurs |
|---|---|
| Canal | formulaire de contact, instagram, mail, téléphone, whatsapp, sms, calendly, mariages.net, studio, réservation site, réservation en ligne, formulaire + insta, autre |
| Provenance | Google, Instagram, FB, Bouche à oreille, Prestataires, photographe, Galerie/Expo, exposition, Crèche ?, fourmillart, autre |
| Contact | client, prospect |
| Prestation | Mariage, Séances, Carte cadeau, Identité, Fêtes, EVJF, autre |
| DetailPrestation | Famille, Grossesse, Nouveau-né, Portrait, EVJF, Couple, Baptême, Duo, Mariage, autre |
| Action public | -, Confirmation, Demande, Devis, Échanges, Ghost, Lien de réservation, Non disponible, Paiement, RDV, Refus, Relance, Réponse, Réservation, Signature |
| Action photographe | Oui, Non (conversion) ; RDV, Réponse, Relance |
| Personne | liste des noms déjà contactés |

Remarques :

- `Canal` et `Canal2` (canal de l'action du photographe) utilisent la même liste de valeurs.
- La liste `Action photographe` mélange en réalité deux usages (état de la conversion et
  type d'action menée) : à clarifier.
- La liste `Personne` est un simple miroir des noms déjà saisis : ce n'est pas un
  référentiel à saisir manuellement.

## Onglet `Suivi` : la saisie d'activité

14 colonnes, environ 150 lignes saisies de janvier 2025 à octobre 2026 :

| Colonne | Contenu | Observations |
|---|---|---|
| Année | 2025, 2026 (et une ligne 2009 : probable erreur de saisie) | Dérivable de la date |
| Mois | janvier … décembre | Dérivable de la date |
| Date | date de l'événement | |
| Nom | personne concernée | Parfois un numéro de téléphone, un prénom seul |
| Contact | prospect / client / vide | |
| Action public | Demande, Paiement, RDV, Relance, Refus, Réservation… | Peut être vide |
| Canal | canal entrant | |
| Provenance | origine | |
| Type | prestation | |
| Séances | détail de la prestation | |
| Action photographe | Réponse, Relance, RDV, Devis, Confirmation… | |
| Canal2 | canal utilisé par le photographe | |
| Commentaire | texte libre | |

Une ligne = un événement du parcours d'une personne (demande, réponse, RDV, devis,
paiement…). Une même personne apparaît donc sur plusieurs lignes au fil de son parcours.

Anomalies relevées à traiter lors de l'import :

- une ligne datée de 2009 (année manifestement erronée) ;
- des incohérences de casse (`cecile plessis` / `cécile plessis` dans GA) ;
- la colonne `Année`/`Mois` redondante avec `Date` : l'application les déduira de la date.

## Onglet `Google Analytics`

Relevé manuel, par année (2025, 2026), avec trois blocs en colonnes mensuelles (janvier à
décembre) :

- `Nb de visiteurs` : visiteurs mensuels du site ;
- `Canaux` : répartition des visiteurs par canal (Direct, Organic Search, Organic Social,
  Referral, Unassigned, AI assistant) ;
- `Requêtes` : requêtes de recherche ayant amené des visiteurs, avec leur nombre.

L'actualisation est aujourd'hui manuelle : la structure est simple (année, mois, valeur)
et donc directement transposable en tables, puis alimentable par l'API GA4.

## Onglet `KPI` : les indicateurs existants

Six tableaux croisés dynamiques, dont deux en cours de construction :

| Indicateur | Source | Regroupement | Mesure | État |
|---|---|---|---|---|
| Nombre de visiteurs Google Analytics | (à venir) | | | En construction |
| Nombre de prospects | lignes `Contact = prospect` | Année > Mois > Canal | nombre de lignes | Complet |
| Nombre de demandes | lignes `Action public = Demande` | Année > Mois > Canal | nombre de lignes | Complet |
| Taux de ghosting | demandes et réponses par mois | Année > Mois | sommes de Demandes, Réponses et taux | Complet |
| RDV par canal | lignes `Action photographe = RDV` | Année > Canal2 | nombre de lignes | Complet |
| Nombre de conversions | (à venir) | | | En construction |

## Onglet `Données KPI` : les règles de calcul

L'onglet contient les structures intermédiaires alimentant les TCD. Ce sont elles qui
portent les règles métier, à réimplémenter en Python :

1. `Nb prospects` : lignes du suivi où `Contact = prospect`, avec Année, Mois, Date, Nom,
   Canal ;
2. `Nb demandes` : lignes où `Action public = Demande`, avec Année, Mois, Nom, Canal,
   Séances ;
3. `Contacts ayant répondus` : lignes où `Action photographe = Réponse` (approximation
   actuelle de la notion de « réponse du contact ») ;
4. `Demandes par année, mois` : comptage des demandes par période ;
5. `Réponses par année, mois` : comptage des réponses par période ;
6. `Taux de ghosting par année, mois` : pour chaque période,
   - `Demandes` = nombre de demandes,
   - `Réponses` = nombre de réponses,
   - `Tx Ghosting Brut` = (Demandes − Réponses) / Demandes,
   - `Taux Ghosting` = maximum(0, Tx Ghosting Brut) : le taux ne peut pas être négatif ;
7. `RDV par année, canal` : lignes où `Action photographe = RDV`, groupées par Année et
   Canal2.

Principe structurant : ces structures intermédiaires ne deviennent **pas** des tables
en base. Elles correspondent à des règles de calcul, donc à du code Python, éventuellement
mises en cache. Seules les données saisies et les relevés GA sont stockées.

## Valeurs témoins pour les tests

L'application devra reproduire les valeurs actuellement calculées (points de contrôle
pour les tests automatisés) :

- Nombre de prospects : 43 en 2025, 48 en 2026, total 91 ;
- Nombre de demandes : 91 au total ;
- Taux de ghosting global : 98 demandes, 62 réponses, taux 36,7 % ;
- RDV par canal : 28 au total (dont téléphone 15, mail 7, studio 3).

Ces valeurs seront figées dans des jeux de tests, en anonymisant les noms de personnes.
