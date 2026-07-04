#!/usr/bin/env python3
"""
generate_manifest.py — build a verse-level SHA-256 integrity manifest
for the Quran, from a Tanzil-format Uthmani text file.

Input format (Tanzil simple text export, pipe-delimited):
    surah|ayah|verse_text
    1|1|بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ
    ...

Output: manifest/quran-uthmani.manifest.json
    {
      "meta": { ... },
      "verses": { "1:1": "sha256hex", "1:2": "sha256hex", ... },
      "surahs": { "1": "sha256hex", ... },     # rollup of verse hashes
      "quran":  "sha256hex"                     # rollup of all verse hashes
    }

Usage:
    python3 generate_manifest.py <source.txt> [--out manifest.json]
"""
import sys
import json
import hashlib
import unicodedata
import argparse
from datetime import datetime, timezone


def normalize(text: str) -> str:
    """Canonical form used for hashing. NFC is the documented choice —
    see docs/SPEC.md for why this matters and what it does NOT catch."""
    return unicodedata.normalize('NFC', text.strip())


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_source(path: str):
    """Parse Tanzil-format pipe-delimited text. Returns list of (surah, ayah, text)."""
    verses = []
    with open(path, encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.rstrip('\n')
            if not line or line.count('|') < 2:
                continue
            parts = line.split('|', 2)
            try:
                surah, ayah = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            verses.append((surah, ayah, parts[2]))
    return verses


def build_manifest(verses, meta_overrides: dict, kind: str = "text"):
    """Build a manifest dict for either the Arabic text (kind='text') or a
    translation (kind='translation'). Hashing/rollup logic is identical for
    both -- only the meta block and the root-hash key name differ."""
    verse_hashes = {}
    surah_verse_hashes = {}
    empty_verses = []

    for surah, ayah, text in verses:
        norm = normalize(text)
        if not norm:
            empty_verses.append(f"{surah}:{ayah}")
        h = sha256_hex(norm)
        key = f"{surah}:{ayah}"
        verse_hashes[key] = h
        surah_verse_hashes.setdefault(surah, []).append(h)

    if empty_verses:
        print(f"WARNING: {len(empty_verses)} verse(s) normalized to empty "
              f"text: {', '.join(empty_verses[:10])}"
              f"{' ...' if len(empty_verses) > 10 else ''}", file=sys.stderr)

    # Surah-level rollup: hash of concatenated verse hashes, in ayah order
    surah_hashes = {}
    for surah, hashes in surah_verse_hashes.items():
        surah_hashes[str(surah)] = sha256_hex(''.join(hashes))

    # Whole-manifest rollup: hash of concatenated surah hashes, in surah order
    root_hash = sha256_hex(''.join(
        surah_hashes[str(s)] for s in sorted(surah_hashes, key=int)
    ))

    meta = {
        "format_version": "1.0",
        "kind": kind,
        "normalization": "NFC",
        "hash_algorithm": "sha256",
        "verse_count": len(verse_hashes),
        "surah_count": len(surah_hashes),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "granularity": "verse",
        "rollup_method": "sha256 of concatenated child hashes, in canonical order",
    }
    meta.update(meta_overrides)

    root_key = "quran" if kind == "text" else "translation_root"

    manifest = {
        "meta": meta,
        "verses": verse_hashes,
        "surahs": surah_hashes,
        root_key: root_hash,
    }
    return manifest


TRANSLATION_META_FIELDS = [
    "translation_id", "translator", "language", "language_name", "direction",
    "distributor", "distributor_url", "distributor_edition_id",
    "edition_version", "edition_note", "retrieved_at", "based_on_arabic",
    "verse_scheme", "supersedes", "canonicity", "canonicity_note",
    "copyright_note",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="path to Tanzil-format pipe-delimited text file")
    ap.add_argument("--out", default="manifest/quran-uthmani.manifest.json")
    ap.add_argument("--source-name", default="tanzil-uthmani",
                     help="value of meta.source for kind=text manifests")
    ap.add_argument("--kind", choices=["text", "translation"], default="text")
    ap.add_argument("--meta-file",
                     help="JSON file with translation meta fields "
                          "(overridden by any matching --translation-* flags)")
    ap.add_argument("--expected-verses", type=int, default=6236)
    ap.add_argument("--allow-verse-count-mismatch", action="store_true",
                     help="for kind=translation: don't fail on verse count "
                          "!= --expected-verses (e.g. differing versification)")
    for field in TRANSLATION_META_FIELDS:
        ap.add_argument(f"--{field.replace('_', '-')}", dest=field, default=None)
    args = ap.parse_args()

    verses = load_source(args.source)

    if args.kind == "text":
        if len(verses) != args.expected_verses:
            print(f"WARNING: expected {args.expected_verses} verses, got "
                  f"{len(verses)}. Check source file format before "
                  f"publishing this manifest.", file=sys.stderr)
        meta_overrides = {"source": args.source_name}
    else:
        if len(verses) != args.expected_verses and not args.allow_verse_count_mismatch:
            print(f"ERROR: expected {args.expected_verses} verses, got "
                  f"{len(verses)}. This usually means the translation uses a "
                  f"different versification (split/merged verses) than the "
                  f"standard scheme -- pass --allow-verse-count-mismatch only "
                  f"if you have confirmed this and set --verse-scheme "
                  f"accordingly.", file=sys.stderr)
            sys.exit(2)

        meta_overrides = {}
        if args.meta_file:
            with open(args.meta_file, encoding='utf-8') as f:
                meta_overrides.update(json.load(f))
        for field in TRANSLATION_META_FIELDS:
            value = getattr(args, field)
            if value is not None:
                meta_overrides[field] = value

    manifest = build_manifest(verses, meta_overrides, kind=args.kind)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=False)

    root_key = "quran" if args.kind == "text" else "translation_root"
    print(f"Wrote {args.out}")
    print(f"  kind: {args.kind}")
    print(f"  verses: {manifest['meta']['verse_count']}")
    print(f"  surahs: {manifest['meta']['surah_count']}")
    print(f"  {root_key}: {manifest[root_key]}")


if __name__ == "__main__":
    main()
