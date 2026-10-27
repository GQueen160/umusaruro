# Umusaruro

Umusaruro is a district maize action sheet for Rwanda. For each of the 30 districts, it shows Season A 2026 maize yield against the national PSTA 5 milestones. It then names the lever the published survey tables support: irrigation, or improved seed. Inorganic fertilizer is named on the same sheet when that table lags.

The readers are a district agronomist and a planner at the Ministry of Agriculture and Animal Resources (MINAGRI). They read the sheet. They do not type figures into it. Every number on a screen names its survey, table, and year. A blank in the source table stays blank. It is never shown as zero.

*Umusaruro* is Kinyarwanda for harvest. The project is an entry in the agriculture track of the [NISR 2026 Big Data Hackathon](https://statistics.gov.rw/about/hackathon/2026-hackathon-competition).

## The problem

Rwanda's agriculture strategy, PSTA 5, sets a maize yield path measured by the Seasonal Agricultural Survey (SAS): 2.06 tonnes per hectare in 2025/26 and 2.26 in 2026/27. Season A 2026, the main maize season, came in at 1.99 t/ha for all farms. That is under both milestones.

The gap is not spread evenly. In the same season, smallholders averaged 1.90 t/ha and large farms 4.34 t/ha (SAS Season A 2026, Table 13). Only two districts, Nyagatare and Kirehe, reached 2.26.

The question is already on the national agenda. In June 2026, Parliament summoned the agriculture minister over maize yield of 2.0 against the 2.26 target. Resolution 3 of the 20th Umushyikirano, in February 2026, names fertilizer, improved seed, and irrigation as the productivity levers. At the March 2026 leadership retreat in Gako, the message was that the inputs exist and the failure is follow-through.

What a district office lacks is one page that says, from published numbers, which of those levers its own smallholders are furthest behind on.

## What the sheet shows

For one district:

1. Season A 2026 maize yield, in kg/ha as printed, and in t/ha.
2. Whether that yield is above or below the PSTA 5 milestone for the named year.
3. How far smallholders are behind large farms in the same district, on irrigation, improved seed, and inorganic fertilizer.
4. One action, irrigation or seed, from fixed rules. Fertilizer is named beside the action when it lags.
5. The survey, table, year, and source link for every number.

## Why maize

Maize is the crop where a government target, a district-level survey figure, and an open public question all line up.

- PSTA 5 has a maize yield milestone, measured with the same survey that prints district yields.
- Season A is the main maize season, and its report prints maize yield for every district.
- Large farms show what a higher yield looks like under the same season and survey: 4.34 t/ha against 1.90 for smallholders.

Beans do not work the same way. Large farms average 0.54 t/ha against 0.70 nationally, so there is no large-farm level to catch up to.

## Why irrigation, seed, and fertilizer

These are the only three inputs where the Season A report prints district figures split by farm type, smallholders (SSF) against large-scale farms (LSF):

| Lever | Table | What the table measures |
| --- | --- | --- |
| Irrigation | 31 | percentage of farmers who irrigated |
| Improved seed | 20 | percentage of farmers who used improved seed, **all crops** |
| Inorganic fertilizer | 25 | percentage of farmers who used inorganic fertilizer, all crops |

That split lets a sheet say how far behind a district's smallholders are, compared with large farms in the same district. They are also the three levers named in the Umushyikirano resolution.

Each lever has a limit the sheet states plainly.

- **Seed means all crops.** Table 20 covers every crop. The maize seed rate, 64.3% improved, is Table 21, and it is national only, with no district column. The sheet says "all-crop seed", never "maize seed".
- **Irrigation is gated by rainfall.** A district with a wide irrigation gap but above-median rain is not told to irrigate first.
- **Fertilizer is a note, not the action.** It is named beside the main action and never replaces it.
- **A gap is not a cause.** Each figure compares two kinds of farm. The sheet does not claim that closing a gap raises yield by a set amount.

## Datasets used

| Dataset | Publisher | What this project takes | In the repository |
| --- | --- | --- | --- |
| [Seasonal Agricultural Survey, Season A 2026](https://statistics.gov.rw/sites/default/files/documents/2026-04/SAS%202026%20Season%20A%20_Final%20Report.pdf) | NISR | Tables 13, 14, 16, 20, 21, 22, 25, and 31, transcribed cell by cell | `data/season_a_2026/cells.csv` |
| [Seasonal Agricultural Survey, Season B 2026](https://statistics.gov.rw/sites/default/files/documents/2026-09/SAS%202026B_Main%20report.pdf) | NISR | Tables 18, 23, and 29, transcribed from the report and checked against the [tables workbook](https://statistics.gov.rw/sites/default/files/documents/2026-09/Tables_2026%20Season%20B.xlsx). Shown beside Season A as a check. | `data/season_b_2026/cells.csv` |
| [PSTA 5, abridged results framework](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf) | MINAGRI | Maize yield milestones: 1.70 (2023 baseline), 1.87, 2.06, 2.26, 2.49, 2.74 t/ha | the evidence contract |
| [CHIRPS v2.0, Africa monthly](https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/) | Climate Hazards Center, UC Santa Barbara | Rainfall, September 2025 to February 2026, summed per district | `data/chirps/season_a_2026_rainfall.csv` |
| [geoBoundaries, Rwanda ADM2](https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM2/) | geoBoundaries, from Open Data Rwanda, CC BY 4.0 | The 30 district boundaries: full detail to sum rainfall, simplified to draw the map | simplified copy in `data/boundaries/rwa_districts.geojson` |
| SAS tables workbooks, 2019 to 2026 (one per year, listed in `data/raw/MANIFEST.csv`) | NISR, CC BY 4.0 | Season A district maize yield, large-farm maize yield, and farmers using improved seed, inorganic fertilizer, and irrigation, by farm type. Built into a back-series, shown as the trend charts and the map's trend layer. The evidence contract does not yet name it; that update is the next step. | raw files in `data/raw/sas/`, cleaned in `data/history/season_a.csv` |
| [Sector Boundary 2022](https://services5.arcgis.com/deNm5epdmeZgcm16/arcgis/rest/services/Sector_Boundary_2022/FeatureServer/1) | NISR | Official province, district, and sector codes (attributes only) | `data/reference/districts.csv`, `data/reference/sectors.csv` |

Season A 2026 is the base file because it is the latest report that prints district maize yield and district irrigation by farm type together. It covers the main maize season. It is not the whole year.

### Read for context, not on the sheet

| Dataset | Why it is not on the sheet |
| --- | --- |
| [SAS Season B 2026, district maize yield](https://statistics.gov.rw/statistical-publications/agriculture-environment/seasonal-agricultural-survey-season-b-2026) | Tables 11 and 12 print Season B district yields, but the evidence contract does not name them, and Season B is the smaller maize season. Only the input tables are used. |
| [SAS 2025 microdata, catalog study 124](https://microdata.statistics.gov.rw/index.php/catalog/124) | Not used until a weighted run reproduces a published national rate, such as 64.3% maize improved seed. It has no variety name and no satisfaction score. No 2026 microdata is on the catalog. |
| [Agricultural Household Survey 2024](https://statistics.gov.rw/sites/default/files/documents/2025-10/AHS%202024_Main%20report.pdf) | Provincial, not district. Its farmer-reason questions on irrigation are not a district table. |
| [RwaSIS](https://www.rab.gov.rw/1-1/news-details/rab-launches-rwanda-digital-soil-information-system-to-improve-agricultural-productivity) | RAB's soil and fertilizer recommendation system. Maize recommendations were still in testing at the November 2024 launch. This project does not replace it. |
| [NST2 2024–2029, abridged](https://www.minecofin.gov.rw/fileadmin/user_upload/Minecofin/Publications/STRATEGIES/NST_2/NST2_2024-2029_Abridged.pdf) | Context for national irrigated-area targets. This project does not re-estimate irrigated hectares. |

## Method

### Transcription

`tools/transcribe_season_a.py` reads a text extract of the NISR PDF and writes one row per printed cell. Yields stay in kg/ha, as printed. Showing t/ha means dividing by 1,000 and rounding half up to two decimals.

A blank is an empty value. The `printed` column records why:

| printed | meaning |
| --- | --- |
| `number` | the PDF printed a number, stored without thousands separators |
| `dash` | the PDF printed a dash |
| `empty` | the column was left empty |
| `absent` | the district has no row in that table |

`Cell.number()` in `umusaruro/cells.py` raises `BlankCell` for every case except `number`. A blank is never read as zero. A printed zero stays zero.

The script refuses to write the file unless the national figures in the contract reproduce: maize 1,897, 1,994, and 4,337 kg/ha, and irrigation 12.6% of smallholders and 60.3% of large farms.

### Season B, as a check

`tools/transcribe_season_b.py` reads the Season B report the same way, with the same column parser and the same blank rules. It writes Tables 18 (seed), 23 (inorganic fertilizer), and 29 (irrigation) to their own file, `data/season_b_2026/cells.csv`. These table numbers are not the Season A numbers. Season B loads into its own object, so it cannot stand in for a Season A cell.

The NISR workbook is read only to check the report. Every one of the 930 transcribed cells must equal the workbook value rounded to the digits the report printed. A printed dash must be an empty or zero workbook cell. Where the workbook stores a zero and the report prints a dash, as for large-farm seed in Nyarugenge and Ngororero, the cell stays blank. The report's dash is what a reader sees, and the report uses it both for zero and for no data.

**The Table 29 footer.** In the workbook, Table 29 is titled "2026 Season B", but its footer reads "Source: NISR, SAS 2025". Every other sheet says SAS 2026. The printed report, page 57, reads "Source: NISR, SAS 2026". The report's own text gives the same national rates as the table: 13.1% of farmers, 11.5% of smallholders, and 56.2% of large farms. Both footers are recorded in `data/season_b_2026/footer_check.csv`. The evidence contract requires a person to resolve this, so the pages show Season B irrigation only after someone types the footer they read on the printed page, with their name and the date (see below). Mukunzi Jonathan read "Source: NISR, SAS 2026" on page 57 on 22 October 2026, so Season B irrigation is shown.

On each district page, Season B gets the same cutoffs, without the rainfall gate, since the rainfall window is Season A's. The page says whether the named lever would also pass in Season B. It never changes the action. With the committed files, the seed gap also reaches its cutoff in 15 of the 19 seed districts. It does not in Rubavu (24.9 points), Gakenke, or Bugesera, and Ngororero has no Season B gap. The irrigation gap also reaches its cutoff in 6 of the 7 irrigation districts. Nyagatare is the exception, at 27.4 points against 30.

### Raw files, codes, and the 2019–2026 back-series

**Raw files.** Every file downloaded from a publisher sits unedited under `data/raw/`. `data/raw/MANIFEST.csv` gives each file's download URL, the NISR page that links it, the publisher, the licence, the day it was retrieved, its size, and its SHA-256. `python3 tools/raw_manifest.py record` downloads every URL again and refuses to write the manifest unless the download equals the local file byte for byte. All nine SAS workbooks passed on 22 October 2026. CI runs `python tools/raw_manifest.py`, which fails if a raw file changes or is not listed.

**Codes.** `tools/fetch_reference.py` reads the attribute table of NISR's Sector Boundary 2022 layer. It writes 416 sectors and 30 districts with their official codes: province 1 to 5, district 11 to 57, sector 1101 to 5715. It checks that the codes nest and that the 30 district names, in order, are the names the SAS tables print. Cleaned tables join on `district_id`, not on spelling.

**Back-series.** `tools/build_history.py` reads one Season A table set per year from the workbooks, 2019 to 2026, and writes `data/history/season_a.csv`. There are five measures:

| lever | measure | farm types | unit |
| --- | --- | --- | --- |
| `maize_yield` | average maize yield | all (national row also by farm type) | kg/ha |
| `maize_yield_lsf` | average maize yield on large farms | large | kg/ha; t/ha in 2019, as printed |
| `seed` | farmers who used improved seed | all, smallholder, large | % |
| `fertilizer` | farmers who used inorganic fertilizer | all, smallholder, large | % |
| `irrigation` | farmers who practised irrigation | all, smallholder, large | % |

Table numbers change every year, and so do the header layouts (2019 splits each farm type into Yes/No or Traditional/Improved columns; 2024 adds a Cereals column). The builder finds each column by its header text and stops if a column cannot be found exactly once. `data/history/quality.csv` records, for each year and measure, the table number, its full title as printed in the workbook, the count of numbers and blanks, the national value, and the district range, so a reader can see what was read.

The rules are the ones used for the printed tables. A value is rounded half up to the digits the reports print: whole kg/ha, one decimal for percentages. The unrounded workbook value is kept beside it. An empty cell, a dash, or a zero is a blank, recorded as `empty`, `dash`, or `zero`. A district with no row is `absent`. The reports print a workbook zero as a dash, so it is not shown as zero.

The builder writes nothing unless these checks pass:

- 30 districts in every district table
- percentages between 0 and 100, yields above zero
- the national value inside the district range
- the national large-farm maize yield equal in both yield tables of a year
- every 2026 value equal to the printed Season A 2026 report cell already transcribed in `data/season_a_2026/cells.csv`; all 343 agree, blanks included

With the committed files the series has 2,742 rows, 2,487 of them numbers. The workbooks are NISR's own published tables, but for 2019 to 2025 they have not been checked against the printed reports cell by cell. Definitions can move between years. For example, 38.6% of farmers used inorganic fertilizer in Season A 2022 and 59.6% in 2023. The titles in `quality.csv` are the place to start before reading a change as a trend.

### Rainfall gate

`tools/chirps_gate.py` sums the six monthly CHIRPS rasters. A district's total is the mean of the six-month sums at the 0.05° grid cells whose centres fall inside the district. The cell count is stored beside the total. Kicukiro rests on 7 cells and Nyarugenge on 2, so those totals are thin.

The median of the 30 totals is 689.25 mm. 15 districts are below it. Rainfall gates irrigation only. It never replaces a NISR cell, and it is not the farmer's reason for irrigating or not.

### Rules

`umusaruro/rules.py` holds the cutoffs. They are the team's, not NISR thresholds.

| Constant | Value | Meaning |
| --- | --- | --- |
| `IRRIGATION_GAP` | 30 | large-farm irrigation minus smallholder irrigation, in points |
| `IRRIGATION_SSF_MAX` | 15 | smallholder irrigation must be under this percent |
| `SEED_GAP` | 25 | Table 20 gap, all crops, in points |
| `SEED_LEAD` | 5 | if seed's lead over irrigation is smaller than this, irrigation stays |
| `FERTILIZER_GAP` | 15 | Table 25 gap that gets fertilizer named |

A district is an irrigation candidate when both irrigation figures exist, the gap is at least 30 points, and fewer than 15% of smallholders irrigate. It becomes the action only when the district's rainfall is below the median. Seed fires when the Table 20 gap is at least 25 points. If both fire, the larger gap is the action, unless seed leads by less than 5 points. A blank large-farm cell cannot open a gap.

`classify(cells, district, rainfall_below_median)` returns a `Decision`. `classify_all(cells, rainfall)` runs all 30 districts.

## Results with the committed files

- **Irrigation, 7 districts:** Gatsibo, Kayonza, Kicukiro, Kirehe, Ngoma, Nyagatare, Rwamagana.
- **All-crop seed, 19 districts.**
- **No action, 4 districts:**
  - Nyarugenge and Karongi have a blank large-farm cell, so no gap can be computed.
  - In Nyanza and Rusizi, at least 15% of smallholders already irrigate, and the seed gap is under 25 points.

Ten districts meet the irrigation numbers. Rainfall removes Karongi, Nyamasheke, and Nyamagabe, which are wetter than the median.

Some results sit one tenth of a point from a cutoff:

- Kirehe smallholder irrigation is 14.9%, against the 15% line.
- Muhanga is 15.2%, so it is not a candidate.
- Gakenke's irrigation gap is 28.7 points, against 30.
- Rwamagana's seed gap is 24.5 points, against 25.

Seed fires in 19 districts and fertilizer is named in 26, because large farms report high input use almost everywhere. Of those 26, 24 sit beside an action; in Nyanza and Karongi, fertilizer is named although no action is. Read those labels as the common case, not as a finding specific to one district. The cutoffs were written into the evidence contract before this rainfall file was computed, and they have not been tuned to its results.

## The engine

The engine, in `engine/`, reads any district table it is given, for any crop, and keeps every value with the row and column it came from. A person confirms what the engine proposes before anything is published.

1. **Read.** `engine/reader.py` opens an `.xlsx` or `.csv` file and returns each sheet as rows, as published. Old `.xls` files are refused with a reason.
2. **Propose.** `engine/detect.py` looks at every sheet. It finds the title, the year and season, and the rows that name a district. It then reads the header, forward-filling merged cells, and proposes what each column carries: a crop, a measure, a farm type (all, small-scale, large-scale), and a basis (share of farmers, plots, or land). Two layouts are understood. In the wide layout, the NISR one, districts run down the side and crops or farm types run across. In the long layout, there is one row per district (and year, crop) and one column per measure. Every skipped column gets a reason, for example "a total of several crops" or "the 'no' or 'traditional' share". A table whose title names nothing the engine reads is listed as not recognised. It is never guessed at.
3. **Confirm.** The proposals are stored. A person checks them, then publishes. The person's name is stored with the dataset.
4. **Store.** Each value becomes one row in the `Observation` table: year, season, NISR district code, crop, measure, farm type, basis, the value, the raw cell text, and the sheet row and column. An empty cell, a dash, and a workbook zero (which NISR prints as a dash) are stored with no value and their reason. A file is identified by its SHA-256, so the same file cannot be loaded twice.

The words the engine recognises (crops, measures, farm types, and the table titles to skip, such as "source of", "type of", and "degree of") are plain lists in `engine/vocab.py`, so a reviewer can read why a column was read as it was.

`python manage.py engine_load_sas --confirm-as "Full Name"` loads the nine SAS workbooks in `data/raw/sas/`. Each is checked against its SHA-256 in `MANIFEST.csv` and goes through the same detector as an upload. With the committed files, this gives 78,845 observations from 192 tables; 66,212 of them carry a number and the rest are blanks with their reason. They cover yield, cultivated and harvested area, and production for 23 crops and crop groups, and the use of improved seed, organic and inorganic fertilizer, pesticides, irrigation, erosion control, mechanization, and agroforestry, in Seasons A, B, and C, from 2019 to 2026.

The engine is checked against the hand-verified back-series. `tests/test_engine.py` reads every workbook the way an upload is read and requires each of the 2,735 values in `data/history/season_a.csv` to come out the same, blank reason included. The 7 districts that history records as absent from a table must produce no value.

The upload screens, the dataset list, and the per-crop analysis come in the next merge requests.

## The application

The sheet is a Django site in `sheet/`. The district sheet reads the committed CSV files when it starts. The engine's datasets and observations are kept in SQLite under `var/`, which git ignores.

| Page | What it shows |
| --- | --- |
| `/` | the national yield against both PSTA 5 milestones, a map of the 30 districts with four layers, and a table of every district's yield, action, and three gaps. Clicking a district opens its sheet in a side panel. |
| `/district/<name>/` | one district: the action and the reasons for it in sentences, yield against each milestone, maize yield across the eight Season A surveys since 2019 with the national line and the PSTA 5 milestone, the three levers with each gap's rank among the districts and, folded, each lever by farm type year by year, the Season B check, the rainfall gate, and how many of its cells a second person has checked |
| `/district/<name>/panel/` | the same sheet, shortened, as a fragment for the side panel |
| `/method/` | the rules and cutoffs, the districts within two points of a cutoff, the display rules, how Season B agrees with the actions, the Table 29 footer evidence, the workbook table read for each year of the back-series, and what the sheet does not claim |

### How "every number names its source" is enforced

The rule is enforced in code, not only by review.

1. `sheet/stats.py` defines `Source` (survey, table, year, link) and `Stat` (a value with its unit and source). A `Source` with any empty field raises an error. A `Stat` without a `Source` raises an error.
2. Templates print a number only through the `{% stat %}` tag. It refuses anything that is not a `Stat` and renders the value with a citation link. Hovering the citation shows the survey, table, and year. Clicking it opens the document.
3. A test parses every page and panel and fails on any digit outside a cited statistic or a marked reference such as "Table 31". It reads inside the SVG map and charts too: a chart's only text is its year labels and its milestone label, both marked as references. A second test checks that every citation has an `https` link and a three-part title.

Blank cells render as text that gives the reason, for example "blank (dash printed)". A gap with a blank side reads "no gap (a cell is blank)". Cells not yet signed by a second person carry a dotted underline.

Other figures follow the same rule. The cutoffs cite the evidence contract. Rainfall cites CHIRPS. A rank, such as "5 of 23 districts", cites the rules and the survey table it ranks. Districts with the same gap share a rank, and districts with a blank gap are not ranked.

### The map

`tools/district_map.py` downloads the geoBoundaries file pinned to commit `9469f09` and checks the 30 names against the Season A districts. It then simplifies the outlines with the Douglas–Peucker method, at a tolerance of 0.002 degrees, and writes the 64 KB file `data/boundaries/rwa_districts.geojson`. The site draws the map as inline SVG on the server, so the page needs no map library. The simplified outlines are for display only. Rainfall is still summed over the full-detail boundaries.

Each district on the map carries four layers, switched by the buttons above it:

| Layer | Colour means | Source |
| --- | --- | --- |
| Action | the action the rules name | rules on SAS Season A 2026 and CHIRPS |
| Milestones | 2026 maize yield at or above the 2026/27 PSTA 5 milestone (2.26 t/ha), between 2.06 and 2.26, or below 2.06 | SAS A 2026 Table 13, PSTA 5 |
| Trend | 2026 maize yield above every earlier Season A result of the same district since 2019, below every one, or in between | the back-series |
| Rainfall | September to February rainfall below or above the median of the districts | CHIRPS |

The trend layer compares a district only with itself. Survey estimates move between years by sampling alone, so a record is a reason to look, not a proven trend. With the committed files, Muhanga, Rulindo, Musanze, and Bugesera reach their highest Season A maize yield since 2019, and no district reaches its lowest.

`sheet/static/sheet/map.js`, about a hundred lines with no library, switches layers and opens the side panel. Without it, the map shows the action layer and every district links to its full page. The layer and the open district are kept in the address (`?layer=trend&d=bugesera`), so a view can be shared. Escape closes the panel, and focus returns to the district.

The trend charts are drawn on the server as SVG by `sheet/charts.py`. A blank year breaks the line; it is never drawn at zero. Under each chart, a table prints every plotted value with its citation, which names the workbook table and the year.

## What this project does not claim

- No maize variety. The survey records improved or traditional seed, not WH 403, WH 605, or WH 507.
- No farmer satisfaction score.
- No learned score of seed against soil and fertilizer.
- No district store or post-harvest ranking. Table 16 puts maize post-harvest loss at 0.3% of use, one national row.
- No national rate copied onto a district.
- No re-estimate of the NST2 irrigated-hectare total.
- No Season B or Season C figure in place of a Season A cell.
- No claim that the 2019–2025 tables use the same definitions every year.

## The evidence contract

[docs/Umusaruro-evidence-contract.pdf](docs/Umusaruro-evidence-contract.pdf) locks the product, with every source link. The editable copy is [docs/Umusaruro-evidence-contract.docx](docs/Umusaruro-evidence-contract.docx). A screen may show a number only when the contract names its survey, table, and year. Changing a cutoff means changing the contract first.

## Second-person check

Each cell a screen can show must be signed by a person against the printed PDF. A cell counts as checked only when that person's typed value matches the file. They type blind: the sign-off sheet does not show the stored value.

`data/season_a_2026/signoff.csv` lists 346 cells. They cover Table 13 maize, Table 14 maize, the Table 16 maize loss row, Tables 20, 25, and 31 by farm type, and the Table 21 maize and bush bean rows. Each row gives the PDF page, the table, the printed row, and the printed column.

1. Open the [Season A 2026 report](https://statistics.gov.rw/sites/default/files/documents/2026-04/SAS%202026%20Season%20A%20_Final%20Report.pdf). Table 13 is on page 39, Table 14 on page 40, Table 16 on page 42, Table 20 on page 46, Table 21 on page 47, Table 25 on page 50, and Table 31 on page 55.
2. Open `signoff.csv` in a spreadsheet. For each row, type the number you see in `value_on_page`, exactly as printed. Commas are fine. Type `-` for a dash, an empty column, or a district with no row.
3. Fill `checker` with your name and `checked_on` with the date as `YYYY-MM-DD`.
4. Run `python3 tools/apply_signoff.py`. Matching cells are marked `checked=true` in `cells.csv`. If any typed value disagrees, the script prints it and writes nothing. Look at the PDF again: either the typing or the transcription is wrong.
5. Commit both files on a branch and open a merge request. The pipeline fails if a typed value disagrees or if a cell is marked checked without a matching signature.

Two people can split the work by table. The sheet can be filled over several sittings. Rows left blank stay unchecked.

### Season B

`data/season_b_2026/signoff.csv` lists the 189 Season B cells the pages can show: smallholders and large farms in every district, plus the national row, for Tables 18, 23, and 29. Use the [Season B report](https://statistics.gov.rw/sites/default/files/documents/2026-09/SAS%202026B_Main%20report.pdf), where Table 18 is on page 46, Table 23 on page 51, and Table 29 on page 57. The steps are the same, and `tools/apply_signoff.py` checks both seasons at once.

To resolve the Table 29 footer, open page 57 and read the line under the table. In `data/season_b_2026/footer_check.csv`, on the row for table 29, type that line into `footer_on_page` exactly as printed, and fill `checker` and `checked_on`. Season B irrigation appears on the pages only when the typed line reads "Source: NISR, SAS 2026" and both other fields are filled.

## Repository layout

| Path | Contents |
| --- | --- |
| `docs/` | evidence contract (PDF and DOCX) and its generator |
| `data/season_a_2026/cells.csv` | transcribed Season A 2026 cells |
| `data/season_a_2026/signoff.csv` | second-person sign-off sheet |
| `data/season_b_2026/cells.csv` | transcribed Season B 2026 cells, Tables 18, 23, and 29 |
| `data/season_b_2026/signoff.csv` | Season B sign-off sheet |
| `data/season_b_2026/footer_check.csv` | report and workbook footers, and the person who resolved them |
| `data/raw/` | unedited downloads; `MANIFEST.csv` gives each file's URL, licence, and SHA-256 |
| `data/reference/` | official NISR province, district, and sector codes |
| `data/history/season_a.csv` | Season A back-series, 2019 to 2026 |
| `data/history/quality.csv` | what was read from each workbook table, and its title |
| `data/chirps/season_a_2026_rainfall.csv` | district rainfall totals |
| `data/boundaries/rwa_districts.geojson` | simplified district outlines for the map, CC BY 4.0 |
| `umusaruro/cells.py` | cell loader; blanks raise `BlankCell` |
| `umusaruro/rainfall.py` | rainfall loader |
| `umusaruro/rules.py` | cutoffs and `classify` |
| `umusaruro/signoff.py` | sign-off sheets and review, both seasons |
| `umusaruro/footers.py` | whether the Table 29 footer has been resolved by a person |
| `umusaruro/history.py` | back-series loader; blanks raise `BlankCell` |
| `umusaruro/xlsx.py` | standard-library XLSX reader used by the tools |
| `engine/vocab.py` | crops, measures, farm types, and title rules the engine recognises |
| `engine/reader.py`, `engine/detect.py` | read a file; propose how each table is read; read it into tidy rows (no Django) |
| `engine/models.py`, `engine/ingest.py` | datasets, tables, observations, crop targets; register and publish |
| `engine/management/commands/engine_load_sas.py` | load the SAS workbooks in `data/raw/sas/` |
| `config/` | Django settings, URLs, and WSGI entry point |
| `sheet/sheet.py` | builds each page's figures from the cells, rainfall, and rules |
| `sheet/stats.py` | `Source` and `Stat`: a number cannot exist without its source |
| `sheet/mapsvg.py` | projects the outlines into the SVG map |
| `sheet/charts.py` | geometry of the trend charts; every plotted value stays a cited `Stat` |
| `sheet/templates/`, `sheet/static/` | pages, shared page parts, style sheet, and `map.js` for layers and the side panel |
| `sheet/tests.py` | page tests, including the audit for numbers without a source |
| `tools/` | transcription, back-series, manifest, reference-code, rainfall, map, and sign-off scripts |
| `tests/` | unit tests for the data and rules modules |

## Running it

To run the site locally:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DJANGO_DEBUG=1
.venv/bin/python manage.py migrate
.venv/bin/python manage.py engine_load_sas --confirm-as "Your Name"
.venv/bin/python manage.py runserver
```

The database and uploads go in `var/`; set `UMUSARURO_VAR` to put them elsewhere. `engine_load_sas` takes about ten seconds and skips workbooks already loaded.

Then open <http://127.0.0.1:8000/>. `DJANGO_DEBUG=1` is for local work only.

In production, set `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` (comma-separated host names), then run:

```bash
python manage.py migrate
python manage.py engine_load_sas --confirm-as "Full Name"
python manage.py collectstatic --noinput
gunicorn config.wsgi
```

WhiteNoise serves the static files. Plain HTTP is redirected to HTTPS. Set `DJANGO_SSL_REDIRECT=0` only if the host already does that redirect.

The data and rules tests need only the Python standard library:

```bash
python3 -m unittest discover -s tests -v
```

The site tests need Django:

```bash
DJANGO_DEBUG=1 .venv/bin/python manage.py test engine sheet
```

To rebuild the map outlines:

```bash
python3 tools/district_map.py
```

To rebuild the cell file from the NISR PDF:

```bash
pdftotext -layout "SAS 2026 Season A _Final Report.pdf" /tmp/sas2026a.txt
python3 tools/transcribe_season_a.py /tmp/sas2026a.txt
```

To rebuild the Season B cells, download the [report](https://statistics.gov.rw/sites/default/files/documents/2026-09/SAS%202026B_Main%20report.pdf) and the [workbook](https://statistics.gov.rw/sites/default/files/documents/2026-09/Tables_2026%20Season%20B.xlsx), then:

```bash
pdftotext -layout "SAS 2026B_Main report.pdf" /tmp/sas2026b.txt
python3 tools/transcribe_season_b.py /tmp/sas2026b.txt "Tables_2026 Season B.xlsx"
```

The script stops if any cell disagrees with the workbook. It keeps any footer already typed in `footer_check.csv`.

To check the raw files, refresh the codes, and rebuild the back-series (standard library only):

```bash
python3 tools/raw_manifest.py          # every raw file against its SHA-256
python3 tools/fetch_reference.py       # NISR codes, needs network
python3 tools/build_history.py         # data/history/season_a.csv and quality.csv
```

To rebuild the rainfall totals, download the six monthly files (`chirps-v2.0.2025.09.tif.gz` through `chirps-v2.0.2026.02.tif.gz`) and the geoBoundaries GeoJSON into `/tmp/chirps`, then:

```bash
python3 -m venv .venv-geo
.venv-geo/bin/pip install rasterio shapely numpy
.venv-geo/bin/python tools/chirps_gate.py /tmp/chirps /tmp/chirps/rwa_adm2.geojson
```

The script stops if a district has no grid cell inside it, if a cell has no data, or if a boundary name differs from the Season A district names.

To regenerate the evidence contract:

```bash
python3 -m venv .venv
.venv/bin/pip install python-docx fpdf2
.venv/bin/python docs/build_evidence_contract.py
```

## Workflow

`main` is the line we submit. `dev` is where merge requests land. Each piece of work goes on its own branch and opens a merge request into `dev`. `dev` merges into `main` when a phase is accepted.

GitLab pipelines run on merge requests and on pushes to `dev` and `main`. There are two jobs:

- `evidence` compiles the Python modules, checks every raw file against `data/raw/MANIFEST.csv`, runs the unit tests (one rebuilds the back-series from the raw workbooks and requires the committed file), and checks that both copies of the evidence contract are present.
- `app` installs `requirements.txt` and runs the site the way it is deployed, with `DEBUG` off. It runs Django's system check, collects the static files, and runs the engine and site tests. Those tests load all nine SAS workbooks into a test database.

## Where the work stands

| Phase | Status |
| --- | --- |
| 1. Evidence contract | done, on `main` |
| 2. Season A cell file | on `main`; second-person sign-off open |
| 2b. Rainfall gate | computed; restored to `dev` by merge request !6 |
| 3. Rules | on `dev` |
| 4. Django application: map, district page, method page | on `dev` |
| 5. Season B 2026 beside Season A | built; Table 29 footer confirmed; Season B sign-off waits for a person |
| 6. Data pipeline: raw-file manifest, NISR codes, 2019–2026 back-series | on `dev` |
| 7. Map layers, side panel, and trend charts from the back-series | built |
| 9. Engine core: reader, detector, models, SAS preload | built |
| 10. Engine screens: dataset list, upload, review and confirm | next |
| 11. Per-crop analysis: drivers with validation, reports, comparison, map crop filter | after 10 |
| 8. Public repository, deployed link, submission | due 23:59, 30 October 2026 |

## Sources

Primary:

- [NISR 2026 Big Data Hackathon](https://statistics.gov.rw/about/hackathon/2026-hackathon-competition)
- [SAS Season A 2026, full report](https://statistics.gov.rw/sites/default/files/documents/2026-04/SAS%202026%20Season%20A%20_Final%20Report.pdf)
- [SAS Season B 2026, publication page](https://statistics.gov.rw/statistical-publications/agriculture-environment/seasonal-agricultural-survey-season-b-2026)
- [SAS 2025 annual report](https://statistics.gov.rw/sites/default/files/documents/2025-12/SAS%202025%20Final%20report.pdf)
- [SAS 2025 microdata catalog](https://microdata.statistics.gov.rw/index.php/catalog/124)
- [PSTA 5, abridged](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf)
- [NST2 2024–2029, abridged](https://www.minecofin.gov.rw/fileadmin/user_upload/Minecofin/Publications/STRATEGIES/NST_2/NST2_2024-2029_Abridged.pdf)
- [Resolutions of the 20th Umushyikirano](https://www.umushyikirano.gov.rw/fileadmin/user_upload/Umushyikirano/Imyanzuro/Resolutions_20th_UMUSHYIKIRANO_-_17_Feb_26.pdf)
- [Agricultural Household Survey 2024](https://statistics.gov.rw/sites/default/files/documents/2025-10/AHS%202024_Main%20report.pdf)
- [CHIRPS](https://www.chc.ucsb.edu/data/chirps) and the [v2.0 Africa monthly files](https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/)
- [geoBoundaries, Rwanda ADM2](https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM2/)
- [RAB, Rwanda Soil Information System launch](https://www.rab.gov.rw/1-1/news-details/rab-launches-rwanda-digital-soil-information-system-to-improve-agricultural-productivity)

Secondary. News reports of public sessions. They are not survey cells.

- [KT Press, 23 March 2026, Gako retreat](https://www.ktpress.rw/2026/03/kagame-criticizes-slow-progress-in-agriculture-urges-shift-from-promises-to-action/)
- [AllAfrica, 29 June 2026, Parliament on the maize target](https://allafrica.com/stories/202606300076.html)

## Model assistance and ownership

Drafting, transcription, the rainfall script, the rules module, and the Django site used model assistance. The competition requires that disclosure. Every cell a screen shows still has to be signed by a person against the printed table.

Under the hackathon rules, intellectual property in the submission transfers to NISR.
