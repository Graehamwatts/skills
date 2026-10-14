# -*- coding: utf-8 -*-
"""Tests for the optional sections in the built report: online views (B2), similar homes nearby (B3), online ads
and marketing (B4), the masthead photo (B6), and how a build carries on when a lookup was skipped (B5).

    python -m unittest tests.test_extras_report      (from the skill folder)

The first half renders the synthetic ledgers. The second half runs the whole pipeline (run_issue.py) on the
synthetic listing with the optional files in its folder. Synthetic data only.
"""
import contextlib
import copy
import html
import io
import json
import os
import re
import shutil
import site
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
sys.path.insert(0, FIX)
if site.getusersitepackages() not in sys.path:
    sys.path.append(site.getusersitepackages())
import sr_contract as C  # noqa: E402
import sr_files as F  # noqa: E402
import sr_render  # noqa: E402
import online_views as OV  # noqa: E402
import nearby_update as NB  # noqa: E402
import run_issue as RI  # noqa: E402
from sr_render import render  # noqa: E402

try:
    import openpyxl  # noqa: F401
    import make_workbook as W  # noqa: E402
    HAVE_XLSX = True
except ImportError:
    HAVE_XLSX = False

ID = C.load_identity()
PHOTO = "https://photos.example.test/218/front.jpg"


def fixture(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


def text_of(page):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))


def section(page, name):
    """The text of one section of a page."""
    at = page.index('data-sr-section="%s"' % name)
    nxt = [page.find('data-sr-section="%s"' % n, at + 20) for n in sr_render.assemble.ORDER if n != name]
    end = min([i for i in nxt if i > 0] or [len(page)])
    return text_of(page[page.index(">", at) + 1:end]).strip()


def small(**blocks):
    d = fixture("ledger_small.json")
    d.update(blocks)
    C.finish_ledger(d)
    problems = C.validate_ledger(d, identity=ID)
    assert not problems, problems
    return d


class OnlineViewsOnThePage(unittest.TestCase):
    def test_a_first_reading_prints_the_count_since_listing_and_no_weekly_figure(self):
        first = {"as_of": "2026-04-13", "portals": ["Zillow"], "weeks": [], "since_listing": {"views": {"Zillow": 812}, "saves": {"Zillow": 31}}}
        d = small(online=first)
        self.assertEqual((d["totals"]["online_views"], d["totals"]["online_saves"], d["weeks"][-1]["online_views"]), (812, 31, None))
        for mode in sr_render.MODES:
            r = render(d, identity=ID, mode=mode, no_hero=True)
            page = r["html"]
            row = text_of(page.split('<tr data-sr-row="online_views">')[1].split("</tr>")[0]).strip()
            self.assertEqual(row, "Online views Zillow not recorded not recorded 812 31 saved")
            self.assertIn("Online views are the running count Zillow showed on Apr 13. A weekly figure needs two readings a week apart, "
                          "so there is none yet.", text_of(page))
            self.assertNotIn("next report.", text_of(page).split("THE NUMBERS")[1].split("WHAT PEOPLE ARE SAYING")[0])
            self.assertNotIn('data-sr-table="chart_views"', page)                 # no weekly figure yet: no chart, no column
            self.assertNotIn('data-sr-col="online_views"', page.split('data-sr-table="weeks"')[1].split("</table>")[0])
            self.assertIn("online", r["info"]["flags"]["sections"])

    def test_running_counts_and_weekly_figures_together(self):
        block, _ = OV.ledger_block(fixture("online_views.json"), fixture("ledger_small.json")["listing"], fixture("ledger_small.json")["report"])
        d = small(online=block)
        page = render(d, identity=ID, no_hero=True)["html"]
        row = text_of(page.split('<tr data-sr-row="online_views">')[1].split("</tr>")[0]).strip()
        self.assertEqual(row, "Online views Zillow and Redfin 230 5 saved 275 8 saved 915 25 saved")
        self.assertIn("915 views since we listed, as counted by Zillow and Redfin.", section(page, "views_chart"))
        weekly = page.split('data-sr-table="weeks"')[1].split("</table>")[0]
        self.assertIn(">915<", weekly.split('data-sr-row="all"')[1])              # the last line is the count since we listed
        self.assertIn("The last line is the count since we listed.", section(page, "weekly_table"))
        self.assertIn("Online views are as counted by Zillow and Redfin, read on Apr 13.", text_of(page))


