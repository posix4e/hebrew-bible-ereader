#!/usr/bin/env python3
"""
Torah Commentary Generator - Creates all EPUB variations
Each commentary as a separate EPUB with portrait/landscape versions
"""

import os
import time
import requests
import re
from typing import List, Dict, Tuple, Optional
from ebooklib import epub
import argparse


class TorahCommentaryGenerator:
    def __init__(self, commentary_name: str = None, orientation: str = "portrait"):
        self.commentary_name = commentary_name
        self.orientation = orientation

        self.book = epub.EpubBook()

        # Set identifier based on commentary and orientation
        identifier = f'torah-{commentary_name or "base"}-{orientation}'
        self.book.set_identifier(identifier)

        # Set title with commentary name
        if commentary_name:
            title = f"Torah with {commentary_name.title()} - {orientation.title()} Edition"
        else:
            title = f"Torah - {orientation.title()} Edition"
        self.book.set_title(title)

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

        # Available commentaries with their API names and display colors
        self.available_commentaries = {
            "rashi": {"api": "Rashi on Genesis", "color": "#8B4513", "hebrew": "רש״י"},
            "ibn_ezra": {"api": "Ibn Ezra on Genesis", "color": "#4169E1", "hebrew": "אבן עזרא"},
            "ramban": {"api": "Ramban on Genesis", "color": "#2F4F4F", "hebrew": "רמב״ן"},
            "sforno": {"api": "Sforno on Genesis", "color": "#8B008B", "hebrew": "ספורנו"},
            "or_hachaim": {
                "api": "Or HaChaim on Genesis",
                "color": "#DAA520",
                "hebrew": "אור החיים",
            },
            "kli_yakar": {"api": "Kli Yakar on Genesis", "color": "#DC143C", "hebrew": "כלי יקר"},
            "malbim": {"api": "Malbim on Genesis", "color": "#228B22", "hebrew": "מלבי״ם"},
            "targum_onkelos": {
                "api": "Targum Onkelos on Genesis",
                "color": "#4682B4",
                "hebrew": "תרגום אונקלוס",
            },
            "targum_jonathan": {
                "api": "Targum Jonathan on Genesis",
                "color": "#5F9EA0",
                "hebrew": "תרגום יונתן",
            },
            "chizkuni": {"api": "Chizkuni, Genesis", "color": "#CD853F", "hebrew": "חזקוני"},
        }

        self.chapters = []

    def clean_text(self, text: str) -> str:
        """Clean HTML and artifacts from text"""
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("&nbsp;", " ")
        text = text.replace("nbsp&", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&apos;", "'")
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
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

    def fetch_commentary(self, book_name: str, chapter: int, verse: int) -> str:
        """Fetch specific commentary for a verse"""
        if not self.commentary_name or self.commentary_name not in self.available_commentaries:
            return ""

        try:
            commentary_info = self.available_commentaries[self.commentary_name]
            api_name = commentary_info["api"].replace("Genesis", book_name)

            url = f"https://www.sefaria.org/api/texts/{api_name}.{chapter}.{verse}"
            response = requests.get(url, params={"context": 0})

            if response.status_code == 200:
                data = response.json()
                text = data.get("he", "") or data.get("text", "")

                if isinstance(text, list):
                    text = " ".join(text)

                return self.clean_text(text) if text else ""

        except Exception as e:
            print(f"Error fetching commentary for {book_name} {chapter}:{verse}: {e}")

        return ""

    def create_css(self) -> str:
        """Create CSS optimized for portrait or landscape with commentary sections"""

        commentary_color = "#8B4513"  # Default brown
        if self.commentary_name and self.commentary_name in self.available_commentaries:
            commentary_color = self.available_commentaries[self.commentary_name]["color"]

        base_css = f"""
        @charset "UTF-8";

        /* Base styles */
        html, body {{
            margin: 0;
            padding: 1em;
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.7;
            background: #faf8f3;
        }}

        /* Chapter header */
        .chapter-header {{
            text-align: center;
            margin-bottom: 2em;
            padding: 1.5em;
            background: linear-gradient(135deg, #1a472a, #2d5016);
            color: white;
            border-radius: 8px;
        }}

        .chapter-title {{
            font-size: 1.8em;
            font-weight: bold;
            margin: 0.3em 0;
        }}

        /* Hebrew text */
        .hebrew {{
            direction: rtl;
            text-align: right;
            font-size: 1.15em;
        }}

        /* Verse container */
        .verse-container {{
            margin: 2em 0;
            background: white;
            border-radius: 8px;
            padding: 1.5em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        /* Verse number */
        .verse-number {{
            font-weight: bold;
            color: #0066cc;
            display: inline-block;
            min-width: 2.5em;
            margin-right: 0.5em;
            padding: 0.3em;
            background: rgba(70,130,180,0.1);
            border-radius: 4px;
            text-align: center;
        }}

        .hebrew .verse-number {{
            margin-right: 0;
            margin-left: 0.5em;
        }}

        /* Commentary section */
        .commentary-section {{
            margin-top: 1.5em;
            padding: 1em;
            background: linear-gradient(135deg, rgba({int(commentary_color[1:3], 16)},{int(commentary_color[3:5], 16)},{int(commentary_color[5:7], 16)},0.05),
                                              rgba({int(commentary_color[1:3], 16)},{int(commentary_color[3:5], 16)},{int(commentary_color[5:7], 16)},0.1));
            border-left: 4px solid {commentary_color};
            border-radius: 4px;
        }}

        .commentary-header {{
            font-weight: bold;
            color: {commentary_color};
            margin-bottom: 0.5em;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .commentary-text {{
            font-size: 0.95em;
            line-height: 1.6;
            color: #444;
        }}

        /* Color-coded sections */
        .hebrew-section, .english-section {{
            padding: 0.8em;
            margin: 0.5em 0;
            border-radius: 4px;
        }}

        .hebrew-section {{
            background: rgba(139,69,19,0.03);
            border-left: 3px solid #8B4513;
        }}

        .english-section {{
            background: rgba(70,130,180,0.03);
            border-left: 3px solid #4682B4;
        }}
        """

        # Add orientation-specific styles
        if self.orientation == "landscape":
            orientation_css = """
        /* Landscape optimization */
        @media (orientation: landscape), (min-width: 1000px) {
            .verse-container {
                display: flex;
                gap: 2em;
            }

            .text-column {
                flex: 1;
            }

            .hebrew-column {
                border-right: 2px solid #e0e0e0;
                padding-right: 2em;
            }

            .english-column {
                padding-left: 2em;
            }

            .commentary-section {
                margin-top: 2em;
                grid-column: 1 / -1;
            }

            body {
                max-width: 1400px;
                margin: 0 auto;
                padding: 1em 2em;
            }
        }

        /* Kobo Color landscape */
        @media (device-width: 1680px) and (device-height: 1264px) {
            body {
                font-size: 15px;
            }

            .verse-container {
                display: flex !important;
            }
        }
        """
        else:  # portrait
            orientation_css = """
        /* Portrait optimization */
        .verse-container {
            display: block;
        }

        .hebrew-section {
            margin-bottom: 1em;
        }

        .english-section {
            margin-bottom: 1em;
        }

        /* Kobo Color portrait */
        @media (device-width: 1264px) and (device-height: 1680px) {
            body {
                font-size: 16px;
                padding: 0.8em;
            }

            .verse-container {
                padding: 1.2em;
            }
        }

        /* Small screens */
        @media (max-width: 600px) {
            .chapter-header {
                padding: 1em;
            }

            .chapter-title {
                font-size: 1.4em;
            }
        }
        """

        return base_css + orientation_css

    def create_chapter_html(
        self, book_name: str, hebrew_name: str, chapter_num: int, text_data: Dict
    ) -> str:
        """Create HTML with commentary as vertical sections"""
        hebrew_verses = text_data["hebrew"]
        english_verses = text_data["english"]

        commentary_display = ""
        if self.commentary_name and self.commentary_name in self.available_commentaries:
            commentary_info = self.available_commentaries[self.commentary_name]
            commentary_display = f" with {commentary_info['hebrew']}"

        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} {chapter_num}{commentary_display}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="chapter-header">
        <div class="chapter-title">{book_name} Chapter {chapter_num}</div>
        <div class="chapter-title hebrew">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</div>
        {"<div class='chapter-title'>" + commentary_display + "</div>" if commentary_display else ""}
    </div>
