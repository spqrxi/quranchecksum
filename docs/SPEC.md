# SPEC

## Hashing

- **Algorithm:** SHA-256, hex-encoded lowercase.
- **Normalization:** each verse string is Unicode-normalized to **NFC**
  before hashing. Leading/trailing whitespace is stripped. No other
  transformation is applied — diacritics, small letters (dagger alif,
  small waw/yeh), and all combining marks are hashed exactly as present in
  the source.
- **Granularity:** one hash per verse (`surah:ayah`), 6,236 total.
- **Rollups:**
  - Surah hash = `sha256(concat(verse_hashes in ayah order))`
  - Whole-Quran hash = `sha256(concat(surah_hashes in surah order))`

  These are simple two-level Merkle-style rollups: they let you compare a
  single "is anything different at all" value, while the verse layer still
  gives you exact localization when something is.

## What a matching hash tells you

That the verse text, after NFC normalization, is byte-identical to the
source manifest was generated from. Nothing more, nothing less.

## What a matching hash does NOT tell you

- **Not a correctness claim.** If the manifest was itself generated from a
  source with an error, a "match" just means your copy has the same error.
  The manifest is only as good as the file it was built from — always check
  `meta.source` and regenerate/compare against the original Tanzil release
  yourself before trusting a manifest from a third party.
- **Not cross-edition equivalence.** A verse hash mismatch between two
  different *legitimate* editions (e.g. Tanzil's Imlāʾī/simple rendering vs
  its own Uthmani rendering) does not mean either is wrong — different
  editions intentionally use different orthographic conventions (full alif
  vs elided alif, different small-letter placement, etc). This manifest
  only tells you "identical or not" — it does **not** grade *why* two
  sources differ. That requires structural analysis below the verse level
  (see Scope in the README), which this release doesn't include.
- **Not tajwīd or qirāʾah validation.** This checks orthographic text
  identity, not recitation correctness.

## Why NFC specifically

Arabic combining marks (harakat, shadda, madda, etc.) can in principle be
represented in different combining orders that render identically but are
different byte sequences. NFC gives a single canonical ordering so that
visually-identical text produces the same hash regardless of how the
combining marks happened to be ordered at the byte level in a given export.
It does **not** resolve differences that are genuine character-level
choices (e.g. presence vs absence of a dagger alif) — those legitimately
produce different hashes, because they are different text.

## Verse addressing

Keys are `"{surah}:{ayah}"` as plain strings, 1-indexed, matching standard
Quran verse numbering (e.g. Al-Fātiḥah = surah 1, verses 1–7). This matches
the addressing scheme used by Tanzil, Quran.com, and virtually all Quran
software.

## Manifest file format

```json
{
  "meta": {
    "format_version": "1.0",
    "source": "tanzil-uthmani",
    "normalization": "NFC",
    "hash_algorithm": "sha256",
    "verse_count": 6236,
    "surah_count": 114,
    "generated_at": "2026-07-04T05:00:00+00:00",
    "granularity": "verse",
    "rollup_method": "sha256 of concatenated child hashes, in canonical order"
  },
  "verses": { "1:1": "<hex>", "1:2": "<hex>", "...": "..." },
  "surahs": { "1": "<hex>", "...": "..." },
  "quran": "<hex>"
}
```

Always check `meta.source` and `meta.generated_at` before trusting a
manifest — regenerate and diff against your own trusted source if in doubt.
