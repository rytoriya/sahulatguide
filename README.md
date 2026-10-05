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
| `fees/` | Pay school, college, university, board and test fees online: 1Bill/Kuickpay how-to, exact codes for major institutions, and 500+ institutions from 1Link's 1Bill biller list (data inline in the page) |
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

## Settings

- WhatsApp contact number: set `WHATSAPP_NUMBER` near the top of the script in `index.html` (e.g. `"923001234567"`).
- The contact form saves messages only when hosted as a Claude artifact; on a normal web host it falls back to "Send on WhatsApp".

## Preview locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000.
