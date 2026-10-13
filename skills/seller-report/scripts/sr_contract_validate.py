# -*- coding: utf-8 -*-
"""sr_contract_validate: validate_ledger and validate_curation for the seller-report skill.

Import these through sr_contract (C.validate_ledger, C.validate_curation), not from this file.
Each returns a list of problems as plain strings. An empty list means the file is clean.
Standard library only.
"""
import datetime
import re

from sr_contract import *            # noqa: F401,F403  (the enumerations and helpers)
from sr_contract_counts import *     # noqa: F401,F403  (the counting rules)


FORBIDDEN_LEDGER_KEYS = frozenset((
    "recommendation", "decision_log", "seller_ask",                       # the report gives feedback only
    "provenance", "source_rows", "rid", "rids", "eid", "row_key", "row_keys", "entry_key", "drive_id",
    "message_id", "source_message_id", "raw_name", "name_raw", "full_name", "phone", "phones", "phone_number",
    "emails", "email_address", "tag_notes", "notes_raw", "text_raw",
    # how a reading was arrived at stays in curation.json; a ledger has one build mode and no review state
    "tag_source", "tag_sources", "tag_review", "confirmed_by", "confirmed_on", "corrected_by", "corrected_on", "unsure"))
LEDGER_KEYS = ("schema_version", "meta", "listing", "report", "themes_vocabulary", "contacts", "open_houses", "offers",
               "weeks", "totals", "pricing_tally", "themes_tally", "liked_tally", "price_periods", "offer_watch",
               "team_side", "market", "marketing", "online", "nearby", "next_week", "sources_used", "data_quality")
_UNSAFE_OK = ("hero_photo", "hero_photo_note", "property_page", "source", "status_source")   # never printed as prose
_ID = re.compile(r"^c\d{3,}$")


def _is_day(v):
    if not isinstance(v, str) or not ISO_DAY.match(v):
        return False
    try:
        parse_date(v)
        return True
    except ValueError:
        return False


def _walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            p = "%s.%s" % (path, k) if path else k
            yield p, k, v
            for x in _walk(v, p):
                yield x
    elif isinstance(node, list):
        for i, v in enumerate(node):
            lab = v.get("id") if isinstance(v, dict) and isinstance(v.get("id"), str) else i
            if not isinstance(v, (dict, list)):
                yield "%s[%s]" % (path, lab), None, v
            for x in _walk(v, "%s[%s]" % (path, lab)):
                yield x


def _enum(P, path, v, allowed, optional=False):
    if v is None and optional:
        return
    if v not in allowed:
        P.append("%s: %r is not one of %s" % (path, v, ", ".join(allowed)))


def _same(P, path, stated, want, nullable=False):
    if nullable and stated is None:
        return
    if stated != want:
        P.append("%s: ledger says %r, the rows give %r" % (path, stated, want))


