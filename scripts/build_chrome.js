#!/usr/bin/env node
/*
 * Put the same site header, tab strip and footer on every page.
 *
 * The header and footer live in one place: partials/header.html and partials/footer.html
 * (styles in site.css, classes prefixed sgc-). This script fills in the tab list and the
 * footer's service links from the data in index.html (TABS, GROUPS, ICON), then writes the
 * result into every page between these markers:
 *   <!-- sg:header --> … <!-- /sg:header -->
 *   <!-- sg:footer --> … <!-- /sg:footer -->
 * Pages that do not have the markers yet get them (their old header is replaced).
 * The current page's tab is marked aria-current="page".
 *
 * Netlify runs this on every deploy (netlify.toml) before build_routes.js.
 * Usage: node scripts/build_chrome.js
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

// Pages that keep their own full-screen layout and get no site header/footer.
const SKIP = new Set(["route-planner"]);

// Return the source of `const NAME = <literal>` (array or object), skipping strings.
function grab(src, name) {
  const start = src.indexOf("const " + name + " = ");
  if (start < 0) throw new Error("Not found in index.html: const " + name);
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
const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

const home = read("index.html");
const GROUPS = Function('"use strict";return (' + grab(home, "GROUPS") + ")")();
const ICON = Function('"use strict";return (' + grab(home, "ICON") + ")")();
const TABS = Function("GROUPS", '"use strict";return (' + grab(home, "TABS") + ")")(GROUPS);

// Same addresses as pathFor() in index.html.
const PAGE_PATH = { home: "/", emergency: "/helplines/", all: "/services/", tools: "/calculators/", portals: "/portals/", contact: "/contact/" };
const hrefFor = (k) => PAGE_PATH[k] || (GROUPS[k] ? `/services/${k}/` : "/");

const LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" style="fill:var(--sgc-accent)"/>' +
  '<path d="M18 52V30a14 14 0 0 1 28 0v22" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>' +
  '<path d="M24 36l6 6 11-12" fill="none" style="stroke:var(--sgc-sun)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>' +
  '<circle cx="47" cy="15" r="4" style="fill:var(--sgc-sun)"/></svg>';

const tabs = TABS.map(([k, label, url, ic]) => {
  if (url) return `<a class="sgc-tab sgc-tool" href="/${url}">${ICON[ic] || ""}${esc(label)}</a>`;
  const cls = "sgc-tab" + (k === "emergency" ? " sgc-red" : "");
  return `<a class="${cls}" href="${hrefFor(k)}" data-go="${k}">${k === "home" ? ICON.home : ""}${esc(label)}</a>`;
}).join("");
const services = Object.entries(GROUPS).map(([k, g]) => `<a href="/services/${k}/" data-go="${k}">${esc(g.name)}</a>`).join("");

const HEADER = read("partials/header.html").trim().replace(/\{\{LOGO\}\}/g, LOGO).replace("{{TABS}}", tabs);
const FOOTER = read("partials/footer.html").trim().replace(/\{\{LOGO\}\}/g, LOGO).replace("{{SERVICES}}", services);

const H0 = "<!-- sg:header -->", H1 = "<!-- /sg:header -->", F0 = "<!-- sg:footer -->", F1 = "<!-- /sg:footer -->";

function setActive(html, folder) {
  if (!folder) return html.replace('href="/" data-go="home">', 'href="/" data-go="home" aria-current="page">'); // home page
  return html.replace(`class="sgc-tab sgc-tool" href="/${folder}/">`, `class="sgc-tab sgc-tool" href="/${folder}/" aria-current="page">`);
}

function stamp(file, folder) {
  let h = read(file);
  const header = `${H0}\n${setActive(HEADER, folder)}\n${H1}`;
  const footer = `${F0}\n${FOOTER}\n${F1}`;

  // Header: refresh between markers, or replace the page's old header the first time.
  if (h.includes(H0)) h = h.slice(0, h.indexOf(H0)) + header + h.slice(h.indexOf(H1) + H1.length);
  else if (!folder) {
    const a = h.indexOf('<div class="notice">'), b = h.indexOf("</nav></div></div>", a);
    if (a < 0 || b < 0) throw new Error("index.html: old header not found");
    h = h.slice(0, a) + header + h.slice(b + "</nav></div></div>".length);
  } else if (/<header class="site">[\s\S]*?<\/header>/.test(h)) h = h.replace(/<header class="site">[\s\S]*?<\/header>/, header);
  else if (/<header>[\s\S]*?<\/header>/.test(h)) h = h.replace(/<header>[\s\S]*?<\/header>/, header);
  else h = h.replace(/<body[^>]*>/, (m) => m + "\n" + header);

  // Footer: refresh between markers, or add it after the page's own content the first time.
  if (h.includes(F0)) h = h.slice(0, h.indexOf(F0)) + footer + h.slice(h.indexOf(F1) + F1.length);
  else if (!folder) h = h.replace(/<footer class="site">[\s\S]*?<\/footer>/, footer);
  else {
    const m = h.indexOf("</main>");
    if (m < 0) throw new Error(file + ": no </main>");
    const after = h.slice(m);
    const own = after.match(/^<\/main>\s*<footer[\s\S]*?<\/footer>/); // the page's own note footer, kept
    const at = m + (own ? own[0].length : "</main>".length);
    h = h.slice(0, at) + "\n" + footer + h.slice(at);
  }
  fs.writeFileSync(path.join(ROOT, file), h);
}

stamp("index.html", "");
const pages = ["index.html"];
for (const d of fs.readdirSync(ROOT, { withFileTypes: true })) {
  if (!d.isDirectory() || d.name.startsWith(".") || SKIP.has(d.name)) continue;
  if (fs.existsSync(path.join(ROOT, d.name, ".generated"))) continue; // copies made by build_routes.js
  if (!fs.existsSync(path.join(ROOT, d.name, "index.html"))) continue;
  stamp(`${d.name}/index.html`, d.name);
  pages.push(`${d.name}/index.html`);
}
console.log(`Header and footer written into ${pages.length} pages: ${pages.join(", ")}`);
