# -*- coding: utf-8 -*-
"""What the tests of the ship gate share: the edits that break one rule of a clean page, and the harness that
writes a data root, builds the sample page and runs the gate. Used by test_checks.py and test_checks_lists.py.

Every page is built inline from the synthetic fixtures by sr_checks.sample_page, which is not the renderer.
Brand values and blocked values are read from identity.json at run time, never typed here.
"""
import copy
import hashlib
import html
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import check_report                                  # noqa: E402
import sr_checks                                     # noqa: E402
import sr_contract as C                              # noqa: E402  (the data contract, to rebuild a ledger a test edits)
from sr_checks import core, layout_probe, page, recount, sample_page   # noqa: E402

UNDER = ">Follow-up</h2>"
LINK_URL = 'href="https://seller-reports.test/record"'
RAW = {"schema_version": 1, "tabs": [{"kind": "showing", "title": "Showing Activity", "rows": [
    {"name_raw": "Odalys Vantongeren", "phones": ["415-555-0142"], "emails": ["odalys@harborlight.test"],
     "entries": [{"text": "Lockbox code 4471. Call me after 5."}]},
    {"name_raw": "Wilhelmina Rasmussen (Willa)", "phones": ["(408) 555-0177"], "emails": []},
    {"name_raw": "Invited by Thaddeus Kowalczyk", "phones": [], "emails": ["tk@northgate.test"]}]}]}


def val(x, t):
    return x(t) if callable(x) else x


def swap(old, new, count=1):
    """An edit: replace text that must be on the sample page."""
    def edit(h, t):
        o, n = val(old, t), val(new, t)
        assert o in h, "the sample page no longer holds %r" % o[:70]
        return h.replace(o, n, count)
    return edit


def para(text):
    """An edit: one more paragraph a seller would read, right under the Follow-up heading."""
    return lambda h, t: swap(UNDER, UNDER + '<p style="margin:4px 0">' + val(text, t) + "</p>")(h, t)


def cell(marker, index, text):
    """An edit: set the text of the index-th <td> in the table row that holds marker."""
    def edit(h, t):
        at = h.index(marker)
        a, b = h.rindex("<tr", 0, at), h.index("</tr>", at)
        bits = re.split(r"(<td [^>]*>)(.*?)(</td>)", h[a:b], flags=re.S)
        bits[2 + 4 * index] = text
        return h[:a] + "".join(bits) + h[b:]
    return edit


def cut(pattern):
    """An edit: remove the first match of a pattern (across lines)."""
    def edit(h, t):
        out, n = re.subn(pattern, "", h, count=1, flags=re.S)
        assert n == 1, "nothing matched %r" % pattern
        return out
    return edit


def chain(*edits):
    def edit(h, t):
        for e in edits:
            h = e(h, t)
        return h
    return edit


def other_dre(t):
    dre, blocked = t.identity["dre"], set(t.identity["blocklist"]["dre"])
    return next(x for x in (dre[:-1] + ch for ch in "0123456789") if x != dre and x not in blocked)


def comment_of(t, cid="c001"):
    return html.escape(next(c for c in t.ledger["contacts"] if c["id"] == cid)["feedback_safe"])


class GateHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity = core.load_identity(core.default_identity_path())
        cls.fixtures = {}
        for key, name in (("small", "ledger_small.json"), ("busy", "ledger_busy.json")):
            with open(os.path.join(HERE, "fixtures", name), encoding="utf-8") as f:
                cls.fixtures[key] = json.load(f)
        cls.clean = {}

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sr-gate-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def gate(self, fx="small", kind="email", hooks=True, edit=None, led=None, args=(), listing=None, file=None,
             raw=True, manifest=None, git=False, allow_synthetic=True, subfolder=None, **_):
        """Writes a data root with the listing and one other listing, builds the page, runs the gate."""
        d = copy.deepcopy(self.fixtures[fx])
        if led:
            led(d, self)
        self.ledger = d
        slug, n = d["meta"]["slug"], d["report"]["issue_number"]
        root = os.path.join(self.tmp, "root")
        folder = os.path.join(root, slug, "issues", "%02d" % n, *([subfolder] if subfolder else []))
        os.makedirs(folder)
        os.makedirs(os.path.join(root, "other-oak"))
        if git:
            os.makedirs(os.path.join(self.tmp, ".git"))
        L = dict(d["listing"], seller_first_names=["Pat", "Sam"], keybox_number="88123456")
        if listing:
            listing(L)
        files = {os.path.join(root, slug, "listing.json"): L, os.path.join(folder, "ledger.json"): d,
                 os.path.join(root, "other-oak", "listing.json"): {"slug": "other-oak", "address": "77 Other Oak Dr", "mls": "ML00000077"}}
        if raw:
            files[os.path.join(root, slug, "raw.json")] = dict(RAW, slug=slug)
        for path, data in files.items():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        text = sample_page.build(d, self.identity, kind=kind, hooks=hooks)
        if edit:
            text = edit(text, self)
        path = os.path.join(folder, file or kind + ".html")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if manifest is not None:
            with open(path, "rb") as f:
                body = f.read()
            m = {"schema_version": 1, "slug": slug, "issue_number": n, "report_date": d["report"]["report_date"],
                 "week_start": d["report"]["week_start"], "week_end": d["report"]["week_end"],
                 "ledger_sha256": core.sha256_file(os.path.join(folder, "ledger.json")),
                 "files": [{"name": os.path.basename(path), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}],
                 "email_bytes": len(body) if kind == "email" else None,
                 "flags": {"link_url": manifest.get("link_url") or "https://seller-reports.test/record"}}
            if manifest.get("build_kind"):
                m["build_kind"] = manifest["build_kind"]
            with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(m, f)
            if manifest.get("tamper"):
                with open(path, "a", encoding="utf-8", newline="\n") as f:
                    f.write("<!-- edited after the snapshot -->\n")
        self.folder, self.path = folder, path
        argv = (["--issue", folder] if not file else [path, "--ledger", os.path.join(folder, "ledger.json"), "--kind", kind])
        argv += ["--today", d["report"]["report_date"]] + (["--allow-synthetic"] if allow_synthetic else []) + list(args)
        self.argv = argv
        a = check_report.parse_args(argv)
        ctxs, waivers = check_report.build_contexts(a)
        return sr_checks.run(ctxs[0], families=a.only.split(",") if a.only else None, waivers=waivers)

    def assertClean(self, rep):
        self.assertTrue(rep.ok, rep.as_text())

    def baseline(self, fx="small", kind="email", hooks=True, **_):
        key = (fx, kind, hooks)
        if key not in self.clean:
            self.clean[key] = self.gate(fx=fx, kind=kind, hooks=hooks)
            shutil.rmtree(os.path.join(self.tmp, "root"))
        self.assertClean(self.clean[key])

    def run_case(self, s):
        self.baseline(**s)                                          # the same page, untouched, passes
        if s.get("led") and not s.get("led_breaks"):
            self.assertClean(self.gate(**dict(s, edit=None)))       # and so does the edited ledger on its own
            shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(**s)
        failing = set(r.id for r in rep.blocking)
        self.assertIn(s["rule"], failing, rep.as_text())
        families = set(r.family for r in rep.blocking)
        self.assertLessEqual(families, set([s["rule"].split(".")[0]]) | set(s.get("also", ())), rep.as_text())
        hit = next(r for r in rep.blocking if r.id == s["rule"])
        self.assertTrue(hit.message, "a failure must say what is wrong")


def top(text):
    """An edit: one more paragraph near the top of the page, right under the numbers heading."""
    under = ">The numbers</h2>"
    return lambda h, t: swap(under, under + '<p style="margin:4px 0">' + val(text, t) + "</p>")(h, t)


def add_cases(cls, cases):
    """Turns each case (one broken rule, and the rule that must catch it) into a test method of cls."""
    def make(spec):
        def test(self):
            self.run_case(spec)
        test.__doc__ = "%s is caught by %s" % (spec["name"].replace("_", " "), spec["rule"])
        return test
    for spec in cases:
        assert not hasattr(cls, "test_catches_" + spec["name"]), spec["name"]
        setattr(cls, "test_catches_" + spec["name"], make(spec))
