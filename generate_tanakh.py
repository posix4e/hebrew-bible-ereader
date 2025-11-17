#!/usr/bin/env python3
"""
Tanakh EPUB Generator for Kobo Libra Colour
Generates a responsive Hebrew/English Bible with custom artwork
"""

import time
import argparse
import re
from pathlib import Path
from typing import Dict, Optional
import json

import requests
from ebooklib import epub
from PIL import Image
from jinja2 import Environment, FileSystemLoader
import io


class TanakhGenerator:
    def __init__(self):
        # Initialize tracking for Chagall images
        self.all_chagall_images = []  # Flat list of all images for distribution
        self.chagall_index = 0  # Track which image to use next

        # Load Chagall images configuration
        self.chagall_images = self._load_chagall_images()

        # Load definitive per-chapter placements if available
        self.chagall_chapter_map = self._load_chagall_placements()

        # Load optional per-book intro image overrides
        self.book_intro_overrides = self._load_book_intro_overrides()

        # Full Tanakh - all books Jews expect
        self.books = [
            # TORAH
            ("Genesis", "בראשית", "Bereshit", 50),
            ("Exodus", "שמות", "Shemot", 40),
            ("Leviticus", "ויקרא", "Vayikra", 27),
            ("Numbers", "במדבר", "Bamidbar", 36),
            ("Deuteronomy", "דברים", "Devarim", 34),
            # NEVI'IM (Prophets)
            ("Joshua", "יהושע", "Yehoshua", 24),
            ("Judges", "שופטים", "Shoftim", 21),
            ("I_Samuel", "שמואל א", "Shmuel_Aleph", 31),
            ("II_Samuel", "שמואל ב", "Shmuel_Bet", 24),
            ("I_Kings", "מלכים א", "Melachim_Aleph", 22),
            ("II_Kings", "מלכים ב", "Melachim_Bet", 25),
            ("Isaiah", "ישעיהו", "Yeshayahu", 66),
            ("Jeremiah", "ירמיהו", "Yirmeyahu", 52),
            ("Ezekiel", "יחזקאל", "Yechezkel", 48),
            ("Hosea", "הושע", "Hoshea", 14),
            ("Joel", "יואל", "Yoel", 4),
            ("Amos", "עמוס", "Amos", 9),
            ("Obadiah", "עובדיה", "Ovadiah", 1),
            ("Jonah", "יונה", "Yonah", 4),
            ("Micah", "מיכה", "Michah", 7),
            ("Nahum", "נחום", "Nachum", 3),
            ("Habakkuk", "חבקוק", "Chavakuk", 3),
            ("Zephaniah", "צפניה", "Tzefaniah", 3),
            ("Haggai", "חגי", "Chaggai", 2),
            ("Zechariah", "זכריה", "Zechariah", 14),
            ("Malachi", "מלאכי", "Malachi", 3),
            # KETUVIM (Writings)
            ("Psalms", "תהילים", "Tehillim", 150),
            ("Proverbs", "משלי", "Mishlei", 31),
            ("Job", "איוב", "Iyov", 42),
            ("Song_of_Songs", "שיר השירים", "Shir_HaShirim", 8),
            ("Ruth", "רות", "Rut", 4),
            ("Lamentations", "איכה", "Eicha", 5),
            ("Ecclesiastes", "קהלת", "Kohelet", 12),
            ("Esther", "אסתר", "Esther", 10),
            ("Daniel", "דניאל", "Daniel", 12),
            ("Ezra", "עזרא", "Ezra", 10),
            ("Nehemiah", "נחמיה", "Nechemya", 13),
            ("I_Chronicles", "דברי הימים א", "Divrei_HaYamim_Aleph", 29),
            ("II_Chronicles", "דברי הימים ב", "Divrei_HaYamim_Bet", 36),
        ]

        # Image mappings for user's artwork - each used once
        self.image_map = {
            ("Genesis", 1): "creation.jpg",  # Creation of the world
            ("Genesis", 22): "sacrificeofabraham.jpg",  # Abraham and Isaac
            ("Exodus", 3): "moses.jpg",  # Moses and burning bush
            ("Joshua", 24): "joshuarockofschem.jpg",  # Joshua at Shechem
            ("I_Samuel", 16): "davidwithhisharp.jpg",  # David chosen as king
            ("I_Kings", 3): "solomon.jpg",  # Solomon's wisdom
            ("Jeremiah", 31): "promisetojerusalem.jpg",  # New covenant promise
            ("Ezekiel", 37): "mysticalcrucifixion.jpg",  # Valley of dry bones vision
        }

        # Set up Jinja2 templates
        self.template_env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

    def _load_chagall_images(self) -> Dict:
        """Load Chagall images mapping from config"""
        chagall_map = {}

        # Try to load from config file
        config_path = Path("chagall_download_config.json")
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)

            # Group images by book
            for item in config:
                book = item["book"]
                if book not in chagall_map:
                    chagall_map[book] = []

                # Check if the image file actually exists
                img_path = Path("images") / item["filename"]
                if img_path.exists():
                    image_data = {
                        "filename": item["filename"],
                        "title": item["title"],
                        "path": str(img_path),
                        "book": book,
                    }
                    chagall_map[book].append(image_data)
                    self.all_chagall_images.append(image_data)

            print(f"  ✓ Loaded {len(self.all_chagall_images)} Chagall images")

        return chagall_map

    def _select_book_image(self, book_name: str) -> Optional[Dict]:
        """Pick an appropriate Chagall image for a given book if available.

        Strategy:
        - Use the first image listed in the config for this book
          (already filtered to existing files).
        - Return a dict with keys: filename, title, path, book;
          or None if unavailable.
        """
        # Respect override if available
        override = self.book_intro_overrides.get(book_name)
        images = self.chagall_images.get(book_name)
        if override and images:
            for img in images:
                if img.get("filename") == override:
                    return img
        if images:
            return images[0]
        return None

    def create_book_intro_page(self, book_name: str, hebrew_name: str) -> Optional[epub.EpubHtml]:
        """Create a decorative intro page for a book with a representative image."""
        img = self._select_book_image(book_name)
        if not img:
            return None

        page = epub.EpubHtml(
            title=f"{book_name} - Introduction",
            file_name=f"{book_name}_intro.xhtml",
            lang="en",
        )

        html = f"""
        <!DOCTYPE html>
        <html xmlns=\"http://www.w3.org/1999/xhtml\">
        <head>
            <title>{book_name} - Introduction</title>
            <link rel=\"stylesheet\" type=\"text/css\" href=\"style.css\"/>
            <style>
                .book-intro {{ text-align:center; margin: 10% auto 5%; }}
                .book-intro h1 {{ font-size: 1.6em; margin: 0.2em 0; }}
                .book-intro h2 {{ font-size: 1.2em; margin: 0.2em 0; color: #555; }}
                .book-intro .img-wrap {{ margin-top: 1.2em; }}
                .book-intro img {{ max-width: 90%; height:auto; }}
                .book-intro .caption {{ font-size: 0.9em; color: #666; margin-top: 0.6em; }}
            </style>
        </head>
        <body>
            <div class=\"book-intro\">
                <h1>{book_name}</h1>
                <h2>{hebrew_name}</h2>
                <div class=\"img-wrap\">
                    <img src=\"images/{img['filename']}\" alt=\"{img['title']}\"/>
                    <div class=\"caption\">{img['title']}</div>
                </div>
            </div>
        </body>
        </html>
        """
        page.content = html
        return page

    def _load_chagall_placements(self) -> Dict:
        """Load filename -> ["Book Chapter"] mapping and build (book,chapter)->[filenames]."""
        mapping_path = Path("chagall_placement_map.json")
        chapter_map = {}
        if mapping_path.exists():
            try:
                with open(mapping_path, "r") as f:
                    placement = json.load(f)
                for filename, chapters in placement.items():
                    for ref in chapters:
                        try:
                            book, chap_str = ref.rsplit(" ", 1)
                            chap = int(chap_str)
                        except Exception:
                            continue
                        chapter_map.setdefault((book, chap), []).append(filename)
                print(f"  ✓ Loaded Chagall chapter placements for {len(placement)} images")
            except Exception:
                pass
        return chapter_map

    def _load_book_intro_overrides(self) -> Dict:
        """Load optional mapping: book -> filename for intro page images."""
        mapping_path = Path("book_intro_overrides.json")
        if mapping_path.exists():
            try:
                with open(mapping_path, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    print(f"  ✓ Loaded book intro overrides for {len(data)} books")
                    return data
            except Exception:
                pass
        return {}

    def get_css(self) -> str:
        """Load CSS from template file"""
        css_path = Path("templates/style_minimal.css")
        if css_path.exists():
            return css_path.read_text()
        else:
            # Fallback to inline CSS if template not found
            return self._get_fallback_css()

    def _get_fallback_css(self) -> str:
        """Fallback CSS if template file not found"""
        return """
        body { font-family: Georgia, serif; line-height: 1.6; margin: 1em; }
        .chapter-container { margin: 0 auto; padding: 1em; }
        .hebrew-text { direction: rtl; text-align: right; font-size: 1.3em; }
        .english-text { direction: ltr; text-align: left; font-size: 1.1em; }
        .verse-number { font-weight: bold; color: #667eea; font-size: 0.9em; margin: 0 0.3em; }
        """

    def fetch_text(self, book: str, chapter: int) -> Dict:
        """Fetch Hebrew and English text from Sefaria API"""
        url = f"https://www.sefaria.org/api/texts/{book}.{chapter}"
        params = {
            "ven": "The_Koren_Jerusalem_Bible",  # Clean English version
            "vhe": "Tanach_with_Nikkud",  # Clean Hebrew with vowels
            "commentary": 0,
            "context": 1,
            "pad": 0,
            "wrapLinks": 0,
            "wrapNamedEntities": 0,
            "stripmarkers": 1,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2)
        return {}

    def create_chapter_responsive(
        self, book_name: str, hebrew_name: str, chapter_num: int, chapter_count: int
    ) -> Optional[epub.EpubHtml]:
        """Create a chapter with responsive Hebrew/English layout"""
        print(f"  Chapter {chapter_num}/{chapter_count}")

        data = self.fetch_text(book_name, chapter_num)
        if not data or "he" not in data or "text" not in data:
            return None

        hebrew_text = data["he"]
        english_text = data["text"]

        if isinstance(hebrew_text, str):
            hebrew_text = [hebrew_text]
        if isinstance(english_text, str):
            english_text = [english_text]

        # Clean and filter verses
        hebrew_verses = []
        for v in hebrew_text:
            if v:
                clean_v = re.sub(r"<[^>]+>", "", v)
                clean_v = re.sub(r"\s+", " ", clean_v)
                clean_v = clean_v.strip()
                if clean_v:
                    hebrew_verses.append(clean_v)

        english_verses = []
        for v in english_text:
            if v:
                clean_v = re.sub(r"<[^>]+>", "", v)
                clean_v = re.sub(r"\s+", " ", clean_v)
                clean_v = clean_v.strip()
                if clean_v:
                    english_verses.append(clean_v)

        # Check for image
        image_file = self.image_map.get((book_name, chapter_num))

        # Prefer definitive Chagall placements when no original artwork is set
        if not image_file and self.chagall_chapter_map:
            files = self.chagall_chapter_map.get((book_name, chapter_num))
            if files:
                image_file = files[0]

        # Create chapter
        chapter = epub.EpubHtml(
            title=f"{book_name} {chapter_num}",
            file_name=f"{book_name}_{chapter_num}.xhtml",
            lang="he",
        )

        # Build HTML with responsive layout
        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{book_name} {chapter_num}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="chapter-container">
        <div class="chapter-header">
            <h1>{book_name} {chapter_num}</h1>
            <h2>{hebrew_name} פרק {self.to_hebrew_numeral(chapter_num)}</h2>
        </div>"""

        if image_file:
            html += f"""
        <div class="chapter-image">
            <img src="images/{image_file}" alt="{book_name} Chapter {chapter_num}"/>
            <div class="image-caption">{book_name} Chapter {chapter_num}</div>
        </div>"""

        html += """
        <div class="verses-container">"""

        # Add verses - simple, no wrapper
        max_verses = max(len(hebrew_verses), len(english_verses))
        for i in range(max_verses):
            if i < len(hebrew_verses):
                html += f"""
            <div class="hebrew-verse">
                <span class="verse-number">{i + 1}</span>{hebrew_verses[i]}
            </div>"""

            if i < len(english_verses):
                html += f"""
            <div class="english-verse">
                <span class="verse-number">{i + 1}</span>{english_verses[i]}
            </div>"""

        html += """
        </div>
    </div>
</body>
</html>"""

        chapter.content = html
        return chapter

    def create_chapter(
        self, book_name: str, hebrew_name: str, chapter_num: int, chapter_count: int
    ) -> Optional[epub.EpubHtml]:
        """Create a chapter with Hebrew/English text and optional images"""
        print(f"  Chapter {chapter_num}/{chapter_count}")

        data = self.fetch_text(book_name, chapter_num)
        if not data or "he" not in data or "text" not in data:
            return None

        hebrew_text = data["he"]
        english_text = data["text"]

        if isinstance(hebrew_text, str):
            hebrew_text = [hebrew_text]
        if isinstance(english_text, str):
            english_text = [english_text]

        # Clean and filter verses (minimal cleaning needed with clean API versions)
        hebrew_verses = []
        for v in hebrew_text:
            if v:
                # Just in case there are any remaining HTML artifacts
                clean_v = re.sub(r"<[^>]+>", "", v)  # Remove any HTML tags
                clean_v = re.sub(r"\s+", " ", clean_v)  # Normalize whitespace
                clean_v = clean_v.strip()
                if clean_v:  # Only add non-empty verses
                    hebrew_verses.append(clean_v)

        english_verses = []
        for v in english_text:
            if v:
                # Just in case there are any remaining HTML artifacts
                clean_v = re.sub(r"<[^>]+>", "", v)  # Remove any HTML tags
                clean_v = re.sub(r"\s+", " ", clean_v)  # Normalize whitespace
                clean_v = clean_v.strip()
                if clean_v:  # Only add non-empty verses
                    english_verses.append(clean_v)

        # Create chapter
        chapter = epub.EpubHtml(
            title=f"{book_name} {chapter_num}",
            file_name=f"{book_name}_{chapter_num}.xhtml",
            lang="he",
        )

        # Check for image - first try original artwork, then definitive Chagall placement
        image_file = self.image_map.get((book_name, chapter_num)) or (
            self.chagall_chapter_map.get((book_name, chapter_num), [None])[0]
        )

        # Try to use template
        try:
            template = self.template_env.get_template("chapter.html")
            html_content = template.render(
                book_name=book_name,
                hebrew_name=hebrew_name,
                chapter_num=chapter_num,
                hebrew_chapter_num=self.to_hebrew_numeral(chapter_num),
                image_file=image_file,
                hebrew_verses=hebrew_verses,
                english_verses=english_verses,
            )
        except Exception:
            # Fallback to inline HTML if template not found
            html_content = self._create_fallback_html(
                book_name, hebrew_name, chapter_num, image_file, hebrew_verses, english_verses
            )

        chapter.content = html_content
        return chapter

    def _create_fallback_html(
        self,
        book_name: str,
        hebrew_name: str,
        chapter_num: int,
        image_file: Optional[str],
        hebrew_verses: list,
        english_verses: list,
    ) -> str:
        """Fallback HTML generation if template not found"""
        html = f"""
        <div class="chapter-container">
            <div class="header-section">
                <h1>{book_name} {chapter_num}</h1>
                <h2>{hebrew_name} פרק {self.to_hebrew_numeral(chapter_num)}</h2>
            </div>
        """

        if image_file:
            html += f"""
            <div class="image-container">
                <img src="images/{image_file}" alt="{book_name} Chapter {chapter_num}"/>
                <div class="image-caption">{book_name} Chapter {chapter_num}</div>
            </div>
            """

        html += '<div class="content-layout">'

        # Hebrew section
        html += '<div class="text-section hebrew-section"><div class="hebrew-text">'
        for i, verse in enumerate(hebrew_verses, 1):
            html += f'<span class="verse-number">{i}</span>{verse} '
        html += "</div></div>"

        # English section
        html += '<div class="text-section english-section"><div class="english-text">'
        for i, verse in enumerate(english_verses, 1):
            html += f'<span class="verse-number">{i}</span>{verse} '
        html += "</div></div>"

        html += "</div></div>"
        return html

    def to_hebrew_numeral(self, num: int) -> str:
        """Convert number to Hebrew numeral"""
        ones = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
        tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
        hundreds = ["", "ק", "ר", "ש", "ת"]

        if num >= 1000:
            return str(num)

        result = ""
        if num >= 100:
            result += hundreds[num // 100]
            num %= 100
        if num >= 10:
            result += tens[num // 10]
            num %= 10
        if num > 0:
            result += ones[num]

        if len(result) > 1:
            result = result[:-1] + "״" + result[-1:]
        elif len(result) == 1:
            result = result + "׳"

        return result

    def generate(
        self, output_file: str = "tanakh.epub", test_mode: bool = False, test2_mode: bool = False
    ):
        """Generate the complete Tanakh EPUB"""
        print("=" * 60)
        print("Tanakh EPUB Generator for Kobo Libra Colour")
        print("=" * 60)

        # Create EPUB
        book = epub.EpubBook()
        book.set_identifier("tanakh-kobo-2024")
        book.set_title("Tanakh - Hebrew Bible")
        book.set_language("he")
        book.add_author("Sefaria.org")

        # Add cover image
        cover_path = Path("images/chagall_moses_tablets_cover.jpg")
        if cover_path.exists():
            with open(cover_path, "rb") as f:
                book.set_cover("cover.jpg", f.read())
            print("  ✓ Added cover image")

        # Add CSS
        css = epub.EpubItem(
            uid="style", file_name="style.css", media_type="text/css", content=self.get_css()
        )
        book.add_item(css)

        # Embed Hebrew font
        font_path = Path("NotoSerifHebrew-Regular.ttf")
        if font_path.exists():
            with open(font_path, "rb") as f:
                font_item = epub.EpubItem(
                    uid="hebrew-font",
                    file_name="fonts/NotoSerifHebrew-Regular.ttf",
                    media_type="application/x-font-ttf",
                    content=f.read(),
                )
                book.add_item(font_item)
                print("  ✓ Embedded Hebrew font")

        # Embed images
        image_dir = Path("images")
        if image_dir.exists():
            images = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.jpeg"))
            for img_path in images:
                with open(img_path, "rb") as f:
                    img = Image.open(f)
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=85, optimize=True)

                    img_item = epub.EpubImage(
                        uid=f"img-{img_path.stem}",
                        file_name=f"images/{img_path.name}",
                        media_type="image/jpeg",
                        content=output.getvalue(),
                    )
                    book.add_item(img_item)
            print(f"  ✓ Embedded {len(images)} illustrations\n")

        # Create dedication page
        dedication_html = """
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <title>Dedication</title>
            <link rel="stylesheet" type="text/css" href="style.css"/>
            <style>
                .dedication {
                    margin: 30% auto;
                    text-align: center;
                    font-style: italic;
                    max-width: 80%;
                }
                .dedication h2 {
                    font-size: 1.5em;
                    margin-bottom: 1em;
                    font-weight: normal;
                }
                .dedication p {
                    font-size: 1.1em;
                    line-height: 1.8;
                    margin: 0.5em 0;
                }
                .dedication .name {
                    font-size: 1.2em;
                    margin-top: 2em;
                    font-weight: bold;
                }
                .dedication .link {
                    font-size: 0.9em;
                    margin-top: 1em;
                    color: #667eea;
                }
            </style>
        </head>
        <body>
            <div class="dedication">
                <h2>Dedication</h2>
                <p>This edition of the Tanakh is dedicated with love to</p>
                <p class="name">Bruno "DaVenzia" Naphtali</p>
                <p>He saved my life</p>
                <p class="link">
                    <a href="https://www.instagram.com/brunodavenzia/">@brunodavenzia</a>
                </p>
            </div>
        </body>
        </html>
        """

        dedication = epub.EpubHtml(title="Dedication", file_name="dedication.xhtml", lang="en")
        dedication.content = dedication_html
        dedication.add_item(css)
        book.add_item(dedication)

        # Add Chagall attribution page if we have Chagall images
        if self.chagall_images:
            attribution_html = """
            <!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <title>Artwork Attribution</title>
                <link rel="stylesheet" type="text/css" href="style.css"/>
                <style>
                    .attribution {
                        margin: 20% auto;
                        text-align: center;
                        max-width: 80%;
                    }
                    .attribution h2 {
                        font-size: 1.4em;
                        margin-bottom: 1em;
                    }
                    .attribution p {
                        font-size: 1em;
                        line-height: 1.6;
                        margin: 0.5em 0;
                    }
                    .attribution .artist {
                        font-weight: bold;
                        font-size: 1.1em;
                        margin: 1em 0;
                    }
                    .attribution .source {
                        font-style: italic;
                        color: #667eea;
                        margin-top: 1.5em;
                    }
                    .attribution a {
                        color: #667eea;
                        text-decoration: none;
                    }
                </style>
            </head>
            <body>
                <div class="attribution">
                    <h2>Artwork Attribution</h2>
                    <p class="artist">Marc Chagall Bible Illustrations</p>
                    <p>This edition includes beautiful Bible illustrations by Marc Chagall,</p>
                    <p>one of the most celebrated artists of the 20th century.</p>
                    <p>His unique vision brings the ancient texts to life with</p>
                    <p>vibrant colors and dreamlike imagery.</p>
                    <p class="source">
                        Images courtesy of artchive.com<br/>
                        <a href="https://www.artchive.com/?s=chagall+bible">
                            www.artchive.com/?s=chagall+bible
                        </a>
                    </p>
                </div>
            </body>
            </html>
            """

            attribution = epub.EpubHtml(
                title="Artwork Attribution", file_name="attribution.xhtml", lang="en"
            )
            attribution.content = attribution_html
            attribution.add_item(css)
            book.add_item(attribution)

        # Process books
        spine = ["nav", dedication]
        toc = [dedication]

        # Add attribution to spine if it exists
        if self.chagall_images:
            spine.append(attribution)
            toc.append(attribution)

        # Determine which books to process
        books_to_process = self.books
        if test2_mode:
            # test2 mode: only first 3 books, first 3 chapters each
            books_to_process = self.books[:3]
            print("🧪 TEST2 MODE: Processing only first 3 books (Genesis, Exodus, Leviticus)")
            print("              with first 3 chapters each\n")

        for book_info in books_to_process:
            english_name, hebrew_name, transliteration, chapter_count = book_info

            # Test mode - only first 3 chapters
            if test_mode or test2_mode:
                chapter_count = min(3, chapter_count)

            print(f"📖 Processing {english_name}...")

            book_chapters = []

            # Add a book intro page (if we have an associated image)
            intro_page = self.create_book_intro_page(english_name, hebrew_name)
            if intro_page:
                intro_page.add_item(css)
                book.add_item(intro_page)
                spine.append(intro_page)
                book_chapters.append(intro_page)
            for chapter_num in range(1, chapter_count + 1):
                chapter = self.create_chapter_responsive(
                    english_name, hebrew_name, chapter_num, chapter_count
                )
                if chapter:
                    chapter.add_item(css)
                    book.add_item(chapter)
                    spine.append(chapter)
                    book_chapters.append(chapter)

            if book_chapters:
                toc.append((epub.Section(f"{english_name} - {hebrew_name}"), book_chapters))

        # Set navigation
        book.toc = toc
        book.spine = spine
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Write EPUB
        print(f"\n📝 Writing to {output_file}...")
        epub.write_epub(output_file, book, {})
        print(f"✅ Generated: {output_file}\n")


def main():
    parser = argparse.ArgumentParser(description="Generate Tanakh EPUB for Kobo")
    parser.add_argument("-o", "--output", default="tanakh.epub", help="Output filename")
    parser.add_argument("--test", action="store_true", help="Test mode - only 3 chapters per book")
    parser.add_argument(
        "--test2", action="store_true", help="Test2 mode - only first 3 books, 3 chapters each"
    )

    args = parser.parse_args()

    generator = TanakhGenerator()
    generator.generate(args.output, args.test, args.test2)


if __name__ == "__main__":
    main()
