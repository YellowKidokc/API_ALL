#!/usr/bin/env python3
"""
run_evaluator.py
================
Main runner for χ-Evaluator v2.

Reads claims from INBOX/*.txt
Calls OpenAI and/or DeepSeek
Writes JSON + Markdown reports to OUTBOX/
Config lives in config.xlsx (created on first run if missing)
"""

import sys
import json
import time
import pathlib
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
INBOX_DIR  = SCRIPT_DIR / "INBOX"
OUTBOX_DIR = SCRIPT_DIR / "OUTBOX"
CONFIG_XL  = SCRIPT_DIR / "config.xlsx"
CONFIG_TXT = SCRIPT_DIR / "config.txt"      # fallback

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

SYSTEM_PROMPT = """You are χ-Evaluator v2, a coherence diagnostic engine based on the Theophysics Master Equation:

χ = G · M · E · S_eff · T · K · R · Q · F · C

This is a product, not a sum. A zero channel collapses total coherence.

You are not a truth oracle. You do not declare truth by authority. You evaluate whether a claim remains structurally coherent across ten channels and under pressure.

Channels:
G — External input / dependency honesty
M — Alignment / reference standard
E — Truth / signal fidelity
S_eff — Entropy / disorder cost
T — Temporal persistence
K — Compression / wisdom density
R — Phase transition / justified regime change
Q — Free will / invitation vs coercion
F — Cross-context binding
C — Integration / whole-system coherence

For each channel score v_pos (0-1), v_neg (0-1), effective_score = v_pos*(1-v_neg).
gradient_direction: +1 (more coherent under pressure), 0 (stable), -1 (decays).

Run pressure states: static, compression, strongest_objection, time, translation,
evidence, implementation, fruit, falsification, hostile_misuse.

Fruit pressure: if believed and lived, does it tend toward Love/Joy/Peace/Patience/
Kindness/Goodness/Faithfulness/Gentleness/Self-Control — or their opposites?

Return ONLY valid JSON. No markdown, no explanation outside JSON."""

USER_TEMPLATE = """Evaluate this claim using χ-Evaluator v2.

CLAIM:
{claim}

Return strict JSON matching the required schema. Be strict — agreement with a claim
does not excuse coercion, self-contradiction, or inability to compress."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def create_config_xlsx():
    """Create a template config.xlsx on first run."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return False

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Settings"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E79")
    key_fill    = PatternFill("solid", fgColor="D6E4F0")

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 50

    ws.append(["Setting", "Value", "Description"])
    for cell in ws[1]:
        cell.font  = header_font
        cell.fill  = header_fill
        cell.alignment = Alignment(horizontal="center")

    settings = [
        ("OPENAI_API_KEY",         "",               "Your OpenAI API key (sk-proj-...)"),
        ("OPENAI_MODEL",           "o3",             "Model: o3, gpt-4o, etc."),
        ("OPENAI_MAX_TOKENS",      "8000",           "Max completion tokens for OpenAI"),
        ("RUN_OPENAI",             "TRUE",           "TRUE to run claims against OpenAI"),
        ("DEEPSEEK_API_KEY",       "",               "Your DeepSeek API key (sk-...)"),
        ("DEEPSEEK_MODEL",         "deepseek-chat",  "deepseek-chat or deepseek-reasoner"),
        ("DEEPSEEK_MAX_TOKENS",    "4096",           "Max tokens for DeepSeek"),
        ("RUN_DEEPSEEK",           "TRUE",           "TRUE to run claims against DeepSeek"),
        ("TEMPERATURE",            "0.3",            "Temperature (ignored for o3/o1 models)"),
        ("CHI_THRESHOLD_COHERENT", "0.50",           "χ above this = coherent verdict"),
        ("CHI_THRESHOLD_FRAGILE",  "0.10",           "χ below this = fragile/collapsed"),
        ("FRUIT_BETA",             "4.0",            "β in Φᵢ(χ) = tanh(β(χ − χ_c))"),
        ("FRUIT_CHI_C",            "0.30",           "χ_c threshold — below this, anti-Fruits dominate"),
        ("ARCHIVE_INBOX",          "TRUE",           "TRUE to move processed files to INBOX/processed/"),
    ]

    for row in settings:
        ws.append(row)
        ws.cell(ws.max_row, 1).fill = key_fill
        ws.cell(ws.max_row, 1).font = Font(bold=True)

    # README sheet
    ws2 = wb.create_sheet("README")
    ws2.column_dimensions["A"].width = 80
    notes = [
        "χ-Evaluator v2 — Configuration",
        "",
        "HOW TO USE:",
        "1. Fill in OPENAI_API_KEY and/or DEEPSEEK_API_KEY in the Settings sheet.",
        "2. Drop .txt files into the INBOX folder.",
        "   One claim per line, or the whole file = one claim.",
        "   Lines starting with # are ignored.",
        "3. Double-click START.bat to run.",
        "4. Results appear in OUTBOX/ as .json and .md files.",
        "",
        "CLAIM FILE FORMATS:",
        "  Single claim:   Just type the claim. The whole file = one claim.",
        "  Multiple claims: One claim per line. Blank lines are skipped.",
        "",
        "OUTPUT:",
        "  claimname_TIMESTAMP_openai.json  — full scored JSON (OpenAI)",
        "  claimname_TIMESTAMP_openai.md    — human-readable report (OpenAI)",
        "  claimname_TIMESTAMP_deepseek.json — same for DeepSeek",
        "  claimname_TIMESTAMP_deepseek.md",
        "",
        "VERDICT MEANINGS:",
        "  coherent           — χ > 0.50, survives pressure",
        "  partially coherent — χ between 0.10 and 0.50",
        "  fragile            — χ between 0.01 and 0.10",
        "  high-signal deception — passes E but fails Q, K, or T",
        "  repairable         — zero channel but not from fatal failure mode",
        "  collapsed          — zero channel from coercion/contradiction/circular logic",
    ]
    for note in notes:
        ws2.append([note])

    wb.save(CONFIG_XL)
    print(f"  Created config.xlsx — open it and fill in your API keys, then run again.")
    return True


