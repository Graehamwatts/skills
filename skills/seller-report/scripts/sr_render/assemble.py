# -*- coding: utf-8 -*-
"""sr_render.assemble: puts the sections in order, wraps the document, and checks the finished page.

The order is the same in every issue: the summary on top, then the details.

    AT A GLANCE    masthead, this week in brief, the numbers, the charts, what people are saying
    THE DETAILS    offers and likely offers, agents who showed the home, disclosure packages, open houses,
                   other inquiries, similar homes nearby, time on the market, online ads and marketing, next week
    THE RECORD     follow-up since we listed, every week in one table, every price comment, the record at each
                   list price, how we count, the footer
"""
import re

import sr_contract as C
from .text import *        # noqa: F401,F403
from .fit import FIT_LEVELS
from .sections_top import s_masthead, s_brief, preheader
from .sections_numbers import s_numbers, s_charts
from .sections_saying import s_saying, s_price_periods, s_price_record
from .sections_lists import s_details_band, s_offers, s_showings, s_disclosure, s_openhouse, s_inquiries, s_history
from .sections_more import s_nearby, s_market, s_marketing, s_next, next_items
from .sections_record import s_record_band, s_followup_record, s_stack, s_howcount, s_footer, TRIES_NOTE, TRIES_USED

# section names in page order, for the tests and for anyone reading a page's data-sr-section hooks
ORDER = ("masthead", "brief", "numbers", "weekly_chart", "views_chart", "saying",
         "details", "offers", "list_showings", "list_disclosure", "open_houses", "list_other_inquiries", "history",
         "nearby", "market", "marketing", "next_week",
         "record", "followup", "weekly_table", "price_comments", "price_periods", "how_we_count", "footer")


