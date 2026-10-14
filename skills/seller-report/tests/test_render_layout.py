# -*- coding: utf-8 -*-
"""Tests for the layout of a seller report page (scripts/sr_render): the summary on top, the details below.

    python -m unittest tests.test_render_layout          (from the seller-report folder)

AT A GLANCE   masthead, this week in brief, one numbers table with one line under it, the week by week charts,
              what people are saying
THE DETAILS   offers and likely offers, then people grouped by what they did. The count in each heading equals
              the number of entries beneath it. This week's people are in full, earlier people one line each,
              and a person on two lists is in full once and a pointer in the other. The link copy and the PDF
              show everyone in full.
THE RECORD    carried forward in every issue

Also the two optional slots a later step fills: online views and similar homes nearby. Synthetic data only.
"""
import copy
import os
import re
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_render import C, FIT_LEVELS, HTTPS, ID, clean, empty_listing, hooked, load, render, sr_render, text_of   # noqa: E402
from sr_checks import page as gate_page                                                                          # noqa: E402
from sr_render import assemble                                                                                   # noqa: E402
from gate_harness import GateHarness                                                                             # noqa: E402

TOP = ("THIS WEEK IN BRIEF", "THE NUMBERS", "week by week", "WHAT PEOPLE ARE SAYING")
DETAILS = ("THE DETAILS", "OFFERS AND LIKELY OFFERS", "SHOWINGS", "DISCLOSURE PACKAGES", "OPEN HOUSES", "OTHER INQUIRIES", "NEXT WEEK")
RECORD = ("THE RECORD SINCE WE LISTED", "Follow-up since we listed", "Every week in one table", "HOW WE COUNT")


def table_of(page, name):
    """The markup of one named table, bars and all, up to the end of the section it sits in."""
    return page.split('data-sr-table="%s"' % name)[1].split("data-sr-section=")[0]


def chart_rows(page, name="chart"):
    """{week number: the markup of that week's row} of a week by week chart."""
    out = {}
    for chunk in table_of(page, name).split('<tr data-sr-row="')[1:]:
        n, _, body = chunk.partition('">')
        out[int(n)] = body
    return out


def entries(html):
    """{list key: [(form, contact id)]} as the page prints them, read with the ship gate's own page reader."""
    return dict((k, [(form, cid) for form, cid, _ in v]) for k, v in gate_page.Page(html).entries().items())


def with_showings_this_week(case):
    """The small fixture plus a key-box showing and a tour an agent reported, both in the report week."""
    d = load("ledger_small.json")
    for cid, name, kind, day in (("c091", "Perpetua L.", "keybox_showing", "2026-04-08"), ("c092", "Evander S.", "agent_reported_tour", "2026-04-10")):
        c = C.blank_contact(cid, name, brokerage="Harborlight Realty")
        c["engagements"] = [{"type": kind, "date": day, "date_quality": "exact", "confirmed": True}]
        d["contacts"].append(c)
    return clean(case, d)


def with_online(case):
    """The small fixture with weekly views and saves from two portals, for the last three weeks."""
    d = load("ledger_small.json")
    d["online"] = {"as_of": "2026-04-13", "portals": ["Zillow", "Redfin"], "weeks": [
        {"n": 3, "views": {"Zillow": 240, "Redfin": 80}, "saves": {"Zillow": 9}},
        {"n": 4, "views": {"Zillow": 210, "Redfin": 65}, "saves": {"Zillow": 6, "Redfin": 2}},
        {"n": 5, "views": {"Zillow": 180, "Redfin": 50}, "saves": {"Zillow": 4, "Redfin": 1}}]}
    return clean(case, d)


def with_nearby(case):
    """The small fixture with a watch list of five similar homes: one of each kind of change, and one unchanged."""
    d = load("ledger_small.json")
    d["nearby"] = {"as_of": "2026-04-13", "checked_for_this_issue": True, "source": "Public listing pages",
                   "scope": "Five 3 bedroom homes within half a mile, chosen on Mar 16", "homes": [
                       {"address": "14 Sample Fern Ln", "beds": 3, "baths": 2, "sqft": 1510, "status": "active", "list_price": 1210000,
                        "days_on_market": 3, "change": "new_listing", "change_date": "2026-04-10"},
                       {"address": "31 Sample Alder Way", "beds": 3, "baths": 2, "sqft": 1440, "status": "active", "list_price": 1150000,
                        "price_before": 1199000, "days_on_market": 40, "change": "price_change", "change_date": "2026-04-08"},
                       {"address": "9 Sample Cedar Ct", "beds": 3, "baths": 2.5, "sqft": 1620, "status": "pending", "list_price": 1249000,
                        "days_on_market": 12, "change": "went_pending", "change_date": "2026-04-09"},
                       {"address": "52 Sample Birch Dr", "beds": 3, "baths": 2, "sqft": 1390, "status": "sold", "list_price": 1175000,
                        "sold_price": 1182000, "days_on_market": 9, "change": "sold", "change_date": "2026-04-07"},
                       {"address": "7 Sample Elm Pl", "beds": 3, "baths": 2, "sqft": 1475, "status": "active", "list_price": 1225000,
                        "days_on_market": 61, "change": "none", "change_date": None}]}
    return clean(case, d)


