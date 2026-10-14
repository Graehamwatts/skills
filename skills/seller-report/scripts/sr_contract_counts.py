# -*- coding: utf-8 -*-
"""sr_contract_counts: the counting rules of the seller-report skill, as code.

references/counting-rules.md says the same thing in words. Import these through sr_contract
(C.recount, C.contact_facts, C.finish_ledger and so on), not from this file.
Standard library only.
"""
import datetime

from sr_contract import *        # noqa: F401,F403  (the enumerations and helpers)


NULLABLE_COUNTS = ("keybox_showings", "disclosure_sent", "disclosure_opened", "disclosure_link_sent",
                   "disclosure_opened_confirmed", "open_house_groups", "online_views", "online_saves")
# report.tracking flag -> the count keys that are null when that kind of fact is not recorded for the listing
TRACKING_KEYS = {"keybox_showings": ("keybox_showings",), "disclosure_sent": ("disclosure_sent", "disclosure_link_sent"),
                 "disclosure_opened": ("disclosure_opened", "disclosure_opened_confirmed")}


def contact_facts(c, week_end_day):
    """Everything derived from one person's touches, as of the end of the report week."""
    we = iso(week_end_day)
    ts = sorted((t for t in c.get("touches") or [] if t["date"] <= we), key=lambda t: t["date"])
    out = [t for t in ts if is_followup(t)]
    out_days = sorted(set(t["date"] for t in out))
    rep_days = sorted(set(t["date"] for t in ts if is_reply(t)))
    last_out, last_rep = (out_days[-1] if out_days else None), (rep_days[-1] if rep_days else None)
    last = ts[-1]["date"] if ts else None
    return {
        "outbound_touches": len(out), "outbound_days": len(out_days), "outbound_dates": out_days,
        "replies": len(rep_days), "reply_dates": rep_days,
        "first_touch_date": ts[0]["date"] if ts else None, "last_touch_date": last,
        "last_outbound_date": last_out, "last_reply_date": last_rep,
        "tries_since_last_answer": len([d for d in out_days if last_rep is None or d > last_rep]),
        "waiting": bool(out_days) and (last_rep is None or last_out > last_rep),
        "days_since_last_touch": (parse_date(we) - parse_date(last)).days if last else None,
        "calls_not_connected": len([t for t in out if t.get("outcome") == "did_not_connect"]),
        "direction_not_recorded": len([t for t in ts if t.get("direction") == "unknown"]),
    }


FOLLOWUP_KEYS = ("outbound_touches", "outbound_days", "replies", "first_touch_date", "last_touch_date",
                 "last_outbound_date", "last_reply_date", "tries_since_last_answer", "days_since_last_touch",
                 "calls_not_connected")


def followup_block(c, week_end_day):
    """The contacts[].followup block stored in the ledger."""
    f = contact_facts(c, week_end_day)
    return dict((k, f[k]) for k in FOLLOWUP_KEYS)


def base_status(c, week_end_day):
    """The status the touches alone give: through_agent, not_yet_contacted, awaiting_reply or replied.
    passed, writing_offer and offer_submitted are tags that replace 'replied' (and 'awaiting_reply' once
    the person has given a final answer)."""
    if c.get("represented_by"):
        return "through_agent"
    f = contact_facts(c, week_end_day)
    if f["last_touch_date"] is None:
        return "not_yet_contacted"
    return "awaiting_reply" if f["waiting"] or not f["replies"] else "replied"


def counted_feedback(c, week_end_day):
    """The person's feedback entries that count as conversations, oldest first."""
    we = iso(week_end_day)
    return sorted((e for e in c.get("feedback_log") or [] if e.get("counts_as_conversation", True) and e["date"] <= we),
                  key=lambda e: e["date"])


