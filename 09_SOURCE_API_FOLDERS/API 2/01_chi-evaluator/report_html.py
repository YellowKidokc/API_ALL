"""
report_html.py
==============
Generates a production-quality HTML report from a chi-evaluator run directory.
One report.html per run, with all claims and both models, full Chart.js visualization.
"""

import json
import math
import pathlib
from datetime import datetime

CHANNEL_ORDER = ["G", "M", "E", "S_eff", "T", "K", "R", "Q", "F", "C"]
CHANNEL_SHORT = {
    "G":     "G  Input",
    "M":     "M  Align",
    "E":     "E  Signal",
    "S_eff": "S  Entropy",
    "T":     "T  Time",
    "K":     "K  Compress",
    "R":     "R  Phase",
    "Q":     "Q  FreeWill",
    "F":     "F  Context",
    "C":     "C  Integr",
}
CHANNEL_FULL = {
    "G":     "External Input / Dependency Honesty",
    "M":     "Alignment / Reference Standard",
    "E":     "Truth / Signal Fidelity",
    "S_eff": "Entropy / Disorder Cost",
    "T":     "Temporal Persistence",
    "K":     "Compression / Wisdom Density",
    "R":     "Phase Transition / Justified Regime Change",
    "Q":     "Free Will / Invitation vs Coercion",
    "F":     "Cross-Context Binding",
    "C":     "Integration / Whole-System Coherence",
}
PRESSURE_ORDER = [
    "static", "compression", "strongest_objection", "time", "translation",
    "evidence", "implementation", "fruit", "falsification", "hostile_misuse",
]
FRUITS     = ["Love","Joy","Peace","Patience","Kindness","Goodness","Faithfulness","Gentleness","Self-Control"]
ANTIFRUITS = ["Hatred","Despair","Anxiety","Impatience","Cruelty","Corruption","Betrayal","Harshness","Addiction"]

MODEL_PALETTE = {
    "o3":             ("#d4af37", "rgba(212,175,55,0.18)", "rgba(212,175,55,0.06)"),
    "deepseek-chat":  ("#2dd4bf", "rgba(45,212,191,0.18)",  "rgba(45,212,191,0.06)"),
    "deepseek":       ("#2dd4bf", "rgba(45,212,191,0.18)",  "rgba(45,212,191,0.06)"),
    "gpt-4o":         ("#4a9eff", "rgba(74,158,255,0.18)",  "rgba(74,158,255,0.06)"),
    "_default":       ("#a855f7", "rgba(168,85,247,0.18)",  "rgba(168,85,247,0.06)"),
}

def _palette(label: str):
    for k, v in MODEL_PALETTE.items():
        if k in label.lower():
            return v
    return MODEL_PALETTE["_default"]

def _geo_mean(channels: list) -> float:
    scores = [c.get("effective_score", 0) for c in channels]
    if not scores:
        return 0.0
    log_sum = sum(math.log(max(s, 1e-10)) for s in scores)
    return round(math.exp(log_sum / len(scores)), 4)

def _verdict_color(verdict: str) -> str:
    v = verdict.lower()
    if "coherent" in v and "partially" not in v: return "#22c55e"
    if "partially" in v:                          return "#d4af37"
    if "fragile" in v:                            return "#f59e0b"
    if "deception" in v:                          return "#a855f7"
    if "collapse" in v:                           return "#ef4444"
    return "#4a9eff"

def _esc(s: str) -> str:
    import html as _h
    return _h.escape(str(s))

def _truncate(s: str, n: int = 260) -> str:
    s = s.replace("\n", " ").replace("\r", " ")
    while "  " in s:
        s = s.replace("  ", " ")
    s = s.strip()
    return (s[:n] + "…") if len(s) > n else s


# ── Data assembly ──────────────────────────────────────────────────────────────

