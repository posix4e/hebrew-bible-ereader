#!/usr/bin/env python3
"""
Torah with Hierarchical TOC and Clean Text
Organized as: Book → Chapter → Version with reading continuity
"""

import time
import requests
import re
from typing import Dict
from ebooklib import epub


class TorahHierarchicalTOC:
    def __init__(self):
        self.book = epub.EpubBook()
        self.book.set_identifier("torah-hierarchical-toc")
        self.book.set_title("Torah - Hierarchical Edition")
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
        self.toc_structure = []  # Will hold hierarchical TOC

    def clean_text(self, text: str) -> str:
        """Clean HTML and artifacts from text"""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Fix nbsp artifacts
        text = text.replace("&nbsp;", " ")
        text = text.replace("nbsp&", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&apos;", "'")
        # Clean up any remaining HTML entities
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
        # Clean up extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

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

            # Clean all text
            hebrew_text = [
                self.clean_text(v) if isinstance(v, str) else self.clean_text(" ".join(v))
                for v in hebrew_text
            ]
            english_text = [
                self.clean_text(v) if isinstance(v, str) else self.clean_text(" ".join(v))
                for v in english_text
            ]

            return {"hebrew": hebrew_text, "english": english_text}

        except Exception as e:
            print(f"Error fetching {book_name} chapter {chapter}: {e}")
            return {"hebrew": [], "english": []}

    def create_hierarchical_css(self) -> str:
        """Create CSS for hierarchical navigation"""
        return """
        @charset "UTF-8";

        /* Base styles */
        html, body {
            margin: 0;
            padding: 1em;
            font-family: serif;
            line-height: 1.6;
        }

        /* Navigation menu styles */
        .nav-menu {
            background: #f5f5f5;
            padding: 1.5em;
            margin-bottom: 2em;
            border-radius: 8px;
        }

        .nav-menu h1 {
            text-align: center;
            color: #1a472a;
            margin-bottom: 1em;
        }

        .nav-section {
            margin: 1em 0;
        }

        .nav-section h2 {
            color: #2d5016;
            border-bottom: 2px solid #ccc;
            padding-bottom: 0.3em;
            margin-bottom: 0.5em;
        }

        .nav-list {
            list-style: none;
            padding: 0;
        }

        .nav-list li {
            padding: 0.5em 0;
        }

        .nav-list a {
            text-decoration: none;
            color: #0066cc;
            padding: 0.3em 0.5em;
            display: inline-block;
        }

        .nav-list a:hover {
            background: #e0e0e0;
            border-radius: 4px;
        }

        /* Version selector */
        .version-selector {
            background: #fffacd;
            padding: 1em;
            margin: 1em 0;
            border: 1px solid #daa520;
            border-radius: 4px;
            text-align: center;
        }

        .version-selector h3 {
            margin: 0 0 0.5em 0;
            color: #8b4513;
        }

        .version-links {
            display: flex;
            justify-content: center;
            gap: 1em;
            flex-wrap: wrap;
        }

        .version-links a {
            background: #1a472a;
            color: white;
            padding: 0.5em 1em;
            border-radius: 4px;
            text-decoration: none;
            transition: background 0.3s;
        }

        .version-links a:hover {
            background: #2d5016;
        }

        /* Chapter header */
        .chapter-header {
            text-align: center;
            margin-bottom: 1em;
            padding-bottom: 0.5em;
            border-bottom: 2px solid #ccc;
        }

        .chapter-title {
            font-size: 1.4em;
            font-weight: bold;
            margin: 0.3em 0;
        }

        /* Navigation bar at top/bottom of chapters */
        .chapter-nav {
            background: #f0f0f0;
            padding: 1em;
            margin: 1em 0;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }

        .chapter-nav a {
            color: #0066cc;
            text-decoration: none;
            padding: 0.5em 1em;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
        }

        .chapter-nav a:hover {
            background: #e0e0e0;
        }

        .current-version {
            font-weight: bold;
            color: #8b4513;
        }

        /* Hebrew text */
        .hebrew {
            direction: rtl;
            text-align: right;
            font-size: 1.1em;
        }

        /* Verse styling */
        .verse {
            margin: 0.8em 0;
        }

        .verse-number {
            font-weight: bold;
            color: #0066cc;
            display: inline-block;
            min-width: 2em;
            margin-right: 0.5em;
        }

        .hebrew .verse-number {
            margin-right: 0;
            margin-left: 0.5em;
        }

        .verse-text {
            display: inline;
        }

        /* Side-by-side for bilingual */
        .bilingual-container {
            display: table;
            width: 100%;
            table-layout: fixed;
        }

        .hebrew-column, .english-column {
            display: table-cell;
            width: 48%;
            padding: 0 1%;
            vertical-align: top;
        }

        .hebrew-column {
            border-right: 1px solid #e0e0e0;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .bilingual-container {
                display: block;
            }

            .hebrew-column, .english-column {
                display: block;
                width: 100%;
                border: none;
            }

            .hebrew-column {
                border-bottom: 1px dotted #ccc;
                margin-bottom: 1em;
                padding-bottom: 1em;
            }
        }
        """

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

    def create_chapter_version(
        self, book_name: str, hebrew_name: str, chapter_num: int, text_data: Dict, version: str
    ) -> str:
        """Create a specific version of a chapter"""
        hebrew_verses = text_data["hebrew"]
        english_verses = text_data["english"]

        # Start HTML
        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} {chapter_num} - {version.title()}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="chapter-header">
        <div class="chapter-title">{book_name} Chapter {chapter_num}</div>
        <div class="chapter-title hebrew">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</div>
        <div class="current-version">{version.title()} Version</div>
    </div>

    <!-- Navigation bar -->
    <div class="chapter-nav">
