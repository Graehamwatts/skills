# -*- coding: utf-8 -*-
"""sr_render.sections_record: the running record that every issue carries forward.

The black band, the follow-up since we listed, every week in one table, how we count, and the footer. (Every
price comment and the record at each list price are in sections_saying.)
"""
import re

import sr_contract as C
from .text import *        # noqa: F401,F403
from .sections_numbers import week_groups, week_val
from .sections_saying import by_price, approx_words


def s_record_band(m):
    L = m.L
    s = kicker("The record since we listed", P["gold"])
    s += '<h2 class="h2" style="margin:5px 0 0;%s;color:%s">%s on the market, every week on the page</h2>' % (
        hf(SIZE["h2"], 700, 1.25), P["on_dark"], cap1(n_(len(m.W), "week")))
    s += para("From here down is the running record since %s. It is carried forward and grows by one row every Monday."
              % md(L["list_date"]), SIZE["text"], top=6, color=P["on_dark_soft"])
    inner = table("<tr>%s%s</tr>" % (c("&nbsp;", "dark", w=6, bg=P["gold"], st="font-size:0;line-height:0"),
                                    c(keep(s, "dark"), "dark", pad="20px 0 20px 14px")))
    return band_gap(0 if OPT.get("print") else 30) + ('<tr><td class="g" data-sr-section="record" bgcolor="%s" style="padding:0 %dpx;color:%s">%s</td></tr>'
                                                       % (P["ink"], SIZE["gutter"], P["on_dark"], inner))


def stat_tiles(tiles):
    """Large gold numbers on black, side by side: [(number, caps label)]."""
    w = 100 // len(tiles)
    cells = ""
    for i, (big, lab) in enumerate(tiles):
        inner = '<div style="%s;color:%s">%s</div><div style="%s;letter-spacing:.1em;color:%s;padding-top:6px">%s</div>' % (
            hf(SIZE["stat"], 800, 1.0), P["gold"], big, hf(SIZE["micro"], 700, 1.3), P["on_dark_soft"], esc(lab).upper())
        cells += c(inner, "dark", w="%d%%" % w, al="center", va="top", pad="2px 4px 0",
                   st=("border-left:1px solid %s;" % P["dark_line"]) if i else "")
    return '<table %s width="100%%"><tr>%s</tr></table>' % (TBL, cells)


