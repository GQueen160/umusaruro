# Implementation report

What was built on `dev`. The classification engine and the published Season A numbers were kept. The product is no longer a maize action sheet. It is a cultivation advisor: farmer, sector, district, and ministry, from before planting to after harvest, with each finding kept under the crop it belongs to.

The farmer still starts on the map. Planners start at `/advisor/`, where the crops the survey prints are grouped (cereals, roots and tubers, banana, legumes, garden and other). Each crop page has the three stages and the district yield table. Irrigation, all-crop seed, and fertilizer stay on `/sheet/`, because those tables are not split by crop. Maize keeps the PSTA 5 comparison and the eight-year series. The other crops are not scored against that milestone.

## What the farmer sees

Open `http://127.0.0.1:8000/`.

The page is a full-screen street map (Leaflet 1.9.4 on OpenStreetMap tiles). The farmer can pan, zoom, search, or walk the official hierarchy:

**akarere → umurenge → akagari → umudugudu**

Choosing a village, or tapping the map, drops a pin. The farmer then taps a crop. Crop names are in Kinyarwanda, with a short English line under each one: ibigori, ibishyimbo, umuceri, ibirayi, ibijumba, imyumbati, amasaka, ibitoki, imboga, soya, ubunyobwa, ingano. Up to four crops can be selected together.

The sheet then shows short advice and a yield target in kilograms per hectare. **Bika intego** stores that target for the village. **Aho ndi** uses the phone or browser location when the device allows it. **Vuga** starts the browser’s speech recognition in `rw-RW` and leaves the words on the screen as a short conversation: what was said, then the reply.

The old planner sheet is still available at `/sheet/`, with its district pages and `/method/`.

## What was added

| Path | Role |
| --- | --- |
| `farm/` | New Django app. It is the homepage. |
| `farm/places.py` | District, sector, cell, and village lookup, search, and “which village is this tap”. |
| `farm/advice.py` | Advice cards and the suggested yield target. |
| `farm/talk.py` | Turns a spoken or typed sentence into a place and crops. |
| `farm/models.py` | `FieldPlan`: village, crops, and the saved target. |
| `farm/templates/farm/home.html` | Map page. |
| `farm/static/farm/farm.js`, `farm.css` | Map, search, cascade, crops, advice, voice. |
| `data/reference/villages.csv` | 14,823 village centroids. |
| `tools/fetch_villages.py` | Rebuilds that file from the NISR layer. |

`config/urls.py` serves `farm` at `/` and the existing `sheet` app beside it. The sheet’s own overview moved from `/` to `/sheet/`.

## Data the map uses

Village points come from the NISR open-data layer **Village Boundary 2022** (`tools/fetch_villages.py`). Only the centroid is stored, not the polygon. The file has 30 districts, 416 sectors, 2,148 cells, and 14,823 villages. Codes nest: village code starts with the cell code, which starts with the sector code, which starts with the district code. The source spells one province “Estern Province”; the loader shows that as “Eastern Province”.

A tap is matched to the nearest village inside the district outline in `data/boundaries/rwa_districts.geojson`. Those outlines are the simplified geoBoundaries file already in the repo. They only decide which district the tap fell in. Rainfall is not computed from them.

## How advice is made

`farm/advice.py` reads the files that were already on `dev`:

- `data/season_a_2026/cells.csv` through `umusaruro.cells`
- `data/chirps/season_a_2026_rainfall.csv` through `umusaruro.rainfall`
- `umusaruro.rules.classify` for the same cutoffs the district sheet uses (irrigation gap 30 points and smallholder irrigation under 15%, seed gap 25 points, fertilizer lag 15 points)

For Nyagatare maize the first card is **Voma**, because small farms irrigate much less than large farms and September–February rainfall is below the district median. The suggested target is **5,292 kg/ha**, the large-farm maize yield in Table 14. If that large-farm cell is blank, as it is for Karongi maize, the target falls back to the district yield in Table 13 (1,517 kg/ha). A blank cell is not shown as zero.

When more than one crop is chosen, the card names the one with the higher published district yield. That comparison is between crops in the survey tables. It is not a named seed variety.

Every card says the figures are for the district. The Seasonal Agricultural Survey is not published per village, so the pin selects the place and the numbers stay the district’s.

## What this build does not do

- It does not invent a soil test. The page says the report has none.
- It does not name a maize variety. Table 20 is improved seed for all crops. Table 21’s maize figure is national only, and the card says so.
- It does not train a model. “Learns the area” here means it reads the published district tables and the rainfall gate for the place the farmer picked.
- It does not replace the engine in `engine/`. That loader is unchanged. The farmer page does not need `engine_load_sas`; it reads the CSV files.
- Voice depends on the browser. If Kinyarwanda recognition is missing, the button says so and the map and crop buttons still work. There is no separate speech model in this repository.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Farmer map |
| GET | `/api/boundaries/` | District outlines |
| GET | `/api/places/` | Next level of the hierarchy |
| GET | `/api/search/?q=` | Village search |
| GET | `/api/locate/?lat=&lon=` | Nearest village to a tap |
| POST | `/api/advice/` | Advice for a district and a list of crops |
| POST | `/api/hear/` | Transcript to place, crops, and advice |
| GET | `/api/plans/` | Latest saved targets |
| POST | `/api/plans/save/` | Save a target; a village is required |

## How to run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DJANGO_DEBUG=1
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Then open `http://127.0.0.1:8000/`.

`DJANGO_DEBUG=1 .venv/bin/python manage.py test farm` runs the farmer tests: a tap in Gitega resolves to the village Gihanga, Nyagatare maize advises irrigation and targets 5,292 kg/ha, a blank large-farm cell is not zero, a shared village name is not guessed, and a target is stored only when a village was chosen.
