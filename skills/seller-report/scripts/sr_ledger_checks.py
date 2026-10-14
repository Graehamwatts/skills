# -*- coding: utf-8 -*-
"""sr_ledger_checks: what build_ledger.py does around the people: machine events, the sources list, the
footing checks that stop a build, the build notes, the operator's short list, and the headline counts it prints.

    apply_events(events, contacts, P, we, through)   key-box and disclosure notices -> engagements
    sources_used(raw, events, extra)                 every source the operator handed over
    footing(ledger, raw, cur, P, ...)                a second count of the headline numbers; any mismatch is a hard stop
    data_quality(ledger, raw, cur, listing, P, ...)  plain build notes kept in the ledger (never printed to a seller)
    notes_for_operator(ledger, raw, listing, P, ...) at most five lines for the chat reply that hands over the draft
    headline(ledger)                                 the numbers an operator checks first

footing() counts from the contact rows with its own loops. It does not call sr_contract.recount, so a
slip in either place shows up as a disagreement instead of passing twice.
Standard library only. No real client data belongs in this file.
"""
import collections

import sr_contract as C

SOURCE_LABELS = {
    "activity_sheet_live": "Live activity sheet, exported to xlsx",
    "activity_sheet_file": "A saved copy of the activity sheet",
    "status_email": "The team's weekly status email",
    "glide_email": "Disclosure platform notices",
    "supra_email": "Key-box showing notices",
    "pasted_notes": "Notes pasted in by the operator",
    "forwarded_email": "Emails forwarded by the operator",
}
SINCE_TEXT = {"keybox_showing": "A key-box showing was logged.", "disclosure_opened": "Opened the disclosure package."}


def apply_events(events, contacts, P, we, through):
    """Machine events (events.json) become engagements. A key-box notice on a day that already has a tour
    reported by the agent upgrades that tour to a key-box showing: it is one visit, not two. A host opening
    the key box is team side and is not a showing."""
    byid = dict((c["id"], c) for c in contacts)
    for ev in sorted(events.get("events") or [], key=lambda e: e.get("date") or (e.get("occurred_at") or "")[:10]):
        day = ev.get("date") or (ev.get("occurred_at") or "")[:10]
        if ev.get("type") == "keybox_showing_end":
            continue
        if ev.get("is_team_side"):
            P.stats["events_team_side"] += 1
            continue
        c = byid.get(ev.get("contact_id"))
        if not day or day > through:
            P.stats["events_after_through"] += 1
            continue
        if c is None or c.get("team_side"):
            P.stats["events_unmatched"] += 1
            continue
        kind = "disclosure_opened" if ev.get("type") == "disclosure_opened" else "keybox_showing"
        if day > we:
            P.since.append({"date": day, "kind": "engagement", "contact_id": c["id"], "name_short": c["name_short"],
                            "summary_safe": SINCE_TEXT[kind], "offer_related": False})
            continue
        engs = c["engagements"]
        if kind == "keybox_showing":
            same = [e for e in engs if e["type"] in C.TOUR_TYPES and e.get("date") == day]
            if same:
                same[0].update(type="keybox_showing", date_quality="exact", confirmed=True)
            else:
                engs.append({"type": "keybox_showing", "date": day, "date_quality": "exact", "confirmed": True})
        elif not any(e["type"] == "disclosure_opened" for e in engs):
            engs.append({"type": "disclosure_opened", "date": day, "date_quality": "exact", "confirmed": True})
        engs.sort(key=lambda e: e.get("date") or "9999")
        P.stats["events_applied"] += 1
    if P.stats["events_unmatched"]:
        P.notes.append("%d machine event(s) could not be tied to a person and are in no count. Match them in events.json." % P.stats["events_unmatched"])


def sources_used(raw, events, extra=()):
    out, seen = [], set()

    def add(kind, label, as_of):
        if kind not in C.SOURCE_KINDS:
            raise SystemExit("unknown source kind %r (one of %s)" % (kind, ", ".join(C.SOURCE_KINDS)))
        if (kind, label) not in seen:
            seen.add((kind, label))
            out.append({"kind": kind, "label": label, "as_of": C.iso(as_of)})

    for s in raw.get("sources") or []:
        add(s["kind"], SOURCE_LABELS.get(s["kind"], "Activity sheet"), s.get("as_of") or raw.get("as_of"))
    for f in events.get("fetched") or []:
        add(f["source"], SOURCE_LABELS.get(f["source"], f["source"].replace("_", " ")), f.get("asked_on"))
    for text in extra or ():
        parts = [p.strip() for p in str(text).split("|")]
        if len(parts) != 3 or not parts[1]:
            raise SystemExit("--source needs KIND|LABEL|YYYY-MM-DD, got %r" % text)
        add(parts[0], parts[1], parts[2])
    return out


