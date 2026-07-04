# USE CASES — worked examples

## 1. App build-time integrity check

Add to your build/CI pipeline:

```bash
python3 scripts/verify.py bundled-quran-text.txt --manifest manifest/quran-uthmani.manifest.json
if [ $? -ne 0 ]; then
  echo "Quran text integrity check failed — build aborted"
  exit 1
fi
```

Run this every time the bundled text file is touched, updated, or exported
from a CMS/database, so a corrupted export never reaches users silently.

## 2. OCR / extraction verification

When digitizing a print source or pulling text from a third-party site,
convert the extracted text to Tanzil pipe-format and run it through
`verify.py`. Any verse that fails is exactly the verse to hand to a human
reviewer — you don't need to proofread all 6,236 verses, only the ones that
don't match.

```bash
python3 scripts/verify.py extracted-from-scan.txt --manifest manifest/quran-uthmani.manifest.json
```

Example output when a scan introduces an error:

```
Checked 6236 verses against manifest (6236 expected, source: tanzil-uthmani)

FAILED — 1 verse(s) do not match:
  2:255: hash mismatch
      expected: 1c0bad4f5eb4f626418d042f2999fa3f3a06917eeae8951eec35b02d58a03e99
      got:      fd9a0c746d990ccef4b09db75e289dbd4e5959487e2e65dc85f6710cba61e2ee
```

This tells you *which* verse to inspect, immediately — no manual diffing of
6,236 lines.

## 3. Tamper / corruption detection (demonstrated)

This exact scenario was tested while building this tool: a single dropped
diacritic in Āyat al-Kursī (2:255) — changing `ٱلْعَظِيمُ` to `ٱلْعَظِيم`
(dropping the final damma) — was caught immediately as a hash mismatch on
that one verse, with the rest of the Quran (6,235 verses) confirmed intact.

## 4. Whole-Quran sanity check

If you just want a single yes/no ("is this file identical to the canonical
source, full stop") without needing to know which verse, compare the
`quran` root hash from a freshly generated manifest to the published one:

```python
import json
a = json.load(open("manifest/quran-uthmani.manifest.json"))
b = json.load(open("candidate.manifest.json"))
print("identical" if a["quran"] == b["quran"] else "differs — check verses{} for details")
```

## 5. Comparing two editions (manual, until cross-edition tooling exists)

Generate a manifest from each source and diff the `verses` dicts directly:

```python
import json
a = json.load(open("tanzil.manifest.json"))["verses"]
b = json.load(open("other-source.manifest.json"))["verses"]
diffs = [k for k in a if a.get(k) != b.get(k)]
print(f"{len(diffs)} verses differ:", diffs[:20])
```

Remember: a difference here does not mean either source is wrong — see
`docs/SPEC.md` for what a mismatch does and doesn't imply between
legitimately different editions.
