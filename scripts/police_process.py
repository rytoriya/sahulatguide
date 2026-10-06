#!/usr/bin/env python3
"""Turn the raw police data into the Police Station Directory's station list.

  python3 scripts/police_process.py requests   match official stations to map points and write
                                                data/police/requests.json (what still needs geocoding)
  python3 scripts/police_process.py build      after the geocode step: write data/police/stations.json
                                                (every station with location, address and source)

Inputs: data/police-stations.txt (official lists), data/police/raw/osm-police.json.gz,
data/police/raw/targets.tar.gz (Karachi Police records and map pins), data/police/raw/geocode.json.
"""
import difflib
import gzip
import io
import json
import os
import re
import sys
import tarfile

sys.path.insert(0, os.path.dirname(__file__))
from police_geo import Locator  # noqa: E402
import police_parse_karachi  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "police", "raw")
NOISE = r"\b(police|station|stations|thana|thanna|ps|p s|pp|p p|ps\.|p\.s|the|of|and|new|old)\b"


def key(name, drop=()):
    s = str(name or "").lower()
    s = s.replace("p.s.", " ").replace("p.s", " ").replace("&", " and ")
    s = re.sub(r"[()\[\],.'`/-]", " ", s)
    s = re.sub(NOISE, " ", s)
    for w in drop:
        w = w.lower().strip()
        if w and re.sub(r"\b%s\b" % re.escape(w), " ", s).strip():
            s = re.sub(r"\b%s\b" % re.escape(w), " ", s)
    s = re.sub(r"\bsadd?ar\b", "saddar", s)
    s = re.sub(r"\bcant(t|onment)?\b", "cantt", s)
    return " ".join(s.split())


def similar(a, b):
    if not a or not b:
        return 0
    if a == b:
        return 1
    ta, tb = set(a.split()), set(b.split())
    if ta and tb and (ta <= tb or tb <= ta):
        return 0.9 if min(len(ta), len(tb)) >= 1 and abs(len(ta) - len(tb)) <= 1 else 0.82
    return difflib.SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------- official lists
def official():
    """{district_id: {"src","url","stations":[{"name","phone","circle"}]}} from data/police-stations.txt"""
    data, cur = {}, None
    for line in open(os.path.join(ROOT, "data", "police-stations.txt"), encoding="utf-8"):
        line = line.strip()
        if not line or (line.startswith("#") and not line.startswith("## ")):
            continue
        if line.startswith("## "):
            did, src, url = [x.strip() for x in line[3:].split("|")]
            cur = data[did] = {"src": src, "url": url, "stations": []}
        elif cur and line.startswith("- "):
            k = line.index(":")
            circle = line[2:k].strip()
            for s in line[k + 1:].split(";"):
                s = s.strip()
                if s:
                    n, _, ph = s.partition("|")
                    cur["stations"].append({"name": n.strip(), "phone": ph.strip(), "circle": circle})
    return data


# ---------------------------------------------------------------- map points
def osm_points(L):
    pts = []
    for e in json.load(gzip.open(os.path.join(RAW, "osm-police.json.gz")))["elements"]:
        t = e.get("tags") or {}
        if t.get("amenity") != "police":
            continue
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        if lat is None:
            continue
        d, prov = L.district(lat, lon)
        if not prov:
            continue
        addr = ", ".join(x for x in [t.get("addr:housenumber"), t.get("addr:street"), t.get("addr:suburb"),
                                       t.get("addr:city") or t.get("addr:place")] if x)
        pts.append({"src": "osm", "id": f"osm:{e['type'][0]}{e['id']}", "lat": round(lat, 6), "lon": round(lon, 6),
                    "district": d["id"] if d else None, "prov": prov,
                    "name": t.get("name:en") or t.get("name") or "", "ur": t.get("name:ur", ""),
                    "phone": t.get("phone") or t.get("contact:phone") or "", "addr": addr})
    return pts


