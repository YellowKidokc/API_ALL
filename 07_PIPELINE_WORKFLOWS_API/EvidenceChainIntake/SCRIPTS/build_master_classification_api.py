import csv
import os
import re
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
INTAKE_ROOT = SCRIPTS_DIR.parent
OUTBOX = INTAKE_ROOT / "OUTBOX"
CATEGORIZED = OUTBOX / "01_CATEGORIZED_DOMAINS"
CLASSIFICATIONS = OUTBOX / "02_CLASSIFICATIONS"
CLASSIFICATIONS.mkdir(parents=True, exist_ok=True)


def load_receipt_titles() -> dict[str, str]:
    titles = {}
    csv_file = OUTBOX / "SEMANTIC_RENAME_RECEIPT_20260903-115501.csv"
    if csv_file.exists():
        try:
            with open(csv_file, encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    old = row.get("old_name", "").strip()
                    title = row.get("title", "").strip()
                    if old and title:
                        titles[old] = title
        except Exception:
            pass
    return titles


RECEIPT_TITLES = load_receipt_titles()


def resolve_title(file_path: Path, content: str) -> str:
    if file_path.name in RECEIPT_TITLES:
        return RECEIPT_TITLES[file_path.name]

    # Try frontmatter title
    m = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", content, re.MULTILINE)
    raw = m.group(1).strip() if m else ""
    if raw and raw.lower() not in ("ckg_evaluation:", "untitled", "none") and not raw.startswith("paper_id:") and not raw.startswith("series:"):
        return raw

    # Try markdown headers
    headers = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)
    ignore_headers = {
        "ckg_evaluation:", "untitled", "intake assessment", "source outline", "at a glance",
        "central claim", "best concise argument", "system or model", "evidence chain",
        "best evidence and sources", "strongest objection and negative controls",
        "complete preserved source", "exact source - untouched"
    }
    for h in headers:
        h_clean = h.strip().strip("*_`\"' ")
        if h_clean.lower() not in ignore_headers and not h_clean.startswith("paper_id:") and not h_clean.startswith("series:"):
            # strip leading prefixes like "OK Thank you"
            h_clean = re.sub(r"^(?:ok\s+thank\s+you\s+)+", "", h_clean, flags=re.I).strip("#* ")
            if h_clean:
                return h_clean

    # Fallback to cleaned filename
    stem = file_path.stem.removesuffix(".knowledge").removesuffix(".epistemic")
    stem = re.sub(r"^\d+[\-_a-zA-Z0-9]*[\-_]", "", stem)
    stem = re.sub(r"[\-_]\d+[\-_]\d+$", "", stem)
    t = stem.replace("-", " ").replace("_", " ").title()
    return t or file_path.stem