def s_followup_record(m):
    """The proof of work since we listed: how many follow-ups, on how many separate days, how many replies, and
    where the answers stand. A black callout with the three numbers in gold."""
    T = m.T
    nd, nr, nw, n3 = T["contacts"], T["replied"], T["awaiting_reply"], T["awaiting_reply_3plus_attempts"]
    if not nd:
        return ""
    soft = P["on_dark_soft"]
    lab = '<b style="color:%s">%%s</b> ' % P["gold"]
    one = lambda k, a, b: a if k == 1 else b
    s = stat_tiles([(hk("followups", num(T["touches_outbound"])), one(T["touches_outbound"], "Follow-up", "Follow-ups")),
                    (hk("followup_days", num(T["outbound_distinct_days"])), one(T["outbound_distinct_days"], "Separate day", "Separate days")),
                    (hk("replies", num(T["replies_inbound"])), one(T["replies_inbound"], "Reply", "Replies"))])
    allp = [x for x in m.direct if x["_out"]]
    vhp = [x for x in allp if x["_via_host"]]
    line = "Our follow-ups went to %s %s%s." % (hk("followup_people", num(len(allp))), one(len(allp), "person", "people"),
                                             (" (%d of them through the open house host)" % len(vhp)) if vhp else "")
    if n3:
        k3 = hk("waiting_3plus", num(n3))
        if nw == 1:
            line += " The %s person still waiting has been tried on 3 or more days." % k3
        elif n3 == nw:
            line += " All %s still waiting have been tried on 3 or more days." % k3
        else:
            line += " %s of the %d still waiting %s been tried on 3 or more days." % (k3, nw, "has" if n3 == 1 else "have")
    s += para(line, SIZE["small"], top=14, color=soft)
    wkp = len([x for x in m.passed if x["_active"]])
    # people who passed earlier and were contacted again this week are in wkp too, so it is not "passed this week"
    bd = ["%d passed%s" % (len(m.passed), (" (%d of them in touch this week)" % wkp) if wkp else "")] if m.passed else []
    if m.open:
        bd.append("%d gave no final answer" % len(m.open))
    if m.offered:
        n_off = len(m.offered)
        bd.append(("%d %s an offer on file" % (n_off, "has" if n_off == 1 else "have")) if m.link else "%d wrote an offer" % n_off)
    if nr and bd:
        s += para(lab % ("Of the %d who answered:" % nr) + join_and(bd) + ".", SIZE["small"], top=6, color=soft)
    if m.open:
        # "still open" read as live prospects. Say how they lean and how long it has been.
        q = LIMITS["quiet_days"]
        intr = len([x for x in m.open if x.get("interest") in ("warm", "hot")])
        und = len([x for x in m.open if x.get("interest") == "cold"])
        oth = len(m.open) - intr - und
        t = join_and([("%d interested" % intr) if intr else "", ("%d undecided" % und) if und else "",
                      ("%d with no read yet" % oth) if oth else ""]) + "."
        # by the last contact in either direction, so a follow-up we made counts as contact too
        old_ = T["open_no_final_answer_quiet"]
        if old_:
            t += " %s had no contact with us in the last %d days." % (
                ("All %d have" % old_) if (old_ == len(m.open) and old_ > 1) else ("%d of them have" % old_) if len(m.open) > 1 else "That person has", q)
        s += para(lab % ("No final answer (%d):" % len(m.open)) + t, SIZE["small"], top=6, color=soft)
    if m.team:
        n_team = len(m.team)
        s += para("%s with us and %s not counted here." % (cap1(n_(n_team, "open house host works", "open house hosts work")),
                                                           "is" if n_team == 1 else "are"), SIZE["small"], top=6, color=soft)
    return sec(keep(h3("Follow-up since we listed", top=0) + card(s, sf="dark", pad="18px 14px 16px", top=10, border=P["ink"])),
               top=26, name="followup")


def days_words(a, b):
    if a == b:
        return md(a)
    return "%s and %s" % (md(a), md(b)) if (b - a).days == 1 else "%s to %s" % (md(a), md(b))


