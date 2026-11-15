#!/bin/bash

# KPI - Script de lancement pour macOS
# Double-cliquez sur ce fichier depuis le Finder pour lancer l'application
# L'environnement virtuel sera créé automatiquement s'il n'existe pas

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
