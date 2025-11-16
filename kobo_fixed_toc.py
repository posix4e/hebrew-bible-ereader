#!/usr/bin/env python3
"""
Kobo-optimized Hebrew Bible EPUB generator with fixed TOC
Simplified, flatter TOC structure that renders properly on Kobo
"""

import time
import requests
from typing import Dict
from ebooklib import epub


class KoboOptimizedEPUB:
    def __init__(self):
        self.book = epub.EpubBook()
        self.book.set_identifier("hebrew-bible-kobo-fixed")
        self.book.set_title("Hebrew Bible - Kobo Edition")
        self.book.set_language("he")
        self.book.add_metadata("DC", "language", "en")

        self.torah_books = [
            ("Genesis", "בראשית", "Bereshit"),
            ("Exodus", "שמות", "Shemot"),
            ("Leviticus", "ויקרא", "Vayikra"),
            ("Numbers", "במדבר", "Bamidbar"),
            ("Deuteronomy", "דברים", "Devarim"),
        ]

        self.chapters = []

    def get_chapter_count(self, book_name: str) -> int:
        """Get the actual number of chapters in a book"""
        try:
            url = f"https://www.sefaria.org/api/texts/{book_name}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if "lengths" in data and len(data["lengths"]) > 0:
                return data["lengths"][0]

            # Fallback to known counts
            known_counts = {
                "Genesis": 50,
                "Exodus": 40,
                "Leviticus": 27,
                "Numbers": 36,
                "Deuteronomy": 34,
            }
            return known_counts.get(book_name, 10)

        except Exception as e:
            print(f"Error getting chapter count for {book_name}: {e}")
            return 10  # Fallback

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

    def create_simple_css(self) -> str:
        """Create simple CSS optimized for Kobo"""
        return """
        @charset "UTF-8";

        body {
            margin: 1em;
            font-family: serif;
            line-height: 1.5;
        }

        /* Simple title styling */
        h1, h2 {
            text-align: center;
            page-break-after: avoid;
            margin: 1em 0;
        }

        h1 {
            font-size: 1.5em;
        }

        h2 {
            font-size: 1.3em;
        }

        /* Hebrew text */
        .hebrew {
            direction: rtl;
            text-align: right;
            font-size: 1.1em;
            margin: 0.5em 0;
        }

        /* English text */
        .english {
            direction: ltr;
            text-align: left;
            margin: 0.5em 0;
        }

        /* Verse container */
        .verse {
            margin: 1em 0;
            clear: both;
        }

        /* Verse numbers */
        .verse-num {
            font-weight: bold;
            color: #666;
            display: inline;
            margin-right: 0.5em;
        }

        /* Simple two-column for landscape (Kobo compatible) */
        @media (orientation: landscape) and (min-device-width: 1000px) {
            .verse {
                width: 100%;
                overflow: hidden;
            }

            .hebrew {
                float: right;
                width: 48%;
                clear: none;
            }

            .english {
                float: left;
                width: 48%;
                clear: none;
            }
        }

        /* Kobo-specific adjustments */
        @media (device-width: 758px) and (device-height: 1024px),
               (device-width: 1264px) and (device-height: 1680px) {
            body {
                margin: 0.5em;
            }
        }
        """

    def create_chapter_html(
        self, book_name: str, hebrew_name: str, chapter_num: int, text_data: Dict
    ) -> str:
        """Create simple HTML optimized for Kobo"""
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
    <h1>{book_name} {chapter_num}</h1>
    <h2 class="hebrew">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</h2>
"""

        max_verses = max(len(hebrew_verses), len(english_verses))

        for i in range(max_verses):
            hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
            english = english_verses[i] if i < len(english_verses) else ""

            # Clean up text
            if isinstance(hebrew, list):
                hebrew = " ".join(hebrew)
            if isinstance(english, list):
                english = " ".join(english)

            # Remove problematic HTML
            import re

            hebrew = re.sub(r"<[^>]+>", "", hebrew)
            english = re.sub(r"<[^>]+>", "", english)

            html += f"""
    <div class="verse">
        <div class="hebrew">
            <span class="verse-num">{self.hebrew_number(i + 1)}</span>
            {hebrew}
        </div>
        <div class="english">
            <span class="verse-num">{i + 1}.</span>
            {english}
        </div>
    </div>
"""

        html += """
</body>
</html>"""
        return html

    def hebrew_number(self, num: int) -> str:
        """Convert to Hebrew numerals"""
        ones = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
        tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]

        if num < 10:
            return ones[num] + "."
        elif num < 100:
            return tens[num // 10] + ones[num % 10] + "."
        else:
            return str(num) + "."

    def generate_kobo_epub(self, output_filename: str = "torah_kobo_fixed.epub"):
        """Generate Kobo-optimized EPUB with simplified TOC"""
        print("Generating Kobo-optimized Torah EPUB...")

        # Add CSS
        css = epub.EpubItem(
            uid="style",
            file_name="styles.css",
            media_type="text/css",
            content=self.create_simple_css(),
        )
        self.book.add_item(css)

        # SIMPLIFIED FLAT TOC - Much better for Kobo!
        flat_toc = []

        for book_idx, (english_name, hebrew_name, transliteration) in enumerate(self.torah_books):
            print(f"Processing {english_name}...")

            # Add a simple book title page
            book_html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{english_name}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div style="text-align: center; margin-top: 30%;">
        <h1>{english_name}</h1>
        <h1 class="hebrew" style="font-size: 2em;">{hebrew_name}</h1>
        <p>{transliteration}</p>
    </div>
</body>
</html>"""

            book_page = epub.EpubHtml(
                title=f"{english_name}",
                file_name=f"{english_name.lower()}_title.xhtml",
                content=book_html,
                lang="he",
            )
            book_page.add_item(css)
            self.book.add_item(book_page)
            self.chapters.append(book_page)

            # Add to flat TOC
            flat_toc.append(book_page)

            # Get actual chapter count from API
            chapter_count = self.get_chapter_count(english_name)
            print(f"  Total chapters: {chapter_count}")

            # Generate ALL chapters
            for chapter_num in range(1, chapter_count + 1):
                print(f"  Chapter {chapter_num}")

                text_data = self.fetch_text(english_name, chapter_num)

                if text_data["hebrew"] or text_data["english"]:
                    html_content = self.create_chapter_html(
                        english_name, hebrew_name, chapter_num, text_data
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

                    # Add directly to flat TOC - no nesting!
                    flat_toc.append(chapter)

                time.sleep(0.1)  # Be nice to API

        # Set the FLAT table of contents - Kobo handles this much better
        self.book.toc = flat_toc

        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Define spine
        self.book.spine = ["nav"] + self.chapters

        # Write EPUB
        print(f"\nWriting Kobo-optimized EPUB to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})
        print(f"✅ Kobo-optimized EPUB generated: {output_filename}")

        # Give tips
        print("\n📱 Kobo Tips:")
        print("  - Use Kobo's built-in TOC (tap center, then Contents)")
        print("  - Adjust font size with Kobo's Aa menu")
        print("  - Landscape mode will show side-by-side text")
        print("  - Portrait mode will stack Hebrew above English")

        return output_filename


if __name__ == "__main__":
    generator = KoboOptimizedEPUB()
    generator.generate_kobo_epub()
