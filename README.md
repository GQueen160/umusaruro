# Umusaruro

Umusaruro is the Kinyarwanda word for harvest.

The survey already printed the harvest for each district. What a farmer or an officer still has to do is find their own figure inside a long national report. Umusaruro does that search. You say who you are, you find the place, you pick the crop, and the screen shows the harvest for that district, with a short reading on water, seed, and fertilizer.

**Start here:** [umusaruro-production.up.railway.app](https://umusaruro-production.up.railway.app/)

The first screen asks who is reading. You can follow the whole visit in English, French, or Kinyarwanda.

## What this solves

A national table answers a national question. The person in front of it is asking a local one: what was harvested here, and do the small farms in this district irrigate, or use improved seed and fertilizer, less than the large farms beside them. Umusaruro keeps the published cell and speaks it to that person.

- A mini farm finds the village, picks the crop, reads the cards, and saves a yield to aim for. The aim is the district harvest.
- A large farm walks the same field. The aim is the large-farm harvest when the survey printed it.
- A sector officer finds the sector, then reads that district. The survey has no sector table, so the figures stay the district's, and the screen says so.
- A district officer sees the 30 districts, and the action the rules name for each one.
- A planner at the Ministry of Agriculture reads every crop, then the district map for water, seed, and fertilizer.

Every number on the screen comes from a published table. A blank cell stays blank.

## How you move through it

1. Choose who is reading.
2. Find the place. Search a village, tap the map, or walk from district to sector, cell, and village.
3. Pick the crop.
4. Read the harvest, and the note on water, seed, and fertilizer.
5. A farmer saves the aim and keeps a plan for the season. A district or sector officer sees only the place they chose.

The chat on the same screen answers a question about a village, a district, or a crop, using those same published figures, in the same three languages.

## Where the numbers come from

The harvest, water, seed, and fertilizer numbers are the Seasonal Agricultural Survey of the National Institute of Statistics of Rwanda, from 2019 through Season B 2026. The workbooks are in `data/raw/sas/`. Each workbook's download link and publication page are in `data/raw/MANIFEST.csv`. The survey collection is the [Seasonal Agricultural Survey](https://statistics.gov.rw/data-sources/surveys/Seasonal-Agricultural-Survey).

Village, cell, sector, and district names are the NISR Village Boundary 2022 layer, saved in `data/reference/`. Season A 2026 rain is CHIRPS, in `data/chirps/`, from [CHIRPS](https://www.chc.ucsb.edu/data/chirps). District outlines are in `data/boundaries/`, from [geoBoundaries](https://www.geoboundaries.org/). The maize country goal is the PSTA 5 milestone, from the [abridged results framework](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf).

## Run it yourself

The public app above is the same visit. To run it on your own machine, from this folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DJANGO_DEBUG=1
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The first screen asks who is reading.
