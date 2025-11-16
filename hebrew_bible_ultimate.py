#!/usr/bin/env python3
"""
Ultimate Hebrew Bible EPUB Generator
Creates a single EPUB with all text combinations accessible through navigation
"""

import os
import json
import requests
import time
from typing import List, Dict, Tuple, Optional
from ebooklib import epub
from config import BibleConfig


class UltimateHebrewBibleEPUB:
    def __init__(self):
        self.book = epub.EpubBook()
        self.book.set_identifier('tanakh-ultimate')
        self.book.set_title('Tanakh - Complete Hebrew Bible')
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
            ('Ezekiel', 'יחזקאל', 'Yechezkel'),
            ('Hosea', 'הושע', 'Hoshea'),
            ('Joel', 'יואל', 'Yoel'),
            ('Amos', 'עמוס', 'Amos'),
            ('Obadiah', 'עובדיה', 'Ovadiah'),
            ('Jonah', 'יונה', 'Yonah'),
            ('Micah', 'מיכה', 'Michah'),
            ('Nahum', 'נחום', 'Nachum'),
            ('Habakkuk', 'חבקוק', 'Chavakuk'),
            ('Zephaniah', 'צפניה', 'Tzefaniah'),
            ('Haggai', 'חגי', 'Chaggai'),
            ('Zechariah', 'זכריה', 'Zechariah'),
            ('Malachi', 'מלאכי', 'Malachi')
        ]

        self.writings_books = [
            ('Psalms', 'תהלים', 'Tehillim'),
            ('Proverbs', 'משלי', 'Mishlei'),
            ('Job', 'איוב', 'Iyov'),
            ('Song of Songs', 'שיר השירים', 'Shir HaShirim'),
            ('Ruth', 'רות', 'Ruth'),
            ('Lamentations', 'איכה', 'Eikhah'),
            ('Ecclesiastes', 'קהלת', 'Kohelet'),
            ('Esther', 'אסתר', 'Esther'),
            ('Daniel', 'דניאל', 'Daniel'),
            ('Ezra', 'עזרא', 'Ezra'),
            ('Nehemiah', 'נחמיה', 'Nehemiah'),
            ('I Chronicles', 'דברי הימים א', 'Divrei Hayamim I'),
            ('II Chronicles', 'דברי הימים ב', 'Divrei Hayamim II')
        ]

        # Different viewing modes
        self.modes = [
            ('hebrew_only', 'Hebrew Only', 'עברית בלבד'),
            ('english_only', 'English Only', 'English Only'),
            ('both_sidebyside', 'Hebrew & English', 'עברית ואנגלית'),
            ('hebrew_rashi', 'Hebrew with Rashi', 'עברית עם רש״י'),
            ('both_rashi', 'Hebrew & English with Rashi', 'עברית ואנגלית עם רש״י')
        ]

        # Footnote display options
        self.footnote_styles = {
            'inline': 'Show commentary inline below verses',
            'endnotes': 'Collect commentary at end of chapter',
            'hidden': 'Hide commentary'
        }

        self.chapters = []
        self.footnote_counter = 0

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

    def fetch_text_with_commentary(self, book_name: str, chapter: int) -> Dict:
        """Fetch Hebrew, English, and commentary from Sefaria API"""
        try:
            # Main text
            url = f"https://www.sefaria.org/api/texts/{book_name}.{chapter}"
            response = requests.get(url, params={'context': 0, 'commentary': 0})
            response.raise_for_status()
            data = response.json()

            hebrew_text = data.get('he', [])
            english_text = data.get('text', [])

            if isinstance(hebrew_text, str):
                hebrew_text = [hebrew_text]
            if isinstance(english_text, str):
                english_text = [english_text]

            # Rashi commentary
            rashi_text = []
            try:
                rashi_url = f"https://www.sefaria.org/api/texts/Rashi_on_{book_name}.{chapter}"
                rashi_response = requests.get(rashi_url)
                if rashi_response.status_code == 200:
                    rashi_data = rashi_response.json()
                    rashi_text = rashi_data.get('he', [])
            except:
                pass

            return {
                'hebrew': hebrew_text,
                'english': english_text,
                'rashi': rashi_text
            }

        except Exception as e:
            print(f"Error fetching {book_name} chapter {chapter}: {e}")
            return {'hebrew': [], 'english': [], 'rashi': []}

    def create_css(self) -> str:
        """Create CSS for all display modes"""
        return '''
        @charset "UTF-8";

        @font-face {
            font-family: "SBL Hebrew";
            src: url("fonts/SBL_Hbrw.ttf");
        }

        body {
            margin: 0;
            padding: 0.5em;
            font-family: "Georgia", serif;
            line-height: 1.6;
        }

        /* Navigation header */
        .mode-header {
            background-color: #f0f0f0;
            padding: 0.5em;
            text-align: center;
            font-weight: bold;
            border-bottom: 2px solid #333;
            margin-bottom: 1em;
        }

        /* Chapter titles */
        .chapter-title {
            text-align: center;
            font-size: 1.5em;
            margin: 1em 0;
            page-break-after: avoid;
        }

        /* Verse containers */
        .verse-container {
            margin: 0.8em 0;
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

        /* Hebrew text */
        .hebrew-text {
            font-family: "SBL Hebrew", "Times New Roman", serif;
            font-size: 1.2em;
            direction: rtl;
            text-align: right;
            margin-bottom: 0.3em;
        }

        /* English text */
        .english-text {
            direction: ltr;
            text-align: left;
            color: #333;
            margin-bottom: 0.3em;
        }

        /* Side-by-side layout */
        .sidebyside-container {
            display: table;
            width: 100%;
            table-layout: fixed;
        }

        .sidebyside-hebrew, .sidebyside-english {
            display: table-cell;
            width: 48%;
            padding: 0 1%;
            vertical-align: top;
        }

        /* Commentary styles */
        .commentary-inline {
            background-color: #f5f5f5;
            border-left: 3px solid #4a90e2;
            padding: 8px 12px;
            margin: 8px 0 12px 0;
            font-size: 0.9em;
        }

        .commentary-hidden {
            display: none;
        }

        .commentary-endnote {
            border-top: 1px solid #ccc;
            margin-top: 2em;
            padding-top: 1em;
        }

        .commentary-number {
            font-weight: bold;
            color: #0066cc;
            margin-right: 8px;
        }

        .rashi-text {
            font-family: "SBL Hebrew", serif;
            direction: rtl;
            text-align: right;
            color: #444;
            line-height: 1.4;
        }

        sup.footnote-marker {
            font-size: 0.7em;
            color: #0066cc;
            font-weight: bold;
        }

        /* Mode-specific hiding */
        .hebrew-only .english-text,
        .hebrew-only .sidebyside-english {
            display: none !important;
        }

        .english-only .hebrew-text,
        .english-only .sidebyside-hebrew {
            display: none !important;
        }

        /* Responsive adjustments */
        @media (orientation: portrait), (max-width: 600px) {
            .sidebyside-container {
                display: block;
            }

            .sidebyside-hebrew, .sidebyside-english {
                display: block;
                width: 100%;
                padding: 0;
            }

            .sidebyside-hebrew {
                border-bottom: 1px dotted #ccc;
                padding-bottom: 0.5em;
                margin-bottom: 0.5em;
            }
        }

        /* Kobo Color optimization */
        @media (width: 1264px), (width: 1680px) {
            body {
                font-size: 16px;
            }

            .hebrew-text {
                font-size: 1.3em;
            }
        }

        /* Book divider */
        .book-divider {
            page-break-before: always;
            text-align: center;
            padding: 2em 0;
        }

        .hebrew-title {
            font-family: "SBL Hebrew", serif;
            font-size: 2em;
            direction: rtl;
        }
        '''

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

    def create_chapter_html(self, book_name: str, hebrew_name: str, chapter_num: int,
                           text_data: Dict, mode: str, footnote_style: str = 'inline') -> str:
        """Create HTML for a chapter in a specific viewing mode"""
        hebrew_verses = text_data['hebrew']
        english_verses = text_data['english']
        rashi_verses = text_data['rashi']

        # Determine mode settings
        show_hebrew = mode in ['hebrew_only', 'both_sidebyside', 'hebrew_rashi', 'both_rashi']
        show_english = mode in ['english_only', 'both_sidebyside', 'both_rashi']
        show_rashi = mode in ['hebrew_rashi', 'both_rashi']
        sidebyside = mode == 'both_sidebyside' or (mode == 'both_rashi' and footnote_style == 'hidden')

        # Mode display name
        mode_name = next((m[1] for m in self.modes if m[0] == mode), mode)

        html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="he" dir="ltr">
