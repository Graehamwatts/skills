# -*- coding: utf-8 -*-
"""sr_contract: the shared contract for the seller-report skill.

Every other script in this skill imports this one module:

    import sr_contract as C

It holds the enumerations and the theme vocabulary (references/data-contract.md describes them), the
date helpers, short_name, slugify, the stable row and entry keys, load_identity, the privacy scan for
seller-facing text, and money / date / count formatters that never emit an em dash or an en dash.

The counting rules live in sr_contract_counts.py (references/counting-rules.md says the same thing in
words) and the validators in sr_contract_validate.py. Both are reachable from here, so callers never
import them directly:

    C.recount(ledger)            every derived number, recomputed from the rows
    C.finish_ledger(ledger)      writes those numbers into the ledger
    C.validate_ledger(ledger)    a list of problems, empty when the ledger is clean
    C.validate_curation(cur)     the same for curation.json

Standard library only. No real client data belongs in this file.
"""
import datetime
import hashlib
import json
import importlib
import os
import re
import sys
import unicodedata

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------------------------
# enumerations
# ---------------------------------------------------------------------------------------------
KINDS = ("agent", "buyer", "open_house_visitor")
TOUR_TYPES = ("keybox_showing", "agent_reported_tour")
DISCLOSURE_TYPES = ("disclosure_on_list", "disclosure_link_sent", "disclosure_opened", "disclosure_shared_by_agent")
ENGAGEMENT_TYPES = TOUR_TYPES + ("inquiry", "open_house_visit") + DISCLOSURE_TYPES
DATE_QUALITY = ("exact", "approximate", "missing")
CHANNELS = ("call", "voicemail", "text", "email", "in_person", "unknown")
DIRECTIONS = ("outbound", "inbound", "unknown")
OUTCOMES = ("sent", "left_voicemail", "no_answer", "did_not_connect", "reached", "replied", "unknown")
PRICE_BUCKETS = ("too_high", "fair_or_positive", "not_raised")
PRICE_REACTIONS = PRICE_BUCKETS + ("unknown",)
INTEREST = ("hot", "warm", "cold", "passed", "unknown")
OFFER_INTENT = ("yes", "maybe", "no", "unknown")
STATUSES = ("not_yet_contacted", "awaiting_reply", "replied", "passed", "writing_offer", "offer_submitted", "through_agent")
ANSWERED_STATUSES = ("replied", "passed", "writing_offer", "offer_submitted")
# Where a reading of the notes came from. Kept in curation.json only. Nothing gates on it and nothing prints it.
# A value the operator corrected, or one from a sheet column, is never overwritten by a later automatic pass.
PROVENANCE = ("claude", "corrected_by_operator", "sheet_column")
PROVENANCE_KEEPS = ("corrected_by_operator", "sheet_column")
TAG_FIELDS = ("price_reaction", "price_asked", "interest", "offer_intent", "themes", "liked", "next_followup_date")
OFFER_STATES = ("received", "countered", "accepted", "declined", "withdrawn", "expired")
GROUPS_SOURCES = ("sheet_column", "parsed_from_prose", "not_recorded")
COUNTED_UNITS = ("groups", "visitors", "guests", "parties", "people")
PRICE_EVENTS = ("listed", "price_change")
FEEDBACK_SOURCES = ("conversation", "written_reply", "open_house_host")
REMARK_REACTIONS = ("too_high", "fair_or_positive", "raised_no_verdict")
REACHED_THROUGH = ("open_house_host",)
SINCE_KINDS = ("touch", "feedback", "engagement", "open_house", "offer", "price_change", "note")
LEAD_STATES = ("live", "earlier_interest")
TAB_KINDS = ("disclosure", "showing", "inquiry", "open_house", "offers", "other")
EVENT_TYPES = ("disclosure_opened", "keybox_showing_start", "keybox_showing_end")
SOURCE_KINDS = ("activity_sheet_live", "activity_sheet_file", "status_email", "open_house_schedule", "offer_summary",
                "glide_email", "supra_email", "pasted_notes", "forwarded_email", "mls_public_page", "market_data",
                "ad_accounts", "portal_page", "operator_numbers", "nearby_lookup", "other")
