# -*- coding: utf-8 -*-
"""Tests for the Gmail-safe copy of the email (sr_render render(..., gmail_safe=True), render_email_pair) and for
the ship gate's rules on it (sr_checks.email_safety, the gmail_* rules).

    python -m unittest tests.test_render_gmail      (from the skill folder)

Why the copy exists: the Gmail connector that makes the draft drops every <img>, turns tel: links into dead
javascript:void(0) links, drops every "background:" declaration, and rewrites web links, and plain-text web
addresses, into short-lived google.com redirects. The copy that goes into the draft is drawn so none of that
matters, and it says exactly what the email says.

Synthetic data only: tests/fixtures/ledger_small.json and ledger_busy.json, changed in memory. Brand values are
read from identity.json at run time.
"""
import copy
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
sys.path.insert(0, SCRIPTS)
import check_report  # noqa: E402
import sr_contract as C  # noqa: E402
import sr_render.api as API  # noqa: E402
from sr_render import RenderRefused, render, render_email_pair  # noqa: E402
from sr_render.assemble import ADDRESS, guard_addresses  # noqa: E402
from sr_render.htmlkit import no_autolink  # noqa: E402
from sr_checks.email_safety import reading_words  # noqa: E402
from sr_checks.page import Page  # noqa: E402

ID = C.load_identity()
HERO = "https://example.com/sample-photo.jpg"
RECORD = "https://example.com/sample-record.html"


def load(name):
    with open(os.path.join(HERE, "fixtures", name), encoding="utf-8") as f:
        return json.load(f)


def words(html):
    return reading_words(Page(html))


class GmailSafeCopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = dict((fx, render_email_pair(load("ledger_%s.json" % fx), hero=HERO)) for fx in ("small", "busy"))

    def test_the_copy_says_exactly_what_the_email_says(self):
        for fx, (email, gmail) in self.pairs.items():
            self.assertEqual(words(gmail["html"]), words(email["html"]), fx)
            self.assertEqual(gmail["info"]["fit_level"], email["info"]["fit_level"], fx)
            self.assertEqual(gmail["info"]["copy"], "gmail")
            self.assertIsNone(email["info"]["copy"])

    def test_the_email_itself_is_not_changed_by_the_copy(self):
        d = load("ledger_busy.json")
        alone = render(d, mode="email", hero=HERO)
        self.assertEqual(alone["html"], self.pairs["busy"][0]["html"])
        self.assertIn(HERO, alone["html"])
        self.assertIn('href="tel:', alone["html"])
        self.assertIn('href="https://%s"' % ID["website"], alone["html"])

    def test_no_photo_no_phone_link_no_web_link_no_colored_span(self):
        for fx, (_, gmail) in self.pairs.items():
            h = gmail["html"]
            self.assertNotIn("<img", h, fx)
            self.assertNotIn("tel:", h, fx)
            self.assertEqual(re.findall(r'href="(https?:[^"]*)"', h), [], fx)
            self.assertIsNone(re.search(r'<(?!t[dhr]\b|table\b|body\b)\w+\b[^>]*style="[^"]*background', h), fx)
            self.assertIsNone(gmail["info"]["flags"]["hero"])
            self.assertIn('<meta name="sr:copy" content="gmail">', h)
            self.assertLess(gmail["info"]["bytes"], 95000)

    def test_the_phone_and_the_website_keep_their_look_as_plain_text(self):
        email, gmail = self.pairs["small"]
        look = re.search(r'<a href="tel:[^"]*" (style="[^"]*")>%s</a>' % re.escape(ID["phone"]), email["html"]).group(1)
        self.assertIn('<span %s>%s</span>' % (look, ID["phone"]), gmail["html"])
        site = ID["website"]
        self.assertNotIn(site, re.sub(r"<[^>]+>", "\x00", gmail["html"]))          # never one run of text
        self.assertIn(site, words(gmail["html"]))                                    # and read exactly as before
        self.assertIn(no_autolink(site, "#FFFFFF"), gmail["html"])
        call = re.search(r"CALL OR TEXT [^<]*", gmail["html"])
        self.assertIsNotNone(call)
        self.assertNotIn("<a ", gmail["html"][call.start() - 200:call.start()])

    def test_a_chip_sits_on_a_table_cell_with_a_bgcolor(self):
        _, gmail = self.pairs["busy"]
        right = re.findall(r'<table role="presentation" cellpadding="0" cellspacing="0" align="right"><tr><td bgcolor="(#[0-9A-F]{6})"', gmail["html"])
        self.assertTrue(right)
        _, small = self.pairs["small"]                       # the online ads chips sit in a line of text
        self.assertGreater(small["html"].count('style="display:inline-table;vertical-align:middle"><tr><td bgcolor="#'), 0)

    def test_an_address_in_a_note_is_written_so_it_is_not_turned_into_a_link(self):
        d = load("ledger_small.json")
        x = next(c for c in d["contacts"] if c.get("feedback_safe"))
        x["feedback_safe"] = x["feedback_safe"].rstrip(".") + ". Saw it on zillow.com first."
        for e in x.get("feedback_log") or []:
            e["text_safe"] = (e.get("text_safe") or "").rstrip(".") + ". Saw it on zillow.com first."
        C.finish_ledger(d)
        email, gmail = render_email_pair(d)
        if "zillow.com" not in email["html"]:
            self.skipTest("the fixture's note is not printed in the email")
        self.assertNotIn("zillow.com", gmail["html"])
        self.assertEqual(words(gmail["html"]), words(email["html"]))
        self.assertEqual(guard_addresses("<p>see www.example.com and <a href=\"mailto:a@b.com\">a@b.com</a></p>"),
                         '<p>see www<span style="color:inherit">.example</span><span style="color:inherit">.com</span> and '
                         '<a href="mailto:a@b.com">a@b.com</a></p>')
        self.assertIsNone(ADDRESS.search("write to pat@example.com"))

    def test_the_record_button_is_the_one_web_link_the_copy_keeps(self):
        email, gmail = render_email_pair(load("ledger_small.json"), link_url=RECORD)
        self.assertIn('href="%s"' % RECORD, gmail["html"])
        self.assertEqual(re.findall(r'href="(https?:[^"]*)"', gmail["html"]), [RECORD])
        self.assertEqual(words(gmail["html"]), words(email["html"]))

    def test_both_step_down_together_when_the_copy_would_not_fit(self):
        d = load("ledger_busy.json")
        real = API.render
        level = render(d, mode="email")["info"]["fit_level"]

        def tight(ledger, **kw):
            if kw.get("gmail_safe") and kw.get("fit_level", 0) <= level:
                raise RenderRefused("size", ["pretend the copy is over the ceiling"])
            return real(ledger, **kw)
        with mock.patch.object(API, "render", tight):
            email, gmail = API.render_email_pair(d)
        self.assertEqual(email["info"]["fit_level"], level + 1)
        self.assertEqual(gmail["info"]["fit_level"], level + 1)
        self.assertEqual(words(gmail["html"]), words(email["html"]))

    def test_only_the_email_has_a_gmail_safe_copy(self):
        d = load("ledger_small.json")
        for mode in ("link", "print"):
            with self.assertRaises(ValueError):
                render(d, mode=mode, gmail_safe=True)
        with self.assertRaises(ValueError):
            render(d, mode="email", fit_level=99)


