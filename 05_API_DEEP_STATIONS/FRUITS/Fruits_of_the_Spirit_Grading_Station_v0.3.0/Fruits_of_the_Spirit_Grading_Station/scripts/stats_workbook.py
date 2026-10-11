"""stats_workbook.py -- Excel export for the Fruits of the Spirit pipeline.

Reads grading_out/<paper>.stats.json + <paper>.lexicon.json (+
<paper>.spans.json when present) and writes grading_out/<paper>.stats.xlsx --
"the Excel of all the statistics".

Sheets:
  Summary        in_report stats, formatted
  All_Statistics every stat key/value/unit/note/in_report
  Per_Sentence   one row per sentence: idx, excerpt, word count, per-category
                 hits + weighted scores, claim-strength counts
  Fruit_Profile  nine axes x (lexicon hits, span signals +/- and enacted/about)
  Spikes         top spikes per category with sentence refs and excerpts
  Spans          span table (role, flags, confidence, uncertainty) when spans exist

Inputs:
  --paper  Path to the graded paper (used to locate the grading_out JSONs).
"""

import argparse
import json
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding="utf-8")

STATION_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = STATION_DIR / "grading_out"

CATEGORIES = ["fruit", "anti_fruit", "grounding", "contradiction", "jargon", "propaganda", "archetype"]
CLAIM_KEYS = ["weak", "moderate", "strong", "forbidden"]
FRUIT_AXES = ["love", "joy", "peace", "patience", "kindness",
              "goodness", "faithfulness", "gentleness", "self_control"]

HDR_FILL = PatternFill("solid", fgColor="141923")
HDR_FONT = Font(color="D9A94A", bold=True)
WRAP = Alignment(vertical="top", wrap_text=True)


def fmt_value(v):
    if isinstance(v, list):
        return json.dumps(v, ensure_ascii=False)
    if v is None:
        return "n/a"
    return v


def style_sheet(ws, widths, wrap_cols=()):
    for cell in ws[1]:
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for col in wrap_cols:
        for row in ws.iter_rows(min_row=2, min_col=col, max_col=col):
            for c in row:
                c.alignment = WRAP
    ws.freeze_panes = "A2"


