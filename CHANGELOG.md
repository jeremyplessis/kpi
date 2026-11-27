# 📜 CHANGELOG - KPI

*Outil de saisie d'activité et de restitution des KPI pour entrepreneurs individuels*

Ce fichier retrace les évolutions du projet **KPI** de manière claire et accessible.
Chaque version est documentée avec ses principales fonctionnalités, corrections et améliorations.

---

## 🔜 **À venir** *(Next Release)*

### 🐛 Corrections de bugs

- **Filtres « Toutes les années » / « Tous les mois » enfin pris en compte** : Sur l'écran KPI, les sélectionner puis cliquer sur « Appliquer les filtres » affichait toute la plage de vos données 🐞
  *Auparavant, ce clic ramenait à la période par défaut des 12 derniers mois, comme si aucun filtre n'avait été choisi. Désormais, seuls un écran ouvert sans filtre ou le lien « Effacer les filtres » appliquent ces 12 derniers mois ; « Toutes les années » / « Tous les mois » couvrent bien du mois le plus ancien au mois le plus récent de votre suivi, et les indicateurs sont recalculés sur cette période complète*

---

## 🎉 **0.0.9** *(26 novembre 2026)*

### ✨ Nouveautés

- **Lien vers l'historique des changements** : Le mot « changements », affiché après le numéro de version dans l'en-tête (ex. « v0.0.8 - changements »), ouvre le fichier `CHANGELOG.md` de la branche en cours sur GitHub dans un nouvel onglet 🌐
  *Exemple : `https://github.com/jeremyplessis/kpi/blob/main/CHANGELOG.md`. Un clic suffit pour savoir ce qui a changé dans la version que vous utilisez, sans quitter l'application*

### 🛠️ Améliorations techniques

- **Ordre de saisie enregistré pour chaque ligne** : Chaque événement du suivi mémorise désormais son rang de saisie (`ordre_saisie`), incrémenté à chaque nouvel enregistrement 💾
  *Ce rang permet de reconstituer l'ordre chronologique exact des saisies, même quand plusieurs événements partagent la même date. Il sert de dernier critère de tri (décroissant) dans le tableau des résultats de l'écran de saisie, sans y apparaître. Les données existantes sont reprises automatiquement : à l'import, l'ordre des lignes du classeur fait foi, et les bases déjà constituées sont migrées à l'ouverture*

---

## 🎉 **0.0.8** *(26 novembre 2026)*

### 🐛 Corrections de bugs

- **Taux de conversion regroupé par statut enfin juste** : Sur l'écran KPI, les lignes « Tous », « client » et « prospect » du tableau dépliable affichaient la somme des taux par canal — jusqu'à 517,9 %, un chiffre sans aucun sens pour un pourcentage 🐞
  *Le taux de chaque regroupement est désormais recalculé depuis les compteurs : confirmations ÷ demandes ouvertes. Exemple avec les données actuelles : prospect à 39,8 % (39 confirmations sur 98 demandes), client à 100 % (7/7), « Tous » à 43,8 % (46/105). La carte de synthèse du tableau de bord affiche elle aussi ce vrai taux global, et non plus une moyenne des taux par canal*

---

## 🎉 **0.0.7** *(25 novembre 2026)*

### 🐛 Corrections de bugs

- **Tableau du taux de ghosting enfin rempli** : Sur l'écran KPI, l'indicateur « Taux de ghosting » affichait un tableau vide alors que son graphique, lui, fonctionnait 🐞
  *Une variable JavaScript manquait dans le script qui construit le tableau : celui-ci ne se remplissait jamais. Le détail mensuel (année, mois, demandes, réponses, taux) s'affiche à nouveau, repliable par année*

- **Taux de ghosting annuel corrigé** : La ligne de l'année n'est plus la somme des taux mensuels, mais le vrai taux calculé sur toute l'année 🧮
  *Exemple : janvier à 50 % et février à 0 % donnent une année à 33,3 % ((3 demandes − 2 réponses) / 3), et non 50 %. Et une année sans aucune demande restée sans réponse affiche désormais « 0,0 % » au lieu de « NaN% »*

---

## 🎉 **0.0.6** *(24 novembre 2026)*

### ✨ Nouveautés

