# Guide : l'écran de saisie du suivi

Ce document décrit l'écran web local qui remplace la saisie manuelle de
l'onglet `Suivi` du classeur d'origine. Il s'adresse à l'utilisatrice
quotidienne (Cécile) et ne suppose aucune connaissance technique.

## Installer l'application

### Création de l'environnement virtuel

Depuis le dossier du projet, exécutez les commandes suivantes dans un terminal :

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

L'environnement virtuel `.venv` est créé localement dans le projet. Le flag `-e .` installe le package en mode éditable, permettant de modifier le code source sans réinstaller.

### Installation dans l'environnement virtuel

Les dépendances suivantes sont automatiquement installées :
- `openpyxl` pour la lecture des fichiers Excel (import initial)
- `fastapi` et `uvicorn` pour le serveur web
- `jinja2` pour les templates
- `python-multipart` pour la gestion des formulaires

Pour installer les dépendances de développement (nécessaires aux tests) :

```bash
.venv/bin/pip install -e ".[dev]"
```

## Démarrer l'application

### Créer un script de lancement pour macOS

Pour lancer l'application directement depuis le Finder sans passer par un terminal manuellement, créez un fichier AppleScript :

1. Ouvrez **Script Editor** (dans `/Applications/Utilitaires/`)
2. Copiez-collez le code suivant :

```applescript
on run
    -- Obtenir le chemin du script AppleScript
    set scriptPath to POSIX path of (path to me)
    
    -- Obtenir le dossier parent (le projet KPI)
    set projectDir to do shell script "dirname " & quoted form of scriptPath
    
    -- Construire la commande shell à exécuter
    set shellScript to "
cd " & quoted form of projectDir & "
if [ ! -d .venv ]; then
    echo \"Création de l'environnement virtuel...\"
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e .
fi
.venv/bin/kpi
"
    
    -- Ouvrir Terminal et exécuter le script
    tell application "Terminal"
        activate
        do script shellScript
    end tell
end run
```

3. Sauvegardez le fichier comme **`KPI.scpt`** dans le dossier du projet
4. **Pour l'exécuter depuis le Finder** :
   - Faites un clic droit sur `KPI.scpt`
   - Sélectionnez **Ouvrir avec** → **Terminal**
   - Ou compilez-le en application via **Fichier** → **Exporter** → Format **Application**

**Alternative recommandée (plus simple)** : Créez un fichier `KPI.command` directement dans le dossier du projet :

1. Ouvrez **TextEdit** (ou un éditeur de texte)
2. Copiez-collez le code suivant :

```bash
#!/bin/bash

# Obtenir le dossier où se trouve ce script
cd "$(dirname "$0")"

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d .venv ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e .
fi

# Lancer l'application KPI
.venv/bin/kpi

# Garder le terminal ouvert après la fermeture de l'application
echo ""
echo "Appuyez sur Entrée pour fermer cette fenêtre..."
read
```

3. Sauvegardez le fichier comme **`KPI.command`** dans le dossier du projet
4. Rendez-le exécutable via le terminal :

```bash
chmod +x KPI.command
```

5. Double-cliquez sur `KPI.command` depuis le Finder : il s'ouvre dans Terminal et lance l'application

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

L'écran se présente en deux colonnes : le formulaire de saisie à
gauche, la liste des derniers événements à droite (les deux se
superposent sur petit écran). Le formulaire est organisé en trois
groupes, calqués sur le classeur d'origine :

| Groupe | Champs |
|---|---|
| Qui et quand | date (pré-remplie avec le jour même), personne, statut |
| La demande | prestation, détail, action du contact, canal, provenance |
| La réponse de la photographe | action, canal de réponse, commentaire |

Points importants :

- **Personne** : le champ propose les noms déjà connus pendant la
  frappe ; un nom absent de la liste est créé automatiquement, aucune
  manipulation séparée n'est nécessaire ;
- **Listes déroulantes** : elles reprennent les valeurs du classeur
  (issues de l'onglet `Listes`) ; une valeur saisie autrefois
  librement dans le classeur apparaît aussi dans la liste ; elles sont
  modifiables à tout moment (voir « Paramétrer les listes » ci-dessous) ;
- **Enregistrement** : après un enregistrement, le formulaire se
  réinitialise mais **garde le nom de la personne** : pour saisir
  plusieurs événements concernant le même contact, on enchaîne sans
  retaper le nom. Un lien « nouvelle personne » réinitialise ce nom ;
- **Validation** : si un champ obligatoire manque ou si la date est
  incorrecte, l'enregistrement est refusé avec un message explicatif et
  **la saisie est intégralement conservée** : rien n'est perdu, on
  corrige et on enregistre à nouveau.

## Les derniers événements

À droite du formulaire, le tableau « Derniers événements » affiche les
interactions les plus récentes **en premier** : c'est le tri par défaut,
par date d'interaction décroissante. Sur petit écran (téléphone), le
tableau se parcourt horizontalement avec le doigt.

Chaque ligne propose, en première colonne à gauche :

- **Modifier** : ré-ouvre le formulaire pré-rempli avec les valeurs de
  l'événement, avec un bouton « Enregistrer la correction » ;
- **Supprimer** : affiche d'abord un écran de confirmation (date et
  personne concernées), car la suppression est définitive.

### Filtrer et trier

- une barre de filtres au-dessus du tableau permet de ne garder que les
  lignes correspondant à un texte : personne, statut, action du
  contact, canal, réponse de la photographe, commentaire. La recherche
  ne tient pas compte de la casse et porte sur un extrait du texte ;
  plusieurs filtres se combinent ; le lien « Effacer les filtres »
  remet la liste à plat ;
- chaque en-tête de colonne est un lien de tri : cliquer une fois trie
  par ordre croissant, cliquer à nouveau inverse le sens (une flèche
  ▲ ou ▼ indique le tri actif). Les filtres restent actifs quand on
  change de tri, et inversement.

## Paramétrer les listes

La page « Listes » (lien dans le bandeau en haut à droite, ou « Gérer
les listes » sous le formulaire) permet de maintenir les valeurs des
listes déroulantes : statuts, prestations, détails, actions, canaux,
provenances.

- **Ajouter** : la valeur apparaît immédiatement dans les listes du
  formulaire ;
- **Renommer** : la nouvelle valeur remplace l'ancienne partout, y
  compris dans les événements déjà enregistrés (pratique pour corriger
  une faute de frappe) ;
- **Retirer** : la valeur disparaît des listes, mais **les événements
  qui l'utilisent conservent leur contenu** — la page indique
  combien d'événements sont concernés. Ré-ajouter plus tard le même nom
  remet la valeur dans la liste.

Chaque valeur affiche le nombre d'événements qui l'utilisent, pour
décider en connaissance de cause.

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

Les tests automatisés (`tests/test_web.py`, 31 tests) couvrent :
l'affichage de l'écran, l'enregistrement d'un événement complet, la
création automatique des personnes et des valeurs libres, le rejet et
la conservation de la saisie en cas d'erreur, le pré-remplissage du nom
après enregistrement, la correction par identifiant, l'écran de
confirmation de suppression, les pages introuvables (404), la protection
des requêtes croisées, l'échappement du HTML saisi, le tri par défaut
par date décroissante, les tris et filtres par colonne, la gestion des
listes (ajout, renommage suivi par les événements, retrait sans perte,
réactivation). Ils nécessitent le paquet de développement `httpx`
(`.venv/bin/pip install -e ".[dev]"`).