def _load_run(run_dir: pathlib.Path) -> list[dict]:
    """Return list of claim groups: [{key, claim_text, models:{label: {...}}}]"""
    claims: dict[str, dict] = {}
    known_labels = list(MODEL_PALETTE.keys()) + ["o1", "gpt-4", "o3-mini"]

    for jf in sorted(run_dir.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        ev   = data.get("evaluation", {})
        ml   = data.get("model_label", "unknown")
        # Strip model label from stem to get claim key
        stem = jf.stem
        claim_key = stem
        for lbl in sorted(known_labels, key=len, reverse=True):
            if stem.lower().endswith(f"_{lbl}"):
                claim_key = stem[: -(len(lbl) + 1)]
                break

        gm = _geo_mean(ev.get("channel_results", []))
        if claim_key not in claims:
            ct = ev.get("claim", "")
            claims[claim_key] = {
                "key":        claim_key,
                "claim_text": ct,
                "models":     {},
                "statements": None,
            }
        claims[claim_key]["models"][ml] = {
            "ev":         ev,
            "usage":      data.get("usage", {}),
            "geo_mean":   gm,
            "model_label": ml,
        }

    # Load synthesized statements for each claim key
    for sf in run_dir.glob("*_statements.json"):
        try:
            sd = json.loads(sf.read_text(encoding="utf-8"))
            ck = sf.stem.replace("_statements", "")
            if ck in claims:
                claims[ck]["statements"] = sd.get("statements", {})
        except Exception:
            pass

    return list(claims.values())


# ── HTML builder ───────────────────────────────────────────────────────────────

def generate_run_report(run_dir: pathlib.Path) -> pathlib.Path | None:
    raw_claims = _load_run(run_dir)
    if not raw_claims:
        return None
    run_ts = run_dir.name  # run_20260617_162556
    # Serialize into a flat structure that all helpers can consume directly
    ser_claims = _serialize_claims(raw_claims)
    html_str = _build_html(ser_claims, run_ts)
    out = run_dir / "report.html"
    out.write_text(html_str, encoding="utf-8")
    return out


def _build_html(claims: list[dict], run_ts: str) -> str:
    # claims is already serialized; embed as JSON data island
    payload = json.dumps({"run": run_ts, "claims": claims}, ensure_ascii=False)

    # Tab nav
    tab_nav = _tab_nav(claims)
    # Claim panels
    panels   = "\n".join(_claim_panel(c, i) for i, c in enumerate(claims))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>χ-Evaluator Report — {_esc(run_ts)}</title>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600&family=Inter:wght@300;400;500;600&family=Oswald:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
{_styles()}
</head>
<body>
<div class="main">

<div class="report-header">
  <h1>χ&thinsp;Evaluator</h1>
  <div class="meta">Coherence Pressure Engine &mdash; {_esc(run_ts)} &mdash; {len(claims)} claim(s)</div>
  <div class="eq mono">χ = G · M · E · S · T · K · R · Q · F · C</div>
</div>

{tab_nav}

<div class="panels">
{panels}
</div>

<div class="footer">
  χ-Evaluator v2 &mdash; POF 2828 &mdash; Theophysics Master Equation
</div>

</div><!-- .main -->

<script type="application/json" id="runData">{payload}</script>
{_scripts()}
</body>
</html>"""


def _serialize_claims(claims: list[dict]) -> list[dict]:
    out = []
    for c in claims:
        models_ser = {}
        for ml, m in c["models"].items():
            ev = m["ev"]
            ch_by_code = {cr["channel"]: cr for cr in ev.get("channel_results", [])}
            channels_ordered = [ch_by_code.get(code, {"channel": code, "v_pos": 0, "v_neg": 0,
                                                        "effective_score": 0, "gradient_direction": 0,
                                                        "confidence": 0, "reasoning": "", "evidence": "",
                                                        "failure_mode": "", "repair_path": ""})
                                for code in CHANNEL_ORDER]
            models_ser[ml] = {
                "model_label":      ml,
                "geo_mean":         m["geo_mean"],
                "static_chi":       ev.get("static_chi", 0),
                "verdict":          ev.get("verdict", ""),
                "gradient":         ev.get("gradient", "neutral"),
                "zero_channels":    ev.get("zero_channels", []),
                "weakest_channels": ev.get("weakest_channels", []),
                "strongest_channels": ev.get("strongest_channels", []),
                "channels":         channels_ordered,
                "pressure_results": ev.get("pressure_results", []),
                "fruit_output":     ev.get("fruit_output", {}),
                "final_report":     ev.get("final_report", ""),
                "usage":            m["usage"],
            }
        out.append({
            "key":        c["key"],
            "claim_text": c["claim_text"],
            "models":     models_ser,
            "statements": c.get("statements") or {},
        })
    return out


# ── HTML components ────────────────────────────────────────────────────────────

def _tab_nav(claims: list[dict]) -> str:
    if len(claims) <= 1:
        return ""
    tabs = []
    for i, c in enumerate(claims):
        short = _truncate(c["claim_text"], 48)
        active = "active" if i == 0 else ""
        tabs.append(f'<button class="tab-btn {active}" onclick="showTab({i})">'
                    f'<span class="tab-num">{i+1}</span> {_esc(short)}</button>')
    return f'<div class="tab-nav">{"".join(tabs)}</div>'


def _claim_panel(claim: dict, idx: int) -> str:
    display = "block" if idx == 0 else "none"
    models  = claim["models"]
    stmts   = claim.get("statements") or {}

    # Summary cards row
    cards = _summary_cards(models, idx)

    # Radar + verdict column
    radar = _radar_section(models, idx)

    # Channel bar (comparison)
    channel_bar = _channel_bar_section(models, idx)

    # v_pos / v_neg decomposition
    decomp = _decomp_section(models, idx)

    # Fruit section
    fruit = _fruit_section(models, idx)

    # Pressure line
    pressure = _pressure_section(models, idx)

    # Channel detail table
    detail = _channel_detail_table(models)

    # Model usage footer
    usage_row = _usage_row(models)

    # Synthesized statements
    statements_html = _statements_section(stmts)

    short_claim = _truncate(claim["claim_text"], 400)

    return f"""<div class="claim-panel" id="panel-{idx}" style="display:{display}">

  <div class="claim-header">
    <div class="claim-text serif">&ldquo;{_esc(short_claim)}&rdquo;</div>
    <div class="claim-key mono">{_esc(claim["key"])}</div>
  </div>

  {statements_html}

  {cards}

  <div class="two-col">
    {radar}
    <div>
      {_gradient_grid(models)}
      {_chi_bars(models, idx)}
    </div>
  </div>

  {channel_bar}

  <div class="two-col">
    {decomp}
    {fruit}
  </div>

  {pressure}

  {detail}

  {usage_row}

</div>"""


def _summary_cards(models: dict, idx: int) -> str:
    cards_html = []
    for ml, m in models.items():
        col, _, _ = _palette(ml)
        verdict   = m["verdict"]
        vcol      = _verdict_color(verdict)
        gm        = m["geo_mean"]
        chi       = m["static_chi"]
        fs        = m["fruit_output"].get("fruit_score", 0.5)
        gradient  = m["gradient"]
        g_arrow   = {"positive": "↑", "negative": "↓", "neutral": "→", "unstable": "⚠"}.get(gradient, "→")
        g_col     = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#a0a0a0", "unstable": "#f59e0b"}.get(gradient, "#a0a0a0")

        weakest = ", ".join(m.get("weakest_channels", []))
        strongest = ", ".join(m.get("strongest_channels", []))

        cards_html.append(f"""<div class="model-card-group">
  <div class="model-label" style="color:{col}">{_esc(ml)}</div>
  <div class="card-row">
    <div class="card">
      <div class="card-label">Verdict</div>
      <div class="card-value" style="color:{vcol};font-size:1.1rem">{_esc(verdict.upper())}</div>
    </div>
    <div class="card">
      <div class="card-label">χ&thinsp;Geo-Mean</div>
      <div class="card-value">{gm:.4f}</div>
      <div class="card-sub">product: {chi:.6f}</div>
    </div>
    <div class="card">
      <div class="card-label">Fruit Score</div>
      <div class="card-value" style="color:{'#22c55e' if fs>0.6 else '#ef4444' if fs<0.4 else '#d4af37'}">{fs:.3f}</div>
      <div class="card-sub">Φ(χ) = tanh(4(χ − 0.3))</div>
    </div>
    <div class="card">
      <div class="card-label">Gradient</div>
      <div class="card-value" style="color:{g_col}">{g_arrow} {_esc(gradient)}</div>
    </div>
    <div class="card">
      <div class="card-label">Weakest</div>
      <div class="card-value" style="font-size:1rem;color:#ef4444">{_esc(weakest)}</div>
    </div>
    <div class="card">
      <div class="card-label">Strongest</div>
      <div class="card-value" style="font-size:1rem;color:#22c55e">{_esc(strongest)}</div>
    </div>
  </div>
</div>""")

    return f'<div class="summary-cards">{"".join(cards_html)}</div>'


def _radar_section(models: dict, idx: int) -> str:
    datasets = []
    for ml, m in models.items():
        col, fill, _ = _palette(ml)
        scores = [round(c.get("effective_score", 0), 4) for c in m["channels"]]
        scores_js = json.dumps(scores)
        datasets.append(f"""{{
          label: {json.dumps(ml)},
          data: {scores_js},
          borderColor: '{col}',
          backgroundColor: '{fill}',
          pointBackgroundColor: '{col}',
          pointRadius: 4,
          borderWidth: 2,
        }}""")

    datasets_js = ",\n".join(datasets)
    labels_js = json.dumps([CHANNEL_SHORT.get(c, c) for c in CHANNEL_ORDER])

    return f"""<div class="chart-box">
  <div class="chart-title">Channel Profile — Radar</div>
  <canvas id="radar-{idx}" style="max-height:340px"></canvas>
  <script>
  (function(){{
    var ctx = document.getElementById('radar-{idx}').getContext('2d');
    new Chart(ctx, {{
      type: 'radar',
      data: {{
        labels: {labels_js},
        datasets: [{datasets_js}]
      }},
      options: {{
        responsive: true,
        scales: {{
          r: {{
            min: 0, max: 1,
            ticks: {{ stepSize: 0.25, color: '#666', backdropColor: 'transparent', font: {{size:10}} }},
            grid: {{ color: '#2a2a2a' }},
            pointLabels: {{ color: '#a0a0a0', font: {{size:10}} }},
            angleLines: {{ color: '#2a2a2a' }},
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#a0a0a0', boxWidth:12 }} }}
        }}
      }}
    }});
  }})();
  </script>
</div>"""


def _channel_bar_section(models: dict, idx: int) -> str:
    labels_js = json.dumps([CHANNEL_SHORT.get(c, c) for c in CHANNEL_ORDER])
    datasets = []
    for ml, m in models.items():
        col, fill, _ = _palette(ml)
        scores = [round(c.get("effective_score", 0), 4) for c in m["channels"]]
        datasets.append(f"""{{
          label: {json.dumps(ml)},
          data: {json.dumps(scores)},
          backgroundColor: '{col}',
          borderColor: '{col}',
          borderWidth: 1,
          borderRadius: 3,
        }}""")

    return f"""<div class="chart-box">
  <div class="chart-title">Channel Scores Comparison</div>
  <canvas id="chanbar-{idx}" style="max-height:260px"></canvas>
  <script>
  (function(){{
    var ctx = document.getElementById('chanbar-{idx}').getContext('2d');
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: {labels_js},
        datasets: [{",".join(datasets)}]
      }},
      options: {{
        responsive: true,
        scales: {{
          y: {{ min:0, max:1, grid:{{color:'#2a2a2a'}}, ticks:{{color:'#666',stepSize:0.25}} }},
          x: {{ grid:{{color:'#1a1a1a'}}, ticks:{{color:'#a0a0a0',font:{{size:10}}}} }}
        }},
        plugins: {{ legend: {{ labels: {{ color:'#a0a0a0', boxWidth:12 }} }} }}
      }}
    }});
  }})();
  </script>