def derive_price_reaction(c, week_end_day):
    """Per person: the latest conversation in which price came up decides. No such conversation: not_raised.
    No conversation at all: unknown."""
    log = counted_feedback(c, week_end_day)
    raised = [e for e in log if e.get("price_reaction") in ("too_high", "fair_or_positive")]
    return raised[-1]["price_reaction"] if raised else ("not_raised" if log else "unknown")


def derive_price_asked(c, week_end_day):
    vals = [e.get("price_asked") for e in counted_feedback(c, week_end_day)]
    return True if True in vals else (False if False in vals else None)


def offer_people_ids(d):
    """People the link copy must never name as weighing or having written an offer."""
    ids = set(o.get("contact_id") for o in d.get("offers") or [] if o.get("contact_id"))
    ids |= set(w["contact_id"] for w in d.get("offer_watch") or [])
    ids |= set(c["id"] for c in d.get("contacts") or []
               if c.get("offer_intent") in ("yes", "maybe") or c.get("status") in ("writing_offer", "offer_submitted"))
    return ids


def contact_lists(c):
    """The lists under "The details" this person belongs to, in the order they are printed.

    showings          anyone not team side with a key-box showing or a tour an agent reported
    disclosure        a person we follow up with who is tied to the disclosure package (on the list, sent, opened)
    open_house        anyone not team side who came to an open house and left a name
    other_inquiries   an inquiry from someone in none of the lists above, and anyone else we follow up with

    The first key is where the person is shown in full. Team-side hosts are in no list, and neither is a buyer
    whose only tie is a package their own agent shared: those buyers are stated as one count."""
    if c.get("team_side"):
        return []
    types = set(e.get("type") for e in c.get("engagements") or [])
    out = []
    if types & set(TOUR_TYPES):
        out.append("showings")
    if is_counted(c) and types & set(DISCLOSURE_TYPES):
        out.append("disclosure")
    if "open_house_visit" in types:
        out.append("open_house")
    if not out and ("inquiry" in types or is_counted(c)):
        out.append("other_inquiries")
    return out


def derive_offer_word(c, offer_ids=()):
    """What the person has said about writing an offer, as an OFFER_WORDS key. An offer on file comes first,
    then what they told us (status and offer_intent). 'not_yet' is someone who said no offer for now and has
    not passed. 'not_discussed' means an offer has not come up."""
    if c.get("id") in offer_ids or c.get("status") == "offer_submitted":
        return "offer_received"
    if c.get("status") == "writing_offer" or c.get("offer_intent") == "yes":
        return "writing_one"
    if c.get("status") == "passed":
        return "no"
    return {"maybe": "possibly", "no": "not_yet"}.get(c.get("offer_intent"), "not_discussed")


def active_in_week(c, week_start_day, week_end_day):
    """True when the log holds a touch in either direction, something the person told us, or something they
    did (a showing, a package, an open house visit, an inquiry) dated inside the report week."""
    a, b = iso(week_start_day), iso(week_end_day)
    dates = [t.get("date") for t in c.get("touches") or []] + [e.get("date") for e in c.get("feedback_log") or []]
    dates += [e.get("date") for e in c.get("engagements") or []]
    return any(day and a <= day <= b for day in dates)


def online_by_week(d):
    """{week number: (views, saves)} from the optional ledger.online block. A week with no figure from any
    portal is not in the result, and a kind with no figure that week is None."""
    out = {}
    for w in (d.get("online") or {}).get("weeks") or []:
        views = [v for v in (w.get("views") or {}).values() if isinstance(v, int)]
        saves = [v for v in (w.get("saves") or {}).values() if isinstance(v, int)]
        if views or saves:
            out[w.get("n")] = (sum(views) if views else None, sum(saves) if saves else None)
    return out


