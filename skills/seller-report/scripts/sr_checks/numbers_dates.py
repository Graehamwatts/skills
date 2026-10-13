# -*- coding: utf-8 -*-
"""sr_checks.numbers_dates: no invented dates.

  person_dates   every date printed inside a person's card (data-sr-person) is a date in that person's own
                 record: a touch, an engagement, a conversation, their next follow-up, an open house they came
                 to, or a date already written in their notes. Blocking.
  page_dates     every date on the page is somewhere in the ledger (or follows from it: a week's Monday or
                 Sunday, the next report date). A warning, because a renderer may print a date the ledger
                 derives in a way this gate does not know.
"""
import datetime
import re

from . import core

MONTH = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
DATE = re.compile(r"(?<![\w$])(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?"
                  r"|Nov(?:ember)?|Dec(?:ember)?)\.? (\d{1,2})(?!\d|[.,]\d|%| ?(?:px|pt)\b)", re.I)
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")


def md(iso):
    return (int(iso[5:7]), int(iso[8:10]))


def printed(text):
    """[(month, day, the text as printed)] for every 'Mar 9' or 'MAR 9' style date in a piece of text.
    A month word must start with a capital, so 'they may 2' is not read as May 2."""
    return [(MONTH[m.group(1)[:3].lower()], int(m.group(2)), m.group(0)) for m in DATE.finditer(text or "")
            if m.group(1)[0].isupper() and 1 <= int(m.group(2)) <= 31]


def _week(iso):
    y, m, d = (int(x) for x in iso[:10].split("-"))
    day = datetime.date(y, m, d)
    mon = day - datetime.timedelta(days=day.weekday())
    return [md(mon.isoformat()), md((mon + datetime.timedelta(days=6)).isoformat())]


def _collect(node, out):
    """Every ISO date value and every date written inside a string, anywhere under node."""
    if isinstance(node, dict):
        for v in node.values():
            _collect(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect(v, out)
    elif isinstance(node, str):
        if ISO.match(node):
            out.add(md(node))
            out.update(_week(node))
        else:
            out.update((m, d) for m, d, _ in printed(node))


def person_set(c, ledger):
    out = set()
    _collect(dict((k, v) for k, v in c.items() if k != "id"), out)
    R = ledger.get("report") or {}
    for k in ("week_start", "week_end", "report_date"):
        if R.get(k):
            out.add(md(R[k]))
    for it in (R.get("since_week_closed") or {}).get("items") or []:
        if it.get("contact_id") == c.get("id"):
            _collect(it, out)
    for o in ledger.get("offers") or []:
        if o.get("contact_id") == c.get("id"):
            _collect(o, out)
    for w in ledger.get("offer_watch") or []:
        if w.get("contact_id") == c.get("id"):
            _collect(w, out)
    if c.get("kind") == "open_house_visitor" or c.get("is_open_house_host") or c.get("reached_through"):
        _collect(ledger.get("open_houses") or [], out)
    for other in ledger.get("contacts") or []:                 # a buyer listed under their agent, and the reverse
        if other.get("represented_by") == c.get("id") or c.get("represented_by") == other.get("id"):
            _collect(other.get("engagements") or [], out)
    _collect((ledger.get("listing") or {}).get("price_history") or [], out)
    return out


def page_set(ledger):
    out = set()
    _collect(ledger, out)
    R = ledger.get("report") or {}
    if R.get("report_date"):
        y, m, d = (int(x) for x in R["report_date"][:10].split("-"))
        for step in (7, 14):
            out.add(md((datetime.date(y, m, d) + datetime.timedelta(days=step)).isoformat()))
    for w in ledger.get("weeks") or []:
        for k in ("start", "end"):
            if w.get(k):
                out.add(md(w[k]))
    for i, e in enumerate(sorted((ledger.get("listing") or {}).get("price_history") or [], key=lambda e: e.get("date") or "")):
        if i and e.get("date"):                                # the last day at the earlier price
            y, m, d = (int(x) for x in e["date"][:10].split("-"))
            out.add(md((datetime.date(y, m, d) - datetime.timedelta(days=1)).isoformat()))
    return out


def check_dates(B, ctx):
    ledger = ctx.ledger
    by_id = dict((c["id"], c) for c in ledger.get("contacts") or [])
    cards = ctx.page.people()
    bad, checked = [], 0
    for cid, nodes in sorted(cards.items()):
        c = by_id.get(cid)
        if c is None:
            continue
        allowed = person_set(c, ledger)
        for n in nodes:
            for m, d, shown in printed(ctx.page.flat(root=n)):
                checked += 1
                if (m, d) not in allowed:
                    bad.append("%s (%s): '%s' is not a date in this person's record" % (cid, c.get("name_short"), shown))
    if cards:
        B.judge("person_dates", sorted(set(bad)), "%d dates printed in %d person cards are all in those people's own records"
                % (checked, len(cards)), "a person's card prints a date that is not in their record")
    known = page_set(ledger)
    text = ctx.seller_flat()
    stray = sorted(set("'%s' in '%s'" % (shown, core.excerpt(text, text.find(shown), text.find(shown) + len(shown), 30))
                       for m, d, shown in printed(text) if (m, d) not in known))
    if stray:
        B.warn("page_dates", "%d date(s) on the page are not in the ledger. Check each one" % len(stray), stray[:8])
    else:
        B.ok("page_dates", "every date on the page is in the ledger or follows from it")
