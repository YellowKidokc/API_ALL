# P02 — Recbole

**Library:** `recbole`
**Port:** 20102
**Status:** scaffolded

## What it does
General-purpose recommendation framework (future)

## Learns from
Structured interaction logs

## Outputs
Ranked recommendations

## Dependencies
None (independent)

## Folder structure
```
P02_recbole/
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
