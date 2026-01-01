#!/usr/bin/env python3
"""
Visualiseur de couvertures EPUB & PDF
Version Python avec Pygame
"""

import pygame
import sys
from pathlib import Path
from typing import Optional, List, Dict
import tkinter as tk
from tkinter import filedialog
import zipfile
from xml.etree import ElementTree as ET
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


class EPDFViewer:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        # Configuration
        self.width = 1400
        self.height = 900
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Visualiseur EPUB & PDF")

        # Polices
        self.font_big = pygame.font.SysFont('Arial', 32)
        self.font_normal = pygame.font.SysFont('Arial', 18)
        self.font_small = pygame.font.SysFont('Arial', 15)

        # Couleurs
        self.COLOR_BG = (102, 125, 235)
        self.COLOR_HEADER = (70, 90, 200)
        self.COLOR_MENU_BG = (50, 50, 50)
        self.COLOR_MENU_HOVER = (80, 80, 80)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_CARD = (255, 255, 255)
        self.COLOR_CARD_COVER = (80, 100, 180)
        self.COLOR_TEXT_DARK = (30, 30, 30)
        self.COLOR_SCROLLBAR = (150, 150, 150)
        self.COLOR_SCROLLBAR_THUMB = (100, 100, 100)

        # État
        self.books: List[Dict] = []
        self.all_books: List[Dict] = []  # Tous les livres (sans filtre)
        self.current_directory: Optional[Path] = None
        self.scroll_offset = 0
        self.max_scroll = 0
        self.running = True
        self.clock = pygame.time.Clock()
        self.search_pattern = None  # Pattern regex pour la recherche

        # Menu
        self.menu_height = 25
        self.menu_open = None  # None ou index du menu ouvert
        self.menus = [
            {"label": "Fichier", "items": [
                {"label": "Ouvrir dossier...", "action": "open"},
                {"label": "Ouvrir récursif...", "action": "open_recursive"},
                {"label": "Quitter", "action": "quit"}
            ]},
            {"label": "Affichage", "items": [
                {"label": "Rafraichir", "action": "refresh"},
                {"label": "Trier par nom", "action": "sort_name"},
                {"label": "Trier par taille", "action": "sort_size"}
            ]},
            {"label": "Rechercher", "items": [
                {"label": "Par nom (regex)...", "action": "search_regex"},
                {"label": "Afficher tout", "action": "show_all"}
            ]}
        ]

        # Grille
        self.card_width = 180
        self.card_height = 280
        self.card_gap = 20
        self.grid_start_y = 120  # Header de 100px + marge de 20px

        # Cache des couvertures avec système de cache glissant
        self.cover_cache: Dict[str, pygame.Surface] = {}
        self.cover_cache_order: List[str] = []  # Pour suivre l'ordre d'accès (LRU)
        self.max_cache_size = 100  # Limite du cache glissant
        self.cover_loading: set = set()  # Couvertures en cours de chargement
        self.covers_to_load: List[Dict] = []  # File d'attente de chargement

        # Scrollbar dragging
        self.scrollbar_dragging = False
        self.scrollbar_width = 12
        self.scrollbar_x = self.width - self.scrollbar_width - 5

        # Optimisation: limiter les chargements par frame
        self.covers_per_frame = 2

        # Popup de détails
        self.show_details_popup = False
        self.selected_book = None
        self.book_metadata = {}

        # Popup de confirmation d'ouverture
        self.show_open_confirmation = False

        # Popup de confirmation de suppression
        self.show_delete_confirmation = False

        # Menu contextuel (clic droit)
        self.show_context_menu = False
        self.context_menu_pos = (0, 0)
        self.context_menu_book = None

        # Bouton Retour
        self.back_button_rect = None

        # Compteur pour afficher le message de cache moins souvent
        self.cache_clean_count = 0

    def scan_directory(self, path: Path, recursive: bool = False):
        """Scanner un dossier pour les EPUB/PDF et les sous-dossiers"""
        self.books.clear()
        self.all_books.clear()
        self.cover_cache.clear()
        self.cover_cache_order.clear()
        self.cover_loading.clear()
        self.covers_to_load.clear()
        self.search_pattern = None

        # Ajouter les dossiers (uniquement en mode non-récursif)
        if not recursive:
            for d in path.iterdir():
                if d.is_dir() and not d.name.startswith('.'):
                    self.all_books.append({
                        'name': d.name,
                        'path': d,
                        'type': 'folder',
                        'size': 0
                    })

        if recursive:
            epub_files = list(path.rglob("*.epub"))
            pdf_files = list(path.rglob("*.pdf"))
        else:
            epub_files = list(path.glob("*.epub"))
            pdf_files = list(path.glob("*.pdf"))

        for f in epub_files:
            self.all_books.append({
                'name': f.name,
                'path': f,
                'type': 'epub',
                'size': f.stat().st_size
            })

        for f in pdf_files:
            self.all_books.append({
                'name': f.name,
                'path': f,
                'type': 'pdf',
                'size': f.stat().st_size
            })

        # Trier: dossiers d'abord, puis fichiers par nom
        self.all_books.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
        self.books = self.all_books.copy()
        self.update_scroll_limits()

        folders_count = sum(1 for b in self.books if b['type'] == 'folder')
        files_count = len(self.books) - folders_count
        print(f"Trouvé {folders_count} dossier(s) et {files_count} livre(s)")

    def update_scroll_limits(self):
        """Calculer les limites de scroll"""
        if not self.books:
            self.max_scroll = 0
            return

        cols = max(1, (self.width - 60) // (self.card_width + self.card_gap))
        rows = (len(self.books) + cols - 1) // cols
        content_height = rows * (self.card_height + self.card_gap) + self.grid_start_y + 50
        self.max_scroll = max(0, content_height - self.height)

    def open_folder_dialog(self, recursive: bool = False):
        """Ouvrir le dialogue de sélection de dossier"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        folder = filedialog.askdirectory(title="Sélectionner un dossier")

        root.destroy()

        if folder:
            self.current_directory = Path(folder)
            self.scan_directory(self.current_directory, recursive)

    def get_cover_surface(self, book: Dict, request_load: bool = True) -> Optional[pygame.Surface]:
        """Obtenir la surface de couverture d'un livre (lazy loading avec cache LRU)"""
        path_str = str(book['path'])

        # Si déjà en cache, marquer comme récemment utilisé
        if path_str in self.cover_cache:
            # Déplacer à la fin de la liste (plus récent)
            if path_str in self.cover_cache_order:
                self.cover_cache_order.remove(path_str)
            self.cover_cache_order.append(path_str)
            return self.cover_cache[path_str]

        # Si pas encore demandé, ajouter à la file d'attente
        if request_load and path_str not in self.cover_loading:
            self.cover_loading.add(path_str)
            self.covers_to_load.append(book)

        return None

    def load_pending_covers(self):
        """Charger quelques couvertures en attente (appelé à chaque frame)"""
        loaded = 0
        while self.covers_to_load and loaded < self.covers_per_frame:
            book = self.covers_to_load.pop(0)
            path_str = str(book['path'])

            # Éviter de recharger
            if path_str in self.cover_cache:
                continue

            cover_surface = None

            if book['type'] == 'epub' and Image:
                try:
                    cover_image = self.extract_epub_cover(book['path'])
                    if cover_image:
                        # Redimensionner
                        cover_image.thumbnail((self.card_width - 10, 200))
                        # Convertir en surface Pygame
                        mode = cover_image.mode
                        size = cover_image.size
                        data = cover_image.tobytes()

                        if mode == 'RGB':
                            cover_surface = pygame.image.fromstring(data, size, 'RGB')
                        elif mode == 'RGBA':
                            cover_surface = pygame.image.fromstring(data, size, 'RGBA')
                except Exception as e:
                    pass  # Silencieux pour ne pas spammer la console

            # Ajouter au cache avec gestion LRU
            self.cover_cache[path_str] = cover_surface
            self.cover_cache_order.append(path_str)

            # Nettoyer le cache si trop grand (cache glissant de 100)
            if len(self.cover_cache) > self.max_cache_size:
                # Supprimer l'entrée la plus ancienne (premier de la liste)
                oldest_key = self.cover_cache_order.pop(0)
                if oldest_key in self.cover_cache:
                    del self.cover_cache[oldest_key]
                    self.cache_clean_count += 1
                    # Afficher un message toutes les 50 fois
                    if self.cache_clean_count % 50 == 0:
                        print(f"Cache glissant actif: {len(self.cover_cache)}/{self.max_cache_size} vignettes ({self.cache_clean_count} nettoyages)")

            loaded += 1

    def extract_epub_cover(self, epub_path: Path) -> Optional[Image.Image]:
        """Extraire la couverture d'un EPUB"""
        try:
            with zipfile.ZipFile(epub_path, 'r') as zf:
                # Chercher container.xml
                container = zf.read('META-INF/container.xml')
                root = ET.fromstring(container)

                # Trouver le fichier OPF
                ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = root.find('.//c:rootfile', ns)
                if rootfile is None:
                    return None

                opf_path = rootfile.get('full-path')
                opf_dir = str(Path(opf_path).parent)

                # Lire le fichier OPF
                opf_content = zf.read(opf_path)
                opf_root = ET.fromstring(opf_content)

                # Chercher l'image de couverture
                # Méthode 1: meta cover
                for meta in opf_root.iter():
                    if meta.get('name') == 'cover':
                        cover_id = meta.get('content')
                        for item in opf_root.iter():
                            if item.get('id') == cover_id:
                                href = item.get('href')
                                if href:
                                    cover_path = f"{opf_dir}/{href}" if opf_dir and opf_dir != '.' else href
                                    cover_path = cover_path.replace('//', '/')
                                    try:
                                        cover_data = zf.read(cover_path)
                                        return Image.open(BytesIO(cover_data))
                                    except:
                                        pass

                # Méthode 2: chercher fichier avec "cover" dans le nom
                for name in zf.namelist():
                    lower = name.lower()
                    if 'cover' in lower and (lower.endswith('.jpg') or lower.endswith('.jpeg') or lower.endswith('.png')):
                        try:
                            cover_data = zf.read(name)
                            return Image.open(BytesIO(cover_data))
                        except:
                            pass

        except Exception as e:
            pass

        return None

    def run(self):
        """Boucle principale"""
        while self.running:
            self.handle_events()
            self.load_pending_covers()  # Charger quelques couvertures par frame
            self.render()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self):
        """Gérer les événements"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.scrollbar_x = self.width - self.scrollbar_width - 5
                self.update_scroll_limits()

            elif event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 40
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Vérifier si on clique sur la scrollbar
                if self.is_click_on_scrollbar(event.pos):
                    self.scrollbar_dragging = True
                    self.handle_scrollbar_click(event.pos)
                else:
                    self.handle_click(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # Clic droit - Ouvrir le livre
                self.handle_right_click(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.scrollbar_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.scrollbar_dragging:
                    self.handle_scrollbar_drag(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.show_context_menu:
                        self.show_context_menu = False
                    elif self.show_delete_confirmation:
                        self.show_delete_confirmation = False
                    elif self.show_open_confirmation:
                        self.show_open_confirmation = False
                    elif self.show_details_popup:
                        self.show_details_popup = False
                    else:
                        self.running = False
                elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.open_folder_dialog()

    def is_click_on_scrollbar(self, pos) -> bool:
        """Vérifier si le clic est sur la scrollbar"""
        if self.max_scroll <= 0:
            return False
        x, y = pos
        bar_y = self.grid_start_y
        bar_height = self.height - self.grid_start_y - 10
        return (self.scrollbar_x <= x <= self.scrollbar_x + self.scrollbar_width and
                bar_y <= y <= bar_y + bar_height)

    def handle_scrollbar_click(self, pos):
        """Gérer le clic sur la scrollbar"""
        self.handle_scrollbar_drag(pos)

    def handle_scrollbar_drag(self, pos):
        """Gérer le glissement de la scrollbar"""
        if self.max_scroll <= 0:
            return

        x, y = pos
        bar_y = self.grid_start_y
        bar_height = self.height - self.grid_start_y - 10

        # Calculer la position relative dans la track
        relative_y = y - bar_y
        ratio = max(0, min(1, relative_y / bar_height))

        # Appliquer le scroll
        self.scroll_offset = int(ratio * self.max_scroll)

    def handle_click(self, pos):
        """Gérer un clic"""
        x, y = pos

        # Gérer le menu contextuel
        if self.show_context_menu:
            menu_x, menu_y = self.context_menu_pos
            menu_width = 200
            item_height = 35
            menu_height = 3 * item_height

            # Vérifier si le clic est dans le menu
            if menu_x <= x < menu_x + menu_width and menu_y <= y < menu_y + menu_height:
                # Item 1: Lire le livre
                if menu_y <= y < menu_y + item_height:
                    self.open_book(self.context_menu_book)
                    self.show_context_menu = False
                    return
                # Item 2: Copier vers...
                elif menu_y + item_height <= y < menu_y + 2 * item_height:
                    self.copy_book(self.context_menu_book)
                    return
                # Item 3: Effacer
                elif menu_y + 2 * item_height <= y < menu_y + 3 * item_height:
                    self.delete_book(self.context_menu_book)
                    return
            else:
                # Clic en dehors = fermer le menu
                self.show_context_menu = False
                return

        # Gérer la popup de confirmation de suppression
        if self.show_delete_confirmation:
            popup_width = 400
            popup_height = 200
            popup_x = (self.width - popup_width) // 2
            popup_y = (self.height - popup_height) // 2

            # Bouton Oui
            btn_yes_x = popup_x + 50
            btn_yes_y = popup_y + popup_height - 60
            btn_yes_w = 120
            btn_yes_h = 40

            if btn_yes_x <= x <= btn_yes_x + btn_yes_w and btn_yes_y <= y <= btn_yes_y + btn_yes_h:
                self.confirm_delete_book()
                return

            # Bouton Non
            btn_no_x = popup_x + popup_width - 170
            btn_no_y = popup_y + popup_height - 60
            btn_no_w = 120
            btn_no_h = 40

            if btn_no_x <= x <= btn_no_x + btn_no_w and btn_no_y <= y <= btn_no_y + btn_no_h:
                self.show_delete_confirmation = False
                return

            # Clic en dehors = fermer
            if not (popup_x <= x <= popup_x + popup_width and popup_y <= y <= popup_y + popup_height):
                self.show_delete_confirmation = False
                return

            return

        # Gérer la popup de confirmation d'ouverture
        if self.show_open_confirmation:
            popup_width = 400
            popup_height = 200
            popup_x = (self.width - popup_width) // 2
            popup_y = (self.height - popup_height) // 2

            # Bouton Oui
            btn_yes_x = popup_x + 50
            btn_yes_y = popup_y + popup_height - 60
            btn_yes_w = 120
            btn_yes_h = 40

            if btn_yes_x <= x <= btn_yes_x + btn_yes_w and btn_yes_y <= y <= btn_yes_y + btn_yes_h:
                self.confirm_open_book()
                return

            # Bouton Non
            btn_no_x = popup_x + popup_width - 170
            btn_no_y = popup_y + popup_height - 60
            btn_no_w = 120
            btn_no_h = 40

            if btn_no_x <= x <= btn_no_x + btn_no_w and btn_no_y <= y <= btn_no_y + btn_no_h:
                self.show_open_confirmation = False
                return

            # Clic en dehors = fermer
            if not (popup_x <= x <= popup_x + popup_width and popup_y <= y <= popup_y + popup_height):
                self.show_open_confirmation = False
                return

            return

        # Fermer la popup si ouverte
        if self.show_details_popup:
            # Vérifier si clic sur le bouton fermer ou en dehors de la popup
            popup_width = 600
            popup_height = 500
            popup_x = (self.width - popup_width) // 2
            popup_y = (self.height - popup_height) // 2

            # Bouton fermer (X en haut à droite)
            close_btn_x = popup_x + popup_width - 40
            close_btn_y = popup_y + 10
            if close_btn_x <= x <= close_btn_x + 30 and close_btn_y <= y <= close_btn_y + 30:
                self.show_details_popup = False
                return

            # Clic en dehors de la popup = fermer
            if not (popup_x <= x <= popup_x + popup_width and popup_y <= y <= popup_y + popup_height):
                self.show_details_popup = False
                return

            # Clic dans la popup = ne rien faire
            return

        # Clic sur le bouton Retour
        if hasattr(self, 'back_button_rect') and self.back_button_rect and self.back_button_rect.collidepoint(x, y):
            parent_dir = self.current_directory.parent
            if parent_dir != self.current_directory:
                self.current_directory = parent_dir
                self.scan_directory(self.current_directory)
                self.scroll_offset = 0
            return

        # Clic sur la barre de menu (maintenant à droite du titre)
        menu_y = 10
        if 10 <= y < 35:  # Zone du menu (hauteur 25px)
            menu_x = 450
            for i, menu in enumerate(self.menus):
                text = self.font_small.render(menu['label'], True, self.COLOR_WHITE)
                menu_width = text.get_width() + 20

                if menu_x <= x < menu_x + menu_width:
                    if self.menu_open == i:
                        self.menu_open = None
                    else:
                        self.menu_open = i
                    return

                menu_x += menu_width

            self.menu_open = None
            return

        # Clic sur un sous-menu ouvert
        if self.menu_open is not None:
            menu = self.menus[self.menu_open]
            menu_x = 450
            for j in range(self.menu_open):
                text = self.font_small.render(self.menus[j]['label'], True, self.COLOR_WHITE)
                menu_x += text.get_width() + 20

            submenu_y = 35  # Juste en dessous du menu (qui est à y=10, hauteur 25)
            submenu_width = 180
            item_height = 25

            for i, item in enumerate(menu['items']):
                item_y = submenu_y + i * item_height
                if menu_x <= x < menu_x + submenu_width and item_y <= y < item_y + item_height:
                    self.execute_action(item['action'])
                    self.menu_open = None
                    return

            self.menu_open = None

        # Clic sur un livre ou dossier
        if self.books:
            cols = max(1, (self.width - 60) // (self.card_width + self.card_gap))
            start_x = 30

            for i, book in enumerate(self.books):
                row = i // cols
                col = i % cols

                card_x = start_x + col * (self.card_width + self.card_gap)
                card_y = self.grid_start_y + row * (self.card_height + self.card_gap) - self.scroll_offset

                if card_x <= x < card_x + self.card_width and card_y <= y < card_y + self.card_height:
                    # Si c'est un dossier, l'ouvrir
                    if book['type'] == 'folder':
                        self.current_directory = book['path']
                        self.scan_directory(self.current_directory)
                    else:
                        self.show_book_details(book)
                    return

    def handle_right_click(self, pos):
        """Gérer un clic droit pour afficher le menu contextuel"""
        x, y = pos

        # Clic droit sur un livre - afficher le menu contextuel
        if self.books:
            cols = max(1, (self.width - 60) // (self.card_width + self.card_gap))
            start_x = 30

            for i, book in enumerate(self.books):
                row = i // cols
                col = i % cols

                card_x = start_x + col * (self.card_width + self.card_gap)
                card_y = self.grid_start_y + row * (self.card_height + self.card_gap) - self.scroll_offset

                if card_x <= x < card_x + self.card_width and card_y <= y < card_y + self.card_height:
                    self.show_context_menu = True
                    self.context_menu_pos = pos
                    self.context_menu_book = book
                    return

    def open_book(self, book: Dict):
        """Afficher une popup de confirmation avant d'ouvrir un livre"""
        self.selected_book = book
        self.show_open_confirmation = True

    def confirm_open_book(self):
        """Ouvrir un livre avec l'application par défaut après confirmation"""
        import subprocess
        import platform

        if not self.selected_book:
            return

        file_path = str(self.selected_book['path'])

        try:
            if platform.system() == 'Windows':
                # Windows: utiliser os.startfile
                import os
                os.startfile(file_path)
                print(f"Ouverture de: {self.selected_book['name']}")
            elif platform.system() == 'Darwin':
                # macOS: utiliser open
                subprocess.run(['open', file_path])
                print(f"Ouverture de: {self.selected_book['name']}")
            else:
                # Linux: utiliser xdg-open
                subprocess.run(['xdg-open', file_path])
                print(f"Ouverture de: {self.selected_book['name']}")
        except Exception as e:
            print(f"Erreur lors de l'ouverture de {self.selected_book['name']}: {e}")

        self.show_open_confirmation = False

    def copy_book(self, book: Dict):
        """Copier un livre vers un autre emplacement"""
        import shutil

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        destination = filedialog.askdirectory(title="Sélectionner le dossier de destination")
        root.destroy()

        if destination:
            source_path = book['path']
            dest_path = Path(destination) / book['name']

            try:
                shutil.copy2(source_path, dest_path)
                print(f"Livre copié: {book['name']} → {destination}")
            except Exception as e:
                print(f"Erreur lors de la copie de {book['name']}: {e}")

        self.show_context_menu = False

    def delete_book(self, book: Dict):
        """Effacer un livre (demander confirmation)"""
        self.selected_book = book
        self.show_delete_confirmation = True
        self.show_context_menu = False

    def confirm_delete_book(self):
        """Confirmer et effacer le livre"""
        import os

        if not self.selected_book:
            return

        try:
            os.remove(self.selected_book['path'])
            print(f"Livre supprimé: {self.selected_book['name']}")

            # Retirer le livre de la liste
            self.books = [b for b in self.books if b['path'] != self.selected_book['path']]

            # Nettoyer le cache
            path_str = str(self.selected_book['path'])
            if path_str in self.cover_cache:
                del self.cover_cache[path_str]
            if path_str in self.cover_cache_order:
                self.cover_cache_order.remove(path_str)

            self.update_scroll_limits()
        except Exception as e:
            print(f"Erreur lors de la suppression de {self.selected_book['name']}: {e}")

        self.show_delete_confirmation = False

    def show_book_details(self, book: Dict):
        """Afficher les détails d'un livre dans une popup"""
        self.selected_book = book
        self.show_details_popup = True

        # Charger les métadonnées si pas déjà fait
        path_str = str(book['path'])
        if path_str not in self.book_metadata:
            if book['type'] == 'epub':
                self.book_metadata[path_str] = self.load_epub_metadata(book['path'])
            elif book['type'] == 'pdf':
                self.book_metadata[path_str] = self.load_pdf_metadata(book['path'])
            else:
                self.book_metadata[path_str] = {}

    def load_epub_metadata(self, epub_path: Path) -> Dict:
        """Charger les métadonnées d'un EPUB"""
        metadata = {
            'title': '',
            'author': '',
            'publisher': '',
            'description': '',
            'language': '',
            'date': ''
        }

        try:
            with zipfile.ZipFile(epub_path, 'r') as zf:
                container = zf.read('META-INF/container.xml')
                root = ET.fromstring(container)

                ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = root.find('.//c:rootfile', ns)
                if rootfile is None:
                    return metadata

                opf_path = rootfile.get('full-path')
                opf_content = zf.read(opf_path)
                opf_root = ET.fromstring(opf_content)

                # Namespace Dublin Core
                dc_ns = {'dc': 'http://purl.org/dc/elements/1.1/'}

                # Extraire les métadonnées
                title_el = opf_root.find('.//dc:title', dc_ns)
                if title_el is not None and title_el.text:
                    metadata['title'] = title_el.text

                author_el = opf_root.find('.//dc:creator', dc_ns)
                if author_el is not None and author_el.text:
                    metadata['author'] = author_el.text

                publisher_el = opf_root.find('.//dc:publisher', dc_ns)
                if publisher_el is not None and publisher_el.text:
                    metadata['publisher'] = publisher_el.text

                description_el = opf_root.find('.//dc:description', dc_ns)
                if description_el is not None and description_el.text:
                    metadata['description'] = description_el.text

                language_el = opf_root.find('.//dc:language', dc_ns)
                if language_el is not None and language_el.text:
                    metadata['language'] = language_el.text

                date_el = opf_root.find('.//dc:date', dc_ns)
                if date_el is not None and date_el.text:
                    metadata['date'] = date_el.text
        except:
            pass

        return metadata

    def load_pdf_metadata(self, pdf_path: Path) -> Dict:
        """Charger les métadonnées d'un PDF"""
        metadata = {
            'title': '',
            'author': '',
            'publisher': '',
            'description': '',
            'language': '',
            'date': ''
        }

        if PdfReader:
            try:
                with open(pdf_path, 'rb') as f:
                    pdf = PdfReader(f)
                    info = pdf.metadata

                    if info:
                        if info.title:
                            metadata['title'] = info.title
                        if info.author:
                            metadata['author'] = info.author
                        if info.producer:
                            metadata['publisher'] = info.producer
                        if info.subject:
                            metadata['description'] = info.subject
                        if info.creation_date:
                            metadata['date'] = str(info.creation_date)
            except:
                pass

        return metadata

    def format_file_size(self, size: int) -> str:
        """Formater la taille de fichier"""
        for unit in ['octets', 'Ko', 'Mo', 'Go']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} To"

    def clean_html_tags(self, text: str) -> str:
        """Nettoyer les balises HTML d'un texte"""
        import re
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Convertir les entités HTML courantes
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def execute_action(self, action: str):
        """Exécuter une action de menu"""
        if action == 'open':
            self.open_folder_dialog(False)
        elif action == 'open_recursive':
            self.open_folder_dialog(True)
        elif action == 'quit':
            self.running = False
        elif action == 'refresh':
            if self.current_directory:
                self.scan_directory(self.current_directory)
        elif action == 'sort_name':
            self.books.sort(key=lambda x: x['name'].lower())
        elif action == 'sort_size':
            self.books.sort(key=lambda x: x['size'], reverse=True)
        elif action == 'search_regex':
            self.open_regex_search_dialog()
        elif action == 'show_all':
            self.show_all_books()

    def open_regex_search_dialog(self):
        """Ouvrir le dialogue de recherche regex"""
        import re
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        pattern = simpledialog.askstring(
            "Recherche par regex",
            "Entrez un pattern regex pour filtrer les noms de fichiers:\n(ex: .*Tolkien.*, ^Le.*epub$, .*[0-9]{4}.*)"
        )

        root.destroy()

        if pattern:
            try:
                # Compiler le pattern pour vérifier qu'il est valide
                regex = re.compile(pattern, re.IGNORECASE)

                # Filtrer les livres
                self.books = [book for book in self.all_books if regex.search(book['name'])]
                self.search_pattern = pattern
                self.scroll_offset = 0
                self.update_scroll_limits()

                print(f"Recherche '{pattern}': {len(self.books)} livre(s) trouvé(s)")
            except re.error as e:
                print(f"Pattern regex invalide: {e}")

    def show_all_books(self):
        """Afficher tous les livres (supprimer le filtre)"""
        self.books = self.all_books.copy()
        self.search_pattern = None
        self.scroll_offset = 0
        self.update_scroll_limits()
        print(f"Affichage de tous les livres: {len(self.books)} livre(s)")

    def render(self):
        """Dessiner l'écran"""
        self.screen.fill(self.COLOR_BG)

        # Header (sans la barre de menu en haut)
        pygame.draw.rect(self.screen, self.COLOR_HEADER, (0, 0, self.width, 100))

        # Titre
        title = self.font_big.render("Visualiseur EPUB & PDF", True, self.COLOR_WHITE)
        self.screen.blit(title, (30, 10))

        # Menu à droite du titre
        menu_end_x = self.render_menu()

        # Bouton Retour (si on n'est pas à la racine) - à droite du menu
        if self.current_directory and self.current_directory.parent != self.current_directory:
            back_button_x = menu_end_x + 20
            back_button_y = 10
            back_button_width = 100
            back_button_height = 30

            # Fond du bouton
            pygame.draw.rect(self.screen, (60, 80, 180),
                           (back_button_x, back_button_y, back_button_width, back_button_height))
            pygame.draw.rect(self.screen, (200, 200, 200),
                           (back_button_x, back_button_y, back_button_width, back_button_height), 2)

            # Texte du bouton
            back_text = self.font_small.render("← Retour", True, self.COLOR_WHITE)
            text_x = back_button_x + (back_button_width - back_text.get_width()) // 2
            text_y = back_button_y + (back_button_height - back_text.get_height()) // 2
            self.screen.blit(back_text, (text_x, text_y))

            # Stocker les coordonnées pour la détection de clic
            self.back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
        else:
            self.back_button_rect = None

        # Info
        if self.books:
            # Compter les dossiers et les livres
            num_folders = sum(1 for b in self.books if b.get('type') == 'folder')
            num_books = len(self.books) - num_folders

            if self.search_pattern:
                info = f"{num_books}/{len(self.all_books)} livre(s) - Filtre: {self.search_pattern}"
            else:
                if num_folders > 0:
                    info = f"{num_folders} dossier(s) et {num_books} livre(s) - Cache: {len(self.cover_cache)}/{self.max_cache_size}"
                else:
                    info = f"{num_books} livre(s) - Cache: {len(self.cover_cache)}/{self.max_cache_size}"
            info_text = self.font_small.render(info, True, self.COLOR_WHITE)
            self.screen.blit(info_text, (30, 50))

        # Grille de livres (avec clipping pour ne pas déborder sur le header)
        clip_rect = pygame.Rect(0, self.grid_start_y, self.width, self.height - self.grid_start_y)
        self.screen.set_clip(clip_rect)
        self.render_books()
        self.screen.set_clip(None)  # Désactiver le clipping

        # Scrollbar
        if self.max_scroll > 0:
            self.render_scrollbar()

        # Popup de détails (au-dessus de tout)
        if self.show_details_popup and self.selected_book:
            self.render_details_popup()

        # Popup de confirmation d'ouverture (au-dessus de tout)
        if self.show_open_confirmation and self.selected_book:
            self.render_open_confirmation_popup()

        # Menu contextuel (au-dessus de tout)
        if self.show_context_menu and self.context_menu_book:
            self.render_context_menu()

        # Popup de confirmation de suppression (au-dessus de tout)
        if self.show_delete_confirmation and self.selected_book:
            self.render_delete_confirmation_popup()

        pygame.display.flip()

    def render_menu(self):
        """Dessiner la barre de menu à droite du titre"""
        # Position de départ du menu (à droite du titre)
        menu_x = 450  # À droite du titre "Visualiseur EPUB & PDF"
        menu_y = 10

        for i, menu in enumerate(self.menus):
            text = self.font_small.render(menu['label'], True, self.COLOR_WHITE)
            menu_width = text.get_width() + 20

            # Fond si survolé/ouvert
            if self.menu_open == i:
                pygame.draw.rect(self.screen, self.COLOR_MENU_HOVER, (menu_x, menu_y, menu_width, 25))

            self.screen.blit(text, (menu_x + 10, menu_y + 5))

            # Sous-menu
            if self.menu_open == i:
                submenu_y = menu_y + 25
                submenu_width = 180
                item_height = 25
                submenu_height = len(menu['items']) * item_height

                pygame.draw.rect(self.screen, self.COLOR_MENU_HOVER,
                               (menu_x, submenu_y, submenu_width, submenu_height))
                pygame.draw.rect(self.screen, (100, 100, 100),
                               (menu_x, submenu_y, submenu_width, submenu_height), 1)

                for j, item in enumerate(menu['items']):
                    item_text = self.font_small.render(item['label'], True, self.COLOR_WHITE)
                    self.screen.blit(item_text, (menu_x + 10, submenu_y + j * item_height + 5))

            menu_x += menu_width

        # Retourner la position finale du menu
        return menu_x

    def render_books(self):
        """Dessiner la grille de livres"""
        if not self.books:
            # Message vide
            empty_text = self.font_normal.render("Aucun livre. Ouvrez un dossier.", True, (200, 200, 200))
            self.screen.blit(empty_text, (self.width // 2 - 100, self.height // 2))
            return

        cols = max(1, (self.width - 60) // (self.card_width + self.card_gap))
        start_x = 30

        # Calculer la plage de lignes visibles pour optimiser
        first_visible_row = max(0, (self.scroll_offset - self.card_height) // (self.card_height + self.card_gap))
        last_visible_row = (self.scroll_offset + self.height) // (self.card_height + self.card_gap) + 1

        # Ne parcourir que les livres potentiellement visibles
        start_index = first_visible_row * cols
        end_index = min(len(self.books), (last_visible_row + 1) * cols)

        for i in range(start_index, end_index):
            book = self.books[i]
            row = i // cols
            col = i % cols

            x = start_x + col * (self.card_width + self.card_gap)
            y = self.grid_start_y + row * (self.card_height + self.card_gap) - self.scroll_offset

            # Ne dessiner que si visible
            if y + self.card_height < self.grid_start_y or y > self.height:
                continue

            self.render_book_card(x, y, book)

    def render_book_card(self, x: int, y: int, book: Dict):
        """Dessiner une carte de livre ou dossier"""
        # Fond carte
        pygame.draw.rect(self.screen, self.COLOR_CARD, (x, y, self.card_width, self.card_height))
        pygame.draw.rect(self.screen, (180, 180, 180), (x, y, self.card_width, self.card_height), 1)

        # Zone couverture
        cover_height = 200

        # Si c'est un dossier, afficher une icône de dossier
        if book['type'] == 'folder':
            pygame.draw.rect(self.screen, (255, 200, 100), (x, y, self.card_width, cover_height))

            # Icône dossier (emoji ou texte)
            folder_icon = self.font_big.render("📁", True, self.COLOR_WHITE)
            icon_x = x + (self.card_width - folder_icon.get_width()) // 2
            icon_y = y + cover_height // 2 - 30
            self.screen.blit(folder_icon, (icon_x, icon_y))
        else:
            pygame.draw.rect(self.screen, self.COLOR_CARD_COVER, (x, y, self.card_width, cover_height))

            # Couverture ou placeholder
            path_str = str(book['path'])
            cover = self.get_cover_surface(book)

            if cover:
                cx = x + (self.card_width - cover.get_width()) // 2
                cy = y + (cover_height - cover.get_height()) // 2
                self.screen.blit(cover, (cx, cy))
            else:
                # Vérifier si en cours de chargement
                is_loading = path_str in self.cover_loading and path_str not in self.cover_cache

                if is_loading and book['type'] == 'epub':
                    # Afficher "..." pour indiquer le chargement
                    loading_text = self.font_normal.render("...", True, self.COLOR_WHITE)
                    lx = x + (self.card_width - loading_text.get_width()) // 2
                    ly = y + cover_height // 2 - 10
                    self.screen.blit(loading_text, (lx, ly))
                else:
                    # Placeholder texte
                    type_text = "EPUB" if book['type'] == 'epub' else "PDF"
                    placeholder = self.font_big.render(type_text, True, self.COLOR_WHITE)
                    px = x + (self.card_width - placeholder.get_width()) // 2
                    py = y + cover_height // 2 - 15
                    self.screen.blit(placeholder, (px, py))

        # Nom du fichier
        name = book['name']
        if name.lower().endswith('.epub'):
            name = name[:-5]
        elif name.lower().endswith('.pdf'):
            name = name[:-4]

        if len(name) > 22:
            name = name[:19] + "..."

        name_text = self.font_small.render(name, True, self.COLOR_TEXT_DARK)
        self.screen.blit(name_text, (x + 5, y + cover_height + 10))

        # Type et taille
        size_kb = book['size'] / 1024
        if size_kb > 1024:
            size_str = f"{size_kb/1024:.1f} Mo"
        else:
            size_str = f"{size_kb:.0f} Ko"

        info = f"{book['type'].upper()} - {size_str}"
        info_text = self.font_small.render(info, True, (100, 100, 100))
        self.screen.blit(info_text, (x + 5, y + cover_height + 30))

    def render_scrollbar(self):
        """Dessiner la scrollbar"""
        bar_y = self.grid_start_y
        bar_height = self.height - self.grid_start_y - 10

        # Track (fond)
        pygame.draw.rect(self.screen, self.COLOR_SCROLLBAR,
                        (self.scrollbar_x, bar_y, self.scrollbar_width, bar_height))

        # Thumb (curseur)
        if self.max_scroll > 0:
            thumb_ratio = self.height / (self.height + self.max_scroll)
            thumb_height = max(30, bar_height * thumb_ratio)
            thumb_y = bar_y + (bar_height - thumb_height) * (self.scroll_offset / self.max_scroll)

            # Couleur plus foncée si en train de glisser
            thumb_color = (70, 70, 70) if self.scrollbar_dragging else self.COLOR_SCROLLBAR_THUMB
            pygame.draw.rect(self.screen, thumb_color,
                           (self.scrollbar_x, thumb_y, self.scrollbar_width, thumb_height))

    def render_details_popup(self):
        """Dessiner la popup de détails d'un livre"""
        # Overlay semi-transparent
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dimensions de la popup
        popup_width = 700
        popup_height = 550
        popup_x = (self.width - popup_width) // 2
        popup_y = (self.height - popup_height) // 2

        # Fond de la popup
        pygame.draw.rect(self.screen, self.COLOR_WHITE, (popup_x, popup_y, popup_width, popup_height))
        pygame.draw.rect(self.screen, self.COLOR_HEADER, (popup_x, popup_y, popup_width, popup_height), 2)

        # Bouton fermer (X)
        close_btn_x = popup_x + popup_width - 40
        close_btn_y = popup_y + 10
        pygame.draw.circle(self.screen, (220, 220, 220), (close_btn_x + 15, close_btn_y + 15), 15)
        close_text = self.font_normal.render("×", True, (100, 100, 100))
        self.screen.blit(close_text, (close_btn_x + 7, close_btn_y + 2))

        # Récupérer les métadonnées
        path_str = str(self.selected_book['path'])
        metadata = self.book_metadata.get(path_str, {})

        # Couverture à gauche
        cover_x = popup_x + 20
        cover_y = popup_y + 50
        cover_surface = self.get_cover_surface(self.selected_book, request_load=True)

        if cover_surface:
            # Redimensionner pour la popup (plus grande)
            cover_w, cover_h = cover_surface.get_size()
            max_cover_height = 400
            scale = min(200 / cover_w, max_cover_height / cover_h)
            new_w = int(cover_w * scale)
            new_h = int(cover_h * scale)
            scaled_cover = pygame.transform.smoothscale(cover_surface, (new_w, new_h))
            self.screen.blit(scaled_cover, (cover_x, cover_y))
            info_x = cover_x + new_w + 30
        else:
            # Placeholder
            placeholder_rect = pygame.Rect(cover_x, cover_y, 180, 260)
            pygame.draw.rect(self.screen, (240, 240, 240), placeholder_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), placeholder_rect, 2)
            info_x = cover_x + 180 + 30

        # Informations à droite
        info_y = popup_y + 50
        line_height = 30

        # Titre
        title = metadata.get('title', self.selected_book['name'])
        if not title:
            title = self.selected_book['name']

        # Limiter la longueur du titre
        if len(title) > 50:
            title = title[:47] + "..."

        title_surface = self.font_big.render(title, True, self.COLOR_HEADER)
        self.screen.blit(title_surface, (info_x, info_y))
        info_y += 40

        # Auteur
        author = metadata.get('author', 'Auteur inconnu')
        if author:
            author_label = self.font_normal.render("Auteur:", True, (100, 100, 100))
            author_text = self.font_normal.render(author, True, (50, 50, 50))
            self.screen.blit(author_label, (info_x, info_y))
            self.screen.blit(author_text, (info_x + 80, info_y))
            info_y += line_height

        # Éditeur
        publisher = metadata.get('publisher', '')
        if publisher:
            pub_label = self.font_normal.render("Éditeur:", True, (100, 100, 100))
            # Limiter la longueur
            if len(publisher) > 40:
                publisher = publisher[:37] + "..."
            pub_text = self.font_normal.render(publisher, True, (50, 50, 50))
            self.screen.blit(pub_label, (info_x, info_y))
            self.screen.blit(pub_text, (info_x + 80, info_y))
            info_y += line_height

        # Date
        date = metadata.get('date', '')
        if date:
            date_label = self.font_normal.render("Date:", True, (100, 100, 100))
            date_text = self.font_normal.render(date[:10], True, (50, 50, 50))  # Limiter aux 10 premiers caractères
            self.screen.blit(date_label, (info_x, info_y))
            self.screen.blit(date_text, (info_x + 80, info_y))
            info_y += line_height

        # Langue
        language = metadata.get('language', '')
        if language:
            lang_label = self.font_normal.render("Langue:", True, (100, 100, 100))
            lang_text = self.font_normal.render(language, True, (50, 50, 50))
            self.screen.blit(lang_label, (info_x, info_y))
            self.screen.blit(lang_text, (info_x + 80, info_y))
            info_y += line_height

        # Taille du fichier
        file_size = self.format_file_size(self.selected_book['size'])
        size_label = self.font_normal.render("Taille:", True, (100, 100, 100))
        size_text = self.font_normal.render(file_size, True, (50, 50, 50))
        self.screen.blit(size_label, (info_x, info_y))
        self.screen.blit(size_text, (info_x + 80, info_y))
        info_y += line_height + 10

        # Résumé/Description
        description = metadata.get('description', '')
        if description:
            # Nettoyer les balises HTML
            description = self.clean_html_tags(description)

            desc_label = self.font_normal.render("Résumé:", True, (100, 100, 100))
            self.screen.blit(desc_label, (info_x, info_y))
            info_y += line_height

            # Découper le texte pour le wrapping
            max_chars_per_line = 45
            words = description.split()
            lines = []
            current_line = ""

            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars_per_line:
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "

            if current_line:
                lines.append(current_line.strip())

            # Limiter à 8 lignes maximum
            max_lines = 8
            for i, line in enumerate(lines[:max_lines]):
                if i == max_lines - 1 and len(lines) > max_lines:
                    line += "..."
                desc_text = self.font_small.render(line, True, (80, 80, 80))
                self.screen.blit(desc_text, (info_x, info_y))
                info_y += 22

        # Indication pour fermer
        close_hint = self.font_small.render("Cliquez sur X ou appuyez sur ESC pour fermer", True, (150, 150, 150))
        self.screen.blit(close_hint, (popup_x + popup_width // 2 - 160, popup_y + popup_height - 30))

    def render_open_confirmation_popup(self):
        """Dessiner la popup de confirmation d'ouverture"""
        # Overlay semi-transparent
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dimensions de la popup
        popup_width = 400
        popup_height = 200
        popup_x = (self.width - popup_width) // 2
        popup_y = (self.height - popup_height) // 2

        # Fond de la popup
        pygame.draw.rect(self.screen, self.COLOR_WHITE, (popup_x, popup_y, popup_width, popup_height))
        pygame.draw.rect(self.screen, self.COLOR_HEADER, (popup_x, popup_y, popup_width, popup_height), 2)

        # Titre
        title_text = self.font_big.render("Ouvrir le livre ?", True, self.COLOR_HEADER)
        title_x = popup_x + (popup_width - title_text.get_width()) // 2
        self.screen.blit(title_text, (title_x, popup_y + 20))

        # Nom du livre
        book_name = self.selected_book['name']
        if len(book_name) > 45:
            book_name = book_name[:42] + "..."

        name_text = self.font_normal.render(book_name, True, (80, 80, 80))
        name_x = popup_x + (popup_width - name_text.get_width()) // 2
        self.screen.blit(name_text, (name_x, popup_y + 70))

        # Message
        msg_text = self.font_small.render("Voulez-vous ouvrir ce livre ?", True, (100, 100, 100))
        msg_x = popup_x + (popup_width - msg_text.get_width()) // 2
        self.screen.blit(msg_text, (msg_x, popup_y + 100))

        # Bouton Oui
        btn_yes_x = popup_x + 50
        btn_yes_y = popup_y + popup_height - 60
        btn_yes_w = 120
        btn_yes_h = 40
        pygame.draw.rect(self.screen, (60, 160, 80), (btn_yes_x, btn_yes_y, btn_yes_w, btn_yes_h))
        pygame.draw.rect(self.screen, (40, 140, 60), (btn_yes_x, btn_yes_y, btn_yes_w, btn_yes_h), 2)
        yes_text = self.font_normal.render("Oui", True, self.COLOR_WHITE)
        yes_x = btn_yes_x + (btn_yes_w - yes_text.get_width()) // 2
        yes_y = btn_yes_y + (btn_yes_h - yes_text.get_height()) // 2
        self.screen.blit(yes_text, (yes_x, yes_y))

        # Bouton Non
        btn_no_x = popup_x + popup_width - 170
        btn_no_y = popup_y + popup_height - 60
        btn_no_w = 120
        btn_no_h = 40
        pygame.draw.rect(self.screen, (160, 60, 60), (btn_no_x, btn_no_y, btn_no_w, btn_no_h))
        pygame.draw.rect(self.screen, (140, 40, 40), (btn_no_x, btn_no_y, btn_no_w, btn_no_h), 2)
        no_text = self.font_normal.render("Non", True, self.COLOR_WHITE)
        no_x = btn_no_x + (btn_no_w - no_text.get_width()) // 2
        no_y = btn_no_y + (btn_no_h - no_text.get_height()) // 2
        self.screen.blit(no_text, (no_x, no_y))

    def render_context_menu(self):
        """Dessiner le menu contextuel"""
        menu_x, menu_y = self.context_menu_pos
        menu_width = 200
        item_height = 35
        menu_height = 3 * item_height

        # Fond du menu
        pygame.draw.rect(self.screen, (240, 240, 240), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (100, 100, 100), (menu_x, menu_y, menu_width, menu_height), 2)

        # Items du menu
        items = [
            ("📖 Lire le livre", (60, 160, 80)),
            ("📁 Copier vers...", (60, 120, 180)),
            ("🗑️ Effacer", (180, 60, 60))
        ]

        for i, (label, color) in enumerate(items):
            item_y = menu_y + i * item_height

            # Fond de l'item
            pygame.draw.rect(self.screen, color, (menu_x + 2, item_y + 2, menu_width - 4, item_height - 4))

            # Texte
            text = self.font_normal.render(label, True, self.COLOR_WHITE)
            text_x = menu_x + 10
            text_y = item_y + (item_height - text.get_height()) // 2
            self.screen.blit(text, (text_x, text_y))

    def render_delete_confirmation_popup(self):
        """Dessiner la popup de confirmation de suppression"""
        # Overlay semi-transparent
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dimensions de la popup
        popup_width = 400
        popup_height = 200
        popup_x = (self.width - popup_width) // 2
        popup_y = (self.height - popup_height) // 2

        # Fond de la popup
        pygame.draw.rect(self.screen, self.COLOR_WHITE, (popup_x, popup_y, popup_width, popup_height))
        pygame.draw.rect(self.screen, (200, 60, 60), (popup_x, popup_y, popup_width, popup_height), 3)

        # Titre
        title_text = self.font_big.render("⚠️ Supprimer le livre ?", True, (200, 60, 60))
        title_x = popup_x + (popup_width - title_text.get_width()) // 2
        self.screen.blit(title_text, (title_x, popup_y + 20))

        # Nom du livre
        book_name = self.selected_book['name']
        if len(book_name) > 45:
            book_name = book_name[:42] + "..."

        name_text = self.font_normal.render(book_name, True, (80, 80, 80))
        name_x = popup_x + (popup_width - name_text.get_width()) // 2
        self.screen.blit(name_text, (name_x, popup_y + 70))

        # Message d'avertissement
        msg_text = self.font_small.render("Cette action est irréversible !", True, (200, 60, 60))
        msg_x = popup_x + (popup_width - msg_text.get_width()) // 2
        self.screen.blit(msg_text, (msg_x, popup_y + 100))

        # Bouton Oui
        btn_yes_x = popup_x + 50
        btn_yes_y = popup_y + popup_height - 60
        btn_yes_w = 120
        btn_yes_h = 40
        pygame.draw.rect(self.screen, (200, 60, 60), (btn_yes_x, btn_yes_y, btn_yes_w, btn_yes_h))
        pygame.draw.rect(self.screen, (160, 40, 40), (btn_yes_x, btn_yes_y, btn_yes_w, btn_yes_h), 2)
        yes_text = self.font_normal.render("Supprimer", True, self.COLOR_WHITE)
        yes_x = btn_yes_x + (btn_yes_w - yes_text.get_width()) // 2
        yes_y = btn_yes_y + (btn_yes_h - yes_text.get_height()) // 2
        self.screen.blit(yes_text, (yes_x, yes_y))

        # Bouton Non
        btn_no_x = popup_x + popup_width - 170
        btn_no_y = popup_y + popup_height - 60
        btn_no_w = 120
        btn_no_h = 40
        pygame.draw.rect(self.screen, (100, 100, 100), (btn_no_x, btn_no_y, btn_no_w, btn_no_h))
        pygame.draw.rect(self.screen, (80, 80, 80), (btn_no_x, btn_no_y, btn_no_w, btn_no_h), 2)
        no_text = self.font_normal.render("Annuler", True, self.COLOR_WHITE)
        no_x = btn_no_x + (btn_no_w - no_text.get_width()) // 2
        no_y = btn_no_y + (btn_no_h - no_text.get_height()) // 2
        self.screen.blit(no_text, (no_x, no_y))


def main():
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    print("=" * 50)
    print("Visualiseur EPUB & PDF")
    print("=" * 50)
    print("Ctrl+O : Ouvrir un dossier")
    print("Clic gauche : Voir les détails")
    print("Clic droit : Lire le livre")
    print("Molette : Défiler")
    print("Echap : Quitter")
    print("=" * 50)

    app = EPDFViewer()
    app.run()


if __name__ == '__main__':
    main()