class Order(unittest.TestCase):
    """B1: the summary on top, a clear divider, the details, then the record."""

    def test_sections_are_in_the_order_the_seller_chose(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            for mode in sr_render.MODES:
                page = render(load(name), identity=ID, mode=mode, no_hero=True)["html"]
                seen = []
                for s in re.findall(r'data-sr-section="([a-z_]+)"', page):
                    if s not in seen and s in assemble.ORDER:
                        seen.append(s)
                with self.subTest(ledger=name, mode=mode):
                    self.assertEqual(seen, [s for s in assemble.ORDER if s in seen])
                    for must in ("masthead", "brief", "numbers", "weekly_chart", "saying", "details", "offers", "list_showings",
                                 "list_disclosure", "open_houses", "next_week", "record", "weekly_table", "how_we_count", "footer"):
                        self.assertIn(must, seen)
                    t = text_of(page)
                    at = [t.index(h) for h in TOP + DETAILS + RECORD]
                    self.assertEqual(at, sorted(at))

    def test_optional_sections_take_their_place_between_the_lists_and_next_week(self):
        d = with_nearby(self)                                   # the small fixture also carries market and marketing
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        at = [t.index(h) for h in ("OTHER INQUIRIES", "SIMILAR HOMES NEARBY", "TIME ON THE MARKET", "ONLINE ADS AND MARKETING", "NEXT WEEK")]
        self.assertEqual(at, sorted(at))

    def test_the_black_band_divides_the_summary_from_the_details(self):
        page = render(load("ledger_busy.json"), identity=ID, no_hero=True)["html"]
        band = page.split('data-sr-section="details"')[1].split("</td></tr></table></td></tr>")[0]
        self.assertIn('bgcolor="#1A1A1A"', page.split('data-sr-section="details"')[1][:60])
        self.assertIn("THE DETAILS", band)
        self.assertIn("Everyone active this week is shown in full. Earlier people have one line each.", text_of(band))
        link = text_of(render(load("ledger_busy.json"), identity=ID, mode="link", no_hero=True)["html"])
        self.assertIn("Everyone is shown in full, with every date we followed up.", link)

    def test_there_is_no_separate_still_waiting_section(self):
        for mode in sr_render.MODES:
            t = text_of(render(load("ledger_busy.json"), identity=ID, mode=mode, no_hero=True)["html"])
            for gone in ("Still waiting to hear back", "THIS WEEK'S CONVERSATIONS", "FOLLOW-UP ", "OFFER WATCH", "THE WEEK IN NUMBERS",
                         "How the follow-up adds up", "Everyone else, with every day we tried", "MARKET CHECK"):
                self.assertNotIn(gone, t)
            self.assertIn("STILL WAITING", t)                   # waiting is a status on the entry


class TheNumbers(unittest.TestCase):
    """One table, three columns, the same rows in every issue, and one line under it."""

    ROWS = ("showings", "disclosure_contacts_new", "open_house_groups", "touches_outbound", "replies_inbound", "offers")

    def rows(self, page):
        table = page.split('data-sr-table="scorecard"')[1].split("</table>")[0]
        out = {}
        for key, body in re.findall(r'<tr data-sr-row="([a-z_]+)">(.*?)</tr>', table, flags=re.S):
            out[key] = [text_of(c) .strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", body, flags=re.S)]
        return out

    def test_every_row_prints_in_every_issue_zero_or_not(self):
        for d in (load("ledger_small.json"), load("ledger_busy.json"), empty_listing(self)):
            for mode in sr_render.MODES:
                page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
                rows = self.rows(page)
                with self.subTest(slug=d["meta"]["slug"], weeks=len(d["weeks"]), mode=mode):
                    self.assertEqual(tuple(rows), self.ROWS)
                    cur, T = d["weeks"][-1], d["totals"]
                    self.assertEqual(rows["showings"][0], "Showings")
                    self.assertEqual(rows["showings"][1], str(cur["showings"]))
                    self.assertEqual(rows["showings"][3], str(T["showings"]))
                    self.assertTrue(rows["disclosure_contacts_new"][0].startswith("Disclosure packages"))
                    self.assertTrue(rows["open_house_groups"][0].startswith("Open house "))
                    self.assertTrue(rows["touches_outbound"][0].startswith("Follow-ups we made"))
                    self.assertEqual(rows["touches_outbound"][3], C.fmt_num(T["touches_outbound"]))
                    self.assertEqual(rows["replies_inbound"], ["Replies we received", str(cur["replies_inbound"]),
                                                               str(d["weeks"][-2]["replies_inbound"]) if len(d["weeks"]) > 1 else "",
                                                               str(T["replies_inbound"])])
                    self.assertEqual(rows["offers"][0::3], ["Offers", str(T["offers"])])
                    heads = text_of(page.split('data-sr-table="scorecard"')[1].split("</tr>")[0])
                    self.assertIn("This week Last week Since we listed", heads)

    def test_showings_are_key_box_showings_plus_reported_tours_and_never_an_inquiry(self):
        d = with_showings_this_week(self)
        cur, T = d["weeks"][-1], d["totals"]
        self.assertEqual((cur["keybox_showings"], cur["agent_reported_tours"], cur["inquiries"], cur["showings"]), (1, 1, 1, 2))
        self.assertEqual(T["showings"], T["keybox_showings"] + T["agent_reported_tours"])
        page = render(d, identity=ID, no_hero=True)["html"]
        t = text_of(page)
        self.assertEqual(self.rows(page)["showings"][1::2], ["2", str(T["showings"])])
        self.assertIn("This week: 2 showings, 1 inquiry", t)                           # the brief counts them the same way
        self.assertIn("Showings count key-box showings (%d since we listed) and tours agents told us about (%d)."
                      % (T["keybox_showings"], T["agent_reported_tours"]), t)
        self.assertIn("A question or a cancelled request is an inquiry, not a showing.", t)
        self.assertIn("Perpetua L. and Evander S.", self.rows(page)["showings"][0])     # the names behind a small count

    def test_the_second_figure_for_packages_opened_only_when_it_is_recorded(self):
        d = load("ledger_small.json")                           # opens are tracked
        page = render(d, identity=ID, no_hero=True)["html"]
        row = self.rows(page)["disclosure_contacts_new"]
        self.assertIn("new people sent the package", row[0])
        self.assertEqual(row[3], "%d %d opened" % (d["totals"]["disclosure_contacts"], d["totals"]["disclosure_opened_confirmed"]))
        self.assertEqual(hooked(page, "total:disclosure_opened_confirmed"), ["%d opened" % d["totals"]["disclosure_opened_confirmed"]])
        busy = self.rows(render(load("ledger_busy.json"), identity=ID, no_hero=True)["html"])["disclosure_contacts_new"]
        self.assertIn("new people on the package list", busy[0])
        self.assertNotIn("opened", " ".join(busy))

    def test_one_line_directly_under_the_table(self):
        for name in ("ledger_busy.json",):
            d = load(name)
            T = d["totals"]
            for mode in sr_render.MODES:
                page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
                after = page.split('data-sr-table="scorecard"')[1].split("</table>", 1)[1]
                line = text_of(after.split('data-sr-section="contact_line"')[1].split("</td></tr></table>")[0])
                self.assertIn("We contacted %d of %d people. %d answered. %d still waiting."
                              % (T["contacted"], T["contacts"], T["replied"], T["awaiting_reply"]), line)
                self.assertIn("%d people have not been reached yet." % T["not_yet_contacted"], line)
                self.assertLess(after.index('data-sr-section="contact_line"'), after.index('data-sr-table="chart"'))
                self.assertLess(len(after.split('data-sr-section="contact_line"')[0]), 400)     # nothing sits between the table and the line

    def test_an_empty_listing_says_so_in_the_line(self):
        t = text_of(render(empty_listing(self), identity=ID, no_hero=True)["html"])
        self.assertIn("Nobody has toured, asked about the home or asked for the disclosure package yet, so there is no one to follow up with.", t)
        self.assertNotIn("We contacted 0 of 0", t)


class Charts(unittest.TestCase):
    """Showings by week and disclosure packages by week, for every week since listing."""

    def test_every_week_has_a_row_zero_weeks_kept_this_week_marked_values_beside_the_bars(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            for mode in ("link", "email") if name == "ledger_small.json" else ("link",):
                page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
                chart, rows = table_of(page, "chart"), chart_rows(page)
                self.assertIn(">Showings</th>", chart)
                self.assertIn(">Packages</th>", chart)
                self.assertEqual(sorted(rows), [w["n"] for w in d["weeks"]])
                for w in d["weeks"]:
                    row = rows[w["n"]]
                    cells = re.findall(r'<td[^>]*align="right"[^>]*>(?:<b>)?(\d+)', row)
                    with self.subTest(ledger=name, week=w["n"]):
                        self.assertEqual([int(x) for x in cells], [w["showings"], w["disclosure_contacts_new"]])     # the value beside each bar
                        self.assertEqual('bgcolor="#EBDCAE"' in row, bool(w["is_current"]))                           # this week is shaded
                        self.assertEqual(row.count('<td height="12"'), (1 if w["showings"] else 0) + (1 if w["disclosure_contacts_new"] else 0))
                self.assertTrue(any(w["showings"] == 0 and w["disclosure_contacts_new"] == 0 for w in d["weeks"]))  # a quiet week keeps its row
                self.assertNotIn("<svg", page)
                self.assertNotIn("<img", chart)

    def test_the_chart_sits_under_the_numbers_and_above_what_people_are_saying(self):
        page = render(load("ledger_busy.json"), identity=ID, no_hero=True)["html"]
        a, b, c = (page.index(x) for x in ('data-sr-table="scorecard"', 'data-sr-table="chart"', 'data-sr-section="saying"'))
        self.assertTrue(a < b < c)

    def test_a_price_change_is_marked_in_the_chart(self):
        t = text_of(render(load("ledger_busy.json"), identity=ID, mode="link", no_hero=True)["html"])
        self.assertIn("Price changed to", t.split("week by week")[1].split("WHAT PEOPLE ARE SAYING")[0])


class Lists(unittest.TestCase):
    """People grouped by what they did. The count in each heading equals the number of entries beneath it."""

    def test_heading_count_equals_entries_in_every_mode(self):
        for d in (load("ledger_small.json"), load("ledger_busy.json"), with_showings_this_week(self), empty_listing(self)):
            want = dict((k, sorted(c["id"] for c in d["contacts"] if k in c["lists"])) for k in C.LIST_KEYS)
            self.assertEqual(dict((k, len(v)) for k, v in want.items()), d["totals"]["lists"])
            for mode in sr_render.MODES:
                page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
                got = entries(page)
                masked = set(o["contact_id"] for o in d["offers"]) if mode != "email" else set()
                for key in C.LIST_KEYS:
                    with self.subTest(slug=d["meta"]["slug"], weeks=len(d["weeks"]), mode=mode, key=key):
                        mine = got.get(key, [])
                        self.assertEqual(len(mine), len(want[key]))
                        self.assertEqual(sorted(cid for _, cid in mine if cid), [i for i in want[key] if i not in masked])
                        if want[key] or key != "other_inquiries":
                            self.assertEqual(hooked(page, "list:" + key), [str(len(want[key]))])
                        else:
                            self.assertEqual(hooked(page, "list:" + key), [])              # no one to list, so no section
                self.assertNotIn(None, got)                                                 # no entry sits outside a list

    def test_a_person_in_two_lists_is_in_full_once_and_a_pointer_in_the_other(self):
        d = load("ledger_small.json")
        c = next(c for c in d["contacts"] if c["id"] == "c001")
        self.assertEqual((c["lists"], c["primary_list"]), (["showings", "disclosure"], "showings"))
        for mode in sr_render.MODES:
            page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
            got = entries(page)
            self.assertIn(("full", "c001"), got["showings"])
            self.assertIn(("pointer", "c001"), got["disclosure"])
            self.assertEqual(page.count('data-sr-entry="full:c001"'), 1)
            self.assertIn("Odalys V.: see Agents who showed the home", text_of(page))
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            byid = dict((c["id"], c) for c in d["contacts"])
            for mode in sr_render.MODES:
                got = entries(render(d, identity=ID, mode=mode, no_hero=True)["html"])
                full = [cid for v in got.values() for form, cid in v if form == "full" and cid]
                self.assertEqual(len(full), len(set(full)))                                 # nobody is in full twice
                for key, v in got.items():
                    for form, cid in v:
                        if cid:
                            self.assertEqual(form == "pointer", byid[cid]["primary_list"] != key, (key, cid, form))
        order = [c["primary_list"] for c in load("ledger_busy.json")["contacts"] if len(c["lists"]) > 1]
        self.assertTrue(order and all(p == "showings" or p == "disclosure" for p in order))   # showings first, then packages

    def test_this_week_in_full_and_earlier_people_in_one_line_each(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            byid = dict((c["id"], c) for c in d["contacts"])
            got = entries(render(d, identity=ID, no_hero=True)["html"])
            for key, v in got.items():
                for form, cid in v:
                    if form != "pointer":
                        self.assertEqual(form, "full" if byid[cid]["active_this_week"] else "line", (name, key, cid))
            for mode in ("link", "print"):                                                  # the link copy and the PDF: everyone in full
                got = entries(render(d, identity=ID, mode=mode, no_hero=True)["html"])
                self.assertEqual(sorted(set(form for v in got.values() for form, _ in v)), ["full", "pointer"])
        t = text_of(render(load("ledger_small.json"), identity=ID, no_hero=True)["html"])
        shown = t.split("SHOWINGS")[1].split("DISCLOSURE PACKAGES")[0]
        self.assertIn("THIS WEEK · 1", shown)
        self.assertIn("EARLIER · 1", shown)
        self.assertIn("Thaddeus K., Northgate Homes. Toured the week of Mar 16. Passed. Last contact Mar 26.", shown)

    def test_what_a_full_entry_says(self):
        d = load("ledger_small.json")
        page = render(d, identity=ID, no_hero=True)["html"]
        card = text_of(page.split('data-sr-entry="full:c001"')[1].split('data-sr-entry=')[0])
        c = next(c for c in d["contacts"] if c["id"] == "c001")
        self.assertIn("Odalys V.", card)
        self.assertIn("Harborlight Realty", card)                                       # short name and brokerage
        self.assertIn("Toured Mar 14 (key box)", card)                                  # what they did and when
        self.assertIn("AS REPORTED TO OUR TEAM", card)
        self.assertIn("Said: ", card)
        self.assertIn("Offer: Possibly", card)
        f = c["followup"]
        self.assertRegex(card, r"Follow-up: %d days? \(%s\): " % (f["outbound_days"], re.escape(", ".join(C.channel_parts([t for t in c["touches"] if C.is_followup(t)])))))
        for t in c["touches"]:
            if C.is_followup(t):
                self.assertIn(C.fmt_date(t["date"]), card.split("Follow-up:")[1])        # every date we tried
        self.assertIn("Responded: Yes, %s" % C.fmt_date(f["last_reply_date"]), card)
        waiting = text_of(page.split('data-sr-entry="full:c003"')[1].split('data-sr-entry=')[0])
        self.assertIn("STILL WAITING", waiting)
        self.assertIn("Said: No feedback from them yet.", waiting)
        self.assertIn("Offer: Not discussed", waiting)
        self.assertIn("Responded: No reply yet after 3 tries", waiting)

    def test_offer_words(self):
        self.assertEqual([k for k, _ in C.OFFER_WORDS], ["offer_received", "writing_one", "possibly", "not_yet", "no", "not_discussed"])
        mk = lambda **kw: dict(dict(id="c1", status="replied", offer_intent="unknown"), **kw)
        self.assertEqual(C.derive_offer_word(mk(), offer_ids=("c1",)), "offer_received")
        self.assertEqual(C.derive_offer_word(mk(status="offer_submitted")), "offer_received")
        self.assertEqual(C.derive_offer_word(mk(status="writing_offer")), "writing_one")
        self.assertEqual(C.derive_offer_word(mk(offer_intent="yes")), "writing_one")
        self.assertEqual(C.derive_offer_word(mk(offer_intent="maybe")), "possibly")
        self.assertEqual(C.derive_offer_word(mk(offer_intent="no")), "not_yet")           # said no for now and has not passed
        self.assertEqual(C.derive_offer_word(mk(status="passed", offer_intent="no")), "no")
        self.assertEqual(C.derive_offer_word(mk()), "not_discussed")

    def test_an_empty_list_prints_one_sentence_and_no_empty_table(self):
        d = empty_listing(self)
        for mode in sr_render.MODES:
            page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
            t = text_of(page)
            self.assertIn("Agents who showed the home (0) No agent has shown the home yet.", t)
            self.assertIn("People on the disclosure package list (0) Nobody has asked for the disclosure package yet.", t)
            self.assertIn("Open house visitors we know of (0) No open house visitor has left a name with us yet.", t)
            self.assertNotIn("OTHER INQUIRIES", t)                                       # shown only when there is someone to list
            self.assertNotIn("data-sr-list=", page)
            self.assertNotIn("data-sr-entry=", page)
            self.assertNotIn("EARLIER", t.split("THE DETAILS")[1].split("NEXT WEEK")[0])
        d = load("ledger_small.json")                                                    # a list with people and nobody new this week
        for c in d["contacts"]:
            if c["id"] == "c001":
                c["touches"] = [x for x in c["touches"] if x["date"] < d["report"]["week_start"]]
                c["feedback_log"] = [x for x in c["feedback_log"] if x["date"] < d["report"]["week_start"]]
        clean(self, d)
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        self.assertIn("Nothing new from the people on this list this week.", t.split("SHOWINGS")[1].split("DISCLOSURE PACKAGES")[0])

    def test_buyers_through_their_agent_are_one_count_not_entries(self):
        d = load("ledger_busy.json")
        k = d["totals"]["disclosure_shared_buyers"]
        self.assertTrue(k)
        page = render(d, identity=ID, no_hero=True)["html"]
        self.assertEqual(hooked(page, "shared_buyers"), [str(k)])
        via = [c["id"] for c in d["contacts"] if c.get("represented_by") and not c["lists"]]
        self.assertEqual(len(via), k)
        self.assertEqual([i for i in via if ('"full:%s"' % i) in page or ('"line:%s"' % i) in page], [])

    def test_open_houses_list_each_session_and_the_visitors_we_know_of(self):
        d = load("ledger_small.json")
        t = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        oh = t.split("OPEN HOUSES")[1].split("OTHER INQUIRIES")[0]
        for o in d["open_houses"]:
            self.assertIn(C.fmt_date(o["date"], weekday=True), oh)
            self.assertIn("Host %s" % o["host"], oh)
        self.assertIn("As reported by each host".upper(), oh)
        self.assertIn("Open house visitors we know of (1)", oh)
        self.assertIn("EARLIER SESSIONS · %d" % (len(d["open_houses"]) - 1), oh)
        email = text_of(render(d, identity=ID, no_hero=True)["html"]).split("OPEN HOUSES")[1].split("OTHER INQUIRIES")[0]
        self.assertIn("EARLIER SESSIONS · %d" % (len(d["open_houses"]) - 1), email)
        self.assertNotIn(d["open_houses"][0]["recap_safe"], email)                       # the email keeps earlier sessions to one line

    def test_the_button_to_the_full_history(self):
        d = load("ledger_busy.json")
        with_link = render(d, identity=ID, **HTTPS)["html"]
        self.assertIn("OPEN THE COMPLETE RECORD", with_link)
        self.assertIn('href="%s"' % HTTPS["link_url"], with_link.split('data-sr-section="history"')[1][:900])
        self.assertLess(with_link.index('data-sr-section="history"'), with_link.index('data-sr-section="next_week"'))
        plain = text_of(render(d, identity=ID, no_hero=True, no_link=True)["html"])
        self.assertIn("is in the complete record. Reply to this email and I will send it to you.", plain)
        self.assertNotIn("OPEN THE COMPLETE RECORD", render(d, identity=ID, mode="link", no_hero=True)["html"])

    def test_the_build_stops_when_a_list_does_not_add_up(self):
        from sr_render.model import Model
        d = load("ledger_small.json")
        render(d, identity=ID, no_hero=True)                    # sets the per-build switches
        m = Model(d, ID, False)
        doc = assemble.build(m, 0)
        self.assertEqual(assemble.footing(doc, m), [])
        short = re.sub(r'<div data-sr-entry="line:c002".*?</div>', "", doc, flags=re.S)
        self.assertTrue(any("entries are marked on the page" in e for e in assemble.footing(short, m)))
        m.entries["showings"].pop()
        self.assertTrue(any(e.startswith("list showings:") for e in assemble.footing(doc, m)))
        m.entries = copy.deepcopy({"showings": [("c001", "full"), ("c002", "full")], "disclosure": [("c001", "full"), ("c003", "full"), ("c004", "line")],
                                   "open_house": [("c004", "pointer")], "other_inquiries": [("c005", "full")]})
        problems = assemble.footing(doc, m)
        self.assertTrue(any("shown in full more than once: c001" in e for e in problems), problems)


class Ceiling(unittest.TestCase):
    def test_the_busy_email_stays_under_95000_bytes(self):
        d = load("ledger_busy.json")
        for kw in (dict(no_hero=True, no_link=True), HTTPS, dict(HTTPS, greeting="Hi Pat and Sam,")):
            r = render(d, identity=ID, **kw)
            self.assertEqual(r["info"]["bytes"], len(r["html"].encode("utf-8")))
            self.assertLessEqual(r["info"]["bytes"], 95000)
            self.assertEqual(r["info"]["max_bytes"], C.LIMITS["email_max_bytes"])
            self.assertEqual(C.LIMITS["email_max_bytes"], 95000)
            self.assertLess(r["info"]["fit_level"], len(FIT_LEVELS) - 3)                   # with room to spare for a busier week


class OnlineViews(unittest.TestCase):
    """B2, the slot: online views join the numbers table, the charts and the record table when the ledger has them."""

    def test_views_feed_the_table_the_chart_and_the_record(self):
        d = with_online(self)
        cur, T = d["weeks"][-1], d["totals"]
        self.assertEqual((cur["online_views"], cur["online_saves"], T["online_views"], T["online_saves"]), (230, 5, 825, 22))
        self.assertEqual([w["online_views"] for w in d["weeks"]], [None, None, 320, 275, 230])
        for mode in sr_render.MODES:
            r = render(d, identity=ID, mode=mode, no_hero=True)
            page, t = r["html"], text_of(r["html"])
            self.assertIn("online", r["info"]["flags"]["sections"])
            row = page.split('<tr data-sr-row="online_views">')[1].split("</tr>")[0]
            self.assertEqual(re.sub(r"\s+", " ", text_of(row)).strip(), "Online views Zillow and Redfin 230 5 saved 275 8 saved 825 22 saved")
            self.assertEqual(page.count('data-sr-table="chart_views"'), 1)
            rows = chart_rows(page, "chart_views")
            self.assertEqual(sorted(rows), [1, 2, 3, 4, 5])
            self.assertIn("not recorded", rows[1])              # never a zero for a week with no figure
            self.assertNotIn('<td height="12"', rows[1])
            self.assertIn(">230<", rows[5])
            self.assertIn("Online views, week by week", t)
            self.assertLess(page.index('data-sr-table="chart"'), page.index('data-sr-table="chart_views"'))
            self.assertLess(page.index('data-sr-table="chart_views"'), page.index('data-sr-section="saying"'))
            weekly = page.split('data-sr-table="weeks"')[1].split("</table>")[0]
            self.assertIn('data-sr-col="online_views"', weekly)
            self.assertIn("825", text_of(weekly.split('data-sr-row="all"')[1]))
            self.assertIn("Views: online views as counted by Zillow and Redfin.", t)

    def test_without_views_nothing_about_them_is_printed(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            self.assertIsNone(d["online"])
            self.assertIsNone(d["totals"]["online_views"])
            r = render(d, identity=ID, no_hero=True)
            self.assertNotIn("online", r["info"]["flags"]["sections"])
            for word in ("Online views", "chart_views", "online_views", "Views"):
                self.assertNotIn(word, r["html"])

    def test_the_contract_checks_the_block(self):
        d = with_online(self)
        d["online"]["weeks"][0]["views"]["Trulia"] = 5
        self.assertTrue(any("online.weeks[0].views" in p for p in C.validate_ledger(d, identity=ID)))
        d = with_online(self)
        d["online"]["weeks"].append({"n": 9, "views": {"Zillow": 1}})
        self.assertTrue(any("online.weeks[3]" in p for p in C.validate_ledger(d, identity=ID)))
        d = with_online(self)
        d["weeks"][-1]["online_views"] = 999
        self.assertTrue(any("online_views" in p for p in C.validate_ledger(d, identity=ID)))


class SimilarHomesNearby(unittest.TestCase):
    """B3, the slot: the section renders when the ledger has a watch list, with what changed this week."""

    def test_the_section_says_what_changed(self):
        d = with_nearby(self)
        for mode in sr_render.MODES:
            r = render(d, identity=ID, mode=mode, no_hero=True)
            self.assertEqual(r["info"]["flags"]["sections"], ["nearby", "market", "marketing"])
            t = text_of(r["html"].split('data-sr-section="nearby"')[1].split('data-sr-section="market"')[0])
            self.assertIn("4 of the 5 homes we are watching changed", t)
            self.assertIn("Five 3 bedroom homes within half a mile, chosen on Mar 16. Checked Apr 13.", t)
            self.assertIn("WHAT CHANGED 14 Sample Fern Ln New listing on Apr 10 at $1,210,000.", t)
            self.assertIn("Price changed on Apr 8: $1,199,000 to $1,150,000.", t)
            self.assertIn("Went pending on Apr 9 after 12 days on the market. Listed at $1,249,000.", t)
            self.assertIn("Sold on Apr 7 for $1,182,000 after 9 days on the market. Listed at $1,175,000.", t)
            # then the whole watch list as one compact table: what changed first, the unchanged home last
            self.assertIn("Home Status Price Days 14 Sample Fern Ln 3 bed, 2 bath, 1,510 sq ft Active $1,210,000 3", t)
            self.assertIn("52 Sample Birch Dr 3 bed, 2 bath, 1,390 sq ft Sold $1,182,000 9", t)       # a sold home shows its sale price
            self.assertIn("7 Sample Elm Pl 3 bed, 2 bath, 1,475 sq ft Active $1,225,000 61", t)
            self.assertLess(t.index("WHAT CHANGED"), t.index("Home Status Price Days"))
            self.assertEqual(t.count("7 Sample Elm Pl"), 1)                                 # unchanged: in the table only
            self.assertLess(t.rindex("14 Sample Fern Ln"), t.index("7 Sample Elm Pl"))
            table = r["html"].split('data-sr-table="nearby"')[1].split("</table>")[0]
            self.assertEqual(re.findall(r'<tr data-sr-row="(\d)"', table), ["0", "1", "2", "3", "4"])
            self.assertNotIn("table-layout:fixed", r["html"].split('data-sr-table="nearby"')[0][-200:])

    def test_it_is_left_out_when_there_is_no_watch_list_or_when_asked(self):
        self.assertNotIn("SIMILAR HOMES NEARBY", text_of(render(load("ledger_small.json"), identity=ID, no_hero=True)["html"]))
        r = render(with_nearby(self), identity=ID, no_hero=True, nearby=False)
        self.assertNotIn("SIMILAR HOMES NEARBY", text_of(r["html"]))
        self.assertNotIn("nearby", r["info"]["flags"]["sections"])

    def test_a_list_not_checked_for_this_issue_says_so(self):
        d = with_nearby(self)
        d["nearby"].update(checked_for_this_issue=False, as_of="2026-04-06")
        for h in d["nearby"]["homes"]:
            h["change"], h["change_date"] = "none", None
        clean(self, d)
        t = text_of(render(d, identity=ID, no_hero=True)["html"])
        self.assertIn("No change among the 5 homes we are watching", t)
        self.assertIn("Last checked Apr 6, not checked again for this report.", t)

    def test_the_contract_checks_the_block(self):
        d = with_nearby(self)
        d["nearby"]["homes"] += [copy.deepcopy(d["nearby"]["homes"][-1]) for _ in range(4)]
        self.assertTrue(any("at most 8 homes" in p for p in C.validate_ledger(d, identity=ID)))
        d = with_nearby(self)
        d["nearby"]["homes"][0]["address"] = d["listing"]["address"]
        self.assertTrue(any("is this listing" in p for p in C.validate_ledger(d, identity=ID)))
        d = with_nearby(self)
        d["nearby"]["homes"][3]["sold_price"] = None
        self.assertTrue(any("sold_price" in p for p in C.validate_ledger(d, identity=ID)))
        d = with_nearby(self)                                   # a buyer's destination is still never an address in a comment
        d["contacts"][0]["feedback_safe"] = "Her clients chose 14 Sample Fern Ln instead."
        self.assertTrue(any("names another address" in p for p in C.validate_ledger(d, identity=ID)))


class ThroughTheGate(GateHarness):
    """The pages the renderer builds pass the ship gate, which counts everything again from the ledger."""

    def rendered(self, fx, kind, led=None):
        def page(_, t):
            return render(t.ledger, identity=ID, mode=kind, no_hero=True, no_link=True)["html"]
        return self.gate(fx=fx, kind=kind, led=led, edit=page)

    def test_both_fixtures_in_every_mode(self):
        for fx in ("small", "busy"):
            for kind in sr_render.MODES:
                with self.subTest(fx=fx, kind=kind):
                    rep = self.rendered(fx, kind)
                    shutil.rmtree(os.path.join(self.tmp, "root"))
                    self.assertTrue(rep.ok, rep.as_text())
                    passed = [r.id for r in rep.results if r.level == "pass"]
                    for rule in ("numbers.table_scorecard", "numbers.chart_weeks", "numbers.chart_series", "numbers.table_weeks",
                                 "numbers.contacted" if fx == "busy" else "numbers.through_host", "numbers.contacts", "numbers.answered",
                                 "numbers.waiting", "numbers.showings_defined", "numbers.list_heading.showings",
                                 "numbers.list_entries.showings", "numbers.list_heading.disclosure", "numbers.list_entries.disclosure",
                                 "numbers.list_entries.open_house", "numbers.list_placement", "numbers.person_lines", "numbers.person_dates",
                                 "numbers.list_this_week" if kind == "email" else "numbers.list_everyone_in_full"):
                        self.assertIn(rule, passed, rule)

    def test_the_short_forms_of_the_optional_sections_in_a_long_email(self):
        """When the email runs out of room the optional sections give way first, and the gate counts their short forms."""
        def led(d, t):
            d["online"], d["nearby"] = with_online(self)["online"], with_nearby(self)["nearby"]
            C.finish_ledger(d)

        def page(_, t):
            full = render(t.ledger, identity=ID, mode="email", no_hero=True, no_link=True)
            r = render(t.ledger, identity=ID, mode="email", no_hero=True, no_link=True, max_bytes=full["info"]["bytes"] - 500)
            t.fit = (full["info"], r["info"])
            return r["html"]
        rep = self.gate(fx="small", kind="email", led=led, edit=page)
        self.assertTrue(rep.ok, rep.as_text())
        full, short = self.fit
        self.assertEqual((full["fit_level"], short["fit_level"]), (0, 1))
        self.assertLess(short["bytes"], full["bytes"] - 6000)                 # the three optional sections gave back more than 6 KB
        with open(self.path, encoding="utf-8") as f:
            html_ = f.read()
        t = text_of(html_)
        self.assertNotIn('data-sr-table="nearby"', html_)
        self.assertIn("The other 1 home did not change: 1 active. Each one is in the complete record.", t)
        self.assertIn("Went pending on Apr 9 after 12 days on the market.", t)          # what changed is still said in full
        self.assertNotIn('data-sr-table="chart_views"', html_)
        self.assertIn('<tr data-sr-row="online_views">', html_)               # the row in the numbers table stays
        self.assertIn("Prepared: YouTube ads.", t)
        self.assertIn("Facebook and Instagram ads SWITCHED ON Last checked Apr 2.", t)
        passed = [r.id for r in rep.results if r.level == "pass"]
        for rule in ("numbers.nearby_counts", "numbers.nearby_table", "numbers.nearby_changes", "numbers.marketing_words", "numbers.table_scorecard"):
            self.assertIn(rule, passed)
        self.assertEqual(FIT_LEVELS[0]["extras"], "full")
        self.assertTrue(all(lv["extras"] == "short" for lv in FIT_LEVELS[1:]))

    def test_with_online_views_and_similar_homes_nearby(self):
        def led(d, t):
            d["online"], d["nearby"] = with_online(self)["online"], with_nearby(self)["nearby"]
            C.finish_ledger(d)
        for kind in sr_render.MODES:
            with self.subTest(kind=kind):
                rep = self.rendered("small", kind, led=led)
                shutil.rmtree(os.path.join(self.tmp, "root"))
                self.assertTrue(rep.ok, rep.as_text())
                passed = [r.id for r in rep.results if r.level == "pass"]
                for rule in ("numbers.table_scorecard", "numbers.chart_views_weeks", "numbers.table_weeks", "numbers.marked_values",
                             "privacy.address_pattern"):
                    self.assertIn(rule, passed, rule)
                self.assertIn("watched home", next(r.message for r in rep.results if r.id == "privacy.address_pattern"))


if __name__ == "__main__":
    unittest.main()
