"""One font across the site: Plus Jakarta Sans (Latin) + Noto Nastaliq Urdu (Urdu).

Rewrites the Google Fonts <link> and every Sora / Noto Sans / JetBrains Mono / Roboto
reference in the pages. Safe to run again.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800'
        '&family=Noto+Nastaliq+Urdu:wght@400;500;700&display=swap">')
JK = '"Plus Jakarta Sans",system-ui,sans-serif'

SUBS = [
    (re.compile(r'<link[^>]*href="https://fonts\.googleapis\.com/css2\?[^"]*"[^>]*>'), LINK),
    (re.compile(r'"Sora",\s*system-ui,\s*sans-serif'), JK),
    (re.compile(r'"Noto Sans",\s*(?:"Segoe UI",\s*)?system-ui,\s*sans-serif'), JK),
    (re.compile(r'"JetBrains Mono",\s*ui-monospace,\s*monospace'), JK),
    (re.compile(r'"Roboto",\s*system-ui,\s*-apple-system,'), '"Plus Jakarta Sans",system-ui,-apple-system,'),
    (re.compile(r'\bRoboto,Arial,sans-serif'), '"Plus Jakarta Sans",system-ui,sans-serif'),
    (re.compile(r'"Sora,sans-serif'), '"Plus Jakarta Sans,sans-serif'),           # SVG font-family attributes
    (re.compile(r'"JetBrains Mono,monospace'), '"Plus Jakarta Sans,sans-serif'),
    (re.compile(r'font-family="Sora[^"]*"'), 'font-family="Plus Jakarta Sans,sans-serif"'),
    (re.compile(r'font-family:\s*Sora\b[^;"}]*'), 'font-family:' + JK),
]

for path in [*ROOT.glob("*.html"), *ROOT.glob("*/index.html"), *ROOT.glob("*.js"), *ROOT.glob("*/*.js"), ROOT / "scripts/build_guides.py"]:
    s = path.read_text(encoding="utf-8")
    t = s
    for rx, rep in SUBS:
        # build_guides.py is a .format() template: keep its braces doubled
        t = rx.sub(rep, t)
    if path.name == "build_guides.py":
        t = t.replace("family=Sora:wght@500;600;700&family=Noto+Sans:wght@400;500;600", "family=Plus+Jakarta+Sans:wght@400;500;600;700;800")
    if t != s:
        path.write_text(t, encoding="utf-8")
        print("updated", path.relative_to(ROOT))
