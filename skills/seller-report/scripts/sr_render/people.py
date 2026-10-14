# -*- coding: utf-8 -*-
"""sr_render.people: one person on the page.

Every person sits in the lists under "The details" in one of three forms:

    entry_full      this week's people, and everyone in the link copy and the PDF: who they are, what they did
                    and when, what they said, where an offer stands, every follow-up date with its channel,
                    and whether they responded
    entry_line      earlier people in the email: one line with the name, what they did, where it stands and
                    the last contact
    entry_pointer   a person shown in full under an earlier list: the name and where to find them

The link copy adds the day by day log under each full entry. Plain text is what we did. Green is only ever
their answer. A message they started is labelled as theirs.
"""
import re

import sr_contract as C
from .text import *        # noqa: F401,F403


def entry_mark(m, x, form):
    """The hook the ship gate counts: data-sr-entry="<full|line|pointer>:<contact id>". A person the link copy
    must not name carries the form alone."""
    return mark("entry", "%s:%s" % (form, "" if x["id"] in m.masked else x["id"]))


def touch_note(t):
    s = (t.get("summary_safe") or "").strip()
    for rx in ASIDES:
        s = rx.sub("", s).strip()
    return None if (not s or BOILER.match(s)) else s


def touch_verb(t):
    ch, oc = t.get("channel"), t.get("outcome")
    if ch == "voicemail" or oc == "left_voicemail":
        return "left a voicemail"
    if ch == "call":
        if oc == "did_not_connect":
            return "called (the call did not go through)"
        return "called (no answer)" if oc == "no_answer" else "called"
    return {"text": "texted", "email": "emailed", "in_person": "met in person"}.get(ch, "reached out")


def touch_word(t):
    """One word for a follow-up in the compact line: 'Sept 20 call, text'."""
    ch, oc = t.get("channel"), t.get("outcome")
    if ch == "voicemail" or oc == "left_voicemail":
        return "voicemail"
    if ch == "call":
        return "call (did not go through)" if oc == "did_not_connect" else "call"
    return {"text": "text", "email": "email", "in_person": "visit"}.get(ch, "follow-up")


def channel_counts(touches):
    """'4 calls, 1 text, 8 emails', or '6 follow-ups' when the log does not give the channel for all."""
    return ", ".join(C.channel_parts(touches))


def dedupe(note, shown_sents):
    """Drops the sentences of a note that the comment block above already prints."""
    if not note or not shown_sents:
        return note
    keep_ = []
    for snt in sentences(note):
        k = norm(snt)
        if any(k == x or (len(x) > 15 and x in k) or (len(k) > 15 and k in x) for x in shown_sents):
            continue
        keep_.append(snt)
    return " ".join(keep_) or None


REPLY_LEAD = re.compile(r"^((the agent|he|she|they)\s+)?(wrote back|answered|replied|called back|texted back|emailed back)\.\s*", re.I)
REACHED_LEAD = re.compile(r"^(reached|spoke (with|to)|talked (with|to)|got through to|connected with)\b", re.I)
TIMES = {2: "twice", 3: "three times", 4: "four times"}


