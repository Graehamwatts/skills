# -*- coding: utf-8 -*-
"""sr_render.sections_numbers: the numbers table, the line under it, and the week by week charts.

One table answers "what happened this week": this week, last week and since we listed, for the same rows in
every issue, zero or not. Showings are key-box showings plus the tours agents told us about; an inquiry is
never a showing. A count the listing does not record prints as "not recorded", never as zero.
"""
import sr_contract as C
from .text import *        # noqa: F401,F403


def names_for(m, types, w):
    a, b = pd(w["start"]), pd(w["end"])
    out = []
    for x, e in m.events(types):
        if a <= pd(e["date"]) <= b:
            nm = dname(m, x, lower=True) if x.get("name_recorded") is False else dname(m, x)
            if nm not in out:
                out.append(nm)
    return out


def week_val(m, w, key):
    """Returns (display, numeric or None)."""
    if w is None:
        return ("", None)
    v = w.get(key)
    if key == "open_house_groups":
        ses = w.get("open_house_sessions")
        if ses == 0:
            return ("none held", None)
        if v is None:
            return ("no count", None)
    if v is None:
        return ("not recorded", None)
    return (num(v), v)


def number_rows(m):
    """(label, small line under the label, week key, since-launch total, second figure). Every row prints in
    every issue, zero or not, so the stack of reports can be compared row for row. Online views join the table
    only when they are recorded. The second figure is (week key, totals key, word): packages opened, views saved."""
    T, tr, cur = m.T, m.track, m.cur
    small = lambda t: '<div style="font-size:%dpx;color:%s;font-weight:400;padding-top:1px">%s</div>' % (SIZE["sub"], P["grey"], t)
    rows = []
    sub = ""
    if cur["showings"] and cur["showings"] <= LIMITS["names_behind_count"]:
        nm = names_for(m, C.TOUR_TYPES, cur)
        if len(nm) == cur["showings"]:
            sub = small(join_and(nm))
    rows.append(("Showings", sub, "showings", T["showings"], None))
    sub = small("new people sent the package" if tr.get("disclosure_sent") else "new people on the package list")
    rows.append(("Disclosure packages", sub, "disclosure_contacts_new", T["disclosure_contacts"],
                 ("disclosure_opened", "disclosure_opened_confirmed", "opened") if tr.get("disclosure_opened") else None))
    sub = small("as each host counted") if (not m.oh_unit and T.get("open_house_groups") is not None) else ""
    rows.append((oh_label(m), sub, "open_house_groups", T.get("open_house_groups"), None))
    sub = ""
    if cur["touches_outbound"]:
        sub = small("to %s on %s" % (hk("week_followup_people", num(cur["outbound_people"])) + (" person" if cur["outbound_people"] == 1 else " people"),
                                    hk("week_followup_days", num(cur["outbound_distinct_days"])) + (" day" if cur["outbound_distinct_days"] == 1 else " days")))
    rows.append(("Follow-ups we made", sub, "touches_outbound", T["touches_outbound"], None))
    rows.append(("Replies we received", "", "replies_inbound", T["replies_inbound"], None))
    rows.append(("Offers", "", "offers", T["offers"], None))
    if m.online:
        rows.append(("Online views", small(esc(join_and(m.online.get("portals") or []))), "online_views", T.get("online_views"),
                     ("online_saves", "online_saves", "saved") if T.get("online_saves") is not None else None))
    return rows


