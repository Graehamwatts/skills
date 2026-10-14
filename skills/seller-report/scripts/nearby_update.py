# -*- coding: utf-8 -*-
r"""nearby_update: the watch list of similar homes nearby, checked once per issue.

    python nearby_update.py plan   --folder "<listing folder>" --asked           (before the one lookup)
    python nearby_update.py store  --folder "<listing folder>" --result <file>   (what the snippet returned)
    python nearby_update.py choose --folder "<listing folder>" --auto            (first use: pick the watch list)
    python nearby_update.py skip   --folder "<listing folder>" --reason blocked  (the site would not answer)
    python nearby_update.py show   --folder "<listing folder>"

Optional. A small watch list (at most 8 comparable homes, chosen once: same property type, similar beds and
size, same area) is re-checked each issue, and the report says what changed that week: new listing, price
change, went pending, sold, withdrawn.

Token thrift (sr_lookups): ONE scripted lookup per issue. "plan" checks that the lookup was asked for and
that the one for this issue is unused, then writes work\nearby_call.js: the snippet scripts\web\nearby_lookup.js
plus one line of arguments. Claude runs that text once in the in-app browser on a public redfin.com page and
saves the compact JSON it returns. "store" keeps it. On first use the same lookup also hands back up to 12
candidates, and "choose" makes the watch list and the first snapshot from them with no second lookup.
When the lookup fails, is blocked or meets a human check: STOP, run "skip", and the report is built without
the section. Never work around a block.

The other source is the MLS: "plan --site mls" plans the one lookup as one Matrix search on MLSListings, after
Graeham signs in himself. scripts\web\matrix_grid.js reads the results grid in two displays and
nearby_from_mls.py turns the two saved results into the result "store" keeps (references/extras.md). Its source
line ("MLSListings, checked <date>") becomes the store's source.

The differences against the previous issue are worked out here in Python, from the dated events of each home
(and, where no date explains a change of status, from the two snapshots, marked approximate).

The file is nearby.json in the listing folder (references/extras.md). ledger_block() turns the snapshot taken
for an issue into ledger.nearby (references/data-contract.md, section 6).
Standard library only. No real client data belongs in this file.
"""
import argparse
import datetime
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sr_contract as C          # noqa: E402
import sr_files as F             # noqa: E402
import sr_lookups as LK          # noqa: E402

EXIT_OK, EXIT_INPUT, EXIT_REFUSED = 0, 2, 4
KEY = "nearby"
SNIPPET = os.path.join(_HERE, "web", "nearby_lookup.js")
MLS_SNIPPET = os.path.join(_HERE, "web", "matrix_grid.js")
MLS_SEARCH_URL = "https://search.mlslistings.com/Matrix/Search/Residential/ResidentialSearch"
SOURCE = "Public listing pages on Redfin"
HOME_KEYS = ("id", "address", "city", "type", "beds", "baths", "sqft", "status", "list_price", "list_date", "pending_date",
             "sold_date", "sold_price", "off_date", "price_change", "dom")
FAMILIES = (("condo", r"condo|co-?op"), ("townhouse", r"town\s?ho"), ("house", r"single|house|detached"))
TYPE_WORDS = {"condo": ("condo", "condos"), "townhouse": ("townhouse", "townhouses"), "house": ("single family home", "single family homes")}
NUMBER_WORDS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight")
CHANGE_WORDS = (("new_listing", "new listing", "new listings"), ("price_change", "price change", "price changes"),
                ("went_pending", "went pending", "went pending"), ("sold", "sold", "sold"),
                ("withdrawn", "taken off the market", "taken off the market"), ("back_on_market", "back on the market", "back on the market"))


def family_of(property_type):
    for key, pattern in FAMILIES:
        if re.search(pattern, property_type or "", re.I):
            return key
    return None


def blank_store(slug):
    return {"schema_version": C.SCHEMA_VERSION, "slug": slug, "source": SOURCE, "search": {}, "scope": None, "chosen_on": None,
            "watch": [], "candidates": None, "snapshots": [], "lookups": []}


