# -*- coding: utf-8 -*-
"""Tests for build_ledger.py (with sr_build_people, sr_notes, sr_ledger_checks) and snapshot_issue.py.

    python -m unittest tests.test_ledger        (from the skill folder)

The listing is synthetic: tests/fixtures/make_workbook.py writes the workbook, listing.json and a tag file
into a temp folder. The expected numbers below were worked out by hand from that workbook, person by person.
"""
import contextlib
import copy
import datetime
import io
import os
import shutil
import site
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))
sys.path.insert(0, os.path.join(HERE, "fixtures"))
if site.getusersitepackages() not in sys.path:
    sys.path.append(site.getusersitepackages())
import sr_contract as C  # noqa: E402
import sr_files as F  # noqa: E402
import sr_notes as N  # noqa: E402
import sr_ledger_checks as K  # noqa: E402
import build_ledger as B  # noqa: E402
import curation_tools as CT  # noqa: E402
import snapshot_issue as S  # noqa: E402
import make_workbook as W  # noqa: E402

try:
    import openpyxl  # noqa: F401
    HAVE_XLSX = True
except ImportError:
    HAVE_XLSX = False


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


def build(folder, **kw):
    kw.setdefault("report_date", W.REPORT_DATE)
    kw.setdefault("built_at", "2026-04-13T09:00:00-07:00")
    with quiet():
        return B.build(folder, **kw)


def person(d, cid):
    return next(c for c in d["contacts"] if c["id"] == cid)


class Notes(unittest.TestCase):
    def test_stock_phrases_are_read_by_rule(self):
        t, formulaic = N.infer_touches("no answer, left a vm. sent a text and email")
        self.assertTrue(formulaic)
        self.assertEqual([(x["channel"], x["outcome"]) for x in t], [("voicemail", "left_voicemail"), ("text", "sent"), ("email", "sent")])
        t, formulaic = N.infer_touches("hang up on me, sent a text and email")
        self.assertTrue(formulaic)
        self.assertEqual((t[0]["channel"], t[0]["outcome"]), ("call", "did_not_connect"))
        t, formulaic = N.infer_touches("sent email, number no longer in service")
        self.assertTrue(formulaic)
        self.assertEqual([(x["channel"], x["outcome"]) for x in t], [("call", "did_not_connect"), ("email", "sent")])

    def test_a_note_that_says_more_is_left_for_tagging(self):
        for text in ("no answer, left a vm. sent a text and email\n>she replied by text that her client is out of town",
                     "called about the price change, she will ask her clients", "sent the disclosure link"):
            self.assertFalse(N.infer_touches(text)[1], text)

    def test_rule_written_summaries_are_safe_for_a_seller(self):
        for t in (N.VOICEMAIL, N.NO_ANSWER, N.NOT_CONNECTED, N.TEXT, N.EMAIL) + tuple(N.COLUMN.values()):
            self.assertEqual(C.safe_text_problems(t["summary_safe"]), [], t["summary_safe"])

    def test_one_follow_up_per_channel_per_day(self):
        day = "2026-03-16"
        ts = [dict(N.VOICEMAIL, date=day, _auto=True), dict(N.TEXT, date=day, _auto=True),
              dict(N.NO_ANSWER, date=day, _auto=True), dict(N.TEXT, date=day, _auto=True), dict(N.EMAIL, date="2026-03-17", _auto=True)]
        kept, dropped = N.settle_day(ts)
        self.assertEqual(dropped, 2)
        self.assertEqual([(t["channel"], t["date"]) for t in kept], [("voicemail", day), ("text", day), ("email", "2026-03-17")])

    def test_labels_and_dead_numbers(self):
        self.assertTrue(N.is_label("refer to showing activity for updates"))
        self.assertTrue(N.is_label("Open house host"))
        self.assertFalse(N.is_label("open house host\n-clients are not interested"))
        self.assertTrue(N.dead_number("number not in service, sent an email"))
        self.assertFalse(N.dead_number("bad number, sent email"))


@unittest.skipUnless(HAVE_XLSX, "openpyxl is not installed")
class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="sr_ledger_")
        cls.folder = os.path.join(cls.tmp, "sample-glen")
        with quiet():
            cls.raw, cls.cur = W.prepare(cls.folder)
        cls.ledger, cls.problems, cls.info = build(cls.folder)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def variant(self, mutate=None, listing=None, **prepare_kw):
        """A copy of the listing folder with its curation (and listing) changed. Returns the folder."""
        folder = os.path.join(self.tmp, "v%d" % len(os.listdir(self.tmp)), "sample-glen")
        if prepare_kw:
            with quiet():
                W.prepare(folder, **prepare_kw)
        else:
            shutil.copytree(self.folder, folder)
        if mutate:
            cur = F.load_json(os.path.join(folder, "curation.json"))
            mutate(cur)
            F.save_json(os.path.join(folder, "curation.json"), cur)
        if listing:
            data = F.load_json(os.path.join(folder, "listing.json"))
            data.update(listing)
            F.save_json(os.path.join(folder, "listing.json"), data)
        return folder

    def entry_key(self, phrase, cur=None):
        for t in self.raw["tabs"]:
            for r in t["rows"]:
                for e in r["entries"]:
                    if phrase in e["text"]:
                        return e["key"]
        raise KeyError(phrase)


