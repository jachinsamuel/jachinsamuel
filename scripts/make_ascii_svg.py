#!/usr/bin/env python3
"""
Convert portrait photo (assets/avatar.png) into a self-typing monochrome ASCII art SVG.
Each row is revealed left-to-right with a terminal block cursor, staggered top-to-bottom.
Canvas is sized to match the height of info-card.svg when placed side-by-side in a 860px table.
"""
from PIL import Image, ImageEnhance, ImageOps
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "assets", "avatar.png")
OUT = os.path.join(HERE, "..", "jachin-ascii.svg")

COLS = 74
ROWS = 44
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense)

CANVAS_W = 370
CANVAS_H = 480
PAD = 15
TITLEBAR_H = 30
STATUS_H = 30

ART_W = CANVAS_W - PAD * 2
ART_H = CANVAS_H - TITLEBAR_H - STATUS_H - PAD
CELL_W = ART_W / COLS
CELL_H = ART_H / ROWS

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#22d3ee"

ROW_DUR = 5.0 / ROWS  # entire typing finishes in ~5 seconds
STAGGER = ROW_DUR

STATIC = bool(os.environ.get("STATIC"))


def generate_ascii_grid():
    if not os.path.exists(SRC):
        print(f"Source image not found at {SRC}", file=sys.stderr)
        sys.exit(1)

    im = Image.open(SRC).convert("L")
    im = ImageOps.autocontrast(im, cutoff=2)
    im = ImageEnhance.Contrast(im).enhance(1.35)
    im = ImageEnhance.Sharpness(im).enhance(1.4)
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    px = im.load()

    rows = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = px[x, y] / 255.0
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.3)
            idx = max(0, min(len(RAMP) - 1, idx))
            chars.append(RAMP[idx])
        rows.append("".join(chars))
    return rows


def render(rows_txt):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>'
        f'<linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#abg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*14}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dotcol}"/>')
    parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="11" '
                 f'text-anchor="middle">jachin@github: ~$ ./portrait.sh</text>')

    art_top = TITLEBAR_H + 8
    font_size = CELL_H * 0.95

    for ry, line in enumerate(rows_txt):
        y = art_top + ry * CELL_H + CELL_H * 0.78
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
                f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')

        if STATIC:
            parts.append(text)
            continue

        parts.append(
            f'<clipPath id="cr{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#cr{ry})">{text}</g>')
        parts.append(
            f'<rect y="{row_y+0.5:.1f}" width="{CELL_W:.1f}" height="{CELL_H-1:.1f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )

    status_line_y = CANVAS_H - STATUS_H
    status_y = status_line_y + 19
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="11.5">'
                 f'jachin@github:~$ whoami <tspan fill="{INK}">Jachin Samuel J</tspan></text>')
    cursor_x = PAD + len("jachin@github:~$ whoami Jachin Samuel J ") * 6.9
    parts.append(f'<rect x="{cursor_x:.1f}" y="{status_y-11:.1f}" width="7" height="13" fill="{CURSOR}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                 f'dur="1s" repeatCount="indefinite"/></rect>')

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    rows = generate_ascii_grid()
    svg = render(rows)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes; {CANVAS_W}x{CANVAS_H})")
