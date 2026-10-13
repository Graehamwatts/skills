# -*- coding: utf-8 -*-
"""sr_render.sections_more: the optional sections (similar homes nearby, time on the market against recent sales,
online ads and marketing) and next week."""
import datetime
import re

import sr_contract as C
from .text import *        # noqa: F401,F403


NEARBY_CHANGED = ("new_listing", "price_change", "went_pending", "sold", "withdrawn", "back_on_market")


def nearby_line(h):
    """What one watched home did this week, or where it stands when nothing changed."""
    ch, when = h.get("change"), (" on %s" % md(h["change_date"])) if h.get("change_date") else ""
    dom = (" after %s on the market" % n_(h["days_on_market"], "day")) if h.get("days_on_market") is not None else ""
    lp = money(h["list_price"]) if h.get("list_price") is not None else None
    if ch == "new_listing":
        return "New listing%s%s." % (when, (" at %s" % lp) if lp else "")
    if ch == "price_change":
        return "Price changed%s: %s to %s." % (when, money(h["price_before"]), lp)
    if ch == "went_pending":
        return "Went pending%s%s%s." % (when, dom, (". Listed at %s" % lp) if lp else "")
    if ch == "sold":
        return "Sold%s for %s%s%s." % (when, money(h["sold_price"]), dom, (". Listed at %s" % lp) if lp else "")
    if ch == "withdrawn":
        return "Taken off the market%s%s." % (when, dom)
    if ch == "back_on_market":
        return "Back on the market%s%s." % (when, (" at %s" % lp) if lp else "")
    st = h.get("status")
    if st == "sold":
        return "No change. Sold for %s%s." % (money(h["sold_price"]), dom)
    day = (", day %d" % h["days_on_market"]) if h.get("days_on_market") is not None else ""
    return "No change. %s%s%s." % (NEARBY_STATUS.get(st, cap1(st or "")), (" at %s" % lp) if lp else "", day)


def s_nearby(m):
    """Optional: the short watch list of similar homes nearby and what changed this week. Public street addresses
    are printed in this one section, as in a market analysis."""
    nb = m.nearby
    if not nb or not nb.get("homes") or not OPT.get("nearby", True):
        return ""
    homes = nb["homes"]
    moved = [h for h in homes if h.get("change") in NEARBY_CHANGED]
    title = ("%s of the %d homes we are watching changed" % (num(len(moved)), len(homes))) if moved else "No change among the %s we are watching" % n_(len(homes), "home")
    lede = esc(nb["scope"]).rstrip(".") + "."
    lede += " Checked %s." % md(nb["as_of"]) if nb.get("checked_for_this_issue") else " Last checked %s, not checked again for this report." % md(nb["as_of"])
    s = head("Similar homes nearby", title, lede)
    rows = ""
    for i, h in enumerate(moved + [h for h in homes if h not in moved]):
        spec = []
        if h.get("beds") is not None:
            spec.append("%s bed" % num(h["beds"]))
        if h.get("baths") is not None:
            spec.append("%s bath" % num(h["baths"]))
        if h.get("sqft"):
            spec.append("%s sq ft" % num(h["sqft"]))
        kind = {"active": "good", "pending": "lean", "sold": "offer", "withdrawn": "hold"}.get(h.get("status"), "hold")
        top = table("<tr>%s%s</tr>" % (
            c('<b style="color:%s">%s</b>%s' % (P["ink"], esc(h["address"]),
                                               ('<br><span style="font-size:%dpx;color:%s">%s</span>' % (SIZE["sub"], P["grey"], ", ".join(spec))) if spec else ""),
              "card", va="top"),
            c(chip(NEARBY_STATUS.get(h.get("status"), "Status not recorded"), kind), "card", al="right", va="top", st="white-space:nowrap;padding-left:8px")))
        rows += "<tr>%s</tr>" % c(top + para(nearby_line(h), SIZE["small"], top=3, color=P["ink"] if h in moved else P["grey"]),
                                  "card", pad="10px 0", line=i > 0)
    s = keep(s + card(table(rows, SIZE["text"]), pad="4px 14px", top=10))
    if nb.get("source"):
        s += para("Source: %s." % esc(nb["source"]).rstrip("."), SIZE["sub"], top=8, color=P["grey"])
    return sec(s, name="nearby")


