# Changelog - Visualiseur EPUB/PDF Python

## Version 1.0.0 - 2025-12-31

### Première version

#### Fonctionnalités implémentées

- ✓ Interface graphique avec Pyglet (OpenGL)
- ✓ Sélection de dossier avec dialogue natif
- ✓ Scan des fichiers EPUB et PDF
- ✓ Affichage en grille responsive
- ✓ Défilement avec molette et touches
- ✓ Extraction des métadonnées EPUB (titre, auteur, éditeur, etc.)
- ✓ Extraction des métadonnées PDF
- ✓ Extraction des couvertures EPUB
- ✓ Icônes pour identifier les types de fichiers
- ✓ Compteur de fichiers (EPUB/PDF)
- ✓ Raccourcis clavier (Ctrl+O, flèches, Home/End, Échap)
- ✓ Redimensionnement de fenêtre

#### Structure du projet

- `main.py` - Application principale
- `book_manager.py` - Gestion des livres et métadonnées
- `ui_manager.py` - Interface utilisateur Pyglet
- `config.py` - Configuration centralisée
- `requirements.txt` - Dépendances Python
- `test_import.py` - Script de vérification
- `README.md` - Documentation principale
- `INSTALL.md` - Guide d'installation
- `run.bat` / `run.sh` - Scripts de lancement

#### Technologies utilisées

- Python 3.8+
- Pyglet 2.0+ (interface OpenGL)
- Pillow 10.0+ (images)
- PyPDF2 3.0+ (PDF)
- ebooklib 0.18+ (EPUB)
- lxml 4.9+ (XML)

#### Notes

- Basé sur la version web HTML/JS du visualiseur EPUB/PDF
- Architecture modulaire pour faciliter les évolutions
- Performance optimisée avec rendering par batch Pyglet

## À venir

### Version 1.1.0 (Planifiée)

- [ ] Modal avec détails complets du livre
- [ ] Extraction de couvertures PDF (première page)
- [ ] Lazy loading des métadonnées
- [ ] Animation de chargement
- [ ] Amélioration de l'UI (ombres, transitions)

### Version 1.2.0 (Planifiée)

- [ ] Recherche par titre/auteur/éditeur
- [ ] Filtres (EPUB/PDF uniquement)
- [ ] Tri (nom, auteur, date, taille)
- [ ] Navigation dans les sous-dossiers
- [ ] Fil d'Ariane (breadcrumb)

### Version 1.3.0 (Planifiée)

- [ ] Lecteur EPUB intégré
- [ ] Lecteur PDF intégré
- [ ] Favoris
- [ ] Export de la liste (CSV, JSON)
- [ ] Recherche profonde récursive
- [ ] Cache des couvertures sur disque

### Version 2.0.0 (Future)

- [ ] Base de données SQLite pour les métadonnées
- [ ] Collections/Bibliothèques personnalisées
- [ ] Tags et catégories
- [ ] Notes et annotations
- [ ] Statistiques de lecture
- [ ] Synchronisation cloud (optionnelle)

## Compatibilité

### Systèmes d'exploitation
- ✓ Windows 10/11
- ✓ Linux (Ubuntu, Debian, Fedora, etc.)
- ✓ macOS 10.14+

### Python
- Minimum : Python 3.8
- Recommandé : Python 3.10+
- Testé avec : Python 3.14

### Formats
- ✓ EPUB 2
- ✓ EPUB 3
- ✓ PDF (tous formats standards)

## Corrections de bugs

### Version 1.0.0
- Correction de l'encodage UTF-8 dans les scripts de test
- Gestion des erreurs d'extraction de métadonnées
- Optimisation du rendu Pyglet avec batching

## Contributions

Ce projet est ouvert aux contributions. Voir README.md pour les détails.