def headline(d):
    T, PT = d["totals"], d["pricing_tally"]
    out = collections.OrderedDict()
    for k in ("contact_records", "contacts", "buyers_via_agent", "team_side_people", "contacted", "not_yet_contacted",
              "replied", "awaiting_reply", "awaiting_reply_3plus_attempts", "touches_outbound", "outbound_person_days",
              "outbound_distinct_days", "replies_inbound", "calls_not_connected", "keybox_showings", "agent_reported_tours",
              "tours_unconfirmed", "inquiries", "disclosure_contacts", "disclosure_shared_buyers", "open_house_sessions",
              "open_house_sessions_without_count", "open_house_sessions_no_visitors", "open_house_groups", "offers",
              "people_with_feedback", "conversations_with_feedback"):
        out[k] = T.get(k)
    out["price_too_high / fair / not_raised"] = "%s / %s / %s" % (PT["too_high"], PT["fair_or_positive"], PT["not_raised"])
    out["themes"] = ", ".join("%s %d" % (r["key"], r["people"]) for r in d["themes_tally"]["rows"]) or "none"
    out["liked (people)"] = d["liked_tally"]["people"]
    out["offer_watch"] = ", ".join("%s %s" % (w["contact_id"], w["lead_state"]) for w in d["offer_watch"]) or "none"
    out["team_side_set_aside"] = "%(people)s people, %(touches_outbound)s follow-ups, %(replies_inbound)s reply days" % T["team_side_set_aside"]
    out["since_week_closed items"] = len(d["report"]["since_week_closed"]["items"])
    return out


