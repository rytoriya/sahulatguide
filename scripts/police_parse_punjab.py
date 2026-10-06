#!/usr/bin/env python3
"""Read every Punjab Police "SDPOs and Police Stations" directory page saved by the data job
(data/police/raw/pages.tar.gz) and return {district_id: [(circle, [(station, phone), …]), …]}.

The pages are tables laid out by column: each column is a circle (sub-division) with its SDPO,
then station names and phone numbers going down, either in alternating rows or in one cell.
"""
import html
import re
import tarfile
from html.parser import HTMLParser

# directory page name -> site district id
PAGE_DISTRICT = {
    "lahoredirectory": "pb-lahore", "rawalpindidirectory": "pb-rawalpindi", "faisalabaddirectory": "pb-faisalabad",
    "gujranwaladirectory": "pb-gujranwala", "multandirectory": "pb-multan", "dgkhan": "pb-dera-ghazi-khan",
    "nankana": "pb-nankana-sahib", "toba_tek_singh": "pb-toba-tek-singh", "mandi_bahauddin": "pb-mandi-bahauddin",
    "rahim_yar_khan": "pb-rahim-yar-khan",
}
PHONE = re.compile(r"^[\d\s\-–/,()+.]*\d{3}[\d\s\-–/,()+.]*$")
OFFICER = re.compile(r"(?i)^(sdpo|s\.?d\.?p\.?o|sp|ssp|dsp|asp|sho|dpo|cpo|ccpo|rpo|in-?charge)\b|\bSP\b|\(operation|\(investigation|\bsp\s*\(")
HEADING = re.compile(r"(?i)\b(division|circle|sub-?division|zone)\b")


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables.append([])
        elif tag == "tr" and self.tables:
            self.row = []
            self.tables[-1].append(self.row)
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
            self.row.append(self.cell)
        elif tag == "br" and self.cell is not None:
            self.cell.append("\n")

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self.cell = None
        elif tag in ("p", "div") and self.cell is not None:
            self.cell.append("\n")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def lines(cell):
    t = html.unescape("".join(cell)).replace("\xa0", " ")
    return [" ".join(x.split()) for x in t.split("\n") if x.strip()]


def district_of(member):
    base = member.rsplit("/", 1)[-1].replace(".html", "").lower()
    if base in PAGE_DISTRICT:
        return PAGE_DISTRICT[base]
    base = re.sub(r"_?directory$", "", base)
    return PAGE_DISTRICT.get(base, "pb-" + base.replace("_", "-"))


def parse_page(text):
    p = Tables()
    p.feed(text)
    circles = {}  # (division, circle) -> list
    order = []
    for table in p.tables:
        ncol = max((len(r) for r in table), default=0)
        col_circle = [""] * ncol
        division = ""
        pending = [None] * ncol  # station name waiting for its phone, per column
        skip_phone = [False] * ncol
        for row in table:
            cells = [lines(c) for c in row]
            nonempty = [c for c in cells if c]
            # a row whose only text is "... Division" sets the division for every column
            if len(nonempty) == 1 and re.search(r"(?i)division", nonempty[0][0]) and not PHONE.match(nonempty[0][0]):
                division = nonempty[0][0]
                col_circle = [""] * ncol
                pending = [None] * ncol
                continue
            for ci, ls in enumerate(cells):
                for ln in ls:
                    if PHONE.match(ln):
                        if pending[ci]:
                            k = (division, col_circle[ci])
                            circles.setdefault(k, [])
                            if k not in order:
                                order.append(k)
                            circles[k][-1] = (circles[k][-1][0], ln)
                            pending[ci] = None
                        skip_phone[ci] = False
                        continue
                    if HEADING.search(ln) and len(ln) < 60:
                        col_circle[ci] = ln
                        pending[ci] = None
                        continue
                    if OFFICER.search(ln) or len(ln) > 60 or ln.lower().startswith(("source", "police station", "s.no")):
                        if pending[ci] and OFFICER.search(ln) and re.match(r"(?i)^s\.?d\.?p\.?o", ln):
                            # the name just above an "SDPO" line is a circle heading, not a station
                            k = (division, col_circle[ci])
                            if circles.get(k) and circles[k][-1][0] == pending[ci] and not circles[k][-1][1]:
                                circles[k].pop()
                            col_circle[ci] = pending[ci] if HEADING.search(pending[ci]) else pending[ci] + " Circle"
                        pending[ci] = None
                        continue
                    k = (division, col_circle[ci])
                    circles.setdefault(k, [])
                    if k not in order:
                        order.append(k)
                    circles[k].append((ln, ""))
                    pending[ci] = ln
    heads = {(c or "").lower().replace(" circle", "").strip() for _, c in order}
    out = []
    for k in order:
        div, circ = k
        label = circ or div
        if div and circ and div.lower() not in circ.lower():
            label = circ
        label = re.sub(r"(?i)^sdpo\s+", "", label)
        # drop circle names that were read as stations (no phone, same name as a circle)
        sts = [(n, ph) for n, ph in circles[k] if n and not (not ph and n.lower().strip() in heads)]
        if sts:
            out.append((label, sts))
    return out


def parse_all(tar_path):
    res = {}
    with tarfile.open(tar_path) as tar:
        for m in tar.getmembers():
            if m.isfile() and "punjabpolice.gov.pk" in m.name and "irectory" in m.name:
                res[district_of(m.name)] = parse_page(tar.extractfile(m).read().decode("utf-8", "replace"))
    return res


if __name__ == "__main__":
    import os
    import sys
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    r = parse_all(os.path.join(ROOT, "data", "police", "raw", "pages.tar.gz"))
    total = 0
    for d, circles in sorted(r.items()):
        n = sum(len(s) for _, s in circles)
        total += n
        print(f"{d:28} {len(circles):3} circles {n:4} stations")
        if len(sys.argv) > 1 and d == sys.argv[1]:
            for c, s in circles:
                print("   ", c, "::", "; ".join(f"{a}|{b}" for a, b in s))
    print("total", total)
