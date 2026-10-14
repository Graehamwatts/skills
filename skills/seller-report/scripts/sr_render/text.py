# -*- coding: utf-8 -*-
"""sr_render.text: what a seller may read.

Names, roles, how a person engaged, the short labels and chips, and the rules for the link copy: no offer price, no
offer terms, no name of an agent who wrote an offer, and nothing that says who may be weighing one.
"""
import re

import sr_contract as C
from .htmlkit import *        # noqa: F401,F403


def scrub_offers(m, s, x=None, wide=False):
    """Link copy only. Drops every sentence that states an offer amount or says someone may write an offer.
    For a person read as weighing an offer or having written one (and when wide is set) it drops every
    sentence that mentions an offer at all. Nothing is left in its place: a marker beside a name would itself
    say whose notes were about an offer. The page states once that these sentences are left out."""
    wide = wide or bool(x is not None and x["id"] in m.offer_people)
    return " ".join(snt for snt in sentences(s)
                    if not (OFFER_INTENT.search(snt) or (OFFER_ANY.search(snt) and (wide or re.search(r"\$\s?\d", snt)))))


def safe(m, text, x=None):
    """Seller-safe text: strips internal asides, shortens blocked brand strings, and in the link copy masks
    agents with an offer on file and takes out offer amounts and any sign of who may be weighing an offer.
    x is the person the text belongs to, when there is one."""
    s = str(text or "")
    for rx in ASIDES:
        s = rx.sub("", s)
    for b in (m.ID.get("blocklist") or {}).get("brand") or []:
        s = re.sub(re.escape(b), b.split()[0], s, flags=re.I)
    if m.link:
        s = scrub_offers(m, s, x)
        for nm in m.masked_names:
            s = s.replace(nm, OFFER_MASK)
        s = re.sub(r"(^|[.!?]\s+)an agent with an offer", lambda g: g.group(1) + "An agent with an offer", s)
    return esc(C.strip_dashes(s.strip()))


def dname(m, x, lower=False):
    if x["id"] in m.masked:
        return OFFER_MASK if lower else cap1(OFFER_MASK)
    if x.get("name_recorded") is False and x.get("kind") == "agent":
        return "an agent whose name we do not have" if lower else "An agent whose name we do not have"
    return safe(m, x["name_short"])


def brokerage(m, x):
    if not x.get("brokerage") or x["id"] in m.masked:
        return None
    b = C.display_brokerage(x["brokerage"], m.ID)
    return esc(b) if b else None


def role(m, x):
    k = x.get("kind")
    r = {"agent": "Agent", "buyer": "Buyer", "open_house_visitor": "Open house visitor"}.get(k, "Contact")
    if x.get("is_open_house_host"):
        r = "Open house host" if x["_team"] else "Agent and open house host"
    b = brokerage(m, x)
    return r + (", " + b if b else "")


def engaged(m, x):
    """How the person came to the home, one short phrase per engagement. Each phrase names its kind: a key-box
    showing, a tour an agent told us about, an inquiry, and the three states of the disclosure package.
    (people.LIST_PHRASES sorts these phrases into the lists by how they start.)"""
    out = []
    for e in x.get("engagements") or []:
        t, q = e["type"], e.get("date_quality")
        if e.get("date_label"):
            when = " the " + esc(e["date_label"])
        elif e.get("date"):
            when = (" about " if q == "approximate" else " ") + md(e["date"])
        else:
            when = ""
        if t in C.TOUR_TYPES and e.get("confirmed") is False:
            s = "On the showing list, tour not confirmed"
        elif t == "keybox_showing":
            s = "Toured" + when + " (key box)"
        elif t == "agent_reported_tour":
            s = "Toured" + when
        elif t == "inquiry":
            s = "Asked about the home" + when
        elif t == "disclosure_on_list":
            s = "On the disclosure package list" + ((" (" + when.strip() + ")") if when else "")
        elif t == "disclosure_link_sent":
            s = "Disclosure package sent" + (" through the host" if x["_via_host"] else "") + when
        elif t == "disclosure_opened":
            s = "Opened the disclosure package" + when
        elif t == "open_house_visit":
            s = "Came to the open house" + when
        elif t == "disclosure_shared_by_agent":
            through = m.byid.get(x.get("represented_by")) or {}
            s = "Got the disclosure package from %s" % ("the open house host" if through.get("is_open_house_host") else "their agent")
        else:
            continue
        if s not in out:
            out.append(s)
    return out