def main():
    ap = argparse.ArgumentParser(description="Excel export of pipeline statistics.")
    ap.add_argument("--paper", required=True, help="Path to the graded paper.")
    args = ap.parse_args()

    stem = Path(args.paper).stem
    stats_path = OUT_DIR / f"{stem}.stats.json"
    lex_path = OUT_DIR / f"{stem}.lexicon.json"
    spans_path = OUT_DIR / f"{stem}.spans.json"
    for p in (stats_path, lex_path):
        if not p.exists():
            sys.exit(f"ERROR: missing {p} -- run lexicon_pass.py and stats_engine.py first.")
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    lex = json.loads(lex_path.read_text(encoding="utf-8"))
    spans_doc = json.loads(spans_path.read_text(encoding="utf-8")) if spans_path.exists() else None

    stat_by_key = {s["key"]: s for s in stats["stats"]}

    wb = openpyxl.Workbook()

    # --- Summary ------------------------------------------------------------
    ws = wb.active
    ws.title = "Summary"
    ws.append(["key", "value", "unit", "note"])
    for s in stats["stats"]:
        if s["in_report"]:
            ws.append([s["key"], fmt_value(s["value"]), s["unit"], s["note"]])
    style_sheet(ws, [38, 60, 16, 70], wrap_cols=(2, 4))

    # --- All_Statistics -----------------------------------------------------
    ws = wb.create_sheet("All_Statistics")
    ws.append(["key", "value", "unit", "note", "in_report"])
    for s in stats["stats"]:
        ws.append([s["key"], fmt_value(s["value"]), s["unit"], s["note"], s["in_report"]])
    style_sheet(ws, [42, 60, 16, 70, 10], wrap_cols=(2, 4))

    # --- Per_Sentence ---------------------------------------------------------
    ws = wb.create_sheet("Per_Sentence")
    header = ["idx", "excerpt", "word_count"]
    for c in CATEGORIES:
        header += [f"{c}_hits", f"{c}_weighted"]
    header += [f"claim_{k}" for k in CLAIM_KEYS] + ["hedges", "absolutes"]
    ws.append(header)
    for s in lex["sentences"]:
        row = [s["idx"], s["text"][:120].replace("\n", " "), s["word_count"]]
        for c in CATEGORIES:
            row += [s["categories"][c]["hits"], s["categories"][c]["weighted_score"]]
        row += [s["claim_strength"][k] for k in CLAIM_KEYS]
        row += [s["hedges"], s["absolutes"]]
        ws.append(row)
    style_sheet(ws, [6, 80, 10] + [8] * (len(header) - 3), wrap_cols=(2,))

    # --- Fruit_Profile ---------------------------------------------------------
    ws = wb.create_sheet("Fruit_Profile")
    ws.append(["axis", "lexicon_hits",
               "span_signals_+", "span_signals_-",
               "enacted_+", "enacted_-", "about_+", "about_-"])
    profile = {a: {"+": 0, "-": 0, "enacted+": 0, "enacted-": 0, "about+": 0, "about-": 0}
               for a in FRUIT_AXES}
    if spans_doc:
        for sp in spans_doc["spans"]:
            if sp["status"] != "ok":
                continue
            for fs in sp["judgment"]["fruit_signals"]:
                axis = fs.get("fruit_id", "").replace("fruit.", "")
                if axis not in profile:
                    continue
                pol = fs.get("polarity", "+")
                kind = fs.get("polarity_kind", "about")
                profile[axis][pol] += 1
                profile[axis][f"{kind}{pol}"] += 1
    for a in FRUIT_AXES:
        lex_hits = stat_by_key.get(f"fruit_axis.{a}.total", {}).get("value", 0)
        p = profile[a]
        ws.append([a, lex_hits, p["+"], p["-"],
                   p["enacted+"], p["enacted-"], p["about+"], p["about-"]])
    style_sheet(ws, [16, 13, 14, 14, 10, 10, 10, 10])

    # --- Spikes ---------------------------------------------------------------
    ws = wb.create_sheet("Spikes")
    ws.append(["category", "rank", "sentence_idx", "z_score", "hits", "excerpt"])
    for c in CATEGORIES:
        top = stat_by_key.get(f"spikes.{c}.top5", {}).get("value", [])
        for rank, sp in enumerate(top, start=1):
            ws.append([c, rank, sp["sentence_idx"], sp["z"], sp["hits"], sp["excerpt"]])
    style_sheet(ws, [14, 6, 12, 10, 8, 100], wrap_cols=(6,))

    # --- Spans ------------------------------------------------------------------
    if spans_doc:
        ws = wb.create_sheet("Spans")
        ws.append(["span_id", "sent_range", "role", "fruit_signals",
                   "gate_flags", "veto_flags", "counterfeit_suspect",
                   "confidence", "uncertainty_note"])
        for sp in spans_doc["spans"]:
            if sp["status"] != "ok":
                ws.append([sp["span_id"], f"s{sp['sent_idx_start']}-{sp['sent_idx_end']}",
                           "INVALID", "", "", "", "", "", sp.get("error", "")])
                continue
            j = sp["judgment"]
            sig = "; ".join(
                f"{fs['fruit_id'].replace('fruit.', '')} {fs['polarity']}"
                f"({fs.get('polarity_kind', '?')},s{fs['strength']})"
                for fs in j["fruit_signals"])
            ws.append([sp["span_id"], f"s{sp['sent_idx_start']}-{sp['sent_idx_end']}",
                       j["role"], sig, ", ".join(j["gate_flags"]),
                       ", ".join(j["veto_flags"]), j["counterfeit_suspect"],
                       j["confidence"], j["uncertainty_note"]])
        style_sheet(ws, [8, 12, 12, 46, 40, 40, 12, 11, 80], wrap_cols=(4, 5, 6, 9))

    out_path = OUT_DIR / f"{stem}.stats.xlsx"
    wb.save(out_path)
    print(f"[xlsx] wrote {out_path} "
          f"({len(wb.sheetnames)} sheets: {', '.join(wb.sheetnames)})")


if __name__ == "__main__":
    main()
