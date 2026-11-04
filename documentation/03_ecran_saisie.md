# Guide : l'écran de saisie du suivi

Ce document décrit l'écran web local qui remplace la saisie manuelle de
l'onglet `Suivi` du classeur d'origine. Il s'adresse à l'utilisatrice
quotidienne (Cécile) et ne suppose aucune connaissance technique.

## Démarrer l'application

Après avoir préparé l'environnement (voir le `README.md` : création d'un
environnement virtuel puis `pip install -e .`), depuis la racine du
projet :

```bash
.venv/bin/kpi
```

Le navigateur s'ouvre automatiquement sur l'écran de saisie. L'application
n'est accessible que depuis ce poste (adresse locale 127.0.0.1, port 8765
par défaut) : rien n'est exposé sur Internet.

Options utiles :

```bash
.venv/bin/kpi --sans-navigateur   # ne pas ouvrir le navigateur
.venv/bin/kpi --base essai.sqlite3   # travailler sur une autre base
.venv/bin/kpi --port 9000         # changer de port si 8765 est occupé
```

Si le port est déjà occupé (par exemple par une autre instance déjà
ouverte), l'application le signale au lieu de démarrer deux fois. Pour
arrêter l'application : `Ctrl+C` dans le terminal.

## L'écran de saisie

L'écran présente un formulaire en trois groupes, calqués sur le classeur
d'origine :

| Groupe | Champs |
|---|---|
| Qui et quand | date (pré-remplie avec le jour même), personne, statut |
| La demande | prestation, détail, action du contact, canal, provenance |
| La réponse de la photographe | action, canal de réponse, commentaire |

Points importants :

- **Personne** : le champ propose les noms déjà connus pendant la
  frappe ; un nom absent de la liste est créé automatiquement, aucune
  manipulation séparée n'est nécessaire ;
- **Listes déroulantes** : elles reprennent exactement les valeurs du
  classeur (issues de l'onglet `Listes`) ; une valeur saisie
  autrefois librement dans le classeur apparaît aussi dans la liste ;
- **Enregistrement** : après un enregistrement, le formulaire se
  réinitialise mais **garde le nom de la personne** : pour saisir
  plusieurs événements concernant le même contact, on enchaîne sans
  retaper le nom. Un lien « nouvelle personne » réinitialise ce nom ;
- **Validation** : si un champ obligatoire manque ou si la date est
  incorrecte, l'enregistrement est refusé avec un message explicatif et
  **la saisie est intégralement conservée** : rien n'est perdu, on
  corrige et on enregistre à nouveau.

## Les derniers événements

Sous le formulaire, le tableau « Derniers événements » affiche les
saisies les plus récentes. Sur petit écran (téléphone), le tableau se
parcourt horizontalement avec le doigt.

Chaque ligne offre deux actions :

- **Modifier** : ré-ouvre le formulaire pré-rempli avec les valeurs de
  l'événement, avec un bouton « Enregistrer la correction » ;
- **Supprimer** : affiche d'abord un écran de confirmation (date et
  personne concernées), car la suppression est définitive.

## Garanties et sécurité

- les données sont enregistrées dans le fichier `kpi.sqlite3` (à la
  racine du projet) au moment même de l'enregistrement : une coupure de
  courant ne perd pas une saisie validée ;
- l'application refuse les requêtes d'écriture provenant d'une page
  autre que l'écran lui-même (protection contre les soumissions
  croisées) ;
- les textes saisis (commentaires, noms) sont affichés tels quels sans
  jamais être interprétés comme du code ;
- une adresse d'événement inexistante (lien périmé) affiche une page
  « non trouvé » plutôt qu'une erreur brute.

## Tests associés

Les tests automatisés (`tests/test_web.py`, 13 tests) couvrent :
l'affichage de l'écran, l'enregistrement d'un événement complet, la
création automatique des personnes et des valeurs libres, le rejet et
la conservation de la saisie en cas d'erreur, le pré-remplissage du nom
après enregistrement, la correction par identifiant, l'écran de
confirmation de suppression, les pages introuvables (404), la protection
des requêtes croisées, l'échappement du HTML saisi et la réponse au
format texte. Ils nécessitent le paquet de développement `httpx`
(`.venv/bin/pip install -e ".[dev]"`).
