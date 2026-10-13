# -*- coding: utf-8 -*-
"""Tests for curation_tools.py and sr_correct.py: Claude's work list, merging Claude's reading of the notes,
and the one step that applies what the operator said after reading the report.

    python -m unittest tests.test_curation      (from the skill folder)

Synthetic data only (tests/fixtures/make_workbook.py), written to a temp folder.
"""
import contextlib
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
import build_ledger as B  # noqa: E402
import curation_tools as CT  # noqa: E402
import intake_sheet  # noqa: E402
import make_workbook as W  # noqa: E402

try:
    import openpyxl  # noqa: F401
    HAVE_XLSX = True
except ImportError:
    HAVE_XLSX = False

STOCK = "no answer, left a vm. sent a text and email"


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


def build(folder, **kw):
    kw.setdefault("report_date", W.REPORT_DATE)
    with quiet():
        return B.build(folder, **kw)


def person(d, cid):
    return next(c for c in d["contacts"] if c["id"] == cid)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


@unittest.skipUnless(HAVE_XLSX, "openpyxl is not installed")
class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="sr_curation_")
        cls.folder = os.path.join(cls.tmp, "sample-glen")
        with quiet():
            cls.raw, cls.cur0 = W.prepare(cls.folder)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.cur = F.load_json(os.path.join(self.folder, "curation.json"))

    def copy(self, cur=None):
        folder = os.path.join(self.tmp, "v%d" % len(os.listdir(self.tmp)), "sample-glen")
        shutil.copytree(self.folder, folder)
        if cur is not None:
            F.save_json(os.path.join(folder, "curation.json"), cur)
        return folder

    def reparse(self, **kw):
        path = W.build(os.path.join(self.tmp, "export_%d.xlsx" % len(os.listdir(self.tmp))), **kw)
        return intake_sheet.parse_workbook(path, W.LISTING["list_date"], W.AS_OF, "sample-glen")

    def key(self, phrase, raw=None):
        for t in (raw or self.raw)["tabs"]:
            for r in t["rows"]:
                for e in r["entries"]:
                    if phrase in e["text"]:
                        return e["key"]
        raise KeyError(phrase)

    def row(self, name, kind, raw=None):
        t = next(t for t in (raw or self.raw)["tabs"] if t["kind"] == kind)
        return next(r for r in t["rows"] if (r["name_raw"] or r["buyer_raw"] or "") == name)


