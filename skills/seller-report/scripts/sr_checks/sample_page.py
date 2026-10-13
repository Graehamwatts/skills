# -*- coding: utf-8 -*-
"""sr_checks.sample_page: the smallest page that satisfies the ship gate.

The order is the report's: the numbers table with the line under it, the week by week chart, what people are
saying, then the details (people grouped by what they did, each list headed by its count), then the record.

It is NOT the renderer and it is not a design. It exists for two reasons:
  1. The gate's tests need a clean page to break one rule at a time, without depending on the renderer.
  2. It is the worked example of the data-sr hooks, so the renderer's author can see each one in place.

Like a renderer, it prints the ledger's stored numbers and counts nothing itself (the one exception is the
whole-week subtotal per list price, which a weekly table needs and the ledger does not store).
build(..., hooks=False) leaves every data-sr attribute out, which is how the tests exercise the gate's
fallback: finding numbers by their sentences and table headings.
"""
import html
import re

from . import core

DOT = " " + chr(0xB7) + " "
NL = chr(10)                      # rows are joined with a line break so no line passes 998 characters
CELL = 'bgcolor="#FFFFFF" style="padding:5px 6px;color:#333333"'
HEAD = 'bgcolor="#C5A55A" style="padding:5px 6px;color:#1A1A1A;font-size:12px"'
STATUS = {"not_yet_contacted": "Not yet reached", "awaiting_reply": "Still waiting", "replied": "Answered", "passed": "Passed",
          "writing_offer": "Answered", "offer_submitted": "Answered", "through_agent": "Through their agent"}
UNIT_ONE = {"groups": "group", "visitors": "visitor", "guests": "guest", "parties": "party", "people": "person"}


def esc(s):
    return html.escape(str(s), quote=True)


def money(v):
    return "${:,}".format(int(v))


def shown(v, empty="not recorded"):
    return empty if v is None else "{:,}".format(v)


def brokerage(name, identity):
    """Another agent's brokerage, with a blocked brand cut to its first word (what sr_contract.display_brokerage does)."""
    s = " ".join(str(name or "").split())
    for b in (identity.get("blocklist") or {}).get("brand") or []:
        s = re.sub(re.escape(b), b.split()[0], s, flags=re.I)
    return re.sub(r"\s+Real Estate$", "", s)


def followup_line(c):
    f = c.get("followup") or {}
    ours = [t for t in c.get("touches") or [] if t.get("direction") == "outbound"]
    if not ours:
        return "No follow-up logged yet."
    n = {"call": 0, "text": 0, "email": 0, "in_person": 0}
    unknown = False
    for t in ours:
        k = "call" if t.get("channel") in ("call", "voicemail") else t.get("channel")
        if k in n:
            n[k] += 1
        else:
            unknown = True
    if unknown:
        parts = ["%d follow-up%s" % (len(ours), "" if len(ours) == 1 else "s")]
    else:
        parts = ["%d %s%s" % (n[k], w, "" if n[k] == 1 else "s") for k, w in (("call", "call"), ("text", "text"), ("email", "email")) if n[k]]
        if n["in_person"]:
            parts.append("%d visit%s in person" % (n["in_person"], "" if n["in_person"] == 1 else "s"))
    d, r = f.get("outbound_days", 0), f.get("replies", 0)
    return "%d day%s of follow-up (%s). %d repl%s." % (d, "" if d == 1 else "s", ", ".join(parts), r, "y" if r == 1 else "ies")


def oh_cell(row):
    if not row.get("open_house_sessions"):
        return "none"
    return "held" if row.get("open_house_groups") is None else str(row["open_house_groups"])


