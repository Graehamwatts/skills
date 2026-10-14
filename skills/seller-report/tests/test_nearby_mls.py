# -*- coding: utf-8 -*-
"""Tests for nearby_from_mls.py: similar homes nearby from a Matrix search on MLSListings, and the MLS route through
nearby_update.py (plan --site mls, store, choose, the ledger block).

    python -m unittest tests.test_nearby_mls      (from the skill folder)

The grids below are written the way scripts/web/matrix_grid.js returns them (tests/test_web_snippets.py runs the
snippet itself on a pretend Matrix page). Synthetic data only: the listing is the fixture listing of
tests/fixtures/make_workbook.py, every other address is invented, and every MLS number starts ML8000.
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
sys.path.insert(0, os.path.join(SKILL, "scripts"))
sys.path.insert(0, os.path.join(HERE, "fixtures"))
import sr_contract as C  # noqa: E402
import sr_files as F  # noqa: E402
import nearby_from_mls as M  # noqa: E402
import nearby_update as NU  # noqa: E402
import make_workbook as W  # noqa: E402

AS_OF = "2026-04-13"
CLOSED_COLS = ["status", "mls", "address", "city", "list_price", "sale_price", "close_date", "dom", "beds", "baths", "sqft", "members_only"]
HOT_COLS = ["status", "mls", "address", "list_price", "change_date", "change_type", "members_only"]


def grid(columns, rows, display, **extra):
    g = {"ok": True, "site": "mlslistings", "grid": "matrix", "as_of": AS_OF, "display": display, "columns": columns, "rows": rows,
         "partial": None, "skipped_columns": [], "duplicate_columns": [], "odd_rows": 0}
    g.update(extra)
    return g


def closed(*more):
    return grid(CLOSED_COLS, [
        ["Active", "ML80000101", "14 Sample Fern Ln", "Fixture City", "$1,210,000", "", "", "3", "3", "2|1", "1,510", ""],
        ["Contingent", "ML80000102", "9 Sample Cedar Ct", "Fixture City", "$1,249,000", "", "", "15", "3", "2", "1,620", ""],
        ["Sold", "ML80000103", "52 SAMPLE BIRCH DR", "Fixture City", "$1,182,000", "$1,190,000", "4/7/2026", "28", "3", "2", "1,390", ""],
        ["Sold", "ML80000104", "7 Sample Hidden Way", "Fixture City", "$999,000", "$1,005,000", "3/30/2026", "12", "3", "2", "1,450", "Members Only"],
        ["Active", "ML00000218", "218 Sample Glen Ct", "Fixture City", "$1,175,000", "", "", "32", "3", "2", "1,480", ""],
    ] + list(more), "my:Closed date template")


def hotsheet(*more):
    return grid(HOT_COLS, [
        ["Active", "ML80000101", "14 Sample Fern Ln", "$1,210,000", "4/10/2026", "New Listing", ""],
        ["Contingent", "ML80000102", "9 Sample Cedar Ct", "$1,249,000", "4/9/2026", "Active > Contingent", ""],
        ["Sold", "ML80000103", "52 SAMPLE BIRCH DR", "$1,190,000", "4/7/2026", "Contingent > Sold", ""],
        ["Sold", "ML80000104", "7 Sample Hidden Way", "$1,005,000", "3/30/2026", "Pending > Sold", "Y"],
        ["Active", "ML00000218", "218 Sample Glen Ct", "$1,175,000", "4/1/2026", "Price Decrease", ""],
    ] + list(more), "Agent 1 Line Hotsheet")


def quiet(fn, *a, **k):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*a, **k)
    return code, out.getvalue()


class FromMatrix(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sr nearby mls ")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.folder = os.path.join(self.tmp, "seller-reports", "sample-glen")
        os.makedirs(os.path.join(self.folder, "work"))
        F.save_json(os.path.join(self.folder, "listing.json"), copy.deepcopy(W.LISTING))

    def market(self, days):
        F.save_json(os.path.join(self.folder, "market.json"), {"sales": [{"address": "52 Sample Birch Dr", "sold_date": "2026-04-07",
                                                                         "sold_price": 1190000, "days_to_contract": days}]})

    def homes(self, result):
        return dict((h["id"], h) for h in result["homes"])

    def test_two_displays_of_one_search_become_one_home_each(self):
        result, lines = M.build(self.folder, [closed(), hotsheet()])
        h = self.homes(result)
        self.assertEqual(sorted(h), ["ML80000101", "ML80000102", "ML80000103"])
        self.assertEqual(h["ML80000101"], {"id": "ML80000101", "address": "14 Sample Fern Ln", "city": "Fixture City", "beds": 3, "baths": 2.5,
                                           "sqft": 1510, "dom": 3, "list_price": 1210000, "status": "active", "list_date": "2026-04-10"})
        self.assertEqual((h["ML80000102"]["status"], h["ML80000102"]["pending_date"], h["ML80000102"]["dom"]), ("pending", "2026-04-09", 15))
        sold = h["ML80000103"]
        self.assertEqual((sold["status"], sold["sold_price"], sold["sold_date"], sold["address"]), ("sold", 1190000, "2026-04-07", "52 Sample Birch Dr"))
        self.assertNotIn("list_price", sold)                       # the Price column of a sold home is never read
        self.assertEqual(sold["dom"], 28)
        self.assertEqual(result["excluded"], {"members_only": 1, "this_listing": 1})
        self.assertEqual((result["site"], result["mode"], result["as_of"], result["source"]),
                         ("mlslistings", "candidates", AS_OF, "MLSListings, checked Apr 13, 2026"))
        self.assertEqual(result["refused"], [])
        self.assertTrue(any("1 members-only" in ln for ln in lines))

    def test_members_only_listings_never_come_through(self):
        result, _ = M.build(self.folder, [closed(), hotsheet()])
        self.assertNotIn("7 Sample Hidden Way", json.dumps(result))
        self.assertNotIn("ML80000104", json.dumps(result))

    def test_a_display_without_the_members_only_column_cannot_vouch_for_a_home(self):
        g = closed()
        g["columns"] = CLOSED_COLS[:-1]
        g["rows"] = [r[:-1] for r in g["rows"]]
        with self.assertRaises(SystemExit) as e:
            M.build(self.folder, [g])
        self.assertIn("Members Only", str(e.exception))
        result, _ = M.build(self.folder, [g, hotsheet()])            # the other display of the same search says
        self.assertEqual(sorted(self.homes(result)), ["ML80000101", "ML80000102", "ML80000103"])

    def test_one_sale_never_shows_two_day_counts(self):
        self.market(26)
        result, lines = M.build(self.folder, [closed(), hotsheet()])
        self.assertNotIn("dom", self.homes(result)["ML80000103"])
        self.assertTrue(any("market chart counts 26 days" in ln for ln in lines))
        self.market(28)
        result, _ = M.build(self.folder, [closed(), hotsheet()])
        self.assertEqual(self.homes(result)["ML80000103"]["dom"], 28)
        self.market(None)                                             # a sale the chart prints with no day count
        result, _ = M.build(self.folder, [closed(), hotsheet()])
        self.assertEqual(self.homes(result)["ML80000103"]["dom"], 28)

    def test_rows_it_cannot_read_are_refused_not_guessed(self):
        bad = [
            ["Coming Soon", "ML80000110", "1 Sample Soon St", "Fixture City", "$900,000", "", "", "0", "3", "2", "1,400", ""],
            ["Active", "ML80000111", "2 Sample Odd St", "Fixture City", "$1.2M", "", "", "4", "3", "2", "1,400", ""],
            ["Active", "ML80000112", "3 Sample Flag St", "Fixture City", "$1,100,000", "", "", "4", "3", "2", "1,400", "maybe"],
            ["Sold", "ML80000113", "4 Sample Sold St", "Fixture City", "$1,000,000", "", "4/2/2026", "9", "3", "2", "1,400", ""],
            ["Sold", "ML80000114", "5 Sample Date St", "Fixture City", "", "$1,000,000", "April 2", "9", "3", "2", "1,400", ""],
            ["Active", "ML80000115", "6 Sample Size St", "Fixture City", "$1,000,000", "", "", "9", "3", "2", "about 1400", ""],
            ["Active", "ML80000116", "8 Sample Twice St", "Fixture City", "$1,000,000", "", "", "9", "3", "2", "1,400", ""],
        ]
        other = ["Active", "ML80000116", "8 Sample Twice St", "$1,050,000", "4/8/2026", "New Listing", ""]
        result, lines = M.build(self.folder, [closed(*bad), hotsheet(other)])
        why = dict((r["mls"], r["why"]) for r in result["refused"])
        self.assertEqual(sorted(why), ["ML80000110", "ML80000111", "ML80000112", "ML80000113", "ML80000114", "ML80000115", "ML80000116"])
        self.assertIn("status not known", why["ML80000110"])
        self.assertIn("price in a form not known", why["ML80000111"])
        self.assertIn("neither yes nor no", why["ML80000112"])
        self.assertIn("no sale price", why["ML80000113"])
        self.assertIn("date in a form not known", why["ML80000114"])
        self.assertIn("square feet", why["ML80000115"])
        self.assertIn("disagree on list price", why["ML80000116"])
        self.assertEqual(sorted(self.homes(result)), ["ML80000101", "ML80000102", "ML80000103"])
        self.assertTrue(any(ln.startswith("refused (not read, not guessed): ML80000110") for ln in lines))

    def test_a_grid_showing_only_some_rows_or_no_grid_is_refused_whole(self):
        with self.assertRaises(SystemExit) as e:
            M.build(self.folder, [closed(), grid(HOT_COLS, hotsheet()["rows"], None, partial={"shown": 50, "total": 73})])
        self.assertIn("50 of its 73 rows", str(e.exception))
        with self.assertRaises(SystemExit) as e:
            M.build(self.folder, [{"ok": False, "site": "mlslistings", "reason": "signed_out"}])
        self.assertIn("Graeham signs in", str(e.exception))
        with self.assertRaises(SystemExit):
            M.build(self.folder, [grid(["mls", "address"], [["ML80000101", "14 Sample Fern Ln"]], None)])
        with self.assertRaises(SystemExit):
            M.build(self.folder, [grid(CLOSED_COLS, [], None, duplicate_columns=["list_price"])])

    def test_contingent_is_pending_and_its_date_is_a_status_change_date_only(self):
        hot = hotsheet()
        hot["rows"][1] = ["Contingent", "ML80000102", "9 Sample Cedar Ct", "$1,249,000", "4/11/2026", "Price Decrease", ""]
        result, lines = M.build(self.folder, [closed(), hot])
        h = self.homes(result)["ML80000102"]
        self.assertEqual(h["status"], "pending")
        self.assertNotIn("pending_date", h)
        self.assertTrue(any("pending date is not known" in ln for ln in lines))

    def test_a_price_change_carries_the_old_price_when_the_display_shows_it(self):
        g = grid(["status", "mls", "address", "list_price", "previous_price", "change_date", "change_type", "members_only"],
                 [["Active", "ML80000120", "11 Sample Cut Ln", "$1,150,000", "$1,199,000", "4/8/2026", "Price Decrease", "N"]], "Hotsheet")
        result, _ = M.build(self.folder, [g])
        self.assertEqual(result["homes"][0]["price_change"], {"date": "2026-04-08", "to": 1150000, "from": 1199000})

    def test_more_than_the_candidate_cap_keeps_the_closest(self):
        rows = [["Active", "ML8000%04d" % (200 + i), "%d Sample Many Rd" % (10 + i), "Fixture City", "$1,100,000", "", "", "5", "3", "2",
                 str(1480 + 20 * i), ""] for i in range(15)]
        result, lines = M.build(self.folder, [grid(CLOSED_COLS, rows, "x")])
        self.assertEqual(len(result["homes"]), C.LIMITS["nearby_candidates_max"])
        self.assertEqual(result["homes"][0]["sqft"], 1480)
        self.assertTrue(any("15 homes came back" in ln for ln in lines))

    def test_the_mls_route_from_plan_to_the_ledger_block(self):
        F.save_json(os.path.join(self.folder, "work", "closed.json"), json.dumps(closed()))      # quoted, as the browser tool hands it back
        F.save_json(os.path.join(self.folder, "work", "hot.json"), hotsheet())
        code, out = quiet(NU.main, ["plan", "--folder", self.folder, "--asked", "--site", "mls", "--report-date", W.REPORT_DATE])
        self.assertEqual(code, 0, out)
        with open(os.path.join(self.folder, "work", "nearby_call.js"), encoding="utf-8") as f:
            call = f.read()
        self.assertIn("globalThis.srMatrixGrid()", call)
        self.assertNotIn("srNearby", call)
        self.assertIn("signs in to MLSListings in the in-app browser himself", out)
        self.assertIn("Agent 1 Line Hotsheet", out)
        code, out = quiet(M.main, ["--folder", self.folder, "--grid", os.path.join(self.folder, "work", "closed.json"),
                                   "--grid", os.path.join(self.folder, "work", "hot.json"), "--type", "Single Family"])
        self.assertEqual(code, 0, out)
        res = os.path.join(self.folder, "work", "nearby_mls_result.json")
        self.assertTrue(all(h["type"] == "Single Family" for h in F.load_json(res)["homes"]))
        code, out = quiet(NU.main, ["store", "--folder", self.folder, "--result", res, "--report-date", W.REPORT_DATE])
        self.assertEqual(code, 0, out)
        code, out = quiet(NU.main, ["choose", "--folder", self.folder, "--auto", "--report-date", W.REPORT_DATE])
        self.assertEqual(code, 0, out)
        store = F.load_json(os.path.join(self.folder, "nearby.json"))
        self.assertEqual(store["source"], "MLSListings, checked Apr 13, 2026")
        self.assertEqual(NU.validate_store(store, W.LISTING), [])
        rd = C.parse_date(W.REPORT_DATE)
        block, notes = NU.ledger_block(store, W.LISTING, NU._report(rd))
        self.assertEqual(block["source"], "MLSListings, checked Apr 13, 2026")
        days = dict((h["address"], h["days_on_market"]) for h in block["homes"])
        self.assertEqual(days, {"14 Sample Fern Ln": 3, "9 Sample Cedar Ct": 15, "52 Sample Birch Dr": 28})
        # a second lookup for the same issue is refused, whichever site it would use
        code, out = quiet(NU.main, ["plan", "--folder", self.folder, "--asked", "--site", "mls", "--report-date", W.REPORT_DATE])
        self.assertEqual(code, NU.EXIT_REFUSED, out)

    def mls_watch_list(self):
        res = os.path.join(self.folder, "work", "nearby_mls_result.json")
        result, _ = M.build(self.folder, [closed(), hotsheet()])
        F.save_json(res, result)
        quiet(NU.main, ["plan", "--folder", self.folder, "--asked", "--site", "mls", "--report-date", W.REPORT_DATE])
        self.assertEqual(quiet(NU.main, ["store", "--folder", self.folder, "--result", res, "--report-date", W.REPORT_DATE])[0], 0)
        self.assertEqual(quiet(NU.main, ["choose", "--folder", self.folder, "--auto", "--report-date", W.REPORT_DATE])[0], 0)
        store = F.load_json(os.path.join(self.folder, "nearby.json"))
        self.assertEqual(store["watch_site"], "mlslistings")
        return store

    def test_a_watch_list_from_the_mls_is_never_looked_up_on_the_public_site(self):
        self.mls_watch_list()
        nxt = "2026-04-20"
        code, out = quiet(NU.main, ["plan", "--folder", self.folder, "--asked", "--site", "redfin", "--report-date", nxt])
        self.assertEqual(code, NU.EXIT_REFUSED, out)
        self.assertIn("Run plan --site mls", out)
        self.assertEqual(LK_for(self.folder, nxt), [])                 # the refusal does not use up the one lookup
        code, out = quiet(NU.main, ["plan", "--folder", self.folder, "--asked", "--report-date", nxt])    # the default follows the list
        self.assertEqual(code, 0, out)
        self.assertIn("on MLSListings", out)
        with open(os.path.join(self.folder, "work", "nearby_call.js"), encoding="utf-8") as f:
            self.assertNotIn("srNearby(", f.read())
        # a result from the public site for that list is refused, never stored
        res = os.path.join(self.folder, "work", "redfin.json")
        F.save_json(res, {"ok": True, "site": "redfin", "mode": "watch", "as_of": "2026-04-20",
                          "homes": [{"id": "ML80000103", "address": "52 Sample Birch Dr", "status": "withdrawn"}]})
        code, out = quiet(NU.main, ["store", "--folder", self.folder, "--result", res, "--report-date", nxt])
        self.assertEqual(code, NU.EXIT_REFUSED, out)
        self.assertIsNone(NU.snapshot_for(F.load_json(os.path.join(self.folder, "nearby.json")), nxt))

    def test_a_public_site_watch_list_is_not_read_from_the_mls(self):
        store = NU.blank_store("sample-glen")
        store.update(watch=[{"id": "9001", "address": "14 Sample Fern Ln", "why": "Same city"}], scope="One home", chosen_on="2026-04-06")
        F.save_json(os.path.join(self.folder, "nearby.json"), store)
        with self.assertRaises(SystemExit) as e:
            M.build(self.folder, [closed(), hotsheet()])
        self.assertIn("chosen from the public site", str(e.exception))
        code, out = quiet(NU.main, ["plan", "--folder", self.folder, "--asked", "--site", "mls", "--report-date", W.REPORT_DATE])
        self.assertEqual(code, NU.EXIT_REFUSED, out)

    def test_a_sale_is_never_undone_by_a_later_check(self):
        sold = {"id": "ML80000103", "address": "52 Sample Birch Dr", "status": "sold", "sold_price": 1190000, "sold_date": "2026-04-07"}
        self.assertEqual(NU.change_of(sold, {"id": "ML80000103", "address": "52 Sample Birch Dr", "status": "withdrawn"}, "2026-04-14", "2026-04-20"),
                         ("none", None, None, False))
        store = NU.blank_store("sample-glen")
        store.update(watch=[{"id": "ML80000103", "address": "52 Sample Birch Dr", "why": "Same city"}], scope="One home", chosen_on="2026-04-06",
                     snapshots=[{"report_date": "2026-04-13", "as_of": "2026-04-13", "homes": [sold]},
                                {"report_date": "2026-04-20", "as_of": "2026-04-20", "homes": [{"id": "ML80000103", "address": "52 Sample Birch Dr",
                                                                                                "status": "withdrawn"}]}])
        block, notes = NU.ledger_block(store, W.LISTING, NU._report(C.parse_date("2026-04-20")))
        self.assertEqual((block["homes"][0]["status"], block["homes"][0]["change"], block["homes"][0]["sold_price"]), ("sold", "none", 1190000))
        self.assertTrue(any("a sale is final" in x for x in notes["also"]))
        self.assertNotIn("taken off the market", notes["summary"])

    def test_a_public_site_result_puts_back_its_own_source(self):
        store = NU.blank_store("sample-glen")
        store["source"] = "MLSListings, checked Apr 13, 2026"
        F.save_json(os.path.join(self.folder, "nearby.json"), store)
        quiet(NU.main, ["plan", "--folder", self.folder, "--asked", "--report-date", W.REPORT_DATE])
        res = os.path.join(self.folder, "work", "redfin.json")
        F.save_json(res, {"ok": True, "site": "redfin", "mode": "candidates", "as_of": AS_OF,
                          "homes": [{"id": 9001, "address": "14 Sample Fern Ln", "status": "active", "list_price": 1210000}]})
        code, out = quiet(NU.main, ["store", "--folder", self.folder, "--result", res, "--report-date", W.REPORT_DATE])
        self.assertEqual(code, 0, out)
        self.assertEqual(F.load_json(os.path.join(self.folder, "nearby.json"))["source"], NU.SOURCE)

    def test_the_cell_readers(self):
        self.assertEqual([M.money(x) for x in ("$930,000", "930000", "$1,005,000.00", "")], [930000, 930000, 1005000, None])
        self.assertEqual([M.day(x) for x in ("10/12/2026", "1/5/26", "2026-10-12")], ["2026-10-12", "2026-01-05", "2026-10-12"])
        self.assertEqual([M.baths(x) for x in ("2", "2.5", "2|1", "3/0")], [2, 2.5, 2.5, 3])
        self.assertEqual([M.sqft(x) for x in ("1,150", "1150/A", "1,343 (Seller)")], [1150, 1150, 1343])
        self.assertEqual([M.status(x) for x in ("Active", "CTG", "Pending", "Sold", "Expired")], ["active", "contingent", "pending", "sold", "withdrawn"])
        self.assertEqual(M.tidy_address("77 SAMPLE RIVER DR #4"), "77 Sample River Dr #4")
        self.assertEqual(M.tidy_address("31 S  Sample Vista Ave"), "31 S Sample Vista Ave")
        for bad in ("$1.2M", "TBD"):
            with self.assertRaises(M.Unreadable):
                M.money(bad)
        with self.assertRaises(M.Unreadable):
            M.day("13/45/2026")
        self.assertEqual([M.day(x) for x in ("4/7/2026 2:15 PM", "4/7/2026 14:15", "4/7/26 9:05:00 am")], ["2026-04-07"] * 3)
        for bad in ("$0", "0", "$500"):                                   # never a home price: a seller must not read "sold for $0"
            with self.assertRaises(M.Unreadable):
                M.money(bad)


def LK_for(folder, rd):
    import sr_lookups as LK
    return LK.for_issue(F.load_json(os.path.join(folder, "nearby.json")), C.parse_date(rd), NU.KEY)


if __name__ == "__main__":
    unittest.main()
