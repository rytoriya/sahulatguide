#!/usr/bin/env python3
"""Read Islamabad Police's station locator (api-loc.php, saved by the data job's targets step).

Returns {"stations": [...], "centres": [...], "offices": [...]}, each item
{"name", "addr", "phone", "ll": [lat, lon], "services", "hours"}.
"""
import json
import os
import tarfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse(tar_path=os.path.join(ROOT, "data", "police", "raw", "targets.tar.gz")):
    out = {"stations": [], "centres": [], "offices": []}
    if not os.path.exists(tar_path):
        return out
    with tarfile.open(tar_path) as tar:
        m = next((m for m in tar.getmembers() if m.name.endswith("islamabadpolice.gov.pk__api-loc.php")), None)
        if not m:
            return out
        rows = json.loads(tar.extractfile(m).read().decode("utf-8", "replace"))
    for r in rows:
        name = r.get("name", "").strip()
        if r.get("type") == "PS" and name.lower().startswith("ps "):
            name = name[3:].strip()
        addr = (r.get("address") or "").strip()
        if addr.upper() in ("N/A", "0") or addr.lower().startswith("in ") and "police station" in addr.lower():
            addr = ""
        item = {"name": name, "addr": addr, "phone": (r.get("contact") or "").strip(),
                "ll": [round(float(r["lat"]), 6), round(float(r["lng"]), 6)],
                "services": "" if str(r.get("services")) == "0" else (r.get("services") or ""), "hours": r.get("hours") or ""}
        out[{"PS": "stations", "PKM": "centres"}.get(r.get("type"), "offices")].append(item)
    return out


if __name__ == "__main__":
    d = parse()
    print({k: len(v) for k, v in d.items()})