class Ledger(Base):
    def test_the_ledger_satisfies_the_contract(self):
        self.assertEqual(self.problems, [])
        self.assertEqual(C.validate_ledger(self.ledger, identity=C.load_identity()), [])
        R = self.ledger["report"]
        self.assertEqual((R["issue_number"], R["report_date"], R["week_start"], R["week_end"]), (5, "2026-04-13", "2026-04-06", "2026-04-12"))
        self.assertEqual((R["days_on_market"], R["weeks_on_market"]), (32, 5))
        self.assertEqual(sorted(self.ledger["meta"]), ["built_at", "slug"], "one build mode: no review state in a ledger")

    def test_headline_counts_worked_out_by_hand(self):
        T = self.ledger["totals"]
        want = {"contact_records": 13, "contacts": 10, "buyers_via_agent": 2, "team_side_people": 1, "contacted": 10, "not_yet_contacted": 0,
                "replied": 8, "awaiting_reply": 2, "awaiting_reply_3plus_attempts": 1, "awaiting_reply_answered_before": 1,
                "touches_outbound": 35, "outbound_person_days": 15, "outbound_distinct_days": 13, "replies_inbound": 16,
                "calls_not_connected": 4, "touches_direction_not_recorded": 1, "keybox_showings": None, "agent_reported_tours": 5,
                "inquiries": 3, "disclosure_contacts": 5, "disclosure_shared_buyers": 2, "open_house_sessions": 10,
                "open_house_sessions_without_count": 1, "open_house_sessions_no_visitors": 2, "open_house_groups": 22,
                "open_house_disclosure_requests": 1, "offers": 1, "people_with_feedback": 7, "conversations_with_feedback": 10}
        self.assertEqual(dict((k, T[k]) for k in want), want)
        self.assertEqual(T["team_side_set_aside"], {"people": 1, "touches_outbound": 3, "replies_inbound": 0})
        self.assertEqual(T["by_status"], {"not_yet_contacted": 0, "awaiting_reply": 2, "replied": 4, "passed": 3, "writing_offer": 0, "offer_submitted": 1})

    def test_this_week_and_the_weeks_before(self):
        weeks = self.ledger["weeks"]
        self.assertEqual([(w["n"], w["start"], w["label"]) for w in weeks][0], (1, "2026-03-09", "Mar 9 to Mar 15"))
        self.assertEqual(weeks[0]["days_listed_in_week"], 4)
        w = weeks[-1]
        self.assertTrue(w["is_current"])
        got = dict((k, w[k]) for k in ("touches_outbound", "outbound_people", "outbound_distinct_days", "replies_inbound", "conversations_with_feedback",
                                         "agent_reported_tours", "inquiries", "offers", "open_house_sessions", "open_house_groups", "keybox_showings"))
        self.assertEqual(got, {"touches_outbound": 15, "outbound_people": 4, "outbound_distinct_days": 5, "replies_inbound": 9,
                               "conversations_with_feedback": 4, "agent_reported_tours": 1, "inquiries": 3, "offers": 1,
                               "open_house_sessions": 2, "open_house_groups": 3, "keybox_showings": None})
        self.assertEqual(weeks[3]["list_price"], 1175000, "the price changed on the Wednesday: most days of that week are at the new price")
        self.assertEqual(sum(x["touches_outbound"] for x in weeks), 35)

    def test_what_people_are_saying(self):
        pt = self.ledger["pricing_tally"]
        self.assertEqual((pt["people_with_feedback"], pt["too_high"], pt["fair_or_positive"], pt["not_raised"]), (7, 2, 1, 4))
        self.assertEqual(pt["open_house_price_remarks"], [{"date": "2026-03-29", "reaction": "too_high", "softened": True,
                                                          "remark_safe": "One open house group felt the price was above what the market supports."}])
        rows = dict((r["key"], (r["people"], r["new_this_week"])) for r in self.ledger["themes_tally"]["rows"])
        self.assertEqual(rows, {"still_deciding": (2, 0), "chose_another_home": (2, 2), "stairs": (1, 0), "condition_disclosures": (1, 0), "buyer_timing": (1, 1)})
        self.assertEqual(self.ledger["liked_tally"]["people"], 5)
        self.assertEqual([p["price"] for p in self.ledger["price_periods"]], [1195000, 1175000])
        first, second = self.ledger["price_periods"]
        self.assertEqual((first["days"], first["agent_reported_tours"], first["price_too_high"], first["price_fair_or_positive"], first["offers"]), (20, 4, 2, 1, 0))
        self.assertEqual((second["days"], second["agent_reported_tours"], second["price_too_high"], second["offers"]), (12, 1, 0, 1))

    def test_per_person_follow_up_arithmetic(self):
        f = person(self.ledger, "c001")["followup"]
        self.assertEqual((f["outbound_touches"], f["outbound_days"], f["replies"], f["first_touch_date"], f["last_touch_date"]), (8, 3, 3, "2026-03-13", "2026-04-07"))
        self.assertEqual(C.fmt_followup(person(self.ledger, "c001")["touches"]), "3 days of follow-up (3 calls, 3 texts, 2 emails)")
        zen = person(self.ledger, "c013")
        self.assertEqual((zen["status"], zen["followup"]["outbound_days"], zen["followup"]["tries_since_last_answer"]), ("awaiting_reply", 3, 3))
        bart = person(self.ledger, "c009")
        self.assertEqual((bart["status"], bart["followup"]["replies"], bart["followup"]["tries_since_last_answer"]), ("awaiting_reply", 1, 1))

    def test_the_same_attempt_typed_on_two_tabs_counts_once(self):
        c = person(self.ledger, "c001")
        on_16 = [t for t in c["touches"] if t["date"] == "2026-03-16"]
        self.assertEqual([t["channel"] for t in on_16], ["voicemail", "text", "email"])
        self.assertEqual(self.info["stats"]["touches_deduped"], 3)

    def test_the_date_columns_fill_what_the_notes_do_not_cover(self):
        c = person(self.ledger, "c001")
        self.assertIn(("2026-04-07", "text", "Sent a text. No note was kept."), [(t["date"], t["channel"], t["summary_safe"]) for t in c["touches"]])
        w = person(self.ledger, "c007")
        on_9 = [t for t in w["touches"] if t["date"] == "2026-04-09"]
        self.assertEqual([(t["channel"], t["direction"]) for t in on_9], [("call", "inbound")], "a Call date on a day she answered: they spoke by phone")
        self.assertEqual((self.info["stats"]["touches_from_columns_only"], self.info["stats"]["reply_channel_from_column"]), (1, 1))

    def test_nothing_after_the_week_end_is_counted(self):
        we = self.ledger["report"]["week_end"]
        for c in self.ledger["contacts"]:
            self.assertTrue(all(t["date"] <= we for t in c["touches"]))
            self.assertTrue(all(f["date"] <= we for f in c["feedback_log"]))
        since = self.ledger["report"]["since_week_closed"]
        self.assertEqual(since["through"], "2026-04-13")
        self.assertEqual([(i["date"], i["kind"], i["contact_id"], i["offer_related"]) for i in since["items"]],
                         [("2026-04-13", "touch", None, False)] * 3 + [("2026-04-13", "touch", "c001", True)])
        for i in since["items"]:                                    # each says what kind of touch it was, for the one line per person per day
            self.assertIn(i.get("direction"), ("outbound", "inbound"), i)
            self.assertTrue(i.get("channel"), i)
        self.assertNotIn("c014", [c["id"] for c in self.ledger["contacts"]], "someone first logged on Monday is not in last week's counts")
        self.assertEqual(person(self.ledger, "c001")["followup"]["last_touch_date"], "2026-04-07")

    def test_a_tighter_through_date_leaves_later_entries_for_the_next_issue(self):
        d, problems, info = build(self.folder, through="2026-04-12")
        self.assertEqual(problems, [])
        self.assertEqual(d["report"]["since_week_closed"]["items"], [])
        self.assertEqual(d["totals"]["touches_outbound"], 35)
        self.assertTrue(any("left for the next issue" in s for s in d["data_quality"]))

    def test_hosts_are_on_our_side_of_the_table(self):
        host = person(self.ledger, "c005")
        self.assertTrue(host["is_open_house_host"] and host["team_side"])
        self.assertEqual(host["engagements"], [], "a host's own row on the disclosure tab is not a disclosure contact")
        self.assertEqual(len(host["touches"]), 3)
        self.assertEqual(self.ledger["team_side"], [{"name_short": "Leocadia M.", "role": "open house host", "sessions_hosted": 9, "contact_id": "c005"},
                                                    {"name_short": "Octavian B.", "role": "open house host", "sessions_hosted": 1, "contact_id": None}])
        self.assertEqual([o["host_contact_id"] for o in self.ledger["open_houses"]].count("c005"), 9)

    def test_buyers_an_agent_brought_are_listed_under_the_agent(self):
        for cid in ("c003", "c004"):
            b = person(self.ledger, cid)
            self.assertEqual((b["represented_by"], b["status"], b["touches"], b["name_short"], b["name_recorded"]), ("c002", "through_agent", [], "Client of Thaddeus O.", False))
            self.assertEqual([e["type"] for e in b["engagements"]], ["disclosure_shared_by_agent"])

    def test_the_dead_number_flag_and_calls_that_did_not_connect(self):
        ig = person(self.ledger, "c010")
        self.assertTrue(ig["phone_out_of_service"])
        self.assertEqual(ig["followup"]["calls_not_connected"], 3)
        self.assertEqual(ig["status"], "passed", "later outreach does not move someone who passed back to waiting")
        self.assertTrue(any("Ignatius D." in s and "out of service" in s for s in self.ledger["data_quality"]))
        self.assertEqual(len([c for c in self.ledger["contacts"] if c["phone_out_of_service"]]), 1)

    def test_harsh_wording_is_softened_and_the_substance_stays(self):
        ig = person(self.ledger, "c010")
        self.assertTrue(ig["softened"])
        self.assertEqual(ig["price_reaction"], "too_high")
        blob = F.dumps(self.ledger).lower()
        for word in ("awful", "way overpriced", "hang up on me", "6505550", "@example.com", "delacroix"):
            self.assertNotIn(word, blob, "raw wording, contact details and full names stay out of the ledger")

    def test_a_row_with_no_name_and_no_showing_time_is_an_inquiry(self):
        c = person(self.ledger, "c011")
        self.assertEqual((c["name_short"], c["name_recorded"]), ("Agent, name not recorded", False))
        self.assertEqual([(e["type"], e["date"]) for e in c["engagements"]], [("inquiry", "2026-04-06")])
        self.assertEqual((c["followup"]["outbound_touches"], c["followup"]["replies"], c["status"]), (0, 1, "passed"))

        def drop(cur):
            del cur["people"]["c011"]["engagements"]
        d, problems, _ = build(self.variant(drop))
        self.assertEqual(problems, [])
        self.assertEqual([(e["type"], e["date"], e["date_quality"]) for e in person(d, "c011")["engagements"]], [("inquiry", "2026-04-06", "approximate")])
        self.assertEqual(d["totals"]["agent_reported_tours"], 5, "an undated row on the showing tab is never counted as a tour by default")
        self.assertTrue(any("no showing date" in s and "Agent, name not recorded" in s for s in d["data_quality"]))

    def test_open_houses_keep_no_count_apart_from_zero(self):
        oh = self.ledger["open_houses"]
        self.assertEqual([(o["date"], o["groups"], o["counted_unit"], o["groups_source"]) for o in oh if o["groups"] in (None, 0)],
                         [("2026-03-14", None, "groups", "not_recorded"), ("2026-03-21", 0, "visitors", "parsed_from_prose"), ("2026-04-04", 0, "visitors", "parsed_from_prose")])
        undated = [o for o in oh if o["date_quality"] == "approximate"]
        self.assertEqual(len(undated), 1)
        self.assertIn("No date is typed", undated[0]["date_note"])
        self.assertEqual([o["counted_unit"] for o in oh if o["groups"]], ["parties", "guests", "groups", "groups", "visitors", "visitors", "visitors"])
        self.assertEqual(next(o for o in oh if o["date"] == "2026-04-05")["groups_source"], "sheet_column")
        self.assertEqual(next(o for o in oh if o["date"] == "2026-03-28")["recap_safe"], "1 group.")

    def test_offers_and_the_offer_watch(self):
        o = self.ledger["offers"][0]
        self.assertEqual((o["id"], o["contact_id"], o["agent_short"], o["brokerage"], o["price"], o["pct_of_list"], o["state"]),
                         ("o1", "c012", "Persephone A.", "Tidewater Homes", 1150000, 97.9, "received"))
        self.assertNotIn("source_row", o)
        self.assertEqual([(w["contact_id"], w["lead_state"]) for w in self.ledger["offer_watch"]], [("c001", "live")])

    def test_the_21_and_30_day_rules_four_weeks_later(self):
        d, problems, _ = build(self.folder, report_date="2026-05-11", through="2026-05-10")
        self.assertEqual(problems, [])
        self.assertEqual([(w["contact_id"], w["lead_state"], w["days_since_last_touch"]) for w in d["offer_watch"]], [("c001", "earlier_interest", 27)])
        T = d["totals"]
        self.assertEqual((T["awaiting_reply"], T["awaiting_reply_quiet"]), (3, 1))
        self.assertEqual((T["open_no_final_answer"], T["open_no_final_answer_quiet"]), (4, 2), "exactly 30 days without contact is not quiet")
        self.assertIn("c014", [c["id"] for c in d["contacts"]])
        self.assertEqual(d["report"]["weeks_on_market"], 9)

    def test_the_listing_block_is_seller_safe(self):
        L = self.ledger["listing"]
        for k in ("sheet", "keybox_number", "listing_folder", "numbering", "tracking"):
            self.assertNotIn(k, L)
        self.assertEqual((L["list_price"], L["seller_first_names"]), (1175000, ["Pat", "Sam"]))
        self.assertEqual(self.ledger["sources_used"], [{"kind": "activity_sheet_live", "label": "Live activity sheet, exported to xlsx", "as_of": "2026-04-13"}])

    def test_data_quality_is_plain_and_safe(self):
        dq = self.ledger["data_quality"]
        self.assertTrue(all(isinstance(s, str) and s.strip() for s in dq))
        self.assertTrue(any("14 note(s) were classified by rule" in s and "19 were read from the wording" in s for s in dq))
        self.assertFalse(any(C.has_dash(s) for s in dq))


