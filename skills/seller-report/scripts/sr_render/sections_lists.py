# -*- coding: utf-8 -*-
"""sr_render.sections_lists: the details. Offers and likely offers, then people grouped by what they did.

The lists match the numbers on top and the way the team's sheet is kept: agents who showed the home, people on
the disclosure package list, open houses with the visitors we know of, and other inquiries. The count in each
heading equals the number of entries beneath it. A person who did two things is shown in full in the first
list they belong to and as a one-line pointer in the others. In the email, people active in the report week
are shown in full and earlier people get one line each; the link copy and the PDF show everyone in full.
"""
import sr_contract as C
from .people import *        # noqa: F401,F403


def s_details_band(m):
    """The black band that divides the summary from the details."""
    s = kicker("The details", P["gold"])
    s += '<h2 class="h2" style="margin:5px 0 0;%s;color:%s">Who came, what they said and how we followed up</h2>' % (
        hf(SIZE["h2"], 700, 1.25), P["on_dark"])
    if m.link:
        txt = "People are grouped by what they did. Everyone is shown in full, with every date we followed up."
    else:
        txt = "People are grouped by what they did. Everyone active this week is shown in full. Earlier people have one line each."
    s += para(txt, SIZE["text"], top=6, color=P["on_dark_soft"])
    inner = table("<tr>%s%s</tr>" % (c("&nbsp;", "dark", w=6, bg=P["gold"], st="font-size:0;line-height:0"),
                                    c(keep(s, "dark"), "dark", pad="20px 0 20px 14px")))
    return band_gap() + ('<tr><td class="g" data-sr-section="details" bgcolor="%s" style="padding:0 %dpx;color:%s">%s</td></tr>'
                         % (P["ink"], SIZE["gutter"], P["on_dark"], inner))


# ---------------------------------------------------------------------------------------------
# offers and likely offers
# ---------------------------------------------------------------------------------------------
def next_no(m, x):
    nm = x["name_short"]
    for i, it in enumerate(m.d.get("next_week") or []):
        if nm in it:
            return i + 1
    return None


def lead_words(m, x):
    """The one line a buyer who is still deciding last gave us, and its date."""
    w = x.get("_lead") or {}
    if w.get("basis_safe"):
        return w["basis_safe"], w.get("basis_date")
    if x["_wk_comments"]:
        return x["_wk_comments"][-1][1], x["_wk_comments"][-1][0]
    if x.get("feedback_safe"):
        return x["feedback_safe"], x.get("feedback_date")
    return "", None


def offer_block(m, o, terms=False):
    """One offer, email only: date, agent, price against the list price that day, where it stands, the terms."""
    x = m.byid.get(o.get("contact_id"))
    who_ = esc(o.get("agent_short") or "Agent not recorded")
    b = C.display_brokerage(o.get("brokerage"), m.ID)
    if b:
        who_ += ", " + esc(b)
    s = '<b style="color:%s">%s%s%s</b>' % (P["ink"], md(o["date"]), DOT, who_)
    bits = []
    if o.get("price") is not None:
        pct = o.get("pct_of_list")
        bits.append("%s%s" % (money(o["price"]), (", %s%% of the list price at the time" % ("%g" % pct)) if pct is not None else ""))
    bits.append(OFFER_STATE.get(o.get("state"), cap1(o.get("state") or "")))
    s += "<br>" + ". ".join(bi for bi in bits if bi) + "."
    if terms and o.get("terms_summary"):
        s += para(esc(o["terms_summary"]), SIZE["small"], top=4)
    if o.get("note_safe"):
        s += para(esc(o["note_safe"]), SIZE["small"], top=4)
    if x and x["_last"] and x["_last"] > pd(o["date"]) and x.get("feedback_safe"):
        s += sp(6) + kicker("As reported to our team" + DOT + md(x["_last"]))
        s += para("<b>Latest from this agent:</b> %s" % esc(x["feedback_safe"]), SIZE["small"], top=2)
    return s


def offers_outcome(m):
    """'1 of those buyers has since chosen another property and 2 have no outcome on record.'"""
    closed, gone, open_ = {}, [], 0
    for o in m.offers:
        x = m.byid.get(o.get("contact_id"))
        st = o.get("state")
        if st in ("accepted", "withdrawn", "declined", "expired"):
            closed[st] = closed.get(st, 0) + 1
        elif x is not None and x["status"] == "passed":
            gone.append(x)
        else:
            open_ += 1
    bits = ["%d %s %s" % (k, "was" if k == 1 else "were", st) if st != "expired" else "%d expired" % k for st, k in sorted(closed.items())]
    if gone:
        elsewhere = all("chose_another_home" in (x.get("themes") or []) for x in gone)
        bits.append("%d of those buyers %s since %s" % (len(gone), "has" if len(gone) == 1 else "have",
                                                        "chosen another property" if elsewhere else "passed"))
    if open_:
        bits.append("%d %s no outcome on record" % (open_, "has" if open_ == 1 else "have"))
    return (cap1(join_and(bits)) + ".") if bits else ""