# ---------------------------------------------------------------------------------------------
# footing: a second, independent count. Any disagreement stops the build.
# ---------------------------------------------------------------------------------------------
def footing(d, raw, cur, P, row_counts, deferred):
    out, T, W, R = [], d["totals"], d["weeks"], d["report"]
    we, first_day = R["week_end"], d["weeks"][0]["start"] if d["weeks"] else R["week_start"]
    contacts = d["contacts"]
    counted = [c for c in contacts if not c["team_side"] and not c["represented_by"]]
    nonteam = [c for c in contacts if not c["team_side"]]

    def same(what, got, want):
        if got != want:
            out.append("does not foot: %s (%s against %s)" % (what, got, want))

    same("contact records = counted people + team side + buyers reached through an agent", len(contacts),
         len(counted) + len([c for c in contacts if c["team_side"]]) + len([c for c in contacts if c["represented_by"]]))
    same("totals.contacts", T["contacts"], len(counted))
    same("contacts = contacted + not yet contacted", T["contacts"], T["contacted"] + T["not_yet_contacted"])
    same("contacted = answered + still waiting", T["contacted"], T["replied"] + T["awaiting_reply"])
    same("people by status add up to contacts", sum(T["by_status"].values()), T["contacts"])
    same("people by interest add up to contacts", sum(T["by_interest"].values()), T["contacts"])
    same("answered = people whose status is replied, passed, writing an offer or offer in", T["replied"],
         len([c for c in counted if c["status"] in C.ANSWERED_STATUSES]))

    outs = [(c["id"], t["date"]) for c in counted for t in c["touches"] if t["direction"] == "outbound"]
    reps = set((c["id"], t["date"]) for c in counted for t in c["touches"] if t["direction"] == "inbound" or t["outcome"] == "reached")
    conv = [(c["id"], f["date"]) for c in counted for f in c["feedback_log"] if f["counts_as_conversation"]]
    tours = [e for c in nonteam for e in c["engagements"] if e["type"] == "agent_reported_tour"]
    kbs = [e for c in nonteam for e in c["engagements"] if e["type"] == "keybox_showing"]
    inqs = [e for c in nonteam for e in c["engagements"] if e["type"] == "inquiry"]
    series = {
        "touches_outbound": [day for _, day in outs], "replies_inbound": [day for _, day in reps],
        "conversations_with_feedback": [day for _, day in conv],
        "agent_reported_tours": [e.get("date") for e in tours], "inquiries": [e.get("date") for e in inqs],
        "offers": [o["date"] for o in d["offers"]], "open_house_sessions": [o["date"] for o in d["open_houses"]],
    }
    if T.get("keybox_showings") is not None:
        series["keybox_showings"] = [e.get("date") for e in kbs]
    for key, days in sorted(series.items()):
        same("totals.%s" % key, T[key], len(days))
        dated = [x for x in days if x]
        if all(w.get(key) is not None for w in W):          # a week nobody could check is null and cannot be summed
            same("weeks add up to the total for %s (entries before the list week and undated ones set aside)" % key,
                 sum(w[key] for w in W), len([x for x in dated if x >= first_day]))
        same("the record at each list price adds up for %s" % key, sum(p[key] for p in d["price_periods"]), len(dated))
    same("follow-ups by channel add up", sum(T["outbound_by_channel"].values()), T["touches_outbound"])
    same("each person's follow-ups add up to the total", sum(c["followup"]["outbound_touches"] for c in counted), T["touches_outbound"])
    same("each person's reply days add up to the total", sum(c["followup"]["replies"] for c in counted), T["replies_inbound"])
    same("separate days", T["outbound_distinct_days"], len(set(day for _, day in outs)))
    same("person days", T["outbound_person_days"], len(set(outs)))
    if not (T["outbound_distinct_days"] <= T["outbound_person_days"] <= T["touches_outbound"]):
        out.append("does not foot: separate days <= person days <= follow-ups (%s, %s, %s)"
                   % (T["outbound_distinct_days"], T["outbound_person_days"], T["touches_outbound"]))
    pre_list = len(set(day for _, day in outs if day < d["listing"]["list_date"]))
    if T["outbound_distinct_days"] - pre_list > R["days_on_market_at_week_end"] + 1:
        out.append("does not foot: %d separate follow-up days in %d days on the market" % (T["outbound_distinct_days"], R["days_on_market_at_week_end"] + 1))
    for w in W:
        if w["outbound_distinct_days"] > 7:
            out.append("does not foot: week %d has %d separate follow-up days" % (w["n"], w["outbound_distinct_days"]))
    for k in ("awaiting_reply_3plus_attempts", "awaiting_reply_answered_before", "awaiting_reply_quiet"):
        if T[k] > T["awaiting_reply"]:
            out.append("does not foot: %s (%s) is more than the people still waiting (%s)" % (k, T[k], T["awaiting_reply"]))

    people = [c for c in counted if any(f["counts_as_conversation"] for f in c["feedback_log"])]
    PT = d["pricing_tally"]
    same("people who gave feedback", PT["people_with_feedback"], len(people))
    same("the three price rows add up to the people who gave feedback", PT["too_high"] + PT["fair_or_positive"] + PT["not_raised"], len(people))
    same("people with no theme", d["themes_tally"]["people_with_no_theme"], len([c for c in people if not c["themes"]]))
    for r in d["themes_tally"]["rows"] + d["liked_tally"]["rows"]:
        if r["people"] > len(people):
            out.append("does not foot: %s is counted for %d people out of %d" % (r["key"], r["people"], len(people)))
    with_count = [o["groups"] for o in d["open_houses"] if o["groups"] is not None]
    same("open house sessions = with a count + without", T["open_house_sessions"], len(with_count) + T["open_house_sessions_without_count"])
    same("open house sessions with no visitors", T["open_house_sessions_no_visitors"], len([g for g in with_count if g == 0]))
    same("open house traffic", T["open_house_groups"], sum(with_count) if with_count else None)

    # no note left behind: every note on a person's row was read, and every one read is in exactly one bucket
    kinds = dict((r["key"], t["kind"]) for t in raw.get("tabs") or [] for r in t["rows"])
    people = cur.get("people") or {}
    hosts = set(cid for cid, p in people.items() if p.get("is_open_house_host"))
    missing_agents = set(p.get("represented_by") for p in people.values() if p.get("represented_by") and p["represented_by"] not in people)
    unread = []
    for t in raw.get("tabs") or []:
        for r in t["rows"]:
            holder = P.held.get(r["key"])
            if holder and (kinds[r["key"]] != "open_house" or holder in hosts) and not (people.get(holder) or {}).get("represented_by") in missing_agents:
                unread += [e["key"] for e in r["entries"] if e["key"] not in P.used_entries]
    if unread:
        out.append("does not foot: %d note(s) on a person's rows were never read (first: %s)" % (len(unread), unread[0]))
    S = P.stats
    same("notes read = by rule + from the wording + undated + later than this issue", len(P.used_entries),
         S["entries_by_rule"] + S["entries_curated"] + S["entries_undated_no_event"] + S["entries_after_through"])
    same("sheet rows = people + ignored + open house + offers + unrecognised tabs + waiting",
         sum(len(t["rows"]) for t in raw.get("tabs") or []), sum(row_counts.values()))
    return out