def build(m, fit=0):
    """One page, ready to send. Nothing on it is addressed to anyone but the seller."""
    m.entries = {}
    OPT["fit"] = FIT_LEVELS[fit]
    parts = [
        # at a glance
        s_masthead(m), s_brief(m), s_numbers(m), s_charts(m), s_saying(m),
        # the details: people grouped by what they did, then the optional sections and next week
        s_details_band(m), s_offers(m), s_showings(m), s_disclosure(m), s_openhouse(m), s_inquiries(m), s_history(m),
        s_nearby(m), s_market(m), s_marketing(m), s_next(m),
        # the record since we listed, carried forward in every issue
        s_record_band(m), s_followup_record(m), s_stack(m), s_price_record(m), s_price_periods(m), s_howcount(m), s_footer(m)]
    # How we count explains "tries" only when an entry on this page counts them
    said = unesc(re.sub(r"<[^>]+>", " ", without_sections("".join(parts), ("how_we_count",))))
    if not TRIES_USED.search(said):
        parts = [p_.replace(TRIES_NOTE, "") for p_ in parts]
    if gmail_safe():
        parts = [guard_addresses(p_) for p_ in parts]
    L, R = m.L, m.R
    title = "Weekly Seller Report No. %02d: %s" % (R["issue_number"], L["address"])
    pre = preheader(m)
    gw = str(SIZE["gutter_wide"])
    maxw = SIZE["print_maxw"] if OPT.get("print") else SIZE["maxw"]       # the print layout uses the width of the paper
    css = (
        "html{color-scheme:light only}body{margin:0;padding:0;-webkit-text-size-adjust:100%;text-size-adjust:100%}"
        "table{border-collapse:separate;border-spacing:0}img{border:0;outline:none;text-decoration:none}"
        "a[x-apple-data-detectors]{color:inherit!important;text-decoration:none!important}"
        "@media (min-width:620px){.g{padding-left:" + gw + "px!important;padding-right:" + gw + "px!important}"
        ".h1{font-size:32px!important}.h2{font-size:24px!important}.lede{font-size:18px!important}}"
        "@media (max-width:340px){.g{padding-left:8px!important;padding-right:8px!important}}"      # a 320 px phone gets 16 px back
        "@page{margin:11mm}@media print{.k{page-break-inside:avoid;break-inside:avoid}h2,h3{page-break-after:avoid;break-after:avoid}"
        "body{-webkit-print-color-adjust:exact;print-color-adjust:exact" + (";zoom:.9" if OPT.get("print") else "") + "}}")
    mso = "td,th,div,p,a,h1,h2,h3,span,b{font-family:Arial,sans-serif!important}" + "".join(
        ".t%d td,.t%d th{font-size:%dpx}" % (k, k, k) for k in sorted(set([SIZE["micro"], SIZE["sub"], SIZE["small"], SIZE["text"], SIZE["body"], SIZE["lede"]])))
    link = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link href="%s" rel="stylesheet">' % F["href"]) if OPT["webfonts"] else ""
    page = P["white"]
    # what this file is, for the ship gate: which page, which listing, issue and week
    stamp = "".join('<meta name="sr:%s" content="%s">' % kv for kv in (
        ("kind", OPT["mode"]), ("slug", esc(m.d["meta"]["slug"])),
        ("issue", R["issue_number"]), ("week", "%s/%s" % (R["week_start"], R["week_end"]))))
    if gmail_safe():
        stamp += '<meta name="sr:copy" content="gmail">'          # the Gmail-safe copy of the email (the ship gate reads it)
    doc = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow,noarchive">%s'
        '<meta name="x-apple-disable-message-reformatting"><meta name="color-scheme" content="light only">'
        '<meta name="supported-color-schemes" content="light only"><title>%s</title>%s<style>%s</style>'
        '<!--[if mso]><style>%s</style>'
        '<xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]--></head>'
        '<body style="margin:0;padding:0;background:%s">'
        '<div style="display:none;max-height:0;overflow:hidden;font-size:1px;line-height:1px;color:%s">%s</div>'
        '<table %s width="100%%" bgcolor="%s"><tr><td align="center" bgcolor="%s" style="padding:0;color:%s">'
        '<!--[if mso]><table role="presentation" width="%d" align="center" cellpadding="0" cellspacing="0"><tr><td><![endif]-->'
        '<table %s width="100%%" style="max-width:%dpx;margin:0 auto;font-family:%s;font-size:%dpx;line-height:1.5;text-align:left">%s</table>'
        '<!--[if mso]></td></tr></table><![endif]-->'
        '</td></tr></table></body></html>'
        % (stamp, esc(title), link, css, mso, page, page, esc(re.sub(r"<[^>]+>", "", pre)), TBL, page, page, P["ink"], maxw,
           TBL, maxw, F["body"], SIZE["text"], "".join(parts)))
    doc = re.sub(r"(?<=[A-Za-z])\.\.(?=[\s<])", ".", doc)        # a short name such as "Odalys V." at the end of a sentence
    # Keep every physical line short (the mail line limit is 998 characters). Lines are packed up to 700
    # characters and only ever broken just before a tag that starts a block, where a line break changes nothing.
    parts = re.split(r"(?=<tr|<p |<h2|<h3|<table |<meta |<style>|<body |<!--\[if mso\]>|<title>|<div style=\"font-size:1px|<div data-sr-entry|<span data-sr-entry)", doc)
    lines, cur = [], ""
    for part in parts:
        if cur and len(cur) + len(part) > 700:
            lines.append(cur)
            cur = ""
        cur += part
    lines.append(cur)
    out = []
    for ln in lines:
        if len(ln) > 900:
            for end in ("</td>", "</th>", "</div>", "</a>", "<br>"):       # after a <br> a line break changes nothing either
                ln = ln.replace(end, end + "\n")
        out.append(ln)
    return "\n".join(out)


# A web address in running text, which a mail program would turn into a link: an optional scheme or www, then
# a name and any ending of 2 to 24 letters (bit.ly, youtu.be, a .ca or a .link address as much as a .com). An
# email address is not one (the name is not preceded by @). Guarding more than an address is harmless: the
# words do not change. sr_checks.email_safety.ADDRESS_PATTERN is the same text (a test keeps them equal).
ADDRESS_PATTERN = r"(?<![\w@.-])(?:https?://)?(?:www\.)?[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24}\b(?![@\w-])"
ADDRESS = re.compile(ADDRESS_PATTERN, re.I)
# what is left linkable in one run of text: a scheme, or www with a dot after it
LINKABLE = re.compile(r"https?://|\bwww\.", re.I)


