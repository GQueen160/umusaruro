# Umusaruro

Umusaruro is a district maize action sheet for a district agronomist and a planner at the Ministry of Agriculture and Animal Resources. The name is the Kinyarwanda word for harvest.

For one district, the sheet will show Season A 2026 maize yield against the PSTA 5 milestones, then the lever the published tables support: irrigation, or all-crop improved seed. Inorganic fertilizer is named on the same sheet when that table lags. The reader does not type figures into the system.

This is the agriculture track of the NISR 2026 Big Data Hackathon. A submission is a public Git repository, a deployed application, and documentation. The deadline is 23:59 on 30 October 2026.

## The contract

[docs/Umusaruro-evidence-contract.pdf](docs/Umusaruro-evidence-contract.pdf) locks the product. The same text is in [docs/Umusaruro-evidence-contract.docx](docs/Umusaruro-evidence-contract.docx). A number may appear on a screen only when that contract names its survey, table, and year.

The contract also says what this project will not claim: a maize variety, a satisfaction score, a learned seed-soil-fertilizer score, a district store, a national rate copied onto a district, or a re-estimate of the NST2 irrigated-hectare total. Table 20 is all-crop improved seed. It is not the maize seed rate. Maize seed, 64.3% improved, is Table 21 and has no district column.

PSTA 5 maize milestones, tonnes per hectare, are baseline 2023 = 1.70, then 1.87, 2.06, 2.26, 2.49, and 2.74. The figure 2.26 is the 2026/27 column. Season A 2026, all farms, is 1,994 kg/ha.

To regenerate the contract from this repository:

```bash
python3 -m venv .venv
.venv/bin/pip install python-docx fpdf2
.venv/bin/python docs/build_evidence_contract.py
```

## Data

`data/season_a_2026/cells.csv` holds the transcribed Season A 2026 cells for Tables 13, 14, 16, 20, 21, 22, 25, and 31. `umusaruro/cells.py` loads that file.

A blank is an empty value. The `printed` column says why:

| printed | meaning |
| --- | --- |
| `number` | the PDF printed a number, stored without thousands separators |
| `dash` | the PDF printed a dash |
| `empty` | the column was left empty |
| `absent` | the district has no row in that table |

`Cell.number()` raises `BlankCell` for every case except `number`. A blank is never read as zero. A printed zero stays zero.

`checked` is false on every row. A second person still has to sign each cell against the printed page before the file is treated as signed off. The tables sit on these pages of the Season A 2026 report: 13 on page 39, 14 on page 40, 16 on page 42, 20 on page 46, 21 on page 47, 22 on page 48, 25 on page 50, and 31 on page 55.

Yields are stored in kg/ha, as printed. Showing tonnes per hectare means dividing by 1,000 and rounding half up to two decimals.

The transcription is rebuilt from a local text extract of the NISR PDF. The PDF is not committed.

```bash
pdftotext -layout "SAS 2026 Season A _Final Report.pdf" /tmp/sas2026a.txt
python3 tools/transcribe_season_a.py /tmp/sas2026a.txt
```

The script refuses to write the file if the contract cells do not match.

### Rainfall gate

`data/chirps/season_a_2026_rainfall.csv` holds one CHIRPS v2.0 total per district for September 2025 through February 2026. `umusaruro/rainfall.py` loads it. A district's total is the mean of the six-month sums at the 0.05° grid cells whose centres fall inside the district. The `cells` column says how many cells that is. Kicukiro rests on 7 cells and Nyarugenge on 2, so read those totals as thin.

The median of the 30 totals is 689.25 mm. 15 districts are below it. Rainfall is a gate on irrigation only. It never replaces a NISR cell, and it is not the farmer's reason for irrigating or not.

District boundaries are the geoBoundaries ADM2 file for Rwanda, built from Open Data Rwanda, CC BY 4.0. The rasters and the boundary file are not committed. To rebuild the totals, download the six monthly Africa files from the [CHIRPS v2.0 folder](https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/) and the boundary file listed by the [geoBoundaries API](https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM2/), then:

```bash
python3 -m venv .venv-geo
.venv-geo/bin/pip install rasterio shapely numpy
.venv-geo/bin/python tools/chirps_gate.py /tmp/chirps /tmp/chirps/rwa_adm2.geojson
```

The script stops if a district has no grid cell inside it, if a cell has no data, or if a boundary name differs from the Season A district names.

## Rules

