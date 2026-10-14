# -*- coding: utf-8 -*-
"""Tests for the optional sources: online views, similar homes nearby, the masthead photo, and the token rules
that keep their lookups cheap (sr_lookups.py, online_views.py, nearby_update.py, hero_photo.py).

    python -m unittest tests.test_extras      (from the skill folder)

Synthetic data only: the fixtures are invented homes and invented figures for the test listing.
"""
import contextlib
import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import sr_contract as C  # noqa: E402
import sr_files as F  # noqa: E402
import sr_lookups as LK  # noqa: E402
import online_views as OV  # noqa: E402
import nearby_update as NB  # noqa: E402
import hero_photo as HP  # noqa: E402

LISTING = {"schema_version": 1, "slug": "sample-glen", "address": "218 Sample Glen Ct", "city": "Fixture City", "state": "CA", "zip": "94000",
           "beds": 3, "baths": 2.0, "sqft": 1480, "property_type": "Single Family", "list_date": "2026-03-12", "list_price": 1195000,
           "price_history": [{"date": "2026-03-12", "price": 1195000, "event": "listed"}], "status": "Active", "mls": "ML00000218",
           "hero_photo": None}
REPORT = {"report_date": "2026-04-13", "week_start": "2026-04-06", "week_end": "2026-04-12"}
RD = "2026-04-13"


def fixture(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


def call(module, *argv):
    """(exit code, everything printed) of one command line."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            code = module.main(list(argv))
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 2
            out.write(str(e.code))
    return code, out.getvalue()


class Folder(unittest.TestCase):
    """A listing folder in a temp place with spaces in its path."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sr extras ")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.folder = os.path.join(self.tmp, "seller-reports", "sample-glen")
        os.makedirs(self.folder)
        self.listing = copy.deepcopy(LISTING)
        self.save_listing()

    def save_listing(self):
        F.save_json(os.path.join(self.folder, "listing.json"), self.listing)

    def write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(data if isinstance(data, str) else json.dumps(data))
        return path


class TokenRules(unittest.TestCase):
    """B5 in code: asked or settings, one lookup per issue, compact JSON only, a block is a skip."""

    def test_nothing_is_planned_unless_asked_or_the_listing_says_so(self):
        store = {}
        with self.assertRaises(LK.Refused) as e:
            LK.plan(store, "nearby", RD, 1, asked=False, by_setting=False, what="similar homes nearby")
        self.assertIn("not asked for", str(e.exception))
        self.assertEqual(store.get("lookups", []), [])
        self.assertEqual(LK.plan(store, "nearby", RD, 1, asked=True)["why"], "asked")
        other = {}
        self.assertEqual(LK.plan(other, "nearby", RD, 1, by_setting=True)["why"], "settings")
        self.assertTrue(LK.setting({"extras": {"nearby": {"every_issue": True}}}, "nearby"))
        self.assertFalse(LK.setting({"extras": {"nearby": {}}}, "nearby"))
        self.assertFalse(LK.setting({}, "online_views"))

    def test_the_cap_is_per_issue_and_holds_whatever_became_of_the_first(self):
        for outcome, reason in (("ok", None), ("skipped", "blocked"), (None, None)):
            store = {}
            LK.plan(store, "nearby", RD, C.LIMITS["nearby_lookups_per_issue"], asked=True)
            if outcome:
                LK.close(store, "nearby", RD, outcome, reason)
            with self.assertRaises(LK.Refused) as e:
                LK.plan(store, "nearby", RD, C.LIMITS["nearby_lookups_per_issue"], asked=True)
            self.assertIn("already used", str(e.exception))
            self.assertEqual(len(store["lookups"]), 1)
            LK.plan(store, "nearby", "2026-04-20", 1, asked=True)          # the next issue has its own
            LK.plan(store, "portal:Zillow", RD, 1, asked=True)             # and each portal has its own page
        self.assertEqual((C.LIMITS["nearby_lookups_per_issue"], C.LIMITS["portal_pages_per_issue"], C.LIMITS["nearby_max_homes"]), (1, 1, 8))

    def test_a_result_needs_a_planned_lookup(self):
        with self.assertRaises(LK.Refused) as e:
            LK.close({}, "nearby", RD, "ok")
        self.assertIn("Run plan first", str(e.exception))
        store = {}
        LK.plan(store, "nearby", RD, 1, asked=True)
        with self.assertRaises(LK.Refused):
            LK.close(store, "nearby", RD, "skipped", "because")           # a skip names one of the known reasons
        x = LK.close(store, "nearby", RD, "skipped", "captcha", "a press and hold box")
        self.assertEqual((x["outcome"], x["reason"]), ("skipped", "captcha"))
        self.assertEqual(LK.skipped(store, RD), [x])
        self.assertEqual(LK.skipped(store, "2026-04-20"), [])

    def test_only_compact_json_is_accepted(self):
        self.assertEqual(LK.read_result('{"ok": true, "homes": []}', 500), {"ok": True, "homes": []})
        self.assertEqual(LK.read_result(json.dumps('{"portal": "Zillow", "views": 5}'), 500)["views"], 5)      # quoted by the browser tool
        for bad, word in (("<html><body>a whole page</body></html>", "not JSON"), ("[1, 2]", "one JSON object"),
                          (json.dumps({"homes": ["x" * 50] * 400}), "over the 12000 byte cap")):
            with self.assertRaises(LK.Refused) as e:
                LK.read_result(bad, C.LIMITS["nearby_json_max_bytes"])
            self.assertIn(word, str(e.exception))

    def test_a_block_is_read_from_the_result_itself(self):
        self.assertEqual(LK.blocked_reason({"ok": False, "blocked": True, "status": 403}), "blocked")
        self.assertEqual(LK.blocked_reason({"portal": "Zillow", "captcha": True}), "captcha")
        self.assertEqual(LK.blocked_reason({"ok": False, "reason": "failed"}), "failed")
        self.assertIsNone(LK.blocked_reason({"ok": True, "homes": []}))
        line = LK.skipped_note("Similar homes nearby", {"reason": "blocked"}, "That section is left out of this report.")
        self.assertEqual(line, "Similar homes nearby could not be checked for this report: the site blocked the request. That section is left out of this report.")
        self.assertFalse(C.has_dash(line))


