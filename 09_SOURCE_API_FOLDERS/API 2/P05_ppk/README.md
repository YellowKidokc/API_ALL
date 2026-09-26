# FIS Portable Preference Kernel Package

This is the “home run” layer for `file-intelligence.station`.

## Big idea

Your current FIS already classifies and renames files.

This package turns FIS into the **Brain ingestion gateway**:

```text
artifact enters
→ extract identity
→ detect features
→ create manifest
→ recommend station routes
→ learn from David's accept/reject/edit behavior
→ produce portable preference model
```

## Why this matters

This is not normal memory.

This is a small private preference kernel:

```text
No raw personal data.
No emails.
No screenshots.
No clipboard history.
No passwords.
```

It stores only:

```text
feature/action weights
route preferences
counts
confidence
```

You can copy the model file to another machine and let another FIS/AI worker know how David likes work routed.

## Install

Copy `fis_addons/` into your station repo or put it on PYTHONPATH.

Run SQL:

```bash
psql -h 192.168.1.97 -U fis_user -d fis_db -f sql/04_artifact_manifest_routes.sql
```

## Quick test

```powershell
python fis_addons\artifact_manifest.py "C:\path\to\paper.md"
```

## Learn a preference

```powershell
python fis_addons\portable_preference_kernel.py learn ^
  --features examples\sample_features.json ^
  --action "route:claim-extractor.station" ^
  --reward 1
```

## Predict routes

```powershell
python fis_addons\portable_preference_kernel.py predict ^
  --features examples\sample_features.json
```

## First real target

Use this first for:

```text
file features → station route recommendation
```

Do not start with full desktop behavior. Prove the kernel with file routing first.