def load(folder, slug=None):
    store = F.load_json(F.listing_paths(folder)["nearby"], default=blank_store(slug))
    for k, v in blank_store(slug).items():
        store.setdefault(k, v)
    return store


def save(folder, store):
    store["snapshots"].sort(key=lambda s: s["report_date"])
    return F.save_json(F.listing_paths(folder)["nearby"], store)


def _day(v):
    try:
        return C.parse_date(v) is not None and bool(C.ISO_DAY.match(str(v)))
    except ValueError:
        return False


def _whole(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def home_problems(h, q):
    P = []
    if not isinstance(h, dict) or h.get("id") in (None, "") or not (h.get("address") or "").strip():
        return ["%s: needs id and address" % q]
    if h.get("status") not in C.NEARBY_STATUSES:
        P.append("%s.status: one of %s" % (q, ", ".join(C.NEARBY_STATUSES)))
    for k in ("list_price", "sold_price", "sqft", "dom"):
        if h.get(k) is not None and not _whole(h[k]):
            P.append("%s.%s: a whole number" % (q, k))
    for k in ("list_date", "pending_date", "sold_date", "off_date"):
        if h.get(k) is not None and not _day(h[k]):
            P.append("%s.%s: an ISO date" % (q, k))
    pc = h.get("price_change")
    if pc is not None and (not isinstance(pc, dict) or not _day(pc.get("date")) or not _whole(pc.get("to"))
                           or (pc.get("from") is not None and not _whole(pc["from"]))):
        P.append("%s.price_change: needs date, to and (when known) from" % q)
    if C.has_dash(h.get("address") or ""):
        P.append("%s.address: has a dash" % q)
    return P


def validate_store(store, listing=None):
    """Problems in nearby.json, as plain strings. Empty when the file is clean."""
    P = []
    if not isinstance(store, dict) or not isinstance(store.get("watch"), list) or not isinstance(store.get("snapshots"), list):
        return ["nearby.json: needs watch and snapshots lists"]
    if len(store["watch"]) > C.LIMITS["nearby_max_homes"]:
        P.append("watch: at most %d homes are watched" % C.LIMITS["nearby_max_homes"])
    ids = [str(w.get("id")) for w in store["watch"] if isinstance(w, dict)]
    if len(ids) != len(set(ids)) or len(ids) != len(store["watch"]):
        P.append("watch: every home needs an id, used once")
    own = C._norm((listing or {}).get("address"))
    for i, w in enumerate(store["watch"]):
        if not isinstance(w, dict) or not (w.get("address") or "").strip() or not (w.get("why") or "").strip():
            P.append("watch[%d]: needs address and why (one plain reason it was chosen)" % i)
        elif own and C._norm(w["address"]) == own:
            P.append("watch[%d]: is this listing, not a nearby home" % i)
    if store["watch"] and (not (store.get("scope") or "").strip() or not _day(store.get("chosen_on"))):
        P.append("a watch list needs scope (one plain sentence) and chosen_on")
    seen = set()
    for i, s in enumerate(store["snapshots"]):
        q = "snapshots[%d]" % i
        if not isinstance(s, dict) or not _day(s.get("report_date")) or not _day(s.get("as_of")) or not isinstance(s.get("homes"), list):
            P.append("%s: needs report_date, as_of and homes" % q)
            continue
        if s["report_date"] in seen:
            P.append("%s: a second snapshot for the issue dated %s (one per issue)" % (q, s["report_date"]))
        seen.add(s["report_date"])
        for j, h in enumerate(s["homes"]):
            P += home_problems(h, "%s.homes[%d]" % (q, j))
    for i, x in enumerate(store.get("lookups") or []):
        if x.get("outcome") not in C.LOOKUP_OUTCOMES or not x.get("report_date") or x.get("key") != KEY:
            P.append("lookups[%d]: needs report_date, key 'nearby' and an outcome (%s)" % (i, ", ".join(C.LOOKUP_OUTCOMES)))
    return P


def clean_home(h):
    """One home as stored: only the known keys, the address tidied, the id as text."""
    out = dict((k, h[k]) for k in HOME_KEYS if h.get(k) is not None)
    out["id"] = str(out.get("id"))
    out["address"] = C.strip_dashes(" ".join(str(out.get("address") or "").split()))
    return out


# ---------------------------------------------------------------------------------------------
# the watch list
# ---------------------------------------------------------------------------------------------
def street_of(address):
    return C._norm(re.sub(r"(#|\b(?:unit|apt|ste|suite)\b).*$", "", address or "", flags=re.I))


def rank_candidates(homes, listing):
    """Candidates in the order they would be picked: the same building or street first, homes still for sale or
    pending before sold ones, then the closest in size."""
    own, size = street_of(listing.get("address")), listing.get("sqft")

    def score(h):
        gap = abs(h["sqft"] - size) / float(size) if (size and h.get("sqft")) else 0.5
        return ((0 if street_of(h["address"]) == own else 2) + (0 if h.get("status") in ("active", "pending") else 1) + gap, h["address"])
    return sorted(homes, key=score)


def why_chosen(h, listing):
    bits = ["Same building" if street_of(h["address"]) == street_of(listing.get("address")) else "Same city"]
    if h.get("beds") is not None and h.get("beds") == listing.get("beds"):
        bits.append("same bedroom count")
    if h.get("sqft") and listing.get("sqft"):
        gap = h["sqft"] - listing["sqft"]
        bits.append("same size" if gap == 0 else "%d sq ft %s" % (abs(gap), "larger" if gap > 0 else "smaller"))
    return ", ".join(bits)


def scope_sentence(watch, listing, chosen_on):
    """'Six 1 bedroom condos in Fixture City, chosen on Mar 16'."""
    beds = sorted(set(w["beds"] for w in watch if w.get("beds") is not None))
    one, many = TYPE_WORDS.get(family_of(listing.get("property_type")), ("home", "homes"))
    word = one if len(watch) == 1 else many
    if beds:
        word = "%s bedroom %s" % ("%g" % beds[0] if len(beds) == 1 else "%g to %g" % (beds[0], beds[-1]), word)
    n = len(watch)
    return "%s %s in %s, chosen on %s" % (NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n), word, listing.get("city") or "the same area",
                                          C.fmt_date(chosen_on))


