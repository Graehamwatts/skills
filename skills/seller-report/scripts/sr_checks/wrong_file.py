# -*- coding: utf-8 -*-
"""sr_checks.wrong_file: this is the right file, for the right home, issue and week.

An older report went out as a sample file under a real name. These rules make that impossible:
  file_name        the file name and title do not start with SAMPLE, MOCKUP or DRAFT
  kind_and_build   the file is the kind and build the page itself says it is
  address          the address on the page equals listing.json
  issue            the issue number on the page equals ledger.report.issue_number
  week             the week on the page is ledger.report's Monday to Sunday week
  greeting         a greeting names this listing's sellers and nobody else
  one_build_mode   the ledger and the manifest carry no review state and no build kind
  synthetic        test data never goes to a seller, and real data never sits inside the skills repo
  manifest         the file's hash, size, issue and week equal the snapshot manifest, when one is given
"""
import datetime
import os
import re

from . import core
from .page import numbers_in

BAD_START = re.compile(r"^[\W_]*(sample|mockup|mock-up|draft|test|example|template|copy of|untitled)\b", re.I)
RANGE = re.compile(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2})(?:, \d{4})? to "
                   r"((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? )?\d{1,2})\b")
GREETING = re.compile(r"\b(?:Hi|Hello|Dear|Good morning|Good afternoon)[ ,]+([A-Z][a-z]+(?:(?:,| and| &) [A-Z][a-z]+)*)\s*[,:.!]")


def day_forms(iso):
    """Ways a day is printed: 'Sept 28', 'Sep 28', 'September 28'."""
    short = core.fmt_day(iso)
    return set((short, short.replace("Sept ", "Sep "), core.fmt_day(iso, long_month=True)))


def week_forms(ws, we):
    out = set()
    for a in day_forms(ws):
        for b in day_forms(we):
            out.add("%s to %s" % (a, b))
        if ws[:7] == we[:7]:
            out.add("%s to %d" % (a, int(we[8:10])))
    return out


def _strings(node):
    if isinstance(node, dict):
        for v in node.values():
            for s in _strings(v):
                yield s
    elif isinstance(node, list):
        for v in node:
            for s in _strings(v):
                yield s
    elif isinstance(node, str):
        yield node


def _norm_day(text):
    mt = re.match(r"([A-Za-z]+)\.? (\d{1,2})", text)
    return "%s %s" % (mt.group(1)[:3].lower(), int(mt.group(2))) if mt else text.lower()


def in_git_repo(path):
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(40):
        if os.path.exists(os.path.join(d, ".git")):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up
    return None


