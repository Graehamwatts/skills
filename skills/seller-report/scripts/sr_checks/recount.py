# -*- coding: utf-8 -*-
"""sr_checks.recount: every headline number of a seller report, counted again from the ledger's rows.

This is a second, separate implementation of references/counting-rules.md. It does not import
sr_contract_counts and it does not import the renderer. The ledger's rows (contacts, open_houses, offers,
listing.price_history, report) are flattened into dated events, and each number is a filter over those
events. When this file and the ledger's stored totals disagree, the gate stops the build and prints both.

Standard library only.
"""
import datetime

ANSWERED = ("replied", "passed", "writing_offer", "offer_submitted")
DISCLOSURE = ("disclosure_on_list", "disclosure_link_sent", "disclosure_opened", "disclosure_shared_by_agent")
PRICE_KEYS = ("too_high", "fair_or_positive", "not_raised")
QUIET_DAYS, LEAD_FRESH_DAYS, TRIES_FLAG = 30, 21, 3
# counts that print as "not recorded" when the listing does not track that kind of fact
TRACKED = {"keybox_showings": "keybox_showings", "disclosure_sent": "disclosure_sent",
           "disclosure_link_sent": "disclosure_sent", "disclosure_opened": "disclosure_opened",
           "disclosure_opened_confirmed": "disclosure_opened"}
LIST_KEYS = ("showings", "disclosure", "open_house", "other_inquiries")
TOURS = ("keybox_showing", "agent_reported_tour")
WEEK_SUM_FIELDS = ("showings", "keybox_showings", "agent_reported_tours", "inquiries", "disclosure_contacts_new", "disclosure_sent",
                   "disclosure_opened", "open_house_sessions", "open_house_sessions_without_count", "touches_outbound",
                   "replies_inbound", "conversations_with_feedback", "price_too_high", "price_fair_or_positive", "offers")


def day(s):
    y, m, d = (int(x) for x in str(s)[:10].split("-"))
    return datetime.date(y, m, d)


def iso(d):
    return d.isoformat()


def monday_of(d):
    return d - datetime.timedelta(days=d.weekday())


def buyer_side(c):
    """A person our team follows up with directly: not a team-side host, not a buyer reached through an agent."""
    return not c.get("team_side") and not c.get("represented_by")


def price_in_effect(history, on):
    """The list price on that day. A day before the first entry belongs to the first price."""
    hist = sorted(history, key=lambda e: e["date"])
    price = hist[0]["price"]
    for e in hist:
        if e["date"][:10] <= on:
            price = e["price"]
    return price


def lists_of(c):
    """The lists under "The details" a person belongs to, in the order they are printed: showings, disclosure,
    open_house, other_inquiries. The first is where the person is shown in full. Counted again here from the
    person's own rows (counting-rules.md, section 15)."""
    if c.get("team_side"):
        return []
    did = set(e.get("type") for e in c.get("engagements") or [])
    out = []
    if did & set(TOURS):
        out.append("showings")
    if buyer_side(c) and did & set(DISCLOSURE):
        out.append("disclosure")
    if "open_house_visit" in did:
        out.append("open_house")
    if not out and ("inquiry" in did or buyer_side(c)):
        out.append("other_inquiries")
    return out


def offer_word_of(c, offer_people):
    """Offer received, writing one, possibly, not yet, no or not discussed, as a key."""
    if c.get("id") in offer_people or c.get("status") == "offer_submitted":
        return "offer_received"
    if c.get("status") == "writing_offer" or c.get("offer_intent") == "yes":
        return "writing_one"
    if c.get("status") == "passed":
        return "no"
    return {"maybe": "possibly", "no": "not_yet"}.get(c.get("offer_intent"), "not_discussed")


def active(c, week_start, week_end):
    """Something dated inside the report week: a touch either way, a remark of theirs, or something they did."""
    dates = [x.get("date") for k in ("touches", "feedback_log", "engagements") for x in c.get(k) or []]
    return any(dt and week_start <= dt[:10] <= week_end for dt in dates)