def contact_line(m):
    """The one line under the table: 'We contacted 60 of 62 people. 55 answered. 5 still waiting.'"""
    T = m.T
    nd, nc, nr, nw = T["contacts"], T["contacted"], T["replied"], T["awaiting_reply"]
    gold = lambda t: '<b style="color:%s">%s</b>' % (P["gold"], t)
    if not nd:
        return ("Nobody has toured, asked about the home or asked for the disclosure package yet, so there is no one to follow up with."
                if not m.via else "The only people on the log so far are buyers who got the disclosure package from their own agent.")
    vh = T["contacted_through_host"]
    ppl = "person" if nd == 1 else "people"
    if vh:
        # someone reached only through a host is not counted as contacted directly, and the line says so in full
        s = "We contacted %s of %s %s directly and %s through the open house host." % (
            gold(num(nc - vh)), gold(hk("contacts", num(nd))), ppl, gold(hk("through_host", num(vh))))
    else:
        s = "We contacted %s of %s %s." % (gold(hk("contacted", num(nc))), gold(hk("contacts", num(nd))), ppl)
    s += " %s answered. %s still waiting." % (gold(hk("answered", num(nr))), gold(hk("waiting", num(nw))))
    return s


def s_numbers(m):
    cur, prev, T = m.cur, m.prev, m.T
    rows = []

    def second(scope, src, key, word):
        """'1 opened' under a number, or the honest empty state for a week that could not be checked."""
        if src is None or key not in src:
            return ""
        v = src.get(key)
        return '<div style="%s;color:%s">%s</div>' % (fz(SIZE["micro"], 1.3), P["grey"], hk("%s:%s" % (scope, key), "%s %s" % (num(v), word) if v is not None else "not checked"))
    for label, sub, key, total, extra in number_rows(m):
        a_txt, a = week_val(m, cur, key)
        b_txt, b = week_val(m, prev, key)
        sf = zebra(len(rows))
        tot = num(total) if total is not None else ("none held" if (key == "open_house_groups" and not m.oh) else
                                                    "no count" if key == "open_house_groups" else "not recorded")
        x2 = (second("week", cur, extra[0], extra[2]), second("last", prev, extra[0], extra[2]), second("total", T, extra[1], extra[2])) if extra else ("", "", "")
        rows.append("<tr%s>%s%s%s%s</tr>" % (
            mark("row", key),
            c(esc(label) + sub, sf, pad="9px 6px 9px 10px", th=True, scope="row", va="middle"),
            c('<div style="%s">%s</div>%s' % (hf(22, 800, 1.1) if a is not None else fz(SIZE["sub"], 1.3, 700), a_txt, x2[0]), sf, w="21%", al="center", pad="8px 2px"),
            c(b_txt + x2[1], sf, w="19%", al="center", pad="9px 2px", st="" if b is not None else "font-size:%dpx" % SIZE["sub"]),
            c("<b>%s</b>%s" % (tot, x2[2]), sf, w="22%", al="center", pad="9px 4px 9px 2px", st="" if total is not None else "font-size:%dpx" % SIZE["sub"])))
    hdr = "<tr>%s%s%s%s</tr>" % (gth("&nbsp;", pad="8px 6px 8px 10px"), gth("This<br>week", al="center", pad="8px 2px", at=mark("col", "this")),
                               gth("Last<br>week", al="center", pad="8px 2px", at=mark("col", "last")),
                               gth("Since<br>we listed", al="center", pad="8px 4px 8px 2px", at=mark("col", "total")))
    s = bar("The numbers")
    s += sheet(table(hdr + "".join(rows), SIZE["text"], 1.3, data=True, name="scorecard"), top=10)
    # the one line under the table, as a black callout with the numbers in gold
    line = '<div style="%s;color:%s">%s</div>' % (fz(SIZE["body"], 1.45, 700), P["on_dark"], contact_line(m))
    if T["not_yet_contacted"]:
        k0 = T["not_yet_contacted"]
        line += '<div style="%s;padding-top:4px">%s %s not been reached yet.</div>' % (
            fz(SIZE["sub"], 1.4, None, P["on_dark_soft"]), hk("not_yet_contacted", num(k0)), "person has" if k0 == 1 else "people have")
    s += card(line, sf="dark", pad="13px 14px 13px", top=10, border=P["ink"], at=mark("section", "contact_line"))
    notes = []
    if m.track.get("keybox_showings"):
        notes.append("Showings count key-box showings (%s since we listed) and tours agents told us about (%s)."
                     % (hk("total:keybox_showings", num(T["keybox_showings"])), hk("total:agent_reported_tours", num(T["agent_reported_tours"]))))
    else:
        notes.append("Showings are the tours agents told us about. This listing has no key-box record.")
    notes.append("A question or a cancelled request is an inquiry, not a showing.")
    blind = [w["n"] for w in m.W if w.get("disclosure_opened") is None]
    if m.track.get("disclosure_opened") and blind:
        notes.append("Package opens in week%s %s could not be checked, so that count may be low." % ("" if len(blind) == 1 else "s", join_and(["%d" % k for k in blind])))
    s += para(" ".join(notes), SIZE["sub"], top=8, color=P["grey"])
    return sec(keep(s), top=22, name="numbers")