def s_offers(m):
    """Offers and likely offers: this week's offers with their terms, buyers who may still write one, and
    every earlier offer. The link copy carries none of it."""
    if m.link:
        txt = ("This copy can be forwarded, so it leaves out offer prices, offer terms, the names of agents with an offer "
               "on file, and who may be weighing one. Sentences about offers are taken out of the notes in this copy.")
        if m.offers:
            wks = sorted(set((m.week_of(o["date"]) or {}).get("n") for o in m.offers if m.week_of(o["date"])))
            states = {}
            for o in m.offers:
                k = OFFER_STATE.get(o.get("state"), "On file").lower()
                states[k] = states.get(k, 0) + 1
            txt += " %s on file, received %s (%s)." % (
                cap1(n_(len(m.offers), "offer")), "in week %s" % join_and(["%d" % w for w in wks]) if wks else "earlier",
                ", ".join("%d %s" % (v, k) for k, v in states.items()))
        return sec(head("Offers and likely offers", "Offer news is shared by email only", txt), name="offers")
    n_now = len(m.offers_week)
    if n_now:
        title = "%s this week" % cap1(n_(n_now, "offer"))
    elif m.fresh_leads:
        k = len(m.fresh_leads)
        title = "No offer this week. %s %s still deciding." % (hk("leads_live", num(k)), "buyer is" if k == 1 else "buyers are")
    else:
        title = "No offer this week, and no one has told us one is coming"
    s = head("Offers and likely offers", title)
    for o in m.offers_week:
        s += card(offer_block(m, o, terms=True), top=10)
    rows = ""
    for i, x in enumerate(m.fresh_leads):
        b = table("<tr>%s%s</tr>" % (
            c('<b style="%s;color:%s">%s</b> <span style="color:%s">%s%s</span>' % (fz(SIZE["body"], 1.4, 700), P["ink"], dname(m, x), P["grey"], DOT, role(m, x)), "card", va="top"),
            c(chip("Still deciding", "lean"), "card", al="right", va="top", st="white-space:nowrap;padding-left:8px")))
        words, when = lead_words(m, x)
        if words:
            b += sp(5) + comment_kicker(m, x, md(when) if when else "") + para(safe(m, words, x), SIZE["text"], top=2, color=P["ink"])
        ln = "<b>Last word:</b> %s." % md(x["_last"])
        k = next_no(m, x)
        if k:
            ln += " <b>Next step:</b> No. %d on next week's list." % k
        b += para(ln, SIZE["small"], top=4)
        rows += "<tr>%s</tr>" % c(b, "card", pad="11px 0", line=i > 0)
    if rows:
        s += card(table(rows), pad="4px 14px", top=10)
    if m.stale_leads:
        names = join_and(["%s (last word %s)" % (dname(m, x), md(x["_last"]) if x["_last"] else "not dated") for x in m.stale_leads])
        listed = [x for x in m.stale_leads if next_no(m, x)]
        tail = ""
        if listed and len(listed) == len(m.stale_leads):
            tail = " %s on next week's list." % ("Both are" if len(listed) == 2 else "All are" if len(listed) > 2 else "It is")
        s += para("<b>Earlier interest we are going back to:</b> %s.%s" % (names, tail), SIZE["text"], top=12)
    ob = m.offers_before
    if ob:
        wks = sorted(set((m.week_of(o["date"]) or {}).get("n") for o in ob if m.week_of(o["date"])))
        lede = ""
        if wks:
            prices = sorted(set(m.price_on(o["date"]) for o in ob if o.get("date")))     # the price on the day of each offer
            lede = "%s came in week %s, when the list price was %s." % (
                ("All %d offers" % len(ob)) if len(ob) > 1 else "The offer", join_and(["%d" % w for w in wks]), join_and([money(p) for p in prices]))
            since = m.cur["n"] - max(wks)
            if since and not m.offers_week:
                lede += " No offer has come in during the %s since." % n_(since, "week")
        out = offers_outcome(m)
        if out:
            lede += " " + out
        rows = "".join("<tr>%s</tr>" % c(offer_block(m, o), "card", pad="10px 0", line=i > 0) for i, o in enumerate(ob))
        s += keep(h3("Earlier offers (%d)" % len(ob), lede.strip() or None, top=18) + card(table(rows, SIZE["text"]), pad="4px 14px", top=10))
    elif not m.offers:
        s += para("No offers have come in since we listed.", SIZE["text"], top=10)
    return sec(s, name="offers")


