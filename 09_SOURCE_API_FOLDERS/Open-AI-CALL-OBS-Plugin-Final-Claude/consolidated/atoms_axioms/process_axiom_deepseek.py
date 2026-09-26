"""
process_axiom_deepseek.py - DeepSeek-direct, high-parallelism AXIOM COMPANION runner.

Differences from process_axiom_pipeline.py:
  * Talks straight to api.deepseek.com (no OpenRouter hop, no free-tier ceiling).
  * Default 24 parallel workers instead of 4. DeepSeek does not publish a hard
    request-rate cap - it queues under load - so worker count is the throttle.
  * Recursive file discovery, and it accepts .lean as well as .md/.txt.
  * Skips vendored trees (.lake, .git, lake-packages, corrupt_backup).
  * Resume: a sha-keyed manifest means a re-run only does what is missing.
  * Each companion is written the moment it completes, so Ctrl+C keeps the work.
  * 429 / 5xx get exponential backoff with Retry-After honoured, plus a global
    cooldown so every worker backs off together instead of dogpiling.

Prompt, rendering, and the Nerve draft format are imported unchanged from
process_axiom_pipeline.py so output stays compatible with the old runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_axiom_pipeline import (  # noqa: E402
    build_axiom_draft_snapshot,
    parse_json,
    render_axiom_companion_md,
)

# ---------------------------------------------------------------------------
# De-anchored prompt.
#
# The original AXIOM_PROMPT in process_axiom_pipeline.py illustrates every
# field with the Existence axiom ("e.g. A1.1", "e.g. Existence", the
# exists-x/Domain-nonempty math core, ex nihilo, Heidegger). At low temperature
# the model copies that exemplar instead of reading the source: a 548-file run
# produced "A1.1 Existence" 526 times.
#
# This version keeps the identical output schema - render_axiom_companion_md
# and the Nerve draft builder are untouched - but replaces every worked example
# with a type description, and says plainly that identity comes from THIS file.
# ---------------------------------------------------------------------------
AXIOM_PROMPT = """You are the Lead Ontological Architect and Canonization Engineer for Theophysics.
You will be given ONE source file. Extract the rigorous components of the single most
important axiom, theorem, definition, or claim that THIS FILE actually states.

IDENTITY RULES - these override everything else:
1. Read the source before naming it. canonical_id, human_label, and math_core must be
   derived from the content of this specific file.
2. Do NOT default to the Existence axiom. "A1.1", "AX-001", "Existence", and the
   "there exists x / Domain is non-empty" formulation are NOT defaults - use them only
   if THIS file is genuinely about the existence primitive. Most files are not.
3. If the file is Lean 4, identify what it actually formalises: read its theorem,
   lemma, def, axiom, structure, and namespace names, and name the axiom after that
   real mathematical or theological content.
4. If the file states no axiom-like claim, say so honestly: set epistemic_status to
   "definition" and human_label to a short accurate description of the file's subject.
   Never invent a canonical axiom that is not there.
5. human_label must be a specific noun phrase drawn from this file's own vocabulary.
   Generic labels ("Existence", "Axiom", "Foundation") are only acceptable when the
   file is unmistakably about exactly that.

SUBSTANCE RULES:
6. "God Is" is the admitted root of the system. Do not pretend to derive God from a
   secular premise or from symbols alone. This is a constraint on how you reason - it
   is NOT an instruction to label every file as the God axiom.
7. Give the minimal formal and mathematical statement, and a self-refutation trap only
   where one genuinely applies.
8. Provide the full Six-Layer Explanatory Lens, grounded in this file's subject matter.
9. Answer the 5 Governing Questions without dodging.