</div>"""


def _decomp_section(models: dict, idx: int) -> str:
    labels_js = json.dumps([CHANNEL_SHORT.get(c, c) for c in CHANNEL_ORDER])
    sections = []
    for ml, m in models.items():
        col, _, _ = _palette(ml)
        vpos = [round(c.get("v_pos", 0), 4) for c in m["channels"]]
        # Effective loss from v_neg: v_pos - effective_score
        vloss = [round(c.get("v_pos", 0) - c.get("effective_score", 0), 4) for c in m["channels"]]
        eid = f"decomp-{idx}-{ml.replace('-','')}"
        sections.append(f"""<div class="chart-box">
  <div class="chart-title">v⁺ / v⁻ Decomposition — {_esc(ml)}</div>
  <canvas id="{eid}" style="max-height:220px"></canvas>
  <script>
  (function(){{
    var ctx = document.getElementById('{eid}').getContext('2d');
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: {labels_js},
        datasets: [
          {{ label:'v⁺ (positive)', data:{json.dumps(vpos)}, backgroundColor:'rgba(34,197,94,0.7)', stack:'s' }},
          {{ label:'v⁻ loss',       data:{json.dumps(vloss)}, backgroundColor:'rgba(239,68,68,0.6)',  stack:'s' }},
        ]
      }},
      options: {{
        responsive: true,
        scales: {{
          y: {{ min:0, max:1, stacked:true, grid:{{color:'#2a2a2a'}}, ticks:{{color:'#666',stepSize:0.25}} }},
          x: {{ stacked:true, grid:{{color:'#1a1a1a'}}, ticks:{{color:'#a0a0a0',font:{{size:10}}}} }}
        }},
        plugins: {{ legend: {{ labels: {{ color:'#a0a0a0', boxWidth:12 }} }} }}
      }}
    }});
  }})();
  </script>
