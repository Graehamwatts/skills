# -*- coding: utf-8 -*-
"""Tests for the seller-report renderer (scripts/render_report.py, scripts/sr_render, scripts/render_previews.py).

    python -m unittest discover -s tests -p "test_render*.py"       (from the seller-report folder)
    python tests\\test_render.py

This file: every flag combination builds, the one build mode, the rules every page keeps,
feedback only, the command line, the preview helper, and the renderer's own source files. What the page says
(the tally, the brief, the link copy, the hooks, the fit ladder, empty states) is in test_render_content.py,
which borrows the helpers defined here.

Synthetic data only: every ledger here is tests/fixtures/ledger_small.json or ledger_busy.json, or a copy of
one changed in memory. Set SR_EDGE_TESTS=1 to also run the layout check in Microsoft Edge.
"""
import contextlib
import copy
import html as _html
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPTS = os.path.join(SKILL, "scripts")
sys.path.insert(0, SCRIPTS)
import sr_contract as C  # noqa: E402
import sr_render  # noqa: E402
import render_previews  # noqa: E402
from sr_render import RenderRefused, render  # noqa: E402
from sr_render.fit import FIT_LEVELS  # noqa: E402
from sr_render.tokens import LIMITS, P, F, PRICE_ROWS  # noqa: E402

ID = C.load_identity()
CLI = os.path.join(SCRIPTS, "render_report.py")
HTTPS = dict(hero="https://example.com/hero.jpg", link_url="https://example.com/record.html")
EM_DASH, EN_DASH = chr(0x2014), chr(0x2013)


def load(name):
    with open(os.path.join(HERE, "fixtures", name), encoding="utf-8") as f:
        return json.load(f)


def text_of(page):
    """The words a reader sees: style blocks and tags out, entities decoded, white space collapsed."""
    page = re.sub(r"<style>.*?</style>|<!--\[if mso\]>.*?<!\[endif\]-->", " ", page, flags=re.S)
    page = re.sub(r"</?(?:span|b|a)\b[^>]*>", "", page)            # inline tags do not break a word or a number
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", page)))


def hooked(page, name):
    """The text of every element the page marks data-sr="<name>" for the ship gate."""
    return re.findall(r'data-sr="%s"[^>]*>([^<]*)<' % re.escape(name), page)


def clean(case, d):
    """Finishes a changed ledger and makes sure it still satisfies the contract before it is rendered."""
    C.finish_ledger(d)
    case.assertEqual(C.validate_ledger(d, identity=ID), [])
    return d


def empty_listing(case):
    """Week one of a listing nobody has reacted to yet: no people, no open houses, no offers."""
    d = load("ledger_small.json")
    d["contacts"], d["open_houses"], d["offers"], d["team_side"], d["next_week"] = [], [], [], [], []
    d["offer_watch"], d["market"], d["marketing"] = [], None, None
    d["pricing_tally"]["open_house_price_remarks"] = []
    d["report"]["since_week_closed"]["items"] = []
    d["listing"]["list_date"] = "2026-04-08"
    d["listing"]["price_history"] = [{"date": "2026-04-08", "price": d["listing"]["list_price"], "event": "listed"}]
    return clean(case, d)


def with_first_contact(case):
    """The small fixture plus an agent who called us before we had followed up with them at all."""
    d = load("ledger_small.json")
    c = C.blank_contact("c090", "Quillon T.", brokerage="Harborlight Realty")
    c["engagements"] = [{"type": "inquiry", "date": "2026-04-09", "date_quality": "exact", "confirmed": True}]
    c["touches"] = [{"date": "2026-04-09", "date_quality": "exact", "channel": "call", "direction": "inbound", "outcome": "replied",
                     "summary_safe": "Called to ask about the home. His client wants a larger yard."}]
    c["feedback_log"] = [{"date": "2026-04-09", "text_safe": "His client wants a larger yard.", "softened": False, "source": "conversation",
                          "counts_as_conversation": True, "price_reaction": "not_raised", "price_asked": None,
                          "themes": ["yard_outdoor"], "liked": []}]
    c["feedback_safe"], c["themes"], c["interest"] = "His client wants a larger yard.", ["yard_outdoor"], "cold"
    d["contacts"].append(c)
    return clean(case, d)