"""

        # Add navigation links
        if chapter_num > 1:
            html += (
                f'        <a href="{book_name.lower()}_{chapter_num - 1}_{version}.xhtml">'
                f"← Previous Chapter</a>\n"
            )
        else:
            html += "        <span></span>\n"

        # Version switcher
        html += f"""
        <div class="version-links">
            <a href="{book_name.lower()}_{chapter_num}_hebrew.xhtml">Hebrew</a>
            <a href="{book_name.lower()}_{chapter_num}_english.xhtml">English</a>
            <a href="{book_name.lower()}_{chapter_num}_bilingual.xhtml">Bilingual</a>
        </div>
"""

        # Next chapter link
        total_chapters = next((b[3] for b in self.torah_books if b[0] == book_name), 0)
        if chapter_num < total_chapters:
            html += (
                f'        <a href="{book_name.lower()}_{chapter_num + 1}_{version}.xhtml">'
                f"Next Chapter →</a>\n"
            )
        else:
            html += "        <span></span>\n"

        html += "    </div>\n\n"

        # Add content based on version
        if version == "hebrew":
            html += '    <div class="hebrew">\n'
            for i, verse in enumerate(hebrew_verses):
                html += f"""
        <div class="verse">
            <span class="verse-number">{self.hebrew_number(i + 1)}</span>
            <span class="verse-text">{verse}</span>
        </div>
"""
            html += "    </div>\n"

        elif version == "english":
            html += '    <div class="english">\n'
            for i, verse in enumerate(english_verses):
                html += f"""
        <div class="verse">
            <span class="verse-number">{i + 1}.</span>
            <span class="verse-text">{verse}</span>
        </div>
"""
            html += "    </div>\n"

        elif version == "bilingual":
            html += '    <div class="bilingual-container">\n'
            html += '        <div class="hebrew-column hebrew">\n'
            for i, verse in enumerate(hebrew_verses):
                html += f"""
            <div class="verse">
                <span class="verse-number">{self.hebrew_number(i + 1)}</span>
                <span class="verse-text">{verse}</span>
            </div>
"""
            html += "        </div>\n"
            html += '        <div class="english-column">\n'
            for i, verse in enumerate(english_verses):
                html += f"""
            <div class="verse">
                <span class="verse-number">{i + 1}.</span>
                <span class="verse-text">{verse}</span>
            </div>
"""
            html += "        </div>\n"
            html += "    </div>\n"

        # Add bottom navigation
        html += """
    <!-- Bottom navigation -->
    <div class="chapter-nav">
"""
        if chapter_num > 1:
            html += (
                f'        <a href="{book_name.lower()}_{chapter_num - 1}_{version}.xhtml">'
                f"← Previous</a>\n"
            )
        else:
            html += "        <span></span>\n"

        html += '        <a href="toc.xhtml">Table of Contents</a>\n'

        if chapter_num < total_chapters:
            html += (
                f'        <a href="{book_name.lower()}_{chapter_num + 1}_{version}.xhtml">'
                f"Next →</a>\n"
            )
        else:
            html += "        <span></span>\n"

        html += """    </div>
