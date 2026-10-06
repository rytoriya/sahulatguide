#!/usr/bin/env python3
"""Read Karachi Police's station pages saved by the data job (data/police/raw/targets.tar.gz).

Each page gives the station's zone, district, sub-division, the SDPO, SHO, SIO and Head Moharrar
with their numbers, and a Google Maps pin. Returns a list of stations:
  {"name", "url", "district" (Karachi Police's label), "sub", "ll": [lat, lon] or None,
   "contacts": [[role, name, phone], …], "updated"}
"""
import html
import json
import os
import re
import tarfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROLES = [("SDPO", "SDPO"), ("SHO", "SHO"), ("SIO", "SIO"), ("Head Muharar", "Head Moharrar")]


def text(raw):
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h\d|span)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return [" ".join(x.split()) for x in t.split("\n") if x.strip()]


def parse_station(raw, url):
    title = re.search(r"(?is)<title>(.*?)</title>", raw)
    name = html.unescape(title.group(1)).split("|")[0].split(" - ")[0].strip() if title else url.rstrip("/").rsplit("/", 1)[-1]
    L = text(raw)
    try:
        i = L.index("Updated on Date:")
    except ValueError:
        return None
    block = L[i:i + 40]

    def after(label, n=1):
        for k, x in enumerate(block):
            if x.upper() == label.upper():
                return block[k + 1:k + 1 + n]
        return []

    contacts = []
    for label, role in ROLES:
        v = after(label, 2)
        if len(v) == 2 and re.search(r"\d{4}", v[1]) and v[0].upper() != "N/A":
            contacts.append([role, v[0].title(), v[1]])
    pin = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", raw)
    jur = re.findall(r"maps/d/(?:u/\d+/)?(?:edit|viewer|embed)\?mid=([A-Za-z0-9_-]+)", raw)
    return {
        "name": name, "url": url,
        "district": (after("DISTRICT") or [""])[0], "zone": (after("ZONE") or [""])[0], "sub": (after("SUB-DIVISION") or [""])[0],
        "ll": [round(float(pin.group(1)), 6), round(float(pin.group(2)), 6)] if pin else None,
        "contacts": contacts, "updated": (after("Updated on Date:") or [""])[0], "jurisdiction": jur[0] if jur else "",
    }


def parse_all(tar_path=os.path.join(ROOT, "data", "police", "raw", "targets.tar.gz")):
    out = []
    if not os.path.exists(tar_path):
        return out
    with tarfile.open(tar_path) as tar:
        for m in tar.getmembers():
            base = m.name.rsplit("/", 1)[-1]
            if m.isfile() and base.startswith("karachipolice.gov.pk__police-station__"):
                slug = base.split("__police-station__", 1)[1]
                st = parse_station(tar.extractfile(m).read().decode("utf-8", "replace"), f"https://karachipolice.gov.pk/police-station/{slug}/")
                if st:
                    out.append(st)
    return out


# Karachi Police district labels -> site district ids ("City" holds the old South's Saddar/Lyari areas)
DISTRICT_ID = {"central": "sd-karachi-central", "cenral": "sd-karachi-central", "east": "sd-karachi-east",
               "south": "sd-karachi-south", "city": "sd-karachi-south", "west": "sd-karachi-west",
               "korangi": "sd-korangi", "district korangi": "sd-korangi", "malir": "sd-malir", "keamari": "sd-keamari"}


def kml_shapes(tar_path=os.path.join(ROOT, "data", "police", "raw", "targets.tar.gz")):
    """{mid: {"polys": [[[lon, lat], …]], "points": [[lat, lon], …]}} from the saved Google My Maps KML files."""
    out = {}
    with tarfile.open(tar_path) as tar:
        for m in tar.getmembers():
            base = m.name.rsplit("/", 1)[-1]
            mm = re.search(r"kml__mid=([A-Za-z0-9_-]+?)_forcekml", base)
            if not (m.isfile() and mm):
                continue
            raw = tar.extractfile(m).read().decode("utf-8", "replace")
            polys = [[[float(a), float(b)] for a, b, *_ in (c.split(",") for c in co.split())]
                     for co in re.findall(r"(?s)<Polygon>.*?<outerBoundaryIs>.*?<coordinates>(.*?)</coordinates>", raw)]
            points = [[float(b), float(a)] for a, b in re.findall(r"(?s)<Point>\s*<coordinates>\s*(-?[\d.]+),(-?[\d.]+)", raw)]
            out[mm.group(1)] = {"polys": polys, "points": points}
    return out


def stations_by_district():
    """{district_id: [station dicts with "jur" (jurisdiction ring) and pins filled from the KML where missing]}"""
    shapes = kml_shapes()
    out = {}
    for s in parse_all():
        did = DISTRICT_ID.get(s["district"].strip().lower())
        if not did:
            continue
        sh = shapes.get(s["jurisdiction"]) or {}
        if len(sh.get("polys", [])) == 1:  # one polygon = this station's area (district-wide maps have many)
            s["jur"] = sh["polys"][0]
        if not s["ll"] and len(sh.get("points", [])) == 1:
            s["ll"] = [round(sh["points"][0][0], 6), round(sh["points"][0][1], 6)]
        out.setdefault(did, []).append(s)
    return out


if __name__ == "__main__":
    s = parse_all()
    print(len(s), "Karachi stations;", sum(1 for x in s if x["ll"]), "with map pins;", sum(1 for x in s if x["contacts"]), "with contacts")
    from collections import Counter
    print(Counter(x["district"] for x in s))
    print(json.dumps(s[0], ensure_ascii=False))

