#!/usr/bin/env python3
"""
Scrape Chagall Bible illustrations from artchive.com to create download config
Writes config incrementally as images are discovered
"""

import time
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json


def save_config(config, config_file="chagall_download_config.json"):
    """Save the current config to file"""
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  💾 Saved {len(config)} entries to {config_file}")


def save_python_config(config, py_file="chagall_config.py"):
    """Save config as Python file"""
    with open(py_file, "w") as f:
        f.write('"""Chagall Bible illustrations configuration for download"""\n\n')
        f.write("CHAGALL_ARTWORKS = [\n")

        for item in config:
            f.write("    {\n")
            f.write(f'        "filename": "{item["filename"]}",\n')
            f.write(f'        "url": "{item["url"]}",\n')
            f.write(f'        "title": {repr(item["title"])},\n')
            f.write(f'        "book": "{item["book"]}",\n')
            f.write(f'        "page_url": "{item["page_url"]}",\n')
            f.write("    },\n")

        f.write("]\n\n")
        f.write('ATTRIBUTION = """Marc Chagall Bible illustrations courtesy of artchive.com\n')
        f.write('Source: https://www.artchive.com/?s=chagall+bible"""\n')


def get_search_results(search_url):
    """Get all artwork links from search results page"""
    print(f"Fetching search results from: {search_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(search_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all article entries
    articles = soup.find_all("article")
    print(f"Found {len(articles)} articles")

    artworks = []

    for article in articles:
        # Get the title
        title_elem = article.find("h2", class_="entry-title")
        if not title_elem:
            continue

        title = title_elem.get_text(strip=True)

        # Get the link to the artwork page
        link_elem = title_elem.find("a")
        if not link_elem or "href" not in link_elem.attrs:
            continue

        artwork_url = link_elem["href"]

        # Get the thumbnail image URL from the search results
        img_elem = article.find("img")
        if img_elem and "src" in img_elem.attrs:
            thumbnail_url = img_elem["src"]

            # Try to get the full-size image URL by modifying the thumbnail URL
            # Thumbnails often have size parameters that can be removed
            full_url = thumbnail_url

            # Remove common WordPress thumbnail size parameters
            full_url = re.sub(r"-\d+x\d+(\.\w+)$", r"\1", full_url)

            artworks.append(
                {
                    "title": title,
                    "page_url": artwork_url,
                    "thumbnail_url": thumbnail_url,
                    "image_url": full_url,
                }
            )

            print(f"  - {title}")

    return artworks


def get_artwork_details(artwork_url, headers):
    """Visit individual artwork page to get full details and image"""
    try:
        response = requests.get(artwork_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find the main image in the content
        content = soup.find("div", class_="entry-content")
        if content:
            img = content.find("img")
            if img and "src" in img.attrs:
                return img["src"]

        # Alternative: look for any large image
        images = soup.find_all("img")
        for img in images:
            src = img.get("src", "")
            # Skip small images and icons
            if "chagall" in src.lower() and not any(
                x in src for x in ["thumbnail", "icon", "-150x", "-300x"]
            ):
                return src

    except Exception as e:
        print(f"    Error getting details: {e}")

    return None


def identify_biblical_reference(title):
    """Try to identify which biblical book this artwork relates to"""
    title_lower = title.lower()

    # Map keywords to biblical books
    mappings = {
        "Genesis": [
            "creation",
            "adam",
            "eve",
            "noah",
            "ark",
            "abraham",
            "isaac",
            "jacob",
            "joseph",
            "sarah",
            "rebecca",
            "rachel",
            "leah",
        ],
        "Exodus": [
            "moses",
            "burning bush",
            "pharaoh",
            "tablets",
            "golden calf",
            "red sea",
            "commandments",
        ],
        "Joshua": ["jericho", "joshua"],
        "Judges": ["samson", "deborah", "gideon"],
        "I_Samuel": ["david", "goliath", "samuel", "saul"],
        "II_Kings": ["solomon", "elijah", "elisha"],
        "Isaiah": ["isaiah"],
        "Jeremiah": ["jeremiah"],
        "Ezekiel": ["ezekiel"],
        "Job": ["job"],
        "Psalms": ["psalm", "psalmist"],
        "Ruth": ["ruth", "naomi", "boaz"],
        "Esther": ["esther", "mordecai", "haman"],
        "Daniel": ["daniel", "lion"],
        "Jonah": ["jonah", "whale"],
        "Song_of_Songs": ["song of songs", "songs"],
    }

    for book, keywords in mappings.items():
        for keyword in keywords:
            if keyword in title_lower:
                return book

    # Check if book name is directly in the title
    books = [
        "Genesis",
        "Exodus",
        "Leviticus",
        "Numbers",
        "Deuteronomy",
        "Joshua",
        "Judges",
        "Samuel",
        "Kings",
        "Isaiah",
        "Jeremiah",
        "Ezekiel",
        "Hosea",
        "Joel",
        "Amos",
        "Obadiah",
        "Jonah",
        "Micah",
        "Nahum",
        "Habakkuk",
        "Zephaniah",
        "Haggai",
        "Zechariah",
        "Malachi",
        "Psalms",
        "Proverbs",
        "Job",
        "Ruth",
        "Esther",
        "Daniel",
    ]

    for book in books:
        if book.lower() in title_lower:
            return book

    return "General"


def main():
    """Main scraping function"""
    search_url = "https://www.artchive.com/?s=chagall+bible"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # Check if we have existing config to resume from
    config_file = Path("chagall_download_config.json")
    existing_config = []
    existing_urls = set()

    if config_file.exists():
        print(f"Found existing config file: {config_file}")
        with open(config_file, "r") as f:
            existing_config = json.load(f)
            existing_urls = {item["page_url"] for item in existing_config}
        print(f"  Loaded {len(existing_config)} existing entries")

    # Get search results
    artworks = get_search_results(search_url)

    print(f"\nFound {len(artworks)} Chagall Bible artworks")

    # Filter out already processed artworks
    new_artworks = [a for a in artworks if a["page_url"] not in existing_urls]
    if len(new_artworks) < len(artworks):
        print(f"Skipping {len(artworks) - len(new_artworks)} already processed artworks")

    print(f"\nProcessing {len(new_artworks)} new artworks...")
    print("(Config saves after each artwork)\n")

    # Start with existing config
    config = existing_config.copy()

    # Process each new artwork
    for i, artwork in enumerate(new_artworks, 1):
        print(f"{i}/{len(new_artworks)}: {artwork['title']}")

        # Try to get better image URL from the artwork page
        if artwork["page_url"]:
            time.sleep(1)  # Be polite to the server
            better_url = get_artwork_details(artwork["page_url"], headers)
            if better_url:
                artwork["image_url"] = better_url
                print(f"   Found full image: {better_url}")

        # Identify biblical reference
        biblical_book = identify_biblical_reference(artwork["title"])
        print(f"   Biblical book: {biblical_book}")

        # Create a safe filename
        safe_title = re.sub(r"[^a-z0-9]+", "_", artwork["title"].lower()).strip("_")
        filename = f"chagall_{safe_title[:50]}.jpg"

        # Add to config
        config.append(
            {
                "filename": filename,
                "url": artwork["image_url"],
                "title": artwork["title"],
                "book": biblical_book,
                "page_url": artwork["page_url"],
            }
        )

        # Save config after each item
        save_config(config)

        # Also update Python config
        save_python_config(config)

    print(f"\n✅ Processing complete!")
    print(f"Total artworks in config: {len(config)}")

    # Summary
    books = {}
    for item in config:
        book = item["book"]
        books[book] = books.get(book, 0) + 1

    print("\n📚 Artworks by Biblical Book:")
    for book, count in sorted(books.items()):
        print(f"   {book}: {count} artwork(s)")

    print(f"\nConfig files:")
    print(f"  • chagall_download_config.json")
    print(f"  • chagall_config.py")
    print(f"\nRun 'python3 download_chagall_images.py' to download the images")


if __name__ == "__main__":
    main()
