#!/usr/bin/env python3
"""
Interactive assistant to assign Book/Chapter locations to Chagall images.

Features
- Loads API key + model from .env (OpenRouter).
- Suggests likely locations from filename/title via:
  1) LLM (if available), else
  2) Offline heuristic (filename parsing of book + roman numerals).
- Lets you accept a suggestion, enter manually, skip, or quit.
- Writes results to chagall_placement_map.json (filename -> ["Book Chapter"]).

Usage
  python3 suggest_placements.py                # interactive, all items
  python3 suggest_placements.py --only-unmapped
  python3 suggest_placements.py --no-ai        # force offline heuristic
  python3 suggest_placements.py --start 20 --limit 30

Environment (.env)
  OPENROUTER_API_KEY=...
  OPENROUTER_MODEL=anthropic/claude-3.5-sonnet   # or any OpenRouter model
"""

from __future__ import annotations
import json
import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv


BOOKS: List[str] = [
    # Torah
    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    # Prophets
    "Joshua",
    "Judges",
    "I_Samuel",
    "II_Samuel",
    "I_Kings",
    "II_Kings",
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
    # Writings
    "Psalms",
    "Proverbs",
    "Job",
    "Song_of_Songs",
    "Ruth",
    "Lamentations",
    "Ecclesiastes",
    "Esther",
    "Daniel",
    "Ezra",
    "Nehemiah",
    "I_Chronicles",
    "II_Chronicles",
]

# Canonical chapter counts aligned with the generator
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


NAME_ALIASES: Dict[str, str] = {
    # Normalize human-ish or filename-ish forms to our canonical keys
    "song of songs": "Song_of_Songs",
    "i samuel": "I_Samuel",
    "ii samuel": "II_Samuel",
    "i kings": "I_Kings",
    "ii kings": "II_Kings",
    "i chronicles": "I_Chronicles",
    "ii chronicles": "II_Chronicles",
}


ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s: str) -> Optional[int]:
    if not s:
        return None
    s = s.upper()
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN_VALUES.get(ch)
        if not v:
            return None
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total or None


def normalize_book_token(tok: str) -> Optional[str]:
    t = tok.strip().replace("_", " ").lower()
    if t in NAME_ALIASES:
        return NAME_ALIASES[t]
    # Exact canonical match
    for b in BOOKS:
        if t == b.lower().replace("_", " "):
            return b
    # Partial fallback (e.g., "samuel" when filename lacks I/II)
    if t == "samuel":
        return "I_Samuel"
    if t == "kings":
        return "I_Kings"
    if t == "chronicles":
        return "I_Chronicles"
    return None


def heuristic_suggest(filename: str, title: str) -> List[Tuple[str, int, float, str]]:
    """Return list of (book, chapter, confidence, rationale) suggestions."""
    hay = f"{filename} {title}".lower()
    suggestions: List[Tuple[str, int, float, str]] = []

    # Find explicit book tokens
    tokens = re.split(r"[^a-z0-9_]+", hay)
    for i, tok in enumerate(tokens):
        book = normalize_book_token(tok)
        if not book:
            continue
        # Look ahead for a roman or arabic number near
        window = " ".join(tokens[i + 1 : i + 6])
        m = re.search(r"\b(\d{1,3}|[ivxlcdm]{1,6})\b", window)
        chap: Optional[int] = None
        if m:
            g = m.group(1)
            chap = int(g) if g.isdigit() else roman_to_int(g)
        if not chap:
            # common fallbacks based on known subjects
            if "goliath" in hay:
                chap = 17 if book in {"I_Samuel", "II_Samuel"} else None
            elif "ladder" in hay or "jacob" in hay and "ladder" in hay:
                chap = 28 if book == "Genesis" else None
            elif "isaac" in hay and "sacrifice" in hay:
                chap = 22 if book == "Genesis" else None
        # If still no chapter but book is clear, propose chapter 1 as a low-confidence default
        if not chap:
            chap = 1
            suggestions.append((book, chap, 0.30, "Book detected; defaulting to chapter 1"))
            continue
        if chap:
            suggestions.append((book, chap, 0.55, f"Heuristic match around '{tok}'"))

    # De-duplicate keep highest confidence
    dedup: Dict[Tuple[str, int], Tuple[str, int, float, str]] = {}
    for b, c, conf, why in suggestions:
        key = (b, c)
        if key not in dedup or conf > dedup[key][2]:
            dedup[key] = (b, c, conf, why)

    out = list(dedup.values())
    out.sort(key=lambda x: (-x[2], BOOKS.index(x[0]) if x[0] in BOOKS else 9999, x[1]))
    return out[:3]


