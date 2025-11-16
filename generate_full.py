#!/usr/bin/env python3
"""Generate the complete Hebrew Bible EPUB with all Torah and Prophet books"""

import time
from hebrew_bible_epub import HebrewBibleEPUB

class FullHebrewBibleEPUB(HebrewBibleEPUB):
    def __init__(self, books_to_include='both'):
        super().__init__()

        if books_to_include == 'torah':
            self.prophet_books = []
        elif books_to_include == 'prophets':
            self.torah_books = []
        # 'both' keeps all books

    def generate_epub(self, output_filename: str = 'hebrew_bible_full.epub'):
        """Generate the complete EPUB file with progress tracking"""
        print("=" * 60)
        print("Hebrew Bible EPUB Generator")
        print("=" * 60)

        start_time = time.time()

        # Calculate total chapters for progress tracking
        total_chapters = 0
        chapters_processed = 0

        print("\nCalculating total chapters...")
        for books in [self.torah_books, self.prophet_books]:
            for english_name, _, _ in books:
                count = self.get_chapter_count(english_name)
                total_chapters += count
                print(f"  {english_name}: {count} chapters")

        print(f"\nTotal chapters to process: {total_chapters}")
        print("=" * 60)

        # Add CSS
        from ebooklib import epub
        css = epub.EpubItem(
            uid='style',
            file_name='styles.css',
            media_type='text/css',
            content=self.create_css()
        )
        self.book.add_item(css)

        all_toc = []

        # Process Torah books
        if self.torah_books:
            print("\n📖 Processing Torah Books...")
            print("-" * 40)

            for english_name, hebrew_name, _ in self.torah_books:
                print(f"\n📗 {english_name} ({hebrew_name})")
                self.add_book_divider(english_name, hebrew_name)

                chapter_count = self.get_chapter_count(english_name)
                book_chapters = []

                for chapter_num in range(1, chapter_count + 1):
                    chapters_processed += 1
                    progress = (chapters_processed / total_chapters) * 100
                    print(f"  [{progress:5.1f}%] Chapter {chapter_num}/{chapter_count}", end='\r')

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

                    # Add small delay to avoid overwhelming the API
                    time.sleep(0.1)

                print(f"  ✓ Completed {chapter_count} chapters")

                if book_chapters:
                    all_toc.append((epub.Section(f'{hebrew_name} - {english_name}'), book_chapters))

        # Process Prophet books
        if self.prophet_books:
            print("\n📖 Processing Prophet Books...")
            print("-" * 40)

            for english_name, hebrew_name, _ in self.prophet_books:
                print(f"\n📘 {english_name} ({hebrew_name})")
                self.add_book_divider(english_name, hebrew_name)

                chapter_count = self.get_chapter_count(english_name)
                book_chapters = []

                for chapter_num in range(1, chapter_count + 1):
                    chapters_processed += 1
                    progress = (chapters_processed / total_chapters) * 100
                    print(f"  [{progress:5.1f}%] Chapter {chapter_num}/{chapter_count}", end='\r')

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

                    # Add small delay to avoid overwhelming the API
                    time.sleep(0.1)

                print(f"  ✓ Completed {chapter_count} chapters")

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
        print("\n" + "=" * 60)
        print(f"📝 Writing EPUB to {output_filename}...")
        epub.write_epub(output_filename, self.book, {})

        elapsed = time.time() - start_time
        print(f"✅ EPUB generated successfully in {elapsed:.1f} seconds")
        print(f"📚 Output: {output_filename}")
        print("=" * 60)

        return output_filename


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'torah':
            generator = FullHebrewBibleEPUB('torah')
            generator.generate_epub('torah.epub')
        elif sys.argv[1] == 'prophets':
            generator = FullHebrewBibleEPUB('prophets')
            generator.generate_epub('prophets.epub')
        else:
            print("Usage: python generate_full.py [torah|prophets]")
            print("  No argument generates both Torah and Prophets")
    else:
        generator = FullHebrewBibleEPUB('both')
        generator.generate_epub('hebrew_bible_full.epub')