def s_stack(m):
    """Every week in one table: one row a week, list price bands, a subtotal for each band."""
    W, cur, T = m.W, m.cur, m.T
    kb = bool(m.track.get("keybox_showings"))
    num_ = lambda fn: (lambda ws: num(sum(fn(w) for w in ws)))

    def views(ws):
        if ws is W:                 # all weeks: the count since we listed, the same number as the table at the top
            return num(T["online_views"]) if T.get("online_views") is not None else "&nbsp;"
        got = [w["online_views"] for w in ws if w.get("online_views") is not None]
        return num(sum(got)) if got else "&nbsp;"
    # Widths are set for a 320 px phone: every header word and every date fits its fixed column on one line.
    # "Shown" is the Showings row of the numbers table: key-box showings plus tours agents told us about.
    # A phone has room for eight columns. When online views are recorded they take the place of the packages
    # column, which the week by week chart at the top already gives for every week.
    ov = bool(m.online_weekly)
    wd_ = (lambda a, b: b) if ov else (lambda a, b: a)
    cols = [("Shown", wd_("14%", "13%"), num_(lambda w: w["showings"]), "showings")]
    if not ov:
        cols.append(("Pkgs", "10%", num_(lambda w: w.get("disclosure_contacts_new") or 0), "disclosure_contacts_new"))
    cols += [("Open<br>house", wd_("12%", "11.5%"), "oh", "open_house_groups"),
             ("Follow<br>ups", wd_("13%", "12%"), num_(lambda w: w["touches_outbound"]), "touches_outbound"),
             ("Talks", wd_("11%", "10.5%"), num_(lambda w: w.get("conversations_with_feedback") or 0), "conversations_with_feedback"),
             ("High/<br>fair", wd_("12%", "11.5%"), lambda ws: "%d&nbsp;/&nbsp;%d" % (sum(w["price_too_high"] for w in ws), sum(w["price_fair_or_positive"] for w in ws)), "PRICE_PAIR"),
             ("Offers", "12%", num_(lambda w: w.get("offers") or 0), "offers")]
    if ov:
        cols.append(("Views", "13.5%", views, "online_views"))
    ncol = len(cols) + 1
    # each header line is one word, so it cannot wrap inside its fixed column (600 keeps Inter inside it at 320 px)
    hs = "font-size:12px;font-weight:600;letter-spacing:-.2px"
    hdr = "<tr>%s%s</tr>" % (gth("Week", w="16%", pad="7px 0 7px 6px", st=hs, at=mark("col", "LABEL")), "".join(
        gth(t, w=wd, al="right", pad="7px 5px 7px 0" if i == len(cols) - 1 else "7px 0", st=hs, at=mark("col", field))
        for i, (t, wd, _, field) in enumerate(cols)))

    def cells(ws, sf, bold, bg=None, fg=None, st=""):
        out = ""
        for _, _, fn, _ in cols:
            if fn == "oh":
                if len(ws) == 1:
                    t = week_val(m, ws[0], "open_house_groups")[0]
                    # the two words are set a size down so they keep a gap from the number beside them on a 320 px phone
                    t = {"none held": '<span style="font-size:%dpx">none</span>' % SIZE["sub"],
                         "no count": '<span style="font-size:%dpx">held</span>' % SIZE["sub"]}.get(t, t)
                else:
                    t = num(sum(w.get("open_house_groups") or 0 for w in ws))
            else:
                t = fn(ws)
            # the alignment sits on each cell, not on the row, so no mail client can drop it.
            # The last column keeps 5 px clear of the edge of the table.
            out += c(("<b>%s</b>" if bold else "%s") % t, sf, bg=bg, fg=fg, al="right", st=st + ("padding-right:5px" if fn is cols[-1][2] else ""))
        return out

    def label(text, sf, bg=None, fg=None, st=""):
        return c(text, sf, bg=bg, fg=fg, al="left", pad="9px 0 9px 6px", th=True, scope="row", st=st + "font-size:12px;font-weight:700;white-space:nowrap")
    rows = hdr
    k = 0
    many = len(m.regimes) > 1
    edge = "border-top:2px solid %s;" % P["ink"]
    for ri, (r, groups) in enumerate(week_groups(m, "table_weeks")):
        ws_all = r["weeks"]
        if many:
            band = ("Week %d" % ws_all[0]["n"]) if len(ws_all) == 1 else "Weeks %d to %d" % (ws_all[0]["n"], ws_all[-1]["n"])
            band += DOT + money(r["price"])
            if r["change_date"]:
                band += " from " + md(r["change_date"]).replace(" ", "&nbsp;")
            elif r["until"]:
                band += " until " + md(r["until"]).replace(" ", "&nbsp;")
        else:
            band = "List price %s" % money(r["price"])
        rows += "<tr>%s</tr>" % c("<b>%s</b>" % band, "dark", span=ncol, pad="7px 8px", fg=P["gold"])
        k = 0
        for ws in groups:
            w = ws[0]
            is_cur = len(ws) == 1 and w["n"] == cur["n"]
            sf = "tint" if is_cur else zebra(k)
            k += 1
            date = "<br>" + md(ws[0]["start"]).replace(" ", "&nbsp;")
            lab = ("<b>%d&nbsp;to&nbsp;%d</b>" % (ws[0]["n"], ws[-1]["n"]) if len(ws) > 1 else "<b>%d</b>" % w["n"]) + date
            # a block of older weeks (see fit.FIT_LEVELS) is marked as such, so nothing reads it as one week
            opened = "<tr%s>" % mark("row", ("block:%d-%d" % (ws[0]["n"], ws[-1]["n"])) if len(ws) > 1 else w["n"])
            rows += "%s%s%s</tr>" % (opened, c(lab, sf, al="left", pad="5px 0 5px 6px", th=True, scope="row", st="font-weight:400"), cells(ws, sf, is_cur))
        sd = r["straddle"]
        if sd:
            # the weeks above are whole weeks: say what the week of the price change holds at the other list price
            got = [n_(sd["keybox"] + sd["tours"], "showing") if (sd["keybox"] + sd["tours"]) else "",
                   ("%s at the open house" % unit_count(sd["oh_groups"], m.oh_unit)) if sd["oh_groups"] else "",
                   n_(sd["offers"], "offer") if sd["offers"] else ""]
            got = join_and(got) or "nothing dated on those days"
            rows += "<tr>%s</tr>" % c("Week %d includes %s at %s: %s." % (sd["week"], days_words(sd["a"], sd["b"]), money(sd["price"]), got),
                                      "card", span=ncol, pad="6px 8px", line=True, st="font-size:%dpx" % SIZE["sub"])
        if many:
            rows += "<tr%s>%s%s</tr>" % (mark("row", "sub:%d" % r["price"]), label(n_(r["n"], "wk"), "card", st=edge), cells(ws_all, "card", True, st=edge))
    rows += "<tr%s>%s%s</tr>" % (mark("row", "all"), label("All %d" % len(W), "dark", fg=P["gold"]), cells(W, "dark", True, fg=P["gold"]))
    if OPT.get("keep"):
        # print: the table may run over a page, but only between rows, and the column heads repeat on the next page
        rows = "<thead>" + hdr + "</thead><tbody>" + re.sub(r"<tr(?=[ >])", '<tr class="k"', rows[len(hdr):]) + "</tbody>"
    s = h3("Every week in one table", top=0) + sheet(table(rows, SIZE["small"], 1.3, data=True, fixed=True, name="weeks"), top=10, k=False)
    wk_sum = lambda key: sum(w.get(key) or 0 for w in W)
    people = m.PT["people_with_feedback"]
    notes = ["<b>Shown</b>: showings, the same count as the Showings row at the top."]
    if not ov:
        pk = "new people on the disclosure package list."
        dated = wk_sum("disclosure_contacts_new")
        if T["disclosure_contacts"] != dated:
            pk += " %d dated in the weeks, %d more with no date on file, %d in all." % (dated, T["disclosure_contacts"] - dated, T["disclosure_contacts"])
        notes.append("<b>Pkgs</b>: " + pk)
    if T.get("tours_undated"):
        notes.append("%s no date on file, so %s in the total since we listed and in no week." % (
            cap1(n_(T["tours_undated"], "showing has", "showings have")), "it is" if T["tours_undated"] == 1 else "they are"))
    notes.append("<b>Open house</b>: %s. None means no open house. Held means one took place with no count kept." % (
        ("%s counted" % UNIT[m.oh_unit][1]) if m.oh_unit else "traffic as each host counted it"))
    fu = "calls, voicemails, texts and emails we made."
    if wk_sum("touches_outbound") != T["touches_outbound"]:
        fu += " %d more were made before the first week, %d in all." % (T["touches_outbound"] - wk_sum("touches_outbound"), T["touches_outbound"])
    notes.append("<b>Follow ups</b>: " + fu)
    talks = "conversations with feedback, one per person per day"
    wsum_c = wk_sum("conversations_with_feedback")
    talks += (", so the %d conversations come from %d different people." % (wsum_c, people)) if wsum_c != people else "."
    notes.append("<b>Talks</b>: " + talks)
    notes.append("<b>High / fair</b>: how many of those said the price is too high, and how many said it is fair or good.")
    if many:
        notes.append("<b>Subtotals</b> add the whole weeks above them." + (" The split by the date of each event is in the table below." if by_price(m) else ""))
    hist = sorted(m.L.get("price_history") or [], key=lambda e: e["date"])
    if len(hist) > 1:
        ph = "Listed %s at %s." % (md(hist[0]["date"]), money(hist[0]["price"]))
        for a, b in zip(hist, hist[1:]):
            ph += " Changed %s to %s." % (md(b["date"]), money(b["price"]))
        notes.append("<b>Price history</b>: " + ph)
    if ov:
        notes.append("<b>Views</b>: online views as counted by %s. A blank means no figure was recorded that week.%s "
                     "New disclosure packages by week are in the chart at the top."
                     % (esc(join_and(m.online.get("portals") or []) or "the listing sites"),
                        " The last line is the count since we listed." if (m.online.get("since_listing") or {}).get("views") else ""))
    if m.R["issue_number"] != cur["n"]:
        notes.append("Issue numbers count the reports we have sent. Week numbers count weeks on the market.")
    return sec(s + para("<br>".join(notes), SIZE["small"], top=10, color=P["grey"], lh=1.5), top=26, name="weekly_table")


