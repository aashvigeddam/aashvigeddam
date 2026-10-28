"""data/contributions.json -> assets/contrib-heatmap.svg

Boxes slide in along a diagonal, then the stats line fades in. STATIC=1 writes
a frozen frame.
"""
import json
import os
from datetime import date
from pathlib import Path

from theme import ACCENT, BAR_H, FONT, MUTED, PALETTE, PROMPT_USER, TEXT, window

ROOT = Path(__file__).resolve().parent.parent
STATIC = os.environ.get("STATIC") == "1"

W = 860
X0 = 44
CELL, GAP = 12, 3
STEP = CELL + GAP
Y0 = BAR_H + 40


def build(data):
    days = data["days"]
    s = data["stats"]
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday

    cells, months = [], []
    last_month = None
    max_delay = 0
    for i, d in enumerate(days):
        idx = i + offset
        week, dow = divmod(idx, 7)
        x = X0 + week * STEP
        y = Y0 + dow * STEP
        lvl = max(0, min(4, d["level"]))
        delay = 0.2 + (week + dow) * 0.018
        max_delay = max(max_delay, delay)
        anim = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
        cells.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[lvl]}"{anim}><title>{d["count"]} on {d["date"]}</title></rect>'
        )
        dt = date.fromisoformat(d["date"])
        if dow == 0 and dt.month != last_month and dt.day <= 7:
            months.append(f'<text class="lbl" x="{x}" y="{Y0 - 10}">{dt.strftime("%b")}</text>')
            last_month = dt.month

    labels = "".join(
        f'<text class="lbl" x="{X0 - 8}" y="{Y0 + r * STEP + CELL - 2}" text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    ly = Y0 + 7 * STEP + 22
    legend_x = W - 24 - 5 * STEP - 40
    legend = [f'<text class="lbl" x="{legend_x - 8}" y="{ly + 10}" text-anchor="end">Less</text>']
    for i, c in enumerate(PALETTE):
        legend.append(f'<rect x="{legend_x + i * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    legend.append(f'<text class="lbl" x="{legend_x + 5 * STEP + 4}" y="{ly + 10}">More</text>')

    best = s["best_day"]
    best_txt = (f'{best["count"]} on {date.fromisoformat(best["date"]).strftime("%b %-d")}'
                if best["count"] else "none yet")
    stat_items = [
        ("contributions", f'{s["total"]:,}'),
        ("current streak", f'{s["current_streak"]}d'),
        ("longest streak", f'{s["longest_streak"]}d'),
        ("best day", best_txt),
    ]
    stat_txt = '<tspan fill="#2a4a78">  |  </tspan>'.join(
        f'<tspan fill="{ACCENT}" font-weight="700">{v}</tspan><tspan fill="{MUTED}"> {k}</tspan>'
        for k, v in stat_items
    )
    stats_line = f'<text class="st" x="{X0}" y="{ly + 10}">{stat_txt}</text>'

    style = f"""
text {{ font-family: {FONT}; }}
.lbl {{ font-size: 10px; fill: {MUTED}; }}
.st {{ font-size: 12px; fill: {TEXT}; }}
"""
    if not STATIC:
        style += f"""
.c {{ opacity: 0; transform-box: fill-box; transform-origin: center;
      animation: drop .35s cubic-bezier(.2,.8,.3,1) forwards; }}
@keyframes drop {{ from {{ opacity: 0; transform: translateY(-7px) scale(.6); }} to {{ opacity: 1; transform: none; }} }}
.st {{ opacity: 0; animation: fade .6s ease-out {max_delay + 0.3:.2f}s forwards; }}
@keyframes fade {{ to {{ opacity: 1; }} }}
"""
    H = ly + 34
    body = "\n".join(months) + labels + "\n".join(cells) + "".join(legend) + stats_line
    return window(W, H, f"{PROMPT_USER}@github: ~/contributions", body, style=style)


if __name__ == "__main__":
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    out = ROOT / "assets" / "contrib-heatmap.svg"
    out.write_text(build(data))
    print(f"wrote {out}")
