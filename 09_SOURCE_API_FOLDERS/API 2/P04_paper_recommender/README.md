# P04 — Paper_Recommender

**Library:** `custom`
**Port:** 20104
**Status:** scaffolded

## What it does
Research paper relevance scoring for Theophysics corpus

## Learns from
Paper approve/reject, citation patterns, reading time

## Outputs
Paper relevance scores, reading order suggestions

## Dependencies
P06_river, P05_ppk

## Folder structure
```
P04_paper_recommender/
  _front_door/    Config, health check, processing scripts
  _inbox/          Drop files here for processing
  _outbox/         Processed results
  _processed/      Archive of processed items
  _logs/           Runtime logs
  _state/          Trained model weights (pkl, json)
  _exports/        Periodic exports (PPK snapshots)
  START.bat         Boot the engine
  HEALTHCHECK.bat   Check engine health
  PROCESS_INBOX.bat Process pending inbox items
```
