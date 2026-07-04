# PROVENANCE

Where this text actually comes from, stated precisely, so nobody mistakes
this manifest for something it isn't.

## The orthographic standard: KFGQPC

The **King Fahd Glorious Qur'an Printing Complex** (Mujamma' al-Malik Fahd
li-Tiba'at al-Mus'haf al-Sharif), Medina, Saudi Arabia, publishes the
**Madinah Mushaf** — the print edition (Ḥafṣ ʿan ʿĀṣim recitation) that has
become the de facto global reference for Uthmani-script Quran orthography.
The Complex has produced over 128 million copies since 1985 and is the
standard cited by essentially every serious digital Quran project as the
orthographic ground truth.

KFGQPC's own **official digital outputs** are:
- **Digital Mus'haf al-Madinah** — vector page images (`dm.qurancomplex.gov.sa`)
- **Uthmani Unicode fonts** — for rendering the script (`fonts.qurancomplex.gov.sa`)

As of this writing, KFGQPC does not publish a plain-text, machine-readable
verse corpus directly. Their outputs are print/visual assets and fonts —
consistent with their mandate as a *printing* complex.

## Where the actual text in this manifest comes from: Tanzil

The verse text hashed in this manifest is the **Tanzil Project**'s Uthmani
digital transcription (`tanzil.net`). Tanzil is not KFGQPC, but its
published methodology is a direct, documented verification against the
Madinah Mushaf:

> "Manual Verification: In this step, the Quran text produced was examined
> thoroughly against the Medina Mushaf... Verse checksums were computed
> manually using all letters and diacritics from the madinah mus'haf and
> then compared to the digital version."

In other words: Tanzil's text is a transcription of the KFGQPC standard,
checked against it verse-by-verse by hand at the time of Tanzil's
preparation. This manifest is a checksum layer **on top of that existing
transcription** — it does not re-derive the text from KFGQPC directly, and
it does not re-verify Tanzil's original manual check.

## What this means for trust in this manifest

- **High confidence, one hop removed.** You are trusting Tanzil's
  documented, one-time manual verification against the Madinah Mushaf, not
  a direct KFGQPC export.
- **This manifest adds:** a re-runnable, automatable check that *your* copy
  matches *Tanzil's* copy — closing the gap between "Tanzil verified it once"
  and "every downstream user can verify their own copy anytime."
- **This manifest does not add:** independent re-verification against the
  physical Madinah Mushaf pages. That would require OCR/manual comparison
  against KFGQPC's vector page images directly — a separate, much larger
  project (see "Future work" below).

## If you need a tighter provenance chain

For use cases requiring verification closer to KFGQPC's own assets
(academic citation, print-house QA, dispute resolution):

1. Compare against KFGQPC's **Digital Mus'haf al-Madinah** vector pages
   (`dm.qurancomplex.gov.sa`) directly — requires OCR or manual
   transcription, since these are page images, not text.
2. Cross-check against **QUL** (Tarteel's Quranic Universal Library),
   which credits KFGQPC directly for its Uthmani script assets and fonts:
   `github.com/TarteelAI/quranic-universal-library`
3. Treat any manifest (including this one) as *evidence*, not proof — the
   strongest claim any digital Quran text tool can honestly make is
   "matches [named source]'s verified transcription," not "is the
   Quran," and this repo makes only the former claim.

## Future work

A genuinely KFGQPC-rooted manifest would require either:
- KFGQPC publishing an official plain-text corpus (not currently available), or
- A dedicated OCR/vector-extraction project against the Digital Mus'haf
  al-Madinah page images, with its own manual review process analogous to
  Tanzil's — out of scope for this repository.

This repo will be updated if KFGQPC publishes a machine-readable text
source directly.

## Translations

Translation manifests make a categorically weaker claim than the Arabic
text manifest, and that difference is load-bearing.

### No canonical source

The Arabic text has a clear reference point: KFGQPC's Madinah Mushaf, via
Tanzil's verified transcription. **No translation has an equivalent single
ground truth.** A given translation (e.g. Saheeh International) exists
across multiple publisher editions that are revised over time, and no
authority certifies one edition as definitively "the" text the way KFGQPC
functions for the Arabic. A translation manifest in this repo therefore
pins one narrow, honest claim: **"this is distributor D's copy of
translation T, as retrieved on date Y"** — not "this is the correct or
official text of this translation."

### Distributor matters

Tanzil and QuranEnc can both distribute "the same" translation and still
differ — in footnote handling, minor wording corrections, or formatting
conventions — even when both are legitimate, good-faith copies. That's why
`distributor` is a first-class field embedded directly in every
translation manifest's filename, not just a metadata note: two manifests
for the same `translation_id` but different `distributor` are expected to
potentially have different hashes, and that difference is not a defect in
either.

### Copyright and the hash-only framing

Unlike the Quran's Arabic text, translations are **copyrighted works**
belonging to their translators/publishers. This repository's approach:
**publish only SHA-256 hashes, never the translation text itself.**

A SHA-256 hash is a one-way digest — it does not permit reconstruction of
the original text, so publishing per-verse hashes is not republishing or
redistributing the copyrighted translation. This framing is sound, with
four caveats worth stating plainly:

1. **Not legal advice.** This is a defensive engineering practice, not a
   legal opinion. If you plan to redistribute anything beyond the hashes
   themselves, consult the specific translation's own license/terms first.
2. **Never commit real translation text into this repository** — including
   in test fixtures. Even a handful of real verses used as a "sample" in a
   test file would itself be a redistribution of copyrighted text. Tests
   in this repo use synthetic/dummy verse strings, never actual
   translation content.
3. **Don't publish anything beyond the plain per-verse SHA-256 hash** —
   no verse lengths, no n-gram or partial hashes, nothing that could aid
   reconstructing the underlying text. Keep the manifest to exactly what's
   specified in `docs/SPEC.md`.
4. **Retrieval-time terms of service are a separate obligation from
   publishing hashes.** Fetching a translation's text from a distributor
   (to compute hashes from) may itself be subject to that distributor's
   terms of service. That obligation belongs to whoever retrieves and
   hashes the text (i.e. the maintainer generating a given manifest), not
   to downstream users who only ever consume the published hashes to run
   `verify.py` against their own already-obtained copy.
