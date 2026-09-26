from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
PROCESS = SCRIPTS_DIR / "PROCESS"
# The protected master is the only place an analysis may be installed.  Discovery
# shelves are copies and must never become independently edited records.
OUTBOX = ROOT / "OUTBOX" / "00_ALL_PROCESSED_ARTICLES"
LOGS = SCRIPTS_DIR / "LOGS"
CKG_TEMPLATE = SCRIPTS_DIR / "SYSTEM_FILES" / "PROMPTS" / "ckg_record_v2.0.md"

EXPECTED_HEADINGS = (
    "At a glance",
    "Central claim",
    "Best concise argument",
    "System or model",
    "Evidence chain",
    "Best evidence and sources",
    "Strongest objection and negative controls",
    "What survives",
    "What this does not establish",
    "Corrections and revisions",
    "Implications",
    "Formal or testable path",
    "Open questions and next actions",
    "Recommended classification and relationships",
)

UNIVERSAL_LEDGER_RULES = """

Universal CKG ledger rules for the three epistemic rows:

* **What survives** must state the narrowest claim that remains defensible after
  the strongest objection. It must name the supporting basis and must not simply
  repeat the central claim.
* **What this does not establish** must set hard boundaries. State nearby claims
  that are not earned, including the distinction between a formal result, an
  empirical result, and any philosophical or theological interpretation. A proof
  of encoded premises is not proof that those premises describe the world.
* **Formal or testable path** must say what could change the atom's standing.
  It must use these labeled parts: `### Lean / formal checks`,
  `### Empirical / literature checks`, and `### Adversarial checks`. In the
  Lean section, include a compact table: proposed theorem or invariant;
  definitions and premises to encode; status (*likely structurally provable*,
  *requires new axioms or definitions*, or *not yet formalizable from source*);
  and exactly what a passing result establishes. A Lean proof verifies encoded
  definitions and premises only; it does not establish physical instantiation
  or theological identity. The other sections give empirical, literature, and
  counterexample tests with a pass/fail condition where possible.

These three sections are mandatory, substantive, and source-bound. Never write
`[OPEN]`, `not run`, or a placeholder in them. If the source supplies no basis,
say what is absent and what verification would be required instead.

Reader-translation rule: in **System or model**, include a `### Terms and
plain-language bridge` subsection. Define every term, symbol, operator, or
equation needed to understand the claim that is likely above a ninth-grade
reading level. For each, provide (1) its exact role in this source, (2) a
plain-language meaning, and (3) one common-sense analogy or concrete example.
An analogy may clarify a structure but must be labeled as an analogy and never
presented as evidence or proof. In the **Lean / formal checks** table, include
a `reader meaning / analogy` column for each proposed formal object.
""".strip()


def ckg_template_contract() -> tuple[str, str]:
    """Return the versioned CKG completion contract and its stable source hash."""
    if not CKG_TEMPLATE.exists():
        raise FileNotFoundError(f"CKG template contract is missing: {CKG_TEMPLATE}")
    contract = CKG_TEMPLATE.read_text(encoding="utf-8").strip()
    if not contract:
        raise ValueError(f"CKG template contract is empty: {CKG_TEMPLATE}")
    return contract, hashlib.sha256(contract.encode("utf-8")).hexdigest()


def registry_value(name: str) -> str:
    if os.name != "nt":
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value).strip()
    except (FileNotFoundError, OSError):
        return ""


