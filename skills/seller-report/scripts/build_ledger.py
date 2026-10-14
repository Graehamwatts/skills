# -*- coding: utf-8 -*-
"""build_ledger: raw.json + curation.json + listing.json (+ events.json) -> ledger.json for one report Monday.

    python build_ledger.py --folder <reports>\\seller-reports\\<slug> --report-date 2026-10-12

The ledger is the seller-safe dataset the renderer reads (references/data-contract.md, section 6). Every
week, total, tally and per-person follow-up number in it is computed in code from the rows, by the rules in
references/counting-rules.md. Nothing is typed.

Hard stops. The build writes nothing and exits with status 2 when:
  - a sheet row is neither a person, an ignored row nor an open house session;
  - a dated note is neither read into curation.json nor a stock phrase the rules can classify (run
    curation_tools.py todo);
  - an open house session has no date and curation gives none;
  - the numbers do not foot (weeks against totals, price periods against totals, people against statuses);
  - sr_contract.validate_ledger finds a problem (privacy scan, enumerations, numbers against rows).

The optional sections come from what is already on file: online_views.json becomes ledger.online, the snapshot
nearby.json holds for this issue becomes ledger.nearby, and marketing.json is kept only when a channel is on or
something was checked for this issue. Nothing is fetched here. A lookup that was skipped leaves its section
out and puts one plain line in notes_for_operator.json.

The cutoff. Nothing dated after the Sunday that ends the report week is in a count. Later entries, up to
--through, go to report.since_week_closed. Entries after --through wait for the next issue.

Beside the ledger the build writes notes_for_operator.json: at most five plain lines Claude puts in the chat
reply that hands over the draft ("Worth a glance before you send"). They are never printed in the report.

ledger.json is PRIVATE working data. It is refused inside a git repo.
Standard library only. No real client data belongs in this file.
"""
import argparse
import datetime
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sr_contract as C                  # noqa: E402
import sr_files as F                     # noqa: E402
import sr_ledger_checks as K             # noqa: E402
import online_views                      # noqa: E402
import nearby_update                     # noqa: E402
import hero_photo                        # noqa: E402
from sr_build_people import People       # noqa: E402

NOT_FOR_LEDGER = ("schema_version", "sheet", "keybox_number", "listing_folder", "numbering", "tracking",
                  "tracking_since", "operator_notes", "status_checked", "extras")
REQUIRED_LISTING = ("slug", "address", "city", "state", "beds", "baths", "sqft", "property_type", "list_date",
                    "price_history", "status", "mls", "hero_photo")
TRACKING = ("keybox_showings", "disclosure_sent", "disclosure_opened")
UNIT_ONE = {"groups": "group", "visitors": "visitor", "guests": "guest", "parties": "party", "people": "person"}


def blank_curation(slug):
    return {"schema_version": C.SCHEMA_VERSION, "slug": slug, "updated": None, "people": {}, "entries": {},
            "open_houses": {}, "offers": [], "ignored_rows": {}, "date_corrections": {}, "overrides": [], "next_week": []}


def report_dates(report_date=None, run_date=None):
    """(week_start, week_end, report_date) as dates. The report date is always a Monday."""
    if report_date:
        rd = C.parse_date(report_date)
        if rd.weekday() != 0:
            raise SystemExit("--report-date %s is a %s. A report is dated the Monday after the week it covers." % (rd, C.WEEKDAYS[rd.weekday()]))
        return rd - datetime.timedelta(days=7), rd - datetime.timedelta(days=1), rd
    return C.report_week(run_date or datetime.date.today())


def issues_on_file(folder):
    """[(issue number, report date)] of the issues on file, from their manifests."""
    out, root = [], os.path.join(folder, "issues")
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            m = F.load_json(os.path.join(root, name, "manifest.json"), default={})
            if m.get("issue_number") is not None and m.get("report_date"):
                out.append((int(m["issue_number"]), m["report_date"]))
    return out


