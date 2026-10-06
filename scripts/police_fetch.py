#!/usr/bin/env python3
"""Collect raw police station data for Pakistan (run by .github/workflows/police-data.yml).

Usage: police_fetch.py [crawl|targets|geocode]   (default: crawl)

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




# ================================================================ step 2: targeted sources
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def get_raw(url, timeout=120, tries=3, ua=BROWSER_UA):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*", "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404, 410):
                return e.code, b""
        except Exception as e:
            print("  retry", url, e, file=sys.stderr)
        time.sleep(6 * (i + 1))
    return 0, b""


def save_raw(url, raw, index, folder="targets"):
    u = urllib.parse.urlparse(url)
    name = (u.netloc.replace("www.", "") + "__" + (u.path.strip("/").replace("/", "__") or "index"))
    if u.query:
        name += "__" + re.sub(r"[^A-Za-z0-9=_-]+", "_", u.query)
    name = name[:180]
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "wb") as f:
        f.write(raw)
    index.write(f"{url}\t{folder}/{name}\t200\n")


def targets():
    idx = open(os.path.join(OUT, "targets-index.tsv"), "w", encoding="utf-8")
    seen = set()

    def fetch(url, follow=None, budget=None):
        if url in seen:
            return b""
        seen.add(url)
        st, raw = get_raw(url)
        if st != 200 or not raw:
            idx.write(f"{url}\t-\t{st}\n")
            return b""
        save_raw(url, raw, idx)
        time.sleep(0.8)
        return raw

    # Karachi Police: WordPress records of every police station, the sitemap and each station page
    for n in range(1, 8):
        raw = fetch(f"https://karachipolice.gov.pk/wp-json/wp/v2/police-station?per_page=100&page={n}")
        if not raw or raw.strip() in (b"[]", b""):
            break
    station_urls = set()
    for sm in ["https://karachipolice.gov.pk/sitemap_index.xml", "https://karachipolice.gov.pk/wp-sitemap.xml",
               "https://karachipolice.gov.pk/police-station-sitemap.xml",
               "https://karachipolice.gov.pk/wp-sitemap-posts-police-station-1.xml"]:
        raw = fetch(sm).decode("utf-8", "replace")
        for loc in re.findall(r"<loc>([^<]+)</loc>", raw):
            if "police-station" in loc and loc.endswith(".xml"):
                for l2 in re.findall(r"<loc>([^<]+)</loc>", fetch(loc).decode("utf-8", "replace")):
                    station_urls.add(l2)
            elif "/police-station/" in loc:
                station_urls.add(loc)
    for page in ["https://karachipolice.gov.pk/services/police-stations-in-karachi/",
                 "https://karachipolice.gov.pk/services/find-police-stations-near-me/"]:
        fetch(page)
    print("Karachi station pages:", len(station_urls))
    mids = set()
    for u in sorted(station_urls):
        raw = fetch(u).decode("utf-8", "replace")
        mids.update(re.findall(r"maps/d/(?:u/\d+/)?(?:edit|viewer|embed)\?mid=([A-Za-z0-9_-]+)", raw))
    for f in os.listdir(os.path.join(OUT, "targets")):
        mids.update(re.findall(r"maps/d/(?:u/\d+/)?(?:edit|viewer|embed)\?mid=([A-Za-z0-9_-]+)",
                               open(os.path.join(OUT, "targets", f), encoding="utf-8", errors="replace").read()))
    print("Google My Maps:", len(mids))
    for mid in sorted(mids):  # every pin of each map, as KML
        fetch(f"https://www.google.com/maps/d/kml?mid={mid}&forcekml=1")

    # Islamabad Police: the station locator on the home page and any data files it loads
    for page in ["https://islamabadpolice.gov.pk/index.php", "https://islamabadpolice.gov.pk/contact.php"]:
        raw = fetch(page).decode("utf-8", "replace")
        for ref in re.findall(r"""["']([^"'\s]+\.(?:json|php)(?:\?[^"'\s]*)?)["']""", raw):
            if any(k in ref.lower() for k in ("locat", "station", "ps", "pkm", "map", "api", "json")):
                fetch(urllib.parse.urljoin(page, ref))

    # Sindh, Balochistan, AJK, GB: retry with a browser user agent and long timeouts; follow station links
    for seeds, pat, budget in [
        (["https://sindhpolice.gov.pk/", "https://sindhpolice.gov.pk/city/police-station"], r"(?i)police-station|/districts?\b", 160),
        (["https://balochistanpolice.gov.pk/", "https://balochistanpolice.gov.pk/dpo_contactdetails",
          "https://balochistanpolice.gov.pk/police_stations", "https://balochistanpolice.gov.pk/police-stations"],
         r"(?i)police[-_ ]?station|dpo|district|contact", 60),
        (["https://police.ajk.gov.pk/", "https://ajkpolice.gov.pk/"], r"(?i)police[-_ ]?station|district|contact", 60),
        (["https://gbp.gov.pk/police-stations/", "https://gbp.gov.pk/total-police-stations-in-gb/"], r"(?i)wp-content/uploads", 30),
    ]:
        queue, n = list(seeds), 0
        host = urllib.parse.urlparse(seeds[0]).netloc.replace("www.", "")
        while queue and n < budget:
            url = queue.pop(0)
            raw = fetch(url)
            n += 1
            if not raw:
                continue
            p = Links()
            try:
                p.feed(raw.decode("utf-8", "replace"))
            except Exception:
                pass
            imgs = re.findall(r"""src=["']([^"']+\.(?:jpe?g|png|webp|pdf))["']""", raw.decode("utf-8", "replace"), re.I) if "gbp.gov.pk" in host else []
            for href in p.links + imgs:
                nxt = urllib.parse.urljoin(url, href.strip()).split("#")[0]
                if urllib.parse.urlparse(nxt).netloc.replace("www.", "") == host and nxt not in seen and re.search(pat, nxt):
                    queue.append(nxt)
        print(f"  {host}: {n} fetched")
    idx.close()