- **Indicateurs de conversion** : Deux nouveaux indicateurs sur l'écran KPI mesurent la conversion des demandes en séances 🧮
  *« Nombre de conversions » compte les confirmations du photographe ; « Taux de conversion » affiche le pourcentage de demandes ouvertes converties, avec détail par statut (client/prospect) et par canal (mail, téléphone, formulaire…) — les canaux à 0 % sont masqués*

- **Filtres par défaut sur 12 mois glissants** : À l'ouverture de l'écran KPI, la période est automatiquement pré-remplie sur les 12 derniers mois 🌐
  *Fini d'avoir à régler les dates à chaque visite : l'écran affiche directement l'année en cours. Le lien « Effacer les filtres » revient à ces 12 derniers mois*

### 🐛 Corrections de bugs

- **Plantage du taux de conversion sur année seule** : Filtrer sur une année sans préciser de mois ne fait plus planter l'application 🐞
  *Le mois par défaut est désormais janvier pour le début et décembre pour la fin de période*

---

## 🎉 **0.0.5** *(22 novembre 2026)*

### 🛠️ Améliorations techniques

- **Mise à jour automatique du lanceur macOS** : `KPI.command` met à jour tout seul le code et les dépendances au lancement 🍎
  *Si le projet a évolué sur GitHub, un `git pull` est effectué automatiquement ; si `pyproject.toml` a changé, les dépendances sont réinstallées dans l'environnement virtuel. En cas de souci (hors ligne, modifications locales), un message s'affiche mais l'application se lance quand même avec le code actuel — désactivable avec `KPI_SANS_MISE_A_JOUR=1`*

---

## 🎉 **0.0.4** *(19 novembre 2026)*

### ✨ Nouveautés

- **Charte graphique de Cécile Plessis Photographe** : L'application adopte l'identité visuelle officielle 🌐
  *Palette beige/sapin, titres en serif expressif, pictogramme en favicon et logo en pied de page, graphiques KPI dans les couleurs de la marque, motif papier millimétré en arrière-plan subtil*

### 🛠️ Améliorations

- **Graphiques en courbe pour prospects et demandes** : Les indicateurs « Nombre de prospects » et « Nombre de demandes » s'affichent désormais en courbe 📈
  *En abscisse les couples année/mois, en ordonnée le total tous canaux confondus — la tendance se lit d'un coup d'œil, comme pour le taux de ghosting*

### 🐛 Corrections de bugs

- **Visualisation graphique vide** : La section « Visualisation graphique » ne s'affichait plus pour les indicateurs à plusieurs dimensions 🐞
  *Une erreur JavaScript (variables redéclarées dans la boucle de génération) empêchait le graphique de se dessiner ; le tableau, lui, restait correct*

---

## 🎉 **0.0.3** *(16 novembre 2026)*

### ✨ Nouveautés

- **Écran de consultation des KPI** : Un nouveau tableau de bord accessible depuis le menu « KPI » 🧮
  *Tous vos indicateurs réunis au même endroit : cartes de synthèse avec évolution mensuelle, filtres par période (année et mois), et page détaillée par indicateur avec graphiques interactifs*

### 🛠️ Améliorations

- **Commentaire complet dans la liste** : La colonne commentaire n'est plus tronquée 📝
  *Le texte revient à la ligne automatiquement (mots longs compris) et une infobulle affiche le commentaire intégral au survol de la souris*
- **Liste paginée** : Les derniers événements s'affichent par pages de 10 📄
  *Liens « Précédent » / « Suivant » en dessous du tableau ; les filtres et le tri actifs sont conservés entre les pages*
- **Formulaire repliable** : Le volet « Nouvel événement » est masqué par défaut 🌐
  *Toute la largeur est consacrée à la liste ; cliquez sur « + Ajouter un événement » pour afficher le formulaire, sur « Fermer » (à côté du titre) pour le replier*

### 📚 Documentation

- **Guide de l'écran de saisie** : Mis à jour pour décrire la pagination, le formulaire repliable et l'infobulle de commentaire 📖

---

## 🎉 **0.0.2** *(15 novembre 2026)*

### ✨ Nouveautés

- **Lanceur macOS** : Ajout d'un script **`KPI.command`** pour lancer l'application directement depuis le Finder 🍎
  *Double-cliquez, l'environnement virtuel est créé automatiquement si nécessaire, et l'application démarre dans Terminal*

