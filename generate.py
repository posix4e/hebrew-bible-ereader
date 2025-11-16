#!/usr/bin/env python3
"""
Interactive Hebrew Bible EPUB Generator

Usage:
    python generate.py                  # Interactive mode
    python generate.py --hebrew-only     # Hebrew text only
    python generate.py --english-only    # English text only
    python generate.py --torah           # Torah only
    python generate.py --prophets        # Prophets only
"""

import argparse
from config import BibleConfig
from hebrew_bible_enhanced import EnhancedHebrewBibleEPUB


def interactive_setup():
    """Interactive configuration setup"""
    config = BibleConfig()

    print("=" * 60)
    print("Hebrew Bible EPUB Generator - Interactive Setup")
    print("=" * 60)

    # Language selection
    print("\nLanguage Display Options:")
    print("1. Both Hebrew and English (side-by-side/stacked)")
    print("2. Hebrew only")
    print("3. English only")
    choice = input("Select language display (1-3) [1]: ").strip() or "1"

    if choice == "2":
        config.DISPLAY_MODE = 'hebrew'
    elif choice == "3":
        config.DISPLAY_MODE = 'english'
    else:
        config.DISPLAY_MODE = 'both'

    # Translation version (if English is included)
    if config.DISPLAY_MODE in ['english', 'both']:
        print("\nEnglish Translation Options:")
        print("1. Default Sefaria translation")
        print("2. JPS (1985)")
        print("3. Koren Jerusalem Bible")
        print("4. Sefaria Community Translation")
        trans_choice = input("Select translation (1-4) [1]: ").strip() or "1"

        translations = {
            "1": "default",
            "2": "The Jewish Publication Society's Tanakh (1985)",
            "3": "The Koren Jerusalem Bible",
            "4": "Sefaria Community Translation"
        }
        config.ENGLISH_VERSION = translations.get(trans_choice, "default")

    # Books selection
    print("\nBooks to Include:")
    print("1. Torah only (Five Books of Moses)")
    print("2. Prophets only (Nevi'im)")
    print("3. Both Torah and Prophets")
    books_choice = input("Select books (1-3) [3]: ").strip() or "3"

    if books_choice == "1":
        config.INCLUDE_TORAH = True
        config.INCLUDE_PROPHETS = False
        output_name = "torah"
    elif books_choice == "2":
        config.INCLUDE_TORAH = False
        config.INCLUDE_PROPHETS = True
        output_name = "prophets"
    else:
        config.INCLUDE_TORAH = True
        config.INCLUDE_PROPHETS = True
        output_name = "tanakh"

    # Commentary options
    if config.DISPLAY_MODE in ['hebrew', 'both']:
        include_rashi = input("\nInclude Rashi commentary as footnotes? (y/n) [n]: ").strip().lower()
        config.INCLUDE_RASHI = include_rashi == 'y'

    # Formatting options
    include_parsha = input("Include Torah portion (Parsha) markers? (y/n) [y]: ").strip().lower()
    config.PARSHA_MARKERS = include_parsha != 'n'

    show_verses = input("Show verse numbers? (y/n) [y]: ").strip().lower()
    config.VERSE_NUMBERS = show_verses != 'n'

    # Output filename
    suffix = ""
    if config.DISPLAY_MODE == 'hebrew':
        suffix = "_hebrew"
    elif config.DISPLAY_MODE == 'english':
        suffix = "_english"

    if config.INCLUDE_RASHI:
        suffix += "_rashi"

    filename = f"{output_name}{suffix}.epub"
    custom_name = input(f"\nOutput filename [{filename}]: ").strip()
    if custom_name:
        filename = custom_name if custom_name.endswith('.epub') else custom_name + '.epub'

    print("\n" + "=" * 60)
    print("Configuration Summary:")
    print(f"  Display: {config.DISPLAY_MODE}")
    if config.DISPLAY_MODE in ['english', 'both']:
        print(f"  Translation: {config.ENGLISH_VERSION}")
    print(f"  Books: {'Torah' if config.INCLUDE_TORAH else ''} {'Prophets' if config.INCLUDE_PROPHETS else ''}")
    print(f"  Rashi Commentary: {'Yes' if config.INCLUDE_RASHI else 'No'}")
    print(f"  Parsha Markers: {'Yes' if config.PARSHA_MARKERS else 'No'}")
    print(f"  Output: {filename}")
    print("=" * 60)

    confirm = input("\nProceed with generation? (y/n) [y]: ").strip().lower()
    if confirm == 'n':
        print("Generation cancelled.")
        return None, None

    return config, filename


def main():
    parser = argparse.ArgumentParser(description='Generate Hebrew Bible EPUB')
    parser.add_argument('--hebrew-only', action='store_true', help='Generate Hebrew text only')
    parser.add_argument('--english-only', action='store_true', help='Generate English text only')
    parser.add_argument('--torah', action='store_true', help='Include Torah only')
    parser.add_argument('--prophets', action='store_true', help='Include Prophets only')
    parser.add_argument('--rashi', action='store_true', help='Include Rashi commentary')
    parser.add_argument('--no-parsha', action='store_true', help='Exclude Parsha markers')
    parser.add_argument('--translation', type=str, help='English translation version')
    parser.add_argument('-o', '--output', type=str, help='Output filename')

    args = parser.parse_args()

    # If no arguments, run interactive mode
    if not any(vars(args).values()):
        config, filename = interactive_setup()
        if config:
            generator = EnhancedHebrewBibleEPUB(config)
            generator.generate_epub(filename)
    else:
        # Build config from arguments
        config = BibleConfig()

        if args.hebrew_only:
            config.DISPLAY_MODE = 'hebrew'
        elif args.english_only:
            config.DISPLAY_MODE = 'english'

        if args.torah and not args.prophets:
            config.INCLUDE_TORAH = True
            config.INCLUDE_PROPHETS = False
        elif args.prophets and not args.torah:
            config.INCLUDE_TORAH = False
            config.INCLUDE_PROPHETS = True

        if args.rashi:
            config.INCLUDE_RASHI = True

        if args.no_parsha:
            config.PARSHA_MARKERS = False

        if args.translation:
            config.ENGLISH_VERSION = args.translation

        output = args.output or 'hebrew_bible.epub'

        print(f"Generating EPUB with configuration:")
        print(f"  Display: {config.DISPLAY_MODE}")
        print(f"  Books: {'Torah' if config.INCLUDE_TORAH else ''} {'Prophets' if config.INCLUDE_PROPHETS else ''}")
        print(f"  Output: {output}")

        generator = EnhancedHebrewBibleEPUB(config)
        generator.generate_epub(output)


if __name__ == '__main__':
    main()