def _guard_one(address):
    scheme = re.match(r"https?://", address, re.I)
    if not scheme:
        return no_autolink(address, "inherit")
    return (esc(scheme.group(0)[:-3]) + '<span style="color:inherit">://</span>'
            + no_autolink(address[scheme.end():], "inherit"))


def guard_addresses(html):
    """The Gmail-safe copy: any web address in running text (outside a link, a tag or a comment) is written with
    htmlkit.no_autolink, so the connector cannot turn it into a redirect, and a scheme's '://' sits in a span of
    its own. The words do not change."""
    out, in_a = [], 0
    for bit in re.split(r"(<!--.*?-->|<[^>]+>)", html, flags=re.S):
        if bit.startswith("<"):
            if re.match(r"<a\b", bit, re.I):
                in_a += 1
            elif re.match(r"</a\s*>", bit, re.I):
                in_a = max(0, in_a - 1)
            out.append(bit)
        elif in_a or not bit:
            out.append(bit)
        else:
            out.append(ADDRESS.sub(lambda mt: _guard_one(unesc(mt.group(0))), bit))
    return "".join(out)


def gmail_problems(doc):
    """What the Gmail connector would break in the Gmail-safe copy. Each one stops the build."""
    err = []
    if re.search(r"<img\b", doc, re.I):
        err.append("the Gmail-safe copy has an image (the connector drops every image)")
    if re.search(r'href="tel:', doc, re.I):
        err.append("the Gmail-safe copy has a tel: link (the connector turns it into a dead link)")
    web = [h for h in re.findall(r'<a\b[^>]*href="(https?:[^"]*)"', doc, re.I) if h != OPT.get("link_url")]
    if web:
        err.append("the Gmail-safe copy links to %s (the connector rewrites web links into redirects)" % web[0][:60])
    bg = re.findall(r'<(?!t[dhr]\b|table\b|body\b)(\w+)\b[^>]*style="[^"]*background', doc, re.I)
    if bg:
        err.append("the Gmail-safe copy colors a %s with a background, which the connector drops (%d)" % (bg[0], len(bg)))
    body = doc[doc.find("<body"):]
    for bit in re.split(r"<a\b.*?</a>", body, flags=re.S | re.I):
        runs = [unesc(t) for t in re.split(r"<[^>]+>", bit)]
        hit = next((h for h in (ADDRESS.search(t) or LINKABLE.search(t) for t in runs) if h), None)
        if hit:
            err.append("the Gmail-safe copy has a web address a mail program would turn into a link: " + hit.group(0))
            break
    return err


def _ledger_text(d):
    """Every string in the ledger, lower case. Used to tell copy the generator wrote from text a person reported."""
    out = []

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            out.append(node.lower())
    walk(d)
    return " \n ".join(out)


def without_sections(doc, names):
    """The page with the named sections cut out (each runs from its hook to the next section's hook)."""
    for name in names:
        a = doc.find('data-sr-section="%s"' % name)
        if a >= 0:
            b = doc.find('data-sr-section="', a + 20)
            doc = doc[:a] + doc[b if b >= 0 else len(doc):]
    return doc