`umusaruro/rules.py` holds the team cutoffs. They are not NISR thresholds.

| Constant | Value | Meaning |
| --- | --- | --- |
| `IRRIGATION_GAP` | 30 | large-farm irrigation minus smallholder irrigation, in points |
| `IRRIGATION_SSF_MAX` | 15 | smallholder irrigation must be under this percent |
| `SEED_GAP` | 25 | Table 20, all crops, percentage of farmers |
| `SEED_LEAD` | 5 | if seed's lead over irrigation is smaller than this, irrigation stays |
| `FERTILIZER_GAP` | 15 | Table 25 lag that gets fertilizer named on the sheet |

Irrigation is a candidate only when both irrigation numbers exist, the gap is at least 30 points, and the smallholder rate is under 15%. It becomes the action only when `rainfall_below_median` is true. Seed fires when the Table 20 gap is at least 25 points. If both fire, the larger gap is the action, unless seed leads by less than 5 points. Fertilizer is named beside the action. It does not replace it. A blank large-farm cell cannot open a gap.

`classify(cells, geography, rainfall_below_median=None)` returns a `Decision`. Seed on that decision means all crops, not maize seed. `classify_all(cells, rainfall)` runs every district with its CHIRPS flag.

With the committed files, the result is:

- Irrigation, 7 districts: Gatsibo, Kayonza, Kicukiro, Kirehe, Ngoma, Nyagatare, Rwamagana.
- All-crop seed, 19 districts.
- No action, 4 districts. Nyarugenge and Karongi have a blank large-farm cell. Nyanza and Rusizi already have smallholder irrigation at or above 15%, and their seed gaps are under 25 points.

Ten districts meet the irrigation arithmetic. Rainfall removes Karongi, Nyamasheke, and Nyamagabe, which are wetter than the median. Gatsibo has both gaps open and keeps irrigation, because its seed gap, 51.8 points, is smaller than its irrigation gap, 55.5.

Seed fires in most districts because large farms report high improved-seed use almost everywhere. Read the seed label as the common case, not a district-specific finding. Fertilizer is named in 25 districts for the same reason.

## Branches

`main` is the line we submit. `dev` is where merge requests land. Work goes on its own branch, then opens a merge request into `dev`. `dev` merges into `main` when a phase is accepted.

Pipelines run on merge requests and on pushes to `dev` and `main`. A push to a feature branch does not start a pipeline. The current job compiles the Python modules and runs the unit tests. It also checks that both copies of the evidence contract are in the tree.

## Tests

From the repository root, with the standard library only:

```bash
python3 -m unittest discover -s tests -v
```

`tests/test_cells.py` checks that the national maize and irrigation figures reproduce, and that a blank cannot be read as zero. `tests/test_rules.py` checks Nyagatare, Kirehe, Kamonyi, Gakenke, Ngoma, a blank large-farm cell, and the cutoffs that sit one tenth of a point away from a different result. `tests/test_rainfall.py` checks the 30 totals, the median, Kicukiro's 7 cells, and the seven irrigation districts.

The tests read the committed CSV files. They do not need rasterio.

## Where the work stands

1. Evidence contract. On `main`.
2. Season A cell file. On `main`. Second-person sign-off is still open. The CHIRPS rainfall file is computed.
3. Rules module, in `umusaruro/rules.py`. With rainfall in, no district is left unresolved.
4. Django application: map, district page, method page. Not started. A statistic will not render without survey, table, and year.
5. Season B 2026, loaded beside Season A. Not started. Season B irrigation is workbook Table 29, and that sheet's footer still says SAS 2025. No Season B irrigation cell is shown until that footer is resolved.
6. Public repository, deployed link, and a disclosure of model assistance. Deadline 30 October 2026, 23:59.

## Sources

The contract lists every link. The ones the code reads now are:

- [SAS Season A 2026](https://statistics.gov.rw/sites/default/files/documents/2026-04/SAS%202026%20Season%20A%20_Final%20Report.pdf)
- [PSTA 5, abridged](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf)
- [CHIRPS v2.0 Africa monthly](https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/)
- [geoBoundaries Rwanda ADM2](https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM2/)
- [NISR 2026 Big Data Hackathon](https://statistics.gov.rw/about/hackathon/2026-hackathon-competition)

## Model assistance

Drafting, transcription checks, and the rules module used model assistance. The competition requires that disclosure in the submission. The cells still have to be signed by a person against the printed tables.
