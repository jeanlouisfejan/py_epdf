"""
Gestionnaire de livres - Extraction des métadonnées EPUB et PDF
"""

from pathlib import Path
from typing import List, Dict, Optional
import zipfile
from xml.etree import ElementTree as ET
from io import BytesIO

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from ebooklib import epub
except ImportError:
    epub = None

from PIL import Image


class BookManager:
    """Gestionnaire des livres EPUB et PDF"""

    def __init__(self):
        self.books: List[Dict] = []
        self.current_directory: Optional[Path] = None

    def scan_directory(self, directory: Path, recursive: bool = False):
        """Scanner un dossier pour trouver les fichiers EPUB et PDF"""
        self.books.clear()
        self.current_directory = directory

        if recursive:
            # Recherche récursive
            epub_files = list(directory.rglob("*.epub"))
            pdf_files = list(directory.rglob("*.pdf"))
        else:
            # Recherche dans le dossier actuel uniquement
            epub_files = list(directory.glob("*.epub"))
            pdf_files = list(directory.glob("*.pdf"))

        # Traiter les fichiers EPUB
        for epub_file in epub_files:
            book_info = {
                'name': epub_file.name,
                'path': epub_file,
                'type': 'epub',
                'size': epub_file.stat().st_size
            }
            self.books.append(book_info)

        # Traiter les fichiers PDF
        for pdf_file in pdf_files:
            book_info = {
                'name': pdf_file.name,
                'path': pdf_file,
                'type': 'pdf',
                'size': pdf_file.stat().st_size
            }
            self.books.append(book_info)

        # Trier par nom
        self.books.sort(key=lambda x: x['name'].lower())

        print(f"Trouvé {len(self.books)} livres dans {directory}")

    def get_current_books(self) -> List[Dict]:
        """Obtenir la liste des livres actuels"""
        return self.books

    def get_book_at_index(self, index: int) -> Optional[Dict]:
        """Obtenir un livre à un index donné"""
        if 0 <= index < len(self.books):
            return self.books[index]
        return None

    def load_epub_metadata(self, book: Dict) -> Dict:
        """Charger les métadonnées d'un fichier EPUB"""
        metadata = {
            'title': book['name'].replace('.epub', ''),
            'author': 'Auteur inconnu',
            'publisher': '',
            'date': '',
            'language': '',
            'description': '',
            'isbn': ''
        }

        try:
            with zipfile.ZipFile(book['path'], 'r') as zip_file:
                # Lire container.xml pour trouver le fichier OPF
                container_xml = zip_file.read('META-INF/container.xml')
                container_root = ET.fromstring(container_xml)

                # Namespace EPUB
                ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = container_root.find('.//container:rootfile', ns)

                if rootfile is not None:
                    opf_path = rootfile.get('full-path')

                    # Lire le fichier OPF
                    opf_xml = zip_file.read(opf_path)
                    opf_root = ET.fromstring(opf_xml)

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

                    date_el = opf_root.find('.//dc:date', dc_ns)
                    if date_el is not None and date_el.text:
                        metadata['date'] = date_el.text

                    language_el = opf_root.find('.//dc:language', dc_ns)
                    if language_el is not None and language_el.text:
                        metadata['language'] = language_el.text

                    description_el = opf_root.find('.//dc:description', dc_ns)
                    if description_el is not None and description_el.text:
                        metadata['description'] = description_el.text

                    identifier_el = opf_root.find('.//dc:identifier', dc_ns)
                    if identifier_el is not None and identifier_el.text:
                        metadata['isbn'] = identifier_el.text

        except Exception as e:
            print(f"Erreur lors du chargement des métadonnées EPUB pour {book['name']}: {e}")

        return metadata

    def load_pdf_metadata(self, book: Dict) -> Dict:
        """Charger les métadonnées d'un fichier PDF"""
        metadata = {
            'title': book['name'].replace('.pdf', ''),
            'author': 'Auteur inconnu',
            'publisher': '',
            'date': '',
            'language': '',
            'description': '',
            'isbn': ''
        }

        if PdfReader is None:
            print("PyPDF2 n'est pas installé")
            return metadata

        try:
            with open(book['path'], 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                info = pdf_reader.metadata

                if info:
                    if info.title:
                        metadata['title'] = info.title
                    if info.author:
                        metadata['author'] = info.author
                    if info.producer:
                        metadata['publisher'] = info.producer
                    if info.creation_date:
                        metadata['date'] = str(info.creation_date)
                    if info.subject:
                        metadata['description'] = info.subject

        except Exception as e:
            print(f"Erreur lors du chargement des métadonnées PDF pour {book['name']}: {e}")

        return metadata

    def extract_epub_cover(self, book: Dict) -> Optional[Image.Image]:
        """Extraire la couverture d'un fichier EPUB"""
        try:
            with zipfile.ZipFile(book['path'], 'r') as zip_file:
                # Lire container.xml
                container_xml = zip_file.read('META-INF/container.xml')
                container_root = ET.fromstring(container_xml)

                ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = container_root.find('.//container:rootfile', ns)

                if rootfile is not None:
                    opf_path = rootfile.get('full-path')
                    opf_dir = str(Path(opf_path).parent)

                    # Lire le fichier OPF
                    opf_xml = zip_file.read(opf_path)
                    opf_root = ET.fromstring(opf_xml)

                    # Chercher la métadonnée de couverture
                    cover_meta = opf_root.find('.//{*}meta[@name="cover"]')

                    if cover_meta is not None:
                        cover_id = cover_meta.get('content')
                        cover_item = opf_root.find(f'.//{"{*}"}item[@id="{cover_id}"]')

                        if cover_item is not None:
                            cover_href = cover_item.get('href')
                            cover_path = f"{opf_dir}/{cover_href}" if opf_dir else cover_href

                            # Lire l'image
                            cover_data = zip_file.read(cover_path)
                            image = Image.open(BytesIO(cover_data))
                            return image

                    # Si pas trouvé, chercher dans le manifest
                    for item in opf_root.findall('.//{*}item'):
                        href = item.get('href', '')
                        if 'cover' in href.lower() and any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png']):
                            cover_path = f"{opf_dir}/{href}" if opf_dir else href
                            cover_data = zip_file.read(cover_path)
                            image = Image.open(BytesIO(cover_data))
                            return image

        except Exception as e:
            print(f"Erreur lors de l'extraction de la couverture EPUB pour {book['name']}: {e}")

        return None

    def extract_pdf_cover(self, book: Dict) -> Optional[Image.Image]:
        """Extraire la première page d'un PDF comme couverture"""
        if PdfReader is None:
            return None

        try:
            # Pour simplifier, on retourne None ici
            # L'extraction d'image PDF nécessite des bibliothèques supplémentaires
            # comme pdf2image qui nécessite poppler
            print(f"Extraction de couverture PDF non implémentée pour {book['name']}")
            return None

        except Exception as e:
            print(f"Erreur lors de l'extraction de la couverture PDF pour {book['name']}: {e}")

        return None

    def format_file_size(self, size: int) -> str:
        """Formater la taille de fichier"""
        for unit in ['octets', 'Ko', 'Mo', 'Go']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} To"
