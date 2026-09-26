#!/usr/bin/env python3
"""Add a scorecard to every chapter note: people/places/orgs, claim signals, scripture, dates,
topic coherence, transcript quality, and cross-references to other chapters and channels.

    python score_chapters.py "C:/.../30_FRAMEWORKS/YOUTUBE"             # every CHANNEL/PLAYLIST folder inside
    python score_chapters.py "C:/.../YOUTUBE" --limit 5                 # quick test on 5 notes per folder
    python score_chapters.py "C:/.../YOUTUBE" --no-embed                # skip coherence (faster)

Writes into each note: a `scorecard:` YAML block + a collapsed Scorecard callout above the transcript
(both replaced on re-run). Per folder: `<Channel> - 000 Scorecard.md`, `_scorecard.csv`, `_entities.json`.
Scores are triage signals for deciding what to read first, not judgments of truth.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

EMBED_MODEL = "X:/05_MODELS/M19_03_EMBEDDINGS_FAST"
START, END = "<!-- scorecard:start -->", "<!-- scorecard:end -->"

NOISE_RE = re.compile(r"\[(music|applause|laughter|__|inaudible)[^\]]*\]", re.I)
FILLER_RE = re.compile(r"\b(uh|um|uhh|umm|you know|i mean)\b", re.I)
SENT_RE = re.compile(r"(?<=[.!?])\s+")
CLAIM_RE = re.compile(
    r"\b(evidence|proves?|proven|fact|facts|according to|studies?|scholars?|historians?|documents?|records?|"
    r"testif\w*|reported|confirmed|data|percent|source[sd]?|eyewitness\w*|manuscripts?|admitted|revealed)\b"
    r"|\b\d{2,4}\b", re.I)
BOOKS = ("Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|"
         "Esther|Job|Psalms?|Proverbs|Ecclesiastes|Song of Songs|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|"
         "Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|"
         "Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|"
         "Hebrews|James|Peter|Jude|Revelation")
SCRIPTURE_RE = re.compile(rf"\b(?:(?:1|2|3|first|second|third|1st|2nd|3rd)\s+)?(?:{BOOKS})\s+(?:chapter\s+)?\d{{1,3}}"
                          rf"(?:\s*(?::|verse|verses)\s*\d{{1,3}}(?:\s*(?:-|to|through)\s*\d{{1,3}})?)?\b", re.I)
YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-4][0-9])\b|\b\d{1,3}\s?(?:AD|A\.D\.|BC|B\.C\.)\b")
ENT_KEEP = {"PERSON": "people", "GPE": "places", "LOC": "places", "FAC": "places", "ORG": "organizations"}
STOP_ENTS = {"god", "lord", "okay", "yeah", "hey", "amen", "bible", "aramaic", "hebrew", "greek", "latin",
             "gospel", "gospels", "new testament", "old testament", "scripture", "scriptures", "torah", "yahweh",
             "christian", "christians", "christianity", "jewish", "muslim", "islam", "the church", "church"}
BOOK_WORDS = {b.lower() for b in BOOKS.split("|")} - {"mark", "luke", "john", "james", "peter", "timothy", "titus",
                                                       "daniel", "jonah", "jude", "ruth", "esther", "job", "amos",
                                                       "micah", "matthew", "joel"}


def split_note(text: str):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    return text[4:end], text[end + 4:]


def get_field(front: str, key: str) -> str:
    m = re.search(rf"(?m)^{key}:\s*(.*)$", front)
    return m.group(1).strip().strip('"') if m else ""


def clean_entity(text: str) -> str:
    text = re.sub(r"^(the|a|an|dr|mr|mrs|ms)\.?\s+", "", text.strip(), flags=re.I)
    text = re.sub(r"['’]s$", "", text).strip(" .,-")
    return text


def scale(value: float, lo: float, hi: float) -> float:
    return max(0.0, min(1.0, (value - lo) / (hi - lo))) if hi > lo else 0.0


def load_notes(folder: Path, limit: int):
    notes = []
    for path in sorted(folder.glob("* - Chapter *.md")):
        raw = path.read_text(encoding="utf-8")
        parts = split_note(raw)
        if not parts:
            continue
        front, body = parts
        transcript = body.split("## Transcript", 1)[1] if "## Transcript" in body else ""
        notes.append({"path": path, "front": front, "body": body, "transcript": transcript.strip(),
                      "channel": get_field(front, "channel"), "chapter": int(get_field(front, "chapter") or 0),
                      "title": get_field(front, "title"), "language": get_field(front, "transcript_language")})
        if limit and len(notes) >= limit:
            break
    return notes


def extract(notes, workers: int):
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["lemmatizer"])
    nlp.max_length = 2_000_000
    jobs = []
    for i, n in enumerate(notes):
        text = NOISE_RE.sub(" ", n["transcript"])
        n["clean"] = re.sub(r"\s+", " ", text).strip()
        for start in range(0, len(n["clean"]), 20_000):
            jobs.append((n["clean"][start:start + 20_000], i))
    for n in notes:
        n["ents"] = {"people": Counter(), "places": Counter(), "organizations": Counter()}
    for doc, i in nlp.pipe(jobs, as_tuples=True, n_process=workers, batch_size=8):
        for ent in doc.ents:
            bucket = ENT_KEEP.get(ent.label_)
            if not bucket:
                continue
            name = clean_entity(ent.text)
            low = re.sub(r"^(first|second|third|1|2|3)\s+", "", name.lower())
            if (len(name) < 3 or name.lower() in STOP_ENTS or low in BOOK_WORDS or not name[0].isupper()
                    or len(name.split()) > 5):
                continue
            notes[i]["ents"][bucket][name] += 1


def coherence(notes):
    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    for n in notes:
        words = n["clean"].split()
        chunks = [" ".join(words[i:i + 200]) for i in range(0, len(words), 200)]
        if len(chunks) < 2:
            n["coherence"] = None
            continue
        vecs = model.encode(chunks, batch_size=64, normalize_embeddings=True)
        centroid = vecs.mean(axis=0)
        centroid /= np.linalg.norm(centroid) or 1
        n["coherence"] = round(float((vecs @ centroid).mean()), 3)


def score(n, person_index):
    words = len(n["clean"].split()) or 1
    per_k = 1000 / words
    sentences = [s for s in SENT_RE.split(n["clean"]) if len(s.split()) > 4]
    claim_sents = sum(1 for s in sentences if CLAIM_RE.search(s))
    scripture = Counter(m.group(0).strip() for m in SCRIPTURE_RE.finditer(n["clean"]))
    years = Counter(m.group(0) for m in YEAR_RE.finditer(n["clean"]))
    fillers = len(FILLER_RE.findall(n["transcript"]))
    noise = len(NOISE_RE.findall(n["transcript"]))
    ents = n["ents"]
    uniq = sum(len(v) for v in ents.values())

    same, other = [], []
    for person in ents["people"]:
        refs = person_index.get(person.lower(), set()) - {(n["channel"], n["chapter"])}
        if any(c == n["channel"] for c, _ in refs):
            same.append(person)
        if any(c != n["channel"] for c, _ in refs):
            other.append(person)

    coh = n.get("coherence")
    parts = {
        "substance": 35 * scale(claim_sents * per_k, 2, 25),
        "entities": 20 * scale(uniq * per_k, 1, 12),
        "coherence": 25 * (scale(coh, 0.45, 0.8) if coh is not None else 0.5),
        "transcript": 10 * (1 - scale(fillers / words * 100, 0.5, 6)),
        "connectivity": 10 * (len(set(same) | set(other)) / len(ents["people"]) if ents["people"] else 0),
    }
    total = round(sum(parts.values()))
    grade = "A" if total >= 75 else "B" if total >= 60 else "C" if total >= 45 else "D"
    coh_label = "n/a" if coh is None else "high" if coh >= 0.7 else "medium" if coh >= 0.55 else "low"
    return {
        "score": total, "grade": grade, "words": words,
        "claim_signals": claim_sents, "claim_signals_per_1k": round(claim_sents * per_k, 1),
        "people": len(ents["people"]), "places": len(ents["places"]), "organizations": len(ents["organizations"]),
        "top_people": [p for p, _ in ents["people"].most_common(8)],
        "top_places": [p for p, _ in ents["places"].most_common(6)],
        "top_organizations": [p for p, _ in ents["organizations"].most_common(6)],
        "scripture_refs": sum(scripture.values()), "top_scripture": [s for s, _ in scripture.most_common(6)],
        "years_mentioned": len(years), "coherence": coh, "coherence_label": coh_label,
        "filler_per_100_words": round(fillers / words * 100, 2), "noise_tags": noise,
        "auto_captions": "auto" in n["language"].lower(),
        "people_in_other_chapters": sorted(same)[:10], "people_in_other_channels": sorted(other)[:10],
        "parts": {k: round(v, 1) for k, v in parts.items()},
    }


def yaml_block(sc) -> str:
    j = lambda v: json.dumps(v, ensure_ascii=False)
    keys = ["score", "grade", "words", "claim_signals", "claim_signals_per_1k", "people", "places", "organizations",
            "top_people", "top_places", "top_organizations", "scripture_refs", "top_scripture", "years_mentioned",
            "coherence", "coherence_label", "filler_per_100_words", "auto_captions",
            "people_in_other_chapters", "people_in_other_channels"]
    lines = ["scorecard:"] + [f"  {k}: {j(sc[k])}" for k in keys]
    lines.append("  parts: " + j(sc["parts"]))
    lines.append('  note: "triage signal, not a truth rating"')
    return "\n".join(lines)


def callout(sc) -> str:
    link = lambda xs: ", ".join(xs) if xs else "none"
    return "\n".join([
        START,
        f"> [!abstract]- Scorecard: {sc['score']}/100 (grade {sc['grade']}) · coherence {sc['coherence_label']}",
        f"> **Claim signals:** {sc['claim_signals']} ({sc['claim_signals_per_1k']}/1k words) · "
        f"**People:** {sc['people']} · **Places:** {sc['places']} · **Orgs:** {sc['organizations']} · "
        f"**Scripture refs:** {sc['scripture_refs']} · **Years/dates:** {sc['years_mentioned']}",
        f"> **Top people:** {link(sc['top_people'])}",
        f"> **Top places:** {link(sc['top_places'])} · **Top orgs:** {link(sc['top_organizations'])}",
        f"> **Scripture:** {link(sc['top_scripture'])}",
        f"> **Also in other chapters:** {link(sc['people_in_other_chapters'])}",
        f"> **Also in other channels:** {link(sc['people_in_other_channels'])}",
        f"> **Transcript:** {'auto-captions' if sc['auto_captions'] else 'manual'} · "
        f"filler {sc['filler_per_100_words']}/100 words · score parts {sc['parts']}",
        "> _Machine-extracted candidates; names may include caption errors. Triage signal, not a truth rating._",
        END,
    ])


def write_note(n, sc):
    front = re.sub(r"(?ms)^scorecard:\n(?:  .*\n?)*", "", n["front"]).rstrip("\n")
    body = re.sub(rf"(?s)\n?{re.escape(START)}.*?{re.escape(END)}\n?", "\n", n["body"])
    body = body.replace("## Transcript", callout(sc) + "\n\n## Transcript", 1)
    n["path"].write_text(f"---\n{front}\n{yaml_block(sc)}\n---{body}", encoding="utf-8", newline="\n")


def channel_report(folder: Path, notes, cards):
    channel = notes[0]["channel"]
    rows = sorted(zip(notes, cards), key=lambda x: -x[1]["score"])
    people = Counter()
    for n in notes:
        people.update({p: 1 for p in n["ents"]["people"]})
    link = lambda n: f"[[{n['path'].stem}|{n['chapter']:03d} {n['title'][:70]}]]"
    grades = Counter(c["grade"] for c in cards)
    lines = [f"# {channel} — Scorecard", "",
             f"**Chapters scored:** {len(cards)} · **Grades:** " + " · ".join(f"{g}: {grades.get(g, 0)}" for g in "ABCD"),
             "", "> Scores rank what to read first. They measure density and structure, not truth.", "",
             "## Highest scoring", ""] + [f"- {c['score']} {link(n)}" for n, c in rows[:15]] + \
            ["", "## Lowest coherence (wanders or mixed content)", ""] + \
            [f"- {c['coherence']} {link(n)}" for n, c in sorted(zip(notes, cards), key=lambda x: x[1]["coherence"] or 9)[:10]] + \
            ["", "## Most-mentioned people (number of chapters)", ""] + [f"- {p} — {k}" for p, k in people.most_common(40)]
    (folder / f"{channel} - 000 Scorecard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (folder / "_scorecard.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["chapter", "title", "score", "grade", "words", "claim_signals_per_1k", "people", "places",
                    "organizations", "scripture_refs", "coherence", "filler_per_100_words"])
        for n, c in sorted(zip(notes, cards), key=lambda x: x[0]["chapter"]):
            w.writerow([n["chapter"], n["title"], c["score"], c["grade"], c["words"], c["claim_signals_per_1k"],
                        c["people"], c["places"], c["organizations"], c["scripture_refs"], c["coherence"],
                        c["filler_per_100_words"]])
    (folder / "_entities.json").write_text(json.dumps(
        {n["chapter"]: {k: dict(v.most_common()) for k, v in n["ents"].items()} for n in notes},
        ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path, help="YOUTUBE folder, or one CHANNEL/PLAYLIST folder")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--no-embed", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    folders = [root] if any(root.glob("* - Chapter *.md")) else \
        sorted(p for p in root.iterdir() if p.is_dir() and re.match(r"(CHANNEL|PLAYLIST) - ", p.name))
    by_folder = {f: load_notes(f, args.limit) for f in folders}
    all_notes = [n for ns in by_folder.values() for n in ns]
    print(f"{len(all_notes)} notes in {len(folders)} folders — extracting entities…", flush=True)
    extract(all_notes, args.workers)
    if not args.no_embed:
        print("coherence embeddings…", flush=True)
        coherence(all_notes)

    person_index = defaultdict(set)
    for n in all_notes:
        for p in n["ents"]["people"]:
            person_index[p.lower()].add((n["channel"], n["chapter"]))

    for folder, notes in by_folder.items():
        if not notes:
            continue
        cards = [score(n, person_index) for n in notes]
        for n, c in zip(notes, cards):
            write_note(n, c)
        channel_report(folder, notes, cards)
        print(f"{folder.name}: {len(cards)} scored · avg {sum(c['score'] for c in cards) / len(cards):.0f}", flush=True)


if __name__ == "__main__":
    main()