def online_totals(d):
    """(views, saves) since the home was listed, from the optional ledger.online block. For each portal: the
    running count the site showed at the latest reading (online.since_listing) when one is on file, otherwise the
    sum of that portal's weekly figures. None when no portal has a figure of that kind."""
    o = d.get("online") or {}
    out = []
    for kind in ("views", "saves"):
        running = dict((p, v) for p, v in ((o.get("since_listing") or {}).get(kind) or {}).items() if isinstance(v, int))
        weekly = {}
        for w in o.get("weeks") or []:
            for p, v in (w.get(kind) or {}).items():
                if isinstance(v, int):
                    weekly[p] = weekly.get(p, 0) + v
        got = [running.get(p, weekly.get(p)) for p in sorted(set(running) | set(weekly))]
        out.append(sum(got) if got else None)
    return tuple(out)


def _periods(L, we):
    hist = sorted((e for e in L["price_history"] if e["date"] <= we), key=lambda e: e["date"])
    out = []
    for i, e in enumerate(hist):
        b = iso(parse_date(hist[i + 1]["date"]) - datetime.timedelta(days=1)) if i + 1 < len(hist) else we
        out.append({"price": e["price"], "start": e["date"], "end": b, "first": i == 0,
                    "days": (parse_date(b) - parse_date(e["date"])).days + 1})
    return out


