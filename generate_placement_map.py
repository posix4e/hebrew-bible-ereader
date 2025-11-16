#!/usr/bin/env python3
"""
Generate a mapping of which Chagall images appear in which chapters of the EPUB
"""

import json
from generate_tanakh import TanakhGenerator


def generate_placement_map():
    """Generate mapping of Chagall images to their chapter placements"""

    # Use the actual generator to get accurate placement
    gen = TanakhGenerator()
    placement_map = {}

    # Simulate the placement logic
    for book_info in gen.books:
        book_name, hebrew_name, transliteration, chapter_count = book_info

        for chapter_num in range(1, chapter_count + 1):
            # Check if original artwork exists
            has_original = (book_name, chapter_num) in gen.image_map

            # If no original artwork, check if Chagall image would be added
            if not has_original and gen.all_chagall_images:
                should_add_image = False

                # Always add image to first chapter of each book
                if chapter_num == 1:
                    should_add_image = True
                # Add image every 6 chapters
                elif chapter_num % 6 == 0:
                    should_add_image = True
                # Special chapters that should have images
                elif (book_name, chapter_num) in [
                    ("Genesis", 22),
                    ("Genesis", 28),
                    ("Exodus", 14),
                    ("Exodus", 20),
                    ("I_Samuel", 17),
                    ("I_Kings", 3),
                    ("Psalms", 23),
                    ("Job", 1),
                ]:
                    should_add_image = True

                if should_add_image:
                    # Get the image that would be used
                    image_idx = gen.chagall_index % len(gen.all_chagall_images)
                    image = gen.all_chagall_images[image_idx]
                    gen.chagall_index += 1

                    if image["filename"] not in placement_map:
                        placement_map[image["filename"]] = []
                    placement_map[image["filename"]].append(f"{book_name} {chapter_num}")

    return placement_map


if __name__ == "__main__":
    placement_map = generate_placement_map()

    # Save the placement map
    with open("chagall_placement_map.json", "w") as f:
        json.dump(placement_map, f, indent=2)

    print(f"Generated placement map for {len(placement_map)} images")

    # Show some examples
    print("\nExample placements:")
    for filename, chapters in list(placement_map.items())[:5]:
        print(f"  {filename}: {', '.join(chapters)}")
