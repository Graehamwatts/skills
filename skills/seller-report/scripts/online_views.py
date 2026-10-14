# -*- coding: utf-8 -*-
r"""online_views: weekly online views and saves per portal, kept per listing so they build up week by week.

    python online_views.py add  --folder "<listing folder>" --portal Zillow --views 812 --saves 31 --counts since_listing
    python online_views.py add  --folder "<listing folder>" --portal Redfin --views 65 --counts week --week 2026-04-06
    python online_views.py plan --folder "<listing folder>" --portal Zillow --asked
    python online_views.py add  --folder "<listing folder>" --result "<what portal_views.js returned>.json"
    python online_views.py skip --folder "<listing folder>" --portal Zillow --reason captcha
    python online_views.py show --folder "<listing folder>"

Optional. The report prints online views only when a figure is on file, and builds fully without one.

Two ways in. The operator types the numbers ("add" with --views), or, when asked, Claude opens the listing's
public page on a portal and runs scripts\web\portal_views.js there, which returns {portal, views, saves, as_of}
and nothing else ("plan" first, then "add --result"). At most ONE page per portal per issue (sr_lookups). When
the page is blocked or shows a human check, stop, run "skip", and the report is built without that portal.

What a figure counts. A site shows a running count since the home was listed (--counts since_listing). The
week's own figure is then the difference between two readings a week apart, so a portal's first reading gives
the "since we listed" number and no weekly bar yet. A figure typed for one week only is --counts week.

The file is online_views.json in the listing folder (references/extras.md):

    {"schema_version": 1, "slug": "...", "lookups": [...],
     "rows": [{"week_start": "2026-04-06", "portal": "Zillow", "views": 812, "saves": 31,
               "counts": "since_listing", "as_of": "2026-04-13", "source": "operator"}]}

One row per week per portal: a later figure for the same week and portal replaces the earlier one.
ledger_block() turns the rows into ledger.online (references/data-contract.md, section 6).
Standard library only. No real client data belongs in this file.
"""
import argparse
import datetime
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sr_contract as C          # noqa: E402
import sr_files as F             # noqa: E402
import sr_lookups as LK          # noqa: E402

EXIT_OK, EXIT_INPUT, EXIT_REFUSED = 0, 2, 4
PORTALS = {"zillow": "Zillow", "redfin": "Redfin", "realtor.com": "Realtor.com", "realtor": "Realtor.com", "homes.com": "Homes.com",
           "homes": "Homes.com", "trulia": "Trulia", "compass": "Compass", "mlslistings": "MLSListings"}
SNIPPET = os.path.join(_HERE, "web", "portal_views.js")


def portal_name(text):
    s = " ".join(str(text or "").split())
    if not s:
        raise SystemExit("a portal name is needed, for example Zillow or Redfin")
    return PORTALS.get(s.lower(), s)


def blank_store(slug):
    return {"schema_version": C.SCHEMA_VERSION, "slug": slug, "rows": [], "lookups": []}


def load(folder, slug=None):
    return F.load_json(F.listing_paths(folder)["online_views"], default=blank_store(slug))


def save(folder, store):
    store["rows"].sort(key=lambda r: (r["week_start"], r["portal"]))
    return F.save_json(F.listing_paths(folder)["online_views"], store)