def choose(store, listing, ids=None, auto=False, why=None, scope=None, on=None):
    """Sets the watch list from the candidates on file (at most 8) and makes the first snapshot from the same
    lookup. Returns the watch list."""
    cand = store.get("candidates") or {}
    homes = cand.get("homes") or []
    if not homes:
        raise SystemExit("no candidates are on file. Run plan, the one lookup, and store first.")
    byid = dict((str(h["id"]), h) for h in homes)
    if auto:
        picked = rank_candidates(homes, listing)[:C.LIMITS["nearby_max_homes"]]
    else:
        missing = [i for i in ids or [] if str(i) not in byid]
        if missing or not ids:
            raise SystemExit("choose needs --auto or --ids from the candidates on file (unknown: %s)" % ", ".join(str(i) for i in missing))
        picked = [byid[str(i)] for i in ids]
    if len(picked) > C.LIMITS["nearby_max_homes"]:
        raise SystemExit("at most %d homes are watched" % C.LIMITS["nearby_max_homes"])
    on = C.iso(on or cand.get("as_of") or datetime.date.today())
    store["watch"] = [{"id": str(h["id"]), "address": h["address"], "beds": h.get("beds"), "baths": h.get("baths"), "sqft": h.get("sqft"),
                       "type": h.get("type"), "why": C.strip_dashes((why or {}).get(str(h["id"])) or why_chosen(h, listing))} for h in picked]
    store["chosen_on"] = on
    store["scope"] = C.strip_dashes(scope) if scope else scope_sentence(store["watch"], listing, on)
    snap = {"report_date": cand["report_date"], "as_of": cand["as_of"], "homes": [clean_home(h) for h in picked]}
    store["snapshots"] = [s for s in store["snapshots"] if s["report_date"] != snap["report_date"]] + [snap]
    return store["watch"]


