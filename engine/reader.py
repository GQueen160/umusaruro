"""Read an uploaded file into sheets of rows.

XLSX through the standard-library reader, CSV through the csv module. A
cell is a Decimal, a string, or None. Nothing is cleaned here; this is
the file as published.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from umusaruro import xlsx

SUPPORTED = (".xlsx", ".csv", ".tsv", ".txt")
NUMBER = re.compile(r"^-?(\d+|\d{1,3}(,\d{3})+)(\.\d+)?$")


class UnreadableFile(ValueError):
    pass


def cell(text: str):
    text = text.strip()
    if text == "":
        return None
    if NUMBER.match(text):
        try:
            return Decimal(text.replace(",", ""))
        except InvalidOperation:
            return text
    return text


def read_csv(data: bytes) -> list[list]:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialect = csv.Sniffer().sniff(text[:20000], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return [[cell(v) for v in row] for row in csv.reader(io.StringIO(text), dialect)]


def read(path: Path, name: str | None = None) -> dict[str, list[list]]:
    suffix = Path(name or path.name).suffix.lower()
    data = path.read_bytes()
    if suffix == ".xlsx" or data[:2] == b"PK":
        if not zipfile.is_zipfile(path):
            raise UnreadableFile("not a valid XLSX file")
        try:
            return xlsx.sheets(path)
        except (KeyError, zipfile.BadZipFile) as exc:
            raise UnreadableFile(f"the workbook could not be read: {exc}") from exc
    if suffix == ".xls" or data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise UnreadableFile("old Excel .xls files are not supported; save the file as .xlsx or .csv")
    if suffix in SUPPORTED:
        return {Path(name or path.name).stem: read_csv(data)}
    raise UnreadableFile(f"unsupported file type {suffix or '(none)'}; use .xlsx or .csv")
