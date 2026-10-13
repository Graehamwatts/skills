# -*- coding: utf-8 -*-
"""sr_render.api: render(), the one way a page is built.

    result = render(ledger, mode="email")
    result = render(ledger, mode="email", hero="https://...", link_url="https://...")

    result["html"]   the page
    result["info"]   what a manifest needs: bytes, fit level, checks run, flags, sections, warnings

There is one build mode. Every page that comes back is clean and ready to send: no notice on top, no panel
at the end, nothing addressed to anyone but the seller. A build is refused (RenderRefused) only when the
ledger does not satisfy the contract, when the lists the page would print do not agree with the ledger's
totals, or when a check on the finished page fails.

The masthead photo and the link to the complete record are used only when they are https addresses. Anything
else (a local path, a relative name) is left off the page, so nothing a seller cannot open is ever printed.
"""
import hashlib
import re

import sr_contract as C
from . import assemble, fit
from .model import Model, ModelError
from .tokens import OPT, LIMITS

MODES = ("email", "link", "print")
_HTTPS = re.compile(r"https://\S+$")


class RenderRefused(Exception):
    """The build was stopped. .stage says where ('ledger', 'model', 'page', 'size') and .problems why."""

    def __init__(self, stage, problems):
        self.stage, self.problems = stage, list(problems)
        Exception.__init__(self, "%s: %s" % (stage, "; ".join(self.problems[:5])))


def default_greeting(ledger):
    """'Hi Pat and Sam,' from listing.seller_first_names, or None when the ledger has no names."""
    names = [n for n in (ledger.get("listing") or {}).get("seller_first_names") or [] if str(n).strip()]
    return ("Hi %s," % C.join_and([str(n).strip() for n in names])) if names else None


def render(ledger, identity=None, mode="email", hero=None, no_hero=False, link_url=None, no_link=False,
           greeting=None, no_greeting=False, webfonts=None, max_bytes=None, market=True, marketing=True, nearby=True):
    """Builds one page from a ledger. See the module docstring. Nothing is written to disk and the ledger is
    not changed."""
    if mode not in MODES:
        raise ValueError("mode must be one of %s" % ", ".join(MODES))
    ID = identity or C.load_identity()
    problems = C.validate_ledger(ledger, identity=ID)
    if problems:
        raise RenderRefused("ledger", problems)
    link = mode in ("link", "print")
    try:
        m = Model(ledger, ID, link)
    except ModelError as e:
        raise RenderRefused("model", e.problems)
    L = ledger["listing"]
    left_off = []
    if no_hero:
        hero = None
    else:
        hero = hero or L.get("hero_photo")
        if hero and not _HTTPS.match(str(hero)):
            left_off.append("the masthead photo is not at an https address, so the page has no photo")
            hero = None
    if link or no_link:
        link_url = None
    elif link_url and not _HTTPS.match(str(link_url)):
        left_off.append("the link to the complete record is not an https address, so the email has no button and offers to send the record instead")
        link_url = None
    OPT.clear()
    OPT.update(mode=mode, hero=hero, link_url=link_url, keep=link, print=(mode == "print"),
               webfonts=bool(link if webfonts is None else webfonts),
               greeting=None if (no_greeting or link) else (greeting or default_greeting(ledger)),
               market=bool(market), marketing=bool(marketing), nearby=bool(nearby))
    ceiling = int(max_bytes or LIMITS["max_bytes"])
    try:
        if link:
            level, doc = 0, assemble.build(m, 0)
        else:
            target = min(LIMITS["fit_target"], ceiling - (LIMITS["max_bytes"] - LIMITS["fit_target"]))
            level, doc = fit.fit_email(lambda lv: assemble.build(m, lv), target)
    except ValueError as e:
        raise RenderRefused("model", [str(e)])
    err, warn = assemble.checks(doc, m)
    if err:
        raise RenderRefused("page", err)
    size = fit.size(doc)
    if not link and size > ceiling:
        raise RenderRefused("size", ["the email is %d bytes, over the %d byte ceiling, at the last step of the fit ladder" % (size, ceiling)])
    sections = [k for k in ("nearby", "market", "marketing") if ledger.get(k) and OPT[k]]
    if m.online:
        sections.insert(0, "online")
    forms = [form for v in m.entries.values() for _, form in v]
    T = ledger["totals"]
    info = dict(
        mode=mode, bytes=size, kb=round(size / 1024.0, 1),
        sha256=hashlib.sha256(doc.encode("utf-8")).hexdigest(), max_bytes=None if link else ceiling,
        fit_level=level,
        flags=dict(webfonts=OPT["webfonts"], hero=hero, link_url=link_url, sections=sections, fit_level=level,
                   greeting=OPT["greeting"]),
        checks=dict(ledger_problems=0, model_checks_run=m.checks_run, page_checks_failed=0),
        warnings=warn + left_off,
        issue_number=ledger["report"]["issue_number"], report_date=ledger["report"]["report_date"],
        lists=dict((k, len(v)) for k, v in m.entries.items()),
        entries=dict((k, forms.count(k)) for k in ("full", "line", "pointer")),
        contacts=T["contacts"], contacted=T["contacted"], answered=T["replied"],
        still_waiting=T["awaiting_reply"], follow_ups=T["touches_outbound"], replies=T["replies_inbound"],
        people_with_feedback=T["people_with_feedback"])
    return dict(html=doc, info=info)
