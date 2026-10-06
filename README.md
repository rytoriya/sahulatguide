# Sahulat Guide (sahulatguide.pk)

Static website explaining Pakistani government services, schemes, loans, travel and delivery, step by step. Plain HTML, CSS and JavaScript — no build step needed to serve it.

## Pages

| Path | What it is |
|---|---|
| `index.html` | Main site: service guides, emergency helplines, calculators, portals, contact |
| `passport/` | Passport services tool: office finder, fee calculator, timings, renewal, visa help |
| `route-planner/` | Road route planner between Pakistani cities |
| `trains/` | Train finder: timetables and estimated fares (generated from `content/trains.md`) |
| `parcels/` | Parcel guide: courier prices and rules (generated from `content/parcels.md`) |
| `police/` | Police Station Directory: all 175 districts by province and division; official station lists with phone numbers and SDPO circles (38 districts, 506 stations) from `data/police-stations.txt`; each district's police stations located on a map (OpenStreetMap via Nominatim + Overpass, matched to official names), distance from the visitor. Rebuild with `node scripts/build_police.js` then `node scripts/build_search_index.js`. |
| `universities/` | Government Universities: 134 public universities by province and type; entry test calendar (MDCAT, NUST NET, ECAT, ETEA, USAT, LAT, NAT/GAT, PIEAS, IBA, NED, MUET, PU and others) with dates, fees, paper pattern, pass marks and merit formulas; fees and admission criteria for 39 universities, each with its source, session year and a confidence label. Data is hand-edited in `universities/data.js` (checked 6 Oct 2026); run `node scripts/build_search_index.js` after editing. |
| `emergency/` | City-wise police stations with official phone numbers (Islamabad, KP cities, Nankana; district police and Rescue 1122 offices for Punjab), plus police, Rescue 1122 and fire stations on a Leaflet map loaded live from OpenStreetMap (Overpass API) with distance from the visitor. City list and numbers are inline in the page. |
| `fees/` | Pay school, college, university, board and test fees online: 1Bill/Kuickpay how-to, exact codes for major institutions, and 500+ institutions from 1Link's 1Bill biller list (data inline in the page) |
| `account/` | My details: sign up / log in, save name, mobile, CNIC, address once; copy buttons; autofills site forms |
| `hospitals/` | Find a hospital: 251 Punjab government and private hospitals, nearest to your town, filters, care-level guide (data in `hospitals/data.js`) |
| `jobs/` | Government jobs: important commission and armed forces recruitment from `data/jobs.json` |
| `rates/` | Daily rates: petrol and diesel, gold and silver, open-market currency, KSE-100 and most active shares, converter and source links. Reads `data/rates.json` and `data/stocks.json`; re-checks every 5 minutes. |
| `vets/` | Find a vet: nearest government vet hospital (every Punjab tehsil, ICT, Karachi, Peshawar, university hospitals), private clinics by city, emergency helplines, animal first-aid helper and weight estimate. Data in `vets/data.js`. Vet guides live in the Farmers category of `index.html`. |
| `admin-units/` | Directory of every division, district and tehsil in Pakistan, council tiers and official election-office numbers (data is inline in the page script, checked 6 Oct 2026) |

## Editing the train and parcel guides

Edit the Markdown in `content/`, then rebuild the HTML pages:

```sh
pip install markdown
python3 scripts/build_guides.py
```

## Site-wide search

Every page has a Search button (shortcuts: `/` or `Ctrl/Cmd+K`) that searches all service guides, categories, tools, guide sections, and every division, district and tehsil. On the homepage, the header search box covers guides, and its "no results" message opens the full search.

- `search.js` — the search button and pop-up. Add `<script src="search.js" defer></script>` (adjust the path) to a page, and put `<span data-sg-search></span>` where the button should go (`data-sg-search="on-dark compact"` for dark headers or icon-only on phones). Without a slot, a floating button appears.
- `search-index.js` — generated data. After adding or changing guides, tools or the directory, rebuild it:

```sh
node scripts/build_search_index.js
```

## Live rates and news

`live-feeds.js` (loaded on the homepage and `rates/`) reads four JSON files in `data/` and re-checks them every 5 minutes:

- `data/rates.json` — fuel, gold/silver, open-market currency (home rate boxes, Daily rates page)
- `data/stocks.json` — KSE-100 and most active shares (home KSE-100 box, Daily rates page)
- `data/headlines.json` — Headlines ticker
- `data/updates.json` — Updates ticker
- `data/jobs.json` — Government jobs panel and `jobs/` page
- `data/scores.json` — Pakistan sports panel

Update these files to change the figures; no rebuild is needed. Formats are in `CHANGES.md`.

## Accounts and saved details

`account.js` (loaded on every page) adds a **Sign in / My details** button and fills any form field marked `data-profile="name"` (keys: `name father mobile email cnic dob city district province address`).

- **Without setup** the site runs in *device-only* mode: details are saved in the visitor's own browser.
- **CNIC never leaves the device**, even when signed in. `firestore.rules` also rejects any server write containing a `cnic` field.

To switch on real accounts (email/password and Google), using Firebase's free plan:

1. Go to console.firebase.google.com → **Add project**.
2. **Build → Authentication → Get started**, then enable **Email/Password** and **Google**.
3. In Authentication → **Settings → Authorized domains**, add your site's domain (e.g. `sahulatguide.pk`).
4. **Build → Firestore Database → Create database** (production mode, a region near Pakistan such as `asia-south1`).
5. In Firestore → **Rules**, paste the contents of `firestore.rules` and **Publish**.
6. **Project settings → Your apps → Web (</>)**, register the app, copy the `firebaseConfig` values into `firebase-config.js` (`window.SG_FIREBASE_CONFIG = { ... }`).

These config values are meant to be public; access is controlled by the rules.

## Settings

- WhatsApp contact number: set `WHATSAPP_NUMBER` near the top of the script in `index.html` (e.g. `"923001234567"`).
- Owner details for the About, Privacy and Terms pages: set `SITE_OWNER`, `SITE_CITY`, `SITE_EMAIL` and `SITE_DOMAIN` next to it.
- The contact form saves messages only when hosted as a Claude artifact; on a normal web host it falls back to "Send on WhatsApp".

## Preview locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Page addresses

Every tab and guide of the main app has its own address, for example `/services/identity/cnic-renewal/`.
`scripts/build_routes.js` copies `index.html` to one folder per address with its own title and description,
and writes `sitemap.xml`. Netlify runs it on every deploy (see `netlify.toml`); the generated folders are in `.gitignore`.

To preview locally:

```sh
node scripts/build_routes.js
python3 -m http.server 8000
```