class NearbyOnThePage(unittest.TestCase):
    def block(self):
        d = fixture("ledger_small.json")
        return NB.ledger_block(fixture("nearby.json"), d["listing"], d["report"])[0]

    def test_what_changed_first_then_the_watch_list_as_a_table(self):
        d = small(nearby=self.block())
        for mode in sr_render.MODES:
            page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
            t = section(page, "nearby")
            self.assertTrue(t.startswith("SIMILAR HOMES NEARBY 4 of the 5 homes we are watching changed "
                                         "Five 3 bedroom single family homes in Fixture City, chosen on Mar 16. Checked Apr 13. WHAT CHANGED"), t[:200])
            self.assertIn("14 Sample Fern Ln Back on the market on Apr 10 at $1,210,000.", t)
            self.assertEqual(re.findall(r'data-sr-row="change:(\d)"', page), ["0", "1", "2", "3"])
            self.assertIn('<span data-sr="nearby_changed">4</span> of the <span data-sr="nearby_homes">5</span> homes', page)
            self.assertIn("Source: Public listing pages.", t)
            self.assertEqual(page.count("7 Sample Elm Pl"), 1)
            self.assertNotIn("Sample Fern Ln", page.replace(page[page.index('data-sr-section="nearby"'):page.index('data-sr-section="market"')], ""))

    def test_a_blank_day_count_is_explained(self):
        nb = self.block()
        note = "A blank means we have no confirmed day count for that home."
        self.assertTrue(all(h.get("days_on_market") is not None for h in nb["homes"]))
        self.assertNotIn(note, section(render(small(nearby=nb), identity=ID, no_hero=True)["html"], "nearby"))
        nb["homes"][1]["days_on_market"] = None
        for mode in sr_render.MODES:
            t = section(render(small(nearby=nb), identity=ID, mode=mode, no_hero=True)["html"], "nearby")
            self.assertIn("for a home still for sale. " + note + " Source:", t)

    def test_a_quiet_week_and_a_change_seen_without_a_date(self):
        nb = self.block()
        for h in nb["homes"]:
            h.update(change="none", change_date=None)
            h.pop("price_before", None)
        t = section(render(small(nearby=nb), identity=ID, no_hero=True)["html"], "nearby")
        self.assertIn("No change among the 5 homes we are watching", t)
        self.assertNotIn("WHAT CHANGED", t)
        nb["homes"][0].update(change="went_pending", change_date="2026-04-13", change_date_approximate=True, status="pending")
        t = section(render(small(nearby=nb), identity=ID, no_hero=True)["html"], "nearby")
        self.assertIn("14 Sample Fern Ln Went pending by Apr 13 after 3 days on the market.", t)      # "by", not "on": the day is not on record
        nb["homes"][0]["change_date_approximate"] = "yes"
        d = fixture("ledger_small.json")
        d["nearby"] = nb
        C.finish_ledger(d)
        self.assertTrue(any("change_date_approximate" in p for p in C.validate_ledger(d, identity=ID)))

    def test_it_can_be_left_out_of_one_build(self):
        r = render(small(nearby=self.block()), identity=ID, no_hero=True, nearby=False)
        self.assertNotIn('data-sr-section="nearby"', r["html"])
        self.assertNotIn("nearby", r["info"]["flags"]["sections"])


