#!/usr/bin/env node
/*
 * Give every tab and guide of the main app its own real page.
 *
 * index.html is one app with many views (categories, guides, helplines, calculators…).
 * This script copies it to one folder per view, e.g.
 *   services/identity/cnic-renewal/index.html
 * and sets that page's own <title>, description, canonical link and social-preview tags,
 * so Google can list each guide and WhatsApp/Facebook show the right preview.
 * The app reads the address when it loads and opens the matching view.
 * It also writes sitemap.xml.
 *
 * Netlify runs this on every deploy (netlify.toml), so the pages always match index.html.
 * The generated folders are not committed (.gitignore).
 *
 * Usage: node scripts/build_routes.js
 * Address rules must match pathFor() / metaFor() in index.html.
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

// Return the source of `const NAME = <literal>` (array or object), skipping strings.
function grab(src, name) {
  const start = src.indexOf("const " + name + " = ");
  if (start < 0) throw new Error("Not found in index.html: const " + name);
  let j = src.slice(start).search(/[\[{"]/) + start;
  if (src[j] === '"') return src.slice(j, src.indexOf('"', j + 1) + 1); // a plain string constant
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
const clip = (t, n) => (t.length > n ? t.slice(0, n).replace(/\s+\S*$/, "") + "…" : t);
const escAttr = (t) => String(t).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const escText = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;");

const home = read("index.html");
const GROUPS = evalLiteral(grab(home, "GROUPS"));
const S = evalLiteral(grab(home, "S"));
const SEO = evalLiteral(grab(home, "SEO"));
const PAGE_SLUG = evalLiteral(grab(home, "PAGE_SLUG"));
const PAGE_META = evalLiteral(grab(home, "PAGE_META"));
const SITE_URL = evalLiteral(grab(home, "SITE_URL"));

// Same rules as metaFor() in index.html.
const routes = [];
routes.push({ path: "/services/", ...PAGE_META.all });
for (const [k, g] of Object.entries(GROUPS)) {
  routes.push({ path: `/services/${k}/`, t: g.name + ": guides and how to apply | Sahulat Guide", d: g.desc + " Step-by-step guides with documents, fees and where to apply." });
}
for (const s of S) {
  const m = SEO[s.id];
  routes.push({ path: `/services/${s.grp}/${s.id}/`, t: (m ? m.t : s.name + ": steps, documents and fees") + " | Sahulat Guide", d: m ? m.d : clip(s.summary, 158) });
}
for (const [k, slug] of Object.entries(PAGE_SLUG)) routes.push({ path: `/${slug}/`, ...PAGE_META[k] });

// Never overwrite a hand-made page.
const generatedTop = new Set(routes.map((r) => r.path.split("/")[1]));
for (const top of generatedTop) {
  const marker = path.join(ROOT, top, ".generated");
  if (fs.existsSync(path.join(ROOT, top)) && !fs.existsSync(marker)) {
    throw new Error(`Folder "${top}/" already exists and was not made by this script. Rename the route in PAGE_SLUG.`);
  }
}

function pageFor(r) {
  const url = SITE_URL + r.path;
  let h = home;
  const swap = (re, to) => {
    if (!re.test(h)) throw new Error("Tag not found in index.html: " + re);
    h = h.replace(re, to);
  };
  swap(/<title>[^<]*<\/title>/, `<title>${escText(r.t)}</title>`);
  swap(/<meta name="description" content="[^"]*">/, `<meta name="description" content="${escAttr(r.d)}">`);
  swap(/<link rel="canonical" href="[^"]*">/, `<link rel="canonical" href="${url}">`);
  swap(/<meta property="og:title" content="[^"]*">/, `<meta property="og:title" content="${escAttr(r.t)}">`);
  swap(/<meta property="og:description" content="[^"]*">/, `<meta property="og:description" content="${escAttr(r.d)}">`);
  swap(/<meta property="og:url" content="[^"]*">/, `<meta property="og:url" content="${url}">`);
  return h;
}

// Clear the previous output, then write every page.
for (const top of generatedTop) fs.rmSync(path.join(ROOT, top), { recursive: true, force: true });
for (const r of routes) {
  const dir = path.join(ROOT, r.path);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "index.html"), pageFor(r));
}
for (const top of generatedTop) fs.writeFileSync(path.join(ROOT, top, ".generated"), "Made by scripts/build_routes.js. Do not edit; edit index.html.\n");

// sitemap.xml: home, every generated page and the tool pages that have their own folder.
const SKIP_TOOLS = new Set(["account"]); // sign-in page, not useful in search
const toolDirs = fs.readdirSync(ROOT, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !d.name.startsWith(".") && !generatedTop.has(d.name) && !SKIP_TOOLS.has(d.name))
  .filter((d) => fs.existsSync(path.join(ROOT, d.name, "index.html")))
  .map((d) => `/${d.name}/`);
const urls = ["/", ...routes.map((r) => r.path), ...toolDirs.sort()];
fs.writeFileSync(path.join(ROOT, "sitemap.xml"),
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  urls.map((u) => `  <url><loc>${SITE_URL}${u}</loc></url>`).join("\n") + "\n</urlset>\n");

console.log(`Wrote ${routes.length} pages and sitemap.xml (${urls.length} addresses).`);
