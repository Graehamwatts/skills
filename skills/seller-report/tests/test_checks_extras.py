# -*- coding: utf-8 -*-
"""Tests of the ship gate for the optional sections: similar homes nearby (its numbers are counted again, and
its public addresses stay in that one section), online ads and marketing (the status words, the scheduled end,
no ad spend), and online views (the count since listing and the day it was read).

    python -m unittest tests.test_checks_extras      (from the seller-report folder)

One rule is broken at a time on a clean page (sr_checks.sample_page, which is not the renderer). Synthetic data only.
"""
import json
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from gate_harness import GateHarness, swap, para, cell, cut, chain, add_cases, top, UNDER     # noqa: E402
import sr_contract as C                                                                 # noqa: E402
import nearby_update as NB                                                              # noqa: E402

CASES = []


def case(name, rule, edit=None, **kw):
    CASES.append(dict(kw, name=name, rule=rule, edit=edit))


def led_nearby(d, t):
    """The watch list of the fixture store, as the builder would put it in the ledger: four changes and one home unchanged."""
    with open(os.path.join(HERE, "fixtures", "nearby.json"), encoding="utf-8") as f:
        store = json.load(f)
    d["nearby"], _ = NB.ledger_block(store, d["listing"], d["report"])


def led_same_building(d, t):
    led_nearby(d, t)
    d["nearby"]["homes"][4]["address"] = "218 Sample Glen Ct #12"        # a unit at this listing's own street address


def led_online_running(d, t):
    """One portal, read once: the running count since listing, and no weekly figure yet."""
    d["online"] = {"as_of": d["report"]["report_date"], "portals": ["Zillow"], "weeks": [], "since_listing": {"views": {"Zillow": 812}, "saves": {"Zillow": 31}}}
    C.finish_ledger(d)


def led_ends(d, t):
    d["marketing"]["channels"][2]["ends_on"] = "2026-04-20"


def led_stale_marketing(d, t):
    for ch in d["marketing"]["channels"]:
        ch.update(status="prepared", checked="2026-03-20")


ROW = ">31 Sample Alder Way</th>"
case("nearby_count_wrong", "numbers.nearby_counts", swap('data-sr="nearby_changed">4<', 'data-sr="nearby_changed">3<'), led=led_nearby)
case("nearby_count_wrong_in_the_sentence", "numbers.nearby_counts",
     swap('<span data-sr="nearby_changed">4</span> of the <span data-sr="nearby_homes">5</span> homes', "2 of the 5 homes"), led=led_nearby)
case("nearby_home_missing_from_the_table", "numbers.nearby_table", cut(r'<tr data-sr-row="4"><th scope="row" [^>]*>7 Sample Elm Pl</th>.*?</tr>\n?'), led=led_nearby)
case("nearby_status_wrong", "numbers.nearby_table", cell(ROW, 0, "Sold"), led=led_nearby)
case("nearby_price_wrong", "numbers.nearby_table", cell(ROW, 1, "$1,160,000"), led=led_nearby)
case("nearby_price_wrong_in_a_table_found_by_its_headings", "numbers.nearby_table",
     chain(swap(' data-sr-table="nearby"', ""), swap(' data-sr-col="price"', ""), cell(ROW, 1, "$1,160,000")), led=led_nearby)
case("nearby_days_wrong", "numbers.nearby_table", cell(ROW, 2, "99"), led=led_nearby)
case("nearby_change_date_wrong", "numbers.nearby_changes", swap("Price changed on Apr 8", "Price changed on Apr 9"), led=led_nearby)
case("nearby_change_price_wrong", "numbers.nearby_changes", swap("$1,199,000 to $1,150,000", "$1,250,000 to $1,150,000"), led=led_nearby)
case("nearby_change_called_something_else", "numbers.nearby_changes", swap("52 Sample Birch Dr: Sold on", "52 Sample Birch Dr: Went pending on"), led=led_nearby)
case("nearby_change_not_printed", "numbers.nearby_changes", cut(r'<p data-sr-row="change:2"[^>]*>.*?</p>\n?'), led=led_nearby)
case("nearby_checked_on_another_day", "numbers.nearby_checked", swap("Checked Apr 13.", "Checked Apr 12."), led=led_nearby)
NO_TABLE = cut(r'<table data-sr-table="nearby".*?</table>')
case("nearby_unchanged_homes_miscounted_in_the_short_form", "numbers.nearby_table",
     chain(NO_TABLE, swap("Checked Apr 13.</p>", "Checked Apr 13.</p><p>The other 2 homes did not change: 2 pending.</p>")), led=led_nearby)
case("nearby_table_missing_from_the_link_copy", "numbers.nearby_table",
     chain(NO_TABLE, swap("Checked Apr 13.</p>", "Checked Apr 13.</p><p>The other 1 home did not change: 1 active.</p>")), led=led_nearby, kind="link")
case("channel_folded_under_the_wrong_word", "numbers.marketing_words",
     swap("The video is uploaded. Nothing has launched.</p>", "The video is uploaded. Nothing has launched.</p><p>Not launched: Facebook and Instagram ads.</p>"))
case("nearby_section_with_no_watch_list", "numbers.nearby_absent",
     swap(UNDER, UNDER + '<div data-sr-section="nearby"><p style="margin:4px 0">Similar homes nearby: nothing changed this week.</p></div>'))