# ---------------------------------------------------------------------------------------------
# what changed since the last issue
# ---------------------------------------------------------------------------------------------
def days_on_market(h, as_of):
    """Days from the list date to the day the home went under contract, sold, left the market, or to the day
    it was checked while still for sale. None when the list date is not known.

    A source that states the figure itself (the MLS does, as "dom") is taken at its word: that is the number an
    agent would quote, and the dates behind it are not always in the result."""
    if h.get("dom") is not None:
        return h["dom"]
    if not h.get("list_date"):
        return None
    end = {"active": as_of, "pending": h.get("pending_date") or as_of, "sold": h.get("pending_date") or h.get("sold_date"),
           "withdrawn": h.get("off_date")}.get(h.get("status"))
    if not end or end < h["list_date"]:
        return None
    return C.days_on_market(h["list_date"], end)


def change_of(prev, cur, first_day, as_of):
    """(change, change_date, price_before, approximate) for one home.

    A dated event decides first: sold, taken off the market, went pending, listed, price changed, when its date
    falls after the previous check (or, with no previous check, on or after the first day of the report week).
    When no dated event explains a difference between the two snapshots, the difference itself is the change,
    dated the day it was seen and marked approximate."""
    def new(day):
        return bool(day) and first_day <= day <= as_of
    st = cur.get("status")
    if st == "sold" and new(cur.get("sold_date")):
        return "sold", cur["sold_date"], None, False
    if st == "withdrawn" and new(cur.get("off_date")):
        return "withdrawn", cur["off_date"], None, False
    if st == "pending" and new(cur.get("pending_date")):
        return "went_pending", cur["pending_date"], None, False
    if st == "active" and new(cur.get("list_date")):
        back = prev is not None and prev.get("list_date") and prev["list_date"] != cur["list_date"]
        return ("back_on_market" if back else "new_listing"), cur["list_date"], None, False
    pc = cur.get("price_change") or {}
    if st in ("active", "pending") and new(pc.get("date")) and pc.get("from") and pc.get("to") and pc["from"] != pc["to"]:
        return "price_change", pc["date"], pc["from"], False
    if prev is not None:
        was = prev.get("status")
        if was != st:
            word = {"pending": "went_pending", "sold": "sold", "withdrawn": "withdrawn", "active": "back_on_market"}[st]
            return word, as_of, None, True
        if st == "active" and prev.get("list_price") and cur.get("list_price") and prev["list_price"] != cur["list_price"]:
            return "price_change", as_of, prev["list_price"], True
    return "none", None, None, False


def snapshot_for(store, report_date):
    rd = C.iso(report_date)
    return next((s for s in store["snapshots"] if s["report_date"] == rd), None)


def previous_snapshot(store, report_date):
    rd = C.iso(report_date)
    older = [s for s in store["snapshots"] if s["report_date"] < rd]
    return max(older, key=lambda s: s["report_date"]) if older else None


def summary_sentence(homes):
    """One sentence: 'No change among the 6 homes we are watching.' or '2 of the 6 homes we are watching changed:
    1 went pending and 1 price change.'"""
    moved = [h for h in homes if h.get("change") not in (None, "none")]
    if not moved:
        return "No change among the %s we are watching." % C.fmt_count(len(homes), "home")
    parts = []
    for key, one, many in CHANGE_WORDS:
        n = len([h for h in moved if h["change"] == key])
        if n:
            parts.append("%d %s" % (n, one if n == 1 else many))
    return "%d of the %s we are watching changed: %s." % (len(moved), C.fmt_count(len(homes), "home"), C.join_and(parts))