def setting(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or registry_value(name) or default


def openrouter_api_key() -> str:
    key = setting("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured. Set it as a Windows user environment variable; "
            "prepared prompts remain in PROCESS."
        )
    return key


def deepseek_api_key() -> str:
    key = setting("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not configured. Set it as a Windows user environment variable; "
            "prepared prompts remain in PROCESS."
        )
    return key


def selected_provider(value: str) -> str:
    provider = value.strip().lower()
    if provider not in {"openrouter", "deepseek"}:
        raise ValueError("--provider must be either 'openrouter' or 'deepseek'.")
    return provider


def clean_response(text: str) -> str:
    text = text.strip()
    fenced = re.fullmatch(r"```(?:markdown|md)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    return text


def validate_response(text: str) -> None:
    found = re.findall(r"(?m)^##\s+(.+?)\s*$", text)
    if found != list(EXPECTED_HEADINGS):
        raise ValueError(
            "Semantic response headings failed validation. Expected exactly: "
            + " | ".join(EXPECTED_HEADINGS)
        )
    if "## Complete preserved source" in text or "BEGIN EXACT SOURCE" in text:
        raise ValueError("Semantic response attempted to reproduce the preserved-source section.")
    sections = dict(
        re.findall(r"(?ms)^##\s+(.+?)\s*$\n(.*?)(?=^##\s+|\Z)", text)
    )
    for heading in ("What survives", "What this does not establish", "Formal or testable path"):
        body = sections.get(heading, "").strip()
        if len(re.sub(r"\s+", "", body)) < 80:
            raise ValueError(f"{heading!r} is too thin; it requires a substantive ledger entry.")
        if re.search(r"\[(?:open|not run)\]|\b(?:open|not run)\b", body, re.IGNORECASE):
            raise ValueError(f"{heading!r} contains a placeholder rather than an answer.")
    formal = sections.get("Formal or testable path", "")
    for subheading in ("Lean / formal checks", "Empirical / literature checks", "Adversarial checks"):
        if not re.search(rf"(?mi)^###\s+{re.escape(subheading)}\s*$", formal):
            raise ValueError(f"Formal or testable path is missing required subsection: {subheading}")
    system = sections.get("System or model", "")
    if not re.search(r"(?mi)^###\s+Terms and plain-language bridge\s*$", system):
        raise ValueError("System or model is missing required subsection: Terms and plain-language bridge")

    # 1. Central claim check - reject generic filler
    central_claim = sections.get("Central claim", "").strip()
    if re.search(r"explains meaning, math, dependencies|this paper presents a framework|comprehensive overview", central_claim, re.IGNORECASE):
        raise ValueError("Central claim contains generic filler instead of the exact, narrow substantive proposition.")

    # 2. Formal results in Best evidence and sources - disallow sorry or admit
    best_evidence = sections.get("Best evidence and sources", "")
    if re.search(r"\b(?:sorry|admit)\b", best_evidence, re.IGNORECASE):
        raise ValueError("Formal results in 'Best evidence and sources' contains 'sorry' or 'admit'. An unproven Lean stub is not a formal result!")


def call_openrouter(prompt: str, model: str, timeout: int, retries: int) -> tuple[str, dict]:
    # Try the requested model first (default: deepseek/deepseek-r1:free).
    # If it is rate-limited (HTTP 429), unavailable, or fails all retries, fall back to paid deepseek/deepseek-v3.2 via OpenRouter
    models_to_try = [model]
    paid_fallback = "deepseek/deepseek-v3.2"
    if model != paid_fallback and paid_fallback not in models_to_try:
        models_to_try.append(paid_fallback)

    last_error: Exception | None = None
    for active_model in models_to_try:
        is_fallback = (active_model != model)
        if is_fallback:
            print(f"[FALLBACK] OpenRouter model '{model}' unavailable or rate-limited; falling back to '{active_model}'...")

        body = json.dumps(
            {
                "model": active_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You create lossless, claim-controlled research case files. Follow the supplied "
                            "heading contract exactly. Separate formal, empirical, philosophical, semantic, "
                            "and theological claims. Never promote a candidate to canon."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "reasoning": {"enabled": True},
                "temperature": 0.1,
                "max_tokens": 7000,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {openrouter_api_key()}",
            "Content-Type": "application/json",
            "X-OpenRouter-Metadata": "enabled",
            "X-OpenRouter-Title": setting("OPENROUTER_APP_NAME", "Evidence Chain Intake"),
        }
        site_url = setting("OPENROUTER_SITE_URL")
        if site_url:
            headers["HTTP-Referer"] = site_url

        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            method="POST",
            headers=headers,
        )
        for attempt in range(1, retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                content = clean_response(payload["choices"][0]["message"]["content"])
                validate_response(content)
                return content, payload.get("usage", {})
            except urllib.error.HTTPError as http_err:
                last_error = http_err
                if http_err.code == 429:
                    print(f"[RATE LIMITED] OpenRouter 429 on '{active_model}'. Attempt {attempt}/{retries}.")
                if attempt < retries:
                    time.sleep(2**attempt)
                else:
                    break
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(2**attempt)
                else:
                    break

    raise RuntimeError(f"OpenRouter semantic analysis failed across all attempted models: {last_error}")


def call_deepseek(prompt: str, model: str, timeout: int, retries: int) -> tuple[str, dict]:
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You create lossless, claim-controlled research case files. Follow the supplied "
                        "heading contract exactly. Separate formal, empirical, philosophical, semantic, "
                        "and theological claims. Never promote a candidate to canon."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 7000,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {deepseek_api_key()}",
            "Content-Type": "application/json",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = clean_response(payload["choices"][0]["message"]["content"])
            validate_response(content)
            return content, payload.get("usage", {})
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"DeepSeek semantic analysis failed after {retries} attempts: {last_error}")


def install_analysis(
    record: str,
    analysis: str,
    provider: str,
    model: str,
    generation: str,
    template_sha256: str,
) -> str:
    marker = "## Complete preserved source"
    at_glance = "## At a glance"
    if marker not in record or at_glance not in record:
        raise ValueError("Knowledge record does not contain the expected semantic/source boundaries.")
    prefix = record.split(at_glance, 1)[0].rstrip()
    source = marker + record.split(marker, 1)[1]
    combined = f"{prefix}\n\n{analysis.rstrip()}\n\n{source}"
    combined = re.sub(
        r"(?m)^semantic_status:\s*.*$",
        "semantic_status: ai_analyzed_pending_review",
        combined,
        count=1,
    )
    captured = datetime.now(timezone.utc).isoformat()
    frontmatter_end = combined.find("\n---", 4)
    if frontmatter_end >= 0:
        old_frontmatter = combined[:frontmatter_end]
        old_frontmatter = re.sub(
            r"(?m)^(?:generation_id|generation_label|ckg_template_contract|ckg_template_sha256|semantic_provider|semantic_model|semantic_analyzed_at):.*\n?",
            "",
            old_frontmatter,
        )
        additions = (
            f'\ngeneration_id: "{generation}"'
            f'\nckg_template_contract: "CKG_RECORD_V2.0"'
            f'\nckg_template_sha256: "{template_sha256}"'
            f'\ngeneration_label: "Generation {generation.removeprefix("G")} — source-pinned analysis"'
            f'\nsemantic_provider: "{provider}"\nsemantic_model: "{model}"\nsemantic_analyzed_at: "{captured}"'
        )
        combined = old_frontmatter.rstrip() + additions + combined[frontmatter_end:]
    return combined


def process_prompt(
    prompt_path: Path,
    provider: str,
    model: str,
    generation: str,
    timeout: int,
    retries: int,
    replace_existing: bool = False,
) -> dict:
    base = prompt_path.name.removesuffix(".analysis-prompt.md")
    record_path = OUTBOX / f"{base}.knowledge.md"
    if not record_path.exists():
        raise FileNotFoundError(f"No matching knowledge record: {record_path}")
    existing = record_path.read_text(encoding="utf-8")
    if "semantic_status: ai_analyzed_pending_review" in existing and not replace_existing:
        return {"record": str(record_path), "status": "already_complete"}
    backup_path = None
    if replace_existing:
        revision_dir = PROCESS / "REVISIONS" / base
        revision_dir.mkdir(parents=True, exist_ok=True)
        revision_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = revision_dir / f"{revision_id}.knowledge.md"
        backup_path.write_text(existing, encoding="utf-8")
    contract, template_sha256 = ckg_template_contract()
    prompt = prompt_path.read_text(encoding="utf-8").rstrip() + "\n\n" + contract + "\n"
    caller = call_openrouter if provider == "openrouter" else call_deepseek
    analysis, usage = caller(prompt, model, timeout, retries)
    completed = install_analysis(existing, analysis, provider, model, generation, template_sha256)
    record_path.write_text(completed, encoding="utf-8")
    receipt = {
        "status": "completed",
        "provider": provider,
        "model": model,
        "generation_id": generation,
        "ckg_template_contract": "CKG_RECORD_V2.0",
        "ckg_template_sha256": template_sha256,
        "template": str(CKG_TEMPLATE),
        "prompt": str(prompt_path),
        "record": str(record_path),
        "previous_record_backup": str(backup_path) if backup_path else None,
        "analysis_sha256": hashlib.sha256(analysis.encode("utf-8")).hexdigest(),
        "usage": usage,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    (PROCESS / f"{base}.semantic.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Complete every prepared Evidence Chain semantic record.")
    parser.add_argument("--provider", default=setting("SEMANTIC_PROVIDER", "openrouter"))
    parser.add_argument("--model", default="", help="Provider model slug; defaults depend on --provider.")
    parser.add_argument("--generation", default=setting("ANALYSIS_GENERATION", "G2"),
                        help="Generation label for newly completed records (default: G2).")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Re-run completed records after first saving each previous record under PROCESS/REVISIONS.",
    )
    parser.add_argument("--only", nargs="+", default=[], help="Run only these prepared prompt base names (without .analysis-prompt.md).")
    args = parser.parse_args()
    provider = selected_provider(args.provider)
    generation = args.generation.strip().upper()
    if not re.fullmatch(r"G[1-9][0-9]*", generation):
        raise SystemExit("--generation must look like G2 or G10")
    model = args.model or (
        setting("OPENROUTER_MODEL", "deepseek/deepseek-r1:free")
        if provider == "openrouter"
        else setting("DEEPSEEK_MODEL", "deepseek-chat")
    )

    LOGS.mkdir(parents=True, exist_ok=True)
    prompts = sorted(PROCESS.glob("*.analysis-prompt.md"))
    if args.only:
        wanted = {value.removesuffix(".analysis-prompt.md") for value in args.only}
        prompts = [p for p in prompts if p.name.removesuffix(".analysis-prompt.md") in wanted]
        missing = wanted - {p.name.removesuffix(".analysis-prompt.md") for p in prompts}
        if missing:
            raise SystemExit("No prepared prompt(s) named: " + ", ".join(sorted(missing)))
        if not prompts:
            raise SystemExit("No prepared prompts selected.")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []
    for prompt in prompts:
        try:
            result = process_prompt(
                prompt,
                provider,
                model,
                generation,
                args.timeout,
                args.retries,
                args.replace_existing,
            )
            results.append(result)
            label = "SKIP - ALREADY COMPLETE" if result.get("status") == "already_complete" else "COMPLETED"
            print(f"[{label}] {prompt.name}")
        except Exception as exc:
            results.append({"prompt": str(prompt), "status": "failed", "error": str(exc)})
            print(f"[FAILED] {prompt.name}: {exc}")
    failures = sum(result.get("status") == "failed" for result in results)
    log = {
        "run_id": run_id,
        "stage": "semantic_analysis",
        "prompt_count": len(prompts),
        "failure_count": failures,
        "results": results,
    }
    (LOGS / f"semantic-{run_id}.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"Semantic analysis completed {len(prompts) - failures}/{len(prompts)} record(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
