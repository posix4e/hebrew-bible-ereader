#!/usr/bin/env python3
"""
Generate a collection of Hebrew Bible EPUBs for different reading preferences
Each EPUB is focused and optimized for its specific purpose
"""

import os
import sys
import time
from hebrew_bible_enhanced import EnhancedHebrewBibleEPUB
from config import BibleConfig


class CollectionGenerator:
    def __init__(self):
        self.collection = [
            # Basic reading versions
            {
                'filename': '01_torah_hebrew.epub',
                'title': 'Torah - Hebrew Only',
                'description': 'Pure Hebrew text for fluent readers',
                'config': {
                    'DISPLAY_MODE': 'hebrew',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': False,
                    'INCLUDE_RASHI': False,
                    'PARSHA_MARKERS': True
                }
            },
            {
                'filename': '02_torah_english_jps.epub',
                'title': 'Torah - English (JPS)',
                'description': 'Modern JPS translation',
                'config': {
                    'DISPLAY_MODE': 'english',
                    'ENGLISH_VERSION': 'Tanakh: The Holy Scriptures, published by JPS',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': False,
                    'INCLUDE_RASHI': False
                }
            },
            {
                'filename': '03_torah_bilingual.epub',
                'title': 'Torah - Hebrew & English',
                'description': 'Side-by-side Hebrew and English',
                'config': {
                    'DISPLAY_MODE': 'both',
                    'ENGLISH_VERSION': 'default',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': False,
                    'INCLUDE_RASHI': False,
                    'PARSHA_MARKERS': True
                }
            },

            # Study editions
            {
                'filename': '04_torah_rashi.epub',
                'title': 'Torah with Rashi',
                'description': 'Hebrew text with Rashi commentary',
                'config': {
                    'DISPLAY_MODE': 'hebrew',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': False,
                    'INCLUDE_RASHI': True,
                    'PARSHA_MARKERS': True
                }
            },
            {
                'filename': '05_torah_study_edition.epub',
                'title': 'Torah Study Edition',
                'description': 'Hebrew, English, and Rashi commentary',
                'config': {
                    'DISPLAY_MODE': 'both',
                    'ENGLISH_VERSION': 'Tanakh: The Holy Scriptures, published by JPS',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': False,
                    'INCLUDE_RASHI': True,
                    'PARSHA_MARKERS': True
                }
            },

            # Prophets
            {
                'filename': '06_prophets_hebrew.epub',
                'title': 'Prophets - Hebrew Only',
                'description': 'Nevi\'im in Hebrew',
                'config': {
                    'DISPLAY_MODE': 'hebrew',
                    'INCLUDE_TORAH': False,
                    'INCLUDE_PROPHETS': True,
                    'INCLUDE_RASHI': False
                }
            },
            {
                'filename': '07_prophets_bilingual.epub',
                'title': 'Prophets - Hebrew & English',
                'description': 'Nevi\'im with translation',
                'config': {
                    'DISPLAY_MODE': 'both',
                    'INCLUDE_TORAH': False,
                    'INCLUDE_PROPHETS': True,
                    'INCLUDE_RASHI': False
                }
            },

            # Complete Tanakh
            {
                'filename': '08_tanakh_hebrew.epub',
                'title': 'Complete Tanakh - Hebrew',
                'description': 'All 24 books in Hebrew',
                'config': {
                    'DISPLAY_MODE': 'hebrew',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': True,
                    'INCLUDE_WRITINGS': False,  # Would need to add this
                    'INCLUDE_RASHI': False
                }
            },

            # Alternative translations
            {
                'filename': '09_torah_koren.epub',
                'title': 'Torah - Koren Translation',
                'description': 'Israeli English translation',
                'config': {
                    'DISPLAY_MODE': 'english',
                    'ENGLISH_VERSION': 'The Koren Jerusalem Bible',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': False,
                    'INCLUDE_RASHI': False
                }
            },
            {
                'filename': '10_torah_jps_1917.epub',
                'title': 'Torah - Classic JPS (1917)',
                'description': 'Traditional Jewish translation',
                'config': {
                    'DISPLAY_MODE': 'english',
                    'ENGLISH_VERSION': 'The Holy Scriptures: A New Translation (JPS 1917)',
                    'INCLUDE_TORAH': True,
                    'INCLUDE_PROPHETS': False,
                    'INCLUDE_RASHI': False
                }
            }
        ]

    def generate_all(self, output_dir='collection', test_mode=False):
        """Generate all EPUBs in the collection"""

        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print("=" * 70)
        print("HEBREW BIBLE EPUB COLLECTION GENERATOR")
        print("=" * 70)
        print(f"\nGenerating {len(self.collection)} EPUBs...")
        print(f"Output directory: {output_dir}")
        print("=" * 70)

        # Generate index file
        self.create_index(output_dir)

        generated = []
        failed = []

        for i, epub_config in enumerate(self.collection, 1):
            print(f"\n[{i}/{len(self.collection)}] {epub_config['title']}")
            print(f"     {epub_config['description']}")
            print(f"     Output: {epub_config['filename']}")

            if test_mode and i > 3:
                print("     [Skipped in test mode]")
                continue

            try:
                # Create config
                config = BibleConfig()
                for key, value in epub_config['config'].items():
                    setattr(config, key, value)

                # Generate EPUB
                generator = EnhancedHebrewBibleEPUB(config)
                output_path = os.path.join(output_dir, epub_config['filename'])

                # In test mode, generate only first few chapters
                if test_mode:
                    # Temporarily limit chapters for testing
                    print("     [Test mode: Limited chapters]")

                generator.generate_epub(output_path)

                generated.append(epub_config['filename'])
                print(f"     ✅ Generated successfully")

                # Small delay between generations
                time.sleep(0.5)

            except Exception as e:
                print(f"     ❌ Failed: {e}")
                failed.append(epub_config['filename'])

        # Summary
        print("\n" + "=" * 70)
        print("GENERATION COMPLETE")
        print(f"✅ Successfully generated: {len(generated)} EPUBs")
        if failed:
            print(f"❌ Failed: {len(failed)} EPUBs")
            for f in failed:
                print(f"   - {f}")

        print(f"\n📚 Collection saved to: {output_dir}/")
        print(f"📋 Index file: {output_dir}/INDEX.md")
        print("=" * 70)

        return generated, failed

    def create_index(self, output_dir):
        """Create an index file describing the collection"""
        index_content = """# Hebrew Bible EPUB Collection

## 📚 About This Collection

This collection provides multiple versions of the Hebrew Bible (Tanakh) optimized for different reading preferences on Kobo Color and other e-readers.

## 📖 Available EPUBs

### Basic Reading Editions

1. **01_torah_hebrew.epub** - Torah in Hebrew only
   - Pure Hebrew text for fluent readers
   - Includes parsha (weekly portion) markers

2. **02_torah_english_jps.epub** - Torah in English (JPS)
   - Modern Jewish Publication Society translation
   - Standard for synagogue use

3. **03_torah_bilingual.epub** - Torah Hebrew & English
   - Side-by-side in landscape, stacked in portrait
   - Perfect for language learning

### Study Editions

4. **04_torah_rashi.epub** - Torah with Rashi Commentary
   - Hebrew text with classic Rashi commentary
   - Essential for traditional study

5. **05_torah_study_edition.epub** - Complete Study Edition
   - Hebrew text + English translation + Rashi
   - Comprehensive study tool

### Prophets (Nevi'im)

6. **06_prophets_hebrew.epub** - Prophets in Hebrew
   - All 21 prophetic books

7. **07_prophets_bilingual.epub** - Prophets Hebrew & English
   - Parallel text for study

### Complete Tanakh

8. **08_tanakh_hebrew.epub** - Complete Hebrew Bible
   - All 24 books in Hebrew

### Alternative Translations

9. **09_torah_koren.epub** - Koren Jerusalem Bible
   - Israeli English translation

10. **10_torah_jps_1917.epub** - Classic JPS (1917)
    - Traditional Jewish translation (Public Domain)

## 🎯 Which Version Should I Use?

- **Just reading in Hebrew**: Use 01_torah_hebrew.epub
- **Just reading in English**: Use 02_torah_english_jps.epub
- **Learning Hebrew**: Use 03_torah_bilingual.epub
- **Traditional study**: Use 04_torah_rashi.epub
- **Comprehensive study**: Use 05_torah_study_edition.epub
- **Comparing translations**: Keep multiple English versions

## 📱 Kobo Color Tips

1. **Portrait Mode**: Text stacks vertically (Hebrew above, English below)
2. **Landscape Mode**: True side-by-side columns
3. **Font Size**: Adjust using Kobo's built-in controls
4. **Navigation**: Use Table of Contents to jump between books/chapters

## ⚙️ Technical Details

- Format: EPUB3
- Hebrew Support: Full RTL with proper fonts
- Optimized for: 1264x1680 (Kobo Color)
- Commentary: Inline below verses for easy reading

## 📅 Weekly Torah Portions

All Torah EPUBs include parsha markers for weekly readings:
- Bereshit (Genesis)
- Shemot (Exodus)
- Vayikra (Leviticus)
- Bamidbar (Numbers)
- Devarim (Deuteronomy)

## 🔄 Updates

Generated using Sefaria API
Last updated: """ + time.strftime("%Y-%m-%d") + """

---

Transfer any EPUB to your Kobo via USB. Each file is standalone and complete.
"""

        index_path = os.path.join(output_dir, 'INDEX.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        print(f"Created index: {index_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate Hebrew Bible EPUB Collection')
    parser.add_argument('--test', action='store_true', help='Test mode (only first 3 EPUBs)')
    parser.add_argument('--output', default='collection', help='Output directory')
    parser.add_argument('--only', type=int, help='Generate only EPUB number N')

    args = parser.parse_args()

    generator = CollectionGenerator()

    if args.only:
        # Generate single EPUB by number
        if 1 <= args.only <= len(generator.collection):
            epub = generator.collection[args.only - 1]
            print(f"Generating single EPUB: {epub['title']}")
            # Generate just this one
            generator.collection = [epub]
            generator.generate_all(args.output, test_mode=False)
        else:
            print(f"Invalid number. Choose 1-{len(generator.collection)}")
    else:
        # Generate all
        generator.generate_all(args.output, test_mode=args.test)


if __name__ == '__main__':
    main()