# -*- coding: utf-8 -*-
"""sr_render.sections_top: the masthead, this week in brief and the inbox preview line."""
import re

import sr_contract as C
from .text import *        # noqa: F401,F403


def s_masthead(m):
    """The masthead: wordmark, REALTOR and DRE, brokerage line, the report name and number, the photo when there
    is one, then the address and four facts (week covered, day on market, list price, offers to date)."""
    ID, L, R, g = m.ID, m.L, m.R, SIZE["gutter"]
    ink = P["ink"]
    out = []
    realtor = esc(ID["realtor_line"]).upper().replace(chr(0xAE), "&reg;")
    out.append(
        '<tr><td class="g" data-sr-section="masthead" bgcolor="%s" style="padding:20px %dpx 14px;background:%s;color:%s">'
        '<div style="%s;letter-spacing:.2em;color:%s">%s</div>'
        '<div style="%s;letter-spacing:.16em;color:%s;padding-top:6px">%s%sDRE #%s</div>'
        '<div style="%s;padding-top:6px">%s</div></td></tr>'
        % (ink, g, ink, P["on_dark_soft"], hf(SIZE["wordmark"], 800, 1.1), P["gold"], esc(ID["name"]).upper(),
           hf(SIZE["micro"], 700, 1.3), P["gold"], realtor, DOT, esc(ID["dre"]),
           fz(SIZE["small"], 1.4, None, P["on_dark_soft"]), esc(ID["brand_line"])))
    title = "Weekly Seller Report" + (", complete record" if m.link else "")
    out.append(
        '<tr><td class="g" data-sr-section="masthead" bgcolor="%s" style="padding:0 %dpx 14px;background:%s;color:%s">'
        '<table %s width="100%%"><tr>%s%s</tr></table></td></tr>'
        % (ink, g, ink, P["on_dark"], TBL,
           c('<div style="%s;color:%s">%s</div><div style="%s;padding-top:2px">Issued %s</div>'
             % (hf(16, 700, 1.3), P["on_dark"], title, fz(SIZE["small"], 1.4, None, P["on_dark_soft"]), long_day(R["report_date"])),
             "dark", pad="12px 0 0", line=True, va="bottom"),
           c('<span style="%s;color:%s">No.&nbsp;%s</span>' % (hf(SIZE["issue_no"], 700, 1.0), P["gold"], hk("issue", "%02d" % R["issue_number"])),
             "dark", al="right", w=84, pad="12px 0 0", line=True, va="bottom")))
    hero = OPT.get("hero")
    if hero:
        # With images blocked this cell shows the alt text, so the text is centered and the slot is kept short.
        w, h = SIZE["maxw"], SIZE["hero_h"]
        alt = "Photo of %s, %s" % (L["address"], L["city"])
        out.append('<tr><td align="center" bgcolor="%s" style="padding:0;background:%s;color:%s;font-size:0;line-height:0">'
                   '<img src="%s" width="%d" height="%d" alt="%s" style="display:block;width:100%%;max-width:%dpx;height:auto;border:0;'
                   'background:%s;color:%s;font-size:14px;line-height:1.5;text-align:center"></td></tr>'
                   % (ink, ink, P["on_dark_soft"], esc(hero), w, h, esc(alt), SIZE["print_maxw"] if OPT.get("print") else w,
                      ink, P["on_dark_soft"]))
    specs = []
    if L.get("beds") is not None:
        specs.append("%s bed" % num(L["beds"]))
    if L.get("baths") is not None:
        specs.append("%s bath" % num(L["baths"]))
    if L.get("sqft"):
        specs.append("%s sq ft" % num(L["sqft"]))
    if L.get("property_type"):
        specs.append(esc(L["property_type"]).lower())
    where = "%s, %s" % (esc(L["city"]), esc(L.get("state") or ""))
    hist = sorted(L.get("price_history") or [], key=lambda e: e["date"])
    price_sub = ("changed %s from %s" % (md(hist[-1]["date"]), money(hist[-2]["price"]))) if len(hist) > 1 else "unchanged since listing"
    n_off = m.T["offers"]
    off_sub = (n_(len(m.offers_week), "new offer") + " this week") if m.offers_week else ("none this week" if n_off else "none yet")
    fields = [
        ("Week covered", hk("week", "%s to %s" % (md(m.WS), md(m.WE))), ""),
        ("On the market", "Day %s" % hk("dom", num(R["days_on_market"])), "listed %s%s%s" % (md(L["list_date"]), DOT, esc(L.get("status") or "status not recorded").lower())),
        ("List price", hk("list_price", money(L["list_price"])), price_sub),
        ("Offers to date", hk("offers_total", num(n_off)), off_sub),
    ]
    rows = ""
    for i, (k, v, sub) in enumerate(fields):
        rows += "<tr>%s%s</tr>" % (
            c(esc(k).upper(), "page", w="37%", pad="7px 8px 7px 0", line=True, th=True, scope="row", va="top",
              st="%s;letter-spacing:.1em;color:%s" % (hf(SIZE["micro"], 700, 1.7), P["grey"])),
            c('<b style="%s;color:%s">%s</b> <span style="%s">%s</span>' % (hf(16, 700, 1.3), P["ink"], v, fz(SIZE["sub"], 1.4, None, P["grey"]), sub),
              "page", pad="7px 0", line=True, va="top"))
    grid = table(rows, data=True)
    out.append(sec('<h1 class="h1" style="margin:0;%s;color:%s">%s</h1>%s%s%s'
                   % (hf(SIZE["h1"], 700, 1.15), P["ink"], hk("address", esc(L["address"])),
                      para(where + DOT + ", ".join(specs), SIZE["small"], top=4, color=P["grey"]), sp(10), grid), top=18, name="masthead"))
    return "".join(out)


