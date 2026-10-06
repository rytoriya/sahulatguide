#!/usr/bin/env python3
"""Collect raw police station data for Pakistan (run by .github/workflows/police-data.yml).

Writes into data/police/raw/:
  osm-police.json      every OpenStreetMap feature tagged amenity=police in and around Pakistan
                       (name, Urdu name, address and phone tags, coordinates)
  pages/<host>/...     the official police websites' station and directory pages, saved as HTML
  pages-index.tsv      url <tab> saved file <tab> HTTP status

Then scripts/build_police.js / the parsing step turn these into the site's data.
Uses only the Python standard library.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "police", "raw")
UA = "SahulatGuide-data/1.0 (+https://sahulatguide.netlify.app; open data for a public-service guide)"


def get(url, data=None, timeout=90, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410):
                return e.code, b""
            err = e
        except Exception as e:  # network hiccup: retry
            err = e
        time.sleep(5 * (i + 1))
    print("  failed:", url, err, file=sys.stderr)
    return 0, b""


# ---------------------------------------------------------------- OpenStreetMap
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
# A box around Pakistan incl. AJK and Gilgit-Baltistan; points are assigned to districts later.
QUERY = """[out:json][timeout:900];
( nwr["amenity"="police"](23.5,60.5,37.2,78.0);
  nwr["police"](23.5,60.5,37.2,78.0);
  nwr["office"="police"](23.5,60.5,37.2,78.0); );
out center tags;"""


def fetch_osm():
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    for url in OVERPASS:
        print("Overpass:", url)
        status, raw = get(url, data=body, timeout=1000, tries=2)
        if status == 200 and raw.startswith(b"{"):
            j = json.loads(raw)
            with open(os.path.join(OUT, "osm-police.json"), "w", encoding="utf-8") as f:
                json.dump(j, f, ensure_ascii=False)
            print("  elements:", len(j.get("elements", [])))
            return
    print("Overpass: all mirrors failed", file=sys.stderr)


# ---------------------------------------------------------------- official websites
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.links.append(v)


# (seed URLs, regex of links worth following on the same site, page budget)
SITES = [
    (["https://punjabpolice.gov.pk/dpocontacts", "https://www.punjabpolice.gov.pk/CityPOContacts",
      "https://www.punjabpolice.gov.pk/LahoreDirectory", "https://www.punjabpolice.gov.pk/RawalpindiDirectory",
      "https://www.punjabpolice.gov.pk/FaisalabadDirectory", "https://www.punjabpolice.gov.pk/GujranwalaDirectory",
      "https://www.punjabpolice.gov.pk/MultanDirectory", "https://www.punjabpolice.gov.pk/"],
     r"(?i)directory|policestation|police-station|dpocontacts|citypocontacts|contact", 250),
    (["https://sindhpolice.gov.pk/", "https://sindhpolice.gov.pk/city/police-station"],
     r"(?i)police-station|/districts?|/range|contact", 250),
    (["https://karachipolice.gov.pk/services/police-stations-in-karachi/"],
     r"(?i)police-station|district|zone", 80),
    (["https://www.cplc.org.pk/list-of-police-station/"], r"(?i)police-station", 20),
    (["https://www.kppolice.gov.pk/phone-directory.php?tid=4", "https://www.kppolice.gov.pk/phone-directory.php",
      "https://www.kppolice.gov.pk/"], r"(?i)phone-directory|police-station|district", 200),
    (["https://balochistanpolice.gov.pk/dpo_contactdetails", "https://balochistanpolice.gov.pk/"],
     r"(?i)police[-_ ]?station|dpo|district|contact|directory", 120),
    (["https://islamabadpolice.gov.pk/contact.php", "https://islamabadpolice.gov.pk/"],
     r"(?i)police[-_ ]?station|contact|zone|directory", 80),
    (["https://police.ajk.gov.pk/", "https://ajkpolice.gov.pk/"],
     r"(?i)police[-_ ]?station|district|contact|directory", 80),
    (["https://gbp.gov.pk/?p=80", "https://gbp.gov.pk/"], r"(?i)\?p=\d+|police[-_ ]?station|district|contact", 80),
]
SKIP = re.compile(r"(?i)\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?|mp4|svg)(\?|$)|logout|login|wp-admin|#")


STRIP = [re.compile(r"(?is)<(script|style|svg|noscript|iframe)\b.*?</\1>"), re.compile(r"(?s)<!--.*?-->")]


def clean(raw):
    """Keep the page's text, tables and links; drop scripts, styles and images to keep files small."""
    t = raw.decode("utf-8", "replace")
    for rx in STRIP:
        t = rx.sub(" ", t)
    t = re.sub(r"(?i)<(img|link|meta)\b[^>]*>", "", t)
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.encode("utf-8")


def save_page(url, raw, status, index):
    u = urllib.parse.urlparse(url)
    name = (u.path.strip("/") or "index").replace("/", "__")
    if u.query:
        name += "__" + re.sub(r"[^A-Za-z0-9=_-]+", "_", u.query)
    name = name[:150] + ".html"
    d = os.path.join(OUT, "pages", u.netloc.replace("www.", ""))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "wb") as f:
        f.write(clean(raw))
    index.write(f"{url}\t{os.path.relpath(os.path.join(d, name), OUT)}\t{status}\n")


def crawl(seeds, follow, budget, index):
    follow = re.compile(follow)
    host = urllib.parse.urlparse(seeds[0]).netloc.replace("www.", "")
    queue, seen, n = list(seeds), set(), 0
    while queue and n < budget:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        status, raw = get(url, timeout=60, tries=2)
        n += 1
        if status != 200 or not raw:
            index.write(f"{url}\t-\t{status}\n")
            continue
        save_page(url, raw, status, index)
        p = Links()
        try:
            p.feed(raw.decode("utf-8", "replace"))
        except Exception:
            pass
        for href in p.links:
            nxt = urllib.parse.urljoin(url, href.strip())
            nu = urllib.parse.urlparse(nxt)
            if nu.scheme not in ("http", "https") or nu.netloc.replace("www.", "") != host:
                continue
            nxt = nxt.split("#")[0]
            if nxt not in seen and not SKIP.search(nxt) and follow.search(nxt):
                queue.append(nxt)
        time.sleep(0.7)  # be polite
    print(f"  {host}: {n} pages fetched")


def main():
    os.makedirs(OUT, exist_ok=True)
    fetch_osm()
    with open(os.path.join(OUT, "pages-index.tsv"), "w", encoding="utf-8") as index:
        for seeds, follow, budget in SITES:
            print("Crawl:", seeds[0])
            crawl(seeds, follow, budget, index)


if __name__ == "__main__":
    main()