class GateOnTheCopy(unittest.TestCase):
    """The ship gate on a folder holding email.html and email_gmail.html, each rule broken once."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="sr gmail gate ")
        d = load("ledger_small.json")
        cls.ledger = d
        email, gmail = render_email_pair(d, hero=HERO)
        cls.email, cls.gmail = email["html"], gmail["html"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)

    def gate(self, gmail=None, with_email=True, name="email_gmail.html"):
        folder = tempfile.mkdtemp(dir=self.root)
        with open(os.path.join(folder, "ledger.json"), "w", encoding="utf-8") as f:
            json.dump(self.ledger, f)
        if with_email:
            with open(os.path.join(folder, "email.html"), "w", encoding="utf-8", newline="\n") as f:
                f.write(self.email)
        with open(os.path.join(folder, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(self.gmail if gmail is None else gmail)
        out = os.path.join(folder, "gate.json")
        argv = (["--issue", folder] if name == "email_gmail.html" else [os.path.join(folder, name), "--ledger", os.path.join(folder, "ledger.json"), "--kind", "email"])
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            check_report.main(argv + ["--only", "email_safety", "--allow-synthetic", "--json", out])
        with open(out, encoding="utf-8") as f:
            rep = json.load(f)
        page = next(p for p in rep["pages"] if p["file"].endswith(name))
        return dict((r["id"], r) for r in page["results"])

    def level(self, res, rule):
        return res["email_safety." + rule]["level"]

    def test_the_clean_copy_passes_every_rule(self):
        res = self.gate()
        for rule in ("gmail_images", "gmail_links", "gmail_backgrounds", "gmail_addresses", "gmail_same_words", "size"):
            self.assertEqual(self.level(res, rule), "pass", rule)

    def test_the_email_itself_is_not_held_to_the_copy_rules(self):
        folder_res = self.gate()
        self.assertTrue(all(not k.startswith("email_safety.gmail") for k in self.gate(gmail=self.email, name="email.html")))
        self.assertIn("email_safety.gmail_images", folder_res)

    def test_each_thing_the_connector_breaks_fails_its_rule(self):
        cases = [
            ("gmail_images", self.gmail.replace("</body>", '<img src="%s" width="10" height="10" alt="x"></body>' % HERO)),
            ("gmail_links", self.gmail.replace("</body>", '<a href="tel:+15555550100" style="display:block;padding:12px 0">Call</a></body>')),
            ("gmail_links", self.gmail.replace("</body>", '<a href="https://example.com/x" style="display:block;padding:12px 0">More</a></body>')),
            ("gmail_backgrounds", self.gmail.replace("</body>", '<span style="background:#E3F0E8">REPLIED</span></body>')),
            ("gmail_addresses", self.gmail.replace("</body>", "<p>example.com</p></body>")),
        ]
        for rule, page in cases:
            res = self.gate(gmail=page)
            self.assertEqual(self.level(res, rule), "fail", rule)

    def test_a_changed_word_fails_and_says_where(self):
        m = re.search(r">(Next week)<", self.gmail) or re.search(r">([A-Z][a-z]{3,} [a-z]{3,})<", self.gmail)
        page = self.gmail[:m.start(1)] + m.group(1) + " now" + self.gmail[m.end(1):]
        res = self.gate(gmail=page)
        self.assertEqual(self.level(res, "gmail_same_words"), "fail")
        self.assertTrue(any("now" in e for e in res["email_safety.gmail_same_words"]["evidence"]))

    def test_without_the_email_beside_it_the_words_cannot_be_compared(self):
        res = self.gate(with_email=False)
        self.assertEqual(self.level(res, "gmail_same_words"), "fail")

    def test_the_record_button_is_a_note_not_a_failure(self):
        email, gmail = render_email_pair(self.ledger, link_url=RECORD)
        keep = (self.email, self.gmail)
        try:
            type(self).email, type(self).gmail = email["html"], gmail["html"]
            res = self.gate()
        finally:
            type(self).email, type(self).gmail = keep
        self.assertEqual(self.level(res, "gmail_links"), "pass")
        self.assertEqual(self.level(res, "gmail_record_button"), "warn")

    def test_too_big_fails(self):
        lines = (95000 - len(self.gmail.encode("utf-8"))) // 901 + 2
        page = self.gmail.replace("</body>", "<!--\n" + ("x" * 900 + "\n") * lines + "-->\n</body>")
        self.assertEqual(self.level(self.gate(gmail=page), "size"), "fail")


if __name__ == "__main__":
    unittest.main()
