# PaperGrading

Purpose:

Describe what this workflow accepts, what it produces, and where the result goes.

## Folders

- `INPUT`: files waiting to be processed
- `OUTPUT`: finished outputs
- `REVIEW`: items needing review
- `ARCHIVE`: completed source/output bundles
- `ERROR`: failures or kicked-back items
- `CONFIG`: local config and config examples
- `PROMPTS`: LLM prompts used by this workflow
- `SCRIPTS`: implementation scripts
- `LOGS`: runtime logs

## Scripts

- `RUN_PIPELINE.bat`: run full workflow
- `RUN_THIS_STAGE.bat`: run this packet only
- `TROUBLESHOOT.bat`: dependency and folder checks

## Current launcher status

The packet entrypoint is not connected to processing stations. It exits with code 2 and reports NOT CONFIGURED; it does not grade or process documents. The shared station implementations are separate from this packet.
