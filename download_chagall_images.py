#!/usr/bin/env python3
"""
Download Chagall Bible illustrations using the scraped configuration
"""

import time
import json
import requests
from pathlib import Path
from typing import Dict, List
import sys


def download_image(url: str, save_path: Path, headers: Dict) -> bool:
    """Download an image from URL and save it"""
    try:
        print(f"  Downloading: {save_path.name}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Check if we got an image
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type:
            print(f"    ✗ Not an image (content-type: {content_type})")
            return False

        # Save the image
        with open(save_path, "wb") as f:
            f.write(response.content)

        # Check file size
        size_kb = save_path.stat().st_size / 1024
        print(f"    ✓ Saved ({size_kb:.1f} KB)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"    ✗ Error: {e}")
        return False
    except Exception as e:
        print(f"    ✗ Unexpected error: {e}")
        return False


def load_config(config_file: str) -> List[Dict]:
    """Load the download configuration"""
    if config_file.endswith(".json"):
        with open(config_file, "r") as f:
            return json.load(f)
    elif config_file.endswith(".py"):
        # Import the Python config file
        import importlib.util

        spec = importlib.util.spec_from_file_location("config", config_file)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module.CHAGALL_ARTWORKS
    else:
        raise ValueError("Config file must be .json or .py")


def main():
    """Main download function"""
    # Determine config file
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        # Try to find config file
        if Path("chagall_download_config.json").exists():
            config_file = "chagall_download_config.json"
        elif Path("chagall_config.py").exists():
            config_file = "chagall_config.py"
        else:
            print("Error: No config file found. Run scrape_chagall.py first.")
            sys.exit(1)

    print(f"Loading configuration from: {config_file}")

    try:
        artworks = load_config(config_file)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    print(f"Found {len(artworks)} artworks to download\n")

    # Create images directory
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)

    # Headers for requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # Track statistics
    downloaded = 0
    skipped = 0
    failed = []

    # Download each image
    for i, artwork in enumerate(artworks, 1):
        print(f"{i}/{len(artworks)}: {artwork['title']}")
        print(f"  Book: {artwork['book']}")

        save_path = images_dir / artwork["filename"]

        # Skip if already exists
        if save_path.exists():
            file_size = save_path.stat().st_size
            if file_size > 1000:  # More than 1KB, probably valid
                print(f"  ⊙ Already exists ({file_size / 1024:.1f} KB)")
                skipped += 1
                continue
            else:
                print(f"  ⚠ Exists but too small ({file_size} bytes), re-downloading")

        # Download the image
        if download_image(artwork["url"], save_path, headers):
            downloaded += 1
        else:
            failed.append(artwork)

        # Be polite to the server
        if i < len(artworks):
            time.sleep(1)

        print()  # Empty line between downloads

    # Summary
    print("=" * 60)
    print(f"Download Summary:")
    print(f"  ✓ Downloaded: {downloaded}")
    print(f"  ⊙ Skipped (already exists): {skipped}")
    print(f"  ✗ Failed: {len(failed)}")

    if failed:
        print(f"\nFailed downloads:")
        for artwork in failed:
            print(f"  - {artwork['filename']} ({artwork['title']})")

    # Create/Update attribution file
    attribution_path = images_dir / "CHAGALL_ATTRIBUTION.txt"
    with open(attribution_path, "w") as f:
        f.write("Marc Chagall Bible Illustrations\n")
        f.write("=" * 50 + "\n\n")
        f.write("All Chagall Bible illustrations in this directory are\n")
        f.write("courtesy of artchive.com\n\n")
        f.write("Source: https://www.artchive.com/?s=chagall+bible\n\n")
        f.write("These images are used with permission as stated by\n")
        f.write("artchive.com, with the requirement that we reference\n")
        f.write("the source.\n\n")
        f.write("Images by Biblical Book:\n")
        f.write("-" * 30 + "\n\n")

        # Group by book
        by_book = {}
        for artwork in artworks:
            book = artwork["book"]
            if book not in by_book:
                by_book[book] = []
            if (images_dir / artwork["filename"]).exists():
                by_book[book].append(artwork)

        for book in sorted(by_book.keys()):
            if by_book[book]:
                f.write(f"{book}:\n")
                for artwork in by_book[book]:
                    f.write(f"  • {artwork['filename']}\n")
                    f.write(f"    {artwork['title']}\n")
                f.write("\n")

    print(f"\n✓ Updated attribution file: {attribution_path}")

    # Create a mapping file for use in the ebook generator
    mapping_file = Path("chagall_book_mapping.py")
    with open(mapping_file, "w") as f:
        f.write('"""Mapping of Chagall illustrations to Bible books"""\n\n')
        f.write("# Maps book names to lists of available Chagall images\n")
        f.write("CHAGALL_BOOK_IMAGES = {\n")

        for book in sorted(by_book.keys()):
            if by_book[book]:
                f.write(f'    "{book}": [\n')
                for artwork in by_book[book]:
                    f.write(f"        {{\n")
                    f.write(f'            "file": "images/{artwork["filename"]}",\n')
                    f.write(f'            "title": {repr(artwork["title"])},\n')
                    f.write(f"        }},\n")
                f.write("    ],\n")

        f.write("}\n\n")
        f.write("ATTRIBUTION_TEXT = (\n")
        f.write('    "Artwork: Marc Chagall Bible illustrations courtesy of "\n')
        f.write('    "artchive.com (https://www.artchive.com/?s=chagall+bible)"\n')
        f.write(")\n")

    print(f"✓ Created book mapping file: {mapping_file}")


if __name__ == "__main__":
    main()
