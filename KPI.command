#!/bin/bash

# KPI - Script de lancement pour macOS
# Double-cliquez sur ce fichier depuis le Finder pour lancer l'application
# L'environnement virtuel sera créé automatiquement s'il n'existe pas
# Le code (git pull) et les dépendances (pip install) sont mis à jour
# automatiquement si nécessaire — désactivable avec KPI_SANS_MISE_A_JOUR=1

# Obtenir le dossier où se trouve ce script
cd "$(dirname "$0")"

# Hash de pyproject.toml, utilisé pour détecter un changement de dépendances
HASH=""
if [ -f pyproject.toml ]; then
    HASH=$(shasum -a 256 pyproject.toml 2>/dev/null | awk '{print $1}')
    if [ -z "$HASH" ]; then
        HASH=$(sha256sum pyproject.toml 2>/dev/null | awk '{print $1}')
    fi
fi

# --- Mise à jour automatique (désactivable avec KPI_SANS_MISE_A_JOUR=1) ---
if [ -z "$KPI_SANS_MISE_A_JOUR" ]; then

    # 1. Mettre à jour le code si le dépôt distant a bougé
    if [ -d .git ]; then
        # lowSpeed* borne un éventuel transfert bloqué (~30 s, car macOS
        # n'a pas la commande timeout)
        if git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 fetch --quiet origin 2>/dev/null; then
            BRANCHE=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
            AMONT=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)
            if [ -z "$AMONT" ]; then
                AMONT="origin/$BRANCHE"
            fi
            RETARD=$(git rev-list --count "HEAD..$AMONT" 2>/dev/null)
            if [ -n "$RETARD" ] && [ "$RETARD" -gt 0 ] 2>/dev/null; then
                echo "Mise à jour du code depuis origin..."
                if git pull --ff-only --quiet origin "$BRANCHE"; then
                    # Le pull a pu modifier ce script en cours de lecture :
                    # on le ré-exécute une fois pour poursuivre avec le
                    # nouveau code (garde-fou _KPI_MAJ_REEXEC anti-boucle)
                    if [ -z "$_KPI_MAJ_REEXEC" ]; then
                        _KPI_MAJ_REEXEC=1 exec bash "$0"
                    fi
                else
                    echo "Attention : git pull impossible (modifications locales ?), lancement avec le code actuel"
                fi
            fi
        else
            echo "Attention : remote origin injoignable, lancement avec le code actuel"
        fi
    fi

    # 2. Mettre à jour les dépendances si pyproject.toml a changé
    if [ -n "$HASH" ] && [ -x .venv/bin/pip ]; then
        if [ ! -f .venv/kpi-pyproject.sha256 ] || [ "$(cat .venv/kpi-pyproject.sha256 2>/dev/null)" != "$HASH" ]; then
            echo "Mise à jour des dépendances..."
            if .venv/bin/pip install -e . --quiet; then
                echo "$HASH" > .venv/kpi-pyproject.sha256
            else
                echo "Attention : installation des dépendances échouée, lancement avec l'environnement actuel"
            fi
        fi
    fi
fi

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d .venv ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e .
    # Stamp initial pour éviter une réinstallation au prochain lancement
    if [ -n "$HASH" ]; then
        echo "$HASH" > .venv/kpi-pyproject.sha256
    fi
fi

# Lancer l'application KPI
.venv/bin/kpi

# Garder le terminal ouvert après la fermeture de l'application
echo ""
echo "Appuyez sur Entrée pour fermer cette fenêtre..."
read
