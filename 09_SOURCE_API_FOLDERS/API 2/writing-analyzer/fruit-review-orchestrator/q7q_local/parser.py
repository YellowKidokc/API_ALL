"""7Q parser layer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .core import DOMAINS, SevenQState


def read_input(path_or_text: str | Path) -> Dict[str, Any]:
    """Read file input or accept direct text."""
    if isinstance(path_or_text, (str, Path)):
        p = Path(path_or_text)
        if isinstance(path_or_text, str) and p.exists():
            content = p.read_text(encoding="utf-8", errors="ignore")
            return {"source": "file", "path": str(p), "filename": p.name, "content": content, "format": p.suffix.lower()}
    return {"source": "direct", "path": "", "filename": "", "content": str(path_or_text), "format": "text"}


def _is_claim_header(line: str) -> bool:
    normalized = line.strip()
    if not normalized:
        return False

    patterns = (
        r"^#+\s*(claim|proposition|thesis|hypothesis|argument|statement|lemma|theorem|observation)\b",
        r"^(claim|proposition|thesis|hypothesis|argument|statement|lemma|theorem|observation)\s*[\d\w\-_.:]*\s*[:.\-]",
        r"^\d+[.)]\s+.*",
        r"^[-*]\s+(claim|proposition|thesis|hypothesis|argument|statement|lemma|theorem|observation)\b",
    )

    return any(re.match(pattern, normalized, flags=re.I) for pattern in patterns)


def decompose_claims(content: str) -> List[Dict[str, Any]]:
    """Split text into likely claim-sized chunks."""
    lines = content.splitlines()
    claims: List[Dict[str, Any]] = []
    current: List[str] = []
    current_header = ""

    def flush_current() -> None:
        if not current:
            return
        statement = " ".join(current).strip()
        if not statement:
            current.clear()
            return
        claim_index = len(claims) + 1
        claims.append({
            "claim_id": f"claim-{claim_index}",
            "statement": statement[:250],
            "heading": current_header.strip() or f"Claim {claim_index}",
            "index": claim_index,
        })
        current.clear()

    for line in lines:
        if _is_claim_header(line):
            flush_current()
            current_header = line.strip()
            current = [line.strip()]
            continue
        current.append(line.strip())

    flush_current()

    if not claims:
        return [{"claim_id": "claim-1", "statement": content[:500].strip(), "heading": "claim-1", "index": 1}]

    return claims


def extract_claims_for_paper(content: str, min_chars: int = 60) -> List[Dict[str, Any]]:
    """Return claim candidates for one 7Q run each.

    If only one candidate is found, it is always returned even if short.
    """
    raw_claims = decompose_claims(content)
    if len(raw_claims) <= 1:
        return raw_claims

    filtered = [c for c in raw_claims if len(c.get("statement", "").strip()) >= min_chars]
    if filtered:
        return filtered

    # fallback to first chunk if every chunk is too short and no alternative exists
    return [raw_claims[0]]


def detect_scale(content: str) -> str:
    text = content.lower()
    scale_markers = {
        "quantum": ["quantum", "subatomic", "wavefunction", "planck"],
        "molecular": ["molecule", "molecular", "atomic"],
        "microscopic": ["cell", "microbe", "microscopic"],
        "mesoscopic": ["mesoscopic", "intermediate", "medium"],
        "macroscopic": ["macroscopic", "visible", "large"],
        "individual": ["individual", "person", "human", "you", "i", "me"],
        "social": ["society", "social", "group", "community"],
        "civilizational": ["civilization", "civilizational", "culture", "history"],
        "cosmic": ["universe", "cosmic", "galaxy"],
        "metaphysical": ["metaphysical", "abstract", "being", "existence"],
    }
    for scale, terms in scale_markers.items():
        if any(t in text for t in terms):
            return scale
    return "metaphysical"


def detect_domains(content: str) -> Tuple[str, List[str]]:
    text = content.lower()
    patterns = {
        "physics": ["gravity", "force", "mass", "energy", "entropy", "quantum", "relativity", "field", "equation"],
        "theology": ["god", "grace", "sin", "faith", "holy", "spirit", "cross", "resurrection", "scripture", "bible"],
        "mathematics": ["theorem", "proof", "lemma", "axiom", "set", "equation", "metric", "integral"],
        "philosophy": ["metaphysics", "ethics", "logic", "ontology", "epistemology", "knowledge"],
        "consciousness": ["conscious", "experience", "awareness", "qualia", "observer"],
        "information_theory": ["information", "entropy", "channel", "capacity", "code", "signal"],
        "biology": ["gene", "cell", "evolution", "organism", "species", "protein"],
        "theophysics": ["chi", "logos", "coherence", "grace", "ten laws"],
    }
    scores = {k: 0 for k in DOMAINS}
    for domain, terms in patterns.items():
        scores[domain] = sum(1 for term in terms if term in text)

    best = max(scores.values())
    primary = max(scores, key=scores.get) if best > 0 else "universal"
    additional = [d for d, s in scores.items() if s > 0 and d != primary][:3]
    return primary if scores[primary] > 0 else "universal", additional


def detect_iso_status(content: str, additional_domains: List[str]) -> str:
    text = content.lower()
    if len(additional_domains) < 2:
        return "NONE"
    iso_markers = ["isomorphism", "mapping", "structural", "same equation", "identical", "correspondence"]
    if any(m in text for m in iso_markers):
        return "ISO_PARALLEL"
    return "ISO_ANALOGY"


def detect_claim_type(content: str) -> str:
    c = content.lower()
    if "therefore" in c or "thus" in c:
        return "mathematical"
    if any(x in c for x in ["if", "because", "causes", "leads"]):
        return "causal"
    if "all" in c and "if" in c:
        return "universal"
    return "descriptive"


def detect_precision(content: str) -> str:
    has_math = bool(re.search(r"[=+*/^()\\d]", content))
    has_units = bool(re.search(r"\b(?:km|kg|m|s|eV|Hz|J|W)\b", content))
    has_numbers = bool(re.search(r"\b\d+\.\d+|\b\d+\s*[kx]\s*10\^", content, re.I))
    if has_math and has_units and has_numbers:
        return "precise"
    if has_math and (has_units or has_numbers):
        return "mathematical"
    wc = len(content.split())
    if wc > 120:
        return "detailed"
    if wc > 40:
        return "basic"
    return "vague"


def detect_scope(content: str) -> str:
    c = content.lower()
    if "every" in c or "always" in c or "universal" in c:
        return "universal"
    if "if" in c or "when" in c:
        return "conditional"
    if "specific" in c or "case" in c or "example" in c:
        return "local"
    return "domain_specific"


def parse_input(content: str) -> SevenQState:
    state = SevenQState()
    state.claim_text = content[:1000]
    state.assertion = content[:500]
    state.run_timestamp = datetime_now_iso()
    state.subclaims = decompose_claims(content)
    state.primary_domain, state.additional_domains = detect_domains(content)
    state.scale = detect_scale(content)
    state.iso_status = detect_iso_status(content, state.additional_domains)
    state.claim_type = detect_claim_type(content)
    state.precision = detect_precision(content)
    state.scope = detect_scope(content)
    return state


def find_inputs(cfg: Dict[str, Any]) -> List[Path]:
    from .core import INPUT_DIR

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {ext.lower() for ext in cfg.get("input_extensions", [".md", ".txt", ".json", ".yaml", ".html"])}
    return sorted([p for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() in allowed and not p.name.startswith(".")])


def datetime_now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()

