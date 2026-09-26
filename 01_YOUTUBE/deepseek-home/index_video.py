r"""Map YouTube transcripts onto the DEBATE MAP, with every argument tagged at the top.

For each raw transcript (subtitles/<Channel>/<title>.md, [mm:ss] lines):
  1. DeepSeek `index` task per chunk (HOME + GLOSSARY + STATE + DEBATE_MAP + TASK), JSON out
  2. merge the chunks, then one `synthesize` call: real speaker names, merged
     duplicates, the list of debates, the best arguments for David
  3. write obsidian_indexed/<Channel>/<title>.md:
       classification -> the N debates -> best for David -> argument write-ups
       -> checks and resources -> people/places/things -> cleaned transcript
  4. keep the merged JSON beside it (<title>.index.json) for atom export

Usage:
  python index_video.py "..\..\subtitles\Daily Dose Of Wisdom\<video>.md"
  python index_video.py "..\..\subtitles\Daily Dose Of Wisdom" --limit 5 --workers 4
  add --force to redo videos already indexed
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import home  # noqa: E402

REPO = HERE.parents[1]                      # yt-transcript-downloader
CLEAN_ROOT = REPO / "obsidian_transcripts"
OUT_ROOT = REPO / "obsidian_indexed"
CHUNK_WORDS = 2500
SETTLE_SECONDS = 120        # skip transcripts modified this recently (download in progress)
MIN_WORDS = 200             # below this the download has no captions; never send it to the API
MODEL = "deepseek-chat"

UI_TIME = re.compile(r"^((?:\d+:)?\d{1,2}:\d{2})\d+ (?:hours?|minutes?|seconds?)"
                     r"(?:, \d+ (?:minutes?|seconds?))*")


def load_map():
    """DEBATE_MAP.md -> ({question_id: (subject_id, question)}, {subject_id: subject})."""
    questions, subjects, current = {}, {}, None
    for line in (HERE / "DEBATE_MAP.md").read_text(encoding="utf-8").splitlines():
        s = re.match(r"^## (S-[A-Z-]+) · (.+)", line)
        q = re.match(r"^- `(Q-[A-Z0-9-]+)` (.+)", line)
        if s:
            current = s.group(1)
            subjects[current] = s.group(2).strip()
        elif q and current:
            questions[q.group(1)] = (current, q.group(2).strip())
    return questions, subjects


QUESTIONS, SUBJECTS = load_map()


def normalize(text):
    """Turn YouTube's copy-pasted transcript panel ('1:011 minute, 1 second...')
    into '[1:01] ...' lines. Files already in [mm:ss] form pass through."""
    if re.search(r"^\[\d+:\d{2}", text, re.M):
        return text
    out = []
    for line in text.splitlines():
        m = UI_TIME.match(line)
        if m:
            line = f"[{m.group(1)}] {line[m.end():].strip()}"
        elif line.startswith("Chapter "):
            line = f"### {line}"
        out.append(line)
    return "\n".join(out)


def meta(text, path):
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), path.stem)
    vid = re.search(r"\*\*Video ID:\*\*\s*`([^`]+)`", text)
    return {"title": title, "video_id": vid.group(1) if vid else "",
            "channel": path.parent.name, "source_file": str(path),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def tag(s):
    """Obsidian-safe nested tag: keep '/', kebab everything else."""
    return "/".join(p for p in (slug(x) for x in s.split("/")) if p)


def book(ref):
    """'1 Corinthians 15:3-8' -> '1 Corinthians' (tag by book, not verse)."""
    return re.sub(r"\s+\d+[\d:,\-– ]*$", "", ref.strip())


def secs(ts):
    n = 0
    for part in str(ts).split(":"):
        n = n * 60 + int(part) if part.isdigit() else n
    return n


class Truncated(Exception):
    """The reply hit the output-token limit; the input must be split."""


def call(client, prompt):
    for attempt in range(2):
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.2, max_tokens=8192,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}])
        if resp.choices[0].finish_reason == "length":
            raise Truncated()
        try:
            return json.loads(resp.choices[0].message.content), resp.usage
        except json.JSONDecodeError:
            if attempt:
                raise
    return None, None


def index_piece(client, lines, title, label, depth=0):
    """Index one chunk; if the reply is cut off, halve the chunk and recurse."""
    try:
        data, usage = call(client, home.build("index", "\n".join(lines), title, *label))
        return [data], usage.prompt_tokens, usage.completion_tokens
    except Truncated:
        if depth >= 3 or len(lines) < 20:
            raise
        mid = len(lines) // 2
        a = index_piece(client, lines[:mid], title, label, depth + 1)
        b = index_piece(client, lines[mid:], title, label, depth + 1)
        return a[0] + b[0], a[1] + b[1], a[2] + b[2]


LIST_KEYS = ["speakers", "arguments", "exchanges", "resources", "claims_to_verify", "new_questions",
             "people", "places", "things", "scripture", "topics", "theophysics_tags",
             "follow_ups", "segments", "stories", "teaching", "concepts", "lessons"]
KEY_OF = {"speakers": "name", "people": "name", "places": "name", "things": "name",
          "resources": "identified_as", "new_questions": "question",
          "exchanges": "objection", "stories": "title", "teaching": "topic",
          "concepts": "concept", "lessons": "lesson"}
STORY_SCALES = ["clarity", "emotional_impact", "memorability", "teaching_value", "retelling_usefulness"]
TEACH_SCALES = ["clarity", "context_attention", "practical_usefulness"]


def score(item, scales):
    """Average of the 1-5 ratings that were actually given (blank stays blank)."""
    got = [((item.get("ratings") or {}).get(s) or {}).get("score") for s in scales]
    got = [g for g in got if isinstance(g, (int, float))]
    return round(sum(got) / len(got), 1) if got else ""


def scores_line(item, scales):
    r = item.get("ratings") or {}
    return " · ".join(f"{s.replace('_', ' ')} {(r.get(s) or {}).get('score', '–')}" for s in scales)


def merge(parts):
    """Combine chunk results, de-duplicating by name/ref."""
    out = {k: [] for k in LIST_KEYS}
    out["chunk_summaries"] = [p.get("summary", "") for p in parts]
    out["summary"] = " ".join(out["chunk_summaries"]).strip()
    seen = {k: set() for k in LIST_KEYS}
    for p in parts:
        for k in LIST_KEYS:
            for item in p.get(k) or []:
                if k == "arguments":
                    name = item.get("name", "").lower()
                    prev = next((a for a in out[k] if a.get("name", "").lower() == name), None)
                    if prev:
                        prev["timestamps"] = prev.get("timestamps", []) + item.get("timestamps", [])
                    else:
                        out[k].append(item)
                    continue
                kf = KEY_OF.get(k)
                ident = (str(item.get(kf) or item.get("spoken_as") or item.get("name") or "")
                         if kf and isinstance(item, dict) else json.dumps(item, sort_keys=True)).lower()
                if ident and ident not in seen[k]:
                    seen[k].add(ident)
                    out[k].append(item)
    return out


def collapse(stamps, gap=90, cap=5):
    """Keep passage starts only: drop stamps within `gap` seconds of the last kept."""
    kept = []
    for t in sorted(set(stamps), key=secs):
        if not kept or secs(t) - secs(kept[-1]) >= gap:
            kept.append(t)
    return kept[:cap]


def synthesize(client, data, m, opening):
    """Second pass over the merged chunks: summary, real names, merged
    duplicates, the video's debates, best arguments for David."""
    brief = {
        "title": m["title"], "channel": m["channel"], "transcript_opening": opening,
        "chunk_summaries": data["chunk_summaries"], "speakers": data["speakers"],
        "people": [p.get("name", "") for p in data["people"]],
        "speaker_labels_used_on_arguments": sorted({a.get("speaker", "") for a in data["arguments"]}),
        "new_questions": data["new_questions"],
        "arguments": [{"name": a.get("name"), "question_id": a.get("question_id"),
                       "family": a.get("family"), "strength": a.get("strength"),
                       "conclusion": a.get("conclusion"),
                       "disputed_steps": [s.get("claim") for s in a.get("steps") or []
                                          if s.get("disputed_by")],
                       "opposing_advocated_in_video": a.get("opposing_advocated_in_video"),
                       "timestamps": a.get("timestamps", [])[:2]} for a in data["arguments"]],
    }
    prompt = home.build("synthesize", json.dumps(brief, ensure_ascii=False, indent=1),
                        m["title"], 1, 1)
    syn, usage = call(client, prompt)

    alias = {k.lower(): v for k, v in (syn.get("people_aliases") or {}).items()}
    people, seen = [], set()
    for p in data["people"]:
        name = alias.get(p.get("name", "").lower(), p.get("name", ""))
        if name and name.lower() not in seen:
            seen.add(name.lower())
            people.append({**p, "name": name})
    data["people"] = people
    for a in data["arguments"]:
        spk = a.get("speaker", "")
        a["speaker"] = alias.get(spk.lower(), spk) or spk

    by_name = {a.get("name", "").lower(): a for a in data["arguments"]}
    for g in syn.get("argument_merges") or []:
        keep = by_name.get(g.get("keep", "").lower())
        for d in g.get("drop") or []:
            gone = by_name.get(d.lower())
            if keep and gone and gone is not keep:
                del by_name[d.lower()]
                keep["timestamps"] = keep.get("timestamps", []) + gone.get("timestamps", [])
                keep["evidence_cited"] = list(dict.fromkeys(
                    (keep.get("evidence_cited") or []) + (gone.get("evidence_cited") or [])))
    data["arguments"] = [a for a in data["arguments"] if a.get("name", "").lower() in by_name]

    for k in ("summary", "speakers", "best_for_david", "debates", "format", "direction",
              "opposition", "subjects", "coverage"):
        if syn.get(k):
            data[k] = syn[k]
    data["follow_ups"] += syn.get("follow_ups") or []
    return usage


