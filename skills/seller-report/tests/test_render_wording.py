# -*- coding: utf-8 -*-
"""Tests for the shared wording rules of a seller report page (scripts/sr_render).

    python -m unittest discover -s tests -p "test_render*.py"       (from the seller-report folder)
    python tests\\test_render_wording.py

Rules that hold for every listing: the heading when no offer is on record, the online views note, the record
intro, a listing with no separate key-box record, the "in touch this week" subhead, the line under the price
rows, the "since the week closed" box (one line per person per day), people who answered after the week
closed, and open house traffic in the hosts' own unit. Synthetic data only: the helpers and the fixtures come
from test_render.py.
"""
import copy
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_render import C, ID, clean, empty_listing, load, render, sr_render, text_of  # noqa: E402
from sr_render.sections_top import SINCE_MAX_LINES, since_line  # noqa: E402
from sr_render.sections_saying import host_remarks_line, week_price_line  # noqa: E402
from sr_render.model import Model  # noqa: E402
from sr_render import people  # noqa: E402
from sr_render.htmlkit import low1  # noqa: E402

MONDAY = "2026-04-13"           # the day after the small fixture's week closed


def email(d, **kw):
    return text_of(render(d, identity=ID, no_hero=True, **kw)["html"])


def touch(cid, name, summary, channel, direction, outcome, date=MONDAY, **more):
    it = {"date": date, "kind": "touch", "contact_id": cid, "name_short": name, "summary_safe": summary, "offer_related": False,
          "channel": channel, "direction": direction, "outcome": outcome}
    it.update(more)
    return it


def since_box(page_text):
    return page_text.split("SINCE THE WEEK CLOSED")[1].split("THE NUMBERS")[0]


class OffersHeading(unittest.TestCase):
    def test_no_offer_and_nobody_deciding_reads_as_a_plain_fact(self):
        t = email(empty_listing(self))
        offers = t.split("OFFERS AND LIKELY OFFERS")[1].split("SHOWINGS")[0]
        self.assertIn("No offer this week", offers)
        self.assertNotIn("no one has told us", t)
        self.assertNotIn("is coming", offers)

    def test_a_note_about_an_offer_after_the_week_points_to_the_top(self):
        d = load("ledger_small.json")
        d["offer_watch"] = []
        for c in d["contacts"]:
            c["offer_intent"], c["offer_basis_safe"], c["offer_basis_date"] = "unknown", None, None
        d["report"]["since_week_closed"]["items"] = [
            touch("c005", "Casimir D.", "Spoke by phone. He will ask his client about making an offer.", "call", "outbound", "reached",
                  offer_related=True)]
        clean(self, d)
        t = email(d)
        offers = t.split("OFFERS AND LIKELY OFFERS")[1].split("SHOWINGS")[0]
        self.assertIn("No offer this week", offers)
        # a note that an agent will ask about an offer is not an offer: the pointer must not say one exists
        self.assertIn("No offers have come in since we listed. A possible offer was discussed after the week closed: see the "
                      "note from Casimir D. (Apr 13) at the top of this report.", offers)
        self.assertNotIn("An offer came", offers)
        self.assertIn("Offer: Not discussed by Sunday, Apr 12. See the Apr 13 note at the top of this report.", t)
        link = text_of(render(d, identity=ID, mode="link", no_hero=True)["html"])
        self.assertNotIn("A possible offer was discussed", link)    # the link copy carries no offer news at all
        self.assertNotIn("ask his client about making an offer", link)
        # an offer that is itself on record after the week closed is said as one
        d["report"]["since_week_closed"]["items"] = [
            {"date": MONDAY, "kind": "offer", "contact_id": "c005", "name_short": "Casimir D.",
             "summary_safe": "An offer came in on Monday. The terms are in next week's report.", "offer_related": True}]
        clean(self, d)
        offers = email(d).split("OFFERS AND LIKELY OFFERS")[1].split("SHOWINGS")[0]
        self.assertIn("An offer came in after the week closed: see the note from Casimir D. (Apr 13) at the top of this report.", offers)
        self.assertNotIn("A possible offer was discussed", offers)

    def test_the_summary_of_earlier_offers_states_recorded_outcomes_only(self):
        d = load("ledger_busy.json")
        for o in d["offers"][:2]:
            o["state"] = "expired"
        d["offers"][2]["state"] = "received"
        clean(self, d)
        t = email(d)
        lede = t.split("Earlier offers (3)")[1][:260]
        self.assertIn("2 expired.", lede)
        self.assertNotIn("no outcome on record", lede)
        self.assertNotIn("has since", lede)


