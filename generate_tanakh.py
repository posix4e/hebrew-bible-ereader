#!/usr/bin/env python3
"""
Tanakh EPUB Generator for Kobo Libra Colour
Generates a responsive Hebrew/English Bible with custom artwork
"""

import time
import argparse
from pathlib import Path
from typing import Dict, Optional

import requests
from ebooklib import epub
from PIL import Image
import io


class TanakhGenerator:
    def __init__(self):
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

    def get_css(self) -> str:
        """Get responsive CSS for Kobo Libra Colour"""
        return """
        @font-face {
            font-family: 'NotoSerifHebrew';
            src: url('fonts/NotoSerifHebrew-Regular.ttf');
            font-weight: normal;
            font-style: normal;
        }

        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 1em;
            background: linear-gradient(to bottom, #faf9f5 0%, #f5f3eb 100%);
        }

        .chapter-container {
            margin: 0 auto;
            padding: 1em;
        }

        .header-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5em;
            border-radius: 12px;
            margin-bottom: 1.5em;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        h1, h2 {
            margin: 0;
        }

        h1 {
            font-size: 1.8em;
            margin-bottom: 0.2em;
        }

        h2 {
            font-size: 1.3em;
            opacity: 0.95;
        }

        .content-layout {
            display: block;
        }

        .text-section {
            background: white;
            border-radius: 8px;
            padding: 1.5em;
            margin-bottom: 1.5em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .hebrew-section {
            direction: rtl;
            text-align: right;
            background: linear-gradient(to right, #f0f4ff, #ffffff);
        }

        .english-section {
            direction: ltr;
            text-align: left;
            background: linear-gradient(to left, #fff9f0, #ffffff);
        }

        .hebrew-text {
            font-family: 'NotoSerifHebrew', serif;
            font-size: 1.3em;
            line-height: 1.8;
            color: #1a202c;
        }

        .english-text {
            font-size: 1.1em;
            line-height: 1.7;
            color: #2d3748;
        }

        .verse-number {
            font-weight: bold;
            color: #667eea;
            font-size: 0.9em;
            margin: 0 0.3em;
        }


        .image-container {
            text-align: center;
            margin: 2em auto;
            padding: 1em;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .image-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }

        .image-caption {
            margin-top: 0.8em;
            font-style: italic;
            color: #718096;
            font-size: 0.9em;
        }

        /* Landscape mode - side by side */
        @media (min-width: 1000px) {
            .content-layout {
                display: flex;
                gap: 2em;
            }

            .text-section {
                flex: 1;
            }

            .hebrew-section {
                margin-right: 0;
            }
        }

        /* Kobo-specific optimizations */
        @media screen and (color: 8) {
            body {
                background: #faf9f5;
            }

            .header-section {
                background: #667eea;
            }

            .hebrew-section, .english-section {
                background: white;
            }
        }
        """

    def fetch_text(self, book: str, chapter: int) -> Dict:
        """Fetch Hebrew and English text from Sefaria API"""
        url = f"https://www.sefaria.org/api/texts/{book}.{chapter}"
        params = {
            "commentary": 0,
            "context": 1,
            "pad": 0,
            "wrapLinks": 0,
            "wrapNamedEntities": 0,
            "multiple": 0,
            "stripmarkers": 0,
            "useTextFamily": "Koren Jerusalem Bible",
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

        # Create chapter content
        chapter = epub.EpubHtml(
            title=f"{book_name} {chapter_num}",
            file_name=f"{book_name}_{chapter_num}.xhtml",
            lang="he",
        )

        html_content = f"""
        <div class="chapter-container">
            <div class="header-section">
                <h1>{book_name} {chapter_num}</h1>
                <h2>{hebrew_name} פרק {self.to_hebrew_numeral(chapter_num)}</h2>
            </div>
        """

        # Add image if mapped for this chapter
        if (book_name, chapter_num) in self.image_map:
            image_file = self.image_map[(book_name, chapter_num)]
            html_content += f"""
            <div class="image-container">
                <img src="images/{image_file}" alt="{book_name} Chapter {chapter_num}"/>
                <div class="image-caption">{book_name} Chapter {chapter_num}</div>
            </div>
            """

        # Add text content
        html_content += '<div class="content-layout">'

        # Hebrew section
        html_content += '<div class="text-section hebrew-section"><div class="hebrew-text">'
        for i, verse in enumerate(hebrew_text, 1):
            if verse:
                html_content += f'<span class="verse-number">{i}</span>{verse} '
        html_content += "</div></div>"

        # English section
        html_content += '<div class="text-section english-section"><div class="english-text">'
        for i, verse in enumerate(english_text, 1):
            if verse:
                html_content += f'<span class="verse-number">{i}</span>{verse} '
        html_content += "</div></div>"

        html_content += "</div>"

        html_content += "</div>"
        chapter.content = html_content

        return chapter

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

    def generate(self, output_file: str = "tanakh.epub", test_mode: bool = False):
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

        # Process books
        spine = ["nav"]
        toc = []

        for book_info in self.books:
            english_name, hebrew_name, transliteration, chapter_count = book_info

            # Test mode - only first 3 chapters
            if test_mode:
                chapter_count = min(3, chapter_count)

            print(f"📖 Processing {english_name}...")

            book_chapters = []
            for chapter_num in range(1, chapter_count + 1):
                chapter = self.create_chapter(english_name, hebrew_name, chapter_num, chapter_count)
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

    args = parser.parse_args()

    generator = TanakhGenerator()
    generator.generate(args.output, args.test)


if __name__ == "__main__":
    main()
