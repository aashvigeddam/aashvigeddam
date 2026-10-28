"""Neofetch-style info card -> assets/info-card.svg

Edit ROWS to change what the card says. STATIC=1 writes a frozen frame.
"""
import os
import textwrap
from html import escape
from pathlib import Path

from theme import ACCENT, DOTS, FONT, MUTED, PALETTE, PROMPT_USER, TEXT, BAR_H, window

ROWS = [
    ("Name", "Aashvi Geddam"),
    ("Now", "Cognitive Science, Class of 2030"),
    ("Founder", "Magnus United"),
    ("Interests", "human-AI interaction, UX research, PM"),
    ("Site", "aashvigeddam.com"),
]

W, H = 490, 430
X0 = 24
FS = 12
LH = 22
CHAR_W = FS * 0.6
KEY_COLS = 11
STATIC = os.environ.get("STATIC") == "1"


def build():
    lines = []  # (svg text element)
    val_x = X0 + KEY_COLS * CHAR_W
    wrap_cols = int((W - val_x - 20) / CHAR_W)
    n_rows = sum(len(textwrap.wrap(v, wrap_cols) or [""]) for _, v in ROWS)
    content_h = 2 * LH + 4 + n_rows * LH + 14 + LH + 6 + LH
    # centre the block vertically in the window body
    y = BAR_H + max(38, (H - BAR_H - content_h) / 2 + 12)

    header = f"{PROMPT_USER}@github"
    lines.append(
        f'<text x="{X0}" y="{y}"><tspan fill="{ACCENT}" font-weight="700">{PROMPT_USER}</tspan>'
        f'<tspan fill="{TEXT}">@</tspan><tspan fill="{ACCENT}" font-weight="700">github</tspan></text>'
    )
    y += LH
    lines.append(f'<text x="{X0}" y="{y}" fill="{MUTED}">{"-" * len(header)}</text>')
    y += LH + 4

    for key, val in ROWS:
        chunks = textwrap.wrap(val, wrap_cols) or [""]
        for i, chunk in enumerate(chunks):
            key_span = (
                f'<tspan fill="{ACCENT}" font-weight="700">{escape(key)}</tspan>'
                f'<tspan fill="{MUTED}">:</tspan>'
                if i == 0 else ""
            )
            lines.append(
                f'<text x="{X0}" y="{y}">{key_span}'
                f'<tspan x="{val_x:.1f}" fill="{TEXT}">{escape(chunk)}</tspan></text>'
            )
            y += LH
    y += 14

    # neofetch colour blocks in the blue palette
    swatches = list(PALETTE) + list(DOTS)
    blocks = "".join(
        f'<rect x="{X0 + i * 30}" y="{y - 14}" width="26" height="16" rx="3" fill="{c}"/>'
        for i, c in enumerate(swatches)
    )
    lines.append(f"<g>{blocks}</g>")
    y += LH + 6

    # blinking prompt at the end
    lines.append(
        f'<text x="{X0}" y="{y}"><tspan fill="{ACCENT}">{PROMPT_USER}@github</tspan>'
        f'<tspan fill="{MUTED}"> ~ $ </tspan></text>'
    )
    cursor_x = X0 + (len(PROMPT_USER) + len("@github ~ $ ")) * CHAR_W
    lines.append(f'<rect class="cur" x="{cursor_x:.1f}" y="{y - 12}" width="8" height="15" fill="{ACCENT}"/>')

    n = len(lines)
    body = []
    for i, el in enumerate(lines):
        if el.startswith('<rect class="cur"'):
            body.append(el)
            continue
        delay = 0.25 + i * 0.12
        anim = "" if STATIC else f' style="animation-delay:{delay:.2f}s"'
        body.append(f'<g class="ln"{anim}>{el}</g>')

    cursor_start = 0.25 + n * 0.12
    style = f"""
text {{ font-family: {FONT}; font-size: {FS}px; white-space: pre; }}
"""
    if not STATIC:
        style += f"""
.ln {{ opacity: 0; animation: in .45s ease-out forwards; }}
@keyframes in {{ from {{ opacity: 0; transform: translateX(-8px); }} to {{ opacity: 1; transform: none; }} }}
.cur {{ opacity: 0; animation: blink 1.1s step-end {cursor_start:.2f}s infinite; }}
@keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
"""
    return window(W, H, f"{PROMPT_USER}@github: ~", "\n".join(body), style=style)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "info-card.svg"
    out.write_text(build())
    print(f"wrote {out}")