# ---------------------------------------------------------------------------------------------
# plain build notes (ledger.data_quality): never printed to a seller
# ---------------------------------------------------------------------------------------------
def data_quality(d, raw, cur, listing, P, row_counts, deferred):
    S, T, R = P.stats, d["totals"], d["report"]
    we, through = R["week_end"], R["since_week_closed"]["through"]
    out = []

    def add(text, *args):
        out.append((text % args if args else text).replace("..", "."))

    def names(items):
        return C.join_and(items).rstrip(".")

    add("The activity sheet was read as exported on %s. This issue counts entries dated on or before %s.",
        C.fmt_date(raw.get("as_of") or we, year=True), C.fmt_date(we, year=True))
    if S["entries_after_week_end"] or R["since_week_closed"]["items"]:
        n_since = len(R["since_week_closed"]["items"])
        add("%d later entr%s shown as logged since the week closed (through %s) and in no count.",
            n_since, "y is" if n_since == 1 else "ies are", C.fmt_date(through))
    waiting = S["entries_after_through"] + S["last_touch_cells_after_through"] + S["open_house_sessions_after_through"]
    if waiting or deferred:
        add("%d dated entr%s after %s and %d sheet row(s) that first appear after it are left for the next issue.",
            waiting, "y" if waiting == 1 else "ies", C.fmt_date(through), len(deferred))
    add("Dates typed without a year were placed by the listing's life (listed %s), never by today's year.", C.fmt_date(listing["list_date"], year=True))
    tr = R["tracking"]
    if not tr["keybox_showings"]:
        add("This listing has no key-box record to read, so the key-box count stays empty, never zero, and every tour is one reported to our team.")
    if not tr["disclosure_sent"] or not tr["disclosure_opened"]:
        add("The disclosure tab lists people, not events. %s not recorded for this listing, so people on the list are dated by their first dated note and marked approximate.",
            "Link sent and package opened are" if not (tr["disclosure_sent"] or tr["disclosure_opened"]) else
            ("Link sent is" if not tr["disclosure_sent"] else "Package opened is"))
    add("%d note(s) were classified by rule (stock phrases such as no answer, left a voicemail, sent a text and email). %d were read from the wording.",
        S["entries_by_rule"], S["entries_curated"])
    if S["touches_from_columns_only"] or S["reply_channel_from_column"]:
        add("The Email, Call and Text columns keep only the latest date for each channel. %d follow-up(s) come from those columns alone, with no note, and %d repl%s took the phone channel from them.",
            S["touches_from_columns_only"], S["reply_channel_from_column"], "y" if S["reply_channel_from_column"] == 1 else "ies")
    if S["buyer_rows_read_into_agent_log"]:
        add("%d row(s) of a buyer an agent brought carry their own notes or contact dates. Those are read into the agent's follow-up log, because follow-up with that buyer is follow-up with the agent.", S["buyer_rows_read_into_agent_log"])
    if S["touches_deduped"]:
        add("%d follow-up(s) typed twice (on two tabs, or as a call and a voicemail on one day) are counted once.", S["touches_deduped"])
    if T["touches_direction_not_recorded"]:
        add("%d contact(s) are logged without saying who called whom. They are not counted as follow-up.", T["touches_direction_not_recorded"])
    approx = [c["name_short"] for c in d["contacts"] for e in c["engagements"] if e["type"] in C.TOUR_TYPES and e.get("date_quality") == "approximate"]
    if approx:
        add("%d tour date(s) come from a note instead of the date cell and are marked approximate: %s.", len(approx), names(approx))
    unconfirmed = [c["name_short"] for c in d["contacts"] for e in c["engagements"] if e["type"] in C.TOUR_TYPES and e.get("confirmed") is False]
    if unconfirmed:
        add("%d tour(s) are on the log with nothing to confirm they took place: %s.", len(unconfirmed), names(unconfirmed))
    if P.auto_inquiries:
        add("%d row(s) on the showing tab have no showing date. Each is read as an inquiry until someone confirms a tour: %s.",
            len(P.auto_inquiries), names(sorted(set(P.auto_inquiries))))
    if T["open_house_sessions_without_count"]:
        add("Open house sessions with no visitor count on record: %d of %d.", T["open_house_sessions_without_count"], T["open_house_sessions"])
    if S["open_house_sessions_waiting_for_a_date"] or S["open_house_sessions_ignored"]:
        add("%d open house session(s) with no date typed are known to fall after this week and wait for a date. %d are set aside in curation.",
            S["open_house_sessions_waiting_for_a_date"], S["open_house_sessions_ignored"])
    if row_counts.get("ignored"):
        add("%d sheet row(s) are set aside in curation as not a buyer-side contact (each with its reason).", row_counts["ignored"])
    if row_counts.get("other"):
        add("%d row(s) sit on tabs the parser does not recognise and are in no count.", row_counts["other"])
    if S["rows_stale"]:
        add("%d row(s) named in curation are no longer in the sheet. Their notes are not in this issue.", S["rows_stale"])
    if S["people_first_seen_after_week_end"]:
        add("%d person record(s) first appear after the week closed and are not in this issue's counts.", S["people_first_seen_after_week_end"])
    if S["same_day_feedback_merged"]:
        add("%d pair(s) of feedback lines logged on one day were joined: a conversation is one person on one day.", S["same_day_feedback_merged"])
    if S["corrections_replaced_by_newer_sheet_value"]:
        add("%d earlier correction(s) gave way to a newer value typed in the sheet's own columns.", S["corrections_replaced_by_newer_sheet_value"])
    if S["sheet_tag_conflicts"]:
        add("%d value(s) in the sheet's own columns differ between two rows of the same person. The row with the latest note was used.", S["sheet_tag_conflicts"])
    if S["comments_rebuilt_as_of_week_end"]:
        add("%d comment(s) quoted an entry made after the week closed and were rebuilt from the entries inside the week.", S["comments_rebuilt_as_of_week_end"])
    softened = [c["name_short"] for c in d["contacts"] if c["softened"]]
    if softened:
        add("%d comment(s) were softened in the paraphrase, with the substance kept: %s.", len(softened), names(softened))
    by_sheet = len([cid for cid, src in P.provenance.items() if "sheet_column" in src.values()])
    if by_sheet:
        add("%d people carry at least one value taken from the sheet's own columns.", by_sheet)
    fixed = len([cid for cid, src in P.provenance.items() if "corrected_by_operator" in src.values()])
    if fixed:
        add("%d people carry at least one value the operator corrected. Those are kept as corrected.", fixed)
    if raw.get("warnings"):
        add("The sheet parser raised %d warning(s). They are listed in the private parse file.", len(raw["warnings"]))
    add("Who made each follow-up and the time of day are not recorded in the sheet.")
    out.extend(P.notes)
    out.extend(s for s in listing.get("operator_notes") or [] if isinstance(s, str) and s.strip())
    return out