def footing(doc, m):
    """The lists under "The details" against the ledger: the count in each heading is the number of entries
    beneath it, every person is on every list they belong to exactly once, and is shown in full at most once."""
    err = []
    T = m.T
    full = {}
    for key in C.LIST_KEYS:
        got = m.entries.get(key) or []
        want = set(x["id"] for x in m.lists[key])
        ids = [i for i, _ in got]
        if len(got) != T["lists"][key] or set(ids) != want or len(ids) != len(set(ids)):
            err.append("list %s: %d entries printed, the heading says %d" % (key, len(got), T["lists"][key]))
        for i, form in got:
            x = m.byid[i]
            if ('data-sr-entry="%s:%s"' % (form, "" if i in m.masked else i)) not in doc:
                err.append("list %s: the entry for %s is not marked on the page" % (key, i))
            if (form == "pointer") != (x.get("primary_list") != key):
                err.append("list %s: %s is printed as a %s, and their first list is %s" % (key, i, form, x.get("primary_list")))
            if form == "full":
                full[i] = full.get(i, 0) + 1
            if m.link and form == "line":
                err.append("list %s: %s is one line in a copy that shows everyone in full" % (key, i))
    twice = sorted(i for i, k in full.items() if k > 1)
    if twice:
        err.append("shown in full more than once: %s" % ", ".join(twice))
    marks = len(re.findall(r'data-sr-entry="', doc))
    if marks != sum(len(v) for v in m.entries.values()):
        err.append("%d entries are marked on the page, %d were placed in the lists" % (marks, sum(len(v) for v in m.entries.values())))
    for key in C.LIST_KEYS:
        if m.lists[key] and ('data-sr="list:%s">%d<' % (key, len(m.lists[key]))) not in doc:
            err.append("list %s: the heading does not print its count" % key)
    return err