<head>
    <meta charset="UTF-8"/>
    <title>{book_name} Ch. {chapter_num} - {mode_name}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body class="{mode}">
    <div class="mode-header">{mode_name}</div>
    <div class="chapter-title">
        <div class="hebrew-title">{hebrew_name} פרק {self.hebrew_number(chapter_num)}</div>
        <div>{book_name} - Chapter {chapter_num}</div>
    </div>
'''

        max_verses = max(len(hebrew_verses), len(english_verses))
        endnotes = []

        for i in range(max_verses):
            hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
            english = english_verses[i] if i < len(english_verses) else ""
            rashi = rashi_verses[i] if i < len(rashi_verses) and show_rashi else ""

            if isinstance(hebrew, list):
                hebrew = " ".join(hebrew)
            if isinstance(english, list):
                english = " ".join(english)
            if isinstance(rashi, list):
                rashi = " ".join(rashi)

            # Clean text
            hebrew = self.clean_text(hebrew)
            english = self.clean_text(english)
            rashi = self.clean_text(rashi)

            # Handle footnotes
            footnote_marker = ""
            if show_rashi and rashi:
                self.footnote_counter += 1
                if footnote_style != 'hidden':
                    footnote_marker = f'<sup class="footnote-marker">[{self.footnote_counter}]</sup>'

                if footnote_style == 'endnotes':
                    endnotes.append((self.footnote_counter, rashi))

            # Create verse HTML
            if sidebyside and show_hebrew and show_english:
                html += f'''
    <div class="verse-container">
        <div class="sidebyside-container">
            <div class="sidebyside-hebrew">
                <span class="verse-number">{self.hebrew_number(i + 1)}</span>
                {hebrew}{footnote_marker}
            </div>
            <div class="sidebyside-english">
                <span class="verse-number">{i + 1}</span>
                {english}
            </div>
        </div>'''
            else:
                html += f'''
    <div class="verse-container">'''

                if show_hebrew:
                    html += f'''
        <div class="hebrew-text">
            <span class="verse-number">{self.hebrew_number(i + 1)}</span>
            {hebrew}{footnote_marker}
        </div>'''

                if show_english:
                    html += f'''
        <div class="english-text">
            <span class="verse-number">{i + 1}</span>
            {english}
        </div>'''

            # Add inline commentary if applicable
            if show_rashi and rashi and footnote_style == 'inline':
                html += f'''
        <div class="commentary-inline">
            <span class="commentary-number">[{self.footnote_counter}]</span>
            <span class="rashi-text">{rashi}</span>
        </div>'''

            html += '''
    </div>'''

        # Add endnotes if applicable
        if endnotes and footnote_style == 'endnotes':
            html += '''
    <div class="commentary-endnote">
        <h3>Commentary</h3>'''
            for num, text in endnotes:
                html += f'''
        <div class="commentary-inline">
            <span class="commentary-number">[{num}]</span>
            <span class="rashi-text">{text}</span>
        </div>'''
            html += '''
    </div>'''

        html += '''
