"""Photo -> monochrome ASCII portrait -> assets/portrait.svg

Usage:
  python scripts/make_portrait.py [path/to/photo.jpg]

With no argument it uses the first image in photo/, and if that folder is
empty it downloads your GitHub avatar. Background removal uses rembg when it
is installed (the GitHub Action installs it); otherwise it is skipped.
STATIC=1 writes a frozen frame.
"""
import io
import os
import sys
from html import escape
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from theme import ACCENT, BAR_H, FONT, PROMPT_USER, USER, window

ROOT = Path(__file__).resolve().parent.parent
RAMP = " .:-=+*#%@"   # sparse -> dense, evenly stepped at small sizes
SHADES = ["#1d3657", "#2c5288", "#4677bd", "#6f9ee6", "#a3c8ff", "#d4e6ff", "#ffffff"]  # dim -> bright
# Glyphs are light on a dark window, so bright skin gets dense glyphs
# and dark hair gets sparse ones, like a photo printed in light.

W, H = 370, 430
PAD_X, PAD_TOP, PAD_BOTTOM = 12, 14, 12
FS = 6.2                  # font size
CHAR_W = FS * 0.6
LINE_H = 7.4
COLS = int((W - 2 * PAD_X) / CHAR_W)
ROWS = int((H - BAR_H - PAD_TOP - PAD_BOTTOM) / LINE_H)
GAMMA = 0.85              # <1 lifts midtones, >1 darkens them
STATIC = os.environ.get("STATIC") == "1"


def load_source(arg):
    if arg:
        return Image.open(arg)
    photos = sorted(p for p in (ROOT / "photo").glob("*")
                    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    if photos:
        print(f"using {photos[0]}")
        return Image.open(photos[0])
    import requests
    url = f"https://github.com/{USER}.png?size=600"
    print(f"no photo found, downloading {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def prep(img):
    """Cut out the subject and boost local contrast.

    Brightness comes from the original photo, not a white composite, so the
    cutout's soft edge doesn't draw a bright outline around the head.
    """
    img = img.convert("RGBA")
    rgb = img.convert("RGB")
    try:
        from rembg import new_session, remove
        # u2net_human_seg is ~170 MB; rembg's newer default model is ~1 GB
        alpha = np.array(remove(img, session=new_session("u2net_human_seg")))[:, :, 3]
        print("background removed")
    except ImportError:
        print("rembg not installed, keeping background")
        alpha = np.full(img.size[::-1], 255, np.uint8)

    mask = alpha > 128
    mask = cv2.erode(mask.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    # keep only the largest blob (the person), dropping stray background bits
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    if n > 2:
        mask = labels == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    ys, xs = np.where(mask)
    gray = np.array(rgb.convert("L"))
    if len(xs):  # crop to the subject
        gray = gray[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        mask = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    return clahe.apply(gray), mask


def fit(img, fill):
    """Pad an image so it fills the COLS x ROWS grid at the right proportions."""
    target_ratio = (COLS * CHAR_W) / (ROWS * LINE_H)
    h, w = img.shape
    if w / h < target_ratio:
        new_w = int(h * target_ratio)
        pad = (new_w - w) // 2
        img = cv2.copyMakeBorder(img, 0, 0, pad, new_w - w - pad, cv2.BORDER_CONSTANT, value=fill)
    else:
        new_h = int(w / target_ratio)
        img = cv2.copyMakeBorder(img, new_h - h, 0, 0, 0, cv2.BORDER_CONSTANT, value=fill)
    return cv2.resize(img, (COLS, ROWS), interpolation=cv2.INTER_AREA)


def to_ascii(gray, mask):
    g = fit(gray, 0).astype(float)
    m = fit(mask.astype(np.uint8) * 255, 0) > 127
    if m.any():  # stretch contrast across the subject only
        lo, hi = np.percentile(g[m], [1, 99.5])
        g = (g - lo) / max(hi - lo, 1)
    g = np.clip(g, 0, 1) ** GAMMA
    n = len(RAMP) - 1
    rows = []
    for r in range(ROWS):
        cells = []
        for c in range(COLS):
            if not m[r, c]:
                cells.append((" ", 0))
            else:
                v = g[r, c]
                cells.append((RAMP[max(1, int(v * n + 0.5))], min(len(SHADES) - 1, int(v * len(SHADES)))))
        rows.append(cells)
    return rows


def spans(cells):
    """Group runs of the same shade into tspans."""
    out, run, shade = [], "", None
    for ch, lv in cells:
        if ch == " ":
            lv = shade if shade is not None else lv
        if shade is not None and lv != shade:
            out.append(f'<tspan fill="{SHADES[shade]}">{escape(run)}</tspan>')
            run = ""
        shade = lv
        run += ch
    if run:
        out.append(f'<tspan fill="{SHADES[shade]}">{escape(run)}</tspan>')
    return "".join(out)


def build(rows):
    x0 = PAD_X
    y0 = BAR_H + PAD_TOP + FS
    row_w = COLS * CHAR_W
    defs, body = [], []
    for i, cells in enumerate(rows):
        y = y0 + i * LINE_H
        line = "".join(ch for ch, _ in cells)
        text = (f'<text x="{x0}" y="{y:.1f}" textLength="{row_w:.1f}" '
                f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{spans(cells)}</text>')
        if STATIC or not line.strip():
            body.append(text)
            continue
        begin = 0.3 + i * 0.06
        dur = 0.32
        defs.append(
            f'<clipPath id="r{i}"><rect x="{x0}" y="{y - FS - 1:.1f}" width="0" height="{LINE_H + 1}">'
            f'<animate attributeName="width" from="0" to="{row_w:.1f}" begin="{begin:.2f}s" '
            f'dur="{dur}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(f'<g clip-path="url(#r{i})">{text}</g>')
        body.append(
            f'<rect x="{x0}" y="{y - FS:.1f}" width="{CHAR_W:.1f}" height="{FS + 1}" fill="{ACCENT}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{x0}" to="{x0 + row_w:.1f}" begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + dur:.2f}s"/></rect>'
        )
    style = f"text {{ font-family: {FONT}; font-size: {FS}px; font-weight: 700; }}"
    return window(W, H, f"{PROMPT_USER}@github: ~/portrait", "\n".join(body),
                  extra_defs="".join(defs), style=style)


if __name__ == "__main__":
    src = load_source(sys.argv[1] if len(sys.argv) > 1 else None)
    gray, mask = prep(src)
    rows = to_ascii(gray, mask)
    out = ROOT / "assets" / "portrait.svg"
    out.write_text(build(rows))
    print(f"wrote {out} ({COLS}x{ROWS})")
