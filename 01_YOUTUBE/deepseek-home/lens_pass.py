r"""Look at a video more closely through one or more LENSES (extra DeepSeek passes).

The standard index (index_video.py) maps every argument. A lens asks one more
focused question of the same cleaned transcript and adds a "Lens" section to
the video's note. Lenses live in lenses/<name>.md; add a file to add a lens.

Usage:
  python lens_pass.py --list                                   numbered focus menu + saved channel focuses
  python lens_pass.py "..\..\subtitles\<Channel>" --pick       ask what to focus on, save it, run
  python lens_pass.py "..\..\subtitles\<Channel>" --focus "3 4 5 16" --ask "prayer" --save
  python lens_pass.py "..\..\subtitles\<Channel>"              run the channel's saved focus
  flags: --limit N, --workers N, --force (redo), --dry-run (save prompts, no API)

A channel's saved focus (focus/<Channel>.json) is also applied by watch_pipeline.py to
every new video from that channel after it is indexed.

Output: obsidian_indexed/<Channel>/_API/<title>.lens.json, rendered into the note.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import home  # noqa: E402
import index_video as iv  # noqa: E402

LENS_DIR = HERE / "lenses"
CHUNK_WORDS = 7000


FOCUS_DIR = HERE / "focus"          # focus/<Channel>.json: the focus David chose for that channel
MAP_LENSES = {"david-arguments"}    # lenses that also need DEBATE_MAP.md in the prompt


def front(name):
    """Front matter of lenses/<name>.md as a dict, plus the body after it."""
    t = (LENS_DIR / f"{name}.md").read_text(encoding="utf-8")
    meta = {}
    fm = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if fm:
        for line in fm.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        t = t[fm.end():]
    return meta, re.sub(r"<!--.*?-->", "", t, flags=re.S).strip()


def lens_info(name):
    """(title, short, body) for one lens; the menu number lives in front matter `id`."""
    meta, body = front(name)
    if name in MAP_LENSES:
        body += "\n\n" + home.read_clean("DEBATE_MAP.md")
    return meta.get("title", name), meta.get("short", name), body


def all_lenses():
    """Lens names in menu-number order."""
    names = [p.stem for p in LENS_DIR.glob("*.md") if not p.stem.startswith("_")]
    return sorted(names, key=lambda n: (int(front(n)[0].get("id", 999)), n))


def resolve(tokens):
    """'3 4 5 16', '3,4,clips' or 'all' -> lens names. Numbers are the menu ids."""
    by_id = {front(n)[0].get("id"): n for n in all_lenses()}
    layers = load_layers()
    out = []
    for tok in re.split(r"[,\s]+", tokens.strip()):
        if not tok or tok == "0":
            continue
        if tok == "all":
            return all_lenses()
        if tok.upper() in layers:        # a layer letter expands to its focus numbers
            out += resolve(" ".join(str(x) for x in layers[tok.upper()]["focus"]))
            continue
        name = by_id.get(tok, tok)
        if not (LENS_DIR / f"{name}.md").exists():
            raise SystemExit(f"no focus '{tok}'. Run: python lens_pass.py --list")
        out.append(name)
    return list(dict.fromkeys(out))


def load_layers():
    f = HERE / "layers.json"
    d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return {k: v for k, v in d.items() if not k.startswith("_")}


def load_focus(channel):
    """{'lenses': [...], 'ask': '...'} saved for a channel, or None."""
    f = FOCUS_DIR / f"{channel}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def save_focus(channel, names, ask):
    FOCUS_DIR.mkdir(exist_ok=True)
    (FOCUS_DIR / f"{channel}.json").write_text(json.dumps(
        {"lenses": names, "ask": ask, "saved": dt.date.today().isoformat()}, indent=2), encoding="utf-8")


def lenses_for(names, ask):
    """Lens dict for run_one: saved lenses by name, plus an optional free-text ask."""
    out = {n: lens_info(n) for n in names}
    if ask:
        k, v = custom_lens(ask)
        out[k] = v
    return out


def custom_lens(ask):
    name = "ask-" + iv.slug(ask)[:40]
    body = (f"# LENS: custom focus\n\nDavid asked you to look closely at this in the video:\n\n"
            f"> {ask}\n\nFind every moment that bears on it, best first. In `why`, say how "
            f"the moment bears on his request.")
    return name, (ask[:60], ask, body)


def build(lens_body, piece, title, part, total):
    fmt = home.read_clean("lenses/_FORMAT.md")
    sections = [home.read_clean("HOME.md"), home.read_clean("GLOSSARY.md"),
                home.read_clean("STATE.md"), lens_body, fmt]
    head = f"# INPUT\nsource: {title}" + (f"\nchunk: {part} of {total}" if total > 1 else "")
    sections.append(f"{head}\n\n{piece}")
    return "\n\n---\n\n".join(s for s in sections if s)


def lens_path(m):
    return iv.paths_for(m)[1].with_name(iv.paths_for(m)[1].name.replace(".index.json", ".lens.json"))


def source(path):
    """(meta, cleaned body) from a raw subtitles/ transcript or a cleaned obsidian_transcripts/ note."""
    text = path.read_text(encoding="utf-8")
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    vid = re.search(r'^video_id:\s*"?([^"\n]+)"?', fm.group(1), re.M) if fm else None
    if vid:   # already a cleaned note
        title = re.search(r'^title:\s*"?(.*?)"?\s*$', fm.group(1), re.M)
        m = {"title": title.group(1) if title else path.stem, "video_id": vid.group(1),
             "channel": path.parent.name, "source_file": str(path)}
        return m, text.split("## Transcript", 1)[-1]
    m = iv.meta(iv.normalize(text), path)
    return m, iv.clean_body(m)


def redraw(m, cleaned):
    """Rewrite the video note so the lens sections appear (no API)."""
    out_md, out_json = iv.paths_for(m)
    if not out_json.exists():
        return
    data = json.loads(out_json.read_text(encoding="utf-8"))
    for k in iv.LIST_KEYS:
        data.setdefault(k, [])
    m = {**m, **{k: v for k, v in (data.get("_meta") or {}).items() if k.startswith("source")}}
    out_md.write_text(iv.render(m, data, cleaned), encoding="utf-8")
    out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_one(path, client, lenses, force=False, dry=False):
    m, cleaned = source(path)
    if not cleaned:
        return f"wait  {m['title']} (no cleaned note yet; run Clean first)"
    lines = [l for l in cleaned.splitlines() if l.strip()]
    if sum(len(l.split()) for l in lines) < iv.MIN_WORDS:
        return f"empty {m['title']}"

    store = lens_path(m)
    saved = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {}
    title = f"{m['title']} [video ID: {m['video_id']}]" if m["video_id"] else m["title"]
    pieces = home.chunk_lines(lines, CHUNK_WORDS, 150)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    done = []
    for name, (ltitle, short, body) in lenses.items():
        if name in saved and not force:
            continue
        items, follow, heads, tin, tout = [], [], [], 0, 0
        for i, piece in enumerate(pieces, 1):
            prompt = build(body, "\n".join(piece), title, i, len(pieces))
            if dry:
                req = HERE / "requests" / f"{stamp}_lens-{name}_{home.slug(m['title'])}_p{i:02d}.md"
                req.parent.mkdir(exist_ok=True)
                req.write_text(prompt, encoding="utf-8")
                continue
            data, usage = iv.call(client, prompt)
            items += data.get("items") or []
            follow += data.get("follow_ups") or []
            if data.get("headline"):
                heads.append(data["headline"])
            tin += usage.prompt_tokens
            tout += usage.completion_tokens
        if dry:
            done.append(f"{name} (dry run: {len(pieces)} prompt(s) saved)")
            continue
        items.sort(key=lambda x: (-int(x.get("score") or 0), iv.secs(x.get("at") or "0:00")))
        saved[name] = {"title": ltitle, "short": short, "headline": " ".join(heads),
                       "items": items[:15], "follow_ups": list(dict.fromkeys(follow)),
                       "ran_at": stamp, "model": iv.MODEL, "tokens_in": tin, "tokens_out": tout}
        with open(HERE / "log.jsonl", "a", encoding="utf-8") as log:
            log.write(json.dumps({"id": f"{stamp}_lens-{name}_{home.slug(m['title'])}",
                                  "time": stamp, "task": f"lens:{name}", "model": iv.MODEL,
                                  "source": title, "parts": len(pieces),
                                  "tokens_in": tin, "tokens_out": tout}) + "\n")
        done.append(f"{name} {len(items)} items, {tin}+{tout} tok")
    if not done:
        return f"skip  {m['title']} (lenses already run; --force to redo)"
    if not dry:
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8")
        redraw(m, cleaned)
    return f"lens  {m['title']}  ({'; '.join(done)})"


def print_menu():
    for n in all_lenses():
        meta, _ = front(n)
        print(f"  {meta.get('id', '?'):>3}  {meta.get('title', n):<32} {meta.get('short', '')}")
    layers = load_layers()
    if layers:
        print("\n  Layers (a letter = a bundle of the numbers above):")
        for k, v in layers.items():
            print(f"  {k:>3}  {v['title']:<32} {' '.join(str(x) for x in v['focus'])}")


def pick(channel):
    """Ask David what to focus on for a channel and save it. Returns (names, ask)."""
    old = load_focus(channel)
    print(f"\nWhat should DeepSeek focus on in '{channel}'?")
    if old:
        print(f"  (saved now: {' '.join(old['lenses']) or 'none'}"
              + (f"; ask: {old['ask']}" if old.get("ask") else "") + ")  Enter = keep it")
    print_menu()
    raw = input("\nNumbers and/or layer letters, e.g. C 7 16 (0 = none, Enter = keep): ").strip()
    if not raw and old:
        return old["lenses"], old.get("ask", "")
    names = resolve(raw)
    ask = input("Anything else, in your own words (Enter = nothing): ").strip()
    save_focus(channel, names, ask)
    print(f"Saved for '{channel}': {', '.join(names) or 'none'}" + (f" + '{ask}'" if ask else ""))
    return names, ask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="transcript files or channel folders")
    ap.add_argument("--lens", "--focus", dest="lens", default="",
                    help="menu numbers or names, e.g. '3 4 5 16' or 'clips,soft-spots' or 'all'")
    ap.add_argument("--ask", default="", help="custom one-off focus in your own words")
    ap.add_argument("--save", action="store_true",
                    help="save --focus/--ask as the standing focus for each channel folder given")
    ap.add_argument("--pick", action="store_true",
                    help="ask interactively what to focus on for each channel folder, save it, then run")
    ap.add_argument("--pick-only", action="store_true", help="like --pick but do not run")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true", help="show the numbered focus menu")
    args = ap.parse_args()

    if args.list:
        print_menu()
        for f in sorted(FOCUS_DIR.glob("*.json")) if FOCUS_DIR.is_dir() else []:
            d = json.loads(f.read_text(encoding="utf-8"))
            print(f"  saved  {f.stem}: {', '.join(d['lenses']) or 'none'}"
                  + (f" + ask '{d['ask']}'" if d.get("ask") else ""))
        return
    if not args.paths:
        ap.error("give transcript files or channel folders")

    dirs = [p for p in map(pathlib.Path, args.paths) if p.is_dir()]
    if args.pick or args.pick_only:
        for d in dirs:
            pick(d.name)
        if args.pick_only:
            return
    elif args.save:
        for d in dirs:
            save_focus(d.name, resolve(args.lens), args.ask.strip())
            print(f"saved focus for {d.name}")

    files = []
    for p in map(pathlib.Path, args.paths):
        files += sorted(p.glob("*.md")) if p.is_dir() else [p]
    files = [f for f in files if not f.name.startswith("_")][:args.limit]

    # explicit --focus/--ask wins; otherwise each file uses its channel's saved focus
    explicit = lenses_for(resolve(args.lens), args.ask.strip()) if (args.lens or args.ask) else None
    plan = {}
    for f in files:
        if explicit is not None:
            plan[f] = explicit
        else:
            saved = load_focus(f.parent.name)
            if saved:
                plan[f] = lenses_for(saved["lenses"], saved.get("ask", ""))
    if not plan:
        ap.error("no focus given and none saved for these channels; use --focus, --ask or --pick")

    client = None
    if not args.dry_run:
        import openai
        client = openai.OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                               base_url="https://api.deepseek.com")
    with cf.ThreadPoolExecutor(args.workers) as pool:
        futs = {pool.submit(run_one, f, client, lz, args.force, args.dry_run): f for f, lz in plan.items()}
        for fut in cf.as_completed(futs):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # keep the batch going
                print(f"FAIL  {futs[fut].name}: {e}", flush=True)


if __name__ == "__main__":
    main()