def s_market(m):
    """Optional and short: this home's days on the market against comparable sales. Every number names its window."""
    mk = m.d.get("market")
    if not mk or not OPT.get("market", True):
        return ""
    sub = mk.get("subject_on_report_date") or {}
    dtc = mk.get("days_to_contract") or {}
    used = [x for x in (mk.get("sales") or []) if x.get("used_in_average") and x.get("days_to_contract") is not None]
    day = sub.get("days_on_market") or m.R["days_on_market"]
    # The lede is written here from the numbers validate_ledger has just recomputed, so it can never lag the page.
    by, of = sub.get("sales_under_contract_by_that_day"), sub.get("of_sales")
    lede = "%s is day %d on the market." % (md(sub.get("date") or m.R["report_date"]), day)
    if by is not None and of:
        lede += " %s of the %d comparable sales %s under contract by that day." % (num(by) if by else "None", of, "was" if by == 1 else "were")
    s = head("Time on the market", "This home against recent sales", lede)
    # this home has no accepted offer, so its row says what it is: days so far, and its status
    st = (m.L.get("status") or "").lower()
    items = [("This home: day %d%s" % (day, (", still %s" % esc(st)) if st == "active" else ((", " + esc(st)) if st else "")), day, True)]
    for x in sorted(used, key=lambda x: x["days_to_contract"]):
        bb = (x.get("beds_baths") or "").split("/")
        lab = "Sold %s %d" % (C.MONTHS[pd(x["sold_date"]).month - 1], pd(x["sold_date"]).year)
        if bb and bb[0]:
            lab += ", %s bed" % bb[0]
        items.append((lab, x["days_to_contract"], False))
    mx = max(v for _, v, _ in items) or 1
    rows = [("bar", lab, [(v, mx, P["gold"] if me else P["gold_dark"])], dict(sf="tint" if me else "card", bold=me)) for lab, v, me in items]
    s = keep(s + card(kicker("Days from listing to an accepted offer") + sp(6) + chart(rows, 50, [(11, 39)]), pad="14px 10px 10px", top=10))
    small = []
    if dtc.get("average") is not None:
        small.append("Average %d days, median %d." % (dtc["average"], dtc["median"]))
    if mk.get("scope"):
        small.append(esc(mk["scope"]).rstrip(".") + ".")
    smp = mk.get("sample") or {}
    if smp.get("excluded") and smp.get("exclusion_reason"):
        small.append("Left out: " + esc(low1(smp["exclusion_reason"])).rstrip(".") + ".")
    if mk.get("as_of"):
        small.append("Sales list as of %s." % md(mk["as_of"]))
    s += para(" ".join(small), SIZE["small"], top=8, color=P["grey"])
    return sec(s, name="market")


def marketing_split(m):
    """(running and checked for this issue, on but last checked earlier, prepared, everything else)."""
    mk = m.d.get("marketing") or {}
    chs = mk.get("channels") or []
    fresh = [ch for ch in chs if C.channel_is_running(ch, m.R)]
    stale = [ch for ch in chs if ch.get("status") == "on" and ch not in fresh]
    nxt = [ch for ch in chs if ch.get("status") == "prepared"]
    off = [ch for ch in chs if ch.get("status") not in ("on", "prepared")]
    return fresh, stale, nxt, off


