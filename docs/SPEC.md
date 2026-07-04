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

## Translation manifests

Everything above (NFC normalization, strip-only, SHA-256, the two-level
rollup) applies **verbatim** to translation manifests. The hashing and
rollup code is identical for the Arabic text and for translations — only
the metadata and one key name differ.

One explicit rule specific to translations: **do not strip or alter
footnote markers, bracketed interpolations, or any other markup** a
distributor includes in the verse field. Whatever string the distributor
ships is hashed exactly (after NFC + strip), the same way the Arabic text
manifest hashes diacritics and small letters exactly as present. This means
a hash mismatch between two distributors' copies of "the same" translation
can legitimately reflect a footnote-convention or interpolation-style
difference, not a translation error — see below.

### `kind` discriminator and root-hash key

Every manifest has `meta.kind`, either `"text"` or `"translation"`. The
name of the whole-manifest root hash key depends on it:

- `kind: "text"` → root hash is under the key **`quran`**
- `kind: "translation"` → root hash is under the key **`translation_root`**

These are deliberately different key names so a consumer can never
accidentally read a translation's root hash as if it were "the Quran"
root hash, or vice versa.

### Translation meta schema

```json
{
  "meta": {
    "format_version": "1.0",
    "kind": "translation",

    "translation_id": "en.sahih",
    "translator": "Saheeh International",
    "language": "en",
    "language_name": "English",
    "direction": "ltr",

    "distributor": "tanzil",
    "distributor_url": "https://tanzil.net/trans/",
    "distributor_edition_id": "en.sahih",
    "edition_version": "unversioned",
    "edition_note": "free text explaining edition_version if not a real version string",
    "retrieved_at": "2026-07-04",

    "based_on_arabic": "tanzil-uthmani",
    "verse_scheme": "tanzil-standard-6236",

    "normalization": "NFC",
    "hash_algorithm": "sha256",
    "verse_count": 6236,
    "surah_count": 114,
    "generated_at": "2026-07-04T05:00:00+00:00",
    "granularity": "verse",
    "rollup_method": "sha256 of concatenated child hashes, in canonical order",

    "canonicity": "none",
    "canonicity_note": "see 'What a translation hash match does NOT tell you' below",
    "copyright_note": "hashes only, no translation text stored -- see docs/PROVENANCE.md#translations",
    "supersedes": null
  },
  "verses": { "1:1": "<hex>", "...": "..." },
  "surahs": { "1": "<hex>", "...": "..." },
  "translation_root": "<hex>"
}
```

- **`translation_id`** identifies the translation itself (e.g. `en.sahih`).
- **`distributor`** identifies who you got this specific copy from
  (`tanzil`, `quranenc`, ...). The **same nominal translation can differ
  slightly between distributors** — different footnote handling, minor
  text revisions — so distributor is a first-class field, not an
  afterthought, and is part of the manifest filename (see below).
- **`distributor_edition_id`** is the distributor's own slug/filename for
  this edition, which may not match `translation_id` exactly.
- **`edition_version` / `retrieved_at`**: some distributors (Tanzil) don't
  publish version strings for translations at all. In that case,
  `edition_version` is `"unversioned"` and `retrieved_at` (the date this
  copy was fetched) plus the manifest's own hashes *are* the practical
  version identity.
- **`verse_scheme`** records which versification the translation is mapped
  onto. This matters — see "Verse count and versification" below.

### File layout and the index

```
manifest/
  quran-uthmani.manifest.json
  translations/
    index.json
    en.sahih.tanzil.manifest.json               <- current alias, always mirrors latest
    en.sahih.tanzil.2026-07-04.manifest.json     <- dated snapshot
```

Filename pattern: `<translation_id>.<distributor>[.<YYYY-MM-DD>].manifest.json`.
The file **without** a date is the stable "current" alias that documentation
can link to without the URL rotting; files **with** a date are immutable
historical snapshots.

`manifest/translations/index.json` is a generated catalog (via
`scripts/build_index.py`, never hand-edited) with one entry per
`(translation_id, distributor)` pair:

```json
{
  "meta": {
    "format_version": "1.0",
    "kind": "translation-index",
    "generated_at": "2026-07-04T05:00:00+00:00",
    "description": "..."
  },
  "translations": [
    {
      "translation_id": "en.sahih",
      "translator": "Saheeh International",
      "language": "en",
      "distributor": "tanzil",
      "current": "en.sahih.tanzil.manifest.json",
      "current_version": "2026-07-04",
      "translation_root": "<hex>",
      "verse_count": 6236,
      "verse_scheme": "tanzil-standard-6236",
      "history": [
        { "version": "2026-07-04", "file": "en.sahih.tanzil.2026-07-04.manifest.json", "translation_root": "<hex>" }
      ]
    }
  ]
}
```

### Staleness model: versioned history, not overwrite

Unlike the Arabic text (which has one long-lived reference version),
translations legitimately get corrected by their publishers over time. So
updates are handled as **versioned history**, not silent overwrites:

- Each time a re-fetch produces different hashes, it's written as a new,
  dated snapshot file — the old one is never deleted or overwritten.
- The undated alias file is updated to be a copy of the latest snapshot,
  so links to it never rot.
- The new manifest's `meta.supersedes` names the prior dated file it
  replaces.
- This means a consumer who pinned an old hash can still find the exact
  manifest that matches their (older) copy, and explain precisely which
  edition-date it corresponds to.

### Verse count and versification

Translation generation (`--kind translation`) **fails by default** if the
parsed verse count doesn't match `--expected-verses` (default 6236). This
is deliberate: some translations split or merge verses relative to the
standard Tanzil scheme (differing ayah boundaries in a handful of surahs),
and a silent count mismatch would cause verses to cross-map to the wrong
keys. Pass `--allow-verse-count-mismatch` only after confirming the
translation's versification is intentional, and set `verse_scheme`
accordingly so the mismatch is documented in the manifest itself, not
hidden. This tool does not attempt automatic verse-scheme remapping.

## What a translation hash match does NOT tell you

All the same caveats as the Arabic text apply, plus translation-specific
ones:

- **Not canonical.** There is no single authoritative text for a
  translation the way KFGQPC is the reference for the Arabic. A match only
  means "byte-identical to the one distributor copy, at the one retrieval
  date, named in this manifest's metadata" — nothing about the translation
  being correct, official, or authoritative.
- **Not equal across distributors.** A hash mismatch between Tanzil's and
  QuranEnc's copies of "the same" translation does not mean either is
  wrong — footnote handling and minor text revisions commonly differ
  between distributors of the same underlying translation.
- **Not equal across versions/dates.** A mismatch between two dated
  snapshots of the same `translation_id`+`distributor` usually just means
  the publisher corrected something between retrieval dates. Check
  `meta.supersedes` and the index's `history` to see which version you
  actually have.
- **Not a copyright grant.** This manifest never contains translation
  text — only hashes. See `docs/PROVENANCE.md#translations` for what that
  does and doesn't imply.