def build(ledger, identity, kind="email", hooks=True, link_url="https://seller-reports.test/record"):
    d, idn = ledger, identity
    L, R, T, PT = d["listing"], d["report"], d["totals"], d["pricing_tally"]
    link = kind in ("link", "print")
    weeks = d["weeks"]
    W = next(w for w in weeks if w.get("is_current"))
    LW = weeks[weeks.index(W) - 1] if weeks.index(W) else None
    writers = set(o.get("contact_id") for o in d.get("offers") or [])
    weighing = set(w["contact_id"] for w in d.get("offer_watch") or []) | set(
        c["id"] for c in d["contacts"] if c.get("offer_intent") in ("yes", "maybe") or c.get("status") == "writing_offer")
    people = [c for c in d["contacts"] if not c.get("team_side") and not c.get("represented_by")]

    def v(hook, text):
        return '<span data-sr="%s">%s</span>' % (hook, esc(text)) if hooks else esc(text)

    def sec(name):
        return ' data-sr-section="%s"' % name if hooks else ""

    def at(name, value):
        return ' %s="%s"' % (name, value) if hooks else ""

    def block(name, inner):
        return '<tr><td%s %s>%s</td></tr>' % (sec(name), CELL, inner)

    def h2(text):
        return '<h2 style="margin:0 0 6px;font-size:18px;color:#1A1A1A">%s</h2>' % esc(text)

    out = ['<!DOCTYPE html>', '<html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>Weekly Seller Report No. %02d: %s</title>' % (R["issue_number"], esc(L["address"]))]
    if hooks:
        out += ['<meta name="sr:kind" content="%s">' % kind,
                '<meta name="sr:slug" content="%s">' % esc(d["meta"]["slug"]), '<meta name="sr:issue" content="%d">' % R["issue_number"],
                '<meta name="sr:week" content="%s/%s">' % (R["week_start"], R["week_end"])]
    if link:
        out.append('<meta name="robots" content="noindex, nofollow">')
    out += ['</head>', '<body style="margin:0;padding:0;background:#F5EFDC">',
            '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" bgcolor="#F5EFDC">']

    # ---- masthead ---------------------------------------------------------------------------
    facts = [str(idn["name"]).upper(), "%s%sDRE #%s" % (esc(idn["realtor_line"]), DOT, idn["dre"]), esc(idn["brand_line"]),
             "Weekly Seller Report", "Issued Monday, %s, %s" % (core.fmt_day(R["report_date"]), R["report_date"][:4]),
             "No. " + v("issue", "%02d" % R["issue_number"]), v("address", L["address"]),
             "WEEK COVERED " + v("week", "%s to %s" % (core.fmt_day(R["week_start"]), core.fmt_day(R["week_end"]))),
             "ON THE MARKET Day " + v("dom", R["days_on_market"]), "LIST PRICE " + v("list_price", money(L["list_price"])),
             "OFFERS TO DATE " + v("offers_total", T["offers"])]
    out.append('<tr><td%s bgcolor="#1A1A1A" style="padding:14px 8px;color:#C5A55A;font-size:14px">%s</td></tr>'
               % (sec("masthead"), NL.join("<div>%s</div>" % f for f in facts)))

    # ---- the numbers: one table, then the line under it ---------------------------------------------
    units = sorted(set(o.get("counted_unit") for o in d.get("open_houses") or [] if o.get("groups") is not None)) or ["groups"]
    card = [("showings", "Showings", "showings"), ("disclosure_contacts_new", "Disclosure packages", "disclosure_contacts"),
            ("open_house_groups", "Open house %s" % (units[0] if len(units) == 1 else "traffic"), "open_house_groups"),
            ("touches_outbound", "Follow-ups we made", "touches_outbound"), ("replies_inbound", "Replies we received", "replies_inbound"),
            ("offers", "Offers", "offers")]
    if T.get("online_views") is not None:
        card.append(("online_views", "Online views", "online_views"))

    def num(row, field):
        if field == "open_house_groups":
            return oh_cell(row)
        return shown(row.get(field))

    rows = ['<tr><th %s>&nbsp;</th><th scope="col"%s %s>This week</th><th scope="col"%s %s>Last week</th>'
            '<th scope="col"%s %s>Since we listed</th></tr>' % (HEAD, at("data-sr-col", "this"), HEAD, at("data-sr-col", "last"), HEAD,
                                                                 at("data-sr-col", "total"), HEAD)]
    for field, label, total in card:
        if field == "open_house_groups":
            tot = shown(T[total]) if T[total] is not None else ("held" if T["open_house_sessions"] else "none")
        else:
            tot = shown(T[total])
        rows.append('<tr%s><th scope="row" %s>%s</th><td %s>%s</td><td %s>%s</td><td %s>%s</td></tr>'
                    % (at("data-sr-row", field), CELL, esc(label), CELL, num(W, field), CELL, num(LW, field) if LW else "", CELL, tot))
    tries = (", %s of them after 3 or more tries" % v("waiting_3plus", T["awaiting_reply_3plus_attempts"])
             if T["awaiting_reply_3plus_attempts"] else "")
    lines = ["We contacted %s of %s people. %s answered. %s still waiting%s."
             % (v("contacted", T["contacted"]), v("contacts", T["contacts"]), v("answered", T["replied"]), v("waiting", T["awaiting_reply"]), tries),
             "This week: we followed up with %s %s on %s %s."
             % (v("week_followup_people", W["outbound_people"]), "person" if W["outbound_people"] == 1 else "people",
                v("week_followup_days", W["outbound_distinct_days"]), "day" if W["outbound_distinct_days"] == 1 else "days"),
             "Showings are key-box showings plus tours agents told us about. An inquiry is never counted as a showing.",
             "Key-box showings since we listed: %s. Tours agents told us about: %s."
             % (v("keybox_showings", shown(T["keybox_showings"])), v("agent_tours", T["agent_reported_tours"]))]
    out.append(block("numbers", h2("The numbers") + '<table%s cellpadding="0" cellspacing="0" width="100%%">%s</table>'
                     % (at("data-sr-table", "scorecard"), NL.join(rows)) + NL.join("<p style=\"margin:4px 0\">%s</p>" % ln for ln in lines)))

    # ---- the week by week chart: showings and disclosure packages, every week since listing ---------
    rows = ['<tr><th scope="col"%s %s>Week of</th><th scope="col"%s %s>Showings</th><th scope="col"%s %s>Packages</th></tr>'
            % (at("data-sr-col", "LABEL"), HEAD, at("data-sr-col", "showings"), HEAD, at("data-sr-col", "disclosure_contacts_new"), HEAD)]
    for w in weeks:
        rows.append('<tr><th scope="row" %s>%d (%s)</th><td %s>%s</td><td %s>%s</td></tr>'
                    % (CELL, w["n"], core.fmt_day(w["start"]), CELL, shown(w["showings"]), CELL, shown(w["disclosure_contacts_new"])))
    out.append(block("weekly_chart", h2("Showings and disclosure packages, week by week") + '<table%s cellpadding="0" cellspacing="0" width="100%%">%s</table>'
                     % (at("data-sr-table", "chart"), NL.join(rows))))

    # ---- what people are saying ---------------------------------------------------------------
    vocab = d["themes_vocabulary"]
    plabel = dict((r["key"], r["label"]) for r in vocab["price_rows"])
    tally = ["<p style=\"margin:4px 0\">Counts out of %s people. One person can raise more than one topic.</p>"
             % v("feedback_people", PT["people_with_feedback"])]
    for key, hook in (("too_high", "price_too_high"), ("fair_or_positive", "price_fair"), ("not_raised", "price_not_raised")):
        tally.append('<tr><td %s>%s</td><td %s>%s</td></tr>' % (CELL, esc(plabel[key]), CELL, v(hook, PT[key])))
    hide = set(t["key"] for t in vocab["themes"] if t.get("hide_in_link_copy"))
    for r in d["themes_tally"]["rows"]:
        if link and r["key"] in hide:
            continue
        hook = "theme:%s" % r["key"] if r["key"] != "other" else "theme:other:%s" % core.fold(r["label"])
        tally.append('<tr><td %s>%s</td><td %s>%s</td></tr>' % (CELL, esc(r["label"]), CELL, v(hook, r["people"])))
    liked = ["<p style=\"margin:8px 0 4px\">What people liked</p>"]
    for r in d["liked_tally"]["rows"]:
        liked.append('<tr><td %s>Liked: %s</td><td %s>%s</td></tr>' % (CELL, esc(r["label"]), CELL, v("liked:%s" % r["key"], r["people"])))
    out.append(block("saying", h2("What people are saying") + tally[0] + '<table cellpadding="0" cellspacing="0" width="100%%">%s</table>'
                     % NL.join(tally[1:]) + liked[0] + '<table cellpadding="0" cellspacing="0" width="100%%">%s</table>' % NL.join(liked[1:])
                     + "<p style=\"margin:4px 0\">These are our team's reading of each conversation, as reported to us.</p>"))

    # ---- offers: the email only ---------------------------------------------------------------
    if not link and d.get("offers"):
        rows = []
        for o in d["offers"]:
            rows.append("<p style=\"margin:4px 0\">%s%s%s, %s. %s, %g%% of the list price at the time. %s. %s</p>"
                        % (core.fmt_day(o["date"]), DOT, esc(o["agent_short"]), esc(brokerage(o.get("brokerage"), idn)),
                           money(o["price"]), o["pct_of_list"], esc(str(o["state"]).capitalize()), esc(o.get("terms_summary") or "")))
        out.append(block("offers", h2("Offers and likely offers") + NL.join(rows)))

    # ---- the details: people grouped by what they did -------------------------------------------
    # The count in each heading is the number of entries beneath it. A person is shown in full (or, when they
    # were not active this week, in one line) in the first list they belong to, and as a pointer in the others.
    # The link copy and the PDF show everyone in full, and never name an agent with an offer on file.
    titles = {"showings": "Agents who showed the home", "disclosure": "People on the disclosure package list",
              "open_house": "Open house visitors we know of", "other_inquiries": "People who asked about the home"}
    out.append(block("details", h2("The details") + "<p style=\"margin:4px 0\">People are grouped by what they did: the agents who showed the "
                     "home, the people on the disclosure package list, the open house visitors we know of, and anyone else who asked "
                     "about the home. The count in each heading is the number of entries beneath it. Everyone active this week is "
                     "shown in full, and earlier people have one line each. Someone who did two things is shown in the first list "
                     "they belong to, and the other lists point to that entry.</p>"))

    def name_of(c):
        if link and c["id"] in writers:
            return "An agent with an offer on file"
        return esc(c["name_short"]) + (", " + esc(brokerage(c["brokerage"], idn)) if c.get("brokerage") else "")

    def entry(c, key):
        cid = "" if (link and c["id"] in writers) else c["id"]
        if c.get("primary_list") != key:
            return '<div%s style="padding:3px 0">%s: see %s</div>' % (at("data-sr-entry", "pointer:" + cid), name_of(c), titles[c["primary_list"]])
        status = STATUS.get(c.get("status"), "Answered")
        if not link and not c.get("active_this_week"):
            return '<div%s style="padding:3px 0">%s%s%s</div>' % (at("data-sr-entry", "line:" + cid), name_of(c), DOT, status)
        body = '<div style="font-weight:700">%s%s%s</div>' % (name_of(c), DOT, status)
        if c.get("feedback_safe") and not (link and (c["id"] in weighing or c["id"] in writers)):
            body += ('<div%s><div style="font-size:12px;color:#666666">AS REPORTED TO OUR TEAM</div><div>%s</div></div>'
                     % (at("data-sr", "comment"), esc(c["feedback_safe"])))
        if not c.get("represented_by"):
            body += '<div style="font-size:13px">%s</div>' % esc(followup_line(c))
        return '<div%s style="padding:6px 0">%s</div>' % (at("data-sr-entry", "full:" + cid), body)

    for key in ("showings", "disclosure", "open_house", "other_inquiries"):
        mine = [c for c in d["contacts"] if key in (c.get("lists") or [])]
        if key == "other_inquiries" and not mine:
            continue
        head = '<h3 style="margin:8px 0 4px;font-size:16px;color:#1A1A1A">%s (%s)</h3>' % (titles[key], v("list:" + key, len(mine)))
        body = NL.join(entry(c, key) for c in mine) if mine else "<p style=\"margin:4px 0\">Nobody is in this list yet.</p>"
        extra = ""
        if key == "disclosure" and T["disclosure_shared_buyers"]:
            extra = "<p style=\"margin:4px 0\">%s more %s got the disclosure package from their own agent.</p>" % (
                v("shared_buyers", T["disclosure_shared_buyers"]), "buyer" if T["disclosure_shared_buyers"] == 1 else "buyers")
        out.append(block("list_" + key, head + extra + "<div%s>%s</div>" % (at("data-sr-list", key), body)))
    since = [it for it in (R.get("since_week_closed") or {}).get("items") or [] if not (link and (it.get("offer_related") or it.get("kind") == "offer"))]
    if since:
        out.append(block("since_week_closed", h2("Since the week closed") + NL.join(
            "<p style=\"margin:4px 0\">%s: %s</p>" % (core.fmt_day(it["date"]), esc(it["summary_safe"])) for it in since)
            + "<p style=\"margin:4px 0\">Logged after Sunday, so it is not in this week's numbers.</p>"))

    # ---- next week ----------------------------------------------------------------------------
    names = dict((c["id"], c["name_short"]) for c in d["contacts"])
    items = [s for s in d.get("next_week") or [] if not (link and any(names[i] in s for i in (writers | weighing) if i in names))]
    out.append(block("next_week", h2("What we are doing next week") + "<ol style=\"margin:0;padding-left:20px\">%s</ol>"
                     % NL.join("<li>%s</li>" % esc(s) for s in items)))

    # ---- the record: follow-up since we listed ---------------------------------------------------
    reached = len(set(c["id"] for c in people if any(t.get("direction") == "outbound" for t in c.get("touches") or [])))
    out.append(block("followup", h2("Follow-up") + "<p style=\"margin:4px 0\">Since we listed: %s follow-ups to %s people, on %s separate days. %s replies.</p>"
                     % (v("followups", T["touches_outbound"]), v("followup_people", reached), v("followup_days", T["outbound_distinct_days"]),
                        v("replies", T["replies_inbound"]))))

    # ---- every week in one table --------------------------------------------------------------
    cols = [("showings", "Shown"), ("agent_reported_tours", "Tours"), ("inquiries", "Inquiries"), ("disclosure_contacts_new", "Pkgs"),
            ("open_house_groups", "Open house"), ("touches_outbound", "Follow ups"), ("outbound_distinct_days", "Days"),
            ("replies_inbound", "Replies"), ("conversations_with_feedback", "Talks"), ("PRICE_PAIR", "High / fair"), ("offers", "Offers")]
    if T.get("online_views") is not None:
        cols.append(("online_views", "Views"))

    def week_cells(row, total=False):
        cells = []
        for field, _ in cols:
            if field == "PRICE_PAIR":
                t = "%d / %d" % (row["price_too_high"], row["price_fair_or_positive"])
            elif field == "outbound_distinct_days" and total:
                t = "&nbsp;"
            elif field == "online_views":
                t = "&nbsp;" if row.get(field) is None else shown(row[field])
            else:
                t = num(row, field)
            cells.append("<td %s>%s</td>" % (CELL, t))
        return NL.join(cells)

    def total_of(rows_):
        s = dict((f, sum(r[f] or 0 for r in rows_) if not any(r.get(f) is None for r in rows_) else None)
                 for f in ("showings", "keybox_showings", "agent_reported_tours", "inquiries", "disclosure_contacts_new", "touches_outbound",
                           "replies_inbound", "conversations_with_feedback", "price_too_high", "price_fair_or_positive", "offers",
                           "open_house_sessions"))
        for f in ("open_house_groups", "online_views"):
            got = [r[f] for r in rows_ if r.get(f) is not None]
            s[f] = sum(got) if got else None
        return s

    rows = ['<tr><th scope="col"%s %s>Week</th>%s</tr>' % (at("data-sr-col", "LABEL"), HEAD, NL.join(
        '<th scope="col"%s %s>%s</th>' % (at("data-sr-col", f), HEAD, esc(lab)) for f, lab in cols))]
    bands = []
    for w in weeks:
        if not bands or bands[-1][0] != w["list_price"]:
            bands.append((w["list_price"], []))
        bands[-1][1].append(w)
    for price, ws in bands:
        for w in ws:
            rows.append('<tr%s><th scope="row" %s>%d %s</th>%s</tr>' % (at("data-sr-row", w["n"]), CELL, w["n"], core.fmt_day(w["start"]), week_cells(w)))
        if len(bands) > 1:
            rows.append('<tr%s><th scope="row" %s>%d wks at %s</th>%s</tr>' % (at("data-sr-row", "sub:%d" % price), CELL, len(ws), money(price),
                                                                          week_cells(total_of(ws), total=True)))
    rows.append('<tr%s><th scope="row" %s>All %d</th>%s</tr>' % (at("data-sr-row", "all"), CELL, len(weeks), week_cells(total_of(weeks), total=True)))
    out.append(block("weekly_table", h2("Every week in one table") + '<table%s cellpadding="0" cellspacing="0" width="100%%">%s</table>'
                     % (at("data-sr-table", "weeks"), NL.join(rows))))

    # ---- the record at each list price ----------------------------------------------------------
    periods = d.get("price_periods") or []
    if len(periods) > 1:
        prow = [("days", "Days on the market"), ("showings", "Showings"), ("inquiries", "Inquiries"),
                ("open_house_groups", "Open house %s" % units[0]), ("touches_outbound", "Follow-ups we made"),
                ("replies_inbound", "Replies we received"), ("conversations_with_feedback", "Conversations with feedback"),
                ("price_too_high", "Said the price is too high"), ("price_fair_or_positive", "Said the price is fair or good"), ("offers", "Offers")]
        rows = ['<tr><th %s>&nbsp;</th>%s</tr>' % (HEAD, NL.join('<th scope="col"%s %s>At %s</th>' % (at("data-sr-col", p["price"]), HEAD, money(p["price"]))
                                                                 for p in periods))]
        for field, label in prow:
            cells = NL.join("<td %s>%s</td>" % (CELL, ("%d of %d" % (p[field], p["conversations_with_feedback"]) if field.startswith("price_")
                                                       else (oh_cell(p) if field == "open_house_groups" else shown(p[field])))) for p in periods)
            rows.append('<tr%s><th scope="row" %s>%s</th>%s</tr>' % (at("data-sr-row", field), CELL, esc(label), cells))
        out.append(block("price_periods", h2("The record at each list price") + '<table%s cellpadding="0" cellspacing="0" width="100%%">%s</table>'
                         % (at("data-sr-table", "periods"), NL.join(rows))))

    # ---- footer -------------------------------------------------------------------------------
    foot = ["<div>%s</div>" % esc(str(idn["name"]).upper()), "<div>%s%sDRE #%s</div>" % (esc(idn["realtor_line"]), DOT, idn["dre"]),
            "<div>%s</div>" % esc(idn["brand_line"]),
            '<div><a href="tel:%s" style="color:#C5A55A">%s</a>%s<a href="mailto:%s" style="color:#C5A55A">%s</a></div>'
            % (re.sub(r"\D", "", idn["phone"]), esc(idn["phone"]), DOT, esc(idn["email"]), esc(idn["email"]))]
    if not link:
        foot.append('<div><a href="%s" style="color:#C5A55A">OPEN THE COMPLETE RECORD</a></div>' % esc(link_url))
    foot.append('<div style="font-size:12px;color:#DDD6C2">%s</div>' % esc(idn["disclaimer"]))
    out.append('<tr><td%s bgcolor="#1A1A1A" style="padding:14px 8px;color:#C5A55A;font-size:13px">%s</td></tr>' % (sec("footer"), NL.join(foot)))
    out += ["</table>", "</body></html>"]
    return "\n".join(out) + "\n"