def recount(d):
    """Recomputes every derived number in a ledger from its rows. validate_ledger compares the stored numbers
    with this, and the ledger builder may use it to fill them in. Needs listing, report, contacts, open_houses
    and offers. Returns totals, weeks, pricing_tally, themes_tally, liked_tally, price_periods, offer_watch
    and followup (by contact id)."""
    L, R = d["listing"], d["report"]
    ws, we = iso(R["week_start"]), iso(R["week_end"])
    contacts = d.get("contacts") or []
    counted = [c for c in contacts if is_counted(c)]
    team = [c for c in contacts if c.get("team_side")]
    facts = dict((c["id"], contact_facts(c, we)) for c in contacts)
    ohs = [o for o in d.get("open_houses") or [] if o["date"] <= we]
    offers = [o for o in d.get("offers") or [] if o["date"] <= we]

    def engs(types, cs):
        return [(c, e) for c in cs for e in c.get("engagements") or [] if e["type"] in types and (e.get("date") or "") <= we]

    nonteam = [c for c in contacts if not c.get("team_side")]
    kb, ar, inq = engs(("keybox_showing",), nonteam), engs(("agent_reported_tour",), nonteam), engs(("inquiry",), nonteam)
    disc = engs(DISCLOSURE_TYPES, counted)
    disc_first = {}
    for c, e in disc:
        if e.get("date") and (c["id"] not in disc_first or e["date"] < disc_first[c["id"]]):
            disc_first[c["id"]] = e["date"]
    disc_ids = set(c["id"] for c, _ in disc)
    out = [(c, t) for c in counted for t in c.get("touches") or [] if t["date"] <= we and is_followup(t)]
    unk = [t for c in counted for t in c.get("touches") or [] if t["date"] <= we and t.get("direction") == "unknown"]
    reps = [(c["id"], day) for c in counted for day in facts[c["id"]]["reply_dates"]]
    conv = [(c, e) for c in counted for e in counted_feedback(c, we)]
    approx = [e["date"] for c in nonteam for e in c.get("engagements") or [] if e.get("date_quality") == "approximate" and e.get("date")]
    approx += [t["date"] for c in counted for t in c.get("touches") or [] if t.get("date_quality") == "approximate"]

    def window(a, b, first=False):
        def inw(day):
            return bool(day) and (first or a <= day) and day <= b
        ses = [o for o in ohs if inw(o["date"])]
        got = [o["groups"] for o in ses if o.get("groups") is not None]
        wout = [(c, t) for c, t in out if inw(t["date"])]
        return {
            "showings": len([1 for _, e in kb + ar if inw(e.get("date"))]),
            "keybox_showings": len([1 for _, e in kb if inw(e.get("date"))]),
            "agent_reported_tours": len([1 for _, e in ar if inw(e.get("date"))]),
            "inquiries": len([1 for _, e in inq if inw(e.get("date"))]),
            "disclosure_contacts_new": len([1 for day in disc_first.values() if inw(day)]),
            "disclosure_sent": len([1 for _, e in disc if e["type"] == "disclosure_link_sent" and inw(e.get("date"))]),
            "disclosure_opened": len([1 for _, e in disc if e["type"] == "disclosure_opened" and inw(e.get("date"))]),
            "open_house_sessions": len(ses),
            "open_house_sessions_without_count": len(ses) - len(got),
            "open_house_groups": sum(got) if got else None,
            "touches_outbound": len(wout),
            "outbound_people": len(set(c["id"] for c, _ in wout)),
            "outbound_distinct_days": len(set(t["date"] for _, t in wout)),
            "replies_inbound": len([1 for _, day in reps if inw(day)]),
            "conversations_with_feedback": len([1 for _, e in conv if inw(e["date"])]),
            "price_too_high": len([1 for _, e in conv if e.get("price_reaction") == "too_high" and inw(e["date"])]),
            "price_fair_or_positive": len([1 for _, e in conv if e.get("price_reaction") == "fair_or_positive" and inw(e["date"])]),
            "offers": len([1 for o in offers if inw(o["date"])]),
        }

    weeks, online = [], online_by_week(d)
    for n, a, b in list_weeks(L["list_date"], ws):
        w = {"n": n, "start": iso(a), "end": iso(b), "is_current": iso(a) == ws,
             "list_price": week_list_price(L["price_history"], L["list_date"], a, b),
             "days_listed_in_week": max(0, min(7, (b - max(a, parse_date(L["list_date"]))).days + 1)),
             "days_on_market_at_week_end": days_on_market(L["list_date"], b)}
        w.update(window(iso(a), iso(b)))
        w["approximate_dates_used"] = len([1 for day in approx if iso(a) <= day <= iso(b)])
        w["online_views"], w["online_saves"] = online.get(n, (None, None))
        weeks.append(w)

    periods = _periods(L, we)
    for p in periods:
        p.update(window(p["start"], p["end"], first=p.pop("first")))
        for k in ("disclosure_contacts_new", "disclosure_sent", "disclosure_opened", "outbound_people",
                  "outbound_distinct_days", "open_house_sessions_without_count"):
            p.pop(k)

    def n_status(*names):
        return len([c for c in counted if c.get("status") in names])

    awaiting = [c for c in counted if c.get("status") == "awaiting_reply"]
    quiet = lambda c: (facts[c["id"]]["days_since_last_touch"] or 0) > LIMITS["quiet_days"]
    by_channel = dict((k, 0) for k in CHANNELS)
    for _, t in out:
        by_channel[t.get("channel") if t.get("channel") in CHANNELS else "unknown"] += 1
    tours = kb + ar
    with_count = [o["groups"] for o in ohs if o.get("groups") is not None]
    by_state = {}
    for o in offers:
        by_state[o.get("state")] = by_state.get(o.get("state"), 0) + 1
    people = [c for c in counted if counted_feedback(c, we)]
    totals = {
        "through": we,
        "contact_records": len(contacts),
        "contacts": len(counted),
        "buyers_via_agent": len([c for c in contacts if c.get("represented_by")]),
        "team_side_people": len(team),
        "contacted": len([c for c in counted if facts[c["id"]]["last_touch_date"]]),
        "contacted_through_host": len([c for c in counted if facts[c["id"]]["last_touch_date"] and c.get("reached_through") == "open_house_host"]),
        "not_yet_contacted": n_status("not_yet_contacted"),
        "replied": n_status(*ANSWERED_STATUSES),
        "awaiting_reply": len(awaiting),
        "awaiting_reply_3plus_attempts": len([c for c in awaiting if facts[c["id"]]["tries_since_last_answer"] >= LIMITS["tries_flag"]]),
        "awaiting_reply_answered_before": len([c for c in awaiting if facts[c["id"]]["replies"]]),
        "awaiting_reply_quiet": len([c for c in awaiting if quiet(c)]),
        "open_no_final_answer": n_status("replied"),
        "open_no_final_answer_quiet": len([c for c in counted if c.get("status") == "replied" and quiet(c)]),
        "by_status": dict((s, n_status(s)) for s in STATUSES if s != "through_agent"),
        "by_interest": dict((s, len([c for c in counted if c.get("interest") == s])) for s in INTEREST),
        "offer_intent_yes_or_maybe": len([c for c in counted if c.get("offer_intent") in ("yes", "maybe")]),
        "touches_outbound": len(out),
        "outbound_by_channel": by_channel,
        "outbound_person_days": sum(facts[c["id"]]["outbound_days"] for c in counted),
        "outbound_distinct_days": len(set(t["date"] for _, t in out)),
        "touches_direction_not_recorded": len(unk),
        "calls_not_connected": len([1 for _, t in out if t.get("outcome") == "did_not_connect"]),
        "replies_inbound": len(reps),
        "showings": len(tours),
        "keybox_showings": len(kb),
        "agent_reported_tours": len(ar),
        "tours_undated": len([1 for _, e in tours if not e.get("date")]),
        "tours_approximate_date": len([1 for _, e in tours if e.get("date_quality") == "approximate"]),
        "tours_unconfirmed": len([1 for _, e in tours if e.get("confirmed") is False]),
        "inquiries": len(inq),
        "inquiries_undated": len([1 for _, e in inq if not e.get("date")]),
        "disclosure_contacts": len(disc_ids),
        "disclosure_contacts_undated": len(disc_ids) - len(disc_first),
        "disclosure_shared_buyers": len([c for c in contacts if c.get("represented_by") and not c.get("team_side")
                                         and any(e["type"] in DISCLOSURE_TYPES for e in c.get("engagements") or [])]),
        "disclosure_link_sent": len([1 for _, e in disc if e["type"] == "disclosure_link_sent"]),
        "disclosure_opened_confirmed": len([1 for _, e in disc if e["type"] == "disclosure_opened"]),
        "open_house_sessions": len(ohs),
        "open_house_sessions_without_count": len(ohs) - len(with_count),
        "open_house_sessions_no_visitors": len([1 for g in with_count if g == 0]),
        "open_house_groups": sum(with_count) if with_count else None,
        "open_house_disclosure_requests": sum(o.get("disclosure_requests") or 0 for o in ohs),
        "offers": len(offers),
        "offers_by_state": by_state,
        "people_with_feedback": len(people),
        "conversations_with_feedback": len(conv),
        "team_side_set_aside": {
            "people": len(team),
            "touches_outbound": sum(facts[c["id"]]["outbound_touches"] for c in team),
            "replies_inbound": sum(facts[c["id"]]["replies"] for c in team)},
        # the lists under "The details": the count in each heading, and how many of those people are shown in full
        "lists": dict((k, len([c for c in contacts if k in contact_lists(c)])) for k in LIST_KEYS),
        "lists_active_this_week": dict((k, len([c for c in contacts if (contact_lists(c) or [None])[0] == k
                                                 and active_in_week(c, ws, we)])) for k in LIST_KEYS),
        "online_views": online_totals(d)[0],
        "online_saves": online_totals(d)[1],
    }

    tally = dict((k, len([c for c in people if c.get("price_reaction") == k])) for k in PRICE_BUCKETS)
    asked = [derive_price_asked(c, we) for c in people]
    pricing = {
        "people_with_feedback": len(people),
        "too_high": tally["too_high"], "fair_or_positive": tally["fair_or_positive"], "not_raised": tally["not_raised"],
        "raised_price": tally["too_high"] + tally["fair_or_positive"],
        "price_asked_recorded": len([a for a in asked if a is not None]),
        "asked_directly": len([a for a in asked if a is True]),
        "conversations_with_feedback": len(conv),
    }

    def new_this_week(c, key, field):
        log = counted_feedback(c, we)
        return (any(key in (e.get(field) or []) for e in log if e["date"] >= ws)
                and not any(key in (e.get(field) or []) for e in log if e["date"] < ws))

    labels = dict((k, lab) for k, lab, _, _ in THEMES)
    groups = dict((k, g) for k, _, g, _ in THEMES)
    rows = []
    for k in THEME_KEYS:
        if k == "other":
            continue
        who = [c for c in people if k in (c.get("themes") or [])]
        if who:
            rows.append({"key": k, "label": labels[k], "group": groups[k], "people": len(who),
                         "new_this_week": len([c for c in who if new_this_week(c, k, "themes")]),
                         "contact_ids": [c["id"] for c in who]})
    others = {}
    for c in people:
        if "other" in (c.get("themes") or []):
            others.setdefault(" ".join((c.get("theme_other") or "Other").split()).lower(), []).append(c)
    for _, who in sorted(others.items()):
        rows.append({"key": "other", "label": " ".join((who[0].get("theme_other") or "Other").split()), "group": "other",
                     "people": len(who), "new_this_week": len([c for c in who if new_this_week(c, "other", "themes")]),
                     "contact_ids": [c["id"] for c in who]})
    order = dict((k, i) for i, k in enumerate(THEME_KEYS))
    rows.sort(key=lambda r: (-r["people"], order[r["key"]], r["label"]))
    themes_tally = {"people_with_feedback": len(people), "rows": rows,
                    "people_with_no_theme": len([c for c in people if not c.get("themes")])}
    lrows = []
    for k, lab in LIKED:
        who = [c for c in people if k in (c.get("liked") or [])]
        if who:
            lrows.append({"key": k, "label": lab, "people": len(who), "contact_ids": [c["id"] for c in who]})
    lrows.sort(key=lambda r: (-r["people"], LIKED_KEYS.index(r["key"])))
    liked_tally = {"people_with_feedback": len(people), "people": len([c for c in people if c.get("liked")]), "rows": lrows}

    watch = []
    for c in counted:
        if c.get("status") in ("passed", "offer_submitted", "not_yet_contacted"):
            continue
        if c.get("offer_intent") in ("yes", "maybe") or c.get("status") == "writing_offer":
            f = facts[c["id"]]
            fresh = f["days_since_last_touch"] is not None and f["days_since_last_touch"] <= LIMITS["offer_lead_fresh_days"]
            watch.append({"contact_id": c["id"], "lead_state": "live" if fresh else "earlier_interest",
                          "last_touch_date": f["last_touch_date"], "days_since_last_touch": f["days_since_last_touch"]})
    watch.sort(key=lambda w: (w["lead_state"] != "live", -(parse_date(w["last_touch_date"]).toordinal() if w["last_touch_date"] else 0), w["contact_id"]))
    return {"totals": totals, "weeks": weeks, "pricing_tally": pricing, "themes_tally": themes_tally,
            "liked_tally": liked_tally, "price_periods": periods, "offer_watch": watch,
            "followup": dict((c["id"], dict((k, facts[c["id"]][k]) for k in FOLLOWUP_KEYS)) for c in contacts)}


