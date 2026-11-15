---
name: changelog-kpi
description: Skill dédiée à la rédaction et mise à jour du fichier CHANGELOG.md pour le projet KPI, avec un format orienté utilisateur, des émoticônes et un ton didactique.
permissions: []
---

# Skill : Gestion du CHANGELOG pour le projet KPI

Cette skill te guide pour **rédaction et la mise à jour** du fichier `CHANGELOG.md` du projet KPI, en respectant les conventions du projet : orientation utilisateur, ton didactique et utilisation d'émoticônes.

## Contexte du projet

Le projet KPI utilise un **CHANGELOG orienté utilisateur** avec :
- Des **émoticônes** pour une lecture visuelle et agréable
- Un **ton didactique** expliquant clairement les évolutions
- Une **structure claire** par version
- Des **exemples concrets** pour chaque fonctionnalité

## Quand mettre à jour le CHANGELOG ?

Mets à jour le CHANGELOG **dans les cas suivants** :

| Situation | Action | Section concernée |
|-----------|--------|-------------------|
| Nouvelle fonctionnalité | Ajouter une entrée sous ✨ Nouveautés | **À venir** ou version future |
| Correction de bug | Ajouter une entrée sous 🐛 Corrections | **À venir** ou version future |
| Amélioration technique | Ajouter une entrée sous 🛠️ Améliorations | **À venir** ou version future |
| Documentation mise à jour | Ajouter une entrée sous 📚 Documentation | **À venir** ou version future |
| Nouvelle version taggée | Créer une nouvelle section de version | Nouvelle section avec date |

## Structure du fichier CHANGELOG.md

```markdown
# 📜 CHANGELOG - KPI

*Outil de saisie d'activité et de restitution des KPI pour entrepreneurs individuels*

---

## 🔜 **À venir** *(Next Release)*

### ✨ Nouveautés
- **Fonctionnalité** : Description claire 🎯
  *Explication ou exemple d'utilisation*

### 🛠️ Améliorations techniques
- **Amélioration** : Description 🔧

### 🐛 Corrections de bugs
- **Bug corrigé** : Description 🐞

### 📚 Documentation
- **Documentation** : Description 📖

---

## 🎉 **X.Y.Z** *(date)*

### ✨ Nouveautés
- **Fonctionnalité** : Description

---

## 📖 **Guide de lecture**

### 💡 Symboles utilisés
| Symbole | Signification |
|--------|---------------|

---

## 📌 **Feuille de route**
```

## Règles de rédaction

### 1. Style général

- **Ton** : Didactique, accessible, positif
- **Public cible** : Utilisateurs finaux (Cécile et autres entrepreneurs)
- **Langage** : Simple, éviter le jargon technique
- **Structure** : Listes à puces pour la lisibilité

### 2. Utilisation des émoticônes

Utilise les émoticônes **de manière cohérente** selon le type de changement :

| Type | Émoticône | Exemple |
|------|-----------|---------|
| Nouvelle fonctionnalité | ✨ | ✨ **Export PDF** : Génération de rapports en PDF 📄 |
| Amélioration technique | 🛠️ | 🛠️ **Performances** : Optimisation des requêtes SQL |
| Correction de bug | 🐛 | 🐛 **Calcul ghosting** : Correction du dédoublonnage |
| Documentation | 📚 | 📚 **Guide utilisateur** : Ajout du manuel 📖 |
| Configuration | 🔧 | 🔧 **Installation** : Simplification du processus |
| Version majeure | 🎉 | 🎉 **1.0.0** : Première version stable |
| Base de données | 💾 | 💾 **SQLite** : Stockage local des données |
| Import/Export | 📥/📤 | 📥 **Import Excel** : Récupération des données existantes |
| Interface | 🌐 | 🌐 **Écran web** : Interface de saisie |
| Calcul | 🧮 | 🧮 **Indicateurs** : Moteur de calcul |
| macOS | 🍎 | 🍎 **Lanceur macOS** : Script pour Finder |
| Version | 🏷️ | 🏷️ **Version auto** : Gestion automatique |