class Todo(Base):
    def test_an_unread_sheet_lists_people_notes_and_sessions(self):
        blank = CT.blank_curation("sample-glen")
        todo = CT.todo(self.raw, blank)
        self.assertEqual(blank["people"], {}, "the work list changes nothing")
        self.assertEqual(todo["counts"]["new_people"], 14)
        self.assertEqual(todo["counts"]["entries"], 21)
        self.assertEqual(todo["counts"]["open_house_sessions"], 10)
        self.assertEqual(todo["counts"]["offer_rows"], 1)
        self.assertEqual(todo["counts"]["showing_rows_without_a_date"], 2)
        self.assertEqual([p["proposed_id"] for p in todo["new_people"]], ["c%03d" % i for i in range(1, 15)])
        self.assertIn("readings_file_format", todo)
        self.assertIn("PRIVATE", todo["WARNING"])

    def test_stock_phrases_and_labels_are_not_on_the_list(self):
        todo = CT.todo(self.raw, CT.blank_curation("sample-glen"))
        texts = [e["text"] for e in todo["entries"]]
        self.assertNotIn(STOCK, texts)
        self.assertNotIn("refer to showing activity for updates", texts)
        self.assertNotIn("open house host", texts)
        with_reply = next(e for e in todo["entries"] if "out of town" in e["text"])
        self.assertEqual(with_reply["reply_lines"], ["she replied by text that her client is out of town"])
        self.assertEqual(with_reply["stock_phrases_seen"], ["voicemail", "text", "email"])
        undated = [e for e in todo["entries"] if e["undated"]]
        self.assertEqual(len(undated), 2)

    def test_merges_are_proposals_only(self):
        todo = CT.todo(self.raw, CT.blank_curation("sample-glen"))
        multi = [p for p in todo["new_people"] if len(p["rows"]) > 1]
        self.assertEqual(sorted((p["basis"], len(p["rows"])) for p in multi), [("name", 2), ("phone", 2), ("phone", 2)])
        self.assertTrue(all(p["needs_a_look"] for p in multi))
        invited = [p for p in todo["new_people"] if p["basis"] == "invited_by"]
        agent = next(p for p in todo["new_people"] if p["rows"][0]["name_raw"] == "Thaddeus Okonkwo")
        self.assertEqual([(p["kind_guess"], p["represented_by_guess"]) for p in invited], [("buyer", agent["proposed_id"])] * 2)
        host = next(p for p in todo["new_people"] if p["rows"][0]["name_raw"] == "Leocadia Marchetti")
        self.assertIn("open_house_host", host["hints"])
        buyer = next(p for p in todo["new_people"] if p["rows"][0]["name_raw"] == "Kestrel")
        self.assertEqual(buyer["kind_guess"], "buyer")

    def test_a_new_row_for_a_known_person_is_offered_not_added(self):
        cur = CT.blank_curation("sample-glen")
        glide = self.row("Odalys Verhoeven", "disclosure")["key"]
        CT.apply_tags(cur, {"people": {"c001": {"rows": [glide], "kind": "agent"}}}, self.raw)
        todo = CT.todo(self.raw, cur)
        offer = [x for x in todo["rows_to_add"] if x["person"] == "c001"]
        self.assertEqual([(x["row"], x["basis"], x["needs_a_look"]) for x in offer], [(self.row("Odalys Verhoeven", "showing")["key"], "phone", True)])
        self.assertEqual(cur["people"]["c001"]["rows"], [glide])
        self.assertEqual(todo["new_people"][0]["proposed_id"], "c002")

    def test_once_tagged_only_untouched_things_remain(self):
        todo = CT.todo(self.raw, self.cur)
        self.assertEqual((todo["counts"]["entries"], todo["counts"]["new_people"], todo["counts"]["offer_rows"]), (0, 0, 0))
        self.assertEqual(todo["counts"]["open_house_sessions"], 7, "seven recaps still have only their count")
        self.assertEqual(todo["counts"]["showing_rows_without_a_date"], 0)

    def test_next_week_only_new_and_edited_notes_need_tags(self):
        raw2 = self.reparse(edits={("showing", 1, 12): "4/13 - he called back, his client wants a second look",
                                   ("glide", 0, 11): "4/7 --called about the price change, she will ask her clients tonight"})
        todo = CT.todo(raw2, self.cur)
        self.assertEqual(todo["counts"]["entries"], 2)
        self.assertEqual(todo["counts"]["new_people"], 0)
        new = next(e for e in todo["entries"] if "second look" in e["text"])
        self.assertEqual((new["person"], new["date"]), ("c009", "2026-04-13"))
        self.assertNotIn("edited_from", new)
        edited = next(e for e in todo["entries"] if "tonight" in e["text"])
        self.assertEqual(edited["edited_from"]["old_curation"]["touches"][0]["summary_safe"], "Called about the price change. She will ask her clients.")
        self.assertEqual(todo["edited_entries"], [edited["key"]])

    def test_a_row_whose_key_changed_is_offered_for_relinking(self):
        raw2 = self.reparse(edits={("showing", 5, 4): 6505550102.0})                # someone added the agent's phone to his showing row
        old = self.row("Thaddeus Okonkwo", "showing")["key"]
        new = self.row("Thaddeus Okonkwo", "showing", raw2)["key"]
        self.assertNotEqual(old, new)
        todo = CT.todo(raw2, self.cur)
        self.assertEqual([(r["old_row"], r["new_row"], r["person"], r["notes_in_common"]) for r in todo["relink_candidates"]], [(old, new, "c002", 2)])
        self.assertEqual(todo["counts"]["new_people"], 0)
        rep = CT.apply_tags(self.cur, {"relink": {old: new}}, raw2)
        self.assertEqual(rep["rejected"], [])
        self.assertIn(new, self.cur["people"]["c002"]["rows"])
        self.assertEqual(C.validate_curation(self.cur), [])
        again = CT.todo(raw2, self.cur)
        self.assertEqual((again["counts"]["relink_candidates"], again["counts"]["entries"], again["counts"]["stale_rows"]), (0, 0, 0))

    def test_rows_first_seen_after_the_cutoff_wait(self):
        todo = CT.todo(self.raw, CT.blank_curation("sample-glen"), through="2026-04-12")
        self.assertEqual(todo["rows_waiting_for_a_later_issue"], [self.row("Quentin Abernathy-Solis", "disclosure")["key"]])
        self.assertEqual(todo["counts"]["new_people"], 13)
        self.assertFalse(any(e["date"] and e["date"] > "2026-04-12" for e in todo["entries"]))


