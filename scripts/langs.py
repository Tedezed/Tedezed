#!/usr/bin/env python3
"""Generate img/langs.svg with the most used languages across all owned repos (private included).

Run locally: GH_TOKEN=$(gh auth token) python3 scripts/langs.py
"""
import json
import os
import urllib.request
from collections import Counter
from html import escape

TOKEN = os.environ["GH_TOKEN"]
OUT = os.path.join(os.path.dirname(__file__), "..", "img", "langs.svg")
TOP = 5
# Dark outline painted under the glyphs so light text stays readable on light and dark themes.
OUTLINE = 'stroke="#6e7681" stroke-opacity="0.4" stroke-width="3" stroke-linejoin="round" paint-order="stroke"'

# Official GitHub linguist colors for the usual suspects; anything else is grey.
COLORS = {
    "Python": "#3572A5", "Shell": "#89e051", "GDScript": "#355570", "C++": "#f34b7d",
    "C#": "#178600", "C": "#555555", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "HTML": "#e34c26", "CSS": "#663399", "Dockerfile": "#384d54", "HCL": "#844FBA",
    "Go": "#00ADD8", "Java": "#b07219", "PHP": "#4F5D95", "Makefile": "#427819",
    "Jinja": "#a52a22", "Smarty": "#f0c040", "Mustache": "#724b3b", "Lua": "#000080",
    "OpenSCAD": "#e5cd45", "ShaderLab": "#222c37", "GLSL": "#5686a5", "Ruby": "#701516",
}


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def repos():
    page = 1
    while batch := get(f"https://api.github.com/user/repos?affiliation=owner&per_page=100&page={page}"):
        yield from (r for r in batch if not r["fork"] and not r["archived"])
        page += 1


def render(totals):
    total = sum(totals.values())
    top = totals.most_common(TOP)
    rest = total - sum(v for _, v in top)
    if rest:
        top.append(("Other", rest))
    items = [(name, v * 100 / total) for name, v in top]
    assert abs(sum(p for _, p in items) - 100) < 0.01

    w, rows = 340, (len(items) + 1) // 2
    h = 85 + rows * 24
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
             f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="none" stroke="#8b949e" stroke-opacity="0.4"/>',
             f'<text x="20" y="32" fill="#e6edf3" {OUTLINE} font-family="Segoe UI,Ubuntu,sans-serif" '
             'font-size="16" font-weight="600">Most Used Languages</text>']
    x = 20.0
    for name, pct in items:
        bw = (w - 40) * pct / 100
        parts.append(f'<rect x="{x:.2f}" y="48" width="{bw:.2f}" height="8" fill="{COLORS.get(name, "#8b949e")}"/>')
        x += bw
    font = f'{OUTLINE} font-family="Segoe UI,Ubuntu,sans-serif" font-size="12"'
    for i, (name, pct) in enumerate(items):
        cx, cy = 20 + (i % 2) * 160, 80 + (i // 2) * 24
        parts.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLORS.get(name, "#8b949e")}"/>'
                     f'<text x="{cx + 16}" y="{cy}" fill="#c9d1d9" {font}>{escape(name)}</text>'
                     f'<text x="{cx + 140}" y="{cy}" fill="#8b949e" text-anchor="end" {font}>{pct:.1f}%</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    totals = Counter()
    for repo in repos():
        totals.update(get(repo["languages_url"]))
    with open(OUT, "w") as f:
        f.write(render(totals))
