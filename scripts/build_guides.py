"""Build the Markdown guides in content/ into standalone HTML pages.

Usage: pip install markdown && python3 scripts/build_guides.py
"""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent

GUIDES = {
    "trains": ("Pakistan Train Finder", "Pakistan Railways timetables and estimated fares by class: cheapest and fastest trains on every major route."),
    "parcels": ("Pakistan Parcel Guide", "Compare TCS, Leopards, M&P, Pakistan Post, bus cargo and international couriers: prices, delivery times and packing tips."),
}


def slugify(value, separator="-"):
    # GitHub-style anchors, so the in-page contents links keep working.
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return value.replace(" ", separator)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Sahulat Guide</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Noto+Sans:wght@400;500;600&display=swap">
<style>
:root{{--bg:#f5f7f6;--surface:#fff;--ink:#17232e;--muted:#5a6872;--line:#dde3e1;--accent:#0d6b52;--accent-soft:#e2f1ec;--r:10px;
  --f-display:"Sora",system-ui,sans-serif;--f-body:"Noto Sans",system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#10171c;--surface:#172129;--ink:#e6ecea;--muted:#9aa8ad;--line:#26343c;--accent:#4fc39d;--accent-soft:#163a31;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#10171c;--surface:#172129;--ink:#e6ecea;--muted:#9aa8ad;--line:#26343c;--accent:#4fc39d;--accent-soft:#163a31;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font:15px/1.65 var(--f-body);margin:0}}
a{{color:var(--accent)}}
.wrap{{max-width:1080px;margin:0 auto;padding-inline:16px}}
header{{border-bottom:1px solid var(--line);background:var(--surface)}}
header .wrap{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-block:12px}}
.brand{{font:700 18px var(--f-display);color:var(--ink);text-decoration:none}}
.brand span{{color:var(--accent)}}
.back{{font-weight:600;font-size:14px;text-decoration:none}}
main{{padding-block:24px 60px}}
h1,h2,h3{{font-family:var(--f-display);line-height:1.25;text-wrap:balance}}
h1{{font-size:clamp(24px,4vw,34px);margin:8px 0 12px}}
h2{{font-size:22px;margin:40px 0 12px;padding-top:12px;border-top:1px solid var(--line)}}
h3{{font-size:17px;margin:26px 0 10px}}
blockquote{{margin:0 0 20px;padding:12px 16px;background:var(--accent-soft);border-left:4px solid var(--accent);border-radius:0 var(--r) var(--r) 0}}
blockquote p{{margin:4px 0}}
.tbl{{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--r);margin:12px 0}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font-family:var(--f-display);font-weight:600;background:var(--accent-soft);white-space:nowrap}}
tr:last-child td{{border-bottom:0}}
td{{font-variant-numeric:tabular-nums}}
code{{font-size:.95em}}
footer{{border-top:1px solid var(--line);color:var(--muted);font-size:13px;padding-block:20px 40px}}
</style>
</head>
<body>
<header><div class="wrap"><a class="brand" href="../">Sahulat <span>Guide</span></a><a class="back" href="../">&larr; All services</a></div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">Independent guide, not affiliated with any government body or company. Confirm every price and time with the official source before you travel or pay.</div></footer>
</body>
</html>
"""


def build(name, title, desc):
    md = (ROOT / "content" / f"{name}.md").read_text(encoding="utf-8")
    body = markdown.markdown(
        md,
        extensions=["tables", "toc"],
        extension_configs={"toc": {"slugify": slugify}},
    )
    body = body.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    out = ROOT / name / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(TEMPLATE.format(title=html.escape(title), desc=html.escape(desc), body=body), encoding="utf-8")
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    for name, (title, desc) in GUIDES.items():
        build(name, title, desc)
