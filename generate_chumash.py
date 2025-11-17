#!/usr/bin/env python3
"""
Chumash-style HTML generator

Creates a print-friendly two-column layout with Hebrew on the right and
English on the left, verse-aligned rows, and optional manual page breaks.

Output: writes a self-contained HTML file and companion CSS into ./chumash_out/
"""

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape


BOOKS_TORAH = [
    ("Genesis", "בראשית", 50),
    ("Exodus", "שמות", 40),
    ("Leviticus", "ויקרא", 27),
    ("Numbers", "במדבר", 36),
    ("Deuteronomy", "דברים", 34),
]


@dataclass
class Verse:
    n: int
    he: str
    en: str
    page_break_before: bool = False


def to_hebrew_numeral(num: int) -> str:
    ones = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
    tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
    hundreds = ["", "ק", "ר", "ש", "ת"]
    if num >= 1000:
        return str(num)
    result = ""
    if num >= 100:
        result += hundreds[num // 100]
        num %= 100
    if num >= 10:
        result += tens[num // 10]
        num %= 10
    if num > 0:
        result += ones[num]
    if len(result) > 1:
        result = result[:-1] + "״" + result[-1:]
    elif len(result) == 1:
        result = result + "׳"
    return result


def fetch_chapter(book: str, chapter: int) -> Dict:
    url = f"https://www.sefaria.org/api/texts/{book}.{chapter}"
    params = {
        "ven": "The_Koren_Jerusalem_Bible",
        "vhe": "Tanach_with_Nikkud",
        "commentary": 0,
        "context": 1,
        "pad": 0,
        "wrapLinks": 0,
        "wrapNamedEntities": 0,
        "stripmarkers": 1,
    }
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
        except Exception:
            if attempt < 2:
                time.sleep(2)
    return {}


def clean_list(value) -> List[str]:
    import re as _re

    if isinstance(value, str):
        value = [value]
    out: List[str] = []
    for v in value or []:
        v = _re.sub(r"<[^>]+>", "", v or "").strip()
        if v:
            out.append(v)
    return out


def load_breaks(path: Optional[Path]) -> Dict[str, Dict[int, List[int]]]:
    """Return mapping: book -> chapter -> list of verse numbers to break before."""
    if not path or not path.exists():
        return {}
    with open(path, "r") as f:
        data = json.load(f)
    # Normalize keys to str->int mapping
    norm: Dict[str, Dict[int, List[int]]] = {}
    for book, chapters in data.items():
        norm[book] = {int(ch): [int(v) for v in verses] for ch, verses in chapters.items()}
    return norm


def build_context_columns(books: List[tuple], limit_chapters: Optional[int], breaks: Dict) -> Dict:
    env = Environment(
        loader=FileSystemLoader("templates"), autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("chumash.html")

    cooked_books = []
    for en_name, he_name, ch_count in books:
        max_ch = limit_chapters or ch_count
        chapters = []
        for ch in range(1, max_ch + 1):
            data = fetch_chapter(en_name, ch)
            if not data:
                continue
            he_list = clean_list(data.get("he"))
            en_list = clean_list(data.get("text"))

            max_len = max(len(he_list), len(en_list))
            he_list += [""] * (max_len - len(he_list))
            en_list += [""] * (max_len - len(en_list))

            forced = set(breaks.get(en_name, {}).get(ch, []))
            verses: List[Verse] = []
            for i in range(max_len):
                verses.append(
                    Verse(
                        n=i + 1,
                        he=he_list[i],
                        en=en_list[i],
                        page_break_before=(i + 1) in forced,
                    )
                )

            chapters.append({"number": ch, "hebrew_num": to_hebrew_numeral(ch), "verses": verses})

        cooked_books.append({"english": en_name, "hebrew": he_name, "chapters": chapters})

    return {"books": cooked_books, "template": template}


def split_verses(max_len: int, break_points: List[int], default_chunk: int) -> List[range]:
    """Return list of index ranges [start..end] for a chapter.
    break_points are 1-based verse starts that open a new spread.
    default_chunk applies when no break points are provided.
    """
    if not break_points:
        break_points = [i for i in range(1, max_len + 1, max(1, default_chunk))]
    # Ensure 1 is included and sorted unique
    s = sorted(set([1] + [b for b in break_points if 1 <= b <= max_len]))
    ranges: List[range] = []
    for i, start in enumerate(s):
        end = (s[i + 1] - 1) if i + 1 < len(s) else max_len
        ranges.append(range(start, end + 1))
    return ranges


def build_context_facing(
    books: List[tuple],
    limit_chapters: Optional[int],
    breaks: Dict,
    default_chunk: int,
    start_blank: bool,
) -> Dict:
    env = Environment(
        loader=FileSystemLoader("templates"), autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("chumash_facing.html")

    spreads = []
    for en_name, he_name, ch_count in books:
        max_ch = limit_chapters or ch_count
        for ch in range(1, max_ch + 1):
            data = fetch_chapter(en_name, ch)
            if not data:
                continue
            he_list = clean_list(data.get("he"))
            en_list = clean_list(data.get("text"))
            max_len = max(len(he_list), len(en_list))
            he_list += [""] * (max_len - len(he_list))
            en_list += [""] * (max_len - len(en_list))

            chapter_breaks = breaks.get(en_name, {}).get(ch, [])
            chunks = split_verses(max_len, chapter_breaks, default_chunk)

            for rng in chunks:
                verses = [
                    {
                        "n": i,
                        "he": he_list[i - 1],
                        "en": en_list[i - 1],
                    }
                    for i in rng
                ]
                spreads.append(
                    {
                        "book_en": en_name,
                        "book_he": he_name,
                        "ch_num": ch,
                        "ch_num_he": to_hebrew_numeral(ch),
                        "verses": verses,
                    }
                )

    return {"spreads": spreads, "template": template, "start_blank": start_blank}


def write_output(ctx: Dict, outdir: Path, filename: str = "chumash.html") -> Path:
    outdir.mkdir(parents=True, exist_ok=True)

    # Copy CSS beside HTML
    # Decide stylesheet by template name
    if ctx.get("template") and getattr(ctx["template"], "name", "").endswith("chumash_facing.html"):
        css_name = "chumash_facing.css"
    else:
        css_name = "chumash.css"

    css_src = Path("templates") / css_name
    css_dst = outdir / "chumash.css"
    css_dst.write_text(css_src.read_text(encoding="utf-8"), encoding="utf-8")

    # Copy Hebrew font into fonts/
    font_src = Path("NotoSerifHebrew-Regular.ttf")
    fonts_dir = outdir / "fonts"
    if font_src.exists():
        fonts_dir.mkdir(parents=True, exist_ok=True)
        (fonts_dir / font_src.name).write_bytes(font_src.read_bytes())

    html_path = outdir / filename
    if getattr(ctx["template"], "name", "").endswith("chumash_facing.html"):
        html = ctx["template"].render(
            spreads=ctx["spreads"], start_blank=ctx.get("start_blank", False)
        )
    else:
        html = ctx["template"].render(books=ctx["books"])
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main():
    parser = argparse.ArgumentParser(description="Generate chumash-style HTML")
    parser.add_argument(
        "--books",
        choices=["torah"],
        default="torah",
        help="Which set of books to include (more options later)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of chapters per book (0 = all)",
    )
    parser.add_argument(
        "--mode",
        choices=["facing", "columns"],
        default="facing",
        help="Layout mode: facing pages (default) or two columns",
    )
    parser.add_argument(
        "--breaks",
        type=Path,
        default=Path("chumash_breaks.json"),
        help="JSON with manual page breaks: { 'Genesis': { '1': [1, 15] } }",
    )
    parser.add_argument(
        "--verses-per-page",
        type=int,
        default=14,
        help="Default verse chunk size when no manual breaks",
    )
    parser.add_argument(
        "--start-blank",
        action="store_true",
        help="Insert a leading blank page so Hebrew appears on right (recto)",
    )
    parser.add_argument(
        "-o", "--outdir", type=Path, default=Path("chumash_out"), help="Output folder"
    )

    args = parser.parse_args()
    books = BOOKS_TORAH
    limit = args.limit if args.limit and args.limit > 0 else None
    breaks = load_breaks(args.breaks)

    if args.mode == "facing":
        ctx = build_context_facing(books, limit, breaks, args.verses_per_page, args.start_blank)
        path = write_output(ctx, args.outdir, filename="chumash_facing.html")
    else:
        ctx = build_context_columns(books, limit, breaks)
        path = write_output(ctx, args.outdir, filename="chumash.html")
    print(f"✅ Wrote {path}")
    print(
        "Print to PDF with:\n - Background graphics ON\n - Paper size 6x9 inches (or A5)\n - Margins: default or 0.7in"
    )


if __name__ == "__main__":
    main()
