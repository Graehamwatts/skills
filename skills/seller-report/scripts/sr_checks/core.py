# -*- coding: utf-8 -*-
"""sr_checks.core: the result type, the run context and the report of the seller-report ship gate.

The gate stands between a build and a seller. It reads the built HTML file and the data the build was made
from (ledger.json, listing.json, raw.json, identity.json, manifest.json) and nothing else. It never imports
the renderer, so a mistake in the renderer cannot hide itself here.

Standard library only. No real client data belongs in this file.
"""
import hashlib
import json
import os
import re

from . import page as P

PASS, FAIL, WARN, SKIP, INFO = "pass", "fail", "warn", "skip", "info"
LEVELS = (PASS, FAIL, WARN, SKIP, INFO)
KINDS = ("email", "link", "print")

DASH_CHARS = "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015))
NBSP = chr(0xA0)
REG = chr(0xAE)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec")
MONTHS_LONG = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December")


class GateInputError(Exception):
    """A file the gate needs is missing or unreadable. The CLI exits with code 2."""


class Result(object):
    """One rule, one verdict, with the evidence that decided it."""
    __slots__ = ("family", "rule", "level", "message", "evidence", "waivable", "waived")

    def __init__(self, family, rule, level, message, evidence=None, waivable=False):
        self.family, self.rule, self.level, self.message = family, rule, level, message
        self.evidence = [str(e) for e in (evidence or [])]
        self.waivable, self.waived = waivable, None

    @property
    def id(self):
        return "%s.%s" % (self.family, self.rule)

    def as_dict(self):
        d = {"id": self.id, "family": self.family, "rule": self.rule, "level": self.level,
             "message": self.message, "evidence": self.evidence}
        if self.waived:
            d["waived"] = self.waived
        return d


class Bag(object):
    """Collects the results of one family of checks."""

    def __init__(self, family):
        self.family, self.results = family, []

    def add(self, rule, level, message, evidence=None, waivable=False):
        r = Result(self.family, rule, level, message, evidence, waivable)
        self.results.append(r)
        return r

    def ok(self, rule, message, evidence=None):
        return self.add(rule, PASS, message, evidence)

    def fail(self, rule, message, evidence=None, waivable=False):
        return self.add(rule, FAIL, message, evidence, waivable)

    def warn(self, rule, message, evidence=None):
        return self.add(rule, WARN, message, evidence)

    def skip(self, rule, message, evidence=None):
        return self.add(rule, SKIP, message, evidence)

    def info(self, rule, message, evidence=None):
        return self.add(rule, INFO, message, evidence)

    def judge(self, rule, bad, ok_message, fail_message, level=FAIL, waivable=False, limit=12):
        """bad: a list of evidence strings. Empty means the rule passed."""
        bad = list(bad)
        if not bad:
            return self.ok(rule, ok_message)
        ev = bad[:limit] + (["and %d more" % (len(bad) - limit)] if len(bad) > limit else [])
        return self.add(rule, level, "%s (%d)" % (fail_message, len(bad)), ev, waivable)


# ---------------------------------------------------------------------------------------------
# small helpers shared by the families
# ---------------------------------------------------------------------------------------------
def squash(s):
    """Whitespace collapsed to single spaces, non-breaking spaces included."""
    return re.sub(r"\s+", " ", (s or "").replace(NBSP, " ")).strip()


def fold(s):
    """squash + lower case, with curly quotes straightened. For 'is this text on the page' tests."""
    s = squash(s).lower()
    for a, b in ((chr(0x2018), "'"), (chr(0x2019), "'"), (chr(0x201C), '"'), (chr(0x201D), '"')):
        s = s.replace(a, b)
    return s


def excerpt(text, start, end=None, pad=45):
    """A short slice of text around a match, for evidence lines."""
    end = start if end is None else end
    a, b = max(0, start - pad), min(len(text), end + pad)
    return ("..." if a else "") + squash(text[a:b]) + ("..." if b < len(text) else "")


