#!/usr/bin/env python3
import os
import json
import requests
from typing import List, Dict, Tuple
from ebooklib import epub


class HebrewBibleEPUB:
    def __init__(self):
        self.book = epub.EpubBook()
        self.book.set_identifier('hebrew-bible-kobo')
        self.book.set_title('Hebrew Bible - Torah and Prophets')
        self.book.set_language('he')
        self.book.add_metadata('DC', 'language', 'en')

        self.torah_books = [
            ('Genesis', 'בראשית', 'Bereshit'),
            ('Exodus', 'שמות', 'Shemot'),
            ('Leviticus', 'ויקרא', 'Vayikra'),
            ('Numbers', 'במדבר', 'Bamidbar'),
            ('Deuteronomy', 'דברים', 'Devarim')
        ]

        self.prophet_books = [
            ('Joshua', 'יהושע', 'Yehoshua'),
            ('Judges', 'שופטים', 'Shoftim'),
            ('I Samuel', 'שמואל א', 'Shmuel I'),
            ('II Samuel', 'שמואל ב', 'Shmuel II'),
            ('I Kings', 'מלכים א', 'Melachim I'),
            ('II Kings', 'מלכים ב', 'Melachim II'),
            ('Isaiah', 'ישעיהו', 'Yeshayahu'),
            ('Jeremiah', 'ירמיהו', 'Yirmiyahu'),
            ('Ezekiel', 'יחזקאל', 'Yechezkel')
        ]

        self.chapters = []
        self.toc = []

    def fetch_text(self, book_name: str, chapter: int) -> Tuple[List[str], List[str]]:
        """Fetch Hebrew and English text from Sefaria API"""
        try:
            url = f"https://www.sefaria.org/api/texts/{book_name}.{chapter}"
            params = {
                'context': 0,
                'commentary': 0
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            hebrew_text = data.get('he', [])
            english_text = data.get('text', [])

            if isinstance(hebrew_text, str):
                hebrew_text = [hebrew_text]
            if isinstance(english_text, str):
                english_text = [english_text]

            return hebrew_text, english_text

        except Exception as e:
            print(f"Error fetching {book_name} chapter {chapter}: {e}")
            return [], []

    def get_chapter_count(self, book_name: str) -> int:
        """Get the number of chapters in a book"""
        try:
            url = f"https://www.sefaria.org/api/texts/{book_name}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if 'lengths' in data and len(data['lengths']) > 0:
                return data['lengths'][0]
            return 0

        except Exception as e:
            print(f"Error getting chapter count for {book_name}: {e}")
            return 0

    def create_css(self) -> str:
        """Create responsive CSS for parallel text display"""
        return '''
        @charset "UTF-8";

        @font-face {
            font-family: "SBL Hebrew";
            src: url("fonts/SBL_Hbrw.ttf");
        }

        html, body {
            margin: 0;
            padding: 0;
            font-family: "Georgia", serif;
            line-height: 1.6;
        }

        .chapter-title {
            text-align: center;
            font-size: 1.5em;
            margin: 1em 0;
            page-break-after: avoid;
        }

        .verse-container {
            margin: 0.5em 0;
            padding: 0.5em;
            clear: both;
        }

        .verse-number {
            font-weight: bold;
            color: #666;
            display: inline-block;
            min-width: 2em;
            margin-right: 0.5em;
        }

        .hebrew-text {
            font-family: "SBL Hebrew", "Times New Roman", serif;
            font-size: 1.2em;
            direction: rtl;
            text-align: right;
            margin-bottom: 0.3em;
        }

        .english-text {
            direction: ltr;
            text-align: left;
            color: #333;
        }

        /* Landscape mode - side by side */
        @media (orientation: landscape) and (min-width: 1000px) {
            .verse-container {
                display: grid;
                grid-template-columns: 48% 48%;
                gap: 4%;
                align-items: start;
            }

            .hebrew-text {
                margin-bottom: 0;
            }
        }

        /* Portrait mode - stacked */
        @media (orientation: portrait), (max-width: 999px) {
            .verse-container {
                display: block;
            }

            .hebrew-text {
                border-bottom: 1px dotted #ccc;
                padding-bottom: 0.3em;
            }
        }

        /* Kobo Color specific optimization */
        @media (width: 1264px), (width: 1680px) {
            body {
                font-size: 16px;
            }

            .hebrew-text {
                font-size: 1.3em;
            }
        }

        .parsha-marker {
            background-color: #f0f0f0;
            padding: 0.5em;
            margin: 1em 0;
            text-align: center;
            font-weight: bold;
            page-break-after: avoid;
        }

        .book-divider {
            page-break-before: always;
            text-align: center;
            padding: 2em 0;
        }

        .book-divider h1 {
            font-size: 2em;
            margin: 0.5em 0;
        }

        .hebrew-title {
            font-family: "SBL Hebrew", serif;
            font-size: 2.5em;
            direction: rtl;
        }
        '''

    def create_chapter_html(self, book_name: str, hebrew_name: str, chapter_num: int,
                           hebrew_verses: List[str], english_verses: List[str]) -> str:
        """Create HTML for a single chapter with parallel texts"""
        html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="he" dir="ltr">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} - Chapter {chapter_num}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="chapter-title">
        <div class="hebrew-title">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</div>
        <div>{book_name} - Chapter {chapter_num}</div>
    </div>