# Marketing channel states and how each reads to a seller. "Running" is not a state: it is said only of a channel
# that is on AND was checked for this issue (channel_is_running). A channel that is on may carry ends_on, the day
# it is scheduled to end. No ad spend amount is ever stored or printed.
MARKETING_STATUSES = (("on", "Switched on"), ("prepared", "Prepared"), ("on_hold", "On hold"),
                      ("not_launched", "Not launched"), ("ended", "Ended"))
MARKETING_STATUS_KEYS = tuple(k for k, _ in MARKETING_STATUSES)
MARKETING_RUNNING, MARKETING_ENDS = "Running", "Scheduled to end"
# The optional sources (online views, similar homes nearby). A figure a site shows is a running count since the
# home was listed; a figure the operator types may be for one week. Every lookup is logged with how it ended.
ONLINE_COUNTS = ("week", "since_listing")
ONLINE_SOURCES = ("operator", "portal_page")
LOOKUP_OUTCOMES = ("planned", "ok", "skipped")
SKIP_REASONS = ("blocked", "captcha", "failed", "pane_unavailable", "not_found")

LIMITS = {
    "offer_lead_fresh_days": 21,   # an offer lead with no contact for longer than this is "earlier interest"
    "quiet_days": 30,              # no contact in either direction for longer than this is "quiet"
    "tries_flag": 3,               # "3 or more tries": separate follow-up days since the last answer
    "email_max_bytes": 95000,      # Gmail clips near 102 KB
    "nearby_max_homes": 8,         # the watch list of similar homes nearby is chosen once and stays this short
    # token thrift: what an optional lookup may cost per issue (references/extras.md). Enforced by sr_lookups.
    "nearby_lookups_per_issue": 1,     # ONE scripted lookup for the similar homes nearby
    "portal_pages_per_issue": 1,       # at most ONE page per portal for online views
    "nearby_candidates_max": 12,       # how many candidate homes the first lookup may hand back
    "nearby_json_max_bytes": 12000,    # a lookup result larger than this is not the compact result and is refused
    "portal_json_max_bytes": 600,
}

# The lists under "The details": people grouped by what they did, so each list matches a number on top and a
# tab of the team's sheet. A person who did two things is shown in full in the first list they belong to, in
# this order, and as a one-line pointer in the others (references/counting-rules.md, section 15).
LISTS = (
    ("showings", "Agents who showed the home"),
    ("disclosure", "Disclosure packages"),
    ("open_house", "Open house visitors we know of"),
    ("other_inquiries", "Other inquiries"),
)
LIST_KEYS = tuple(k for k, _ in LISTS)
# What a person has said about writing an offer, in the words an entry prints after "Offer".
OFFER_WORDS = (
    ("offer_received", "Offer received"),
    ("writing_one", "Writing one"),
    ("possibly", "Possibly"),
    ("not_yet", "Not yet"),
    ("no", "No"),
    ("not_discussed", "Not discussed"),
)
OFFER_WORD_KEYS = tuple(k for k, _ in OFFER_WORDS)
# Similar homes nearby (optional): where each watched home stands, and what changed since the last issue.
NEARBY_STATUSES = ("active", "pending", "sold", "withdrawn")
NEARBY_CHANGES = ("new_listing", "price_change", "went_pending", "sold", "withdrawn", "back_on_market", "none")

