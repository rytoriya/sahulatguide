# Changes

## 7 October 2026: Police Station Directory with addresses, maps and a guide

### Data (all in data/police/)
- **1,214 police stations** in 107 of 175 districts (was 506 in 38): 1,126 from official police sources, the rest named police stations mapped on OpenStreetMap in districts without an official list.
- **Punjab:** every "SDPOs and Police Stations" directory page of Punjab Police, 36 districts, about 700 stations with circle and phone.
- **Karachi:** all 111 Karachi Police stations with the official map pin, the SDPO, SHO, SIO and Head Moharrar with numbers, and 103 jurisdiction areas.
- **Islamabad:** all 27 stations from the Islamabad Police locator with official address, phone and location, plus 11 Police Khidmat Markaz centres (services, hours).
- **KP:** the KP Police phone directory (existing list).
- **On the map:** 796 stations (348 exact, 8 found by name, 440 approximate at their town or area). 418 have no pin yet; their cards link to a Google Maps search.
- **Addresses:** 791 stations, from the police (Islamabad), OpenStreetMap or reverse geocoding (Nominatim).
- Sindh outside Karachi, Balochistan and AJK police websites refused or did not answer, so those districts rely on OpenStreetMap.

### How the data is collected
- `.github/workflows/police-data.yml` runs on GitHub (Actions tab, "Police station data") because the police websites, OpenStreetMap and Nominatim cannot be reached from the development environment. Steps: `crawl` (OpenStreetMap + official pages), `targets` (Karachi, Islamabad, retries), `geocode` (Nominatim, 1 request a second, reads `data/police/requests.json`). Results are committed to `data/police/raw/`.
- Parsers: `scripts/police_parse_punjab.py`, `police_parse_karachi.py`, `police_parse_islamabad.py`; `scripts/police_update_official.py` merges them into `data/police-stations.txt`.
- `scripts/police_process.py requests|requests2|build` places points in districts (geoBoundaries tehsil boundaries in `data/police/boundaries/`, CC BY 4.0), matches official stations to map points, writes geocoding requests and builds `police/districts/<id>.json`.
- Refresh: run the workflow steps, then `python3 scripts/police_update_official.py && python3 scripts/police_process.py build && node scripts/build_police.js`.

### The page (/police/?d=<district>)
- Loads its district file (no live map lookups): district boundary drawn and map zoomed to it, solid pins for exact locations, dashed for approximate, grey for other police points, amber for Islamabad service centres; Karachi jurisdiction areas, and "which station covers you" when you share your location or tap the map.
- Every station card shows the address, phone, officers where published, how exact the location is, directions and Google Maps.
- "How police stations work in <district>" (police/guide.js) at the bottom: who runs a station, registering an FIR (section 154 CrPC, free copy, Justice of Peace under 22-A), services, your rights, and the province's complaint routes.
- The map stays in view beside the list on wide screens.

## 7 October 2026: external links are nofollow

- Every link to another website now has `rel="nofollow"` (with `noopener` where it opens a new tab). Links within Sahulat Guide are unchanged, so search engines still follow them.
- Links written in the HTML: `scripts/nofollow_links.js` adds it (100 links today). Netlify runs it on every deploy, so links added later are covered.
- Links built by page scripts (news tickers, maps and directions, directories, university and job links, WhatsApp): `links.js`, loaded on every page through the shared footer, marks them as they appear.
- The Markdown guide builder (`scripts/build_guides.py`) writes external links with `nofollow` too.
- Checked in a browser on 20 pages: 862 external links, all nofollow; no internal link marked.

## 7 October 2026: one header and footer on every page

