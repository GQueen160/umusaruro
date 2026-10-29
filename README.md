# Umusaruro

Umusaruro is the Kinyarwanda word for harvest.

## What this system is

Umusaruro is a map for one growing season in Rwanda. You say who you are, find the place, and pick the crop. The screen then shows what the national survey printed for that district: the harvest, and a short note on water, seed, and fertilizer. You can read it in English, French, or Kinyarwanda.

A number on the screen is a number from a published table. If the table left a cell blank, the screen leaves it blank.

## What problem it is tackling

A farmer and an agricultural officer need the survey figure for their own place, not a national average pasted onto the map. The reports are long, and they are not written as a next step for one village or one district. This system turns those published cells into a short reading: what was harvested here, and whether small farms in this district irrigate or use improved seed and fertilizer less than the large farms beside them.

## Who it is for

- A mini farm, with one small plot. Find the village, pick the crop, read the cards, and save a yield to aim for. The aim is the district harvest.
- A large farm. The same field. The aim is the large-farm harvest when the survey printed it.
- A sector agricultural officer. Find the sector on the map, then open that district. The survey is not printed per sector.
- A district agricultural officer. See the 30 districts, and the action the rules name for each one.
- A planner at the Ministry of Agriculture. Read every crop, then the district map for water, seed, and fertilizer.

## How to start it

From this folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DJANGO_DEBUG=1
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The first screen asks who is reading.

Video demo: [YouTube channel](https://www.youtube.com/@umusarurotv1228).
