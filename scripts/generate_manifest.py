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


def build_manifest(verses, source_name: str):
    verse_hashes = {}
    surah_verse_hashes = {}

    for surah, ayah, text in verses:
        norm = normalize(text)
        h = sha256_hex(norm)
        key = f"{surah}:{ayah}"
        verse_hashes[key] = h
        surah_verse_hashes.setdefault(surah, []).append(h)

    # Surah-level rollup: hash of concatenated verse hashes, in ayah order
    surah_hashes = {}
    for surah, hashes in surah_verse_hashes.items():
        surah_hashes[str(surah)] = sha256_hex(''.join(hashes))

    # Whole-Quran rollup: hash of concatenated surah hashes, in surah order
    quran_hash = sha256_hex(''.join(
        surah_hashes[str(s)] for s in sorted(surah_hashes, key=int)
    ))

    manifest = {
        "meta": {
            "format_version": "1.0",
            "source": source_name,
            "orthographic_standard": "Madinah Mushaf (King Fahd Glorious "
                "Qur'an Printing Complex, Medina)",
            "provenance_note": (
                "Text is Tanzil Project's Uthmani digital transcription, "
                "verified by Tanzil against the Madinah Mushaf using manual "
                "verse checksums during their text preparation process. "
                "This is not a direct machine-readable export from KFGQPC "
                "itself -- KFGQPC's own official digital outputs are vector "
                "page images and Unicode-compliant fonts (see "
                "dm.qurancomplex.gov.sa and fonts.qurancomplex.gov.sa), not "
                "a plain-text corpus. See docs/PROVENANCE.md."
            ),
            "normalization": "NFC",
            "hash_algorithm": "sha256",
            "verse_count": len(verse_hashes),
            "surah_count": len(surah_hashes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "granularity": "verse",
            "rollup_method": "sha256 of concatenated child hashes, in canonical order",
        },
        "verses": verse_hashes,
        "surahs": surah_hashes,
        "quran": quran_hash,
    }
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="path to Tanzil-format pipe-delimited text file")
    ap.add_argument("--out", default="manifest/quran-uthmani.manifest.json")
    ap.add_argument("--source-name", default="tanzil-uthmani")
    args = ap.parse_args()

    verses = load_source(args.source)
    if len(verses) != 6236:
        print(f"WARNING: expected 6236 verses, got {len(verses)}. "
              f"Check source file format before publishing this manifest.",
              file=sys.stderr)

    manifest = build_manifest(verses, args.source_name)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=False)

    print(f"Wrote {args.out}")
    print(f"  verses: {manifest['meta']['verse_count']}")
    print(f"  surahs: {manifest['meta']['surah_count']}")
    print(f"  quran root hash: {manifest['quran']}")


if __name__ == "__main__":
    main()