case("nearby_unit_in_the_same_building_outside_its_section", "privacy.address_pattern",
     para("Her clients said they prefer 218 Sample Glen Ct #12."), led=led_same_building)
case("ad_spend_printed", "numbers.marketing_no_spend", swap("Two ads were running at the last check.", "Two ads were running at the last check. Spend so far is $45."))
case("ad_spend_printed_in_words", "numbers.marketing_no_spend", swap("Two ads were running at the last check.", "Two ads ran. 45 dollars spent."))
case("channel_given_the_wrong_status_word", "numbers.marketing_words", swap("YouTube ads PREPARED", "YouTube ads RUNNING"))
case("switched_on_channel_without_its_last_check", "numbers.marketing_words",
     swap("Facebook and Instagram ads SWITCHED ON Last checked Apr 2.", "Facebook and Instagram ads SWITCHED ON"))
case("scheduled_end_on_another_day", "numbers.marketing_words", swap("Scheduled to end Apr 20.", "Scheduled to end Apr 27."), led=led_ends)
case("scheduled_end_that_nobody_recorded", "numbers.marketing_words",
     swap("Facebook and Instagram ads SWITCHED ON Last checked Apr 2.", "Facebook and Instagram ads SWITCHED ON Last checked Apr 2. Scheduled to end Apr 20."))
case("ads_section_when_nothing_was_on_or_recorded", "numbers.marketing_recorded",
     swap(UNDER, UNDER + '<div data-sr-section="marketing"><p style="margin:4px 0">YouTube ads PREPARED</p></div>'), led=led_stale_marketing)
case("online_views_since_listing_wrong", "numbers.table_scorecard", cell('data-sr-row="online_views"', 2, "999"), led=led_online_running)
case("online_views_since_listing_wrong_in_the_weekly_table", "numbers.table_weeks", cell('data-sr-row="all"', 11, "999"), led=led_online_running)
case("online_views_read_on_another_day", "numbers.online_as_of", top("Online views are the running count Zillow showed on Apr 12."), led=led_online_running)


class OptionalSections(GateHarness):
    def test_the_clean_page_passes_these_rules_for_real(self):
        def led(d, t):
            led_nearby(d, t)
            led_online_running(d, t)
            led_ends(d, t)
        rep = self.gate(led=led, edit=top("Online views are the running count Zillow showed on Apr 13."))
        self.assertTrue(rep.ok, rep.as_text())
        passed = set(r.id for r in rep.results if r.level == "pass")
        for rule in ("numbers.nearby_counts", "numbers.nearby_table", "numbers.nearby_changes", "numbers.nearby_checked", "numbers.marketing_recorded",
                     "numbers.marketing_no_spend", "numbers.marketing_words", "numbers.online_as_of", "numbers.table_scorecard", "privacy.address_pattern"):
            self.assertIn(rule, passed, rep.as_text())
        table = next(r for r in rep.results if r.id == "numbers.nearby_table")
        self.assertIn("5 rows, 15 cells", table.message)

    def test_a_page_may_leave_the_optional_sections_out(self):
        no_sections = chain(cut(r'<tr><td data-sr-section="nearby".*?</table></td></tr>'), cut(r'<tr><td data-sr-section="marketing".*?</td></tr>'))
        rep = self.gate(led=led_nearby, edit=no_sections)
        self.assertTrue(rep.ok, rep.as_text())
        self.assertFalse([r.id for r in rep.results if "nearby_" in r.id or "marketing_words" in r.id])

    def test_a_long_email_may_say_the_unchanged_homes_in_one_sentence(self):
        short = chain(NO_TABLE, swap("Checked Apr 13.</p>", "Checked Apr 13.</p><p>The other 1 home did not change: 1 active.</p>"))
        rep = self.gate(led=led_nearby, edit=short)
        self.assertTrue(rep.ok, rep.as_text())
        said = next(r for r in rep.results if r.id == "numbers.nearby_table")
        self.assertIn("the 1 homes that did not change are counted by status", said.message)

    def test_an_ad_channel_named_after_a_product_is_not_read_as_a_tool_name(self):
        def led(d, t):
            d["marketing"]["channels"].append({"channel": "ChatGPT ads", "status": "not_launched", "checked": "2026-04-13", "detail": "Not part of this launch."})
        rep = self.gate(led=led)
        self.assertTrue(rep.ok, rep.as_text())
        self.assertIn("ChatGPT ads NOT LAUNCHED", rep.ctx.seller_flat())
        shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(led=led, edit=para("This summary was checked with ChatGPT."))
        self.assertIn("hygiene.internal_notes", [r.id for r in rep.blocking])

    def test_spend_is_the_only_one_of_these_the_operator_may_waive(self):
        edit = swap("Two ads were running at the last check.", "Two ads were running at the last check. Spend so far is $45.")
        rep = self.gate(edit=edit, args=["--waive", "numbers.marketing_no_spend=Graeham asked to show the ad cost this week"])
        self.assertTrue(rep.ok, rep.as_text())
        shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(led=led_nearby, edit=swap("Checked Apr 13.", "Checked Apr 12."), args=["--waive", "numbers.nearby_checked=close enough"])
        self.assertFalse(rep.ok)


add_cases(OptionalSections, CASES)

if __name__ == "__main__":
    unittest.main()