# The fixed theme vocabulary. Price is NOT a theme: it is always its own row, from price_reaction.
THEME_GROUPS = (
    ("home", "About the home and its setting"),
    ("changeable", "Things we can change"),
    ("buyer", "About the buyer"),
    ("other", "Other"),
)
# key, seller-facing label, group, hidden in the link copy (true when the row hints at who may be weighing an offer)
THEMES = (
    ("location", "Location or surroundings", "home", False),
    ("size_layout", "Size or layout", "home", False),
    ("floor_level", "Floor level", "home", False),
    ("stairs", "Stairs", "home", False),
    ("parking", "Parking", "home", False),
    ("yard_outdoor", "Yard or outdoor space", "home", False),
    ("hoa", "HOA", "home", False),
    ("condition_disclosures", "Condition or disclosures", "changeable", False),
    ("staging", "Staging or presentation", "changeable", False),
    ("buyer_timing", "Buyer's timing", "buyer", False),
    ("still_deciding", "Still deciding", "buyer", True),
    ("chose_another_home", "Chose or preferred another property", "buyer", False),
    ("no_reason", "No reason given", "buyer", False),
    ("other", "Other", "other", False),
)
LIKED = (
    ("home_overall", "The home overall"),
    ("layout_space", "Layout or space"),
    ("condition_updates", "Condition or updates"),
    ("light_views", "Light or views"),
    ("outdoor_space", "Yard or outdoor space"),
    ("location", "Location"),
    ("community", "Community or amenities"),
    ("value", "Value for the price"),
    ("other", "Other"),
)
THEME_KEYS = tuple(t[0] for t in THEMES)
LIKED_KEYS = tuple(k for k, _ in LIKED)


def themes_vocabulary():
    """The top-level themes_vocabulary block every ledger carries."""
    return {
        "version": 1,
        "groups": [{"key": k, "label": lab} for k, lab in THEME_GROUPS],
        "themes": [{"key": k, "label": lab, "group": g, "hide_in_link_copy": h} for k, lab, g, h in THEMES],
        "liked": [{"key": k, "label": lab} for k, lab in LIKED],
        "price_rows": [{"key": "too_high", "label": "Said the price is too high"},
                       {"key": "fair_or_positive", "label": "Said the price is fair or good"},
                       {"key": "not_raised", "label": "Gave no view on price"}],
    }


def blank_contact(cid, name_short, kind="agent", brokerage=None):
    """A contact with every required key at its empty value. The builder fills in the rows and readings, and
    finish_ledger (or settle_contact) then sets the fields that follow from the rows."""
    return {
        "id": cid, "name_short": name_short, "name_recorded": True, "brokerage": brokerage, "kind": kind,
        "is_open_house_host": False, "team_side": False, "represented_by": None, "reached_through": None,
        "phone_out_of_service": False,
        "engagements": [], "touches": [], "feedback_log": [],
        "feedback_safe": None, "feedback_date": None,
        "price_reaction": "unknown", "price_asked": None, "interest": "unknown", "offer_intent": "unknown",
        "status": "not_yet_contacted", "status_note_safe": None,
        "themes": [], "theme_other": None, "liked": [], "liked_other": None, "softened": False,
        "next_followup_date": None,
        "offer_basis_safe": None, "offer_basis_date": None, "followup": {},
        "lists": [], "primary_list": None, "offer_word": "not_discussed", "active_this_week": False,
    }


def blank_ledger(slug):
    """A ledger with every top-level key present and empty. See references/data-contract.md."""
    return {
        "schema_version": SCHEMA_VERSION,
        "meta": {"slug": slug, "built_at": None},
        "listing": {"slug": slug}, "report": {}, "themes_vocabulary": themes_vocabulary(),
        "contacts": [], "open_houses": [], "offers": [], "weeks": [], "totals": {},
        "pricing_tally": {"open_house_price_remarks": []}, "themes_tally": {}, "liked_tally": {},
        "price_periods": [], "offer_watch": [], "team_side": [], "market": None, "marketing": None,
        "online": None, "nearby": None,
        "next_week": [], "sources_used": [], "data_quality": [],
    }