class AdsAndMarketingOnThePage(unittest.TestCase):
    """B4: switched on, scheduled to end, prepared, on hold, not launched. Running only when checked for this issue."""

    def ledger(self, edit=None):
        d = fixture("ledger_small.json")
        chans = d["marketing"]["channels"]
        chans[2]["ends_on"] = "2026-04-20"
        chans += [{"channel": "TikTok", "status": "on_hold", "checked": "2026-04-02", "detail": "The account settings need fixing first."},
                  {"channel": "Google Display", "status": "not_launched", "checked": "2026-04-02", "detail": "No campaign is set up."}]
        if edit:
            edit(d)
        C.finish_ledger(d)
        return d

    def test_the_status_words(self):
        d = self.ledger()
        self.assertEqual(C.validate_ledger(d, identity=ID), [])
        t = section(render(d, identity=ID, no_hero=True)["html"], "marketing")
        self.assertTrue(t.startswith("ONLINE ADS AND MARKETING 2 channels running, 1 switched on and last checked Apr 2, 1 prepared, 1 on hold, 1 not launched"), t[:160])
        self.assertIn("MLS and home search sites RUNNING On the MLS since Mar 12.", t)
        self.assertIn("Facebook and Instagram ads SWITCHED ON Last checked Apr 2. Scheduled to end Apr 20. Two ads were running at the last check.", t)
        self.assertIn("YouTube ads PREPARED Last checked Apr 2.", t)
        self.assertIn("On hold: TikTok. Not launched: Google Display.", t)
        self.assertNotIn("Facebook and Instagram ads RUNNING", t)
        link = section(render(d, identity=ID, mode="link", no_hero=True)["html"], "marketing")      # the full copy gives each its own row
        self.assertIn("TikTok ON HOLD Last checked Apr 2. The account settings need fixing first.", link)
        self.assertIn("Google Display NOT LAUNCHED Last checked Apr 2. No campaign is set up.", link)

    def test_an_end_date_that_has_passed_is_said_in_the_past(self):
        def edit(d):
            d["marketing"]["channels"][2]["ends_on"] = "2026-04-09"
        t = section(render(self.ledger(edit), identity=ID, no_hero=True)["html"], "marketing")
        self.assertIn("SWITCHED ON Last checked Apr 2. Was scheduled to end Apr 9.", t)

    def test_the_section_prints_only_when_something_is_on_or_was_recorded_for_the_issue(self):
        def stale(d):
            for ch in d["marketing"]["channels"]:
                ch.update(status="prepared" if ch["status"] == "on" else ch["status"], checked="2026-03-20")
                ch.pop("ends_on", None)
        d = self.ledger(stale)
        self.assertFalse(C.marketing_recorded(d["marketing"], d["report"]))
        self.assertNotIn('data-sr-section="marketing"', render(d, identity=ID, no_hero=True)["html"])

        def checked_this_week(d):
            stale(d)
            d["marketing"]["channels"][3]["checked"] = "2026-04-08"
        d = self.ledger(checked_this_week)
        self.assertTrue(C.marketing_recorded(d["marketing"], d["report"]))
        self.assertIn("4 prepared, 1 on hold, 1 not launched", section(render(d, identity=ID, no_hero=True)["html"], "marketing"))

    def test_no_ad_spend_and_a_real_end_date(self):
        def spend(d):
            d["marketing"]["channels"][2]["detail"] = "Two ads are on. Spend so far is $45."
        self.assertTrue(any("dollar amount" in p for p in C.validate_ledger(self.ledger(spend), identity=ID)))

        def bad_end(d):
            d["marketing"]["channels"][3]["ends_on"] = "2026-04-20"                # a channel that is not on has no scheduled end
        self.assertTrue(any("ends_on" in p for p in C.validate_ledger(self.ledger(bad_end), identity=ID)))
        self.assertEqual(C.money_amounts("No spend or clicks had been recorded at the first check, at 12:26 am."), [])
        self.assertEqual(len(C.money_amounts("Spent $1,200 on Meta and 300 dollars on video.")), 2)

    def test_these_pages_pass_the_renderers_own_checks_in_every_mode(self):
        d = self.ledger()
        d["online"], _ = OV.ledger_block(fixture("online_views.json"), d["listing"], d["report"])
        d["nearby"], _ = NB.ledger_block(fixture("nearby.json"), d["listing"], d["report"])
        C.finish_ledger(d)
        for mode in sr_render.MODES:
            r = render(d, identity=ID, mode=mode, hero=PHOTO)
            self.assertEqual(r["info"]["flags"]["sections"], ["online", "nearby", "market", "marketing"])
            self.assertFalse(C.has_dash(r["html"]))
            if mode == "email":
                self.assertLess(r["info"]["bytes"], C.LIMITS["email_max_bytes"])


