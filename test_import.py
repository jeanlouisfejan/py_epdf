#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier l'installation
"""

import sys
import io

# Forcer l'encodage UTF-8 pour la sortie
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_imports():
    """Tester tous les imports nécessaires"""
    print("=" * 60)
    print("Test des dépendances - Visualiseur EPUB/PDF")
    print("=" * 60)
    print()

    tests = [
        ("pyglet", "Interface graphique"),
        ("PIL", "Traitement d'images (Pillow)"),
        ("PyPDF2", "Lecture PDF"),
        ("ebooklib", "Lecture EPUB"),
        ("lxml", "Parsing XML"),
        ("tkinter", "Dialogues de fichiers")
    ]

    results = []

    for module_name, description in tests:
        try:
            __import__(module_name)
            status = "✓ OK"
            success = True
        except ImportError as e:
            status = f"✗ ERREUR: {e}"
            success = False

        results.append(success)
        print(f"{module_name:15} ({description:30}): {status}")

    print()
    print("=" * 60)

    if all(results):
        print("✓ Tous les modules sont correctement installés!")
        print("Vous pouvez lancer l'application avec: python main.py")
        return 0
    else:
        print("✗ Certains modules sont manquants.")
        print("Installez les dépendances avec: pip install -r requirements.txt")
        return 1

def test_python_version():
    """Vérifier la version de Python"""
    version = sys.version_info
    print(f"Version de Python: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8 ou supérieur est requis!")
        return False

    print("✓ Version de Python compatible")
    return True

if __name__ == "__main__":
    print()
    if not test_python_version():
        sys.exit(1)

    print()
    sys.exit(test_imports())