def first_date(row, cur):
    """The earliest dated record on a sheet row (a note, the date cell, a date column), or None."""
    fixes = cur.get("date_corrections") or {}
    dates = [(fixes.get(e["key"]) or {}).get("date") or e.get("date") for e in row["entries"]]
    dates += [w.get("date") for w in row.get("when") or []] + list((row.get("last_touch") or {}).values())
    dates = [d for d in dates if d]
    return min(dates) if dates else None


def count_phrase(n, unit):
    if n is None:
        return None
    if n == 0:
        return "No visitors."
    return "%d %s." % (n, UNIT_ONE[unit] if n == 1 else unit)


# ---------------------------------------------------------------------------------------------
# rows: every one is a person, an ignored row, an open house session, or waiting for a later issue
# ---------------------------------------------------------------------------------------------
def account_for_rows(raw, cur, P, through):
    """Returns (deferred row keys, counts). Adds a hard stop to P.problems for each row nobody has placed."""
    ignored = cur.get("ignored_rows") or {}
    offer_rows = set(o.get("source_row") for o in cur.get("offers") or [] if o.get("source_row"))
    inviters = raw.get("inviter_candidates") or {}
    deferred, pending, counts = set(), [], {"people": 0, "ignored": 0, "open_house": 0, "offers": 0, "other": 0, "deferred": 0}
    for t in raw.get("tabs") or []:
        for r in t["rows"]:
            k = r["key"]
            if t["kind"] == "open_house":
                counts["open_house"] += 1
            elif k in P.held:
                counts["people"] += 1
            elif k in ignored:
                counts["ignored"] += 1
            elif t["kind"] == "other":
                counts["other"] += 1
            elif t["kind"] == "offers":
                if k in offer_rows:
                    counts["offers"] += 1
                else:
                    P.problems.append("offers tab %r row %d is not in curation.json (add the offer with source_row, or ignore the row). Key %s" % (t["title"], r["row"], k))
            else:
                first = first_date(r, cur)
                if first and first > through:
                    deferred.add(k)
                else:
                    pending.append((t, r))
    for t, r in pending:                                   # a buyer row waits when the agent who invited them waits
        cands = inviters.get(r["key"]) or []
        if r.get("invited_by_raw") and cands and all(c in deferred for c in cands):
            deferred.add(r["key"])
        else:
            P.problems.append("tab %r row %d is not accounted for: it is not a person, not ignored and not later than this issue. Key %s"
                              % (t["title"], r["row"], r["key"]))
    counts["deferred"] = len(deferred)
    return deferred, counts