**Ne pas utiliser** : 😀 😂 👍 (trop subjectifs ou informels)

### 3. Format des entrées

Chaque entrée doit suivre ce format :

```markdown
- **Nom de la fonctionnalité** : Description concise 🏷️
  *Explication ou exemple en italien (optionnel)*
```

**Exemples concrets** :

✅ **Bonne pratique** :
```markdown
- **Affichage de la version** : Ajout de l'option `-v` / `--version` pour connaître la version exacte 📋
  *Exemple : `kpi version 0.0.1.post7+dirty`*
```

❌ **À éviter** :
```markdown
- Ajout de -v pour la version
```

### 4. Organisation par catégories

Les changements doivent être **groupés par type** dans chaque version :

1. **✨ Nouveautés** (nouvelles fonctionnalités visibles par l'utilisateur)
2. **🛠️ Améliorations techniques** (optimisations, refactoring)
3. **🐛 Corrections de bugs** (fixes de problèmes)
4. **📚 Documentation** (mises à jour de la documentation)

**Ordre recommandé** : Nouveautés → Améliorations → Corrections → Documentation

### 5. Sections spéciales

#### Section "À venir" (Next Release)

Utilisée pour les changements **non encore taggés** dans une version officielle.

```markdown
## 🔜 **À venir** *(Next Release)*
```

#### Nouvelles versions taggées

Quand une nouvelle version est taggée dans git, crée une **nouvelle section** avec :

```markdown
## 🎉 **X.Y.Z** *(date)*
```

**Format de la date** : `jj mois aaaa` (ex: `28 octobre 2026`)

### 6. Version initiale

La version **0.0.1** est la première version stable et doit contenir toutes les fonctionnalités de base.

## Exemples complets

### Exemple 1 : Nouvelle fonctionnalité

```markdown
### ✨ Nouveautés

- **Lanceur macOS** : Ajout d'un script **`KPI.command`** pour lancer l'application directement depuis le Finder 🍎
  *Double-cliquez, l'environnement virtuel est créé automatiquement si nécessaire, et l'application démarre dans Terminal*
```

### Exemple 2 : Correction de bug

```markdown
### 🐛 Corrections de bugs

- **Affichage de la version** : Correction du problème où `kpi -v` affichait `0.0.0` au lieu de la version git 🏷️
  *La version est désormais correctement lue depuis les tags git avec setuptools-scm*
```

### Exemple 3 : Nouvelle version taggée

```markdown
## 🎉 **0.0.1** *(28 octobre 2026)*

### ✨ Premier lancement !

Bienvenue à la première version stable de **KPI** ! Cette version pose les bases de votre outil de suivi d'activité.

### 🏗️ Fonctionnalités de base

- **Base de données SQLite** : Stockage local de toutes vos données dans un simple fichier `kpi.sqlite3` 💾
  *Sauvegardez, copiez, partagez votre fichier : c'est votre base de données complète !*
```

## Procédure de mise à jour

### 1. Pour un nouveau commit (non taggé)

```bash
# 1. Vérifier la version actuelle
git describe --tags

# 2. Modifier le CHANGELOG.md
#    - Ajouter une entrée dans la section "À venir"
#    - Utiliser le bon émoticône selon le type
#    - Rédiger une description claire

# 3. Commiter les changements
git add CHANGELOG.md
git commit -m "docs: mettre à jour le CHANGELOG pour [description]"
```

### 2. Pour une nouvelle version taggée

```bash
# 1. Vérifier que tous les changements sont documentés dans "À venir"

# 2. Créer une nouvelle section pour la version
#    - Copier le contenu de "À venir" dans la nouvelle section
#    - Ajouter la date du tag
#    - Vider ou supprimer la section "À venir"

# 3. Créer le tag git
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push --tags

# 4. Commiter le CHANGELOG
git add CHANGELOG.md
git commit -m "docs: préparer le CHANGELOG pour la version X.Y.Z"
```

### 3. Vérification avant commit

Avant de commiter le CHANGELOG, vérifie :

- [ ] Les émoticônes sont **cohérentes** avec le type de changement
- [ ] Les descriptions sont **claires et accessibles**
- [ ] Le ton est **didactique et positif**
- [ ] Les exemples (si présents) sont **corrects et utiles**
- [ ] La structure **respecte les catégories** (Nouveautés → Améliorations → Corrections → Documentation)

## Bonnes pratiques

### ✅ À faire

- **Être concis** : Une phrase par entrée
- **Utiliser des verbes d'action** : "Ajout", "Correction", "Amélioration"
- **Expliquer l'impact utilisateur** : "Permet de...", "Facilite..."
- **Donner des exemples** quand cela éclaircit le propos
- **Grouper les changements similaires** sous une même entrée

### ❌ À éviter

- **Jargon technique** : "Refactorisation du Repository pattern"
- **Descriptions trop vagues** : "Fix bug"
- **Entrées trop longues** : Plus de 2 lignes
- **Émoticônes incohérents** : Utiliser ✨ pour une correction de bug
- **Oublier les catégories** : Mélanger nouvelles fonctionnalités et corrections

## Template rapide

```markdown
- **Nom** : Description 🏷️
  *Explication*
```

## Ressources

- [Keep a Changelog](https://keepachangelog.com/) - Standard pour les CHANGELOG
- [Conventional Commits](https://www.conventionalcommits.org/) - Pour les messages de commit
- [Émoticônes GitHub](https://github.com/ikatyang/emoji-cheat-sheet) - Liste complète des émoticônes

## Application au projet KPI

### Contenu spécifique à documenter

| Éléments | Émoticône | Section | Exemple |
|----------|-----------|---------|---------|
| Écran de saisie | 🌐 | Nouveautés | ✨ **Écran de saisie** : Interface web pour enregistrer les événements 🌐 |
| Indicateurs KPI | 🧮 | Nouveautés | ✨ **Taux de ghosting** : Calcul automatique du taux de ghosting 🧮 |
| Base SQLite | 💾 | Fonctionnalités de base | 💾 **Base SQLite** : Stockage dans un fichier unique 💾 |
| Import Excel | 📥 | Fonctionnalités de base | 📥 **Import initial** : Récupération du classeur Excel 📥 |
| Export PDF | 📤 | À venir | ✨ **Export PDF** : Génération de rapports en PDF 📤 |
| Lanceur macOS | 🍎 | Nouveautés | 🍎 **Lanceur macOS** : Script exécutable depuis le Finder 🍎 |
| Version auto | 🏷️ | Améliorations | 🛠️ **Version auto** : Gestion automatique via setuptools-scm 🏷️ |

### Feuille de route à intégrer

Le projet KPI suit une feuille de route claire. Intègre les prochaines étapes dans le CHANGELOG :

```markdown
## 📌 **Feuille de route**

| Étape | Fonctionnalité | Statut | Version prévue |
|-------|---------------|--------|----------------|
| 4 | Écrans de consultation KPI + Export PDF | ⏳ En cours | 0.0.2 |
| 5 | Connecteur Google Analytics 4 | ⏳ À venir | 0.1.0 |
```

## Vérification finale

Avant de finaliser une mise à jour du CHANGELOG :

1. **Lis le fichier complet** pour vérifier la cohérence
2. **Vérifie les dates** des versions taggées
3. **Teste les exemples** si présents
4. **Assure-toi** que chaque changement important est documenté
5. **Vérifie** que le ton reste didactique et accessible

---

*Cette skill est spécifique au projet KPI et suit ses conventions particulières.*