- **Affichage de la version** : Ajout de l'option `-v` / `--version` pour connaître la version exacte de l'application en cours d'exécution 📋
  *Exemple : `kpi version 0.0.2` ou `kpi version 0.0.2.post1+dirty` selon votre position dans le dépôt*

- **Gestion automatique des versions** : La version est désormais déterminée automatiquement depuis les tags Git 🏷️
  *Plus besoin de mettre à jour manuellement le numéro de version !*

### 🛠️ Améliorations techniques

- Ajout de **setuptools-scm** comme dépendance pour une gestion robuste des versions à partir des tags Git 🔧
- Configuration des schémas de version (`post-release`, `dirty-tag`) pour un affichage clair et informatif 📊

---

## 🎉 **0.0.1** *(28 octobre 2026)*

### ✨ Premier lancement !

Bienvenue à la première version stable de **KPI** ! Cette version pose les bases de votre outil de suivi d'activité.

### 🏗️ Fonctionnalités de base

- **Base de données SQLite** : Stockage local de toutes vos données dans un simple fichier `kpi.sqlite3` 💾
  *Sauvegardez, copiez, partagez votre fichier : c'est votre base de données complète !*

- **Import du classeur existant** : Récupération de toutes vos données depuis le classeur Excel d'origine 📥
  *Plus besoin de ressaisir vos historiques !*

- **Moteur de calcul des KPI** : Calcul automatique des indicateurs clés selon vos règles métiers 🧮
  - Nombre de prospects
  - Nombre de demandes  
  - Taux de ghosting
  - RDV par canal

- **Écran de saisie web** : Interface conviviale accessible depuis votre navigateur 🌐
  *Saisie rapide, pré-remplissage intelligent, gestion des listes déroulantes*

### 📊 Indicateurs disponibles

| Indicateur | Description | Utilité |
|------------|-------------|---------|
| 📈 Nombre de prospects | Contacts suivis par mois et canal | Suivre votre pipeline |
| 📞 Nombre de demandes | Demandes reçues (dédoublonnées) | Mesurer l'intérêt |
| 👻 Taux de ghosting | Demandes sans réponse | Optimiser votre suivi |
| 📅 RDV par canal | Rendez-vous obtenus | Évaluer vos canaux |

### 🔧 Configuration requise

- Python 3.13 ou plus récent
- Environnement virtuel recommandé

---

## 📖 **Guide de lecture**

### 🏷️ Format des versions

Les versions de KPI suivent le format **`X.Y.Z`** où :
- **X** : Version majeure (changements importants, incompatibilités)
- **Y** : Version mineure (nouvelles fonctionnalités)
- **Z** : Version de correction (bug fixes)

En mode développement, vous verrez des versions comme :
- `0.0.1` → Version exacte du tag
- `0.0.1.post7` → 7 commits après le tag 0.0.1
- `0.0.1.post7+dirty` → 7 commits après + modifications non commitées

### 💡 Symboles utilisés

| Symbole | Signification |
|--------|---------------|
| ✨ | Nouvelle fonctionnalité |
| 🛠️ | Amélioration technique |
| 🐛 | Correction de bug |
| 📚 | Documentation |
| 🔧 | Configuration/Outils |
| 🎉 | Version majeure/Release |

---

## 📌 **Feuille de route**

| Étape | Fonctionnalité | Statut | Version prévue |
|-------|---------------|--------|----------------|
| 1 | Base SQLite + Import | ✅ Terminé | 0.0.1 |
| 2 | Moteur de calcul KPI | ✅ Terminé | 0.0.1 |
| 3 | Écran de saisie | ✅ Terminé | 0.0.1 |
| 4 | Lanceur macOS + gestion des versions | ✅ Terminé | 0.0.2 |
| 5 | Écrans de consultation + Export PDF | 🚧 Consultation livrée en 0.0.3, PDF à venir | 0.0.3 |
| 6 | Connecteur Google Analytics 4 | ⏳ À venir | 0.1.0 |
| 7 | Indicateurs reportés (visiteurs GA, conversions) | ⏳ À venir | 0.1.0 |

---

*💬 Besoin d'aide ou d'éclaircissements ? Consultez la [documentation](documentation/) ou le [README](README.md).*
