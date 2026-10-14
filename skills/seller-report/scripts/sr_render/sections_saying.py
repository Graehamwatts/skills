# -*- coding: utf-8 -*-
"""sr_render.sections_saying: what people are saying.

The summary on top carries one ranked tally of the main points since listing, each as a plain count out of
the people who gave feedback. Price is always three rows, even at zero. The record half keeps every price
comment and the plain table of the record at each list price.

Feedback only: these sections state counts. They never suggest a price, and they add no sentence about what
it means when someone did not bring up price.
"""
import sr_contract as C
from .text import *        # noqa: F401,F403


def who_words(m, n):
    """'55 agents and buyers', '1 agent', '4 people' (when an open house visitor is among them)."""
    kinds = set(x.get("kind") for x in m.fed)
    if kinds <= set(["agent"]):
        return n_(n, "agent")
    if "open_house_visitor" in kinds:
        return n_(n, "person", "people")
    return "%s agents and buyers" % num(n) if n != 1 else "1 person"


def week_price_line(m):
    """What this week's conversations added on price, as plain counts."""
    cur = m.cur
    conv, hi, fair = cur.get("conversations_with_feedback") or 0, cur.get("price_too_high") or 0, cur.get("price_fair_or_positive") or 0
    if not conv:
        return "No conversations with feedback this week."
    if not (hi + fair):
        return "This week: %s. Nobody gave a view on price." % n_(conv, "conversation")
    rest = conv - hi - fair
    said = join_and([("%d said the price is too high" % hi) if hi else "", ("%d said it is fair or good" % fair) if fair else "",
                     ("%d gave no view on price" % rest) if rest > 0 else ""])
    return "This week: %s. %s." % (n_(conv, "conversation"), cap1(said))


def host_remarks_line(m, rem):
    """'Since we listed, open house hosts have also passed on 2 remarks about price, none of them this week (the
    latest was Aug 9).' The line sits right after the sentence about this week's conversations, so it always
    says how many of the hosts' remarks fall in the report week."""
    n = len(rem)
    days = sorted(pd(r["date"]) for r in rem if r.get("date"))
    s = "Since we listed, open house hosts have also passed on %s about price" % n_(n, "remark")
    if len(days) != n:
        return s + "."                              # a remark with no date on file: nothing is said about the week
    k = len([d for d in days if m.WS <= d <= m.WE])
    if n == 1:
        return s + (", and it came this week." if k else ", on %s, before this week." % md(days[-1]))
    if not k:
        return s + ", none of them this week (the latest was %s)." % md(days[-1])
    return s + ", %s of them this week." % ("all" if k == n else "%d" % k)