def _check_contact(P, c, p, we, ids, vocab_themes):
    for k in ("id", "name_short", "kind", "engagements", "touches", "feedback_log", "price_reaction", "price_asked",
              "interest", "offer_intent", "status", "softened", "themes", "liked", "next_followup_date",
              "is_open_house_host", "team_side", "represented_by", "phone_out_of_service", "followup",
              "feedback_safe", "feedback_date", "brokerage"):
        if k not in c:
            P.append("%s: missing %s" % (p, k))
    if any(k not in c for k in ("engagements", "touches", "feedback_log", "status", "themes", "liked")):
        return
    _enum(P, p + ".kind", c.get("kind"), KINDS)
    _enum(P, p + ".price_reaction", c.get("price_reaction"), PRICE_REACTIONS)
    _enum(P, p + ".interest", c.get("interest"), INTEREST)
    _enum(P, p + ".offer_intent", c.get("offer_intent"), OFFER_INTENT)
    _enum(P, p + ".status", c.get("status"), STATUSES)
    _enum(P, p + ".reached_through", c.get("reached_through"), REACHED_THROUGH, optional=True)
    if c.get("price_asked") not in (True, False, None):
        P.append("%s.price_asked: must be true, false or null" % p)
    for k in ("softened", "is_open_house_host", "team_side", "phone_out_of_service"):
        if not isinstance(c.get(k), bool):
            P.append("%s.%s: must be true or false" % (p, k))
    if c.get("name_recorded", True) and not SHORT_NAME.match(c.get("name_short") or ""):
        P.append("%s.name_short: %r is not in the 'First L.' form (set name_recorded false for a label)" % (p, c.get("name_short")))
    if c.get("next_followup_date") is not None and not _is_day(c["next_followup_date"]):
        P.append("%s.next_followup_date: not an ISO date" % p)
    rb = c.get("represented_by")
    if rb is not None:
        if rb not in ids or rb == c.get("id"):
            P.append("%s.represented_by: %r is not another contact's id" % (p, rb))
        elif ids[rb].get("represented_by"):
            P.append("%s.represented_by: %s is itself reached through someone else" % (p, rb))
        if c.get("touches"):
            P.append("%s: a buyer reached through an agent carries no touches of their own (log them on the agent)" % p)
    own = [e for e in c["engagements"] if e.get("type") in TOUR_TYPES + DISCLOSURE_TYPES + ("inquiry",)]
    if c.get("team_side") and not c.get("is_open_house_host"):
        P.append("%s.team_side: only an open house host can be team side" % p)
    if c.get("is_open_house_host") and not rb and c.get("team_side") != (not own):
        P.append("%s.team_side: a host is team side unless they brought a buyer of their own (engagements say %s)"
                 % (p, "they did" if own else "they did not"))
    for i, e in enumerate(c["engagements"]):
        q = "%s.engagements[%d]" % (p, i)
        _enum(P, q + ".type", e.get("type"), ENGAGEMENT_TYPES)
        _enum(P, q + ".date_quality", e.get("date_quality"), DATE_QUALITY)
        if (e.get("date") is None) != (e.get("date_quality") == "missing"):
            P.append("%s: date and date_quality disagree (a missing date is null with quality 'missing')" % q)
        elif e.get("date") is not None and (not _is_day(e["date"]) or e["date"] > we):
            P.append("%s.date: %r is not an ISO date on or before the week end" % (q, e.get("date")))
        if e.get("confirmed", True) not in (True, False):
            P.append("%s.confirmed: must be true or false" % q)
    seen = set()
    for i, t in enumerate(c["touches"]):
        q = "%s.touches[%d]" % (p, i)
        _enum(P, q + ".channel", t.get("channel"), CHANNELS)
        _enum(P, q + ".direction", t.get("direction"), DIRECTIONS)
        _enum(P, q + ".outcome", t.get("outcome"), OUTCOMES)
        _enum(P, q + ".date_quality", t.get("date_quality", "exact"), ("exact", "approximate"))
        if not _is_day(t.get("date")) or t["date"] > we:
            P.append("%s.date: %r is not an ISO date on or before the week end (later entries go in report.since_week_closed)" % (q, t.get("date")))
            return
        if not isinstance(t.get("summary_safe"), str) or not t["summary_safe"].strip():
            P.append("%s.summary_safe: missing" % q)
        if t.get("direction") == "inbound" and t.get("outcome") not in ("replied", "unknown"):
            P.append("%s.outcome: an inbound touch is 'replied' or 'unknown'" % q)
        if t.get("direction") == "outbound" and t.get("outcome") == "replied":
            P.append("%s.outcome: an outbound touch that was answered is 'reached'" % q)
        if t.get("direction") == "outbound" and t.get("channel") != "unknown":
            key = (t["date"], channel_family(t.get("channel")))
            if key in seen:
                P.append("%s: second outbound %s touch on %s (one per channel per day; a call that went to voicemail is one touch)"
                         % (q, key[1], key[0]))
            seen.add(key)
    days = set()
    for i, e in enumerate(c["feedback_log"]):
        q = "%s.feedback_log[%d]" % (p, i)
        if not _is_day(e.get("date")) or e["date"] > we:
            P.append("%s.date: %r is not an ISO date on or before the week end" % (q, e.get("date")))
            return
        if not isinstance(e.get("text_safe"), str) or not e["text_safe"].strip():
            P.append("%s.text_safe: missing" % q)
        _enum(P, q + ".price_reaction", e.get("price_reaction"), PRICE_REACTIONS)
        _enum(P, q + ".source", e.get("source"), FEEDBACK_SOURCES)
        if e.get("price_asked") not in (True, False, None):
            P.append("%s.price_asked: must be true, false or null" % q)
        if not isinstance(e.get("softened"), bool) or not isinstance(e.get("counts_as_conversation"), bool):
            P.append("%s: softened and counts_as_conversation must be true or false" % q)
        if e.get("counts_as_conversation"):
            if e["date"] in days:
                P.append("%s: second conversation on %s (a conversation is one person on one day)" % (q, e["date"]))
            days.add(e["date"])
            if e.get("source") == "open_house_host":
                P.append("%s: a host's secondhand recap does not count as a conversation" % q)
            if e.get("price_reaction") == "unknown":
                P.append("%s.price_reaction: a counted conversation is too_high, fair_or_positive or not_raised" % q)
        for k in e.get("themes") or []:
            if k not in c["themes"]:
                P.append("%s.themes: %r is not in the person's themes" % (q, k))
        for k in e.get("liked") or []:
            if k not in c["liked"]:
                P.append("%s.liked: %r is not in the person's liked list" % (q, k))
    for k in c["themes"]:
        if k not in vocab_themes:
            P.append("%s.themes: %r is not in themes_vocabulary" % (p, k))
    for k in c["liked"]:
        if k not in LIKED_KEYS:
            P.append("%s.liked: %r is not in the liked vocabulary" % (p, k))
    if ("other" in c["themes"]) != bool((c.get("theme_other") or "").strip()):
        P.append("%s: theme 'other' and theme_other go together" % p)
    if ("other" in c["liked"]) != bool((c.get("liked_other") or "").strip()):
        P.append("%s: liked 'other' and liked_other go together" % p)
    if c.get("softened") != (bool(c.get("feedback_softened")) or any(e.get("softened") for e in c["feedback_log"])):
        P.append("%s.softened: must be true exactly when the comment or one of the feedback entries was softened" % p)
    if c.get("feedback_date") is not None and c.get("feedback_safe") is None:
        P.append("%s: feedback_date without feedback_safe" % p)
    if c.get("feedback_date") is not None and (not _is_day(c["feedback_date"]) or c["feedback_date"] > we):
        P.append("%s.feedback_date: not an ISO date on or before the week end" % p)
    if not is_counted(c):
        if rb is not None and c.get("status") != "through_agent":
            P.append("%s.status: a buyer reached through an agent is 'through_agent'" % p)
        return
    log = counted_feedback(c, we)
    _same(P, p + ".price_reaction", c.get("price_reaction"), derive_price_reaction(c, we))
    _same(P, p + ".price_asked", c.get("price_asked"), derive_price_asked(c, we))
    if log and not c.get("feedback_safe"):
        P.append("%s: has a counted conversation but no feedback_safe" % p)
    if log and any(e.get("themes") for e in log) and set(k for e in log for k in e.get("themes") or []) != set(c["themes"]):
        P.append("%s.themes: must be the themes of the person's counted conversations taken together" % p)
    if not log and (c["themes"] or c["liked"]):
        P.append("%s: themes and liked points need a counted conversation" % p)
    f = contact_facts(c, we)
    st, base = c.get("status"), base_status(c, we)
    if st == "through_agent":
        P.append("%s.status: 'through_agent' needs represented_by" % p)
    elif (st == "not_yet_contacted") != (base == "not_yet_contacted"):
        P.append("%s.status: %s, but the touches give %s" % (p, st, base))
    elif st == "awaiting_reply" and not (f["waiting"] or not f["replies"]):
        P.append("%s.status: awaiting_reply, but their last answer (%s) is not older than our last follow-up (%s)"
                 % (p, f["last_reply_date"], f["last_outbound_date"]))
    elif st == "replied" and base != "replied":
        P.append("%s.status: replied, but our latest follow-up (%s) has not been answered" % (p, f["last_outbound_date"]))
    if st == "passed" and c.get("interest") != "passed" or (c.get("interest") == "passed" and st != "passed"):
        P.append("%s: status 'passed' and interest 'passed' go together" % p)
    if isinstance(c.get("followup"), dict):
        for k in FOLLOWUP_KEYS:
            _same(P, "%s.followup.%s" % (p, k), c["followup"].get(k), f[k])