def openrouter_suggest(
    filename: str, title: str, model: str, api_key: str
) -> List[Tuple[str, int, float, str]]:
    url = "https://openrouter.ai/api/v1/chat/completions"
    system_msg = (
        "You are a precise librarian. Infer the subject's canonical Tanakh location "
        "(Book and Chapter) from the given image filename and title. Use only the Tanakh books in the provided list."
    )
    valid_books = ", ".join(BOOKS)
    user_prompt = f"""
Filename: {filename}
Title: {title}

Output strict JSON with key "suggestions" as an array of up to 3 items, each:
  {{"book": <one of [{valid_books}]>, "chapter": <int>, "confidence": <0.0-1.0>, "rationale": <short string>}}
Prefer parsing any book name and roman numerals in the name/title. If unsure, omit.
"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        obj = json.loads(content)
        raw = obj.get("suggestions", [])
        out: List[Tuple[str, int, float, str]] = []
        for s in raw:
            book = s.get("book")
            chap = s.get("chapter")
            conf = float(s.get("confidence", 0))
            why = s.get("rationale", "")
            if isinstance(book, str) and isinstance(chap, int) and 1 <= chap <= 150:
                out.append((book, chap, conf, why))
        return out[:3]
    except Exception as e:
        print(f"[openrouter] error: {e}")
        return []


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def allocate_next_free_chapter(
    book: str, desired_chap: int, placement: Dict[str, List[str]]
) -> int:
    """If desired chapter is taken, move this image to the end of the book.
    Specifically, assign the highest-numbered unused chapter. If none, keep desired.
    """
    max_chaps = BOOK_CHAPTER_COUNTS.get(book)
    if not max_chaps:
        return desired_chap

    # Build used set for book
    used = set()
    for refs in placement.values():
        if not refs:
            continue
        try:
            b, c_str = refs[0].rsplit(" ", 1)
            if b == book:
                used.add(int(c_str))
        except Exception:
            continue

    if desired_chap not in used:
        return desired_chap

    # Find the highest-numbered free chapter (toward the end)
    for cand in range(max_chaps, 0, -1):
        if cand not in used:
            return cand
    # Fallback - return desired if all chapters are used
    return desired_chap


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0, help="Start index in config list")
    parser.add_argument("--limit", type=int, default=None, help="Max items to process")
    parser.add_argument(
        "--only-unmapped", action="store_true", help="Skip images already in placement map"
    )
    parser.add_argument(
        "--no-ai", action="store_true", help="Disable OpenRouter and use heuristics only"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.65,
        help="Confidence threshold for accepting suggestions",
    )
    parser.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        help="Stop immediately when a good decision can't be made",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Allow skipping uncertain items without stopping",
    )
    parser.set_defaults(strict=True)
    args = parser.parse_args()

    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    api_key = os.getenv("OPENROUTER_API_KEY")
    # Prefer explicit OPENROUTER_MODEL, else the user's fast model alias
    model = (
        os.getenv("OPENROUTER_MODEL")
        or os.getenv("LLM_MODEL_FAST")
        or "anthropic/claude-3.5-sonnet"
    )

    use_ai = provider == "openrouter" and api_key and not args.no_ai
    if use_ai:
        print(f"Using OpenRouter model: {model}")
    else:
        print("OpenRouter disabled/missing or --no-ai; using offline heuristics.")

    cfg_path = Path("chagall_download_config.json")
    items = load_json(cfg_path, [])
    map_path = Path("chagall_placement_map.json")
    placement: Dict[str, List[str]] = load_json(map_path, {})

    items = [it for it in items if it.get("filename")]
    start = max(0, args.start)
    stop = len(items) if args.limit is None else min(len(items), start + args.limit)

    duplicates_moved: List[Tuple[str, str, int, int]] = []  # (filename, book, wanted, assigned)

    for idx, it in enumerate(items[start:stop], start):
        fn = it.get("filename")
        title = it.get("title", "")
        if args.only_unmapped and fn in placement:
            continue

        print("-" * 60)
        print(f"[{idx}] {fn}")
        print(f"     {title}")
        existing = placement.get(fn)
        if existing:
            print(f"  Existing: {existing}")

        # Handle cover-like items (do not force a mapping)
        low = f"{fn} {title}".lower()
        if "cover" in low:
            print("  Detected cover-like image; skipping chapter placement.")
            continue

        # Get suggestions
        suggestions: List[Tuple[str, int, float, str]] = []
        if use_ai:
            suggestions = openrouter_suggest(fn, title, model, api_key)
        if not suggestions:
            suggestions = heuristic_suggest(fn, title)

        # Prefer highest-confidence first
        suggestions.sort(key=lambda s: s[2], reverse=True)
        best_conf = max((s[2] for s in suggestions), default=0.0)

        # Auto-accept if highly confident (>= 0.8)
        if suggestions and suggestions[0][2] >= 0.8:
            b, c, conf, _ = suggestions[0]
            c2 = allocate_next_free_chapter(b, c, placement)
            placement[fn] = [f"{b} {c2}"]
            save_json(map_path, placement)
            if c2 != c:
                duplicates_moved.append((fn, b, c, c2))
                note = " (moved to end)"
            else:
                note = ""
            print(f"  Auto-accepted: {b} {c2}{note} (p≈{conf:.2f})")
            continue
        if suggestions:
            for i, (b, c, conf, why) in enumerate(suggestions, 1):
                flag = "*" if conf >= args.threshold else " "
                print(f" {flag} {i}. {b} {c}  (p≈{conf:.2f})  - {why}")
        else:
            print("  No suggestions.")

        # Strict mode: if we cannot make a good decision, require explicit choice or stop
        if not suggestions or best_conf < args.threshold:
            print(f"  Uncertain decision (max≈{best_conf:.2f} < threshold {args.threshold:.2f}).")
            # If suggestions exist, allow selection even if below threshold
            while True:
                prompt = ("  Pick [1..{n}], m=manual, or press Enter to stop and save > ").format(
                    n=len(suggestions)
                )
                choice = input(prompt).strip().lower()
                if choice == "":
                    print("  Stopping due to low confidence. Progress saved.")
                    save_json(map_path, placement)
                    sys.exit(2 if args.strict else 0)
                if choice == "m":
                    manual = input("  Enter Book Chapter (e.g., Genesis 22): ").strip()
                    m = re.match(r"^\s*([A-Za-z_ ]+)\s+(\d{1,3})\s*$", manual)
                    if not m:
                        print("  Invalid format, try again.")
                        continue
                    book_in = m.group(1).strip()
                    chap = int(m.group(2))
                    norm = normalize_book_token(book_in) or book_in.replace(" ", "_")
                    chap2 = allocate_next_free_chapter(norm, chap, placement)
                    placement[fn] = [f"{norm} {chap2}"]
                    save_json(map_path, placement)
                    if chap2 != chap:
                        duplicates_moved.append((fn, norm, chap, chap2))
                        note = " (moved to end)"
                    else:
                        note = ""
                    print(f"  Saved: {placement[fn]}{note}")
                    break
                if choice.isdigit():
                    k = int(choice)
                    if 1 <= k <= len(suggestions):
                        b, c, *_ = suggestions[k - 1]
                        c2 = allocate_next_free_chapter(b, c, placement)
                        placement[fn] = [f"{b} {c2}"]
                        save_json(map_path, placement)
                        if c2 != c:
                            duplicates_moved.append((fn, b, c, c2))
                            note = " (moved to end)"
                        else:
                            note = ""
                        print(f"  Saved: {placement[fn]}{note}")
                        break
                    else:
                        print("  Out of range.")
                else:
                    print("  Unknown option.")
            # after resolving low-confidence via manual or pick, proceed to next item
            continue

        # We have a confident suggestion; prompt user decisively
        while True:
            choice = (
                input("Pick [1..{n}], m=manual, q=quit > ".format(n=len(suggestions)))
                .strip()
                .lower()
            )
            if choice == "q":
                print("Quitting.")
                save_json(map_path, placement)
                return
            if choice == "m":
                manual = input("Enter Book Chapter (e.g., Genesis 22): ").strip()
                m = re.match(r"^\s*([A-Za-z_ ]+)\s+(\d{1,3})\s*$", manual)
                if not m:
                    print("  Invalid format, try again.")
                    continue
                book_in = m.group(1).strip()
                chap = int(m.group(2))
                norm = normalize_book_token(book_in) or book_in.replace(" ", "_")
                chap2 = allocate_next_free_chapter(norm, chap, placement)
                placement[fn] = [f"{norm} {chap2}"]
                save_json(map_path, placement)
                if chap2 != chap:
                    duplicates_moved.append((fn, norm, chap, chap2))
                    note = " (moved to end)"
                else:
                    note = ""
                print(f"  Saved: {placement[fn]}{note}")
                break
            if choice.isdigit():
                k = int(choice)
                if 1 <= k <= len(suggestions):
                    b, c, *_ = suggestions[k - 1]
                    c2 = allocate_next_free_chapter(b, c, placement)
                    placement[fn] = [f"{b} {c2}"]
                    save_json(map_path, placement)
                    if c2 != c:
                        duplicates_moved.append((fn, b, c, c2))
                        note = " (moved to end)"
                    else:
                        note = ""
                    print(f"  Saved: {placement[fn]}{note}")
                    break
                else:
                    print("  Out of range.")
            else:
                print("  Unknown option.")

    save_json(map_path, placement)
    if duplicates_moved:
        print("\nMoved duplicates to end:")
        for fn, b, want, got in duplicates_moved[:20]:
            print(f"  {fn}: {b} {want} -> {got}")
        if len(duplicates_moved) > 20:
            print(f"  ... and {len(duplicates_moved) - 20} more")
    print("\nAll done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