</div>""")

    return f'<div>{"".join(sections)}</div>'


def _fruit_section(models: dict, idx: int) -> str:
    sections = []
    for ml, m in models.items():
        col, _, _ = _palette(ml)
        fo   = m["fruit_output"]
        fs   = fo.get("fruit_score", 0.5)
        afs  = round(1.0 - fs, 3)
        fruits    = fo.get("dominant_fruits", [])
        antifruits = fo.get("dominant_antifruits", [])

        fruit_badges = " ".join(f'<span class="badge badge-green">{_esc(f)}</span>' for f in fruits)
        anti_badges  = " ".join(f'<span class="badge badge-red">{_esc(f)}</span>' for f in antifruits)
        if not fruit_badges:
            fruit_badges = '<span class="dim">—</span>'
        if not anti_badges:
            anti_badges  = '<span class="dim">—</span>'

        eid = f"fruit-{idx}-{ml.replace('-','')}"
        sections.append(f"""<div class="chart-box">
  <div class="chart-title">Fruit Coherence — {_esc(ml)}</div>
  <div style="display:flex;gap:1.5rem;align-items:center">
    <div style="width:140px;flex-shrink:0">
      <canvas id="{eid}"></canvas>
    </div>
    <div>
      <div class="card-label" style="margin-bottom:0.5rem">FRUITS <span class="mono" style="color:#22c55e">{fs:.3f}</span></div>
      <div style="margin-bottom:0.75rem">{fruit_badges}</div>
      <div class="card-label" style="margin-bottom:0.5rem">ANTI-FRUITS <span class="mono" style="color:#ef4444">{afs:.3f}</span></div>
      <div>{anti_badges}</div>
      <div style="margin-top:0.8rem;font-size:0.72rem;color:#666">Φ(χ) = tanh(4·(χ − 0.30))</div>
    </div>
  </div>
  <script>
  (function(){{
    var ctx = document.getElementById('{eid}').getContext('2d');
    new Chart(ctx, {{
      type: 'doughnut',
      data: {{
        labels: ['Fruits','Anti-Fruits'],
        datasets: [{{
          data: [{round(fs,4)}, {round(afs,4)}],
          backgroundColor: ['rgba(34,197,94,0.75)','rgba(239,68,68,0.6)'],
          borderColor:     ['#22c55e','#ef4444'],
          borderWidth: 2,
        }}]
      }},
      options: {{
        responsive:true, cutout:'68%',
        plugins:{{
          legend:{{display:false}},
          tooltip:{{callbacks:{{label:function(c){{return c.label+': '+c.raw.toFixed(3)}}}}}}
        }}
      }}
    }});
  }})();
  </script>