"""

        # Create verses with commentary
        for i in range(max(len(hebrew_verses), len(english_verses))):
            hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
            english = english_verses[i] if i < len(english_verses) else ""
            verse_num = i + 1

            html += f"""
    <div class="verse-container">"""

            if self.orientation == "landscape":
                # Side-by-side layout for landscape
                html += f"""
        <div class="text-column hebrew-column">
            <div class="hebrew-section hebrew">
                <span class="verse-number">{self.hebrew_number(verse_num)}</span>
                <span class="verse-text">{hebrew}</span>
            </div>
        </div>
        <div class="text-column english-column">
            <div class="english-section">
                <span class="verse-number">{verse_num}.</span>
                <span class="verse-text">{english}</span>
            </div>
        </div>"""
            else:
                # Stacked layout for portrait
                html += f"""
        <div class="hebrew-section hebrew">
            <span class="verse-number">{self.hebrew_number(verse_num)}</span>
            <span class="verse-text">{hebrew}</span>
        </div>
        <div class="english-section">
            <span class="verse-number">{verse_num}.</span>
            <span class="verse-text">{english}</span>
        </div>"""

            # Add commentary if available
            if self.commentary_name:
                commentary = self.fetch_commentary(book_name, chapter_num, verse_num)
                if commentary:
                    commentary_info = self.available_commentaries[self.commentary_name]
                    html += f"""
        <div class="commentary-section">
            <div class="commentary-header">{commentary_info['hebrew']} on verse {verse_num}</div>
            <div class="commentary-text hebrew">{commentary}</div>
        </div>"""

            html += """
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
            return ones[num]
        elif num < 100:
            return tens[num // 10] + ones[num % 10]
        else:
            return str(num)

    def generate_epub(self, output_filename: str = None, test_mode: bool = True):
        """Generate the EPUB with commentary"""

        if not output_filename:
            if self.commentary_name:
                output_filename = f"torah_{self.commentary_name}_{self.orientation}.epub"
            else:
                output_filename = f"torah_{self.orientation}.epub"

        print("=" * 60)
        print(f"Torah {self.commentary_name or 'Base'} Edition - {self.orientation.title()}")
        print("=" * 60)

        # Add CSS
        css = epub.EpubItem(
            uid="style", file_name="styles.css", media_type="text/css", content=self.create_css()
        )
        self.book.add_item(css)

        # Flat TOC for Kobo compatibility
        flat_toc = []

        for book_data in self.torah_books:
            english_name, hebrew_name, transliteration, total_chapters = book_data

            if self.commentary_name:
                commentary_info = self.available_commentaries[self.commentary_name]
                print(f"\n📖 Processing {english_name} with {commentary_info['hebrew']}...")
            else:
                print(f"\n📖 Processing {english_name}...")

            # Generate chapters (limited for testing)
            chapters_to_generate = min(3, total_chapters) if test_mode else total_chapters

            for chapter_num in range(1, chapters_to_generate + 1):
                print(f"  Chapter {chapter_num}/{total_chapters}")

                # Fetch text
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

        return output_filename


def generate_all_versions():
    """Generate all EPUB combinations"""

    commentaries = [
        None,  # Base version without commentary
        "rashi",
        "ibn_ezra",
        "ramban",
        "sforno",
        "or_hachaim",
        "kli_yakar",
        "malbim",
        "targum_onkelos",
        "targum_jonathan",
        "chizkuni",
    ]

    orientations = ["portrait", "landscape"]

    generated_files = []

    for commentary in commentaries:
        for orientation in orientations:
            print(f"\n{'='*60}")
            print(f"Generating: {commentary or 'Base'} - {orientation}")
            print("=" * 60)

            generator = TorahCommentaryGenerator(
                commentary_name=commentary, orientation=orientation
            )

            filename = generator.generate_epub(test_mode=True)
            generated_files.append(filename)

            time.sleep(0.5)  # Be nice to the API

    print("\n" + "=" * 60)
    print("✅ All versions generated successfully!")
    print("=" * 60)
    print("\nGenerated files:")
    for f in generated_files:
        print(f"  📚 {f}")

    return generated_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Torah EPUBs with commentaries")
    parser.add_argument(
        "--commentary",
        choices=[
            "rashi",
            "ibn_ezra",
            "ramban",
            "sforno",
            "or_hachaim",
            "kli_yakar",
            "malbim",
            "targum_onkelos",
            "targum_jonathan",
            "chizkuni",
        ],
        help="Commentary to include",
    )
    parser.add_argument(
        "--orientation",
        choices=["portrait", "landscape"],
        default="portrait",
        help="Orientation optimization",
    )
    parser.add_argument("--all", action="store_true", help="Generate all versions")
    parser.add_argument(
        "--full", action="store_true", help="Generate full Torah (not just test chapters)"
    )
    parser.add_argument("-o", "--output", help="Output filename")

    args = parser.parse_args()

    if args.all:
        generate_all_versions()
    else:
        generator = TorahCommentaryGenerator(
            commentary_name=args.commentary, orientation=args.orientation
        )
        generator.generate_epub(output_filename=args.output, test_mode=not args.full)