def settle_contact(c, week_end_day, week_start_day=None, offer_ids=()):
    """Sets the fields of one contact that follow from its rows, in place: followup, price_reaction, price_asked,
    softened, themes and liked (when the feedback entries carry them), feedback_date, status, lists,
    primary_list, offer_word and (given the week start) active_this_week. A status of passed, writing_offer or
    offer_submitted is a tag and is kept; any other status is replaced by what the touches give (see
    base_status). offer_ids are the ids of the people with an offer on file."""
    we = iso(week_end_day)
    log = counted_feedback(c, we)
    c["followup"] = followup_block(c, we)
    if is_counted(c):
        c["price_reaction"], c["price_asked"] = derive_price_reaction(c, we), derive_price_asked(c, we)
        for field, order in (("themes", THEME_KEYS), ("liked", LIKED_KEYS)):
            if any(e.get(field) for e in log):
                got = set(k for e in log for k in e.get(field) or [])
                c[field] = [k for k in order if k in got]
    anylog = sorted((e for e in c.get("feedback_log") or [] if e["date"] <= we), key=lambda e: e["date"])
    c["softened"] = bool(c.get("feedback_softened")) or any(e.get("softened") for e in anylog)
    if anylog and not c.get("feedback_safe"):
        c["feedback_safe"] = anylog[-1]["text_safe"]
    if anylog and c.get("feedback_safe"):
        c["feedback_date"] = anylog[-1]["date"]
    if c.get("represented_by"):
        c["status"] = "through_agent"
    elif c.get("status") not in ("passed", "writing_offer", "offer_submitted"):
        c["status"] = base_status(c, we)
    c["lists"] = contact_lists(c)
    c["primary_list"] = c["lists"][0] if c["lists"] else None
    c["offer_word"] = derive_offer_word(c, offer_ids)
    if week_start_day is not None:
        c["active_this_week"] = active_in_week(c, week_start_day, we)
    return c