</div>""")

    return f'<div>{"".join(sections)}</div>'


def _pressure_section(models: dict, idx: int) -> str:
    # Only render if at least one model has pressure results
    has_pressure = any(m["pressure_results"] for m in models.values())
    if not has_pressure:
        return ""

    datasets = []
    for ml, m in models.items():
        col, _, _ = _palette(ml)
        pr = m["pressure_results"]
        pr_by_state = {p["pressure_state"]: p.get("chi", 0) for p in pr}
        vals = [round(pr_by_state.get(s, 0), 4) for s in PRESSURE_ORDER]
        datasets.append(f"""{{
          label: {json.dumps(ml)},
          data: {json.dumps(vals)},
          borderColor: '{col}',
          backgroundColor: 'transparent',
          pointBackgroundColor: '{col}',
          pointRadius: 5,
          borderWidth: 2,
          tension: 0.3,
        }}""")

    labels_js = json.dumps([s.replace("_", " ").title() for s in PRESSURE_ORDER])

    return f"""<div class="chart-box">
  <div class="chart-title">Pressure States — χ Across 10 Conditions</div>
  <canvas id="pressure-{idx}" style="max-height:220px"></canvas>
  <script>
  (function(){{
    var ctx = document.getElementById('pressure-{idx}').getContext('2d');
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: {labels_js},
        datasets: [{",".join(datasets)}]
      }},
      options: {{
        responsive:true,
        scales:{{
          y:{{ min:0, max:1, grid:{{color:'#2a2a2a'}}, ticks:{{color:'#666',stepSize:0.25}} }},
          x:{{ grid:{{color:'#1a1a1a'}}, ticks:{{color:'#a0a0a0',font:{{size:10}}}} }}
        }},
        plugins:{{ legend:{{ labels:{{ color:'#a0a0a0', boxWidth:12 }} }} }}
      }}
    }});
  }})();
  </script>
