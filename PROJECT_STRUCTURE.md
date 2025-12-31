# Structure du projet py_epdf

## Arborescence

```
py_epdf/
├── venv/                    # Environnement virtuel Python
│   ├── Scripts/            # Scripts Python (Windows)
│   ├── Lib/               # Bibliothèques installées
│   └── ...
│
├── main.py                 # ★ Point d'entrée principal de l'application
├── book_manager.py         # Gestion des livres et extraction des métadonnées
├── ui_manager.py           # Interface utilisateur avec Pyglet
├── config.py               # Configuration centralisée
│
├── requirements.txt        # Dépendances Python
├── .gitignore             # Fichiers à ignorer par Git
│
├── run.bat                # Script de lancement (Windows)
├── run.sh                 # Script de lancement (Linux/macOS)
├── test_import.py         # Script de test des dépendances
│
├── README.md              # Documentation principale
├── INSTALL.md             # Guide d'installation détaillé
├── CHANGELOG.md           # Historique des versions
└── PROJECT_STRUCTURE.md   # Ce fichier
```

## Fichiers principaux

### main.py (★ Point d'entrée)
- Classe `EPDFViewer` qui hérite de `pyglet.window.Window`
- Gestion des événements (clavier, souris, redimensionnement)
- Boucle principale de l'application
- Coordination entre `BookManager` et `UIManager`

**Rôle**: Chef d'orchestre de l'application

### book_manager.py
- Classe `BookManager` pour gérer les livres
- Scan des dossiers (EPUB et PDF)
- Extraction des métadonnées EPUB (via ebooklib/lxml)
- Extraction des métadonnées PDF (via PyPDF2)
- Extraction des couvertures EPUB
- Formatage des données

**Rôle**: Backend - Gestion des données

### ui_manager.py
- Classe `UIManager` pour l'interface
- Rendu avec Pyglet (OpenGL)
- Grille responsive de livres
- Gestion des cartes de livres
- Gestion du scroll
- Détection des clics

**Rôle**: Frontend - Affichage et interaction

### config.py
- Constantes de configuration
- Dimensions de la fenêtre
- Tailles des cartes
- Couleurs
- Paramètres de performance

**Rôle**: Configuration centralisée

## Fichiers de documentation

### README.md
- Vue d'ensemble du projet
- Fonctionnalités
- Guide d'utilisation rapide
- Technologies utilisées
- Comparaison avec la version web

### INSTALL.md
- Instructions d'installation détaillées
- Pour Windows, Linux et macOS
- Résolution de problèmes
- Vérification de l'installation

### CHANGELOG.md
- Historique des versions
- Fonctionnalités ajoutées
- Bugs corrigés
- Roadmap future

### PROJECT_STRUCTURE.md (ce fichier)
- Structure du projet
- Description de chaque fichier
- Architecture de l'application

## Fichiers utilitaires

### requirements.txt
Liste des dépendances Python :
- pyglet >= 2.0.0
- Pillow >= 10.0.0
- PyPDF2 >= 3.0.0
- ebooklib >= 0.18
- lxml >= 4.9.0

### .gitignore
Fichiers à ignorer par Git :
- `__pycache__/`
- `*.pyc`
- `venv/`
- `.vscode/`
- etc.

### Scripts de lancement

**run.bat** (Windows)
```batch
@echo off
call venv\Scripts\activate.bat
python main.py
deactivate
```

**run.sh** (Linux/macOS)
```bash
#!/bin/bash
source venv/bin/activate
python main.py
deactivate
```

### test_import.py
Script de vérification :
- Teste tous les imports
- Vérifie la version Python
- Affiche un rapport de statut

## Architecture de l'application

```
┌─────────────────────────────────────────┐
│           main.py                       │
│      EPDFViewer (Window)                │
│  - Gestion des événements               │
│  - Coordination des composants          │
└──────────┬──────────────────────┬───────┘
           │                      │
           ├──────────────────────┤
           │                      │
   ┌───────▼─────────┐    ┌──────▼────────┐
   │  BookManager    │    │  UIManager    │
   │                 │    │               │
   │ - Scan dossiers │    │ - Rendu       │
   │ - Métadonnées   │    │ - Grille      │
   │ - Couvertures   │    │ - Scroll      │
   └─────────────────┘    └───────────────┘
           │                      │
           └──────────┬───────────┘
                      │
              ┌───────▼──────┐
              │   config.py  │
              │ Configuration│
              └──────────────┘
```

## Flux de données

1. **Démarrage** : `main.py` crée une fenêtre Pyglet
2. **Sélection** : L'utilisateur sélectionne un dossier
3. **Scan** : `BookManager` scanne le dossier
4. **Extraction** : Métadonnées et couvertures sont extraites
5. **Affichage** : `UIManager` dessine la grille
6. **Interaction** : L'utilisateur clique/scroll
7. **Événements** : `main.py` gère les événements
8. **Mise à jour** : `UIManager` redessine

## Dépendances externes

```
main.py
  ├── pyglet (fenêtre, rendu OpenGL)
  ├── tkinter (dialogue de sélection)
  └── pathlib (gestion des chemins)

book_manager.py
  ├── PyPDF2 (lecture PDF)
  ├── ebooklib (lecture EPUB)
  ├── lxml (parsing XML)
  ├── Pillow (images)
  └── zipfile (extraction EPUB)

ui_manager.py
  └── pyglet (rendu graphique)
```

## Extension future

Pour ajouter une nouvelle fonctionnalité :

1. **Backend** : Modifier `book_manager.py`
   - Nouvelles méthodes de scan
   - Nouveaux formats de fichiers
   - Nouvelles métadonnées

2. **Frontend** : Modifier `ui_manager.py`
   - Nouveaux éléments UI
   - Nouvelles interactions
   - Nouveaux modes d'affichage

3. **Configuration** : Ajouter dans `config.py`
   - Nouvelles constantes
   - Nouveaux paramètres

4. **Coordination** : Modifier `main.py`
   - Nouveaux événements
   - Nouvelles actions

## Principes de conception

- **Séparation des responsabilités** : UI séparée de la logique métier
- **Configuration centralisée** : Constantes dans `config.py`
- **Modularité** : Chaque fichier a un rôle précis
- **Extensibilité** : Facile d'ajouter de nouvelles fonctionnalités
- **Documentation** : Code commenté et README détaillés