'''

        max_verses = max(len(hebrew_verses), len(english_verses))

        for i in range(max_verses):
            hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
            english = english_verses[i] if i < len(english_verses) else ""

            if isinstance(hebrew, list):
                hebrew = " ".join(hebrew)
            if isinstance(english, list):
                english = " ".join(english)

            html += f'''
    <div class="verse-container">
        <div class="hebrew-text">
            <span class="verse-number">{self.hebrew_number(i + 1)}</span>
            {hebrew}
        </div>
        <div class="english-text">
            <span class="verse-number">{i + 1}</span>
            {english}
        </div>
    </div>
'''

        html += '''
</body>
</html>'''
        return html

    def hebrew_number(self, num: int) -> str:
        """Convert number to Hebrew numerals"""
        ones = ['', 'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט']
        tens = ['', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ']

        if num < 10:
            return ones[num]
        elif num < 100:
            ten = num // 10
            one = num % 10
            return tens[ten] + ones[one]
        else:
            return str(num)

    def add_book_divider(self, book_name: str, hebrew_name: str):
        """Add a book divider page"""
        html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="he" dir="ltr">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <div class="book-divider">
        <h1 class="hebrew-title">{hebrew_name}</h1>
        <h1>{book_name}</h1>
    </div>
</body>
</html>'''

        chapter = epub.EpubHtml(
            title=book_name,
            file_name=f'{book_name.replace(" ", "_").lower()}_divider.xhtml',
            content=html,
            lang='he'
        )
        self.book.add_item(chapter)
        self.chapters.append(chapter)

    def generate_epub(self, output_filename: str = 'hebrew_bible.epub'):
        """Generate the complete EPUB file"""
        print("Generating Hebrew Bible EPUB...")

        # Add CSS
        css = epub.EpubItem(
            uid='style',
            file_name='styles.css',
            media_type='text/css',
            content=self.create_css()
        )
        self.book.add_item(css)

        # Process Torah books
        print("\nProcessing Torah books...")
        torah_toc = []

        for english_name, hebrew_name, _ in self.torah_books:
            print(f"Processing {english_name}...")
            self.add_book_divider(english_name, hebrew_name)

            chapter_count = self.get_chapter_count(english_name)
            book_chapters = []

            for chapter_num in range(1, chapter_count + 1):
                print(f"  Chapter {chapter_num}/{chapter_count}")
                hebrew_verses, english_verses = self.fetch_text(english_name, chapter_num)

                if hebrew_verses or english_verses:
                    html_content = self.create_chapter_html(
                        english_name, hebrew_name, chapter_num,
                        hebrew_verses, english_verses
                    )

                    chapter = epub.EpubHtml(
                        title=f'{english_name} {chapter_num}',
                        file_name=f'{english_name.replace(" ", "_").lower()}_{chapter_num}.xhtml',
                        content=html_content,
                        lang='he'
                    )
                    chapter.add_item(css)

                    self.book.add_item(chapter)
                    self.chapters.append(chapter)
                    book_chapters.append(chapter)

            if book_chapters:
                torah_toc.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

        # Process Prophet books
        print("\nProcessing Prophet books...")
        prophet_toc = []

        for english_name, hebrew_name, _ in self.prophet_books:
            print(f"Processing {english_name}...")
            self.add_book_divider(english_name, hebrew_name)

            chapter_count = self.get_chapter_count(english_name)
            book_chapters = []

            for chapter_num in range(1, chapter_count + 1):
                print(f"  Chapter {chapter_num}/{chapter_count}")
                hebrew_verses, english_verses = self.fetch_text(english_name, chapter_num)

                if hebrew_verses or english_verses:
                    html_content = self.create_chapter_html(
                        english_name, hebrew_name, chapter_num,
                        hebrew_verses, english_verses
                    )

                    chapter = epub.EpubHtml(
                        title=f'{english_name} {chapter_num}',
                        file_name=f'{english_name.replace(" ", "_").lower()}_{chapter_num}.xhtml',
                        content=html_content,
                        lang='he'
                    )
                    chapter.add_item(css)

                    self.book.add_item(chapter)
                    self.chapters.append(chapter)
                    book_chapters.append(chapter)

            if book_chapters:
                prophet_toc.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

        # Add table of contents
        self.book.toc = torah_toc + prophet_toc

        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Define spine
        self.book.spine = ['nav'] + self.chapters

        # Write EPUB file
        print(f"\nWriting EPUB to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})
        print(f"EPUB generated successfully: {output_filename}")

        return output_filename


if __name__ == '__main__':
    generator = HebrewBibleEPUB()
    generator.generate_epub('hebrew_bible_kobo.epub')