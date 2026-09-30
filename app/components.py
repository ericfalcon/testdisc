"""Shared styling and readout primitives.

Design thesis: this is an instrument, not a personality quiz. Every number the
app reports carries uncertainty, so the signature element is the error bar — the
same visual grammar for dimension scores, win rates and strain. Numbers are set
in a monospace face and labelled like instrument channels; nothing is reported
as a bare figure.
"""

from __future__ import annotations

import html
import math

import streamlit as st

INK = "#0F2233"
SLATE = "#46586B"
PAPER = "#F7F8FA"
RULE = "#DCE3EA"
SIGNAL = "#1B6E8C"
FLAG = "#B4471F"

STYLE_COLOURS = {"D": "#C2453B", "I": "#C98A16", "S": "#2E8B5A", "C": "#2C6FB5"}
DOMAIN_COLOURS = {
    "Construire": "#6B4C9A",
    "Mobiliser": "#C9762B",
    "Relier": "#1F8A70",
    "Éclairer": "#2F5D8A",
}
TRIAD_COLOURS = {
    "Corps": "#8A4B3E",
    "Cœur": "#B23A5E",
    "Tête": "#4A5FA8",
}
CONFIDENCE_COLOURS = {"High": "#2E8B5A", "Moderate": "#C98A16", "Low": FLAG}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* Base type scale bumped up: this is read on trainees' own screens, often
   projected or read quickly before a training session, so body copy and the
   test questions need to be comfortably legible rather than compact. Since
   almost every size below is in rem, scaling the root percentage scales the
   whole app proportionally in one place. */
html {{ font-size: 118%; }}

.stApp {{ background: {PAPER}; }}
/* Streamlit's header is fixed and overlays the top of the page, so the first
   line needs to clear it rather than slide underneath. */
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ max-width: 920px; padding-top: 4.75rem; padding-bottom: 4rem; }}

html, body, [class*="css"], .stMarkdown, .stRadio label {{
    font-family: 'Source Sans 3', system-ui, sans-serif;
    color: {INK};
    font-size: 1.05rem;
}}
.stMarkdown p, .panel p, [data-testid="stMarkdownContainer"] p {{
    font-size: 1.05rem; line-height: 1.62;
}}
h1, h2, h3, h4 {{ font-family: 'Archivo', system-ui, sans-serif; letter-spacing: -0.015em; }}

/* Instrument channel labels: mono, spaced, quiet. Used as eyebrows everywhere. */
.chan {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    line-height: 1.7;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {SLATE};
}}
.num {{ font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; }}

.masthead {{ border-bottom: 1px solid {RULE}; padding-bottom: 1.1rem; margin-bottom: 1.8rem; }}
.masthead h1 {{
    font-size: 1.72rem; font-weight: 700; margin: 0.25rem 0 0.3rem 0; line-height: 1.15;
}}
.masthead p {{ color: {SLATE}; margin: 0; font-size: 0.98rem; }}

/* ---- the signature: a value with its uncertainty drawn, never a bare number */
.readout {{ margin: 0 0 1.05rem 0; }}
.readout-head {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }}
.readout-val {{ font-family: 'IBM Plex Mono', monospace; font-size: 1.02rem; font-weight: 600; font-variant-numeric: tabular-nums; }}
.readout-pm {{ font-size: 0.78rem; font-weight: 400; color: {SLATE}; margin-left: 5px; }}
.track {{ position: relative; height: 15px; background: transparent; }}
.track:before {{
    content: ""; position: absolute; left: 0; right: 0; top: 7px; height: 1px; background: {RULE};
}}
.ci {{ position: absolute; top: 4px; height: 7px; border-radius: 1px; opacity: 0.26; }}
.ci:before, .ci:after {{
    content: ""; position: absolute; top: -3px; width: 1px; height: 13px; background: currentColor; opacity: 0.85;
}}
.ci:before {{ left: 0; }} .ci:after {{ right: 0; }}
.pt {{ position: absolute; top: 1px; width: 3px; height: 13px; border-radius: 1px; }}

/* ---- cards */
.panel {{
    background: #FFFFFF; border: 1px solid {RULE}; border-radius: 3px;
    padding: 20px 24px; margin-bottom: 16px;
}}
.panel h4 {{ margin: 0 0 0.5rem 0; font-size: 1.06rem; font-weight: 600; }}
.panel p {{ margin: 0 0 0.55rem 0; line-height: 1.62; }}
.panel p:last-child {{ margin-bottom: 0; }}