class OnlineViewsStore(unittest.TestCase):
    """B2: figures per week per portal build up week by week into ledger.online."""

    def test_running_counts_become_weekly_figures_and_weekly_figures_stay(self):
        block, notes = OV.ledger_block(fixture("online_views.json"), LISTING, REPORT)
        self.assertEqual(block["portals"], ["Zillow", "Redfin"])
        self.assertEqual(block["as_of"], "2026-04-13")
        self.assertEqual(block["weeks"], [{"n": 4, "saves": {"Zillow": 6, "Redfin": 2}, "views": {"Zillow": 210, "Redfin": 65}},
                                          {"n": 5, "saves": {"Zillow": 4, "Redfin": 1}, "views": {"Zillow": 180, "Redfin": 50}}])
        self.assertEqual(block["since_listing"], {"views": {"Zillow": 800}, "saves": {"Zillow": 22}})      # the row for Apr 13 to 19 waits
        self.assertEqual(notes, {"skipped": [], "glance": [], "also": []})
        d = {"online": block}
        self.assertEqual(C.online_totals(d), (800 + 115, 22 + 3))
        self.assertEqual(C.online_by_week(d), {4: (275, 8), 5: (230, 5)})

    def test_a_first_reading_gives_the_count_since_listing_and_no_weekly_bar(self):
        store = OV.blank_store("sample-glen")
        OV.add_row(store, "zillow", 812, 31, "since_listing", "2026-04-13", source="portal_page")
        self.assertEqual(store["rows"][0]["week_start"], "2026-04-06")           # a Monday reading belongs to the week just ended
        block, notes = OV.ledger_block(store, LISTING, REPORT)
        self.assertEqual((block["weeks"], block["since_listing"]), ([], {"views": {"Zillow": 812}, "saves": {"Zillow": 31}}))
        self.assertEqual(C.online_totals({"online": block}), (812, 31))
        self.assertEqual(C.online_by_week({"online": block}), {})
        self.assertEqual(notes["also"], ["Zillow: first reading. A weekly figure starts with the next reading."])
        self.assertEqual((notes["glance"], notes["skipped"]), ([], []))

    def test_week_one_holds_everything_since_the_list_date(self):
        store = OV.blank_store("sample-glen")
        OV.add_row(store, "Zillow", 140, None, "since_listing", "2026-03-16")
        block, _ = OV.ledger_block(store, LISTING, {"report_date": "2026-03-16", "week_start": "2026-03-09", "week_end": "2026-03-15"})
        self.assertEqual(block["weeks"], [{"n": 1, "views": {"Zillow": 140}}])

    def test_a_count_that_went_down_gives_no_weekly_figure_and_says_so(self):
        store = OV.blank_store("sample-glen")
        OV.add_row(store, "Zillow", 500, None, "since_listing", "2026-04-06")
        OV.add_row(store, "Zillow", 480, None, "since_listing", "2026-04-13")
        block, notes = OV.ledger_block(store, LISTING, REPORT)
        self.assertEqual(block["weeks"], [])
        self.assertEqual(block["since_listing"]["views"], {"Zillow": 480})
        self.assertIn("went down between readings (500 to 480)", notes["glance"][0])

    def test_one_row_per_week_per_portal_and_the_week_a_reading_belongs_to(self):
        store = OV.blank_store("sample-glen")
        OV.add_row(store, "Redfin", 60, 2, "week", "2026-04-13")
        OV.add_row(store, "redfin", 66, 3, "week", "2026-04-14")                 # a correction the next day replaces it
        self.assertEqual([(r["portal"], r["views"], r["week_start"]) for r in store["rows"]], [("Redfin", 66, "2026-04-06")])
        self.assertEqual(C.iso(OV.default_week("2026-04-12")), "2026-04-06")     # read on the Sunday that ends the week
        self.assertEqual(C.iso(OV.default_week("2026-04-15")), "2026-04-06")     # read midweek: the report being built
        OV.add_row(store, "Redfin", 40, None, "week", "2026-04-13", week="2026-03-31")
        self.assertEqual(sorted(r["week_start"] for r in store["rows"]), ["2026-03-30", "2026-04-06"])
        self.assertEqual(OV.validate_store(store), [])
        for kw in (dict(views=-1), dict(views=None, saves=None), dict(views=1.5)):
            with self.assertRaises(SystemExit):
                OV.add_row(store, "Redfin", kw.get("views"), kw.get("saves"), "week", "2026-04-13")
        with self.assertRaises(SystemExit):
            OV.add_row(store, "Redfin", 5, None, "total", "2026-04-13")

    def test_the_store_is_validated(self):
        self.assertEqual(OV.validate_store(fixture("online_views.json")), [])
        bad = fixture("online_views.json")
        bad["rows"][0]["week_start"] = "2026-03-24"                              # a Tuesday
        bad["rows"][1]["counts"] = "weekly"
        bad["rows"].append(dict(bad["rows"][2]))
        problems = " ".join(OV.validate_store(bad))
        for word in ("the Monday of the week", "counts: one of week, since_listing", "a second row for Redfin"):
            self.assertIn(word, problems)

    def test_the_ledger_takes_the_block_and_counts_it(self):
        d = fixture("ledger_small.json")
        d["online"], _ = OV.ledger_block(fixture("online_views.json"), LISTING, REPORT)
        C.finish_ledger(d)
        self.assertEqual(C.validate_ledger(d, identity=C.load_identity()), [])
        self.assertEqual((d["totals"]["online_views"], d["totals"]["online_saves"]), (915, 25))
        self.assertEqual([w["online_views"] for w in d["weeks"]], [None, None, None, 275, 230])
        d["online"]["since_listing"]["views"]["Zillow"] = 300                    # less than its own weeks added up
        self.assertTrue(any("running count (300) is less than" in p for p in C.validate_ledger(d, identity=C.load_identity())))
        d["online"]["since_listing"] = {"views": {"Trulia": 5}}
        self.assertTrue(any("online.since_listing.views.Trulia" in p for p in C.validate_ledger(d, identity=C.load_identity())))


