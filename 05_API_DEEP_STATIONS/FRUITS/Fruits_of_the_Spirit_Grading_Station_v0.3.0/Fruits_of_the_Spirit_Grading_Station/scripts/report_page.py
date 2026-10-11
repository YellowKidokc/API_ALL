"""report_page.py -- Paper Grade Dashboard (Fruits Grading Station edition).

Renders grading_out/<paper>.report.html from the three run JSONs
(<paper>.lexicon.json, <paper>.stats.json, <paper>.spans.json). Follows the
master paper-grade-dashboard template: fixed topbar with section nav, hero with
grade badge, stats ribbon, pg-sec-head section pattern (dot + kicker + h2 +
desc), pg- class prefix, BEGIN/END component markers, data-component/data-name
attributes, design tokens (--bg:#050505, --gold:#d4af37, --green:#4ade80,
--amber:#fb923c, --red:#f87171, --blue:#38bdf8, Oswald/Crimson Text/Inter/
JetBrains Mono, max-width 1100px).

Charts are inline SVG generated in Python (charts_svg.py) -- no external JS
libraries; works over file:// and prints. Tiny vanilla JS only for the
heartbeat hover inspector and the ledger click-through.

Sections: Metrics (stats ribbon) / Heartbeat (per-sentence TRUTH EKG with
hover inspector + top-5 peaks & valleys) / Fruits (nine-fruit profile, enacted
vs about) / Gates (7 gates + veto conditions) / Claims (role donut + claim
strength) / Ledger (clickable span table) / Report ("The Reading", an essayist
profile of the paper -- one DeepSeek call at temp 0.3 with prompt
prompts/fruits_narrative_v1.0.txt, cached in grading_out/<paper>.narrative.json
-- reused when both the brief hash and the narrative prompt hash match).

Template sections with no data source yet (7Q coverage, derivation chain,
station marks, kill conditions) are OMITTED -- see the RESERVED comment in the
HTML head. Every number on the page traces to the run JSONs.

Inputs:
  --paper  Path to the graded paper.
"""

import argparse
import hashlib
import html
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

import charts_svg

sys.stdout.reconfigure(encoding="utf-8")

STATION_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
OUT_DIR = STATION_DIR / "grading_out"
RUBRIC_PATH = SCRIPTS_DIR / "rubric" / "fruits_rubric_v0.3.0.json"
WEIGHTS_PATH = SCRIPTS_DIR / "weights.json"
NARRATIVE_PROMPT_PATH = SCRIPTS_DIR / "prompts" / "fruits_narrative_v1.0.txt"
NARRATIVE_PROMPT_VERSION = "fruits_narrative_v1.0"

BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"

FRUIT_AXES = ["love", "joy", "peace", "patience", "kindness",
              "goodness", "faithfulness", "gentleness", "self_control"]
HB_CATS = ["fruit", "anti_fruit", "grounding", "contradiction", "propaganda", "jargon"]

# DeepSeek standard list rates (USD per 1M tokens) used for the cost estimate.
RATE_HIT, RATE_MISS, RATE_OUT = 0.07, 0.27, 1.10


def esc(s):
    return html.escape(str(s), quote=True)


