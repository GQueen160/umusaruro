import re
from decimal import Decimal
from html.parser import HTMLParser
from unittest import mock

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from umusaruro import cells as cell_file
from umusaruro import footers
from umusaruro import rainfall as rainfall_file
from umusaruro import rules

from sheet import sheet
from sheet.stats import CONTRACT, Source, Stat, sas_a, tonnes

ALLOWED = {"stat", "ref"}
SKIPPED_TAGS = {"style", "script"}


class DigitAudit(HTMLParser):
    """Collect text with a digit that is not inside a cited statistic or a marked reference."""

    def __init__(self):
        super().__init__()
        self.stack = []
        self.loose = []
        self.stats = 0
        self.cites = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        allowed = bool(classes & ALLOWED) or tag in SKIPPED_TAGS
        inherited = self.stack[-1][1] if self.stack else False
        self.stack.append((tag, allowed or inherited))
        if "stat" in classes:
            self.stats += 1
        if "cite" in classes:
            self.cites.append(attrs)

    def handle_endtag(self, tag):
        while self.stack:
            open_tag, _ = self.stack.pop()
            if open_tag == tag:
                break

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_data(self, data):
        inside = self.stack[-1][1] if self.stack else False
        if not inside and re.search(r"\d", data):
            self.loose.append(data.strip())


def audit(html: str) -> DigitAudit:
    parser = DigitAudit()
    parser.feed(html)
    return parser


def pages():
    yield reverse("overview")
    yield reverse("method")
    for name in sheet.districts():
        yield reverse("district", args=[sheet.slug(name)])
        yield reverse("district_panel", args=[sheet.slug(name)])


class StatTests(SimpleTestCase):
    def test_a_source_needs_survey_table_year(self):
        with self.assertRaises(ValueError):
            Source(survey="SAS", table="", year="2026", url="https://x", short="x")
        with self.assertRaises(TypeError):
            Stat(Decimal("1"), "%", None)

    def test_tonnes_round_half_up(self):
        self.assertEqual(tonnes(Decimal("1994")), Decimal("1.99"))
        self.assertEqual(tonnes(Decimal("2515")), Decimal("2.52"))
        self.assertEqual(tonnes(Decimal("2887")), Decimal("2.89"))

    def test_blank_is_never_zero(self):
        for printed in ("dash", "empty", "absent", "derived"):
            text = Stat(None, "%", sas_a("20"), printed).text()
            self.assertNotIn("0", text)
            self.assertIn("blank" if printed != "derived" else "no gap", text)
        with self.assertRaises(ValueError):
            Stat(None, "%", sas_a("20"), "number")

    def test_kg_keeps_thousands_separator(self):
        self.assertEqual(Stat(Decimal("1994"), "kg/ha", sas_a("13")).text(), "1,994 kg/ha")

    def test_ranks_share_ties_and_skip_blanks(self):
        got = sheet.ranks({"a": Decimal("40"), "b": Decimal("50"), "c": Decimal("40"), "d": None})
        self.assertEqual(got, {"b": 1, "a": 2, "c": 2})


class AuditTests(SimpleTestCase):
    def test_audit_catches_a_bare_number(self):
        self.assertEqual(audit("<main><p>Yield was 1,994 kg/ha.</p></main>").loose, ["Yield was 1,994 kg/ha."])
        self.assertEqual(audit('<p><span class="ref">Table 13</span> and <b>2.06</b></p>').loose, ["2.06"])

    def test_audit_accepts_cited_numbers(self):
        html = '<p><span class="stat"><span class="v">1.99 t/ha</span><a class="cite" title="a, b, c">T13</a></span></p>'
        self.assertEqual(audit(html).loose, [])

    def test_audit_reads_inside_svg(self):
        self.assertEqual(audit('<svg><text x="1">2,260 kg/ha</text></svg>').loose, ["2,260 kg/ha"])
        self.assertEqual(audit('<svg><text class="ref" x="1">2019</text></svg>').loose, [])


class PageTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(HTTP_X_FORWARDED_PROTO="https")

    def test_every_page_renders(self):
        for url in pages():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_plain_http_is_redirected(self):
        response = Client().get(reverse("overview"))
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].startswith("https://"))

    def test_unknown_district_is_404(self):
        self.assertEqual(self.client.get("/district/atlantis/").status_code, 404)

    def test_no_number_without_its_source(self):
        for url in pages():
            with self.subTest(url=url):
                found = audit(self.client.get(url).content.decode())
                self.assertEqual(found.loose, [], f"digits outside a cited statistic on {url}")
                self.assertGreater(found.stats, 0)
                self.assertEqual(found.stats, len(found.cites))
                for cite in found.cites:
                    self.assertTrue(cite.get("href", "").startswith("https://"))
                    self.assertRegex(cite.get("title", ""), r".+, .+, .+")

    def test_map_links_every_district_once(self):
        html = self.client.get(reverse("overview")).content.decode()
        for name in sheet.districts():
            self.assertEqual(html.count(f'href="/district/{sheet.slug(name)}/" class="region'), 1, name)

    def test_map_colours_match_the_rules(self):
        html = self.client.get(reverse("overview")).content.decode()
        _cells, _rain, decisions = sheet.data()
        for action in ("irrigation", "seed", None):
            expected = sum(1 for d in decisions.values() if d.action == action)
            self.assertEqual(html.count(f'class="region action-{action or "none"}'), expected)

    def test_contract_districts(self):
        nyagatare = self.client.get("/district/nyagatare/").content.decode()
        self.assertIn("2,887 kg/ha", nyagatare)
        self.assertIn("2.89 t/ha", nyagatare)
        self.assertIn("Irrigation", nyagatare)
        nyarugenge = self.client.get("/district/nyarugenge/").content.decode()
        self.assertIn("No action from these rules", nyarugenge)
        self.assertIn("blank (", nyarugenge)

    def test_seed_lead_claimed_only_when_seed_gap_is_wider(self):
        _cells, _rain, decisions = sheet.data()
        for name, d in decisions.items():
            if d.action != "irrigation" or not d.seed_fires:
                continue
            with self.subTest(district=name):
                html = self.client.get(f"/district/{sheet.slug(name)}/").content.decode()
                self.assertEqual("leads the irrigation gap" in html, d.seed_gap > d.irrigation_gap)

    def test_seed_is_never_called_maize_seed(self):
        for url in pages():
            with self.subTest(url=url):
                self.assertNotIn("maize seed rate", self.client.get(url).content.decode().lower())

    def test_constants_cite_the_contract(self):
        html = self.client.get(reverse("method")).content.decode()
        self.assertIn(CONTRACT.full, html)


class MapAndTrendTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(HTTP_X_FORWARDED_PROTO="https")
        self.overview = self.client.get(reverse("overview")).content.decode()

    def test_every_region_carries_all_four_layers_and_its_panel(self):
        rows = {row.name: row for row in sheet.overview()["rows"]}
        for name, row in rows.items():
            slug = sheet.slug(name)
            classes = (f'class="region action-{row.action or "none"} milestone-{row.milestone_band} '
                       f'trend-{row.trend_band} rain-{row.rain_band}')
            self.assertIn(classes, self.overview)
            self.assertIn(f'data-panel="/district/{slug}/panel/"', self.overview)

    def test_layer_counts_add_up_to_thirty(self):
        for layer in sheet.overview()["layers"]:
            with self.subTest(layer=layer.key):
                self.assertEqual(sum(item.count.value for item in layer.items), 30)

    def test_milestone_bands_follow_table_13(self):
        cells, _rain, _d = sheet.data()
        for name in sheet.districts():
            kg = cells.get("13", name, "all", "maize", "yield").value
            band = sheet.milestone_band(kg)
            self.assertEqual(band == "late", kg >= Decimal("2260"), name)
            self.assertEqual(band == "below", kg < Decimal("2060"), name)

    def test_trend_band_compares_a_district_only_with_itself(self):
        for name in sheet.districts():
            series = sheet.by_year("maize_yield", name, "all")
            earlier = [s.value for y, s in series.items() if y < sheet.LATEST]
            band = sheet.trend_band(name)
            self.assertEqual(band == "high", series[sheet.LATEST].value > max(earlier), name)
            self.assertEqual(band == "low", series[sheet.LATEST].value < min(earlier), name)

    def test_latest_history_point_is_the_printed_cell(self):
        cells, _rain, _d = sheet.data()
        for name in sheet.districts():
            self.assertEqual(sheet.by_year("maize_yield", name, "all")[sheet.LATEST].value,
                             cells.get("13", name, "all", "maize", "yield").value)

    def test_panel_is_a_fragment_with_the_action_and_the_trend(self):
        html = self.client.get(reverse("district_panel", args=["nyagatare"])).content.decode()
        self.assertNotIn("<html", html)
        self.assertIn("Irrigation", html)
        self.assertIn("2,887 kg/ha", html)
        self.assertIn('class="chart"', html)
        self.assertIn('href="/district/nyagatare/"', html)
        self.assertEqual(self.client.get("/district/atlantis/panel/").status_code, 404)

    def test_chart_cites_every_year_and_never_plots_a_blank(self):
        trend = sheet.district_trend("Nyarugenge")
        irrigation = next(l for l in trend.levers if l.key == "irrigation")
        large = irrigation.chart.lines[1]
        for mark in large.marks:
            self.assertEqual(mark.y is None, mark.stat.value is None)
        self.assertTrue(any(m.y is None for m in large.marks))
        html = self.client.get("/district/nyarugenge/").content.decode()
        for year in trend.years:
            self.assertRegex(html, rf'title="Seasonal Agricultural Survey, Season A, tables workbook, Table \d+, {year}"')

    def test_method_page_lists_the_table_read_each_year(self):
        rows = {year: tables for year, _url, tables in sheet.history_tables()}
        self.assertEqual(rows[2026], ["13", "14", "20", "25", "31"])
        self.assertEqual(rows[2019], ["13", "16", "28", "37", "48"])
        self.assertIn('id="back-series"', self.client.get(reverse("method")).content.decode())

    def test_record_districts_say_so(self):
        for name in sheet.districts():
            if sheet.trend_band(name) == "high":
                html = self.client.get(f"/district/{sheet.slug(name)}/").content.decode()
                self.assertIn("is the highest maize yield in", html)