def read_config_xlsx() -> dict:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(CONFIG_XL, data_only=True)
        ws = wb["Settings"]
        cfg = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1] is not None:
                cfg[str(row[0]).strip()] = str(row[1]).strip()
        return cfg
    except Exception as e:
        print(f"  [WARNING] Could not read config.xlsx: {e}")
        return {}


def read_config_txt() -> dict:
    cfg = {}
    if not CONFIG_TXT.exists():
        return cfg
    for line in CONFIG_TXT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip()
    return cfg


def load_config() -> dict:
    if CONFIG_XL.exists():
        cfg = read_config_xlsx()
        if cfg:
            return cfg
    return read_config_txt()


def cfg_bool(cfg: dict, key: str, default: bool = True) -> bool:
    v = cfg.get(key, str(default)).upper()
    return v in {"TRUE", "1", "YES", "ON"}


def cfg_float(cfg: dict, key: str, default: float) -> float:
    try:
        return float(cfg.get(key, default))
    except (TypeError, ValueError):
        return default


def cfg_int(cfg: dict, key: str, default: int) -> int:
    try:
        return int(float(cfg.get(key, default)))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def is_o3(model: str) -> bool:
    return model.startswith("o3") or model.startswith("o1")


def call_openai(cfg: dict, claim: str) -> tuple[str, dict]:
    import openai

    api_key    = cfg.get("OPENAI_API_KEY", "")
    model      = cfg.get("OPENAI_MODEL", "o3")
    max_tokens = cfg_int(cfg, "OPENAI_MAX_TOKENS", 8000)

    client = openai.OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_TEMPLATE.format(claim=claim)},
    ]

    kwargs = {
        "model":    model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }

    if is_o3(model):
        kwargs["max_completion_tokens"] = max_tokens
    else:
        kwargs["max_tokens"]  = max_tokens
        kwargs["temperature"] = cfg_float(cfg, "TEMPERATURE", 0.3)

    t0 = time.time()
    resp = client.chat.completions.create(**kwargs)
    elapsed = time.time() - t0

    usage = {}
    if resp.usage:
        usage = {
            "prompt_tokens":     resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "elapsed_s":         round(elapsed, 2),
            "model":             model,
        }

    return resp.choices[0].message.content, usage


def call_deepseek(cfg: dict, claim: str) -> tuple[str, dict]:
    import openai

    api_key    = cfg.get("DEEPSEEK_API_KEY", "")
    model      = cfg.get("DEEPSEEK_MODEL", "deepseek-chat")
    max_tokens = cfg_int(cfg, "DEEPSEEK_MAX_TOKENS", 4096)
    temperature = cfg_float(cfg, "TEMPERATURE", 0.3)

    client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_TEMPLATE.format(claim=claim)},
    ]

    t0 = time.time()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
        temperature=temperature,
    )
    elapsed = time.time() - t0

    usage = {}
    if resp.usage:
        usage = {
            "prompt_tokens":     resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "elapsed_s":         round(elapsed, 2),
            "model":             model,
        }

    return resp.choices[0].message.content, usage


# ---------------------------------------------------------------------------
# Claim parsing
# ---------------------------------------------------------------------------