</div>"""


def _gradient_grid(models: dict) -> str:
    arrows = {1: ("↑", "#22c55e"), 0: ("→", "#666"), -1: ("↓", "#ef4444")}
    rows = [f'<div class="grad-grid">']
    rows.append(f'<div class="grad-header"></div>')
    for ml in models:
        col, _, _ = _palette(ml)
        rows.append(f'<div class="grad-header" style="color:{col}">{_esc(ml[:8])}</div>')

    for ch in CHANNEL_ORDER:
        rows.append(f'<div class="grad-label mono">{_esc(ch)}</div>')
        for ml, m in models.items():
            cr = next((c for c in m["channels"] if c.get("channel") == ch), {})
            gd = cr.get("gradient_direction", 0)
            sym, col = arrows.get(gd, ("?", "#666"))
            rows.append(f'<div class="grad-cell" style="color:{col}">{sym}</div>')
    rows.append('</div>')

    return f'<div class="chart-box"><div class="chart-title">Gradient Directions</div>{"".join(rows)}</div>'


def _chi_bars(models: dict, idx: int) -> str:
    """Small horizontal bars showing χ product and geo-mean per model."""
    items = []
    for ml, m in models.items():
        col, _, _ = _palette(ml)
        gm  = m["geo_mean"]
        chi = m["static_chi"]
        pct = int(gm * 100)
        items.append(f"""<div style="margin-bottom:0.9rem">
  <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:1px;color:#666;margin-bottom:0.3rem">
    {_esc(ml)} — geo-mean</div>
  <div style="background:#1a1a1a;border-radius:3px;height:6px;margin-bottom:0.2rem">
    <div style="width:{pct}%;height:100%;background:{col};border-radius:3px"></div></div>
  <div style="display:flex;justify-content:space-between;font-size:0.7rem;font-family:JetBrains Mono,monospace">
    <span style="color:{col}">{gm:.4f}</span>
    <span style="color:#444">prod: {chi:.6f}</span>
  </div>
</div>""")

    return f'<div class="chart-box"><div class="chart-title">χ Scale</div>{"".join(items)}</div>'


def _statements_section(stmts: dict) -> str:
    if not stmts or not any(stmts.get(k) for k in
                            ("one_liner","formal_scientific","theological_narrative","cross_model_comparison")):
        return ""

    STMT_DEFS = [
        ("one_liner",               "One-Liner",            "#d4af37", "Shareable, citable summary"),
        ("formal_scientific",       "Formal Scientific",    "#4a9eff", "For academic reviewers and papers"),
        ("theological_narrative",   "Theological Narrative","#22c55e", "Plain-language spiritual interpretation"),
        ("cross_model_comparison",  "Cross-Model",          "#2dd4bf", "O3 vs DeepSeek agreement and divergence"),
    ]

    cards = []
    for key, label, color, desc in STMT_DEFS:
        text = stmts.get(key, "")
        if not text:
            continue
        cards.append(f"""<div class="stmt-card">
  <div class="stmt-label" style="color:{color}">{label}</div>
  <div class="stmt-desc">{desc}</div>
  <div class="stmt-text serif">{_esc(text)}</div>
</div>""")

    if not cards:
        return ""

    return f"""<div class="chart-box stmts-box">
  <div class="chart-title">&#9670; Synthesized Statements — Fruit-Anchored</div>
  <div class="stmts-grid">{"".join(cards)}</div>
</div>"""


def _channel_detail_table(models: dict) -> str:
    rows = []
    for ch in CHANNEL_ORDER:
        col_cells = []
        for ml, m in models.items():
            palette_col, _, _ = _palette(ml)
            cr = next((c for c in m["channels"] if c.get("channel") == ch), {})
            es   = cr.get("effective_score", 0)
            reas = _esc(cr.get("reasoning", "")) or '<span class="dim">—</span>'
            fm   = cr.get("failure_mode", "")
            fm_html = (f'<span class="badge badge-red">{_esc(fm)}</span>' if fm else "")
            rp   = cr.get("repair_path", "")
            rp_html = (f'<div style="margin-top:0.3rem;font-size:0.72rem;color:#a0a0a0">{_esc(rp)}</div>' if rp else "")
            bar_pct = int(es * 100)
            col_cells.append(f"""<td>
  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem">
    <span class="mono" style="color:{palette_col};font-size:0.85rem">{es:.3f}</span>
    <div style="flex:1;background:#1a1a1a;height:4px;border-radius:2px">
      <div style="width:{bar_pct}%;height:100%;background:{palette_col};border-radius:2px"></div></div>
  </div>
  <div style="font-size:0.78rem;color:#a0a0a0;line-height:1.4">{reas}</div>
  {fm_html}{rp_html}
