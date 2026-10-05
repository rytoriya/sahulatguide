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

## Editing the train and parcel guides

Edit the Markdown in `content/`, then rebuild the HTML pages:

```sh
pip install markdown
python3 scripts/build_guides.py
```

## Settings

- WhatsApp contact number: set `WHATSAPP_NUMBER` near the top of the script in `index.html` (e.g. `"923001234567"`).
- The contact form saves messages only when hosted as a Claude artifact; on a normal web host it falls back to "Send on WhatsApp".

## Preview locally

```sh
python3 -m http.server 8000
```

Then open http://localhost:8000.