# ---------------------------------------------------------------------------------------------
# open houses and offers
# ---------------------------------------------------------------------------------------------
def build_open_houses(raw, cur, P, contacts, we, through):
    """(sessions for the ledger, price remarks, host tallies). Later sessions go to P.since."""
    byid = dict((c["id"], c) for c in contacts)
    notes = cur.get("open_houses") or {}
    out, remarks, hosts, bare = [], [], {}, 0
    for t in raw.get("tabs") or []:
        if t["kind"] != "open_house":
            continue
        for r in t["rows"]:
            holder = byid.get(P.held.get(r["key"]))
            holder = holder if holder and holder["is_open_house_host"] else None
            for s in r.get("sessions") or []:
                cu = notes.get(s["key"]) or {}
                where = "open house tab %r row %d, session %d" % (t["title"], r["row"], s["index"])
                if cu.get("ignore"):
                    P.stats["open_house_sessions_ignored"] += 1
                    continue
                if (cu.get("unsure") or "").strip() and (cu.get("date") or s["date"] or "9") <= we:
                    P.unsure.append(("Open house", cu["unsure"].strip()))
                date = cu.get("date") or s["date"]
                quality = cu.get("date_quality") or ("exact" if date == s["date"] else "approximate")
                if date is None:
                    if cu.get("not_before") and cu["not_before"] > we:
                        P.stats["open_house_sessions_waiting_for_a_date"] += 1
                    else:
                        P.problems.append("%s has no date typed. Give it one in curation.json open_houses (key %s), with date_quality 'approximate'." % (where, s["key"]))
                    continue
                if date > through:
                    P.stats["open_house_sessions_after_through"] += 1
                    continue
                groups, unit, source = s["groups"], s["counted_unit"], s["groups_source"]
                if "groups" in cu and cu["groups"] != s["groups"]:
                    groups = cu["groups"]
                    source = cu.get("groups_source") or ("not_recorded" if groups is None else "parsed_from_prose")
                unit = cu.get("counted_unit") or unit or "groups"
                host = cu.get("host") or C.short_name(r.get("name_raw")) or "Host not recorded"
                recap = cu["recap_safe"] if "recap_safe" in cu else count_phrase(groups, unit)
                if "recap_safe" not in cu and (s.get("text") or "").strip():
                    bare += 1
                entry = {"date": date, "date_quality": quality, "host": host,
                         "host_contact_id": holder["id"] if holder else None,
                         "time_text": cu.get("time_text") or s.get("time_text"), "groups": groups, "counted_unit": unit,
                         "groups_source": source, "recap_safe": recap, "softened": bool(cu.get("softened")),
                         "disclosure_requests": cu["disclosure_requests"] if "disclosure_requests" in cu else (0 if groups == 0 else None)}
                for k in ("date_note", "schedule_sheet_date", "on_schedule_sheet"):
                    if cu.get(k) is not None:
                        entry[k] = cu[k]
                if date > we:
                    P.since.append({"date": date, "kind": "open_house", "contact_id": None, "name_short": host,
                                    "summary_safe": "Open house. " + (recap or "No count is on record yet."), "offer_related": False})
                    continue
                out.append(entry)
                key = (host, entry["host_contact_id"])
                hosts[key] = hosts.get(key, 0) + 1
                pr = cu.get("price_remark")
                if pr:
                    remarks.append({"date": date, "reaction": pr.get("reaction"), "remark_safe": pr.get("remark_safe"),
                                    "softened": bool(pr.get("softened"))})
    out.sort(key=lambda o: o["date"])
    remarks.sort(key=lambda x: x["date"])
    if bare:
        P.notes.append("%d open house recap(s) have not been paraphrased yet, so only the count is shown for them." % bare)
    return out, remarks, hosts