def tags(x):
    out = []
    if x.get("price_reaction") in PRICE_TAG:
        out.append(PRICE_TAG[x["price_reaction"]])
    if x.get("interest") in INTEREST_TAG and x["status"] != "passed":
        out.append(INTEREST_TAG[x["interest"]])
    return out


def status_chip(m, x):
    st = x["status"]
    if x["_team"]:
        return chip("Open house host", "hold")
    if st == "offer_submitted":
        return chip("Offer submitted", "offer")
    if st == "writing_offer":
        return chip("Writing an offer", "offer")
    if st == "passed":
        return chip("Passed", "hold")
    later = m.after_answer.get(x["id"]) if st in ("awaiting_reply", "not_yet_contacted") else None
    if later:
        # they answered after the week closed and the box at the top says so: the card must not read as stale beside
        # it. The counts are as of the week end and do not change.
        return chip("Answered %s" % md(later), "good")
    if st == "awaiting_reply":
        # "awaiting reply" read as "never replied"; some of these people answered an earlier follow-up
        return chip("Still waiting", "wait")
    if st == "not_yet_contacted":
        return chip("Not yet reached", "hold")
    if x["_via"]:
        # we follow up through someone else, so this person has given us no answer of their own
        through = m.byid.get(x.get("represented_by")) or {}
        return chip("Through the host" if through.get("is_open_house_host") else "Through their agent", "hold")
    if x in m.fresh_leads and not m.link:
        return chip("Still deciding", "lean")
    return chip("Replied", "good")


def standing_words(m, x):
    """How the brief describes someone we heard from this week. The link copy never says who is near an offer."""
    if x["status"] == "passed":
        return "passed"
    if not m.link:
        if x["status"] in ("offer_submitted", "writing_offer"):
            return "wrote an offer"
        if x.get("offer_intent") in ("yes", "maybe"):
            return "still deciding"
    return {"warm": "interested", "hot": "interested", "cold": "undecided"}.get(x.get("interest"), "in touch")


# how each standing reads after a name or a count: (one person, several)
STANDING_VERB = {"passed": ("passed", "passed"), "wrote an offer": ("wrote an offer", "wrote an offer"),
                 "still deciding": ("is still deciding", "are still deciding"), "interested": ("is interested", "are interested"),
                 "undecided": ("is undecided", "are undecided"), "in touch": ("has not said either way", "have not said either way")}


def comment_kicker(m, x, when=""):
    """Every paraphrased comment says whose report it is."""
    src = "As reported by the host" if x["_via_host"] else "As reported to our team"
    return kicker(src + ((DOT + when) if when else ""))


def unit_count(n, unit):
    """Open house traffic in the host's own unit: '3 groups', '1 visitor'. A group is never turned into people."""
    one, many = UNIT.get(unit or "", ("visitor", "visitors"))
    return n_(n, one, many)


def oh_count(m, o):
    g = o.get("groups")
    if g is None:
        return "no count kept"
    if g == 0:
        return "no visitors"
    return unit_count(g, o.get("counted_unit"))


def oh_total_words(m, n):
    """The since-launch traffic total: '40 groups counted'. When hosts counted in different units it says so and
    nothing is added up as people."""
    if m.oh_unit:
        return "%s counted" % unit_count(n, m.oh_unit)
    units = sorted(set(o.get("counted_unit") for o in m.oh if o.get("groups") is not None and o.get("counted_unit")))
    how = join_and(["some hosts counted %s" % units[0]] + ["some %s" % u for u in units[1:]]) if units else "as each host counted"
    return "%s in total (%s)" % (hk("oh_traffic", num(n)), how)


def oh_label(m):
    one, many = UNIT.get(m.oh_unit or "", ("visitor", "visitors"))
    return ("Open house %s" % many) if m.oh_unit else "Open house traffic"