def _check_market(P, m, R):
    for k in ("as_of", "data_through", "refreshed_for_this_issue", "scope", "source", "method", "sample", "days_to_contract",
              "subject_on_report_date", "sales"):                # statement_safe is optional and is never printed
        if k not in m:
            P.append("market: missing %s" % k)
    if any(x.startswith("market: missing") for x in P):
        return
    if not _is_day(m["as_of"]) or not _is_day(m["data_through"]) or not isinstance(m["refreshed_for_this_issue"], bool):
        P.append("market: as_of and data_through are ISO dates and refreshed_for_this_issue is true or false")
    used = sorted(s.get("days_to_contract") for s in m["sales"] if s.get("used_in_average"))
    if not used or any(not isinstance(v, int) for v in used):
        P.append("market.sales: every sale used in the average needs days_to_contract")
        return
    mid = len(used) // 2
    med = used[mid] if len(used) % 2 else (used[mid - 1] + used[mid]) / 2.0
    dtc, smp, sub = m["days_to_contract"], m["sample"], m["subject_on_report_date"]
    for name, got, want in (("sample.used", smp.get("used"), len(used)), ("sample.closed", smp.get("closed"), len(m["sales"])),
                            ("sample.excluded", smp.get("excluded"), len(m["sales"]) - len(used)),
                            ("days_to_contract.values_sorted", dtc.get("values_sorted"), used),
                            ("days_to_contract.average", dtc.get("average"), int(sum(used) / float(len(used)) + 0.5)),
                            ("days_to_contract.median", dtc.get("median"), int(med + 0.5)),
                            ("days_to_contract.shortest", dtc.get("shortest"), used[0]),
                            ("days_to_contract.longest", dtc.get("longest"), used[-1]),
                            ("subject_on_report_date.date", sub.get("date"), R["report_date"]),
                            ("subject_on_report_date.days_on_market", sub.get("days_on_market"), R["days_on_market"]),
                            ("subject_on_report_date.of_sales", sub.get("of_sales"), len(used)),
                            ("subject_on_report_date.sales_under_contract_by_that_day", sub.get("sales_under_contract_by_that_day"),
                             len([v for v in used if v <= R["days_on_market"]]))):
        _same(P, "market." + name, got, want)


def _check_marketing(P, m):
    if not _is_day(m.get("as_of")) or not isinstance(m.get("channels"), list) or not m.get("channels"):
        P.append("marketing: needs as_of (an ISO date) and a channels list")
        return
    for i, ch in enumerate(m["channels"]):
        q = "marketing.channels[%d]" % i
        _enum(P, q + ".status", ch.get("status"), MARKETING_STATUS_KEYS)
        if not (ch.get("channel") or "").strip() or not _is_day(ch.get("checked")) or not (ch.get("detail") or "").strip():
            P.append("%s: needs channel, checked (an ISO date) and detail" % q)