def day_rows(m, x, shown_comment=""):
    """Returns [dict(date, html, week, n_out, n_rep)] with one entry per day."""
    days, order = {}, []
    for t in x["_t"]:
        k = t["date"]
        if k not in days:
            days[k] = []
            order.append(k)
        days[k].append(t)
    shown = [norm(z) for z in sentences(shown_comment)]
    masked = x["id"] in m.masked
    ink = '<b style="color:%s">%%s</b>' % P["ink"]
    rows, had_out = [], False
    for k in sorted(order):
        ts, d = days[k], pd(k)
        outs = [t for t in ts if C.is_followup(t)]
        verbs, ours, theirs, n_rep = [], [], [], 0
        for t in ts:
            note, dr, ch = touch_note(t), t.get("direction"), t.get("channel")
            if masked:
                note = None
            if dr == "outbound" and not C.is_reply(t):          # a follow-up with no answer that day
                if note:
                    ours.append(safe(m, note, x))
                else:
                    v = touch_verb(t)
                    if v not in verbs:
                        verbs.append(v)
            elif dr == "outbound":                              # a call of ours that reached them
                n_rep += 1
                f1 = first_sentence(note or "")
                more = (note or "")[len(f1):].strip()
                if f1 and REACHED_LEAD.match(f1) and len(f1.split()) <= 5:
                    f1 = ""                                     # "Reached her by phone." is the green label below
                rest = dedupe(more, shown) if more else None
                if f1:
                    ours.append(safe(m, f1, x))
                else:
                    v = touch_verb(t)
                    if v not in verbs:
                        verbs.append(v)
                lab = "Reached them by phone." if ch == "call" else "They answered."
                if more and not rest:
                    lab = lab[:-1] + ", as reported above."
                theirs.append([lab, safe(m, rest, x) if rest else "", True])
            elif dr == "inbound":                               # they answered, or they got in touch first
                n_rep += 1
                if note:
                    note = REPLY_LEAD.sub("", note).strip() or None
                had_note = bool(note)
                note = dedupe(note, shown)
                if had_note and not note:
                    theirs.append(["Replied, as reported above." if (had_out or outs) else "Contacted us, as reported above.", "", True])
                    continue
                mt = re.match(r"(?i)(replied by \w+|replied)\b(\.?)\s*", note or "")
                if mt:
                    rest = note[mt.end():]
                    theirs.append([cap1(mt.group(1)) + ("." if (mt.group(2) or not rest) else ""), safe(m, rest, x) if rest else "", True])
                    continue
                by = {"text": " by text", "email": " by email", "call": " by phone"}.get(ch, "")
                lab = ("Replied" + by + ".") if (had_out or outs) else {
                    "call": "They called.", "email": "They emailed.", "text": "They texted."}.get(ch, "They contacted us.")
                theirs.append([lab, safe(m, note, x) if note else "", True])
            else:                                               # the log does not say who started it
                kept = dedupe(note, shown) if note else None
                ours.append(safe(m, kept, x) if kept else ("Spoke with them, as reported above." if note else "Spoke with them."))
        if outs:
            had_out = True
        n_rep = min(n_rep, 1)       # one reply per person per day
        # two bare replies on one day read "Replied twice."
        merged = []
        for lab, rest, is_green in theirs:
            same = next((e for e in merged if e[0] == lab and not e[1] and not rest), None)
            if same:
                same[3] += 1
            else:
                merged.append([lab, rest, is_green, 1])
        lines = []
        for lab, rest, is_green, k_ in merged:
            if k_ > 1:
                lab = "%s %s." % (lab[:-1], TIMES.get(k_, "%d times" % k_))
            lines.append((green(lab) if is_green else (ink % lab)) + ((" " + rest) if rest else ""))
        outb = ([cap1(join_and(verbs)) + "."] if verbs else []) + [o for o in ours if o]
        html = " ".join(outb) + ("<br>" if (outb and lines) else "") + "<br>".join(lines)
        rows.append(dict(date=d, html=html or "Contact logged.", week=(m.WS <= d <= m.WE), n_out=len(outs), n_rep=n_rep))
    return rows


def follow_line(m, x, dates=False):
    """What we did for this person, in days first: '6 days of follow-up (6 calls, 6 texts).'
    dates=True lists the days, which is the proof on rows that do not print each day."""
    od, out = x["_out_days"], x["_out"]
    if not od:
        return ""
    if x["_via_host"]:
        t = out[-1]
        return "Package sent through the open house host %s%s. Nobody on our team has reached this visitor directly." % (
            "about " if t.get("date_quality") == "approximate" else "on ", md(t["date"]))
    if x.get("phone_out_of_service"):
        dead = [t for t in out if t.get("channel") in ("call", "voicemail", "text")]
        live = [t for t in out if t not in dead]
        if live and dead:
            ld = sorted(set(pd(t["date"]) for t in live))
            return "%s on %s%s. %s went to a number that is out of service." % (
                cap1(join_and(C.channel_parts(live))), n_(len(ld), "day"), (" (%s)" % dates_compact(ld)) if dates else "",
                cap1(join_and(C.channel_parts(dead))))
        if dead:
            return "%s of follow-up%s: %s, to a number that is out of service." % (
                n_(len(od), "day"), (" (%s)" % dates_compact(od)) if dates else "", channel_counts(out))
    if dates:
        s = "%s of follow-up (%s): %s." % (n_(len(od), "day"), dates_compact(od), channel_counts(out))
    else:
        s = "%s of follow-up (%s)." % (n_(len(od), "day"), channel_counts(out))
    dead = x["followup"].get("calls_not_connected") or 0
    if dead and not x.get("phone_out_of_service"):
        s += " %s did not go through." % cap1(n_(dead, "call"))
    return s


