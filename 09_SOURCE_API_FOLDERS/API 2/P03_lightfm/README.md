# P03 — Lightfm

**Library:** `lightfm`
**Port:** 20103
**Status:** blocked

## What it does
Hybrid collaborative + content-based recommendations (blocked on Windows build)

## Learns from
User-item interactions + item metadata

## Outputs
Hybrid recommendation scores

## Dependencies
None (independent)

## Folder structure
```
P03_lightfm/
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
