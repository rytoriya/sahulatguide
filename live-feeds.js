/*
 * live-feeds.js — daily rates, KSE-100 and news for Sahulat Guide.
 *
 * Reads four JSON files from data/ (relative to this script):
 *   data/rates.json      fuel, gold/silver, open-market currency
 *   data/stocks.json     KSE-100 index and most active shares
 *   data/headlines.json  Pakistan news headlines (each links to its article)
 *   data/updates.json    government service updates (each links to its source)
 *   data/jobs.json       important government recruitment (home panel, jobs/ page)
 *   data/scores.json     Pakistan sport: fixtures, live and results (home panel)
 * and re-checks them every 5 minutes while the page is open. Update the JSON
 * files (by hand or with a scheduled job) and every page shows the new figures
 * without a rebuild.
 *
 * What it draws, if the page has the slot:
 *   #rateSide  three rotating boxes: Fuel, gold & silver · Currency · KSE-100
 *   #belt2     Headlines ticker
 *   #belt      Updates ticker (replaces the built-in list once the file loads)
 *   #scores    Pakistan sports panel        #jobsMini  top 5 open government jobs
 * Other pages can listen for the "sg-feeds" event: e.detail = {rates, stocks, headlines, updates, checked}.
 */
(function(){
  const me = document.currentScript;
  const base = new URL("data/", me ? me.src : location.href);
  const FEEDS = ["rates","stocks","headlines","updates","jobs","scores"];
  const state = {checked:null};
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  const nf = (v,d=0) => (v==null||isNaN(v)) ? "—" : Number(v).toLocaleString("en-PK",{minimumFractionDigits:d,maximumFractionDigits:d});
  const fmtTime = iso => { try{ return new Date(iso).toLocaleString("en-PK",{day:"numeric",month:"short",hour:"numeric",minute:"2-digit"}); }catch(_){ return ""; } };
  const stale = (iso,h) => { const t = Date.parse(iso); return !t || Date.now()-t > h*3600e3; };
  const pill = (c,d,good) => { if (c==null) return ""; const up = +c>0, dn = +c<0;
    const cls = !up&&!dn ? "eq" : (good ? (up?"gup":"gdn") : (up?"up":"dn"));
    return `<span class="sgf-chg ${cls}">${up?"▲ ":dn?"▼ ":""}${nf(Math.abs(c),d)}${good&&d===2&&Math.abs(c)<50?"":""}</span>`; };
  const pct = c => c==null ? "" : `<span class="sgf-chg ${+c>0?"gup":+c<0?"gdn":"eq"}">${+c>0?"▲ ":+c<0?"▼ ":""}${nf(Math.abs(c),2)}%</span>`;
  const vol = v => v==null ? "—" : v>=1e6 ? nf(v/1e6,2)+"M" : v>=1e3 ? nf(v/1e3,1)+"K" : nf(v);

  function marketOpen(){
    const now = new Date(Date.now() + (new Date().getTimezoneOffset()+300)*60e3); // Pakistan time
    const d = now.getDay(), m = now.getHours()*60+now.getMinutes();
    if (d===0||d===6) return false;
    if (d===5) return (m>=555&&m<720)||(m>=870&&m<990);
    return m>=570 && m<930;
  }

  /* ---------- Home: three rotating boxes ---------- */
  const CSS = `
.sgf-side{display:grid;gap:10px;align-content:center}
.sgf-box{background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden;display:grid;grid-template-rows:auto 1fr auto;box-shadow:var(--shadow-sm,none)}
.sgf-box .rh{display:flex;justify-content:space-between;align-items:center;gap:6px;padding:6px 10px;background:var(--accent-soft)}
.sgf-box.fx .rh{background:var(--amber-soft)}
.sgf-box.px .rh{background:var(--sky)}
.sgf-box .rh b{font:600 11.5px var(--f-display);display:flex;gap:6px;align-items:center}
.sgf-box .rh b svg{width:14px;height:14px}
.sgf-box .mk{font:600 9.5px var(--f-mono);text-transform:uppercase;letter-spacing:.06em;padding:1px 5px;border-radius:4px;background:var(--bg);color:var(--muted)}
.sgf-box .mk.open{background:var(--accent);color:var(--accent-ink)}
.sgf-stage{min-height:84px;padding:8px 10px 4px}
.sgf-it{display:grid;gap:2px}
@media (prefers-reduced-motion:no-preference){.sgf-it.in{animation:sgfin .45s ease both}@keyframes sgfin{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}}
.sgf-it .nm{display:flex;justify-content:space-between;align-items:baseline;gap:6px;font-weight:600;font-size:12.5px}
.sgf-it .nm .ur{font-family:var(--f-urdu);font-size:11.5px;color:var(--muted);font-weight:500;line-height:1.8}
.sgf-it .nm .co{font-weight:500;color:var(--muted);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:60%}
.sgf-it .cc{font:600 11.5px var(--f-mono);background:var(--bg);padding:1px 5px;border-radius:4px}
.sgf-it .big{font:700 19px var(--f-display);font-variant-numeric:tabular-nums;line-height:1.15}
.sgf-it .big small{font:500 11.5px var(--f-body);color:var(--muted);margin-left:3px}
.sgf-it .two{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.sgf-it .two span{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.sgf-it .two b{display:block;font:700 16px var(--f-display);font-variant-numeric:tabular-nums}
.sgf-it .sub{font-size:11px;color:var(--muted);display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.sgf-chg{font:600 11px var(--f-mono);padding:1px 5px;border-radius:5px;white-space:nowrap}
.sgf-chg.up,.sgf-chg.gdn{background:var(--stamp-soft);color:var(--stamp)}
.sgf-chg.dn,.sgf-chg.gup{background:var(--accent-soft);color:var(--accent)}
.sgf-chg.eq{background:var(--bg);color:var(--muted)}
.sgf-dots{display:flex;gap:2px;padding:0 8px 4px;flex-wrap:wrap}
.sgf-dots button{width:14px;height:14px;padding:0;border:0;background:none;cursor:pointer;display:grid;place-items:center}
.sgf-dots button::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--line)}
.sgf-dots button[aria-current="true"]::before{background:var(--accent);width:12px;border-radius:4px}
.sgf-box.fx .sgf-dots button[aria-current="true"]::before{background:var(--amber)}
.sgf-box.px .sgf-dots button[aria-current="true"]::before{background:var(--ink)}
.sgf-box .rf{display:flex;justify-content:space-between;gap:6px;align-items:center;padding:5px 10px;border-top:1px solid var(--line);font-size:10.5px;color:var(--muted)}
.sgf-box .rf a{font:600 11px var(--f-body);color:var(--accent);text-decoration:none;white-space:nowrap}
.sgf-stale{color:var(--amber);font-weight:600}
@media (prefers-reduced-motion:no-preference){.sgf-flash{animation:sgfflash 1.2s ease}@keyframes sgfflash{0%{background:color-mix(in srgb,var(--sun) 45%,transparent)}100%{background:transparent}}}
.ticker .item .src{font:500 11px var(--f-mono);color:var(--muted);margin-left:8px}`;
  function addCSS(){ if (document.getElementById("sgf-css")) return; const s=document.createElement("style"); s.id="sgf-css"; s.textContent=CSS; document.head.appendChild(s); }

  const ROT = {};
  function rotator(box, slides, delay){
    const st = box.querySelector(".sgf-stage"), dots = box.querySelector(".sgf-dots");
    let r = ROT[box.id];
    if (!r){ r = ROT[box.id] = {i:0, paused:false};
      ["mouseenter","focusin"].forEach(ev=>box.addEventListener(ev,()=>r.paused=true));
      ["mouseleave","focusout"].forEach(ev=>box.addEventListener(ev,()=>r.paused=false));
      dots.addEventListener("click",e=>{ const d=e.target.closest("[data-i]"); if(d){ r.i=+d.dataset.i; r.show(); } });
      setTimeout(()=>{ setInterval(()=>{ if(r.paused||document.hidden) return; r.i=(r.i+1)%r.slides.length; r.show(); }, 4500); }, delay);
    }
    r.slides = slides; if (r.i>=slides.length) r.i=0;
    r.show = () => { st.innerHTML = `<div class="sgf-it in">${r.slides[r.i]||""}</div>`;
      dots.innerHTML = r.slides.map((_,k)=>`<button type="button" data-i="${k}" aria-label="Show item ${k+1}" aria-current="${k===r.i}"></button>`).join(""); };
    r.show();
  }
  const IC = {
    fuel:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16"/><path d="M3 21h13"/><path d="M15 9h2a2 2 0 0 1 2 2v6a1.5 1.5 0 0 0 3 0V8l-3-3"/><rect x="7" y="6" width="5" height="4" rx="1"/></svg>`,
    fx:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.6-1.5-3-1.5-1.7 0-3 .8-3 2s1.3 1.7 3 2 3 .8 3 2-1.3 2-3 2c-1.4 0-2.6-.6-3-1.6M12 6v2M12 16v2"/></svg>`,
    px:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/></svg>`
  };
  function box(id, cls, icon, title, right, link, linkText, ext){
    return `<div class="sgf-box ${cls}" id="${id}"><div class="rh"><b>${icon}${title}</b>${right}</div><div class="sgf-stage" aria-live="polite"></div><div class="sgf-dots" role="group" aria-label="Choose item"></div>
      <div class="rf"><span class="when"></span><a href="${link}"${ext?' target="_blank" rel="noopener"':""}>${linkText}</a></div></div>`;
  }
  let last = {};
  function drawSide(){
    const side = document.getElementById("rateSide"); if (!side) return;
    const R = state.rates, P = state.stocks;
    if (!side.dataset.ready){
      addCSS();
      const ratesUrl = new URL("../rates/", base).href;
      side.classList.add("sgf-side");
      side.innerHTML = box("sgfA","","" + IC.fuel,"Fuel, gold &amp; silver","",ratesUrl,"All rates →") +
        box("sgfB","fx",IC.fx,"Currency rates","",ratesUrl,"All rates →") +
        box("sgfC","px",IC.px,"KSE-100 · PSX",`<span class="mk" id="sgfMk">Closed</span>`,"https://dps.psx.com.pk/","Live on PSX ↗",true);
      side.dataset.ready = "1";
      setInterval(mkState, 60e3);
    }
    if (R){
      const a = [...R.fuel.items.map(x=>`<div class="nm"><span>${esc(x.name)}</span><span class="ur" lang="ur">${esc(x.ur||"")}</span></div><div class="big">Rs ${nf(x.price,2)}<small>/ litre</small></div><div class="sub">${pill(x.chg,2)}<span>${esc(R.fuel.date)}</span></div>`),
        ...R.metals.items.map(x=>`<div class="nm"><span>${esc(x.name)}</span><span class="ur" lang="ur">${esc(x.ur||"")}</span></div><div class="big">Rs ${nf(x.tola)}<small>/ tola</small></div><div class="sub">${pill(x.chg,0)}<span>10 g: Rs ${nf(x.g10)}</span></div>`)];
      const b = R.fx.items.map(x=>`<div class="nm"><span><span class="cc">${esc(x.code)}</span> ${esc(x.name)}</span><span class="ur" lang="ur">${esc(x.ur||"")}</span></div><div class="two"><div><span>Buying</span><b>${nf(x.buy,2)}</b></div><div><span>Selling</span><b>${nf(x.sell,2)}</b></div></div><div class="sub">${x.chg==null?"":pill(x.chg,2)}<span>Rs per 1 ${esc(x.code)}</span></div>`);
      rotator(document.getElementById("sgfA"), a, 0); rotator(document.getElementById("sgfB"), b, 2200);
      const w = (stale(R.updated,36)?`<span class="sgf-stale">May be outdated · </span>`:"") + "Updated " + esc(fmtTime(R.updated));
      side.querySelectorAll("#sgfA .when,#sgfB .when").forEach(e=>e.innerHTML=w);
    }
    if (P){
      const ix = P.index;
      const c = [`<div class="nm"><span>${esc(ix.name||"KSE-100")} index</span><span class="ur" lang="ur">کے ایس ای ۱۰۰</span></div><div class="big" data-k="IDX">${nf(ix.value,2)}</div><div class="sub">${pill(ix.chg,2,true)}${pct(ix.pct)}</div>`,
        ...P.items.map(x=>`<div class="nm"><span class="cc">${esc(x.sym)}</span><span class="co">${esc(x.name)}</span></div><div class="big" data-k="${esc(x.sym)}">Rs ${nf(x.price,2)}</div><div class="sub">${pct(x.pct)}<span>Vol ${vol(x.vol)}</span></div>`)];
      rotator(document.getElementById("sgfC"), c, 1100);
      side.querySelector("#sgfC .when").innerHTML = (stale(P.updated,30)?`<span class="sgf-stale">May be outdated · </span>`:"") + "As of " + esc(fmtTime(ix.asof||P.updated));
      const cur = {IDX:ix.value}; P.items.forEach(x=>cur[x.sym]=x.price);
      Object.keys(cur).forEach(k=>{ if (last[k]!=null && last[k]!==cur[k]) side.querySelectorAll(`[data-k="${k}"]`).forEach(e=>{e.classList.remove("sgf-flash"); void e.offsetWidth; e.classList.add("sgf-flash");}); });
      last = cur;
    }
    mkState();
  }
  function mkState(){ const m = document.getElementById("sgfMk"); if (!m) return; const o = marketOpen(); m.textContent = o?"Market open":"Closed"; m.className = "mk"+(o?" open":""); }

  /* ---------- Tickers ---------- */
  function belt(id, items){
    const el = document.getElementById(id); if (!el) return;
    el.innerHTML = items + `<span aria-hidden="true" style="display:contents">${items.replace(/href="[^"]*"/g,'tabindex="-1"')}</span>`;
  }
  function drawTickers(){
    addCSS();
    const H = state.headlines, U = state.updates;
    if (H && H.items && H.items.length)
      belt("belt2", H.items.map(h=>`<span class="item"><b>${esc(h.src||"News")}</b><a href="${esc(h.url)}" target="_blank" rel="noopener">${esc(h.t)}</a></span>`).join("") + `<span class="item"><b>Updated</b>${esc(fmtTime(H.updated))}</span>`);
    if (U && U.items && U.items.length)
      belt("belt", U.items.map(u=>`<span class="item"><b>${esc(u.d)}</b>${u.url?`<a href="${esc(u.url)}" target="_blank" rel="noopener">${esc(u.t)}</a>`:(u.svc?`<a href="#${esc(u.svc)}">${esc(u.t)}</a>`:esc(u.t))}${u.src?`<span class="src">${esc(u.src)}</span>`:""}</span>`).join("") + `<span class="item"><b>Updated</b>${esc(fmtTime(U.updated))}</span>`);
  }

  /* ---------- Home panels: sports and jobs ---------- */
  const JOB_STATUS = {open:["Open","open"],closing:["Closing","closed"],upcoming:["Upcoming","check"],test:["Test date","check"],none:["No ads now","check"],closed:["Closed","closed"]};
  window.SGJobStatus = JOB_STATUS;
  function drawPanels(){
    const sc = document.getElementById("scores"), S = state.scores;
    if (sc && S && S.items){
      sc.innerHTML = S.items.length ? S.items.map(x=>`<div class="score"><span class="st${/live/i.test(x.status)?" live":""}">${esc(x.status)}</span><b>${esc(x.title)}</b><span>${esc(x.sport)} · ${esc(x.detail||"")}</span></div>`).join("") : `<div class="empty">No Pakistan matches scheduled right now.</div>`;
      const u = document.getElementById("scoresUpd"); if (u) u.textContent = "Updated " + fmtTime(S.updated);
    }
    const jm = document.getElementById("jobsMini"), J = state.jobs;
    if (jm && J && J.items){
      const live = J.items.filter(j=>j.status!=="closed" && j.status!=="none").slice(0,5);
      jm.innerHTML = live.length ? live.map(j=>`<div class="jrow"><span><b>${esc(j.title)}</b><br><span style="font-size:13px;color:var(--muted)">${esc(j.org)} · ${esc(j.last)}</span></span><span class="pill ${(JOB_STATUS[j.status]||[,"check"])[1]}">${esc((JOB_STATUS[j.status]||[j.status])[0])}</span></div>`).join("") : `<div class="empty">No open government jobs listed right now.</div>`;
    }
  }

  /* ---------- Loading ---------- */
  async function load(name){
    try{ const r = await fetch(new URL(name+".json", base).href + "?t=" + Math.floor(Date.now()/60e3), {cache:"no-store"}); if (!r.ok) return null; return await r.json(); }catch(_){ return null; }
  }
  async function check(){
    const got = await Promise.all(FEEDS.map(load));
    FEEDS.forEach((f,i)=>{ if (got[i]) state[f] = got[i]; });
    state.checked = new Date();
    drawSide(); drawTickers(); drawPanels();
    document.dispatchEvent(new CustomEvent("sg-feeds", {detail: state}));
  }
  window.SGFeeds = {check, state, marketOpen};
  const start = () => { check(); setInterval(()=>{ if (!document.hidden) check(); }, 5*60e3); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