def _check_online(P, o, n_weeks):
    """Optional online views and saves per portal and week. The weekly and since-launch sums are derived."""
    if not isinstance(o, dict) or not _is_day(o.get("as_of")):
        P.append("online: needs as_of (an ISO date), portals and weeks")
        return
    portals = o.get("portals")
    if not isinstance(portals, list) or not portals or any(not isinstance(p, str) or not p.strip() for p in portals) \
            or len(set(portals)) != len(portals):
        P.append("online.portals: a list of portal names, each once")
        return
    seen = set()
    for i, w in enumerate(o.get("weeks") if isinstance(o.get("weeks"), list) else [None]):
        q = "online.weeks[%d]" % i
        if not isinstance(w, dict) or not isinstance(w.get("n"), int) or not 1 <= w["n"] <= n_weeks or w["n"] in seen:
            P.append("%s: needs n, the number of a week of this listing, used once" % q)
            continue
        seen.add(w["n"])
        for kind in ("views", "saves"):
            vals = w.get(kind) or {}
            if not isinstance(vals, dict) or any(k not in portals for k in vals):
                P.append("%s.%s: keyed by a name in online.portals" % (q, kind))
            elif any(v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < 0) for v in vals.values()):
                P.append("%s.%s: every figure is a whole number, or null when not recorded" % (q, kind))


def _check_nearby(P, nb, L):
    """Optional watch list of similar homes nearby. Public street addresses are allowed in this block only."""
    if not isinstance(nb, dict) or not _is_day(nb.get("as_of")) or not isinstance(nb.get("checked_for_this_issue"), bool) \
            or not (nb.get("scope") or "").strip() or not isinstance(nb.get("homes"), list):
        P.append("nearby: needs as_of (an ISO date), checked_for_this_issue (true or false), scope and homes")
        return
    if len(nb["homes"]) > LIMITS["nearby_max_homes"]:
        P.append("nearby.homes: at most %d homes are watched" % LIMITS["nearby_max_homes"])
    own = re.sub(r"[^a-z0-9]+", " ", (L.get("address") or "").lower()).strip()
    for i, h in enumerate(nb["homes"]):
        q = "nearby.homes[%d]" % i
        if not isinstance(h, dict) or not (h.get("address") or "").strip():
            P.append("%s: needs an address" % q)
            continue
        if re.sub(r"[^a-z0-9]+", " ", h["address"].lower()).strip() == own:
            P.append("%s: is this listing, not a nearby home" % q)
        _enum(P, q + ".status", h.get("status"), NEARBY_STATUSES)
        _enum(P, q + ".change", h.get("change"), NEARBY_CHANGES)
        for k in ("list_price", "sold_price", "price_before", "days_on_market", "sqft"):
            if h.get(k) is not None and (not isinstance(h[k], int) or isinstance(h[k], bool) or h[k] < 0):
                P.append("%s.%s: a whole number, or null when not recorded" % (q, k))
        if h.get("change") not in (None, "none") and not _is_day(h.get("change_date")):
            P.append("%s.change_date: a change needs the day it happened" % q)
        if h.get("change_date") is not None and (not _is_day(h["change_date"]) or h["change_date"] > nb["as_of"]):
            P.append("%s.change_date: an ISO date no later than as_of" % q)
        if h.get("status") == "sold" and not isinstance(h.get("sold_price"), int):
            P.append("%s.sold_price: a sold home needs its price" % q)
        if h.get("change") == "price_change" and (not isinstance(h.get("price_before"), int) or not isinstance(h.get("list_price"), int)):
            P.append("%s: a price change needs price_before and list_price" % q)


