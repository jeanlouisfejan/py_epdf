"""
Gestionnaire d'interface utilisateur avec Pygame
"""

import pygame
from typing import List, Dict, Optional, Tuple


class UIManager:
    """Gestionnaire de l'interface utilisateur"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # Configuration de la grille
        self.card_width = 200
        self.card_height = 320
        self.gap = 25
        self.padding = 30

        # Livres à afficher
        self.books: List[Dict] = []

        # Scrollbar
        self.scrollbar_width = 15
        self.scrollbar_padding = 5

        # Menu
        self.menu_height = 30
        self.menu_items = [
            {'label': 'Fichier', 'submenu': [
                {'label': 'Ouvrir dossier...', 'action': 'open_folder'},
                {'label': 'Ouvrir récursif...', 'action': 'open_recursive'},
                {'separator': True},
                {'label': 'Quitter', 'action': 'quit'}
            ]},
            {'label': 'Affichage', 'submenu': [
                {'label': 'Rafraîchir', 'action': 'refresh'},
                {'label': 'Trier par nom', 'action': 'sort_name'},
                {'label': 'Trier par taille', 'action': 'sort_size'}
            ]},
            {'label': 'Aide', 'submenu': [
                {'label': 'Raccourcis clavier', 'action': 'shortcuts'},
                {'label': 'À propos', 'action': 'about'}
            ]}
        ]
        self.active_menu = None
        self.menu_hover = None

        # Polices
        try:
            self.font_title = pygame.font.SysFont('Arial', 24)
            self.font_normal = pygame.font.SysFont('Arial', 12)
            self.font_small = pygame.font.SysFont('Arial', 10)
            self.font_menu = pygame.font.SysFont('Arial', 11)
            self.font_icon = pygame.font.SysFont('Arial', 48)
        except:
            self.font_title = pygame.font.Font(None, 32)
            self.font_normal = pygame.font.Font(None, 16)
            self.font_small = pygame.font.Font(None, 14)
            self.font_menu = pygame.font.Font(None, 15)
            self.font_icon = pygame.font.Font(None, 64)

        # Couleurs
        self.color_bg = (102, 125, 235)
        self.color_header = (102, 126, 234)
        self.color_menu_bg = (60, 60, 60)
        self.color_menu_hover = (80, 80, 80)
        self.color_white = (255, 255, 255)
        self.color_gray = (200, 200, 200)
        self.color_dark_gray = (100, 100, 100)
        self.color_text_dark = (33, 37, 41)
        self.color_scrollbar_track = (200, 200, 200)
        self.color_scrollbar_thumb = (102, 126, 234)

    def update_books(self, books: List[Dict]):
        """Mettre à jour la liste des livres"""
        self.books = books
        print(f"[DEBUG] {len(books)} livres chargés dans l'UI")

    def calculate_content_height(self) -> int:
        """Calculer la hauteur totale du contenu"""
        if not self.books:
            return 0

        # Calculer le nombre de colonnes
        available_width = self.width - 2 * self.padding
        cols = max(1, available_width // (self.card_width + self.gap))

        # Calculer le nombre de lignes
        rows = (len(self.books) + cols - 1) // cols

        # Hauteur totale
        total_height = rows * (self.card_height + self.gap) + 200

        return total_height

    def draw(self, screen: pygame.Surface, scroll_offset: int, max_scroll: int = 0):
        """Dessiner l'interface"""
        # Dessiner le menu en haut
        self.draw_menu(screen)

        # Dessiner le header
        self.draw_header(screen)

        # Dessiner les livres avec scroll
        if self.books:
            self.draw_books_grid(screen, scroll_offset)
            # Dessiner la scrollbar si nécessaire
            if max_scroll > 0:
                self.draw_scrollbar(screen, scroll_offset, max_scroll)
        else:
            self.draw_empty_state(screen)

    def draw_menu(self, screen: pygame.Surface):
        """Dessiner le menu"""
        # Fond du menu
        pygame.draw.rect(screen, self.color_menu_bg,
                        (0, 0, self.width, self.menu_height))

        # Dessiner les items du menu
        x_offset = 10
        for i, menu_item in enumerate(self.menu_items):
            text = self.font_menu.render(menu_item['label'], True, self.color_white)
            item_width = text.get_width() + 20

            # Fond si survol ou actif
            if self.menu_hover == i or self.active_menu == i:
                pygame.draw.rect(screen, self.color_menu_hover,
                               (x_offset, 0, item_width, self.menu_height))

            # Texte du menu
            screen.blit(text, (x_offset + 10, self.menu_height // 2 - text.get_height() // 2))

            x_offset += item_width

        # Dessiner le sous-menu si actif
        if self.active_menu is not None:
            self.draw_submenu(screen, self.active_menu)

    def draw_submenu(self, screen: pygame.Surface, menu_index: int):
        """Dessiner un sous-menu"""
        if menu_index >= len(self.menu_items):
            return

        menu_item = self.menu_items[menu_index]
        submenu = menu_item.get('submenu', [])

        if not submenu:
            return

        # Calculer la position X du menu
        x_offset = 10
        for i in range(menu_index):
            text = self.font_menu.render(self.menu_items[i]['label'], True, self.color_white)
            x_offset += text.get_width() + 20

        # Dimensions du sous-menu
        submenu_width = 200
        item_height = 25
        submenu_height = sum(10 if item.get('separator') else item_height for item in submenu)

        # Position du sous-menu
        submenu_y = self.menu_height

        # Fond du sous-menu
        pygame.draw.rect(screen, self.color_menu_hover,
                        (x_offset, submenu_y, submenu_width, submenu_height))

        # Bordure
        pygame.draw.rect(screen, self.color_dark_gray,
                        (x_offset, submenu_y, submenu_width, submenu_height), 1)

        # Dessiner les items
        y_offset = submenu_y
        for item in submenu:
            if item.get('separator'):
                # Ligne de séparation
                sep_y = y_offset + 5
                pygame.draw.line(screen, self.color_dark_gray,
                               (x_offset + 5, sep_y),
                               (x_offset + submenu_width - 5, sep_y), 1)
                y_offset += 10
            else:
                # Texte de l'item
                text = self.font_small.render(item['label'], True, self.color_white)
                screen.blit(text, (x_offset + 10, y_offset + item_height // 2 - text.get_height() // 2))
                y_offset += item_height

    def draw_header(self, screen: pygame.Surface):
        """Dessiner l'en-tête"""
        # Rectangle de fond pour le header
        header_y = self.menu_height
        pygame.draw.rect(screen, self.color_header,
                        (0, header_y, self.width, 150))

        # Titre
        title_text = self.font_title.render("📚 Visualiseur de couvertures EPUB & PDF",
                                            True, self.color_white)
        title_x = self.width // 2 - title_text.get_width() // 2
        title_y = header_y + 30 - title_text.get_height() // 2
        screen.blit(title_text, (title_x, title_y))

        # Bouton de sélection de dossier
        btn_y = header_y + 50
        self.draw_button(screen, self.padding, btn_y, 220, 50,
                        "📁 Sélectionner un dossier")

        # Info du dossier
        if self.books:
            epub_count = sum(1 for book in self.books if book['type'] == 'epub')
            pdf_count = sum(1 for book in self.books if book['type'] == 'pdf')
            info_text = f"{len(self.books)} livre(s) - {epub_count} EPUB, {pdf_count} PDF"

            info_surface = self.font_normal.render(info_text, True, self.color_gray)
            screen.blit(info_surface, (self.padding, btn_y + 60))

    def draw_button(self, screen: pygame.Surface, x: int, y: int,
                   width: int, height: int, text: str):
        """Dessiner un bouton"""
        # Rectangle du bouton
        pygame.draw.rect(screen, self.color_header, (x, y, width, height))

        # Bordure
        pygame.draw.rect(screen, self.color_white, (x, y, width, height), 2)

        # Texte du bouton
        text_surface = self.font_normal.render(text, True, self.color_white)
        text_x = x + width // 2 - text_surface.get_width() // 2
        text_y = y + height // 2 - text_surface.get_height() // 2
        screen.blit(text_surface, (text_x, text_y))

    def draw_books_grid(self, screen: pygame.Surface, scroll_offset: int):
        """Dessiner la grille de livres"""
        if not self.books:
            return

        # Calculer le nombre de colonnes
        available_width = self.width - 2 * self.padding
        cols = max(1, available_width // (self.card_width + self.gap))

        # Position de départ (sous le header)
        header_bottom = self.menu_height + 150 + 10
        start_y = header_bottom

        # Dessiner chaque livre
        visible_count = 0
        for i, book in enumerate(self.books):
            row = i // cols
            col = i % cols

            x = self.padding + col * (self.card_width + self.gap)
            y = start_y + row * (self.card_height + self.gap) - scroll_offset

            # Ne dessiner que les livres visibles
            if -self.card_height < y < self.height:
                self.draw_book_card(screen, x, y, book)
                visible_count += 1

        # Debug: afficher le nombre de livres visibles (seulement la première fois)
        if not hasattr(self, '_debug_shown'):
            print(f"[DEBUG] Dessin de {visible_count}/{len(self.books)} livres visibles")
            print(f"[DEBUG] Colonnes: {cols}, Start Y: {start_y}, Scroll: {scroll_offset}")
            self._debug_shown = True

    def draw_book_card(self, screen: pygame.Surface, x: int, y: int, book: Dict):
        """Dessiner une carte de livre"""
        # Fond de la carte
        pygame.draw.rect(screen, self.color_white,
                        (x, y, self.card_width, self.card_height))

        # Bordure
        pygame.draw.rect(screen, self.color_gray,
                        (x, y, self.card_width, self.card_height), 2)

        # Zone de couverture
        cover_height = 240
        pygame.draw.rect(screen, self.color_header,
                        (x, y, self.card_width, cover_height))

        # Icône du type de fichier
        icon = '📖' if book['type'] == 'epub' else '📄'
        try:
            icon_surface = self.font_icon.render(icon, True, self.color_white)
            icon_x = x + self.card_width // 2 - icon_surface.get_width() // 2
            icon_y = y + cover_height // 2 - icon_surface.get_height() // 2
            screen.blit(icon_surface, (icon_x, icon_y))
        except:
            # Fallback si l'emoji ne s'affiche pas
            type_text = "EPUB" if book['type'] == 'epub' else "PDF"
            type_surface = self.font_title.render(type_text, True, self.color_white)
            type_x = x + self.card_width // 2 - type_surface.get_width() // 2
            type_y = y + cover_height // 2 - type_surface.get_height() // 2
            screen.blit(type_surface, (type_x, type_y))

        # Nom du fichier (sans extension)
        name = book['name'].replace('.epub', '').replace('.pdf', '')
        if len(name) > 25:
            name = name[:22] + '...'

        name_surface = self.font_small.render(name, True, self.color_text_dark)
        name_x = x + self.card_width // 2 - name_surface.get_width() // 2
        name_y = y + cover_height + 20
        screen.blit(name_surface, (name_x, name_y))

        # Auteur (si disponible)
        author = 'Chargement...'
        if 'metadata' in book:
            author = book['metadata'].get('author', 'Auteur inconnu')

        if len(author) > 30:
            author = author[:27] + '...'

        author_surface = self.font_small.render(author, True, (108, 117, 125))
        author_x = x + self.card_width // 2 - author_surface.get_width() // 2
        author_y = y + cover_height + 40
        screen.blit(author_surface, (author_x, author_y))

    def draw_empty_state(self, screen: pygame.Surface):
        """Dessiner l'état vide"""
        text1 = self.font_normal.render("📚 Aucun fichier", True, (108, 117, 125))
        text2 = self.font_small.render("Sélectionnez un dossier contenant des EPUB ou PDF",
                                      True, (108, 117, 125))

        text1_x = self.width // 2 - text1.get_width() // 2
        text1_y = self.height // 2 - 20
        text2_x = self.width // 2 - text2.get_width() // 2
        text2_y = self.height // 2 + 10

        screen.blit(text1, (text1_x, text1_y))
        screen.blit(text2, (text2_x, text2_y))

    def draw_scrollbar(self, screen: pygame.Surface, scroll_offset: int, max_scroll: int):
        """Dessiner la barre de défilement"""
        # Zone de scrollbar
        scrollbar_x = self.width - self.scrollbar_width - self.scrollbar_padding
        scrollbar_y = 10 + self.menu_height
        scrollbar_track_height = self.height - 170 - self.menu_height

        # Fond de la track
        pygame.draw.rect(screen, self.color_scrollbar_track,
                        (scrollbar_x, scrollbar_y, self.scrollbar_width, scrollbar_track_height))

        # Calculer la taille et position du thumb
        if max_scroll > 0:
            visible_ratio = self.height / (self.height + max_scroll)
            thumb_height = max(30, scrollbar_track_height * visible_ratio)

            scroll_ratio = scroll_offset / max_scroll if max_scroll > 0 else 0
            thumb_y = scrollbar_y + (scrollbar_track_height - thumb_height) * scroll_ratio

            # Dessiner le thumb
            pygame.draw.rect(screen, self.color_scrollbar_thumb,
                           (scrollbar_x, thumb_y, self.scrollbar_width, thumb_height))

    def is_select_folder_button_clicked(self, x: int, y: int) -> bool:
        """Vérifier si le bouton de sélection est cliqué"""
        btn_x = self.padding
        btn_y = self.menu_height + 50  # header_y (30) + 50
        btn_width = 220
        btn_height = 50
        clicked = (btn_x <= x <= btn_x + btn_width and
                   btn_y <= y <= btn_y + btn_height)
        if clicked:
            print(f"[DEBUG] Bouton zone: ({btn_x}, {btn_y}) à ({btn_x + btn_width}, {btn_y + btn_height})")
        return clicked

    def get_book_at_position(self, x: int, y: int) -> Optional[int]:
        """Obtenir l'index du livre à une position donnée"""
        if not self.books:
            return None

        # Calculer le nombre de colonnes
        available_width = self.width - 2 * self.padding
        cols = max(1, available_width // (self.card_width + self.gap))

        # Position de départ (sous le header)
        header_bottom = self.menu_height + 150 + 10
        start_y = header_bottom

        for i, book in enumerate(self.books):
            row = i // cols
            col = i % cols

            card_x = self.padding + col * (self.card_width + self.gap)
            card_y = start_y + row * (self.card_height + self.gap)

            if (card_x <= x <= card_x + self.card_width and
                card_y <= y <= card_y + self.card_height):
                return i

        return None

    def get_menu_at_position(self, x: int, y: int) -> Optional[int]:
        """Obtenir l'index du menu cliqué"""
        if y < 0 or y > self.menu_height:
            return None

        x_offset = 10
        for i, menu_item in enumerate(self.menu_items):
            text = self.font_menu.render(menu_item['label'], True, self.color_white)
            item_width = text.get_width() + 20
            if x_offset <= x <= x_offset + item_width:
                return i
            x_offset += item_width

        return None

    def get_submenu_action(self, menu_index: int, x: int, y: int) -> Optional[str]:
        """Obtenir l'action du sous-menu cliqué"""
        if menu_index >= len(self.menu_items):
            return None

        menu_item = self.menu_items[menu_index]
        submenu = menu_item.get('submenu', [])

        if not submenu:
            return None

        # Calculer la position X du menu
        x_offset = 10
        for i in range(menu_index):
            text = self.font_menu.render(self.menu_items[i]['label'], True, self.color_white)
            x_offset += text.get_width() + 20

        # Dimensions du sous-menu
        submenu_width = 200
        item_height = 25
        submenu_height = sum(10 if item.get('separator') else item_height for item in submenu)

        submenu_y = self.menu_height

        # Vérifier si le clic est dans le sous-menu
        if not (x_offset <= x <= x_offset + submenu_width and
                submenu_y <= y <= submenu_y + submenu_height):
            return None

        # Trouver l'item cliqué
        y_offset = submenu_y
        for item in submenu:
            if item.get('separator'):
                y_offset += 10
            else:
                if y_offset <= y <= y_offset + item_height:
                    return item.get('action')
                y_offset += item_height

        return None

    def on_resize(self, width: int, height: int):
        """Gestion du redimensionnement"""
        self.width = width
        self.height = height