</td>""")

        rows.append(f"""<tr>
  <td class="ch-code">
    <div class="mono" style="color:#d4af37">{_esc(ch)}</div>
    <div style="font-size:0.7rem;color:#666">{_esc(CHANNEL_FULL.get(ch,''))}</div>
  </td>
  {"".join(col_cells)}
</tr>""")

    # Build header
    ths = "".join(f'<th style="color:{_palette(ml)[0]}">{_esc(ml)}</th>' for ml in models)

    return f"""<div class="chart-box">
  <div class="chart-title">Channel Detail &amp; Reasoning</div>
  <table class="detail-table">
    <thead><tr><th>Channel</th>{ths}</tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>"""


def _usage_row(models: dict) -> str:
    cards = []
    for ml, m in models.items():
        col, _, _ = _palette(ml)
        u = m["usage"]
        pt = u.get("prompt_tokens", "?")
        ct = u.get("completion_tokens", "?")
        el = u.get("elapsed_s", "?")
        cards.append(f"""<div class="card">
  <div class="card-label" style="color:{col}">{_esc(ml)}</div>
  <div class="card-sub">in {pt} tok / out {ct} tok / {el}s</div>
</div>""")

    return f'<div class="card-row">' + "".join(cards) + "</div>"


# ── Styles ─────────────────────────────────────────────────────────────────────

def _styles() -> str:
    return """<style>
:root {
  --bg:#0a0a0a; --surface:#0f0f0f; --surface2:#1a1a1a;
  --border:#2a2a2a; --gold:#d4af37; --gold-dim:rgba(212,175,55,0.1);
  --text:#e8e8e8; --text-dim:#a0a0a0; --text-muted:#666;
  --red:#ef4444; --blue:#4a9eff; --teal:#2dd4bf; --green:#22c55e; --orange:#f59e0b;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;font-size:15px}
.serif{font-family:'Crimson Text',serif}
.mono{font-family:'JetBrains Mono',monospace}
.main{max-width:1100px;margin:0 auto;padding:2rem 1.5rem 4rem}
.dim{color:#444;font-style:italic}

/* Header */
.report-header{margin-bottom:2rem;padding-bottom:1.5rem;border-bottom:1px solid var(--border)}
h1{font-family:'Oswald',sans-serif;font-size:2rem;color:var(--gold);text-transform:uppercase;letter-spacing:3px;margin-bottom:0.25rem}
.meta{font-size:0.8rem;color:var(--text-muted);margin-bottom:0.5rem}
.eq{font-size:0.8rem;color:#444;letter-spacing:1px}

/* Tabs */
.tab-nav{display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:1.5rem;padding:0.75rem;
  background:var(--surface);border:1px solid var(--border);border-radius:8px}
.tab-btn{font-family:'Oswald',sans-serif;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;
  color:var(--text-muted);background:transparent;border:1px solid transparent;border-radius:4px;
  padding:0.4rem 0.8rem;cursor:pointer;text-align:left;transition:all 0.15s;display:flex;align-items:center;gap:0.5rem}
.tab-btn:hover{color:var(--text-dim);background:var(--surface2)}
.tab-btn.active{color:var(--gold);border-color:rgba(212,175,55,0.3);background:var(--gold-dim)}
.tab-num{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;
  border-radius:50%;background:var(--surface2);font-size:0.65rem;color:var(--text-muted);flex-shrink:0}

/* Claim panel */
.claim-panel{margin-bottom:3rem}
.claim-header{margin-bottom:1.5rem;padding:1.25rem 1.5rem;
  background:var(--surface);border:1px solid var(--border);border-radius:8px;
  border-left:4px solid var(--gold)}
.claim-text{font-size:1.05rem;color:var(--text);line-height:1.55;margin-bottom:0.5rem}
.claim-key{font-size:0.72rem;color:var(--text-muted)}

/* Summary cards */
.summary-cards{margin-bottom:1rem}
.model-card-group{margin-bottom:1rem}
.model-label{font-family:'Oswald',sans-serif;font-size:0.75rem;text-transform:uppercase;
  letter-spacing:1px;margin-bottom:0.5rem;padding-bottom:0.25rem;border-bottom:1px solid var(--border)}
.card-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:0.75rem;margin-bottom:0.5rem}
.card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:0.85rem 1rem}
.card-label{font-size:0.65rem;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin-bottom:0.35rem}
.card-value{font-family:'Oswald',sans-serif;font-size:1.45rem;color:var(--gold)}
.card-sub{font-size:0.72rem;color:var(--text-muted);margin-top:0.2rem}

/* Layout */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}
.chart-box{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1.25rem;margin-bottom:1rem}
.chart-title{font-family:'Oswald',sans-serif;font-size:0.75rem;text-transform:uppercase;
  letter-spacing:1px;color:var(--text-muted);margin-bottom:0.9rem}

