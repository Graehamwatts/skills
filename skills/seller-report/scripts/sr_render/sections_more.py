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
    ch = h.get("change")
    when = (" %s %s" % ("by" if h.get("change_date_approximate") else "on", md(h["change_date"]))) if h.get("change_date") else ""
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
    return "No change."


def nearby_order(nb):
    """[(index in the ledger, home)]: the homes that changed first, then the rest, each in the ledger's order."""
    homes = list(enumerate(nb["homes"]))
    return [x for x in homes if x[1].get("change") in NEARBY_CHANGED] + [x for x in homes if x[1].get("change") not in NEARBY_CHANGED]


def s_nearby(m):
    """Optional: the short watch list of similar homes nearby. What changed this week comes first, then the whole
    list as one compact table. Public street addresses are printed in this one section, as in a market analysis."""
    nb = m.nearby
    if not nb or not nb.get("homes") or not OPT.get("nearby", True):
        return ""
    order = nearby_order(nb)
    moved = [(i, h) for i, h in order if h.get("change") in NEARBY_CHANGED]
    n, k = len(order), len(moved)
    word = "home" if n == 1 else "homes"
    if moved:
        title = "%s of the %s %s we are watching changed" % (hk("nearby_changed", num(k)), hk("nearby_homes", num(n)), word)
    else:
        title = "No change among the %s %s we are watching" % (hk("nearby_homes", num(n)), word)
    lede = esc(nb["scope"]).rstrip(".") + "."
    lede += " Checked %s." % md(nb["as_of"]) if nb.get("checked_for_this_issue") else " Last checked %s, not checked again for this report." % md(nb["as_of"])
    s = head("Similar homes nearby", title, lede)
    if moved:
        rows = "".join("<tr%s>%s</tr>" % (mark("row", "change:%d" % i), c('<b>%s</b><br>%s' % (esc(h["address"]), nearby_line(h)), "card", pad="9px 0", line=j > 0))
                       for j, (i, h) in enumerate(moved))
        s += keep(subhead("What changed", top=14) + card(table(rows, SIZE["text"], 1.45, name="nearby_changes"), pad="2px 14px", top=6))
    if not m.link and OPT["fit"]["extras"] != "full":
        # a long email: what changed stays, and the homes that did not change are said in one sentence
        still = [h for _, h in order if h.get("change") not in NEARBY_CHANGED]
        if still:
            by = [(len([h for h in still if h.get("status") == st]), NEARBY_STATUS[st].lower()) for st in C.NEARBY_STATUSES]
            said = join_and(["%d %s" % (k_, word_) for k_, word_ in by if k_])
            if moved:
                line = "The other %s did not change: %s." % (n_(len(still), "home"), said)
            else:
                line = "Where they stand: %s." % said
            s += para(line + " Each one is in the complete record.", SIZE["text"], top=10, at=mark("row", "unchanged"))
        if nb.get("source"):
            s += para("Source: %s." % esc(nb["source"]).rstrip("."), SIZE["sub"], top=8, color=P["grey"])
        return sec(s, name="nearby")
    hs = "font-size:12px;letter-spacing:.04em;text-transform:uppercase"
    hdr = "<tr>%s%s%s%s</tr>" % (gth("Home", w="38%", pad="7px 4px 7px 8px", st=hs, at=mark("col", "LABEL")),
                                 gth("Status", w="21%", pad="7px 4px", st=hs, at=mark("col", "status")),
                                 gth("Price", w="27%", al="right", pad="7px 4px", st=hs, at=mark("col", "price")),
                                 gth("Days", w="14%", al="right", pad="7px 8px 7px 2px", st=hs, at=mark("col", "days")))
    rows = hdr
    for j, (i, h) in enumerate(order):
        sf = zebra(j)
        spec = []
        if h.get("beds") is not None:
            spec.append("%s bed" % num(h["beds"]))
        if h.get("baths") is not None:
            spec.append("%s bath" % num(h["baths"]))
        if h.get("sqft"):
            spec.append("%s sq ft" % num(h["sqft"]))
        price = h.get("sold_price") if h.get("status") == "sold" else h.get("list_price")
        home = "<b>%s</b>%s" % (esc(h["address"]), ('<br><span style="font-size:%dpx;color:%s">%s</span>' % (SIZE["micro"], P["grey"], ", ".join(spec))) if spec else "")
        rows += "<tr%s>%s%s%s%s</tr>" % (
            mark("row", i),
            c(home, sf, pad="8px 4px 8px 8px", th=True, scope="row", va="top", st="font-weight:400"),
            c(esc(NEARBY_STATUS.get(h.get("status"), "Not recorded")), sf, pad="8px 4px", va="top", st="font-weight:700"),
            c(money(price) if price is not None else "not recorded", sf, al="right", pad="8px 4px", va="top",
              st="white-space:nowrap" if price is not None else "font-size:%dpx" % SIZE["micro"]),
            c(num(h["days_on_market"]) if h.get("days_on_market") is not None else "&nbsp;", sf, al="right", pad="8px 8px 8px 2px", va="top"))
    s += sheet(table(rows, SIZE["sub"], 1.4, data=True, name="nearby"), top=12 if moved else 10)
    notes = ["Price is the list price, or the sale price for a home that sold.",
             "Days run from the list date to an accepted offer, a sale or the day the home left the market, and to the day we checked for a home still for sale."]
    if any(h.get("days_on_market") is None for _, h in order):
        notes.append("A blank means we have no confirmed day count for that home.")
    if nb.get("source"):
        notes.append("Source: %s." % esc(nb["source"]).rstrip("."))
    s += para(" ".join(notes), SIZE["sub"], top=8, color=P["grey"])
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
    """(running and checked for this issue, switched on but last checked earlier, prepared, everything else)."""
    mk = m.d.get("marketing") or {}
    chs = mk.get("channels") or []
    fresh = [ch for ch in chs if C.channel_is_running(ch, m.R)]
    stale = [ch for ch in chs if ch.get("status") == "on" and ch not in fresh]
    nxt = [ch for ch in chs if ch.get("status") == "prepared"]
    off = [ch for ch in chs if ch.get("status") not in ("on", "prepared")]
    return fresh, stale, nxt, off