def timeline(m, x, shown_comment=""):
    """The day by day log (link copy): one row per day of contact, with the note kept for that day."""
    out = []
    for r in day_rows(m, x, shown_comment):
        first = not out
        out.append("<tr>%s%s</tr>" % (
            c(md(r["date"]), "card", w=62, pad="6px 8px 6px 0", line=not first, th=True, scope="row", va="top",
              st="font-size:14px;font-weight:%d" % (700 if r["week"] else 400)),
            c(r["html"], "card", pad="6px 0", line=not first, va="top")))
    return table("".join(out), SIZE["small"], data=True)


# ---------------------------------------------------------------------------------------------
# the parts of an entry
# ---------------------------------------------------------------------------------------------
def who(m, x):
    """(name, role and brokerage) as two pieces of text."""
    name = dname(m, x)
    r = role(m, x)
    return name, ("" if name.lower().startswith(r.lower()) else r)


LIST_PHRASES = {"showings": ("Toured", "On the showing list"),
                "disclosure": ("On the disclosure", "Disclosure package", "Opened the disclosure", "Got the disclosure"),
                "open_house": ("Came to the open house",), "other_inquiries": ("Asked about",)}


def did_words(m, x, key=None, only=False):
    """What the person did and when, as short phrases. With a list key, the phrases that put them in that list
    come first; only=True keeps just those (what else they did is their pointer in the other list)."""
    bits = engaged(m, x)
    if key:
        first = LIST_PHRASES[key]
        mine = [b for b in bits if b.startswith(first)]
        bits = (mine or bits[:1]) if only else mine + [b for b in bits if not b.startswith(first)]
    return bits


def follow_days(m, x, limit=None):
    """'Sept 20 call · Sept 22 text · Oct 5 voicemail, text': every day we followed up, with the channel. Days in
    the report week are bold. Past the limit, the oldest days fold into a count with their first and last date."""
    days = {}
    for t in x["_out"]:
        days.setdefault(t["date"], []).append(t)
    keys = sorted(days)
    old = []
    if limit and len(keys) > limit + 1:
        old, keys = keys[:len(keys) - limit], keys[len(keys) - limit:]
    parts = []
    for k in keys:
        words = []
        for t in days[k]:
            w = touch_word(t)
            if w not in words and w != "follow-up":          # a day with no channel on record is just its date
                words.append(w)
        d = pd(k)
        s = ("%s%s %s" % ("about " if any(t.get("date_quality") == "approximate" for t in days[k]) else "", md(d), ", ".join(words))).strip()
        parts.append(('<b style="color:%s">%s</b>' % (P["ink"], s)) if m.WS <= d <= m.WE else s)
    lead = ""
    if old:
        lead = "%s from %s to %s, then " % (n_(len(old), "earlier day"), md(old[0]), md(old[-1]))
    return lead + DOT.join(parts)