# ---------------------------------------------------------------------------------------------
# what the operator should glance at: for the chat reply that hands over the Gmail draft, never for the report
# ---------------------------------------------------------------------------------------------
GLANCE_LIMIT = 5


def notes_for_operator(d, raw, listing, P, extra=(), optional=None):
    """The small file written beside the ledger. worth_a_glance holds at most five short plain lines, most
    important first, for the chat reply ("Worth a glance before you send"). also_noted keeps the rest for
    Claude. Nothing here is printed in a report and nothing here stops a build."""
    R, T = d["report"], d["totals"]
    ws, we = R["week_start"], R["week_end"]
    ranked = []

    def add(rank, text, *args):
        s = (text % args if args else text).replace("..", ".").strip()
        if s and s not in [x[2] for x in ranked]:
            ranked.append((rank, len(ranked), s))

    def names(items, limit=4):
        items = sorted(set(items))
        return C.join_and(items[:limit] + (["%d more" % (len(items) - limit)] if len(items) > limit else [])).rstrip(".")

    def in_week(day):
        return bool(day) and ws <= day <= we

    as_of = raw.get("as_of") or we
    if as_of < we:
        add(0, "The activity sheet was exported on %s, before the week ended on %s, so the last days of the week may be missing.",
            C.fmt_date(as_of), C.fmt_date(we))
    for s in extra or []:                                   # what Claude noticed across sources for this issue
        add(1, s)
    for s in (optional or {}).get("glance") or []:          # about an optional section: a count that went down, a heavy photo
        add(5, s)
    for s in (optional or {}).get("also") or []:
        add(8, s)
    for who, s in P.unsure:                                 # what Claude was unsure of while reading a note
        add(1, s if (who or "") in s else "%s: %s" % (who, s))
    week_tours = [(c, e) for c in d["contacts"] for e in c["engagements"] if e["type"] in C.TOUR_TYPES and in_week(e.get("date"))]
    unconfirmed = [c["name_short"] for c, e in week_tours if e.get("confirmed") is False]
    if unconfirmed:
        add(2, "Could not tell from the notes whether %s took place: %s. %s counted as a tour.",
            "this tour" if len(unconfirmed) == 1 else "these tours", names(unconfirmed), "It is" if len(unconfirmed) == 1 else "They are")
    guessed = set(P.auto_inquiries)
    guessed_week = [c["name_short"] for c in d["contacts"] if c["name_short"] in guessed
                    and any(e["type"] == "inquiry" and in_week(e.get("date")) for e in c["engagements"])]
    if guessed_week:
        add(2, "%s on the showing tab with no showing date, so %s counted as an inquiry, not a tour: %s.",
            "1 person is" if len(guessed_week) == 1 else "%d people are" % len(guessed_week),
            "that is" if len(guessed_week) == 1 else "each is", names(guessed_week))
    toned = [c["name_short"] for c in d["contacts"] for f in c["feedback_log"] if f.get("softened") and in_week(f.get("date"))]
    if toned:
        add(3, "The wording of %s was toned down, with the substance kept: %s.",
            "1 comment this week" if len(set(toned)) == 1 else "%d comments this week" % len(set(toned)), names(toned))
    approx = [c["name_short"] for c, e in week_tours if e.get("date_quality") == "approximate"]
    if approx:
        add(4, "%s this week %s dated from a note, not the date cell, so the report gives the date as approximate: %s.",
            "1 tour" if len(approx) == 1 else "%d tours" % len(approx), "is" if len(approx) == 1 else "are", names(approx))
    bare = [o for o in d["open_houses"] if in_week(o["date"]) and o.get("groups") is None]
    if bare:
        add(4, "%s this week %s no visitor count on the sheet, so the report says no count was kept.",
            "1 open house" if len(bare) == 1 else "%d open houses" % len(bare), "has" if len(bare) == 1 else "have")
    S = P.stats
    if S["open_house_sessions_waiting_for_a_date"]:
        n = S["open_house_sessions_waiting_for_a_date"]
        add(4, "%s on the sheet with no date typed. %s not in this report until the date is added.",
            "1 open house session is" if n == 1 else "%d open house sessions are" % n, "It is" if n == 1 else "They are")
    if S["corrections_replaced_by_newer_sheet_value"]:
        add(3, "%d of your earlier corrections gave way to a newer value typed in the sheet's own columns.", S["corrections_replaced_by_newer_sheet_value"])
    if S["sheet_tag_conflicts"]:
        add(5, "The sheet's own columns disagree between two rows of the same person in %d place(s). The row with the latest note was used.", S["sheet_tag_conflicts"])
    if T["touches_direction_not_recorded"]:
        n = T["touches_direction_not_recorded"]
        add(5, "%s logged without saying who called whom, so %s not counted as follow-up.",
            "1 contact is" if n == 1 else "%d contacts are" % n, "it is" if n == 1 else "they are")
    for s in P.notes:
        add(6, s)
    for s in listing.get("operator_notes") or []:
        if isinstance(s, str) and s.strip():
            add(6, s)
    if raw.get("warnings"):
        add(7, "The sheet parser raised %d warning(s). They are listed in the private parse file.", len(raw["warnings"]))
    ranked.sort()
    # A lookup that was blocked or failed is always said: its line keeps a place at the end of the five (two at
    # most; a third waits in also_noted), because the section it would have filled is missing from the report.
    skipped = [C.strip_dashes(s) for s in (optional or {}).get("skipped") or []]
    kept = skipped[:2]
    top = [C.strip_dashes(s) for rank, _, s in ranked if rank < 7][:GLANCE_LIMIT - len(kept)] + kept     # rank 7 and up is for Claude only
    lines = [C.strip_dashes(s) for _, _, s in ranked] + skipped
    return {"schema_version": C.SCHEMA_VERSION, "slug": d["meta"]["slug"], "issue_number": R["issue_number"],
            "report_date": R["report_date"], "week_start": ws, "week_end": we,
            "how_to_use": "worth_a_glance goes in the chat reply that hands over the Gmail draft, under the words "
                          "'Worth a glance before you send'. At most five lines. Never put any of this in the report.",
            "worth_a_glance": top, "also_noted": [s for s in lines if s not in top]}