def karachi_pins(L):
    """Station pins from Karachi Police's own pages (Google Maps place links) and Google My Maps KML."""
    pts = []
    tf = os.path.join(RAW, "targets.tar.gz")
    if not os.path.exists(tf):
        return pts
    with tarfile.open(tf) as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            raw = tar.extractfile(m).read().decode("utf-8", "replace")
            if "karachipolice.gov.pk" in m.name:
                for name, lat, lon in re.findall(r"maps/place/([^/@\"]+)/@[^\"]*?!3d(-?[\d.]+)!4d(-?[\d.]+)", raw):
                    pts.append(("kp-page", re.sub(r"\+", " ", re.sub(r"%[0-9A-Fa-f]{2}", " ", name)), float(lat), float(lon), m.name))
            if "google.com__maps__d__kml" in m.name:
                for pm in re.findall(r"(?s)<Placemark>(.*?)</Placemark>", raw):
                    nm = re.search(r"(?s)<name>(.*?)</name>", pm)
                    co = re.search(r"(?s)<Point>\s*<coordinates>\s*(-?[\d.]+),(-?[\d.]+)", pm)
                    if nm and co:
                        pts.append(("kml", re.sub(r"<!\[CDATA\[|\]\]>", "", nm.group(1)).strip(), float(co.group(2)), float(co.group(1)), m.name))
    out = []
    for kind, name, lat, lon, srcfile in pts:
        d, prov = L.district(lat, lon)
        if prov:
            out.append({"src": "karachipolice" if kind == "kp-page" else "kml", "id": f"{kind}:{lat:.5f},{lon:.5f}", "lat": lat, "lon": lon,
                        "district": d["id"] if d else None, "prov": prov, "name": name, "ur": "", "phone": "", "addr": ""})
    return out


# ---------------------------------------------------------------- matching
def match(L, off, pts):
    dist = {d["id"]: d for d in L.D}
    by_d = {}
    for p in pts:
        if p["district"]:
            by_d.setdefault(p["district"], []).append(p)
    kar = police_parse_karachi.stations_by_district()
    result = {}
    for did, d in dist.items():
        drop = [d["name"], d["hq"]] + d["name"].split()
        stations = [dict(s) for s in (off.get(did, {}).get("stations") or [])]
        # official pins first (Karachi Police publishes each station's location and jurisdiction)
        for s in stations:
            for k in kar.get(did, []):
                if key(k["name"]) == key(s["name"]) and k["ll"]:
                    s.update({"lat": k["ll"][0], "lon": k["ll"][1], "loc": "official", "ref": "kp:" + k["url"], "addr": "", "ur": "",
                              "contacts": k["contacts"], "page": k["url"]})
                    if k.get("jur"):
                        s["jur"] = [[round(x, 4), round(y, 4)] for x, y in _simplify(k["jur"], 0.0008)]
                    break
        cand = by_d.get(did, [])
        pairs = []
        for i, s in enumerate(stations):
            if "lat" in s:
                continue
            ks = key(s["name"], drop)
            for j, p in enumerate(cand):
                sc = similar(ks, key(p["name"], drop))
                if sc >= 0.84:
                    pairs.append((sc, i, j))
        used_s, used_p = set(), set()
        for sc, i, j in sorted(pairs, reverse=True):
            if i in used_s or j in used_p:
                continue
            used_s.add(i); used_p.add(j)
            p = cand[j]
            stations[i].update({"lat": p["lat"], "lon": p["lon"], "loc": p["src"], "ref": p["id"], "addr": p["addr"], "ur": p["ur"]})
        extra = [p for j, p in enumerate(cand) if j not in used_p]
        result[did] = {"stations": stations, "extra": extra}
    return result


