/*
 * Sahulat Guide site-wide search.
 * Include on any page with:  <script src="search.js" defer></script>  (adjust the path)
 * Put <span data-sg-search></span> where the Search button should go
 * (add data-sg-search="on-dark" on dark backgrounds, "wide" for a full-width search field). Without a slot, a floating
 * button is added. Shortcuts: "/" or Ctrl/Cmd+K. Data comes from search-index.js,
 * built by scripts/build_search_index.js.
 */
(function () {
  "use strict";
  if (window.__sgSearch) return;
  window.__sgSearch = true;

  var me = document.currentScript || document.querySelector('script[src*="search.js"]');
  var BASE = new URL(".", me ? me.src : location.href).href;
  var GROUP_ORDER = ["Service", "Category", "Tool", "University", "Section", "Police", "Fee", "Place"];
  var GROUP_LABEL = { Service: "Services", Category: "Categories", Tool: "Tools", Section: "Guide sections", University: "Universities & entry tests", Fee: "Pay fees online", Police: "Police stations", Place: "Districts & tehsils" };
  var ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/></svg>';

  /* ---------- styles (scoped, themed) ---------- */
  var css = [
    ".sg-root{--sg-bg:#ffffff;--sg-ink:#17232e;--sg-muted:#5a6872;--sg-line:#dde3e1;--sg-accent:#0d6b52;--sg-soft:#e2f1ec;--sg-shade:rgba(10,20,18,.45)}",
    "@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .sg-root{--sg-bg:#172129;--sg-ink:#e6ecea;--sg-muted:#9aa8ad;--sg-line:#2b3a43;--sg-accent:#4fc39d;--sg-soft:#163a31;--sg-shade:rgba(0,0,0,.6)}}",
    ":root[data-theme=dark] .sg-root{--sg-bg:#172129;--sg-ink:#e6ecea;--sg-muted:#9aa8ad;--sg-line:#2b3a43;--sg-accent:#4fc39d;--sg-soft:#163a31;--sg-shade:rgba(0,0,0,.6)}",
    ".sg-btn{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:8px 14px;border-radius:999px;border:1px solid var(--sg-line);background:var(--sg-bg);color:var(--sg-ink);font-family:inherit;font-weight:600;font-size:14px;line-height:1;cursor:pointer;white-space:nowrap}",
    ".sg-btn:hover{border-color:var(--sg-accent)}",
    ".sg-btn:focus-visible,.sg-x:focus-visible,.sg-opt:focus-visible{outline:3px solid var(--sg-accent);outline-offset:2px}",
    ".sg-btn svg{width:18px;height:18px;flex:none}",
    ".sg-btn kbd{font-weight:700;font-size:11px;line-height:1;font-family:inherit;color:var(--sg-muted);border:1px solid var(--sg-line);border-radius:5px;padding:3px 5px}",
    ".sg-btn.sg-dark{background:rgba(255,255,255,.16);border-color:rgba(255,255,255,.35);color:#fff;backdrop-filter:blur(8px)}",
    ".sg-btn.sg-dark kbd{color:rgba(255,255,255,.8);border-color:rgba(255,255,255,.4)}",
    ".sg-btn.sg-float{position:fixed;left:16px;bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:9998;box-shadow:0 6px 20px rgba(0,0,0,.18)}",
    "@media (max-width:560px){.sg-btn kbd{display:none}.sg-btn.sg-compact .sg-l{display:none}.sg-btn.sg-compact{padding:8px 10px}}",
    ".sg-btn.sg-wide{width:100%;min-height:46px;padding:11px 16px;color:var(--sg-muted);font-weight:500;font-size:15px;box-shadow:0 1px 2px rgba(13,60,48,.05),0 2px 6px -2px rgba(13,60,48,.06);text-align:left}",
    ".sg-btn.sg-wide .sg-l{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.5;padding-block:1px}",
    ".sg-btn.sg-wide svg{color:var(--sg-muted)}",
    ".sg-ov{position:fixed;inset:0;z-index:9999;background:var(--sg-shade);display:flex;justify-content:center;align-items:flex-start;padding:max(8vh,16px) 12px 16px}",
    ".sg-ov[hidden]{display:none}",
    ".sg-panel{width:100%;max-width:660px;max-height:min(78vh,720px);display:flex;flex-direction:column;background:var(--sg-bg);color:var(--sg-ink);border:1px solid var(--sg-line);border-radius:18px;box-shadow:0 24px 60px rgba(0,0,0,.3);overflow:hidden;font-family:inherit}",
    ".sg-head{display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid var(--sg-line)}",
    ".sg-head svg{width:20px;height:20px;color:var(--sg-muted);flex:none}",
    ".sg-in{flex:1;min-width:0;border:0;outline:0;background:transparent;color:var(--sg-ink);font-family:inherit;font-size:16px;line-height:1.4;padding:6px 0}",
    ".sg-in::-webkit-search-cancel-button{display:none}",
    ".sg-x{border:1px solid var(--sg-line);background:transparent;color:var(--sg-muted);border-radius:8px;padding:5px 9px;font-family:inherit;font-weight:600;font-size:12px;line-height:1;cursor:pointer}",
    ".sg-list{overflow-y:auto;padding:6px 6px 10px;overscroll-behavior:contain}",
    ".sg-grp{font-family:inherit;font-weight:600;font-size:11px;line-height:1;letter-spacing:.07em;text-transform:uppercase;color:var(--sg-muted);padding:12px 10px 6px}",
    ".sg-opt{display:flex;gap:12px;align-items:flex-start;justify-content:space-between;padding:10px;border-radius:10px;color:var(--sg-ink);text-decoration:none;cursor:pointer}",
    ".sg-opt[aria-selected=true]{background:var(--sg-soft)}",
    ".sg-t{font-weight:600;font-size:15px;line-height:1.35}",
    ".sg-t mark{background:none;color:var(--sg-accent);font-weight:700}",
    ".sg-s{font-size:13px;color:var(--sg-muted);line-height:1.4;margin-top:2px}",
    ".sg-ur{font-family:'Noto Nastaliq Urdu','Jameel Noori Nastaleeq',serif;font-size:14px;color:var(--sg-muted);direction:rtl;line-height:1.8;flex:none;max-width:40%;text-align:right}",
    ".sg-empty,.sg-hint{padding:18px 12px;color:var(--sg-muted);font-size:14px;line-height:1.5}",
    ".sg-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 10px 8px}",
    ".sg-chip{border:1px solid var(--sg-line);background:transparent;color:var(--sg-ink);border-radius:999px;padding:6px 11px;font-family:inherit;font-size:13px;line-height:1;cursor:pointer}",
    ".sg-chip:hover{border-color:var(--sg-accent)}",
    ".sg-foot{border-top:1px solid var(--sg-line);padding:8px 14px;font-size:12px;color:var(--sg-muted);display:flex;gap:14px;flex-wrap:wrap}",
    "@media (max-width:560px){.sg-ov{padding:0}.sg-panel{max-width:none;max-height:100%;height:100%;border-radius:0;border:0}.sg-foot{display:none}}",
  ].join("\n");
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  /* ---------- helpers ---------- */
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function norm(s) { return String(s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, ""); }

  /* ---------- buttons ---------- */
  function makeButton(variant) {
    var b = el("button", "sg-root sg-btn", ICON + '<span class="sg-l">Search</span><kbd>/</kbd>');
    b.type = "button";
    b.setAttribute("aria-haspopup", "dialog");
    b.setAttribute("aria-label", "Search Sahulat Guide");
    var v = " " + (variant || "") + " ";
    if (v.indexOf(" on-dark ") >= 0) b.classList.add("sg-dark");
    if (v.indexOf(" compact ") >= 0) b.classList.add("sg-compact");
    if (v.indexOf(" wide ") >= 0) { b.classList.add("sg-wide"); b.querySelector(".sg-l").textContent = "Search: passport, bill, car loan, bus, cargo…"; }
    b.addEventListener("click", function () { open(b); });
    return b;
  }
  function mountButtons() {
    if (me && me.hasAttribute("data-no-button")) return;
    var slots = document.querySelectorAll("[data-sg-search]");
    if (slots.length) {
      for (var i = 0; i < slots.length; i++) slots[i].appendChild(makeButton(slots[i].getAttribute("data-sg-search")));
    } else {
      var f = makeButton();
      f.classList.add("sg-float");
      document.body.appendChild(f);
    }
  }

  /* ---------- dialog ---------- */
  var ov, input, list, lastFocus, results = [], active = -1, data = null, loading = false;
  function buildDialog() {
    ov = el("div", "sg-root sg-ov");
    ov.hidden = true;
    ov.innerHTML =
      '<div class="sg-panel" role="dialog" aria-modal="true" aria-label="Search Sahulat Guide">' +
      '<div class="sg-head">' + ICON +
      '<input class="sg-in" id="sg-input" type="search" autocomplete="off" spellcheck="false" placeholder="Search services, tools, districts…" role="combobox" aria-expanded="true" aria-controls="sg-list" aria-autocomplete="list">' +
      '<button class="sg-x" type="button">Esc</button></div>' +
      '<div class="sg-list" id="sg-list" role="listbox" aria-label="Results"></div>' +
      '<div class="sg-foot"><span>↑ ↓ to move</span><span>Enter to open</span><span>Esc to close</span></div></div>';
    document.body.appendChild(ov);
    input = ov.querySelector(".sg-in");
    list = ov.querySelector(".sg-list");
    ov.querySelector(".sg-x").addEventListener("click", close);
    ov.addEventListener("mousedown", function (e) { if (e.target === ov) close(); });
    input.addEventListener("input", function () { render(input.value); });
    input.addEventListener("keydown", onKey);
    ov.addEventListener("keydown", function (e) {
      if (e.key === "Tab") { // keep focus inside the dialog
        var f = [input, ov.querySelector(".sg-x")];
        var i = f.indexOf(document.activeElement);
        e.preventDefault();
        f[(i + (e.shiftKey ? f.length - 1 : 1)) % f.length].focus();
      }
    });
    list.addEventListener("click", function (e) {
      var chip = e.target.closest(".sg-chip");
      if (chip) { input.value = chip.textContent; render(input.value); input.focus(); }
    });
  }

  function loadData(cb) {
    if (data) return cb();
    if (window.SG_INDEX) { data = prep(window.SG_INDEX); return cb(); }
    if (loading) return;
    loading = true;
    var s = document.createElement("script");
    s.src = BASE + "search-index.js";
    s.onload = function () { data = prep(window.SG_INDEX || []); loading = false; cb(); };
    s.onerror = function () { loading = false; list.innerHTML = '<div class="sg-empty">Search could not load. Check your connection and try again.</div>'; };
    document.head.appendChild(s);
  }
  function prep(raw) {
    return raw.map(function (r) {
      return { type: r[0], title: r[1], ur: r[2], sub: r[3], url: r[4], t: norm(r[1]), hay: norm(r[1] + " " + r[3] + " " + r[5]), urRaw: r[2] || "" };
    });
  }

  function open(from, query) {
    lastFocus = from || document.activeElement;
    if (!ov) buildDialog();
    ov.hidden = false;
    document.documentElement.style.overflow = "hidden";
    input.value = query || "";
    list.innerHTML = '<div class="sg-hint">Loading…</div>';
    input.focus();
    loadData(function () { render(input.value); });
  }
  function close() {
    if (!ov || ov.hidden) return;
    ov.hidden = true;
    document.documentElement.style.overflow = "";
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  var SUGGEST = ["Passport", "CNIC", "Domicile", "Driving licence", "Electricity bill", "BISP", "Bannu", "Health card", "Hajj", "Train"];
  function render(q) {
    if (!data) return;
    var nq = norm(q).trim();
    results = []; active = -1;
    if (!nq && !q.trim()) {
      list.innerHTML = '<div class="sg-hint">Search every service guide, tool, and all districts and tehsils of Pakistan. Type in English or Urdu.</div><div class="sg-chips">' +
        SUGGEST.map(function (s) { return '<button type="button" class="sg-chip">' + esc(s) + "</button>"; }).join("") + "</div>";
      input.setAttribute("aria-activedescendant", "");
      return;
    }
    var words = nq.split(/\s+/).filter(Boolean), raw = q.trim();
    var scored = [];
    for (var i = 0; i < data.length; i++) {
      var d = data[i], score = 0, ok = true;
      if (raw && d.urRaw && d.urRaw.indexOf(raw) >= 0) score = 60;
      else {
        for (var w = 0; w < words.length; w++) { if (d.hay.indexOf(words[w]) < 0) { ok = false; break; } }
        if (!ok) continue;
        if (d.t === nq) score = 100;
        else if (d.t.indexOf(nq) === 0) score = 80;
        else if (d.t.indexOf(nq) >= 0) score = 60;
        else if (words.every(function (x) { return d.t.indexOf(x) >= 0; })) score = 45;
        else score = 20;
      }
      score += { Service: 8, Category: 6, Tool: 7, Section: 2, University: 4, Police: 3, Fee: 1, Place: 0 }[d.type] || 0;
      if (d.type === "Place" && /tehsil|taluka/i.test(d.title)) score -= 3;
      if (d.type === "Place" && / District$/.test(d.title)) score += 2;
      scored.push([score, d]);
    }
    scored.sort(function (a, b) { return b[0] - a[0] || a[1].title.length - b[1].title.length; });
    var groups = {}, total = 0;
    for (var k = 0; k < scored.length && total < 40; k++) {
      var it = scored[k][1], g = groups[it.type] || (groups[it.type] = []);
      if (g.length < (it.type === "Place" ? 8 : 6)) { g.push(it); total++; }
    }
    var html = "";
    GROUP_ORDER.forEach(function (type) {
      if (!groups[type]) return;
      html += '<div class="sg-grp" role="presentation">' + GROUP_LABEL[type] + "</div>";
      groups[type].forEach(function (it) {
        var idx = results.length;
        results.push(it);
        html += '<a class="sg-opt" role="option" id="sg-o' + idx + '" aria-selected="false" tabindex="-1" href="' + esc(BASE + it.url) + '">' +
          '<span style="min-width:0"><span class="sg-t">' + mark(it.title, words) + '</span><span class="sg-s" style="display:block">' + esc(it.sub) + "</span></span>" +
          (it.ur ? '<span class="sg-ur" lang="ur">' + esc(it.ur) + "</span>" : "") + "</a>";
      });
    });
    list.innerHTML = html || '<div class="sg-empty">Nothing found for “' + esc(q) + '”. Try a shorter word, such as “licence” or a district name.</div>';
    if (results.length) setActive(0);
  }
  function mark(title, words) {
    var out = esc(title);
    words.forEach(function (w) {
      if (w.length < 2) return;
      var re = new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }
  function setActive(i) {
    var prev = list.querySelector('[aria-selected="true"]');
    if (prev) prev.setAttribute("aria-selected", "false");
    active = i;
    var cur = document.getElementById("sg-o" + i);
    if (cur) { cur.setAttribute("aria-selected", "true"); cur.scrollIntoView({ block: "nearest" }); input.setAttribute("aria-activedescendant", cur.id); }
  }
  function onKey(e) {
    if (e.key === "Escape") { e.preventDefault(); close(); }
    else if (e.key === "ArrowDown" && results.length) { e.preventDefault(); setActive((active + 1) % results.length); }
    else if (e.key === "ArrowUp" && results.length) { e.preventDefault(); setActive((active - 1 + results.length) % results.length); }
    else if (e.key === "Enter" && active >= 0) {
      e.preventDefault();
      var a = document.getElementById("sg-o" + active);
      if (a) { close(); location.href = a.href; }
    }
  }

  /* Clicking a result that only changes the hash on this page still closes the dialog. */
  document.addEventListener("click", function (e) { if (e.target.closest && e.target.closest(".sg-opt")) close(); });

  /* ---------- shortcuts ---------- */
  document.addEventListener("keydown", function (e) {
    var t = e.target, typing = t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    if ((e.key === "k" || e.key === "K") && (e.ctrlKey || e.metaKey)) { e.preventDefault(); open(); }
    else if (e.key === "/" && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); open(); }
  });

  window.SahulatSearch = { open: open, close: close };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountButtons);
  else mountButtons();
})();
