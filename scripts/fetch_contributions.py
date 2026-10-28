"""Scrape the public contribution calendar -> data/contributions.json

No token needed: it reads https://github.com/users/<user>/contributions.
Usage: python scripts/fetch_contributions.py [saved.html]
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from bs4 import BeautifulSoup

from theme import USER

ROOT = Path(__file__).resolve().parent.parent


def get_html(arg):
    if arg:
        return Path(arg).read_text()
    import requests
    r = requests.get(f"https://github.com/users/{USER}/contributions",
                     headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    r.raise_for_status()
    return r.text


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    counts = {}
    for tip in soup.find_all("tool-tip"):
        m = re.match(r"\s*(No|\d[\d,]*) contributions?", tip.get_text())
        if m and tip.get("for"):
            counts[tip["for"]] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "level": int(td.get("data-level", 0)),
            "count": counts.get(td.get("id"), 0),
        })
    days.sort(key=lambda d: d["date"])
    if len(days) < 300:
        raise SystemExit(f"only parsed {len(days)} days; GitHub markup may have changed")
    return days


def stats(days):
    total = sum(d["count"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    # current streak: today may not have activity yet, so start from yesterday if needed
    current = 0
    rev = list(reversed(days))
    if rev and rev[0]["count"] == 0:
        rev = rev[1:]
    for d in rev:
        if d["count"] == 0:
            break
        current += 1
    best = max(days, key=lambda d: d["count"])
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"] > 0),
    }


if __name__ == "__main__":
    days = parse(get_html(sys.argv[1] if len(sys.argv) > 1 else None))
    out = ROOT / "data" / "contributions.json"
    out.write_text(json.dumps({"user": USER, "stats": stats(days), "days": days}, indent=1))
    print(f"wrote {out}: {len(days)} days, {sum(d['count'] for d in days)} contributions")
