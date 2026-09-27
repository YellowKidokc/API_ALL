# 55_LEAN_PAPERS

Every Lean source (or claim written for Lean) in the Lean inbox becomes:

| file (in `<item>/03_REPORT/`) | for whom |
|---|---|
| `1_FORMAL.md` | paper 1: readers who know Lean and formal verification |
| `2_READER.md` | paper 2: someone who has never used Lean (six fixed headings) |
| `3_CLAIMS.md` | each claim filled into `templates/lean/CLAIM_TEMPLATE.md`; assumptions only by id |
| `4_ASSUMPTIONS.md` | the assumptions paper (`templates/lean/ASSUMPTIONS_TEMPLATE.md`), reviewed before anything is run |

- Script: `55_lean_papers.py` (`ONE_MENU.bat 55`; `--lane priority|series|general`, `--group "Trinity Proofs"`)
- Works on: `lean_inbox` → `lean_outbox` (point both at any folder in `paths.json`; the scripts never live there)
- Menu options it accepts: limit, workers, provider, model, focus, redo
- One source = the whole file in every call (never chunked; files above `context_words` are skipped with a message).
  Sources run side by side (default 30, `--workers 50`), each getting the same four calls.

## Inbox

```
lean_inbox/
  00_PRIORITY/                  first
  01_SERIES/<series name>/      the folder name is the series
  02_GENERAL/<group name>/      grouped like a series without being one (e.g. "One pagers")
```

The group travels into the outbox: `lean_outbox/<lane>/<group>/<item>/`.

## Masters (rebuilt after every item, in inbox order)

- `00_ALL_CLAIMS.md`: every claim through the claim template, grouped by lane and group.
- `00_ALL_ASSUMPTIONS.md`: every assumptions paper, same order.
- `00_ASSUMPTIONS_REVIEW.xlsx`: one row per assumption with a `review` column. Your marks are kept when it is rebuilt.

## Rules enforced in code

- The model never certifies: `LEAN_CERTIFIED` or any unknown status becomes `CANDIDATE`; only the compiler certifies.
- A control is `PASS` only when it cites the source line that records the result (`L88: ...`); otherwise `NOT_RUN`.
- Claims point to assumptions by id; unknown ids are dropped.

## API goals

| id | title | asks for |
|---|---|---|
| `API-55.1` | LEAN_ASSUMPTIONS | every assumption with line, kind, load-bearing, plus the assumptions paper |
| `API-55.2` | LEAN_CLAIMS | up to 12 claims for the claim template (no assumptions inside) |
| `API-55.3` | LEAN_FORMAL_PAPER | paper 1: formal, for Lean readers |
| `API-55.4` | LEAN_READER_PAPER | paper 2: for someone new to Lean |