- Every page now has the same header as the home page: the notice bar, logo, full-width search, "Pay school & university fees", "My details" and the full tab strip (the current page's tab is underlined). Every page also has the same full footer (services, useful links, company links, emergency numbers).
- One source: `partials/header.html` and `partials/footer.html`, styled in `site.css` (classes start with `sgc-` so page styles never clash). `scripts/build_chrome.js` writes them into every page between `<!-- sg:header -->` / `<!-- sg:footer -->` markers, building the tab list and footer service links from `TABS` and `GROUPS` in `index.html`. Netlify runs it on every deploy.
- To change the header or footer: edit the partial, then run `node scripts/build_chrome.js`. Do not edit the copies between the markers in the pages.
- New pages: add the two marker pairs (or a `<header class="site">` / `</main>`) and run the script; the page is picked up automatically.
- Pages keep their own notes at the bottom (sources, disclaimers) above the site footer.
- The road route planner keeps its full-screen map layout without the site header and footer.
- The passport page's own bar no longer repeats Search and My details (they are in the site header).
- Search: new `data-sg-search="wide"` style, a full-width search field used in the header.

## 6 October 2026 (late night): every tab and guide has its own page address

Before, the main app's tabs and guides only had `#` addresses (`/#identity`, `/#cnic-renewal`). To Google those are all the same page as the home page. Now each one is a real page, like `/police/`:

| Before | Now |
|---|---|
| `/#identity` | `/services/identity/` |
| `/#cnic-renewal` | `/services/identity/cnic-renewal/` |
| `/#all` | `/services/` |
| `/#emergency` (helplines tab) | `/helplines/` |
| `/#tools` | `/calculators/` |
| `/#portals`, `/#contact`, `/#about`, `/#privacy`, `/#terms` | `/portals/`, `/contact/`, `/about/`, `/privacy/`, `/terms/` |

- Each page has its own title, description, canonical link and WhatsApp/Facebook preview text (from the `SEO` object where a guide has one, otherwise its name and summary).
- Clicking a tab or guide changes the address; Back and Forward work. Old `#` links people already shared still open the right page and switch to the new address.
- `scripts/build_routes.js` writes these pages (95 of them) and `sitemap.xml`. Netlify runs it on every deploy (`netlify.toml`), so the pages always match `index.html`; the generated folders are not committed. If a page is ever missing, Netlify serves the app and it still opens the right view.
- `index.html` has `<base href="/">` so its links, scripts and data load from any depth. Open the site through a local server (`python3 -m http.server`), not as a file.
- Search results, tool-page links and `robots.txt` point to the new addresses.

## 6 October 2026 (night): one font and no sideways scrolling on phones

### One typeface across the whole site
- Every page now uses **Plus Jakarta Sans** (already used on the passport page). Sora, Noto Sans, JetBrains Mono and Roboto are gone. Urdu text keeps **Noto Nastaliq Urdu**.
- Codes, reference numbers, dates and the search key hint use the same font with even-width figures instead of a coding font.
- `scripts/unify_fonts.py` rewrites the font links and font names in every page; run it again if a new page brings in another font.

### Mobile: the page no longer slides left and right
- New shared stylesheet `site.css`, linked last from every page: stops the page itself from scrolling sideways, stops phones from enlarging some text blocks on their own, and wraps long words and URLs.
- Real overflow fixed at its source: sub-page headers on 360-440px phones (the words "Sahulat Guide" hide, the logo stays), the universities test cards, page grids on emergency, account, police and universities, and the passport "Office hours" line on very small phones.
- Pakistan sports panel: on phones the date sits above the match title, so titles read in 1-2 lines.
- Checked on all 15 pages at 320, 360, 390 and 414px wide: nothing wider than the screen.

## 6 October 2026 (evening) — features from the chat version brought into the code

The claude.ai version of the site had several features built in earlier chats that were not in this code yet. They are now added, in this code's style (tool pages in their own folder):

### Find a hospital (new page `hospitals/`)
- 251 government and private hospitals across all 41 Punjab districts (teaching, specialist, DHQ, THQ, private/trust, armed forces, social security), with beds and notes where known.
- Nearest hospitals to your town or Google Maps coordinates, with filters (any, 24/7 emergency, specialist, government only) and directions.
- "Which hospital for what" guide to the five care levels (BHU → teaching), ambulance 1122 and health helpline 1033.
- Search and filters by division, district, type and sector; district summary panel; division/district index (new districts marked).
- "For people / For animals" switch at the top; animals goes to `vets/`.
- Home page: "Find a hospital near you" box (opens `hospitals/?where=<town>`), with a "Need a vet?" link.
- Data in `hospitals/data.js`.

### Government jobs (new page `jobs/`)
- Important FPSC, PPSC, SPSC, KPPSC, BPSC, AJK PSC and armed forces recruitment with status (open, closing, upcoming, test date), posts, last date, who can apply and the official website.
- Filters: All · Open now · Public service commissions · Armed forces.
- Home page: "Government jobs" panel with the top 5 open jobs.
- Data in `data/jobs.json`.

### Pakistan sports (home page panel)
- Pakistan cricket and other major sport: fixtures, live matches and results. Data in `data/scores.json`.

### About, Privacy Policy, Terms & Disclaimer
- Three pages at `#about`, `#privacy`, `#terms` (Google AdSense-ready wording, cookies, opt-out links, not-a-government-site disclaimer).
- Fill in `SITE_OWNER`, `SITE_CITY`, `SITE_EMAIL` and `SITE_DOMAIN` near the top of the script in `index.html`; blanks show as highlighted placeholders until then.

### Site footer
- Full footer: about blurb, all service categories, useful links (jobs, rates, hospitals, vets, police, universities, calculators, portals, emergency), company links (About, Contact, Privacy, Terms) and emergency numbers.

### "About" boxes on guides
- 28 guides now show an "About: …" box with a search-friendly title, a short description and "also searched as" keywords (`SEO` object in `index.html`).

### Tabs and tools
- Tab strip: **Find a hospital** and **Govt jobs** added next to Daily rates.
- "Tools & directories" and Calculators: cards for Find a hospital and Government jobs.
- Site search: Find a hospital, Government jobs and About/Privacy/Terms added.

### Live data
`live-feeds.js` now also reads `data/jobs.json` and `data/scores.json` (home panels and `jobs/`).

## 6 October 2026 — Daily rates, KSE-100, live tickers, veterinary care

These changes were first built and tested in the Claude chat version of the site (the claude.ai artifact "Sahulat Guide Pakistan") and are now added to this code.

### 1. Daily rates (new page `rates/`)
- Petrol (Super) and high-speed diesel price per litre with the change from the last notification.
- Gold 24K, gold 22K and silver, per tola and per 10 g (Sarafa association rate).
- Open-market currency rates, buying and selling: USD, AED, SAR, AUD, GBP, EUR, CAD.
- KSE-100 index with point and % change, and the 5 most active shares by volume (price, % change, volume), each linking to its PSX page. Shows "Market open" / "Closed" from Pakistan market hours.
- Quick currency converter.
- Links to sites that publish these rates every day: OGRA, Dawn Business, Business Recorder, UrduPoint, State Bank of Pakistan, Forex.pk, PSX Data Portal.
- **Auto-update** switch and **Check now** button. With auto-update on, the page re-reads the data every 5 minutes.
- Added to the tab strip as **Daily rates**, and as a card in "Tools & directories" and the Calculators tab.

### 2. Rotating rate boxes on the home page
- Three small boxes to the right of the hero (stacked below it on tablets and phones):
  - **Fuel, gold & silver** — petrol, diesel, gold 24K, gold 22K, silver.
  - **Currency rates** — USD, AED, SAR, AUD, GBP, EUR, CAD (buying and selling).
  - **KSE-100 · PSX** — the index, then the most active shares.
- Each box shows one item at a time and moves to the next every 4.5 seconds (staggered), pauses on hover, and has dots to jump to an item. Prices that change since the last check flash briefly.
- Footer of each box: last-updated time ("May be outdated" after 36 h / 30 h), and a link to the Daily rates page or to PSX.
- Sized small on purpose (236 px column, compact text).

### 3. Updates and Headlines tickers linked to their sources
- **Updates** ticker: each item now links to its official source (FBR, HEC, SBP, OGRA …) or a news report, with the source name shown. The "Updates" label jumps to the Latest updates list.
- **Headlines** ticker (new, under Updates): 6–8 Pakistan news headlines, each linking to the article (Dawn, Geo, Express Tribune, Business Recorder, APP, Radio Pakistan). The "Headlines" label opens Dawn's latest news.
- Both end with an "Updated" time.

### 4. Veterinary care (no new tab — inside existing sections)
- **Farmers** category: new topic **Veterinary care** with 5 guides:
  - `vet-free-treatment` — free animal treatment at Punjab government vet hospitals (Rs 2 slip, helpline 08000-9211, facility levels, mobile vet fleet of Sept 2026).
  - `vet-vaccination` — free livestock vaccination & deworming package, with a disease calendar (HS, FMD, BQ, LSD, PPR, ET, CCPP, Newcastle).
  - `vet-doctors` — how to reach a vet doctor: helplines, mobile units and home visits, by province (Punjab, ICT 051-9108384, KP, Sindh/Karachi).
  - `vet-kp-mobile` — KP Ehsaas-e-Bezaban Sehat Gaari: 145 mobile vet clinics, 27 mobile labs (launched 1 Oct 2026).
  - `vet-pets` — pet care: government, university and private clinics, and a pet vaccination package checklist.
- Guide sheets can now set their own section headings (`hd`) and table title (`tableTitle`); other guides are unchanged.
- **Scheme finder** (Calculators tab): new need "Sick animal / veterinary care".
- **New page `vets/` (Find a vet)**:
  - Nearest vet centre by town or Google Maps coordinates: a Civil Veterinary Hospital in each of 143 Punjab tehsil towns, 4 university vet hospitals (UVAS Lahore, UAF Faisalabad, CVAS Jhang, Cholistan University Bahawalpur), ICT's 4 vet hospitals, Richmond Crawford (Karachi) and the Peshawar vet hospital. Filters: Any / Government (free) / Private clinics / For pets. Directions links to Google Maps.
  - Animal emergency panel with helplines.
  - Private vet clinics by city: Lahore, Karachi, Islamabad, Rawalpindi, Faisalabad, Multan, Peshawar (37 clinics).
  - Searchable list of government and university vet hospitals.
  - **Animal first-aid helper** for home or remote areas: 5 animal types × 11 problems (diarrhoea, bloat, wounds, fever, ticks, heat stroke, difficult birth, milk fever, poisoning, dog bite/rabies, sudden bird deaths), each with "Do now", "Don't" and "Call a vet straight away if". No prescription drug doses.
  - Weight estimate from chest girth and body length (for label doses).
  - Linked from the Farmers guides, the home "Tools & directories" grid and the Calculators tab.

### Files
| File | What changed |
|---|---|
| `index.html` | Headlines ticker; linked Updates label; rate boxes beside the hero; Daily rates tab; Daily rates + Find a vet cards; Veterinary care topic and 5 guides; `hd`/`tableTitle` support; scheme finder option |
| `live-feeds.js` | **New.** Loads `data/*.json`, draws the home rate boxes and both tickers, re-checks every 5 minutes, fires an `sg-feeds` event other pages use |
| `rates/index.html` | **New.** Daily rates page |
| `vets/index.html`, `vets/data.js` | **New.** Find a vet page and its data |
| `data/rates.json`, `data/stocks.json`, `data/headlines.json`, `data/updates.json` | **New.** The live figures (see below) |
| `scripts/build_search_index.js` | Adds Daily rates and Find a vet to site search |
| `search-index.js` | Rebuilt |

### How the figures stay up to date
The pages read `data/rates.json`, `data/stocks.json`, `data/headlines.json` and `data/updates.json`. Change those files and every visitor sees the new figures within 5 minutes, with no rebuild. Formats:

- `rates.json`: `{updated, fuel:{date,note,items:[{k,name,ur,price,chg}]}, metals:{date,note,items:[{k,name,ur,tola,g10,chg}]}, fx:{date,note,items:[{code,name,ur,buy,sell,chg}]}}`
- `stocks.json`: `{updated, index:{name,value,chg,pct,high,low,asof}, items:[{sym,name,price,pct,vol}], itemsAsof}`
- `headlines.json`: `{updated, items:[{t,src,url}]}`
- `updates.json`: `{updated, items:[{d,t,src,url,svc}]}` (`svc` = a guide id or "")

On the claude.ai version these are refreshed automatically by scheduled tasks (rates 6×/day, KSE-100 hourly on weekdays 9:50 am–4:50 pm, headlines/updates every 4 hours). For this code, the JSON files hold the figures as of 6 Oct 2026, 4:30 pm; they need the same refresh pointed at this repo to stay current.

### Sources checked (6 Oct 2026)
Dawn, Business Recorder, TechX, UrduPoint, Times of Karachi (fuel, gold, silver, currency); Business Recorder and KSE Alert (KSE-100); Pakera (Punjab helpline 08000-9211, KP mobile vets); ProPakistani (Punjab mobile vet fleet); ICT Administration (ICT vet hospitals); Arab News (Richmond Crawford hospital); Jhang and Sialkot district livestock pages; Paltuu.pk and PetPitari (private clinics).