class OnlineViewsCommands(Folder):
    def test_the_operators_numbers_go_in_without_any_lookup(self):
        code, out = call(OV, "add", "--folder", self.folder, "--portal", "zillow", "--views", "812", "--saves", "31", "--counts", "since_listing",
                         "--as-of", "2026-04-13")
        self.assertEqual(code, 0, out)
        self.assertIn("filed: Zillow, week of Apr 6, 2026: 812 views, 31 saves (the running count since listing, read Apr 13, operator).", out)
        store = F.load_json(os.path.join(self.folder, "online_views.json"))
        self.assertEqual(store["lookups"], [])
        self.assertEqual(store["rows"][0]["source"], "operator")
        code, out = call(OV, "add", "--folder", self.folder, "--portal", "Zillow", "--views", "5")       # which kind of count is never guessed
        self.assertEqual(code, 2)
        self.assertIn("--counts", out)
        code, out = call(OV, "show", "--folder", self.folder, "--report-date", RD)
        self.assertIn("since listing: views {'Zillow': 812}", out)

    def test_one_page_per_portal_per_issue_and_only_when_asked(self):
        code, out = call(OV, "plan", "--folder", self.folder, "--portal", "Zillow", "--report-date", RD)
        self.assertEqual(code, OV.EXIT_REFUSED)
        self.assertIn("REFUSED: online views on Zillow: not asked for", out)
        self.assertFalse(os.path.exists(os.path.join(self.folder, "online_views.json")))
        code, out = call(OV, "plan", "--folder", self.folder, "--portal", "Zillow", "--asked", "--report-date", RD, "--url", "https://portal.example.test/home/218")
        self.assertEqual(code, 0, out)
        self.assertIn("planned: ONE page on Zillow", out)
        self.assertIn("portal_views.js", out)
        self.assertIn("STOP. Do not try another way.", out)
        code, out = call(OV, "plan", "--folder", self.folder, "--portal", "Zillow", "--asked", "--report-date", RD)
        self.assertEqual(code, OV.EXIT_REFUSED)
        self.assertIn("already used", out)
        self.assertEqual(call(OV, "plan", "--folder", self.folder, "--portal", "Redfin", "--asked", "--report-date", RD)[0], 0)
        result = self.write("zillow.json", {"portal": "Zillow", "views": 812, "saves": 31, "as_of": "2026-04-13"})
        code, out = call(OV, "add", "--folder", self.folder, "--result", result, "--report-date", RD)
        self.assertEqual(code, 0, out)
        store = F.load_json(os.path.join(self.folder, "online_views.json"))
        self.assertEqual([(r["portal"], r["views"], r["counts"], r["source"], r["week_start"]) for r in store["rows"]],
                         [("Zillow", 812, "since_listing", "portal_page", "2026-04-06")])
        self.assertEqual([(x["key"], x["outcome"]) for x in store["lookups"]], [("portal:Zillow", "ok"), ("portal:Redfin", "planned")])
        code, out = call(OV, "add", "--folder", self.folder, "--result", result, "--report-date", RD)      # the same result twice
        self.assertEqual(code, OV.EXIT_REFUSED)
        self.assertIn("no lookup is open for portal:Zillow", out)

    def test_the_listing_settings_can_ask_for_every_issue(self):
        self.listing["extras"] = {"online_views": {"every_issue": True, "pages": {"Redfin": "https://portal.example.test/home/218"}}}
        self.save_listing()
        code, out = call(OV, "plan", "--folder", self.folder, "--portal", "redfin", "--report-date", RD)
        self.assertEqual(code, 0, out)
        self.assertIn("https://portal.example.test/home/218", out)
        self.assertEqual(F.load_json(os.path.join(self.folder, "online_views.json"))["lookups"][0]["why"], "settings")

    def test_a_blocked_page_is_a_skip_with_a_plain_line_and_no_figure(self):
        call(OV, "plan", "--folder", self.folder, "--portal", "Zillow", "--asked", "--report-date", RD)
        result = self.write("blocked.json", json.dumps(json.dumps({"portal": "Zillow", "captcha": True})))
        code, out = call(OV, "add", "--folder", self.folder, "--result", result, "--report-date", RD)
        self.assertEqual(code, 0, out)
        self.assertIn("SKIPPED: Zillow gave no figure (the site asked for a human check)", out)
        store = F.load_json(os.path.join(self.folder, "online_views.json"))
        self.assertEqual(store["rows"], [])
        block, notes = OV.ledger_block(store, self.listing, REPORT)
        self.assertIsNone(block)
        self.assertEqual(notes["skipped"], ["Online views on Zillow could not be checked for this report: the site asked for a human check. "
                                           "The report is built without a new figure from that site."])
        call(OV, "plan", "--folder", self.folder, "--portal", "Redfin", "--asked", "--report-date", RD)
        code, out = call(OV, "skip", "--folder", self.folder, "--portal", "Redfin", "--reason", "blocked", "--report-date", RD)
        self.assertEqual(code, 0, out)
        self.assertEqual(len(OV.ledger_block(F.load_json(os.path.join(self.folder, "online_views.json")), self.listing, REPORT)[1]["skipped"]), 2)
        page = self.write("page.html", "<html>" + "x" * 5000 + "</html>")
        call(OV, "plan", "--folder", self.folder, "--portal", "Trulia", "--asked", "--report-date", RD)
        code, out = call(OV, "add", "--folder", self.folder, "--result", page, "--report-date", RD)
        self.assertEqual(code, OV.EXIT_REFUSED)
        self.assertIn("compact JSON", out)