class Apply(Base):
    def test_the_readings_file_becomes_a_valid_curation(self):
        self.assertEqual(C.validate_curation(self.cur), [])
        self.assertEqual(len(self.cur["people"]), 14)
        self.assertEqual(self.cur["people"]["c001"]["tags"]["interest"], {"value": "cold", "provenance": "claude"})
        self.assertTrue(all(e["provenance"] == "claude" for e in self.cur["entries"].values()))
        self.assertEqual(self.cur["people"]["c003"]["represented_by"], "c002")
        self.assertEqual(self.cur["updated"], W.AS_OF)

    def test_apply_never_overwrites_what_the_operator_corrected(self):
        key = self.key("price is fair")
        CT.correct(self.cur, {"people": {"c009": {"interest": "hot", "feedback_safe": "He said the price is fair."}},
                              "entries": {key: {"text_safe": "He said the price is fair for the area."}}}, self.raw, by="Adrian", on="2026-04-13")
        rep = CT.apply_tags(self.cur, {"people": {"c009": {"tags": {"interest": "cold"}, "feedback_safe": "A new reading.", "brokerage": "Northgate Realty"}},
                                        "entries": {key: {"touches": [], "feedback": None}}}, self.raw)
        self.assertEqual(self.cur["people"]["c009"]["tags"]["interest"]["value"], "hot")
        self.assertEqual(self.cur["people"]["c009"]["feedback_safe"], "He said the price is fair.")
        self.assertEqual(self.cur["entries"][key]["feedback"]["text_safe"], "He said the price is fair for the area.")
        self.assertEqual(self.cur["people"]["c009"]["brokerage"], "Northgate Realty", "a field nobody corrected is still Claude's to set")
        self.assertEqual(len(rep["kept"]), 3)
        self.assertIn("people.c009.brokerage", rep["applied"])

    def test_apply_rejects_what_it_cannot_place(self):
        taken = self.cur["people"]["c001"]["rows"][0]
        rep = CT.apply_tags(self.cur, {"people": {"c020": {"rows": [taken], "kind": "agent"}, "c021": {"kind": "agent"}, "x1": {"rows": []},
                                                  "c022": {"rows": ["showing:0000000000"]}},
                                        "entries": {"showing:0000000000/note/2026-04-01/abcdef12": {"touches": []}},
                                        "ignored_rows": {taken: "not a contact"}}, self.raw)
        self.assertEqual(len(rep["rejected"]), 6)
        self.assertEqual(sorted(self.cur["people"]), sorted(self.cur0["people"]))
        self.assertNotIn(taken, self.cur["ignored_rows"])

    def test_unsafe_wording_is_not_saved(self):
        folder = self.copy()
        before = F.sha256_file(os.path.join(folder, "curation.json"))
        tags = os.path.join(folder, "readings.json")
        F.save_json(tags, {"entries": {self.key("sent the disclosure link"): {"touches": [
            {"channel": "email", "direction": "outbound", "outcome": "sent", "summary_safe": "Emailed thaddeus@example.com the link."}]}}})
        with quiet():
            code = CT.main(["apply", "--folder", folder, "--readings", tags])
        self.assertEqual(code, 2)
        self.assertEqual(F.sha256_file(os.path.join(folder, "curation.json")), before)