def week_items(m):
    """What happened this week, as short phrases: showings (one number, never an inquiry), inquiries, new
    disclosure packages, open house traffic in the host's own unit."""
    cur = m.cur
    sh = cur["showings"]            # key-box showings plus tours agents reported; an inquiry is never a showing
    items = [no_(sh, "showing")]
    if cur.get("inquiries"):
        items.append(n_(cur["inquiries"], "inquiry", "inquiries"))
    if cur.get("disclosure_contacts_new"):
        items.append(n_(cur["disclosure_contacts_new"], "new disclosure package"))
    ses, grp = len(m.oh_week), cur.get("open_house_groups")
    if not ses:
        items.append("no open house")
    elif grp:
        unit = m.oh_week[0].get("counted_unit") if len(set(o.get("counted_unit") for o in m.oh_week)) == 1 else None
        cnt = unit_count(grp, unit) if unit else "%s open house visits, as each host counted" % num(grp)
        items.append("%s at %s" % (cnt, "the open house" if ses == 1 else "%d open houses" % ses))
    elif grp == 0:
        items.append("no visitors at %s" % ("%s's open house" % C.WEEKDAYS[pd(m.oh_week[0]["date"]).weekday()] if ses == 1 else "%d open houses" % ses))
    else:
        items.append("%s with no count kept" % n_(ses, "open house"))
    busy = bool(sh or cur.get("offers") or grp or (cur.get("inquiries") or 0) > 1)
    return ("This week" if busy else "A quiet week"), items


def heard_this_week(m):
    """People we heard from this week, and how each came to be in touch (see Model.heard_how)."""
    heard = [x for x in m.active if m.wk(x, "rep")]
    how = [m.heard_how(x) for x in heard]
    return heard, how.count("first"), how.count("earlier")


def heard_extra(first, earlier):
    """', including 1 who contacted us first' when the people we heard from are not all answers to this week's follow-up."""
    bits = []
    if first:
        bits.append("%d who contacted us first" % first)
    if earlier:
        bits.append("%d answering a follow-up from an earlier week" % earlier)
    return (", including " + join_and(bits)) if bits else ""