class FixedLines(unittest.TestCase):
    def test_the_record_intro_makes_no_promise_about_mondays(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            for mode in sr_render.MODES:
                t = text_of(render(load(name), identity=ID, mode=mode, no_hero=True)["html"])
                self.assertIn("It is carried forward from report to report.", t)
                self.assertNotIn("every Monday", t)

    def test_a_listing_with_no_key_box_record_never_says_so(self):
        d = load("ledger_small.json")
        d["report"]["tracking"]["keybox_showings"] = False
        for c in d["contacts"]:
            for e in c["engagements"]:
                if e["type"] == "keybox_showing":
                    e["type"] = "agent_reported_tour"
        clean(self, d)
        for mode in sr_render.MODES:
            t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"])
            self.assertIn("Showings are tours on the showing log plus tours agents told us about.", t)
            self.assertIn("Showings: tours on the showing log plus tours an agent or buyer told us about.", t)
            self.assertNotIn("no key-box record", t)
            self.assertNotIn("not recorded for this listing", t)
            self.assertNotIn("key box", t.lower().replace("-", " "))
        t = email(load("ledger_small.json"))                        # a listing that has the record still says what it counts
        self.assertIn("Showings count key-box showings (", t)
        self.assertIn("Showings: key-box showings plus tours an agent or buyer told us about.", t)

    def test_the_subhead_counts_people_in_touch_not_showings(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            for mode in sr_render.MODES:
                t = text_of(render(load(name), identity=ID, mode=mode, no_hero=True)["html"])
                lists = t.split("OFFERS AND LIKELY OFFERS")[1].split("NEXT WEEK")[0]
                self.assertRegex(lists, r"IN TOUCH THIS WEEK · \d+")
                self.assertIsNone(re.search(r"(?<!IN TOUCH )THIS WEEK · \d", lists), "a bare THIS WEEK count reads as a count of showings")

    def test_the_line_under_the_price_rows(self):
        class M(object):
            cur = {"conversations_with_feedback": 17, "price_too_high": 0, "price_fair_or_positive": 0}
        self.assertEqual(week_price_line(M()), "This week: 17 conversations. Nobody gave a view on price.")
        M.cur = {"conversations_with_feedback": 1, "price_too_high": 0, "price_fair_or_positive": 0}
        self.assertEqual(week_price_line(M()), "This week: 1 conversation. Nobody gave a view on price.")
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            w = d["weeks"][-1]
            self.assertTrue(w["conversations_with_feedback"] and not (w["price_too_high"] + w["price_fair_or_positive"]))
            for mode in sr_render.MODES:
                t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"])
                self.assertIn("Nobody gave a view on price.", t.split("WHAT PEOPLE ARE SAYING")[1])
                self.assertNotIn("Price did not come up", t)
        brief = email(load("ledger_busy.json")).split("THIS WEEK IN BRIEF")[1].split("THE NUMBERS")[0]
        self.assertIn("Nobody gave a view on price in the 6 conversations, and", brief)

    def test_the_weekly_table_legend_explains_only_the_words_it_prints(self):
        d = load("ledger_small.json")
        t = email(d)
        legend = t.split("Open house: ")[1].split("Follow ups:")[0]
        table = t.split("Every week in one table")[1].split("Shown:")[0]
        self.assertEqual("None means no open house." in legend, " none " in table)
        self.assertEqual("Held means one took place with no count kept." in legend, " held " in table)
        self.assertIn("None means no open house.", legend)          # the small fixture has a week with no open house
        for o in d["open_houses"]:                                  # every week had an open house and every host kept a count
            if o["groups"] is None:
                o.update(groups=2, groups_source=d["open_houses"][0]["groups_source"])
        dates = set(o["date"] for o in d["open_houses"])
        for w in d["weeks"]:
            if not any(w["start"] <= day <= w["end"] for day in dates):
                d["open_houses"].append(dict(copy.deepcopy(d["open_houses"][0]), date=w["start"], groups=1))
        clean(self, d)
        legend = email(d).split("Open house: ")[1].split("Follow ups:")[0]
        self.assertEqual(legend.strip(), "groups counted.")


class SinceTheWeekClosed(unittest.TestCase):
    """One line per person per day: what we did first, then their answer."""

    def test_one_person_one_day_is_one_line(self):
        tries = [touch("c1", "A", "Called about the new list price, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail"),
                 touch("c1", "A", "Sent a text about the new list price.", "text", "outbound", "sent"),
                 touch("c1", "A", "Sent an email about the new list price.", "email", "outbound", "sent")]
        self.assertEqual(since_line(tries), ("We called, texted and emailed about the new list price. No answer yet.", False))
        said = touch("c1", "A", "Said his clients picked a home nearer their work.", "unknown", "inbound", "replied")
        self.assertEqual(since_line([tries[0], said] + tries[1:]),
                         ("We called, texted and emailed about the new list price. He said his clients picked a home nearer their work.", True))
        wrote = touch("c1", "A", "Replied that her client wants a second visit.", "unknown", "inbound", "replied")
        plain = [touch("c1", "A", "Called, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail"),
                 touch("c1", "A", "Sent a text.", "text", "outbound", "sent")]
        self.assertEqual(since_line(plain + [wrote]), ("We called and texted. She replied that her client wants a second visit.", True))

    def test_an_answer_on_a_call_from_our_own_call_column_says_we_called(self):
        got = touch("c1", "A", "Replied that they would like the floor plan.", "call", "inbound", "replied", our_call=True)
        sent = touch("c1", "A", "Sent a text. No note was kept.", "text", "outbound", "sent")
        self.assertEqual(since_line([got, sent]), ("We called and texted. They replied that they would like the floor plan.", True))
        got.pop("our_call")
        self.assertEqual(since_line([got, sent]), ("We texted. They replied that they would like the floor plan.", True))

    def test_a_call_that_did_not_connect_is_said_plainly(self):
        items = [touch("c1", "A", "Called. The call did not connect.", "call", "outbound", "did_not_connect"),
                 touch("c1", "A", "Sent an email about the new list price.", "email", "outbound", "sent")]
        # the call is said before the line says it did not connect
        self.assertEqual(since_line(items), ("We called and emailed about the new list price. The call did not connect.", False))
        self.assertEqual(since_line(items[:1] + [touch("c1", "A", "Called again. The call did not connect.", "call", "outbound", "did_not_connect")]),
                         ("We called. The calls did not connect.", False))
        vm = touch("c1", "A", "Called, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail")
        self.assertEqual(since_line([items[0], vm]), ("We called. One call did not connect.", False))

    def test_a_single_entry_prints_as_written(self):
        one = touch("c1", "A", "Reached him by phone about the open house. He said his client would come by on Sunday.",
                    "call", "outbound", "reached")
        self.assertEqual(since_line([one]), (one["summary_safe"], True))
        vm = touch("c1", "A", "Called, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail")
        self.assertEqual(since_line([vm]), ("Called, no answer. Left a voicemail.", False))
        old = {"date": MONDAY, "kind": "touch", "contact_id": "c1", "name_short": "A", "summary_safe": "Sent a text on Monday morning. No answer yet."}
        self.assertEqual(since_line([old]), (old["summary_safe"], False))            # an entry with no channel on record

    def test_a_call_that_reached_them_leads_the_line(self):
        items = [touch("c1", "A", "Reached her by phone. She said her client liked the garden.", "call", "outbound", "reached"),
                 touch("c1", "A", "Sent a text.", "text", "outbound", "sent")]
        self.assertEqual(since_line(items), ("Reached her by phone. She said her client liked the garden. We also texted.", True))

    def test_the_box_prints_one_line_for_each_person(self):
        d = load("ledger_small.json")
        d["report"]["since_week_closed"]["items"] = [
            touch("c003", "Wilhelmina R.", "Called, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail"),
            touch("c003", "Wilhelmina R.", "Replied that her client is still looking at other homes.", "text", "inbound", "replied"),
            touch("c003", "Wilhelmina R.", "Sent a text.", "text", "outbound", "sent"),
            touch("c002", "Thaddeus K.", "Sent an email.", "email", "outbound", "sent")]
        clean(self, d)
        for mode in sr_render.MODES:
            box = since_box(text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"]))
            self.assertEqual(box.count("Apr 13 · "), 2, mode)
            self.assertIn("Apr 13 · Wilhelmina R.: We called and texted. She replied that her client is still looking at other homes.", box)
            self.assertIn("Apr 13 · Thaddeus K.: Sent an email.", box)

    def test_a_long_box_keeps_the_answers_and_counts_the_rest(self):
        d = load("ledger_busy.json")
        people = [c for c in d["contacts"] if C.is_counted(c)][:SINCE_MAX_LINES + 3]
        items = []
        for i, c in enumerate(people):
            items.append(touch(c["id"], c["name_short"], "Called, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail",
                               date=d["report"]["since_week_closed"]["through"]))
            items.append(touch(c["id"], c["name_short"], "Sent a text.", "text", "outbound", "sent", date=items[-1]["date"]))
            if i < 2:
                items.append(touch(c["id"], c["name_short"], "Replied that her client is still deciding.", "text", "inbound", "replied",
                                   date=items[-1]["date"]))
        d["report"]["since_week_closed"]["items"] = items
        clean(self, d)
        box = since_box(email(d))
        self.assertEqual(len(re.findall(r"Mar 23 · ", box)), 2)
        self.assertIn("We also followed up with %d more people who have not answered yet." % (len(people) - 2), box)
        for c in people[2:]:
            self.assertNotIn(c["name_short"] + ":", box)
        d["report"]["since_week_closed"]["items"] = [it for it in items if it["contact_id"] in [c["id"] for c in people[:SINCE_MAX_LINES]]]
        clean(self, d)
        box = since_box(email(d))                                   # ten lines or fewer: everyone has a line
        self.assertEqual(len(re.findall(r"Mar 23 · ", box)), SINCE_MAX_LINES)
        self.assertNotIn("We also followed up with", box)


class AnsweredAfterTheWeekClosed(unittest.TestCase):
    """Someone in the box at the top never reads as stale further down the same page. No count changes."""

    def setUp(self):
        self.base = load("ledger_small.json")
        d = load("ledger_small.json")
        d["report"]["since_week_closed"]["items"] = [
            touch("c003", "Wilhelmina R.", "Called, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail"),
            touch("c003", "Wilhelmina R.", "Replied that her client is still looking at other homes.", "text", "inbound", "replied"),
            touch("c001", "Odalys V.", "Reached her by phone. She said her clients want to see the home again.", "call", "outbound", "reached"),
            touch("c004", "Open house visitor, Mar 28", "Sent a text.", "text", "outbound", "sent")]
        self.d = clean(self, d)

    def card(self, page, cid, form="full"):
        return text_of(page.split('data-sr-entry="%s:%s"' % (form, cid))[1].split("data-sr-entry=")[0])

    def test_the_full_entry_points_to_the_top(self):
        page = render(self.d, identity=ID, no_hero=True)["html"]
        waiting = self.card(page, "c003")
        self.assertNotIn("No feedback from them yet", waiting)
        self.assertIn("Responded: No reply by Sunday, Apr 12. Answered Apr 13, see the top of this report.", waiting)
        self.assertNotIn("No reply yet", waiting)
        again = self.card(page, "c001")
        self.assertRegex(again, r"Responded: Yes, Apr 8 \(\d replies in all\)\. More on Apr 13, see the top of this report\.")

    def test_someone_we_only_tried_again_keeps_their_line(self):
        page = render(self.d, identity=ID, no_hero=True)["html"]
        line = self.card(page, "c004", "line")
        self.assertNotIn("see the top of this report", line)        # a try of ours is not an answer of theirs

    def test_without_an_entry_at_the_top_nothing_changes(self):
        d = load("ledger_small.json")
        d["report"]["since_week_closed"]["items"] = []
        clean(self, d)
        page = render(d, identity=ID, no_hero=True)["html"]
        waiting = self.card(page, "c003")
        self.assertIn("Said: No feedback from them yet.", waiting)
        self.assertIn("Responded: No reply yet after 3 tries", waiting)

    def test_a_one_line_entry_points_to_the_top_too(self):
        d = load("ledger_busy.json")
        x = next(c for c in d["contacts"] if C.is_counted(c) and c["status"] == "awaiting_reply" and not c["active_this_week"])
        d["report"]["since_week_closed"]["items"] = [
            touch(x["id"], x["name_short"], "Replied that the buyers chose another home.", "text", "inbound", "replied",
                  date=d["report"]["since_week_closed"]["through"])]
        clean(self, d)
        page = render(d, identity=ID, no_hero=True)["html"]
        line = self.card(page, x["id"], "line")
        self.assertIn("No reply by Sunday, Mar 22. Answered Mar 23, see the top of this report.", line)
        self.assertNotIn("No reply since", line)
        self.assertNotIn("No reply yet", line)

    def test_no_count_moves(self):
        a, b = email(self.base), email(self.d)
        for t in (a, b):
            self.assertIn("still waiting.", t)
        table = lambda t: t.split("THE NUMBERS")[1].split("We contacted")[0]
        line = lambda t: re.search(r"We contacted .*? still waiting\.", t.split("THE NUMBERS")[1]).group(0)
        self.assertEqual((table(a), line(a)), (table(b), line(b)))
        self.assertEqual(self.base["totals"], self.d["totals"])
        # the badge follows the text: someone who answered after the week closed is not badged as still waiting
        for mode in sr_render.MODES:
            page = render(self.d, identity=ID, mode=mode, no_hero=True)["html"]
            card = self.card(page, "c003")
            self.assertNotIn("STILL WAITING", card, mode)
            self.assertEqual(card.count("ANSWERED APR 13"), 1, mode)
            self.assertEqual(self.card(render(self.base, identity=ID, mode=mode, no_hero=True)["html"], "c003").count("STILL WAITING"), 1)
        self.assertIn("still waiting.", email(self.d).split("THE NUMBERS")[1].split("WHAT PEOPLE ARE SAYING")[0])       # the count is as of Sunday


class OpenHouseTrafficKeepsTheHostsUnit(unittest.TestCase):
    """The note for a price-change week in the weekly table: groups stay groups."""

    def note(self, d):
        t = email(d)
        return re.search(r"Week \d+ includes [^:]+: [^.]+\.", t.split("Every week in one table")[1]).group(0)

    def test_groups_stay_groups_when_another_host_counted_visitors(self):
        d = load("ledger_busy.json")
        self.assertIn("6 groups at the open houses", self.note(d))  # two sessions on those days
        d["open_houses"][0]["counted_unit"] = "visitors"            # a host on other days counted people
        clean(self, d)
        note = self.note(d)
        self.assertIn("6 groups at the open houses", note)
        self.assertNotIn("visitors", note)

    def test_hosts_who_counted_differently_on_those_days_are_not_added_as_one_unit(self):
        d = load("ledger_busy.json")
        next(o for o in d["open_houses"] if o["date"] == "2026-02-08")["counted_unit"] = "visitors"
        clean(self, d)
        note = self.note(d)
        self.assertIn("6 open house visits, as each host counted", note)
        self.assertNotIn("6 groups", note)
        self.assertNotIn("6 visitors", note)


class OneLineEntries(unittest.TestCase):
    """What a one-line entry may say: nothing a reader could take for words the person did not say this week."""

    def setUp(self):
        self.d = load("ledger_busy.json")
        self.m = Model(self.d, ID)

    def test_a_price_view_from_an_earlier_list_price_is_left_to_the_record(self):
        m = self.m
        changed = self.d["listing"]["price_history"][-1]["date"]
        seen = set()
        for x in m.direct:
            if x.get("price_reaction") not in ("too_high", "fair_or_positive"):
                continue
            said = max(e["date"] for e in C.counted_feedback(x, m.WE) if e.get("price_reaction") == x["price_reaction"])
            now = said >= changed
            seen.add(now)
            self.assertEqual(people.price_view_current(m, x), now, x["id"])
            bits = people.line_bits(m, x, x["primary_list"], 2)
            self.assertEqual(any(b.startswith("Said the price") for b in bits), now, (x["id"], bits))
        self.assertEqual(seen, set([True, False]), "the fixture holds a remark from each side of the price change")

    def test_passed_says_when_only_if_every_answer_falls_in_one_month(self):
        m = self.m
        seen = set()
        for x in m.passed:
            months = set((d.year, d.month) for d in x["_reply_days"])
            one = len(months) == 1 and x["_reply_days"][-1] < m.WS
            seen.add(one)
            short = people.line_bits(m, x, x["primary_list"], 0)
            if one:
                self.assertIn("Passed in %s" % people.MONTH_NAMES[x["_reply_days"][0].month - 1], short, x["id"])
            else:
                self.assertIn("Passed", short, x["id"])
            long_ = people.line_bits(m, x, x["primary_list"], 2)     # the long form gives the last contact date instead
            self.assertIn("Passed", long_)
            self.assertFalse(any(b.startswith("Passed in") for b in long_))
        self.assertIn(True, seen)

    def test_this_week_says_what_we_told_them_when_they_have_not_answered(self):
        m = self.m
        x = m.passed[0]
        day = self.d["report"]["week_start"]
        told = {"date": day, "channel": "call", "direction": "outbound", "outcome": "unknown", "summary_safe": "Told him about the new list price."}
        x["_out"], x["_reply_days"] = [told], []
        self.assertEqual(people.week_words(m, x), "Told about the new list price this week")
        x["_out"] = [told, dict(told, summary_safe="Sent a text about the next open house.")]
        self.assertEqual(people.week_words(m, x), "We followed up this week")        # two subjects: no single thing to say
        x["_out"], x["_reply_days"] = [told], [m.WS]
        self.assertEqual(people.week_words(m, x), "Answered this week")              # they answered: the line does not speak for them
        x["_out"], x["_reply_days"] = [dict(told, summary_safe="Sent a text.")], []
        self.assertEqual(people.week_words(m, x), "We followed up this week")
        x["_out"], x["_reply_days"] = [], []
        self.assertEqual(people.week_words(m, x), "In touch this week")              # they did something: no answer, no follow-up

    def test_an_answer_this_week_is_said_once(self):
        d = load("ledger_busy.json")
        m = Model(d, ID)
        x = next(c for c in m.active if m.wk(c, "rep") and c["status"] == "replied" and c["id"] not in m.offer_ids
                 and c.get("offer_word") not in ("possibly", "writing_one"))
        line = text_of(people.entry_line(m, x, x["primary_list"], 0, first=True, this_week=True))
        self.assertIn("Answered this week", line)
        self.assertEqual(line.count("Answered"), 1, line)
        # the point raised this week follows, in the words of the tally: never "no reason given", never more than two
        labels = dict((t["key"], t["label"]) for t in d["themes_vocabulary"]["themes"])
        for y in m.active:
            if not m.wk(y, "rep"):
                continue
            said = []
            for e in C.counted_feedback(y, m.WE):
                if e["date"] >= d["report"]["week_start"]:
                    said += [k for k in e["themes"] if k not in said and k not in ("other", "no_reason")]
            words = people.week_words(m, y)
            if said:
                self.assertEqual(words, "Answered this week: " + C.join_and([low1(labels[k]) for k in said[:2]]), y["id"])
            else:
                self.assertEqual(words, "Answered this week", y["id"])
            self.assertNotIn("no reason given", words)
        earlier = text_of(people.entry_line(m, x, x["primary_list"], 0, first=True))
        self.assertRegex(earlier, r"Answered(, (interested|undecided))?\.")      # an earlier person keeps the standing as it was

    def test_the_weeks_own_events_lead_the_list(self):
        d = load("ledger_small.json")
        m = Model(d, ID)
        for key in C.LIST_KEYS:
            now = m.members(key)[0]
            did = [any(e.get("date") and d["report"]["week_start"] <= e["date"] <= d["report"]["week_end"] for e in x["engagements"]) for x in now]
            self.assertEqual(did, sorted(did, reverse=True), key)     # anyone who toured, asked or joined a list this week comes first

    def test_a_buyer_followed_through_a_host_is_not_shown_as_having_replied(self):
        d = load("ledger_small.json")
        via = next(c for c in d["contacts"] if c.get("represented_by"))
        m = Model(d, ID, link=True)
        x = m.byid[via["id"]]
        chip = text_of(people.status_chip(m, x)).strip().upper()
        self.assertEqual(chip, "THROUGH THEIR AGENT")
        self.assertIn("Got the disclosure package from their agent", people.engaged(m, x))
        host = next(c for c in d["contacts"] if c["id"] == via["represented_by"])
        host["is_open_house_host"] = True
        m = Model(d, ID, link=True)
        x = m.byid[via["id"]]
        self.assertEqual(text_of(people.status_chip(m, x)).strip().upper(), "THROUGH THE HOST")
        self.assertIn("Got the disclosure package from the open house host", people.engaged(m, x))

    def test_someone_first_tried_after_the_week_closed_is_not_left_as_never_tried(self):
        d = load("ledger_small.json")
        c = C.blank_contact("c091", "Rosalind P.", "buyer", None)
        c["engagements"] = [{"type": "disclosure_on_list", "date": None, "date_quality": "missing", "confirmed": True}]
        d["contacts"].append(c)
        d["report"]["since_week_closed"]["items"] = [
            touch("c091", "Rosalind P.", "Called, no answer. Left a voicemail.", "voicemail", "outbound", "left_voicemail")]
        clean(self, d)
        t = email(d)
        self.assertIn("Not reached by Sunday, Apr 12. First tried Apr 13, see the top of this report", t)
        d["report"]["since_week_closed"]["items"] = []
        clean(self, d)
        self.assertNotIn("First tried", email(d))


class HostRemarksAboutPrice(unittest.TestCase):
    """The line right after 'This week: N conversations' never lets an older host remark read as this week's."""

    def test_remarks_from_earlier_weeks_are_dated(self):
        d = load("ledger_busy.json")
        self.assertEqual([r["date"] for r in d["pricing_tally"]["open_house_price_remarks"]], ["2026-02-07", "2026-02-14"])
        for mode in sr_render.MODES:
            t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"]).split("WHAT PEOPLE ARE SAYING")[1]
            price = t.split("OTHER POINTS PEOPLE RAISED")[0]
            self.assertIn("This week: 6 conversations. Nobody gave a view on price.", price)
            self.assertIn("Since we listed, open house hosts have also passed on 2 remarks about price, "
                          "none of them this week (the latest was Feb 14). They are ", price)
            self.assertIn(" and are not in these counts.", t)
            self.assertNotIn("Open house hosts also passed on", t)

    def test_a_remark_in_the_report_week_is_counted_as_this_weeks(self):
        d = load("ledger_busy.json")
        d["pricing_tally"]["open_house_price_remarks"][1]["date"] = d["report"]["week_end"]
        clean(self, d)
        t = email(d).split("WHAT PEOPLE ARE SAYING")[1]
        self.assertIn("Since we listed, open house hosts have also passed on 2 remarks about price, 1 of them this week. They are ", t)
        self.assertNotIn("the latest was", t)

    def test_the_other_counts(self):
        m = Model(load("ledger_busy.json"), ID)
        wk, old = m.R["week_start"], "2026-02-14"
        line = lambda days: host_remarks_line(m, [{"date": day} for day in days])
        self.assertEqual(line([old]), "Since we listed, open house hosts have also passed on 1 remark about price, on Feb 14, before this week.")
        self.assertEqual(line([wk]), "Since we listed, open house hosts have also passed on 1 remark about price, and it came this week.")
        self.assertEqual(line([wk, wk]), "Since we listed, open house hosts have also passed on 2 remarks about price, all of them this week.")
        self.assertEqual(line([old, None]), "Since we listed, open house hosts have also passed on 2 remarks about price.")


class SmallLines(unittest.TestCase):
    """Lines that read like a template until they say exactly what is on the page."""

    def test_the_package_row_never_says_sent(self):
        for name in ("ledger_small.json", "ledger_busy.json"):          # the small listing records sends, the busy one does not
            t = email(load(name))
            numbers = t.split("THE NUMBERS")[1].split("WHAT PEOPLE ARE SAYING")[0]
            self.assertIn("new people on the package list", numbers)
            self.assertNotIn("sent the package", t)

    def test_a_package_sent_through_a_host_keeps_its_subject(self):
        d = load("ledger_small.json")
        m = Model(d, ID)
        x = next(c for c in m.direct if c["_via_host"])
        bits = people.line_bits(m, x, "disclosure", 2)
        self.assertTrue(bits[0].startswith("Package sent through the host"), bits)
        self.assertFalse(any(b.startswith("Sent through") for b in bits))
        other = next(c for c in m.direct if not c["_via_host"] and any(e["type"] == "disclosure_link_sent" for e in c["engagements"]))
        self.assertTrue(any(b.startswith("Sent ") for b in people.line_bits(m, other, "disclosure", 2)))    # everyone else keeps the short form

    def test_an_agent_with_no_name_on_file_is_not_said_to_have_withheld_it(self):
        d = load("ledger_busy.json")
        x = next(c for c in d["contacts"] if c.get("name_recorded") is False and c["kind"] == "agent")
        m = Model(d, ID)
        self.assertEqual(people.dname(m, m.byid[x["id"]]), "An agent whose name we do not have")
        self.assertEqual(people.dname(m, m.byid[x["id"]], lower=True), "an agent whose name we do not have")
        for mode in sr_render.MODES:
            self.assertNotIn("did not leave a name", text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"]))

    def test_the_reading_of_the_counts_names_the_team_once(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            t = email(load(name))
            self.assertIn("These counts are our team's reading of each conversation. ", t)
            self.assertNotIn("each conversation, as reported", t)

    def test_tries_are_explained_only_when_the_page_counts_them(self):
        d = load("ledger_small.json")
        t = email(d)
        counted = r"\d+ tr(y|ies)\b|Last tried|First tried|tried on \d"
        self.assertRegex(t.split("HOW WE COUNT")[0], counted)                    # someone on this page has been tried
        self.assertIn("Tries are the separate days we followed up since their last answer.", t)
        t = email(empty_listing(self))                                           # nobody to try: no word to explain
        self.assertNotRegex(t.split("HOW WE COUNT")[0], counted)
        self.assertIn("every date we tried", t)                                  # the line about the complete record is not a count
        self.assertNotIn("Tries are", t)
        self.assertIn("Still waiting: our latest follow-up to that person has not been answered. Follow-ups:", t)

    def test_no_final_answer_does_not_say_the_number_twice(self):
        d = load("ledger_busy.json")
        for c in d["contacts"]:
            if C.is_counted(c) and c["status"] == "replied":
                c["interest"] = "cold"
        clean(self, d)
        k = d["totals"]["open_no_final_answer"]
        self.assertGreater(k, 1)
        t = email(d)
        self.assertIn("No final answer (%d): all undecided." % k, t)
        self.assertNotIn("%d undecided" % k, t)
        mixed = email(load("ledger_busy.json"))                                  # a mix still gives each count
        self.assertRegex(mixed, r"No final answer \(\d+\): \d+ interested and \d+ undecided\.")

    def test_a_pointer_names_the_heading_this_page_prints(self):
        d = load("ledger_busy.json")                                             # agents and buyers toured: the heading says so
        m = Model(d, ID)
        self.assertEqual(people.list_title(m, "showings"), "Agents and buyers who toured the home")
        for mode in sr_render.MODES:
            t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"])
            self.assertIn("Agents and buyers who toured the home (", t)
            self.assertNotIn("ee Agents who showed the home", t)
            self.assertRegex(t, r"[Ss]ee Agents and buyers who toured the home")
        small = load("ledger_small.json")                                        # agents only: the heading and its pointers agree too
        self.assertEqual(people.list_title(Model(small, ID), "showings"), "Agents who showed the home")
        t = email(small)
        self.assertIn("Agents who showed the home (", t)
        self.assertNotIn("Agents and buyers who toured the home", t)

    def test_the_record_heading_fits_a_table_that_folds_older_weeks(self):
        import sr_checks.numbers as gate_numbers
        with open(gate_numbers.__file__, encoding="utf-8") as f:
            src = f.read()
        shape = re.search(r'Claim\("weeks_on_market".*?shapes=\[\(r"(.*?)" % N', src, re.S).group(1)
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            for mode in sr_render.MODES:
                t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"])
                self.assertRegex(t, r"\d+ weeks? on the market, week by week")
                self.assertNotIn("every week on the page", t)
                # the ship gate still finds the count in this heading and checks it against the ledger
                found = re.search(shape % r"(\d+)", t)
                self.assertIsNotNone(found, shape)
                self.assertEqual(int(found.group(1)), len(d["weeks"]))


if __name__ == "__main__":
    unittest.main()
