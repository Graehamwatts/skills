# -*- coding: utf-8 -*-
"""Tests for what a seller report page says (scripts/sr_render).

    python -m unittest discover -s tests -p "test_render*.py"       (from the seller-report folder)
    python tests\\test_render_content.py

What people are saying, the brief, the link copy, the hooks the ship gate reads, the fit ladder, and the
honest empty states. Synthetic data only: the helpers and the fixtures come from test_render.py.
"""
import copy
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_render import (C, FIT_LEVELS, HTTPS, ID, PRICE_ROWS, RenderRefused, clean, empty_listing, hooked, load,  # noqa: E402
                         render, scaled,  sr_render, text_of, with_first_contact)


class WhatPeopleAreSaying(unittest.TestCase):
    """D7: a ranked tally with counts out of the people who gave feedback. Price is always three rows."""

    def test_price_rows_always_print(self):
        cases = [load("ledger_small.json"), load("ledger_busy.json"), empty_listing(self)]
        for d in cases:
            for mode in sr_render.MODES:
                t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"])
                n = d["pricing_tally"]["people_with_feedback"]
                unit = "person" if n == 1 else "people"
                for key, label in PRICE_ROWS:
                    with self.subTest(slug=d["meta"]["slug"], mode=mode, row=key):
                        self.assertIn("%s %d of %d %s" % (label, d["pricing_tally"][key], n, unit), t)
        self.assertEqual([lab for _, lab in PRICE_ROWS],
                         ["Said the price is too high", "Said the price is fair or good", "Did not bring up price"])

    def test_zero_price_rows_at_zero(self):
        d = load("ledger_small.json")                       # nobody raised price
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        self.assertIn("Said the price is too high 0 of 2 people", t)
        self.assertIn("Did not bring up price 2 of 2 people", t)

    def test_ranked_points_with_counts_and_what_the_week_added(self):
        d = load("ledger_busy.json")
        t = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        n = d["themes_tally"]["people_with_feedback"]
        self.assertIn("WHAT PEOPLE ARE SAYING", t)
        self.assertIn("A person can be counted under more than one point.", t)
        shown = [r for r in d["themes_tally"]["rows"] if r["key"] != "still_deciding"]       # hidden in the link copy
        at = [t.index("%s %s%d of %d people" % (r["label"], ("%d new this week " % r["new_this_week"]) if r["new_this_week"] else "", r["people"], n))
              for r in shown]
        self.assertEqual(at, sorted(at))                    # in ranked order
        self.assertEqual([r["people"] for r in shown], sorted((r["people"] for r in shown), reverse=True))
        for r in d["liked_tally"]["rows"]:
            self.assertIn("%s %d of %d people" % (r["label"], r["people"], n), t)
        self.assertIn("%d of the %d people named something they liked." % (d["liked_tally"]["people"], n), t)

    def test_section_sits_after_the_conversations_and_before_the_numbers(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            t = text_of(render(load(name), identity=ID, no_hero=True)["html"])
            order = [t.index(h) for h in ("THIS WEEK IN BRIEF", "FOLLOW-UP", "THIS WEEK'S CONVERSATIONS", "WHAT PEOPLE ARE SAYING",
                                          "THE WEEK IN NUMBERS", "NEXT WEEK", "THE RECORD SINCE WE LISTED", "Every week in one table", "HOW WE COUNT")]
            self.assertEqual(order, sorted(order))

    def test_email_keeps_the_main_points_and_names_the_rest(self):
        d = load("ledger_busy.json")
        r = render(d, identity=ID, no_hero=True)
        t = text_of(r["html"])
        cap = FIT_LEVELS[r["info"]["fit_level"]]["points"]
        rows = d["themes_tally"]["rows"]
        n = d["themes_tally"]["people_with_feedback"]
        self.assertIn("%s %d of %d people" % (rows[cap - 1]["label"], rows[cap - 1]["people"], n), t.replace("1 new this week ", ""))
        self.assertIn("Also raised:", t)
        self.assertIn("(%d" % rows[-1]["people"], t.split("Also raised:")[1].split(".")[0])

    def test_bars_are_table_cells_drawn_to_scale(self):
        d = load("ledger_busy.json")
        page = render(d, identity=ID, no_hero=True)["html"]
        pt = d["pricing_tally"]
        want = max(3, int(round(100.0 * pt["not_raised"] / pt["people_with_feedback"])))
        self.assertIn('<table role="presentation" cellpadding="0" cellspacing="0" width="%d%%"><tr><td height="8" bgcolor="#C5A55A"' % want, page)
        self.assertIn('<td colspan="2" bgcolor="#F5EFDC" style="font-size:0">', page)        # the cream track

    def test_record_keeps_every_price_comment_and_the_plain_table(self):
        d = load("ledger_busy.json")
        t = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        self.assertIn("Every price comment on record", t)
        self.assertIn("The record at each list price", t)
        said = sum(1 for c in d["contacts"] if C.is_counted(c) for e in c["feedback_log"]
                   if e["counts_as_conversation"] and e["price_reaction"] in ("too_high", "fair_or_positive"))
        self.assertEqual(t.count("List price at the time:"), said)
        for p in d["price_periods"]:
            self.assertIn("At %s" % C.fmt_money(p["price"]), t)
            self.assertIn("%d of %d" % (p["price_too_high"], p["conversations_with_feedback"]), t)
        for row in ("Days on the market", "Key-box showings", "Tours reported to our team", "Open house groups", "Offers"):
            self.assertIn(row, t.split("The record at each list price")[1].split("Every price comment on record")[0])

    def test_single_price_listing_has_no_per_price_table(self):
        t = text_of(render(load("ledger_small.json"), identity=ID, mode="link", no_hero=True)["html"])
        self.assertNotIn("The record at each list price", t)


class Brief(unittest.TestCase):
    """The brief is built from counts and reads naturally when replies outnumber follow-ups."""

    def brief(self, d, **kw):
        t = text_of(render(d, identity=ID, no_hero=True, **kw)["html"])
        return t.split("THIS WEEK IN BRIEF")[1].split("FOLLOW-UP")[0]

    def test_someone_who_contacted_us_first(self):
        d = with_first_contact(self)
        cur = d["weeks"][-1]
        self.assertGreater(cur["replies_inbound"], cur["outbound_people"])          # the case the mockup read badly
        b = self.brief(d)
        self.assertIn("My team followed up with 2 people on 2 days. We heard from 3 people this week, including 2 who contacted us first:", b)
        self.assertNotRegex(b, r"followed up with \d+ (person|people) on \d+ days? and heard back from")

    def test_plain_week(self):
        d = load("ledger_small.json")
        d["contacts"] = [c for c in d["contacts"] if not C.is_counted(c) or any(C.is_followup(t) for t in c["touches"])]
        clean(self, d)                                      # nobody left who called us first
        b = self.brief(d)
        self.assertIn("My team followed up with 2 people on 2 days and heard back from 1: Odalys V. is still deciding.", b)
        self.assertIn("no offers have come in yet", b)

    def test_no_follow_up_this_week(self):
        d = load("ledger_small.json")
        ws = d["report"]["week_start"]
        for c in d["contacts"]:
            c["touches"] = [t for t in c["touches"] if t["date"] < ws]
            c["feedback_log"] = [e for e in c["feedback_log"] if e["date"] < ws]
            c["engagements"] = [e for e in c["engagements"] if (e.get("date") or "") < ws]
        d["contacts"] = [c for c in d["contacts"] if c["touches"] or c["engagements"] or c.get("represented_by")]
        for c in d["contacts"]:
            c["feedback_safe"], c["feedback_date"], c["themes"], c["liked"] = None, None, [], []
        clean(self, d)
        b = self.brief(d)
        self.assertIn("My team did not make any follow-up contacts this week.", b)
        self.assertNotIn("heard", b)

    def test_heard_back_never_exceeds_people_followed_up_in_one_clause(self):
        for d in (load("ledger_small.json"), load("ledger_busy.json"), with_first_contact(self), scaled(self, 2)):
            b = self.brief(d)
            mt = re.search(r"followed up with (\d+) (?:person|people) on \d+ days? and heard back from (\d+)", b)
            if mt:
                self.assertLessEqual(int(mt.group(2)), int(mt.group(1)))

    def test_override_replaces_the_text_in_the_email_only(self):
        d = load("ledger_small.json")
        d["report"]["brief_override"] = "A steady week. Two agents got back to us.\n\nMore below."
        clean(self, d)
        b = self.brief(d)
        self.assertIn("A steady week. Two agents got back to us.", b)
        self.assertIn("More below.", b)
        self.assertNotIn("My team followed up", b)
        self.assertIn(ID["name"].split()[0], b)                                         # still signed
        link = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        self.assertNotIn("A steady week.", link)
        self.assertIn("My team followed up", link)

    def test_greeting(self):
        d = load("ledger_small.json")
        self.assertIn("Hi Pat and Sam,", self.brief(d))                                 # from listing.seller_first_names
        self.assertIn("Dear Pat,", self.brief(d, greeting="Dear Pat,"))
        self.assertNotIn("Hi Pat", self.brief(d, no_greeting=True))
        self.assertNotIn("Hi ", self.brief(load("ledger_busy.json")))                   # no names in the ledger, no greeting
        self.assertNotIn("Hi Pat", text_of(render(d, identity=ID, mode="link", no_hero=True)["html"]))

    def test_every_number_names_its_kind(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            for mode in sr_render.MODES:
                t = text_of(render(load(name), identity=ID, mode=mode, no_hero=True)["html"]).lower()
                self.assertIsNone(re.search(r"\b\d+ showings?\b(?! list)", t.replace("key-box showing", "kb")), mode)


class LinkCopy(unittest.TestCase):
    """D2(b): no offer price, no terms, no name of an agent who wrote an offer, nobody shown as weighing one."""

    @classmethod
    def setUpClass(cls):
        cls.d = load("ledger_busy.json")
        cls.email = render(cls.d, identity=ID, no_hero=True)["html"]
        cls.pages = dict((mode, render(cls.d, identity=ID, mode=mode, no_hero=True)["html"]) for mode in ("link", "print"))

    def test_the_email_does_carry_the_offers(self):
        t = text_of(self.email)
        for o in self.d["offers"]:
            self.assertIn(C.fmt_money(o["price"]), t)
            self.assertIn(o["agent_short"], t)
        self.assertIn("STILL DECIDING", t)

    def test_a_new_offer_moves_up_and_shows_its_terms_in_the_email_only(self):
        d = load("ledger_busy.json")
        o = d["offers"][0]
        o["date"] = d["report"]["week_end"]
        o["terms_summary"] = "Cash, 14 day close, no contingencies."
        o["pct_of_list"] = round(100.0 * o["price"] / C.price_on(d["listing"]["price_history"], o["date"]), 1)
        clean(self, d)
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        self.assertIn("1 offer this week", t)
        self.assertIn("Cash, 14 day close, no contingencies.", t)
        self.assertLess(t.index("OFFER WATCH"), t.index("FOLLOW-UP"))               # right under the brief
        link = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        self.assertNotIn("Cash, 14 day close", link)
        self.assertNotIn(C.fmt_money(o["price"]), link)
        self.assertNotIn(o["agent_short"], link)

    def test_no_offer_price_terms_or_agent(self):
        list_prices = set(C.fmt_money(e["price"]) for e in self.d["listing"]["price_history"])
        for mode, page in self.pages.items():
            t = text_of(page)
            for o in self.d["offers"]:
                with self.subTest(mode=mode, offer=o["id"]):
                    if C.fmt_money(o["price"]) not in list_prices:
                        self.assertNotIn(C.fmt_money(o["price"]), t)
                    self.assertNotIn(o["agent_short"], t)
                    self.assertNotIn(o["terms_summary"], t)
                    self.assertNotIn("%g%%" % o["pct_of_list"], t)
            self.assertIn("%d offers on file" % len(self.d["offers"]), t)              # the count alone is not private

    def test_nobody_is_shown_as_weighing_an_offer(self):
        for mode, page in self.pages.items():
            t = text_of(page)
            self.assertNotIn("STILL DECIDING", t)
            self.assertNotIn("Still deciding", t)                                       # the theme row is hidden too
            for w in self.d["offer_watch"]:
                self.assertNotIn(w["basis_safe"], t)
            self.assertNotIn("Earlier interest we are going back to", t)
            self.assertIn("Offer news is shared by email only", t)

    def test_offer_notes_logged_after_the_week_are_left_out(self):
        d = load("ledger_busy.json")
        d["report"]["since_week_closed"]["items"].append(
            {"date": d["report"]["since_week_closed"]["through"], "kind": "note", "contact_id": None, "name_short": None,
             "summary_safe": "A second buyer asked how to submit their paperwork.", "offer_related": True})
        clean(self, d)
        self.assertIn("A second buyer asked how to submit their paperwork.", text_of(render(d, identity=ID, no_hero=True)["html"]))
        self.assertNotIn("A second buyer asked", text_of(render(d, identity=ID, mode="link", no_hero=True)["html"]))

    def test_the_complete_record_names_everyone_else(self):
        t = text_of(self.pages["link"])
        self.assertIn("Everyone else, with every day we tried", t)
        masked = set(o["contact_id"] for o in self.d["offers"])
        for c in self.d["contacts"]:
            if C.is_counted(c) and c["id"] not in masked and c.get("name_recorded", True):
                self.assertIn(c["name_short"], t)

    def test_print_layout(self):
        self.assertIn("zoom:.9", self.pages["print"])
        self.assertIn("max-width:780px", self.pages["print"])
        self.assertIn('class="k"', self.pages["print"])
        self.assertNotIn("zoom:.9", self.pages["link"])
        self.assertIn("listed in short form", text_of(self.pages["print"]))


class GateHooks(unittest.TestCase):
    """The page marks its numbers, sections, people and tables so check_report.py can count them again."""

    def test_stamp_says_what_the_file_is(self):
        d = load("ledger_busy.json")
        for mode in sr_render.MODES:
            page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
            for name, want in (("kind", mode), ("slug", "sample-orchard"), ("issue", "11"), ("week", "2026-03-16/2026-03-22")):
                self.assertIn('<meta name="sr:%s" content="%s">' % (name, want), page)
            self.assertNotIn('name="sr:build"', page, "there is one build mode, so the page does not name one")

    def test_hooked_numbers_are_the_ledger_numbers(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            T, PT, cur = d["totals"], d["pricing_tally"], d["weeks"][-1]
            for mode in sr_render.MODES:
                page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
                want = {"answered": T["replied"], "waiting": T["awaiting_reply"], "followups": T["touches_outbound"],
                        "followup_days": T["outbound_distinct_days"], "replies": T["replies_inbound"],
                        "week_followups": cur["touches_outbound"], "week_followup_people": cur["outbound_people"],
                        "week_followup_days": cur["outbound_distinct_days"], "price_too_high": PT["too_high"],
                        "price_fair": PT["fair_or_positive"], "price_not_raised": PT["not_raised"]}
                if not T["contacted_through_host"]:
                    want.update(contacted=T["contacted"], contacts=T["contacts"])
                if T["awaiting_reply_3plus_attempts"]:
                    want["waiting_3plus"] = T["awaiting_reply_3plus_attempts"]
                for hook, n in want.items():
                    with self.subTest(ledger=name, mode=mode, hook=hook):
                        self.assertEqual(hooked(page, hook), [C.fmt_num(n)])
                hidden = set(["still_deciding"]) if mode != "email" else set()
                for r in d["themes_tally"]["rows"]:
                    key = "theme:%s" % r["key"] if r["key"] != "other" else "theme:other:%s" % r["label"].lower()
                    self.assertEqual(hooked(page, key), [] if r["key"] in hidden else [str(r["people"])], key)
                for r in d["liked_tally"]["rows"]:
                    self.assertEqual(hooked(page, "liked:" + r["key"]), [str(r["people"])])

    def test_through_the_host_is_said_in_full(self):
        d = load("ledger_small.json")                           # one visitor reached only through the host
        self.assertEqual(d["totals"]["contacted_through_host"], 1)
        page = render(d, identity=ID, no_hero=True)["html"]
        self.assertIn("Contacted 4 of 5 directly and 1 through the open house host.", text_of(page))
        self.assertEqual(hooked(page, "contacted"), [])         # the tile shows 4, so it is not marked as the total

    def test_sections_are_named(self):
        page = render(load("ledger_busy.json"), identity=ID, no_hero=True)["html"]
        for name in ("masthead", "brief", "since_week_closed", "followup", "conversations", "waiting", "saying", "offers",
                     "numbers", "open_houses", "next_week", "weekly_chart", "weekly_table", "price_periods", "price_comments", "adds_up",
                     "how_we_count", "footer"):
            self.assertIn('data-sr-section="%s"' % name, page)
        self.assertNotIn('data-sr-section="draft_notice"', page)
        self.assertNotIn('data-sr-section="reviewer_panel"', page)
        for bad in ("recommendation", "decision_log", "seller_ask", "from_you"):
            self.assertNotIn('data-sr-section="%s"' % bad, page)
        over = load("ledger_small.json")
        over["report"]["brief_override"] = "A steady week."
        self.assertIn('data-sr-section="brief_override"', render(clean(self, over), identity=ID, no_hero=True)["html"])

    def test_tables_are_named_and_every_week_keeps_its_row(self):
        d = load("ledger_busy.json")
        r = render(d, identity=ID, no_hero=True)
        self.assertGreaterEqual(r["info"]["fit_level"], 2)       # the chart is folding older weeks at this level
        page = r["html"]
        for name in ("scorecard", "weeks", "periods"):
            self.assertEqual(page.count('data-sr-table="%s"' % name), 1)
        self.assertIn('data-sr-col="PRICE_PAIR"', page)
        table = page.split('data-sr-table="weeks"')[1].split("</table>")[0]
        for w in d["weeks"]:
            self.assertIn("<b>%d</b><br>" % w["n"], table)
        self.assertNotIn("data-sr-row", table)
        for p in d["price_periods"]:
            self.assertIn('data-sr-col="%d"' % p["price"], page)

    def test_a_very_long_listing_marks_the_blocks_it_folds(self):
        from sr_render import assemble, tokens
        from sr_render.model import Model
        d = load("ledger_busy.json")
        render(d, identity=ID, no_hero=True)                    # sets the per-build switches
        m = Model(d, ID, False)
        page = assemble.build(m, len(FIT_LEVELS) - 1)
        self.assertIn('data-sr-row="block:1-3"', page)
        self.assertLessEqual(FIT_LEVELS[-1]["table_weeks"], 8)
        self.assertTrue(all(lv["table_weeks"] is None for lv in FIT_LEVELS[:7]))
        self.assertEqual(tokens.OPT["fit"], FIT_LEVELS[-1])

    def test_people_are_marked_but_never_an_offer_agent_in_the_link_copy(self):
        d = load("ledger_busy.json")
        offer = set(o["contact_id"] for o in d["offers"])
        email = render(d, identity=ID, no_hero=True)["html"]
        link = render(d, identity=ID, mode="link", no_hero=True)["html"]
        ids = lambda page: set(re.findall(r'data-sr-person="(c\d+)"', page))
        counted = set(c["id"] for c in d["contacts"] if C.is_counted(c))
        self.assertTrue(ids(email) and ids(email) <= counted)
        self.assertEqual(ids(link) & offer, set())
        self.assertGreater(len(ids(link)), len(ids(email)))


class FitLadder(unittest.TestCase):
    def test_small_listing_shows_everyone(self):
        d = load("ledger_small.json")
        r = render(d, identity=ID, no_hero=True)
        self.assertEqual(r["info"]["fit_level"], 0)
        self.assertEqual(r["info"]["people_with_follow_up_shown"], d["totals"]["contacted"])
        self.assertIn("Everyone we have been in touch with is shown above", text_of(r["html"]))

    def test_busy_listing_steps_down_and_stays_under_the_ceiling(self):
        r = render(load("ledger_busy.json"), identity=ID, no_hero=True)
        self.assertGreater(r["info"]["fit_level"], 0)
        self.assertLessEqual(r["info"]["bytes"], 95000)
        t = text_of(r["html"])
        self.assertIn("Everyone else, in the complete record", t)                      # and the footing still adds up
        self.assertIn("Total since we listed %d %d" % (r["info"]["follow_ups"], r["info"]["replies"]), t)

    def test_the_fit_level_does_not_depend_on_photo_or_link(self):
        d = load("ledger_busy.json")
        a = render(d, identity=ID, no_hero=True, no_link=True)
        b = render(d, identity=ID, **HTTPS)
        self.assertLessEqual(abs(a["info"]["fit_level"] - b["info"]["fit_level"]), 1)
        self.assertLessEqual(b["info"]["bytes"], 95000)

    def test_much_bigger_listings_still_fit(self):
        for times in (2, 4):
            d = scaled(self, times)
            r = render(d, identity=ID, no_hero=True)
            with self.subTest(times=times, contacts=d["totals"]["contacts"], fit=r["info"]["fit_level"]):
                self.assertLessEqual(r["info"]["bytes"], 95000)
                self.assertLess(r["info"]["fit_level"], len(FIT_LEVELS))
            self.assertGreater(len(render(d, identity=ID, mode="link", no_hero=True)["html"]), 95000)   # the link copy is never trimmed

    def test_a_ceiling_nothing_can_meet_is_refused(self):
        with self.assertRaises(RenderRefused) as cm:
            render(load("ledger_busy.json"), identity=ID, no_hero=True, max_bytes=30000)
        self.assertEqual(cm.exception.stage, "size")


class ZeroAndThin(unittest.TestCase):
    def test_a_listing_nobody_has_reacted_to(self):
        d = empty_listing(self)
        self.assertEqual(len(d["weeks"]), 1)
        for mode in sr_render.MODES:
            t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"])
            with self.subTest(mode=mode):
                self.assertIn("Nobody is on the log to follow up with yet.", t)
                self.assertIn("Nobody has toured, asked about the home or asked for the disclosure package yet", t)
                self.assertIn("Nobody has given us feedback yet", t)
                self.assertIn("Said the price is too high 0 of 0 people", t)
                self.assertIn("No open house has been held yet", t)
                self.assertIn("No offers have come in since we listed.", t) if mode == "email" else None
                self.assertIn("No tours have been logged yet.", t)
                self.assertIn("Week 1 was a partial week", t)
                self.assertNotIn("None of", t)
                self.assertNotIn("nan", t.lower().split())

    def test_not_recorded_is_never_printed_as_zero(self):
        d = load("ledger_busy.json")                                # sends and opens of the package are not tracked
        self.assertIsNone(d["totals"]["disclosure_link_sent"])
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        self.assertNotIn("Disclosure packages sent", t)
        self.assertIn("Sends and opens are not recorded.", t)
        d["report"]["tracking"]["keybox_showings"] = False
        for c in d["contacts"]:
            for e in c["engagements"]:
                if e["type"] == "keybox_showing":
                    e["type"] = "agent_reported_tour"
        clean(self, d)
        self.assertIsNone(d["totals"]["keybox_showings"])
        t = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        self.assertIn("Key-box showings are not recorded for this listing.", t)
        self.assertNotIn("Key box", t.split("Every week in one table")[1].split("Tours:")[0])
        self.assertIn("Pkgs", t.split("Every week in one table")[1])

    def test_open_house_counts_keep_three_states_apart(self):
        d = load("ledger_small.json")
        t = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        self.assertIn("No visitors", t)             # held, nobody came
        self.assertIn("No count kept", t)           # held, nobody wrote a number down
        self.assertIn("none", t.split("Every week in one table")[1])           # no session that week

    def test_mixed_open_house_units_are_not_added_as_people(self):
        d = load("ledger_small.json")
        d["open_houses"][0]["counted_unit"] = "visitors"
        clean(self, d)
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        self.assertIn("some hosts counted groups and some visitors", t)
        self.assertIn("Open house traffic", t)
        self.assertNotIn("Open house groups", t)

    def test_no_next_week_items(self):
        d = load("ledger_small.json")
        d["next_week"] = []
        clean(self, d)
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        self.assertIn("Your next report arrives Monday, Apr 20.", t)
        self.assertNotIn("What we are doing next week", t)


if __name__ == "__main__":
    unittest.main()