def s_howcount(m):
    """Plain definitions in one box. The same rules as references/counting-rules.md."""
    T = m.T
    nw = T["awaiting_reply"]
    items = [("Contacted", "at least one call, text, email or conversation with that person is on record.")]
    wait = "our latest follow-up to that person has not been answered."
    k = T.get("awaiting_reply_answered_before") or 0
    if k:
        wait += " %s answered an earlier one." % (("All %d" % k) if (k == nw and k > 1) else ("%d of the %d" % (k, nw)) if nw > 1 else "That person")
    items.append(("Answered", "they have answered our latest follow-up, or told us where they stand."))
    items.append(("Still waiting", wait + " Tries are the separate days we followed up since their last answer."))
    fu = ("each call, voicemail, text or email we made counts once, so a voicemail plus a text on one day is two. "
          "Each person's entry also gives the number of separate days.")
    dead = T.get("calls_not_connected") or 0
    if dead:
        fu += " A call that did not go through counts as a try: %s did not." % n_(dead, "call")
    if m.via_host:
        fu += " A package sent through an open house host for a visitor counts as one."
    items.append(("Follow-ups", fu))
    items.append(("Separate days", "calendar dates with a follow-up, each counted once however many people we tried that day."))
    items.append(("Replies", "a day on which someone answered us or got in touch, counted once per person per day."))
    tours = ("key-box showings plus tours an agent or buyer told us about. A question, or a showing request that was "
             "cancelled or postponed, is an inquiry and is never counted as a showing.")
    if not m.track.get("keybox_showings"):
        tours += " Key-box showings are not recorded for this listing."
    unc = T.get("tours_unconfirmed") or 0
    if unc:
        tours += " %s on the showing list with no confirmation that the tour took place." % cap1(n_(unc, "tour is", "tours are"))
    items.append(("Showings", tours))
    pk = "new people on the disclosure package list, each counted once, in the week of their first dated entry."
    if T.get("disclosure_shared_buyers"):
        pk += " Buyers who got the package from their own agent are stated on their own line and are not added in."
    items.append(("Disclosure packages", pk))
    items.append(("The lists in the details", "people are grouped by what they did, and the count in each heading is the number of entries "
                  "under it. A person who did two things is shown in full in the first list they belong to (showings, then disclosure "
                  "packages, then open houses) and as a one-line pointer in the others."))
    kept = [x for x in m.direct if x.get("is_open_house_host")]
    if m.team or kept:
        h = ""
        if m.team:
            k = len(m.team)
            out_ = T["team_side_set_aside"]["touches_outbound"]
            h = "%s on our side of the table. %s not counted as %s" % (
                cap1(n_(k, "host works", "hosts work")), "That host is" if k == 1 else "They are", "a contact" if k == 1 else "contacts")
            h += (", and our %s to them %s not counted as follow-up." % (n_(out_, "message"), "is" if out_ == 1 else "are")) if out_ else "."
        if kept:
            k = len(kept)
            h += " %s also showed the home to %s and %s counted as %s." % (
                cap1(n_(k, "more host" if m.team else "host")), "a buyer of their own" if k == 1 else "buyers of their own",
                "is" if k == 1 else "are", "an agent" if k == 1 else "agents")
        items.append(("Open house hosts", h.strip()))
    items.append(("What people are saying", "counts are out of the people who told us something themselves. When a person spoke about "
                  "price more than once, their latest remark decides their row."))
    items.append(("Did not bring up price", "we spoke and the person did not mention price."))
    dts = []
    if T.get("tours_approximate_date"):
        dts.append("%s, taken from the first note that mentions the tour." % cap1(approx_words(m)))
    if T.get("inquiries_undated"):
        dts.append("%d of the %d inquiries %s no date, so the weeks add to %d." % (
            T["inquiries_undated"], T["inquiries"], "has" if T["inquiries_undated"] == 1 else "have", T["inquiries"] - T["inquiries_undated"]))
    if dts:
        items.append(("Dates", " ".join(dts)))
    items.append(("Feedback", "our team's summary of what each agent or buyer told us, as reported to our team. It is not a word for word quote."))
    if not m.link and OPT["fit"]["howcount"] == "short":
        # an email short on room keeps the definitions a seller needs most and says where the rest are
        keep_ = ("Contacted", "Answered", "Still waiting", "Follow-ups", "Showings", "What people are saying", "Feedback")
        items = [(k, v) for k, v in items if k in keep_]
        items.append(("Everything else", "the complete record carries every definition, including how dates, open house hosts and the lists are counted."))
    body = kicker("How we count", P["ink"])
    body += "".join(para("<b>%s:</b> %s" % (k, v), SIZE["small"], top=6, lh=1.5) for k, v in items)
    return sec(card(body, sf="card", pad="14px 14px 14px", top=0), top=26, bot=36, name="how_we_count")


