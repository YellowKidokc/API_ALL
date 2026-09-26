# 19 — Markovify (Text Prediction for Slug Generation)

**Library:** `markovify` v0.9.4
**Type:** Markov chain text generator
**Use case:** "David would name this..." slug predictions
**Model size:** Grows with corpus, stays small
**Status:** WIRED — corpus grows from every approved rename

## Files in this folder

| File | Purpose |
|------|---------|
| config.json | Model config and status |
| approved_slugs.jsonl | Training corpus — every approved rename |
| README.md | This file |

## How it works

Every time David approves a rename through FIS, the approved filename
gets appended to `approved_slugs.jsonl` as a JSON line:

```json
{"name": "GKC3F_consciousness-substrate_TP.CS_000147.md", "domain": "TP", "reward": 1.0, "timestamp": "2026-06-03T..."}
```

After 20+ approved names accumulate, Markovify builds a Markov chain
from the corpus and can predict slugs for new files. The naming
learner checks Markovify BEFORE generating the default YAKE slug,
so the system increasingly names files the way David would.

## Connection to River (Model 18)

Independent. Markovify doesn't feed from or into River.
Both receive signals from the same approve/reject events,
but they learn different things:
- River: learns WHICH classifications David accepts
- Markovify: learns WHAT NAMES David likes

## Corpus format

Each line in `approved_slugs.jsonl`:
```json
{
  "name": "the approved filename",
  "domain": "TP",
  "reward": 1.0,
  "timestamp": "ISO-8601"
}
```

Rejections are stored with `reward: -1.0` so the corpus
captures both positive and negative examples.