def check(ctx):
    B = core.Bag("wrong_file")
    page, d = ctx.page, ctx.ledger
    R, M = d.get("report") or {}, d.get("meta") or {}
    whole = page.text()
    flat = core.squash(whole)

    # ---- file name and title ----------------------------------------------------------------
    bad = []
    for label, value in (("the file name", ctx.file_name), ("the title", page.title)):
        mt = BAD_START.match(value or "")
        if mt:
            bad.append("%s starts with '%s': %s" % (label, mt.group(1).upper(), (value or "")[:70]))
    parts = [p.lower() for p in re.split(r"[\\/]", ctx.html_path)]
    if "draft" in parts[-3:-1]:
        bad.append("the file sits inside a folder named 'draft'. There is one build and it lives in the issue folder")
    if not page.title:
        bad.append("the page has no title")
    B.judge("file_name", bad, "the file name and the title read as the real report", "the file is named or titled as something else")

    # ---- the page says what it is ---------------------------------------------------------------
    bad = []
    said_kind = page.metas.get("sr:kind")
    if said_kind and said_kind != ctx.kind:
        bad.append("the page says it is the %s copy (meta sr:kind); it is being checked as %s" % (said_kind, ctx.kind))
    stem = os.path.splitext(ctx.file_name)[0].lower()
    if stem in core.KINDS and stem != ctx.kind:
        bad.append("the file is named %s and is being checked as the %s copy" % (ctx.file_name, ctx.kind))
    slugs = [("ledger.meta.slug", M.get("slug")), ("ledger.listing.slug", (d.get("listing") or {}).get("slug")),
             ("listing.json", (ctx.listing or {}).get("slug")), ("manifest", (ctx.manifest or {}).get("slug")),
             ("the page (meta sr:slug)", page.metas.get("sr:slug")), ("the listing folder", ctx.opts.get("slug_dir_name"))]
    known = [(w, s) for w, s in slugs if s]
    if len(set(s for _, s in known)) > 1:
        bad.append("the slugs do not agree: " + ", ".join("%s=%s" % x for x in known))
    B.judge("kind_and_listing", bad, "the file is the %s copy of listing '%s'" % (ctx.kind, M.get("slug")),
            "the file is not what it is being shipped as")

    # ---- address ------------------------------------------------------------------------------
    led_addr = (d.get("listing") or {}).get("address") or ""
    bad = []
    if ctx.listing is None:
        B.add("listing_json", core.FAIL,
              "listing.json was not given, so the address was compared with the ledger only",
              ["pass --listing <listing folder>\\listing.json"])
        addr = led_addr
    else:
        addr = ctx.listing.get("address") or ""
        if core.fold(addr) != core.fold(led_addr):
            bad.append("listing.json says '%s', the ledger was built for '%s'" % (addr, led_addr))
    if not addr:
        bad.append("no address on record to compare the page with")
    else:
        hooks = page.hooks("address")
        for n in hooks:
            if core.fold(page.flat(root=n)) != core.fold(addr):
                bad.append("data-sr=address prints '%s'; the listing is '%s'" % (page.flat(root=n)[:70], addr))
        if not hooks and core.fold(addr) not in core.fold(flat):
            bad.append("'%s' is not printed on the page" % addr)
        if core.fold(addr) not in core.fold(page.title) and re.search(r"\d{2,6} [A-Z]", page.title or ""):
            bad.append("the title names a different address: '%s'" % page.title[:80])
    B.judge("address", bad, "the address on the page is %s" % addr, "the address on the page is not this listing's")

    # ---- issue number ---------------------------------------------------------------------------
    issue, bad, seen = R.get("issue_number"), [], 0
    for n in page.hooks("issue"):
        seen += 1
        if numbers_in(page.flat(root=n)) != [issue]:
            bad.append("data-sr=issue prints '%s'; this is issue %s" % (page.flat(root=n)[:40], issue))
    for label, text in (("the title", page.title), ("the masthead", flat[:900])):
        mt = re.search(r"\b(?:No\.|Issue|Report)\s*#?\s*0*(\d{1,3})\b", text or "")
        if mt:
            seen += 1
            if int(mt.group(1)) != issue:
                bad.append("%s says '%s'; the ledger says issue %s" % (label, mt.group(0), issue))
    for label, value in (("the page (meta sr:issue)", page.metas.get("sr:issue")), ("the manifest", (ctx.manifest or {}).get("issue_number")),
                         ("the issue folder", ctx.opts.get("issue_dir_number"))):
        if value not in (None, "") and str(value).lstrip("0") != str(issue):
            bad.append("%s says issue %s; the ledger says %s" % (label, value, issue))
    if not seen:
        bad.append("the issue number (%s) is not printed in the title or the masthead" % issue)
    B.judge("issue", bad, "issue No. %s, on the page and in the ledger" % issue, "the issue number does not match the ledger")

    # ---- the week -----------------------------------------------------------------------------
    ws, we, rd = R.get("week_start"), R.get("week_end"), R.get("report_date")
    bad = []
    try:
        a, b, c = (datetime.date(*[int(x) for x in s[:10].split("-")]) for s in (ws, we, rd))
        if a.weekday() != 0 or (b - a).days != 6 or (c - b).days != 1:
            bad.append("the ledger's week is not Monday to Sunday with the report dated the Monday after (%s, %s, %s)" % (ws, we, rd))
    except (TypeError, ValueError, AttributeError):
        bad.append("the ledger's week dates are not ISO dates (%r, %r, %r)" % (ws, we, rd))
    if not bad:
        forms = week_forms(ws, we)
        hooks = page.hooks("week")
        for n in hooks:
            if not any(f in page.flat(root=n) for f in forms):
                bad.append("data-sr=week prints '%s'; the week is %s to %s" % (page.flat(root=n)[:50], core.fmt_day(ws), core.fmt_day(we)))
        top = (page.title or "") + " \n " + flat[:1200]
        if not hooks and not any(f in flat for f in forms):
            bad.append("the week %s to %s is not printed on the page" % (core.fmt_day(ws), core.fmt_day(we)))
        first = RANGE.search(top)
        if first and (_norm_day(first.group(1)) != _norm_day(core.fmt_day(ws))):
            bad.append("the masthead gives the week as '%s'; the ledger covers %s to %s" % (first.group(0), core.fmt_day(ws), core.fmt_day(we)))
        typed = core.fold(" \n ".join(_strings(d)))            # ranges the team wrote themselves are not the report week
        for mt in RANGE.finditer(flat):                      # a 'Mon D to Mon D' range that opens on this week's Monday ends on its Sunday
            if not re.match(r"[A-Za-z]", mt.group(2)) or core.fold(mt.group(0)) in typed:
                continue
            if _norm_day(mt.group(1)) == _norm_day(core.fmt_day(ws)) and _norm_day(mt.group(2)) != _norm_day(core.fmt_day(we)):
                bad.append("'%s': the week that starts %s ends %s" % (mt.group(0), core.fmt_day(ws), core.fmt_day(we)))
        for mt in re.finditer(r"\bIssued (?:[A-Z][a-z]+, )?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2})\b", flat):
            if _norm_day(mt.group(1)) != _norm_day(core.fmt_day(rd)):
                bad.append("the page says '%s'; the report is dated %s" % (mt.group(0), core.fmt_day(rd)))
        listed = (d.get("listing") or {}).get("list_date")
        for mt in re.finditer(r"\bListed (?:on )?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2})\b", flat[:2500]):
            if listed and _norm_day(mt.group(1)) != _norm_day(core.fmt_day(listed)):
                bad.append("the page says '%s'; the home was listed %s" % (mt.group(0), core.fmt_day(listed)))
        said = page.metas.get("sr:week")
        if said and said != "%s/%s" % (ws, we):
            bad.append("the page says week %s (meta sr:week); the ledger says %s/%s" % (said, ws, we))
        mf = ctx.manifest or {}
        for k, v in (("week_start", ws), ("week_end", we), ("report_date", rd)):
            if mf.get(k) and mf[k] != v:
                bad.append("the manifest's %s is %s; the ledger's is %s" % (k, mf[k], v))
        if not any(f in flat for f in day_forms(rd)):
            B.warn("report_date", "the report date (%s) is not printed on the page" % core.fmt_day(rd))
    B.judge("week", bad, "the week on the page is %s to %s" % (core.fmt_day(ws) if ws else "?", core.fmt_day(we) if we else "?"),
            "the week on the page does not match the ledger")
    today = ctx.opts.get("today")
    if today and rd and not bad:
        gap = (datetime.date(*[int(x) for x in today[:10].split("-")]) - c).days
        if gap < 0 or gap > 13:
            B.warn("freshness", "the report is dated %s and today is %s (%d days apart). Is this the issue you mean to send?"
                   % (rd, today, gap))

    # ---- greeting -----------------------------------------------------------------------------
    names = (ctx.listing or {}).get("seller_first_names") or (d.get("listing") or {}).get("seller_first_names")
    mt = GREETING.search(ctx.seller_flat()[:2500])
    if mt:
        greeted = re.split(r", | and | & ", mt.group(1))
        if names is None:
            B.warn("greeting", "the page greets %s, and no seller_first_names are on record to compare with" % mt.group(1))
        else:
            wrong = [g for g in greeted if g not in names and g not in ("there", "All", "Everyone")]
            B.judge("greeting", ["the page greets %s; the sellers on record are %s" % (", ".join(wrong), ", ".join(names))] if wrong else [],
                    "the greeting names this listing's sellers", "the greeting names someone who is not this listing's seller")

    # ---- one build mode; test data stays test data ---------------------------------------------------
    stale = ["ledger.meta.%s" % k for k in ("tag_review", "confirmed_by", "confirmed_on") if k in M]
    stale += ["manifest.%s" % k for k in ("build_kind", "tag_review") if k in (ctx.manifest or {})]
    B.judge("one_build_mode", stale, "the ledger and the manifest carry no review state and no build kind",
            "the data still carries a review state or a build kind. Rebuild it with the current scripts")
    synthetic = bool(M.get("synthetic"))
    bad = []
    if synthetic and not ctx.opts.get("allow_synthetic"):
        bad.append("the ledger is marked synthetic (test data)")
    repo = in_git_repo(ctx.html_path)
    if repo and not synthetic:
        bad.append("real listing data is being built inside a git repository (%s). Reports are built under the private "
                   "seller-reports folder" % repo)
    B.judge("synthetic", bad, "test data and real data are each where they belong",
            "test data is headed to a seller, or real data sits in a repository")

    # ---- the snapshot manifest ------------------------------------------------------------------
    mf = ctx.manifest
    if mf is None:
        B.skip("manifest", "no manifest was given, so the file's hash was not compared with a snapshot")
        return B.results
    bad = []
    entry = next((f for f in mf.get("files") or [] if f.get("name") == ctx.file_name), None)
    if entry is None:
        bad.append("the manifest lists no file named %s" % ctx.file_name)
    else:
        digest = core.sha256_file(ctx.html_path)
        if entry.get("sha256") != digest:
            bad.append("the file's sha256 is %s...; the manifest recorded %s..." % (digest[:16], str(entry.get("sha256"))[:16]))
        if entry.get("bytes") is not None and entry["bytes"] != len(ctx.raw_bytes):
            bad.append("the file is %d bytes; the manifest recorded %s" % (len(ctx.raw_bytes), entry["bytes"]))
    if ctx.ledger_path and mf.get("ledger_sha256") and mf["ledger_sha256"] != core.sha256_file(ctx.ledger_path):
        bad.append("the ledger file is not the one the manifest was written for (ledger_sha256 differs)")
    if ctx.kind == "email" and mf.get("email_bytes") is not None and mf["email_bytes"] != len(ctx.raw_bytes):
        bad.append("the manifest's email_bytes is %s; the file is %d bytes" % (mf["email_bytes"], len(ctx.raw_bytes)))
    B.judge("manifest", bad, "the file is byte for byte the one in the snapshot manifest",
            "the file is not the one the snapshot manifest describes")
    return B.results