# ---------------------------------------------------------------------------------------------
# dates
# ---------------------------------------------------------------------------------------------
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:$|[T ])")
ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(v):
    """ISO text ('2026-10-05', or a full ISO timestamp), a date or a datetime -> datetime.date. None stays None."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    m = _ISO.match(str(v).strip())
    if not m:
        raise ValueError("not an ISO date: %r" % (v,))
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def iso(d):
    return None if d is None else parse_date(d).isoformat()


def week_start(d):
    """The Monday of the week that holds d."""
    d = parse_date(d)
    return d - datetime.timedelta(days=d.weekday())


def week_end(d):
    """The Sunday of the week that holds d."""
    return week_start(d) + datetime.timedelta(days=6)


def week_index(d, list_date):
    """1 for any day in the week the home was listed, 2 for the next week, and so on. 0 or less is before that week."""
    return (week_start(d) - week_start(list_date)).days // 7 + 1


def report_week(run_date):
    """(week_start, week_end, report_date) for a report built on run_date.

    The week covered is the latest Monday to Sunday week that had fully ended before run_date. The report is
    dated the Monday after it, whatever day it is built. Built on Mon Oct 12 or Thu Oct 15: Oct 5 to Oct 11,
    dated Oct 12."""
    run = parse_date(run_date)
    end = run - datetime.timedelta(days=run.weekday() + 1)
    return end - datetime.timedelta(days=6), end, end + datetime.timedelta(days=1)


def list_weeks(list_date, last_week_start):
    """[(n, start, end)] for every week from the list week through the report week. Quiet weeks are kept."""
    out, ws, last, n = [], week_start(list_date), week_start(last_week_start), 0
    while ws <= last:
        n += 1
        out.append((n, ws, ws + datetime.timedelta(days=6)))
        ws += datetime.timedelta(days=7)
    return out


def days_on_market(list_date, on):
    """Calendar days from the list date to that day. The list date itself is day 0."""
    return (parse_date(on) - parse_date(list_date)).days


def price_on(price_history, day):
    """The list price in effect on that day (the first price for any day before the first entry)."""
    hist = sorted(price_history, key=lambda e: e["date"])
    val, day = hist[0]["price"], iso(day)
    for e in hist:
        if e["date"] <= day:
            val = e["price"]
    return val


def week_list_price(price_history, list_date, start, end):
    """The price in effect on the most listed days of that week. A tie goes to the later price."""
    a, b, days = max(parse_date(start), parse_date(list_date)), parse_date(end), {}
    while a <= b:
        p = price_on(price_history, a)
        days[p] = days.get(p, 0) + 1
        a += datetime.timedelta(days=1)
    if not days:
        return price_on(price_history, end)
    top = max(days.values())
    tied = [p for p in days if days[p] == top]          # dict order is the order the prices took effect
    return tied[-1]


def next_issue_number(first_issue_number, issued, report_date):
    """issued: [(number, report_date)] of the issues already on file for this listing.
    The same report date keeps its number. Otherwise numbering continues by one, starting from the listing's
    first_issue_number when nothing is on file."""
    rd = iso(report_date)
    for n, d in issued or []:
        if iso(d) == rd:
            return int(n)
    return max(int(n) for n, _ in issued) + 1 if issued else int(first_issue_number or 1)


# ---------------------------------------------------------------------------------------------
# formatters (never an em dash or an en dash)
# ---------------------------------------------------------------------------------------------
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
DASHES = re.compile("[\u2012\u2013\u2014\u2015]")


def has_dash(s):
    return bool(DASHES.search(s or ""))


def strip_dashes(s):
    """Rewrites typed dashes the plain way: a range between numbers becomes ' to ', anything else a comma or hyphen."""
    s = re.sub("(?<=\\d)\\s*[\u2012\u2013\u2014\u2015]\\s*(?=\\d)", " to ", s or "")
    s = re.sub("\\s+[\u2012\u2013\u2014\u2015]\\s+", ", ", s)
    return DASHES.sub("-", s)


def fmt_date(d, year=False, weekday=False, approximate=False):
    """'Oct 5', 'Oct 5, 2026', 'Mon, Oct 5', 'about Oct 5'."""
    d = parse_date(d)
    s = "%s %d" % (MONTHS[d.month - 1], d.day)
    if weekday:
        s = "%s, %s" % (WEEKDAYS[d.weekday()][:3], s)
    if year:
        s += ", %d" % d.year
    return ("about " + s) if approximate else s


def fmt_date_long(d):
    """'Monday, Oct 5, 2026'."""
    d = parse_date(d)
    return "%s, %s %d, %d" % (WEEKDAYS[d.weekday()], MONTHS[d.month - 1], d.day, d.year)


def fmt_range(a, b, year=False):
    """'Sept 28 to Oct 4'."""
    return "%s to %s" % (fmt_date(a), fmt_date(b, year=year))


def fmt_money(v, empty="not recorded"):
    """798888 -> '$798,888'. None gives the honest empty state."""
    if v is None:
        return empty
    v = int(round(v))
    return ("-$%s" if v < 0 else "$%s") % "{:,}".format(abs(v))


def fmt_money_short(v, empty="not recorded"):
    """798888 -> '$799K', 1250000 -> '$1.25M'."""
    if v is None:
        return empty
    v = int(round(v))
    if abs(v) >= 1000000:
        return "$%sM" % ("%.2f" % (v / 1000000.0)).rstrip("0").rstrip(".")
    return "$%dK" % int(round(v / 1000.0)) if abs(v) >= 1000 else "$%d" % v


def fmt_pct(x, digits=0, empty="not recorded"):
    """0.983 -> '98%'."""
    return empty if x is None else ("%." + str(digits) + "f%%") % (x * 100.0)


def fmt_num(v):
    return "{:,}".format(v) if isinstance(v, int) else ("%g" % v)


def fmt_count(n, one, many=None):
    """(1, 'call') -> '1 call', (2, 'reply', 'replies') -> '2 replies'."""
    return "%s %s" % (fmt_num(n), one if n == 1 else (many or one + "s"))


def join_and(items):
    items = [i for i in items if i]
    return "".join(items) if len(items) <= 1 else ", ".join(items[:-1]) + " and " + items[-1]


def channel_parts(touches):
    """['4 calls', '1 text', '8 emails'], or ['6 follow-ups'] when the log does not give the channel for all.
    A voicemail is a call."""
    if any(t.get("channel") in (None, "unknown") for t in touches):
        return [fmt_count(len(touches), "follow-up")]
    n = {"call": 0, "text": 0, "email": 0, "in_person": 0}
    for t in touches:
        n["call" if t["channel"] in ("call", "voicemail") else t["channel"]] += 1
    parts = [fmt_count(n["call"], "call") if n["call"] else "", fmt_count(n["text"], "text") if n["text"] else "",
             fmt_count(n["email"], "email") if n["email"] else "",
             fmt_count(n["in_person"], "visit in person", "visits in person") if n["in_person"] else ""]
    return [p for p in parts if p]


def fmt_followup(touches):
    """Days first, touches second: '6 days of follow-up (6 calls, 6 texts)'. Pass the outbound touches."""
    out = [t for t in touches if is_followup(t)]
    if not out:
        return "no follow-up logged yet"
    days = len(set(t["date"][:10] for t in out))
    return "%s of follow-up (%s)" % (fmt_count(days, "day"), ", ".join(channel_parts(out)))


# ---------------------------------------------------------------------------------------------
# names, slugs, stable keys
# ---------------------------------------------------------------------------------------------
_BRACKETS = re.compile(r"\([^)]*\)|\[[^\]]*\]|\([^)]*$")
_INVITED = re.compile(r"^\s*invited\s+by\b\s*[:\-]?\s*", re.I)
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<![\d$,.])(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?![\d,])")
_NAME_PREFIX = {"mr", "mrs", "ms", "miss", "dr"}
_NAME_SUFFIX = {"jr", "sr", "ii", "iii", "iv", "md", "phd", "esq"}


def invited_by(raw):
    """'Invited by Yang Li' -> 'Yang Li'. None when the cell is not an 'Invited by' row."""
    s = " ".join(str(raw or "").split())
    return _INVITED.sub("", s).strip() or None if _INVITED.match(s) else None


def _cap(tok):
    if len(tok) > 1 and (tok.islower() or tok.isupper()):
        return "-".join(p[:1].upper() + p[1:].lower() for p in tok.split("-"))
    return tok[:1].upper() + tok[1:]


def short_name(raw):
    """How a person is named to a seller: 'Yang Li' -> 'Yang L.'.

    Edge cases: a nickname in brackets is dropped ('Robert (Bob) Hale' -> 'Robert H.'); a single name stays
    as it is ('Kestrel'); 'Hale, Robert' -> 'Robert H.'; 'Ann Lee / Teo Park' keeps the first person and
    'Ann & Bob Lee' gives 'Ann L.'; titles and suffixes go ('Dr. Ann Lee Jr.' -> 'Ann L.'); a typed phone or
    email is removed; a cell with no name gives '' (set name_recorded false); an 'Invited by Yang Li' row gives
    'Client of Yang L.' (see invited_by). Two people can shorten to the same label, so a short name is never a
    key: contacts are keyed by id."""
    s = " ".join(str(raw or "").replace("\u00a0", " ").split())
    if not s:
        return ""
    if _INVITED.match(s):
        inner = short_name(_INVITED.sub("", s))
        return ("Client of " + inner) if inner else ""
    s = _PHONE.sub(" ", _EMAIL.sub(" ", _BRACKETS.sub(" ", s)))
    parts = re.split(r"\s*(/|\||&|\+|\band\b|\s-\s)\s*", s, maxsplit=1, flags=re.I)
    s = parts[0]
    if (len(parts) == 3 and parts[1].strip().lower() in ("&", "+", "and") and len(s.split()) == 1
            and len(parts[2].split()) >= 2 and "," not in parts[2]):
        s = s + " " + parts[2].split()[-1]          # 'Ann & Bob Lee': the couple share the last name
    if "," in s:
        left, right = [p.strip() for p in s.split(",", 1)]
        s = (right + " " + left) if (len(left.split()) == 1 and len(right.split()) == 1) else left
    toks = [t.strip(".,;:'\"") for t in s.split()]
    toks = [t for t in toks if re.search(r"[^\W\d_]", t)]
    while toks and toks[0].lower() in _NAME_PREFIX:
        toks.pop(0)
    while len(toks) > 1 and toks[-1].lower() in _NAME_SUFFIX:
        toks.pop()
    if not toks:
        return ""
    if len(toks) == 1:
        return _cap(toks[0])
    initial = re.search(r"[^\W\d_]", toks[-1]).group(0).upper()
    return "%s %s." % (_cap(toks[0]), initial)


# 'Yang L.', 'Ana Lucia V.' or a single name such as 'Kestrel'. A full last name does not match.
SHORT_NAME = re.compile(r"^[^\W\d_][\w'\-]*(?:(?: [^\W\d_][\w'\-]*)* [^\W\d_]\.)?$", re.U)


def slugify(text, max_len=60):
    """'218 W Sample Glen Rd #214' -> '218-w-sample-glen-rd-214'."""
    s = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:max_len].strip("-")


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", str(s or "")).lower()).strip()


def row_key(tab_kind, name="", phones=(), emails=(), extra=""):
    """A key for one sheet row that survives re-exports, re-sorting and inserted rows, because it is made
    from who the row is about and not from where the row sits. Two rows with the same basis get the same
    key: the parser adds '~2', '~3' in sheet order. `extra` is for rows with no person (an open house row
    uses its date text)."""
    if tab_kind not in TAB_KINDS:
        raise ValueError("unknown tab kind: %r" % (tab_kind,))
    basis = "|".join([_norm(name), ",".join(sorted(re.sub(r"\D", "", p)[-10:] for p in phones if p)),
                      ",".join(sorted(str(e).strip().lower() for e in emails if e)), _norm(extra)])
    return "%s:%s" % (tab_kind, hashlib.sha1(basis.encode("utf-8")).hexdigest()[:10])


def entry_key(row, field, date, text):
    """A key for one dated note inside a row. It changes when the note's wording changes, which is the point:
    an edited note has to be read again. field is 'feedback' or 'note'."""
    return "%s/%s/%s/%s" % (row, field, iso(date) or "undated", hashlib.sha1(_norm(text).encode("utf-8")).hexdigest()[:8])


# ---------------------------------------------------------------------------------------------
# identity (brand facts and the blocklist are read at run time, never typed into code)
# ---------------------------------------------------------------------------------------------
def default_identity_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(os.path.dirname(here)), "shared-references", "identity.json")


def load_identity(path=None):
    """Reads shared-references/identity.json. Returns the brand facts a report prints plus the blocklist."""
    path = path or default_identity_path()
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    idn, blk = raw["identity"], raw.get("_blocked_values") or {}
    title = idn.get("title") or "REALTOR"
    return {
        "name": idn["name"], "title": title,
        "realtor_line": title if title.endswith("\u00ae") else title + "\u00ae",
        "brokerage": idn.get("brokerage"), "team": idn.get("team"), "brand_line": idn.get("brand_line"),
        "dre": idn["dre"], "phone": idn.get("phone"), "email": idn.get("email"), "website": idn.get("website"),
        "disclaimer": (idn.get("cobrand_lockup") or {}).get("compass_required_disclaimer") or "",
        "blocklist": {"dre": list(blk.get("dre_blocklist") or []), "brand": list(blk.get("brand_blocklist") or [])},
        "path": path,
    }


def display_brokerage(name, identity=None):
    """How another agent's brokerage is printed. The ledger keeps the name as recorded, even when it is a
    brand on the blocklist (it is a fact about that agent, not our brand). On the page a blocked brand is cut
    to its first word and a trailing 'Real Estate' is dropped, so no blocked string reaches the output."""
    s = " ".join(str(name or "").split())
    for b in ((identity or {}).get("blocklist") or {}).get("brand") or []:
        s = re.sub(re.escape(b), b.split()[0], s, flags=re.I)
    return re.sub(r"\s+Real Estate$", "", s) or None


def find_blocked(text, identity):
    """The blocked values present in text. Brand values match in any letter case."""
    text, low = text or "", (text or "").lower()
    bl = identity["blocklist"]
    return [v for v in bl["dre"] if v and v in text] + [v for v in bl["brand"] if v and v.lower() in low]


# ---------------------------------------------------------------------------------------------
# what a seller may read
# ---------------------------------------------------------------------------------------------
_ACCESS = re.compile(r"\b(?:lock\s?box|key\s?box|door|gate|garage|alarm|access|entry)\s+(?:code|combo|combination)\b"
                     r"|\bcode\s*(?:is|:|#)\s*\d{3,}", re.I)
_FIRST_PERSON = re.compile(r"(?<![\w'])I(?:'m|'ll|'ve|'d)?(?![\w'])|\b(?:on|told|tell|call(?:ed)?|text(?:ed)?|email(?:ed)?) me\b", 0)
_STREET = re.compile(r"\b(\d{2,6})\s+((?:[NSEW]\.?\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+"
                     r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ct|Court|Ln|Lane|Way|Blvd|Boulevard|Pl|Place|Cir|Circle|Ter|Terrace)\b")
_SENSITIVE_HINTS = re.compile(
    r"\b(disab\w*|wheelchair|cancer|surgery|hospital\w*|diagnos\w*|illness|pregnan\w*|divorc\w*|passed away|funeral"
    r"|bankrupt\w*|pre-?approv\w*|credit score|down ?payment|lost (?:his|her|their) job|laid off)\b", re.I)


def safe_text_problems(text, allow=(), own_address=None, streets=True):
    """Hard privacy and style rules for any text a seller could read. Returns short problem strings.
    allow: exact strings that may appear (Graeham's own phone and email). own_address: the listing's address."""
    out, s = [], text or ""
    for a in allow:
        if a:
            s = s.replace(a, " ")
    if has_dash(s):
        out.append("has an em dash or en dash")
    if _PHONE.search(s):
        out.append("has a phone number")
    if _EMAIL.search(s):
        out.append("has an email address")
    if _ACCESS.search(s):
        out.append("mentions an access code")
    if _FIRST_PERSON.search(s):
        out.append("has a first-person aside")
    if streets:
        own = _norm(own_address or "")
        for m in _STREET.finditer(s):
            if not own.startswith(_norm(m.group(1) + " " + m.group(2))):
                out.append("names another address (%s)" % m.group(0))
    return out


def sensitive_hints(text):
    """Soft hints (health, family, finances) that the paraphrase must leave out. Not a verdict."""
    return sorted(set(m.group(0).lower() for m in _SENSITIVE_HINTS.finditer(text or "")))


# ---------------------------------------------------------------------------------------------
# the counting rules and the validators (implemented in the two sibling modules)
# ---------------------------------------------------------------------------------------------
def is_followup(t):
    """A follow-up is a call, voicemail, text or email our team made. One per channel per day."""
    return t.get("direction") == "outbound"


def is_reply(t):
    """They answered: they got in touch, or we reached them on a call. Counted once per person per day."""
    return t.get("direction") == "inbound" or t.get("outcome") == "reached"


def money_amounts(text):
    """Dollar amounts written in a sentence ('$1,200', '45 dollars', 'USD 300'). Used to keep ad spend out."""
    return re.findall(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:dollars|usd)\b|\busd\s?\d[\d,]*", text or "", flags=re.I)


def marketing_recorded(marketing, report):
    """The online ads and marketing section prints only when a channel is switched on, or when something was
    checked for this issue (on or after the first day of the report week)."""
    chs = (marketing or {}).get("channels") or []
    start = iso(report["week_start"])
    return any(ch.get("status") == "on" or (ch.get("checked") or "") >= start for ch in chs)


def channel_is_running(channel, report):
    """A marketing channel may be called running only when it is on AND was checked for this issue
    (on or after the last day of the report week). Otherwise print its state with the date last checked."""
    return channel.get("status") == "on" and (channel.get("checked") or "") >= iso(report["week_end"])


def is_counted(c):
    """Buyer-side people we follow up with directly. Team-side hosts and buyers reached through their agent are not."""
    return not c.get("team_side") and not c.get("represented_by")


def channel_family(ch):
    return "phone" if ch in ("call", "voicemail") else ch


def _lazy(module, name, doc):
    def call(*args, **kwargs):
        return getattr(importlib.import_module(module), name)(*args, **kwargs)
    call.__name__, call.__doc__ = name, doc
    return call


_C, _V = "sr_contract_counts", "sr_contract_validate"
contact_facts = _lazy(_C, "contact_facts", "Everything derived from one person's touches, as of the week end.")
followup_block = _lazy(_C, "followup_block", "The contacts[].followup block stored in the ledger.")
base_status = _lazy(_C, "base_status", "The status the touches alone give.")
counted_feedback = _lazy(_C, "counted_feedback", "The person's feedback entries that count as conversations.")
derive_price_reaction = _lazy(_C, "derive_price_reaction", "The person's price reaction, from their conversations.")
derive_price_asked = _lazy(_C, "derive_price_asked", "Whether price was asked directly: true, false or None.")
offer_people_ids = _lazy(_C, "offer_people_ids", "People the link copy must never name as weighing an offer.")
contact_lists = _lazy(_C, "contact_lists", "The lists under 'The details' a person belongs to, in order.")
derive_offer_word = _lazy(_C, "derive_offer_word", "What a person has said about writing an offer (an OFFER_WORDS key).")
active_in_week = _lazy(_C, "active_in_week", "True when a person did something, or we did, inside the report week.")
online_by_week = _lazy(_C, "online_by_week", "{week number: (views, saves)} from the optional ledger.online block.")
online_totals = _lazy(_C, "online_totals", "(views, saves) since listing: the site's running count, else the sum of the weeks.")
recount = _lazy(_C, "recount", "Every derived number in a ledger, recomputed from its rows.")
finish_ledger = _lazy(_C, "finish_ledger", "Fills every derived block of a ledger from its rows, in place.")
settle_contact = _lazy(_C, "settle_contact", "Sets the derived fields of one contact from its rows, in place.")
validate_ledger = _lazy(_V, "validate_ledger", "validate_ledger(d, identity=None) -> list of problems.")
validate_curation = _lazy(_V, "validate_curation", "validate_curation(d) -> list of problems.")
