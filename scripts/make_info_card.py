#!/usr/bin/env python3
"""
Build a neofetch-style info card SVG to sit beside the ASCII portrait.
Styled with the Blue Visual System:
  Midnight #050b14, Deep Navy #091224, Sapphire #1e3a8a, Cyan #38bdf8, Ivory #f0f6fc.
Lines fade/slide in on a short stagger.
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

W, H = 490, 480
PAD = 20
TITLEBAR_H = 30
KEY_X = PAD
VAL_X = PAD + 95
LINE_H = 22

BG = "#050b14"
BG2 = "#091224"
FRAME = "#1e3a8a"
MUTED = "#64748b"
INK = "#f0f6fc"
KEY = "#38bdf8"       # Cyan keys in Blue Visual System
SECTION = "#60a5fa"   # Sky blue section headers
GREEN = "#38bdf8"
ACCENT = "#2563eb"
CYAN = "#06b6d4"

ROWS = [
    ("host",),
    ("kv", "Identity", "Jachin Samuel J"),
    ("kv", "Role", "Software Engineer & AI Developer"),
    ("kv", "Education", "B.Tech CSE @ Karunya Institute"),
    ("kv", "Standing", "CGPA 8.93 / 10.0"),
    ("kv", "Location", "India"),
    ("gap",),
    ("sec", "Stack"),
    ("kv", "Languages", "Python, TypeScript, JavaScript, C++"),
    ("kv", "Frontend", "React, Next.js, Tailwind, Framer"),
    ("kv", "Backend", "FastAPI, Flask, PostgreSQL, SQLite"),
    ("kv", "Applied AI", "Ollama, Local RAG, Vector Search"),
    ("gap",),
    ("sec", "Key Deployments"),
    ("bul", "FoodyBuddy — Live campus ordering & payments"),
    ("bul", "Ace — AI Git Copilot published on PyPI"),
    ("bul", "Nexus — Enterprise local RAG platform"),
    ("bul", "MaternCare — Maternal risk assessment ML app"),
]


def esc(s):
    return html.escape(s)


def rise(inner, i):
    """fade + slight upward slide, staggered by row index; freezes visible."""
    if STATIC:
        return f"<g>{inner}</g>"
    delay = 0.15 + i * 0.05
    return (f'<g opacity="0" transform="translate(0,5)">{inner}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" '
            f'begin="{delay:.2f}s" dur="0.4s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/></g>')


def render():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>'
        f'<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-opacity="0.6"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.4"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">jachin@github: ~$ neofetch</text>')

    y = TITLEBAR_H + 28
    for i, row in enumerate(ROWS):
        kind = row[0]
        if kind == "gap":
            y += LINE_H * 0.4
            continue
        if kind == "host":
            inner = (f'<text x="{KEY_X}" y="{y:.1f}" font-size="13.5" font-weight="700">'
                     f'<tspan fill="{KEY}">jachin</tspan><tspan fill="{MUTED}">@</tspan>'
                     f'<tspan fill="{SECTION}">github</tspan></text>'
                     f'<line x1="{KEY_X+112}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                     f'stroke="{FRAME}" stroke-opacity="0.6"/>')
        elif kind == "sec":
            title = esc(row[1])
            inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="12" font-weight="700">'
                     f'&#8212; {title}</text>'
                     f'<line x1="{KEY_X + len(title)*8 + 20}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                     f'stroke="{FRAME}" stroke-opacity="0.5"/>')
        elif kind == "kv":
            k, v = esc(row[1]), esc(row[2])
            inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="12" font-weight="700">{k}</text>'
                     f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="12">{v}</text>')
        elif kind == "bul":
            v = esc(row[1])
            inner = (f'<circle cx="{KEY_X+3}" cy="{y-4:.1f}" r="2.5" fill="{CYAN}"/>'
                     f'<text x="{KEY_X+14}" y="{y:.1f}" fill="{INK}" font-size="11.5">{v}</text>')
        parts.append(rise(inner, i))
        y += LINE_H

    parts.append("</svg>")
    svg = "".join(parts)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT, len(svg), "bytes")


if __name__ == "__main__":
    render()