class TagsAndOverrides(Base):
    def test_a_sheet_column_beats_claudes_reading(self):
        c = person(self.ledger, "c001")
        self.assertEqual(self.cur["people"]["c001"]["tags"]["interest"]["value"], "cold")
        self.assertEqual((c["interest"], c["offer_intent"], c["next_followup_date"], c["price_reaction"]), ("warm", "maybe", "2026-04-15", "too_high"))
        self.assertEqual(self.info["provenance"]["c001"]["interest"], "sheet_column")
        self.assertNotIn("tag_source", c, "where a reading came from stays out of the ledger")
        self.assertNotIn("tag_sources", c)

    def test_a_persons_correction_beats_the_sheet_until_the_sheet_changes(self):
        def corrected(seen):
            def go(cur):
                cur["people"]["c001"]["tags"]["interest"] = {"value": "cold", "provenance": "corrected_by_operator", "corrected_by": "Adrian",
                                                             "corrected_on": "2026-04-13", "sheet_value_seen": seen}
            return go
        d, problems, info = build(self.variant(corrected("warm")))
        self.assertEqual(problems, [])
        self.assertEqual((person(d, "c001")["interest"], info["provenance"]["c001"]["interest"]), ("cold", "corrected_by_operator"))
        d, problems, info = build(self.variant(corrected("hot")))              # the sheet said hot when corrected and says warm now
        self.assertEqual((person(d, "c001")["interest"], info["provenance"]["c001"]["interest"]), ("warm", "sheet_column"))
        self.assertTrue(any("gave way to a newer value" in s for s in d["data_quality"]))
        self.assertTrue(any("gave way to a newer value" in s for s in info["notes_for_operator"]["worth_a_glance"]))

    def test_a_price_tag_with_no_dated_remark_lands_on_the_latest_conversation(self):
        key = self.entry_key("price feels high")

        def missed(cur):
            cur["entries"][key]["feedback"]["price_reaction"] = "not_raised"
        d, problems, info = build(self.variant(missed))
        self.assertEqual(problems, [])
        c = person(d, "c001")
        self.assertEqual((c["price_reaction"], c["feedback_log"][-1]["price_reaction"], info["provenance"]["c001"]["price_reaction"]), ("too_high", "too_high", "sheet_column"))
        self.assertEqual(d["pricing_tally"]["too_high"], 2)

        def overruled(cur):
            cur["people"]["c010"]["tags"]["price_reaction"] = {"value": "not_raised", "provenance": "corrected_by_operator", "corrected_by": "Graeham", "corrected_on": "2026-04-13"}
        d, problems, _ = build(self.variant(overruled))
        self.assertEqual(problems, [])
        self.assertEqual((d["pricing_tally"]["too_high"], d["pricing_tally"]["not_raised"]), (1, 5))

    def test_notes_on_a_buyers_row_are_read_into_the_agents_log(self):
        folder = self.variant(edits={("glide", 2, 7): datetime.datetime(2026, 4, 2)})        # a Call date typed on an "Invited by" row
        d, problems, info = build(folder)
        self.assertEqual(problems, [])
        self.assertEqual(person(d, "c003")["touches"], [])
        agent = person(d, "c002")
        self.assertIn(("2026-04-02", "call", "outbound"), [(t["date"], t["channel"], t["direction"]) for t in agent["touches"]])
        self.assertEqual(d["totals"]["touches_outbound"], 36)
        self.assertTrue(any("follow-up with that buyer is follow-up with the agent" in s for s in d["data_quality"]))

    def test_a_price_change_after_the_report_date_is_left_out(self):
        later = copy.deepcopy(W.LISTING["price_history"]) + [{"date": "2026-04-20", "price": 1150000, "event": "price_change"}]
        d, problems, _ = build(self.variant(listing={"price_history": later, "list_price": 1150000}))
        self.assertEqual(problems, [])
        self.assertEqual(([e["price"] for e in d["listing"]["price_history"]], d["listing"]["list_price"]), ([1195000, 1175000], 1175000))

    def test_tracking_says_what_is_recorded_and_null_is_not_zero(self):
        self.assertIsNone(self.ledger["totals"]["keybox_showings"])
        self.assertIsNone(self.ledger["weeks"][0]["disclosure_opened"])
        d, problems, _ = build(self.variant(listing={"tracking": {"keybox_showings": True, "disclosure_sent": True, "disclosure_opened": True},
                                                      "tracking_since": {"disclosure_opened": "2026-03-23"}}))
        self.assertEqual(problems, [])
        self.assertEqual((d["totals"]["keybox_showings"], d["totals"]["agent_reported_tours"]), (5, 0), "the showing tab is the key-box log on this listing")
        self.assertEqual([w["disclosure_opened"] for w in d["weeks"]], [None, None, 0, 0, 0])
        self.assertEqual((d["totals"]["disclosure_opened_confirmed"], d["totals"]["disclosure_link_sent"]), (0, 0))

    def test_machine_events_become_engagements(self):
        folder = self.variant(listing={"tracking": {"keybox_showings": True, "disclosure_sent": False, "disclosure_opened": True}})
        F.save_json(os.path.join(folder, "events.json"), {"schema_version": 1, "slug": "sample-glen",
                    "fetched": [{"asked_on": "2026-04-13", "source": "glide_email", "window": ["2026-03-12", "2026-04-13"]}],
                    "events": [{"id": "e1", "type": "disclosure_opened", "date": "2026-03-20", "contact_id": "c002", "is_team_side": False},
                               {"id": "e2", "type": "disclosure_opened", "date": "2026-03-21", "contact_id": "c005", "is_team_side": True},
                               {"id": "e3", "type": "keybox_showing_start", "date": "2026-03-14", "contact_id": "c001", "is_team_side": False},
                               {"id": "e4", "type": "keybox_showing_end", "date": "2026-03-14", "contact_id": "c001", "is_team_side": False}]})
        d, problems, _ = build(folder)
        self.assertEqual(problems, [])
        self.assertIn(("disclosure_opened", "2026-03-20"), [(e["type"], e["date"]) for e in person(d, "c002")["engagements"]])
        self.assertEqual(len([e for e in person(d, "c001")["engagements"] if e["type"] == "keybox_showing"]), 1, "one visit, not two")
        self.assertEqual(d["totals"]["disclosure_opened_confirmed"], 1, "the host's own view is team side")
        self.assertIsNone(d["totals"]["disclosure_link_sent"], "link sent is not recorded for this listing")
        self.assertIn("glide_email", [s["kind"] for s in d["sources_used"]])

    def test_the_market_block_is_recomputed_from_its_sales(self):
        folder = self.variant()
        sales = [{"address": "1 Fixture Way", "days_to_contract": n, "used_in_average": n is not None} for n in (10, 20, 40, None)]
        F.save_json(os.path.join(folder, "market.json"), {"as_of": "2026-04-10", "data_through": "2026-04-10", "refreshed_for_this_issue": True,
                    "scope": "Synthetic sales", "source": "Synthetic", "method": "List date to contract date.",
                    "sample": {"exclusion_reason": "No contract date."}, "days_to_contract": {}, "subject_on_report_date": {},
                    "sales": sales, "statement_safe": "Three synthetic sales."})
        d, problems, _ = build(folder)
        self.assertEqual(problems, [])
        m = d["market"]
        self.assertEqual((m["sample"]["closed"], m["sample"]["used"], m["sample"]["excluded"]), (4, 3, 1))
        self.assertEqual((m["days_to_contract"]["average"], m["days_to_contract"]["median"], m["days_to_contract"]["values_sorted"]), (23, 20, [10, 20, 40]))
        self.assertEqual((m["subject_on_report_date"]["days_on_market"], m["subject_on_report_date"]["sales_under_contract_by_that_day"]), (32, 2))


