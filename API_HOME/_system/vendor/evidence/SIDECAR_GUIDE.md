# Evidence sidecars and short codes

Each generated evidence companion now receives a metadata file ending in `.sidecar`
inside the dedicated **EVIDENCE\SIDECAR** folder.
Its original article is unchanged. The pipeline also records the processed original
after moving it from the inbox. A copy of each card is stored in:

`D:\GitHub\David-OSv3\_FIS_ROOT_SIDECAR_ARCHIVE\EVIDENCE`

## Three subject levels

The card preserves the companion's primary, secondary, and tertiary domains,
plus its keyword tags. These are subject classifications, not three different
processing-depth settings. Missing classifications are explicitly marked
`needs_classification`; an output's existence alone does not prove that its
claims were verified.

## Short-code glossary

| Code | Full meaning |
| --- | --- |
| ME | Master Equation |
| MATH | Mathematics |
| PHYS | Physics |
| THEO | Theology |
| INFO | Information Theory |
| CONS | Consciousness |
| QM | Quantum Mechanics |
| GR | General Relativity |
| TD | Thermodynamics |
| AI | Artificial Intelligence |
| EPI | Epistemology |
| UNCL | No matching short code yet |

ME is the requested abbreviation; the remaining codes are an initial editable
set. `SIDECAR_CODES.json` beside this document is the machine-readable glossary.
Add aliases there to recognize alternate spellings. Restart a running pipeline
after changing the glossary. Codes indicate terms mentioned in the companion;
the primary domain remains the authoritative main-subject field.

Cards store codes, full meanings, and a compact label such as `MATH-ME`.
Sidecar filenames use stable fingerprints, keeping full subject names out of
their paths. Existing article filenames are unchanged. Each card records its
source article's name and full path.

## Search and maintenance

Double-click **SEARCH_SIDECARS.bat**, then type `ME`, `Master Equation`, or `math`.
Search covers the David OS archive and prints matching source paths. This does
not depend on Windows indexing the contents of an unfamiliar extension.

Double-click **SYNC_SIDECARS.bat** to backfill or repair all outbox cards.
The scan records existing outputs as `output_observed`, rather than claiming
to have witnessed their original processing. It reports missing classifications
and errors. Re-running it does not modify articles.

New stacked companions are recorded automatically by `article_stack.py`.
The turbo intake runner additionally records each newly processed original.
Scripts that bypass that shared writer need the sync shortcut afterward.
Already running Python processes need restarting to load the new hook.

The David OS archive must be accessible at the path above on the machine
running the pipeline. If mirroring fails, the card in EVIDENCE\SIDECAR is retained and
the pipeline emits `SIDECAR RETRY NEEDED`; use sync once access is restored.
No extra model/API calls are made for sidecar generation.