class NearbyDiff(unittest.TestCase):
    """B3: where each watched home stands and what changed since the last issue, worked out in Python."""

    def test_the_ledger_section_for_the_issue(self):
        block, notes = NB.ledger_block(fixture("nearby.json"), LISTING, REPORT)
        self.assertEqual((block["as_of"], block["checked_for_this_issue"], block["source"]), ("2026-04-13", True, "Public listing pages"))
        self.assertEqual(block["scope"], "Five 3 bedroom single family homes in Fixture City, chosen on Mar 16")
        got = [(h["address"], h["status"], h["change"], h["change_date"], h["days_on_market"]) for h in block["homes"]]
        self.assertEqual(got, [("14 Sample Fern Ln", "active", "back_on_market", "2026-04-10", 3),
                               ("31 Sample Alder Way", "active", "price_change", "2026-04-08", 40),
                               ("9 Sample Cedar Ct", "pending", "went_pending", "2026-04-09", 12),
                               ("52 Sample Birch Dr", "sold", "sold", "2026-04-07", 9),
                               ("7 Sample Elm Pl", "active", "none", None, 61)])
        self.assertEqual((block["homes"][1]["price_before"], block["homes"][1]["list_price"]), (1199000, 1150000))
        self.assertEqual(block["homes"][3]["sold_price"], 1182000)
        self.assertEqual(notes["summary"], "4 of the 5 homes we are watching changed: 1 price change, 1 went pending, 1 sold and 1 back on the market.")
        d = fixture("ledger_small.json")
        d["nearby"] = block
        C.finish_ledger(d)
        self.assertEqual(C.validate_ledger(d, identity=C.load_identity()), [])

    def test_an_issue_with_no_snapshot_has_no_section(self):
        store = fixture("nearby.json")
        block, notes = NB.ledger_block(store, LISTING, {"report_date": "2026-04-20", "week_start": "2026-04-13", "week_end": "2026-04-19"})
        self.assertIsNone(block)
        self.assertEqual(notes["skipped"], [])
        self.assertIn("were not checked for this issue", notes["also"][0])
        first, _ = NB.ledger_block(store, LISTING, {"report_date": "2026-04-06", "week_start": "2026-03-30", "week_end": "2026-04-05"})
        self.assertEqual([h["change"] for h in first["homes"]], ["none"] * 5)      # nothing dated inside that week, and no earlier check

    def test_a_dated_event_decides_and_a_bare_difference_is_marked_approximate(self):
        f = NB.change_of
        act = {"status": "active", "list_price": 500000, "list_date": "2026-03-01"}
        self.assertEqual(f(None, act, "2026-04-06", "2026-04-13"), ("none", None, None, False))
        self.assertEqual(f(None, dict(act, list_date="2026-04-08"), "2026-04-06", "2026-04-13"), ("new_listing", "2026-04-08", None, False))
        self.assertEqual(f(act, dict(act, status="pending"), "2026-04-07", "2026-04-13"), ("went_pending", "2026-04-13", None, True))
        self.assertEqual(f(act, dict(act, list_price=480000), "2026-04-07", "2026-04-13"), ("price_change", "2026-04-13", 500000, True))
        self.assertEqual(f(dict(act, status="pending"), act, "2026-04-07", "2026-04-13"), ("back_on_market", "2026-04-13", None, True))
        gone = dict(act, status="withdrawn", off_date="2026-04-09")
        self.assertEqual(f(act, gone, "2026-04-07", "2026-04-13"), ("withdrawn", "2026-04-09", None, False))
        old = dict(act, price_change={"date": "2026-03-20", "from": 520000, "to": 500000})                # an old cut is not this week's news
        self.assertEqual(f(old, old, "2026-04-07", "2026-04-13"), ("none", None, None, False))
        self.assertEqual(NB.days_on_market(gone, "2026-04-13"), 39)
        self.assertIsNone(NB.days_on_market({"status": "active"}, "2026-04-13"))

    def test_the_summary_is_one_sentence(self):
        self.assertEqual(NB.summary_sentence([{"change": "none"}] * 6), "No change among the 6 homes we are watching.")
        self.assertEqual(NB.summary_sentence([{"change": "sold"}]), "1 of the 1 home we are watching changed: 1 sold.")
        self.assertEqual(NB.summary_sentence([{"change": "new_listing"}, {"change": "new_listing"}, {"change": "none"}]),
                         "2 of the 3 homes we are watching changed: 2 new listings.")

    def test_the_store_is_validated(self):
        self.assertEqual(NB.validate_store(fixture("nearby.json"), LISTING), [])
        bad = fixture("nearby.json")
        bad["watch"] += [dict(bad["watch"][0], id=str(9100 + i)) for i in range(4)]
        bad["watch"][1]["address"] = LISTING["address"]
        bad["watch"][2]["why"] = ""
        bad["snapshots"].append(dict(bad["snapshots"][1]))
        bad["snapshots"][0]["homes"][0]["status"] = "expired"
        problems = " ".join(NB.validate_store(bad, LISTING))
        for word in ("at most 8 homes", "is this listing", "needs address and why", "a second snapshot for the issue dated 2026-04-13", "status: one of"):
            self.assertIn(word, problems)


