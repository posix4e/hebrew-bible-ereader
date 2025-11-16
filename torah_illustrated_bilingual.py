#!/usr/bin/env python3
"""
Torah Illustrated Bilingual Edition
Hebrew and English with story-relevant artwork using Unicode art and CSS
"""

import os
import time
import requests
import re
from typing import List, Dict, Tuple, Optional
from ebooklib import epub


class TorahIllustratedBilingual:
    def __init__(self):
        self.book = epub.EpubBook()
        self.book.set_identifier("torah-illustrated-bilingual")
        self.book.set_title("Torah - Illustrated Bilingual Edition")
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

        # Story-specific illustrations for key chapters
        self.chapter_illustrations = {
            "Genesis": {
                1: {"symbol": "🌌", "title": "Creation", "art": "stars_and_light"},
                2: {"symbol": "🌳", "title": "Garden of Eden", "art": "garden"},
                3: {"symbol": "🍎", "title": "The Fall", "art": "tree_of_knowledge"},
                6: {"symbol": "🚢", "title": "Noah's Ark", "art": "ark"},
                7: {"symbol": "🌈", "title": "The Flood", "art": "rainbow"},
                11: {"symbol": "🏗️", "title": "Tower of Babel", "art": "tower"},
                12: {"symbol": "⭐", "title": "Abraham's Journey", "art": "stars"},
                18: {"symbol": "👥", "title": "Three Visitors", "art": "tent"},
                22: {"symbol": "🐏", "title": "The Binding of Isaac", "art": "altar"},
                28: {"symbol": "🪜", "title": "Jacob's Ladder", "art": "ladder"},
                37: {"symbol": "🧥", "title": "Joseph's Coat", "art": "colored_coat"},
                41: {"symbol": "🌾", "title": "Pharaoh's Dreams", "art": "wheat"},
            },
            "Exodus": {
                1: {"symbol": "👶", "title": "Moses in the Basket", "art": "river"},
                3: {"symbol": "🔥", "title": "Burning Bush", "art": "fire"},
                7: {"symbol": "🐸", "title": "The Plagues Begin", "art": "plagues"},
                12: {"symbol": "🚪", "title": "Passover", "art": "doorpost"},
                14: {"symbol": "🌊", "title": "Splitting of the Sea", "art": "waves"},
                16: {"symbol": "🍞", "title": "Manna from Heaven", "art": "bread"},
                19: {"symbol": "⛰️", "title": "Mount Sinai", "art": "mountain"},
                20: {"symbol": "📜", "title": "Ten Commandments", "art": "tablets"},
                25: {"symbol": "🕍", "title": "The Tabernacle", "art": "sanctuary"},
                32: {"symbol": "🐄", "title": "Golden Calf", "art": "calf"},
            },
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

    def create_illustrated_css(self) -> str:
        """Create CSS with beautiful illustrations and colors"""
        return """
        @charset "UTF-8";

        /* Base styles */
        html, body {
            margin: 0;
            padding: 0;
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.8;
            background: linear-gradient(to bottom, #fdf6e3 0%, #f7f0dd 100%);
            color: #2c3e50;
        }

        /* Chapter illustrations */
        .chapter-illustration {
            text-align: center;
            padding: 3em 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            position: relative;
            overflow: hidden;
            min-height: 300px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }

        .illustration-symbol {
            font-size: 8em;
            margin-bottom: 0.3em;
            animation: float 6s ease-in-out infinite;
            filter: drop-shadow(0 10px 20px rgba(0,0,0,0.3));
        }

        .illustration-title {
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 0.5em;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            25% { transform: translateY(-10px) rotate(-2deg); }
            75% { transform: translateY(10px) rotate(2deg); }
        }

        /* Art backgrounds */
        .art-stars_and_light {
            background: radial-gradient(ellipse at top, #0f2027, #203a43, #2c5364);
        }

        .art-garden {
            background: linear-gradient(to bottom, #56ab2f, #a8e063);
        }

        .art-ark {
            background: linear-gradient(to bottom, #373b44, #4286f4);
        }

        .art-rainbow {
            background: linear-gradient(to right, #f093fb, #f5576c, #ffd700, #4facfe, #43e97b);
        }

        .art-tower {
            background: linear-gradient(to top, #8e44ad, #3498db);
        }

        .art-fire {
            background: linear-gradient(to top, #ff4b1f, #ff9068);
        }

        .art-waves {
            background: linear-gradient(120deg, #89f7fe 0%, #66a6ff 100%);
        }

        .art-mountain {
            background: linear-gradient(to bottom, #e6dada, #274046);
        }

        .art-tablets {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        /* Chapter header */
        .chapter-header {
            text-align: center;
            padding: 2em;
            background: white;
            margin-bottom: 2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .chapter-title {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin: 0.3em 0;
        }

        .hebrew-title {
            font-family: 'David Libre', serif;
            direction: rtl;
        }

        /* Content container */
        .content-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2em;
        }

        /* Verse container with beautiful styling */
        .verse-container {
            background: white;
            border-radius: 12px;
            margin: 2em 0;
            padding: 2em;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }

        .verse-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(to right, #667eea, #764ba2, #f093fb);
        }

        /* Key verse highlighting */
        .key-verse {
            background: linear-gradient(to right, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-left: 4px solid #667eea;
            padding-left: 1em;
        }

        /* Hebrew and English sections */
        .hebrew-section, .english-section {
            padding: 1em;
            margin: 0.5em 0;
        }

        .hebrew-section {
            direction: rtl;
            text-align: right;
            font-size: 1.15em;
            background: rgba(139, 69, 19, 0.03);
            border-radius: 8px;
        }

        .english-section {
            background: rgba(70, 130, 180, 0.03);
            border-radius: 8px;
        }

        /* Verse numbers with decoration */
        .verse-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.5em;
            height: 2.5em;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 50%;
            font-weight: bold;
            margin-right: 1em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .hebrew-section .verse-number {
            margin-right: 0;
            margin-left: 1em;
        }

        /* Special decorations for specific verses */
        .verse-1 .verse-number {
            width: 3em;
            height: 3em;
            font-size: 1.2em;
            background: linear-gradient(135deg, #f093fb, #f5576c);
        }

        /* Landscape optimization */
        @media (orientation: landscape) and (min-width: 1000px) {
            .verse-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2em;
            }

            .hebrew-section {
                border-right: 2px solid #e0e0e0;
                padding-right: 2em;
            }

            .english-section {
                padding-left: 2em;
            }

            .chapter-illustration {
                min-height: 400px;
            }

            .illustration-symbol {
                font-size: 10em;
            }
        }

        /* Portrait optimization */
        @media (orientation: portrait) {
            .verse-container {
                display: block;
            }

            .hebrew-section {
                margin-bottom: 1em;
            }

            .chapter-illustration {
                min-height: 250px;
            }

            .illustration-symbol {
                font-size: 6em;
            }
        }

        /* Kobo Color optimizations */
        @media (device-width: 1264px) and (device-height: 1680px) {
            body {
                font-size: 16px;
            }

            .verse-container {
                padding: 1.5em;
            }
        }

        @media (device-width: 1680px) and (device-height: 1264px) {
            body {
                font-size: 15px;
            }

            .verse-container {
                display: grid !important;
            }
        }
        """

    def create_illustrated_chapter_html(
        self, book_name: str, hebrew_name: str, chapter_num: int, text_data: Dict
    ) -> str:
        """Create HTML with illustrations for key chapters"""
        hebrew_verses = text_data["hebrew"]
        english_verses = text_data["english"]

        # Check if this chapter has special illustration
        illustration = None
        if book_name in self.chapter_illustrations:
            illustration = self.chapter_illustrations[book_name].get(chapter_num)

        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} {chapter_num}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>"""

        # Add illustration if this is a key chapter
        if illustration:
            html += f"""
    <div class="chapter-illustration art-{illustration['art']}">
        <div class="illustration-symbol">{illustration['symbol']}</div>
        <div class="illustration-title">{illustration['title']}</div>
    </div>"""

        html += f"""
    <div class="chapter-header">
        <div class="chapter-title">{book_name} Chapter {chapter_num}</div>
        <div class="chapter-title hebrew-title">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</div>
    </div>

    <div class="content-container">"""

        # Add verses with special styling for key verses
        for i in range(max(len(hebrew_verses), len(english_verses))):
            hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
            english = english_verses[i] if i < len(english_verses) else ""
            verse_num = i + 1

            # Mark key verses (verse 1, and specific important verses)
            verse_class = "verse-container"
            if verse_num == 1:
                verse_class += " verse-1 key-verse"

            html += f"""
        <div class="{verse_class}">
            <div class="hebrew-section">
                <span class="verse-number">{self.hebrew_number(verse_num)}</span>
                <span class="verse-text">{hebrew}</span>
            </div>
            <div class="english-section">
                <span class="verse-number">{verse_num}</span>
                <span class="verse-text">{english}</span>
            </div>
        </div>"""

        html += """
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

    def generate_epub(
        self, output_filename: str = "torah_illustrated_bilingual.epub", test_mode: bool = True
    ):
        """Generate the illustrated bilingual EPUB"""
        print("=" * 60)
        print("Torah Illustrated Bilingual Edition Generator")
        print("Beautiful Hebrew-English text with story illustrations")
        print("=" * 60)

        # Add CSS
        css = epub.EpubItem(
            uid="style",
            file_name="styles.css",
            media_type="text/css",
            content=self.create_illustrated_css(),
        )
        self.book.add_item(css)

        # Flat TOC for Kobo compatibility
        flat_toc = []

        for book_data in self.torah_books:
            english_name, hebrew_name, transliteration, total_chapters = book_data

            print(f"\n🎨 Processing {english_name}...")

            # Generate only key illustrated chapters for testing
            if test_mode and english_name in self.chapter_illustrations:
                chapters_to_generate = list(self.chapter_illustrations[english_name].keys())[:3]
            else:
                chapters_to_generate = range(1, min(3, total_chapters) + 1)

            for chapter_num in chapters_to_generate:
                if isinstance(chapter_num, range):
                    chapter_num = list(chapter_num)[0]

                print(f"  Chapter {chapter_num}")

                # Fetch text
                text_data = self.fetch_text(english_name, chapter_num)

                if text_data["hebrew"] or text_data["english"]:
                    html_content = self.create_illustrated_chapter_html(
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

        # Add dedication page at the end
        dedication_html = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>Dedication</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div style="min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 2em; text-align: center;">
        <div style="max-width: 600px;">
            <div style="font-size: 3em; margin-bottom: 0.5em;">🎨</div>
            <h1 style="font-size: 2em; margin-bottom: 1em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">Dedication</h1>
            <p style="font-size: 1.3em; line-height: 1.8; font-style: italic; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
                This illustrated edition is lovingly dedicated to<br/>
                <strong style="font-size: 1.2em;">Bruno "DaVenzia" Naphtali</strong><br/>
                whose artistic spirit and creative vision<br/>
                continue to inspire beauty in all forms.
            </p>
            <div style="margin-top: 2em; font-size: 1.1em; opacity: 0.9;">
                May these illustrated words of Torah<br/>
                bring light and color to all who read them.
            </div>
        </div>
    </div>
</body>
</html>"""

        dedication_page = epub.EpubHtml(
            title="Dedication", file_name="dedication.xhtml", content=dedication_html, lang="en"
        )
        dedication_page.add_item(css)
        self.book.add_item(dedication_page)
        self.chapters.append(dedication_page)
        flat_toc.append(dedication_page)

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

        print("\n🎨 Features:")
        print("  • Story-relevant illustrations for key chapters")
        print("  • Beautiful gradient backgrounds")
        print("  • Color-coded Hebrew and English sections")
        print("  • Special highlighting for important verses")
        print("  • Optimized for both portrait and landscape")

        return output_filename


if __name__ == "__main__":
    import sys

    # Check if we want full Torah or just test
    test = "--test" in sys.argv or not "--full" in sys.argv

    generator = TorahIllustratedBilingual()
    generator.generate_epub(test_mode=test)
