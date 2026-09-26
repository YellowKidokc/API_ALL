"""Rules for 11_CKG_PHYSICS, enforced in code (David's standard: real isomorphism constrains predictions in both
domains; if it's only analogy, it is flagged as analogy).

- A stage counts as mapped only when its match is direct/analogous AND it cites a timestamp or quote.
- STRUCTURAL needs: at least 3 mapped stages, directional == yes, and a stated prediction. Otherwise -> ANALOGY.
- IDENTITY needs everything STRUCTURAL needs plus every stage mapped "direct". Otherwise -> STRUCTURAL (if earned).
- A mirror with no mapped stage at all -> NONE.
- directional is recomputed from the stage order: a mapped stage listed out of order makes it "partly".
"""
from __future__ import annotations

LEVELS = ("NONE", "ANALOGY", "STRUCTURAL", "IDENTITY")


def enforce(mirror: dict) -> dict:
    m = dict(mirror)
    log = []
    stages = [s for s in m.get("stages") or [] if isinstance(s, dict)]
    mapped = [s for s in stages if s.get("match") in ("direct", "analogous") and str(s.get("timestamp") or "").strip()]
    unmapped_cited = [s for s in stages if s.get("match") in ("direct", "analogous") and not str(s.get("timestamp") or "").strip()]
    if unmapped_cited:
        log.append(f"{len(unmapped_cited)} stage(s) claimed a match without a timestamp or quote: not counted")
    directional = str(m.get("directional") or "no").lower()
    if m.get("out_of_order") and directional == "yes":
        directional = "partly"
        log.append("stages listed out of order: directional -> partly")
    claimed = str(m.get("level") or "NONE").upper()
    claimed = claimed if claimed in LEVELS else "NONE"
    level = claimed
    if not mapped:
        level = "NONE"
    if level in ("STRUCTURAL", "IDENTITY") and not (len(mapped) >= 3 and directional == "yes" and str(m.get("prediction") or "").strip()):
        why = []
        if len(mapped) < 3:
            why.append(f"only {len(mapped)} mapped stage(s)")
        if directional != "yes":
            why.append(f"directional is {directional}")
        if not str(m.get("prediction") or "").strip():
            why.append("no transferring prediction")
        level = "ANALOGY"
        log.append(f"{claimed} -> ANALOGY ({', '.join(why)})")
    if level == "IDENTITY" and not all(s.get("match") == "direct" for s in stages):
        level = "STRUCTURAL"
        log.append("IDENTITY -> STRUCTURAL (not every stage is a direct match)")
    if level != claimed and not any(claimed in x for x in log):
        log.append(f"{claimed} -> {level}")
    m.update({"level_claimed": claimed, "level": level, "directional": directional, "mapped_stages": len(mapped),
              "total_stages": len(stages), "rules_applied": log})
    return m
