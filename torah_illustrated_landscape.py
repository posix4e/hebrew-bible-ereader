#!/usr/bin/env python3
"""
Torah Illustrated Landscape Edition with Artistic Elements
Beautiful side-by-side bilingual text with thematic artwork
"""

import time
import requests
import re
from typing import Dict
from ebooklib import epub


class TorahIllustratedLandscape:
    def __init__(self):
        self.book = epub.EpubBook()
        self.book.set_identifier("torah-illustrated-landscape")
        self.book.set_title("Torah - Illustrated Landscape Edition")
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

        # Thematic artwork for each book
        self.book_themes = {
            "Genesis": {
                "symbol": "🌍",
                "colors": ["#87CEEB", "#228B22", "#8B4513"],  # Sky, earth, soil
                "art": "creation",
                "motifs": ["stars", "rainbow", "tree"],
            },
            "Exodus": {
                "symbol": "🔥",
                "colors": ["#DC143C", "#FFD700", "#4169E1"],  # Red sea, gold, blue
                "art": "liberation",
                "motifs": ["waves", "tablets", "pillar"],
            },
            "Leviticus": {
                "symbol": "🕊️",
                "colors": ["#FFFFFF", "#FFD700", "#8B008B"],  # White, gold, purple
                "art": "holiness",
                "motifs": ["altar", "incense", "crown"],
            },
            "Numbers": {
                "symbol": "⭐",
                "colors": ["#DAA520", "#4682B4", "#8B4513"],  # Gold, steel blue, brown
                "art": "journey",
                "motifs": ["tent", "staff", "cloud"],
            },
            "Deuteronomy": {
                "symbol": "📜",
                "colors": ["#8B4513", "#DAA520", "#2F4F4F"],  # Brown, gold, slate
                "art": "covenant",
                "motifs": ["scroll", "mountain", "blessing"],
            },
        }

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
        """Create CSS with artistic elements for landscape display"""
        return """
        @charset "UTF-8";

        /* Base styles */
        html, body {
            margin: 0;
            padding: 0;
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.7;
            height: 100%;
            background: linear-gradient(to bottom, #faf8f3 0%, #f5f1e8 100%);
        }

        /* Book divider with art */
        .book-divider {
            page-break-before: always;
            text-align: center;
            padding: 20% 0;
            position: relative;
            overflow: hidden;
            background: linear-gradient(
                135deg,
                var(--color1) 0%,
                var(--color2) 50%,
                var(--color3) 100%
            );
        }

        .book-art {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            opacity: 0.1;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 20em;
        }

        .book-divider h1 {
            font-size: 3em;
            margin: 0.5em 0;
            color: white;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
            position: relative;
            z-index: 2;
        }

        .hebrew-book-title {
            font-size: 3.5em;
            direction: rtl;
            font-family: 'David Libre', 'Times New Roman', serif;
        }

        .book-symbol {
            font-size: 4em;
            margin: 0.5em 0;
            animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        /* Chapter decorations */
        .chapter-header {
            text-align: center;
            margin-bottom: 2em;
            padding: 1.5em 0;
            position: relative;
            background: linear-gradient(to right, transparent, rgba(218,165,32,0.1), transparent);
        }

        .chapter-decoration {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            font-size: 3em;
            opacity: 0.2;
            color: var(--accent-color);
        }

        .chapter-title {
            font-size: 1.6em;
            font-weight: bold;
            margin: 0.3em 0;
            color: #2d5016;
        }

        /* Parsha markers with decorative border */
        .parsha-marker {
            background: linear-gradient(to right, #fffacd, #fff5e6, #fffacd);
            padding: 1em;
            margin: 2em 0;
            text-align: center;
            font-weight: bold;
            border: 2px solid #daa520;
            border-radius: 8px;
            position: relative;
            box-shadow: 0 4px 6px rgba(218,165,32,0.2);
        }

        .parsha-marker::before,
        .parsha-marker::after {
            content: "✦";
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            color: #daa520;
            font-size: 1.5em;
        }

        .parsha-marker::before {
            left: 1em;
        }

        .parsha-marker::after {
            right: 1em;
        }

        /* Main container for side-by-side layout */
        .content-container {
            width: 100%;
            display: table;
            table-layout: fixed;
            margin: 0 auto;
            max-width: 1400px;
        }

        /* Side-by-side columns with decorative separator */
        .hebrew-column, .english-column {
            display: table-cell;
            width: 47%;
            padding: 1.5%;
            vertical-align: top;
            position: relative;
        }

        .hebrew-column {
            direction: rtl;
            text-align: right;
            background: linear-gradient(to left, transparent 0%, rgba(139,69,19,0.02) 100%);
        }

        .english-column {
            direction: ltr;
            text-align: left;
            background: linear-gradient(to right, transparent 0%, rgba(70,130,180,0.02) 100%);
        }

        /* Decorative column separator */
        .column-separator {
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom,
                transparent 0%,
                #daa520 10%,
                #daa520 90%,
                transparent 100%);
            transform: translateX(-50%);
        }

        /* Column headers with decoration */
        .column-header {
            font-weight: bold;
            text-align: center;
            padding: 0.8em 0;
            margin-bottom: 1.5em;
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(255,250,205,0.5));
            border-radius: 8px;
            border: 1px solid rgba(218,165,32,0.3);
            position: relative;
        }

        /* Verse styling with alternating backgrounds */
        .verse {
            margin: 1em 0;
            padding: 0.5em;
            border-radius: 4px;
            transition: background-color 0.3s;
        }

        .verse:nth-child(even) {
            background: rgba(255,255,255,0.3);
        }

        .verse:hover {
            background: rgba(255,250,205,0.3);
        }

        .verse-number {
            font-weight: bold;
            color: #0066cc;
            display: inline-block;
            min-width: 2.5em;
            margin-right: 0.5em;
            padding: 0.2em 0.4em;
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(240,248,255,0.5));
            border-radius: 4px;
            text-align: center;
        }

        .hebrew-column .verse-number {
            margin-right: 0;
            margin-left: 0.5em;
        }

        .verse-text {
            display: inline;
            font-size: 1.1em;
            line-height: 1.8;
        }

        /* Special verse decorations */
        .verse-1 {
            position: relative;
            padding-top: 2em !important;
        }

        .verse-1::before {
            content: "❋";
            position: absolute;
            top: 0.5em;
            left: 50%;
            transform: translateX(-50%);
            color: #daa520;
            font-size: 1.2em;
        }

        /* Landscape optimization with artistic touch */
        @media (orientation: landscape) and (min-width: 1000px) {
            body {
                font-size: 16px;
            }

            .content-container {
                padding: 0 2em;
            }

            .verse-text {
                font-size: 1.15em;
            }
        }

        /* Portrait fallback */
        @media (orientation: portrait) {
            .content-container {
                display: block;
            }

            .hebrew-column, .english-column {
                display: block;
                width: 100%;
                border: none;
                margin-bottom: 1em;
            }

            .column-separator {
                display: none;
            }

            .hebrew-column {
                border-bottom: 2px solid #daa520;
                padding-bottom: 1em;
            }
        }

        /* Kobo Color specific optimizations */
        @media (device-width: 1264px) and (device-height: 1680px) {
            body {
                font-size: 15px;
            }

            .verse-text {
                font-size: 1.2em;
                letter-spacing: 0.02em;
            }

            .content-container {
                padding: 0 1.5em;
            }
        }

        /* Genesis theme */
        .genesis-theme {
            --color1: #87CEEB;
            --color2: #228B22;
            --color3: #8B4513;
            --accent-color: #228B22;
        }

        /* Exodus theme */
        .exodus-theme {
            --color1: #DC143C;
            --color2: #FFD700;
            --color3: #4169E1;
            --accent-color: #DC143C;
        }

        /* Leviticus theme */
        .leviticus-theme {
            --color1: #FFFFFF;
            --color2: #FFD700;
            --color3: #8B008B;
            --accent-color: #8B008B;
        }

        /* Numbers theme */
        .numbers-theme {
            --color1: #DAA520;
            --color2: #4682B4;
            --color3: #8B4513;
            --accent-color: #4682B4;
        }

        /* Deuteronomy theme */
        .deuteronomy-theme {
            --color1: #8B4513;
            --color2: #DAA520;
            --color3: #2F4F4F;
            --accent-color: #2F4F4F;
        }
        """

    def create_illustrated_chapter_html(
        self,
        book_name: str,
        hebrew_name: str,
        chapter_num: int,
        text_data: Dict,
        parsha_name: str = None,
    ) -> str:
        """Create illustrated HTML for landscape side-by-side display"""
        hebrew_verses = text_data["hebrew"]
        english_verses = text_data["english"]

        # Get theme for this book
        theme = self.book_themes.get(book_name, self.book_themes["Genesis"])
        theme_class = f"{book_name.lower()}-theme"

        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" class="{theme_class}">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} {chapter_num}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="chapter-header">
        <div class="chapter-decoration">{theme['symbol']}</div>
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
        <div class="column-separator"></div>
        <div class="hebrew-column">
            <div class="column-header">עברית</div>