def person_facts(c, week_end):
    """What one person's touches say, as of the Sunday the report week ended."""
    ts = sorted((t for t in c.get("touches") or [] if t.get("date") and t["date"][:10] <= week_end),
                key=lambda t: t["date"])
    ours = [t for t in ts if t.get("direction") == "outbound"]
    our_days = sorted(set(t["date"][:10] for t in ours))
    answer_days = sorted(set(t["date"][:10] for t in ts if t.get("direction") == "inbound" or t.get("outcome") == "reached"))
    last_answer = answer_days[-1] if answer_days else None
    last_any = ts[-1]["date"][:10] if ts else None
    since = [d for d in our_days if last_answer is None or d > last_answer]
    ch = {"call": 0, "text": 0, "email": 0, "in_person": 0, "unknown": 0}
    for t in ours:
        k = t.get("channel")
        ch["call" if k in ("call", "voicemail") else (k if k in ch else "unknown")] += 1
    return {
        "touches": len(ours), "days": len(our_days), "our_days": our_days, "replies": len(answer_days),
        "answer_days": answer_days, "last_any": last_any, "last_ours": our_days[-1] if our_days else None,
        "last_answer": last_answer, "tries_since_answer": len(since),
        "waiting": bool(our_days) and (last_answer is None or our_days[-1] > last_answer),
        "silent_days": (day(week_end) - day(last_any)).days if last_any else None,
        "by_channel": ch, "not_connected": len([t for t in ours if t.get("outcome") == "did_not_connect"]),
        "ours": ours,
    }


def conversations(c, week_end):
    """The person's own dated remarks that count as conversations, oldest first."""
    return sorted((e for e in c.get("feedback_log") or []
                   if e.get("counts_as_conversation", True) and e.get("date") and e["date"][:10] <= week_end),
                  key=lambda e: e["date"])


def price_row(c, week_end):
    """too_high, fair_or_positive, not_raised, or None when the person never told us anything.
    The latest conversation in which price came up decides."""
    log = conversations(c, week_end)
    said = [e for e in log if e.get("price_reaction") in ("too_high", "fair_or_positive")]
    return said[-1]["price_reaction"] if said else ("not_raised" if log else None)


