# -*- coding: utf-8 -*-
"""Tests for run_issue.py: the one command that takes a listing from the sheet export to the checked report.

    python -m unittest tests.test_run_issue      (from the skill folder)

Synthetic data only (tests/fixtures/make_workbook.py), written to a temp folder. The Edge steps (PDF, phone
pictures, phone layout) are switched off here; test_render.py and test_checks.py cover them.
"""
import contextlib
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
sys.path.insert(0, os.path.join(SKILL, "scripts"))
sys.path.insert(0, os.path.join(HERE, "fixtures"))
if site.getusersitepackages() not in sys.path:
    sys.path.append(site.getusersitepackages())
import sr_files as F  # noqa: E402
import curation_tools as CT  # noqa: E402
import run_issue as RI  # noqa: E402
import snapshot_issue as S  # noqa: E402
import make_workbook as W  # noqa: E402

try:
    import openpyxl  # noqa: F401
    HAVE_XLSX = True
except ImportError:
    HAVE_XLSX = False

FAST = ["--no-pdf", "--no-previews", "--no-probe", "--allow-synthetic", "--report-date", W.REPORT_DATE]


def run(*argv):
    """(exit code, everything printed)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = RI.main(list(argv))
    return code, out.getvalue()


@unittest.skipUnless(HAVE_XLSX, "openpyxl is not installed")
class RunIssue(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sr run issue ")              # a path with spaces
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.folder = os.path.join(self.tmp, "seller-reports", "sample-glen")

    def prepared(self, read=True):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            raw, cur = W.prepare(self.folder, tagged=read)
        return raw, cur

    def test_it_stops_when_claude_has_notes_to_read_and_says_what_next(self):
        self.prepared(read=False)
        code, out = run("--folder", self.folder, *FAST)
        self.assertEqual(code, RI.EXIT_TO_READ)
        self.assertIn("STOPPED: Claude has reading to do", out)
        self.assertIn("21 note(s) not read yet", out)
        self.assertRegex(out, r"NEXT: read .*todo\.json")
        self.assertIn("curation_tools.py", out)
        self.assertTrue(os.path.exists(os.path.join(self.folder, "work", "todo.json")))
        self.assertFalse(os.path.exists(os.path.join(self.folder, "ledger.json")))
        self.assertFalse(os.path.exists(os.path.join(self.folder, "issues")))

    def test_from_the_sheet_export_to_the_checked_report_in_one_command(self):
        self.prepared()
        code, out = run("--folder", self.folder, "--sheet", os.path.join(self.folder, "export.xlsx"), "--as-of", W.AS_OF,
                        "--glance", "The team's status email counts 2 tours. This report counts 3, because one was logged later.", *FAST)
        self.assertEqual(code, RI.EXIT_READY, out)
        issue = os.path.join(self.folder, "issues", "05")
        self.assertEqual(sorted(os.listdir(issue)), ["email.html", "email_gmail.html", "ledger.json", "link.html", "manifest.json", "notes_for_operator.json", "print.html"])
        self.assertFalse(os.path.exists(os.path.join(issue, "draft")))
        m = F.load_json(os.path.join(issue, "manifest.json"))
        self.assertNotIn("build_kind", m)
        self.assertNotIn("tag_review", m)
        self.assertEqual((m["checks"]["ship_gate"]["passed"], m["checks"]["ship_gate"]["blocking"], m["checks"]["ship_gate"]["pages"]), (True, 0, 4))
        with open(os.path.join(issue, "email.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertLess(len(page.encode("utf-8")), 95000)
        text = re.sub(r"<[^>]+>", " ", page).lower()
        for word in ("draft", "do not send", "reviewer", "not for the seller", "status email"):
            self.assertNotIn(word, text)
        self.assertIsNone(re.search(r"\b(un)?tag(s|ged|ging)?\b", text))
        # what the operator hears: the report is ready, what is worth a glance, and the next step. Nothing about checks or tags.
        self.assertIn("READY: Weekly Seller Report No. 05", out)
        self.assertIn("Worth a glance before you send", out)
        self.assertIn("The team's status email counts 2 tours.", out)
        self.assertIn("all checks passed on 4 page(s)", out)
        self.assertRegex(out, r"NEXT: put email_gmail\.html in the body of an unsent Gmail draft")
        self.assertIsNone(re.search(r"\b(un)?tag(s|ged|ging)?\b|unreviewed|confirm the tags", out.lower()))
        notes = F.load_json(os.path.join(issue, "notes_for_operator.json"))
        self.assertLessEqual(len(notes["worth_a_glance"]), 5)
        self.assertEqual(F.load_json(os.path.join(self.folder, "ledger.json")), F.load_json(os.path.join(issue, "ledger.json")))

    def test_every_build_keeps_a_gmail_safe_copy_that_says_the_same_words(self):
        self.prepared()
        hero = "https://example.com/sample-photo.jpg"
        code, out = run("--folder", self.folder, "--hero", hero, *FAST)
        self.assertEqual(code, RI.EXIT_READY, out)
        issue = os.path.join(self.folder, "issues", "05")
        with open(os.path.join(issue, "email.html"), encoding="utf-8") as f:
            email = f.read()
        with open(os.path.join(issue, "email_gmail.html"), encoding="utf-8") as f:
            gmail = f.read()
        self.assertIn(hero, email)
        self.assertIn('href="tel:', email)
        self.assertNotIn("<img", gmail)
        self.assertNotIn("tel:", gmail)
        self.assertEqual(re.findall(r'href="(https?:[^"]*)"', gmail), [])
        self.assertIsNone(re.search(r'<span[^>]*background', gmail))
        self.assertLess(len(gmail.encode("utf-8")), 95000)
        self.assertIn("Gmail-safe copy (this one goes in the body of the unsent Gmail draft)", out)
        m = F.load_json(os.path.join(issue, "manifest.json"))
        self.assertIn("email_gmail.html", [x["name"] for x in m["files"]])
        self.assertEqual(m["email_gmail_bytes"], len(gmail.encode("utf-8")))
        self.assertEqual(m["email_bytes"], len(email.encode("utf-8")))
        gate = F.load_json(os.path.join(self.folder, "work", "gate.json"))
        page = next(p for p in gate["pages"] if p["file"].endswith("email_gmail.html"))
        rules = dict((r["id"], r["level"]) for r in page["results"])
        for rule in ("gmail_images", "gmail_links", "gmail_backgrounds", "gmail_addresses", "gmail_same_words", "size"):
            self.assertEqual(rules.get("email_safety." + rule), "pass", rule)

    def test_a_plain_correction_then_the_same_command_rebuilds_the_report(self):
        self.prepared()
        self.assertEqual(run("--folder", self.folder, *FAST)[0], RI.EXIT_READY)
        before = F.load_json(os.path.join(self.folder, "issues", "05", "ledger.json"))["pricing_tally"]["too_high"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(CT.main(["correct", "--folder", self.folder, "--who", "Ignatius", "--set", "price_reaction=not_raised",
                                      "--why", "He never said it was overpriced"]), 0)
        code, out = run("--folder", self.folder, *FAST)
        self.assertEqual(code, RI.EXIT_READY, out)
        after = F.load_json(os.path.join(self.folder, "issues", "05", "ledger.json"))["pricing_tally"]["too_high"]
        self.assertEqual(after, before - 1)

    def test_a_failed_check_stops_the_run_in_plain_words_and_keeps_nothing(self):
        _, cur = self.prepared()
        key = next(k for k, e in cur["entries"].items() if e.get("feedback") and "kitchen" in e["feedback"]["text_safe"])
        cur["entries"][key]["feedback"]["text_safe"] = "His client said the kitchen is disgusting and the home is a dump."
        F.save_json(os.path.join(self.folder, "curation.json"), cur)
        code, out = run("--folder", self.folder, *FAST)
        self.assertEqual(code, RI.EXIT_CHECKS, out)
        self.assertIn("STOPPED: a check failed, so nothing was kept and nothing should go in a draft.", out)
        self.assertIn("[tone.", out)
        self.assertIn("NEXT:", out)
        self.assertFalse(os.path.exists(os.path.join(self.folder, "issues")))

    def test_an_issue_recorded_as_sent_is_not_replaced_without_being_told(self):
        self.prepared()
        self.assertEqual(run("--folder", self.folder, *FAST)[0], RI.EXIT_READY)
        S.record(self.folder, 5, gmail_draft_id="draft-1", sent_on=W.REPORT_DATE)
        kept = F.sha256_file(os.path.join(self.folder, "issues", "05", "email.html"))
        with contextlib.redirect_stdout(io.StringIO()):
            CT.main(["correct", "--folder", self.folder, "--who", "Ignatius", "--set", "price_reaction=not_raised"])
        code, out = run("--folder", self.folder, *FAST)
        self.assertEqual(code, RI.EXIT_SENT, out)
        self.assertIn("recorded as sent", out)
        self.assertIn("--replace-sent", out)
        self.assertEqual(F.sha256_file(os.path.join(self.folder, "issues", "05", "email.html")), kept)
        code, out = run("--folder", self.folder, "--replace-sent", *FAST)
        self.assertEqual(code, RI.EXIT_READY, out)
        self.assertNotEqual(F.sha256_file(os.path.join(self.folder, "issues", "05", "email.html")), kept)

    def test_missing_inputs_stop_with_the_next_step(self):
        os.makedirs(self.folder)
        code, out = run("--folder", self.folder, *FAST)
        self.assertEqual(code, RI.EXIT_INPUT)
        self.assertIn("NEXT: write listing.json", out)
        F.save_json(os.path.join(self.folder, "listing.json"), W.LISTING)
        code, out = run("--folder", self.folder, *FAST)
        self.assertEqual(code, RI.EXIT_INPUT)
        self.assertIn("NEXT: export the listing's View Activity sheet", out)
        code, out = run("--folder", self.folder, "--report-date", "2026-04-14", "--no-pdf")
        self.assertEqual(code, RI.EXIT_INPUT)
        self.assertIn("NEXT:", out)

    def test_there_is_no_draft_or_final_switch(self):
        for gone in ("--draft", "--final", "--allow-unreviewed"):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                RI.main(["--folder", self.folder, gone])
        with open(os.path.join(SKILL, "scripts", "run_issue.py"), encoding="utf-8") as f:
            self.assertNotIn("send_message", f.read())


if __name__ == "__main__":
    unittest.main()