def mask_tail(s, keep=2):
    """'650-555-0142' -> '**********42'. Evidence never repeats a private value in full."""
    s = str(s)
    return "*" * max(0, len(s) - keep) + s[-keep:]


def mask_email(s):
    name, _, dom = str(s).partition("@")
    return (name[:1] + "***@" + dom) if dom else mask_tail(s)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise GateInputError("cannot read %s (%s): %s" % (what, path, e))


def fmt_day(iso, long_month=False):
    """'2026-10-05' -> 'Oct 5' (or 'October 5')."""
    y, m, d = (int(x) for x in iso[:10].split("-"))
    return "%s %d" % ((MONTHS_LONG if long_month else MONTHS)[m - 1], d)


def money_forms(v):
    """Every way a whole-dollar amount is likely to be printed: 710000 -> $710,000, 710,000, 710000, $710K."""
    v = int(round(v))
    out = ["${:,}".format(v), "{:,}".format(v), str(v)]
    if v >= 1000:
        k = v / 1000.0
        out += ["$%dK" % round(k), "$%dk" % round(k)] if abs(k - round(k)) < 1e-9 else ["$%.1fK" % k, "$%.1fk" % k]
    if v >= 1000000:
        out.append("$%sM" % ("%.2f" % (v / 1000000.0)).rstrip("0").rstrip("."))
    return out


def load_identity(path):
    """The brand facts and the blocklist, read from identity.json at run time. Nothing here is typed in code."""
    raw = read_json(path, "identity.json")
    idn, blk = raw.get("identity") or {}, raw.get("_blocked_values") or {}
    title = idn.get("title") or "REALTOR"
    tag = idn.get("tagline") or {}
    return {
        "name": idn.get("name"), "title": title,
        "realtor_line": title if title.endswith(REG) else title + REG,
        "brokerage": idn.get("brokerage"), "team": idn.get("team"), "brand_line": idn.get("brand_line"),
        "dre": idn.get("dre"), "phone": idn.get("phone"), "email": idn.get("email"), "website": idn.get("website"),
        "disclaimer": (idn.get("cobrand_lockup") or {}).get("compass_required_disclaimer") or "",
        "retired_taglines": [t for t in (tag.get("retired") or []) if isinstance(t, str)],
        "blocklist": {"dre": [v for v in blk.get("dre_blocklist") or [] if v],
                      "brand": [v for v in blk.get("brand_blocklist") or [] if v]},
        "path": path,
    }


def default_identity_path():
    here = os.path.dirname(os.path.abspath(__file__))            # .../seller-report/scripts/sr_checks
    skills = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    return os.path.join(skills, "shared-references", "identity.json")


