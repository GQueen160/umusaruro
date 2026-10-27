"""Line charts drawn as inline SVG on the server.

A chart is geometry only. Every plotted value is a Stat, and the template
prints those Stats, with their citations, in a table under the chart. The
SVG itself carries no number except the year labels, which are marked as
references. A blank year breaks the line; it is never drawn at zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sheet.stats import Stat

WIDTH = 640
HEIGHT = 220
LEFT, RIGHT, TOP, BOTTOM = 16, 16, 14, 28


@dataclass(frozen=True)
class Mark:
    year: int
    x: float
    y: float | None
    stat: Stat


@dataclass(frozen=True)
class Line:
    key: str
    label: str
    marks: list[Mark]
    paths: list[str]


@dataclass(frozen=True)
class Guide:
    label: str
    y: float
    stat: Stat

    @property
    def label_y(self) -> float:
        return round(self.y - 5, 1)


@dataclass(frozen=True)
class Chart:
    width: int
    height: int
    baseline: float
    years: list[tuple[int, float]]
    lines: list[Line]
    guides: list[Guide]
    left: int = LEFT
    right: int = WIDTH - RIGHT
    year_y: int = HEIGHT - 8


def chart(years: list[int], series: list[tuple[str, str, dict[int, Stat]]], guides: list[tuple[str, Stat]] = (),
          top: Decimal | None = None) -> Chart:
    """series: (key, label, {year: Stat}). The y axis starts at zero and ends at `top` or just above the largest value."""
    values = [s.value for _k, _l, by_year in series for s in by_year.values() if s.value is not None]
    values += [g.value for _l, g in guides if g.value is not None]
    ceiling = float(top if top is not None else max(values) * Decimal("1.1")) or 1.0
    span_x = WIDTH - LEFT - RIGHT
    span_y = HEIGHT - TOP - BOTTOM
    step = span_x / max(len(years) - 1, 1)
    xs = {year: round(LEFT + i * step, 1) for i, year in enumerate(years)}

    def y_of(value: Decimal) -> float:
        return round(TOP + span_y * (1 - float(value) / ceiling), 1)

    lines = []
    for key, label, by_year in series:
        marks = [Mark(year, xs[year], None if by_year[year].value is None else y_of(by_year[year].value), by_year[year])
                 for year in years if year in by_year]
        paths, run = [], []
        for mark in marks + [None]:
            if mark is not None and mark.y is not None:
                run.append(mark)
                continue
            if len(run) > 1:
                paths.append("M" + "L".join(f"{m.x},{m.y}" for m in run))
            run = []
        lines.append(Line(key, label, marks, paths))
    return Chart(WIDTH, HEIGHT, float(HEIGHT - BOTTOM), [(y, xs[y]) for y in years], lines,
                 [Guide(label, y_of(stat.value), stat) for label, stat in guides if stat.value is not None])
