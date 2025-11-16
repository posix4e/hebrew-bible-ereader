#!/usr/bin/env python3
"""
Torah Bilingual EPUB optimized for landscape side-by-side reading
Perfect for Kobo Color in landscape mode
"""

import time
import requests
import re
from typing import Dict
from ebooklib import epub


class TorahLandscapeBilingual:
    def __init__(self):
        self.book = epub.EpubBook()
        self.book.set_identifier("torah-landscape-bilingual")
        self.book.set_title("Torah - Bilingual Landscape Edition")
        self.book.set_language("he")
        self.book.add_metadata("DC", "language", "en")
        self.book.add_author("Sefaria.org")

        self.torah_books = [
            ("Genesis", "בראשית", "Bereshit", 50),
            ("Exodus", "שמות", "Shemot", 40),
            ("Leviticus", "ויקרא", "Vayikra", 27),
            ("Numbers", "במדבר", "Bamidbar", 36),
            ("Deuteronomy", "דברים", "Devarim", 34),
        ]

        self.chapters = []

    def fetch_text(self, book_name: str, chapter: int) -> Dict:
        """Fetch Hebrew and English text from Sefaria API"""
        try:
            url = f"https://www.sefaria.org/api/texts/{book_name}.{chapter}"
            response = requests.get(url, params={"context": 0})
            response.raise_for_status()
            data = response.json()

            hebrew_text = data.get("he", [])
            english_text = data.get("text", [])

            if isinstance(hebrew_text, str):
                hebrew_text = [hebrew_text]
            if isinstance(english_text, str):
                english_text = [english_text]

            return {"hebrew": hebrew_text, "english": english_text}

        except Exception as e:
            print(f"Error fetching {book_name} chapter {chapter}: {e}")
            return {"hebrew": [], "english": []}

    def create_landscape_css(self) -> str:
        """Create CSS optimized for landscape side-by-side display"""
        return """
        @charset "UTF-8";

        /* Base styles */
        html, body {
            margin: 0;
            padding: 0.5em;
            font-family: serif;
            line-height: 1.6;
            height: 100%;
        }

        /* Chapter header */
        .chapter-header {
            text-align: center;
            margin-bottom: 1em;
            padding-bottom: 0.5em;
            border-bottom: 2px solid #ccc;
            page-break-after: avoid;
        }

        .chapter-title {
            font-size: 1.4em;
            font-weight: bold;
            margin: 0.3em 0;
        }

        /* Main container for side-by-side layout */
        .content-container {
            width: 100%;
            display: table;
            table-layout: fixed;
        }

        /* Side-by-side columns */
        .hebrew-column, .english-column {
            display: table-cell;
            width: 48%;
            padding: 0 1%;
            vertical-align: top;
        }

        .hebrew-column {
            direction: rtl;
            text-align: right;
            border-right: 1px solid #e0e0e0;
        }

        .english-column {
            direction: ltr;
            text-align: left;
        }

        /* Column headers */
        .column-header {
            font-weight: bold;
            text-align: center;
            padding: 0.5em 0;
            margin-bottom: 1em;
            background-color: #f5f5f5;
            border-radius: 4px;
        }

        /* Verse styling */
        .verse {
            margin: 0.8em 0;
            min-height: 2em;
        }

        .verse-number {
            font-weight: bold;
            color: #0066cc;
            display: inline-block;
            min-width: 2em;
            margin-right: 0.5em;
        }

        .hebrew-column .verse-number {
            margin-right: 0;
            margin-left: 0.5em;
        }

        .verse-text {
            display: inline;
            font-size: 1.05em;
        }

        /* Ensure landscape optimization */
        @media (orientation: landscape) {
            .content-container {
                display: table !important;
            }

            .hebrew-column, .english-column {
                display: table-cell !important;
            }
        }

        /* Portrait fallback - stack vertically */
        @media (orientation: portrait) {
            .content-container {
                display: block;
            }

            .hebrew-column, .english-column {
                display: block;
                width: 100%;
                border: none;
                margin-bottom: 0.5em;
            }

            .hebrew-column {
                border-bottom: 1px dotted #ccc;
                padding-bottom: 0.5em;
            }
        }

        /* Kobo Color specific optimizations */
        @media (device-width: 1264px) and (device-height: 1680px) {
            body {
                font-size: 15px;
            }

            .verse-text {
                font-size: 1.1em;
            }
        }

        /* Book divider page */
        .book-divider {
            page-break-before: always;
            text-align: center;
            padding: 30% 0;
        }

        .book-divider h1 {
            font-size: 2.5em;
            margin: 0.5em 0;
        }

        .hebrew-book-title {
            font-size: 3em;
            direction: rtl;
        }

        /* Parsha markers */
        .parsha-marker {
            background-color: #fffacd;
            padding: 0.5em;
            margin: 1em 0;
            text-align: center;
            font-weight: bold;
            border: 1px solid #daa520;
            border-radius: 4px;
        }
        """

    def create_chapter_html(
        self,
        book_name: str,
        hebrew_name: str,
        chapter_num: int,
        text_data: Dict,
        parsha_name: str = None,
    ) -> str:
        """Create HTML optimized for landscape side-by-side display"""
        hebrew_verses = text_data["hebrew"]
        english_verses = text_data["english"]

        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} {chapter_num}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="chapter-header">
        <div class="chapter-title">{book_name} Chapter {chapter_num}</div>
        <div class="chapter-title">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</div>
    </div>
"""

        # Add parsha marker if applicable
        if parsha_name:
            html += f"""
    <div class="parsha-marker">
        פרשת {parsha_name}
    </div>
"""

        # Start side-by-side container
        html += """
    <div class="content-container">
        <div class="hebrew-column">
            <div class="column-header">עברית</div>