# ================================================================ step 3: addresses and coordinates (Nominatim)
def geocode():
    """Reads data/police/requests.json: {"reverse": [[id, lat, lon], …], "forward": [[id, query], …]}
    and writes data/police/raw/geocode.json with Nominatim's answers (1 request per second, as its policy asks)."""
    req = json.load(open(os.path.join(ROOT, "data", "police", "requests.json"), encoding="utf-8"))
    out_path = os.path.join(OUT, "geocode.json")
    out = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {"reverse": {}, "forward": {}}
    base = "https://nominatim.openstreetmap.org"
    t0 = time.time()
    for i, (key, lat, lon) in enumerate(req.get("reverse", [])):
        if key in out["reverse"] or time.time() - t0 > 5.3 * 3600:
            continue
        st, raw = get(f"{base}/reverse?format=jsonv2&zoom=18&addressdetails=1&accept-language=en&lat={lat}&lon={lon}", timeout=60)
        if st == 200 and raw:
            out["reverse"][key] = json.loads(raw)
        time.sleep(1.1)
        if i % 200 == 0:
            print("reverse", i)
            json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    for i, (key, q) in enumerate(req.get("forward", [])):
        if key in out["forward"] or time.time() - t0 > 5.3 * 3600:
            continue
        st, raw = get(f"{base}/search?format=jsonv2&limit=3&countrycodes=pk&addressdetails=1&accept-language=en&q={urllib.parse.quote(q)}", timeout=60)
        if st == 200 and raw:
            out["forward"][key] = json.loads(raw)
        time.sleep(1.1)
        if i % 200 == 0:
            print("forward", i)
            json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    print("geocode:", len(out["reverse"]), "reverse,", len(out["forward"]), "forward")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "crawl"
    os.makedirs(OUT, exist_ok=True)
    {"crawl": main, "targets": targets, "geocode": geocode}[step]()