def validate_ledger(d, identity=None):
    """Checks a ledger against the contract. Returns a list of problems; an empty list means it is clean.

    There is one build mode: every ledger that passes is ready to render and send.
    identity (from load_identity) adds the brand blocklist scan and lets Graeham's own phone and email through."""
    P = []
    if not isinstance(d, dict):
        return ["ledger: not an object"]
    for k in LEDGER_KEYS:
        if k not in d:
            P.append("ledger: missing top-level key %s" % k)
    for k in d:
        if k not in LEDGER_KEYS:
            P.append("ledger: unknown top-level key %s" % k)
    for path, k, _ in _walk(d):
        if k in FORBIDDEN_LEDGER_KEYS:
            P.append("%s: key %r is not allowed in a ledger" % (path, k))
    if P:
        return P
    if d["schema_version"] != SCHEMA_VERSION:
        P.append("schema_version: expected %d" % SCHEMA_VERSION)
    L, R, M = d["listing"], d["report"], d["meta"]
    for k in ("slug", "address", "city", "state", "beds", "baths", "sqft", "property_type", "list_date", "list_price",
              "price_history", "status", "mls", "hero_photo"):
        if k not in L:
            P.append("listing: missing %s" % k)
    for k in ("issue_number", "report_date", "week_start", "week_end", "days_on_market", "days_on_market_at_week_end",
              "weeks_on_market", "tracking", "since_week_closed"):
        if k not in R:
            P.append("report: missing %s" % k)
    for k in ("slug", "built_at"):
        if k not in M:
            P.append("meta: missing %s" % k)
    if P:
        return P
    if M["slug"] != L["slug"] or slugify(L["slug"]) != L["slug"]:
        P.append("listing.slug: must be a slug and match meta.slug")
    for k in ("list_date",):
        if not _is_day(L[k]):
            P.append("listing.%s: not an ISO date" % k)
    for k in ("report_date", "week_start", "week_end"):
        if not _is_day(R[k]):
            P.append("report.%s: not an ISO date" % k)
    hist = L["price_history"]
    if not isinstance(hist, list) or not hist:
        P.append("listing.price_history: needs at least the 'listed' entry")
    else:
        for i, e in enumerate(hist):
            _enum(P, "listing.price_history[%d].event" % i, e.get("event"), PRICE_EVENTS)
            if not _is_day(e.get("date")) or not isinstance(e.get("price"), int):
                P.append("listing.price_history[%d]: needs an ISO date and a whole-dollar price" % i)
        if [e.get("date") for e in hist] != sorted(e.get("date") or "" for e in hist) or hist[0].get("event") != "listed":
            P.append("listing.price_history: oldest first, starting with the 'listed' entry")
    if P:
        return P
    ws, we, rd = R["week_start"], R["week_end"], R["report_date"]
    if parse_date(ws).weekday() != 0:
        P.append("report.week_start: %s is not a Monday" % ws)
    if iso(week_end(ws)) != we:
        P.append("report.week_end: must be the Sunday after week_start")
    if iso(parse_date(we) + datetime.timedelta(days=1)) != rd:
        P.append("report.report_date: must be the Monday after week_end")
    if L["list_date"] > we:
        P.append("listing.list_date: after the report week")
    if any(e["date"] > rd for e in hist):
        P.append("listing.price_history: holds a change dated after the report date")
    if L["list_price"] != price_on(hist, rd):
        P.append("listing.list_price: must be the price in effect on the report date (%s)" % price_on(hist, rd))
    if not isinstance(R["issue_number"], int) or R["issue_number"] < 1:
        P.append("report.issue_number: must be a whole number from 1")
    _same(P, "report.days_on_market", R["days_on_market"], days_on_market(L["list_date"], rd))
    _same(P, "report.days_on_market_at_week_end", R["days_on_market_at_week_end"], days_on_market(L["list_date"], we))
    tr = R["tracking"] if isinstance(R["tracking"], dict) else {}
    for k in TRACKING_KEYS:
        if not isinstance(tr.get(k), bool):
            P.append("report.tracking.%s: must be true or false" % k)
    since = R["since_week_closed"] if isinstance(R["since_week_closed"], dict) else {}
    if not isinstance(since.get("items"), list) or not _is_day(since.get("through")) or since.get("through") < we:
        P.append("report.since_week_closed: needs 'through' (an ISO date on or after the week end) and an 'items' list")
    if P:
        return P
    cids = dict((c.get("id"), c) for c in d["contacts"] if isinstance(c, dict))
    for i, it in enumerate(since["items"]):
        q = "report.since_week_closed.items[%d]" % i
        _enum(P, q + ".kind", it.get("kind"), SINCE_KINDS)
        if not _is_day(it.get("date")) or it["date"] <= we or it["date"] > since["through"]:
            P.append("%s.date: must be after the week end and no later than 'through'" % q)
        if it.get("contact_id") is not None and it["contact_id"] not in cids:
            P.append("%s.contact_id: unknown contact" % q)
        if not (it.get("summary_safe") or "").strip():
            P.append("%s.summary_safe: missing" % q)
        if it.get("kind") == "offer" and re.search(r"\$|\d{3},\d{3}", it.get("summary_safe") or ""):
            P.append("%s: an offer logged after the week closed is noted without its price or terms" % q)
    V = d["themes_vocabulary"]
    if V != themes_vocabulary():
        P.append("themes_vocabulary: must equal sr_contract.themes_vocabulary() (the vocabulary is fixed)")
    vocab = set(THEME_KEYS)
    if len(cids) != len(d["contacts"]):
        P.append("contacts: ids must be unique")
    for c in d["contacts"]:
        if not isinstance(c.get("id"), str) or not _ID.match(c["id"]):
            P.append("contacts: id %r is not in the form c001" % (c.get("id"),))
            continue
        n = len(P)
        _check_contact(P, c, "contacts[%s]" % c["id"], we, cids, vocab)
        if len(P) > n and any("missing" in x for x in P[n:]):
            return P
    labels = {}
    for c in d["contacts"]:
        if is_counted(c):
            labels.setdefault((c.get("name_short"), c.get("brokerage")), []).append(c["id"])
    for (nm, _), who in sorted(labels.items(), key=lambda kv: kv[1]):
        if len(who) > 1:
            P.append("contacts: %s share the label %r; a seller could not tell them apart" % (", ".join(who), nm))
    for i, o in enumerate(d["open_houses"]):
        q = "open_houses[%d]" % i
        for k in ("date", "date_quality", "host", "groups", "groups_source", "counted_unit", "recap_safe", "disclosure_requests"):
            if k not in o:
                P.append("%s: missing %s" % (q, k))
        if not _is_day(o.get("date")) or o["date"] > we:
            P.append("%s.date: not an ISO date on or before the week end" % q)
        _enum(P, q + ".groups_source", o.get("groups_source"), GROUPS_SOURCES)
        _enum(P, q + ".counted_unit", o.get("counted_unit"), COUNTED_UNITS)
        _enum(P, q + ".date_quality", o.get("date_quality"), ("exact", "approximate"))
        if (o.get("groups") is None) != (o.get("groups_source") == "not_recorded"):
            P.append("%s: groups is null exactly when groups_source is 'not_recorded'" % q)
        if o.get("host_contact_id") is not None and o["host_contact_id"] not in cids:
            P.append("%s.host_contact_id: unknown contact" % q)
    for i, o in enumerate(d["offers"]):
        q = "offers[%d]" % i
        for k in ("date", "agent_short", "brokerage", "price", "pct_of_list", "terms_summary", "state", "contact_id"):
            if k not in o:
                P.append("%s: missing %s" % (q, k))
        if not _is_day(o.get("date")) or o["date"] > we:
            P.append("%s.date: not an ISO date on or before the week end" % q)
            continue
        _enum(P, q + ".state", o.get("state"), OFFER_STATES)
        if o.get("contact_id") is not None and o["contact_id"] not in cids:
            P.append("%s.contact_id: unknown contact" % q)
        if isinstance(o.get("price"), int) and o.get("pct_of_list") is not None:
            want = round(100.0 * o["price"] / price_on(hist, o["date"]), 1)
            if abs(o["pct_of_list"] - want) > 0.05:
                P.append("%s.pct_of_list: ledger says %s, price over the list price that day gives %s" % (q, o["pct_of_list"], want))
    for i, r in enumerate((d["pricing_tally"] or {}).get("open_house_price_remarks") or []):
        _enum(P, "pricing_tally.open_house_price_remarks[%d].reaction" % i, r.get("reaction"), REMARK_REACTIONS)
        if not _is_day(r.get("date")) or not (r.get("remark_safe") or "").strip():
            P.append("pricing_tally.open_house_price_remarks[%d]: needs a date and remark_safe" % i)
    if P:
        return P

    # where each person is listed under "The details", and what they have said about an offer
    offer_ids = set(o.get("contact_id") for o in d["offers"] if o.get("contact_id"))
    for c in d["contacts"]:
        p, lists = "contacts[%s]" % c["id"], contact_lists(c)
        for k, wanted in (("lists", lists), ("primary_list", lists[0] if lists else None),
                          ("offer_word", derive_offer_word(c, offer_ids)), ("active_this_week", active_in_week(c, ws, we))):
            if k not in c:
                P.append("%s: missing %s" % (p, k))
            else:
                _same(P, "%s.%s" % (p, k), c[k], wanted)
    if d["online"] is not None:
        _check_online(P, d["online"], len(list_weeks(L["list_date"], ws)))
    if P:
        return P

    # the stored numbers against the rows
    want = recount(d)
    T = d["totals"]
    for k in sorted(set(T) | set(want["totals"])):
        if k not in want["totals"]:
            P.append("totals.%s: unknown key" % k)
        elif k not in T:
            P.append("totals: missing %s" % k)
        else:
            _same(P, "totals." + k, T[k], want["totals"][k], nullable=k in NULLABLE_COUNTS)
    for flag, keys in TRACKING_KEYS.items():
        for k in keys:
            if k in T and (T[k] is None) == bool(tr[flag]):
                P.append("totals.%s: is %s while report.tracking.%s is %s (null means not recorded)"
                         % (k, "null" if T[k] is None else "a number", flag, str(tr[flag]).lower()))
    _same(P, "report.weeks_on_market", R["weeks_on_market"], len(want["weeks"]))
    if len(d["weeks"]) != len(want["weeks"]):
        P.append("weeks: expected %d weeks from the list week to the report week (quiet weeks are kept), found %d"
                 % (len(want["weeks"]), len(d["weeks"])))
    else:
        for w, x in zip(d["weeks"], want["weeks"]):
            for k in sorted(set(w) | set(x)):
                if k == "label":
                    continue
                if k not in x:
                    P.append("weeks[%s].%s: unknown key" % (x["n"], k))
                elif k not in w:
                    P.append("weeks[%s]: missing %s" % (x["n"], k))
                else:
                    _same(P, "weeks[%s].%s" % (x["n"], k), w[k], x[k], nullable=k in NULLABLE_COUNTS)
            for flag, keys in TRACKING_KEYS.items():
                for k in keys:
                    if k in w and w[k] is not None and not tr[flag]:
                        P.append("weeks[%s].%s: a number while report.tracking.%s is false" % (x["n"], k, flag))
            if "label" in w and has_dash(w["label"]):
                P.append("weeks[%s].label: has a dash" % x["n"])
    pt = dict(d["pricing_tally"])
    pt.pop("open_house_price_remarks", None)
    for name, stated, wanted in (("pricing_tally", pt, want["pricing_tally"]), ("themes_tally", d["themes_tally"], want["themes_tally"]),
                                 ("liked_tally", d["liked_tally"], want["liked_tally"])):
        if stated != wanted:
            for k in sorted(set(stated) | set(wanted)):
                if stated.get(k) != wanted.get(k):
                    P.append("%s.%s: ledger says %r, the rows give %r" % (name, k, stated.get(k), wanted.get(k)))
    if "open_house_price_remarks" not in d["pricing_tally"]:
        P.append("pricing_tally: missing open_house_price_remarks (an empty list when there are none)")
    if d["price_periods"] != want["price_periods"]:
        P.append("price_periods: does not match the record split by event date against listing.price_history")
    stated_watch = [dict((k, w.get(k)) for k in ("contact_id", "lead_state", "last_touch_date", "days_since_last_touch")) for w in d["offer_watch"]]
    if stated_watch != want["offer_watch"]:
        P.append("offer_watch: must list every open offer lead, 'live' only with contact in the last %d days (rows give %r)"
                 % (LIMITS["offer_lead_fresh_days"], [(w["contact_id"], w["lead_state"]) for w in want["offer_watch"]]))
    span = max(1, R["days_on_market_at_week_end"] + 1)
    if T.get("outbound_distinct_days", 0) > span and not any(t["date"] < L["list_date"] for c in d["contacts"] for t in c["touches"]):
        P.append("totals.outbound_distinct_days: %d separate days in %d days on the market" % (T["outbound_distinct_days"], span))

    # everything a seller could read
    allow = [identity.get("phone"), identity.get("email")] if identity else []
    for path, k, v in _walk(d):
        if isinstance(v, str) and k not in _UNSAFE_OK and not path.startswith("themes_vocabulary"):
            streets = path.split(".")[0].split("[")[0] in ("contacts", "open_houses", "next_week", "report", "offer_watch", "pricing_tally")
            for why in safe_text_problems(v, allow=allow, own_address=L["address"], streets=streets):
                P.append("%s: %s" % (path, why))
            if identity and k != "brokerage":      # another agent's brokerage is a fact; see display_brokerage
                for b in find_blocked(v, identity):
                    P.append("%s: holds a blocked brand value (see identity.json)" % path)
    if any(not isinstance(s, str) or not s.strip() for s in d["next_week"] + d["data_quality"]):
        P.append("next_week and data_quality: every item is a sentence")
    for i, s in enumerate(d["sources_used"]):
        _enum(P, "sources_used[%d].kind" % i, s.get("kind") if isinstance(s, dict) else None, SOURCE_KINDS)
        if isinstance(s, dict) and (not (s.get("label") or "").strip() or not _is_day(s.get("as_of"))):
            P.append("sources_used[%d]: needs a label and an as_of date" % i)
    if d["market"] is not None:
        _check_market(P, d["market"], R)
    if d["marketing"] is not None:
        _check_marketing(P, d["marketing"])
    if d["nearby"] is not None:
        _check_nearby(P, d["nearby"], L)
    for i, t in enumerate(d["team_side"]):
        if not (t.get("name_short") or "").strip() or not (t.get("role") or "").strip() or not isinstance(t.get("sessions_hosted"), int):
            P.append("team_side[%d]: needs name_short, role and sessions_hosted" % i)
        if t.get("contact_id") is not None and (t["contact_id"] not in cids or not cids[t["contact_id"]].get("team_side")):
            P.append("team_side[%d].contact_id: must be a team-side contact" % i)
    if not d["sources_used"]:
        P.append("sources_used: empty; a ledger names every source the operator handed over")
    return P