class NearbyCommands(Folder):
    def test_first_use_one_lookup_gives_the_candidates_the_watch_list_and_the_first_snapshot(self):
        code, out = call(NB, "plan", "--folder", self.folder, "--report-date", RD)
        self.assertEqual(code, NB.EXIT_REFUSED)
        self.assertIn("not asked for", out)
        self.listing["extras"] = {"nearby": {"search": {"region_id": 99001, "region_type": 6}}}
        self.save_listing()
        code, out = call(NB, "plan", "--folder", self.folder, "--asked", "--report-date", RD)
        self.assertEqual(code, 0, out)
        self.assertIn("planned: ONE lookup of similar homes nearby for the issue dated 2026-04-13 (first use: candidates for the watch list).", out)
        with open(os.path.join(self.folder, "work", "nearby_call.js"), encoding="utf-8") as f:
            js = f.read()
        self.assertIn("globalThis.srNearby = async function", js)
        last = js.strip().splitlines()[-1]
        self.assertTrue(last.startswith("JSON.stringify(await globalThis.srNearby({"))
        args = json.loads(last[len("JSON.stringify(await globalThis.srNearby("):-2])
        self.assertEqual((args["mode"], args["family"], args["search"], args["max"]), ("candidates", "house", {"region_id": 99001, "region_type": 6}, 12))
        self.assertEqual(args["subject"]["address"], "218 Sample Glen Ct")
        self.assertNotIn("watch", args)
        code, out = call(NB, "plan", "--folder", self.folder, "--asked", "--report-date", RD)
        self.assertEqual(code, NB.EXIT_REFUSED)                                   # the ONE lookup of this issue is taken
        self.assertIn("already used (planned). Do not run another.", out)

        code, out = call(NB, "store", "--folder", self.folder, "--result", os.path.join(FIX, "nearby_lookup_candidates.json"), "--report-date", RD)
        self.assertEqual(code, 0, out)
        self.assertIn("stored: 6 candidates for the watch list", out)             # the subject itself is never a candidate
        self.assertIn("No second lookup is needed.", out)
        code, out = call(NB, "choose", "--folder", self.folder, "--auto")
        self.assertEqual(code, 0, out)
        store = F.load_json(os.path.join(self.folder, "nearby.json"))
        self.assertEqual(store["scope"], "Six 3 bedroom single family homes in Fixture City, chosen on Apr 13")
        self.assertEqual(store["watch"][0]["address"], "7 Sample Elm Pl")         # still for sale and the closest in size
        self.assertEqual(store["watch"][0]["why"], "Same city, same bedroom count, 5 sq ft smaller")
        self.assertEqual([w["address"] for w in store["watch"][-2:]], ["40 Sample Glen Ct", "52 Sample Birch Dr"])     # sold homes come last
        condo = dict(self.listing, address="218 Sample Glen Ct #214", property_type="Condominium", beds=1, sqft=776)
        units = [{"id": "1", "address": "9 Sample Far Rd #2", "status": "active", "sqft": 776, "beds": 1},
                 {"id": "2", "address": "218 Sample Glen Ct #322", "status": "sold", "sqft": 800, "beds": 1}]
        self.assertEqual([h["id"] for h in NB.rank_candidates(units, condo)], ["2", "1"])                # the same building comes first
        self.assertEqual(NB.why_chosen(units[1], condo), "Same building, same bedroom count, 24 sq ft larger")
        self.assertEqual(NB.scope_sentence(units, condo, "2026-04-13"), "Two 1 bedroom condos in Fixture City, chosen on Apr 13")
        self.assertEqual(NB.validate_store(store, self.listing), [])
        block, notes = NB.ledger_block(store, self.listing, REPORT)
        self.assertEqual(len(block["homes"]), 6)
        changes = dict((h["address"], h["change"]) for h in block["homes"])
        self.assertEqual(changes["14 Sample Fern Ln"], "new_listing")             # with no earlier check, the dated events of this week
        self.assertEqual(changes["40 Sample Glen Ct"], "none")                    # sold in February: not this week's news
        self.assertEqual(changes["52 Sample Birch Dr"], "sold")
        self.assertEqual([x["outcome"] for x in store["lookups"]], ["ok"])

        nxt = "2026-04-20"                                                        # the next issue: the watch list is looked up, once
        code, out = call(NB, "plan", "--folder", self.folder, "--asked", "--report-date", nxt)
        self.assertEqual(code, 0, out)
        with open(os.path.join(self.folder, "work", "nearby_call.js"), encoding="utf-8") as f:
            args = json.loads(f.read().strip().splitlines()[-1][len("JSON.stringify(await globalThis.srNearby("):-2])
        self.assertEqual(args["mode"], "watch")
        self.assertEqual(len(args["watch"]), 6)
        code, out = call(NB, "store", "--folder", self.folder, "--result", os.path.join(FIX, "nearby_lookup_watch.json"), "--report-date", nxt)
        self.assertEqual(code, 0, out)
        self.assertIn("3 of the 5 homes we are watching changed: 1 went pending, 1 taken off the market and 1 back on the market.", out)
        self.assertIn("1 home on the watch list had no usable record in this check and is left out: 52 Sample Birch Dr.", out)
        block, _ = NB.ledger_block(F.load_json(os.path.join(self.folder, "nearby.json")), self.listing,
                                   {"report_date": nxt, "week_start": "2026-04-13", "week_end": "2026-04-19"})
        got = dict((h["address"], (h["status"], h["change"], h["change_date"])) for h in block["homes"])
        self.assertEqual(got["14 Sample Fern Ln"], ("pending", "went_pending", "2026-04-17"))
        self.assertEqual(got["7 Sample Elm Pl"], ("withdrawn", "withdrawn", "2026-04-15"))
        self.assertEqual(got["9 Sample Cedar Ct"], ("active", "back_on_market", "2026-04-20"))       # pending last week, active now, no date
        self.assertTrue(next(h for h in block["homes"] if h["address"] == "9 Sample Cedar Ct")["change_date_approximate"])

    def test_a_blocked_lookup_is_skipped_and_the_build_goes_on_without_the_section(self):
        store = fixture("nearby.json")
        store["snapshots"], store["lookups"] = store["snapshots"][:1], store["lookups"][:1]
        F.save_json(os.path.join(self.folder, "nearby.json"), store)
        self.listing["extras"] = {"nearby": {"every_issue": True}}
        self.save_listing()
        self.assertEqual(call(NB, "plan", "--folder", self.folder, "--report-date", RD)[0], 0)
        blocked = self.write("blocked.json", {"ok": False, "blocked": True, "status": 403, "requests": 1})
        code, out = call(NB, "store", "--folder", self.folder, "--result", blocked, "--report-date", RD)
        self.assertEqual(code, 0, out)
        self.assertIn("SKIPPED: the lookup gave no homes (the site blocked the request). The report is built without the section. Do not try another way.", out)
        code, out = call(NB, "plan", "--folder", self.folder, "--report-date", RD)
        self.assertEqual(code, NB.EXIT_REFUSED)                                   # a block is never retried
        self.assertIn("already used (skipped, blocked)", out)
        block, notes = NB.ledger_block(F.load_json(os.path.join(self.folder, "nearby.json")), self.listing, REPORT)
        self.assertIsNone(block)
        self.assertEqual(notes["skipped"], ["Similar homes nearby could not be checked for this report: the site blocked the request. "
                                           "That section is left out of this report."])
        code, out = call(NB, "show", "--folder", self.folder, "--report-date", RD)
        self.assertIn("no section for the issue dated 2026-04-13", out)
        self.assertIn("lookup: skipped (blocked)", out)

    def test_skip_by_hand_and_a_result_that_is_not_compact(self):
        self.assertEqual(call(NB, "skip", "--folder", self.folder, "--reason", "captcha", "--report-date", RD)[0], NB.EXIT_REFUSED)
        call(NB, "plan", "--folder", self.folder, "--asked", "--report-date", RD)
        page = self.write("page.json", json.dumps({"ok": True, "homes": [{"id": i, "address": "x" * 300} for i in range(60)]}))
        code, out = call(NB, "store", "--folder", self.folder, "--result", page, "--report-date", RD)
        self.assertEqual(code, NB.EXIT_REFUSED)
        self.assertIn("over the 12000 byte cap", out)
        code, out = call(NB, "skip", "--folder", self.folder, "--reason", "pane_unavailable", "--detail", "the pane did not open", "--report-date", RD)
        self.assertEqual(code, 0, out)
        self.assertIn("the browser pane was not available", out)