def ledger_block(store, listing, report):
    """(ledger.nearby or None, {"skipped": [...], "glance": [...], "also": [...], "summary": sentence or None}) for one issue.

    The section is built only from a snapshot taken for this issue. With none (not asked for, or the lookup was
    skipped) the block is None and the page has no such section."""
    notes = {"skipped": [], "glance": [], "also": [], "summary": None}
    rd, ws = C.iso(report["report_date"]), C.iso(report["week_start"])
    for x in LK.skipped(store, rd, KEY):
        notes["skipped"].append(LK.skipped_note("Similar homes nearby", x, "That section is left out of this report."))
    snap = snapshot_for(store, rd)
    if not snap or not store.get("watch"):
        if store.get("watch") and not notes["skipped"]:
            notes["also"].append("Similar homes nearby were not checked for this issue, so the report has no such section.")
        return None, notes
    prev = previous_snapshot(store, rd)
    first_day = C.iso(C.parse_date(prev["as_of"]) + datetime.timedelta(days=1)) if prev else ws
    was = dict((h["id"], h) for h in (prev or {}).get("homes") or [])
    now = dict((h["id"], h) for h in snap["homes"])
    homes, missing = [], []
    for w in store["watch"]:
        cur = now.get(str(w["id"]))
        if cur is None:
            missing.append(w["address"])
            continue
        change, when, before, approx = change_of(was.get(cur["id"]), cur, first_day, snap["as_of"])
        h = {"address": w["address"], "beds": w.get("beds"), "baths": w.get("baths"), "sqft": w.get("sqft"), "status": cur["status"],
             "list_price": cur.get("list_price"), "sold_price": cur.get("sold_price"), "days_on_market": days_on_market(cur, snap["as_of"]),
             "change": change, "change_date": when}
        if before is not None:
            h["price_before"] = before
        if approx:
            h["change_date_approximate"] = True
        if h["status"] == "sold" and h["sold_price"] is None:
            missing.append(w["address"])                   # a sale with no price on record cannot be printed
            continue
        homes.append(h)
    if missing:
        notes["also"].append("%s on the watch list had no usable record in this check and %s left out: %s."
                             % (C.fmt_count(len(missing), "home"), "is" if len(missing) == 1 else "are", C.join_and(missing)))
    if not homes:
        return None, notes
    notes["summary"] = summary_sentence(homes)
    block = {"as_of": snap["as_of"], "checked_for_this_issue": True, "scope": store["scope"], "source": store.get("source") or SOURCE,
             "homes": homes}
    return block, notes


# ---------------------------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------------------------
def _issue(a):
    if getattr(a, "report_date", None):
        rd = C.parse_date(a.report_date)
        if rd.weekday() != 0:
            raise SystemExit("--report-date %s is not a Monday" % rd)
        return rd
    return C.report_week(datetime.date.today())[2]


def _report(rd):
    return {"report_date": C.iso(rd), "week_start": C.iso(rd - datetime.timedelta(days=7)), "week_end": C.iso(rd - datetime.timedelta(days=1))}


def call_text(store, listing, rd):
    """The text Claude runs once in the browser: the snippet, then one line of arguments."""
    cfg = ((listing.get("extras") or {}).get("nearby") or {}).get("search") or {}
    search = dict(cfg, **(store.get("search") or {}))
    args = {"mode": "watch" if store.get("watch") else "candidates", "family": family_of(listing.get("property_type")),
            "subject": dict((k, listing.get(k)) for k in ("address", "city", "state", "zip", "beds", "baths", "sqft")),
            "search": dict((k, search.get(k)) for k in ("region_id", "region_type", "market", "uipt") if search.get(k) is not None),
            "max": C.LIMITS["nearby_candidates_max"], "sold_days": 120, "tz": "America/Los_Angeles"}
    if store.get("watch"):
        args["watch"] = [{"id": w["id"], "address": w["address"]} for w in store["watch"]]
    with open(SNIPPET, encoding="utf-8") as f:
        code = f.read()
    return code.rstrip() + "\n\nJSON.stringify(await globalThis.srNearby(%s))\n" % json.dumps(args, separators=(",", ":"))


