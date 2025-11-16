#!/usr/bin/env python3
"""
Hebrew Bible PDF Generator for Kobo Color
Generates PDFs with side-by-side Hebrew/English text
"""

import os
import requests
import time
from typing import List, Dict, Tuple
from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle, Spacer
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping


class HebrewBiblePDF:
    def __init__(self, display_mode='both', page_orientation='portrait'):
        """
        Initialize PDF generator
        display_mode: 'hebrew', 'english', or 'both'
        page_orientation: 'portrait' or 'landscape'
        """
        self.display_mode = display_mode
        self.page_orientation = page_orientation

        # Kobo Color dimensions: 1264x1680 pixels at 300 DPI
        # That's approximately 4.2" x 5.6"
        # We'll use A5 which is close: 5.8" x 8.3"
        if page_orientation == 'landscape':
            self.pagesize = landscape(A5)
        else:
            self.pagesize = A5

        self.torah_books = [
            ('Genesis', 'בראשית', 'Bereshit'),
            ('Exodus', 'שמות', 'Shemot'),
            ('Leviticus', 'ויקרא', 'Vayikra'),
            ('Numbers', 'במדבר', 'Bamidbar'),
            ('Deuteronomy', 'דברים', 'Devarim')
        ]

        self.setup_fonts()
        self.setup_styles()

    def setup_fonts(self):
        """Register Hebrew fonts with ReportLab"""
        # Try to find a Hebrew font on the system
        hebrew_fonts = [
            '/System/Library/Fonts/Supplemental/Arial Hebrew.ttc',
            '/Library/Fonts/Arial Hebrew.ttf',
            '/usr/share/fonts/truetype/fonts-sil-ezra/SILEOT.ttf'
        ]

        for font_path in hebrew_fonts:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('Hebrew', font_path))
                    self.hebrew_font = 'Hebrew'
                    return
                except:
                    continue

        # Fallback to Helvetica if no Hebrew font found
        print("Warning: No Hebrew font found, using Helvetica")
        self.hebrew_font = 'Helvetica'

    def setup_styles(self):
        """Setup paragraph styles for Hebrew and English"""
        self.styles = getSampleStyleSheet()

        # Hebrew style - right to left
        self.styles.add(ParagraphStyle(
            name='Hebrew',
            parent=self.styles['Normal'],
            fontName=self.hebrew_font,
            fontSize=12,
            alignment=TA_RIGHT,
            rightIndent=0,
            leftIndent=0,
            wordWrap='RTL'
        ))

        # English style
        self.styles.add(ParagraphStyle(
            name='English',
            parent=self.styles['Normal'],
            fontName='Times-Roman',
            fontSize=11,
            alignment=TA_LEFT
        ))

        # Chapter title style
        self.styles.add(ParagraphStyle(
            name='ChapterTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12
        ))

        # Book title style
        self.styles.add(ParagraphStyle(
            name='BookTitle',
            parent=self.styles['Title'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=24
        ))

    def fetch_text(self, book_name: str, chapter: int) -> Tuple[List[str], List[str]]:
        """Fetch Hebrew and English text from Sefaria API"""
        try:
            url = f"https://www.sefaria.org/api/texts/{book_name}.{chapter}"
            response = requests.get(url)
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

    def clean_text(self, text: str) -> str:
        """Remove HTML tags and special characters that break ReportLab"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Replace special quotes and characters
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('—', '-').replace('–', '-')
        # Escape XML special characters for ReportLab
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def create_verse_table(self, hebrew_verses: List[str], english_verses: List[str]) -> List:
        """Create formatted content for verses"""
        story = []

        if self.display_mode == 'both' and self.page_orientation == 'landscape':
            # Side-by-side layout for landscape mode
            data = []
            max_verses = max(len(hebrew_verses), len(english_verses))

            for i in range(max_verses):
                hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
                english = english_verses[i] if i < len(english_verses) else ""

                if isinstance(hebrew, list):
                    hebrew = " ".join(hebrew)
                if isinstance(english, list):
                    english = " ".join(english)

                # Clean text
                hebrew = self.clean_text(hebrew)
                english = self.clean_text(english)

                # Create verse number
                verse_num = str(i + 1)

                # Format Hebrew and English with verse numbers
                hebrew_para = Paragraph(f"<b>{verse_num}.</b> {hebrew}", self.styles['Hebrew'])
                english_para = Paragraph(f"<b>{verse_num}.</b> {english}", self.styles['English'])

                data.append([hebrew_para, english_para])

            # Create table with two columns
            table = Table(data, colWidths=[self.pagesize[0]*0.45, self.pagesize[0]*0.45])
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(table)

        else:
            # Stacked layout for portrait or single language
            max_verses = max(len(hebrew_verses), len(english_verses))

            for i in range(max_verses):
                verse_content = []

                if self.display_mode in ['hebrew', 'both']:
                    hebrew = hebrew_verses[i] if i < len(hebrew_verses) else ""
                    if isinstance(hebrew, list):
                        hebrew = " ".join(hebrew)
                    hebrew = self.clean_text(hebrew)

                    hebrew_para = Paragraph(
                        f"<b>{i + 1}.</b> {hebrew}",
                        self.styles['Hebrew']
                    )
                    verse_content.append(hebrew_para)

                if self.display_mode in ['english', 'both']:
                    english = english_verses[i] if i < len(english_verses) else ""
                    if isinstance(english, list):
                        english = " ".join(english)
                    english = self.clean_text(english)

                    english_para = Paragraph(
                        f"<b>{i + 1}.</b> {english}",
                        self.styles['English']
                    )
                    verse_content.append(english_para)

                if self.display_mode == 'both':
                    verse_content.append(Spacer(1, 6))

                # Keep verse together on same page
                story.append(KeepTogether(verse_content))
                story.append(Spacer(1, 6))

        return story

    def generate_pdf(self, output_filename: str = 'torah.pdf', books_to_include=None):
        """Generate the PDF file"""
        print(f"Generating Hebrew Bible PDF...")
        print(f"Display mode: {self.display_mode}")
        print(f"Orientation: {self.page_orientation}")

        # Create PDF document
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=self.pagesize,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        story = []

        # Add title page
        story.append(Paragraph("Torah", self.styles['BookTitle']))
        story.append(Paragraph("תורה", self.styles['BookTitle']))
        story.append(PageBreak())

        # Process books
        books = books_to_include or self.torah_books

        for english_name, hebrew_name, transliteration in books[:1]:  # Just Genesis for testing
            print(f"\nProcessing {english_name}...")

            # Add book title
            story.append(Paragraph(f"{english_name} - {hebrew_name}", self.styles['BookTitle']))
            story.append(PageBreak())

            chapter_count = self.get_chapter_count(english_name)

            for chapter_num in range(1, min(4, chapter_count + 1)):  # Just first 3 chapters for testing
                print(f"  Chapter {chapter_num}/{chapter_count}")

                # Add chapter title
                chapter_title = f"{english_name} Chapter {chapter_num}"
                story.append(Paragraph(chapter_title, self.styles['ChapterTitle']))

                # Fetch and add verses
                hebrew_verses, english_verses = self.fetch_text(english_name, chapter_num)

                if hebrew_verses or english_verses:
                    verse_content = self.create_verse_table(hebrew_verses, english_verses)
                    story.extend(verse_content)

                story.append(PageBreak())

                # Small delay to be nice to the API
                time.sleep(0.1)

        # Build PDF
        print(f"\nWriting PDF to {output_filename}...")
        doc.build(story)
        print(f"PDF generated successfully: {output_filename}")

        return output_filename


if __name__ == '__main__':
    import sys

    # Parse simple command line arguments
    display_mode = 'both'
    orientation = 'portrait'

    if '--hebrew-only' in sys.argv:
        display_mode = 'hebrew'
    elif '--english-only' in sys.argv:
        display_mode = 'english'

    if '--landscape' in sys.argv:
        orientation = 'landscape'

    # Generate PDF
    generator = HebrewBiblePDF(display_mode=display_mode, page_orientation=orientation)

    if orientation == 'landscape' and display_mode == 'both':
        output = 'torah_sidebyside.pdf'
    elif display_mode == 'hebrew':
        output = 'torah_hebrew.pdf'
    elif display_mode == 'english':
        output = 'torah_english.pdf'
    else:
        output = 'torah.pdf'

    generator.generate_pdf(output)