def s_marketing(m):
    """Optional and short: online ads and the rest of the marketing, in the status words the team uses: switched
    on, scheduled to end, prepared, on hold, not launched. "Running" is said only of a channel that is on and was
    checked for this issue. No ad spend is printed. The section is left out unless a channel is on or something
    was checked for this issue."""
    mk = m.d.get("marketing")
    if not mk or not mk.get("channels") or not OPT.get("marketing", True) or not C.marketing_recorded(mk, m.R):
        return ""
    fresh, stale, nxt, off = marketing_split(m)
    bits = []
    if fresh:
        bits.append("%s running" % n_(len(fresh), "channel"))
    for dte in sorted(set(ch["checked"] for ch in stale)):
        bits.append("%d switched on and last checked %s" % (len([ch for ch in stale if ch["checked"] == dte]), md(dte)))
    if nxt:
        bits.append("%d prepared" % len(nxt))
    for key, word in (("on_hold", "on hold"), ("not_launched", "not launched"), ("ended", "ended")):
        k = len([ch for ch in off if ch.get("status") == key])
        if k:
            bits.append("%d %s" % (k, word))
    s = head("Online ads and marketing", cap1(", ".join(bits)))
    short = not m.link and OPT["fit"]["extras"] != "full"       # a long email: prepared channels join the one sentence
    shown = fresh + stale + ([] if short else nxt) + (off if m.link else [])       # the email names the channels that are off in one sentence
    rows = ""
    for i, ch in enumerate(shown):
        st = ch.get("status")
        if ch in fresh:
            lab, kind = C.MARKETING_RUNNING, "good"
        else:
            lab, kind = MARKETING_WORD.get(st, cap1(st or "")), {"on": "hold", "prepared": "lean"}.get(st, "hold")
        when = []
        if ch not in fresh:
            when.append("Last checked %s." % md(ch["checked"]))
        if ch.get("ends_on"):
            ahead = pd(ch["ends_on"]) >= pd(m.R["report_date"])
            when.append("%s %s." % (C.MARKETING_ENDS if ahead else "Was " + low1(C.MARKETING_ENDS), md(ch["ends_on"])))
        asof = ('<div style="%s">%s</div>' % (fz(SIZE["sub"], 1.4, 700, P["grey"]), " ".join(when))) if when else ""
        # the whole detail is printed: the later sentences are where the caveats live
        rows += "<tr%s>%s</tr>" % (mark("row", "channel:%d" % mk["channels"].index(ch)), c(
            '<b style="color:%s">%s</b>&nbsp; %s%s%s' % (P["ink"], esc(ch["channel"]), chip(lab, kind, inline=True), asof,
                                                         para(safe(m, ch.get("detail") or ""), SIZE["text"], top=3)),
            "card", pad="10px 0", line=i > 0, va="top"))
    if rows:
        s = keep(s + card(table(rows, SIZE["text"], name="marketing"), pad="4px 14px", top=10))
    folded = (nxt if short else []) + ([] if m.link else off)
    if folded:
        said = []
        for key, word in (("prepared", "Prepared"), ("on_hold", "On hold"), ("not_launched", "Not launched"), ("ended", "Ended")):
            names = [esc(ch["channel"]) for ch in folded if ch.get("status") == key]
            if names:
                said.append("%s: %s." % (word, join_and(names)))
        s += para(" ".join(said), SIZE["small"], top=8, color=P["grey"])
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