# ---------------------------------------------------------------------------------------------
# the run context
# ---------------------------------------------------------------------------------------------
class Ctx(object):
    """Everything one check run reads. Built once per HTML file.

    html_path     the built page
    ledger        ledger.json as rendered (required)
    listing       listing.json, or None (then ledger.listing stands in and the gate says so)
    raw           raw.json (PRIVATE), or None
    identity      load_identity(...) result
    manifest      manifest.json of the issue, or None
    kind          email | link | print
    data_root     the folder that holds one folder per listing, or None
    opts          dict of operator switches (see check_report.py)
    """

    def __init__(self, html_path, ledger, identity, kind, listing=None, raw=None, manifest=None,
                 data_root=None, ledger_path=None, manifest_path=None, opts=None, notes=None):
        self.html_path = os.path.abspath(html_path)
        self.file_name = os.path.basename(self.html_path)
        try:
            with open(self.html_path, "rb") as f:
                self.raw_bytes = f.read()
        except OSError as e:
            raise GateInputError("cannot read the page (%s): %s" % (html_path, e))
        self.source = self.raw_bytes.decode("utf-8", "replace")
        self.page = P.Page(self.source)
        self.ledger, self.identity, self.kind = ledger, identity, kind
        self.listing, self.raw, self.manifest, self.data_root = listing, raw, manifest, data_root
        self.ledger_path, self.manifest_path = ledger_path, manifest_path
        self.opts = dict(opts or {})
        self.notes = list(notes or [])              # how kind and inputs were resolved
        self._cache = {}

    # -- regions of the page ---------------------------------------------------------------
    def seller_text(self):
        """What a seller could read: all of the body text, the hidden preheader included. There is one build
        mode, so every word on a page is the seller's to read and every check reads the whole page."""
        if "seller_text" not in self._cache:
            self._cache["seller_text"] = self.page.text()
        return self._cache["seller_text"]

    def seller_flat(self):
        if "seller_flat" not in self._cache:
            self._cache["seller_flat"] = squash(self.seller_text())
        return self._cache["seller_flat"]

    def section_text(self, *names):
        """Text of the named sections (data-sr-section), or None when the page carries no such hook."""
        nodes = [n for nm in names for n in self.page.sections(nm)]
        if not nodes:
            return None
        return squash(" \n ".join(self.page.text(root=n) for n in nodes))

    # -- data helpers ----------------------------------------------------------------------
    def address(self):
        return ((self.listing or {}).get("address") or (self.ledger.get("listing") or {}).get("address") or "")

    def counted(self):
        return [c for c in self.ledger.get("contacts") or [] if not c.get("team_side") and not c.get("represented_by")]



# ---------------------------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------------------------
class Report(object):
    def __init__(self, ctx, results):
        self.ctx, self.results = ctx, list(results)

    def count(self, level):
        return len([r for r in self.results if r.level == level])

    @property
    def blocking(self):
        return [r for r in self.results if r.level == FAIL]

    @property
    def ok(self):
        return not self.blocking

    def as_dict(self):
        c = self.ctx
        return {
            "file": c.html_path, "kind": c.kind, "bytes": len(c.raw_bytes),
            "ok": self.ok, "blocking": len(self.blocking),
            "counts": dict((lv, self.count(lv)) for lv in LEVELS),
            "notes": c.notes,
            "results": [r.as_dict() for r in self.results],
        }

    def as_text(self, verbose=False):
        c = self.ctx
        out = ["%s  [%s, %s bytes]" % (c.html_path, c.kind, "{:,}".format(len(c.raw_bytes)))]
        out += ["  note: " + n for n in c.notes]
        fam = None
        quiet = 0
        for r in self.results:
            if not verbose and (r.level == PASS or (r.level == SKIP and r.family == "numbers")):
                quiet += r.level == SKIP
                continue
            if r.family != fam:
                fam = r.family
                out.append("  [%s]" % fam)
            tag = {PASS: "pass", FAIL: "FAIL", WARN: "warn", SKIP: "skip", INFO: "info"}[r.level]
            out.append("    %s  %-34s %s" % (tag, r.id, r.message))
            for e in r.evidence:
                out.append("            - " + e)
            if r.waived:
                out.append("            waived by the operator: " + r.waived)
        if quiet:
            out.append("  %d supporting numbers were not located on the page, so they were not checked (-v lists them and the "
                       "data-sr hook each one needs)" % quiet)
        out.append("  %s: %d blocking, %d warnings, %d passed, %d skipped"
                   % ("OK TO GO ON" if self.ok else "BLOCKED", len(self.blocking), self.count(WARN), self.count(PASS),
                      self.count(SKIP)))
        return "\n".join(out)


def apply_waivers(results, waivers):
    """waivers: {rule id: reason}. Only a rule marked waivable can be waived; the failure becomes a warning and
    the reason is printed with it. Returns the ids that were asked for and could not be waived."""
    refused = []
    for rid, reason in (waivers or {}).items():
        hit = [r for r in results if r.id == rid]
        for r in hit:
            if r.level != FAIL:
                continue
            if r.waivable and (reason or "").strip():
                r.level, r.waived = WARN, reason.strip()
            else:
                refused.append(rid)
    return sorted(set(refused))