def recount(d):
    """Returns a dict of everything the page may print. Keys:
    week_start, week_end, weeks (rows, oldest first), this_week, last_week, totals, pricing, themes (rows),
    liked (rows), periods (rows), bands (whole-week subtotals per list price), people (facts by contact id),
    statuses (problems found between a stored status and the touches), extra (numbers the page states in
    sentences: people followed up with, this week's channels, live offer leads)."""
    L, R = d["listing"], d["report"]
    ws, we = R["week_start"][:10], R["week_end"][:10]
    listed = L["list_date"][:10]
    everyone = d.get("contacts") or []
    counted = [c for c in everyone if buyer_side(c)]
    not_team = [c for c in everyone if not c.get("team_side")]
    facts = dict((c["id"], person_facts(c, we)) for c in everyone)

    def dated_ok(e):
        return not e.get("date") or e["date"][:10] <= we

    # ---- events ---------------------------------------------------------------------------
    def engagements(kind, people):
        return [(c, e) for c in people for e in c.get("engagements") or [] if e.get("type") == kind and dated_ok(e)]

    keybox = engagements("keybox_showing", not_team)
    tours = engagements("agent_reported_tour", not_team)
    inquiries = engagements("inquiry", not_team)
    package = [(c, e) for c in counted for e in c.get("engagements") or [] if e.get("type") in DISCLOSURE and dated_ok(e)]
    first_package = {}
    for c, e in package:
        if e.get("date"):
            cur = first_package.get(c["id"])
            first_package[c["id"]] = min(cur, e["date"][:10]) if cur else e["date"][:10]
    package_people = set(c["id"] for c, _ in package)
    followups = [(c, t) for c in counted for t in facts[c["id"]]["ours"]]
    answers = [(c["id"], dy) for c in counted for dy in facts[c["id"]]["answer_days"]]
    talks = [(c, e) for c in counted for e in conversations(c, we)]
    sessions = [o for o in d.get("open_houses") or [] if o.get("date") and o["date"][:10] <= we]
    offers = [o for o in d.get("offers") or [] if o.get("date") and o["date"][:10] <= we]

    def window(a, b, open_start=False):
        def inside(dt):
            return bool(dt) and (open_start or a <= dt[:10]) and dt[:10] <= b
        ses = [o for o in sessions if inside(o["date"])]
        counts = [o["groups"] for o in ses if o.get("groups") is not None]
        mine = [(c, t) for c, t in followups if inside(t["date"])]
        said = [e for _, e in talks if inside(e["date"])]
        return {
            "showings": len([1 for _, e in keybox + tours if inside(e.get("date"))]),
            "keybox_showings": len([1 for _, e in keybox if inside(e.get("date"))]),
            "agent_reported_tours": len([1 for _, e in tours if inside(e.get("date"))]),
            "inquiries": len([1 for _, e in inquiries if inside(e.get("date"))]),
            "disclosure_contacts_new": len([1 for dt in first_package.values() if inside(dt)]),
            "disclosure_sent": len([1 for _, e in package if e["type"] == "disclosure_link_sent" and inside(e.get("date"))]),
            "disclosure_opened": len([1 for _, e in package if e["type"] == "disclosure_opened" and inside(e.get("date"))]),
            "open_house_sessions": len(ses),
            "open_house_sessions_without_count": len(ses) - len(counts),
            "open_house_groups": sum(counts) if counts else None,
            "touches_outbound": len(mine),
            "outbound_people": len(set(c["id"] for c, _ in mine)),
            "outbound_distinct_days": len(set(t["date"][:10] for _, t in mine)),
            "replies_inbound": len([1 for _, dy in answers if inside(dy)]),
            "conversations_with_feedback": len(said),
            "price_too_high": len([1 for e in said if e.get("price_reaction") == "too_high"]),
            "price_fair_or_positive": len([1 for e in said if e.get("price_reaction") == "fair_or_positive"]),
            "offers": len([1 for o in offers if inside(o["date"])]),
            "by_channel": _channels([t for _, t in mine]),
        }

    # ---- weeks ----------------------------------------------------------------------------
    online = {}
    for w in ((d.get("online") or {}).get("weeks") or []) if isinstance(d.get("online"), dict) else []:
        seen = [[v for v in (w.get(kind) or {}).values() if isinstance(v, int)] for kind in ("views", "saves")]
        if seen[0] or seen[1]:
            online[w.get("n")] = (sum(seen[0]) if seen[0] else None, sum(seen[1]) if seen[1] else None)
    weeks, start, n = [], monday_of(day(listed)), 0
    while start <= day(ws):
        n += 1
        end = start + datetime.timedelta(days=6)
        first_listed_day = max(start, day(listed))
        tally, dt = {}, first_listed_day
        while dt <= end:
            p = price_in_effect(L["price_history"], iso(dt))
            tally[p] = tally.get(p, 0) + 1
            dt += datetime.timedelta(days=1)
        best = max(tally.values()) if tally else 0
        row = {"n": n, "start": iso(start), "end": iso(end), "is_current": iso(start) == ws,
               "list_price": [p for p in tally if tally[p] == best][-1] if tally else price_in_effect(L["price_history"], iso(end)),
               "days_listed_in_week": max(0, min(7, (end - first_listed_day).days + 1)),
               "days_on_market_at_week_end": (end - day(listed)).days}
        row.update(window(iso(start), iso(end)))
        row["online_views"], row["online_saves"] = online.get(n, (None, None))
        weeks.append(row)
        start += datetime.timedelta(days=7)

    # ---- list price periods, split by the date of each event ------------------------------------
    hist = sorted((e for e in L["price_history"] if e["date"][:10] <= we), key=lambda e: e["date"])
    periods = []
    for i, e in enumerate(hist):
        end = iso(day(hist[i + 1]["date"]) - datetime.timedelta(days=1)) if i + 1 < len(hist) else we
        p = {"price": e["price"], "start": e["date"][:10], "end": end, "days": (day(end) - day(e["date"])).days + 1}
        p.update(window(p["start"], end, open_start=(i == 0)))
        periods.append(p)

    # ---- whole-week subtotals per list price (the bands of the weekly table) ----------------------
    bands = []
    for w in weeks:
        if not bands or bands[-1]["price"] != w["list_price"]:
            bands.append({"price": w["list_price"], "weeks": []})
        bands[-1]["weeks"].append(w["n"])
    for b in bands:
        b.update(sum_weeks([w for w in weeks if w["n"] in b["weeks"]]))
    all_weeks = sum_weeks(weeks)
    # the "all weeks" line of online views is the count since listing: a site's running count where one was read
    all_weeks["online_views"], all_weeks["online_saves"] = _online_since(d, "views"), _online_since(d, "saves")

    # ---- totals ---------------------------------------------------------------------------
    def with_status(*names):
        return [c for c in counted if c.get("status") in names]

    waiting = with_status("awaiting_reply")
    open_people = with_status("replied")

    def quiet(c):
        return (facts[c["id"]]["silent_days"] or 0) > QUIET_DAYS

    counts_all = [o["groups"] for o in sessions if o.get("groups") is not None]
    both = keybox + tours
    spoke = [c for c in counted if conversations(c, we)]
    days_all = set(t["date"][:10] for _, t in followups)
    by_state = {}
    for o in offers:
        by_state[o.get("state")] = by_state.get(o.get("state"), 0) + 1
    team = [c for c in everyone if c.get("team_side")]
    totals = {
        "contact_records": len(everyone),
        "contacts": len(counted),
        "buyers_via_agent": len([c for c in everyone if c.get("represented_by")]),
        "team_side_people": len(team),
        "contacted": len([c for c in counted if facts[c["id"]]["last_any"]]),
        "contacted_through_host": len([c for c in counted if facts[c["id"]]["last_any"] and c.get("reached_through") == "open_house_host"]),
        "not_yet_contacted": len(with_status("not_yet_contacted")),
        "replied": len(with_status(*ANSWERED)),
        "awaiting_reply": len(waiting),
        "awaiting_reply_3plus_attempts": len([c for c in waiting if facts[c["id"]]["tries_since_answer"] >= TRIES_FLAG]),
        "awaiting_reply_answered_before": len([c for c in waiting if facts[c["id"]]["replies"]]),
        "awaiting_reply_quiet": len([c for c in waiting if quiet(c)]),
        "open_no_final_answer": len(open_people),
        "open_no_final_answer_quiet": len([c for c in open_people if quiet(c)]),
        "touches_outbound": len(followups),
        "outbound_person_days": sum(facts[c["id"]]["days"] for c in counted),
        "outbound_distinct_days": len(days_all),
        "touches_direction_not_recorded": len([1 for c in counted for t in c.get("touches") or []
                                               if t.get("date") and t["date"][:10] <= we and t.get("direction") == "unknown"]),
        "calls_not_connected": sum(facts[c["id"]]["not_connected"] for c in counted),
        "replies_inbound": len(answers),
        "showings": len(both),
        "keybox_showings": len(keybox),
        "agent_reported_tours": len(tours),
        "tours_undated": len([1 for _, e in both if not e.get("date")]),
        "tours_approximate_date": len([1 for _, e in both if e.get("date_quality") == "approximate"]),
        "tours_unconfirmed": len([1 for _, e in both if e.get("confirmed") is False]),
        "inquiries": len(inquiries),
        "inquiries_undated": len([1 for _, e in inquiries if not e.get("date")]),
        "disclosure_contacts": len(package_people),
        "disclosure_contacts_undated": len(package_people) - len(first_package),
        "disclosure_shared_buyers": len([c for c in everyone if c.get("represented_by") and not c.get("team_side")
                                         and any(e.get("type") in DISCLOSURE for e in c.get("engagements") or [])]),
        "disclosure_link_sent": len([1 for _, e in package if e["type"] == "disclosure_link_sent"]),
        "disclosure_opened_confirmed": len([1 for _, e in package if e["type"] == "disclosure_opened"]),
        "open_house_sessions": len(sessions),
        "open_house_sessions_without_count": len(sessions) - len(counts_all),
        "open_house_sessions_no_visitors": len([1 for g in counts_all if g == 0]),
        "open_house_groups": sum(counts_all) if counts_all else None,
        "offers": len(offers),
        "offers_by_state": by_state,
        "people_with_feedback": len(spoke),
        "conversations_with_feedback": len(talks),
        "by_status": dict((s, len(with_status(s))) for s in ("not_yet_contacted", "awaiting_reply", "replied", "passed",
                                                             "writing_offer", "offer_submitted")),
        "team_side_set_aside": {"people": len(team), "touches_outbound": sum(facts[c["id"]]["touches"] for c in team),
                                "replies_inbound": sum(facts[c["id"]]["replies"] for c in team)},
        "lists": dict((k, len([c for c in everyone if k in lists_of(c)])) for k in LIST_KEYS),
        "lists_active_this_week": dict((k, len([c for c in everyone if (lists_of(c) or [None])[0] == k and active(c, ws, we)]))
                                       for k in LIST_KEYS),
        "online_views": _online_since(d, "views"),
        "online_saves": _online_since(d, "saves"),
    }

    # ---- what people are saying -------------------------------------------------------------
    rows = dict((k, 0) for k in PRICE_KEYS)
    row_of = {}
    for c in spoke:
        row_of[c["id"]] = price_row(c, we)
        rows[row_of[c["id"]]] += 1
    asked = []
    for c in spoke:
        vals = [e.get("price_asked") for e in conversations(c, we)]
        asked.append(True if True in vals else (False if False in vals else None))
    pricing = dict(rows, people_with_feedback=len(spoke), raised_price=rows["too_high"] + rows["fair_or_positive"],
                   price_asked_recorded=len([a for a in asked if a is not None]),
                   asked_directly=len([a for a in asked if a is True]), conversations_with_feedback=len(talks))

    vocab = d.get("themes_vocabulary") or {}
    theme_labels = dict((t["key"], t) for t in vocab.get("themes") or [])
    liked_labels = dict((t["key"], t["label"]) for t in vocab.get("liked") or [])

    def first_this_week(c, key, field):
        log = conversations(c, we)
        return (any(key in (e.get(field) or []) for e in log if e["date"][:10] >= ws)
                and not any(key in (e.get(field) or []) for e in log if e["date"][:10] < ws))

    themes = []
    for key in [t["key"] for t in vocab.get("themes") or []]:
        who = [c for c in spoke if key in (c.get("themes") or [])]
        if not who:
            continue
        if key == "other":
            by_label = {}
            for c in who:
                by_label.setdefault(" ".join((c.get("theme_other") or "Other").split()).lower(), []).append(c)
            for _, grp in sorted(by_label.items()):
                themes.append({"key": "other", "label": " ".join((grp[0].get("theme_other") or "Other").split()),
                               "people": len(grp), "new_this_week": len([c for c in grp if first_this_week(c, "other", "themes")]),
                               "hide_in_link_copy": False, "contact_ids": [c["id"] for c in grp]})
        else:
            themes.append({"key": key, "label": theme_labels[key]["label"], "people": len(who),
                           "new_this_week": len([c for c in who if first_this_week(c, key, "themes")]),
                           "hide_in_link_copy": bool(theme_labels[key].get("hide_in_link_copy")),
                           "contact_ids": [c["id"] for c in who]})
    liked = []
    for key, label in liked_labels.items():
        who = [c for c in spoke if key in (c.get("liked") or [])]
        if who:
            liked.append({"key": key, "label": label, "people": len(who), "contact_ids": [c["id"] for c in who]})

    # ---- offer leads ------------------------------------------------------------------------
    leads = []
    for c in counted:
        if c.get("status") in ("passed", "offer_submitted", "not_yet_contacted"):
            continue
        if c.get("offer_intent") in ("yes", "maybe") or c.get("status") == "writing_offer":
            gap = facts[c["id"]]["silent_days"]
            leads.append({"contact_id": c["id"], "lead_state": "live" if gap is not None and gap <= LEAD_FRESH_DAYS else "earlier_interest"})
    offer_people = set(o.get("contact_id") for o in d.get("offers") or [] if o.get("contact_id"))
    weighing = set(l["contact_id"] for l in leads) | set(c["id"] for c in everyone
                                                           if c.get("offer_intent") in ("yes", "maybe") or c.get("status") == "writing_offer")

    # ---- a stored status against the touches --------------------------------------------------
    statuses = []
    for c in counted:
        f, st = facts[c["id"]], c.get("status")
        if (st == "not_yet_contacted") != (f["last_any"] is None):
            statuses.append("%s: status %s, but the log shows %s" % (c["id"], st, "no contact" if f["last_any"] is None else "contact on " + f["last_any"]))
        elif st == "awaiting_reply" and f["replies"] and not f["waiting"]:
            statuses.append("%s: shown as still waiting, but their last answer (%s) is not older than our last follow-up (%s)"
                            % (c["id"], f["last_answer"], f["last_ours"]))
        elif st == "replied" and (f["waiting"] or not f["replies"]):
            statuses.append("%s: shown as answered, but our latest follow-up (%s) has no answer after it" % (c["id"], f["last_ours"]))
        want = price_row(c, we) or "unknown"
        if c.get("price_reaction") != want:
            statuses.append("%s: price reaction stored as %s, the conversations give %s" % (c["id"], c.get("price_reaction"), want))
    for c in everyone:
        if c.get("represented_by") and c.get("status") != "through_agent":
            statuses.append("%s: a buyer reached through an agent must have status through_agent" % c["id"])

    cur = [w for w in weeks if w["is_current"]]
    this_week = cur[0] if cur else None
    last_week = weeks[weeks.index(this_week) - 1] if this_week is not None and weeks.index(this_week) > 0 else None
    no_final = dict((k, len([c for c in open_people if c.get("interest") in v]))
                    for k, v in (("interested", ("warm", "hot")), ("undecided", ("cold",)), ("no_read", ("unknown", None))))
    market = None
    M = d.get("market")
    if isinstance(M, dict) and M.get("sales"):
        used = sorted(s["days_to_contract"] for s in M["sales"] if s.get("used_in_average") and isinstance(s.get("days_to_contract"), int))
        if used:
            mid = len(used) // 2
            med = used[mid] if len(used) % 2 else (used[mid - 1] + used[mid]) / 2.0
            dom = (day(R["report_date"]) - day(listed)).days
            market = {"used": len(used), "closed": len(M["sales"]), "average": int(sum(used) / float(len(used)) + 0.5),
                      "median": int(med + 0.5), "shortest": used[0], "longest": used[-1],
                      "under_contract_by_now": len([v for v in used if v <= dom])}
    channels = ((d.get("marketing") or {}).get("channels") or []) if isinstance(d.get("marketing"), dict) else []
    members = dict((k, [c["id"] for c in everyone if k in lists_of(c)]) for k in LIST_KEYS)
    placed = dict((c["id"], {"lists": lists_of(c), "primary": (lists_of(c) or [None])[0], "active": active(c, ws, we),
                             "offer_word": offer_word_of(c, offer_people)}) for c in everyone)
    running = [ch for ch in channels if ch.get("status") == "on" and (ch.get("checked") or "") >= we]
    return {
        "week_start": ws, "week_end": we, "weeks": weeks, "this_week": this_week, "last_week": last_week,
        "totals": totals, "pricing": pricing, "themes": themes, "liked": liked, "periods": periods, "bands": bands,
        "all_weeks": all_weeks, "people": facts, "statuses": statuses, "price_row_of": row_of,
        "lists": members, "placed": placed,
        "extra": {
            "followup_people": len(set(c["id"] for c, _ in followups)),
            "followup_people_through_host": len(set(c["id"] for c, _ in followups if c.get("reached_through") == "open_house_host")),
            "leads_live": len([l for l in leads if l["lead_state"] == "live"]),
            "leads_earlier": len([l for l in leads if l["lead_state"] == "earlier_interest"]),
            "leads": leads, "offer_people": offer_people, "weighing": weighing,
            "people_with_no_theme": len([c for c in spoke if not c.get("themes")]),
            "liked_people": len([c for c in spoke if c.get("liked")]),
            "days_on_market": (day(R["report_date"]) - day(listed)).days,
            "days_on_market_at_week_end": (day(we) - day(listed)).days,
            "weeks_on_market": len(weeks),
            "units": sorted(set(o.get("counted_unit") for o in sessions if o.get("groups") is not None and o.get("counted_unit"))),
            "week_reply_people": len(set(cid for cid, dy in answers if ws <= dy <= we)),
            "no_final": no_final, "market": market,
            "marketing_running": len(running), "marketing_not_running": [ch.get("channel") for ch in channels if ch not in running],
        },
    }


