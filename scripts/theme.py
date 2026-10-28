"""Shared blue palette and terminal-window chrome for every SVG.

Each SVG carries its own dark window background, so the art reads the same
whether a visitor uses GitHub in light or dark mode.
"""

USER = "aashvigeddam"
PROMPT_USER = "aashvi"

BG = "#0a1628"          # window body (deep navy)
BAR = "#0f2140"         # title bar
BORDER = "#1e3a64"      # window outline
DOTS = ("#1f6feb", "#388bfd", "#79c0ff")
TEXT = "#c9d8ec"        # body text
MUTED = "#6b85a8"       # secondary text
ACCENT = "#58a6ff"      # keys, highlights
ASCII_FILL = "#a8cfff"  # (unused; portrait shades live in make_portrait.py)

# heatmap levels 0..4 (GitHub uses five levels)
PALETTE = ["#13233d", "#0d3a7a", "#1758c2", "#2f81f7", "#9ccbff"]

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

BAR_H = 28


def window(width, height, title, body, extra_defs="", style=""):
    """Wrap SVG body markup in a terminal window."""
    dots = "".join(
        f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{c}"/>'
        for i, c in enumerate(DOTS)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<defs>{extra_defs}</defs>
<style>{style}</style>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<path d="M0.5 {BAR_H} V10.5 a10 10 0 0 1 10 -10 H{width - 10.5} a10 10 0 0 1 10 10 V{BAR_H} Z" fill="{BAR}"/>
<line x1="0.5" y1="{BAR_H}" x2="{width - 0.5}" y2="{BAR_H}" stroke="{BORDER}"/>
{dots}
<text x="{width / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" style="font-family:{FONT};font-size:11px;fill:{MUTED}">{title}</text>
{body}
</svg>
"""
