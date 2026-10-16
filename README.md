# Umusaruro

District maize action sheet for the NISR 2026 Big Data Hackathon, agriculture track.

The product contract is [docs/Umusaruro-evidence-contract.pdf](docs/Umusaruro-evidence-contract.pdf). A screen may show a number only when that contract names its survey, table, and year.

Season A 2026 cells are in `data/season_a_2026/cells.csv`. A blank value is empty. It is not zero. `checked` stays false until a second person signs the cell against the printed page.

## Branches

`main` is the line we submit. `dev` is where merge requests land. Work goes on its own branch, then opens a merge request into `dev`. `dev` merges into `main` when a phase is accepted.

Pipelines run on merge requests and on pushes to `dev` and `main`.