class HardStops(Base):
    def stopped(self, mutate=None, **kw):
        d, problems, _ = build(self.variant(mutate, **kw))
        self.assertIsNone(d, "a build with a problem writes no ledger")
        return problems

    def test_a_note_nobody_has_read_stops_the_build(self):
        key = self.entry_key("called about the price change")
        problems = self.stopped(lambda cur: cur["entries"].pop(key))
        self.assertEqual(len(problems), 1)
        self.assertIn("has not been read into curation.json yet", problems[0])
        self.assertIn(key, problems[0])

    def test_an_undated_line_must_be_accounted_for(self):
        key = self.entry_key("2-3 buyers of mine")
        problems = self.stopped(lambda cur: cur["entries"].pop(key))
        self.assertTrue(any("undated line is not accounted for" in p for p in problems))

    def test_a_row_nobody_placed_stops_the_build(self):
        problems = self.stopped(lambda cur: cur["people"].pop("c008"))
        self.assertTrue(any("is not accounted for" in p and "Glide View Activity" in p for p in problems))

    def test_an_offer_row_must_be_in_curation(self):
        problems = self.stopped(lambda cur: cur["offers"].clear())
        self.assertTrue(any("offers tab" in p for p in problems))

    def test_an_open_house_session_with_no_date_stops_the_build(self):
        def drop(cur):
            for k in [k for k, v in cur["open_houses"].items() if v.get("date_quality") == "approximate"]:
                del cur["open_houses"][k]
        problems = self.stopped(drop)
        self.assertTrue(any("has no date typed" in p for p in problems))

    def test_unsafe_wording_in_curation_stops_the_build(self):
        key = self.entry_key("called about the price change")

        def leak(cur):
            cur["entries"][key]["touches"][0]["summary_safe"] = "Called her at 650-555-0101. I left a message."
        problems = self.stopped(leak)
        self.assertTrue(all(p.startswith("curation.json:") for p in problems))
        self.assertTrue(any("phone number" in p for p in problems) and any("first-person" in p for p in problems))

    def test_one_person_is_never_shown_two_ways(self):
        def both(cur):
            cur["people"]["c012"]["tags"]["interest"] = {"value": "passed", "provenance": "claude"}
        problems = self.stopped(both)
        self.assertTrue(any("never shown both ways" in p for p in problems))

    def test_passed_with_no_dated_contact_is_not_shown_as_an_answer(self):
        def ghost(cur):
            for k in [k for k in cur["entries"] if k.split("/")[0] in cur["people"]["c011"]["rows"]]:
                cur["entries"][k] = {"touches": [], "feedback": None, "provenance": "claude"}
        folder = self.variant(ghost, edits={("showing", 3, 9): None})        # no Call date either
        d, problems, _ = build(folder)
        self.assertEqual(problems, [])
        self.assertEqual((person(d, "c011")["status"], person(d, "c011")["interest"]), ("not_yet_contacted", "unknown"))
        self.assertTrue(any("is marked passed, but no dated" in s for s in d["data_quality"]))

    def test_numbers_that_do_not_foot_stop_the_build(self):
        real = K.data_quality

        def tamper(d, *args):
            d["totals"]["contacted"] -= 1
            d["weeks"][1]["touches_outbound"] += 2
            return real(d, *args)
        K.data_quality = tamper
        try:
            d, problems, _ = build(self.folder)
        finally:
            K.data_quality = real
        self.assertIsNone(d)
        self.assertTrue(any(p.startswith("does not foot: contacts = contacted + not yet contacted") for p in problems))
        self.assertTrue(any(p.startswith("does not foot: weeks add up to the total for touches_outbound") for p in problems))

    def test_the_command_line_writes_nothing_when_it_stops(self):
        key = self.entry_key("sent the disclosure link")
        folder = self.variant(lambda cur: cur["entries"].pop(key))
        with quiet():
            code = B.main(["--folder", folder, "--report-date", W.REPORT_DATE])
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(os.path.join(folder, "ledger.json")))
        with quiet():
            self.assertEqual(B.main(["--folder", self.variant(), "--report-date", W.REPORT_DATE, "--source", "pasted_notes|Notes pasted in by the operator|2026-04-13"]), 0)
        with self.assertRaises(SystemExit), quiet():
            B.main(["--folder", self.folder, "--report-date", "2026-04-14"])