def pl(n, one, many=None):
    return f"{n} {one if n == 1 else (many or one + 's')}"


def js(x):
    return json.dumps(x, ensure_ascii=False)


def qlabel(qid, data):
    if qid in QUESTIONS:
        return QUESTIONS[qid][1]
    d = next((d for d in data.get("debates", []) if d.get("question_id") == qid), None)
    return (d or {}).get("question", qid)


def render(m, data, body):
    url = f"https://www.youtube.com/watch?v={m['video_id']}" if m["video_id"] else ""

    def at(ts):
        return f"[{ts}]({url}&t={secs(ts)}s)" if url else f"[{ts}]"

    # number arguments in debate order so the map at the top links down to them
    debates = data.get("debates") or []
    order = {d.get("question_id"): i for i, d in enumerate(debates)}
    rank = {"strong": 0, "moderate": 1, "weak": 2}
    args = sorted(data["arguments"], key=lambda a: (
        order.get(a.get("question_id"), 99), rank.get(a.get("strength"), 3),
        secs((a.get("timestamps") or ["0:00"])[0])))
    for i, a in enumerate(args, 1):
        a["id"] = f"A{i:02d}"
    ref = {a.get("name", "").lower(): a for a in args}

    def link(name):
        a = ref.get(str(name).lower())
        return f"[[#{a['id']} · {a['name']}|{a['id']}]]" if a else str(name)

    qids = list(dict.fromkeys(a.get("question_id") or "NEW" for a in args))
    sids = list(dict.fromkeys(QUESTIONS.get(q, ("S-NEW",))[0] for q in qids))
    names = lambda k: [x.get("name", "") for x in data[k] if x.get("name")]  # noqa: E731
    tags = (["youtube", "transcript", "indexed", f"channel/{slug(m['channel'])}",
             f"format/{slug(data.get('format', 'unknown'))}"]
            + [f"subject/{s.lower()}" for s in sids]
            + [f"q/{q.lower()}" for q in qids]
            + sorted({f"arg/{tag(a.get('family', 'other'))}" for a in args})
            + [f"person/{slug(n)}" for n in names("people")]
            + [f"place/{slug(n)}" for n in names("places")]
            + [f"thing/{slug(n)}" for n in names("things")]
            + sorted({"scripture/" + slug(book(s.get("ref", ""))) for s in data["scripture"]
                      if s.get("ref")})
            + [f"topic/{tag(t)}" for t in data["topics"]]
            + sorted({f"story/{tag(t)}" for s in data.get("stories") or [] for t in s.get("themes", [])})
            + [f"concept/{slug(c.get('concept', ''))}" for c in data.get("concepts") or []]
            + sorted({f"segment/{x.get('kind', '')}" for x in data.get("segments") or [] if x.get("kind")})
            + [t if t.startswith("var-") else slug(t) for t in data["theophysics_tags"]])
    tags = list(dict.fromkeys(t for t in tags if t and not t.endswith("/")))

    run = data.get("_meta") or {}
    fm = ["---",
          "record_version: CKG_ATOM_RECORD_V3.2_UNIFIED",
          "template_status: REVIEW_DRAFT",
          "argument_focus:",
          "  profile_version: ARGUMENT_FIRST_V1",
          "  profile_status: REVIEW_DRAFT",
          "  base_template: CKG_ATOM_RECORD_V3.2_UNIFIED",
          f"  source_format: {js(data.get('format') or None)}",
          f"  source_direction_summary: {js(data.get('direction') or None)}",
          f"  opposition_representation: {js(data.get('opposition') or None)}",
          "  inventory_status: PARTIAL",
          "  counting_rule_version: ARGUMENT_INVENTORY_V1",
          f"  source_coverage: {js(data.get('coverage') or None)}",
          "  counts:",
          f"    subject_areas: {len(sids)}",
          f"    debate_questions: {len(debates) or len(qids)}",
          f"    argument_families: {len({a.get('family', 'other').split('/')[0] for a in args})}",
          f"    argument_versions: {len(args)}",
          f"    claims: {sum(len(a.get('steps') or []) for a in args)}",
          f"    actual_exchanges: {len(data.get('exchanges') or [])}",
          f"    stories: {len(data.get('stories') or [])}",
          "content_type: youtube-video",
          f"source_file: {js(m.get('source_file'))}",
          f"source_sha256: {js(m.get('source_sha256'))}",
          "lifecycle_state: RAW",
          "review_status: NOT_REVIEWED",
          "evidence_assessment_status: NOT_ASSESSED",
          "formal_build_status: NOT_RUN",
          "admission: {graph: candidate, human_ruling: pending, ruling_actor: null, ruling_date: null}",
          "stations: {enabled: {ckg: true, stories: true, atoms: false, lean4: false}}",
          f"provider: deepseek",
          f"model: {MODEL}",
          f"usage_tokens: {js({'in': run.get('tokens_in'), 'out': run.get('tokens_out')} if run else None)}",
          f"title: {js(m['title'])}",
          f"channel: {js(m['channel'])}",
          f"video_id: {js(m['video_id'])}",
          f"url: {js(url)}",
          f"format: {js(data.get('format', ''))}",
          f"direction: {js(data.get('direction', ''))}",
          f"opposition: {js(data.get('opposition', ''))}",
          f"speakers: {js([s.get('name', '') for s in data['speakers']])}",
          f"subjects: {js([SUBJECTS.get(s, s) for s in sids])}",
          f"subject_count: {len(sids)}",
          f"question_count: {len(debates) or len(qids)}",
          f"family_count: {len({a.get('family', 'other').split('/')[0] for a in args})}",
          f"argument_version_count: {len(args)}",
          f"exchange_count: {len(data.get('exchanges') or [])}",
          "inventory: PARTIAL",
          f"questions: {js(qids)}",
          f"best_for_david: {js([b.get('argument', '') for b in data.get('best_for_david', [])])}",
          f"people: {js([f'[[{n}]]' for n in names('people')])}",
          f"places: {js([f'[[{n}]]' for n in names('places')])}",
          f"things: {js([f'[[{n}]]' for n in names('things')])}",
          f"scripture: {js(list(dict.fromkeys(s.get('ref', '') for s in data['scripture'])))}",
          f"story_count: {len(data.get('stories') or [])}",
          f"stories: {js([s.get('title', '') for s in data.get('stories') or []])}",
          f"concepts: {js(list(dict.fromkeys(c.get('concept', '') for c in data.get('concepts') or [])))}",
          f"indexed_on: {dt.date.today().isoformat()}",
          f"indexed_by: {MODEL}",
          f"tags: {js(tags)}",
          "---", ""]

    def row(cells):
        return "| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |"

    fams = sorted({a.get("family", "other").split("/")[0] for a in args})
    n_subj, n_q = len(sids), len(debates) or len(qids)
    subj_rows = data.get("subjects") or []
    exchanges = data.get("exchanges") or []

    # ---- Argument overview (CKG A17 front section) ----
    L = [f"# {m['title']}", "",
         f"**Channel:** [[{m['channel']}]]" + (f" · [Watch on YouTube]({url})" if url else ""), "",
         '<a id="overview"></a>', "",
         "## Argument overview", "",
         f"> [!abstract] {data.get('format', 'source').capitalize()} · "
         f"{pl(n_subj, 'subject')} · {pl(n_q, 'debate question')} · "
         f"{pl(len(fams), 'argument family', 'argument families')} · "
         f"{pl(len(args), 'argument version')}",
         f"> **Source direction:** {data.get('direction', '')}",
         f"> **Opposition represented:** {data.get('opposition', '')}",
         f"> **Also:** {pl(len(data.get('stories') or []), 'story', 'stories')} · "
         f"{pl(len(data.get('teaching') or []), 'teaching segment')} · "
         f"{pl(len(data.get('scripture') or []), 'scripture reference')} · "
         f"{pl(len(data.get('lessons') or []), 'practical lesson')}",
         f"> **Inventory:** PARTIAL (AI extraction, not yet human-reviewed) · "
         f"**Coverage:** {data.get('coverage', 'full transcript')}", ">"]
    for s in data["speakers"]:
        pos = " · ".join(v for v in (s.get("religious_position"), s.get("metaphysical_position"),
                                     s.get("scientific_views")) if v)
        L.append(f"> - **{s.get('name', '')}** ({s.get('role', '')}){': ' + pos if pos else ''}")
    L += [">", f"> {data['summary']}", "",
          f"This source covers {pl(n_subj, 'subject')}, raises {pl(n_q, 'distinct debate question')}, "
          f"and presents {pl(len(args), 'argument version')}. These counts describe this video, not the whole field.", ""]

    if data.get("best_for_david"):
        L += ["## Best for David", ""]
        L += [f"- {link(b.get('argument', ''))} **{b.get('argument', '')}**: {b.get('why', '')}"
              for b in data["best_for_david"]] + [""]

    # ---- Subject map ----
    L += ["## Subject map", "", row(["Subject", "What is being argued", "Questions", "Arguments", "Where"]),
          "|---|---|---|---|---|"]
    for s in subj_rows or [{"subject_id": x} for x in sids]:
        sid = s.get("subject_id", "")
        sq = [q for q in qids if QUESTIONS.get(q, ("S-NEW",))[0] == sid]
        sa = [a for a in args if a.get("question_id") in sq]
        L.append(row([f"`{sid}` {SUBJECTS.get(sid, sid)}", s.get("summary", ""), len(sq), len(sa),
                      s.get("span", "")]))
    L.append("")

    # ---- Argument catalog ----
    L += ['<a id="argument-catalog"></a>', "", "## Argument catalog", "",
          row(["Argument", "Family · version", "In plain language", "Direction", "Question", "At"]),
          "|---|---|---|---|---|---|"]
    for a in args:
        ts = a.get("timestamps") or []
        L.append(row([link(a.get("name", "")) + " " + a.get("name", "")
                      + ("" if a.get("complete", True) else " *(incomplete)*"),
                      f"{a.get('family', '')} · {a.get('version', '')}",
                      a.get("plain") or a.get("conclusion", ""), a.get("stance", ""),
                      f"`{a.get('question_id', 'NEW')}`", at(ts[0]) if ts else ""]))
    L.append("")

    # ---- Questions that remain open ----
    L += [f"## Questions that remain open ({n_q})", "",
          row(["#", "Neutral question", "Source's answer", "Alternatives (how represented)",
               "Split point", "Verdict", "Next needed", "Args"]),
          "|---|---|---|---|---|---|---|---|"]
    for i, d in enumerate(debates, 1):
        qid = d.get("question_id", "")
        rep = d.get("rival_representation") or ("direct" if d.get("rival_advocated") else "")
        L.append(row([i, f"`{qid}` {qlabel(qid, data)}", d.get("position_defended", ""),
                      d.get("rival_view", "") + (f" *({rep})*" if rep else ""),
                      d.get("split_point", ""), d.get("verdict", ""), d.get("next_needed", ""),
                      " ".join(link(n) for n in d.get("arguments", []))]))
    L.append("")

    # ---- Stories, teaching, concepts, lessons ----
    stories = sorted(data.get("stories") or [], key=lambda s: secs(s.get("start") or "0"))
    for i, s in enumerate(stories, 1):
        s["id"] = f"S{i:02d}"
    stories.sort(key=lambda s: -(score(s, STORY_SCALES) or 0))
    if stories:
        L += ['<a id="stories"></a>', "", f"## Stories and testimonies ({len(stories)})", "",
              "*How well each story is told (AI proposal, 1 weak · 3 usable · 5 especially strong) "
              "is rated separately from whether it is verified.*", ""]
        for s in stories:
            L += [f"### {s['id']} · 📖 {s.get('title', '')}", "",
                  f"`told {score(s, STORY_SCALES) or '?'}/5` · {s.get('story_type', '')} · "
                  f"told by {s.get('teller', '')} · {at(s['start']) if s.get('start') else ''}"
                  f"{'–' + s['end'] if s.get('end') else ''} · evidence: {s.get('evidence_status', '')} · "
                  f"presented as {s.get('presented_as', '')}", "",
                  s.get("summary", ""), ""]
            r = s.get("ratings") or {}
            rows = [("Conflict → turning point → outcome",
                     " → ".join(x for x in (s.get("conflict"), s.get("turning_point"), s.get("outcome")) if x)),
                    ("Speaker's lesson", s.get("lesson", "")),
                    ("Scripture", ", ".join(s.get("scripture") or [])),
                    ("Useful for", s.get("useful_for", "")),
                    ("Offered as evidence for", link(s["used_as_evidence_for"]) + " "
                     + s["used_as_evidence_for"] if s.get("used_as_evidence_for") else "told for its own sake"),
                    ("Ratings", "; ".join(f"{k.replace('_', ' ')} {(r.get(k) or {}).get('score', '–')} "
                                         f"({(r.get(k) or {}).get('reason', '')})" for k in STORY_SCALES)),
                    ("David's rating", "")]
            L += [f"- **{k}:** {v}" for k, v in rows] + [""]
            themes = [f"#story/{tag(t)}" for t in s.get("themes", []) if tag(t)]
            if themes:
                L += [" ".join(themes), ""]
    teaching = data.get("teaching") or []
    if teaching:
        L += [f"## Bible teaching ({len(teaching)})", "",
              row(["Taught", "Speaker", "Approach", "Clarity / context / usefulness", "Summary", "At"]),
              "|---|---|---|---|---|---|"]
        for t in teaching:
            L.append(row([t.get("topic", ""), t.get("speaker", ""), t.get("approach", ""),
                          scores_line(t, TEACH_SCALES), t.get("summary", ""),
                          at(t["start"]) if t.get("start") else ""]))
        L.append("")
    if data.get("concepts"):
        L += ["## Theological concepts", ""]
        L += [f"- **[[{c.get('concept', '')}]]**: {c.get('interpretation', '')} "
              f"({c.get('speaker', '')}{', ' + at(c['at']) if c.get('at') else ''})"
              for c in data["concepts"]] + [""]
    if data.get("lessons"):
        L += ["## Practical lessons", ""]
        L += [f"- {x.get('lesson', '')} *(supported by: {x.get('supported_by', '')})*"
              f"{' ' + at(x['at']) if x.get('at') else ''}" for x in data["lessons"]] + [""]

    # ---- The disagreement: exchanges that actually occur ----
    L += ['<a id="objections"></a>', "", "## The disagreement — objections and replies", ""]
    if exchanges:
        L += [row(["#", "Target", "Objection (by, mode)", "Reply", "Follow-up", "Coverage"]),
              "|---|---|---|---|---|---|"]
        for i, e in enumerate(sorted(exchanges, key=lambda e: secs(e.get("objection_at", "0"))), 1):
            L.append(row([i, link(e.get("target_argument", "")),
                          f"{e.get('objection', '')} ({e.get('objection_by', '')}, "
                          f"{e.get('mode', '')}, {at(e['objection_at']) if e.get('objection_at') else ''})",
                          e.get("reply", "") + (f" ({at(e['reply_at'])})" if e.get("reply_at") else ""),
                          e.get("follow_up", ""), e.get("coverage", "")]))
        L.append("")
    else:
        L += ["No objection-and-reply exchanges occur in the source.", ""]
    L += ["*Analyst-proposed objections are listed per argument below as PROPOSED; "
          "they did not occur in the source.*", ""]

    # ---- How the arguments are built ----
    L += ['<a id="argument"></a>', "", f"## How the arguments are built ({len(args)})", ""]
    current = None
    for a in args:
        qid = a.get("question_id") or "NEW"
        if qid != current:
            current = qid
            L += [f"#### {qid} · {qlabel(qid, data)}", ""]
        ts = " ".join(at(t) for t in a.get("timestamps", []))
        L += [f"### {a['id']} · {a.get('name', '')}", "",
              f"`{a.get('strength', '?')}` · #arg/{tag(a.get('family', 'other'))} · "
              f"{a.get('version', '')} · {a.get('stance', '')} · {a.get('speaker', '')} · {ts}"
              + ("" if a.get("complete", True) else " · **incomplete**"), ""]
        for s in a.get("steps") or []:
            dis = f"  ⚔ *disputed by {s['disputed_by']}*" if s.get("disputed_by") else ""
            L.append(f"{s.get('n', '')}. ({s.get('role', '')}) {s.get('claim', '')}{dis}")
        L += ["", f"**Conclusion:** {a.get('conclusion', '')}", ""]
        q = a.get("quote") or {}
        if q.get("text"):
            L += [f"> \"{q['text']}\" ({at(q['at']) if q.get('at') else ''})", ""]
        opp = a.get("opposing_as_described", "")
        if opp:
            opp += " *(argued by an advocate)*" if a.get("opposing_advocated_in_video") \
                else " *(as described by the speaker)*"
        chk = a.get("checks") or {}
        rows = [("Hidden premises", "; ".join(a.get("hidden_premises") or [])),
                ("Rival positions", "; ".join(a.get("competing_positions") or [])),
                ("Opposing view", opp),
                ("Evidence cited", "; ".join(a.get("evidence_cited") or [])),
                ("Support", f"{a.get('support', '')} · falsifiable: {a.get('falsifiable', '')} · "
                            f"confidence: {a.get('confidence', '')}"),
                ("Strongest objection (PROPOSED)", a.get("strongest_objection", "")),
                ("Answered in video", a.get("objection_answered", "")),
                ("What survives", a.get("what_survives", "")),
                ("Not established", a.get("not_established", "")),
                ("Use for David", a.get("use_for_david", "")),
                ("Formal check", chk.get("formal", "")),
                ("Empirical check", chk.get("empirical", "")),
                ("Adversarial check", chk.get("adversarial", ""))]
        L += [f"- **{k}:** {v}" for k, v in rows if v] + [""]
        extra = [f"#topic/{tag(t)}" for t in a.get("tags", []) if tag(t)]
        if extra:
            L += [" ".join(extra), ""]

    # ---- Where to investigate ----
    L += ['<a id="argument-resources"></a>', "", "## Where to investigate each argument", ""]
    if data["resources"]:
        L += ["**Cited by the source**", "",
              row(["Spoken as", "Resolved identity", "Kind", "At", "Cited for", "Verification"]),
              "|---|---|---|---|---|---|"]
        for r in data["resources"]:
            L.append(row([r.get("spoken_as", ""), f"[[{r.get('identified_as', '')}]]"
                          + (f" ({r['author']})" if r.get("author") else ""), r.get("kind", ""),
                          at(r["at"]) if r.get("at") else "", r.get("supports", ""),
                          "IDENTITY_VERIFIED" if r.get("verified") else "UNRESOLVED"]))
        L.append("")
    queries = [(a, q) for a in args for q in a.get("research_queries") or []]
    if queries:
        L += ["**Further research (proposed searches, not citations)**", "",
              row(["Argument", "Proposed query", "Status"]), "|---|---|---|"]
        L += [row([link(a.get("name", "")), q, "NOT_SEARCHED"]) for a, q in queries] + [""]
    if data["claims_to_verify"]:
        L += ["**Claims to verify**", ""]
        L += [f"- [ ] {c.get('claim', '')} ({at(c['at']) if c.get('at') else ''}): {c.get('why', '')}"
              for c in data["claims_to_verify"]] + [""]
    if data["new_questions"]:
        L += ["## Proposed new map questions", ""]
        L += [f"- {q.get('subject_id', '')}: {q.get('question', '')}" for q in data["new_questions"]] + [""]

    L += ["## People, places, things", ""]
    for label, k, extra in [("People", "people", "role"), ("Places", "places", "context"),
                            ("Things", "things", "context")]:
        if data[k]:
            L += ["**" + label + ":** " + " · ".join(
                f"[[{x.get('name', '')}]]" + (f" ({x.get(extra)})" if x.get(extra) else "")
                for x in data[k]), ""]
    if data["scripture"]:
        L += ["**Scripture:** " + " · ".join(
            f"{s.get('ref', '')} ({s.get('mode', '')}{', ' + at(s['at']) if s.get('at') else ''})"
            for s in data["scripture"]), ""]
    if data["follow_ups"]:
        L += ["## Follow-ups", ""] + [f"- {f}" for f in data["follow_ups"]] + [""]

    L += lens_sections(m, at)
    L += ["---", "", "## Transcript", "", body.strip(), ""]
    return "\n".join(fm + L)