class Correct(Base):
    """What the operator says after reading the report, applied in one step and kept for later weeks."""

    def test_a_plain_correction_is_recorded_and_reaches_the_ledger(self):
        done = CT.correct(self.cur, {"people": {"c009": {"price_reaction": "too_high"},
                                                "c001": {"interest": "cold"},
                                                "c010": {"feedback_safe": "His client is not interested and said the price is too high.", "note": "Shorter."}}},
                          self.raw, by="Graeham", on="2026-04-13")
        self.assertIn("c009.price_reaction = too_high", done)
        tag = self.cur["people"]["c001"]["tags"]["interest"]
        self.assertEqual((tag["value"], tag["provenance"], tag["corrected_by"], tag["corrected_on"], tag["sheet_value_seen"]),
                         ("cold", "corrected_by_operator", "Graeham", "2026-04-13", "warm"))
        fix = [o for o in self.cur["overrides"] if o["path"] == "people.c010.feedback_safe"]
        self.assertEqual((fix[0]["by"], fix[0]["on"], fix[0]["reason"]), ("Graeham", "2026-04-13", "Shorter."))
        self.assertEqual(C.validate_curation(self.cur), [])
        d, problems, info = build(self.copy(self.cur))
        self.assertEqual(problems, [])
        self.assertEqual(person(d, "c009")["price_reaction"], "too_high")
        self.assertEqual((d["pricing_tally"]["too_high"], d["pricing_tally"]["fair_or_positive"], d["pricing_tally"]["not_raised"]), (3, 0, 4))
        self.assertEqual(person(d, "c001")["interest"], "cold", "the operator's correction beats the sheet column")
        self.assertEqual(person(d, "c010")["feedback_safe"], "His client is not interested and said the price is too high.")
        self.assertEqual(info["provenance"]["c001"]["interest"], "corrected_by_operator")
        self.assertNotIn("corrected_by_operator", F.dumps(d), "where a value came from is never in the ledger")

    def test_he_never_said_it_was_overpriced_holds_in_later_weeks(self):
        folder = self.copy()
        with quiet():
            code = CT.main(["correct", "--folder", folder, "--who", "Ignatius", "--set", "price_reaction=not_raised",
                            "--why", "Ignatius never said it was overpriced", "--by", "Graeham", "--on", "2026-04-13"])
        self.assertEqual(code, 0)
        cur = F.load_json(os.path.join(folder, "curation.json"))
        tag = cur["people"]["c010"]["tags"]["price_reaction"]
        self.assertEqual((tag["value"], tag["provenance"], tag["corrected_by"]), ("not_raised", "corrected_by_operator", "Graeham"))
        before, _, _ = build(self.folder)
        d, problems, _ = build(folder)
        self.assertEqual(problems, [])
        self.assertEqual(person(d, "c010")["price_reaction"], "not_raised")
        self.assertEqual(d["pricing_tally"]["too_high"], before["pricing_tally"]["too_high"] - 1)
        # next week Claude reads the notes again and still thinks he said the price is high: the correction stands
        rep = CT.apply_tags(cur, {"people": {"c010": {"tags": {"price_reaction": "too_high", "interest": "passed"}}}}, self.raw)
        self.assertEqual(cur["people"]["c010"]["tags"]["price_reaction"]["value"], "not_raised")
        self.assertEqual(rep["kept"], ["people.c010.price_reaction (corrected by operator)"])
        F.save_json(os.path.join(folder, "curation.json"), cur)
        later, problems, _ = build(folder, report_date="2026-04-20", through="2026-04-19")
        self.assertEqual(problems, [])
        self.assertEqual(person(later, "c010")["price_reaction"], "not_raised")

    def test_take_out_the_part_about_the_kitchen(self):
        folder = self.copy()
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(CT.main(["correct", "--folder", folder, "--find", "kitchen"]), 0)
        self.assertIn("2 sentence(s) the report prints hold 'kitchen'", out.getvalue())
        self.assertIn("Ignatius D. (c010)", out.getvalue())
        self.assertEqual(F.load_json(os.path.join(folder, "curation.json")), self.cur, "--find changes nothing")
        with quiet():
            code = CT.main(["correct", "--folder", folder, "--who", "Ignatius D.", "--reword",
                            "He gave negative feedback on the kitchen and specifically said the price is too high.",
                            "--to", "He specifically said the price is too high.", "--on", "2026-04-13"])
        self.assertEqual(code, 0)
        cur = F.load_json(os.path.join(folder, "curation.json"))
        key = self.key("kitchen is awful")
        self.assertEqual(cur["entries"][key]["feedback"]["text_safe"], "His client is not interested. He specifically said the price is too high.")
        self.assertEqual((cur["entries"][key]["provenance"], cur["entries"][key]["corrected_by"]), ("corrected_by_operator", "operator"))
        d, problems, _ = build(folder)
        self.assertEqual(problems, [])
        self.assertNotIn("kitchen", F.dumps(person(d, "c010")))
        rep = CT.apply_tags(cur, {"entries": {key: {"touches": [], "feedback": None}}}, self.raw)
        self.assertEqual(rep["kept"], ["entries[%s] (corrected by the operator)" % key], "a later automatic pass leaves the wording alone")

    def test_remove_takes_out_the_sentence_and_refuses_to_leave_an_entry_empty(self):
        key = self.key("loved the yard")
        owner = CT.holders(self.cur)[key.split("/")[0]]
        done = CT.correct(self.cur, {"scope": owner, "remove": ["stairs"]}, self.raw, on="2026-04-13")
        self.assertEqual(self.cur["entries"][key]["feedback"]["text_safe"], "His clients loved the yard.")
        self.assertEqual(self.cur["entries"][key]["touches"][0]["summary_safe"], "Said his clients loved the yard.")
        self.assertGreaterEqual(len(done), 2)
        with self.assertRaises(SystemExit) as stop:
            CT.correct(self.cur, {"scope": owner, "remove": ["loved the yard"]}, self.raw)
        self.assertIn("would leave an entry with no words", str(stop.exception))
        with self.assertRaises(SystemExit):
            CT.correct(self.cur, {"scope": owner, "remove": ["a phrase that is nowhere"]}, self.raw)
        with self.assertRaises(SystemExit) as stop:
            CT.correct(self.cur, {"scope": owner, "reword": [["loved the yard", "loved it. Call 650-555-0199"]]}, self.raw)
        self.assertIn("has a phone number", str(stop.exception))

    def test_the_person_is_found_by_a_plain_name_or_nothing_changes(self):
        self.assertEqual(CT.find_person(self.cur, self.raw, "c010"), ["c010"])
        self.assertEqual(CT.find_person(self.cur, self.raw, "ignatius"), ["c010"])
        self.assertEqual(CT.find_person(self.cur, self.raw, "Ignatius Delacroix"), ["c010"])
        self.assertEqual(CT.find_person(self.cur, self.raw, "Nobody Atall"), [])
        folder = self.copy()
        before = F.sha256_file(os.path.join(folder, "curation.json"))
        with quiet():
            self.assertEqual(CT.main(["correct", "--folder", folder, "--who", "Nobody Atall", "--set", "interest=cold"]), 2)
        self.assertEqual(F.sha256_file(os.path.join(folder, "curation.json")), before)
        with self.assertRaises(SystemExit), quiet():
            CT.main(["correct", "--folder", folder])
        with self.assertRaises(SystemExit), quiet():
            CT.main(["correct", "--folder", folder, "--set", "interest=cold"])

    def test_values_are_typed_the_plain_way(self):
        self.assertEqual(CT.parse_value("themes", "size_layout, parking"), ["size_layout", "parking"])
        self.assertEqual(CT.parse_value("themes", "none"), [])
        self.assertEqual(CT.parse_value("price_asked", "yes"), True)
        self.assertIsNone(CT.parse_value("status", "null"))
        self.assertEqual(CT.parse_value("feedback_safe", "Liked the yard."), "Liked the yard.")
        folder = self.copy()
        with quiet():
            self.assertEqual(CT.main(["correct", "--folder", folder, "--who", "c009", "--set", "interest=scorching"]), 2,
                             "a value outside the vocabulary is not saved")

    def test_merge_and_split_never_reuse_an_id(self):
        CT.correct(self.cur, {"merge": [{"keep": "c012", "absorb": "c013", "reason": "Test merge."}]}, self.raw, by="Adrian", on="2026-04-13")
        self.assertNotIn("c013", self.cur["people"])
        zen = self.row("Zenobia Achterberg", "showing")["key"]
        self.assertIn(zen, self.cur["people"]["c012"]["rows"])
        self.assertEqual(CT.next_id(self.cur), "c015")
        CT.correct(self.cur, {"split": [{"person": "c012", "rows": [zen]}]}, self.raw, by="Adrian", on="2026-04-13")
        self.assertEqual(self.cur["people"]["c015"]["rows"], [zen])
        self.assertNotIn(zen, self.cur["people"]["c012"]["rows"])
        self.assertEqual(CT.next_id(self.cur), "c016")
        self.assertEqual(C.validate_curation(self.cur), [])
        with self.assertRaises(SystemExit):
            CT.correct(self.cur, {"split": [{"person": "c015", "rows": [zen]}]}, self.raw, by="Adrian")

    def test_a_correction_names_a_known_person_and_a_known_field(self):
        with self.assertRaises(SystemExit):
            CT.correct(self.cur, {"people": {"c099": {"interest": "cold"}}}, self.raw, by="Adrian")
        with self.assertRaises(SystemExit):
            CT.correct(self.cur, {"people": {"c001": {"rows": []}}}, self.raw, by="Adrian")

    def test_there_is_no_review_step_and_no_confirm_step(self):
        for gone in ("review", "confirm"):
            with self.assertRaises(SystemExit), quiet():
                CT.main([gone, "--folder", self.folder])
            self.assertFalse(hasattr(CT, gone))
        scripts = os.path.join(SKILL, "scripts")
        self.assertFalse(os.path.exists(os.path.join(scripts, "sr_review_page.py")))
        for name in ("curation_tools.py", "sr_correct.py"):
            text = read(os.path.join(scripts, name)).lower()
            for word in ("tag-review", "tag review", "sign_off", "sign-off", "human_confirmed", "unreviewed"):
                self.assertNotIn(word, text, "%s still mentions %s" % (name, word))