class Snapshot(Base):
    def ready(self):
        """A folder with ledger.json written and a folder of rendered files beside it."""
        folder = self.variant()
        d, problems, info = build(folder)
        self.assertEqual(problems, [])
        F.save_json(os.path.join(folder, "ledger.json"), d)
        F.save_json(os.path.join(folder, "notes_for_operator.json"), info["notes_for_operator"])
        render = os.path.join(folder, "render")
        os.makedirs(render)
        for name, text in (("email.html", "<html>synthetic email</html>"), ("link.html", "<html>synthetic link copy</html>")):
            with open(os.path.join(render, name), "w", encoding="utf-8") as f:
                f.write(text)
        return folder, d, render

    def test_an_issue_is_kept_with_hashes_and_can_be_rebuilt(self):
        folder, d, render = self.ready()
        code, m, msgs = S.freeze(folder, render)
        self.assertEqual(code, 0, msgs)
        target = os.path.join(folder, "issues", "05")
        self.assertEqual(sorted(os.listdir(target)), ["email.html", "ledger.json", "link.html", "manifest.json", "notes_for_operator.json"])
        self.assertFalse(os.path.exists(os.path.join(target, "draft")), "there is one build and no draft folder")
        self.assertEqual((m["issue_number"], m["report_date"]), (5, "2026-04-13"))
        self.assertNotIn("build_kind", m)
        self.assertNotIn("tag_review", m)
        self.assertEqual(m["ledger_sha256"], F.sha256_file(os.path.join(target, "ledger.json")))
        self.assertEqual(F.load_json(os.path.join(target, "ledger.json")), d)
        self.assertEqual(m["email_bytes"], os.path.getsize(os.path.join(render, "email.html")))
        with open(os.path.join(render, "email.html"), "w", encoding="utf-8") as f:
            f.write("<html>the email after a correction</html>")
        code, m2, msgs = S.freeze(folder, render)
        self.assertEqual(code, 0, "a rebuild after a correction replaces the files")
        with open(os.path.join(target, "email.html"), encoding="utf-8") as f:
            self.assertIn("after a correction", f.read())

    def test_nothing_waits_on_a_person_confirming_anything(self):
        folder, d, render = self.ready()
        self.assertEqual(sorted(d["meta"]), ["built_at", "slug"])
        self.assertEqual(S.freeze(folder, render)[0], 0)
        self.assertFalse(hasattr(CT, "confirm"))
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(os.path.abspath(S.__file__)), "sr_review_page.py")))

    def test_an_issue_recorded_as_sent_is_not_replaced(self):
        folder, d, render = self.ready()
        self.assertEqual(S.next_number(folder, W.REPORT_DATE)[0], 5)
        code, m, msgs = S.freeze(folder, render)
        self.assertEqual(code, 0, msgs)
        m3 = S.record(folder, 5, gmail_draft_id="draft-123")
        self.assertEqual((m3["delivery"]["gmail_draft_id"], m3["delivery"]["sent_on"]), ("draft-123", None))
        self.assertEqual(S.freeze(folder, render)[0], 0, "a Gmail draft alone does not lock the issue")
        S.record(folder, 5, gmail_draft_id="draft-123", sent_on="2026-04-13")
        path = os.path.join(folder, "issues", "05", "manifest.json")
        before = F.sha256_file(path)
        with open(os.path.join(render, "email.html"), "w", encoding="utf-8") as f:
            f.write("<html>a different email</html>")
        code, m2, msgs = S.freeze(folder, render)
        self.assertEqual(code, S.EXIT_REFUSED)
        self.assertTrue(any("recorded as sent" in x for x in msgs))
        self.assertEqual(F.sha256_file(path), before)
        with open(os.path.join(folder, "issues", "05", "email.html"), encoding="utf-8") as f:
            self.assertIn("synthetic email", f.read())
        self.assertEqual(S.next_number(folder, W.REPORT_DATE)[0], 5, "a rebuild for the same report date keeps its number")
        self.assertEqual(S.next_number(folder, "2026-04-20")[0], 6)
        nxt, problems, _ = build(folder, report_date="2026-04-20", through="2026-04-19")
        self.assertEqual(problems, [])
        self.assertEqual(nxt["report"]["issue_number"], 6)
        code, m4, msgs = S.freeze(folder, render, replace_sent=True)
        self.assertEqual(code, 0, msgs)
        self.assertIsNone(m4["delivery"]["sent_on"])

    def test_an_email_over_the_limit_is_not_kept(self):
        folder, d, render = self.ready()
        with open(os.path.join(render, "email.html"), "w", encoding="utf-8") as f:
            f.write("x" * C.LIMITS["email_max_bytes"])
        code, m, msgs = S.freeze(folder, render)
        self.assertEqual(code, 2)
        self.assertTrue(any("Gmail clips" in x for x in msgs))
        self.assertFalse(os.path.exists(os.path.join(folder, "issues", "05", "manifest.json")))

    def test_a_rebuild_without_the_gmail_safe_copy_removes_the_old_one(self):
        folder, d, render = self.ready()
        with open(os.path.join(render, "email_gmail.html"), "w", encoding="utf-8") as f:
            f.write("<html>synthetic gmail copy</html>")
        self.assertEqual(S.freeze(folder, render)[0], 0)
        target = os.path.join(folder, "issues", "05")
        self.assertTrue(os.path.exists(os.path.join(target, "email_gmail.html")))
        os.remove(os.path.join(render, "email_gmail.html"))
        with open(os.path.join(render, "email.html"), "w", encoding="utf-8") as f:
            f.write("<html>the email after a correction</html>")
        code, m, msgs = S.freeze(folder, render)
        self.assertEqual(code, 0, msgs)
        self.assertFalse(os.path.exists(os.path.join(target, "email_gmail.html")))
        self.assertNotIn("email_gmail.html", [x["name"] for x in m["files"]])
        self.assertIsNone(m["email_gmail_bytes"])
        self.assertTrue(any("old one was removed" in x for x in msgs))

    def test_there_must_be_an_email_to_keep(self):
        folder, d, render = self.ready()
        os.remove(os.path.join(render, "email.html"))
        code, m, msgs = S.freeze(folder, render)
        self.assertEqual(code, 2)
        self.assertTrue(any("no rendered email.html" in x for x in msgs))


