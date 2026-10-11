"""Triage rules for 10_CKG_THEOLOGY, enforced in code (the model proposes, this decides).

1. Default CLEAN: any verdict other than CLEAN / ?? without a timestamp becomes NOTE.
2. At most three FLAGs. Candidates are ranked: Warrant (2), Doctrine tier (3) and Opponent (9) first,
   then severity, then row order. The rest become NOTE, marked "dropped by cap".
3. Rows 16 and 17 never compete for a slot, and CLAIMs never count toward the cap.
   A hit on row 17 is always CLAIM.
4. Rows 5 and 6 (church history) cannot be CLAIM: they stay FLAG at most and are marked verify.
5. Row 15 without acquired comments is ?? ("no comments acquired").
6. Row 13: collapse_question is its own required field; the row is FLAG only when the speaker steers around it.
7. Platform probes are notes: never FLAG.
8. Kept CLAIM rows are appended to the argument layer as claims (source "rubric row N").
"""
from __future__ import annotations

import re
from typing import Any

VERDICTS = ("CLEAN", "NOTE", "FLAG", "CLAIM", "??")
PRIORITY_ROWS = (2, 3, 9)
CAP_EXEMPT = (16, 17)
HISTORY_ROWS = (5, 6)
MAX_FLAGS = 3
TS = re.compile(r"\d{1,2}:\d{2}")


def load_rubric(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4 and parts[0].isdigit():
            rows.append({"row": int(parts[0]), "probe": parts[1], "question": parts[2], "expands_when": parts[3]})
    return rows


def _words(text: str, n: int = 12) -> str:
    words = str(text or "").split()
    return " ".join(words[:n]) + ("…" if len(words) > n else "")


def enforce(reply: dict, rubric: list[dict], comments_available: bool) -> dict[str, Any]:
    """Apply the rules to a model reply. Returns rows (one per rubric probe), kept expansions and a change log."""
    by_row: dict[int, dict] = {}
    for r in reply.get("rubric", []) or []:
        try:
            by_row[int(r.get("row"))] = r
        except (TypeError, ValueError):
            continue
    log: list[str] = []
    rows: list[dict] = []
    for spec in rubric:
        n = spec["row"]
        r = by_row.get(n, {})
        verdict = str(r.get("verdict", "??")).upper().strip()
        if verdict not in VERDICTS:
            log.append(f"row {n}: unknown verdict '{verdict}' -> ??")
            verdict = "??"
        if n not in by_row:
            log.append(f"row {n}: missing from reply -> ??")
        row = {"row": n, "probe": spec["probe"], "verdict": verdict, "line": _words(r.get("line", "")),
               "severity": _num(r.get("severity")), "timestamp": str(r.get("timestamp") or ""),
               "expansion": str(r.get("expansion") or ""), "mode": str(r.get("mode") or ""),
               "verify": bool(r.get("verify")), "note": ""}
        if n == 15 and not comments_available:
            row.update(verdict="??", line="no comments acquired", expansion="", note="rule 5")
        if n == 17 and row["verdict"] in ("NOTE", "FLAG"):
            row["verdict"] = "CLAIM"
            log.append("row 17: a hit on Unexplained-right is always CLAIM")
        if n in HISTORY_ROWS:
            row["verify"] = True
            if row["verdict"] == "CLAIM":
                row["verdict"] = "FLAG"
                row["note"] = "history is a lead to verify, not a claim"
                log.append(f"row {n}: CLAIM -> FLAG (church history must be verified first)")
        if n == 13:
            steers = bool(reply.get("steers_around"))
            if row["verdict"] in ("FLAG", "CLAIM") and not steers:
                row["verdict"] = "NOTE"
                log.append("row 13: FLAG only when the speaker steers around the collapse question")
            if not row["line"]:
                row["line"] = _words(reply.get("collapse_question", ""))
        if row["verdict"] in ("NOTE", "FLAG", "CLAIM") and not TS.search(row["timestamp"]) and n != 15:
            if row["verdict"] != "NOTE":
                log.append(f"row {n}: {row['verdict']} without a timestamp -> NOTE")
                row["note"] = "no timestamp given"
            row["verdict"] = "NOTE"
        rows.append(row)

    # The cap: rows 16/17 exempt, CLAIMs never counted.
    flags = [r for r in rows if r["verdict"] == "FLAG" and r["row"] not in CAP_EXEMPT]
    flags.sort(key=lambda r: (r["row"] not in PRIORITY_ROWS, -r["severity"], r["row"]))
    for rank, r in enumerate(flags, 1):
        if rank > MAX_FLAGS:
            r["verdict"] = "NOTE"
            r["note"] = f"dropped by the cap (ranked {rank})"
            log.append(f"row {r['row']}: FLAG dropped by the three-flag cap (ranked {rank})")
    for r in rows:
        if r["verdict"] not in ("FLAG", "CLAIM"):
            r["expansion"] = ""
    return {"rows": rows, "log": log,
            "flags": [r["row"] for r in rows if r["verdict"] == "FLAG"],
            "claims": [r["row"] for r in rows if r["verdict"] == "CLAIM"],
            "unknown": [r["row"] for r in rows if r["verdict"] == "??"]}


def platform_notes(reply: dict, probe_names: list[str]) -> dict[str, str]:
    """Platform probes are one-line notes, whatever the model called them."""
    raw = reply.get("platform_probes") or {}
    out = {}
    for name in probe_names:
        value = raw.get(name, "")
        if isinstance(value, dict):
            value = value.get("line") or value.get("note") or ""
        out[name] = _words(value) or "??"
    return out


def claims_into_graph(argument_layer: dict, rows: list[dict]) -> dict:
    layer = {k: list(v) if isinstance(v, list) else v for k, v in (argument_layer or {}).items()}
    layer.setdefault("claims", [])
    for r in rows:
        if r["verdict"] == "CLAIM":
            layer["claims"].append({"id": f"RC{r['row']:02d}", "text": r["expansion"] or r["line"],
                                    "mode": r["mode"] or "CONJECTURE", "status": "UNRESOLVED",
                                    "source": f"rubric row {r['row']} ({r['probe']})", "timestamp": r["timestamp"]})
    return layer


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
