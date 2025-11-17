#!/usr/bin/env python3
"""
Normalize chagall_placement_map.json:
- For each book: if a chapter has multiple images, move all but the first to the
  highest-numbered unused chapters (i.e., to the end of the book).
- If any image is assigned to an out-of-range chapter, reassign to the highest
  free chapter within that book.

Writes changes in place and prints a concise summary.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple


BOOK_CHAPTER_COUNTS: Dict[str, int] = {
    # Torah
    "Genesis": 50,
    "Exodus": 40,
    "Leviticus": 27,
    "Numbers": 36,
    "Deuteronomy": 34,
    # Prophets
    "Joshua": 24,
    "Judges": 21,
    "I_Samuel": 31,
    "II_Samuel": 24,
    "I_Kings": 22,
    "II_Kings": 25,
    "Isaiah": 66,
    "Jeremiah": 52,
    "Ezekiel": 48,
    "Hosea": 14,
    "Joel": 4,
    "Amos": 9,
    "Obadiah": 1,
    "Jonah": 4,
    "Micah": 7,
    "Nahum": 3,
    "Habakkuk": 3,
    "Zephaniah": 3,
    "Haggai": 2,
    "Zechariah": 14,
    "Malachi": 3,
    # Writings
    "Psalms": 150,
    "Proverbs": 31,
    "Job": 42,
    "Song_of_Songs": 8,
    "Ruth": 4,
    "Lamentations": 5,
    "Ecclesiastes": 12,
    "Esther": 10,
    "Daniel": 12,
    "Ezra": 10,
    "Nehemiah": 13,
    "I_Chronicles": 29,
    "II_Chronicles": 36,
}


def parse_ref(ref: str) -> Tuple[str, int] | None:
    try:
        book, chap_str = ref.rsplit(" ", 1)
        return book, int(chap_str)
    except Exception:
        return None


def highest_free(book: str, used: set[int]) -> int | None:
    maxc = BOOK_CHAPTER_COUNTS.get(book)
    if not maxc:
        return None
    for cand in range(maxc, 0, -1):
        if cand not in used:
            return cand
    return None


def main() -> None:
    path = Path("chagall_placement_map.json")
    data: Dict[str, List[str]] = json.loads(path.read_text())

    # Build per-book usage and detect out-of-range
    per_book: Dict[str, Dict[int, List[str]]] = {}
    changes: List[str] = []

    for fn, refs in data.items():
        if not refs:
            continue
        parsed = parse_ref(refs[0])
        if not parsed:
            continue
        book, chap = parsed
        maxc = BOOK_CHAPTER_COUNTS.get(book)
        if not maxc:
            # Unknown books ignored
            continue
        if chap < 1 or chap > maxc:
            # Out of range -> move to highest free
            used = {
                c
                for r in data.values()
                if r and (pr := parse_ref(r[0])) and pr[0] == book and 1 <= pr[1] <= maxc
                for c in [pr[1]]
            }
            dest = highest_free(book, used)
            if dest is not None:
                data[fn] = [f"{book} {dest}"]
                changes.append(f"fix-range: {fn}: {book} {chap} -> {dest}")
                chap = dest
        per_book.setdefault(book, {}).setdefault(chap, []).append(fn)

    # Resolve duplicates by moving extras to end
    for book, chmap in per_book.items():
        maxc = BOOK_CHAPTER_COUNTS.get(book)
        if not maxc:
            continue
        used = {ch for ch, fns in chmap.items() if fns}
        # Walk chapters in ascending order; for any with >1, keep first and move rest
        for chap in sorted(chmap.keys()):
            fns = chmap[chap]
            if len(fns) <= 1:
                continue
            # keep first
            keep = fns[0]
            for fn in fns[1:]:
                dest = highest_free(book, used)
                if dest is None:
                    # No free spots; put at the end of the book
                    dest = maxc
                if dest == chap:
                    continue
                data[fn] = [f"{book} {dest}"]
                used.add(dest)
                changes.append(f"move-dup: {fn}: {book} {chap} -> {dest}")

    # Write back
    path.write_text(json.dumps(data, indent=2))

    # Summary
    if changes:
        print("Applied changes:")
        for line in changes[:50]:
            print("  ", line)
        if len(changes) > 50:
            print(f"  ... and {len(changes) - 50} more")
    else:
        print("No changes needed.")


if __name__ == "__main__":
    main()
