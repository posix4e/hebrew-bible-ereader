#!/usr/bin/env python3
"""Generate a sample EPUB with just the first 2 chapters of each book for testing"""

from hebrew_bible_epub import HebrewBibleEPUB

class SampleHebrewBibleEPUB(HebrewBibleEPUB):
    def __init__(self):
        super().__init__()
        # Only include first book from Torah and Prophets for testing
        self.torah_books = [
            ('Genesis', 'בראשית', 'Bereshit'),
        ]
        self.prophet_books = [
            ('Isaiah', 'ישעיהו', 'Yeshayahu'),
        ]

    def generate_epub(self, output_filename: str = 'hebrew_bible_sample.epub'):
        """Generate a sample EPUB file with limited chapters"""
        print("Generating Hebrew Bible Sample EPUB...")

        # Add CSS
        from ebooklib import epub
        css = epub.EpubItem(
            uid='style',
            file_name='styles.css',
            media_type='text/css',
            content=self.create_css()
        )
        self.book.add_item(css)

        # Process Torah books (only first 2 chapters)
        print("\nProcessing Torah sample...")
        torah_toc = []

        for english_name, hebrew_name, _ in self.torah_books:
            print(f"Processing {english_name}...")
            self.add_book_divider(english_name, hebrew_name)

            book_chapters = []

            for chapter_num in range(1, 3):  # Only first 2 chapters
                print(f"  Chapter {chapter_num}")
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

        # Process Prophet books (only first 2 chapters)
        print("\nProcessing Prophets sample...")
        prophet_toc = []

        for english_name, hebrew_name, _ in self.prophet_books:
            print(f"Processing {english_name}...")
            self.add_book_divider(english_name, hebrew_name)

            book_chapters = []

            for chapter_num in range(1, 3):  # Only first 2 chapters
                print(f"  Chapter {chapter_num}")
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
        print(f"Sample EPUB generated successfully: {output_filename}")

        return output_filename


if __name__ == '__main__':
    generator = SampleHebrewBibleEPUB()
    generator.generate_epub()