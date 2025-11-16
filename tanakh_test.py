#!/usr/bin/env python3
"""Quick test to generate Tanakh with Torah, Prophets, and Writings"""

from hebrew_bible_ultimate import UltimateHebrewBibleEPUB

class TanakhTest(UltimateHebrewBibleEPUB):
    def generate_epub(self, output_filename: str = 'tanakh_test.epub', footnote_style: str = 'inline'):
        """Generate test EPUB with just Hebrew mode but all three sections"""
        print("Generating Tanakh test with all three sections...")

        # Add CSS
        from ebooklib import epub
        css = epub.EpubItem(
            uid='style',
            file_name='styles.css',
            media_type='text/css',
            content=self.create_css()
        )
        self.book.add_item(css)

        main_toc = []
        mode_id = 'hebrew_only'

        # Torah - just Genesis ch 1-2
        print("\n📖 Torah:")
        torah_section = []
        for book in self.torah_books[:1]:  # Just Genesis
            english_name, hebrew_name, _ = book
            print(f"  {english_name}")
            book_chapters = []

            for ch in range(1, 3):  # 2 chapters
                self.footnote_counter = 0
                text_data = self.fetch_text_with_commentary(english_name, ch)

                if text_data['hebrew'] or text_data['english']:
                    html = self.create_chapter_html(
                        english_name, hebrew_name, ch,
                        text_data, mode_id, footnote_style
                    )

                    chapter = epub.EpubHtml(
                        title=f'{english_name} {ch}',
                        file_name=f'torah_{english_name.lower()}_{ch}.xhtml',
                        content=html,
                        lang='he'
                    )
                    chapter.add_item(css)
                    self.book.add_item(chapter)
                    self.chapters.append(chapter)
                    book_chapters.append(chapter)

            if book_chapters:
                torah_section.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

        # Prophets - just Isaiah ch 1-2
        print("\n📖 Prophets:")
        prophets_section = []
        for book in [b for b in self.prophet_books if b[0] == 'Isaiah']:
            english_name, hebrew_name, _ = book
            print(f"  {english_name}")
            book_chapters = []

            for ch in range(1, 3):
                self.footnote_counter = 0
                text_data = self.fetch_text_with_commentary(english_name, ch)

                if text_data['hebrew'] or text_data['english']:
                    html = self.create_chapter_html(
                        english_name, hebrew_name, ch,
                        text_data, mode_id, footnote_style
                    )

                    chapter = epub.EpubHtml(
                        title=f'{english_name} {ch}',
                        file_name=f'prophets_{english_name.lower()}_{ch}.xhtml',
                        content=html,
                        lang='he'
                    )
                    chapter.add_item(css)
                    self.book.add_item(chapter)
                    self.chapters.append(chapter)
                    book_chapters.append(chapter)

            if book_chapters:
                prophets_section.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

        # Writings - Psalms 1-3 and Daniel 1-2
        print("\n📖 Writings:")
        writings_section = []
        for book in [b for b in self.writings_books if b[0] in ['Psalms', 'Daniel']]:
            english_name, hebrew_name, _ = book
            print(f"  {english_name}")
            book_chapters = []

            max_ch = 3 if english_name == 'Psalms' else 2
            for ch in range(1, max_ch + 1):
                self.footnote_counter = 0
                text_data = self.fetch_text_with_commentary(english_name, ch)

                if text_data['hebrew'] or text_data['english']:
                    html = self.create_chapter_html(
                        english_name, hebrew_name, ch,
                        text_data, mode_id, footnote_style
                    )

                    chapter = epub.EpubHtml(
                        title=f'{english_name} {ch}',
                        file_name=f'writings_{english_name.lower()}_{ch}.xhtml',
                        content=html,
                        lang='he'
                    )
                    chapter.add_item(css)
                    self.book.add_item(chapter)
                    self.chapters.append(chapter)
                    book_chapters.append(chapter)

            if book_chapters:
                writings_section.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

        # Build TOC
        if torah_section:
            main_toc.append((epub.Section('Torah / תורה'),
                           [item for section, items in torah_section for item in [section] + items]))
        if prophets_section:
            main_toc.append((epub.Section('Prophets / נביאים'),
                           [item for section, items in prophets_section for item in [section] + items]))
        if writings_section:
            main_toc.append((epub.Section('Writings / כתובים'),
                           [item for section, items in writings_section for item in [section] + items]))

        self.book.toc = main_toc
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())
        self.book.spine = ['nav'] + self.chapters

        print(f"\n📝 Writing to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})
        print(f"✅ Complete Tanakh test generated: {output_filename}")

if __name__ == '__main__':
    gen = TanakhTest()
    gen.generate_epub()