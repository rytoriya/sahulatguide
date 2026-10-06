"""Build the Markdown guides in content/ into standalone HTML pages.

The site header and footer are filled in afterwards by scripts/build_chrome.js.

Usage: pip install markdown && python3 scripts/build_guides.py && node scripts/build_chrome.js
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;500;700&display=swap">
<style>
:root{{--bg:#f5f7f6;--surface:#fff;--ink:#17232e;--muted:#5a6872;--line:#dde3e1;--accent:#0d6b52;--accent-soft:#e2f1ec;--r:10px;
  --f-display:"Plus Jakarta Sans",system-ui,sans-serif;--f-body:"Plus Jakarta Sans",system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#10171c;--surface:#172129;--ink:#e6ecea;--muted:#9aa8ad;--line:#26343c;--accent:#4fc39d;--accent-soft:#163a31;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#10171c;--surface:#172129;--ink:#e6ecea;--muted:#9aa8ad;--line:#26343c;--accent:#4fc39d;--accent-soft:#163a31;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font:15px/1.65 var(--f-body);margin:0}}
a{{color:var(--accent)}}
.wrap{{max-width:1080px;margin:0 auto;padding-inline:16px}}
header{{position:sticky;top:0;z-index:10;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--surface) 88%,transparent);backdrop-filter:saturate(1.6) blur(12px);-webkit-backdrop-filter:saturate(1.6) blur(12px)}}
header .wrap{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-block:12px}}
.brand{{display:flex;align-items:center;gap:10px;font:700 18px var(--f-display);color:var(--ink);text-decoration:none;letter-spacing:-.01em}}
.brand svg{{width:34px;height:34px}}
.brand > span{{color:var(--ink)}}
.brand > span > span{{color:var(--accent)}}
.back{{white-space:nowrap;font-weight:600;font-size:14px;text-decoration:none;padding:8px 14px;border:1px solid var(--line);border-radius:999px;background:var(--surface);transition:border-color .2s}}
.back:hover{{border-color:var(--accent)}}
.hdr-r{{display:flex;align-items:center;gap:8px}}
@media (max-width:480px){{.back{{padding:8px 10px;font-size:13px}}}}
body{{-webkit-font-smoothing:antialiased}}
main{{padding-block:24px 60px}}
h1,h2,h3{{font-family:var(--f-display);line-height:1.25;text-wrap:balance}}
h1{{font-size:clamp(28px,4.4vw,44px);letter-spacing:-.03em;line-height:1.08;margin:16px 0 20px}}
h2{{font-size:clamp(20px,2.4vw,25px);letter-spacing:-.02em;margin:56px 0 14px;scroll-margin-top:80px}}
h3{{scroll-margin-top:80px}}
h3{{font-size:17px;margin:26px 0 10px}}
blockquote{{margin:0 0 20px;padding:16px 20px;background:var(--accent-soft);border-left:4px solid var(--accent);border-radius:0 14px 14px 0;max-width:80ch}}
blockquote p{{margin:4px 0}}
.tbl{{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:16px;margin:14px 0;box-shadow:0 1px 2px rgba(16,32,28,.05),0 1px 3px rgba(16,32,28,.06)}}
tbody tr{{transition:background-color .15s}}
tbody tr:hover{{background:color-mix(in srgb,var(--accent-soft) 45%,transparent)}}
main > ol, main > ul{{max-width:75ch}}
h2 + ol{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px 20px 16px 40px;display:grid;gap:4px;max-width:520px}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font:600 12px var(--f-body);text-transform:uppercase;letter-spacing:.05em;color:var(--muted);background:var(--bg);white-space:nowrap}}
tr:last-child td{{border-bottom:0}}
td{{font-variant-numeric:tabular-nums}}
code{{font-size:.95em}}
footer{{border-top:1px solid var(--line);color:var(--muted);font-size:13px;padding-block:20px 40px}}
</style>
<link rel="stylesheet" href="../site.css">
</head>
<body>
<!-- sg:header -->
<!-- /sg:header -->
<main class="wrap">
{body}
</main>
<footer><div class="wrap">Independent guide, not affiliated with any government body or company. Confirm every price and time with the official source before you travel or pay.</div></footer>
<!-- sg:footer -->
<!-- /sg:footer -->
<script src="../search.js" defer></script>
<script src="../account.js" defer></script>
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