def week_groups(m, key="weeks"):
    """Weeks for the per-week chart (key "weeks") and table (key "table_weeks"): [(regime, [group])] where a group
    is a list of weeks. Every week is its own group until the email runs out of room (see fit.FIT_LEVELS); then
    weeks older than the latest N are shown in blocks of four inside their list price band. The link copy always
    lists every week."""
    n = None if m.link else OPT["fit"][key]
    keep_ = set(w["n"] for w in (m.W[-n:] if n else m.W))
    out = []
    for r in m.regimes:
        groups, old = [], [w for w in r["weeks"] if w["n"] not in keep_]
        for i in range(0, len(old), 4):
            groups.append(old[i:i + 4])
        groups += [[w] for w in r["weeks"] if w["n"] in keep_]
        out.append((r, groups))
    return out


CHART_SERIES = [("Showings", "showings", "showing", "showings"),
                ("Packages", "disclosure_contacts_new", "package", "packages")]


def s_charts(m):
    """Showings by week and disclosure packages by week, for every week since listing. Quiet weeks keep their
    row, this week is shaded, and each value sits beside its bar."""
    W, cur, T = m.W, m.cur, m.T
    sr = CHART_SERIES
    val = lambda w, i: w.get(sr[i][1]) or 0
    cnt = lambda k, i: n_(k, sr[i][2], sr[i][3])
    mx = max([val(w, 0) for w in W] + [val(w, 1) for w in W] + [1])        # one scale for both columns
    best = max(W, key=lambda w: val(w, 0))
    if val(best, 0) == 0:
        lede = "No showings have been logged yet."
    elif best["n"] == cur["n"]:
        lede = "This week had the most showings so far: %d." % val(best, 0)
    else:
        lede = "Week %d had the most showings: %d. This week had %s." % (best["n"], val(best, 0), "none" if val(cur, 0) == 0 else "%d" % val(cur, 0))
    # label, then a number and a bar for each column. The two bar tracks are the same width, so one scale holds.
    lw, series = 34, [(8, 25), (8, 25)]
    ths = "font-size:12px;letter-spacing:.04em;text-transform:uppercase"
    hdr = "<tr>%s%s%s</tr>" % (gth("Week of", pad="7px 4px 7px 6px", st=ths, at=mark("col", "LABEL")),
                               c(sr[0][0], "gold", span=2, pad="7px 4px 7px 8px", va="bottom", th=True, st=ths, at=mark("col", sr[0][1])),
                               c(sr[1][0], "gold", span=2, pad="7px 4px 7px 8px", va="bottom", th=True, st=ths, at=mark("col", sr[1][1])))
    rows = []
    grouped = False
    for ri, (r, groups) in enumerate(week_groups(m)):
        if ri:
            when = (DOT + wmd(r["change_date"]).replace(" ", "&nbsp;")) if r["change_date"] else ""
            rows.append(("note", "<b>Price changed to %s%s</b>" % (money(r["price"]), when), dict(sf="dark", fg=P["gold"], pad="6px 8px")))
        for ws in groups:
            off = sum(w.get("offers") or 0 for w in ws)
            if len(ws) > 1:
                grouped = True
                rows.append(("note", "Weeks %d to %d, from %s: <b>%s</b>, <b>%s</b>" % (
                    ws[0]["n"], ws[-1]["n"], md(ws[0]["start"]), cnt(sum(val(w, 0) for w in ws), 0), cnt(sum(val(w, 1) for w in ws), 1)), dict(sf="cream")))
            else:
                w = ws[0]
                is_cur = w["n"] == cur["n"]
                col = P["gold"] if is_cur else P["gold_dark"]
                rows.append(("bar", "%d%s%s" % (w["n"], DOT, md(w["start"])), [(val(w, 0), mx, col), (val(w, 1), mx, col)],
                             dict(sf="tint" if is_cur else "card", bold=is_cur, nowrap=True, at=mark("row", w["n"]))))
            if off:
                rows.append(("note", "<b>%s came in %s</b>" % (cap1(n_(off, "offer")), "that week" if len(ws) == 1 else "those weeks"),
                             dict(pad="0 6px 5px")))
    body = chart(rows, lw, series, head_row=hdr, name="chart")
    s = h3("Showings and disclosure packages, week by week", lede, top=0)
    s += sheet(body, top=10)
    notes = ["The shaded row is this week."]
    if pd(W[0]["start"]) < pd(m.L["list_date"]):
        notes.append("Week 1 was a partial week: the home went on the market on %s." % wmd(m.L["list_date"]))
    dated = sum(val(w, 1) for w in W)
    if T["disclosure_contacts"] != dated:
        kk = T["disclosure_contacts"] - dated
        notes.append("%d more %s on the package list with no date on file." % (kk, "person is" if kk == 1 else "people are"))
    if T.get("tours_undated"):
        notes.append("%s no date on file and %s not in a week." % (cap1(n_(T["tours_undated"], "showing has", "showings have")), "is" if T["tours_undated"] == 1 else "are"))
    if grouped:
        notes.append("Older weeks are shown in blocks of four to keep this email short. The complete record shows each one.")
    s += para(" ".join(notes), SIZE["sub"], top=8, color=P["grey"])
    out = sec(keep(s), top=24, name="weekly_chart")
    if m.online:
        out += s_views_chart(m)
    return out


