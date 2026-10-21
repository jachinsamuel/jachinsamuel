#!/usr/bin/env python3
"""
Convert prepped portrait photo into a clean, monochrome self-typing ASCII art SVG
styled with the Blue Visual System:
  - High-contrast ivory text (#f0f6fc) on deep midnight canvas (#050b14 -> #091224)
  - Sapphire frame border (#1e3a8a) with cyan block cursor (#38bdf8)
  - Subject cleanly isolated (background washes out to pure blank spaces)
  - Each row reveals left-to-right with a cyan block cursor riding the wipe edge
  - Staggered top to bottom: prints once over ~5s and freezes cleanly in terminal style
"""
from PIL import Image, ImageEnhance
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "jachin-ascii.svg")

CANVAS_W = 370
CANVAS_H = 480
PAD = 14
TITLEBAR_H = 30
STATUS_H = 30

ART_W = CANVAS_W - PAD * 2
COLS = 114
CELL_W = ART_W / COLS
CELL_H = CELL_W * 1.8
ROWS = round((CANVAS_H - TITLEBAR_H - STATUS_H - PAD) / CELL_H)
ART_H = ROWS * CELL_H

RAMP = " .`:-=+*cs#%@"
CONTRAST = 1.05
BRIGHTNESS = 1.0
GAMMA = 1.05
WHITE_FLOOR = 0.88

BG = "#050b14"
BG2 = "#091224"
FRAME = "#1e3a8a"
TITLE_TEXT = "#64748b"
INK = "#f0f6fc"
CURSOR = "#38bdf8"

TOTAL_TYPE_DUR = 5.0
ROW_DUR = TOTAL_TYPE_DUR / ROWS
STAGGER = ROW_DUR


def convert_image():
    if not os.path.exists(SRC):
        print(f"Error: {SRC} does not exist", file=sys.stderr)
        sys.exit(1)

    im = Image.open(SRC).convert("L")
    im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    px = im.load()

    rows = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = pow(px[x, y] / 255.0, GAMMA)
            if lum >= WHITE_FLOOR:
                chars.append(" ")
            else:
                idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
                idx = max(0, min(len(RAMP) - 1, idx))
                chars.append(RAMP[idx])
        rows.append("".join(chars))
    return rows


def render(rows):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>'
        f'<linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#abg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-opacity="0.6"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.4"/>',
    ]

    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*14}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dotcol}"/>')
    parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="11" '
                 f'text-anchor="middle">jachin@github: ~$ ./portrait.sh</text>')

    art_top = TITLEBAR_H + 8
    font_size = CELL_H * 0.90

    for ry, line in enumerate(rows):
        y = art_top + ry * CELL_H + CELL_H * 0.74
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER

        safe = html.escape(line)
        text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
                f'font-size="{font_size:.1f}" textLength="{ART_W:.1f}" lengthAdjust="spacing">{safe}</text>')

        parts.append(
            f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.3f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')

        parts.append(
            f'<rect y="{row_y+0.5:.1f}" width="{CELL_W:.2f}" height="{CELL_H-1:.2f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/>'
            f'</rect>'
        )

    status_line_y = CANVAS_H - STATUS_H
    status_y = status_line_y + 19
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}" stroke-opacity="0.4"/>')
    parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="11.5">'
                 f'jachin@github:~$ whoami <tspan fill="{INK}">Jachin Samuel J</tspan></text>')
    cursor_x = PAD + len("jachin@github:~$ whoami Jachin Samuel J ") * 6.9
    parts.append(f'<rect x="{cursor_x:.1f}" y="{status_y-11:.1f}" width="7" height="13" fill="{CURSOR}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                 f'dur="1s" repeatCount="indefinite"/></rect>')

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    rows = convert_image()
    svg = render(rows)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Successfully wrote {OUT} ({len(svg)} bytes; {CANVAS_W}x{CANVAS_H})")
