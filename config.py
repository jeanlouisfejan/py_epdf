"""
Configuration de l'application
"""

# Fenêtre
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_TITLE = "📚 Visualiseur de couvertures EPUB & PDF"

# Grille de livres
CARD_WIDTH = 200
CARD_HEIGHT = 320
CARD_GAP = 25
CARD_PADDING = 30

# Couleurs (R, G, B, A)
COLOR_PRIMARY = (102, 126, 234, 255)  # Bleu-violet
COLOR_BACKGROUND = (248, 249, 250, 255)  # Gris clair
COLOR_TEXT_PRIMARY = (33, 37, 41, 255)  # Gris foncé
COLOR_TEXT_SECONDARY = (108, 117, 125, 255)  # Gris moyen
COLOR_WHITE = (255, 255, 255, 255)
COLOR_BORDER = (200, 200, 200, 255)

# Défilement
SCROLL_SPEED = 30
SCROLL_KEYBOARD_SPEED = 50

# Performance
LAZY_LOAD_THRESHOLD = 50  # Nombre de livres avant d'activer le lazy loading
CACHE_SIZE = 100  # Nombre de couvertures en cache

# Formats supportés
SUPPORTED_FORMATS = ['.epub', '.pdf']

# Images
COVER_WIDTH = 200
COVER_HEIGHT = 240
DEFAULT_COVER_COLOR = COLOR_PRIMARY
