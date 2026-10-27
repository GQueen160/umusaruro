"""Read an XLSX workbook with the standard library.

Each sheet comes back as a list of rows, each row a list of cell values by
column position. Numbers are Decimals at the 15 significant digits Excel
shows, so a stored 40.049999999999997 reads as 40.05. Strings stay strings.
Empty cells are None, so a blank keeps its column.
"""

from __future__ import annotations

import re
import zipfile
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def excel_number(text: str) -> Decimal:
    return Decimal(format(float(text), ".15g"))


def column_index(ref: str) -> int:
    index = 0
    for letter in re.match(r"[A-Z]+", ref).group():
        index = index * 26 + ord(letter) - 64
    return index - 1


def _text(node) -> str:
    return "".join(t.text or "" for t in node.iter(f"{{{NS['m']}}}t"))


def sheets(path: Path) -> dict[str, list[list]]:
    with zipfile.ZipFile(path) as book:
        strings = []
        if "xl/sharedStrings.xml" in book.namelist():
            strings = [_text(item) for item in ElementTree.fromstring(book.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        rels = ElementTree.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.get("Id"): rel.get("Target") for rel in rels}
        out = {}
        for sheet in ElementTree.fromstring(book.read("xl/workbook.xml")).find("m:sheets", NS):
            target = targets[sheet.get(REL)].lstrip("/")
            target = target if target.startswith("xl/") else f"xl/{target}"
            rows = []
            for row in ElementTree.fromstring(book.read(target)).iter(f"{{{NS['m']}}}row"):
                values = {}
                for c in row.findall("m:c", NS):
                    v = c.find("m:v", NS)
                    kind = c.get("t")
                    if kind == "s" and v is not None:
                        value = strings[int(v.text)]
                    elif kind == "inlineStr" and c.find("m:is", NS) is not None:
                        value = _text(c.find("m:is", NS))
                    elif kind in ("str", "e") and v is not None:
                        value = v.text
                    elif v is not None:
                        value = excel_number(v.text)
                    else:
                        continue
                    values[column_index(c.get("r"))] = value
                if values:
                    rows.append([values.get(i) for i in range(max(values) + 1)])
            out[sheet.get("name").strip()] = rows
        return out
