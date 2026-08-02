#!/usr/bin/env python3
"""
Generate an animated GitHub contribution heatmap SVG (squares light up cell by cell).
Usage: python scripts/generate_streak_svg.py [username] [contrib-heatmap.svg]
"""
import sys
import json
import os
import datetime
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "Premkumar1845"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")


def get_data(user):
    url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-bot/1.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"API failed ({e}); falling back to data/contributions.json...", file=sys.stderr)
        local_path = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    ldata = json.load(f)
                contribs = []
                for d in ldata.get("days", []):
                    cnt = d.get("count", 0)
                    lvl = 0
                    if cnt > 8: lvl = 4
                    elif cnt > 5: lvl = 3
                    elif cnt > 2: lvl = 2
                    elif cnt > 0: lvl = 1
                    contribs.append({"date": d["date"], "count": cnt, "level": lvl})
                return {"contributions": contribs, "total": {"lastYear": ldata.get("total_contributions", len(contribs))}}
            except Exception as ex:
                print(f"Local file fallback error: {ex}", file=sys.stderr)
        
        # Emergency dummy data if net/file not ready
        today = datetime.date.today()
        dummy_contribs = []
        for i in range(365):
            dt = (today - datetime.timedelta(days=364 - i)).isoformat()
            dummy_contribs.append({"date": dt, "count": 1 if i % 3 == 0 else 0, "level": 1 if i % 3 == 0 else 0})
        return {"contributions": dummy_contribs, "total": {"lastYear": 120}}


data = get_data(USER)
contribs = data.get("contributions", [])
total = data.get("total", {}).get("lastYear", len(contribs))

CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 28
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
GRAY = "#7d8590"
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

n = len(contribs)
NW = (n + 6) // 7
W = LEFT + NW * (CELL + GAP) + 20
H = TOP + 7 * (CELL + GAP) + 36

REVEAL, DUR = 3.6, 0.55
maxorder = max(1.0, (NW - 1) + 6 * 0.55)

rects, labels = [], []
if contribs:
    sd = datetime.date.fromisoformat(contribs[0]["date"])
    last_m = None
    for wk in range(NW):
        d = sd + datetime.timedelta(days=wk * 7)
        if d.month != last_m:
            last_m = d.month
            labels.append(f'<text class="lbl" x="{LEFT+wk*(CELL+GAP)}" y="{TOP-8}">{MONTHS[d.month-1]}</text>')

for name, r in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
    labels.append(f'<text class="lbl" x="4" y="{TOP+r*(CELL+GAP)+CELL-2}">{name}</text>')

for i, c in enumerate(contribs):
    wk, row, lvl = i // 7, i % 7, c.get("level", 0)
    x = LEFT + wk * (CELL + GAP)
    y = TOP + row * (CELL + GAP)
    delay = round((wk + row * 0.55) / maxorder * REVEAL, 3)
    cls = "c g" if lvl >= 1 else "c e"
    rects.append(
        f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
        f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s"/>'
    )

TITLEBAR_H = 26
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
<defs>
  <linearGradient id="cbg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{BG2}"/>
    <stop offset="1" stop-color="{BG}"/>
  </linearGradient>
</defs>
<style>
  text.lbl {{ fill:{GRAY}; font-size:11px; font-weight:500; }}
  text.total {{ fill:#e6edf3; font-size:13px; font-weight:600; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.15}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" rx="10" fill="url(#cbg)"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="none" stroke="{FRAME}" stroke-width="1"/>
{''.join(labels)}
{''.join(rects)}
<text class="total" x="{LEFT}" y="{H-12}">{total:,} contributions in the last year</text>
</svg>'''

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Wrote {OUT}: {n} days, {total:,} contributions ({len(svg)//1024} KB)")
