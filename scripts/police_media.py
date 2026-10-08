#!/usr/bin/env python3
"""Collect licensed photos and badges of Pakistan's police from Wikimedia Commons.

Run by .github/workflows/police-media.yml (the development environment cannot reach Commons).
Writes into data/police/media/:
  candidates.json   every file found, with title, description, categories, author, licence
                    and why it matched (nothing is hidden, so choices can be reviewed)
  files/<id>.<ext>  downloaded copies (photos at 1280 px wide, SVG badges as they are plus a
                    512 px PNG) of files that look Pakistani AND carry a free licence

Only files under a free licence (public domain, CC0, CC BY, CC BY-SA) are downloaded; the
author, licence and source URL are kept so credits can be shown on the site.
Standard library only.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "police", "media")
FILES = os.path.join(OUT, "files")
API = "https://commons.wikimedia.org/w/api.php"
UA = "SahulatGuide-media/1.0 (https://sahulatguide.netlify.app; a public-service guide; open licences only)"
MAX_BYTES = 70 * 1024 * 1024

CATEGORIES = [
    "Police stations in Pakistan", "Police stations in Punjab, Pakistan", "Police stations in Sindh",
    "Police stations in Khyber Pakhtunkhwa", "Police stations in Balochistan, Pakistan",
    "Police stations in Islamabad", "Police stations in Karachi", "Police stations in Lahore",
    "Police stations in Peshawar", "Police stations in Rawalpindi", "Police stations in Quetta",
    "Police stations in Faisalabad", "Police stations in Multan", "Police stations in Hyderabad, Pakistan",
    "Police in Pakistan", "Law enforcement in Pakistan", "Police vehicles in Pakistan",
    "Police officers of Pakistan", "Police of Pakistan", "Police badges of Pakistan",
    "Punjab Police (Pakistan)", "Sindh Police", "Khyber Pakhtunkhwa Police", "Balochistan Police",
    "Islamabad Capital Territory Police", "Islamabad Police", "Azad Kashmir Police", "Gilgit-Baltistan Police",
    "Karachi Police", "Lahore Police", "Peshawar Police", "Frontier Constabulary", "Elite Police (Pakistan)",
    "Dolphin Force", "Logos of police forces of Pakistan", "Emblems of Pakistan police",
    "Pakistan Rangers", "Police training in Pakistan", "Police Khidmat Markaz",
]
CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar", "Quetta", "Faisalabad", "Multan", "Gujranwala",
          "Hyderabad Sindh", "Sialkot", "Sukkur", "Bahawalpur", "Abbottabad", "Mardan", "Swat", "Gilgit", "Skardu",
          "Muzaffarabad", "Mirpur", "Sargodha", "Larkana", "Mansehra", "Kohat", "Swabi", "Gujrat", "Sahiwal", "Jhelum"]
SEARCHES = (["police station Pakistan", "thana Pakistan", "police chowki Pakistan", "police headquarters Pakistan",
             "Punjab Police logo", "Sindh Police logo", "Khyber Pakhtunkhwa Police logo", "Balochistan Police logo",
             "Islamabad Police logo", "Azad Kashmir Police logo", "Gilgit-Baltistan Police logo", "Pakistan police badge",
             "Police Khidmat Markaz", "Police Lines Pakistan", "police Central Police Office Pakistan"]
            + [f"police station {c}" for c in CITIES] + [f"police {c} Pakistan" for c in CITIES[:12]])

PK_WORDS = re.compile(r"pakistan|punjab|sindh|khyber|pakhtunkhwa|balochistan|islamabad|karachi|lahore|peshawar|quetta|rawalpindi|"
                      r"faisalabad|multan|hyderabad,? sindh|gilgit|baltistan|azad kashmir|muzaffarabad|\bkpk\b|\bkp\b|thana|sialkot|"
                      r"gujranwala|sukkur|abbottabad|mardan|swat|skardu|mirpur|sargodha|larkana|mansehra|kohat|swabi|bahawalpur", re.I)
NOT_PK = re.compile(r"\bindia\b|indian|delhi|mumbai|kolkata|bangalore|hyderabad,? telangana|telangana|kerala|tamil|bangladesh|"
                    r"dhaka|nepal|sri lanka|karnataka|maharashtra|uttar pradesh|west bengal|jammu and kashmir police|\bj&k\b|chennai", re.I)
FREE = re.compile(r"^(cc0|cc[- ]by(?!-nc)|cc[- ]by-sa|public domain|pd[- ]|attribution|no restrictions|gfdl|"
                  r"free ?art|copyrighted free use|cc[- ]zero)", re.I)
NONFREE = re.compile(r"nc|non-?free|fair use|nd\b|all rights reserved|copyrighted$", re.I)
BADGE_WORDS = re.compile(r"logo|emblem|badge|crest|insignia|seal|flag", re.I)


def call(params, tries=4):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  retry", e, file=sys.stderr)
            time.sleep(4 * (i + 1))
    return {}


def clean(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def category_files(cat, depth=1, seen=None):
    seen = seen if seen is not None else set()
    out = []
    cont = {}
    while True:
        j = call(dict(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit="500", cmtype="file|subcat", **cont))
        for m in (j.get("query", {}).get("categorymembers") or []):
            if m["ns"] == 6:
                out.append(m["title"])
            elif m["ns"] == 14 and depth > 0 and m["title"] not in seen:
                seen.add(m["title"])
                out += category_files(m["title"][len("Category:"):], depth - 1, seen)
        cont = (j.get("continue") or {})
        if not cont:
            break
        time.sleep(0.3)
    return out


def search_files(q):
    j = call(dict(action="query", list="search", srsearch=q, srnamespace="6", srlimit="50"))
    return [m["title"] for m in (j.get("query", {}).get("search") or [])]


def info(titles):
    res = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        j = call(dict(action="query", titles="|".join(chunk), prop="imageinfo|categories", cllimit="max",
                      iiprop="url|size|mime|extmetadata", iiurlwidth="1280"))
        for p in (j.get("query", {}).get("pages") or []):
            ii = (p.get("imageinfo") or [{}])[0]
            if not ii:
                continue
            md = ii.get("extmetadata") or {}
            g = lambda k: clean((md.get(k) or {}).get("value", ""))
            res[p["title"]] = {
                "title": p["title"], "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_")),
                "url": ii.get("url"), "thumb": ii.get("thumburl"), "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"), "size": ii.get("size"),
                "description": g("ImageDescription")[:500], "artist": g("Artist")[:200], "credit": g("Credit")[:200],
                "license": g("LicenseShortName"), "license_url": (md.get("LicenseUrl") or {}).get("value", ""),
                "usage": g("UsageTerms")[:120], "restrictions": g("Restrictions"), "attribution_required": g("AttributionRequired"),
                "date": g("DateTimeOriginal")[:40],
                "categories": [c["title"][9:] for c in (p.get("categories") or [])][:40],
            }
        time.sleep(0.3)
    return res


def judge(rec):
    text = " ".join([rec["title"], rec["description"], " ".join(rec["categories"]), rec["credit"]])
    rec["pk"] = bool(PK_WORDS.search(text)) and not NOT_PK.search(text)
    lic = rec["license"] or rec["usage"]
    rec["free"] = bool(FREE.search(lic)) and not NONFREE.search(lic) and not rec["restrictions"]
    rec["badge"] = bool(BADGE_WORDS.search(rec["title"]))
    rec["police"] = bool(re.search(r"police|thana|constabulary|rangers|dolphin|khidmat", text, re.I))
    return rec


def fetch(url, path):
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
            return True
        except urllib.error.HTTPError as e:
            if e.code in (404, 403):
                return False
            time.sleep(8 * (i + 1))
        except Exception:
            time.sleep(5 * (i + 1))
    return False


def main():
    os.makedirs(FILES, exist_ok=True)
    titles = {}
    for cat in CATEGORIES:
        fs = category_files(cat)
        print(f"category {cat}: {len(fs)} files")
        for t in fs:
            titles.setdefault(t, []).append("cat:" + cat)
        time.sleep(0.3)
    for q in SEARCHES:
        fs = search_files(q)
        print(f"search {q}: {len(fs)} files")
        for t in fs:
            titles.setdefault(t, []).append("q:" + q)
        time.sleep(0.3)
    print("distinct files:", len(titles))
    recs = info(list(titles))
    for t, rec in recs.items():
        rec["found_by"] = titles.get(t, [])[:6]
        judge(rec)
    cands = sorted(recs.values(), key=lambda r: (not r["pk"], not r["police"], r["title"]))
    json.dump(cands, open(os.path.join(OUT, "candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("candidates:", len(cands), "pk:", sum(r["pk"] for r in cands), "free+pk+police:", sum(r["pk"] and r["free"] and r["police"] for r in cands))

    total, n = 0, 0
    for i, r in enumerate(cands):
        if not (r["pk"] and r["free"] and (r["police"] or r["badge"])):
            continue
        if r["mime"] not in ("image/jpeg", "image/png", "image/svg+xml", "image/webp") or (r["w"] or 0) < 400:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", r["title"][5:].rsplit(".", 1)[0].lower()).strip("-")[:70]
        ext = {"image/jpeg": "jpg", "image/png": "png", "image/svg+xml": "svg", "image/webp": "webp"}[r["mime"]]
        r["file"] = f"{slug}.{ext}"
        if r["mime"] == "image/svg+xml":
            ok = fetch(r["url"], os.path.join(FILES, r["file"]))
            if ok and r.get("thumb"):
                fetch(r["thumb"].replace("1280px", "512px"), os.path.join(FILES, slug + ".png"))
                r["png"] = slug + ".png"
        else:
            ok = fetch(r["thumb"] or r["url"], os.path.join(FILES, r["file"]))
        if ok:
            n += 1
            total += os.path.getsize(os.path.join(FILES, r["file"]))
        else:
            r.pop("file", None)
        if total > MAX_BYTES:
            print("size cap reached")
            break
        time.sleep(0.4)
    json.dump(cands, open(os.path.join(OUT, "candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"downloaded {n} files, {total/1e6:.1f} MB")


if __name__ == "__main__":
    main()