.theme-card {{
    background: #FFFFFF; border: 1px solid {RULE}; border-left: 3px solid {SIGNAL};
    border-radius: 3px; padding: 18px 22px; margin-bottom: 12px;
}}
.theme-rank {{ font-family: 'IBM Plex Mono', monospace; color: {SLATE}; font-size: 0.8rem; }}
.theme-name {{ font-family: 'Archivo', sans-serif; font-size: 1.14rem; font-weight: 600; }}
.theme-cost {{
    border-top: 1px dashed {RULE}; margin-top: 12px; padding-top: 10px;
    font-size: 0.93rem; color: {SLATE};
}}
.theme-cost b {{ color: {INK}; }}

.caveat {{
    border-left: 3px solid {FLAG}; background: #FDF6F3; padding: 14px 18px;
    border-radius: 0 3px 3px 0; margin-bottom: 18px; font-size: 0.95rem;
}}
.caveat ul {{ margin: 0.4rem 0 0 1rem; padding: 0; }}

.tag {{
    display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    letter-spacing: 0.1em; text-transform: uppercase; padding: 3px 9px;
    border: 1px solid {RULE}; border-radius: 2px; margin-right: 6px; color: {SLATE};
    background: #FFFFFF;
}}

/* ---- question screen */
.qprompt {{
    font-family: 'Archivo', sans-serif; font-size: 1.58rem; font-weight: 500;
    line-height: 1.4; margin: 0.2rem 0 0.15rem 0;
}}
.qframe {{ color: {SLATE}; font-size: 1.02rem; font-style: italic; margin-bottom: 1.4rem; }}
.qcard {{ animation: rise 220ms ease-out; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ .qcard {{ animation: none; }} }}

/* The two statements of a graduated forced-choice item, with the five-point
   scale sandwiched between them ("phrase du haut" / "phrase du bas"). */
.pole {{
    font-family: 'Archivo', sans-serif; font-size: 1.1rem; font-weight: 500;
    line-height: 1.45; padding: 14px 18px; border: 1px solid {RULE}; border-radius: 3px;
    background: #FFFFFF;
}}
.pole-a {{ margin-bottom: 12px; }}
.pole-b {{ margin-top: 12px; }}

.meter {{ height: 2px; background: {RULE}; margin: 6px 0 26px 0; }}
.meter > div {{ height: 2px; background: {SIGNAL}; transition: width 220ms ease-out; }}

/* ---- widgets */
/* Options share one row and never wrap onto a second: five cells for the agree
   scale, two for a forced choice. Equal basis of 0 makes every cell the same
   width regardless of how long its label is. */
.stRadio > div[role="radiogroup"] {{
    display: flex; width: 100%;
    flex-direction: row; flex-wrap: nowrap; align-items: stretch;
    gap: 8px; padding: 4px 0 16px 0;
}}
/* The group is fit-content by default, so the cells were dividing a container
   narrower than the column and clipping their labels. */
.stRadio, .stRadio > div {{ width: 100%; }}
.stRadio > div[role="radiogroup"] > label {{
    flex: 1 1 0; min-width: 0; overflow: visible; margin: 0; padding: 11px 13px;
    background: #FFFFFF; border: 1px solid {RULE}; border-radius: 3px;
    font-size: 0.96rem; line-height: 1.4; align-items: flex-start;
    justify-content: center;
    transition: border-color 120ms ease, background 120ms ease;
}}
/* The five-point scale is tighter than a two-way choice, so it gets a smaller
   type size. French labels ("Pas du tout d'accord", "Tout à fait d'accord")
   run longer than the original English ones, so each cell wraps onto two
   lines rather than forcing one line and overflowing into its neighbour.
   justify-content centres the radio dot + text as a block within the cell,
   the same way the "Suivant" button centres its own label below it. */
.stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) {{ gap: 6px; }}
.stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label {{
    padding: 11px 8px; font-size: 0.92rem; align-items: center;
    justify-content: center;
    white-space: normal; text-align: center; word-break: break-word;
}}
.stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label div {{
    white-space: normal;
}}
.stRadio > div[role="radiogroup"] > label:hover {{ border-color: {SIGNAL}; background: #FBFDFE; }}
.stRadio > div[role="radiogroup"] > label:focus-within {{ outline: 2px solid {INK}; outline-offset: 1px; }}

/* Below tablet width five across stops fitting, so the scale stacks instead. */
@media (max-width: 680px) {{
    .stRadio > div[role="radiogroup"] {{ flex-wrap: wrap; }}
    .stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label,
    .stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label div {{
        white-space: normal;
    }}
    .stRadio > div[role="radiogroup"] > label {{ flex: 1 1 46%; }}
}}
.stButton > button {{
    background: {SIGNAL}; color: #FFFFFF; border: 1px solid {SIGNAL}; border-radius: 3px;
    font-family: 'Archivo', sans-serif; font-weight: 600; letter-spacing: 0.01em;
    padding: 0.62rem 1.5rem; transition: background 140ms ease;
}}
.stButton > button:hover {{ background: #12556D; border-color: #12556D; color: #FFFFFF; }}
.stButton > button:focus-visible {{ outline: 2px solid {INK}; outline-offset: 2px; }}
.stDownloadButton > button {{
    background: #FFFFFF; color: {INK}; border: 1px solid {RULE}; border-radius: 3px; font-weight: 600;
}}
.stExpander {{ border: 1px solid {RULE} !important; border-radius: 3px !important; background: #FFFFFF; }}
[data-testid="stExpanderDetails"] {{ font-size: 0.92rem; }}
footer, #MainMenu {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ display: none; }}
/* Streamlit adds an anchor link to headings; these are not linkable sections. */
.stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a, .stMarkdown h4 a {{ display: none; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def masthead(title: str, subtitle: str, eyebrow: str = "") -> None:
    st.markdown(
        f"""<div class="masthead">
              {f'<div class="chan">{html.escape(eyebrow)}</div>' if eyebrow else ''}
              <h1>{html.escape(title)}</h1>
              <p>{subtitle}</p>
            </div>""",
        unsafe_allow_html=True,
    )


def errorbar(channel: str, value: float, error: float, colour: str,
             vmax: float = 100.0, suffix: str = "") -> str:
    """One measured value with its uncertainty drawn as a band and a marker."""
    lo = max(0.0, value - error) / vmax * 100.0
    hi = min(vmax, value + error) / vmax * 100.0
    point = min(max(value / vmax * 100.0, 0.0), 100.0)
    pm = f'<span class="readout-pm">± {error:.0f}</span>' if error else ""
    return f"""<div class="readout">
      <div class="readout-head">
        <span class="chan">{html.escape(channel)}</span>
        <span class="readout-val">{value:.0f}{suffix}{pm}</span>
      </div>
      <div class="track">
        <div class="ci" style="left:{lo:.2f}%;width:{max(hi - lo, 0.6):.2f}%;background:{colour};color:{colour};"></div>
        <div class="pt" style="left:calc({point:.2f}% - 1.5px);background:{colour};"></div>
      </div>
    </div>"""


def panel(title: str, body_html: str, icon: str = "") -> None:
    head = f"{icon} {html.escape(title)}" if icon else html.escape(title)
    st.markdown(f'<div class="panel"><h4>{head}</h4>{body_html}</div>', unsafe_allow_html=True)


def caveat(title: str, body: str, bullets: list[str] | None = None) -> None:
    items = "".join(f"<li>{html.escape(b)}</li>" for b in (bullets or []))
    st.markdown(
        f'<div class="caveat"><b>{html.escape(title)}</b><br>{body}'
        f'{f"<ul>{items}</ul>" if items else ""}</div>',
        unsafe_allow_html=True,
    )


# The traditional Enneagram figure: 9 points evenly spaced on a circle,
# numbered 1-9 clockwise starting from the top, joined by the "hexad"
# (1-4-2-8-5-7-1) and the "triangle" (3-9-6-3). This layout and those two
# connecting figures are the public-domain symbol itself, not tied to any one
# instrument or author — reproducing it here is like drawing a standard
# compass rose, not copying a proprietary diagram.
_HEXAD = (1, 4, 2, 8, 5, 7, 1)
_TRIANGLE = (3, 9, 6, 3)


def _wheel_point(number: int, cx: float, cy: float, r: float) -> tuple[float, float]:
    angle = math.radians(90 - (number - 9) % 9 * 40)
    return cx + r * math.cos(angle), cy - r * math.sin(angle)


_LABEL_FONT_SIZE = 12.5
# Rough advance width for Archivo semibold at this size — no text-measurement
# API is available server-side, so this trades exactness for a deliberately
# generous estimate: an overestimate wastes a little margin, an underestimate
# clips a name, and French type names run long ("Perfectionniste",
# "Individualiste"), so the estimate errs wide on purpose.
_LABEL_CHAR_WIDTH = _LABEL_FONT_SIZE * 0.62


def _label_bbox(x: float, y: float, anchor: str, text: str) -> tuple[float, float, float, float]:
    width = len(text) * _LABEL_CHAR_WIDTH
    if anchor == "start":
        x0, x1 = x, x + width
    elif anchor == "end":
        x0, x1 = x - width, x
    else:
        x0, x1 = x - width / 2, x + width / 2
    # Baseline-relative: most of a cap-height glyph sits above the baseline,
    # a little (descenders, accents) below it.
    y0, y1 = y - _LABEL_FONT_SIZE * 0.8, y + _LABEL_FONT_SIZE * 0.3
    return x0, y0, x1, y1


def enneagram_wheel(entries: list[dict], top_names: set[str]) -> str:
    """An SVG rendering of the classic Enneagram circle, with each of the 9
    points sized and shaded by how often that type won when it was offered —
    a positioning, not just a ranked list. ``entries`` is a list of dicts with
    name / number / domain / colour / win_rate for all 9 types.

    The viewBox is computed from the actual content rather than hardcoded:
    a hardcoded box clipped the name label of the winning type whenever it
    was one of the longer French names ("Questionneur", "Individualiste") —
    an SVG's default overflow is hidden, so anything placed past a fixed
    viewBox edge simply disappears rather than wrapping or shrinking."""
    cx, cy, r_outer = 170.0, 170.0, 128.0
    by_number = {e["number"]: e for e in entries}
    # The circle plus the largest possible marker (radius 27) and its
    # highlight ring (+4) and stroke, with a little slack.
    min_x, min_y = cx - r_outer - 34, cy - r_outer - 34
    max_x, max_y = cx + r_outer + 34, cy + r_outer + 34

    lines = []
    for seq in (_HEXAD, _TRIANGLE):
        pts = [_wheel_point(n, cx, cy, r_outer) for n in seq]
        d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
        lines.append(f'<path d="{d}" fill="none" stroke="{SLATE}" stroke-width="1.6" opacity="0.75"/>')

    # Win rates across 9 types usually cluster in a narrow absolute band (a
    # dominant type might win 40% of its match-ups, the last-place type 10%),
    # so sizing markers off the raw 0-1 scale barely moves the radius. Sizing
    # relative to this person's own spread instead (smallest win rate -> the
    # floor size, largest -> the ceiling) keeps the dots clearly graduated
    # regardless of how compressed or spread out the actual scores are.
    rates = [e["win_rate"] for e in entries]
    rate_min, rate_span = min(rates), max(rates) - min(rates) or 1.0

    markers = []
    for number in range(1, 10):
        e = by_number[number]
        x, y = _wheel_point(number, cx, cy, r_outer)
        rate = e["win_rate"]
        norm = (rate - rate_min) / rate_span
        radius = 9 + norm * 18
        is_top = e["name"] in top_names
        ring = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius + 4:.1f}" fill="none" stroke="{e["colour"]}" stroke-width="2"/>' if is_top else ""
        markers.append(
            f'{ring}'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{e["colour"]}" '
            f'fill-opacity="{0.28 + norm * 0.62:.2f}" stroke="{e["colour"]}" stroke-width="1.2"/>'
            f'<text x="{x:.1f}" y="{y + 3.5:.1f}" text-anchor="middle" '
            f'font-family="IBM Plex Mono, monospace" font-size="11" font-weight="600" '
            f'fill="{"#FFFFFF" if norm > 0.5 else INK}">{number}</text>'
        )
        if is_top:
            label_x = cx + (x - cx) * 1.34
            label_y = cy + (y - cy) * 1.34
            anchor = "middle" if abs(x - cx) < 8 else ("start" if x > cx else "end")
            markers.append(
                f'<text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="{anchor}" '
                f'font-family="Archivo, sans-serif" font-size="{_LABEL_FONT_SIZE}" font-weight="600" '
                f'fill="{e["colour"]}">{html.escape(e["name"])}</text>'
            )
            x0, y0, x1, y1 = _label_bbox(label_x, label_y, anchor, e["name"])
            min_x, min_y = min(min_x, x0), min(min_y, y0)
            max_x, max_y = max(max_x, x1), max(max_y, y1)

    pad = 8
    vb_x, vb_y = min_x - pad, min_y - pad
    vb_w, vb_h = (max_x - min_x) + 2 * pad, (max_y - min_y) + 2 * pad

    return f"""<svg viewBox="{vb_x:.1f} {vb_y:.1f} {vb_w:.1f} {vb_h:.1f}" width="100%" \
style="max-width:400px;display:block;margin:0 auto;">
      <circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" stroke="{RULE}" stroke-width="1.2"/>
      {''.join(lines)}
      {''.join(markers)}
    </svg>"""


def meter(fraction: float) -> None:
    st.markdown(
        f'<div class="meter"><div style="width:{max(0.0, min(1.0, fraction)) * 100:.1f}%"></div></div>',
        unsafe_allow_html=True,
    )
