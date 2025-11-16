#!/usr/bin/env python3
import os
import json
import requests
import time
from typing import List, Dict, Tuple, Optional
from ebooklib import epub
from config import BibleConfig


class EnhancedHebrewBibleEPUB:
    def __init__(self, config: Optional[BibleConfig] = None):
        self.config = config or BibleConfig()
        self.book = epub.EpubBook()
        self.book.set_identifier('hebrew-bible-kobo-enhanced')
        self.book.set_title('Hebrew Bible - Tanakh')
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

        # Torah portions (parshiyot) mapping
        self.parshiyot = {
            'Genesis': [
                (1, 'Bereshit', 'בראשית'),
                (6, 'Noach', 'נח'),
                (12, 'Lech-Lecha', 'לך-לך'),
                (18, 'Vayera', 'וירא'),
                (23, 'Chayei Sarah', 'חיי שרה'),
                (25, 'Toldot', 'תולדות'),
                (28, 'Vayetzei', 'ויצא'),
                (32, 'Vayishlach', 'וישלח'),
                (37, 'Vayeshev', 'וישב'),
                (41, 'Miketz', 'מקץ'),
                (44, 'Vayigash', 'ויגש'),
                (47, 'Vayechi', 'ויחי')
            ],
            'Exodus': [
                (1, 'Shemot', 'שמות'),
                (6, 'Vaera', 'וארא'),
                (10, 'Bo', 'בא'),
                (13, 'Beshalach', 'בשלח'),
                (18, 'Yitro', 'יתרו'),
                (21, 'Mishpatim', 'משפטים'),
                (25, 'Terumah', 'תרומה'),
                (27, 'Tetzaveh', 'תצוה'),
                (30, 'Ki Tisa', 'כי תשא'),
                (35, 'Vayakhel', 'ויקהל'),
                (38, 'Pekudei', 'פקודי')
            ]
        }

        self.chapters = []
        self.toc = []
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

    def fetch_text_with_version(self, book_name: str, chapter: int) -> Dict:
        """Fetch Hebrew and English text with specific version from Sefaria API"""
        try:
            url = f"https://www.sefaria.org/api/texts/{book_name}.{chapter}"
            params = {
                'context': 0,
                'commentary': 0
            }

            # Add version parameter if specified
            if self.config.ENGLISH_VERSION != 'default':
                params['ven'] = self.config.ENGLISH_VERSION

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Get Hebrew text
            hebrew_text = data.get('he', [])
            if isinstance(hebrew_text, str):
                hebrew_text = [hebrew_text]

            # Get English text
            english_text = data.get('text', [])
            if isinstance(english_text, str):
                english_text = [english_text]

            # Get commentary if requested
            commentary = {}
            if self.config.INCLUDE_RASHI:
                try:
                    rashi_url = f"https://www.sefaria.org/api/texts/Rashi_on_{book_name}.{chapter}"
                    rashi_response = requests.get(rashi_url)
                    if rashi_response.status_code == 200:
                        rashi_data = rashi_response.json()
                        commentary['rashi'] = rashi_data.get('he', [])
                except:
                    pass

            return {
                'hebrew': hebrew_text,
                'english': english_text,
                'commentary': commentary,
                'version_title': data.get('versionTitle', ''),
                'hebrew_version_title': data.get('heVersionTitle', '')
            }

        except Exception as e:
            print(f"Error fetching {book_name} chapter {chapter}: {e}")
            return {'hebrew': [], 'english': [], 'commentary': {}}

    def create_enhanced_css(self) -> str:
        """Create enhanced responsive CSS with configuration support"""
        display_rules = ""

        if self.config.DISPLAY_MODE == 'hebrew':
            display_rules = ".english-text { display: none; }"
        elif self.config.DISPLAY_MODE == 'english':
            display_rules = ".hebrew-text { display: none; }"

        return f'''
        @charset "UTF-8";

        @font-face {{
            font-family: "SBL Hebrew";
            src: url("fonts/SBL_Hbrw.ttf");
        }}

        html, body {{
            margin: 0;
            padding: 0;
            font-family: "Georgia", serif;
            line-height: 1.6;
        }}

        .chapter-title {{
            text-align: center;
            font-size: 1.5em;
            margin: 1em 0;
            page-break-after: avoid;
        }}

        .verse-container {{
            margin: 0.5em 0;
            padding: 0.5em;
            clear: both;
        }}

        .verse-number {{
            font-weight: bold;
            color: #666;
            display: {'inline-block' if self.config.VERSE_NUMBERS else 'none'};
            min-width: 2em;
            margin-right: 0.5em;
        }}

        .hebrew-text {{
            font-family: "SBL Hebrew", "Times New Roman", serif;
            font-size: {self.config.HEBREW_FONT_SIZE};
            direction: rtl;
            text-align: right;
            margin-bottom: 0.3em;
        }}

        .english-text {{
            direction: ltr;
            text-align: left;
            color: #333;
            font-size: {self.config.ENGLISH_FONT_SIZE};
        }}

        {display_rules}

        /* Landscape mode - side by side */
        @media (orientation: landscape) and (min-width: 1000px) {{
            .verse-container {{
                display: {'grid' if self.config.SIDE_BY_SIDE_IN_LANDSCAPE else 'block'};
                grid-template-columns: 48% 48%;
                gap: 4%;
                align-items: start;
            }}

            .hebrew-text {{
                margin-bottom: {'0' if self.config.SIDE_BY_SIDE_IN_LANDSCAPE else '0.3em'};
            }}
        }}

        /* Portrait mode - stacked */
        @media (orientation: portrait), (max-width: 999px) {{
            .verse-container {{
                display: block;
            }}

            .hebrew-text {{
                border-bottom: 1px dotted #ccc;
                padding-bottom: 0.3em;
            }}
        }}

        /* Kobo Color specific optimization */
        @media (width: 1264px), (width: 1680px) {{
            body {{
                font-size: 16px;
            }}

            .hebrew-text {{
                font-size: 1.3em;
            }}
        }}

        .parsha-marker {{
            background-color: #f0f0f0;
            padding: 0.5em;
            margin: 1em 0;
            text-align: center;
            font-weight: bold;
            page-break-after: avoid;
            display: {'block' if self.config.PARSHA_MARKERS else 'none'};
        }}

        .book-divider {{
            page-break-before: always;
            text-align: center;
            padding: 2em 0;
        }}

        .book-divider h1 {{
            font-size: 2em;
            margin: 0.5em 0;
        }}

        .hebrew-title {{
            font-family: "SBL Hebrew", serif;
            font-size: 2.5em;
            direction: rtl;
        }}

        sup {{
            font-size: 0.7em;
            color: #0066cc;
            font-weight: bold;
        }}

        .commentary-inline {{
            background-color: #f5f5f5;
            border-left: 3px solid #4a90e2;
            padding: 8px 12px;
            margin: 8px 0 12px 0;
            font-size: 0.9em;
        }}

        .commentary-number {{
            font-weight: bold;
            color: #0066cc;
            margin-right: 8px;
        }}

        .rashi-text {{
            font-family: "SBL Hebrew", serif;
            direction: rtl;
            text-align: right;
            display: inline-block;
            width: calc(100% - 30px);
            color: #444;
            line-height: 1.4;
        }}

        .version-info {{
            font-size: 0.8em;
            color: #666;
            text-align: center;
            margin: 0.5em 0;
            font-style: italic;
        }}
        '''

    def create_enhanced_chapter_html(self, book_name: str, hebrew_name: str,
                                   chapter_num: int, text_data: Dict) -> str:
        """Create enhanced HTML for a chapter with all features"""
        hebrew_verses = text_data['hebrew']
        english_verses = text_data['english']
        commentary = text_data.get('commentary', {})

        # Check for parsha marker
        parsha_html = ""
        if self.config.PARSHA_MARKERS and book_name in self.parshiyot:
            for chapter, parsha_eng, parsha_heb in self.parshiyot[book_name]:
                if chapter == chapter_num:
                    parsha_html = f'''
    <div class="parsha-marker">
        <div class="hebrew-title">פרשת {parsha_heb}</div>
        <div>Parashat {parsha_eng}</div>
    </div>'''
                    break

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
    </div>'''

        # Add version info if not default
        if self.config.ENGLISH_VERSION != 'default' and text_data.get('version_title'):
            html += f'''
    <div class="version-info">Translation: {text_data['version_title']}</div>'''

        # Add parsha marker if applicable
        html += parsha_html

        max_verses = max(len(hebrew_verses), len(english_verses))

        for i in range(max_verses):
            hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
            english = english_verses[i] if i < len(english_verses) else ""

            if isinstance(hebrew, list):
                hebrew = " ".join(hebrew)
            if isinstance(english, list):
                english = " ".join(english)

            # Add Rashi commentary as inline note or popup if available
            footnote_ref = ""
            rashi_inline = ""
            if self.config.INCLUDE_RASHI and commentary.get('rashi'):
                if i < len(commentary['rashi']) and commentary['rashi'][i]:
                    self.footnote_counter += 1
                    rashi_text = commentary['rashi'][i]
                    if isinstance(rashi_text, list):
                        rashi_text = " ".join(rashi_text)

                    # For EPUB, use a superscript number with the commentary inline below the verse
                    footnote_ref = f'<sup>[{self.footnote_counter}]</sup>'
                    rashi_inline = f'''<div class="commentary-inline">
                        <span class="commentary-number">[{self.footnote_counter}]</span>
                        <span class="rashi-text">{rashi_text}</span>
                    </div>'''

            html += f'''
    <div class="verse-container">'''

            if self.config.DISPLAY_MODE in ['hebrew', 'both']:
                html += f'''
        <div class="hebrew-text">
            <span class="verse-number">{self.hebrew_number(i + 1)}</span>
            {hebrew}{footnote_ref}
        </div>'''

            if self.config.DISPLAY_MODE in ['english', 'both']:
                html += f'''
        <div class="english-text">
            <span class="verse-number">{i + 1}</span>
            {english}
        </div>'''

            # Add Rashi commentary inline if present
            if rashi_inline:
                html += rashi_inline

            html += '''
    </div>'''

        # Footnotes are now inline, so we don't need this section

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

    def generate_epub(self, output_filename: str = 'hebrew_bible_enhanced.epub'):
        """Generate the enhanced EPUB file"""
        print("=" * 60)
        print("Enhanced Hebrew Bible EPUB Generator")
        print("=" * 60)
        print(f"Display Mode: {self.config.DISPLAY_MODE}")
        print(f"English Version: {self.config.ENGLISH_VERSION}")
        print(f"Include Rashi: {self.config.INCLUDE_RASHI}")
        print(f"Include Torah: {self.config.INCLUDE_TORAH}")
        print(f"Include Prophets: {self.config.INCLUDE_PROPHETS}")
        print("=" * 60)

        # Add CSS
        css = epub.EpubItem(
            uid='style',
            file_name='styles.css',
            media_type='text/css',
            content=self.create_enhanced_css()
        )
        self.book.add_item(css)

        all_toc = []

        # Process Torah if included
        if self.config.INCLUDE_TORAH:
            print("\n📖 Processing Torah...")
            for english_name, hebrew_name, _ in self.torah_books:
                print(f"Processing {english_name}...")

                book_chapters = []
                chapter_count = self.get_chapter_count(english_name)
                for chapter_num in range(1, chapter_count + 1):
                    print(f"  Chapter {chapter_num}")
                    text_data = self.fetch_text_with_version(english_name, chapter_num)

                    if text_data['hebrew'] or text_data['english']:
                        html_content = self.create_enhanced_chapter_html(
                            english_name, hebrew_name, chapter_num, text_data
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

                    time.sleep(self.config.API_DELAY)

                if book_chapters:
                    all_toc.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

        # Add table of contents
        self.book.toc = all_toc

        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Define spine
        self.book.spine = ['nav'] + self.chapters

        # Write EPUB file
        print(f"\n📝 Writing EPUB to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})
        print(f"✅ EPUB generated successfully: {output_filename}")

        return output_filename


if __name__ == '__main__':
    # Example with custom configuration
    config = BibleConfig()
    config.DISPLAY_MODE = 'both'  # Show both Hebrew and English
    config.ENGLISH_VERSION = 'default'  # Use default translation
    config.INCLUDE_RASHI = True  # Include Rashi commentary
    config.PARSHA_MARKERS = True  # Show Torah portion markers

    generator = EnhancedHebrewBibleEPUB(config)
    generator.generate_epub('hebrew_bible_custom.epub')