# ---------------------------------------------------------------------------------------------
# one list of people
# ---------------------------------------------------------------------------------------------
def lines_card(inner, top=8):
    return card('<div style="%s">%s</div>' % (fz(SIZE["small"], 1.45), inner), pad="4px 14px", top=top, k=False)


def list_people(m, key):
    """The entries of one list. Returns the HTML, wrapped so the ship gate can count the entries against the
    heading. Email: this week's people in full, earlier people one line each, pointers last. Link copy and
    PDF: everyone in full."""
    K = OPT["fit"]
    now, earlier, ptr = m.members(key)
    n = len(now) + len(earlier) + len(ptr)
    if not n:
        return ""
    out = ""
    if m.link:
        if now:
            cards = [entry_full(m, x, key) for x in now]
            out += keep(subhead("This week%s%d" % (DOT, len(now)), top=14) + cards[0]) + "".join(cards[1:])
        if earlier:
            cards = [entry_full(m, x, key) for x in earlier]
            out += keep(subhead("Earlier%s%d" % (DOT, len(earlier)), top=18 if now else 14) + cards[0]) + "".join(cards[1:])
    else:
        full, extra = now[:K["full"]], now[K["full"]:]
        if now:
            cards = [entry_full(m, x, key, K["days"]) for x in full]
            out += subhead("This week%s%d" % (DOT, len(now)), top=14) + "".join(cards)
            if extra:
                out += lines_card("".join(entry_line(m, x, key, max(0, K["line_detail"]), first=(i == 0), this_week=True) for i, x in enumerate(extra)))
        elif earlier and not any(x["_active"] for x in ptr):
            out += para("Nothing new from the people on this list this week.", SIZE["text"], top=10)
        if earlier:
            out += subhead("Earlier%s%d" % (DOT, len(earlier)), top=18 if now else 12)
            if K["line_detail"] < 0:
                out += lines_card(line_names(m, earlier, key))
            else:
                out += lines_card("".join(entry_line(m, x, key, K["line_detail"], first=(i == 0)) for i, x in enumerate(earlier)))
    if ptr:
        out += subhead("Already listed above%s%d" % (DOT, len(ptr)), top=18 if (now or earlier) else 14)
        if m.link or K["pointers"] == "lines":
            out += lines_card("".join(entry_pointer(m, x, key, first=(i == 0)) for i, x in enumerate(ptr)))
        else:
            out += para(pointer_names(m, ptr, key), SIZE["small"], top=6, color=P["grey"])
    return "<div%s>%s</div>" % (mark("list", key), out)


def count_title(m, key, title):
    """'Agents who showed the home (34)': the count is the number of entries beneath the heading."""
    return "%s (%s)" % (title, hk("list:" + key, num(len(m.lists[key]))))


def s_showings(m):
    T, cur = m.T, m.cur
    xs = m.lists["showings"]
    agents_only = all(x.get("kind") == "agent" for x in xs)
    title = count_title(m, "showings", LIST_TITLE["showings"] if agents_only else "Agents and buyers who toured the home")
    if not xs:
        return sec(head("Showings", title, "No agent has shown the home yet."), name="list_showings")
    lede = "%s since we listed, %s this week." % (n_(T["showings"], "showing"), "none" if not cur["showings"] else num(cur["showings"]))
    extra = []
    if T.get("tours_unconfirmed"):
        k = T["tours_unconfirmed"]
        extra.append("%s on the showing list with no confirmation that the tour took place." % cap1(n_(k, "of them is", "of them are")))
    if T.get("tours_approximate_date"):
        k = T["tours_approximate_date"]
        extra.append("%s approximate and %s about." % (cap1(n_(k, "date is", "dates are")), "says" if k == 1 else "say"))
    if T.get("tours_undated"):
        extra.append("%s no date on file." % cap1(n_(T["tours_undated"], "showing has", "showings have")))
    s = head("Showings", title, lede + ((" " + " ".join(extra)) if extra else ""))
    return sec(s + list_people(m, "showings"), name="list_showings")


