import re
from decimal import Decimal
from html.parser import HTMLParser

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from sheet import sheet
from sheet.stats import CONTRACT, Source, Stat, sas_a, tonnes

ALLOWED = {"stat", "ref"}
SKIPPED_TAGS = {"style", "script", "svg"}


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
