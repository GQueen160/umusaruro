"""Provenance of every raw file under data/raw.

data/raw/MANIFEST.csv names, for each raw file, the URL it was downloaded
from, the publication page that links it, the publisher, the licence, the
day it was retrieved, its size and its SHA-256. Raw files are never edited.
Cleaned tables are built from them by the tools and can be rebuilt.

    python tools/raw_manifest.py            verify every file against the manifest
    python tools/raw_manifest.py record     download each URL again, require it to equal
                                            the local file byte for byte, then write the manifest
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "MANIFEST.csv"
FIELDS = ["path", "url", "landing_page", "publisher", "license", "retrieved_on", "bytes", "sha256"]

NISR = "National Institute of Statistics of Rwanda (NISR)"
CC_BY = "CC BY 4.0 (https://statistics.gov.rw/terms-use)"
FILES = "https://statistics.gov.rw/sites/default/files/documents"
SURVEYS = "https://statistics.gov.rw/data-sources/surveys/Seasonal-Agricultural-Survey/Seasonal-Agricultural-Survey"
PUBLICATIONS = "https://statistics.gov.rw/statistical-publications/agriculture-environment"

SOURCES = [
    ("sas/sas_2019_annual_tables.xlsx", f"{FILES}/2024-10/SAS%202019%20_Annual%20report%20_Tables.xlsx",
     f"{SURVEYS}/seasonal-agricultural-survey-2019"),
    ("sas/sas_2020_tables.xlsx", f"{FILES}/2024-10/USAS%202020%20_Final_Tables.xlsx",
     f"{SURVEYS}/seasonal-agricultural-survey-2020"),
    ("sas/sas_2021_tables.xlsx", f"{FILES}/2024-10/SAS%202021_Tables.xlsx",
     f"{SURVEYS}/seasonal-agricultural-survey-2021"),
    ("sas/sas_2022_tables.xlsx", f"{FILES}/2026-09/SAS%202022_Tables_0.xlsx",
     f"{SURVEYS}/seasonal-agricultural-survey-2022"),
    ("sas/sas_2023_annual_tables.xlsx", f"{FILES}/2024-10/SAS%202023_Annual%20Tables%20%283%29.xlsx",
     f"{SURVEYS}/seasonal-agricultural-survey-2023"),
    ("sas/sas_2024_season_a_tables.xlsx", f"{FILES}/2024-10/Tables_2024%20Season%20A%20%281%29.xlsx",
     f"{PUBLICATIONS}/seasonal-agricultural-survey-A-2024"),
    ("sas/sas_2025_season_a_tables.xlsx", f"{FILES}/2025-05/Tables_2025%20Season%20A.xlsx",
     f"{SURVEYS}/seasonal-agricultural-survey-season-2025"),
    ("sas/sas_2026_season_a_tables.xlsx", f"{FILES}/2026-04/Tables_2026%20Season%20A.xlsx",
     f"{PUBLICATIONS}/seasonal-agricultural-survey-season-2026"),
    ("sas/sas_2026_season_b_tables.xlsx", f"{FILES}/2026-09/Tables_2026%20Season%20B.xlsx",
     f"{PUBLICATIONS}/seasonal-agricultural-survey-season-b-2026"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "umusaruro-manifest/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def read() -> list[dict]:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify() -> list[str]:
    problems = []
    listed = set()
    for row in read():
        path = RAW / row["path"]
        listed.add(path)
        if not path.exists():
            problems.append(f"{row['path']}: missing")
            continue
        data = path.read_bytes()
        if len(data) != int(row["bytes"]) or sha256(data) != row["sha256"]:
            problems.append(f"{row['path']}: differs from the manifest")
    for path in sorted(RAW.rglob("*")):
        if path.is_file() and path != MANIFEST and path not in listed:
            problems.append(f"{path.relative_to(RAW)}: not in the manifest")
    return problems


def record() -> None:
    previous = {row["path"]: row for row in read()} if MANIFEST.exists() else {}
    today = datetime.date.today().isoformat()
    rows = []
    for rel, url, landing in SOURCES:
        local = (RAW / rel).read_bytes()
        remote = download(url)
        if sha256(remote) != sha256(local):
            raise SystemExit(f"{rel}: the file at {url} is not the local copy")
        kept = previous.get(rel, {})
        same = kept.get("sha256") == sha256(local)
        rows.append({
            "path": rel, "url": url, "landing_page": landing, "publisher": NISR, "license": CC_BY,
            "retrieved_on": kept["retrieved_on"] if same else today,
            "bytes": str(len(local)), "sha256": sha256(local),
        })
        print(f"{rel}: matches {url}")
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} entries to {MANIFEST}")


def main():
    if sys.argv[1:] == ["record"]:
        record()
        return
    problems = verify()
    if problems:
        raise SystemExit("raw files do not match the manifest:\n" + "\n".join(problems))
    print(f"{len(read())} raw files match {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