def via_sentence(m):
    """Buyers who got the package from their own agent or a host: one count, never added to the list."""
    T = m.T
    k = T.get("disclosure_shared_buyers") or 0
    if not k:
        return ""
    s = "%s got the package from their own agent or an open house host. We follow up with them through that agent, so they are not in this list." % (
        cap1(hk("shared_buyers", num(k)) + (" more buyer" if k == 1 else " more buyers")))
    if m.link and m.via:
        by = {}
        for x in m.via:
            a = x.get("represented_by")
            # agents with an offer on file are one unnamed entry, however many of them there are
            nm = ("agents with an offer on file" if a in m.masked else dname(m, m.byid[a])) if a in m.byid else "an open house host"
            by[nm] = by.get(nm, 0) + 1
        s += " By agent: " + ", ".join("%s (%d)" % (nm, n) for nm, n in sorted(by.items(), key=lambda r: (-r[1], r[0]))) + "."
    return s


def s_disclosure(m):
    T, cur, tr = m.T, m.cur, m.track
    xs = m.lists["disclosure"]
    title = count_title(m, "disclosure", "People on the disclosure package list")
    if not xs:
        s = head("Disclosure packages", title, "Nobody has asked for the disclosure package yet.")
        via = via_sentence(m)
        return sec(s + (para(via, SIZE["text"], top=8) if via else ""), name="list_disclosure")
    new = cur.get("disclosure_contacts_new") or 0
    lede = "%s this week." % (cap1(no_(new, "new person", "new people")))
    bits = []
    if tr.get("disclosure_sent") and T.get("disclosure_link_sent") is not None:
        bits.append("%s sent" % n_(T["disclosure_link_sent"], "package link"))
    if tr.get("disclosure_opened") and T.get("disclosure_opened_confirmed") is not None:
        bits.append("%s opened that we know of" % num(T["disclosure_opened_confirmed"]))
    if bits:
        lede += " %s since we listed." % cap1(join_and(bits))
    elif not tr.get("disclosure_sent") and not tr.get("disclosure_opened"):
        lede += " The log lists who is on the package list. Sends and opens are not recorded."
    s = head("Disclosure packages", title, lede)
    via = via_sentence(m)
    if via:
        s += para(via, SIZE["small"], top=6, color=P["grey"])
    return sec(s + list_people(m, "disclosure"), name="list_disclosure")


def session_line(m, o, recap=False):
    """One open house session in one line: date, the count in the host's own unit, the host."""
    txt = '<b style="color:%s">%s</b>%s%s%sHost %s' % (P["ink"], wmd(o["date"]), DOT, cap1(oh_count(m, o)), DOT, esc(o.get("host") or "not recorded"))
    rc = safe(m, o.get("recap_safe") or "")
    if recap and rc and norm(rc) != norm(oh_count(m, o)):
        txt += "<br>" + rc
    return txt


def host_row(m, x, first):
    """Link copy: an open house host, shown apart from the people we follow up with."""
    ses = sorted((o for o in m.oh if o.get("host_contact_id") == x["id"] or (not o.get("host_contact_id") and o.get("host") == x["name_short"])),
                 key=lambda o: o["date"])
    recaps = len([o for o in ses if o.get("recap_safe")])
    bits = []
    if ses:
        bits.append("Hosted %s" % join_and([md(o["date"]) for o in ses]))
        bits.append("Recap on file" if recaps == len(ses) else ("Recap on file for %d of %d" % (recaps, len(ses)) if recaps else "No recap on file"))
    if x["_out"]:
        bits.append("%s from us on %s" % (n_(len(x["_out"]), "message"), dates_compact(x["_out_days"])))
    if x["_n_rep"]:
        bits.append(n_(x["_n_rep"], "reply", "replies") + " from the host")
    s = table("<tr>%s%s</tr>" % (
        c('<b style="%s;color:%s">%s</b>' % (fz(SIZE["body"], 1.4, 700), P["ink"], dname(m, x)), "card", va="top"),
        c(status_chip(m, x), "card", al="right", va="top", st="white-space:nowrap;padding-left:8px")))
    if x.get("feedback_safe"):
        s += sp(4) + kicker("As reported by the host") + para(safe(m, x["feedback_safe"], x), SIZE["text"], top=2, color=P["ink"])
    if bits:
        s += para(". ".join(bits) + ".", SIZE["small"], top=3, lh=1.45)
    return "<tr>%s</tr>" % c(s, "card", pad="11px 0", line=not first)