</body>
</html>'''
        return html

    def clean_text(self, text: str) -> str:
        """Remove problematic HTML and escape special characters"""
        if not text:
            return ""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Escape special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def generate_epub(self, output_filename: str = 'hebrew_bible_ultimate.epub',
                     footnote_style: str = 'inline'):
        """Generate the ultimate EPUB with all viewing modes"""
        print("=" * 60)
        print("Complete Tanakh EPUB Generator")
        print("=" * 60)
        print("This EPUB will contain:")
        print(f"  Torah: {len(self.torah_books)} books")
        print(f"  Prophets: {len(self.prophet_books)} books")
        print(f"  Writings: {len(self.writings_books)} books")
        print("\nDisplay modes:")
        for mode_id, mode_name, hebrew_name in self.modes:
            print(f"  • {mode_name} ({hebrew_name})")
        print(f"\nFootnote style: {footnote_style}")
        print("=" * 60)

        # Add CSS
        css = epub.EpubItem(
            uid='style',
            file_name='styles.css',
            media_type='text/css',
            content=self.create_css()
        )
        self.book.add_item(css)

        # Main table of contents structure
        main_toc = []

        # Process each viewing mode
        for mode_id, mode_name, mode_hebrew in self.modes:
            print(f"\n📖 Generating {mode_name} version...")
            mode_toc = []

            # Process Torah
            torah_section = []
            for english_name, hebrew_name, _ in self.torah_books:
                print(f"  Torah: {english_name}...")

                book_chapters = []
                chapter_count = self.get_chapter_count(english_name)

                # Limit chapters for testing (3 chapters for Genesis, 2 for others)
                max_chapters = 3 if english_name == 'Genesis' else 2
                for chapter_num in range(1, min(max_chapters + 1, chapter_count + 1)):
                    print(f"    Chapter {chapter_num}")

                    # Reset footnote counter for each chapter
                    self.footnote_counter = 0

                    # Fetch text and commentary
                    text_data = self.fetch_text_with_commentary(english_name, chapter_num)

                    if text_data['hebrew'] or text_data['english']:
                        html_content = self.create_chapter_html(
                            english_name, hebrew_name, chapter_num,
                            text_data, mode_id, footnote_style
                        )

                        # Create unique filename for this mode and chapter
                        file_name = f'{mode_id}_{english_name.lower()}_{chapter_num}.xhtml'

                        chapter = epub.EpubHtml(
                            title=f'{english_name} {chapter_num}',
                            file_name=file_name,
                            content=html_content,
                            lang='he'
                        )
                        chapter.add_item(css)

                        self.book.add_item(chapter)
                        self.chapters.append(chapter)
                        book_chapters.append(chapter)

                    time.sleep(0.1)  # Be nice to the API

                if book_chapters:
                    torah_section.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

            # Process Prophets
            prophets_section = []
            for english_name, hebrew_name, _ in self.prophet_books[:3]:  # First 3 prophet books for testing
                print(f"  Prophets: {english_name}...")

                book_chapters = []
                chapter_count = self.get_chapter_count(english_name)

                # Limit to 2 chapters per prophet book for testing
                for chapter_num in range(1, min(3, chapter_count + 1)):
                    print(f"    Chapter {chapter_num}")

                    # Reset footnote counter for each chapter
                    self.footnote_counter = 0

                    # Fetch text and commentary
                    text_data = self.fetch_text_with_commentary(english_name, chapter_num)

                    if text_data['hebrew'] or text_data['english']:
                        html_content = self.create_chapter_html(
                            english_name, hebrew_name, chapter_num,
                            text_data, mode_id, footnote_style
                        )

                        # Create unique filename for this mode and chapter
                        file_name = f'{mode_id}_{english_name.replace(" ", "_").lower()}_{chapter_num}.xhtml'

                        chapter = epub.EpubHtml(
                            title=f'{english_name} {chapter_num}',
                            file_name=file_name,
                            content=html_content,
                            lang='he'
                        )
                        chapter.add_item(css)

                        self.book.add_item(chapter)
                        self.chapters.append(chapter)
                        book_chapters.append(chapter)

                    time.sleep(0.1)

                if book_chapters:
                    prophets_section.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

            # Process Writings (all books)
            writings_section = []
            for english_name, hebrew_name, _ in self.writings_books[:5]:  # First 5 Writings books for testing
                print(f"  Writings: {english_name}...")

                book_chapters = []
                chapter_count = self.get_chapter_count(english_name)

                # Limit chapters for testing (3 for Psalms, 2 for others)
                max_chapters = 3 if english_name == 'Psalms' else 2
                for chapter_num in range(1, min(max_chapters + 1, chapter_count + 1)):
                    print(f"    Chapter {chapter_num}")

                    # Reset footnote counter for each chapter
                    self.footnote_counter = 0

                    # Fetch text and commentary
                    text_data = self.fetch_text_with_commentary(english_name, chapter_num)

                    if text_data['hebrew'] or text_data['english']:
                        html_content = self.create_chapter_html(
                            english_name, hebrew_name, chapter_num,
                            text_data, mode_id, footnote_style
                        )

                        # Create unique filename for this mode and chapter
                        file_name = f'{mode_id}_{english_name.replace(" ", "_").lower()}_{chapter_num}.xhtml'

                        chapter = epub.EpubHtml(
                            title=f'{english_name} {chapter_num}',
                            file_name=file_name,
                            content=html_content,
                            lang='he'
                        )
                        chapter.add_item(css)

                        self.book.add_item(chapter)
                        self.chapters.append(chapter)
                        book_chapters.append(chapter)

                    time.sleep(0.1)

                if book_chapters:
                    writings_section.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

            # Combine Torah, Prophets, and Writings into mode TOC
            if torah_section or prophets_section or writings_section:
                mode_contents = []
                if torah_section:
                    mode_contents.append((epub.Section('Torah / תורה'),
                                         [item for section, items in torah_section for item in [section] + items]))
                if prophets_section:
                    mode_contents.append((epub.Section('Prophets / נביאים'),
                                         [item for section, items in prophets_section for item in [section] + items]))
                if writings_section:
                    mode_contents.append((epub.Section('Writings / כתובים'),
                                         [item for section, items in writings_section for item in [section] + items]))

                mode_toc = (epub.Section(f'{mode_name} / {mode_hebrew}'),
                           [item for section, items in mode_contents for item in [section] + items])

            # Add this mode to the main TOC
            if mode_toc:
                main_toc.append(mode_toc)

        # Set the table of contents
        self.book.toc = main_toc

        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Define spine (reading order)
        self.book.spine = ['nav'] + self.chapters

        # Write EPUB file
        print(f"\n📝 Writing EPUB to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})
        print(f"✅ EPUB generated successfully: {output_filename}")
        print(f"📚 Navigate between versions using the Table of Contents")

        return output_filename


if __name__ == '__main__':
    import sys

    # Parse footnote style from command line
    footnote_style = 'inline'  # default

    if '--footnotes-end' in sys.argv:
        footnote_style = 'endnotes'
    elif '--footnotes-hidden' in sys.argv:
        footnote_style = 'hidden'

    print("Footnote display:", footnote_style)

    generator = UltimateHebrewBibleEPUB()
    generator.generate_epub('hebrew_bible_ultimate.epub', footnote_style)