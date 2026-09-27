from pathlib import Path  # ONE_MENU
import os  # ONE_MENU
"""Build the cross-channel catalog from every obsidian_indexed/*/*.index.json.

No API calls. Writes:
  obsidian_indexed/<Channel>/_CHANNEL_OVERVIEW.md   meta view of one channel
  obsidian_indexed/_DEBATES/<Q-ID>.md               every argument on one question, all channels
  obsidian_indexed/_DEBATES/_INDEX.md               all questions with counts
  obsidian_indexed/catalog.xlsx                     Videos / Arguments / Exchanges / Channels / Questions
  obsidian_indexed/catalog.sqlite                   the same tables, for SQL

Run it any time after indexing: python build_catalog.py
"""
import collections
import datetime as dt
import json
import pathlib
import re
import sqlite3
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from index_video import (OUT_ROOT, QUESTIONS, SUBJECTS, STORY_SCALES, TEACH_SCALES,  # noqa: E402
                         book, score, secs)

SUBS_ROOT = Path(os.environ.get("ONE_MENU_PATH_YT_SUBTITLES") or OUT_ROOT.parent / "subtitles")
RANK = {"strong": 0, "moderate": 1, "weak": 2}


def load():
    videos = []
    for f in sorted(OUT_ROOT.glob("*/_API/*.index.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d["_stem"] = f.name[:-len(".index.json")]
        videos.append(d)
    return videos


def watch(v, ts):
    vid = v["_meta"].get("video_id")
    return f"https://www.youtube.com/watch?v={vid}&t={secs(ts)}s" if vid and ts else ""


def qtext(qid):
    return QUESTIONS.get(qid, ("S-NEW", qid))[1]


def rows(videos):
    """Flatten into table rows shared by Excel and SQLite."""
    V, A, E = [], [], []
    for v in videos:
        m = v["_meta"]
        args = v.get("arguments", [])
        subj = {s.get("subject_id"): s for s in v.get("subjects") or []}
        V.append({
            "video_id": m.get("video_id", ""), "channel": m["channel"], "title": m["title"],
            "url": f"https://www.youtube.com/watch?v={m.get('video_id')}" if m.get("video_id") else "",
            "format": v.get("format", ""), "direction": v.get("direction", ""),
            "opposition": v.get("opposition", ""),
            "speakers": "; ".join(s.get("name", "") for s in v.get("speakers", [])),
            "summary": v.get("summary", ""),
            "main_subjects": "; ".join(SUBJECTS.get(k, k) for k, s in subj.items()
                                       if s.get("depth") in ("main-focus", "substantial")),
            "questions": "; ".join(sorted({a.get("question_id", "") for a in args})),
            "question_count": len(v.get("debates") or []),
            "argument_count": len(args),
            "exchange_count": len(v.get("exchanges") or []),
            "resources": "; ".join(r.get("identified_as") or r.get("spoken_as", "")
                                   for r in v.get("resources", [])),
            "note": m.get("note", ""), "indexed_at": m.get("indexed_at", ""),
            "status": "indexed (AI, unreviewed)", "priority": "", "notes": ""})
        for a in args:
            ts = a.get("timestamps") or []
            A.append({
                "argument_id": f"{m.get('video_id', m['title'][:20])}-{a.get('id', '')}",
                "video_id": m.get("video_id", ""), "channel": m["channel"], "video_title": m["title"],
                "subject": SUBJECTS.get(QUESTIONS.get(a.get("question_id"), ("S-NEW",))[0], "NEW"),
                "question_id": a.get("question_id", ""), "question": qtext(a.get("question_id", "")),
                "name": a.get("name", ""), "family": a.get("family", ""), "version": a.get("version", ""),
                "speaker": a.get("speaker", ""), "stance": a.get("stance", ""),
                "strength": a.get("strength", ""), "support": a.get("support", ""),
                "provenance": a.get("provenance", ""), "attributed_to": a.get("attributed_to", ""),
                "start": ts[0] if ts else "", "link": watch(v, ts[0] if ts else ""),
                "plain": a.get("plain") or a.get("conclusion", ""),
                "strongest_objection": a.get("strongest_objection", ""),
                "what_survives": a.get("what_survives", ""),
                "use_for_david": a.get("use_for_david", ""),
                "note_link": f"[[{v['_stem']}#{a.get('id', '')} · {a.get('name', '')}]]"})
        for i, e in enumerate(v.get("exchanges") or [], 1):
            E.append({"video_id": m.get("video_id", ""), "channel": m["channel"], "order": i,
                      "target_argument": e.get("target_argument", ""), "objection": e.get("objection", ""),
                      "objection_by": e.get("objection_by", ""), "mode": e.get("mode", ""),
                      "reply": e.get("reply", ""), "coverage": e.get("coverage", ""),
                      "link": watch(v, e.get("objection_at", ""))})
    S, P, T, K, L = [], [], [], [], []
    for v in videos:
        m = v["_meta"]
        base = {"video_id": m.get("video_id", ""), "channel": m["channel"], "video_title": m["title"]}
        for s in v.get("stories") or []:
            r = s.get("ratings") or {}
            S.append({**base, "story_id": f"{m.get('video_id', '')}-{s.get('id', '')}",
                      "title": s.get("title", ""), "story_type": s.get("story_type", ""),
                      "teller": s.get("teller", ""), "start": s.get("start", ""), "end": s.get("end", ""),
                      "link": watch(v, s.get("start", "")), "summary": s.get("summary", ""),
                      "lesson": s.get("lesson", ""), "presented_as": s.get("presented_as", ""),
                      "evidence_status": s.get("evidence_status", ""),
                      "themes": "; ".join(s.get("themes") or []),
                      "scripture": "; ".join(s.get("scripture") or []),
                      "useful_for": s.get("useful_for", ""),
                      **{f"ai_{k}": (r.get(k) or {}).get("score", "") for k in STORY_SCALES},
                      "ai_told_avg": score(s, STORY_SCALES),
                      **{f"david_{k}": "" for k in STORY_SCALES}, "david_notes": "",
                      "note_link": f"[[{v['_stem']}#{s.get('id', '')} · 📖 {s.get('title', '')}]]"})
        for s in v.get("scripture") or []:
            P.append({**base, "ref": s.get("ref", ""), "book": book(s.get("ref", "")),
                      "mode": s.get("mode", ""), "speaker": s.get("speaker", ""), "at": s.get("at", ""),
                      "link": watch(v, s.get("at", "")), "context": s.get("context", "")})
        for t in v.get("teaching") or []:
            r = t.get("ratings") or {}
            T.append({**base, "topic": t.get("topic", ""), "speaker": t.get("speaker", ""),
                      "approach": t.get("approach", ""), "start": t.get("start", ""),
                      "link": watch(v, t.get("start", "")), "summary": t.get("summary", ""),
                      **{f"ai_{k}": (r.get(k) or {}).get("score", "") for k in TEACH_SCALES},
                      "ai_avg": score(t, TEACH_SCALES), "david_rating": ""})
        for c in v.get("concepts") or []:
            K.append({**base, "concept": c.get("concept", ""), "interpretation": c.get("interpretation", ""),
                      "speaker": c.get("speaker", ""), "link": watch(v, c.get("at", ""))})
        for x in v.get("lessons") or []:
            L.append({**base, "lesson": x.get("lesson", ""), "supported_by": x.get("supported_by", ""),
                      "link": watch(v, x.get("at", ""))})

    C = []
    for ch, vs in _group(V, "channel").items():
        chargs = [a for a in A if a["channel"] == ch]
        downloaded = len(list((SUBS_ROOT / ch).glob("*.md"))) if (SUBS_ROOT / ch).is_dir() else ""
        C.append({"channel": ch, "downloaded": downloaded, "indexed": len(vs),
                  "arguments": len(chargs),
                  "top_questions": "; ".join(q for q, _ in collections.Counter(
                      a["question_id"] for a in chargs).most_common(8)),
                  "top_speakers": "; ".join(s for s, _ in collections.Counter(
                      x.strip() for r in vs for x in r["speakers"].split(";") if x.strip()).most_common(6)),
                  "last_indexed": max(r["indexed_at"] for r in vs)})
    Q = []
    for qid, qa in _group(A, "question_id").items():
        st = collections.Counter(a["strength"] for a in qa)
        Q.append({"question_id": qid, "subject": qa[0]["subject"], "question": qtext(qid),
                  "arguments": len(qa), "videos": len({a["video_id"] for a in qa}),
                  "channels": len({a["channel"] for a in qa}),
                  "strong": st["strong"], "moderate": st["moderate"], "weak": st["weak"]})
    return {"Videos": V, "Arguments": A, "Exchanges": E, "Stories": S, "Scripture": P,
            "Teaching": T, "Concepts": K, "Lessons": L, "Channels": C,
            "Questions": sorted(Q, key=lambda q: -q["arguments"])}


def _group(items, key):
    out = collections.defaultdict(list)
    for it in items:
        out[it[key]].append(it)
    return out


def cell(x):
    return str(x).replace("|", "\\|").replace("\n", " ")


def table(header, body):
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + \
           ["| " + " | ".join(cell(c) for c in r) + " |" for r in body]


def channel_overviews(videos, t):
    A, E = t["Arguments"], t["Exchanges"]
    by_channel = collections.defaultdict(list)
    for v in videos:
        by_channel[v["_meta"]["channel"]].append(v)
    for ch, vs in by_channel.items():
        args = [a for a in A if a["channel"] == ch]
        ex = [e for e in E if e["channel"] == ch]
        downloaded = len(list((SUBS_ROOT / ch).glob("*.md"))) if (SUBS_ROOT / ch).is_dir() else "?"
        strength = collections.Counter(a["strength"] for a in args)
        prov = collections.Counter(a["provenance"] or "unrecorded" for a in args)
        cover = collections.Counter(e["coverage"] for e in ex)
        fmt = collections.Counter(v.get("format", "") for v in vs)
        advocate = sum(1 for v in vs if v.get("opposition") in ("defended-by-advocate", "mixed"))
        spk = collections.Counter(s.get("name", "") for v in vs for s in v.get("speakers", []))
        L = ["---", f"title: {json.dumps(ch + ' — channel overview')}", "type: channel-overview",
             f"channel: {json.dumps(ch)}", f"videos_downloaded: {downloaded}",
             f"videos_indexed: {len(vs)}", f"arguments: {len(args)}",
             f"updated: {dt.date.today().isoformat()}", "tags: [\"channel-overview\"]", "---", "",
             f"# {ch} — channel overview", "",
             f"> [!abstract] {len(vs)} of {downloaded} downloaded videos indexed · {len(args)} arguments · "
             f"{len({a['question_id'] for a in args})} distinct debate questions",
             f"> **Formats:** " + ", ".join(f"{k or '?'} {n}" for k, n in fmt.most_common()),
             f"> **Opposition actually present:** {advocate} of {len(vs)} videos have an advocate of the rival view",
             f"> **Argument strength (AI assessment):** strong {strength['strong']} · "
             f"moderate {strength['moderate']} · weak {strength['weak']}",
             f"> **Origin:** " + ", ".join(f"{k} {n}" for k, n in prov.most_common()),
             f"> **Objections raised in-source:** {len(ex)} · " + ", ".join(
                 f"{k.lower().replace('_', ' ')} {n}" for k, n in cover.most_common()), "",
             "*Counts cover indexed videos only. Strength is an AI rating, not a verdict; "
             "'win or lose' is read from whether in-source objections were answered.*", ""]
        qa = _group(args, "question_id")
        L += ["## Debates this channel covers", ""]
        L += table(["Question", "Subject", "Videos", "Args", "Strong/Mod/Weak", "Page"],
                   [[f"`{q}` {qtext(q)}", g[0]["subject"], len({a['video_id'] for a in g}), len(g),
                     "/".join(str(sum(a["strength"] == s for a in g)) for s in ("strong", "moderate", "weak")),
                     f"[[_DEBATES/{q}|open]]"]
                    for q, g in sorted(qa.items(), key=lambda kv: -len(kv[1]))])
        best = sorted([a for a in args if a["strength"] == "strong"], key=lambda a: a["question_id"])
        L += ["", f"## Strongest arguments ({len(best)})", ""]
        L += [f"- {a['note_link']} · `{a['question_id']}` · {a['speaker']} · "
              f"{a['provenance'] or '?'}{' (' + a['attributed_to'] + ')' if a['attributed_to'] else ''}"
              for a in best] or ["- none rated strong yet"]
        st = sorted([s for s in t["Stories"] if s["channel"] == ch],
                    key=lambda s: -(s["ai_told_avg"] or 0))
        L += ["", f"## Notable stories ({len(st)} total)", ""]
        L += [f"- {s['note_link']} · told {s['ai_told_avg'] or '?'}/5 · {s['story_type']} · "
              f"evidence: {s['evidence_status']} · {s['summary']}" for s in st[:10]] or ["- none yet"]
        tc = sorted([x for x in t["Teaching"] if x["channel"] == ch], key=lambda x: -(x["ai_avg"] or 0))
        L += ["", "## Strongest teaching segments", ""]
        L += [f"- **{x['topic']}** ({x['speaker']}, {x['approach']}) · {x['ai_avg'] or '?'}/5 · "
              f"[{x['start']}]({x['link']})" for x in tc[:8]] or ["- none yet"]
        chap = collections.Counter(re.sub(r"(\d+):.*$", r"\1", p["ref"]) for p in t["Scripture"]
                                   if p["channel"] == ch and p["ref"])
        L += ["", "## Most-used Bible passages", ""]
        L += [f"- {r} ({n}×)" for r, n in chap.most_common(12)] or ["- none yet"]
        con = collections.Counter(c["concept"].lower() for c in t["Concepts"] if c["channel"] == ch)
        L += ["", "## Recurring theological concepts", ""]
        L += [f"- [[{c}]] ({n}×)" for c, n in con.most_common(12)] or ["- none yet"]
        L += ["", "## Recurring speakers", ""]
        L += [f"- [[{s}]] ({n} video{'s' if n > 1 else ''})" for s, n in spk.most_common(15)]
        L += ["", "## Videos", ""]
        L += table(["Video", "Format", "Debates", "Args", "Direction"],
                   [[f"[[{v['_stem']}]]", v.get("format", ""), len(v.get("debates") or []),
                     len(v.get("arguments", [])), v.get("direction", "")] for v in vs])
        (OUT_ROOT / ch / "_CHANNEL_OVERVIEW.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def debate_pages(A, Q):
    d = OUT_ROOT / "_DEBATES"
    d.mkdir(exist_ok=True)
    for qid, qa in _group(A, "question_id").items():
        qa.sort(key=lambda a: (RANK.get(a["strength"], 3), a["channel"]))
        L = ["---", f"title: {json.dumps(qid + ' · ' + qtext(qid))}", "type: debate-question",
             f"question_id: {qid}", f"subject: {json.dumps(qa[0]['subject'])}",
             f"arguments: {len(qa)}", f"tags: [\"debate\", \"q/{qid.lower()}\"]", "---", "",
             f"# {qtext(qid)}", "", f"`{qid}` · {qa[0]['subject']} · {len(qa)} arguments from "
             f"{len({a['video_id'] for a in qa})} videos across {len({a['channel'] for a in qa})} channels", ""]
        for stance, g in sorted(_group(qa, "stance").items()):
            L += [f"## {stance or 'unclassified'} ({len(g)})", ""]
            L += table(["Argument", "Strength", "Speaker", "Origin", "Video", "Jump"],
                       [[a["note_link"] + " — " + a["plain"], a["strength"], a["speaker"],
                         a["provenance"] + (f" ({a['attributed_to']})" if a["attributed_to"] else ""),
                         f"{a['channel']}: {a['video_title']}", f"[{a['start']}]({a['link']})" if a["link"] else ""]
                        for a in g]) + [""]
        (d / f"{qid}.md").write_text("\n".join(L), encoding="utf-8")
    L = ["# All debate questions", "", f"Updated {dt.date.today().isoformat()}", ""]
    L += table(["Question", "Subject", "Args", "Videos", "Channels", "Strong/Mod/Weak"],
               [[f"[[{q['question_id']}]] {q['question']}", q["subject"], q["arguments"], q["videos"],
                 q["channels"], f"{q['strong']}/{q['moderate']}/{q['weak']}"] for q in Q])
    (d / "_INDEX.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def safe(s, n=90):
    return re.sub(r'[<>:"/\\|?*#^\[\]]', "", str(s)).strip()[:n] or "untitled"


def write_record(path, fields, body):
    """Write one record note. Fields David typed (david_*) are carried over, never overwritten."""
    keep = {}
    if path.exists():
        parts = path.read_text(encoding="utf-8").split("---", 2)
        for line in (parts[1] if len(parts) > 2 else "").splitlines():
            k, _, v = line.partition(":")
            if k.startswith("david_") and v.strip() not in ("", '""'):
                keep[k] = v.strip()
    fm = ["---"] + [f"{k}: {keep.get(k) or json.dumps(v, ensure_ascii=False)}" for k, v in fields.items()]
    fm += [f"{k}: {v}" for k, v in keep.items() if k not in fields] + ["---", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fm) + body, encoding="utf-8")


def record_notes(videos):
    """One small note per argument, story and teaching segment (inside each channel),
    and one shared note per person/place/thing, cited resource and concept."""
    people, resources, concepts = (collections.defaultdict(list) for _ in range(3))
    for v in videos:
        m = v["_meta"]
        ch, vid, stem = OUT_ROOT / m["channel"], m.get("video_id", ""), v["_stem"]
        yt = lambda ts: watch(v, ts)  # noqa: E731
        for a in v.get("arguments", []):
            aid = f"{vid}-{a.get('id', '')}"
            ts = (a.get("timestamps") or [""])[0]
            steps = "\n".join(f"{s.get('n', '')}. ({s.get('role', '')}) {s.get('claim', '')}"
                              + (f" ⚔ *disputed by {s['disputed_by']}*" if s.get("disputed_by") else "")
                              for s in a.get("steps") or [])
            body = (f"# {a.get('name', '')}\n\n{a.get('plain', '')}\n\n{steps}\n\n"
                    f"**Conclusion:** {a.get('conclusion', '')}\n\n"
                    f"- **Strongest objection (PROPOSED):** {a.get('strongest_objection', '')}\n"
                    f"- **What survives:** {a.get('what_survives', '')}\n"
                    f"- **Not established:** {a.get('not_established', '')}\n"
                    f"- **Use for David:** {a.get('use_for_david', '')}\n\n"
                    f"Source: [[{stem}#{a.get('id', '')} · {a.get('name', '')}|{m['title']}]]"
                    + (f" · [watch at {ts}]({yt(ts)})" if ts else "") +
                    f" · debate: [[{a.get('question_id', '')}]]\n")
            write_record(ch / "Arguments" / f"{aid} {safe(a.get('name', ''))}.md", {
                "type": "argument", "argument_id": aid, "video_id": vid, "channel": m["channel"],
                "question_id": a.get("question_id", ""), "family": a.get("family", ""),
                "version": a.get("version", ""), "stance": a.get("stance", ""),
                "speaker": a.get("speaker", ""), "strength": a.get("strength", ""),
                "support": a.get("support", ""), "provenance": a.get("provenance", ""),
                "attributed_to": a.get("attributed_to", ""), "admission": "candidate",
                "tags": ["argument", f"q/{a.get('question_id', '').lower()}",
                         "arg/" + a.get("family", "other")],
                "david_strength": "", "david_notes": ""}, body)
        for s in v.get("stories") or []:
            sid = f"{vid}-{s.get('id', '')}"
            r = s.get("ratings") or {}
            rows = "\n".join(f"| {k.replace('_', ' ')} | {(r.get(k) or {}).get('score', '')} | "
                             f"{(r.get(k) or {}).get('reason', '')} |" for k in STORY_SCALES)
            body = (f"# {s.get('title', '')}\n\n{s.get('summary', '')}\n\n"
                    f"**Setup → turning point → outcome:** {s.get('conflict', '')} → "
                    f"{s.get('turning_point', '')} → {s.get('outcome', '')}\n\n"
                    f"**Lesson:** {s.get('lesson', '')}\n\n"
                    f"| AI rating | Score | Reason |\n|---|---|---|\n{rows}\n\n"
                    f"Source: [[{stem}#{s.get('id', '')} · 📖 {s.get('title', '')}|{m['title']}]]"
                    + (f" · [watch at {s['start']}]({yt(s['start'])})" if s.get("start") else "") + "\n")
            write_record(ch / "Stories" / f"{sid} {safe(s.get('title', ''))}.md", {
                "type": "story", "story_id": sid, "video_id": vid, "channel": m["channel"],
                "story_type": s.get("story_type", ""), "teller": s.get("teller", ""),
                "presented_as": s.get("presented_as", ""), "evidence_status": s.get("evidence_status", ""),
                "used_as_evidence_for": s.get("used_as_evidence_for", ""),
                "ai_told_avg": score(s, STORY_SCALES), "themes": s.get("themes") or [],
                "scripture": s.get("scripture") or [], "admission": "candidate",
                "tags": ["story"] + [f"story/{t}" for t in s.get("themes") or []],
                **{f"david_{k}": "" for k in STORY_SCALES}, "david_notes": ""}, body)
        for i, t in enumerate(v.get("teaching") or [], 1):
            tid = f"{vid}-T{i:02d}"
            body = (f"# {t.get('topic', '')}\n\n{t.get('summary', '')}\n\n"
                    f"Approach: {t.get('approach', '')} · ratings: "
                    + " · ".join(f"{k.replace('_', ' ')} {((t.get('ratings') or {}).get(k) or {}).get('score', '–')}"
                                 for k in TEACH_SCALES)
                    + f"\n\nSource: [[{stem}|{m['title']}]]"
                    + (f" · [watch at {t['start']}]({yt(t['start'])})" if t.get("start") else "") + "\n")
            write_record(ch / "Teaching" / f"{tid} {safe(t.get('topic', ''))}.md", {
                "type": "teaching", "teaching_id": tid, "video_id": vid, "channel": m["channel"],
                "speaker": t.get("speaker", ""), "approach": t.get("approach", ""),
                "ai_avg": score(t, TEACH_SCALES), "tags": ["teaching"], "david_rating": ""}, body)
        for kind in ("people", "places", "things"):
            for x in v.get(kind) or []:
                if x.get("name"):
                    people[x["name"]].append((kind, x.get("role") or x.get("context", ""), m, stem))
        for r in v.get("resources") or []:
            key = r.get("identified_as") or r.get("spoken_as")
            if key:
                resources[key].append((r, m, stem, v))
        for c in v.get("concepts") or []:
            if c.get("concept"):
                concepts[c["concept"].lower()].append((c, m, stem, v))

    for name, apps in people.items():
        body = f"# {name}\n\n| Appears in | Channel | Role / context |\n|---|---|---|\n" + "\n".join(
            f"| [[{stem}]] | {m['channel']} | {role} |" for _, role, m, stem in apps) + "\n"
        write_record(OUT_ROOT / "_PEOPLE" / f"{safe(name)}.md",
                     {"type": apps[0][0].rstrip("s") if apps[0][0] != "people" else "person",
                      "name": name, "appearances": len(apps), "tags": ["entity"], "david_notes": ""}, body)
    for name, cites in resources.items():
        r0 = cites[0][0]
        body = (f"# {name}\n\n**Verification:** UNRESOLVED (identity not checked)\n\n"
                "| Cited in | As spoken | For the claim | At |\n|---|---|---|---|\n" + "\n".join(
                    f"| [[{stem}]] | {r.get('spoken_as', '')} | {r.get('supports', '')} | "
                    + (f"[{r['at']}]({watch(v, r['at'])})" if r.get("at") else "") + " |"
                    for r, m, stem, v in cites) + "\n")
        write_record(OUT_ROOT / "_EVIDENCE" / f"{safe(name)}.md",
                     {"type": "resource", "name": name, "kind": r0.get("kind", ""),
                      "author": r0.get("author", ""), "verification": "UNRESOLVED",
                      "cited_times": len(cites), "tags": ["resource"], "david_notes": ""}, body)
    for name, uses in concepts.items():
        body = f"# {name}\n\n| Interpretation | Speaker | Video |\n|---|---|---|\n" + "\n".join(
            f"| {c.get('interpretation', '')} | {c.get('speaker', '')} | [[{stem}]]"
            + (f" [{c['at']}]({watch(v, c['at'])})" if c.get("at") else "") + " |"
            for c, m, stem, v in uses) + "\n"
        write_record(OUT_ROOT / "_THEOLOGY" / f"{safe(name)}.md",
                     {"type": "concept", "concept": name, "uses": len(uses),
                      "tags": ["concept"], "david_notes": ""}, body)


def write_tables(tables):
    import openpyxl
    from openpyxl.styles import Font
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    db_path = OUT_ROOT / "catalog.sqlite"
    db_path.unlink(missing_ok=True)
    db = sqlite3.connect(db_path)
    for name, rs in tables.items():
        ws = wb.create_sheet(name)
        if not rs:
            continue
        cols = list(rs[0])
        ws.append(cols)
        for c in ws[1]:
            c.font = Font(bold=True)
        for r in rs:
            ws.append([r[c] for c in cols])
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        db.execute(f'CREATE TABLE "{name.lower()}" ({", ".join(f"[{c}]" for c in cols)})')
        db.executemany(f'INSERT INTO "{name.lower()}" VALUES ({", ".join("?" * len(cols))})',
                       [[str(r[c]) if not isinstance(r[c], (int, float)) else r[c] for c in cols] for r in rs])
    db.commit()
    db.close()
    wb.save(OUT_ROOT / "catalog.xlsx")


def main():
    videos = load()
    t = rows(videos)
    channel_overviews(videos, t)
    debate_pages(t["Arguments"], t["Questions"])
    record_notes(videos)
    write_tables(t)
    print(", ".join(f"{len(v)} {k.lower()}" for k, v in t.items()) + f" -> {OUT_ROOT}")


if __name__ == "__main__":
    main()