def cmd_plan(a):
    paths = F.listing_paths(a.folder)
    listing = F.load_json(paths["listing"])
    store, rd = load(a.folder, listing.get("slug")), _issue(a)
    try:
        LK.plan(store, KEY, rd, C.LIMITS["nearby_lookups_per_issue"], asked=a.asked, by_setting=LK.setting(listing, "nearby"),
                what="similar homes nearby")
    except LK.Refused as e:
        F.say("REFUSED: %s" % e)
        return EXIT_REFUSED
    save(a.folder, store)
    me = os.path.join(_HERE, "nearby_update.py")
    if getattr(a, "site", "redfin") == "mls":
        return plan_mls(a, paths, listing, store, rd, me)
    call = F.save_text(os.path.join(paths["work"], "nearby_call.js"), call_text(store, listing, rd))
    F.say("planned: ONE lookup of similar homes nearby for the issue dated %s (%s)."
          % (C.iso(rd), "the watch list of %d" % len(store["watch"]) if store["watch"] else "first use: candidates for the watch list"))
    F.say("  1. Open one public redfin.com page in the in-app browser (the page for the listing's city is enough). No sign-in, no forms.")
    F.say("  2. Run the text of this file there, once, as it is: %s" % call)
    F.say("  3. Save exactly what it returned to a file and run:  python \"%s\" store --folder \"%s\" --result <file> --report-date %s"
          % (me, os.path.abspath(a.folder), C.iso(rd)))
    F.say("  If the page or the lookup is blocked, shows a human check or fails: STOP. Do not try another way. Run:  python \"%s\" skip --folder \"%s\" --reason <%s> --report-date %s"
          % (me, os.path.abspath(a.folder), "|".join(C.SKIP_REASONS), C.iso(rd)))
    return EXIT_OK


def plan_mls(a, paths, listing, store, rd, me):
    """The one lookup, made on MLSListings: one Matrix search read in two displays (references/extras.md)."""
    with open(MLS_SNIPPET, encoding="utf-8") as f:
        code = f.read()
    call = F.save_text(os.path.join(paths["work"], "nearby_call.js"), code.rstrip() + "\n\nglobalThis.srMatrixGrid()\n")
    work, folder = paths["work"], os.path.abspath(a.folder)
    beds = listing.get("beds")
    F.say("planned: ONE lookup of similar homes nearby for the issue dated %s, on MLSListings (%s)."
          % (C.iso(rd), "the watch list of %d" % len(store["watch"]) if store["watch"] else "first use: candidates for the watch list"))
    F.say("  1. Graeham signs in to MLSListings in the in-app browser himself. Claude never types a password or a code.")
    F.say("  2. Matrix Residential Search: %s" % MLS_SEARCH_URL)
    F.say("     Status: Active, Contingent, Pending, Sold. Property sub type: %s. Beds: %s. City or zip: %s. COE Date: a start date with a"
          " plus, such as 6/1/2026+ (the close date applies to sold rows only). Search once."
          % (listing.get("property_type") or "the listing's", ("%s" % beds) if beds is not None else "the listing's", listing.get("city") or "the listing's"))
    F.say("  3. Results display 'my:Closed date template'. Run the text of this file there once: %s" % call)
    F.say("     Save exactly what it returned to %s" % os.path.join(work, "mls_grid_closed.json"))
    F.say("  4. Switch the display to 'Agent 1 Line Hotsheet' (same results, no new search). Run the same text again and save it to %s"
          % os.path.join(work, "mls_grid_hotsheet.json"))
    F.say("  5. python \"%s\" --folder \"%s\" --grid \"%s\" --grid \"%s\"%s"
          % (os.path.join(_HERE, "nearby_from_mls.py"), folder, os.path.join(work, "mls_grid_closed.json"), os.path.join(work, "mls_grid_hotsheet.json"),
             (" --city \"%s\"" % listing["city"]) if listing.get("city") else ""))
    F.say("     then:  python \"%s\" store --folder \"%s\" --result \"%s\" --report-date %s"
          % (me, folder, os.path.join(work, "nearby_mls_result.json"), C.iso(rd)))
    F.say("  If the page is a sign-in page, shows an error or a human check: STOP. Do not try another way. Run:  python \"%s\" skip --folder \"%s\" --reason <%s> --report-date %s"
          % (me, folder, "|".join(C.SKIP_REASONS), C.iso(rd)))
    return EXIT_OK


