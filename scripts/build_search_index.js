#!/usr/bin/env node
/*
 * Build search-index.js, the data behind the site-wide search (search.js).
 *
 * Reads the guide data in index.html, the directory data in admin-units/index.html
 * and the section headings of the train and parcel guides, and writes
 * search-index.js at the site root.
 *
 * Usage: node scripts/build_search_index.js
 * Run it again whenever guides, tools or the directory change.
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

// Return the source of `const NAME = <literal>` (array or object), skipping strings.
function grab(src, name) {
  const start = src.indexOf("const " + name + " = ");
  if (start < 0) throw new Error("Not found: " + name);
  let j = src.slice(start).search(/[\[{]/) + start;
  const open = j;
  let depth = 0, quote = null;
  for (; j < src.length; j++) {
    const c = src[j];
    if (quote) { if (c === "\\") { j++; continue; } if (c === quote) quote = null; continue; }
    if (c === '"' || c === "'" || c === "`") { quote = c; continue; }
    if (c === "[" || c === "{") depth++;
    else if (c === "]" || c === "}") { depth--; if (!depth) break; }
  }
  return src.slice(open, j + 1);
}
const evalLiteral = (code) => Function('"use strict";return (' + code + ")")();
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const clip = (s, n) => (s.length > n ? s.slice(0, n).replace(/\s+\S*$/, "") + "…" : s);

const items = []; // [type, title, urdu, subtitle, url, extra keywords]

/* ---- Service guides (index.html) ---- */
const home = read("index.html");
const GROUPS = evalLiteral(grab(home, "GROUPS"));
const S = evalLiteral(grab(home, "S"));
const REGION = { national: "Nationwide", punjab: "Punjab", sindh: "Sindh", kp: "KP", balochistan: "Balochistan", ict: "Islamabad", ajkgb: "AJK & GB" };
for (const s of S) {
  const g = GROUPS[s.grp];
  const sub = (g.subs.find((x) => x[0] === s.sub) || [, ""])[1];
  const region = s.region.map((r) => REGION[r] || r).join(" · ");
  items.push(["Service", s.name, s.ur || "", `${g.name} · ${region}`, "#" + s.id,
    [s.by, sub, g.name, clip(s.summary, 160)].join(" ")]);
}
for (const [k, g] of Object.entries(GROUPS)) {
  items.push(["Category", g.name, "", g.desc, "#" + k, g.subs.map((x) => x[1]).join(" ")]);
}
items.push(["Category", "Emergency helplines", "ایمرجنسی", "Police, Rescue 1122, ambulance and other helplines", "#emergency", "emergency helpline 15 1122 ambulance fire"]);
items.push(["Category", "Calculators", "", "Scheme finder and loan instalment calculator", "#tools", "calculator emi loan instalment scheme finder"]);
items.push(["Category", "More services (official portals)", "", "Links to official government websites", "#portals", "portal website directory links"]);

/* ---- Tool pages ---- */
const TOOLS = [
  ["Passport services", "پاسپورٹ", "Nearest passport office, fee calculator, timings, renewal, visa help", "passport/", "passport office fee dgip visa renewal"],
  ["Road route planner", "", "Routes, distances and travel times between Pakistani cities", "route-planner/", "road route map distance travel motorway highway"],
  ["Train finder", "ٹرین", "Pakistan Railways timetables and estimated fares", "trains/", "train railway timetable fare ticket"],
  ["Parcel guide", "پارسل", "Courier prices and rules: TCS, Leopards, M&P, Pakistan Post", "parcels/", "parcel courier delivery tcs leopards post"],
  ["Pay school & university fees", "فیس آن لائن", "Pay fee vouchers with 1Bill or Kuickpay; 500+ institutions", "fees/", "fee fees voucher challan school college university 1bill kuickpay pay online"],
  ["My details (sign in)", "میری معلومات", "Save your name, mobile, CNIC and address once; copy them into any form", "account/", "account sign in login sign up register profile my details cnic save"],
  ["Police, Rescue 1122 & fire near you", "قریبی تھانہ", "City-wise police stations with official numbers; Rescue 1122 and fire stations on a map", "emergency/", "police station thana nearest map rescue 1122 fire brigade ambulance emergency"],
  ["Districts & Union Councils", "اضلاع اور یونین کونسلز", "Every division, district and tehsil in Pakistan, and who to call", "admin-units/", "district tehsil union council division province directory"],
];
for (const [t, ur, d, u, k] of TOOLS) items.push(["Tool", t, ur, d, u, k]);

/* ---- Sections of the Markdown guides ---- */
for (const [dir, label] of [["trains", "Train finder"], ["parcels", "Parcel guide"]]) {
  const html = read(dir + "/index.html");
  for (const m of html.matchAll(/<h2 id="([^"]+)">([\s\S]*?)<\/h2>/g)) {
    if (m[1] === "contents") continue;
    const title = m[2].replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").replace(/&#39;/g, "'").replace(/&quot;/g, '"').trim();
    items.push(["Section", title, "", label, `${dir}/#${m[1]}`, label]);
  }
}

/* ---- City emergency pages ---- */
const emg = read("emergency/index.html");
for (const m of emg.matchAll(/\{id:"([a-z]+)",name:"([^"]+)",prov:"([^"]+)"/g)) {
  items.push(["Tool", `Police stations in ${m[2]}`, "", `Police, Rescue 1122 and fire stations on a map · ${m[3]}`, `emergency/?city=${m[1]}`, "police station thana rescue 1122 fire brigade near me"]);
}

/* ---- Institutions that take fees online (fees page) ---- */
const feeSrc = read("fees/index.html");
const INST = evalLiteral(grab(feeSrc, "INST"));
for (const [name, type] of INST) {
  items.push(["Fee", name, "", `Pay fees online with 1Bill · ${type}`, `fees/?q=${encodeURIComponent(name)}`, "fee voucher pay online 1bill"]);
}

/* ---- Divisions, districts and tehsils (admin-units) ---- */
const dirSrc = read("admin-units/index.html");
const PROV = evalLiteral(grab(dirSrc, "PROV"));
for (const p of PROV) {
  items.push(["Place", p.name, p.ur, "Province / territory", `admin-units/?p=${p.id}`, "province"]);
  for (const [dn, dur, list] of p.divs) {
    const divLabel = dn + (dn.includes("Territory") ? "" : " Division");
    items.push(["Place", divLabel, dur, p.name, `admin-units/?p=${p.id}`, "division"]);
    for (const [line] of list) {
      const parts = line.split("|");
      const [name, ur, hq] = parts;
      const id = p.id + "-" + slug(name);
      items.push(["Place", name + " District", ur, `${dn} · ${p.name} · HQ ${hq}`, `admin-units/?d=${id}`, "district"]);
      for (const t of parts.slice(3)) {
        const tn = t.split(":")[0];
        const word = p.tehsilWord === "taluka" ? "Taluka" : "Tehsil";
        items.push(["Place", `${tn} ${word}`, "", `${name} District · ${p.name}`, `admin-units/?d=${id}&t=${slug(tn)}`, word.toLowerCase()]);
      }
    }
  }
}

const out = "/* Generated by scripts/build_search_index.js — do not edit by hand. */\n" +
  "window.SG_INDEX=" + JSON.stringify(items) + ";\n";
fs.writeFileSync(path.join(ROOT, "search-index.js"), out);
const counts = items.reduce((a, i) => ((a[i[0]] = (a[i[0]] || 0) + 1), a), {});
console.log("search-index.js:", items.length, "entries", counts);