</body>
</html>"""

        return html

    def create_toc_page(self) -> str:
        """Create main table of contents page"""
        html = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="nav-menu">
        <h1>Torah - Table of Contents</h1>
        <p style="text-align: center; color: #666; margin-bottom: 2em;">
            Select a book, then a chapter, then choose your reading version
        </p>
"""

        for book_data in self.torah_books:
            english_name, hebrew_name, transliteration, total_chapters = book_data

            html += f"""
        <div class="nav-section">
            <h2>{english_name} - {hebrew_name}</h2>
            <ul class="nav-list">
"""

            # Add chapter links
            for chapter in range(1, min(total_chapters + 1, 11)):  # Show first 10 chapters
                html += f"""
                <li>
                    <a href="{english_name.lower()}_{chapter}_selector.xhtml">
                        Chapter {chapter} - פרק {self.hebrew_number(chapter)}
                    </a>
                </li>
"""

            if total_chapters > 10:
                html += f"""
                <li style="font-style: italic; color: #999;">
                    ... and {total_chapters - 10} more chapters
                </li>
"""

            html += """            </ul>
        </div>
"""

        html += """    </div>
</body>
</html>"""
        return html

    def create_chapter_selector(self, book_name: str, hebrew_name: str, chapter_num: int) -> str:
        """Create version selector page for a chapter"""
        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} {chapter_num} - Select Version</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="chapter-header">
        <div class="chapter-title">{book_name} Chapter {chapter_num}</div>
        <div class="chapter-title hebrew">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</div>
    </div>

    <div class="version-selector">
        <h3>Select Reading Version</h3>
        <div class="version-links">
            <a href="{book_name.lower()}_{chapter_num}_hebrew.xhtml">Hebrew Only</a>
            <a href="{book_name.lower()}_{chapter_num}_english.xhtml">English Only</a>
            <a href="{book_name.lower()}_{chapter_num}_bilingual.xhtml">Bilingual (Side-by-Side)</a>
        </div>
    </div>

    <div style="text-align: center; margin-top: 2em;">
        <a href="toc.xhtml" style="color: #666;">← Back to Table of Contents</a>
    </div>
</body>
</html>"""
        return html

    def generate_epub(self, output_filename: str = "torah_hierarchical.epub"):
        """Generate the hierarchical EPUB"""
        print("=" * 60)
        print("Torah Hierarchical TOC Edition Generator")
        print("With clean text and version continuity")
        print("=" * 60)

        # Add CSS
        css = epub.EpubItem(
            uid="style",
            file_name="styles.css",
            media_type="text/css",
            content=self.create_hierarchical_css(),
        )
        self.book.add_item(css)

        # Create main TOC page
        toc_html = self.create_toc_page()
        toc_page = epub.EpubHtml(
            title="Table of Contents", file_name="toc.xhtml", content=toc_html, lang="he"
        )
        toc_page.add_item(css)
        self.book.add_item(toc_page)
        self.chapters.append(toc_page)

        # Build hierarchical TOC structure
        epub_toc = []

        for book_data in self.torah_books:
            english_name, hebrew_name, transliteration, total_chapters = book_data
            print(f"\n📖 Processing {english_name}...")

            # Book entry in TOC
            book_chapters = []

            # Generate only first 5 chapters for testing
            chapters_to_generate = min(5, total_chapters)

            for chapter_num in range(1, chapters_to_generate + 1):
                print(f"  Chapter {chapter_num}/{total_chapters}")

                # Fetch text once for all versions
                text_data = self.fetch_text(english_name, chapter_num)

                if not text_data["hebrew"] and not text_data["english"]:
                    continue

                # Create chapter selector page
                selector_html = self.create_chapter_selector(english_name, hebrew_name, chapter_num)
                selector_page = epub.EpubHtml(
                    title=f"{english_name} {chapter_num}",
                    file_name=f"{english_name.lower()}_{chapter_num}_selector.xhtml",
                    content=selector_html,
                    lang="he",
                )
                selector_page.add_item(css)
                self.book.add_item(selector_page)
                self.chapters.append(selector_page)

                # Create version pages
                version_pages = []
                for version in ["hebrew", "english", "bilingual"]:
                    version_html = self.create_chapter_version(
                        english_name, hebrew_name, chapter_num, text_data, version
                    )

                    version_page = epub.EpubHtml(
                        title=f"{english_name} {chapter_num} - {version.title()}",
                        file_name=f"{english_name.lower()}_{chapter_num}_{version}.xhtml",
                        content=version_html,
                        lang="he",
                    )
                    version_page.add_item(css)
                    self.book.add_item(version_page)
                    self.chapters.append(version_page)
                    version_pages.append(version_page)

                # Add to hierarchical TOC
                chapter_toc = (selector_page, tuple(version_pages))
                book_chapters.append(chapter_toc)

                time.sleep(0.1)  # API courtesy

            # Add book to main TOC
            if book_chapters:
                epub_toc.append((epub.Section(f"{english_name} - {hebrew_name}"), book_chapters))

        # Set TOC
        self.book.toc = epub_toc

        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Define spine
        self.book.spine = ["nav"] + self.chapters

        # Write EPUB
        print(f"\n📝 Writing to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})
        print(f"✅ Generated: {output_filename}")

        print("\n📱 Navigation Instructions:")
        print("  1. Open Table of Contents")
        print("  2. Select a Book (e.g., Genesis)")
        print("  3. Select a Chapter (e.g., Chapter 1)")
        print("  4. Choose your version (Hebrew, English, or Bilingual)")
        print("  5. Use navigation links to continue in the same version")
        print("\n✨ Text has been cleaned of HTML artifacts")

        return output_filename


if __name__ == "__main__":
    generator = TorahHierarchicalTOC()
    generator.generate_epub()
