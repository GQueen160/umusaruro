"""Numbers that carry their source.

Every number a page shows is a Stat. A Stat cannot be built without a
survey, a table, and a year, and the only way a template prints one is the
`stat` tag, which prints the citation with it. A blank stays blank: it is
shown as the reason it is blank, never as zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

SAS_A_2026_URL = (
    "https://statistics.gov.rw/sites/default/files/documents/2026-04/"
    "SAS%202026%20Season%20A%20_Final%20Report.pdf"
)
SAS_B_2026_URL = "https://statistics.gov.rw/sites/default/files/documents/2026-09/SAS%202026B_Main%20report.pdf"
PSTA_5_URL = (
    "https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/"
    "Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf"
)
CHIRPS_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/"
CONTRACT_URL = "https://gitlab.com/mukunzijonathan/umusaruro/-/blob/main/docs/Umusaruro-evidence-contract.pdf"
RULES_URL = "https://gitlab.com/mukunzijonathan/umusaruro/-/blob/main/umusaruro/rules.py"

BLANK_TEXT = {
    "dash": "blank (dash printed)",
    "empty": "blank (column empty)",
    "absent": "blank (no row in the table)",
    "derived": "no gap (a cell is blank)",
    "zero": "blank (zero in the workbook, printed as a dash)",
}


@dataclass(frozen=True)
class Source:
    survey: str
    table: str
    year: str
    url: str
    short: str

    def __post_init__(self):
        for field in ("survey", "table", "year", "url", "short"):
            if not getattr(self, field).strip():
                raise ValueError(f"a source needs a {field}")

    @property
    def full(self) -> str:
        return f"{self.survey}, {self.table}, {self.year}"


def sas_a(table: str) -> Source:
    return Source(
        survey="Seasonal Agricultural Survey, Season A",
        table=f"Table {table}",
        year="2026",
        url=SAS_A_2026_URL,
        short=f"SAS A 2026 T{table}",
    )


def sas_b(table: str) -> Source:
    return Source(
        survey="Seasonal Agricultural Survey, Season B",
        table=f"Table {table}",
        year="2026",
        url=SAS_B_2026_URL,
        short=f"SAS B 2026 T{table}",
    )


def sas(season: str, table: str) -> Source:
    return {"A": sas_a, "B": sas_b}[season](table)


def sas_workbook(year: int, table: str, url: str) -> Source:
    """A Season A table read from NISR's published tables workbook for that year."""
    return Source(
        survey="Seasonal Agricultural Survey, Season A, tables workbook",
        table=f"Table {table}",
        year=str(year),
        url=url,
        short=f"SAS A {year} T{table}",
    )


HISTORY = Source(
    survey="Umusaruro Season A back-series from the SAS workbooks",
    table="data/history/season_a.csv",
    year="2019 to 2026",
    url="https://gitlab.com/mukunzijonathan/umusaruro/-/blob/main/data/history/season_a.csv",
    short="back-series",
)


def psta(column: str) -> Source:
    return Source(
        survey="PSTA 5 results framework, maize productivity",
        table=f"column {column}",
        year=column,
        url=PSTA_5_URL,
        short=f"PSTA 5 {column}",
    )


CHIRPS = Source(
    survey="CHIRPS v2.0 Africa monthly",
    table="district six-month sum",
    year="Sep 2025 to Feb 2026",
    url=CHIRPS_URL,
    short="CHIRPS Sep 2025-Feb 2026",
)

CONTRACT = Source(
    survey="Umusaruro evidence contract",
    table="rules section",
    year="2026",
    url=CONTRACT_URL,
    short="contract rules",
)

RULES = Source(
    survey="Umusaruro rules on SAS Season A 2026 and CHIRPS",
    table="Tables 20, 25, 31 and the rainfall gate",
    year="2026",
    url=RULES_URL,
    short="rules, SAS A 2026",
)

RULES_B = Source(
    survey="Umusaruro rules applied to SAS Season B 2026",
    table="Tables 18, 23, 29, same cutoffs, no rainfall gate",
    year="2026",
    url=RULES_URL,
    short="rules, SAS B 2026",
)

SIGNOFF = Source(
    survey="Umusaruro second-person sign-off",
    table="data/season_a_2026/cells.csv, checked column",
    year="2026",
    url="https://gitlab.com/mukunzijonathan/umusaruro/-/blob/main/data/season_a_2026/signoff.csv",
    short="sign-off",
)

SIGNOFF_B = Source(
    survey="Umusaruro second-person sign-off, Season B",
    table="data/season_b_2026/cells.csv, checked column",
    year="2026",
    url="https://gitlab.com/mukunzijonathan/umusaruro/-/blob/main/data/season_b_2026/signoff.csv",
    short="sign-off B",
)

FOOTER_CHECK = Source(
    survey="Umusaruro Season B footer check",
    table="data/season_b_2026/footer_check.csv",
    year="2026",
    url="https://gitlab.com/mukunzijonathan/umusaruro/-/blob/main/data/season_b_2026/footer_check.csv",
    short="footer check",
)


@dataclass(frozen=True)
class Ref:
    """A year, season, or table name inside a sentence. Printed as a marked reference, never as a statistic."""
    text: str


def tonnes(kg: Decimal) -> Decimal:
    """kg/ha to t/ha: divide by 1,000, round half up to two decimals."""
    return (kg / Decimal(1000)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Stat:
    value: Decimal | None
    unit: str
    source: Source
    printed: str = "number"
    checked: bool = False

    def __post_init__(self):
        if not isinstance(self.source, Source):
            raise TypeError("a statistic needs a Source")
        if self.value is None and self.printed not in BLANK_TEXT:
            raise ValueError(f"blank statistic with unknown reason {self.printed!r}")

    is_stat = True

    @property
    def blank(self) -> bool:
        return self.value is None

    def number(self) -> str:
        """The value alone, formatted as text() formats it. Only for a cell whose header names the unit."""
        if self.value is None:
            return BLANK_TEXT[self.printed]
        value = self.value
        if self.unit == "kg/ha":
            return f"{int(value):,}" if value == value.to_integral_value() else f"{value:,}"
        return f"{value}"

    def text(self) -> str:
        if self.value is None:
            return BLANK_TEXT[self.printed]
        number = self.number()
        if self.unit == "%":
            return f"{number}%"
        return f"{number} {self.unit}" if self.unit else number


def in_tonnes(stat: Stat) -> Stat:
    if stat.value is None:
        return stat
    return Stat(tonnes(stat.value), "t/ha", stat.source, stat.printed, stat.checked)
