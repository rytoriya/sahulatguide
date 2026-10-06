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
| `emergency/` | City-wise police stations with official phone numbers (Islamabad, KP cities, Nankana; district police and Rescue 1122 offices for Punjab), plus police, Rescue 1122 and fire stations on a Leaflet map loaded live from OpenStreetMap (Overpass API) with distance from the visitor. City list and numbers are inline in the page. |
| `fees/` | Pay school, college, university, board and test fees online: 1Bill/Kuickpay how-to, exact codes for major institutions, and 500+ institutions from 1Link's 1Bill biller list (data inline in the page) |
| `account/` | My details: sign up / log in, save name, mobile, CNIC, address once; copy buttons; autofills site forms |
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
- The contact form saves messages only when hosted as a Claude artifact; on a normal web host it falls back to "Send on WhatsApp".

## Preview locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000.