class MastheadPhoto(unittest.TestCase):
    def test_an_https_photo_is_used_and_anything_else_is_left_off(self):
        d = small()
        r = render(d, identity=ID, hero=PHOTO)
        self.assertIn('src="%s"' % PHOTO, r["html"])
        self.assertEqual(r["info"]["flags"]["hero"], PHOTO)
        d["listing"]["hero_photo"] = PHOTO                                        # or from the listing's own settings
        self.assertIn('src="%s"' % PHOTO, render(d, identity=ID)["html"])
        d["listing"]["hero_photo"] = r"C:\Users\someone\Pictures\front.jpg"
        r = render(d, identity=ID)
        self.assertNotIn("<img", r["html"])
        self.assertTrue(any("not at an https address" in w for w in r["info"]["warnings"]))


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = RI.main(list(argv))
    return code, out.getvalue()


@unittest.skipUnless(HAVE_XLSX, "openpyxl is not installed")
class BuiltWithTheOptionalFiles(unittest.TestCase):
    """The whole pipeline: what is on file in the listing folder reaches the ledger, the pages and the checks."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sr extras run ")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.folder = os.path.join(self.tmp, "seller-reports", "sample-glen")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            W.prepare(self.folder, tagged=True)
        self.fast = ["--folder", self.folder, "--no-pdf", "--no-previews", "--no-probe", "--allow-synthetic", "--report-date", W.REPORT_DATE]

    def put(self, name, data):
        F.save_json(os.path.join(self.folder, name), data)

    def issue(self, name):
        path = os.path.join(self.folder, "issues", "05", name)
        if name.endswith(".json"):
            return F.load_json(path)
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_online_views_and_similar_homes_on_file_are_in_the_report_and_pass_the_checks(self):
        self.put("online_views.json", fixture("online_views.json"))
        self.put("nearby.json", fixture("nearby.json"))
        code, out = run(*self.fast)
        self.assertEqual(code, RI.EXIT_READY, out)
        self.assertIn("all checks passed on 3 page(s)", out)
        d = self.issue("ledger.json")
        self.assertEqual((d["totals"]["online_views"], d["totals"]["online_saves"]), (915, 25))
        self.assertEqual(len(d["nearby"]["homes"]), 5)
        kinds = [s["kind"] for s in d["sources_used"]]
        for kind in ("portal_page", "operator_numbers", "nearby_lookup"):
            self.assertIn(kind, kinds)
        self.assertNotIn("extras", d["listing"])
        # the synthetic offer is for the same amount as one watched home's list price. That public price may be
        # printed in the similar homes section of the link copy, and nowhere else on it
        self.assertEqual(d["offers"][0]["price"], d["nearby"]["homes"][1]["list_price"])
        link = self.issue("link.html")
        self.assertEqual(link.count("$1,150,000"), sr_render.assemble.without_sections(link, ("offers",)).count("$1,150,000"))
        self.assertNotIn("$1,150,000", sr_render.assemble.without_sections(link, ("nearby",)))
        self.assertEqual(self.issue("manifest.json")["flags"]["sections"][:2], ["online", "nearby"])
        for name in ("email.html", "link.html", "print.html"):
            page = self.issue(name)
            self.assertIn("SIMILAR HOMES NEARBY", text_of(page))
            self.assertIn('<tr data-sr-row="online_views">', page)
        gate = F.load_json(os.path.join(self.folder, "work", "gate.json"))
        passed = set(r["id"] for pg in gate["pages"] for r in pg["results"] if r["level"] == "pass")
        for rule in ("numbers.nearby_counts", "numbers.nearby_table", "numbers.nearby_changes", "numbers.nearby_checked", "numbers.table_scorecard"):
            self.assertIn(rule, passed)
        code, out = run(*(self.fast + ["--no-nearby"]))
        self.assertEqual(code, RI.EXIT_READY, out)
        self.assertNotIn("SIMILAR HOMES NEARBY", text_of(self.issue("email.html")))

    def test_a_skipped_lookup_leaves_the_section_out_and_says_so_in_the_chat_reply_only(self):
        store = fixture("nearby.json")
        store["snapshots"] = store["snapshots"][:1]
        store["lookups"][1].update(outcome="skipped", reason="blocked")
        self.put("nearby.json", store)
        views = OV.blank_store("sample-glen")
        views["lookups"] = [{"report_date": W.REPORT_DATE, "key": "portal:Zillow", "planned_at": "2026-04-13T09:00:00-07:00", "why": "asked",
                             "outcome": "skipped", "reason": "captcha", "detail": None}]
        self.put("online_views.json", views)
        code, out = run(*self.fast)
        self.assertEqual(code, RI.EXIT_READY, out)                                # the build carries on
        d = self.issue("ledger.json")
        self.assertIsNone(d["nearby"])
        self.assertIsNone(d["online"])
        notes = self.issue("notes_for_operator.json")
        self.assertIn("Similar homes nearby could not be checked for this report: the site blocked the request. That section is left out of this report.",
                      notes["worth_a_glance"])
        self.assertIn("Online views on Zillow could not be checked for this report: the site asked for a human check. "
                      "The report is built without a new figure from that site.", notes["worth_a_glance"])
        self.assertLessEqual(len(notes["worth_a_glance"]), 5)
        self.assertIn("Similar homes nearby could not be checked for this report", out)
        # however much else there is to say, a skipped lookup keeps its place among the five, at the end
        many = [x for i in range(6) for x in ("--glance", "Something else worth a look, number %d." % (i + 1))]
        code, out = run(*(self.fast + many))
        self.assertEqual(code, RI.EXIT_READY, out)
        top = self.issue("notes_for_operator.json")["worth_a_glance"]
        self.assertEqual(len(top), 5)
        self.assertTrue(top[0].startswith("Something else worth a look"))
        self.assertTrue(top[3].startswith("Similar homes nearby could not be checked") or top[3].startswith("Online views on Zillow could not be checked"))
        self.assertEqual(len([x for x in top if "could not be checked for this report" in x]), 2)
        for name in ("email.html", "link.html", "print.html"):
            t = text_of(self.issue(name))
            for word in ("SIMILAR HOMES NEARBY", "could not be checked", "blocked", "human check", "Online views"):
                self.assertNotIn(word, t)

    def test_a_file_that_is_not_valid_stops_the_build_in_plain_words(self):
        bad = fixture("online_views.json")
        bad["rows"][0]["counts"] = "weekly"
        self.put("online_views.json", bad)
        code, out = run(*self.fast)
        self.assertEqual(code, RI.EXIT_LEDGER, out)
        self.assertIn("online_views.json: rows[0].counts: one of week, since_listing", out)

    def test_the_photo_in_the_listing_settings_is_the_masthead(self):
        listing = F.load_json(os.path.join(self.folder, "listing.json"))
        listing["hero_photo"] = PHOTO
        listing["extras"] = {"hero": {"page": "https://example.test/homes/218-sample-glen", "width": 4750, "height": 3166, "bytes": 3580264,
                                      "set_on": "2026-04-13"}}
        self.put("listing.json", listing)
        code, out = run(*self.fast)
        self.assertEqual(code, RI.EXIT_READY, out)
        self.assertIn('src="%s"' % PHOTO, self.issue("email.html"))
        self.assertEqual(self.issue("manifest.json")["flags"]["hero"], PHOTO)
        self.assertNotIn("extras", self.issue("ledger.json")["listing"])
        self.assertIn("The masthead photo is a 3.6 MB file, so it may load slowly on a phone. A smaller copy of the same photo would be better.",
                      self.issue("notes_for_operator.json")["worth_a_glance"])
        self.assertNotIn("3.6 MB", self.issue("email.html"))

    def test_marketing_last_checked_long_ago_with_nothing_on_is_left_out_with_a_note_for_claude(self):
        self.put("marketing.json", {"as_of": "2026-03-20", "channels": [
            {"channel": "YouTube ads", "status": "prepared", "checked": "2026-03-20", "detail": "The video is uploaded. Nothing has launched."}]})
        code, out = run(*self.fast)
        self.assertEqual(code, RI.EXIT_READY, out)
        self.assertIsNone(self.issue("ledger.json")["marketing"])
        self.assertTrue(any("last checked before this report's week" in s for s in self.issue("notes_for_operator.json")["also_noted"]))
        self.assertNotIn("ONLINE ADS AND MARKETING", text_of(self.issue("email.html")))


if __name__ == "__main__":
    unittest.main()