def follow_value(m, x, limit=None):
    """After "Follow-up:": days first and touches second, then each date with its channel.
    '3 days (2 calls, 1 text): Sept 20 call · Sept 22 text · Oct 5 call.'"""
    od, out = x["_out_days"], x["_out"]
    if not od:
        if x["_n_rep"]:
            return "None needed. They contacted us." if x["status"] == "passed" else "None needed so far. They contacted us."
        return "None logged yet."
    if x["_via_host"]:
        return follow_line(m, x)
    days = follow_days(m, x, limit)
    if x.get("phone_out_of_service"):
        s = follow_line(m, x) + " " + days + "."
    else:
        s = "%s (%s): %s." % (n_(len(od), "day"), channel_counts(out), days)
        dead = x["followup"].get("calls_not_connected") or 0
        if dead and "did not go through" not in days:           # the day itself says so unless it was folded away
            s += " %s did not go through." % cap1(n_(dead, "call"))
    if x.get("next_followup_date"):
        s += " Next: %s." % md(x["next_followup_date"])
    return s


def responded_value(m, x):
    """'Yes, Oct 7', or 'No reply yet after 3 tries'. A try is a separate day we followed up since their last answer."""
    st, last_in, tries = x["status"], x["_last_in"], x["_tries"]
    if x["_via"]:
        through = m.byid.get(x.get("represented_by")) or {}
        return "We follow up through the open house host" if through.get("is_open_house_host") else "We follow up through their agent"
    if x["_via_host"]:
        return "Reached only through the open house host so far"
    later = m.after_answer.get(x["id"])          # they answered after the week closed: the box at the top has it
    if st == "not_yet_contacted":
        if later:
            return "Not reached by %s. Answered %s, see the top of this report." % (m.week_end_words(), md(later))
        if m.after_tried.get(x["id"]):
            return "Not reached by %s. First tried %s, see the top of this report." % (m.week_end_words(), md(m.after_tried[x["id"]]))
        return "Not yet reached"
    if st == "awaiting_reply":
        if later:
            return "%sNo reply by %s. Answered %s%s, see the top of this report." % (
                ("Answered %s. " % md(last_in)) if last_in else "", m.week_end_words(), "again " if last_in else "", md(later))
        if last_in and tries:
            return "Answered %s. No reply to %s since." % (md(last_in), n_(tries, "try", "tries"))
        if last_in:
            return "Answered %s. Nothing since." % md(last_in)
        return ("No reply yet after %s" % n_(tries, "try", "tries")) if tries else "No reply yet"
    more = (". More on %s, see the top of this report." % md(later)) if later else ""
    if not last_in:
        return "Yes" + more
    s = green("Yes") + ", %s" % md(last_in)
    if x["_n_rep"] > 1:
        s += " (%s in all)" % n_(x["_n_rep"], "reply", "replies")
    return s + more


def offer_value(m, x):
    """The Offer row, email only: writing one, possibly, not yet, no, or not discussed."""
    w = x.get("offer_word") or "not_discussed"
    if w == "offer_received":
        o = next((o for o in m.offers if o.get("contact_id") == x["id"]), None)
        s = ("Offer received %s" % md(o["date"])) if o else OFFER_WORD[w]
        if o and o.get("state") and o["state"] != "received":
            s += ". %s." % OFFER_STATE.get(o["state"], cap1(o["state"]))
        elif x["status"] == "passed":
            s += ". Has since passed."
        return s
    # a note about an offer logged after the week closed is in the box at the top: this row points there
    later = m.after_offer.get(x["id"])
    more = (". See the %s note at the top of this report." % md(later)) if later else ""
    if w in ("writing_one", "possibly"):
        lead = x.get("_lead") or {}
        when = lead.get("basis_date") or x.get("offer_basis_date")
        s = OFFER_WORD[w]
        if lead.get("lead_state") == "earlier_interest":
            return s + (", as of %s. No word since." % md(when) if when else ". No word in the last %d days." % LIMITS["lead_fresh_days"])
        return s + ((", as of %s" % md(when)) if when else "") + more
    if later:
        return "%s by %s%s" % (OFFER_WORD[w], m.week_end_words(), more)
    return OFFER_WORD[w]