CURATION_KEYS = ("schema_version", "slug", "updated", "people", "entries", "open_houses", "offers", "ignored_rows",
                 "date_corrections", "overrides", "next_week")


def validate_curation(d):
    """Checks curation.json (Claude's reading of the notes plus the operator's corrections). Returns a list of problems."""
    P = []
    if not isinstance(d, dict):
        return ["curation: not an object"]
    for k in CURATION_KEYS:
        if k not in d:
            P.append("curation: missing %s" % k)
    for k in d:
        if k not in CURATION_KEYS:
            P.append("curation: unknown key %s" % k)
    if P:
        return P
    if d["schema_version"] != SCHEMA_VERSION:
        P.append("schema_version: expected %d" % SCHEMA_VERSION)
    used = {}
    for cid, p in sorted(d["people"].items()):
        q = "people[%s]" % cid
        if not _ID.match(cid):
            P.append("%s: id is not in the form c001" % q)
        if not isinstance(p.get("rows"), list) or not p["rows"]:
            P.append("%s.rows: needs at least one raw row key" % q)
        for r in p.get("rows") or []:
            if r in used:
                P.append("%s.rows: row %s is already merged into %s" % (q, r, used[r]))
            used[r] = cid
        _enum(P, q + ".kind", p.get("kind"), KINDS)
        _enum(P, q + ".reached_through", p.get("reached_through"), REACHED_THROUGH, optional=True)
        if p.get("represented_by") is not None and p["represented_by"] not in d["people"]:
            P.append("%s.represented_by: unknown person" % q)
        tags = p.get("tags") or {}
        for k, tag in tags.items():
            if k not in TAG_FIELDS:
                P.append("%s.tags: unknown tag %r" % (q, k))
                continue
            if not isinstance(tag, dict) or "value" not in tag:
                P.append("%s.tags.%s: needs {value, provenance}" % (q, k))
                continue
            _enum(P, "%s.tags.%s.provenance" % (q, k), tag.get("provenance"), PROVENANCE)
            v = tag["value"]
            if k == "price_reaction":
                _enum(P, "%s.tags.%s.value" % (q, k), v, PRICE_REACTIONS)
            elif k == "interest":
                _enum(P, "%s.tags.%s.value" % (q, k), v, INTEREST)
            elif k == "offer_intent":
                _enum(P, "%s.tags.%s.value" % (q, k), v, OFFER_INTENT)
            elif k == "price_asked" and v not in (True, False, None):
                P.append("%s.tags.price_asked.value: must be true, false or null" % q)
            elif k == "themes" and any(x not in THEME_KEYS for x in v or []):
                P.append("%s.tags.themes.value: outside the theme vocabulary" % q)
            elif k == "liked" and any(x not in LIKED_KEYS for x in v or []):
                P.append("%s.tags.liked.value: outside the liked vocabulary" % q)
            elif k == "next_followup_date" and v is not None and not _is_day(v):
                P.append("%s.tags.next_followup_date.value: not an ISO date" % q)
            if tag.get("provenance") == "corrected_by_operator" and not tag.get("corrected_on"):
                P.append("%s.tags.%s: a value the operator corrected carries corrected_on" % (q, k))
        for k in ("feedback_safe", "theme_other", "liked_other", "status_note_safe", "offer_basis_safe"):
            for why in safe_text_problems(p.get(k) or "", streets=False):
                P.append("%s.%s: %s" % (q, k, why))
        for kind, fld in (("touches", "summary_safe"), ("feedback", "text_safe")):       # dated lines not tied to a sheet note
            for i, it in enumerate((p.get("extra") or {}).get(kind) or []):
                for why in safe_text_problems((it or {}).get(fld) or "", streets=False):
                    P.append("%s.extra.%s[%d].%s: %s" % (q, kind, i, fld, why))
        for rk, engs in sorted((p.get("engagements") or {}).items()):
            for i, e in enumerate(engs or []):
                for why in safe_text_problems((e or {}).get("note") or "", streets=False):
                    P.append("%s.engagements[%s][%d].note: %s" % (q, rk, i, why))
    for key, e in sorted(d["entries"].items()):
        q = "entries[%s]" % key
        if key.count("/") != 3:
            P.append("%s: not an entry key (see sr_contract.entry_key)" % q)
        for i, t in enumerate(e.get("touches") or []):
            _enum(P, "%s.touches[%d].channel" % (q, i), t.get("channel"), CHANNELS)
            _enum(P, "%s.touches[%d].direction" % (q, i), t.get("direction"), DIRECTIONS)
            _enum(P, "%s.touches[%d].outcome" % (q, i), t.get("outcome"), OUTCOMES)
            for why in safe_text_problems(t.get("summary_safe") or "", streets=False):
                P.append("%s.touches[%d].summary_safe: %s" % (q, i, why))
        fb = e.get("feedback")
        if fb is not None:
            _enum(P, q + ".feedback.price_reaction", fb.get("price_reaction"), PRICE_REACTIONS)
            _enum(P, q + ".feedback.source", fb.get("source"), FEEDBACK_SOURCES)
            for why in safe_text_problems(fb.get("text_safe") or "", streets=False):
                P.append("%s.feedback.text_safe: %s" % (q, why))
            if not isinstance(fb.get("softened"), bool):
                P.append("%s.feedback.softened: must be true or false" % q)
        _enum(P, q + ".provenance", e.get("provenance"), PROVENANCE)
    for key, why in d["ignored_rows"].items():
        if key in used:
            P.append("ignored_rows[%s]: this row is also merged into %s" % (key, used[key]))
        if not (why or "").strip():
            P.append("ignored_rows[%s]: say why" % key)
    for key, c in d["date_corrections"].items():
        if not _is_day(c.get("date")) or c.get("date_quality") not in ("exact", "approximate") or not (c.get("reason") or "").strip():
            P.append("date_corrections[%s]: needs date, date_quality and reason" % key)
    for i, o in enumerate(d["overrides"]):
        if not all((o.get(k) or "") for k in ("path", "by", "on")) or "value" not in o:
            P.append("overrides[%d]: needs path, value, by and on" % i)
    return P
