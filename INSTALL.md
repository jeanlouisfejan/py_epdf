# Guide d'installation - Visualiseur EPUB/PDF

## Installation rapide (Windows)

### 1. Prérequis
- Python 3.8 ou supérieur installé
- Vérifier : `python --version` dans le terminal

### 2. Installation automatique

Double-cliquez sur `run.bat` - le script fera tout automatiquement!

### 3. Installation manuelle

Si vous préférez installer manuellement :

```bash
# Créer l'environnement virtuel (déjà fait normalement)
python -m venv venv

# Activer l'environnement virtuel
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

## Installation (Linux/macOS)

### 1. Prérequis

```bash
# Ubuntu/Debian - Installer tkinter si nécessaire
sudo apt-get install python3-tk python3-venv

# macOS
brew install python-tk
```

### 2. Installation

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

Ou utilisez le script :

```bash
chmod +x run.sh
./run.sh
```

## Vérification de l'installation

Pour vérifier que tout est correctement installé :

```bash
# Activer le venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Vérifier les imports
python -c "import pyglet; import PIL; import PyPDF2; import ebooklib; print('OK!')"
```

## Dépendances

Le fichier `requirements.txt` contient :
- **pyglet** : Interface graphique OpenGL
- **Pillow** : Traitement d'images
- **PyPDF2** : Lecture PDF
- **ebooklib** : Lecture EPUB
- **lxml** : Parsing XML

## Résolution de problèmes

### "python n'est pas reconnu..."
- Assurez-vous que Python est dans le PATH
- Ou utilisez `py` au lieu de `python`

### Erreur avec tkinter
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk
```

### Erreur "No module named 'PIL'"
```bash
pip install --upgrade Pillow
```

### Performance lente
- Fermez les autres applications
- Réduisez le nombre de livres dans le dossier

## Mise à jour

Pour mettre à jour les dépendances :

```bash
# Activer le venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Mettre à jour
pip install --upgrade -r requirements.txt
```

## Désinstallation

Supprimez simplement le dossier `py_epdf` complet.
