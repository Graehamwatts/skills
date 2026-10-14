# -*- coding: utf-8 -*-
r"""nearby_from_mls: similar homes nearby from an MLSListings Matrix search, in the shape nearby_update.py stores.

    python nearby_from_mls.py --folder "<listing folder>" --grid <closed template.json> --grid <hotsheet.json>
                              [--city "San Jose"] [--type Townhouse] [--as-of 2026-10-13] [--out <result.json>]
    then:  python nearby_update.py store --folder "<listing folder>" --result <result.json> --report-date <Monday>

The public site lookup can be blocked (it answered 403 on Oct 13, 2026). The MLS is the other source: Graeham
signs in to MLSListings himself, runs one Matrix search, and scripts\web\matrix_grid.js reads the results grid
once in each of two displays (references\extras.md has the search and the displays). Each run is saved to a
file as it came back. This turns those files into one result:

  - rows are joined by MLS number, so the closed date template (price, sale price, close date, DOM) and the
    Agent 1 Line Hotsheet (change date, change type) of the same search become one home each
  - a listing flagged in the M.O. (Members Only) column is left out: members-only data never goes to a seller
  - the listing itself is left out (by its MLS number and by its address)
  - Contingent counts as pending, and its pending date is the change date
  - the MLS's own DOM is carried as "dom". Where the same sale is also in the market chart (market.json) with
    a different day count, the dom is dropped, so one sale never shows two day counts
  - the close date is the sold date and the sale price is the sold price. For a sold home the "Price" column
    is never read as the sale price
  - the store's source reads "MLSListings, checked <date>"

A row it cannot read is refused, never guessed: a status it does not know, a price, date or count in a form it
does not know, a members-only flag that is neither yes nor no, a sold home with no sale price or close date, or
two displays that disagree about the same home. Refused rows are listed by MLS number and left out. A grid
that shows only some of its rows (Matrix pages its results) is refused whole: show every row and run it again.

Exit 0 with a result written. 2 when nothing usable came back or an input is wrong.
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
import nearby_update as NU       # noqa: E402

EXIT_OK, EXIT_INPUT = 0, 2
SITE = "mlslistings"
MIN_PRICE = 10000                 # a Price or Sale Price under this is not a home price ($0 on a grid is a blank)
GRID_MAX_BYTES = 200000
FIELDS = ("status", "mls", "address", "city", "type", "list_price", "previous_price", "sale_price", "close_date", "dom",
          "beds", "baths", "sqft", "change_date", "change_type", "members_only")
STATUS = [("active", r"active|act|a|new|back on market|bom"),
          ("contingent", r"contingent|ctg|cont|c|active under contract|auc|aco|pending show|pending continue to show"),
          ("pending", r"pending|pnd|pend|p|under contract|uc|pending do not show"),
          ("sold", r"sold|sld|s|closed|cls"),
          ("withdrawn", r"withdrawn|wthdn|wdn|w|expired|exp|x|canceled|cancelled|can|cxl|off market|hold|temp off market|tom")]
YES, NO = ("y", "yes", "true", "x", "mo", "members only", "member only", "1", "✓", "✔"), ("", "n", "no", "false", "0", "-")
STATUS_CHANGE = re.compile(r"pend|cont|ctg|status|under contract|uc\b|>|\bto\b|sold|clos|exp|withdr|cancel", re.I)


def source_line(as_of):
    return "MLSListings, checked %s" % C.fmt_date(as_of, year=True)


class Unreadable(ValueError):
    """One value in a form this script does not know."""


# ---------------------------------------------------------------------------------------------
# reading one cell
# ---------------------------------------------------------------------------------------------
def money(s):
    t = (s or "").strip()
    if not t:
        return None
    mt = re.fullmatch(r"\$?\s*(\d{1,3}(?:,\d{3})+|\d+)(?:\.00)?", t)
    if not mt:
        raise Unreadable("a price in a form not known: %r" % t)
    v = int(mt.group(1).replace(",", ""))
    if v < MIN_PRICE:
        raise Unreadable("a price too small to be a home price: %r" % t)
    return v


def day(s):
    """'4/7/2026', '4/7/26', '2026-04-07', also with a time after it ('4/7/2026 2:15 PM'): the date only."""
    t = (s or "").strip()
    if not t:
        return None
    mt = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})(?:\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?)?", t)
    try:
        if mt:
            y = int(mt.group(3))
            return datetime.date(y + 2000 if y < 100 else y, int(mt.group(1)), int(mt.group(2))).isoformat()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
            return datetime.date(*[int(x) for x in t.split("-")]).isoformat()
    except ValueError:
        pass
    raise Unreadable("a date in a form not known: %r" % t)


def whole(s, what):
    t = (s or "").strip()
    if not t:
        return None
    mt = re.fullmatch(r"(\d{1,3}(?:,\d{3})+|\d+)", t)
    if not mt:
        raise Unreadable("%s in a form not known: %r" % (what, t))
    return int(mt.group(1).replace(",", ""))


def sqft(s):
    t = (s or "").strip()
    if not t:
        return None
    mt = re.fullmatch(r"(\d{1,3}(?:,\d{3})+|\d+)\s*(?:/\s*[A-Za-z ]{1,12}|\(\s*[A-Za-z ]{1,12}\s*\))?", t)
    if not mt:
        raise Unreadable("square feet in a form not known: %r" % t)
    return int(mt.group(1).replace(",", ""))


def baths(s):
    """'2', '2.5', '2|1' or '2/1' (full and half baths) -> 2, 2.5, 2.5."""
    t = (s or "").strip()
    if not t:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", t):
        v = float(t)
    else:
        mt = re.fullmatch(r"(\d+)\s*[|/]\s*(\d+)", t)
        if not mt:
            raise Unreadable("baths in a form not known: %r" % t)
        v = int(mt.group(1)) + 0.5 * int(mt.group(2))
    return int(v) if v == int(v) else v


def status(s):
    t = re.sub(r"\s+", " ", (s or "").strip().lower())
    for word, pattern in STATUS:
        if re.fullmatch(pattern, t):
            return word
    raise Unreadable("a status not known: %r" % (s or ""))


def members_only(s):
    t = re.sub(r"\s+", " ", (s or "").strip().lower())
    if t in NO:
        return False
    if t in YES:
        return True
    raise Unreadable("a members-only flag that is neither yes nor no: %r" % (s or ""))


def tidy_address(s):
    t = C.strip_dashes(" ".join((s or "").split()))
    if t and t == t.upper() and re.search(r"[A-Z]{3}", t):      # an address the grid prints in capitals
        t = " ".join(w if (re.search(r"\d|#", w) or w in ("N", "S", "E", "W", "NE", "NW", "SE", "SW")) else w.capitalize() for w in t.split())
    return t


READERS = {"list_price": money, "previous_price": money, "sale_price": money, "close_date": day, "change_date": day,
           "dom": lambda s: whole(s, "days on market"), "beds": lambda s: whole(s, "beds"), "baths": baths, "sqft": sqft,
           "status": status, "members_only": members_only}


def read_row(columns, cells):
    """{field: value} for one grid row. Raises Unreadable."""
    raw = dict(zip(columns, cells))
    out = {}
    try:
        sold = status(raw.get("status")) == "sold"
    except Unreadable:
        sold = False
    for f in FIELDS:
        if f not in raw:
            continue
        if sold and f in ("list_price", "previous_price"):
            continue                      # a display's Price column may hold the list price or the sale price of a sold home: never read
        v = raw[f]
        out[f] = READERS[f](v) if f in READERS else ((" ".join(str(v).split()) or None) if f != "address" else (tidy_address(v) or None))
    if not out.get("mls"):
        raise Unreadable("no MLS number")
    if not out.get("address"):
        raise Unreadable("no address")
    if "status" not in out:
        raise Unreadable("no status")
    return out


# ---------------------------------------------------------------------------------------------
# reading the saved grids
# ---------------------------------------------------------------------------------------------
def load_grid(path_or_text):
    text = path_or_text
    if isinstance(path_or_text, str) and len(path_or_text) < 400 and os.path.exists(path_or_text):
        if os.path.getsize(path_or_text) > GRID_MAX_BYTES:
            raise SystemExit("%s is %d bytes. matrix_grid.js returns compact rows; this is something else. Never save a page."
                             % (path_or_text, os.path.getsize(path_or_text)))
        with open(path_or_text, encoding="utf-8") as f:
            text = f.read()
    try:
        data = json.loads((text or "").strip())
        if isinstance(data, str):                     # the browser tool quotes what a snippet returns
            data = json.loads(data)
    except ValueError as e:
        raise SystemExit("a grid result is not JSON (%s). Save exactly what matrix_grid.js returned." % e)
    if not isinstance(data, dict):
        raise SystemExit("a grid result must be one JSON object, as matrix_grid.js returns it")
    return data


def grid_problem(g):
    """None when the grid can be read, else a plain reason."""
    if g.get("site") != SITE or g.get("ok") is not True:
        why = g.get("reason")
        if why == "signed_out":
            return "the page was a sign-in page. Graeham signs in to MLSListings himself; then run the grid script again"
        return "the page showed no results grid (%s)" % (why or "not a matrix_grid.js result")
    cols = g.get("columns")
    if not isinstance(cols, list) or not isinstance(g.get("rows"), list) or any(c not in FIELDS for c in cols):
        return "the result has no columns and rows in the shape matrix_grid.js returns"
    if any(not isinstance(r, list) or len(r) != len(cols) for r in g["rows"]):
        return "a row does not have one value for each column"
    for f in ("mls", "address", "status"):
        if f not in cols:
            return "the grid has no %s column" % f
    if g.get("partial"):
        p = g["partial"]
        return ("the grid shows %s of its %s rows (Matrix pages its results). Show every row on one page and run the grid "
                "script again" % (p.get("shown"), p.get("total")))
    if g.get("duplicate_columns"):
        return "the grid has two columns for %s, so it is not clear which one to read" % ", ".join(g["duplicate_columns"])
    return None


def merge(grids):
    """({mls: values}, [(mls, reason)], as_of). A home seen in two displays is one home; any field both displays
    read must agree."""
    homes, refused, days = {}, {}, []
    for gi, g in enumerate(grids):
        if g.get("as_of"):
            days.append(g["as_of"])
        for cells in g["rows"]:
            mls = " ".join(str(cells[g["columns"].index("mls")]).split())
            try:
                vals = read_row(g["columns"], cells)
            except Unreadable as e:
                refused[mls or "row without an MLS number"] = str(e)
                continue
            have = homes.setdefault(vals["mls"], {})
            for k, v in vals.items():
                if v is None:
                    continue
                if k in have and have[k] != v:
                    refused[vals["mls"]] = "the two displays disagree on %s (%r and %r)" % (k.replace("_", " "), have[k], v)
                have.setdefault(k, v)
    for mls in refused:
        homes.pop(mls, None)
    return homes, sorted(refused.items()), max(days) if days else None


# ---------------------------------------------------------------------------------------------
# one home in the store's shape
# ---------------------------------------------------------------------------------------------
def store_home(v, city=None, kind=None):
    """(home dict for nearby_update, note or None). Raises Unreadable."""
    st = v["status"]
    h = {"id": v["mls"], "address": v["address"]}
    if v.get("city") or city:
        h["city"] = v.get("city") or city
    if v.get("type") or kind:
        h["type"] = v.get("type") or kind
    for k in ("beds", "baths", "sqft", "dom"):
        if v.get(k) is not None:
            h[k] = v[k]
    note = None
    ct, cd = v.get("change_type") or "", v.get("change_date")
    if st == "sold":
        if v.get("sale_price") is None:
            raise Unreadable("sold, and the grid shows no sale price (the Price column is not read as one)")
        if v.get("close_date") is None:
            raise Unreadable("sold, and the grid shows no close date")
        h.update(status="sold", sold_price=v["sale_price"], sold_date=v["close_date"])
        return h, None
    if v.get("list_price") is None:
        raise Unreadable("%s, and the grid shows no list price" % st)
    h["list_price"] = v["list_price"]
    if st in ("pending", "contingent"):
        h["status"] = "pending"
        if cd and (not ct or STATUS_CHANGE.search(ct)):
            h["pending_date"] = cd
        else:
            note = "%s: its pending date is not known (%s)" % (v["mls"], "no change date" if not cd else "the latest change is '%s'" % ct)
    elif st == "withdrawn":
        h["status"] = "withdrawn"
        if cd and (not ct or STATUS_CHANGE.search(ct)):
            h["off_date"] = cd
    else:
        h["status"] = "active"
        if cd and re.search(r"new|listed|back on|bom|re-?activ|re-?list", ct, re.I):
            h["list_date"] = cd
        elif cd and re.search(r"price|decrease|increase|reduc", ct, re.I):
            h["price_change"] = dict({"date": cd, "to": v["list_price"]}, **({"from": v["previous_price"]} if v.get("previous_price") else {}))
    return h, note


def market_days(folder):
    """{address key: days_to_contract} for every sale in the market chart (market.json), when one is on file."""
    path = F.listing_paths(folder).get("market") or os.path.join(folder, "market.json")
    m = F.load_json(path, default=None) if os.path.exists(path) else None
    return dict((C._norm(s.get("address")), s.get("days_to_contract")) for s in (m or {}).get("sales") or [] if s.get("address"))


def build(folder, grids, city=None, kind=None, as_of=None, mode=None):
    """(result dict for nearby_update store, report lines). Raises SystemExit when nothing can be used."""
    listing = F.load_json(F.listing_paths(folder)["listing"])
    store = NU.load(folder, listing.get("slug"))
    bad = [(i + 1, grid_problem(g)) for i, g in enumerate(grids)]
    bad = [(i, p) for i, p in bad if p]
    if bad:
        raise SystemExit("; ".join("grid %d: %s" % x for x in bad))
    values, refused, seen_on = merge(grids)
    as_of = C.iso(as_of or seen_on or datetime.date.today())
    mode = mode or ("watch" if store.get("watch") else "candidates")
    if mode == "watch" and store.get("watch") and not any(NU.is_mls_id(w.get("id")) for w in store["watch"]):
        raise SystemExit("the watch list on file was chosen from the public site (its ids are that site's property numbers, not MLS "
                         "numbers), so no MLS row can match it. Run nearby_update.py plan --site redfin, or choose a new watch "
                         "list from the MLS (nearby_from_mls.py --mode candidates, then nearby_update.py store and choose)")
    own_mls, own_addr = str(listing.get("mls") or "").strip().upper(), C._norm(listing.get("address"))
    chart = market_days(folder)
    homes, notes = [], []
    left = {"members_only": 0, "this_listing": 0}
    for mls in sorted(values):
        v = values[mls]
        if "members_only" not in v:
            refused.append((mls, "no display it is in shows the M.O. (Members Only) column, so it is not known whether it may be shown"))
            continue
        if v.get("members_only"):
            left["members_only"] += 1
            continue
        if (own_mls and mls.upper() == own_mls) or C._norm(v["address"]) == own_addr:
            left["this_listing"] += 1
            continue
        try:
            h, note = store_home(v, city=city, kind=kind)
        except Unreadable as e:
            refused.append((mls, str(e)))
            continue
        if note:
            notes.append(note)
        key = C._norm(h["address"])
        if h["status"] == "sold" and h.get("dom") is not None and chart.get(key) is not None and chart[key] != h["dom"]:
            notes.append("%s: the market chart counts %d days for this sale and the MLS %d, so the nearby list leaves its day count out"
                         % (h["address"], chart[key], h["dom"]))
            del h["dom"]
        homes.append(h)
    if mode == "watch" and store.get("watch"):
        want = set(str(w["id"]) for w in store["watch"])
        homes = [h for h in homes if h["id"] in want]
    elif len(homes) > C.LIMITS["nearby_candidates_max"]:
        n = len(homes)
        homes = NU.rank_candidates(homes, listing)[:C.LIMITS["nearby_candidates_max"]]
        notes.append("%d homes came back; the %d closest to this listing are kept as candidates" % (n, len(homes)))
    if not homes:
        raise SystemExit("no home could be used: %s" % ("; ".join("%s %s" % x for x in refused[:6]) or "the grids hold no rows"))
    for i, h in enumerate(homes):
        P = NU.home_problems(NU.clean_home(h), "homes[%d]" % i)
        if P:
            raise SystemExit("a home is not in the shape the store needs: " + "; ".join(P[:3]))
    result = {"ok": True, "site": SITE, "mode": mode, "as_of": as_of, "source": source_line(as_of), "homes": homes,
              "excluded": left, "refused": [{"mls": m, "why": w[:120]} for m, w in refused[:20]]}
    lines = ["%d home(s) for the %s, as checked on %s." % (len(homes), "watch list" if mode == "watch" else "candidates", C.fmt_date(as_of)),
             "left out: %d members-only listing(s), %d for this listing itself." % (left["members_only"], left["this_listing"])]
    lines += ["refused (not read, not guessed): %s: %s" % x for x in refused]
    lines += ["note: " + n for n in notes]
    return result, lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="Similar homes nearby from a Matrix search on MLSListings (saved matrix_grid.js results).",
                                 epilog="Exit 0: a result was written. 2: nothing usable, or an input is wrong.")
    ap.add_argument("--folder", required=True, help="the listing folder: <reports>\\seller-reports\\<slug>")
    ap.add_argument("--grid", action="append", required=True, help="a file holding exactly what matrix_grid.js returned (repeatable: one per display)")
    ap.add_argument("--city", help="the city the search was limited to, when the grid has no City column")
    ap.add_argument("--type", dest="kind", help="the property sub type the search was limited to, when the grid has no such column")
    ap.add_argument("--as-of", help="YYYY-MM-DD the grids were read. Default: the day the grid script gave")
    ap.add_argument("--mode", choices=("candidates", "watch"), help="default: watch when nearby.json has a watch list")
    ap.add_argument("--out", help="where to write the result. Default: <folder>\\work\\nearby_mls_result.json")
    a = ap.parse_args(argv)
    try:
        grids = [load_grid(p) for p in a.grid]
        result, lines = build(a.folder, grids, city=a.city, kind=a.kind, as_of=a.as_of, mode=a.mode)
    except SystemExit as e:
        if isinstance(e.code, int):
            raise
        F.say("STOPPED: %s" % e)
        return EXIT_INPUT
    out = a.out or os.path.join(F.listing_paths(a.folder)["work"], "nearby_mls_result.json")
    F.save_json(out, result)
    for ln in lines:
        F.say(ln)
    F.say("written: %s" % out)
    F.say("NEXT: python \"%s\" store --folder \"%s\" --result \"%s\" --report-date <the Monday of this issue>"
          % (os.path.join(_HERE, "nearby_update.py"), os.path.abspath(a.folder), out))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