def _channels(touches):
    out = {"call": 0, "text": 0, "email": 0, "in_person": 0, "unknown": 0}
    for t in touches:
        k = t.get("channel")
        out["call" if k in ("call", "voicemail") else (k if k in out else "unknown")] += 1
    return out


def _online_since(d, kind):
    """Views or saves since the home was listed, counted again: for each portal the running count the site showed
    at the latest reading when the ledger has one, otherwise that portal's weekly figures added up."""
    o = d.get("online") if isinstance(d.get("online"), dict) else {}
    per = {}
    for w in o.get("weeks") or []:
        for portal, v in ((w.get(kind) or {}) if isinstance(w, dict) else {}).items():
            if isinstance(v, int):
                per[portal] = per.get(portal, 0) + v
    for portal, v in (((o.get("since_listing") or {}).get(kind)) or {}).items():
        if isinstance(v, int):
            per[portal] = v
    return sum(per.values()) if per else None


def _sum_known(values):
    got = [v for v in values if v is not None]
    return sum(got) if got else None


def sum_weeks(rows):
    """Whole-week sums. open_house_groups adds the sessions that kept a count and stays None when none did, and
    the online figures add the weeks that have one."""
    out = dict((k, sum(w[k] for w in rows)) for k in WEEK_SUM_FIELDS)
    for k in ("open_house_groups", "online_views", "online_saves"):
        out[k] = _sum_known([w.get(k) for w in rows])
    return out