class OptionalSections(Base):
    """The extras print only when they were read for this issue, and one sale never shows two day counts."""

    def views(self, folder, weeks):
        rows = [{"week_start": w, "portal": "Zillow", "views": 400 + 100 * i, "saves": 10 + i, "counts": "since_listing",
                 "as_of": w, "source": "operator"} for i, w in enumerate(weeks)]
        F.save_json(os.path.join(folder, "online_views.json"), {"schema_version": 1, "slug": "sample-glen", "rows": rows, "lookups": []})

    def test_online_views_print_only_when_read_for_this_issue(self):
        folder = self.variant()
        self.views(folder, ["2026-03-23", "2026-03-30"])                    # readings from earlier weeks only
        d, problems, info = build(folder)
        self.assertEqual(problems, [])
        self.assertIsNone(d["online"])
        n = info["notes_for_operator"]
        self.assertTrue(any("not read for this issue" in x for x in (n.get("worth_a_glance") or []) + (n.get("also_noted") or [])), n)
        self.views(folder, ["2026-03-30", "2026-04-06"])                    # one taken for this issue's week
        d, problems, info = build(folder)
        self.assertEqual(problems, [])
        self.assertIsNotNone(d["online"])
        d, problems, info = build(folder, online=False)                     # --no-online
        self.assertEqual(problems, [])
        self.assertIsNone(d["online"])

    def test_one_sale_one_day_count_even_when_the_chart_came_later(self):
        nearby = {"homes": [{"address": "52 Sample Birch Dr", "status": "sold", "days_on_market": 28},
                            {"address": "9 Sample Cedar Ct", "status": "pending", "days_on_market": 15},
                            {"address": "3 Sample Same Rd", "status": "sold", "days_on_market": 20}]}
        market = {"sales": [{"address": "52 SAMPLE BIRCH DR", "days_to_contract": 26}, {"address": "3 Sample Same Rd", "days_to_contract": 20},
                            {"address": "9 Sample Cedar Ct", "days_to_contract": 4}]}
        lines = B.one_day_count(nearby, market)
        days = dict((h["address"], h["days_on_market"]) for h in nearby["homes"])
        self.assertEqual(days, {"52 Sample Birch Dr": None, "9 Sample Cedar Ct": 15, "3 Sample Same Rd": 20})
        self.assertEqual(len(lines), 1)
        self.assertIn("26 days", lines[0])
        self.assertEqual(B.one_day_count(nearby, None), [])


