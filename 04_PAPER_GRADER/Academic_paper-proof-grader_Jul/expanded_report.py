from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape
from pathlib import Path


HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8-sig"))
OUTPUT = Path(CFG["output_dir"])
REPORT_DIR = OUTPUT / "expanded_reports"


def pct(part: int, whole: int) -> int:
    if whole <= 0:
        return 0
    return round((part / whole) * 100)


def load_reports() -> list[dict]:
    reports = []
    for path in sorted(OUTPUT.glob("GTQ_*.paper-grade.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_json_path"] = str(path)
        reports.append(data)
    return reports


def claim_stats(claims: list[dict]) -> dict:
    total = len(claims)
    evidence = sum(1 for c in claims if not c.get("evidence_bar", "").startswith("No explicit"))
    falsifiable = sum(1 for c in claims if c.get("Q5_falsifiability") == "present")
    bounded = sum(1 for c in claims if c.get("Q6_boundary") == "present")
    high_risk = sum(1 for c in claims if c.get("Q7_listener_risk") == "high")
    avg_maturity = 0.0
    if total:
        avg_maturity = sum(int(c.get("claim_maturity_level", 0)) for c in claims) / total
    return {
        "claim_count": total,
        "evidence_count": evidence,
        "evidence_pct": pct(evidence, total),
        "falsifiable_count": falsifiable,
        "falsifiable_pct": pct(falsifiable, total),
        "boundary_count": bounded,
        "boundary_pct": pct(bounded, total),
        "high_risk_count": high_risk,
        "avg_maturity": avg_maturity,
    }


def grade_label(stats: dict, metrics: dict) -> tuple[str, int]:
    score = 50
    score += min(15, metrics.get("equation_count", 0) // 4)
    score += min(15, stats["evidence_pct"] // 5)
    score += min(10, stats["falsifiable_pct"] // 8)
    score += min(10, stats["boundary_pct"] // 10)
    score -= min(20, stats["high_risk_count"] * 4)
    score = max(0, min(100, score))
    if score >= 85:
        return "Strong release candidate", score
    if score >= 70:
        return "Promising with repair targets", score
    if score >= 55:
        return "Useful draft, needs reviewer hardening", score
    return "High-risk draft, needs structural repair", score


def top_claims(claims: list[dict], limit: int = 8) -> list[dict]:
    return sorted(
        claims,
        key=lambda c: (
            int(c.get("claim_maturity_level", 0)),
            1 if not c.get("evidence_bar", "").startswith("No explicit") else 0,
        ),
        reverse=True,
    )[:limit]


def weak_claims(claims: list[dict], limit: int = 8) -> list[dict]:
    return sorted(
        claims,
        key=lambda c: (
            c.get("Q5_falsifiability") != "present",
            c.get("Q6_boundary") != "present",
            c.get("evidence_bar", "").startswith("No explicit"),
            int(c.get("claim_maturity_level", 0)),
        ),
        reverse=True,
    )[:limit]


def compact(text: str, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def md_report(data: dict) -> str:
    metrics = data["metrics"]
    claims = data.get("claims", [])
    stats = claim_stats(claims)
    label, score = grade_label(stats, metrics)
    strongest = top_claims(claims)
    weakest = weak_claims(claims)

    lines = [
        f"# Expanded Paper Review - {data['paper_id']}",
        "",
        "## 1. Executive Verdict",
        "",
        f"Overall rating: **{score}/100 - {label}**.",
        "",
        (
            f"This article contains {metrics['word_count']} words, {metrics['section_count']} sections, "
            f"{metrics['equation_count']} equation candidates, and {stats['claim_count']} extracted claim candidates. "
            f"The current grader sees an average claim maturity of {stats['avg_maturity']:.2f}/7. "
            "This is a structural review, not a final truth judgment."
        ),
        "",
        "The main editorial question is whether the article's strongest claims are framed at the same level as their support. "
        "When the article speaks in formal or empirical language, it needs either direct evidence, a stated boundary, "
        "or a clean kill condition. Where those are absent, the piece may still be valuable, but it should be labeled as "
        "model, analogy, or structural correspondence rather than proof.",
        "",
        "## 2. Score Dashboard",
        "",
        f"- Evidence-linked claims: {stats['evidence_count']}/{stats['claim_count']} ({stats['evidence_pct']}%)",
        f"- Falsifiability / prediction language present: {stats['falsifiable_count']}/{stats['claim_count']} ({stats['falsifiable_pct']}%)",
        f"- Explicit boundary language present: {stats['boundary_count']}/{stats['claim_count']} ({stats['boundary_pct']}%)",
        f"- High listener-risk claims: {stats['high_risk_count']}",
        f"- Equation density: {metrics['equation_count']} equation candidates across {metrics['word_count']} words",
        f"- Top lexical handles: {metrics['top_terms']}",
        "",
        "## 3. Claim Architecture",
        "",
        "The claim architecture is the real load-bearing layer. The article is strongest when it states a concrete mapping, "
        "names the mechanism, and admits what would break it. It weakens when a suggestive pattern is voiced as if the "
        "reader has already granted the full framework.",
        "",
    ]

    for idx, claim in enumerate(strongest, 1):
        lines.extend(
            [
                f"### Strong Claim {idx}",
                "",
                f"Section: {claim.get('section', 'Unknown')}",
                "",
                f"> {compact(claim.get('one_sentence_claim', ''))}",
                "",
                f"Maturity: {claim.get('claim_maturity_level')} - {claim.get('claim_maturity_label')}",
                f"Evidence: {claim.get('evidence_bar')}",
                f"Boundary: {claim.get('proof_boundary')}",
                "",
            ]
        )

    lines.extend(
        [
            "## 4. Weakest Links / Repair Targets",
            "",
            "These are not automatic failures. They are the places a hostile reader can push hardest. "
            "The repair is usually simple: add a boundary sentence, add a concrete falsification condition, "
            "or downgrade the claim from proof-language to model-language.",
            "",
        ]
    )
    for idx, claim in enumerate(weakest, 1):
        lines.extend(
            [
                f"### Repair Target {idx}",
                "",
                f"Section: {claim.get('section', 'Unknown')}",
                "",
                f"> {compact(claim.get('one_sentence_claim', ''))}",
                "",
                f"Kill condition: {claim.get('kill_conditions')}",
                f"Not claimed: {claim.get('not_claimed')}",
                "",
            ]
        )

    lines.extend(
        [
            "## 5. Reviewer Attack Surface",
            "",
            "A serious reviewer will not usually attack the whole article at once. They will isolate one overstrong bridge "
            "between domains and ask whether the bridge is derivation, structural isomorphism, analogy, or rhetoric. "
            "That is the key audit axis. The article should survive by making those levels visible.",
            "",
            "Primary attacks to expect:",
            "",
            "- The equations are present but may not yet constrain the theological interpretation.",
            "- Some claims have no explicit evidence marker in the extracted sentence.",
            "- Several claims need kill conditions precise enough to let the framework lose.",
            "- If a claim says or implies formal proof, the report should point to the exact formal artifact.",
            "",
            "## 6. Recommended Revision Pass",
            "",
            "Recommended pass order:",
            "",
            "1. Keep the article's main argument intact.",
            "2. Add one boundary sentence near each high-maturity claim that lacks evidence.",
            "3. Add a short falsification clause for the central mapping.",
            "4. Mark each cross-domain bridge as derivation, isomorphism, analogy, or narrative framing.",
            "5. Preserve strong claims only where the article can show the supporting chain.",
            "",
            "## 7. Output Status",
            "",
            f"Generated from `{data['_json_path']}` at {datetime.now().isoformat(timespec='seconds')}.",
            "This expanded review is derived from the deterministic paper-grade JSON and should be treated as a reader-facing audit layer.",
            "",
        ]
    )
    return "\n".join(lines)


def html_report(data: dict, markdown: str) -> str:
    body = escape(markdown)
    body = re.sub(r"^# (.*)$", r"<h1>\1</h1>", body, flags=re.MULTILINE)
    body = re.sub(r"^## (.*)$", r"<h2>\1</h2>", body, flags=re.MULTILINE)
    body = re.sub(r"^### (.*)$", r"<h3>\1</h3>", body, flags=re.MULTILINE)
    body = re.sub(r"^\- (.*)$", r"<li>\1</li>", body, flags=re.MULTILINE)
    body = re.sub(r"^&gt; (.*)$", r"<blockquote>\1</blockquote>", body, flags=re.MULTILINE)
    body = body.replace("\n\n", "</p><p>")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Expanded Paper Review - {escape(data['paper_id'])}</title>
<style>
body {{ margin:0; background:#111; color:#eee; font-family: Georgia, serif; line-height:1.65; }}
main {{ max-width: 920px; margin:0 auto; padding:48px 28px; }}
h1,h2,h3 {{ color:#d7b46a; line-height:1.2; }}
h1 {{ font-size:2.2rem; }}
h2 {{ margin-top:2.2rem; border-top:1px solid #4a3d21; padding-top:1.2rem; }}
blockquote {{ border-left:4px solid #d7b46a; margin:1rem 0; padding:0.8rem 1rem; background:#1a1711; }}
li {{ margin:0.3rem 0 0.3rem 1.2rem; }}
p {{ margin:1rem 0; }}
</style>
</head>
<body><main><p>{body}</p></main></body>
</html>
"""


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    reports = load_reports()
    index_rows = []
    for data in reports:
        markdown = md_report(data)
        stem = data["paper_id"]
        md_path = REPORT_DIR / f"{stem}.expanded-review.md"
        html_path = REPORT_DIR / f"{stem}.expanded-review.html"
        md_path.write_text(markdown, encoding="utf-8")
        html_path.write_text(html_report(data, markdown), encoding="utf-8")
        stats = claim_stats(data.get("claims", []))
        label, score = grade_label(stats, data["metrics"])
        index_rows.append((stem, score, label, md_path.name, html_path.name))

    index = ["# Expanded GTQ Review Index", ""]
    for stem, score, label, md_name, html_name in index_rows:
        index.append(f"- {stem}: {score}/100 - {label} | `{md_name}` | `{html_name}`")
    (REPORT_DIR / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"expanded reports written: {len(reports)}")
    print(REPORT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