def _count(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def validate_store(store):
    """Problems in online_views.json, as plain strings. Empty when the file is clean."""
    P = []
    if not isinstance(store, dict) or not isinstance(store.get("rows"), list):
        return ["online_views.json: needs a rows list"]
    seen = set()
    for i, r in enumerate(store["rows"]):
        q = "rows[%d]" % i
        if not isinstance(r, dict):
            P.append("%s: not an object" % q)
            continue
        try:
            ws = C.parse_date(r.get("week_start"))
            ok_week = ws is not None and ws.weekday() == 0
        except ValueError:
            ok_week = False
        if not ok_week:
            P.append("%s.week_start: the Monday of the week the figure belongs to" % q)
        if not isinstance(r.get("portal"), str) or not r["portal"].strip():
            P.append("%s.portal: missing" % q)
        if not _count(r.get("views")) and r.get("views") is not None:
            P.append("%s.views: a whole number, or null" % q)
        if not _count(r.get("saves")) and r.get("saves") is not None:
            P.append("%s.saves: a whole number, or null" % q)
        if r.get("views") is None and r.get("saves") is None:
            P.append("%s: holds no figure" % q)
        if r.get("counts") not in C.ONLINE_COUNTS:
            P.append("%s.counts: one of %s" % (q, ", ".join(C.ONLINE_COUNTS)))
        if r.get("source") not in C.ONLINE_SOURCES:
            P.append("%s.source: one of %s" % (q, ", ".join(C.ONLINE_SOURCES)))
        try:
            if C.parse_date(r.get("as_of")) is None:
                raise ValueError
        except ValueError:
            P.append("%s.as_of: the day the figure was read (an ISO date)" % q)
        key = (r.get("week_start"), r.get("portal"))
        if key in seen:
            P.append("%s: a second row for %s in the week of %s (one row per week per portal)" % (q, key[1], key[0]))
        seen.add(key)
    for i, x in enumerate(store.get("lookups") or []):
        if x.get("outcome") not in C.LOOKUP_OUTCOMES or not x.get("report_date") or not x.get("key"):
            P.append("lookups[%d]: needs report_date, key and an outcome (%s)" % (i, ", ".join(C.LOOKUP_OUTCOMES)))
    return P


def default_week(as_of):
    """The Monday of the week a reading belongs to when nobody says: the week that ends on a Sunday reading,
    otherwise the last week that had fully ended (the week the report being built covers)."""
    d = C.parse_date(as_of)
    return C.week_start(d) if d.weekday() == 6 else C.report_week(d)[0]


def add_row(store, portal, views, saves, counts, as_of, week=None, source="operator"):
    """Files one figure. Returns the row. A row for the same week and portal is replaced."""
    if counts not in C.ONLINE_COUNTS:
        raise SystemExit("--counts is week (the figure is for that week only) or since_listing (the running count the site shows)")
    if not _count(views) and views is not None or not _count(saves) and saves is not None or (views is None and saves is None):
        raise SystemExit("views and saves are whole numbers. Give at least one. Never estimate a figure.")
    ws = C.iso(C.week_start(week) if week else default_week(as_of))
    row = {"week_start": ws, "portal": portal_name(portal), "views": views, "saves": saves, "counts": counts,
           "as_of": C.iso(as_of), "source": source}
    store["rows"] = [r for r in store["rows"] if (r["week_start"], r["portal"]) != (ws, row["portal"])] + [row]
    return row


# ---------------------------------------------------------------------------------------------
# rows -> ledger.online
# ---------------------------------------------------------------------------------------------
def ledger_block(store, listing, report):
    """(ledger.online or None, {"skipped": [...], "glance": [...], "also": [...]}) for the issue in `report`.
    skipped: one plain line per lookup of this issue that was blocked or failed. glance: other things the operator
    should see. also: for Claude only.

    Rows dated after the report week are left for a later issue, so a rebuild of an older issue does not change.
    For a running count, the week's figure is this reading minus the reading of the week before. With no reading
    the week before there is no weekly figure (null), except in week 1, where everything since the list date is
    that week. A count that went down gives no weekly figure and a note."""
    notes = {"skipped": [], "glance": [], "also": []}
    rd, ws = C.iso(report["report_date"]), C.iso(report["week_start"])
    for x in LK.skipped(store, rd):
        portal = (x.get("key") or "").split(":", 1)[-1]
        notes["skipped"].append(LK.skipped_note("Online views on %s" % portal, x, "The report is built without a new figure from that site."))
    rows = [r for r in store.get("rows") or [] if r["week_start"] <= ws and r["week_start"] >= C.iso(C.week_start(listing["list_date"]))]
    if not rows:
        return None, notes
    order = []
    for name in (((listing.get("extras") or {}).get("online_views") or {}).get("portals") or []) + [r["portal"] for r in sorted(rows, key=lambda r: (r["week_start"], r["portal"]))]:
        if name not in order and any(r["portal"] == name for r in rows):
            order.append(name)
    weeks, since = {}, {"views": {}, "saves": {}}
    for portal in order:
        mine = sorted((r for r in rows if r["portal"] == portal), key=lambda r: r["week_start"])
        for kind in ("views", "saves"):
            prev, running, after = None, None, 0
            for r in mine:
                v, n = r.get(kind), C.week_index(r["week_start"], listing["list_date"])
                if v is None:
                    continue
                if r["counts"] == "week":
                    weeks.setdefault(n, {"views": {}, "saves": {}})[kind][portal] = v
                    after += v
                    continue
                figure = None
                if n == 1:
                    figure = v
                elif prev is not None and prev[0] == n - 1:
                    if v >= prev[1]:
                        figure = v - prev[1]
                    else:
                        notes["glance"].append("%s's count of %s went down between readings (%s to %s), so no weekly figure is shown for the week of %s."
                                               % (portal, kind, C.fmt_num(prev[1]), C.fmt_num(v), C.fmt_date(r["week_start"])))
                elif prev is None and n == C.week_index(ws, listing["list_date"]):
                    first = "%s: first reading. A weekly figure starts with the next reading." % portal
                    if first not in notes["also"]:
                        notes["also"].append(first)
                if figure is not None:
                    weeks.setdefault(n, {"views": {}, "saves": {}})[kind][portal] = figure
                prev, running, after = (n, v), v, 0
            if running is not None:
                since[kind][portal] = running + after
    block = {"as_of": max(r["as_of"] for r in rows), "portals": order,
             "weeks": [dict(n=n, **dict((k, v) for k, v in sorted(weeks[n].items()) if v)) for n in sorted(weeks)]}
    since = dict((k, v) for k, v in since.items() if v)
    if since:
        block["since_listing"] = since
    return block, notes


def sources(store, block, report=None):
    """sources_used lines for the ledger: one per way the figures on file came in."""
    out = []
    if not block:
        return out
    last = C.iso(report["week_start"]) if report else "9999"
    used = [r for r in store.get("rows") or [] if r["portal"] in block["portals"] and r["week_start"] <= last]
    for source, kind, label in (("portal_page", "portal_page", "Public listing pages, read for online views"),
                                ("operator", "operator_numbers", "Online view counts given by the operator")):
        mine = [r for r in used if r["source"] == source]
        if mine:
            out.append("%s|%s|%s" % (kind, label, max(r["as_of"] for r in mine)))
    return out


# ---------------------------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------------------------
def _issue(a, listing):
    """The report date of the issue being built: --report-date, or the Monday after the last full week."""
    if getattr(a, "report_date", None):
        rd = C.parse_date(a.report_date)
        if rd.weekday() != 0:
            raise SystemExit("--report-date %s is not a Monday" % rd)
        return rd
    return C.report_week(datetime.date.today())[2]


def _report(listing, rd):
    return {"report_date": C.iso(rd), "week_start": C.iso(rd - datetime.timedelta(days=7)), "week_end": C.iso(rd - datetime.timedelta(days=1))}


def cmd_plan(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store, rd, portal = load(a.folder, listing.get("slug")), _issue(a, listing), portal_name(a.portal)
    cfg = (listing.get("extras") or {}).get("online_views") or {}
    try:
        LK.plan(store, "portal:" + portal, rd, C.LIMITS["portal_pages_per_issue"], asked=a.asked, by_setting=LK.setting(listing, "online_views"),
                what="online views on %s" % portal)
    except LK.Refused as e:
        F.say("REFUSED: %s" % e)
        return EXIT_REFUSED
    save(a.folder, store)
    url = a.url or (cfg.get("pages") or {}).get(portal)
    F.say("planned: ONE page on %s for the issue dated %s." % (portal, C.iso(rd)))
    F.say("  1. Open this public page in the in-app browser (no sign-in, no forms): %s" % (url or "the listing's public page on %s (no address is on file: ask the operator for it)" % portal))
    F.say("  2. Run the snippet %s on it. It returns {portal, views, saves, as_of} and nothing else." % SNIPPET)
    F.say("  3. Save what it returned to a file and run:  python \"%s\" add --folder \"%s\" --result <file> --report-date %s"
          % (os.path.join(_HERE, "online_views.py"), os.path.abspath(a.folder), C.iso(rd)))
    F.say("  If the page is blocked, shows a human check or does not load: STOP. Do not try another way. Run:  python \"%s\" skip --folder \"%s\" --portal %s --reason <blocked|captcha|failed|pane_unavailable|not_found> --report-date %s"
          % (os.path.join(_HERE, "online_views.py"), os.path.abspath(a.folder), portal, C.iso(rd)))
    return EXIT_OK


def cmd_add(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store = load(a.folder, listing.get("slug"))
    if a.result:
        rd = _issue(a, listing)
        try:
            data = LK.read_result(a.result, C.LIMITS["portal_json_max_bytes"], "portal views")
            portal = portal_name(data.get("portal") or a.portal)
            why = LK.blocked_reason(data)
            if why is None and not _count(data.get("views")) and not _count(data.get("saves")):
                why = "not_found"
            if why:
                LK.close(store, "portal:" + portal, rd, "skipped", why, data.get("detail") or data.get("error"))
                save(a.folder, store)
                F.say("SKIPPED: %s gave no figure (%s). The report is built without it. Do not try another way." % (portal, LK.SKIP_WORDS[why]))
                return EXIT_OK
            LK.close(store, "portal:" + portal, rd, "ok")
        except LK.Refused as e:
            F.say("REFUSED: %s" % e)
            return EXIT_REFUSED
        as_of = data.get("as_of") or C.iso(datetime.date.today())
        row = add_row(store, portal, data.get("views") if _count(data.get("views")) else None,
                      data.get("saves") if _count(data.get("saves")) else None, "since_listing", as_of,
                      week=rd - datetime.timedelta(days=7), source="portal_page")
    else:
        if not a.portal or (a.views is None and a.saves is None) or not a.counts:
            raise SystemExit("add needs --portal, --views or --saves, and --counts (week or since_listing). Or --result <file> from the snippet.")
        week = a.week or ((C.parse_date(a.report_date) - datetime.timedelta(days=7)) if a.report_date else None)
        row = add_row(store, a.portal, a.views, a.saves, a.counts, a.as_of or datetime.date.today(), week=week, source="operator")
    problems = validate_store(store)
    if problems:
        raise SystemExit("online_views.json would not be valid: " + "; ".join(problems[:4]))
    save(a.folder, store)
    F.say("filed: %s, week of %s: %s views, %s saves (%s, read %s, %s)."
          % (row["portal"], C.fmt_date(row["week_start"], year=True), "no" if row["views"] is None else C.fmt_num(row["views"]),
             "no" if row["saves"] is None else C.fmt_num(row["saves"]),
             "the running count since listing" if row["counts"] == "since_listing" else "that week only", C.fmt_date(row["as_of"]), row["source"]))
    return EXIT_OK


def cmd_skip(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store, rd, portal = load(a.folder, listing.get("slug")), _issue(a, listing), portal_name(a.portal)
    try:
        LK.close(store, "portal:" + portal, rd, "skipped", a.reason, a.detail)
    except LK.Refused as e:
        F.say("REFUSED: %s" % e)
        return EXIT_REFUSED
    save(a.folder, store)
    F.say("skipped: %s (%s). The report is built without a new figure from it, and the chat reply says so." % (portal, LK.SKIP_WORDS[a.reason]))
    return EXIT_OK


def cmd_show(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store, rd = load(a.folder, listing.get("slug")), _issue(a, listing)
    block, notes = ledger_block(store, listing, _report(listing, rd))
    if a.json:
        F.say(F.dumps({"online": block, "notes": notes}).rstrip())
        return EXIT_OK
    if not block:
        F.say("no online views are on file for the issue dated %s." % C.iso(rd))
    else:
        F.say("online views for the issue dated %s (read %s): %s" % (C.iso(rd), C.fmt_date(block["as_of"]), C.join_and(block["portals"])))
        for w in block["weeks"]:
            F.say("  week %d: views %s, saves %s" % (w["n"], w.get("views") or "none", w.get("saves") or "none"))
        if block.get("since_listing"):
            F.say("  since listing: views %s, saves %s" % (block["since_listing"].get("views") or "none", block["since_listing"].get("saves") or "none"))
    for line in notes["skipped"] + notes["glance"] + notes["also"]:
        F.say("  note: " + line)
    for x in LK.for_issue(store, rd):
        F.say("  lookup: %s, %s%s" % (x["key"], x["outcome"], (" (" + x["reason"] + ")") if x.get("reason") else ""))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(description="Online views and saves per portal for one listing (optional).",
                                 epilog="Exit 0 done. 2 an input is wrong. 4 refused by the token rules (not asked for, or the one page for this issue is used).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--folder", required=True, help="the listing folder: <reports>\\seller-reports\\<slug>")
        p.add_argument("--report-date", help="the Monday the issue is dated. Default: the Monday after the last full week")
        return p
    p = common(sub.add_parser("plan", help="before opening a portal page: checks the rules and logs the one page for this issue"))
    p.add_argument("--portal", required=True)
    p.add_argument("--asked", action="store_true", help="the operator asked for this in this session")
    p.add_argument("--url", help="the listing's public page on that portal, when listing.json does not hold it")
    p.set_defaults(fn=cmd_plan)
    p = common(sub.add_parser("add", help="file a figure: the operator's numbers, or the snippet's result"))
    p.add_argument("--portal")
    p.add_argument("--views", type=int)
    p.add_argument("--saves", type=int)
    p.add_argument("--counts", choices=C.ONLINE_COUNTS, help="week: that week only. since_listing: the running count the site shows")
    p.add_argument("--as-of", help="the day the figure was read. Default: today")
    p.add_argument("--week", help="any day of the week the figure belongs to. Default: the week the report covers")
    p.add_argument("--result", help="a file holding exactly what portal_views.js returned")
    p.set_defaults(fn=cmd_add)
    p = common(sub.add_parser("skip", help="the page was blocked, asked for a human check, or failed: close the lookup"))
    p.add_argument("--portal", required=True)
    p.add_argument("--reason", required=True, choices=C.SKIP_REASONS)
    p.add_argument("--detail")
    p.set_defaults(fn=cmd_skip)
    p = common(sub.add_parser("show", help="what the report will print for this issue"))
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_show)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