def stands_words(m, x):
    """Where it stands, in a few words, for the one-line entry."""
    st, last_in, tries = x["status"], x["_last_in"], x["_tries"]
    if x["_via"]:
        through = m.byid.get(x.get("represented_by")) or {}
        return "Followed through the open house host" if through.get("is_open_house_host") else "Followed through their agent"
    if x["_via_host"]:
        return "Reached only through the open house host"
    later = m.after_answer.get(x["id"])
    if later and st in ("not_yet_contacted", "awaiting_reply"):
        return "%s by %s. Answered %s, see the top of this report" % (
            "Not reached" if st == "not_yet_contacted" else "No reply", m.week_end_words(), md(later))
    if st == "not_yet_contacted":
        if m.after_tried.get(x["id"]):
            return "Not reached by %s. First tried %s, see the top of this report" % (m.week_end_words(), md(m.after_tried[x["id"]]))
        return "Not yet reached"
    if st == "awaiting_reply":
        if last_in:
            return "No reply since %s%s" % (md(last_in), (" (%s)" % n_(tries, "try", "tries")) if tries else "")
        return ("No reply yet after %s" % n_(tries, "try", "tries")) if tries else "No reply yet"
    if st == "passed":
        return "Passed"
    if not m.link:
        if st == "offer_submitted":
            return "Wrote an offer"
        if st == "writing_offer" or x.get("offer_word") == "writing_one":
            return "Writing an offer"
        if x.get("offer_word") == "possibly":
            return "Answered, an offer is possible"
    return {"warm": "Answered, interested", "hot": "Answered, interested", "cold": "Answered, undecided"}.get(x.get("interest"), "Answered")


def said_text(m, x, week):
    """(comment, date) a full entry prints: this week's words for someone active this week, else the comment on file."""
    if x["id"] in m.masked:
        return "", None
    if week and x["_wk_comments"]:
        text, when = " ".join(t for _, t in x["_wk_comments"]), x["_wk_comments"][-1][0]
    else:
        text, when = x.get("feedback_safe") or "", x.get("feedback_date")
    if m.link and text:
        text = scrub_offers(m, text, x)
    return text.strip(), when


def _field(label, value):
    """One labelled line of a full entry: Said, Offer, Follow-up, Responded."""
    return '<p style="margin:6px 0 0"><b>%s:</b> %s</p>' % (label, value)


def entry_full(m, x, key, limit=None):
    """One person in full: who, what they did and when, then Said, Offer, Follow-up and Responded."""
    m.entries.setdefault(key, []).append((x["id"], "full"))
    name, r = who(m, x)
    s = table("<tr>%s%s</tr>" % (
        c('<h3 style="margin:0;%s;color:%s">%s</h3>' % (hf(SIZE["h3"] - 1, 700, 1.25), P["ink"], name), "card", va="top"),
        c(status_chip(m, x), "card", al="right", va="top", st="white-space:nowrap;padding-left:8px")))
    did = did_words(m, x, key)
    head_ = ([r] if r else []) + did
    if head_:
        s += para(DOT.join(head_), SIZE["small"], top=3, color=P["grey"], lh=1.45)
    text, when = said_text(m, x, x["_active"])
    masked = x["id"] in m.masked
    fields = ""
    if text:
        lab = "" if text.lower().startswith("said ") else "<b>Said:</b> "         # never "Said: Said ..."
        body = comment_kicker(m, x, md(when) if when else "") + para(lab + safe(m, text, x), SIZE["text"], top=3, color=P["ink"])
        tg = tags(x)
        if tg:
            body += para(DOT.join(tg), SIZE["sub"], top=4, color=P["grey"], weight=700)
        s += sp(9) + table("<tr>%s%s</tr>" % (
            c("&nbsp;", "card", w=4, bg=P["gold"], st="font-size:0;line-height:0"),
            c(body, "cream", pad="8px 12px 9px", at=' data-sr="comment"')))
    elif masked:
        fields += _field("Said", "Kept to the email copy.")
    elif not m.link and x["id"] not in m.after_ids:
        # The link copy prints no empty "Said:" line: there, a missing comment may be one whose sentences about an
        # offer were taken out, and the page must not say which. Someone in the "since the week closed" box at the
        # top gets no such line either: the box already says what has happened since.
        fields += _field("Said", "No feedback from them yet.")
    if not m.link:
        fields += _field("Offer", offer_value(m, x))
    fields += _field("Follow-up", follow_value(m, x, limit)) + _field("Responded", responded_value(m, x))
    s += '<div style="%s">%s</div>' % (fz(SIZE["small"], 1.45), fields)
    if OPT.get("mode") == "link" and x["_t"] and not masked:
        s += sp(10) + kicker("Day by day") + sp(2) + timeline(m, x, text)
    return card(s, pad="12px 14px 12px", top=10, at=entry_mark(m, x, "full"))


