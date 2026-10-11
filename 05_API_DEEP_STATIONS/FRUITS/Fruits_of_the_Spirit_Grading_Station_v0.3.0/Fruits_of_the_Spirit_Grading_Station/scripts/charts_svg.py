"""charts_svg.py -- inline-SVG chart builders for the Fruits grading report.

Pure Python, no JS libraries: every chart is deterministic SVG embedded in the
report HTML (works over file:// and prints). Used by report_page.py.

Charts:
  heartbeat_svg  per-sentence weighted TRUTH score polyline + smoothed overlay,
                 zero line, min/max markers, hover overlay rect (tiny vanilla
                 JS in report_page.py drives the inspector).
  fruit_profile_svg  nine fruit axes: lexicon-hit bars + diverging span-signal
                 bars (+ right / - left, enacted solid, about hatched).
  donut_svg      role distribution donut.
  hbars_svg      generic labeled horizontal bars (claim strength etc.).
"""

import html

GOLD = "#d4af37"
GREEN = "#4ade80"
AMBER = "#fb923c"
RED = "#f87171"
BLUE = "#38bdf8"
MUTED = "#5a5a5a"
GRID = "rgba(212,175,55,0.08)"


def esc(s):
    return html.escape(str(s), quote=True)


def sma(values, window=9):
    """Simple moving average, same length as input (partial windows at edges)."""
    out = []
    half = window // 2
    for i in range(len(values)):
        lo, hi = max(0, i - half), min(len(values), i + half + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def _fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _polyline(values, w, h, ymin, ymax, pad_l, pad_t, pad_r, pad_b):
    n = len(values)
    if n == 0:
        return "", []
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    span = (ymax - ymin) or 1.0
    pts = []
    for i, v in enumerate(values):
        x = pad_l + (i / max(1, n - 1)) * iw
        y = pad_t + (1 - (v - ymin) / span) * ih
        pts.append((round(x, 2), round(y, 2)))
    return " ".join(f"{x},{y}" for x, y in pts), pts


def heartbeat_svg(values, smoothed, n_sent, vbw=1040, vbh=300):
    """Per-sentence TRUTH heartbeat. Returns SVG markup string."""
    pad_l, pad_t, pad_r, pad_b = 48, 16, 12, 26
    ymin = min(min(values), 0.0)
    ymax = max(max(values), 0.0)
    if ymax == ymin:
        ymax = ymin + 1.0
    raw_pts, pts = _polyline(values, vbw, vbh, ymin, ymax, pad_l, pad_t, pad_r, pad_b)
    smo_pts, _ = _polyline(smoothed, vbw, vbh, ymin, ymax, pad_l, pad_t, pad_r, pad_b)

    iw, ih = vbw - pad_l - pad_r, vbh - pad_t - pad_b

    def y_of(v):
        return round(pad_t + (1 - (v - ymin) / (ymax - ymin)) * ih, 2)

    parts = [f'<svg viewBox="0 0 {vbw} {vbh}" width="100%" '
             f'preserveAspectRatio="none" style="display:block;height:300px" '
             f'data-component="data-viz" data-name="heartbeat-svg">']
    # horizontal gridlines + y labels (4 steps)
    for i in range(5):
        v = ymin + (ymax - ymin) * i / 4
        y = y_of(v)
        parts.append(f'<line x1="{pad_l}" y1="{y}" x2="{vbw - pad_r}" y2="{y}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l - 5}" y="{y + 3}" text-anchor="end" '
                     f'font-size="9" fill="{MUTED}" font-family="JetBrains Mono,monospace">{_fmt(v)}</text>')
    # x ticks: 10 evenly spaced sentence indices
    for i in range(11):
        idx = round(i * (n_sent - 1) / 10)
        x = round(pad_l + (idx / max(1, n_sent - 1)) * iw, 2)
        parts.append(f'<text x="{x}" y="{vbh - 8}" text-anchor="middle" font-size="9" '
                     f'fill="{MUTED}" font-family="JetBrains Mono,monospace">{idx}</text>')
    # zero line
    zy = y_of(0.0)
    parts.append(f'<line x1="{pad_l}" y1="{zy}" x2="{vbw - pad_r}" y2="{zy}" '
                 f'stroke="rgba(229,227,223,0.25)" stroke-width="1" stroke-dasharray="3,3"/>')
    # raw + smoothed polylines
    parts.append(f'<polyline id="hb-raw" points="{raw_pts}" fill="none" '
                 f'stroke="rgba(212,175,55,0.30)" stroke-width="1"/>')
    parts.append(f'<polyline id="hb-smooth" points="{smo_pts}" fill="none" '
                 f'stroke="{GOLD}" stroke-width="2.2"/>')
    # min / max markers
    imax = max(range(len(values)), key=lambda i: values[i])
    imin = min(range(len(values)), key=lambda i: values[i])
    for idx, col, tag in ((imax, GOLD, "max"), (imin, RED, "min")):
        x, y = pts[idx]
        ly = max(12.0, y - 8) if tag == "max" else min(vbh - pad_b - 4, y + 14)
        parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{col}"/>')
        parts.append(f'<text x="{min(max(x, 60.0), vbw - 80.0)}" y="{ly}" font-size="9" fill="{col}" '
                     f'font-family="JetBrains Mono,monospace">{tag} s{idx} {_fmt(values[idx])}</text>')
    # hover cursor + overlay
    parts.append(f'<line id="hb-cursor" x1="0" y1="{pad_t}" x2="0" y2="{vbh - pad_b}" '
                 f'stroke="{BLUE}" stroke-width="1" visibility="hidden"/>')
    parts.append(f'<rect id="hb-overlay" x="{pad_l}" y="{pad_t}" width="{iw}" height="{ih}" '
                 f'fill="transparent" onmousemove="hbMove(evt)" onmouseleave="hbLeave()"/>')
    parts.append("</svg>")
    return "".join(parts)


def fruit_profile_svg(profile, lex_hits, row_h=30, vbw=1040):
    """Nine fruit axes. profile[axis] = {"en+":n,"en-":n,"ab+":n,"ab-":n}.
    Left half: lexicon hits bar. Right half: diverging span-signal bar."""
    label_w = 120
    lex_x, lex_w = label_w + 8, 300
    sig_c = lex_x + lex_w + 170   # diverging center
    sig_half = 190
    axes = list(lex_hits.keys())
    vbh = 30 + row_h * len(axes) + 24
    max_lex = max(list(lex_hits.values()) + [1])
    max_sig = max([sum(p.values()) for p in profile.values()] + [1])

    parts = [f'<svg viewBox="0 0 {vbw} {vbh}" width="100%" style="display:block" '
             f'data-component="data-viz" data-name="fruit-profile-svg">']
    parts.append(
        f'<defs><pattern id="hatch" width="6" height="6" patternTransform="rotate(45)" '
        f'patternUnits="userSpaceOnUse">'
        f'<rect width="6" height="6" fill="{GREEN}" fill-opacity="0.55"/>'
        f'<line x1="0" y1="0" x2="0" y2="6" stroke="#0a0a0a" stroke-width="2.4"/></pattern>'
        f'<pattern id="hatch-neg" width="6" height="6" patternTransform="rotate(45)" '
        f'patternUnits="userSpaceOnUse">'
        f'<rect width="6" height="6" fill="{RED}" fill-opacity="0.55"/>'
        f'<line x1="0" y1="0" x2="0" y2="6" stroke="#0a0a0a" stroke-width="2.4"/></pattern></defs>')
    parts.append(f'<text x="{label_w}" y="16" font-size="10" fill="{MUTED}" '
                 f'font-family="JetBrains Mono,monospace" letter-spacing="1">FRUIT</text>')
    parts.append(f'<text x="{lex_x}" y="16" font-size="10" fill="{MUTED}" '
                 f'font-family="JetBrains Mono,monospace" letter-spacing="1">LEXICON HITS</text>')
    parts.append(f'<text x="{sig_c}" y="16" text-anchor="middle" font-size="10" fill="{MUTED}" '
                 f'font-family="JetBrains Mono,monospace" letter-spacing="1">SPAN SIGNALS  − | +</text>')

    for i, a in enumerate(axes):
        y = 30 + i * row_h
        cy = y + row_h / 2
        parts.append(f'<text x="{label_w - 8}" y="{cy + 4}" text-anchor="end" font-size="12" '
                     f'fill="#e5e3df" font-family="Crimson Text,serif">{esc(a.replace("_", " "))}</text>')
        # lexicon bar
        lv = lex_hits[a]
        lw = round(lv / max_lex * lex_w, 1)
        parts.append(f'<rect x="{lex_x}" y="{y + 6}" width="{max(lw, 0.5)}" height="{row_h - 12}" '
                     f'rx="2" fill="{BLUE}" fill-opacity="0.75"/>')
        parts.append(f'<text x="{lex_x + lw + 6}" y="{cy + 4}" font-size="10" fill="{MUTED}" '
                     f'font-family="JetBrains Mono,monospace">{lv}</text>')
        # diverging signal bar
        p = profile[a]
        center_y1, center_y2 = y + 4, y + row_h - 4
        parts.append(f'<line x1="{sig_c}" y1="{center_y1}" x2="{sig_c}" y2="{center_y2}" '
                     f'stroke="rgba(229,227,223,0.25)" stroke-width="1"/>')
        w_en = round(p["en+"] / max_sig * sig_half, 1)
        w_ab = round(p["ab+"] / max_sig * sig_half, 1)
        x = sig_c
        if w_en:
            parts.append(f'<rect x="{x}" y="{y + 6}" width="{w_en}" height="{row_h - 12}" fill="{GREEN}"/>')
            x += w_en
        if w_ab:
            parts.append(f'<rect x="{x}" y="{y + 6}" width="{w_ab}" height="{row_h - 12}" fill="url(#hatch)"/>')
        w_en_n = round(p["en-"] / max_sig * sig_half, 1)
        w_ab_n = round(p["ab-"] / max_sig * sig_half, 1)
        x = sig_c
        if w_en_n:
            parts.append(f'<rect x="{x - w_en_n}" y="{y + 6}" width="{w_en_n}" height="{row_h - 12}" fill="{RED}"/>')
            x -= w_en_n
        if w_ab_n:
            parts.append(f'<rect x="{x - w_ab_n}" y="{y + 6}" width="{w_ab_n}" height="{row_h - 12}" fill="url(#hatch-neg)"/>')
        pos, neg = p["en+"] + p["ab+"], p["en-"] + p["ab-"]
        parts.append(f'<text x="{sig_c + sig_half + 8}" y="{cy + 4}" font-size="10" '
                     f'fill="{MUTED}" font-family="JetBrains Mono,monospace">+{pos} / −{neg}</text>')
    parts.append("</svg>")
    return "".join(parts)


def donut_svg(items, size=240, thickness=34):
    """items: list of (label, value, color). Donut via stroke-dasharray circles."""
    import math
    total = sum(v for _, v, _ in items) or 1
    r = (size - thickness) / 2
    cx = cy = size / 2
    circ = 2 * math.pi * r
    parts = [f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
             f'data-component="data-viz" data-name="role-donut-svg">']
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1a1a1a" stroke-width="{thickness}"/>')
    offset = circ * 0.25  # start at top
    for label, v, color in items:
        seg = v / total * circ
        if seg <= 0:
            continue
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{thickness}" stroke-dasharray="{seg:.2f} {circ - seg:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}"><title>{esc(label)}: {v}</title></circle>')
        offset += seg
    parts.append(f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="26" fill="{GOLD}" '
                 f'font-family="Oswald,sans-serif">{total}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 16}" text-anchor="middle" font-size="9" fill="{MUTED}" '
                 f'font-family="JetBrains Mono,monospace" letter-spacing="1">SPANS</text>')
    parts.append("</svg>")
    return "".join(parts)


def hbars_svg(items, vbw=520, row_h=26):
    """items: list of (label, value, color). Labeled horizontal bars."""
    label_w = 110
    bar_w = vbw - label_w - 60
    vbh = 8 + row_h * len(items) + 4
    max_v = max([v for _, v, _ in items] + [1])
    parts = [f'<svg viewBox="0 0 {vbw} {vbh}" width="100%" style="display:block" '
             f'data-component="data-viz" data-name="hbars-svg">']
    for i, (label, v, color) in enumerate(items):
        y = 8 + i * row_h
        w = round(v / max_v * bar_w, 1)
        parts.append(f'<text x="{label_w - 8}" y="{y + row_h / 2 + 4}" text-anchor="end" '
                     f'font-size="11" fill="#e5e3df" font-family="Inter,sans-serif">{esc(label)}</text>')
        parts.append(f'<rect x="{label_w}" y="{y + 4}" width="{max(w, 0.5)}" height="{row_h - 8}" '
                     f'rx="2" fill="{color}" fill-opacity="0.8"/>')
        parts.append(f'<text x="{label_w + w + 6}" y="{y + row_h / 2 + 4}" font-size="10" '
                     f'fill="{MUTED}" font-family="JetBrains Mono,monospace">{v}</text>')
    parts.append("</svg>")
    return "".join(parts)