"""

        # Add Hebrew verses with special styling for first verse
        for i, verse in enumerate(hebrew_verses):
            verse_class = "verse verse-1" if i == 0 else "verse"
            html += f"""
            <div class="{verse_class}">
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
            verse_class = "verse verse-1" if i == 0 else "verse"
            html += f"""
            <div class="{verse_class}">
                <span class="verse-number">{i + 1}</span>
                <span class="verse-text">{verse}</span>
            </div>
"""

        html += """
        </div>
    </div>
</body>
</html>"""
        return html

    def create_book_divider_html(
        self, english_name: str, hebrew_name: str, transliteration: str
    ) -> str:
        """Create artistic book divider page"""
        theme = self.book_themes.get(english_name, self.book_themes["Genesis"])
        theme_class = f"{english_name.lower()}-theme"

        return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" class="{theme_class}">
<head>
    <meta charset="UTF-8"/>
    <title>{english_name}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="book-divider">
        <div class="book-art">{theme['symbol']}</div>
        <div class="book-symbol">{theme['symbol']}</div>
        <h1>{english_name}</h1>
        <h1 class="hebrew-book-title">{hebrew_name}</h1>
        <p style="font-size: 1.5em; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            {transliteration}
        </p>
    </div>
</body>
</html>"""

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
            "Leviticus": {
                1: "ויקרא",
                6: "צו",
                8: "שמיני",
                12: "תזריע",
                14: "מצורע",
                16: "אחרי מות",
                19: "קדושים",
                21: "אמור",
                25: "בהר",
                26: "בחקתי",
            },
            "Numbers": {
                1: "במדבר",
                4: "נשא",
                8: "בהעלתך",
                13: "שלח",
                16: "קרח",
                19: "חקת",
                22: "בלק",
                25: "פנחס",
                30: "מטות",
                33: "מסעי",
            },
            "Deuteronomy": {
                1: "דברים",
                3: "ואתחנן",
                7: "עקב",
                11: "ראה",
                16: "שופטים",
                21: "כי תצא",
                26: "כי תבוא",
                29: "נצבים",
                31: "וילך",
                32: "האזינו",
                33: "וזאת הברכה",
            },
        }

        book_parshiyot = parshiyot.get(book, {})
        return book_parshiyot.get(chapter, None)

    def generate_epub(
        self, output_filename: str = "torah_illustrated_landscape.epub", full_torah: bool = False
    ):
        """Generate the illustrated bilingual landscape EPUB"""
        print("=" * 60)
        print("Torah Illustrated Landscape Edition Generator")
        print("Beautiful side-by-side reading with artistic elements")
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

            theme_symbol = self.book_themes[english_name]["symbol"]
            print(f"\n🎨 Creating {english_name} with {theme_symbol} theme...")

            # Add artistic book divider page
            book_html = self.create_book_divider_html(english_name, hebrew_name, transliteration)

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
            chapters_to_generate = total_chapters if full_torah else min(5, total_chapters)

            for chapter_num in range(1, chapters_to_generate + 1):
                print(f"  Chapter {chapter_num}/{total_chapters}")

                # Check for parsha
                parsha = self.get_parsha_for_chapter(english_name, chapter_num)

                # Fetch text
                text_data = self.fetch_text(english_name, chapter_num)

                if text_data["hebrew"] or text_data["english"]:
                    html_content = self.create_illustrated_chapter_html(
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

        print("\n🎨 Features of this Illustrated Edition:")
        print("  • Beautiful color themes for each book")
        print("  • Decorative elements and symbols")
        print("  • Elegant parsha markers")
        print("  • Artistic book dividers")
        print("  • Optimized for landscape reading")
        print("\n📱 Best viewed in landscape orientation on Kobo Color")

        return output_filename


if __name__ == "__main__":
    import sys

    # Check if we want full Torah or just sample
    full = "--full" in sys.argv

    generator = TorahIllustratedLandscape()

    if full:
        print("Generating FULL Illustrated Torah (this will take several minutes)...")
        generator.generate_epub("torah_illustrated_landscape_full.epub", full_torah=True)
    else:
        print("Generating illustrated sample (5 chapters per book)...")
        generator.generate_epub("torah_illustrated_landscape_sample.epub", full_torah=False)