def s_views_chart(m):
    """Online views by week, when they are recorded. A week with no figure says so and draws no bar."""
    W, cur, T = m.W, m.cur, m.T
    got = [w["online_views"] for w in W if w.get("online_views") is not None]
    if not got:
        return ""
    mx = max(got + [1])
    ths = "font-size:12px;letter-spacing:.04em;text-transform:uppercase"
    hdr = "<tr>%s%s</tr>" % (gth("Week of", pad="7px 4px 7px 6px", st=ths, at=mark("col", "LABEL")),
                             c("Views", "gold", span=2, pad="7px 4px 7px 8px", va="bottom", th=True, st=ths, at=mark("col", "online_views")))
    rows = []
    for w in W:
        is_cur = w["n"] == cur["n"]
        v = w.get("online_views")
        bar_ = (v or 0, mx, P["gold"] if is_cur else P["gold_dark"]) + (() if v is not None else ("not recorded",))
        rows.append(("bar", "%d%s%s" % (w["n"], DOT, md(w["start"])), [bar_],
                     dict(sf="tint" if is_cur else "card", bold=is_cur, nowrap=True, at=mark("row", w["n"]))))
    portals = join_and(m.online.get("portals") or [])
    lede = "%s since we listed, as counted by %s." % (n_(T["online_views"], "view"), esc(portals) or "the listing sites")
    s = h3("Online views, week by week", lede, top=0) + sheet(chart(rows, 34, [(22, 44)], head_row=hdr, name="chart_views"), top=10)
    notes = ["Each site counts views its own way, so these are a trend, not an exact count."]
    if m.online.get("as_of"):
        notes.append("Read on %s." % md(m.online["as_of"]))
    s += para(" ".join(notes), SIZE["sub"], top=8, color=P["grey"])
    return sec(keep(s), top=22, name="views_chart")