def s_openhouse(m):
    """Each session (date, host, visitors in the host's own unit, notable comments), then the visitors we know of."""
    T, K = m.T, OPT["fit"]
    title_v = count_title(m, "open_house", LIST_TITLE["open_house"])
    none_v = "No open house visitor has left a name with us yet."
    if not m.oh:
        s = head("Open houses", "No open house has been held yet")
        s += h3(title_v, None if m.lists["open_house"] else none_v, top=18) + list_people(m, "open_house")
        return sec(s, name="open_houses")
    total ="%s %s since we listed" % (hk("oh_sessions", num(len(m.oh))), "session" if len(m.oh) == 1 else "sessions")
    if T.get("open_house_groups") is not None:
        total += ", %s" % oh_total_words(m, T["open_house_groups"])
    nc = T.get("open_house_sessions_without_count")
    if nc:
        total += ", %s with no count kept" % n_(nc, "session")
    prior = sorted(m.oh_before, key=lambda o: o["date"], reverse=True)
    s = head("Open houses", ("%s this week" % cap1(n_(len(m.oh_week), "open house"))) if m.oh_week else "No open house this week",
             cap1(total) + ".")
    by_host = "<tr>%s</tr>" % c(kicker("As reported by the host"), "card", pad="10px 0 0")
    rows, said = "", False
    for i, o in enumerate(m.oh_week):
        bits = [wmd(o["date"])]
        if o.get("time_text"):
            bits.append(esc(o["time_text"]))
        line2 = "Host %s%s%s" % (esc(o.get("host") or "not recorded"), DOT, cap1(oh_count(m, o)))
        dr = o.get("disclosure_requests")
        if dr:
            line2 += DOT + n_(dr, "disclosure request")
        rc = safe(m, o.get("recap_safe") or "")
        recap = bool(rc and norm(rc) != norm(oh_count(m, o)))
        said = said or recap
        rows += "<tr>%s</tr>" % c('<b style="color:%s">%s</b><br>%s%s' % (
            P["ink"], DOT.join(bits), line2, para(rc, SIZE["text"], top=3, color=P["ink"]) if recap else ""),
            "card", pad="10px 0", line=i > 0)
    if rows:
        s = keep(s + card(table((by_host if said else "") + rows, SIZE["text"]), pad="4px 14px", top=10))
    if prior:
        hd = subhead("Earlier sessions%s%d" % (DOT, len(prior)), top=16)
        if m.link:
            def session(i, is_first):
                return "<tr>%s</tr>" % c(session_line(m, prior[i], recap=True), "card", pad="8px 0", line=not is_first, st="font-size:%dpx" % SIZE["small"])
            s += row_cards(session, len(prior), hd + sp(4) + kicker("As reported by each host"), pad="4px 14px", top=6)
        elif K["sessions"] is None or len(prior) <= K["sessions"]:
            s += hd + lines_card("".join('<div style="padding:6px 0;%scolor:%s">%s</div>' % (
                "" if i == 0 else "border-top:1px solid %s;" % P["line"], P["grey"], session_line(m, o)) for i, o in enumerate(prior)))
        else:
            o = prior[0]
            s += para("%s before this week. The most recent was %s: %s, host %s. Each one is in the complete record." % (
                cap1(n_(len(prior), "session")), wmd(o["date"]), oh_count(m, o), esc(o.get("host") or "not recorded")), SIZE["small"], top=10)
    s += h3(title_v, None if m.lists["open_house"] else none_v, top=20) + list_people(m, "open_house")
    if m.link and m.team:
        rows = "".join(host_row(m, x, i == 0) for i, x in enumerate(m.team))
        s += keep(h3("Open house hosts, on our side of the table (%d)" % len(m.team),
                     "Hosts work with us. They are not counted as contacts, and our messages to them are not counted as follow-up.") +
                  card(table(rows), pad="4px 14px", top=10))
    return sec(s, name="open_houses")


def s_inquiries(m):
    """Only when there is someone to list: people who asked about the home and are in none of the lists above."""
    xs = m.lists["other_inquiries"]
    if not xs:
        return ""
    T = m.T
    title = count_title(m, "other_inquiries", "People who asked about the home")
    lede = "%s since we listed. The people here are in none of the lists above." % cap1(n_(T["inquiries"], "inquiry", "inquiries"))
    return sec(head("Other inquiries", title, lede) + list_people(m, "other_inquiries"), name="list_other_inquiries")


def s_history(m):
    """Email only: the way to everyone's full history."""
    if m.link:
        return ""
    url = OPT.get("link_url")
    txt = "Every person above, with every date we tried and every comment since we listed, is in the complete record"
    if url:
        s = para(txt + ".", SIZE["text"], top=0) + sp(10) + button(url, "OPEN THE COMPLETE RECORD", sf="light")
    else:
        s = para(txt + ". Reply to this email and I will send it to you.", SIZE["text"], top=0)
    return sec(s, top=22, name="history")