def s_marketing(m):
    """Optional and short: what is running, what was last checked earlier, what is next. A channel is called
    running only when it is on and was checked for this issue."""
    mk = m.d.get("marketing")
    if not mk or not mk.get("channels") or not OPT.get("marketing", True):
        return ""
    fresh, stale, nxt, _ = marketing_split(m)
    if not fresh and not stale and not nxt:
        return ""
    old = lambda ch: pd(ch["checked"]) < pd(m.R["week_end"])
    bits = []
    if fresh:
        bits.append("%s confirmed running for this report" % n_(len(fresh), "channel"))
    for dte in sorted(set(ch["checked"] for ch in stale)):
        bits.append("%d last checked %s" % (len([ch for ch in stale if ch["checked"] == dte]), md(dte)))
    if nxt:
        bits.append("%d next" % len(nxt))
    s = head("Online ads and marketing", cap1(", ".join(bits)))
    rows = ""
    for i, ch in enumerate(fresh + stale + nxt):
        if ch in nxt:
            lab, kind = "Next", "lean"
        elif ch in stale:
            lab, kind = "Last checked %s" % md(ch["checked"]), "hold"
        else:
            lab, kind = "Running", "good"
        # a queued channel that was not looked at again gets its date in words; the running ones carry it in the chip
        asof = ('<div style="%s">As of %s</div>' % (fz(SIZE["sub"], 1.4, 700, P["grey"]), md(ch["checked"]))) if (ch in nxt and old(ch)) else ""
        # the whole detail is printed: the later sentences are where the caveats live
        rows += "<tr>%s</tr>" % c(
            '<b style="color:%s">%s</b>&nbsp; %s%s%s' % (P["ink"], esc(ch["channel"]), chip(lab, kind), asof,
                                                         para(safe(m, ch.get("detail") or ""), SIZE["text"], top=3)),
            "card", pad="10px 0", line=i > 0, va="top")
    s = keep(s + card(table(rows, SIZE["text"]), pad="4px 14px", top=10))
    return sec(s, name="marketing")


def next_items(m):
    """The next-week list. In the link copy, lines about people who may be weighing an offer fold into one
    line with no names, and no line says anything about an offer."""
    items = list(m.d.get("next_week") or [])
    if not m.link:
        return [safe(m, it) for it in items]
    hot = [x["name_short"] for x in m.contacts if x["id"] in m.offer_people] + list(m.masked_names)
    out, folded, at = [], 0, None
    for it in items:
        if any(nm and nm in it for nm in hot):
            folded += 1
            at = len(out) if at is None else at
            continue
        kept = scrub_offers(m, it, wide=True)
        if kept.strip():
            out.append(safe(m, kept))
    if folded:
        out.insert(at, "Check back with %s on where %s. %s in the email copy." % (
            n_(folded, "agent"), "the buyer stands" if folded == 1 else "their buyers stand", "The name is" if folded == 1 else "Their names are"))
    return out


def s_next(m):
    ID = m.ID
    items = next_items(m)
    s = head("Next week", "What we are doing next week" if items else None)
    if items:
        rows = "".join("<tr>%s%s</tr>" % (
            c("<b>%d</b>" % (i + 1), "card", w=26, pad="10px 0", line=i > 0, va="top"),
            c(it, "card", pad="10px 0", line=i > 0, va="top")) for i, it in enumerate(items))
        s = keep(s + card(table(rows, SIZE["text"], 1.5), pad="4px 14px", top=10))
    nxt = pd(m.R["report_date"]) + datetime.timedelta(days=7)
    line = "Your next report arrives %s." % long_day(nxt).rsplit(",", 1)[0]
    if not m.link:
        line += " To go over anything before then, reply to this email or call or text me."
    s += para(line, SIZE["body"], top=14)
    if not m.link:
        tel = re.sub(r"[^0-9]", "", ID["phone"])
        s += sp(14) + button("tel:+1" + tel, "CALL OR TEXT %s%s<span style=\"white-space:nowrap\">%s</span>" % (
            esc(ID["name"].split()[0]).upper(), DOT, esc(ID["phone"])))
    return sec(s, bot=6, name="next_week")
