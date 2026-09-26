# Integration Notes — Portable Preference Kernel + Artifact Manifest

## What this adds

This package upgrades `file-intelligence.station` from a renamer/classifier into the front door of the Brain.

Existing FIS already does:

```text
file → text extraction → hash → keywords/entities → domain/subject → proposed name → Postgres
```

This add-on adds:

```text
file → universal artifact manifest → station route plan → portable preference prediction → feedback update
```

## Core concept

`file-intelligence.station` should be the customs checkpoint for every artifact:

```text
What is this?
Have we seen it before?
What does it contain?
Where should it go?
Which stations should process it next?
What does David usually want with this kind of file?
```

## Files

- `portable_preference_kernel.py`
  - tiny portable learned preference model
  - stores weights, not raw private data

- `artifact_manifest.py`
  - creates `.fis_manifest.json`
  - detects features and routes
  - can optionally use the preference kernel

- `sql/04_artifact_manifest_routes.sql`
  - adds `artifact_manifests`
  - adds `artifact_routes`
  - adds `preference_events`

## How to test

```powershell
python artifact_manifest.py "O:\_Theophysics_v3\some-paper.md"
```

With preference model:

```powershell
python artifact_manifest.py "O:\_Theophysics_v3\some-paper.md" --model-path portable_preference_kernel.json
```

Teach the kernel:

```powershell
python portable_preference_kernel.py learn ^
  --features sample_features.json ^
  --action "route:math-translation-layer.station" ^
  --reward 1
```

Predict:

```powershell
python portable_preference_kernel.py predict --features sample_features.json
```

## Where to patch into FIS

In `fis/pipeline.py`, after the `return` result is built, call manifest creation:

```python
from fis_addons.artifact_manifest import build_manifest
from pathlib import Path

manifest = build_manifest(Path(file_path), result, model_path=Path("portable_preference_kernel.json"))
# write manifest JSON or store in Postgres
```

Better production version:
- insert manifest into `artifact_manifests`
- insert routes into `artifact_routes`
- let station runner poll `artifact_routes WHERE status='pending'`

## Privacy

The preference kernel intentionally does not store raw content.

It stores:
- feature tokens
- action names
- weights
- counts

It filters:
- raw text
- clipboard text
- emails
- passwords
- screenshots
- API keys
- secrets

## The right first use case

Start with file routing, not screenshots/clipboard.

Learn:

```text
file features → accepted station routes
```

Example:
- markdown + equations + claims → claim-extractor + math-translation-layer
- HTML + topbar + tabs → html-article + labeler
- Lean file → axioms + proof checker route
- transcript → transcribe/classify + summarizer + claim extractor

Once this works, extend to:
- clipboard routing
- desktop actions
- AI tone preferences
- naming preferences
- browser research routing