class HeroPhoto(Folder):
    """B6: a stable public https photo, found on a page that is already open, or no photo."""

    def setUp(self):
        Folder.setUp(self)
        self.answers = ("image/jpeg", 250000)                 # what the address's headers say; no test touches the network

        def probe(url, timeout=20):
            if isinstance(self.answers, Exception):
                raise self.answers
            return self.answers
        real, HP.probe = HP.probe, probe
        self.addCleanup(setattr, HP, "probe", real)

    def test_only_a_public_https_photo_of_a_usable_size(self):
        self.assertIsNone(HP.check("https://photos.example.test/218/front.jpg", 1600))
        for url, width, word in (("http://photos.example.test/a.jpg", 1600, "https"), (r"C:\Users\someone\front.jpg", None, "https"),
                                 ("https://photos.example.test/a.jpg?token=abc", 1600, "expires"), ("https://photos.example.test/a.jpg", 400, "at least 600"),
                                 ("https://localhost/a.jpg", 1600, "private")):
            self.assertIn(word, HP.check(url, width))

    def test_set_from_the_snippet_result_and_clear(self):
        result = self.write("hero.json", json.dumps(json.dumps({"photo_url": "https://photos.example.test/218/front.jpg", "width": 1600, "height": 1067,
                                                                "page": "https://example.test/homes/218-sample-glen"})))
        code, out = call(HP, "set", "--folder", self.folder, "--result", result)
        self.assertEqual(code, 0, out)
        listing = F.load_json(os.path.join(self.folder, "listing.json"))
        self.assertEqual(listing["hero_photo"], "https://photos.example.test/218/front.jpg")
        self.assertEqual(listing["extras"]["hero"]["page"], "https://example.test/homes/218-sample-glen")
        none = self.write("none.json", {"photo_url": None, "why": "the page names no share image"})
        code, out = call(HP, "set", "--folder", self.folder, "--result", none)
        self.assertEqual(code, 0)
        self.assertIn("The report is built without one.", out)
        self.assertEqual(F.load_json(os.path.join(self.folder, "listing.json"))["hero_photo"], "https://photos.example.test/218/front.jpg")
        self.assertEqual(listing["extras"]["hero"]["bytes"], 250000)
        self.assertIsNone(HP.heavy_note(listing))
        self.assertEqual(call(HP, "set", "--folder", self.folder, "--url", "http://x.example.test/a.jpg")[0], 2)
        self.assertEqual(call(HP, "clear", "--folder", self.folder)[0], 0)
        self.assertIsNone(F.load_json(os.path.join(self.folder, "listing.json"))["hero_photo"])
        self.assertIn("none the report can use", call(HP, "show", "--folder", self.folder)[1])

    def test_the_address_must_answer_as_an_image_and_a_heavy_file_is_said_plainly(self):
        url = "https://photos.example.test/218/front.jpg"
        self.answers = ("text/html", 5000)
        code, out = call(HP, "set", "--folder", self.folder, "--url", url)
        self.assertIn("answers as text/html, not as an image", out)
        self.assertIsNone(F.load_json(os.path.join(self.folder, "listing.json"))["hero_photo"])
        self.answers = OSError("no route")
        code, out = call(HP, "set", "--folder", self.folder, "--url", url)
        self.assertIn("did not answer", out)
        self.assertIsNone(F.load_json(os.path.join(self.folder, "listing.json"))["hero_photo"])
        self.answers = ("image/jpeg", 3580264)
        code, out = call(HP, "set", "--folder", self.folder, "--url", url, "--page", "https://example.test/homes/218-sample-glen")
        self.assertEqual(code, 0, out)
        listing = F.load_json(os.path.join(self.folder, "listing.json"))
        self.assertEqual(listing["hero_photo"], url)
        note = HP.heavy_note(listing)
        self.assertEqual(note, "The masthead photo is a 3.6 MB file, so it may load slowly on a phone. A smaller copy of the same photo would be better.")
        self.assertIn(note, out)
        listing["hero_photo"] = None
        self.assertIsNone(HP.heavy_note(listing))


if __name__ == "__main__":
    unittest.main()