class NotesForOperator(Base):
    def test_at_most_five_plain_lines_and_never_in_the_ledger(self):
        d, problems, info = build(self.folder, glance=["The count of tours here is 3. The team's status email says 4, because it counts a phone inquiry as a tour."])
        self.assertEqual(problems, [])
        notes = info["notes_for_operator"]
        self.assertLessEqual(len(notes["worth_a_glance"]), 5)
        self.assertIn("status email says 4", notes["worth_a_glance"][0], "what Claude noticed for this issue leads")
        text = " ".join(notes["worth_a_glance"] + notes["also_noted"])
        self.assertNotRegex(text.lower(), r"\btag(s|ged|ging)?\b|\breview|\bconfirm")
        self.assertFalse(C.has_dash(text))
        self.assertNotIn("notes_for_operator", d)
        self.assertFalse(any("status email says 4" in s for s in d["data_quality"]))

    def test_what_claude_was_unsure_of_is_listed_until_the_operator_corrects_it(self):
        def unsure(cur):
            cur["people"]["c009"]["unsure"] = "Could not tell whether Bartholomew N. toured the home or only asked about it."
        folder = self.variant(unsure)
        d, problems, info = build(folder)
        self.assertEqual(problems, [])
        self.assertIn("Could not tell whether Bartholomew N. toured the home or only asked about it.", info["notes_for_operator"]["worth_a_glance"])
        self.assertNotIn("unsure", person(d, "c009"))
        cur = F.load_json(os.path.join(folder, "curation.json"))
        CT.correct(cur, {"people": {"c009": {"interest": "cold"}}}, self.raw, by="Graeham", on="2026-04-13")
        F.save_json(os.path.join(folder, "curation.json"), cur)
        d, problems, info = build(folder)
        self.assertEqual(problems, [])
        self.assertFalse(any("Could not tell" in s for s in info["notes_for_operator"]["worth_a_glance"]))
        self.assertEqual(person(d, "c009")["interest"], "cold")

    def test_the_command_line_writes_the_notes_beside_the_ledger(self):
        folder = self.variant()
        with quiet():
            self.assertEqual(B.main(["--folder", folder, "--report-date", W.REPORT_DATE, "--glance", "One line from Claude."]), 0)
        notes = F.load_json(os.path.join(folder, "notes_for_operator.json"))
        self.assertEqual(notes["worth_a_glance"][0], "One line from Claude.")
        self.assertEqual((notes["issue_number"], notes["report_date"]), (5, W.REPORT_DATE))


if __name__ == "__main__":
    unittest.main()
