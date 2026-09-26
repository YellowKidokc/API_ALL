# Fruits of the Spirit Grading Station

This folder is a drop-in station for `EVIDENCE\OUTBOX`. It grades papers from the sibling `PROCESSED_ORIGINALS` folder and writes one authoritative JSON record plus one readable Markdown dossier per paper.

The system treats the Fruits as a nine-dimensional evidence profile, not a sentiment score. Truth and evidence are hard gates. Contradiction can be mixed, local, productive, unresolved, or load-bearing; it is not automatically classified as hate or anti-fruit. High scores cannot compensate for material deception, coercion, concealed exported harm, refusal of correction on a load-bearing claim, or a counterfeit mechanism that repeatedly produces an anti-fruit.

## Files

- `run_fruits_pilot_2.bat` grades at most two papers with two concurrent workers.
- `run_fruits_full_12.bat` grades the whole input folder with twelve concurrent workers.
- `run_fruits_validate_only.bat` validates configuration, rubric sources, prompts, and schemas without calling an API.
- `install_fruits_requirements.bat` installs the two document readers used for DOCX and PDF inputs.
- `config.json` contains paths, model providers, and run settings. It contains environment-variable names, never API keys.
- `scripts\fruits_grade.py` is the runner.
- `scripts\rubric\fruits_rubric_v0.3.0.json` is the executable rubric.
- `scripts\schema\fruits_report_v0.3.0.schema.json` is the JSON contract.
- `scripts\prompts\fruits_system_v0.3.0.txt` is the grading instruction.

## Placement

Place this entire folder in:

```text
EVIDENCE\OUTBOX\Fruits_of_the_Spirit_Grading_Station
```

The default configuration then resolves:

```text
Input:  EVIDENCE\PROCESSED_ORIGINALS
Output: EVIDENCE\OUTBOX\Fruits_of_the_Spirit_Grading
```

The Excel workbooks remain shared canonical sources in `Desktop\Folders\Master EXCEL OK`; they are fingerprinted in each run manifest rather than copied into every paper result.

The accompanying `Fruits_of_the_Spirit_Epistemic_Rating_System_Canonical.md` should sit beside this station folder in `OUTBOX`. Its hash is recorded when available.

## API configuration

Set at least one key in Windows before launching:

```bat
setx OPENAI_API_KEY "your-key"
setx DEEPSEEK_API_KEY "your-key"
```

Open a new Command Prompt after `setx`. Only providers whose key environment variable is present are activated. Additional OpenAI-compatible endpoints can be added to `config.json` without changing the runner.

## Outputs

For `paper.docx`, the station creates:

```text
Fruits_of_the_Spirit_Grading\paper\paper.fruits.json
Fruits_of_the_Spirit_Grading\paper\paper.fruits.md
Fruits_of_the_Spirit_Grading\paper\paper.run.json
```

The `.fruits.json` file is canonical. The `.fruits.md` file is rendered from it and then appends the extracted original text. The run receipt records source and rubric hashes, provider/model, prompt version, timing, schema status, and errors.

## Safe operating sequence

1. Run `install_fruits_requirements.bat` once.
2. Run `run_fruits_validate_only.bat`.
3. Run `run_fruits_pilot_2.bat` and inspect both JSON and Markdown results.
4. Repair the rubric or prompt if the evidence links are weak.
5. Run `run_fruits_full_12.bat` only after the pilot passes human review.

Existing valid results are skipped unless `--force` is supplied. Invalid model responses are preserved as diagnostic files and never presented as completed grades.

## Scope boundary

The station evaluates observable text, cited evidence, mechanisms, outputs, correction behavior, and stated boundaries. It does not claim access to hidden motives, salvation status, or divine origin. Its “formal receipt” proves only that a declared source, rubric, evidence profile, gate set, aggregation rule, and veto rule were processed consistently.
