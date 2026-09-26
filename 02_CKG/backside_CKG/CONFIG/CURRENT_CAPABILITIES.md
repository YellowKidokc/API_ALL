# CKG staged review — 30-worker preparation

Run CHECK_CKG_INBOX.bat first. Place copies in INBOX/01_PRIORITY, INBOX/02_SERIES/<series>, or INBOX/03_GENERAL/<collection>. INBOX/00_WAITING_NOT_PROCESSED is never selected. An untouched copy of every source opened by the runner is saved to OUTBOX/00_ORIGINAL_UNTOUCHED. Successfully processed source files are moved to OUTBOX/00_ORIGINAL; failed or waiting items stay in INBOX.

RUN_CKG_30_WORKERS.bat reports unique eligible inputs and asks ALL or a number. To prepare a 30-paper batch, enter 30. Thirty workers means up to thirty documents in progress, not thirty calls per document simultaneously. Defaults use DeepSeek deepseek-chat, configurable in CONFIG/ckg.json; no provider fallback. Credentials come from DEEPSEEK_API_KEY or CONFIG/keys.local.json. No credential is bundled.

This profile makes twelve calls per new paper: mapping, ten CKG sections, final audit. A thirty-paper run therefore normally makes 360 calls, plus provider retries. No live API call has been made to validate quality/model access in this build. Begin with one paper and inspect it before committing the thirty-paper batch.

Each successful stage is saved. A restart reuses validated checkpoints for unchanged inputs, template, model and prompt. Original bytes, JSON records, per-session selected/result records, and published output hashes are retained. Completed outputs with missing or changed hashes are republished from stage checkpoints. A simultaneous second runner is rejected. Input copying should finish in WAITING before release; changed files are rejected after selection. Interrupted items remain in SELECTED without completion; restart selects them again.

Outputs: OUTBOX/ (companions and processed sources, readable-name copies), OUTBOX/00_ORIGINAL_UNTOUCHED (intake backup), OUTBOX/00_ORIGINAL (processed source originals), OUTBOX/02_BY_DOMAIN (companion copies), OUTBOX/03_BY_TAG (companion copies by keyword), OUTBOX/04_BY_SERIES (companion copies), OUTBOX/CLAIMS_PROOFS_EVIDENCE, OUTBOX/00_MASTER_INDEX.csv, session records in SYSTEM/RECORDS. Grades default UNSCORED. Every result is candidate AI analysis, never admission or proof verification.

## Explicit implementation limits

- Full Atom opening, the eleven-dimension per-declaration proof payload, normalized definition/argument/math extraction, blind-review execution, and validation against the repository's complete Atom schema are not implemented in this profile. The output marks these pending.
- Lean files receive source analysis only; no compiler runs. Station folders influence intake provenance; specialized station executors have not all been connected.
- Grader, Fruits, series synthesis, feeder/watch scheduling and dashboard migration are not enabled. Use manual batches.
- Supported UTF-8 inputs: Markdown, text, Lean, TeX, HTML. HTML is currently read as source text. PDFs/Office files are reported unsupported. Sources over 100,000 characters require future chunked intake and are rejected, never silently truncated.
- UUIDs represent source-version objects; cross-document semantic identity reconciliation remains pending. The readable address uses the paper UUID until a shared human-number registry is implemented.
- A header or score emitted in model prose is an AI proposal, not a runner-attested result. The machine package is the source of operational status.
- HTTP transient retries can repeat ambiguous paid requests; successful persisted stages are reused. Source preservation and checkpoints are on the selected workspace filesystem, so NAS availability remains required.

Offline tests cover 30-worker processing, duplicate/waiting exclusion, stable checkpoint reuse, exact-source quotation rejection and isolated failure. This is a tested source-review runner, not yet the complete agreed multi-station system.