SHORT_IN_LIST = (("On the disclosure package list (", "On the list "), ("On the disclosure package list", "On the list"),
                 ("Disclosure package sent", "Sent"), ("Opened the disclosure package", "Opened"))


def line_bits(m, x, key, detail):
    """What a one-line entry says after the name (see fit.FIT_LEVELS, line_detail)."""
    did = did_words(m, x, key, only=True) if detail else []
    if key == "disclosure":
        for i, b in enumerate(did):
            for long_, short_ in SHORT_IN_LIST:
                if b.startswith(long_):
                    if b.startswith("Disclosure package sent through"):
                        short_ = "Package sent"          # "Sent through the host" could be read as the visitor being sent
                    did[i] = (short_ + b[len(long_):]).rstrip(")")
                    break
    stands = stands_words(m, x)
    if stands == "Passed" and detail <= 1:
        # with no "Last contact" date on the line, say when: every answer this person gave us falls in one month
        months = set((d.year, d.month) for d in x["_reply_days"])
        if len(months) == 1 and x["_reply_days"][-1] < m.WS:
            y, mo = months.pop()
            stands = "Passed in %s%s" % (MONTH_NAMES[mo - 1], "" if y == m.WE.year else " %d" % y)
    bits = list(did) + [stands]
    if x.get("price_reaction") in ("too_high", "fair_or_positive") and x["id"] not in m.masked and price_view_current(m, x):
        bits.append(PRICE_TAG[x["price_reaction"]])
    if m.after_answer.get(x["id"]) and x["status"] not in ("awaiting_reply", "not_yet_contacted"):
        bits.append("More on %s at the top of this report" % md(m.after_answer[x["id"]]))
    if detail > 1 and x["_last"] and x["status"] != "awaiting_reply":
        bits.append("Last contact %s" % md(x["_last"]))
    elif detail > 1 and x["_last_out"] and x["status"] == "awaiting_reply" and not x["_via_host"]:
        # (someone reached only through a host has one dated step, the package, and the line already gives it)
        # a date the log does not give exactly is never printed as if it did
        loose = any(t.get("date_quality") == "approximate" for t in x["_out"] if pd(t["date"]) == x["_last_out"])
        bits.append("Last tried %s%s" % ("about " if loose else "", md(x["_last_out"])))
    return bits


MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
WEEK_ABOUT = re.compile(r"\babout ([^.,;:]+)")


def price_view_current(m, x):
    """True when the person's view on price was given at today's list price. A one-line entry has no room to say
    which price a remark was about, so a remark made at an earlier list price is left to the price record."""
    said = [e["date"] for e in C.counted_feedback(x, m.WE) if e.get("price_reaction") == x.get("price_reaction")]
    return bool(said) and m.price_on(max(said)) == m.L["list_price"]


def week_words(m, x):
    """What a one-line entry says about this week: 'Answered this week' when they did, with the point they raised
    ('Answered this week: chose or preferred another property'). When only we reached out
    it says so, and about what when there was one subject ('Told about the new list price this week'). Someone
    who only did something (came to an open house, say) is 'In touch this week'."""
    out = m.wk(x, "out")
    if out and not m.wk(x, "rep") and x["id"] not in m.masked:
        topics = set(mt.group(1).strip() for t in out for mt in [WEEK_ABOUT.search(t.get("summary_safe") or "")] if mt)
        if len(topics) == 1:
            return "Told about %s this week" % esc(topics.pop())
        return "We followed up this week"
    if not m.wk(x, "rep"):
        return "In touch this week"
    # the point they raised this week, in the words of the tally on top (at most two), so the line says why
    keys = []
    for e in C.counted_feedback(x, m.WE):
        if pd(e["date"]) >= m.WS:
            keys += [k for k in e.get("themes") or [] if k not in keys and k not in ("other", "no_reason")]
    labels = dict((t["key"], t["label"]) for t in m.d["themes_vocabulary"]["themes"])
    if keys and x["id"] not in m.masked:
        return "Answered this week: " + join_and([low1(labels[k]) for k in keys[:2] if k in labels])
    return "Answered this week"