def checks(doc, m):
    """Checks on the finished page. Returns (errors, warnings). Any error stops the build."""
    err, warn = footing(doc, m), []
    ID = m.ID
    if C.has_dash(doc):
        err.append("an em dash or en dash is on the page")
    if C.find_blocked(doc, ID):
        err.append("a blocked brand or DRE value from identity.json is on the page")
    if ID["dre"] not in doc:
        err.append("the DRE from identity.json is missing")
    low = doc.lower()
    body = re.sub(r"<[^>]+>", " ", doc)
    text = re.sub(r"\s+", " ", unesc(body))
    tlow = text.lower()
    for wd in WORDS_BANNED:
        if wd in tlow:
            warn.append("filler word present: " + wd)
    # feedback only: the generator never suggests a price, asks for a decision, or reads meaning into silence
    told = _ledger_text(m.d)
    for wd in FEEDBACK_ONLY_BANNED:
        if wd in tlow:
            (warn if wd in told else err).append(
                "feedback only: '%s' is on the page%s" % (wd, " (it comes from text in the ledger; check that it is something a person said)" if wd in told else ""))
    ph = set(re.findall(r"\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b", body)) - set([ID["phone"]])
    if ph:
        err.append("phone-like strings that are not the agent's own: %s" % sorted(ph))
    em = set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", body)) - set([ID["email"]])
    if em:
        err.append("email-like strings that are not the agent's own: %s" % sorted(em))
    # one build mode: nothing on a page is addressed to a reviewer, and the page never speaks of how it was made
    for wd in NEVER_ON_A_PAGE:
        if wd in tlow and wd not in told:
            err.append("working wording is on the page: '%s'" % wd)
    for note in m.d.get("data_quality") or []:
        if len(note) > 30 and note.lower() in tlow:
            err.append("a build note is printed on the page: %s" % note[:60])
    if re.search(r"file:/|[A-Za-z]:[\\/]+Users|/Users/|AppData[\\/]", doc):
        err.append("a local file path is in the page")
    if 'name="robots" content="noindex' not in doc:
        err.append("the page is not marked noindex")
    if 'style="display:none;max-height:0' not in doc:
        err.append("the inbox preview line is missing")
    for key, lab in PRICE_ROWS:
        if lab not in text:
            err.append("price row missing: " + lab)
    if m.link:
        amounts = set(money(o["price"]) for o in m.offers if o.get("price") is not None) - set(
            money(e["price"]) for e in (m.L.get("price_history") or [])) - set([money(m.L["list_price"])])
        # a watched home or a comparable sale may carry the same public price as an offer: those two sections print
        # public record amounts, so an offer amount is looked for everywhere else
        private = without_sections(doc, ("nearby", "market"))
        for a in amounts:
            if a in private:
                err.append("link copy carries an offer amount: " + a)
        for o in m.offers:
            if o.get("agent_short") and o["agent_short"] in body:
                err.append("link copy names an agent with an offer: " + o["agent_short"])
            others = set(x.get("brokerage") for x in m.contacts if x["id"] not in m.masked)
            if o.get("brokerage") and o["brokerage"] not in others and o["brokerage"].split()[0] in body:
                err.append("link copy carries the brokerage of an agent with an offer: " + o["brokerage"])
            if o.get("terms_summary") and o["terms_summary"][:40] in doc:
                err.append("link copy carries offer terms")
        # The copy says it leaves out who may be weighing an offer, so the build proves it three ways.
        own = text.replace("an offer on file", "").replace("who may be weighing one", "")
        # 1. no offer-intent wording anywhere on the page (the page's own phrases are set aside)
        hit = OFFER_INTENT.search(own)
        if hit:
            err.append("link copy has offer-intent wording: ..." + own[max(0, hit.start() - 70):hit.end() + 30] + "...")
        # 2. no sentence about an offer from the notes of anyone read as weighing or having written one
        for x in m.contacts:
            if x["id"] not in m.offer_people:
                continue
            notes = ([x.get("feedback_safe"), x.get("offer_basis_safe"), (x.get("_lead") or {}).get("basis_safe")]
                     + [t.get("summary_safe") for t in x["touches"]] + [e.get("text_safe") for e in (x.get("feedback_log") or [])])
            for snt in set(z for nt in notes for z in sentences(nt or "")):
                if (OFFER_ANY.search(snt) or OFFER_INTENT.search(snt)) and snt in text:
                    err.append("link copy prints an offer sentence from %s's notes: %s" % (x["name_short"], snt[:80]))
        # 3. the next-week list names none of them
        nxt = " ".join(next_items(m))
        for x in m.contacts:
            if x["id"] in m.offer_people and x["name_short"] in nxt:
                err.append("link copy next-week list names someone who may be weighing an offer: " + x["name_short"])
        if "STILL&nbsp;DECIDING" in doc or "STILL DECIDING" in doc:
            err.append("link copy shows a Still deciding chip")
        for it in (m.R.get("since_week_closed") or {}).get("items") or []:
            if (it.get("offer_related") or it.get("kind") == "offer") and it.get("summary_safe") and it["summary_safe"] in text:
                err.append("link copy prints an offer note logged after the week closed")
    if SIZE["issue_no"] >= SIZE["wordmark"]:
        err.append("the issue number is set as large as the wordmark (brand rule: the name leads and is largest in its band)")
    for tag in ("<script", "<svg", "display:flex", "display:grid", "position:absolute", "position:fixed", "background-image", "<form"):
        if tag in low:
            err.append("email-unsafe construct: " + tag)
    if re.search(r'bgcolor="#[0-9A-Fa-f]{3}"', doc):
        err.append("three-digit bgcolor attribute")
    sizes = [int(x) for x in re.findall(r"font-size:(\d+)px", doc)] + [int(x) for x in re.findall(r"font:\d+ (\d+)px", doc)]
    small = [x for x in sizes if 1 < x < 12]
    if small:
        err.append("text under 12px: %s" % sorted(set(small)))
    cells = re.findall(r"<t[dh]\b[^>]*>", re.sub(r"<!--\[if mso\]>.*?<!\[endif\]-->", "", doc, flags=re.S))
    bare = [t for t in cells if "bgcolor=" not in t]
    if bare:
        err.append("%d cells without a background of their own, e.g. %s" % (len(bare), bare[0][:90]))
    # a cell on black or gold always states its own text color: ink inherited onto black would not be read
    dark = [t for t in cells if ('bgcolor="%s"' % P["ink"] in t) and "color:" not in t and "font-size:0" not in t]
    if dark:
        err.append("%d cells on black without a text color of their own, e.g. %s" % (len(dark), dark[0][:90]))
    for a in re.findall(r"<a\b[^>]*>", doc):
        pad = re.search(r"padding:(\d+)px", a)
        if "display:block" not in a or not pad or int(pad.group(1)) < 11:
            err.append("a link is not a block at least %d px tall: %s" % (LIMITS["tap_px"], a[:80]))
    if gmail_safe():
        err += gmail_problems(doc)
    longest = max(len(ln) for ln in doc.split("\n"))
    if longest > 990:
        warn.append("longest line is %d characters" % longest)
    return err, warn
