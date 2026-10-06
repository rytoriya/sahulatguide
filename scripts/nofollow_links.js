#!/usr/bin/env node
/*
 * Mark every external link written in the site's HTML with rel="nofollow".
 *
 * Looks at each <a> tag whose href starts with http://, https:// or // and points to another
 * website, and adds "nofollow" to its rel (keeping noopener etc.). Links to sahulatguide.* are
 * left alone. Safe to run again. Links that page scripts build at runtime are handled by
 * links.js, which every page loads through the shared footer.
 *
 * Netlify runs this on every deploy (netlify.toml).
 * Usage: node scripts/nofollow_links.js
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const OWN = /(^|\.)sahulatguide\.(netlify\.app|pk)$/i;

function isExternal(href) {
  const m = href.match(/^(?:https?:)?\/\/([^/?#:]+)/i);
  return !!m && !OWN.test(m[1]);
}

function mark(tag) {
  const h = tag.match(/\shref=(["'])(.*?)\1/i);
  if (!h || !isExternal(h[2])) return tag;
  const r = tag.match(/\srel=(["'])(.*?)\1/i);
  if (r) {
    const rel = r[2].split(/\s+/).filter(Boolean);
    if (rel.includes("nofollow")) return tag;
    return tag.replace(r[0], ` rel=${r[1]}${["nofollow", ...rel].join(" ")}${r[1]}`);
  }
  return tag.replace(/^<a\b/i, '<a rel="nofollow"');
}

// Hand-made pages and partials; generated route copies are made from index.html afterwards.
const files = ["index.html", "partials/header.html", "partials/footer.html"];
for (const d of fs.readdirSync(ROOT, { withFileTypes: true })) {
  if (!d.isDirectory() || d.name.startsWith(".")) continue;
  if (fs.existsSync(path.join(ROOT, d.name, ".generated"))) continue;
  if (fs.existsSync(path.join(ROOT, d.name, "index.html"))) files.push(`${d.name}/index.html`);
}

let total = 0;
for (const f of files) {
  const p = path.join(ROOT, f);
  if (!fs.existsSync(p)) continue;
  const src = fs.readFileSync(p, "utf8");
  let n = 0;
  const out = src.replace(/<a\b[^>]*>/gi, (tag) => { const t = mark(tag); if (t !== tag) n++; return t; });
  if (n) { fs.writeFileSync(p, out); console.log(`${f}: ${n} external links marked nofollow`); total += n; }
}
console.log(`Done: ${total} links changed.`);