def s_footer(m):
    ID = m.ID
    web = ID.get("website") or ""
    soft = P["on_dark_soft"]
    a = 'style="display:block;padding:11px 0;color:%s;font-weight:700;text-decoration:underline"' % P["on_dark"]
    note = ""
    if m.link:
        note = ("This copy leaves out offer prices, offer terms, the names of agents with an offer on file and who may be "
                "weighing one.")
    realtor = esc(ID["realtor_line"]).upper().replace(chr(0xAE), "&reg;")
    links = '<a href="tel:+1%s" %s>%s</a><a href="mailto:%s" %s>%s</a>' % (
        re.sub(r"[^0-9]", "", ID["phone"]), a, esc(ID["phone"]), esc(ID["email"]), a, esc(ID["email"]))
    if web:
        links += '<a href="https://%s" %s>%s</a>' % (esc(web), a, esc(web))
    return (
        '<tr><td class="g" data-sr-section="footer" bgcolor="%s" style="padding:28px %dpx 32px;background:%s;color:%s">'
        '<div style="%s;letter-spacing:.2em;color:%s">%s</div>'
        '<div style="%s;letter-spacing:.16em;color:%s;padding-top:6px">%s%sDRE #%s</div>'
        '<div style="%s;padding-top:8px">%s</div>'
        '<div style="%s;padding-top:8px">%s</div>'
        '%s<div style="%s;padding-top:14px">%s</div></td></tr>'
        % (P["ink"], SIZE["gutter"], P["ink"], soft, hf(18, 800, 1.1), P["gold"], esc(ID["name"]).upper(),
           hf(SIZE["micro"], 700, 1.3), P["gold"], realtor, DOT, esc(ID["dre"]),
           fz(SIZE["text"], 1.4, None, soft), esc(ID["brand_line"]),
           fz(SIZE["text"], 1.3), links,
           ('<div style="%s;padding-top:12px">%s</div>' % (fz(SIZE["small"], 1.5, None, soft), note)) if note else "",
           fz(SIZE["sub"], 1.5, None, soft), esc(ID.get("disclaimer") or "")))