"""

        # Add Hebrew verses
        for i, verse in enumerate(hebrew_verses):
            if isinstance(verse, list):
                verse = " ".join(verse)

            # Clean HTML from text
            verse = re.sub(r"<[^>]+>", "", verse)

            html += f"""
            <div class="verse">
                <span class="verse-number">{self.hebrew_number(i + 1)}</span>
                <span class="verse-text">{verse}</span>
            </div>
"""

        # English column
        html += """
        </div>
        <div class="english-column">
            <div class="column-header">English</div>
"""

        # Add English verses
        for i, verse in enumerate(english_verses):
            if isinstance(verse, list):
                verse = " ".join(verse)

            # Clean HTML from text
            verse = re.sub(r"<[^>]+>", "", verse)

            html += f"""
            <div class="verse">
                <span class="verse-number">{i + 1}.</span>
                <span class="verse-text">{verse}</span>
            </div>
"""

        html += """
        </div>
    </div>
</body>
</html>"""
        return html

    def hebrew_number(self, num: int) -> str:
        """Convert to Hebrew numerals"""
        ones = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
        tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]

        if num < 10:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + ones[num % 10]
        else:
            return str(num)

    def get_parsha_for_chapter(self, book: str, chapter: int) -> str:
        """Get parsha name if this chapter starts a new parsha"""
        parshiyot = {
            "Genesis": {
                1: "בראשית",
                6: "נח",
                12: "לך לך",
                18: "וירא",
                23: "חיי שרה",
                25: "תולדות",
                28: "ויצא",
                32: "וישלח",
                37: "וישב",
                41: "מקץ",
                44: "ויגש",
                47: "ויחי",
            },
            "Exodus": {
                1: "שמות",
                6: "וארא",
                10: "בא",
                13: "בשלח",
                18: "יתרו",
                21: "משפטים",
                25: "תרומה",
                27: "תצוה",
                30: "כי תשא",
                35: "ויקהל",
                38: "פקודי",
            },
            # Add more as needed
        }

        book_parshiyot = parshiyot.get(book, {})
        return book_parshiyot.get(chapter, None)

    def generate_epub(
        self, output_filename: str = "torah_landscape_bilingual.epub", full_torah: bool = True
    ):
        """Generate the bilingual landscape-optimized EPUB"""
        print("=" * 60)
        print("Torah Bilingual Landscape Edition Generator")
        print("Optimized for side-by-side reading on e-readers")
        print("=" * 60)

        # Add CSS
        css = epub.EpubItem(
            uid="style",
            file_name="styles.css",
            media_type="text/css",
            content=self.create_landscape_css(),
        )
        self.book.add_item(css)

        # Flat TOC for Kobo compatibility
        flat_toc = []

        for book_data in self.torah_books:
            if len(book_data) == 4:
                english_name, hebrew_name, transliteration, total_chapters = book_data
            else:
                english_name, hebrew_name, transliteration = book_data
                total_chapters = 50  # Default for Genesis

            print(f"\n📖 Processing {english_name}...")

            # Add book divider page
            book_html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{english_name}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="book-divider">
        <h1>{english_name}</h1>
        <h1 class="hebrew-book-title">{hebrew_name}</h1>
        <p style="font-size: 1.2em;">{transliteration}</p>
    </div>
</body>
</html>"""

            book_page = epub.EpubHtml(
                title=english_name,
                file_name=f"{english_name.lower()}_title.xhtml",
                content=book_html,
                lang="he",
            )
            book_page.add_item(css)
            self.book.add_item(book_page)
            self.chapters.append(book_page)
            flat_toc.append(book_page)

            # Generate chapters
            # For testing, limit chapters; for full, use all
            chapters_to_generate = total_chapters if full_torah else min(5, total_chapters)

            for chapter_num in range(1, chapters_to_generate + 1):
                print(f"  Chapter {chapter_num}/{total_chapters}")

                # Check for parsha
                parsha = self.get_parsha_for_chapter(english_name, chapter_num)

                # Fetch text
                text_data = self.fetch_text(english_name, chapter_num)

                if text_data["hebrew"] or text_data["english"]:
                    html_content = self.create_chapter_html(
                        english_name, hebrew_name, chapter_num, text_data, parsha
                    )

                    chapter = epub.EpubHtml(
                        title=f"{english_name} {chapter_num}",
                        file_name=f"{english_name.lower()}_{chapter_num}.xhtml",
                        content=html_content,
                        lang="he",
                    )
                    chapter.add_item(css)

                    self.book.add_item(chapter)
                    self.chapters.append(chapter)
                    flat_toc.append(chapter)

                time.sleep(0.1)  # API courtesy

        # Set TOC
        self.book.toc = flat_toc

        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Define spine
        self.book.spine = ["nav"] + self.chapters

        # Write EPUB
        print(f"\n📝 Writing to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})
        print(f"✅ Generated: {output_filename}")

        print("\n📱 Kobo Tips for Best Experience:")
        print("  • Rotate to LANDSCAPE mode for side-by-side display")
        print("  • Use smallest margins in Kobo settings")
        print("  • Adjust font size with Aa menu")
        print("  • Hebrew on right, English on left")

        return output_filename


if __name__ == "__main__":
    import sys

    # Check if we want full Torah or just sample
    full = "--full" in sys.argv

    generator = TorahLandscapeBilingual()

    if full:
        print("Generating FULL Torah (this will take several minutes)...")
        generator.generate_epub("torah_landscape_bilingual_full.epub", full_torah=True)
    else:
        print("Generating sample (5 chapters per book)...")
        generator.generate_epub("torah_landscape_bilingual_sample.epub", full_torah=False)