def requests(L, res):
    rev, fwd = [], []
    dist = {d["id"]: d for d in L.D}
    pnames = {"pb": "Punjab", "sd": "Sindh", "kp": "Khyber Pakhtunkhwa", "bl": "Balochistan", "ict": "Islamabad",
              "ajk": "Azad Kashmir", "gb": "Gilgit-Baltistan"}
    for did, r in res.items():
        d = dist[did]
        for s in r["stations"]:
            if "lat" in s:
                if not s.get("addr"):
                    rev.append([s["ref"], s["lat"], s["lon"]])
            else:
                fwd.append([f"{did}|{s['name']}|ps", f"{s['name']} police station, {d['name']}, {pnames[d['prov']]}"])
                place = re.sub(r"(?i)\b(city|saddar|sadar|cantt|cantonment|police|station|ps|women|model|town|new|old|\(.*?\))\b", " ", s["name"])
                place = " ".join(place.split())
                if place and len(place) > 2:
                    fwd.append([f"{did}|{s['name']}|place", f"{place}, {d['name']}, {pnames[d['prov']]}"])
        for p in r["extra"]:
            if not p.get("addr"):
                rev.append([p["id"], p["lat"], p["lon"]])
    seen = set()
    rev = [x for x in rev if not (x[0] in seen or seen.add(x[0]))]
    return {"reverse": rev, "forward": fwd}


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "requests"
    L = Locator()
    off = official()
    pts = osm_points(L)  # Karachi's official pins are applied in match()
    res = match(L, off, pts)
    n_off = sum(len(r["stations"]) for r in res.values())
    n_loc = sum(1 for r in res.values() for s in r["stations"] if "lat" in s)
    print(f"official stations: {n_off}, located from map data: {n_loc}; map points: {len(pts)}, "
          f"unmatched map points: {sum(len(r['extra']) for r in res.values())}")
    if step == "requests":
        req = requests(L, res)
        json.dump(req, open(os.path.join(ROOT, "data", "police", "requests.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"requests.json: {len(req['reverse'])} reverse, {len(req['forward'])} forward")
    if step == "build":
        build(L, res)
    return L, res



# ---------------------------------------------------------------- final build
NOT_STATION = re.compile(r"(?i)check ?post|checkpoint|chowki|picket|naka|barrier|lines\b|office|headquarter|\bhq\b|house|"
                         r"academy|training|school|college|hospital|traffic|motorway|fia\b|\bfc\b|frontier corps|rangers|levies|"
                         r"anti.?narc|ctd|cid|special branch|khidmat|dolphin|eagle|rescue|beat|post\b|camp|mess|colony|quarter")
IS_STATION = re.compile(r"(?i)police station|\bthana\b|\bp\.?s\.?\b|تھانہ")


def address_of(nom):
    """A short readable address from a Nominatim result."""
    a = (nom or {}).get("address") or {}
    parts = [a.get("road"), a.get("neighbourhood") or a.get("quarter"), a.get("suburb"),
             a.get("city") or a.get("town") or a.get("village") or a.get("hamlet") or a.get("county")]
    seen, out = set(), []
    for p in parts:
        if p and p.lower() not in seen and not re.search(r"(?i)tehsil|district|division", p):
            seen.add(p.lower())
            out.append(p)
    return ", ".join(out)


def build(L, res):
    geo = {}
    gp = os.path.join(RAW, "geocode.json")
    if os.path.exists(gp):
        geo = json.load(open(gp, encoding="utf-8"))
    rev, fwd = geo.get("reverse", {}), geo.get("forward", {})
    dist = {d["id"]: d for d in L.D}
    out, stats = {}, {"exact": 0, "found": 0, "area": 0, "none": 0}

    def in_district(lat, lon, did):
        d, _ = L.district(lat, lon)
        return d and d["id"] == did

    for did, r in res.items():
        stations, extra = [], []
        for s in r["stations"]:
            st = {"n": s["name"], "ph": s.get("phone", ""), "c": s.get("circle", "")}
            for f in ("contacts", "page", "jur"):
                if s.get(f):
                    st[f] = s[f]
            if "lat" in s:
                st.update(ll=[s["lat"], s["lon"]], q="exact", a=s.get("addr") or address_of(rev.get(s["ref"])), ur=s.get("ur", ""))
            else:
                hit = None
                for cand in fwd.get(f"{did}|{s['name']}|ps") or []:
                    if cand.get("category") == "amenity" and cand.get("type") == "police" and in_district(float(cand["lat"]), float(cand["lon"]), did):
                        hit = ("found", cand)
                        break
                if not hit:
                    for cand in fwd.get(f"{did}|{s['name']}|place") or []:
                        if cand.get("category") in ("place", "boundary", "landuse", "highway") and in_district(float(cand["lat"]), float(cand["lon"]), did):
                            hit = ("area", cand)
                            break
                if hit:
                    kind, cand = hit
                    st.update(ll=[round(float(cand["lat"]), 6), round(float(cand["lon"]), 6)], q=kind,
                              a=address_of(cand) if kind == "found" else (cand.get("name") or address_of(cand)))
            stats[st.get("q", "none")] += 1
            stations.append(st)
        for p in r["extra"]:
            item = {"n": p["name"] or "Police point", "ph": p.get("phone", ""), "ll": [p["lat"], p["lon"]], "q": "exact",
                    "a": p.get("addr") or address_of(rev.get(p["id"])), "ur": p.get("ur", "")}
            if not r["stations"] and p["name"] and IS_STATION.search(p["name"]) and not NOT_STATION.search(p["name"]):
                item["c"] = ""
                stations.append(item)
                stats["exact"] += 1
            else:
                extra.append(item)
        out[did] = {"stations": stations, "extra": extra}
    json.dump(out, open(os.path.join(ROOT, "data", "police", "stations.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    write_district_files(L, out, official())
    total = sum(len(v["stations"]) for v in out.values())
    print(f"stations.json: {total} stations in {sum(1 for v in out.values() if v['stations'])} districts; "
          f"located exactly {stats['exact']}, found by name {stats['found']}, approximate {stats['area']}, no location {stats['none']}; "
          f"other police points {sum(len(v['extra']) for v in out.values())}")



# ---------------------------------------------------------------- per-district files for the page
def _simplify(pts, tol):
    """Douglas-Peucker on a ring of [lon, lat] points."""
    if len(pts) < 5:
        return pts
    def d(p, a, b):
        (x, y), (x1, y1), (x2, y2) = p, a, b
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return ((x - x1) ** 2 + (y - y1) ** 2) ** .5
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return ((x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2) ** .5
    keep = [0, len(pts) - 1]
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        best, idx = 0, None
        for k in range(i + 1, j):
            dd = d(pts[k], pts[i], pts[j])
            if dd > best:
                best, idx = dd, k
        if idx is not None and best > tol:
            keep.append(idx)
            stack += [(i, idx), (idx, j)]
    return [pts[k] for k in sorted(keep)]


def outlines(L):
    """{district_id: [polygon rings…]} built from tehsil boundaries, simplified for the web."""
    out = {}
    for name, polys, (x0, y0, x1, y1) in L.adm3.feats:
        ring = max((p[0] for p in polys), key=len)
        # a point inside the tehsil: try the bbox centre, then ring vertices nudged inward
        cand = [((y0 + y1) / 2, (x0 + x1) / 2)] + [(ring[k][1] * .98 + (y0 + y1) / 2 * .02, ring[k][0] * .98 + (x0 + x1) / 2 * .02) for k in range(0, len(ring), max(1, len(ring) // 12))]
        did = None
        for la, lo in cand:
            d, _ = L.district(la, lo)
            if d:
                did = d["id"]
                break
        if not did:
            continue
        for p in polys:
            r = _simplify([[round(x, 4), round(y, 4)] for x, y in p[0]], 0.004)
            if len(r) >= 4:
                out.setdefault(did, []).append(r)
    return out


def write_district_files(L, built, off):
    os.makedirs(os.path.join(ROOT, "police", "districts"), exist_ok=True)
    outl = outlines(L)
    n = 0
    for d in L.D:
        did = d["id"]
        b = built.get(did, {"stations": [], "extra": []})
        rings = outl.get(did, [])
        xs = [p[0] for r in rings for p in r] + [s["ll"][1] for s in b["stations"] + b["extra"] if s.get("ll")]
        ys = [p[1] for r in rings for p in r] + [s["ll"][0] for s in b["stations"] + b["extra"] if s.get("ll")]
        bbox = [min(ys), min(xs), max(ys), max(xs)] if xs else None
        o = off.get(did, {})
        doc = {"id": did, "bbox": bbox, "outline": rings, "stations": b["stations"], "extra": b["extra"],
               "src": o.get("src", ""), "url": o.get("url", "")}
        json.dump(doc, open(os.path.join(ROOT, "police", "districts", did + ".json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        n += 1
    print(f"police/districts/: {n} files")


if __name__ == "__main__":
    main()