def finish_ledger(d):
    """Fills every derived block of a ledger from its rows, in place, and returns it.

    The builder writes listing, report, contacts, open_houses and offers, then calls this. It settles every
    contact (settle_contact), then sets weeks, totals, pricing_tally (keeping open_house_price_remarks), themes_tally,
    liked_tally, price_periods and offer_watch (keeping each lead's basis_safe and basis_date), and turns the
    counts report.tracking marks as not recorded into nulls. Week labels are kept, and so is a null already
    set on a nullable count for a week that could not be checked."""
    R = d["report"]
    offer_ids = set(o.get("contact_id") for o in d.get("offers") or [] if o.get("contact_id"))
    for c in d["contacts"]:
        settle_contact(c, R["week_end"], R["week_start"], offer_ids)
    d.setdefault("online", None)
    d.setdefault("nearby", None)
    want = recount(d)
    tr = R.get("tracking") or {}
    old_weeks = dict((w.get("n"), w) for w in d.get("weeks") or [])
    for w in want["weeks"]:
        old = old_weeks.get(w["n"]) or {}
        if old.get("label"):
            w["label"] = old["label"]
        for flag, keys in TRACKING_KEYS.items():
            for k in keys:
                if k in w and (not tr.get(flag) or (k in old and old[k] is None)):
                    w[k] = None
    for flag, keys in TRACKING_KEYS.items():
        for k in keys:
            if k in want["totals"] and not tr.get(flag):
                want["totals"][k] = None
    d["weeks"], d["totals"] = want["weeks"], want["totals"]
    remarks = (d.get("pricing_tally") or {}).get("open_house_price_remarks") or []
    d["pricing_tally"] = dict(want["pricing_tally"], open_house_price_remarks=remarks)
    d["themes_tally"], d["liked_tally"], d["price_periods"] = want["themes_tally"], want["liked_tally"], want["price_periods"]
    basis = dict((w.get("contact_id"), w) for w in d.get("offer_watch") or [])
    byid = dict((c["id"], c) for c in d["contacts"])
    for w in want["offer_watch"]:
        old, c = basis.get(w["contact_id"]) or {}, byid[w["contact_id"]]
        w["basis_safe"] = old.get("basis_safe") or c.get("offer_basis_safe")
        w["basis_date"] = old.get("basis_date") or c.get("offer_basis_date")
    d["offer_watch"] = want["offer_watch"]
    R["weeks_on_market"] = len(want["weeks"])
    R["days_on_market"] = days_on_market(d["listing"]["list_date"], R["report_date"])
    R["days_on_market_at_week_end"] = days_on_market(d["listing"]["list_date"], R["week_end"])
    return d