def brief_sentences(m):
    """This week in brief, built from the week's counts, in Graeham's voice. It states what happened and what
    people said. It never suggests a price and never says what silence on price means."""
    cur = m.cur
    lead, items = week_items(m)
    out = ["%s: %s." % (lead, join_and(items))]
    ppl = cur["outbound_people"]
    days = cur["outbound_distinct_days"]           # calendar days, not one per person
    heard, first, earlier = heard_this_week(m)
    detail = ""
    if heard:
        groups, order = {}, []
        for x in heard:
            w = standing_words(m, x)
            if w not in groups:
                groups[w] = []
                order.append(w)
            groups[w].append(x)
        if len(heard) <= 4:
            bits = []
            for w in order:
                xs = groups[w]
                named = [dname(m, x) for x in xs if x.get("name_recorded") is not False and x["id"] not in m.masked]
                anon = len(xs) - len(named)
                who = named + ([n_(anon, "agent") if named else cap1(n_(anon, "agent"))] if anon else [])
                bits.append("%s %s" % (join_and(who), STANDING_VERB[w][0 if len(xs) == 1 else 1]))
            detail = join_and(bits)
        else:
            detail = join_and(["%d %s" % (len(groups[w]), STANDING_VERB[w][0 if len(groups[w]) == 1 else 1]) for w in order])
    k = len(heard)
    if not m.direct:
        s = "Nobody is on the log to follow up with yet."
    elif ppl:
        s = "My team followed up with %s on %s" % (n_(ppl, "person", "people"), n_(days, "day"))
        if not heard:
            s += " and has not heard back yet."
        elif not first and not earlier:
            s += " and heard back from %d: %s." % (k, detail)
        else:
            # replies can outnumber the people we followed up with: someone reached out first, or answered late
            s += ". We heard from %s this week%s: %s." % (n_(k, "person", "people"), heard_extra(first, earlier), detail)
    else:
        s = ("Everyone we have contacted has answered, so my team had no follow-up to make this week." if (m.contacted and not m.awaiting)
             else "My team did not make any follow-up contacts this week.")
        if heard:
            s += " We heard from %s%s: %s." % (n_(k, "person", "people"), heard_extra(first, 0), detail)
    out.append(s)
    conv, hi, fair = cur.get("conversations_with_feedback") or 0, cur.get("price_too_high") or 0, cur.get("price_fair_or_positive") or 0
    if cur.get("offers"):
        off = "we received %s" % n_(cur["offers"], "offer")
    else:
        off = "no offers came in" if m.offers else "no offers have come in yet"
    if conv and not (hi + fair):
        where = "this week's one conversation" if conv == 1 else "either conversation" if conv == 2 else "the %d conversations" % conv
        out.append("Nobody gave a view on price in %s, and %s." % (where, off))
    elif conv == 1:
        out.append("In this week's one conversation we were told the price is %s, and %s." % ("too high" if hi else "fair or good", off))
    elif conv:
        said = join_and([("%d said the price is too high" % hi) if hi else "",
                         ("%d said %s is fair or good" % (fair, "it" if hi else "the price")) if fair else ""])
        out.append("Of this week's %d conversations, %s, and %s." % (conv, said, off))
    else:
        out.append(cap1(off) + ".")
    return out


def preheader(m):
    """The inbox preview line. Long enough (about 110 to 135 characters) that the mail client does not run on
    into the first visible text of the email."""
    T = m.T
    s = re.sub(r"<[^>]+>", "", brief_sentences(m)[0])
    vh = T["contacted_through_host"]        # someone reached only through a host is not counted as contacted here either
    if T["contacts"]:
        s += " We contacted %d of %d%s, %d answered." % (T["contacted"] - vh, T["contacts"], " directly" if vh else "", T["replied"])
    else:
        s += " Nobody is on the log to follow up with yet."
    tail = " %s this week." % (cap1(n_(len(m.offers_week), "new offer")) if m.offers_week else "No offers")
    return s + (tail if len(s) + len(tail) <= 135 else "")


SINCE_VERB = (("call", "called"), ("voicemail", "called"), ("text", "texted"), ("email", "emailed"))
SINCE_ABOUT = re.compile(r"\babout ([^.,;:]+)")
SINCE_MAX_LINES = 10            # past this many lines the box prints the people who answered and counts the rest


def _since_text(it):
    s = (it.get("summary_safe") or "").strip()
    for rx in ASIDES:
        s = rx.sub("", s).strip()
    return s


def _since_answer(text):
    """Their answer as a sentence with a subject: 'Said his clients ...' reads 'He said his clients ...'."""
    mt = re.match(r"(Said|Replied|Wrote back|Answered)\b", text)
    if not mt:
        return text
    who = re.search(r"\b(his|her) (clients?|buyers?)\b", text)
    subj = {"his": "He", "her": "She"}.get(who.group(1), "They") if who else "They"
    return "%s %s%s" % (subj, mt.group(1).lower(), text[mt.end():])