def footer_state(resolved: bool):
    """Set whether a second person has confirmed the Table 29 footer, whatever the committed file says."""
    cells_b, _resolved = sheet.season_b()
    return mock.patch.object(sheet, "season_b", return_value=(cells_b, resolved))


def footer_resolved():
    return footer_state(True)


class SeasonBTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(HTTP_X_FORWARDED_PROTO="https")

    def page(self, name):
        return self.client.get(f"/district/{sheet.slug(name)}/").content.decode()

    def test_actions_come_from_season_a_only(self):
        _cells, _rain, decisions = sheet.data()
        self.assertEqual(decisions, rules.classify_all(cell_file.load(), rainfall_file.load()))
        with footer_resolved():
            for name, d in decisions.items():
                self.assertEqual(sheet.district_sheet(name).decision, d)

    def test_irrigation_is_withheld_until_the_footer_is_confirmed(self):
        with footer_state(False):
            kirehe = self.page("Kirehe")
            self.assertIn("SAS B 2026 T18", kirehe)
            self.assertNotIn("SAS B 2026 T29", kirehe)
            self.assertIn("Not shown until a second person confirms", kirehe)
            self.assertNotIn("SAS B 2026 T29", self.client.get(reverse("method")).content.decode())
            for url in pages():
                with self.subTest(url=url):
                    self.assertEqual(audit(self.client.get(url).content.decode()).loose, [])

    def test_committed_footer_state_matches_the_file(self):
        self.assertEqual(sheet.season_b()[1], footers.resolved("29"))

    def test_irrigation_shows_once_the_footer_is_confirmed(self):
        with footer_resolved():
            kirehe = self.page("Kirehe")
            self.assertIn("SAS B 2026 T29", kirehe)
            self.assertIn("80.0%", kirehe)
            self.assertIn("Season B agrees: the irrigation gap is", kirehe)
            nyagatare = self.page("Nyagatare")
            self.assertIn("Season B differs: the irrigation gap is", nyagatare)
            for url in pages():
                with self.subTest(url=url):
                    self.assertEqual(audit(self.client.get(url).content.decode()).loose, [])

    def test_season_b_notes(self):
        self.assertIn("Season B agrees: the all-crop seed gap is", self.page("Gasabo"))
        rubavu = self.page("Rubavu")
        self.assertIn("Season B differs: the all-crop seed gap is", rubavu)
        self.assertIn("24.9 points", rubavu)
        ngororero = self.page("Ngororero")
        self.assertIn("In Season B the all-crop seed gap cannot be computed", ngororero)
        self.assertIn("blank (dash printed)", ngororero)
        self.assertNotIn("Season B agrees", self.page("Nyarugenge"))
        self.assertNotIn("Season B differs", self.page("Nyarugenge"))

    def test_method_page_counts_agreement(self):
        seed = next(a for a in sheet.season_b_agreement() if a.action == "seed")
        self.assertEqual((seed.agree.value, seed.total.value), (Decimal(15), Decimal(19)))
        self.assertEqual([n for n, _s in seed.differ], ["Rubavu", "Gakenke", "Bugesera"])
        self.assertEqual([n for n, _s in seed.blank], ["Ngororero"])
        with footer_state(False):
            irrigation = next(a for a in sheet.season_b_agreement() if a.action == "irrigation")
            self.assertTrue(irrigation.withheld)
        with footer_resolved():
            irrigation = next(a for a in sheet.season_b_agreement() if a.action == "irrigation")
            self.assertEqual((irrigation.agree.value, irrigation.total.value), (Decimal(6), Decimal(7)))
            self.assertEqual([n for n, _s in irrigation.differ], ["Nyagatare"])