def extract_claims(text: str) -> list[str]:
    """One claim per line, or whole file treated as a single document."""
    lines = [l.strip() for l in text.splitlines()]
    content_lines = [l for l in lines if l and not l.startswith("#")]

    if not content_lines:
        return []

    if len(content_lines) == 1:
        return [content_lines[0]]

    # Documents (> 20 non-header lines, or avg line > 120 chars) → one block
    avg_len = sum(len(l) for l in content_lines) / len(content_lines)
    if len(content_lines) > 20 or avg_len > 120:
        return [text.strip()]

    return content_lines


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_result(ev, usage: dict, run_dir: pathlib.Path, stem: str, model_label: str):
    from chi_engine import asdict
    ts = datetime.datetime.now().strftime("%H%M%S")

    out = {
        "evaluation":  json.loads(ev.to_json()),
        "usage":       usage,
        "model_label": model_label,
    }

    json_path = run_dir / f"{stem}_{model_label}.json"
    md_path   = run_dir / f"{stem}_{model_label}.md"

    json_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(ev.to_markdown(model_label), encoding="utf-8")

    return json_path, md_path


def print_summary(ev, model_label: str):
    v = ev.verdict.upper()
    zeros = ", ".join(ev.zero_channels) if ev.zero_channels else "none"
    print(f"    Verdict  : {v}")
    print(f"    χ prod   : {ev.static_chi:.6f}   geo-mean: {ev.geo_mean:.4f}   gradient: {ev.gradient}")
    print(f"    Zero ch  : {zeros}")
    print(f"    Weakest  : {', '.join(ev.weakest_channels)}")
    print(f"    Fruit    : {ev.fruit_output.fruit_score:.3f}  "
          f"({', '.join(ev.fruit_output.dominant_fruits) or 'none'})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    from chi_engine import parse_model_json

    # Ensure config exists
    if not CONFIG_XL.exists() and not CONFIG_TXT.exists():
        print()
        print("  First run — creating config.xlsx...")
        try:
            import openpyxl
            create_config_xlsx()
        except ImportError:
            # Write a plain config.txt instead
            CONFIG_TXT.write_text(
                "OPENAI_API_KEY=\nOPENAI_MODEL=o3\nOPENAI_MAX_TOKENS=8000\n"
                "RUN_OPENAI=TRUE\nDEEPSEEK_API_KEY=\nDEEPSEEK_MODEL=deepseek-chat\n"
                "DEEPSEEK_MAX_TOKENS=4096\nRUN_DEEPSEEK=TRUE\nTEMPERATURE=0.3\n"
                "FRUIT_BETA=4.0\nFRUIT_CHI_C=0.30\nARCHIVE_INBOX=TRUE\n",
                encoding="utf-8"
            )
            print("  Created config.txt — fill in API keys, then run again.")
        sys.exit(0)

    cfg = load_config()

    run_openai   = cfg_bool(cfg, "RUN_OPENAI",   True)
    run_deepseek = cfg_bool(cfg, "RUN_DEEPSEEK", True)
    archive      = cfg_bool(cfg, "ARCHIVE_INBOX", True)

    oa_key = cfg.get("OPENAI_API_KEY",   "")
    ds_key = cfg.get("DEEPSEEK_API_KEY", "")

    if run_openai and not oa_key:
        print("  [WARNING] RUN_OPENAI=TRUE but OPENAI_API_KEY is empty — skipping OpenAI.")
        run_openai = False
    if run_deepseek and not ds_key:
        print("  [WARNING] RUN_DEEPSEEK=TRUE but DEEPSEEK_API_KEY is empty — skipping DeepSeek.")
        run_deepseek = False

    if not run_openai and not run_deepseek:
        sys.exit("ERROR: No API keys set. Fill in config.xlsx (or config.txt) and run again.")

    INBOX_DIR.mkdir(exist_ok=True)
    OUTBOX_DIR.mkdir(exist_ok=True)
    processed_dir = INBOX_DIR / "processed"

    inbox_files = sorted(INBOX_DIR.glob("*.txt"))
    if not inbox_files:
        print("  No .txt files in INBOX. Drop claim files there and run again.")
        sys.exit(0)

    print()
    print("=" * 60)
    print("  χ-EVALUATOR v2")
    print("=" * 60)
    print(f"  OpenAI   : {cfg.get('OPENAI_MODEL','—') if run_openai else 'disabled'}")
    print(f"  DeepSeek : {cfg.get('DEEPSEEK_MODEL','—') if run_deepseek else 'disabled'}")
    print(f"  Files    : {len(inbox_files)}")

    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTBOX_DIR / f"run_{ts}"
    run_dir.mkdir(exist_ok=True)
    print(f"  Output   : {run_dir}")

    total_claims = 0
    total_cost   = 0.0

    for inbox_file in inbox_files:
        text   = inbox_file.read_text(encoding="utf-8", errors="replace")
        claims = extract_claims(text)
        if not claims:
            print(f"\n  [SKIP] {inbox_file.name} — no claims found")
            continue

        print(f"\n  ── {inbox_file.name}  ({len(claims)} claim(s)) ──")

        for i, claim in enumerate(claims, 1):
            if len(claims) > 1:
                print(f"\n    Claim {i}: {claim[:80]}...")
            else:
                print(f"\n    {claim[:100]}...")

            stem = f"{inbox_file.stem}_claim{i:02d}" if len(claims) > 1 else inbox_file.stem
            collected_evs = {}   # model_label -> evaluation dict (for synthesis)

            # OpenAI
            if run_openai:
                model_label = cfg.get("OPENAI_MODEL", "openai")
                print(f"    [{model_label}] calling...")
                try:
                    raw, usage = call_openai(cfg, claim)
                    ev = parse_model_json(raw)
                    if ev:
                        if not ev.claim:
                            ev.claim = claim
                        if not ev.compressed_claim:
                            ev.compressed_claim = (claim[:120] + "…") if len(claim) > 120 else claim
                        save_result(ev, usage, run_dir, stem, model_label)
                        print_summary(ev, model_label)
                        print(f"    Done {usage.get('elapsed_s','?')}s  "
                              f"in={usage.get('prompt_tokens','?')} "
                              f"out={usage.get('completion_tokens','?')}")
                        import json as _json
                        collected_evs[model_label] = _json.loads(ev.to_json())
                    else:
                        print(f"    [ERROR] Could not parse {model_label} response as χ-Evaluation JSON")
                        (run_dir / f"{stem}_{model_label}_raw.txt").write_text(raw, encoding="utf-8")
                except Exception as e:
                    print(f"    [ERROR] OpenAI: {e}")

            # DeepSeek
            if run_deepseek:
                model_label = cfg.get("DEEPSEEK_MODEL", "deepseek")
                print(f"    [{model_label}] calling...")
                try:
                    raw, usage = call_deepseek(cfg, claim)
                    ev = parse_model_json(raw)
                    if ev:
                        if not ev.claim:
                            ev.claim = claim
                        if not ev.compressed_claim:
                            ev.compressed_claim = (claim[:120] + "…") if len(claim) > 120 else claim
                        save_result(ev, usage, run_dir, stem, model_label)
                        print_summary(ev, model_label)
                        print(f"    Done {usage.get('elapsed_s','?')}s  "
                              f"in={usage.get('prompt_tokens','?')} "
                              f"out={usage.get('completion_tokens','?')}")
                        import json as _json
                        collected_evs[model_label] = _json.loads(ev.to_json())
                    else:
                        print(f"    [ERROR] Could not parse {model_label} response")
                        (run_dir / f"{stem}_{model_label}_raw.txt").write_text(raw, encoding="utf-8")
                except Exception as e:
                    print(f"    [ERROR] DeepSeek: {e}")

            # Synthesize statements from both model evaluations
            if collected_evs:
                print(f"    [synthesis] generating Fruit-anchored statements...")
                try:
                    from synthesize_statements import synthesize
                    stmts = synthesize(claim, collected_evs, cfg)
                    if stmts:
                        stmts_path = run_dir / f"{stem}_statements.json"
                        stmts_path.write_text(
                            _json.dumps({"claim": claim, "statements": stmts}, indent=2,
                                        ensure_ascii=False),
                            encoding="utf-8"
                        )
                        # Also write a clean .md for quick reading
                        md_path = run_dir / f"{stem}_statements.md"
                        md_lines = [
                            f"# Synthesized Statements",
                            f"",
                            f"**Claim:** {claim[:200]}",
                            f"",
                            f"## One-Liner",
                            stmts.get("one_liner", ""),
                            f"",
                            f"## Formal Scientific",
                            stmts.get("formal_scientific", ""),
                            f"",
                            f"## Theological Narrative",
                            stmts.get("theological_narrative", ""),
                            f"",
                            f"## Cross-Model Comparison",
                            stmts.get("cross_model_comparison", ""),
                        ]
                        md_path.write_text("\n".join(md_lines), encoding="utf-8")
                except Exception as e:
                    print(f"    [synthesis] failed: {e}")

            total_claims += 1

        # Archive processed file
        if archive:
            processed_dir.mkdir(exist_ok=True)
            dest = processed_dir / inbox_file.name
            if dest.exists():
                dest = processed_dir / f"{inbox_file.stem}_{ts}{inbox_file.suffix}"
            inbox_file.rename(dest)

    # Generate HTML report
    try:
        from report_html import generate_run_report
        html_path = generate_run_report(run_dir)
        if html_path:
            print(f"          HTML            : {html_path}")
    except Exception as e:
        print(f"  [WARNING] HTML generation failed: {e}")

    print()
    print("=" * 60)
    print(f"  Done.   Claims processed : {total_claims}")
    print(f"          Output           : {run_dir}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
