#!/usr/bin/env python3
"""
Generate a definitive mapping of which Chagall images belong to which chapters
by parsing biblical references from artwork titles in chagall_download_config.json.
"""

import json
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional


BOOK_NAME_MAP = {
    "Genesis": "Genesis",
    "Exodus": "Exodus",
    "Leviticus": "Leviticus",
    "Numbers": "Numbers",
    "Deuteronomy": "Deuteronomy",
    "Joshua": "Joshua",
    "Judges": "Judges",
    "I Samuel": "I_Samuel",
    "II Samuel": "II_Samuel",
    "I Kings": "I_Kings",
    "II Kings": "II_Kings",
    "Isaiah": "Isaiah",
    "Jeremiah": "Jeremiah",
    "Ezekiel": "Ezekiel",
    "Hosea": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obadiah",
    "Jonah": "Jonah",
    "Micah": "Micah",
    "Nahum": "Nahum",
    "Habakkuk": "Habakkuk",
    "Zephaniah": "Zephaniah",
    "Haggai": "Haggai",
    "Zechariah": "Zechariah",
    "Malachi": "Malachi",
    "Psalms": "Psalms",
    "Proverbs": "Proverbs",
    "Job": "Job",
    "Song of Songs": "Song_of_Songs",
    "Ruth": "Ruth",
    "Lamentations": "Lamentations",
    "Ecclesiastes": "Ecclesiastes",
    "Esther": "Esther",
    "Daniel": "Daniel",
    "Ezra": "Ezra",
    "Nehemiah": "Nehemiah",
    "I Chronicles": "I_Chronicles",
    "II Chronicles": "II_Chronicles",
}


def roman_to_int(roman: str) -> Optional[int]:
    if not roman:
        return None
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    roman = roman.upper()
    for ch in reversed(roman):
        if ch not in values:
            return None
        val = values[ch]
        if val < prev:
            total -= val
        else:
            total += val
        prev = val
    return total or None


def extract_refs_from_title(title: str) -> List[Tuple[str, int]]:
    """Return a list of (book_key, chapter_int) inferred from the title.
    We search for known book names and the first numeral (Roman or Arabic) following it.
    """
    refs: List[Tuple[str, int]] = []
    if not title:
        return refs

    hay = title

    # Sort book keys by length to avoid partial matches (e.g., 'I Kings' before 'Kings')
    for book_key in sorted(BOOK_NAME_MAP.keys(), key=len, reverse=True):
        # Case-insensitive search
        m = re.search(rf"\b{re.escape(book_key)}\b", hay, flags=re.IGNORECASE)
        if not m:
            continue
        end = m.end()
        # Search up to next closing paren or end
        tail = hay[end:]
        seg = re.split(r"[)]", tail, maxsplit=1)[0]
        # Find the first numeric token (Roman or Arabic)
        mnum = re.search(r"\b([IVXLCDM]+|\d{1,3})\b", seg, flags=re.IGNORECASE)
        if not mnum:
            continue
        tok = mnum.group(1)
        if tok.isdigit():
            chap = int(tok)
        else:
            chap = roman_to_int(tok)
        if not chap:
            continue
        refs.append((BOOK_NAME_MAP[book_key], chap))
    # Deduplicate while preserving order
    seen = set()
    unique: List[Tuple[str, int]] = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def generate_placement_map() -> Dict[str, List[str]]:
    """Build filename -> ["Book Chapter", ...] mapping from download config titles."""
    path = Path("chagall_download_config.json")
    if not path.exists():
        raise SystemExit("chagall_download_config.json not found")

    config = json.loads(path.read_text())
    placement: dict[str, list[str]] = {}
    for item in config:
        filename = item.get("filename")
        title = item.get("title", "")
        if not filename:
            continue
        refs = extract_refs_from_title(title)
        if not refs:
            # No explicit biblical reference found; skip
            continue
        for book_key, chap in refs[:1]:  # use the primary reference
            placement.setdefault(filename, []).append(f"{book_key} {chap}")
    return placement


if __name__ == "__main__":
    placement_map = generate_placement_map()
    with open("chagall_placement_map.json", "w") as f:
        json.dump(placement_map, f, indent=2)
    print(f"Generated placement map for {len(placement_map)} images")
    # Show a few examples
    for i, (fn, chapters) in enumerate(placement_map.items()):
        if i >= 5:
            break
        print(f"  {fn}: {', '.join(chapters)}")
