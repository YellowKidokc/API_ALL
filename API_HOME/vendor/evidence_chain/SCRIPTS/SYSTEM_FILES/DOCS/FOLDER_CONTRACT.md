# Folder Contract

| Folder | Purpose |
|---|---|
| `INBOX` | Source files waiting for intake |
| `PROCESS` | Receipts and model-ready semantic prompts |
| `OUTBOX/01_PROCESSED_UNSORTED` | Newly processed records awaiting organization |
| `OUTBOX/02_SORTED_READY_TO_TRANSFER` | Reviewed records approved for the transfer stage |
| `OUTBOX/03_TRANSFERRED` | Completed-transfer records or receipts |
| `OUTBOX/99_HOLD` | Records deliberately prevented from advancing |
| `QUESTIONS` | Low-confidence decisions requiring David |
| `ORIGINALS` | Timestamped exact source copies |
| `TRANSFER` | Optional destination staging |
| `LOGS` | Processing and transfer receipts |
| `SCRIPTS` | Executable workflow code |
| `SYSTEM_FILES` | Configuration, prompts, schemas, and documentation |

Sources are never silently overwritten, shortened, moved, or deleted. Outputs remain candidate
records until separately reviewed and admitted through the appropriate authority.
