# Evidence Chain Intake

Portable scripts and Windows launchers for the source-preserving evidence intake workflow.

## Daily start

The launchers create their empty runtime folders automatically, so the workflow can be copied into another NLP project without copying papers, outputs, or logs.

Run `RUN_DAILY_API_PREFLIGHT.bat` before production. It:

1. asks how many documents may run;
2. asks whether quality, speed, or long-document capacity matters most;
3. discovers OpenRouter text models currently priced at zero;
4. ranks models for the selected priority;
5. tests candidates for JSON compliance, source fidelity, and epistemic accuracy against a scored reference comparison;
6. selects the first passing model and writes a dated routing receipt;
7. caps the free workload and prepares the intake environment.

The comparison gate accepts equivalent wording only when at least 90 percent of the required reference criteria are present. A failed candidate is recorded and the next eligible free model is tested.

## Boundaries

- Source documents, generated output, API keys, logs, and model-history receipts are not stored in this repository.
- Generated analysis remains candidate material. Passing a model test or completing this pipeline does not establish canon admission.
- Each source document is preserved intact; the default planning target is 8,000-9,000 source words per batch.
