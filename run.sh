#!/bin/bash
# Script de lancement pour le visualiseur EPUB/PDF (Linux/macOS)

echo "========================================"
echo "Visualiseur de couvertures EPUB et PDF"
echo "========================================"
echo ""

# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application
python main.py

# Désactiver l'environnement virtuel à la fin
deactivate