def s_saying(m):
    """What people are saying: the ranked tally, the last part of the summary on top, right above "The details"."""
    PT, TT, LT, K = m.PT, m.TT, m.LT, OPT["fit"]
    den = PT["people_with_feedback"]
    unit = "person" if den == 1 else "people"
    if den:
        title = "What %s %s told us since we listed" % (who_words(m, den), "has" if den == 1 else "have")
        conv = PT.get("conversations_with_feedback")
        lede = "Every count is out of the %s who gave us feedback%s. A person can be counted under more than one point." % (
            "1 person" if den == 1 else "%s people" % num(den), (" (%s)" % n_(conv, "conversation")) if (conv and conv != den) else "")
    else:
        title = "Nobody has given us feedback yet"
        lede = "The rows below fill in as agents and buyers tell us what they think."
    s = head("What people are saying", title, lede)

    # 1. price: always three rows, plain counts, even at zero
    hooks = {"too_high": "price_too_high", "fair_or_positive": "price_fair", "not_raised": "price_not_raised"}
    rows = "".join(point_row(lab, PT[key], den, first=(i == 0), unit=unit, hook=hooks[key]) for i, (key, lab) in enumerate(PRICE_ROWS))
    price = kicker("Price", P["ink"]) + sp(8) + table(rows, SIZE["text"], 1.4)
    notes = [week_price_line(m)] if den else []
    if PT.get("price_asked_recorded"):
        notes.append("We asked about price directly with %s of the %d people where that was noted." % (
            hk("price_asked", num(PT["asked_directly"])), PT["price_asked_recorded"]))
    rem = PT.get("open_house_price_remarks") or []
    if rem:
        where = "listed in the record below" if (m.link or K["price_comments"]) else "in the complete record"
        notes.append("%s %s %s and %s not in these counts."
                     % (host_remarks_line(m, rem), "It is" if len(rem) == 1 else "They are", where, "is" if len(rem) == 1 else "are"))
    if notes:
        price += para(" ".join(notes), SIZE["small"], top=10, color=P["grey"])
    groups = [price]

    # 2. the other points people raised, ranked by people
    hidden = set(t["key"] for t in m.d["themes_vocabulary"]["themes"] if t.get("hide_in_link_copy")) if m.link else set()
    points = [r for r in TT.get("rows") or [] if r["key"] not in hidden]
    if points:
        cap = len(points) if m.link else K["points"]
        top, rest = points[:cap], points[cap:]
        if len(rest) == 1:                    # one leftover row costs as much as the sentence that would replace it
            top, rest = points, []
        new = lambda r: ("%d new this week" % r["new_this_week"]) if r.get("new_this_week") else ""
        th = lambda r: "theme:%s" % r["key"] if r["key"] != "other" else "theme:other:%s" % norm(r["label"])
        rows = "".join(point_row(r["label"], r["people"], den, sub=new(r), first=(i == 0), unit=unit, hook=th(r)) for i, r in enumerate(top))
        body = kicker("Other points people raised", P["ink"]) + sp(8) + table(rows, SIZE["text"], 1.4)
        tail = []
        if rest:
            tail.append("Also raised: %s." % ", ".join("%s (%s%s)" % (
                low1(r["label"]), hk(th(r), num(r["people"])), (", %s" % new(r)) if new(r) else "") for r in rest))
        none = TT.get("people_with_no_theme") or 0
        if none and not hidden:
            tail.append("%s raised none of these points." % cap1(n_(none, "person", "people")))
        if tail:
            body += para(" ".join(tail), SIZE["small"], top=10, color=P["grey"])
        groups.append(body)

    # 3. what people liked
    liked = LT.get("rows") or []
    if liked:
        cap = len(liked) if m.link else max(3, K["points"] // 2)
        top, rest = liked[:cap], liked[cap:]
        if len(rest) == 1:
            top, rest = liked, []
        rows = "".join(point_row(r["label"], r["people"], den, first=(i == 0), unit=unit, hook="liked:" + r["key"]) for i, r in enumerate(top))
        body = kicker("What people liked", P["ink"]) + sp(8) + table(rows, SIZE["text"], 1.4)
        tail = "%s named something they liked." % cap1("%d of the %d %s" % (LT["people"], den, unit))
        if rest:
            tail += " Also liked: %s." % ", ".join("%s (%s)" % (low1(r["label"]), hk("liked:" + r["key"], num(r["people"]))) for r in rest)
        body += para(tail, SIZE["small"], top=10, color=P["grey"])
        groups.append(body)
    if OPT.get("keep"):
        s = keep(s + card(groups[0], pad="16px 16px 14px", top=12)) + "".join(card(g, pad="16px 16px 14px", top=10) for g in groups[1:])
    else:
        s += card((sp(16) + rule_line() + sp(14)).join(groups), pad="16px 16px 14px", top=12)
    s += para("These counts are our team's reading of each conversation.", SIZE["small"], top=8, color=P["grey"])
    return sec(s, name="saying")


def approx_words(m):
    """'12 of the 34 showing dates are approximate'."""
    T = m.T
    k = T["tours_approximate_date"]
    return "%d of the %d showing dates %s approximate" % (k, T["showings"], "is" if k == 1 else "are")


def rule_line():
    return ('<table %s width="100%%"><tr><td height="1" bgcolor="%s" style="font-size:0;line-height:0">&nbsp;</td></tr></table>'
            % (TBL, P["line"]))


def by_price(m):
    """True when the record is shown per list price: the price changed, and the weekly table shows it as bands."""
    return len(m.periods) > 1 and len(m.regimes) > 1


def s_price_periods(m):
    """The record at each list price, split by the date of each event. A plain table, no commentary."""
    if not by_price(m):
        return ""
    T, ps = m.T, m.periods
    span = lambda p: md(p["start"]).replace(" ", "&nbsp;") if p["start"] == p["end"] else "%s to<br>%s" % (
        md(p["start"]).replace(" ", "&nbsp;"), md(p["end"]).replace(" ", "&nbsp;"))

    def traffic(p):
        if not p.get("open_house_sessions"):
            return "none held"
        g = p.get("open_house_groups")
        return "no count kept" if g is None else num(g)
    of = lambda k: (lambda p: "%d of %d" % (p[k], p["conversations_with_feedback"]))
    spec = [("Dates", span, False, "SKIP"), ("Days on the market", lambda p: num(p["days"]), False, "days"),
            ("Showings", lambda p: num(p["showings"]), True, "showings"),
            (oh_label(m), traffic, False, "open_house_groups"),
            ("Offers", lambda p: num(p["offers"]), True, "offers"),
            ("Said the price is too high", of("price_too_high"), False, "price_too_high"),
            ("Said the price is fair or good", of("price_fair_or_positive"), False, "price_fair_or_positive")]
    wd = "%d%%" % (56 // len(ps))
    # three list prices or more: tighter cells, so the table still fits a 320 px phone in the link copy's wider font
    tight = len(ps) > 2
    lpad, vpad, hfont = ("8px 4px 8px 6px", "8px 5px 8px 2px", 13) if tight else ("8px 6px 8px 8px", "8px 8px 8px 4px", 14)
    hdr = "<tr>%s%s</tr>" % (gth("&nbsp;", pad=lpad), "".join(
        gth("At<br>%s" % money(p["price"]), w=wd, al="right", pad=vpad, st="font-size:%dpx;line-height:1.3" % hfont, at=mark("col", p["price"])) for p in ps))
    rows = ""
    for i, (label, fn, bold, field) in enumerate(spec):
        sf = zebra(i)
        rows += "<tr%s>%s%s</tr>" % (
            mark("row", field),
            c(label, sf, pad=lpad, th=True, scope="row", st="font-weight:400"),
            "".join(c(("<b>%s</b>" if bold else "%s") % fn(p), sf, al="right", pad=vpad) for p in ps))
    note = "Counted by the date of each showing, open house, offer and conversation."
    if T.get("tours_approximate_date"):
        note += " %s." % cap1(approx_words(m))
    if T.get("tours_undated"):
        note += " %s no date and %s in no column." % (cap1(n_(T["tours_undated"], "showing has", "showings have")), "is" if T["tours_undated"] == 1 else "are")
    nc = T.get("open_house_sessions_without_count")
    if nc:
        note += " %s kept no count." % cap1(n_(nc, "open house session"))
    note += " Price comments are out of the conversations logged at each price."
    return sec(keep(h3("The record at each list price", top=0) +
                    sheet(table(hdr + rows, SIZE["text"], 1.35, data=True, name="periods"), top=10) +
                    para(note, SIZE["small"], top=8, color=P["grey"])), top=26, name="price_periods")


def price_comments(m):
    """Every conversation in which price came up: [(date, person, entry)], oldest first."""
    out = []
    for x in m.direct:
        for e in C.counted_feedback(x, m.WE):
            if e.get("price_reaction") in ("too_high", "fair_or_positive"):
                out.append((e["date"], x, e))
    return sorted(out, key=lambda r: (r[0], r[1]["id"]))


def s_price_record(m):
    """Carried forward: every price comment with the list price at the time, then what hosts passed on."""
    pc = price_comments(m)
    rem = m.PT.get("open_house_price_remarks") or []
    if not pc and not rem:
        return ""
    if not m.link and not OPT["fit"]["price_comments"] and pc:
        wk = sorted(set(m.week_of(d)["n"] for d, _, _ in pc if m.week_of(d)))
        txt = "%s on record%s. Each one, with the list price at the time, is in the complete record." % (
            cap1(n_(len(pc), "price comment is", "price comments are")), (", from week%s %s" % ("" if len(wk) == 1 else "s", join_and(["%d" % k for k in wk]))) if wk else "")
        return sec(h3("Price comments on record", top=0) + para(txt, SIZE["text"], top=6), top=26, name="price_comments")
    s = h3("Every price comment on record", "As reported to our team, oldest first.", top=0)
    if pc:
        rows = ""
        for i, (fd, x, e) in enumerate(pc):
            wk = m.week_of(fd)
            said = "" if x["id"] in m.masked else safe(m, e["text_safe"], x)
            rows += "<tr>%s</tr>" % c(
                '<b style="color:%s">%s%s%s</b> <span style="color:%s">%s%s</span>%s%s' % (
                    P["ink"], ("Week %d%s%s" % (wk["n"], DOT, md(fd))) if wk else md(fd), DOT, dname(m, x), P["grey"], DOT, role(m, x),
                    para(said, SIZE["text"], top=3, color=P["ink"]) if said else "",
                    para("<b>%s.</b> List price at the time: %s." % (PRICE_TAG[e["price_reaction"]], money(m.price_on(fd))), SIZE["small"], top=4)),
                "card", pad="11px 0", line=i > 0)
        s = keep(s + card(table(rows, SIZE["text"]), pad="4px 16px", top=10))
    if rem:
        s += para("<b>At open houses, as reported by the hosts, not in the counts:</b> " +
                  " ".join("%s: %s" % (md(r["date"]), safe(m, r["remark_safe"])) for r in rem) +
                  " Open house visitors are not logged one by one, so these remarks cannot be counted against a total.", SIZE["small"], top=10)
    return sec(s, top=26, name="price_comments")