def js_data(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def grade_badge(stats_by_key):
    """Signal share: positive weighted activity as % of total weighted
    activity. 0-100 by construction; letter band is a display convention."""
    pos = float(stats_by_key.get("truth.positive_component", {}).get("value", 0) or 0)
    neg = abs(float(stats_by_key.get("truth.negative_component", {}).get("value", 0) or 0))
    share = round(100 * pos / (pos + neg), 1) if (pos + neg) > 0 else 0.0
    band = "A" if share >= 90 else "B" if share >= 75 else "C" if share >= 60 \
        else "D" if share >= 45 else "F"
    return share, band


# ---------------------------------------------------------------------------
# "What this means" -- one DeepSeek call, cached by brief hash
# ---------------------------------------------------------------------------

def build_brief(spans_doc, stats_doc, profile, lex_hits, gate_counts,
                veto_spans, counterfeit_spans, role_dist,
                signal_share, signal_band, peaks, valleys):
    return {
        "paper": spans_doc["paper"],
        "in_report_stats": [
            {"key": s["key"], "value": s["value"], "unit": s["unit"]}
            for s in stats_doc["stats"] if s["in_report"]],
        "signal_share_pct": signal_share,
        "signal_share_band": signal_band,
        "gate_flag_counts": dict(gate_counts),
        "veto_spans": veto_spans,
        "counterfeit_suspect_spans": counterfeit_spans,
        "fruit_profile_span_signals": profile,
        "fruit_lexicon_hits": lex_hits,
        "role_distribution": dict(role_dist),
        "spans_graded": sum(1 for s in spans_doc["spans"] if s["status"] == "ok"),
        "peaks": peaks,
        "valleys": valleys,
    }


def load_narrative_prompt():
    if not NARRATIVE_PROMPT_PATH.exists():
        sys.exit(f"ERROR: missing narrative prompt {NARRATIVE_PROMPT_PATH}")
    text = NARRATIVE_PROMPT_PATH.read_text(encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, sha


def what_this_means(api_key, brief, prompt_text):
    body = {
        "model": MODEL,
        "temperature": 0.3,
        "max_tokens": 1400,
        "messages": [
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": json.dumps(brief, ensure_ascii=False)},
        ],
    }
    r = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=body, timeout=240,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"], data.get("usage", {})


def get_narrative(stem, brief, prompt_text, prompt_sha):
    """Return (reading_html, meta). Reuses grading_out/<stem>.narrative.json
    when the brief hash AND the narrative prompt hash match; otherwise makes
    the single API call."""
    cache_path = OUT_DIR / f"{stem}.narrative.json"
    brief_sha = hashlib.sha256(
        json.dumps(brief, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if (cached.get("brief_sha256") == brief_sha
                    and cached.get("narrative_prompt_sha256") == prompt_sha):
                return cached["reading"], f"cached narrative · generated {cached.get('generated_at', '?')}"
        except (ValueError, KeyError):
            pass
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "[The Reading SKIPPED: DEEPSEEK_API_KEY not set]", "skipped"
    try:
        reading, usage = what_this_means(api_key, brief, prompt_text)
        cache_path.write_text(json.dumps({
            "brief_sha256": brief_sha,
            "narrative_prompt": NARRATIVE_PROMPT_VERSION,
            "narrative_prompt_sha256": prompt_sha,
            "reading": reading, "usage": usage,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": MODEL, "temperature": 0.3,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        return reading, (f"generated by {MODEL} (temperature 0.3), "
                         f"prompt {NARRATIVE_PROMPT_VERSION}, "
                         f"tokens: {usage.get('total_tokens', '?')}")
    except Exception as e:
        return f"[The Reading generation FAILED: {type(e).__name__}: {e}]", "error"


def reading_to_html(reading):
    out = []
    for para in esc(reading).split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("## "):
            out.append(f'<h3 class="pg-read-h">{esc(para[3:])}</h3>')
        elif para.startswith("# "):
            out.append(f'<h3 class="pg-read-h">{esc(para[2:])}</h3>')
        else:
            out.append(f"<p>{para}</p>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Page CSS (template tokens + heartbeat/ledger additions)
# ---------------------------------------------------------------------------

CSS = """
:root{
  --bg:#050505; --surface:#0a0a0a; --surface2:#111; --surface3:#1a1a1a;
  --border:#222; --border-2:#2a2a2a; --border-hi:#3a3a3a;
  --text:#e5e3df; --text-dim:#9a9a9a; --text-muted:#5a5a5a;
  --gold:#d4af37; --gold-dim:rgba(212,175,55,.1);
  --green:#4ade80; --green-dim:rgba(74,222,128,.1);
  --amber:#fb923c; --amber-dim:rgba(251,146,60,.1);
  --red:#f87171; --red-dim:rgba(248,113,113,.1);
  --blue:#38bdf8; --blue-dim:rgba(56,189,248,.1);
  --serif:'Crimson Text',Georgia,serif; --mono:'JetBrains Mono',ui-monospace,monospace;
  --display:'Oswald','Inter',sans-serif; --sans:'Inter',system-ui,sans-serif;
  --max:1100px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}

/* ═══════ COMPONENT:topbar ═══════ */
.pg-header{position:fixed;top:0;left:0;right:0;z-index:50;display:flex;align-items:center;justify-content:space-between;padding:.65rem 1.5rem;backdrop-filter:blur(14px) saturate(140%);background:rgba(8,8,8,.92);border-bottom:1px solid var(--border)}
.pg-brand{display:flex;align-items:center;gap:.6rem}
.pg-mark{font-family:var(--serif);font-size:1.3rem;color:var(--gold);line-height:1}
.pg-name{font-family:var(--mono);font-size:.58rem;letter-spacing:.2em;color:var(--text-muted);text-transform:uppercase}
.pg-name span{color:var(--gold)}
.pg-nav{display:flex;gap:.1rem;flex-wrap:wrap}
.pg-nav a{font-family:var(--display);font-size:.55rem;letter-spacing:.12em;text-transform:uppercase;padding:.4rem .55rem;border-radius:4px;color:var(--text-dim);transition:all .15s}
.pg-nav a:hover,.pg-nav a.active{color:var(--gold);background:var(--gold-dim)}
@media(max-width:800px){.pg-nav{display:none}}

/* ═══════ COMPONENT:hero ═══════ */
.pg-hero{position:relative;padding:6.5rem 1.5rem 2.5rem;overflow:hidden}
.pg-hero::before{content:'';position:absolute;top:15%;left:50%;transform:translate(-50%,-50%);width:700px;height:350px;background:radial-gradient(ellipse,rgba(212,175,55,.04) 0%,transparent 65%);pointer-events:none}
.pg-hero-inner{max-width:var(--max);margin:0 auto;position:relative}
.pg-hero-row{display:flex;align-items:flex-start;justify-content:space-between;gap:2rem;flex-wrap:wrap}
.pg-hero-text{flex:1;min-width:260px}
.pg-hero-eyebrow{font-family:var(--mono);font-size:.58rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin-bottom:.7rem}
.pg-hero h1{font-family:var(--display);font-weight:500;font-size:clamp(1.8rem,4.5vw,3rem);line-height:1.08;color:#fff;margin-bottom:.7rem;letter-spacing:.02em}
.pg-hero-sub{font-family:var(--serif);font-size:1rem;color:var(--text-dim);line-height:1.55;font-style:italic;max-width:560px;margin-bottom:.8rem}
.pg-hero-address{font-family:var(--mono);font-size:.62rem;color:var(--text-muted);line-height:1.7;padding:.8rem 1rem;background:var(--surface2);border:1px solid var(--border);border-radius:6px;margin-top:.6rem;overflow-wrap:anywhere}
.pg-hero-address b{color:var(--text-dim)}
.pg-grade-badge{flex:0 0 auto;padding:1.3rem 1.8rem;background:var(--surface2);border:1px solid var(--border);border-radius:8px;text-align:center;min-width:150px}
.pg-grade-label{font-family:var(--mono);font-size:.52rem;letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted);margin-bottom:.35rem}
.pg-grade-value{font-family:var(--display);font-size:2.8rem;color:var(--gold);line-height:1}
.pg-grade-sub{font-family:var(--mono);font-size:.55rem;color:var(--text-dim);margin-top:.35rem}

/* ═══════ COMPONENT:stats-ribbon ═══════ */
.pg-stats{max-width:var(--max);margin:0 auto;padding:0 1.5rem 2.5rem}
.pg-stats-inner{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:0;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--surface2)}
.pg-stat{padding:1rem .6rem;text-align:center;border-right:1px solid var(--border)}
.pg-stat:last-child{border-right:0}
.pg-stat-num{font-family:var(--display);font-size:1.35rem;color:var(--gold);display:block;margin-bottom:.15rem}
.pg-stat-label{font-family:var(--mono);font-size:.5rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:.08em}

/* ═══════ COMPONENT:section:generic ═══════ */
.pg-sec{max-width:var(--max);margin:0 auto;padding:2.5rem 1.5rem}
.pg-sec-head{display:flex;align-items:center;gap:.7rem;margin-bottom:.45rem}
.pg-sec-dot{width:7px;height:7px;border-radius:50%;background:var(--gold)}
.pg-sec-kicker{font-family:var(--mono);font-size:.6rem;color:var(--text-muted);letter-spacing:.15em;text-transform:uppercase}
.pg-sec h2{font-family:var(--serif);font-size:clamp(1.25rem,2.5vw,1.6rem);font-weight:400;color:#fff;margin-bottom:.2rem}
.pg-sec-desc{font-size:.84rem;color:var(--text-dim);max-width:640px;margin-bottom:1.3rem;line-height:1.55}
.pg-panel{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:1.1rem 1.2rem}

/* ═══════ COMPONENT:heartbeat ═══════ */
.pg-inspector{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:.9rem 1.1rem;margin-bottom:.8rem;min-height:96px}
.pg-inspector h3{font-family:var(--mono);font-size:.58rem;letter-spacing:.15em;color:var(--gold);text-transform:uppercase;margin-bottom:.45rem}
.pg-insp-text{font-family:var(--serif);font-size:1.02rem;color:var(--text);margin-bottom:.45rem}
.pg-insp-meta{display:flex;gap:1.1rem;flex-wrap:wrap;font-size:.72rem;color:var(--text-dim)}
.pg-insp-meta span{font-family:var(--mono)}
.pg-toggle-row{display:flex;gap:.45rem;flex-wrap:wrap;margin-bottom:.7rem}
.pg-toggle{background:var(--surface2);border:1px solid var(--border);color:var(--text-dim);padding:.25rem .7rem;border-radius:4px;cursor:pointer;font-size:.72rem;font-family:var(--sans)}
.pg-toggle:hover{border-color:var(--gold);color:var(--text)}
.pg-toggle.active{background:var(--gold);color:#000;border-color:var(--gold)}
.pg-ekg-tables{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-top:1rem}
@media(max-width:800px){.pg-ekg-tables{grid-template-columns:1fr}}

/* ═══════ COMPONENT:gates ═══════ */
.pg-gate-row{display:flex;align-items:center;gap:.8rem;padding:.6rem .8rem;background:var(--surface2);border:1px solid var(--border);border-radius:5px;margin-bottom:.4rem}
.pg-gate-id{font-family:var(--mono);font-size:.68rem;color:var(--blue);min-width:220px}
.pg-gate-q{flex:1;font-size:.76rem;color:var(--text-dim)}
.pg-pill{display:inline-block;padding:.15rem .6rem;border-radius:10px;font-size:.62rem;font-weight:600;letter-spacing:.05em;font-family:var(--mono);white-space:nowrap}
.pg-pill.ok{background:var(--green-dim);color:var(--green)}
.pg-pill.warn{background:var(--amber-dim);color:var(--amber)}
.pg-pill.fail{background:var(--red-dim);color:var(--red)}
.pg-hard{font-family:var(--mono);font-size:.5rem;color:var(--red);border:1px solid var(--red);border-radius:3px;padding:.05rem .3rem}
.pg-veto-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.45rem;margin-top:1rem}
.pg-veto-card{padding:.7rem .9rem;background:var(--surface2);border:1px solid var(--border);border-radius:5px;border-left:3px solid var(--red);font-size:.78rem;color:var(--text-dim)}
.pg-veto-card .n{font-family:var(--display);font-size:1.1rem;color:var(--text);float:right}

/* ═══════ COMPONENT:claims ═══════ */
.pg-claims-grid{display:grid;grid-template-columns:auto 1fr;gap:1.4rem;align-items:start}
@media(max-width:800px){.pg-claims-grid{grid-template-columns:1fr}}
.pg-legend{font-size:.74rem;color:var(--text-dim)}
.pg-legend .sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:.35rem;vertical-align:middle}
.pg-legend .row{display:flex;justify-content:space-between;gap:1rem;padding:.18rem 0}
.pg-legend .row b{font-family:var(--mono);color:var(--text);font-weight:500}

/* ═══════ COMPONENT:ledger ═══════ */
.pg-table-wrap{overflow:auto;-webkit-overflow-scrolling:touch;max-height:560px;border:1px solid var(--border);border-radius:8px}
.pg-table{width:100%;border-collapse:collapse;font-size:.78rem;min-width:760px}
.pg-table th{text-align:left;padding:.6rem .7rem;font-family:var(--mono);font-size:.52rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em;border-bottom:1px solid var(--border);font-weight:500;position:sticky;top:0;background:var(--bg)}
.pg-table td{padding:.45rem .7rem;border-bottom:1px solid var(--border-2);color:var(--text);vertical-align:top}
.pg-table tbody tr{cursor:pointer}
.pg-table tbody tr:hover td{background:var(--surface2)}
.pg-table tbody tr.sel td{background:var(--surface3)}
.pg-table td:first-child{font-family:var(--mono);font-size:.7rem;color:var(--gold);white-space:nowrap}
.pg-chip{display:inline-block;font-family:var(--mono);font-size:.55rem;padding:.12rem .4rem;border-radius:3px;letter-spacing:.05em;background:var(--blue-dim);color:var(--blue)}
.pg-flag{font-family:var(--mono);font-size:.62rem;color:var(--amber)}
.pg-veto{font-family:var(--mono);font-size:.62rem;color:var(--red);font-weight:600}
.pg-conf{font-family:var(--mono);font-size:.68rem;color:var(--text-dim)}
.pg-detail{display:none;margin-top:.9rem}
.pg-detail pre{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:.8rem;font:11px/1.5 var(--mono);color:var(--text);white-space:pre-wrap;max-height:300px;overflow:auto}
.pg-detail h3{font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;color:var(--blue);text-transform:uppercase;margin:.9rem 0 .3rem}

/* ═══════ COMPONENT:report ═══════ */
.pg-reading p{font-size:.92rem;color:var(--text);margin-bottom:.9rem;line-height:1.7}
.pg-read-h{font-family:var(--serif);font-size:1.1rem;color:var(--gold);margin:1.1rem 0 .5rem}
.pg-read-meta{font-family:var(--mono);font-size:.58rem;color:var(--text-muted);margin-top:.8rem}

/* ═══════ COMPONENT:footer ═══════ */
.pg-footer{max-width:var(--max);margin:2.5rem auto 0;padding:2rem 1.5rem;text-align:center;border-top:1px solid var(--border)}
.pg-footer .feq{font-family:var(--mono);font-size:.7rem;color:var(--gold);opacity:.5;margin-bottom:.5rem}
.pg-footer p{color:var(--text-muted);font-size:.72rem;margin:.2rem 0}

@media(max-width:640px){
  .pg-hero-row{flex-direction:column}
  .pg-grade-badge{align-self:flex-start}
  .pg-stats-inner{grid-template-columns:repeat(3,1fr)}
  .pg-stat{border-bottom:1px solid var(--border)}
}
@media print{.pg-header{position:static}.pg-table-wrap{max-height:none;overflow:visible}}
"""

JS = r"""
/* ═══════ COMPONENT:script:scroll-header ═══════ */
window.addEventListener('scroll',()=>{
  document.getElementById('pg-header').classList.toggle('pg-header-scrolled', window.scrollY > 60);
});
/* ═══════ COMPONENT:script:smooth-nav ═══════ */
document.querySelectorAll('.pg-nav a[href^="#"]').forEach(link=>{
  link.addEventListener('click', e=>{
    const target = document.querySelector(link.getAttribute('href'));
    if(target){ e.preventDefault(); target.scrollIntoView({behavior:'smooth', block:'start'}); }
  });
});
/* ═══════ COMPONENT:script:heartbeat-inspector ═══════ */
const HB = %HB_DATA%;
const HBM = %HB_META%;
function hbMove(evt){
  const r = evt.target.getBoundingClientRect();
  let idx = Math.round((evt.clientX - r.left) / r.width * (HBM.n - 1));
  idx = Math.max(0, Math.min(HBM.n - 1, idx));
  const s = HB[idx];
  document.getElementById('hb-text').textContent = s.t;
  document.getElementById('hb-idx').textContent = 's' + s.i;
  document.getElementById('hb-total').textContent = s.w.toFixed(2);
  document.getElementById('hb-fruit').textContent = s.c[0];
  document.getElementById('hb-anti').textContent = s.c[1];
  document.getElementById('hb-ground').textContent = s.c[2];
  document.getElementById('hb-contra').textContent = s.c[3];
  document.getElementById('hb-prop').textContent = s.c[4];
  document.getElementById('hb-jargon').textContent = s.c[5];
  const cur = document.getElementById('hb-cursor');
  cur.setAttribute('x1', HBM.padL + idx / Math.max(1, HBM.n - 1) * HBM.iw);
  cur.setAttribute('x2', HBM.padL + idx / Math.max(1, HBM.n - 1) * HBM.iw);
  cur.setAttribute('visibility', 'visible');
}
function hbLeave(){ document.getElementById('hb-cursor').setAttribute('visibility','hidden'); }
function hbToggle(id, btn){
  const el = document.getElementById(id);
  el.style.display = (el.style.display === 'none') ? '' : 'none';
  btn.classList.toggle('active');
}
/* ═══════ COMPONENT:script:ledger-detail ═══════ */
const DETAIL = %DETAIL%;
function showSpan(id){
  document.querySelectorAll('#pg-ledger tbody tr').forEach(r=>
    r.classList.toggle('sel', r.dataset.span === String(id)));
  const d = DETAIL[id]; if(!d) return;
  const el = document.getElementById('pg-detail');
  el.style.display = 'block';
  document.getElementById('d-title').textContent =
    'Span ' + id + '  ·  sentences ' + d.range + '  ·  ' + d.role;
  document.getElementById('d-text').textContent = d.text;
  document.getElementById('d-lex').textContent = d.lex;
  document.getElementById('d-json').textContent = JSON.stringify(d.judgment, null, 2);
  el.scrollIntoView({behavior:'smooth', block:'nearest'});
}
"""


def span_lex_summary(sp, lex):
    by_idx = {s["idx"]: s for s in lex["sentences"]}
    out = []
    for i in range(sp["sent_idx_start"], sp["sent_idx_end"] + 1):
        s = by_idx.get(i)
        if not s:
            continue
        matched = {c: s["categories"][c]["matched_terms"]
                   for c in ("fruit", "anti_fruit", "grounding", "contradiction",
                             "jargon", "propaganda")
                   if s["categories"][c]["matched_terms"]}
        out.append({"idx": i, "matched": matched,
                    "claim_strength": {k: v for k, v in s["claim_strength"].items() if v},
                    "hedges": s["hedges"], "absolutes": s["absolutes"]})
    return out


def main():
    ap = argparse.ArgumentParser(description="Paper Grade Dashboard — Fruits Grading Station edition.")
    ap.add_argument("--paper", required=True, help="Path to the graded paper.")
    args = ap.parse_args()

    stem = Path(args.paper).stem
    lex = json.loads((OUT_DIR / f"{stem}.lexicon.json").read_text(encoding="utf-8"))
    stats_doc = json.loads((OUT_DIR / f"{stem}.stats.json").read_text(encoding="utf-8"))
    spans_path = OUT_DIR / f"{stem}.spans.json"
    if not spans_path.exists():
        sys.exit(f"ERROR: missing {spans_path} -- run span_judge.py first.")
    spans_doc = json.loads(spans_path.read_text(encoding="utf-8"))
    rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))

    sbk = {s["key"]: s for s in stats_doc["stats"]}
    ok_spans = [s for s in spans_doc["spans"] if s["status"] == "ok"]
    m = spans_doc["manifest"]

    # ---- aggregates -------------------------------------------------------
    gate_counts = Counter()
    veto_counts = Counter()
    veto_spans, counterfeit_spans = [], []
    for sp in ok_spans:
        j = sp["judgment"]
        for g in j["gate_flags"]:
            gate_counts[g] += 1
        for v in j["veto_flags"]:
            veto_counts[v] += 1
        if j["veto_flags"]:
            veto_spans.append(sp["span_id"])
        if j["counterfeit_suspect"]:
            counterfeit_spans.append(sp["span_id"])

    profile = {a: {"en+": 0, "en-": 0, "ab+": 0, "ab-": 0} for a in FRUIT_AXES}
    any_kind_missing = False
    for sp in ok_spans:
        for fs in sp["judgment"]["fruit_signals"]:
            a = fs.get("fruit_id", "").replace("fruit.", "")
            if a not in profile:
                continue
            kind = fs.get("polarity_kind")
            if kind not in ("enacted", "about"):
                any_kind_missing = True
                kind = "about"
            pol = fs.get("polarity", "+")
            profile[a][f"{'en' if kind == 'enacted' else 'ab'}{pol}"] += 1

    lex_hits = {a: sbk.get(f"fruit_axis.{a}.total", {}).get("value", 0) for a in FRUIT_AXES}
    role_dist = Counter(sp["judgment"]["role"] for sp in ok_spans)
    n_sent = sbk.get("volume.sentences", {}).get("value", len(lex["sentences"]))
    n_words = sbk.get("volume.words", {}).get("value", 0)
    n_spans = len(spans_doc["spans"])
    n_claims = role_dist.get("CLAIM", 0)
    n_evidence = role_dist.get("EVIDENCE", 0)
    n_gates = sum(gate_counts.values())
    n_veto = sum(veto_counts.values())

    tok = m.get("tokens", {})
    cost = (tok.get("cache_hit", 0) * RATE_HIT + tok.get("cache_miss", 0) * RATE_MISS
            + tok.get("completion", 0) * RATE_OUT) / 1e6
    cost_str = f"${cost:.3f}" if tok else "n/a"

    share, band = grade_badge(sbk)
    truth = sbk.get("truth.score", {}).get("value", "?")

    # ---- heartbeat --------------------------------------------------------
    series = stats_doc["series"]["weighted_total"]
    smoothed = charts_svg.sma(series, window=9)
    heartbeat = charts_svg.heartbeat_svg(series, smoothed, len(series))
    hb_data = []
    for s in lex["sentences"]:
        hb_data.append({
            "i": s["idx"],
            "t": s["text"][:160],
            "w": round(series[s["idx"]], 3),
            "c": [round(s["categories"][c]["weighted_score"], 2) for c in HB_CATS],
        })
    hb_meta = {"n": len(series), "padL": 48, "iw": 1040 - 48 - 12}

    sent_by_idx = {s["idx"]: s for s in lex["sentences"]}

    def dom_cat(i):
        s = sent_by_idx[i]
        return max(HB_CATS, key=lambda c: abs(s["categories"][c]["weighted_score"]))

    order = sorted(range(len(series)), key=lambda i: series[i], reverse=True)
    peaks = order[:5]
    valleys = sorted(range(len(series)), key=lambda i: series[i])[:5]

    def ekg_rows(idxs, cls):
        rows = ""
        for i in idxs:
            rows += (f'<tr><td>{i}</td><td class="pg-conf" style="color:var(--{"green" if cls=="high" else "red"})">'
                     f'{series[i]:.2f}</td><td class="pg-flag">{dom_cat(i)}</td>'
                     f'<td style="color:var(--text-dim);font-size:.72rem">{esc(sent_by_idx[i]["text"][:110])}</td></tr>')
        return rows

    # ---- charts ------------------------------------------------------------
    fruit_svg = charts_svg.fruit_profile_svg(profile, lex_hits)
    role_colors = {"CLAIM": charts_svg.GOLD, "EVIDENCE": charts_svg.GREEN,
                   "MECHANISM": charts_svg.BLUE, "DEFINITION": "#a78bfa",
                   "OBJECTION": charts_svg.AMBER, "CONCESSION": "#f472b6",
                   "BOUNDARY": "#94a3b8", "RHETORIC": charts_svg.RED}
    role_items = [(r, role_dist[r], role_colors.get(r, "#666"))
                  for r in sorted(role_dist, key=lambda r: role_dist[r], reverse=True)]
    donut = charts_svg.donut_svg(role_items)
    cs_items = [(k, sbk.get(f"claim_strength.{k}.count", {}).get("value", 0), c)
                for k, c in (("weak", charts_svg.GREEN), ("moderate", charts_svg.BLUE),
                             ("strong", charts_svg.AMBER), ("forbidden", charts_svg.RED))]
    cs_bars = charts_svg.hbars_svg(cs_items)

    # ---- narrative ----------------------------------------------------------
    brief_peaks = [{"idx": i, "score": round(series[i], 3),
                    "excerpt": sent_by_idx[i]["text"][:160]} for i in peaks]
    brief_valleys = [{"idx": i, "score": round(series[i], 3),
                      "excerpt": sent_by_idx[i]["text"][:160]} for i in valleys]
    brief = build_brief(spans_doc, stats_doc, profile, lex_hits, gate_counts,
                        veto_spans, counterfeit_spans, dict(role_dist),
                        share, band, brief_peaks, brief_valleys)
    narrative_prompt_text, narrative_prompt_sha = load_narrative_prompt()
    reading, reading_meta = get_narrative(stem, brief, narrative_prompt_text,
                                          narrative_prompt_sha)
    reading_html = reading_to_html(reading)

    # ---- gates html -----------------------------------------------------------
    gates_html = ""
    for g in rubric["gates"]:
        n = gate_counts.get(g["id"], 0)
        if n == 0:
            pill, cls = "CLEAR", "ok"
        elif g["hard"]:
            pill, cls = f"FLAGGED ×{n}", "fail"
        else:
            pill, cls = f"FLAGGED ×{n}", "warn"
        hard = ' <span class="pg-hard">HARD</span>' if g["hard"] else ""
        gates_html += (f'<div class="pg-gate-row" data-component="gate-row" data-name="{esc(g["id"])}">'
                       f'<span class="pg-gate-id">{esc(g["id"])}</span>{hard}'
                       f'<span class="pg-gate-q">{esc(g["question"])}</span>'
                       f'<span class="pg-pill {cls}">{pill}</span></div>')
    vetoes_html = ""
    for v in rubric["veto_conditions"]:
        n = veto_counts.get(v, 0)
        vetoes_html += (f'<div class="pg-veto-card" data-component="veto-card" '
                        f'data-name="{esc(v)}"><span class="n">{n}</span>{esc(v)}</div>')

    # ---- ledger ----------------------------------------------------------------
    detail_js = {}
    rows_html = ""
    for sp in spans_doc["spans"]:
        rng = f's{sp["sent_idx_start"]}–{sp["sent_idx_end"]}'
        if sp["status"] == "ok":
            j = sp["judgment"]
            sig = "; ".join(f'{fs["fruit_id"].replace("fruit.", "")} {fs["polarity"]}'
                            f'/{fs.get("polarity_kind", "?")}'
                            for fs in j["fruit_signals"]) or "—"
            gates = ", ".join(j["gate_flags"])
            vetoes = ", ".join(j["veto_flags"]) + (" [counterfeit]" if j["counterfeit_suspect"] else "")
            rows_html += (f'<tr data-span="{sp["span_id"]}" onclick="showSpan({sp["span_id"]})">'
                          f'<td>{sp["span_id"]}</td><td class="pg-conf">{rng}</td>'
                          f'<td><span class="pg-chip">{j["role"]}</span></td>'
                          f'<td style="font-size:.68rem">{esc(sig)}</td>'
                          f'<td class="pg-flag">{esc(gates)}</td>'
                          f'<td class="pg-veto">{esc(vetoes)}</td>'
                          f'<td class="pg-conf">{j["confidence"]}</td></tr>')
            detail_js[sp["span_id"]] = {
                "range": rng, "role": j["role"], "text": sp["text"],
                "lex": json.dumps(span_lex_summary(sp, lex), ensure_ascii=False, indent=1),
                "judgment": j,
            }
        else:
            rows_html += (f'<tr><td>{sp["span_id"]}</td><td class="pg-conf">{rng}</td>'
                          f'<td><span class="pg-chip">INVALID</span></td>'
                          f'<td colspan="4" class="pg-veto">{esc(sp.get("error", ""))}</td></tr>')

    kind_note = (' Note: this run predates prompt v0.3.1 — signals have no '
                 'enacted/about split and are shown as "about".') if any_kind_missing else ""

    stats_ribbon = [
        (f"{n_sent:,}", "Sentences"), (f"{n_spans}", "Spans"), (f"{n_words:,}", "Words"),
        (f"{n_claims}", "Claims"), (f"{n_evidence}", "Evidence"),
        (f"{n_gates}", "Gate flags"), (f"{n_veto}", "Vetoes"), (cost_str, "Est. cost"),
    ]
    ribbon_html = "".join(
        f'<div class="pg-stat" data-component="stat" data-name="stat-{esc(l.lower().replace(" ", "-"))}">'
        f'<span class="pg-stat-num">{esc(v)}</span><span class="pg-stat-label">{esc(l)}</span></div>'
        for v, l in stats_ribbon)

    weights_sha = m.get("weights_sha256", "")
    gen_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<!--
  PAGE_META
  title: {esc(stem)} — Paper Grade Dashboard (Fruits Grading Station edition)
  template: paper-grade-dashboard
  generator: report_page.py (Fruits Grading Station)
  RESERVED SECTIONS (no data source yet — intentionally omitted, not fabricated):
    7Q coverage, derivation chain, station marks, kill conditions.
    They join when those stations come online.
-->
<head>
<!-- BEGIN:COMPONENT:head:head-paper-grade -->
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{esc(stem)} — Paper Grade Dashboard</title>
<meta name="author" content="David Lowe"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500;600;700&family=Oswald:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<!-- END:COMPONENT:head:head-paper-grade -->
<!-- BEGIN:COMPONENT:style:style-paper-grade -->
<style>{CSS}</style>
<!-- END:COMPONENT:style:style-paper-grade -->
</head>
<body>

<!-- BEGIN:COMPONENT:topbar:header-paper-grade -->
<header class="pg-header" id="pg-header" data-component="topbar" data-name="header-paper-grade">
  <span class="pg-brand">
    <span class="pg-mark">χ</span>
    <span class="pg-name"><span>Paper Grade</span> // Dashboard · Fruits Station</span>
  </span>
  <nav class="pg-nav" aria-label="Dashboard navigation" data-component="nav" data-name="section-nav">
    <a href="#metrics">Metrics</a>
    <a href="#heartbeat">Heartbeat</a>
    <a href="#fruits">Fruits</a>
    <a href="#gates">Gates</a>
    <a href="#claims">Claims</a>
    <a href="#ledger">Ledger</a>
    <a href="#report">Report</a>
  </nav>
</header>
<!-- END:COMPONENT:topbar:header-paper-grade -->

<!-- BEGIN:COMPONENT:hero:hero-paper-grade -->
<section class="pg-hero" data-component="hero" data-name="hero-paper-grade">
  <div class="pg-hero-inner">
    <div class="pg-hero-row">
      <div class="pg-hero-text" data-component="hero-text" data-name="hero-text">
        <div class="pg-hero-eyebrow" data-static="true">Fruits Grading Station · Paper Grader Surface</div>
        <h1 id="main-content">{esc(stem)}</h1>
        <p class="pg-hero-sub">Three-stage epistemic grading: lexicon pass, statistics engine, span-level
        judgment. This page makes the audit readable — the canonical record remains the JSON/XLSX.</p>
        <div class="pg-hero-address" data-component="data-block" data-name="semantic-address">
          <b>Source:</b> {esc(spans_doc["paper"])}<br/>
          <b>Model:</b> {esc(m["model"])} · <b>Prompt:</b> {esc(m.get("prompt_version", ""))} sha {esc(m["prompt_sha256"][:12])} ·
          <b>Rubric:</b> sha {esc(m["rubric_sha256"][:12])}<br/>
          <b>Weights:</b> sha {esc(weights_sha[:12])} · <b>Spans:</b> {m["ok"]} ok / {m["invalid"]} invalid ·
          <b>Tokens:</b> {tok.get("total", "?"):,} · <b>TRUTH:</b> {esc(truth)}
        </div>
      </div>
      <div class="pg-grade-badge" data-component="data-block" data-name="grade-badge">
        <div class="pg-grade-label">Signal Share</div>
        <div class="pg-grade-value">{share}<span style="font-size:1.2rem;color:var(--text-dim)">%</span></div>
        <div class="pg-grade-sub">band {band} · positive / (positive + |negative|)<br/>of weighted lexicon activity · TRUTH {esc(truth)}</div>
      </div>
    </div>
  </div>
</section>
<!-- END:COMPONENT:hero:hero-paper-grade -->

<!-- BEGIN:COMPONENT:section:stats-ribbon -->
<section class="pg-stats" id="metrics" data-component="section" data-name="stats-ribbon">
  <div class="pg-stats-inner">{ribbon_html}</div>
</section>
<!-- END:COMPONENT:section:stats-ribbon -->

<!-- BEGIN:COMPONENT:section:heartbeat -->
<section class="pg-sec" id="heartbeat" data-component="section" data-name="heartbeat">
  <div class="pg-sec-head"><span class="pg-sec-dot"></span><span class="pg-sec-kicker">Signal</span></div>
  <h2>Sentence Heartbeat — per-sentence TRUTH score</h2>
  <p class="pg-sec-desc">Weighted score of every sentence (fruit +1.0 · grounding +2.0 · anti-fruit −1.5 ·
  contradiction −0.5 · jargon −0.3 · propaganda −2.0). Hover the trace to inspect any sentence.</p>

  <div class="pg-inspector" data-component="panel" data-name="sentence-inspector">
    <h3>Sentence inspector — hover the trace</h3>
    <div class="pg-insp-text" id="hb-text">Hover over the chart to inspect a sentence…</div>
    <div class="pg-insp-meta">
      <div>idx <span id="hb-idx">—</span></div>
      <div>total <span id="hb-total">—</span></div>
      <div style="color:var(--green)">fruit <span id="hb-fruit">—</span></div>
      <div style="color:var(--red)">anti <span id="hb-anti">—</span></div>
      <div style="color:var(--blue)">ground <span id="hb-ground">—</span></div>
      <div style="color:var(--amber)">contra <span id="hb-contra">—</span></div>
      <div style="color:var(--red)">prop <span id="hb-prop">—</span></div>
      <div>jargon <span id="hb-jargon">—</span></div>
    </div>
  </div>

  <div class="pg-toggle-row" data-component="controls" data-name="heartbeat-toggles">
    <button class="pg-toggle active" onclick="hbToggle('hb-raw', this)">raw</button>
    <button class="pg-toggle active" onclick="hbToggle('hb-smooth', this)">smoothed (SMA-9)</button>
  </div>

  <div class="pg-panel" data-component="panel" data-name="heartbeat-chart">{heartbeat}</div>

  <div class="pg-ekg-tables">
    <div class="pg-panel" data-component="panel" data-name="ekg-peaks">
      <h3 style="font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;color:var(--green);text-transform:uppercase;margin-bottom:.5rem">Top 5 peaks</h3>
      <table class="pg-table" style="min-width:0"><thead><tr><th>#</th><th>score</th><th>dominant</th><th>excerpt</th></tr></thead>
      <tbody>{ekg_rows(peaks, "high")}</tbody></table>
    </div>
    <div class="pg-panel" data-component="panel" data-name="ekg-valleys">
      <h3 style="font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;color:var(--red);text-transform:uppercase;margin-bottom:.5rem">Top 5 valleys</h3>
      <table class="pg-table" style="min-width:0"><thead><tr><th>#</th><th>score</th><th>dominant</th><th>excerpt</th></tr></thead>
      <tbody>{ekg_rows(valleys, "low")}</tbody></table>
    </div>
  </div>
</section>
<!-- END:COMPONENT:section:heartbeat -->

<!-- BEGIN:COMPONENT:section:fruits-snapshot -->
<section class="pg-sec" id="fruits" data-component="section" data-name="fruits-snapshot">
  <div class="pg-sec-head"><span class="pg-sec-dot"></span><span class="pg-sec-kicker">Fruits Vector</span></div>
  <h2>Nine-Fruit Profile</h2>
  <p class="pg-sec-desc">Lexicon hits (Stage 1) vs. span-judged signals (Stage 3). Span signals split by
  polarity_kind: <b style="color:var(--green)">solid = enacted</b> (the text itself exhibits the fruit),
  <b>hatched = about</b> (the text discusses it in the world). − signals (anti-fruit pole) in red.{esc(kind_note)}</p>
  <div class="pg-panel">{fruit_svg}</div>
</section>
<!-- END:COMPONENT:section:fruits-snapshot -->

<!-- BEGIN:COMPONENT:section:gates -->
<section class="pg-sec" id="gates" data-component="section" data-name="gates">
  <div class="pg-sec-head"><span class="pg-sec-dot"></span><span class="pg-sec-kicker">Gates &amp; Vetoes</span></div>
  <h2>Gate Status</h2>
  <p class="pg-sec-desc">The seven rubric gates. A flag means at least one span raised the gate's question;
  hard gates are called out. Veto conditions below with span counts.</p>
  {gates_html}
  <h3 style="font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;color:var(--red);text-transform:uppercase;margin:1.2rem 0 .5rem">Veto conditions</h3>
  <div class="pg-veto-grid">{vetoes_html}</div>
</section>
<!-- END:COMPONENT:section:gates -->

<!-- BEGIN:COMPONENT:section:claims -->
<section class="pg-sec" id="claims" data-component="section" data-name="claims">
  <div class="pg-sec-head"><span class="pg-sec-dot"></span><span class="pg-sec-kicker">Claims</span></div>
  <h2>Claims Analysis</h2>
  <p class="pg-sec-desc">Rhetorical role distribution across {n_spans} spans (left) and claim-strength
  lexicon counts (right).</p>
  <div class="pg-claims-grid">
    <div class="pg-panel" style="display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap">
      {donut}
      <div class="pg-legend">{"".join(f'<div class="row"><span><span class="sw" style="background:{c}"></span>{esc(l)}</span><b>{v}</b></div>' for l, v, c in role_items)}</div>
    </div>
    <div class="pg-panel">
      <h3 style="font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;color:var(--gold);text-transform:uppercase;margin-bottom:.5rem">Claim strength (lexicon)</h3>
      {cs_bars}
      <div class="pg-legend" style="margin-top:.6rem">
        <div class="row"><span>hedge : absolute</span><b>{esc(sbk.get("hedge_to_absolute_ratio", {}).get("value", "n/a"))}</b></div>
        <div class="row"><span>grounding : claim</span><b>{esc(sbk.get("grounding_to_claim_ratio", {}).get("value", "n/a"))}</b></div>
        <div class="row"><span>strong : weak</span><b>{esc(sbk.get("claim_strength.strong_to_weak_ratio", {}).get("value", "n/a"))}</b></div>
      </div>
    </div>
  </div>
</section>
<!-- END:COMPONENT:section:claims -->

<!-- BEGIN:COMPONENT:section:ledger -->
<section class="pg-sec" id="ledger" data-component="section" data-name="ledger">
  <div class="pg-sec-head"><span class="pg-sec-dot"></span><span class="pg-sec-kicker">Ledger</span></div>
  <h2>Span Ledger</h2>
  <p class="pg-sec-desc">Every graded span in document order. Click a row for the full span text, its
  Stage 1 lexicon evidence, and the raw judgment JSON.</p>
  <div class="pg-table-wrap">
  <table class="pg-table" id="pg-ledger" data-component="table" data-name="span-ledger">
    <thead><tr><th>span</th><th>sents</th><th>role</th><th>fruit signals</th>
    <th>gate flags</th><th>veto / counterfeit</th><th>conf</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  </div>
  <div class="pg-detail pg-panel" id="pg-detail" data-component="panel" data-name="span-detail">
    <h3 id="d-title" style="color:var(--gold);margin-top:0"></h3>
    <h3>Span text</h3><pre id="d-text"></pre>
    <h3>Lexicon evidence (Stage 1)</h3><pre id="d-lex"></pre>
    <h3>Judgment JSON</h3><pre id="d-json"></pre>
  </div>
</section>
<!-- END:COMPONENT:section:ledger -->

<!-- BEGIN:COMPONENT:section:report -->
<section class="pg-sec" id="report" data-component="section" data-name="report">
  <div class="pg-sec-head"><span class="pg-sec-dot"></span><span class="pg-sec-kicker">Reading</span></div>
  <h2>The Reading</h2>
  <p class="pg-sec-desc">What this paper is like — and what it costs you to read it.
  A profile generated from the measured stats above; every characteristic cites the
  number or sentence it stands on.</p>
  <div class="pg-panel pg-reading">{reading_html}
    <div class="pg-read-meta">{esc(reading_meta)}</div>
  </div>
</section>
<!-- END:COMPONENT:section:report -->

<!-- BEGIN:COMPONENT:footer:footer-paper-grade -->
<footer class="pg-footer" data-component="footer" data-name="footer-paper-grade">
  <div class="feq">χ = f(G, M, E, S, T, K, R, Q, F, C)</div>
  <p>Fruits of the Spirit Grading Station · Paper Grade Dashboard</p>
  <p data-component="note" data-name="generation-stamp" style="margin-top:.35rem;font-size:.65rem">
    Generated {esc(gen_ts)} · sources: {esc(stem)}.lexicon.json / .stats.json / .spans.json<br/>
    weights sha {esc(weights_sha[:12])} · rubric sha {esc(m["rubric_sha256"][:12])} · prompt sha {esc(m["prompt_sha256"][:12])} ·
    narrative prompt {esc(NARRATIVE_PROMPT_VERSION)} sha {esc(narrative_prompt_sha[:12])}
  </p>
</footer>
<!-- END:COMPONENT:footer:footer-paper-grade -->

<!-- BEGIN:COMPONENT:script:script-paper-grade -->
<script>{JS.replace("%HB_DATA%", js_data(hb_data)).replace("%HB_META%", js_data(hb_meta)).replace("%DETAIL%", js_data(detail_js))}</script>
<!-- END:COMPONENT:script:script-paper-grade -->
</body>
</html>"""

    out_path = OUT_DIR / f"{stem}.report.html"
    out_path.write_text(html_doc, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"[report] wrote {out_path} ({size_kb:.0f} KB)")
    print(f"[report] what-this-means: {reading_meta}")


if __name__ == "__main__":
    main()