def entry_line(m, x, key, detail=2, first=False, this_week=False):
    """One line for an earlier person: the name, what they did, where it stands, the last contact."""
    m.entries.setdefault(key, []).append((x["id"], "line"))
    b = brokerage(m, x)
    bits = line_bits(m, x, key, detail)
    if this_week:
        wk = week_words(m, x)
        if wk.startswith("Answered this week"):
            # "Answered, undecided. Answered this week." says it twice: the standing keeps only how they lean
            lean = {"Answered, interested": "Interested", "Answered, undecided": "Undecided", "Answered": None}
            bits = [lean.get(b, b) for b in bits if lean.get(b, b)]
        bits.append(wk)
    name = dname(m, x)
    lead = (", %s. " % b) if (b and detail > 1) else (" " if name.endswith(".") else ". ")       # 'Odalys V. Toured ...', never 'V..'
    return '<div%s style="padding:6px 0%s"><b>%s</b>%s%s.</div>' % (
        entry_mark(m, x, "line"), "" if first else ";border-top:1px solid %s" % P["line"], name, lead, ". ".join(bits))


def line_names(m, xs, key):
    """The last step of the fit ladder: earlier people as names grouped by where it stands, still one entry each."""
    groups, order = {}, []
    for x in xs:
        m.entries.setdefault(key, []).append((x["id"], "line"))
        st = stands_words(m, x)
        if x["status"] in ("awaiting_reply", "not_yet_contacted") and m.after_answer.get(x["id"]):
            st = "Answered after the week closed, see the top of this report"
        elif x["status"] == "awaiting_reply":
            st = "No reply yet"
        if st not in groups:
            groups[st] = []
            order.append(st)
        more = m.after_answer.get(x["id"]) if x["status"] not in ("awaiting_reply", "not_yet_contacted") else None
        groups[st].append('<span%s>%s</span>%s' % (entry_mark(m, x, "line"), dname(m, x), (" (more on %s at the top)" % md(more)) if more else ""))
    return "".join('<p style="margin:6px 0 0"><b>%s (%d):</b> %s</p>' % (st, len(groups[st]), ", ".join(groups[st])) for st in order)


def list_title(m, key):
    """The heading a list carries on this page, without its count. The showings list is 'Agents who showed the
    home' only when everyone in it is an agent."""
    if key == "showings" and not all(x.get("kind") == "agent" for x in m.lists["showings"]):
        return "Agents and buyers who toured the home"
    return LIST_TITLE[key]


def entry_pointer(m, x, key, first=False):
    """A person shown in full under an earlier list: 'Odalys V.: see Agents who showed the home'."""
    m.entries.setdefault(key, []).append((x["id"], "pointer"))
    return '<div%s style="padding:5px 0%s"><b>%s</b>: see %s</div>' % (
        entry_mark(m, x, "pointer"), "" if first else ";border-top:1px solid %s" % P["line"], dname(m, x), list_title(m, x["primary_list"]))


def pointer_names(m, xs, key):
    """The same pointers as one run of names, for an email short on room. Each name is still one entry."""
    groups, order = {}, []
    for x in xs:
        m.entries.setdefault(key, []).append((x["id"], "pointer"))
        k = x["primary_list"]
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append('<span%s>%s</span>' % (entry_mark(m, x, "pointer"), dname(m, x)))
    return "<br>".join("See %s: %s" % (list_title(m, k), ", ".join(groups[k])) for k in order)
