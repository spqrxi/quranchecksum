#!/usr/bin/env python3
"""
build_index.py — regenerate manifest/translations/index.json by scanning
manifest/translations/*.manifest.json.

Filename conventions:
    <translation_id>.<distributor>.manifest.json               current alias
    <translation_id>.<distributor>.<date>.manifest.json         dated snapshot

Usage:
    python3 build_index.py [--dir manifest/translations] [--out manifest/translations/index.json]
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone


def parse_filename(name: str):
    """Return (translation_id, distributor, date_or_None) or None if the
    filename doesn't match the expected pattern."""
    if not name.endswith(".manifest.json"):
        return None
    stem = name[: -len(".manifest.json")]
    parts = stem.split(".")
    if len(parts) < 2:
        return None
    # date part, if present, is the last component and looks like YYYY-MM-DD
    date = None
    if len(parts) >= 3 and len(parts[-1]) == 10 and parts[-1].count("-") == 2:
        date = parts[-1]
        parts = parts[:-1]
    distributor = parts[-1]
    translation_id = ".".join(parts[:-1])
    if not translation_id or not distributor:
        return None
    return translation_id, distributor, date


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="manifest/translations")
    ap.add_argument("--out", default=None,
                     help="defaults to <dir>/index.json")
    args = ap.parse_args()

    base = Path(args.dir)
    out_path = Path(args.out) if args.out else base / "index.json"

    groups = {}  # (translation_id, distributor) -> {"current": file, "history": [...]}

    for path in sorted(base.glob("*.manifest.json")):
        if path.name == "index.json":
            continue
        parsed = parse_filename(path.name)
        if parsed is None:
            print(f"WARNING: skipping unrecognized filename {path.name}", file=sys.stderr)
            continue
        translation_id, distributor, date = parsed

        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)

        meta = manifest.get("meta", {})
        root_hash = manifest.get("translation_root")
        key = (translation_id, distributor)
        entry = groups.setdefault(key, {
            "translation_id": translation_id,
            "translator": meta.get("translator"),
            "language": meta.get("language"),
            "distributor": distributor,
            "current": None,
            "current_version": None,
            "translation_root": None,
            "verse_count": meta.get("verse_count"),
            "verse_scheme": meta.get("verse_scheme"),
            "history": [],
        })

        if date is None:
            entry["current"] = path.name
            entry["current_version"] = meta.get("retrieved_at") or meta.get("edition_version")
            entry["translation_root"] = root_hash
            entry["verse_count"] = meta.get("verse_count")
            entry["verse_scheme"] = meta.get("verse_scheme")
        else:
            entry["history"].append({
                "version": date,
                "file": path.name,
                "translation_root": root_hash,
            })

    for entry in groups.values():
        entry["history"].sort(key=lambda h: h["version"])
        if entry["current"] is None and entry["history"]:
            # no undated alias present -- fall back to the latest dated snapshot
            latest = entry["history"][-1]
            entry["current"] = latest["file"]
            entry["current_version"] = latest["version"]
            entry["translation_root"] = latest["translation_root"]

    index = {
        "meta": {
            "format_version": "1.0",
            "kind": "translation-index",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "description": "Catalog of translation integrity manifests. "
                "Hashes only; no translation text is stored in this "
                "repository. Translations are copyrighted by their publishers.",
        },
        "translations": list(groups.values()),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2, sort_keys=False)

    print(f"Wrote {out_path} ({len(groups)} translation/distributor entries)")


if __name__ == "__main__":
    main()
