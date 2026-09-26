# 18 — River (Online Streaming ML)

**Library:** `river` v0.21.2
**Type:** Incremental learning — one event at a time, microsecond latency
**Use case:** Real-time behavior learning from every approve/reject action
**Model size:** Kilobytes forever
**Status:** WIRED — learns from /approve and /reject on port 8420

## Files in this folder

| File | Purpose |
|------|---------|
| config.json | Model config and status |
| river_naming_state.pkl | River model weights (created on first learn event) |
| README.md | This file |

## How it works

River runs inside the FIS naming learner (`fis/naming_learner.py`).
Every time David approves or rejects a rename through the GUI or API,
River updates its weights in microseconds. The state is saved to
`river_naming_state.pkl` in THIS folder every 10 events.

## Connection to PPK (Model 17)

River is the learning engine. PPK is the portable output.
Every 50 events, River exports compressed preference weights
to `17_portable_preference_kernel/naming_ppk.json`.

BIL/River collects signals -> PPK stores portable preference identity.

## Connection to Markovify (Model 19)

Every approved rename appends the approved name to
`19_markovify_text/approved_slugs.jsonl`. After 20+ approvals,
Markovify can predict slugs from that corpus.

## Wiring

```
FIS /approve (port 8420)
    → naming_learner.learn_approve()
        → River updates weights (this folder)
        → Slug corpus appends (Model 19 folder)
        → Every 50 events: export to PPK (Model 17 folder)

FIS /reject (port 8420)
    → naming_learner.learn_reject()
        → River updates weights (this folder)
        → If correction given: learns the correction as positive
```