def since_line(items):
    """(text, answered) for one person on one day after the week closed: what we did in one short sentence,
    then their answer if they gave one. A single entry prints as it was written."""
    answered = any(it.get("kind") != "touch" or C.is_reply(it) for it in items)
    texts = [_since_text(it) for it in items]
    typed = all(it.get("kind") == "touch" and it.get("direction") in ("outbound", "inbound") for it in items)
    if len(items) == 1 or not typed:
        return " ".join(t for t in texts if t), answered
    tries = [it for it in items if it["direction"] == "outbound" and not C.is_reply(it)]
    reached = [it for it in items if it["direction"] == "outbound" and C.is_reply(it)]
    theirs = [it for it in items if it["direction"] == "inbound"]
    dead = [it for it in tries if it.get("outcome") == "did_not_connect"]
    did = set(it.get("channel") for it in tries)             # a call that did not connect is still a call we made
    if any(it.get("our_call") for it in theirs):
        did.add("call")
    verbs = []
    for ch, verb in SINCE_VERB:
        if ch in did and verb not in verbs:
            verbs.append(verb)
    other = len([it for it in tries if it not in dead and it.get("channel") not in dict(SINCE_VERB)])
    if other and not verbs:
        verbs.append("followed up")
    about = set(mt.group(1).strip() for it in tries for mt in [SINCE_ABOUT.search(_since_text(it))] if mt)
    topic = (" about " + about.pop()) if len(about) == 1 else ""
    out = [_since_text(it) for it in reached]                 # a call that reached them is already a full sentence
    if verbs:
        out.append("We %s%s%s." % ("also " if reached else "", join_and(verbs), "" if reached else topic))
    if dead:
        live = [it for it in tries if it not in dead and it.get("channel") in ("call", "voicemail")]
        out.append("The calls did not connect." if len(dead) > 1 else "One call did not connect." if live else "The call did not connect.")
    out += [_since_answer(_since_text(it)) for it in theirs]
    if not answered and not dead:
        out.append("No answer yet.")
    return " ".join(t for t in out if t), answered


def since_lines(m):
    """The 'since the week closed' box: [(date, contact or None, name, text, answered)], one per person per day,
    and the number of people folded into the closing sentence when the box would run long."""
    groups, order = {}, []
    for i, it in enumerate(m.after):
        who = it.get("contact_id") or it.get("name_short")
        k = (it["date"], who if who else "#%d" % i)
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(it)
    rows = []
    for k in order:
        items = groups[k]
        x = m.byid.get(items[0].get("contact_id"))
        name = dname(m, x) if x else (safe(m, items[0]["name_short"]) if items[0].get("name_short") else "")
        text, answered = since_line(items)
        rows.append(dict(date=k[0], x=x, name=name, text=text, answered=answered, who=k[1]))
    folded = []
    if len(rows) > SINCE_MAX_LINES:
        folded = [r for r in rows if not r["answered"]]
        rows = [r for r in rows if r["answered"]]
    return rows, len(set(r["who"] for r in folded))


def override_paragraphs(text):
    return [p_.strip() for p_ in re.split(r"\n\s*\n", text or "") if p_.strip()]


def s_brief(m):
    ID = m.ID
    first_name = esc(ID["name"].split()[0])
    body = ""
    greet = OPT.get("greeting")
    if greet and not m.link:
        body += para(esc(greet), SIZE["body"], top=0, color=P["ink"])
    over = None if m.link else override_paragraphs(m.R.get("brief_override"))       # the link copy keeps to the counts
    if over:
        # a person replaced the text: it prints as written, paragraph by paragraph
        for i, t in enumerate(over):
            body += '<p class="lede" data-sr-section="brief_override" style="margin:%dpx 0 0;%s;color:%s">%s</p>' % (
                (10 if body else 0), fz(SIZE["lede"], 1.55), P["ink"], safe(m, t))
    else:
        sents = brief_sentences(m)
        body += '<p class="lede" style="margin:%dpx 0 0;%s;color:%s"><b>%s</b> %s</p>' % (
            10 if body else 0, fz(SIZE["body"], 1.5), P["ink"], sents[0], " ".join(sents[1:]))
    body += para("<b>%s</b>" % first_name, SIZE["text"], top=6, color=P["ink"])
    s = bar("This week in brief") + card(body, pad="14px 16px 14px", top=10, edge=True)
    if m.after:
        rows = ""
        lines, folded = since_lines(m)
        for r in lines:
            rows += para("<b>%s%s:</b> %s" % (md(r["date"]), (DOT + r["name"]) if r["name"] else "", safe(m, r["text"], r["x"])),
                         SIZE["small"], top=4)
        if folded:
            rows += para("We also followed up with %s who %s not answered yet." % (
                n_(folded, "more person", "more people") if lines else n_(folded, "person", "people"), "has" if folded == 1 else "have"),
                SIZE["small"], top=4)
        s += card(kicker("Since the week closed" + DOT + "as reported to our team", P["ink"]) + rows +
                  para("Logged after Sunday, so it is not in this week's numbers.", SIZE["sub"], top=5, color=P["grey"]),
                  sf="card", pad="12px 16px 12px", top=8, at=mark("section", "since_week_closed"))
    return sec(s, top=22, name="brief")