NAMES_A = ["Bel", "Cor", "Dar", "Fen", "Gal", "Hal", "Jor", "Kel", "Lor", "Mar", "Nor", "Pel", "Quin", "Ros", "Sel", "Tam", "Val", "Wen", "Yar", "Zel"]
NAMES_B = ["a", "en", "ia", "on", "is", "or", "yn", "eth", "an", "il"]


def scaled(case, times):
    """The busy fixture with its ordinary contacts cloned, to push the email against the size ceiling."""
    d = load("ledger_busy.json")
    held = set(o.get("contact_id") for o in d["offers"]) | set(w["contact_id"] for w in d["offer_watch"])
    held |= set(c.get("represented_by") for c in d["contacts"]) | set(o.get("host_contact_id") for o in d["open_houses"])
    held |= set(t.get("contact_id") for t in d["team_side"]) | set(i.get("contact_id") for i in d["report"]["since_week_closed"]["items"])
    base = [c for c in d["contacts"] if C.is_counted(c) and c["id"] not in held and not c.get("is_open_house_host")]
    n = 0
    for _ in range(times - 1):
        for c in base:
            x = copy.deepcopy(c)
            x["id"] = "c%04d" % (9000 + n)
            x["name_short"] = "%s%s %s." % (NAMES_A[n % 20], NAMES_B[(n // 20) % 10], "ABCDEFGHJKLMNPRSTW"[(n // 200) % 18])
            x["name_recorded"] = True
            n += 1
            d["contacts"].append(x)
    return clean(case, d)


class Builds(unittest.TestCase):
    """Every flag combination builds, and every email stays under the ceiling."""

    def test_every_flag_combination(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            raw = load(name)
            for mode in sr_render.MODES:
                for hero in ("https", "none"):
                    for link in ("https", "none"):
                        for greet in ("default", "text", "none"):
                            for fonts in (None, True, False):
                                kw = dict(mode=mode, webfonts=fonts)
                                kw.update(dict(hero=HTTPS["hero"]) if hero == "https" else dict(no_hero=True))
                                kw.update(dict(link_url=HTTPS["link_url"]) if link == "https" else dict(no_link=True))
                                kw.update({"default": {}, "text": dict(greeting="Hi Pat and Sam,"), "none": dict(no_greeting=True)}[greet])
                                with self.subTest(ledger=name, **kw):
                                    r = render(raw, identity=ID, **kw)
                                    info, page = r["info"], r["html"]
                                    self.assertEqual(info["bytes"], len(page.encode("utf-8")))
                                    self.assertEqual(info["checks"]["ledger_problems"], 0)
                                    self.assertGreater(info["checks"]["model_checks_run"], 20)
                                    if mode == "email":
                                        self.assertLessEqual(info["bytes"], C.LIMITS["email_max_bytes"])

    def test_optional_sections_can_be_left_out(self):
        d = load("ledger_small.json")
        a = render(d, identity=ID, no_hero=True)
        b = render(d, identity=ID, no_hero=True, market=False, marketing=False)
        self.assertEqual(a["info"]["flags"]["sections"], ["market", "marketing"])
        self.assertEqual(b["info"]["flags"]["sections"], [])
        self.assertIn("TIME ON THE MARKET", text_of(a["html"]))
        self.assertIn("ONLINE ADS AND MARKETING", text_of(a["html"]))
        self.assertNotIn("TIME ON THE MARKET", text_of(b["html"]))
        self.assertNotIn("MARKETING", text_of(b["html"]))
        busy = render(load("ledger_busy.json"), identity=ID, no_hero=True)        # a ledger without them simply has none
        self.assertEqual(busy["info"]["flags"]["sections"], [])

    def test_render_does_not_change_the_ledger(self):
        d = load("ledger_busy.json")
        before = copy.deepcopy(d)
        for mode in sr_render.MODES:
            render(d, identity=ID, mode=mode, no_hero=True)
        self.assertEqual(d, before)

    def test_same_ledger_same_bytes(self):
        d = load("ledger_small.json")
        self.assertEqual(render(d, identity=ID, no_hero=True)["info"]["sha256"], render(d, identity=ID, no_hero=True)["info"]["sha256"])

    def test_bad_mode(self):
        with self.assertRaises(ValueError):
            render(load("ledger_small.json"), identity=ID, mode="fax")


class OneBuildMode(unittest.TestCase):
    """Every build is clean and ready to send. Nothing waits on anyone confirming anything."""

    def test_no_notice_no_panel_no_working_words_in_any_mode(self):
        for name in ("ledger_small.json", "ledger_busy.json"):
            for mode in sr_render.MODES:
                with self.subTest(ledger=name, mode=mode):
                    r = render(load(name), identity=ID, mode=mode, no_hero=True)
                    page, t = r["html"], text_of(r["html"]).lower()
                    for word in ("draft", "do not send", "not for the seller", "for the reviewer", "reviewer", "unreviewed",
                                 "not yet confirmed", "to confirm", "left out of the final", "claude"):
                        self.assertNotIn(word, t)
                    self.assertIsNone(re.search(r"\b(un)?tag(s|ged|ging)?\b", t), "the word tag is never on a page")
                    for hook in ("draft_notice", "reviewer_panel"):
                        self.assertNotIn('data-sr-section="%s"' % hook, page)
                    self.assertNotIn('name="sr:build"', page)
                    self.assertNotIn("#FFE45C", page.upper(), "the yellow of the old notice is gone")
                    for key in ("build_kind", "tag_review", "unreviewed_people", "allowed_unreviewed", "reviewer_notes", "seller_part_bytes"):
                        self.assertNotIn(key, r["info"])

    def test_build_notes_are_never_printed(self):
        d = load("ledger_busy.json")
        d["data_quality"] = ["Synthetic build note number %d, long enough to be found if it were ever printed on a page." % i for i in range(12)]
        d["report"]["as_of_note"] = "Synthetic operator note that no seller may ever read."
        clean(self, d)
        for mode in sr_render.MODES:
            t = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"])
            self.assertNotIn("Synthetic build note", t)
            self.assertNotIn("Synthetic operator note", t)

    def test_render_takes_no_draft_or_final_switch(self):
        for kw in (dict(final=True), dict(allow_unreviewed=True), dict(draft=True)):
            with self.assertRaises(TypeError):
                render(load("ledger_small.json"), identity=ID, **kw)
        self.assertFalse(os.path.exists(os.path.join(SCRIPTS, "sr_render", "review.py")))

    def test_a_photo_or_link_that_is_not_https_is_left_off(self):
        d = load("ledger_small.json")
        for hero in ("assets/hero.jpg", "http://example.com/h.jpg"):
            r = render(d, identity=ID, hero=hero, link_url="record.html")
            self.assertNotIn(hero, r["html"])
            self.assertNotIn("record.html", r["html"])
            self.assertEqual((r["info"]["flags"]["hero"], r["info"]["flags"]["link_url"]), (None, None))
            self.assertEqual(len(r["info"]["warnings"]), 2)
            self.assertIn("Reply to this email and I will send it to you.", text_of(r["html"]))
        r = render(d, identity=ID, **HTTPS)
        self.assertIn(HTTPS["hero"], r["html"])
        self.assertIn(HTTPS["link_url"], r["html"])
        self.assertEqual(r["info"]["warnings"], [])
        render(d, identity=ID, mode="link", no_hero=True)                         # the link copy needs no link to itself

    def test_a_local_path_never_reaches_the_page(self):
        d = load("ledger_small.json")
        d["listing"]["hero_photo"] = r"C:\Users\Someone\Pictures\front.jpg"
        self.assertNotIn("Someone", render(d, identity=ID)["html"])                # not https, so it is not used
        self.assertNotIn("Someone", render(d, identity=ID, hero=d["listing"]["hero_photo"])["html"])

    def test_ledger_https_photo_is_used(self):
        d = load("ledger_small.json")
        d["listing"]["hero_photo"] = HTTPS["hero"]
        self.assertIn(HTTPS["hero"], render(d, identity=ID)["html"])
        self.assertNotIn(HTTPS["hero"], render(d, identity=ID, no_hero=True)["html"])

    def test_a_ledger_that_breaks_the_contract_is_refused(self):
        d = load("ledger_small.json")
        d["totals"]["contacted"] += 1
        with self.assertRaises(RenderRefused) as cm:
            render(d, identity=ID, no_hero=True)
        self.assertEqual(cm.exception.stage, "ledger")
        d = load("ledger_small.json")
        d["recommendation"] = "Lower the price."
        with self.assertRaises(RenderRefused):
            render(d, identity=ID, no_hero=True)


class PageRules(unittest.TestCase):
    """Rules every page keeps, in every mode."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {}
        for name in ("ledger_small.json", "ledger_busy.json"):
            d = load(name)
            for mode in sr_render.MODES:
                cls.pages[(name, mode, "plain")] = render(d, identity=ID, mode=mode, no_hero=True, no_link=True)["html"]
                cls.pages[(name, mode, "photo and link")] = render(d, identity=ID, mode=mode, **HTTPS)["html"]

    def each(self):
        for key, page in sorted(self.pages.items()):
            with self.subTest(page=key):
                yield key, page

    def test_no_dash_characters(self):
        for _, page in self.each():
            self.assertNotIn(EM_DASH, page)
            self.assertNotIn(EN_DASH, page)
            self.assertFalse(C.has_dash(page))

    def test_no_blocked_identity_value(self):
        for _, page in self.each():
            self.assertEqual(C.find_blocked(page, ID), [])

    def test_brand_facts_come_from_identity(self):
        for _, page in self.each():
            t = text_of(page)
            for fact in (ID["name"].upper(), "DRE #" + ID["dre"], ID["brand_line"], ID["phone"], ID["email"], ID["disclaimer"][:60]):
                self.assertIn(fact, t)
            self.assertIn("REALTOR&reg;", page)

    def test_a_blocked_brokerage_is_shortened_on_the_page(self):
        blocked = ID["blocklist"]["brand"][0]                  # read at run time: a blocked value is never typed in code
        d = load("ledger_small.json")
        d["contacts"][0]["brokerage"] = blocked
        clean(self, d)
        for mode in sr_render.MODES:
            page = render(d, identity=ID, mode=mode, no_hero=True)["html"]
            self.assertEqual(C.find_blocked(page, ID), [])
            self.assertIn(blocked.split()[0], text_of(page))

    def test_noindex_and_preheader(self):
        for _, page in self.each():
            self.assertIn('<meta name="robots" content="noindex,nofollow,noarchive">', page)
            self.assertRegex(page, r'<div style="display:none;max-height:0;overflow:hidden[^>]*>[^<]{60,}</div>')

    def test_every_cell_states_its_background_and_dark_cells_their_text_color(self):
        for _, page in self.each():
            body = re.sub(r"<!--\[if mso\]>.*?<!\[endif\]-->", "", page, flags=re.S)
            for cell in re.findall(r"<t[dh]\b[^>]*>", body):
                self.assertIn("bgcolor=", cell)
                if 'bgcolor="#1A1A1A"' in cell or 'bgcolor="#C5A55A"' in cell:          # black and gold never inherit their text color
                    self.assertTrue("color:" in cell or "font-size:0" in cell, cell)
            self.assertIsNone(re.search(r'bgcolor="#[0-9A-Fa-f]{3}"', page))
            # the ink every light cell inherits is set once on the page and again on every section
            self.assertIn('style="padding:0;color:#1A1A1A">', page)

    def test_nothing_under_12_px(self):
        for _, page in self.each():
            sizes = [int(x) for x in re.findall(r"font-size:(\d+)px", page)] + [int(x) for x in re.findall(r"font:\d+ (\d+)px", page)]
            self.assertTrue(sizes)
            self.assertEqual([x for x in sizes if 1 < x < 12], [])

    def test_every_link_is_a_block_at_least_40_px_tall(self):
        for _, page in self.each():
            links = re.findall(r"<a\b[^>]*>", page)
            self.assertGreaterEqual(len(links), 3)
            for a in links:
                self.assertIn("display:block", a)
                pad = int(re.search(r"padding:(\d+)px", a).group(1))
                self.assertGreaterEqual(2 * pad + 18, LIMITS["tap_px"], a)          # two paddings and one line of text

    def test_email_safe_markup_only(self):
        for _, page in self.each():
            low = page.lower()
            for bad in ("<script", "<svg", "display:flex", "display:grid", "position:absolute", "position:fixed", "background-image", "<form"):
                self.assertNotIn(bad, low)
            self.assertLessEqual(max(len(ln) for ln in page.split("\n")), 998)     # the mail line limit

    def test_the_cma_look(self):
        self.assertEqual((P["ink"], P["gold"], P["gold_dark"], P["cream"], P["grey"], P["white"]),
                         ("#1A1A1A", "#C5A55A", "#A88B3D", "#F5EFDC", "#666666", "#FFFFFF"))
        self.assertTrue(F["head"].startswith("Montserrat,") and F["body"].startswith("Inter,"))
        for _, page in self.each():
            self.assertIn('<body style="margin:0;padding:0;background:#FFFFFF">', page)      # a white page, so no band shows beside the column
            self.assertIn("font-family:Inter,", page)
            # section header: a gold left border cell, then gold caps on black
            self.assertRegex(page, r'<td width="6" bgcolor="#C5A55A"[^>]*>&nbsp;</td><td bgcolor="#1A1A1A" style="[^"]*color:#C5A55A;font:800 15px')
            self.assertRegex(page, r'<th bgcolor="#C5A55A"[^>]*style="color:#1A1A1A')              # gold table header rows
            self.assertRegex(page, r'font:800 30px/1\.0 Montserrat[^"]*;color:#C5A55A')               # large gold numbers on black
            for navy in ("#1B2A4A", "#35456B", "#F8F4E8", "Source Sans", "Plus Jakarta", "DM Sans"):
                self.assertNotIn(navy, page)

    def test_web_fonts_only_where_they_load(self):
        for (name, mode, kind), page in self.each():
            self.assertEqual("fonts.googleapis.com" in page, mode != "email")


class FeedbackOnly(unittest.TestCase):
    """D6: the report states what people said. It never suggests a price or asks for a decision."""

    def test_no_recommendation_wording_in_generated_copy(self):
        banned = ["recommend", "from you:", "decision log", "price reduction", "reduce the price", "lower the price", "we suggest",
                  "should consider", "tell us nothing", "tells us nothing", "nobody thinks", "no one thinks", "not the same as buyers agreeing",
                  "where the price should sit", "talk about price", "sample wording"]
        cases = [load("ledger_small.json"), load("ledger_busy.json"), empty_listing(self), with_first_contact(self)]
        for d in cases:
            told = json.dumps(d).lower()
            for mode in sr_render.MODES:
                low = text_of(render(d, identity=ID, mode=mode, no_hero=True)["html"]).lower()
                for wd in banned:
                    self.assertNotIn(wd, told)                 # the fixtures do not use these words, so any hit is generated copy
                    with self.subTest(slug=d["meta"]["slug"], mode=mode, word=wd):
                        self.assertNotIn(wd, low)

    def test_no_code_path_for_a_recommendation(self):
        for root, _, files in os.walk(os.path.join(SCRIPTS, "sr_render")):
            for f in files:
                if f.endswith(".py") and f != "tokens.py":       # tokens.py holds the banned list itself
                    with open(os.path.join(root, f), encoding="utf-8") as fh:
                        src = fh.read().lower()
                    for wd in ("recommendation", "sample_rec", "seller_ask", "decision_log", "statement_safe"):
                        self.assertNotIn(wd, src, "%s mentions %s" % (f, wd))

    def test_generated_wording_that_slips_in_stops_the_build(self):
        d = load("ledger_small.json")
        d["next_week"].append("Talk with the sellers about a price reduction.")     # a person wrote it: allowed, with a warning
        clean(self, d)
        r = render(d, identity=ID, no_hero=True)
        self.assertTrue(any("price reduction" in w for w in r["info"]["warnings"]))
        from sr_render import assemble, sections_more
        real = sections_more.s_next
        try:
            assemble.s_next = lambda m: real(m).replace("What we are doing next week", "We recommend a new price next week")
            with self.assertRaises(RenderRefused) as cm:
                render(load("ledger_small.json"), identity=ID, no_hero=True)
            self.assertEqual(cm.exception.stage, "page")
            self.assertIn("recommend", " ".join(cm.exception.problems))
        finally:
            assemble.s_next = real


class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        r = subprocess.run([sys.executable, "-I", CLI] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")

    def test_email_link_and_print(self):
        src = os.path.join(HERE, "fixtures", "ledger_small.json")
        with tempfile.TemporaryDirectory(prefix="sr render test ") as tmp:              # a path with spaces
            out = os.path.join(tmp, "issue 05", "email.html")
            code, so, se = self.run_cli(src, out, "--no-hero", "--info", os.path.join(tmp, "info.json"))
            self.assertEqual(code, 0, se)
            info = json.loads(so)
            self.assertEqual((info["mode"], info["fit_level"]), ("email", 0))
            self.assertNotIn("build_kind", info)
            with open(out, encoding="utf-8") as f:
                self.assertNotIn("DRAFT", f.read())
            with open(os.path.join(tmp, "info.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["sha256"], info["sha256"])
            for flag, mode in (("--link-copy", "link"), ("--print", "print")):
                code, so, se = self.run_cli(src, os.path.join(tmp, mode + ".html"), flag, "--no-hero")
                self.assertEqual(code, 0, se)
                self.assertEqual(json.loads(so)["mode"], mode)
            code, so, se = self.run_cli(src, out, "--no-hero", "--link-url", HTTPS["link_url"], "--seller-greeting", "Hi Pat,")
            self.assertEqual(code, 0, se)                                               # a rebuild replaces the file
            with open(out, encoding="utf-8") as f:
                page = f.read()
            self.assertIn("Hi Pat,", page)
            self.assertIn(HTTPS["link_url"], page)
            self.assertNotIn("\r\n", page)

    def test_conflicting_and_retired_switches_are_rejected(self):
        src = os.path.join(HERE, "fixtures", "ledger_small.json")
        with tempfile.TemporaryDirectory() as tmp:
            for pair in (("--link-copy", "--print"), ("--hero", "x.jpg", "--no-hero"), ("--link-url", "x", "--no-link"),
                         ("--draft",), ("--final",), ("--allow-unreviewed",), ("--overwrite",)):
                code, _, _ = self.run_cli(src, os.path.join(tmp, "x.html"), *pair)
                self.assertNotEqual(code, 0, pair)
                self.assertFalse(os.path.exists(os.path.join(tmp, "x.html")))

    def test_help_with_no_arguments(self):
        code, so, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("--link-copy", so)
        self.assertIn("one build mode", so)
        for gone in ("--draft", "--final", "--allow-unreviewed", "--overwrite"):
            self.assertNotIn(gone, so)


class Previews(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(render_previews.name_of(r"C:\some folder\issue 05\email.html"), "email")
        self.assertTrue(render_previews.url(r"C:\a b\c#1.html").endswith("/a%20b/c%231.html"))
        self.assertEqual(render_previews.CHECK_WIDTHS, (390, 360, 320))

    def test_pdf_wants_the_print_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = os.path.join(tmp, "email.html")
            with open(page, "w", encoding="utf-8") as f:
                f.write(render(load("ledger_small.json"), identity=ID, no_hero=True)["html"])
            with contextlib.redirect_stdout(io.StringIO()) as said:
                self.assertEqual(render_previews.pdf(page, os.path.join(tmp, "x.pdf")), 1)
            self.assertIn("not built with --print", said.getvalue())
            self.assertFalse(os.path.exists(os.path.join(tmp, "x.pdf")))

    @unittest.skipUnless(os.environ.get("SR_EDGE_TESTS") == "1" and any(os.path.exists(p) for p in render_previews.EDGE_PATHS),
                         "set SR_EDGE_TESTS=1 to run the layout check in Microsoft Edge")
    def test_layout_check_in_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("ledger_small.json", "ledger_busy.json"):
                page = os.path.join(tmp, name.replace(".json", ".html"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(render(load(name), identity=ID, no_hero=True)["html"])
                fails, _ = render_previews.check(page, render_previews.name_of(page))
                self.assertEqual(fails, [])
            out = os.path.join(tmp, "print.html")
            with open(out, "w", encoding="utf-8") as f:
                f.write(render(load("ledger_small.json"), identity=ID, mode="print", no_hero=True)["html"])
            self.assertEqual(render_previews.pdf(out, os.path.join(tmp, "report.pdf")), 0)


class SourceHygiene(unittest.TestCase):
    """The renderer's own files: no dash characters, no blocked value, nothing over the size limit."""

    def files(self):
        out = [CLI, os.path.join(SCRIPTS, "render_previews.py"), os.path.abspath(__file__), os.path.join(HERE, "test_render_content.py")]
        pkg = os.path.join(SCRIPTS, "sr_render")
        return out + [os.path.join(pkg, f) for f in sorted(os.listdir(pkg)) if f.endswith(".py")]

    def test_sources(self):
        for path in self.files():
            with open(path, encoding="utf-8") as f:
                src = f.read()
            with self.subTest(file=os.path.basename(path)):
                self.assertFalse(C.has_dash(src))
                self.assertEqual(C.find_blocked(src, ID), [])
                self.assertLess(len(src.encode("utf-8")), 45000)                    # one clear job per file
                self.assertIsNone(re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", src))    # no stray control character

    def test_no_brand_fact_is_typed_into_the_renderer(self):
        for path in self.files():
            with open(path, encoding="utf-8") as f:
                src = f.read()
            for fact in (ID["dre"], ID["phone"], ID["email"], ID["brand_line"], ID["name"]):
                self.assertNotIn(fact, src, os.path.basename(path))


if __name__ == "__main__":
    unittest.main()
