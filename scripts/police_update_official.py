#!/usr/bin/env python3
"""Merge station lists parsed from official police pages into data/police-stations.txt.

For each district found in a parsed source, its station lines ("- circle: name|phone; …")
are replaced; its office: and link: lines are kept. The block's source becomes the page it
was read from. Districts not in a parsed source are left as they are.

Usage: python3 scripts/police_update_official.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import police_parse_karachi  # noqa: E402
import police_parse_punjab  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TXT = os.path.join(ROOT, "data", "police-stations.txt")
RAW = os.path.join(ROOT, "data", "police", "raw")


def punjab_url(did):
    special = {"pb-lahore": "LahoreDirectory", "pb-rawalpindi": "RawalpindiDirectory", "pb-faisalabad": "FaisalabadDirectory",
               "pb-gujranwala": "GujranwalaDirectory", "pb-multan": "MultanDirectory", "pb-dera-ghazi-khan": "dgkhan_directory",
               "pb-nankana-sahib": "nankana_directory", "pb-gujrat": "gujrat_dIrectory"}
    page = special.get(did) or did[3:].replace("-", "_") + "_directory"
    return "https://punjabpolice.gov.pk/" + page


def parsed_sources():
    """{district_id: (source name, url, [(circle, [(name, phone)])])}"""
    out = {}
    for did, circles in police_parse_punjab.parse_all(os.path.join(RAW, "pages.tar.gz")).items():
        if sum(len(s) for _, s in circles):
            out[did] = ("Punjab Police", punjab_url(did), circles)
    for did, sts in police_parse_karachi.stations_by_district().items():
        circles = {}
        for st in sts:
            sho = next((c for c in st["contacts"] if c[0] == "SHO"), None)
            name = " ".join(st["name"].replace("Police Station", "").replace("police station", "").split()) or st["name"]
            circles.setdefault((st["sub"] or "").title() + " Sub-Division" if st["sub"] else "", []).append((name, sho[2] if sho else ""))
        out[did] = ("Karachi Police", "https://karachipolice.gov.pk/services/police-stations-in-karachi/", sorted(circles.items()))
    return out


def clean(s):
    return " ".join(str(s).replace(";", ",").replace("|", "/").split())


def main():
    src = parsed_sources()
    lines = open(TXT, encoding="utf-8").read().split("\n")
    out, i, done = [], 0, set()
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("## "):
            did = ln[3:].split("|")[0].strip()
            block = [ln]
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                block.append(lines[i])
                i += 1
            if did in src:
                name, url, circles = src[did]
                keep = [b for b in block[1:] if b.startswith(("office:", "link:"))]
                keep = [k for k in keep if url.lower() not in k.lower()]
                out.append(f"## {did} | {name} | {url}")
                out.extend(keep)
                for c, sts in circles:
                    out.append(f"- {clean(c)}: " + "; ".join(f"{clean(n)}|{clean(p)}" for n, p in sts))
                out.append("")
                done.add(did)
            else:
                out.extend(block)
            continue
        out.append(ln)
        i += 1
    while out and out[-1] == "":
        out.pop()
    for did in sorted(set(src) - done):  # districts with no block yet
        name, url, circles = src[did]
        out += ["", f"## {did} | {name} | {url}"] + [f"- {clean(c)}: " + "; ".join(f"{clean(n)}|{clean(p)}" for n, p in s) for c, s in circles]
    open(TXT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"updated {len(done)} districts, added {len(set(src) - done)}")


if __name__ == "__main__":
    main()