def lens_sections(m, at):
    """Extra passes from lens_pass.py, kept in <title>.lens.json beside the index JSON."""
    f = paths_for(m)[1]
    f = f.with_name(f.name.replace(".index.json", ".lens.json"))
    if not f.exists():
        return []
    L = []
    for name, lens in json.loads(f.read_text(encoding="utf-8")).items():
        L += [f"## Lens · {lens.get('title', name)}", "", f"*{lens.get('short', '')}*", ""]
        if lens.get("headline"):
            L += [lens["headline"], ""]
        for x in lens.get("items") or []:
            when = at(x["at"]) if x.get("at") else ""
            if x.get("end"):
                when += f"–{x['end']}"
            L += [f"- **{x.get('label', '')}** {when} · {'★' * int(x.get('score') or 0)}"]
            if x.get("quote"):
                L += [f"  > {x['quote']}"]
            L += [f"  {x.get('why', '')}" + (f" *Use:* {x['use']}" if x.get("use") else "")]
        L += [""]
    return L


def paths_for(m):
    """<Channel>/Videos/<title>.md and <Channel>/_API/<title>.index.json."""
    safe = re.sub(r'[<>:"/\\|?*]', "", m["title"])[:150]
    ch = OUT_ROOT / m["channel"]
    return ch / "Videos" / (safe + ".md"), ch / "_API" / (safe + ".index.json")


