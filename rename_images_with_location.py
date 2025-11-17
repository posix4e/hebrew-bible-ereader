#!/usr/bin/env python3
"""
Rename Chagall images to include their book/chapter location and update references.

Scheme: <Book>_<Chapter>__<original_filename>
  - Example: Genesis_22__chagall_abraham_is_going_to_sacrifice_his_son_according_to.jpg

Updates:
  - images/<file>
  - chagall_download_config.json (filename fields)
  - chagall_placement_map.json (keys)

Run with --apply to perform changes; otherwise prints a dry-run plan.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil


def load_json(path: Path):
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Perform file renames and update JSONs")
    args = ap.parse_args()

    images_dir = Path("images")
    cfg_path = Path("chagall_download_config.json")
    map_path = Path("chagall_placement_map.json")

    config = load_json(cfg_path)
    placement = load_json(map_path)

    # Build a quick lookup: filename -> primary ref "Book Chapter"
    primary_ref: dict[str, str] = {}
    for fn, refs in placement.items():
        if not refs:
            continue
        primary_ref[fn] = refs[0]

    plan: list[tuple[Path, Path]] = []
    name_map: dict[str, str] = {}  # old -> new

    for item in config:
        fn = item.get("filename")
        if not fn:
            continue
        ref = primary_ref.get(fn)
        if not ref:
            continue
        try:
            book, chap = ref.rsplit(" ", 1)
        except Exception:
            continue
        # Compose new filename
        new_fn = f"{book}_{chap}__{fn}"
        src = images_dir / fn
        dst = images_dir / new_fn
        if not src.exists():
            continue
        if src == dst:
            continue
        plan.append((src, dst))
        name_map[fn] = new_fn

    # Print plan
    print(f"Found {len(plan)} files to rename")
    for src, dst in plan[:10]:
        print(f"  {src.name} -> {dst.name}")
    if len(plan) > 10:
        print(f"  ... and {len(plan)-10} more")

    if not args.apply:
        print("\nDry run. Use --apply to perform changes.")
        return

    # Perform renames
    for src, dst in plan:
        if dst.exists():
            # Avoid overwriting; keep original
            print(f"SKIP (exists): {dst.name}")
            continue
        shutil.move(str(src), str(dst))

    # Update config filenames
    changed = 0
    for item in config:
        fn = item.get("filename")
        if fn in name_map:
            item["filename"] = name_map[fn]
            changed += 1
    cfg_path.write_text(json.dumps(config, indent=2))
    print(f"Updated chagall_download_config.json entries: {changed}")

    # Update placement map keys
    new_placement = {}
    for fn, refs in placement.items():
        new_fn = name_map.get(fn, fn)
        new_placement[new_fn] = refs
    map_path.write_text(json.dumps(new_placement, indent=2))
    print("Updated chagall_placement_map.json keys")


if __name__ == "__main__":
    main()
