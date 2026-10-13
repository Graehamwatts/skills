# -*- coding: utf-8 -*-
"""Tests of the ship gate for the summary and the details: the numbers table and the line under it, the week by
week chart, what a showing counts, and the lists of people grouped by what they did (the count in each heading
equals the number of entries beneath it; a person who did two things is shown in full once).

    python -m unittest tests.test_checks_lists      (from the seller-report folder)
"""
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from gate_harness import GateHarness, swap, para, cell, cut, chain, add_cases     # noqa: E402
from sr_checks import core, recount                                               # noqa: E402

CASES = []


def case(name, rule, edit=None, **kw):
    CASES.append(dict(kw, name=name, rule=rule, edit=edit))


case("the_line_under_the_numbers_is_wrong", "numbers.contacted", swap("We contacted 5 of 5 people.", "We contacted 4 of 5 people."), hooks=False)
case("chart_missing", "numbers.chart_weeks", cut(r'<table data-sr-table="chart".*?</table>'))
case("chart_week_missing", "numbers.chart_weeks", cut(r'<tr><th scope="row" [^>]*>2 \(Mar 16\)</th>.*?</tr>\n'))
case("chart_bar_wrong", "numbers.chart_weeks", cell(">3 (Mar 23)</th>", 0, "7"))
case("chart_bar_wrong_without_hooks", "numbers.chart_weeks", cell(">3 (Mar 23)</th>", 1, "7"), hooks=False)
case("chart_without_the_packages", "numbers.chart_series",
     chain(swap(' data-sr-col="disclosure_contacts_new"', ""), swap(">Packages</th>", ">Other</th>")))
case("an_inquiry_counted_as_a_showing", "numbers.table_scorecard", cell('data-sr-row="showings"', 2, "3"))
case("showings_wrong_in_a_sentence", "numbers.showings", para("3 showings since we listed, none this week."))
case("showings_not_defined", "numbers.showings_defined",
     swap("Showings are key-box showings plus tours agents told us about. An inquiry is never counted as a showing.", "Showings are below."))
case("a_row_of_the_numbers_table_is_missing", "numbers.table_scorecard", cut(r'<tr data-sr-row="offers">.*?</tr>\n'))
case("list_heading_count_wrong", "numbers.list_heading.showings", swap('data-sr="list:showings">2<', 'data-sr="list:showings">3<'))
case("list_heading_count_wrong_without_hooks", "numbers.list_heading.disclosure",
     swap("People on the disclosure package list (3)", "People on the disclosure package list (4)"), hooks=False)
case("list_entry_missing", "numbers.list_entries.showings", cut(r'<div data-sr-entry="line:c002".*?</div>\n'), also=("numbers",))
case("list_entry_for_someone_who_does_not_belong", "numbers.list_entries.other_inquiries",
     swap('<div data-sr-list="other_inquiries">', '<div data-sr-list="other_inquiries"><div data-sr-entry="pointer:c002" style="padding:3px 0">Ignatius D.</div>'))
case("person_shown_in_full_twice", "numbers.list_placement", swap('data-sr-entry="pointer:c001"', 'data-sr-entry="full:c001"'))
case("pointer_where_the_full_entry_belongs", "numbers.list_placement", swap('data-sr-entry="full:c001"', 'data-sr-entry="pointer:c001"'))
case("link_copy_with_a_one_line_entry", "numbers.list_everyone_in_full", swap('data-sr-entry="full:c002"', 'data-sr-entry="line:c002"'), kind="link")


class ListsAndCharts(GateHarness):
    def test_the_lists_are_counted_from_the_ledger_not_from_the_page(self):
        """The count in each heading equals the number of entries beneath it, and both equal the gate's own count."""
        for fx in ("small", "busy"):
            for kind in ("email", "link", "print"):
                rep = self.gate(fx=fx, kind=kind)
                shutil.rmtree(os.path.join(self.tmp, "root"))
                passed = [r.id for r in rep.results if r.level == core.PASS]
                for key in ("showings", "disclosure", "open_house"):
                    self.assertIn("numbers.list_heading." + key, passed, (fx, kind))
                    self.assertIn("numbers.list_entries." + key, passed, (fx, kind))
                self.assertIn("numbers.list_placement", passed, (fx, kind))
                self.assertIn("numbers.list_everyone_in_full" if kind != "email" else "numbers.list_this_week", passed, (fx, kind))
        d = self.fixtures["busy"]
        mine = recount.recount(d)
        self.assertEqual(dict((k, len(v)) for k, v in mine["lists"].items()), d["totals"]["lists"])
        self.assertEqual(mine["totals"]["lists"]["disclosure"], mine["totals"]["disclosure_contacts"])
        both = [cid for cid in mine["lists"]["showings"] if cid in mine["lists"]["disclosure"]]
        self.assertTrue(both)                                           # people who did two things
        self.assertTrue(all(mine["placed"][cid]["primary"] == "showings" for cid in both))
        self.assertEqual(mine["totals"]["showings"], mine["totals"]["keybox_showings"] + mine["totals"]["agent_reported_tours"])
        self.assertTrue(mine["totals"]["inquiries"])                    # the fixture has inquiries, and none is a showing

    def test_a_person_active_this_week_folded_into_one_line_is_a_warning(self):
        rep = self.gate(edit=swap('data-sr-entry="full:c001"', 'data-sr-entry="line:c001"'))
        self.assertClean(rep)
        self.assertIn("numbers.list_this_week", [r.id for r in rep.results if r.level == core.WARN])

    def test_the_link_copy_may_leave_an_offer_agent_unnamed_and_nobody_else(self):
        rep = self.gate(fx="busy", kind="link")
        self.assertClean(rep)
        shutil.rmtree(os.path.join(self.tmp, "root"))
        named = next(c["id"] for c in self.fixtures["busy"]["contacts"]
                     if c.get("primary_list") == "showings" and c["id"] not in [o["contact_id"] for o in self.fixtures["busy"]["offers"]])
        rep = self.gate(fx="busy", kind="link", edit=swap('data-sr-entry="full:%s"' % named, 'data-sr-entry="full:"'))
        self.assertIn("numbers.list_entries.showings", [r.id for r in rep.blocking], rep.as_text())


add_cases(ListsAndCharts, CASES)


if __name__ == "__main__":
    unittest.main()
