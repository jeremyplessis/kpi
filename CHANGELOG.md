# 📜 CHANGELOG - KPI

*Outil de saisie d'activité et de restitution des KPI pour entrepreneurs individuels*

Ce fichier retrace les évolutions du projet **KPI** de manière claire et accessible.
Chaque version est documentée avec ses principales fonctionnalités, corrections et améliorations.

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
