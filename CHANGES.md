# Changes

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