Return ONLY valid JSON with exactly this structure. Every value below describes what to
put there - none of them are content to copy:
{
  "canonical_id": "<short id for THIS axiom, derived from the file, e.g. its chain position or a slug of its subject>",
  "legacy_id": "<prior id if the file states one, else empty string>",
  "human_label": "<specific noun phrase naming what THIS file is about>",
  "epistemic_status": "<one of: primitive | core_axiom | derived_lemma | definition>",
  "v2_3_tier": "<dependency tier, e.g. Tier 0 for no dependencies, else Tier 1 / Tier 2>",
  "domain": "<one of: Primordial | Physical | Metaphysical | Informational>",
  "formal_definition": "<precise formal statement of what THIS file claims>",
  "math_core": "<LaTeX for THIS file's central formal expression>",
  "math_word_equation": "<plain meaning of that expression>",
  "self_refutation_proof": "<step-by-step logic showing denial presupposes it, or empty string if not applicable>",
  "common_sense_meaning": "<plain-language explanation for a normal reader>",
  "governing_questions": {
    "answers": "<what question this atom answers>",
    "solves": "<what problem it solves>",
    "breaks_if_false": "<what breaks if it is false, weak, or misplaced>",
    "lets_next_carry": "<what it lets the next atom carry>",
    "unresolved": "<what remains unresolved after it>"
  },
  "what_this_solves": "<the explanatory burden this addresses>",
  "why_this_matters": "<why it must be explicit rather than smuggled in>",
  "six_layer_lens": {
    "rhetorical": "<linguistic/human framing for THIS subject>",
    "metaphysical": "<ontological reading of THIS subject>",
    "theological": "<theological mapping, with an explicit boundary reminder>",
    "scientific": "<how physics or science bears on THIS subject>",
    "mathematical": "<formal logic or set-theoretic encoding of THIS subject>",
    "encyclopedia": "<relevant external scholarly reference for THIS subject>"
  },
  "dependency_spine": {
    "direct_upstream": ["<nodes this depends on, or 'None (foundational)'>"],
    "direct_downstream": ["<nodes that depend on this>"],
    "blast_radius": "<one of: STRUCTURAL | LOCAL | INERT>"
  },
  "warrant": {
    "claim": "<the exact claim statement>",
    "evidence": "<what supports it>",
    "proof_test": "<the proof or specification that would test it>",
    "counterevidence": "<the strongest challenge to it>",
    "kill_condition": "<what would falsify it>",
    "assumptions": ["<assumptions required>"]
  },
  "orientation": {
    "ascent": "<from ordinary experience up to this formal claim>",
    "translation": "<ordinary language rendered into formal notation>",
    "descent": "<the formal claim returned to common-sense discourse>"
  },
  "bridges": {
    "home_domain": "<this atom's native domain>",
    "native_domains": ["<fields where it lives naturally>"],
    "bridge_candidates": ["<cross-domain connections worth drawing>"]
  }
}
Do NOT wrap in markdown fences. Output clean JSON only."""

DEEPSEEK_URL = os.environ.get("DEEPSEEK_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

SKIP_PARTS = (".lake", ".git", "lake-packages", "corrupt_backup")
EXTS = (".lean", ".md", ".txt")
MANIFEST_NAME = "_manifest.jsonl"

# Global throttle: one worker hitting 429 parks everybody briefly.
_throttle_until = 0.0
_throttle_lock = threading.Lock()
_print_lock = threading.Lock()
_counter_lock = threading.Lock()
_done = 0
_failed = 0


_DECL_RE = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+|partial\s+|unsafe\s+)*"
    r"(theorem|lemma|axiom|def|abbrev|structure|class|inductive|instance|namespace)\s+"
    r"([A-Za-z_][A-Za-z0-9_.'₀-₉]*)",
    re.M,
)


def lean_outline(text, limit=40):
    """Pull real declaration names out of a Lean/markdown source.

    Import blocks and licence headers dominate the first few hundred lines of
    most Lean files, so a model reading top-down sees no subject matter and
    reaches for a generic axiom. Listing the actual declarations fixes that.
    """
    seen = []
    for kind, name in _DECL_RE.findall(text):
        entry = "%s %s" % (kind, name)
        if entry not in seen:
            seen.append(entry)
        if len(seen) >= limit:
            break
    return "\n".join("  - " + s for s in seen)


def log(msg):
    """Print without ever letting the console's encoding kill a worker.

    The Windows console is cp1252. Labels legitimately contain chi, primes and
    other non-cp1252 characters, and an unprintable one raised UnicodeEncodeError
    inside the worker thread, which propagated out of fut.result() and aborted
    the whole run. Output is cosmetic; it must never end the batch.
    """
    with _print_lock:
        try:
            print(msg, flush=True)
        except UnicodeEncodeError:
            enc = (getattr(sys.stdout, "encoding", None) or "ascii")
            print(msg.encode(enc, "replace").decode(enc, "replace"), flush=True)
        except Exception:
            pass


def _cooldown(seconds):
    global _throttle_until
    with _throttle_lock:
        _throttle_until = max(_throttle_until, time.time() + seconds)


def _wait_for_throttle():
    while True:
        with _throttle_lock:
            remaining = _throttle_until - time.time()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 2.0))


def call_deepseek(text, filename, retries, max_tokens):
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set.")
    outline = lean_outline(text)
    header = "AXIOM SOURCE FILE: %s" % filename
    if outline:
        # Surfacing the real declaration names up front stops the model from
        # skimming boilerplate imports and falling back on a generic axiom.
        header += (
            "\n\nDECLARATIONS FOUND IN THIS FILE (name the axiom after this content, "
            "not after any example):\n" + outline
        )
    user_prompt = "%s\n\n=== TEXT ===\n%s\n=== END TEXT ===" % (header, text[:25000])
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": AXIOM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    last_err = "unknown"
    for attempt in range(retries + 1):
        _wait_for_throttle()
        try:
            req = urllib.request.Request(
                DEEPSEEK_URL,
                data=payload,
                headers={
                    "Authorization": "Bearer " + DEEPSEEK_API_KEY,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            choices = body.get("choices") or []
            if not choices:
                raise RuntimeError("No completion: %s" % (body.get("error") or body))
            raw = (choices[0].get("message") or {}).get("content")
            if not isinstance(raw, str) or not raw.strip():
                raise RuntimeError("Empty completion.")
            return parse_json(raw)

        except urllib.error.HTTPError as exc:
            code = exc.code
            try:
                last_err = "HTTP %s: %s" % (code, exc.read().decode("utf-8", "replace")[:200])
            except Exception:
                last_err = "HTTP %s" % code
            # Key / billing problems will not fix themselves on retry.
            if code in (401, 402, 403):
                raise RuntimeError(last_err)
            if code == 429 or code >= 500:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                if retry_after and str(retry_after).strip().isdigit():
                    wait = float(str(retry_after).strip())
                else:
                    wait = min(60.0, (2 ** attempt) + random.uniform(0, 1.5))
                if code == 429:
                    _cooldown(wait)
                if attempt < retries:
                    time.sleep(wait)
                    continue
            elif attempt < retries:
                time.sleep(min(30.0, 2 ** attempt))
                continue
            raise RuntimeError(last_err)

        except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
            last_err = str(exc)[:200]
            if attempt < retries:
                time.sleep(min(30.0, (2 ** attempt) + random.uniform(0, 1.0)))
                continue
            raise RuntimeError(last_err)

    raise RuntimeError(last_err)


def discover(root, exts):
    """Walk the tree, pruning vendored dirs BEFORE descending into them.

    rglob("*") yields every entry and only then lets us skip it, so it still
    crawls all of .lake/packages/mathlib. Over SMB that cost ~167 seconds of
    dead silence on this tree. os.walk lets us delete unwanted directories
    from dirnames in place, so they are never entered at all.
    """
    out = []
    scanned = 0
    t0 = time.time()
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_PARTS and not d.startswith(".git")
        ]
        base = Path(dirpath)
        for name in filenames:
            scanned += 1
            if os.path.splitext(name)[1].lower() not in exts:
                continue
            p = base / name
            try:
                if p.stat().st_size == 0:
                    continue
            except OSError:
                continue
            out.append(p)
        if scanned and scanned % 2000 == 0:
            log("    ...scanned %d files, %d matches (%.0fs)" % (scanned, len(out), time.time() - t0))
    log("  Scan: %d files seen, %d matched, %.1fs" % (scanned, len(out), time.time() - t0))
    return sorted(out)


def process_one(path, outbox, manifest, manifest_lock, total, retries, max_tokens):
    global _done, _failed
    key = str(path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        log("[!] unreadable %s: %s" % (path.name, exc))
        return None
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

    prior = manifest.get(key)
    if prior and prior.get("sha") == sha and (outbox / prior.get("md", "")).exists():
        with _counter_lock:
            _done += 1
            n = _done
        log("[%d/%d] skip (done)  %s" % (n, total, path.name))
        return {"filename": path.name, "path": path, "raw_text": text,
                "sha": sha, "data": prior["data"]}

    try:
        data = call_deepseek(text, path.name, retries, max_tokens)
    except Exception as exc:
        with _counter_lock:
            _failed += 1
        log("[!] FAIL %s: %s" % (path.name, exc))
        with manifest_lock:
            with (outbox / "_errors.log").open("a", encoding="utf-8") as fh:
                fh.write("%s\t%s\t%s\n" % (datetime.now().isoformat(), key, exc))
        return None

    # Name the output after the SOURCE file, not after the model's canonical_id.
    # Ids are model output and collide constantly; the source path is unique by
    # construction, so this guarantees one companion per input and a name you can
    # trace back to its origin.
    cid = str(data.get("canonical_id", path.stem)).replace(".", "_").replace("/", "_")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem)[:80]
    md_name = "%s__%s_COMPANION.md" % (stem, sha[:8])
    (outbox / md_name).write_text(
        render_axiom_companion_md(data, path.name, sha), encoding="utf-8"
    )
    record = {"key": key, "sha": sha, "md": md_name, "data": data}
    with manifest_lock:
        manifest[key] = record
        # Append one line per completion instead of rewriting the whole manifest.
        # The old full rewrite was O(n^2) over a network share and left the file
        # truncated to zero bytes between truncate and write - a Ctrl+C inside
        # that window destroyed the resume record for every finished file.
        with (outbox / MANIFEST_NAME).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    with _counter_lock:
        _done += 1
        n = _done
    log("[%d/%d] ok  %s -> %s %s" % (n, total, path.name, cid, data.get("human_label", "")))
    return {"filename": path.name, "path": path, "raw_text": text, "sha": sha, "data": data}


def main():
    default_inbox = Path(
        r"W:\Desktop\_____pipeline-workflows-main\LEAN_FLOOR\00_INBOX__UNTOUCHED_SOURCES"
    )
    ap = argparse.ArgumentParser(description="DeepSeek parallel AXIOM COMPANION runner")
    ap.add_argument("--folder", default=None, help="Input folder (searched recursively)")
    ap.add_argument("--file", default=None, help="Single file instead of a folder")
    ap.add_argument("--out", default=None, help="Output folder")
    ap.add_argument("--workers", type=int, default=24, help="Parallel API calls (default 24)")
    ap.add_argument("--limit", type=int, default=0, help="Only process the first N files")
    ap.add_argument("--retries", type=int, default=4, help="Retries per file (default 4)")
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--ext", default=",".join(EXTS), help="Comma list of extensions")
    ap.add_argument("--no-resume", action="store_true", help="Ignore manifest and redo everything")
    args = ap.parse_args()

    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY is not set in this environment.")
        return 2

    exts = tuple(
        e if e.startswith(".") else "." + e
        for e in (x.strip().lower() for x in args.ext.split(",")) if e
    )

    if args.file:
        files = [Path(args.file.strip(' "'))]
        root = files[0].parent
    else:
        root = Path(args.folder.strip(' "')) if args.folder else default_inbox
        if not root.is_dir():
            print("ERROR: input folder not found: %s" % root)
            return 2
        print("Scanning %s ..." % root, flush=True)
        files = discover(root, exts)

    if args.limit > 0:
        files = files[:args.limit]
    if not files:
        print("[!] No matching files under %s" % root)
        return 0

    if args.out:
        outbox = Path(args.out.strip(' "'))
    else:
        outbox = root.parent / "OUTBOX" / ("%s_AXIOMS_DEEPSEEK_V2" % datetime.now().strftime("%Y-%m-%d"))
    outbox.mkdir(parents=True, exist_ok=True)

    manifest = {}
    if not args.no_resume:
        # New append-only log.
        mpath = outbox / MANIFEST_NAME
        if mpath.exists():
            bad = 0
            with mpath.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        manifest[rec["key"]] = rec
                    except Exception:
                        bad += 1  # a torn final line costs one file, not the run
            if bad:
                print("  (ignored %d unreadable manifest line(s))" % bad)
        # Migrate a readable manifest from the older single-JSON format.
        legacy = outbox / "_manifest.json"
        if legacy.exists() and legacy.stat().st_size > 0:
            try:
                for k, v in json.loads(legacy.read_text(encoding="utf-8")).items():
                    v.setdefault("key", k)
                    manifest.setdefault(k, v)
            except Exception:
                print("  (legacy _manifest.json unreadable - ignoring it)")

    total = len(files)
    started = time.time()
    print("=" * 64)
    print("AXIOM PIPELINE - DeepSeek direct - %s" % DEEPSEEK_MODEL)
    print("  Input:   %s" % root)
    print("  Output:  %s" % outbox)
    print("  Files:   %d   (already in manifest: %d)" % (total, len(manifest)))
    print("  Workers: %d parallel   retries: %d" % (args.workers, args.retries))
    print("=" * 64)

    global _failed
    mlock = threading.Lock()
    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(process_one, f, outbox, manifest, mlock, total,
                            args.retries, args.max_tokens): f
                for f in files
            }
            for fut in as_completed(futures):
                # One unexpected worker exception must not abort the batch.
                try:
                    r = fut.result()
                except Exception as exc:
                    _failed += 1
                    log("[!] worker error on %s: %s" % (futures[fut].name, exc))
                    continue
                if r:
                    results.append(r)
    except KeyboardInterrupt:
        print("\n[!] Interrupted - finished companions and the manifest are saved.")

    if results:
        results.sort(key=lambda x: x["filename"])
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        (outbox / ("axioms_raw_%s.json" % stamp)).write_text(
            json.dumps([r["data"] for r in results], indent=2), encoding="utf-8"
        )
        draft = build_axiom_draft_snapshot(results)
        (outbox / ("nerve-draft_%s_axioms.json" % stamp)).write_text(
            json.dumps(draft, indent=2), encoding="utf-8"
        )
        (outbox / "LATEST_AXIOM_DRAFT.json").write_text(
            json.dumps(draft, indent=2), encoding="utf-8"
        )

    elapsed = time.time() - started
    print("")
    print("=" * 64)
    print("DONE  %d companion(s)  |  %d failed  |  %.1f min" % (len(results), _failed, elapsed / 60.0))
    if _failed:
        print("  Failures listed in: %s" % (outbox / "_errors.log"))
    print("  Output: %s" % outbox)
    print("  Re-run the same command to retry only what is missing.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
