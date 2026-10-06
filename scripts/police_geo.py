"""Place points in Pakistan's districts (shared by the police data scripts).

Uses geoBoundaries tehsil (ADM3), district (ADM2) and province (ADM1) boundaries in
data/police/boundaries/ and the site's own district list (with tehsils) from the
Districts & Union Councils page, so new districts are handled through their tehsils.
"""
import difflib
import json
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BND = os.path.join(ROOT, "data", "police", "boundaries")

# Boundary names (old Karachi towns and cantonments, spelling variants) -> a tehsil or district on the site.
ALIAS = {
    "clifton cantonment": "Saddar", "karachi cantonment": "Saddar", "manora cantonment": "Keamari",
    "faisal cantonment": "Shah Faisal", "korangi creek cantonment": "Korangi", "malir cantonment": "Airport",
    "malir": "Airport", "n.nazimabad town": "North Nazimabad", "kiamari town": "Keamari", "liaqatabad town": "Liaquatabad",
    "site town": "SITE", "baldia town": "Baldia", "bin qasim town": "Bin Qasim", "gadap town": "Gadap",
}

PROV_OF_ADM1 = {"Punjab": "pb", "Sindh": "sd", "Khyber Pakhtunkhwa": "kp", "Balochistan": "bl",
                "Islamabad Capital Territory": "ict", "Azad Kashmir": "ajk", "Gilgit-Baltistan": "gb"}


def norm(s):
    s = str(s or "").lower().replace("_", " ")
    s = re.sub(r"\b(tehsil|taluka|taluk|talukas|sub[- ]?division|sub|subdivision|district|agency|frontier region|fr|town|cantonment)\b", " ", s)
    s = s.replace("dera ", "d ").replace("d.i.", "d i ").replace("d.g.", "d g ")
    return re.sub(r"[^a-z]", "", s)


def districts():
    js = r"""
const fs=require('fs');const s=fs.readFileSync(process.argv[1],'utf8');
const i=s.indexOf('const PROV = ');let j=s.indexOf('[',i),d=0,q=null;const o=j;
for(;j<s.length;j++){const c=s[j];if(q){if(c=='\\'){j++;continue}if(c==q)q=null;continue}
 if(c=='"'||c=="'"||c=='`'){q=c;continue}if(c=='['||c=='{')d++;else if(c==']'||c=='}'){d--;if(!d)break}}
const P=Function('return ('+s.slice(o,j+1)+')')();const slug=x=>x.toLowerCase().replace(/[^a-z0-9]+/g,'-');
const out=[];for(const p of P)for(const dv of p.divs)for(const [line] of dv[2]){const parts=line.split('|');
 out.push({id:p.id+'-'+slug(parts[0]),prov:p.id,name:parts[0],ur:parts[1],hq:parts[2],div:dv[0],tehsils:parts.slice(3).map(t=>t.split(':')[0])})}
process.stdout.write(JSON.stringify(out));"""
    out = subprocess.run(["node", "-e", js, os.path.join(ROOT, "admin-units", "index.html")],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# ---------------------------------------------------------------- geometry
def _rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def _inside(lon, lat, poly):
    """poly = [outer ring, holes…]"""
    def in_ring(r):
        c = False
        for i in range(len(r)):
            x1, y1 = r[i][0], r[i][1]
            x2, y2 = r[i - 1][0], r[i - 1][1]
            if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1 + 1e-15) + x1:
                c = not c
        return c
    return in_ring(poly[0]) and not any(in_ring(h) for h in poly[1:])


class Layer:
    def __init__(self, path):
        self.feats = []
        for f in json.load(open(path, encoding="utf-8"))["features"]:
            polys = _rings(f["geometry"])
            xs = [p[0] for poly in polys for p in poly[0]]
            ys = [p[1] for poly in polys for p in poly[0]]
            self.feats.append((f["properties"]["shapeName"], polys, (min(xs), min(ys), max(xs), max(ys))))

    def find(self, lat, lon):
        for name, polys, (x0, y0, x1, y1) in self.feats:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and any(_inside(lon, lat, p) for p in polys):
                return name
        return None


class Locator:
    def __init__(self):
        self.adm1 = Layer(os.path.join(BND, "pak-ADM1.geojson"))
        self.adm2 = Layer(os.path.join(BND, "pak-ADM2.geojson"))
        self.adm3 = Layer(os.path.join(BND, "pak-ADM3.geojson"))
        self.D = districts()
        self.by_tehsil, self.by_name = {}, {}
        for d in self.D:
            self.by_name.setdefault((d["prov"], norm(d["name"])), d)
            for t in d["tehsils"]:
                self.by_tehsil.setdefault((d["prov"], norm(t)), d)
            self.by_tehsil.setdefault((d["prov"], norm(d["hq"])), d)

    def _match(self, table, prov, name, cutoff):
        key = (prov, norm(name))
        if key in table:
            return table[key]
        keys = [k[1] for k in table if k[0] == prov]
        m = difflib.get_close_matches(norm(name), keys, n=1, cutoff=cutoff)
        return table[(prov, m[0])] if m else None

    def district(self, lat, lon):
        """Return (district dict or None, province id or None)."""
        a1 = self.adm1.find(lat, lon)
        prov = PROV_OF_ADM1.get(a1)
        if not prov:
            return None, None
        t = self.adm3.find(lat, lon)
        if t:
            t = ALIAS.get(t.lower(), t)
            d = self._match(self.by_tehsil, prov, t, 0.84)
            if d:
                return d, prov
        a2 = self.adm2.find(lat, lon)
        if a2:
            d = self._match(self.by_name, prov, a2, 0.8) or self._match(self.by_tehsil, prov, a2, 0.84)
            if d:
                return d, prov
        if prov in ("ict",):
            return next(x for x in self.D if x["prov"] == "ict"), prov
        return None, prov
