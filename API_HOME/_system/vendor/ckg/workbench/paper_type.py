"""Paper-type tagger ("master equation Namer").

Derives a short, stable type tag from the CKG map so filenames start with
the paper's category: ``MEQ_...``, ``APOLO_...``, ``YT_...``, etc.
"""

from __future__ import annotations

import re
from pathlib import Path


def _safe_filename(text: str) -> str:
    safe = re.sub(r"[^\w\s-]", "", str(text).strip()).strip()
    safe = re.sub(r"[-\s]+", "_", safe)
    return safe[:80].strip("_")


def paper_type_tag(map_data: dict) -> str:
    """Return a short uppercase tag for the paper's category."""
    domain = (map_data.get("domain") or "").lower()
    project = (map_data.get("project") or "").lower()
    title = (map_data.get("title") or "").lower()
    purpose = (map_data.get("purpose") or "").lower()
    keywords = " ".join(str(k).lower() for k in map_data.get("keywords") or [])
    all_text = f"{domain} {project} {title} {purpose} {keywords}"

    if "youtube" in project or "youtube" in domain or "channel" in project:
        return "YT"
    if "master equation" in all_text:
        return "MEQ"
    if "apologetics" in domain or "apologetics" in project:
        return "APOLO"
    if "theology" in domain:
        return "THEO"
    if "biblical" in domain or "new testament" in domain:
        return "BIBLE"
    if "historical jesus" in domain:
        return "HIST"
    if "philosophy" in domain:
        return "PHIL"
    if "physics" in domain:
        return "PHYS"
    if any(x in domain for x in ("science", "biology", "cosmology", "evolutionary")):
        return "SCI"
    if any(x in domain for x in ("methodology", "epistemology")):
        return "METH"
    return "OTHER"


def tagged_name(map_data: dict, paper_uuid: str, suffix: str, max_stem_len: int = 120) -> str:
    """Readable filename with a leading type tag.

    Falls back to ``<tag>_<UUID><suffix>`` when no title is available.
    The total stem length (tag + base name) is capped at ``max_stem_len``.
    """
    tag = paper_type_tag(map_data)
    title = (map_data.get("title") or "").strip()
    keywords = map_data.get("keywords") or []

    if title:
        stem = _safe_filename(title)
        if stem and keywords:
            kw_part = "_".join(_safe_filename(str(k)) for k in keywords[:3] if k)
            if kw_part:
                reserved = len(tag) + len(stem) + 4  # tag + __ + __
                max_kw = max(0, max_stem_len - reserved)
                if max_kw:
                    kw_part = kw_part[:max_kw].rstrip("_")
                    if kw_part:
                        stem = f"{stem}__{kw_part}"
        name = f"{stem}{suffix}"
    else:
        name = f"{paper_uuid}{suffix}"

    # Prepend tag, but keep the whole stem within bounds.
    full_stem = Path(name).stem
    if len(full_stem) + len(tag) + 1 > max_stem_len:
        trim_to = max(0, max_stem_len - len(tag) - 1)
        full_stem = full_stem[:trim_to].rstrip("_")
    return f"{tag}_{full_stem}{suffix}"