# Parse metadata from files in 01_CATEGORIZED_DOMAINS
domains_data = {}
for domain_dir in sorted(CATEGORIZED.iterdir()):
    if not domain_dir.is_dir():
        continue
    domain_name = domain_dir.name
    files_list = []
    for file_path in sorted(domain_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in {".md", ".txt"}:
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = ""

        title = resolve_title(file_path, content)

        # Extract reuse recommendation / grade
        grade_match = re.search(r"reuse_grade:\s*[\"']?(.*?)[\"']?$", content, re.MULTILINE)
        grade = grade_match.group(1).strip() if grade_match else "N/A"

        score_match = re.search(r"reuse_score:\s*([\d\.]+)", content, re.MULTILINE)
        score = score_match.group(1).strip() if score_match else "0"

        recom_match = re.search(r"canonical_recommendation:\s*[\"']?(.*?)[\"']?$", content, re.MULTILINE)
        recom = recom_match.group(1).strip() if recom_match else "HOLD"

        # Extract governing question / concise answer
        gq_match = re.search(r"\*\*Governing question:\*\*\s*(.+)$", content, re.MULTILINE)
        if not gq_match:
            gq_match = re.search(r"\|\s*\*\*Governing Question\*\*\s*\|\s*(.+?)\s*\|", content)
        gov_q = gq_match.group(1).strip() if gq_match else ""

        rel_from_domain = file_path.relative_to(domain_dir).as_posix()
        files_list.append({
            "filename": file_path.name,
            "rel_path": rel_from_domain,
            "title": title,
            "grade": grade,
            "score": score,
            "recommendation": recom,
            "governing_question": gov_q
        })
    domains_data[domain_name] = files_list

# Generate 00_MASTER_AXIOM_API.md
lines = [
    "# Theophysics Axiomatic Architecture & Master Classification API",
    "## A Unified Formal & Epistemic Index",
    "",
    "> **Status:** Dynamic Classification Interface  ",
    f"> **Total Categorized Domains:** {len(domains_data)}  ",
    f"> **Total Registered Domain Nodes:** {sum(len(f) for f in domains_data.values())}  ",
    "> **Architectural Foundation:** `FULL AXIOM API.md` (Information-Theoretic Closure & Boundary Formalism)",
    "",
    "---",
    "",
    "## 📐 Core Formal Framework (Summary of Axiomatic System $S$)",
    "",
    "Based on the canonical formal treatment in `FULL AXIOM API.md`:",
    "",
    "### 1. Fundamental Boundary Definitions",
    "- **$S = (\\Sigma, O, C)$**: Formal system with state space $\\Sigma$, operation set $O$, constraint set $C$.",
    "- **$\\mathcal{C}(t) \\in [0,1]$**: Coupled logical-thermodynamic state fidelity (coherence measure).",
    "- **$\\mathcal{I}_c(S)$**: Gödelian boundary of $S$ (statements well-formed but undecidable within $S$).",
    "- **$\\partial S$**: Boundary interface between $S$ and its complement $S^c$.",
    "- **$S(X) = V(X) \\land T(X) \\land P(X) \\land R(X) \\land E(X)$**: Five closure conditions (Validation, Truth, Halting, Negentropy, Ground of Existence).",
    "",
    "### 2. Core Theorems & Domain Obstructions",
    "- **Theorem 1 (Non-Self-Sufficiency):** $\\text{Coherent}(S) \\implies \\neg S(S)$. No finite closed system can sustain persistent internal coherence without external input.",
    "- **Theorem 2 (Failure Mode Partition):**",
    "  - **Class A (Self-Reference Obstruction):** $\\{V, T, P\\}$ (Gödel, Tarski, Turing).",
    "  - **Class B (Thermodynamic Obstruction):** $\\{R, E_{\\text{cost}}\\}$ (Landauer bound: $\\Delta E \\ge k T \\ln 2$ per bit erased, Clausius-Boltzmann).",
    "  - **Class C (Explanatory Ground):** $\\{E_{\\text{ground}}\\}$ (Leibnizian sufficient reason requires non-circular dependency).",
    "- **Theorem 3 (Required External Input $\\mathcal{I}$):** Must possess Externality, Sufficiency across all 5 failures, Asymmetric Cost-bearing by the source, and State-Independence.",
    "- **Theorem 4 (Coupling Dynamics):** $d\\mathcal{C}/dt = F(\\mathcal{C}, S) + \\kappa(s(t)) \\cdot \\mathcal{I}(t)$, where internal alignment state $s \\in \\{-1, 0, +1\\}$ modulates absorption.",
    "",
    "---",
    "",
    "## 🗂️ Interactive Master Domain Index",
    ""
]

for domain, files in domains_data.items():
    domain_clean = domain.replace("_", " ")
    lines.append(f"### 📁 `{domain}` ({len(files)} documents)")
    lines.append(f"*Category Path: `OUTBOX/01_CATEGORIZED_DOMAINS/{domain}`*")
    lines.append("")
    lines.append("| Document Title | Score / Grade | Recommendation | Core Focus / Governing Question | Link |")
    lines.append("|---|:---:|:---:|---|:---:|")
    for f in files:
        rel_link = f"../01_CATEGORIZED_DOMAINS/{domain}/{f['rel_path']}"
        q_text = f['governing_question'] if f['governing_question'] else f['filename']
        if len(q_text) > 85:
            q_text = q_text[:82] + "..."
        clean_title = f['title'].replace("|", "\\|")
        q_text = q_text.replace("|", "\\|")
        lines.append(f"| **{clean_title}** | `{f['grade']}` ({f['score']}/100) | `{f['recommendation']}` | {q_text} | [Open]({rel_link}) |")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("## 🔗 Cross-Domain Navigational Directives")
lines.append("- To re-run folder sorting and title synchronization: run `RUN_SORT_AND_FIX_TITLES.bat` from root.")
lines.append("- To re-generate this index API after new intakes: run `python SCRIPTS/build_master_classification_api.py`.")
lines.append("- To process new documents with Quoted-Anchor Cards: drop files into `INBOX/` and run `RUN_EPISTEMIC_INTAKE_V2.bat`.")

out_file = CLASSIFICATIONS / "00_MASTER_AXIOM_API.md"
out_file.write_text("\n".join(lines), encoding="utf-8")
print(f"Generated master classification API at: {out_file} ({len(lines)} lines)")