def printable(d, name, value, week=None):
    """The value a page may print for a count: None ('not recorded') when the listing does not track that
    kind of fact, or when the ledger marks that one week as not checked."""
    flag = TRACKED.get(name)
    if flag and not ((d.get("report") or {}).get("tracking") or {}).get(flag):
        return None
    if week is not None and name in week and week[name] is None and name != "open_house_groups":
        return None
    return value


def differences(d, mine):
    """Where the ledger's stored numbers and this recount disagree: [(path, stored, counted)]."""
    out = []

    def cmp(path, stored, counted, name=None, week=None):
        want = printable(d, name, counted, week) if name else counted
        if stored != want:
            out.append((path, stored, want))

    T = d.get("totals") or {}
    for k, v in mine["totals"].items():
        if k not in T:
            out.append(("totals." + k, "missing", v))
        else:
            cmp("totals." + k, T[k], v, name=k)
    stored_weeks = d.get("weeks") or []
    if len(stored_weeks) != len(mine["weeks"]):
        out.append(("weeks", "%d rows" % len(stored_weeks), "%d rows" % len(mine["weeks"])))
    else:
        for sw, w in zip(stored_weeks, mine["weeks"]):
            for k, v in w.items():
                if k == "by_channel":
                    continue
                if k not in sw:
                    out.append(("weeks[%d].%s" % (w["n"], k), "missing", v))
                else:
                    cmp("weeks[%d].%s" % (w["n"], k), sw[k], v, name=k, week=sw)
    PT = d.get("pricing_tally") or {}
    for k, v in mine["pricing"].items():
        cmp("pricing_tally." + k, PT.get(k, "missing"), v)
    TT = d.get("themes_tally") or {}
    stored_rows = sorted((r.get("key"), r.get("label"), r.get("people"), r.get("new_this_week")) for r in TT.get("rows") or [])
    my_rows = sorted((r["key"], r["label"], r["people"], r["new_this_week"]) for r in mine["themes"])
    if stored_rows != my_rows:
        out.append(("themes_tally.rows", stored_rows, my_rows))
    cmp("themes_tally.people_with_feedback", TT.get("people_with_feedback", "missing"), mine["pricing"]["people_with_feedback"])
    cmp("themes_tally.people_with_no_theme", TT.get("people_with_no_theme", "missing"), mine["extra"]["people_with_no_theme"])
    LT = d.get("liked_tally") or {}
    stored_rows = sorted((r.get("key"), r.get("people")) for r in LT.get("rows") or [])
    my_rows = sorted((r["key"], r["people"]) for r in mine["liked"])
    if stored_rows != my_rows:
        out.append(("liked_tally.rows", stored_rows, my_rows))
    cmp("liked_tally.people", LT.get("people", "missing"), mine["extra"]["liked_people"])
    stored_periods = d.get("price_periods") or []
    if len(stored_periods) != len(mine["periods"]):
        out.append(("price_periods", "%d rows" % len(stored_periods), "%d rows" % len(mine["periods"])))
    else:
        for i, (sp, p) in enumerate(zip(stored_periods, mine["periods"])):
            for k, v in p.items():
                if k in sp:
                    cmp("price_periods[%d].%s" % (i, k), sp[k], v)
    watch = sorted((w.get("contact_id"), w.get("lead_state")) for w in d.get("offer_watch") or [])
    mine_watch = sorted((l["contact_id"], l["lead_state"]) for l in mine["extra"]["leads"])
    if watch != mine_watch:
        out.append(("offer_watch", watch, mine_watch))
    R = d.get("report") or {}
    cmp("report.days_on_market", R.get("days_on_market"), mine["extra"]["days_on_market"])
    cmp("report.days_on_market_at_week_end", R.get("days_on_market_at_week_end"), mine["extra"]["days_on_market_at_week_end"])
    cmp("report.weeks_on_market", R.get("weeks_on_market"), mine["extra"]["weeks_on_market"])
    for c in d.get("contacts") or []:
        here = mine["placed"][c["id"]]
        for sk, mk in (("lists", "lists"), ("primary_list", "primary"), ("offer_word", "offer_word"), ("active_this_week", "active")):
            if c.get(sk, "missing") != here[mk]:
                out.append(("contacts[%s].%s" % (c["id"], sk), c.get(sk, "missing"), here[mk]))
        f, s = mine["people"][c["id"]], c.get("followup") or {}
        for sk, mk in (("outbound_touches", "touches"), ("outbound_days", "days"), ("replies", "replies"),
                       ("tries_since_last_answer", "tries_since_answer"), ("last_reply_date", "last_answer"),
                       ("last_outbound_date", "last_ours"), ("last_touch_date", "last_any")):
            if sk in s and s[sk] != f[mk]:
                out.append(("contacts[%s].followup.%s" % (c["id"], sk), s[sk], f[mk]))
    return out