/* Gradient grid */
.grad-grid{display:grid;gap:2px;font-size:0.8rem}
.grad-header{font-family:'Oswald',sans-serif;font-size:0.65rem;text-transform:uppercase;
  letter-spacing:0.08em;color:var(--text-muted);padding:0.2rem 0.4rem}
.grad-label{color:var(--text-muted);padding:0.2rem 0.4rem;font-size:0.78rem}
.grad-cell{text-align:center;padding:0.25rem 0.4rem;font-size:1.1rem;font-weight:600}

/* Detail table */
.detail-table{width:100%;border-collapse:collapse;font-size:0.82rem}
.detail-table th{font-family:'Oswald',sans-serif;font-size:0.65rem;text-transform:uppercase;
  letter-spacing:0.1em;color:var(--text-muted);padding:0.6rem 0.75rem;text-align:left;
  border-bottom:2px solid var(--border)}
.detail-table td{padding:0.65rem 0.75rem;border-bottom:1px solid var(--border);vertical-align:top}
.detail-table tr:hover td{background:rgba(212,175,55,0.02)}
.ch-code{width:140px;white-space:nowrap}

/* Badges */
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.7rem;font-weight:600;margin:2px}
.badge-green{background:rgba(34,197,94,0.15);color:#22c55e}
.badge-red{background:rgba(239,68,68,0.15);color:#ef4444}
.badge-gold{background:rgba(212,175,55,0.15);color:var(--gold)}
.badge-blue{background:rgba(74,158,255,0.15);color:#4a9eff}

/* Synthesized statements */
.stmts-box{border-color:rgba(212,175,55,0.35);background:rgba(212,175,55,0.03)}
.stmts-grid{display:grid;grid-template-columns:1fr 1fr;gap:0.85rem}
.stmt-card{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:0.9rem 1rem}
.stmt-label{font-family:'Oswald',sans-serif;font-size:0.7rem;text-transform:uppercase;
  letter-spacing:1px;margin-bottom:0.2rem;font-weight:600}
.stmt-desc{font-size:0.7rem;color:var(--text-muted);margin-bottom:0.6rem}
.stmt-text{font-size:0.93rem;line-height:1.6;color:var(--text)}
@media(max-width:700px){.stmts-grid{grid-template-columns:1fr}}

.footer{text-align:center;margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--border);
  font-size:0.72rem;color:var(--text-muted)}

@media(max-width:700px){
  .two-col{grid-template-columns:1fr}
  .card-row{grid-template-columns:1fr 1fr}
}
</style>"""


# ── Scripts ────────────────────────────────────────────────────────────────────

def _scripts() -> str:
    return """<script>
function showTab(idx) {
  document.querySelectorAll('.claim-panel').forEach((p,i) => p.style.display = i===idx?'block':'none');
  document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', i===idx));
}

// Set gradient grid column counts dynamically
document.querySelectorAll('.grad-grid').forEach(function(g){
  // count headers to determine columns
  var cols = g.querySelectorAll('.grad-header').length;
  if(cols > 0) g.style.gridTemplateColumns = '80px ' + Array(cols).fill('1fr').join(' ');
});
</script>"""


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    run_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not run_path or not run_path.is_dir():
        print("Usage: python report_html.py <run_dir>")
        sys.exit(1)
    out = generate_run_report(run_path)
    print(f"Report: {out}")
