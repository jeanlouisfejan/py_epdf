# Visualiseur EPUB & PDF

Application de visualisation et gestion de bibliothèque numérique pour fichiers EPUB et PDF.

## Fonctionnalités

- 📚 **Affichage des couvertures** : Grille de vignettes avec aperçu des couvertures
- 🔍 **Détails des livres** : Clic gauche pour voir titre, auteur, éditeur, résumé
- 📖 **Lecture** : Ouvrir les livres dans votre lecteur par défaut
- 📁 **Copie de fichiers** : Copier des livres vers un autre emplacement
- 🗑️ **Suppression** : Effacer des livres avec confirmation
- ⚡ **Cache glissant** : Optimisation mémoire avec cache LRU de 100 vignettes
- 🎨 **Interface moderne** : Menu, scrollbar, popups avec Pygame

## Installation

### Prérequis

- Python 3.14+
- Windows, macOS ou Linux

### Installation des dépendances

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

```bash
python main.py
```

### Raccourcis clavier

- **Ctrl+O** : Ouvrir un dossier
- **Molette** : Défiler dans la bibliothèque
- **Echap** : Quitter ou fermer les popups

### Souris

- **Clic gauche** sur une vignette : Afficher les détails du livre
- **Clic droit** sur une vignette : Menu contextuel
  - 📖 Lire le livre
  - 📁 Copier vers...
  - 🗑️ Effacer

## Dépendances

- pygame-ce : Interface graphique
- Pillow : Traitement d'images
- PyPDF2 : Extraction de métadonnées PDF
- ebooklib : Support EPUB
- lxml : Parsing XML

## Performance

- Gestion de bibliothèques de 1000+ livres
- Cache limité à 100 vignettes en mémoire
- Chargement progressif des couvertures
- Rendu uniquement des éléments visibles

## Licence

MIT