def clean_body(m):
    """Cleaned transcript body from clean_library.py's note, matched by video ID."""
    folder = CLEAN_ROOT / m["channel"]
    if folder.is_dir() and m["video_id"]:
        for f in folder.glob("*.md"):
            t = f.read_text(encoding="utf-8")
            if f'video_id: "{m["video_id"]}"' in t[:1500]:
                return t.split("## Transcript", 1)[-1]
    return None


def index_one(path, client, force=False, render_only=False):
    text = normalize(path.read_text(encoding="utf-8"))
    m = meta(text, path)
    out_md, out_json = paths_for(m)
    out_dir = out_md.parent
    if render_only:
        if not out_json.exists():
            return f"skip  {m['title']} (not indexed yet)"
        data = json.loads(out_json.read_text(encoding="utf-8"))
        for k in LIST_KEYS:
            data.setdefault(k, [])
        body = text.split("## Transcript", 1)[-1]
        m = {**m, **{k: v for k, v in (data.get("_meta") or {}).items() if k.startswith("source")}}
        out_md.write_text(render(m, data, clean_body(m) or body), encoding="utf-8")
        out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")  # keeps IDs
        return f"render {m['title']}"
    if time.time() - path.stat().st_mtime < SETTLE_SECONDS:
        return f"wait  {m['title']} (still being written; next run picks it up)"
    if out_json.exists() and not force:
        old = json.loads(out_json.read_text(encoding="utf-8")).get("_meta", {}).get("source_sha256")
        if old in (None, m["source_sha256"]):
            return f"skip  {m['title']}"
        # transcript changed since it was indexed: fall through and redo it
    body_words = len(text.split("## Transcript", 1)[-1].split())
    if body_words < MIN_WORDS:
        return f"empty {m['title']} ({body_words} words: no captions downloaded; re-fetch this transcript)"
    cleaned = clean_body(m)
    if not cleaned:
        return (f"wait  {m['title']} (no cleaned Obsidian note yet; run the Clean step first. "
                "Nothing goes to the API before conversion and cleaning)")

    body = text.split("## Transcript", 1)[-1]
    lines = [l for l in body.splitlines() if l.strip()]
    pieces = home.chunk_lines(lines, CHUNK_WORDS, 150)
    title = f"{m['title']} [video ID: {m['video_id']}]" if m["video_id"] else m["title"]
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    parts, tin, tout = [], 0, 0
    for i, piece in enumerate(pieces, 1):
        got, pin, pout = index_piece(client, piece, title, (i, len(pieces)))
        parts += got
        tin += pin
        tout += pout
    merged = merge(parts)
    usage = synthesize(client, merged, m, "\n".join(lines[:40]))
    tin += usage.prompt_tokens
    tout += usage.completion_tokens
    for a in merged["arguments"]:
        a["timestamps"] = collapse(a.get("timestamps") or [])

    out_dir.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render(m, merged, cleaned or body), encoding="utf-8")
    merged["_meta"] = {**m, "model": MODEL, "indexed_at": stamp, "chunks": len(pieces),
                       "tokens_in": tin, "tokens_out": tout, "note": str(out_md)}
    out_json.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(HERE / "log.jsonl", "a", encoding="utf-8") as log:
        log.write(json.dumps({"id": f"{stamp}_index_{home.slug(m['title'])}", "time": stamp,
                              "task": "index", "model": MODEL, "source": title,
                              "parts": len(pieces), "tokens_in": tin, "tokens_out": tout}) + "\n")
    return (f"done  {m['title']}  ({len(merged.get('debates', []))} debates, "
            f"{len(merged['arguments'])} args, {len(pieces)} chunk(s), {tin}+{tout} tokens"
            + ("" if cleaned else ", raw transcript: no cleaned note found") + ")")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="transcript files or channel folders")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--render-only", action="store_true",
                    help="rebuild notes from saved .index.json, no API calls")
    args = ap.parse_args()

    files = []
    for p in map(pathlib.Path, args.paths):
        files += sorted(p.glob("*.md")) if p.is_dir() else [p]
    files = [f for f in files if not f.name.startswith("_")][:args.limit]

    import openai
    client = openai.OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                           base_url="https://api.deepseek.com")
    with cf.ThreadPoolExecutor(args.workers) as pool:
        futs = {pool.submit(index_one, f, client, args.force, args.render_only): f for f in files}
        for fut in cf.as_completed(futs):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # keep the batch going
                print(f"FAIL  {futs[fut].name}: {e}", flush=True)


if __name__ == "__main__":
    main()
