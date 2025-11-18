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
        # Optional explicit mapping mode
        self.explicit_enabled = False
        self.explicit_book_intro = {}
        self.explicit_chapter_map = {}
        # Initialize tracking for Chagall images
        self.all_chagall_images = []  # Flat list of all images for distribution
        self.chagall_index = 0  # Track which image to use next

        # Full Tanakh - all books Jews expect (define early for ordering logic)
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

        # Load explicit simple mapping, if present (overrides all logic)
        self._load_explicit_config()

        # Load Chagall images configuration
        self.chagall_images = self._load_chagall_images()

        # Load definitive per-chapter placements if available
        self.chagall_chapter_map = self._load_chagall_placements()

        # Pre-compute a balanced distribution of images across chapters per book
        # using available Chagall images for that book. This avoids bunching
        # images near the end when placements are clustered.
        self.balanced_chapter_map = self._build_balanced_placements()

        # Load optional per-book intro image overrides (ignored if explicit mode)
        self.book_intro_overrides = self._load_book_intro_overrides()

        # Track how each image is used to build an Illustration Index
        # { filename: [
        #     { 'kind': 'intro', 'book': str },
        #     { 'kind': 'chapter', 'book': str, 'chapter': int }
        # ] }
        self.image_usages = {}

        # Enforce unique usage of images across the EPUB
        self.used_images = set()  # set[str]

        # Map filename -> source book as defined in chagall config
        self.source_book_by_filename = {}
        for img in self.all_chagall_images:
            fn = img.get("filename")
            bk = img.get("book") or "General"
            if fn:
                self.source_book_by_filename[fn] = bk

        # For biasing and fairness: maintain order and basic counts
        self.book_order = [b[0] for b in self.books]
        self.source_book_usage_counts = {b: 0 for b in self.book_order + ["General"]}

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

    def _load_explicit_config(self):
        """Load explicit placements if provided in explicit_placements.json.

        Schema:
        {
          "book_intro": { "Genesis": "image.jpg", ... },
          "chapters": [ {"book": "Genesis", "chapter": 1, "image": "file.jpg"}, ... ]
        }
        """
        cfg_path = Path("explicit_placements.json")
        if not cfg_path.exists():
            return
        try:
            data = json.load(open(cfg_path))
            intro = data.get("book_intro", {})
            ch_list = data.get("chapters", [])
            if isinstance(intro, dict) and isinstance(ch_list, list):
                # Build chapter map
                chap_map = {}
                for ent in ch_list:
                    if not isinstance(ent, dict):
                        continue
                    b = ent.get("book")
                    c = ent.get("chapter")
                    f = ent.get("image")
                    if b and isinstance(c, int) and f:
                        chap_map[(b, c)] = f
                self.explicit_book_intro = intro
                self.explicit_chapter_map = chap_map
                self.explicit_enabled = True
                msg = (
                    f"  ✓ Loaded explicit placements: {len(intro)} intros, "
                    f"{len(chap_map)} chapter images"
                )
                print(msg)
        except Exception:
            # Ignore malformed explicit file
            pass

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
        - Prefer an unused image for this book.
        - If override exists, try it only if unused; otherwise look for next unused.
        - Fallback: an unused "General" image.
        - Return a dict with keys: filename, title, path, book;
          or None if unavailable.
        """
        if self.explicit_enabled:
            # In explicit mode, intros are required and chosen exactly
            filename = self.explicit_book_intro.get(book_name)
            if not filename:
                raise ValueError(f"Missing explicit intro image for book: {book_name}")
            # Find the image dict for this filename
            for img in self.all_chagall_images:
                if img.get("filename") == filename:
                    return img
            # If not a Chagall image, allow non-config images too
            img_path = Path("images") / filename
            if not img_path.exists():
                raise FileNotFoundError(f"Intro image not found for {book_name}: {filename}")
            return {
                "filename": filename,
                "title": Path(filename).stem.replace("_", " "),
                "path": str(img_path),
                "book": "General",
            }

        override = self.book_intro_overrides.get(book_name)
        images = self.chagall_images.get(book_name) or []

        # Helper to find first unused in a list of image dicts
        def first_unused(img_list):
            for im in img_list:
                fn = im.get("filename")
                if fn and fn not in self.used_images:
                    return im
            return None

        # Try override if available and unused
        if override:
            for img in images:
                if img.get("filename") == override and img.get("filename") not in self.used_images:
                    return img

        # Try first unused image for this book
        pick = first_unused(images)
        if pick:
            return pick

        # Fallback to "General" pool if available
        general = self.chagall_images.get("General") or []
        pick = first_unused(general)
        if pick:
            return pick
        return None

    def create_book_intro_page(self, book_name: str, hebrew_name: str) -> Optional[epub.EpubHtml]:
        """Create a decorative intro page for a book with a representative image."""
        img = self._select_book_image(book_name)
        if not img:
            return None

        # Record usage as an intro image
        self.image_usages.setdefault(img["filename"], []).append(
            {"kind": "intro", "book": book_name}
        )
        # Emit log line for intro image usage
        print(f"    ↳ Intro image for {book_name}: {img['filename']}")

        # Enforce uniqueness in explicit mode
        if self.explicit_enabled and img["filename"] in self.used_images:
            raise ValueError(f"Image reused across intro/chapters: {img['filename']}")
        # Mark image as used
        self.used_images.add(img["filename"])
        src_bk = self.source_book_by_filename.get(img["filename"], "General")
        self.source_book_usage_counts[src_bk] = self.source_book_usage_counts.get(src_bk, 0) + 1

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
        """Load filename -> "Book Chapter" mapping and build (book,chapter)->[filenames].

        Supports backward-compat with older format where the value was a list of refs; if a list
        is provided, only the first entry is used.
        """
        mapping_path = Path("chagall_placement_map.json")
        chapter_map = {}
        if mapping_path.exists():
            try:
                with open(mapping_path, "r") as f:
                    placement = json.load(f)
                count = 0
                for filename, ref_val in placement.items():
                    # Accept string or list; if list, take the first element
                    if isinstance(ref_val, list):
                        ref = ref_val[0] if ref_val else None
                    else:
                        ref = ref_val
                    if not isinstance(ref, str):
                        continue
                    try:
                        book, chap_str = ref.rsplit(" ", 1)
                        chap = int(chap_str)
                    except Exception:
                        continue
                    chapter_map.setdefault((book, chap), []).append(filename)
                    count += 1
                print(f"  ✓ Loaded Chagall chapter placements for {count} images")
            except Exception:
                pass
        return chapter_map

    def _build_balanced_placements(self) -> Dict:
        """Create a balanced (book, chapter) -> filename mapping.

        Strategy:
        - For each book that has Chagall images in the download config, spread
          those images evenly across the book's chapter range.
        - Uses simple even spacing: floor((i+1)*(chapters+1)/(N+1)).
        - Defers uniqueness enforcement to runtime (we skip used images if
          an intro consumed one earlier).
        """
        balanced = {}
        # Build quick lookup for chapter counts
        chapter_count_by_book = {b[0]: b[3] for b in self.books}

        for book, images in (self.chagall_images or {}).items():
            chapters = chapter_count_by_book.get(book)
            if not chapters or not images:
                continue

            # Keep the declared order from config; take filenames only
            filenames = [im.get("filename") for im in images if im.get("filename")]
            if not filenames:
                continue

            # Limit number of placements to number of chapters
            count = min(len(filenames), chapters)
            # Compute evenly spaced target chapter numbers (1-based)
            targets = [
                max(1, min(chapters, (i + 1) * (chapters + 1) // (count + 1))) for i in range(count)
            ]

            # Assign sequentially; if two targets collide, nudge forward to next free
            used_targets = set()
            fi = 0
            for t in targets:
                # Ensure unique chapter target
                chap = t
                while chap in used_targets and chap <= chapters:
                    chap += 1
                if chap > chapters:
                    # wrap backwards to find free slot
                    chap = t
                    while chap in used_targets and chap >= 1:
                        chap -= 1
                    if chap < 1 or chap in used_targets:
                        # give up if no slot
                        continue
                used_targets.add(chap)
                # Pick next filename
                if fi >= len(filenames):
                    break
                balanced[(book, chap)] = filenames[fi]
                fi += 1

        return balanced

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
        image_file = None
        if self.explicit_enabled:
            image_file = self.explicit_chapter_map.get((book_name, chapter_num))
        else:
            image_file = self.image_map.get((book_name, chapter_num))
        # Fall back to balanced placement schedule
        if not image_file and not self.explicit_enabled:
            image_file = self.balanced_chapter_map.get((book_name, chapter_num))

        # Prefer definitive Chagall placements when no original artwork is set
        # Candidate selection function
        def pick_candidate_for_chapter(book_name: str, chapter_num: int) -> Optional[str]:
            if not self.chagall_chapter_map:
                return None
            files = list(self.chagall_chapter_map.get((book_name, chapter_num)) or [])
            if not files:
                return None

            # Filter to unused
            unused = [f for f in files if f not in self.used_images]
            if not unused:
                return None

            # Score candidates:
            #  - prefer source == book
            #  - then lower usage of source book
            #  - then earlier source book in order
            def score(fn: str):
                src = self.source_book_by_filename.get(fn, "General")
                prefer = 0 if src == book_name else 1
                usage = self.source_book_usage_counts.get(src, 0)
                order = (
                    self.book_order.index(src)
                    if src in self.book_order
                    else len(self.book_order) + 1
                )
                return (prefer, usage, order, fn)

            unused.sort(key=score)
            return unused[0]

        # Respect uniqueness: if original-map image is already used, ignore it
        if image_file and image_file in self.used_images:
            if self.explicit_enabled:
                raise ValueError(f"Image reused across intro/chapters: {image_file}")
            image_file = None

        if not image_file and not self.explicit_enabled:
            image_file = pick_candidate_for_chapter(book_name, chapter_num)

        # Record usage as chapter image if present
        if image_file:
            self.image_usages.setdefault(image_file, []).append(
                {"kind": "chapter", "book": book_name, "chapter": chapter_num}
            )
            # Emit log line for chapter image usage
            print(f"    ↳ Chapter image: {book_name} {chapter_num} -> {image_file}")
            # Mark used and update counts
            self.used_images.add(image_file)
            src_bk = self.source_book_by_filename.get(image_file, "General")
            self.source_book_usage_counts[src_bk] = self.source_book_usage_counts.get(src_bk, 0) + 1

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

    def _image_title_for_filename(self, filename: str) -> str:
        """Best-effort human title for an image filename.
        Prefer title from Chagall config; otherwise derive from filename.
        """
        # Try from loaded Chagall config
        for img in self.all_chagall_images:
            if img.get("filename") == filename:
                return img.get("title") or filename
        # Derive from filename
        stem = Path(filename).stem
        return stem.replace("_", " ").replace("-", " ").strip().title() or filename

    def _usage_label(self, filename: str) -> str:
        """Create a concise label describing how an image is used."""
        usages = self.image_usages.get(filename, [])
        if not usages:
            return "Gallery / Unused"

        parts = []
        # Prefer stable ordering: intro first, then chapters by book/chapter
        intro_parts = [u for u in usages if u.get("kind") == "intro"]
        chap_parts = [u for u in usages if u.get("kind") == "chapter"]
        for u in intro_parts:
            parts.append(f"Book Intro — {u['book']}")
        for u in sorted(chap_parts, key=lambda x: (x.get("book", ""), x.get("chapter", 0))):
            parts.append(f"Chapter — {u['book']} {u['chapter']}")
        return "; ".join(parts) if parts else "Gallery / Unused"

    def _build_illustration_pages(self, book: epub.EpubBook, css: epub.EpubItem):
        """Create a page per image and return (toc_section, pages_list).
        Adds pages to the book and returns an epub.Section and list of page items.
        """
        image_dir = Path("images")
        if not image_dir.exists():
            return None, []

        # Enumerate all JPEG images that were embedded
        all_images = sorted(
            list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.jpeg")),
            key=lambda p: p.name.lower(),
        )

        pages = []
        for img_path in all_images:
            filename = img_path.name
            title_text = self._image_title_for_filename(filename)
            usage_text = self._usage_label(filename)

            page = epub.EpubHtml(
                title=f"Illustration — {title_text}",
                file_name=f"img_{img_path.stem}.xhtml",
                lang="en",
            )
            page_html = f"""
            <!DOCTYPE html>
            <html xmlns=\"http://www.w3.org/1999/xhtml\">
            <head>
                <title>Illustration — {title_text}</title>
                <link rel=\"stylesheet\" type=\"text/css\" href=\"style.css\"/>
                <style>
                    .illustration-page {{ text-align:center; margin: 8% auto 5%; }}
                    .illustration-page h1 {{ font-size: 1.3em; margin: 0.2em 0; }}
                    .illustration-page .usage {{ font-size: 0.95em; color:#666;
                                              margin: 0.4em 0 0.8em; }}
                    .illustration-page img {{ max-width: 92%; height:auto; }}
                    .illustration-page .caption {{ font-size: 0.9em; color:#555;
                                                margin-top: 0.6em; }}
                </style>
            </head>
            <body>
                <div class=\"illustration-page\">
                    <h1>{title_text}</h1>
                    <div class=\"usage\">{usage_text}</div>
                    <img src=\"images/{filename}\" alt=\"{title_text}\"/>
                    <div class=\"caption\">{title_text}</div>
                </div>
            </body>
            </html>
            """
            page.content = page_html
            page.add_item(css)
            book.add_item(page)
            pages.append(page)

        if pages:
            section = epub.Section("Illustration Index")
            return section, pages
        return None, []

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
                # Emit log line for embedded image asset
                print(f"  • Embedded image asset: {img_path.name}")
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

        # After processing all books/chapters, build per-image pages and add to TOC
        illus_section, illus_pages = self._build_illustration_pages(book, css)
        if illus_pages:
            toc.append((illus_section, illus_pages))
            spine.extend(illus_pages)

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