def build_team_side(contacts, hosts):
    """The people on our side of the table: hosts who brought no buyer of their own."""
    byid = dict((c["id"], c) for c in contacts)
    out, seen = [], set()
    for (host, cid), n in sorted(hosts.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        if cid and not byid[cid]["team_side"]:
            continue                                         # a host who also showed the home to a buyer counts as an agent
        out.append({"name_short": host, "role": "open house host", "sessions_hosted": n, "contact_id": cid})
        seen.add(cid)
    for c in contacts:
        if c["team_side"] and c["id"] not in seen:
            out.append({"name_short": c["name_short"], "role": "open house host", "sessions_hosted": 0, "contact_id": c["id"]})
    return out


def build_offers(cur, hist, contacts, P, we, through):
    byid = dict((c["id"], c) for c in contacts)
    out = []
    for i, o in enumerate(cur.get("offers") or []):
        date, cid = o.get("date"), o.get("contact_id")
        if not date or not isinstance(o.get("price"), int):
            P.problems.append("offers[%d]: needs a date and a whole-dollar price" % i)
            continue
        if date > through:
            P.stats["offers_after_through"] += 1
            continue
        person = byid.get(cid)
        if date > we:
            P.since.append({"date": date, "kind": "offer", "contact_id": cid if person else None,
                            "name_short": (person or {}).get("name_short") or o.get("agent_short"),
                            "summary_safe": "A new offer came in.", "offer_related": True})
            continue
        if cid is not None and not person:
            P.problems.append("offers[%d].contact_id: %s is not a person in this ledger" % (i, cid))
            continue
        out.append({"id": o.get("id") or "o%d" % (i + 1), "date": date, "contact_id": cid,
                    "agent_short": o.get("agent_short") or (person or {}).get("name_short"),
                    "brokerage": o.get("brokerage") if "brokerage" in o else (person or {}).get("brokerage"),
                    "price": o["price"], "pct_of_list": round(100.0 * o["price"] / C.price_on(hist, date), 1),
                    "terms_summary": o.get("terms_summary"), "state": o.get("state") or "received", "note_safe": o.get("note_safe")})
    out.sort(key=lambda o: (o["date"], o["id"]))
    return out


def fill_market(market, days_listed, report_date):
    """Recomputes every derived number of the optional market block from its sales rows."""
    used = sorted(s["days_to_contract"] for s in market["sales"] if s.get("used_in_average"))
    if not used:
        raise SystemExit("market.json: no sale is marked used_in_average")
    mid = len(used) // 2
    med = used[mid] if len(used) % 2 else (used[mid - 1] + used[mid]) / 2.0
    market["sample"] = dict(market.get("sample") or {}, closed=len(market["sales"]), used=len(used), excluded=len(market["sales"]) - len(used))
    market["days_to_contract"] = dict(market.get("days_to_contract") or {}, average=int(sum(used) / float(len(used)) + 0.5),
                                      median=int(med + 0.5), shortest=used[0], longest=used[-1], values_sorted=used,
                                      over_90_days=len([v for v in used if v > 90]))
    market["subject_on_report_date"] = dict(market.get("subject_on_report_date") or {}, date=C.iso(report_date),
                                            days_on_market=days_listed, of_sales=len(used),
                                            sales_under_contract_by_that_day=len([v for v in used if v <= days_listed]))
    return market


def one_day_count(nearby, market):
    """One sale, one day count: a sold home in the nearby list that is also in the market chart with a different
    day count loses its nearby count (the chart's is the one the page explains). Changes `nearby` in place and
    returns plain lines for Claude. nearby_from_mls.py applies the same rule at import, against the market.json
    on file then; this catches a chart written or refreshed after the nearby lookup."""
    if not nearby or not market:
        return []
    chart = dict((C._norm(s.get("address")), s["days_to_contract"]) for s in market.get("sales") or []
                 if s.get("address") and s.get("days_to_contract") is not None)
    out = []
    for h in nearby.get("homes") or []:
        k = C._norm(h.get("address"))
        if h.get("status") == "sold" and h.get("days_on_market") is not None and k in chart and chart[k] != h["days_on_market"]:
            out.append("%s: the market chart counts %d days for this sale and the nearby list %d, so the nearby list leaves its count out."
                       % (h["address"], chart[k], h["days_on_market"]))
            h["days_on_market"] = None
    return out


# ---------------------------------------------------------------------------------------------
# the build
# ---------------------------------------------------------------------------------------------
def build(folder, report_date=None, run_date=None, through=None, issue=None, sources=(), as_of_note=None, built_at=None, glance=(),
          brief=None, online=True):
    """Returns (ledger or None, problems, info). The ledger is None when there is a hard stop."""
    paths = F.listing_paths(folder)
    listing, raw = F.load_json(paths["listing"]), F.load_json(paths["raw"])
    cur = F.load_json(paths["curation"], default=blank_curation(listing.get("slug")))
    events = F.load_json(paths["events"], default={"events": [], "fetched": []})
    ws, we, rd = [C.iso(d) for d in report_dates(report_date, run_date)]
    as_of = raw.get("as_of") or we
    through = C.iso(through) if through else max(we, min(as_of, C.iso(datetime.date.today())))
    if through < we:
        raise SystemExit("--through %s is before the week end %s" % (through, we))
    for k in REQUIRED_LISTING:
        if k not in listing:
            raise SystemExit("listing.json: missing %s" % k)
    if as_of < we:
        F.shout("the sheet was exported on %s, before the report week ended on %s. The week may be missing entries." % (as_of, we))
    problems = ["curation.json: " + p for p in C.validate_curation(cur)]
    if problems:
        return None, problems, {}

    d = C.blank_ledger(listing["slug"])
    hist = [dict(e) for e in sorted(listing["price_history"], key=lambda e: e["date"]) if e["date"] <= rd]
    L = dict((k, v) for k, v in listing.items() if k not in NOT_FOR_LEDGER)
    L.update(price_history=hist, list_price=C.price_on(hist, rd) if hist else None)
    d["listing"] = L
    tracking = dict((k, bool((listing.get("tracking") or {}).get(k))) for k in TRACKING)

    P = People(listing, raw, cur, we, through)
    contacts = P.build()
    deferred, row_counts = account_for_rows(raw, cur, P, through)
    K.apply_events(events, contacts, P, we, through)
    d["contacts"] = contacts
    d["open_houses"], remarks, hosts = build_open_houses(raw, cur, P, contacts, we, through)
    d["offers"] = build_offers(cur, hist, contacts, P, we, through)
    d["pricing_tally"] = {"open_house_price_remarks": remarks}
    d["team_side"] = build_team_side(contacts, hosts)
    d["next_week"] = [s for s in cur.get("next_week") or [] if isinstance(s, str) and s.strip()]

    on_file = issues_on_file(paths["folder"])
    number = int(issue) if issue else C.next_issue_number((listing.get("numbering") or {}).get("first_issue_number"), on_file, rd)
    P.since.sort(key=lambda it: (it["date"], it.get("contact_id") or "", it["summary_safe"]))
    d["report"] = {"issue_number": number, "report_date": rd, "week_start": ws, "week_end": we, "tracking": tracking,
                   "since_week_closed": {"through": through, "items": P.since}, "as_of_note": as_of_note}
    if brief and brief.strip():                            # the agent's own words for "This week in brief", this issue only
        d["report"]["brief_override"] = C.strip_dashes(brief.strip())
    since = listing.get("tracking_since") or {}
    d["weeks"] = []
    for n, a, b in C.list_weeks(listing["list_date"], ws):
        w = {"n": n, "label": C.fmt_range(a, b)}
        for flag, day in since.items():                    # a week nobody could check stays null, never zero
            if flag in TRACKING and tracking[flag] and C.iso(a) < day:
                w[flag] = None
        d["weeks"].append(w)

    optional = {"skipped": [], "glance": [], "also": []}    # plain lines about the optional sections, for the chat reply
    market = F.load_json(paths["market"], default={}) or None
    if market:
        d["market"] = fill_market(market, C.days_on_market(listing["list_date"], rd), rd)
    d["marketing"] = F.load_json(paths["marketing"], default={}) or None
    if d["marketing"] and not C.marketing_recorded(d["marketing"], d["report"]):
        d["marketing"] = None                              # nothing is on and nothing was checked for this issue
        optional["also"].append("The ad and marketing status on file was last checked before this report's week and nothing is switched on, so that section is left out.")
    # the optional sources: only what is already on file. Nothing is fetched here (sr_lookups holds the rules)
    views, nearby = F.load_json(paths["online_views"], default={}), F.load_json(paths["nearby"], default={})
    extra_sources = []
    if views and not online:
        optional["also"].append("Online views are on file but were left out of this build (--no-online).")
    if views and online:
        problems += ["online_views.json: " + p for p in online_views.validate_store(views)]
        if not problems:
            block, notes = online_views.ledger_block(views, listing, d["report"])
            # printed only when a reading was taken for this issue: a reading from an earlier week would print an
            # old "since we listed" figure on a week nobody asked for the views (SKILL.md, rule 6)
            if block and any(r.get("week_start") == ws for r in views.get("rows") or []):
                d["online"] = block
                extra_sources += online_views.sources(views, d["online"], d["report"])
            elif block:
                notes["also"].append("Online views were not read for this issue, so the report leaves them out (the last reading is "
                                     "from an earlier week). Read them again with online_views.py when they are asked for.")
            for k in optional:
                optional[k] += notes[k]
    if nearby:
        problems += ["nearby.json: " + p for p in nearby_update.validate_store(nearby, listing)]
        if not problems:
            d["nearby"], notes = nearby_update.ledger_block(nearby, listing, d["report"])
            if d["nearby"]:
                extra_sources.append("nearby_lookup|%s|%s" % (d["nearby"]["source"], d["nearby"]["as_of"]))
                optional["also"] += one_day_count(d["nearby"], d.get("market"))
            for k in optional:
                optional[k] += notes[k]
    if problems:
        return None, problems, {}
    heavy = hero_photo.heavy_note(listing)
    if heavy:
        optional["glance"].append(heavy)
    d["sources_used"] = K.sources_used(raw, events, list(sources) + extra_sources)

    d["meta"] = {"slug": listing["slug"], "built_at": built_at or datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()}
    info = {"row_counts": row_counts, "deferred_rows": sorted(deferred), "stats": dict(P.stats), "issue_number": number,
            "provenance": P.provenance}                      # where each reading came from. Stays out of the ledger
    if P.problems:
        return None, P.problems, info
    try:
        C.finish_ledger(d)
    except Exception as exc:                                 # a malformed row surfaces here; report it as a hard stop
        return None, ["the rows could not be counted: %s: %s" % (type(exc).__name__, exc)], info
    d["data_quality"] = K.data_quality(d, raw, cur, listing, P, row_counts, deferred)
    problems = K.footing(d, raw, cur, P, row_counts, deferred)
    problems += C.validate_ledger(d, identity=C.load_identity())
    info["headline"] = K.headline(d)
    if not problems:
        info["notes_for_operator"] = K.notes_for_operator(d, raw, listing, P, glance, optional)
    return (None if problems else d), problems, info


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build ledger.json for one report Monday (PRIVATE output).")
    ap.add_argument("--folder", required=True, help="the listing folder: <reports>\\seller-reports\\<slug>")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--report-date", help="the Monday the report is dated (it covers the Monday to Sunday week before)")
    g.add_argument("--run-date", help="the day the report is being built. Default: today. The week covered is the last one that fully ended")
    ap.add_argument("--through", help="include entries after the week end up to this date in 'since the week closed'. Default: the sheet's export date")
    ap.add_argument("--issue", type=int, help="override the issue number. Default: continue the numbering on file")
    ap.add_argument("--source", action="append", default=[], metavar="KIND|LABEL|YYYY-MM-DD",
                    help="another source the operator handed over in this session (repeatable). KIND is one of sr_contract.SOURCE_KINDS")
    ap.add_argument("--as-of-note", help="an operator note kept in the ledger. Never printed to a seller")
    ap.add_argument("--glance", action="append", default=[], metavar="SENTENCE",
                    help="one plain line for 'Worth a glance before you send' (repeatable): something Claude is unsure of "
                         "for this issue, such as a count that differs from the team's status email and why")
    ap.add_argument("--notes-out", help="default: notes_for_operator.json beside the ledger")
    ap.add_argument("--brief-file", help="a text file with the agent's own words for 'This week in brief' (this issue only, email only)")
    ap.add_argument("--no-online", action="store_true", help="leave the online views on file out of this issue")
    ap.add_argument("--out", help="default: <folder>\\ledger.json")
    ap.add_argument("--rejected-out", help="when the build stops, also save the list of problems to this file")
    a = ap.parse_args(argv)
    brief = None
    if a.brief_file:
        with open(a.brief_file, encoding="utf-8") as f:
            brief = f.read()
    ledger, problems, info = build(a.folder, a.report_date, a.run_date, a.through, a.issue, a.source, a.as_of_note, glance=a.glance, brief=brief,
                                    online=not a.no_online)
    if problems:
        F.shout("the ledger was NOT written. %d problem(s):" % len(problems))
        for p in problems:
            F.say("  -", p)
        if a.rejected_out:
            F.save_json(a.rejected_out, {"problems": problems, "info": info})
        return 2
    out = F.save_json(a.out or F.listing_paths(a.folder)["ledger"], ledger)
    R = ledger["report"]
    F.say("ledger written (PRIVATE): %s" % out)
    F.say("  issue %d, dated %s, covering %s." % (R["issue_number"], R["report_date"], C.fmt_range(R["week_start"], R["week_end"])))
    for k, v in info["headline"].items():
        F.say("  %-34s %s" % (k, v))
    notes = F.save_json(a.notes_out or os.path.join(os.path.dirname(out), "notes_for_operator.json"), info["notes_for_operator"])
    F.say("notes for the chat reply (never for the report): %s" % notes)
    for line in info["notes_for_operator"]["worth_a_glance"]:
        F.say("  -", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