@unittest.skipUnless(HAVE_XLSX, "openpyxl is not installed")
class CommandLine(unittest.TestCase):
    def test_todo_apply_correct_then_a_ledger(self):
        tmp = tempfile.mkdtemp(prefix="sr_curation_cli_")
        try:
            folder = os.path.join(tmp, "sample-glen")
            with quiet():
                raw, _ = W.prepare(folder, tagged=False)
                self.assertEqual(CT.main(["todo", "--folder", folder]), 0)
            todo = F.load_json(os.path.join(folder, "work", "todo.json"))
            self.assertEqual(todo["counts"]["entries"], 21)
            self.assertIn("readings_file_format", todo)
            F.save_json(os.path.join(folder, "readings.json"), W.tags_for(raw))
            with quiet():
                self.assertEqual(CT.main(["apply", "--folder", folder, "--readings", os.path.join(folder, "readings.json")]), 0)
            d, problems, _ = build(folder)
            self.assertEqual(problems, [], "the report builds straight after Claude's reading: nobody is asked to confirm anything")
            F.save_json(os.path.join(folder, "corrections.json"), {"by": "Adrian", "on": "2026-04-13", "people": {"c009": {"interest": "hot"}}})
            with quiet():
                self.assertEqual(CT.main(["correct", "--folder", folder, "--file", os.path.join(folder, "corrections.json")]), 0)
                self.assertEqual(CT.main(["apply", "--folder", folder, "--readings", os.path.join(folder, "readings.json")]), 0)
            cur = F.load_json(os.path.join(folder, "curation.json"))
            self.assertEqual((cur["people"]["c009"]["tags"]["interest"]["value"], cur["people"]["c009"]["tags"]["interest"]["corrected_by"]),
                             ("hot", "Adrian"), "a second automatic pass leaves the correction alone")
            d, problems, _ = build(folder)
            self.assertEqual(problems, [])
            self.assertEqual(person(d, "c009")["interest"], "hot")
            self.assertFalse(os.path.exists(os.path.join(folder, "review")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