def cmd_store(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store, rd = load(a.folder, listing.get("slug")), _issue(a)
    try:
        data = LK.read_result(a.result, C.LIMITS["nearby_json_max_bytes"], "similar homes")
        why = LK.blocked_reason(data)
        if why is None and not isinstance(data.get("homes"), list):
            why = "failed"
        if why:
            LK.close(store, KEY, rd, "skipped", why, data.get("detail"))
            save(a.folder, store)
            F.say("SKIPPED: the lookup gave no homes (%s). The report is built without the section. Do not try another way." % LK.SKIP_WORDS[why])
            return EXIT_OK
        homes = [clean_home(h) for h in data["homes"] if isinstance(h, dict)]
        problems = [p for i, h in enumerate(homes) for p in home_problems(h, "homes[%d]" % i)]
        if problems:
            raise SystemExit("the result is not in the expected shape: " + "; ".join(problems[:4]))
        LK.close(store, KEY, rd, "ok")
    except LK.Refused as e:
        F.say("REFUSED: %s" % e)
        return EXIT_REFUSED
    as_of = data.get("as_of") if _day(data.get("as_of")) else C.iso(datetime.date.today())
    # the source the section names is the one this result came from: nearby_from_mls.py says "MLSListings, checked
    # Oct 13, 2026"; the public site snippet says nothing, and its own line is used
    if isinstance(data.get("source"), str) and data["source"].strip():
        store["source"] = C.strip_dashes(" ".join(data["source"].split()))[:120]
    elif data.get("site") == "redfin":
        store["source"] = SOURCE
    for k, v in (data.get("search") or {}).items():
        if v is not None:
            store["search"][k] = v
    if data.get("mode") == "watch" and store["watch"]:
        want = set(str(w["id"]) for w in store["watch"])
        snap = {"report_date": C.iso(rd), "as_of": as_of, "homes": [h for h in homes if h["id"] in want]}
        store["snapshots"] = [s for s in store["snapshots"] if s["report_date"] != snap["report_date"]] + [snap]
        save(a.folder, store)
        block, notes = ledger_block(store, listing, _report(rd))
        F.say("stored: the watch list as checked on %s, for the issue dated %s." % (C.fmt_date(as_of), C.iso(rd)))
        F.say("  " + (notes["summary"] or "Nothing usable came back for the watched homes."))
        for line in notes["also"]:
            F.say("  note: " + line)
        return EXIT_OK
    own = C._norm(listing.get("address"))
    homes = [h for h in homes if C._norm(h["address"]) != own][:C.LIMITS["nearby_candidates_max"]]
    store["candidates"] = {"report_date": C.iso(rd), "as_of": as_of, "homes": homes, "dropped": data.get("dropped") or {}}
    save(a.folder, store)
    F.say("stored: %s for the watch list, as checked on %s. Nothing is watched yet." % (C.fmt_count(len(homes), "candidate"), C.fmt_date(as_of)))
    for h in rank_candidates(homes, listing):
        F.say("  %-10s %-32s %s bed, %s sq ft, %s, %s" % (h["id"], h["address"], h.get("beds", "?"), h.get("sqft", "?"), h.get("status"),
                                                        C.fmt_money(h.get("sold_price") if h.get("status") == "sold" else h.get("list_price"))))
    F.say("NEXT: pick at most %d with  choose --auto  (the order above)  or  choose --ids <id> <id> ...  No second lookup is needed."
          % C.LIMITS["nearby_max_homes"])
    return EXIT_OK


def cmd_choose(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store = load(a.folder, listing.get("slug"))
    why = dict(x.split("=", 1) for x in a.why or [] if "=" in x)
    watch = choose(store, listing, ids=a.ids, auto=a.auto, why=why, scope=a.scope)
    problems = validate_store(store, listing)
    if problems:
        raise SystemExit("nearby.json would not be valid: " + "; ".join(problems[:4]))
    save(a.folder, store)
    F.say("watch list set (%s): %s." % (C.fmt_count(len(watch), "home"), store["scope"]))
    for w in watch:
        F.say("  %-32s %s" % (w["address"], w["why"]))
    return EXIT_OK


def cmd_skip(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store, rd = load(a.folder, listing.get("slug")), _issue(a)
    try:
        LK.close(store, KEY, rd, "skipped", a.reason, a.detail)
    except LK.Refused as e:
        F.say("REFUSED: %s" % e)
        return EXIT_REFUSED
    save(a.folder, store)
    F.say("skipped: similar homes nearby (%s). The report is built without that section, and the chat reply says so." % LK.SKIP_WORDS[a.reason])
    return EXIT_OK


def cmd_show(a):
    listing = F.load_json(F.listing_paths(a.folder)["listing"])
    store, rd = load(a.folder, listing.get("slug")), _issue(a)
    block, notes = ledger_block(store, listing, _report(rd))
    if a.json:
        F.say(F.dumps({"nearby": block, "notes": notes}).rstrip())
        return EXIT_OK
    F.say("watch list: %s" % (store.get("scope") or "none chosen yet"))
    if block:
        F.say("  %s" % notes["summary"])
        for h in block["homes"]:
            F.say("  %-32s %-9s %-12s %s" % (h["address"], h["status"], h["change"], h.get("change_date") or ""))
    else:
        F.say("  no section for the issue dated %s." % C.iso(rd))
    for line in notes["skipped"] + notes["glance"] + notes["also"]:
        F.say("  note: " + line)
    for x in LK.for_issue(store, rd, KEY):
        F.say("  lookup: %s%s" % (x["outcome"], (" (" + x["reason"] + ")") if x.get("reason") else ""))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(description="Similar homes nearby: the watch list and one check per issue (optional).",
                                 epilog="Exit 0 done. 2 an input is wrong. 4 refused by the token rules (not asked for, or the one lookup for this issue is used).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--folder", required=True, help="the listing folder: <reports>\\seller-reports\\<slug>")
        p.add_argument("--report-date", help="the Monday the issue is dated. Default: the Monday after the last full week")
        return p
    p = common(sub.add_parser("plan", help="before the lookup: checks the rules, logs it, writes work\\nearby_call.js"))
    p.add_argument("--asked", action="store_true", help="the operator asked for this in this session")
    p.add_argument("--site", choices=("redfin", "mls"), default="redfin",
                   help="redfin: the public site snippet. mls: one Matrix search on MLSListings, after Graeham signs in (nearby_from_mls.py)")
    p.set_defaults(fn=cmd_plan)
    p = common(sub.add_parser("store", help="keep what the snippet returned (candidates on first use, the snapshot after)"))
    p.add_argument("--result", required=True, help="a file holding exactly what the snippet returned")
    p.set_defaults(fn=cmd_store)
    p = common(sub.add_parser("choose", help="first use: set the watch list from the candidates on file"))
    p.add_argument("--auto", action="store_true", help="take the first 8 in ranked order")
    p.add_argument("--ids", nargs="*", help="the ids to watch, at most 8")
    p.add_argument("--why", action="append", metavar="ID=REASON", help="why a home was chosen (default: written from its facts)")
    p.add_argument("--scope", help="the sentence the report prints above the list (default: written from the list)")
    p.set_defaults(fn=cmd_choose)
    p = common(sub.add_parser("skip", help="the lookup was blocked, met a human check, or failed: close it"))
    p.add_argument("--reason", required=True, choices=C.SKIP_REASONS)
    p.add_argument("--detail")
    p.set_defaults(fn=cmd_skip)
    p = common(sub.add_parser("show", help="what the report will print for this issue"))
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_show)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
