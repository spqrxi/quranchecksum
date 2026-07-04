#!/usr/bin/env python3
"""
verify.py — check a Quran text source against a published manifest.

Usage:
    python3 verify.py <source.txt> [--manifest manifest/quran-uthmani.manifest.json]

Exit codes:
    0  all verses match
    1  one or more verses failed (details printed to stdout)
    2  input error (bad file, wrong verse count, etc.)

This is the tool an app build step, CI pipeline, or OCR/extraction workflow
runs to confirm text integrity before shipping or ingesting it.
"""
import sys
import json
import argparse
from generate_manifest import load_source, normalize, sha256_hex


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="path to Tanzil-format pipe-delimited text file to check")
    ap.add_argument("--manifest", default="manifest/quran-uthmani.manifest.json")
    args = ap.parse_args()

    try:
        with open(args.manifest, encoding='utf-8') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: manifest not found at {args.manifest}", file=sys.stderr)
        sys.exit(2)

    verses = load_source(args.source)
    if not verses:
        print("ERROR: no verses parsed from source file", file=sys.stderr)
        sys.exit(2)

    known = manifest["verses"]
    failures = []
    checked = 0

    for surah, ayah, text in verses:
        key = f"{surah}:{ayah}"
        if key not in known:
            failures.append((key, "NOT_IN_MANIFEST", None, None))
            continue
        h = sha256_hex(normalize(text))
        checked += 1
        if h != known[key]:
            failures.append((key, "HASH_MISMATCH", known[key], h))

    missing = set(known) - {f"{s}:{a}" for s, a, _ in verses}

    print(f"Checked {checked} verses against manifest "
          f"({manifest['meta']['verse_count']} expected, "
          f"source: {manifest['meta']['source']})")

    if not failures and not missing:
        print(f"PASS — all verses match. Quran root hash: {manifest['quran']}")
        sys.exit(0)

    if failures:
        print(f"\nFAILED — {len(failures)} verse(s) do not match:")
        for key, kind, expected, got in failures:
            if kind == "NOT_IN_MANIFEST":
                print(f"  {key}: not found in manifest (unexpected verse key)")
            else:
                print(f"  {key}: hash mismatch")
                print(f"      expected: {expected}")
                print(f"      got:      {got}")

    if missing:
        print(f"\nMISSING — {len(missing)} verse(s) in manifest not found in source:")
        for key in sorted(missing)[:20]:
            print(f"  {key}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")

    sys.exit(1)


if __name__ == "__main__":
    main()
