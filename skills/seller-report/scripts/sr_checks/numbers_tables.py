# -*- coding: utf-8 -*-
"""sr_checks.numbers_tables: the tables of numbers, the week by week charts and the per-person follow-up lines.

Read cell by cell and compared with the gate's own recount:
  scorecard   "The numbers": this week, last week, since we listed. Showings, disclosure packages, open house
              traffic, follow-ups, replies and offers print in every issue, zero or not
  chart       the week by week chart: showings and disclosure packages, one row for every week since listing
  chart_views online views by week, when they are recorded
  weeks       "Every week in one table": one row per week, a subtotal per list price, a total
  periods     "The record at each list price": split by the date of each event

Showings are key-box showings plus tours agents reported, one number. An inquiry is never in it: the gate
recounts the number from the tour rows alone, so a page that adds inquiries in does not match.

A table is found by data-sr-table="scorecard|chart|chart_views|weeks|periods" and read through data-sr-col on
its column heads and data-sr-row on its rows. Without those hooks it is found by its headings ("This week",
"Last week", "Week", "Follow ups") and its rows by their labels. A column or row the gate cannot name is
reported, never guessed at.
"""
import re

from . import core
from . import recount as RC
from .page import numbers_in

N = r"(\d{1,3}(?:,\d{3})+|\d+)"
PAIR, LABEL = "PRICE_PAIR", "LABEL"
COLS = (  # column heads of the weekly table and the charts: exact text after normalising
    (("showings", "shown"), "showings"),
    (("key-box showings", "key box showings", "key-box", "key box", "keybox", "by key box"), "keybox_showings"),
    (("tours reported", "reported tours", "agent tours", "tours"), "agent_reported_tours"),
    (("inquiries", "inq"), "inquiries"),
    (("disclosure packages", "new packages", "new pkgs", "packages", "pkgs"), "disclosure_contacts_new"),
    (("packages sent", "pkgs sent", "sent"), "disclosure_sent"),
    (("packages opened", "pkgs opened", "opened"), "disclosure_opened"),
    (("open house", "open houses"), "open_house_groups"),
    (("follow ups", "follow-ups", "followups"), "touches_outbound"),
    (("people",), "outbound_people"),
    (("days",), "outbound_distinct_days"),
    (("replies",), "replies_inbound"),
    (("talks", "conversations"), "conversations_with_feedback"),
    (("high / fair", "high / fair or good", "too high / fair"), PAIR),
    (("too high", "high"), "price_too_high"),
    (("fair or good", "fair"), "price_fair_or_positive"),
    (("offers",), "offers"),
    (("views", "online views"), "online_views"),
    (("saves", "online saves"), "online_saves"),
    (("week", "week of", "wk"), LABEL),
)
ROWS = (  # row labels of the scorecard and the per-price table: the label starts with one of these
    ("showings", "showings"),
    ("key-box showings", "keybox_showings"), ("key box showings", "keybox_showings"), ("showings by key box", "keybox_showings"),
    ("tours reported", "agent_reported_tours"), ("tours agents told us about", "agent_reported_tours"),
    ("agent-reported tours", "agent_reported_tours"), ("tours", "agent_reported_tours"),
    ("inquiries", "inquiries"),
    ("disclosure packages", "disclosure_contacts_new"), ("new people on the disclosure package list", "disclosure_contacts_new"),
    ("disclosure packages sent", "disclosure_sent"), ("packages sent", "disclosure_sent"),
    ("disclosure packages opened", "disclosure_opened"), ("packages opened", "disclosure_opened"),
    ("open house sessions", "open_house_sessions"), ("open houses held", "open_house_sessions"),
    ("open house groups", "open_house_groups"), ("open house visitors", "open_house_groups"),
    ("open house guests", "open_house_groups"), ("open house parties", "open_house_groups"),
    ("open house people", "open_house_groups"), ("open house traffic", "open_house_groups"),
    ("follow-ups we made", "touches_outbound"), ("follow-ups", "touches_outbound"), ("follow ups", "touches_outbound"),
    ("separate days", "outbound_distinct_days"), ("days we followed up", "outbound_distinct_days"),
    ("people we followed up with", "outbound_people"),
    ("replies we received", "replies_inbound"), ("replies", "replies_inbound"),
    ("conversations with feedback", "conversations_with_feedback"), ("conversations", "conversations_with_feedback"),
    ("offers", "offers"),
    ("online views", "online_views"),
    ("days on the market", "days"),
    ("price read as too high", "price_too_high"), ("said the price is too high", "price_too_high"),
    ("price read as fair", "price_fair_or_positive"), ("said the price is fair", "price_fair_or_positive"),
    ("dates", "SKIP"),
)
TOTAL_OF = {"showings": "showings", "keybox_showings": "keybox_showings", "agent_reported_tours": "agent_reported_tours",
            "inquiries": "inquiries",
            "disclosure_contacts_new": "disclosure_contacts", "disclosure_sent": "disclosure_link_sent",
            "disclosure_opened": "disclosure_opened_confirmed", "open_house_groups": "open_house_groups",
            "open_house_sessions": "open_house_sessions", "touches_outbound": "touches_outbound",
            "replies_inbound": "replies_inbound", "conversations_with_feedback": "conversations_with_feedback",
            "offers": "offers", "outbound_distinct_days": "outbound_distinct_days", "online_views": "online_views"}
# the rows the numbers table prints in every issue, zero or not
EVERY_ISSUE = ("showings", "disclosure_contacts_new", "open_house_groups", "touches_outbound", "replies_inbound", "offers")
KNOWN_FIELDS = set(f for _, f in COLS) | set(f for _, f in ROWS) | set(("outbound_people", "days"))
FOLDED = ((r"(\d+) showings?\b", "showings"), (r"(\d+) packages?\b", "disclosure_contacts_new"),
          (r"(\d+) key[- ]?box showings?", "keybox_showings"), (r"(\d+) (?:reported )?tours?\b", "agent_reported_tours"),
          (r"(\d+) inquir(?:y|ies)", "inquiries"), (r"(\d+) follow-ups?", "touches_outbound"), (r"(\d+) offers?\b", "offers"))
MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d+)")
MONTH = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)[a-z]*\.? (\d{1,2})\b")


def norm(s):
    s = re.sub(r"\s+", " ", re.sub(r"[.:*]+$", "", (s or "").replace(core.NBSP, " ").strip().lower())).strip()
    return re.sub(r"\s*/\s*", " / ", s)


def col_field(cell):
    hook = cell.node.get("data-sr-col")
    if hook:
        return hook
    t = norm(cell.text)
    for names, field in COLS:
        if t in names:
            return field
    return None


def row_field(tr, label):
    hook = tr.get("data-sr-row")
    if hook:
        return hook
    t = norm(label)
    best = None
    for name, field in ROWS:
        if t.startswith(name) and (best is None or len(name) > len(best[0])):
            best = (name, field)
    return best[1] if best else None


def grid(tb):
    """(header cells, body rows) of a table, or None when it has no row of column heads."""
    for i, (_, cells) in enumerate(tb.rows[:4]):
        heads = [c for c in cells if c.node.has("data-sr-col") or (c.node.tag == "th" and c.node.get("scope") != "row")]
        if len(heads) >= 2:
            return cells, tb.rows[i + 1:]
    return None


def at(cells, col):
    for c in cells:
        if c.col == col and c.span == 1:
            return c
    return None


def cell_problem(field, want, text, sessions=None):
    """None when the cell agrees with the recount, else a sentence saying how it differs."""
    nums = numbers_in(text)
    if field == "open_house_groups" and want is None:
        if nums:
            return "prints '%s', but %s" % (text, "an open house was held with no count kept" if sessions else "no open house was held")
        if sessions and not re.search(r"held|no count", text, re.I):
            return "an open house was held with no count kept; the cell says '%s'" % text
        if not sessions and re.search(r"\bheld\b", text, re.I) and not re.search(r"\b(?:none|not|no)\b", text, re.I):
            return "no open house was held; the cell says '%s'" % text
        return None
    if want is None:
        return "prints '%s' for a fact that is not recorded (it must say not recorded)" % text if nums else None
    if isinstance(want, tuple):
        return None if tuple(nums[:len(want)]) == want else "prints '%s', the rows give %s" % (text, " / ".join(str(x) for x in want))
    if not nums or nums[0] != want:
        return "prints '%s', the rows give %d" % (text or "nothing", want)
    return None


def _week_value(ctx, row, field, stored=None):
    if field == PAIR:
        return (row["price_too_high"], row["price_fair_or_positive"])
    if field not in row:
        return KeyError
    return RC.printable(ctx.ledger, field, row[field], stored)


# ---------------------------------------------------------------------------------------------
# every week in one table
# ---------------------------------------------------------------------------------------------
def _weeks_tables(ctx):
    """[(table, rule name)] for every table with one row per week: the ones marked data-sr-table="weeks", "chart"
    or "chart_views", plus any other table whose first column is headed 'Week' and that has a column the gate
    can name. Returns (tables, whether the weekly table was found by its hook, whether a chart was found)."""
    out, named_weeks, chart = [], False, False
    for tb in ctx.page.tables():
        if tb.name == "weeks":
            out.append((tb, "table_weeks" if not named_weeks else "table_weeks_%d" % (len(out) + 1)))
            named_weeks = True
        elif tb.name in ("chart", "chart_views"):
            out.append((tb, tb.name + "_weeks"))
            chart = chart or tb.name == "chart"
    if not named_weeks or not chart:
        loose = []
        for tb in ctx.page.tables():
            g = grid(tb)
            if tb.name or not g:
                continue
            head = g[0]
            if head and norm(head[0].text).startswith("week") and len([c for c in head[1:] if col_field(c)]) >= 1:
                loose.append(tb)
        # without hooks: the table with the most columns is the weekly table, the others are charts
        loose.sort(key=lambda tb: -len(grid(tb)[0]))
        for i, tb in enumerate(loose):
            if not named_weeks and i == 0:
                out.append((tb, "table_weeks"))
            elif i or named_weeks:
                out.append((tb, "chart_weeks" if not chart else "chart_weeks_%d" % (i + 1)))
                chart = True
    return out, named_weeks, chart


def _check_weeks(B, ctx, m, tb, hooked, rule):
    header, body = grid(tb) or ([], [])
    cols, unknown = {}, []
    what = "weekly table" if rule.startswith("table") else "week by week chart"
    for c in header:
        f = col_field(c)
        if f == LABEL or (c.col == 0 and f is None):
            continue
        if f is None or (f != PAIR and f not in KNOWN_FIELDS):
            unknown.append(c.text or "(blank)")
        else:
            cols[c.col] = f
    stored = dict((w.get("n"), w) for w in ctx.ledger.get("weeks") or [])
    weeks = dict((w["n"], w) for w in m["weeks"])
    bad, checked, seen, since_sub = [], 0, [], []
    for tr, cells in body:
        if len(cells) == 1:                 # one sentence across the table: 'Weeks 1 to 3, from Jan 5: 4 key-box showings and 5 tours'
            fold = re.match(r"weeks? (\d+) to (\d+)\b", norm(cells[0].text))
            said = [(f, int(mt.group(1))) for pattern, f in FOLDED for mt in [re.search(pattern, cells[0].text, re.I)] if mt]
            if fold and said and all(i in weeks for i in range(int(fold.group(1)), int(fold.group(2)) + 1)):
                inside = list(range(int(fold.group(1)), int(fold.group(2)) + 1))
                total = RC.sum_weeks([weeks[i] for i in inside])
                seen += inside
                since_sub += inside
                for f, got in said:
                    checked += 1
                    if RC.printable(ctx.ledger, f, total[f]) != got:
                        bad.append("weeks %d to %d in one line, %s: prints %d, the rows give %s" % (inside[0], inside[-1], f, got, total[f]))
            continue
        if len(cells) < 2 or not cells[0].text:
            continue
        key, label = tr.get("data-sr-row"), cells[0].text
        kind, n, span = None, None, None
        if key:
            rng = re.fullmatch(r"(?:block:)?(\d+)-(\d+)", key)
            kind = "week" if key.isdigit() else ("all" if key == "all" else ("sub" if key.startswith("sub") else ("range" if rng else None)))
            n = int(key) if key.isdigit() else None
            span = (int(rng.group(1)), int(rng.group(2))) if rng else None
        else:
            low = norm(label)
            mt = re.match(r"(\d+)\b(?!\s*wks?\b)", low)
            rng = re.match(r"(?:weeks? )?(\d+) to (\d+)\b", low)
            if re.match(r"all\b|total\b|since we listed", low):
                kind = "all"
            elif re.match(r"\d+\s*wks?\b|subtotal", low):
                kind = "sub"
            elif rng:
                kind, span = "range", (int(rng.group(1)), int(rng.group(2)))
            elif mt:
                kind, n = "week", int(mt.group(1))
        if kind is None:
            continue
        if kind == "range":                 # several quiet or early weeks folded into one row (an email short on room)
            inside = [i for i in range(span[0], span[1] + 1)]
            if span[0] > span[1] or any(i not in weeks for i in inside):
                bad.append("row '%s': weeks %d to %d are not all weeks of this listing" % (label, span[0], span[1]))
                continue
            want_row = RC.sum_weeks([weeks[i] for i in inside])
            name = "weeks %d to %d in one row" % span
            seen += inside
            since_sub += inside
            md = MONTH.search(label)
            start = core.fmt_day(weeks[span[0]]["start"])
            if md and "%s %s" % (md.group(1).replace("Sept", "Sep"), md.group(2)) != start.replace("Sept", "Sep"):
                bad.append("the row for weeks %d to %d is dated '%s %s'; week %d starts %s" % (span + (md.group(1), md.group(2), span[0], start)))
        elif kind == "week":
            if n not in weeks:
                bad.append("row '%s': there is no week %s (the listing has %d weeks)" % (label, n, len(weeks)))
                continue
            want_row, name = weeks[n], "week %d" % n
            seen.append(n)
            since_sub.append(n)
            md = MONTH.search(label)
            start = core.fmt_day(want_row["start"])
            if md and "%s %s" % (md.group(1).replace("Sept", "Sep"), md.group(2)) != start.replace("Sept", "Sep"):
                bad.append("week %d is dated '%s %s'; that week starts %s" % (n, md.group(1), md.group(2), start))
        elif kind == "sub":
            want_row, name = RC.sum_weeks([weeks[i] for i in since_sub]), "subtotal of weeks %s" % _span(since_sub)
            since_sub = []
        else:
            want_row, name = m["all_weeks"], "total of all %d weeks" % len(weeks)
            said = re.match(r"all (\d+)\b", norm(label))
            if said and int(said.group(1)) != len(weeks):
                bad.append("the total row is labeled '%s'; the listing has %d weeks" % (label, len(weeks)))
        for col, field in sorted(cols.items()):
            cell = at(cells, col)
            if cell is None:
                continue
            want = _week_value(ctx, want_row, field, stored.get(n) if kind == "week" else None)
            if want is KeyError:
                continue
            why = cell_problem(field, want, cell.text, want_row.get("open_house_sessions"))
            checked += 1
            if why:
                bad.append("%s, %s: %s" % (name, field if field != PAIR else "too high / fair", why))
    missing = [n for n in sorted(weeks) if n not in seen]
    if missing:
        bad.append("no row for week%s %s: every week since the list week is kept, quiet weeks included"
                   % ("" if len(missing) == 1 else "s", ", ".join(str(n) for n in missing)))
    if not cols:
        bad.append("no column of the %s could be named (add data-sr-col to its column heads)" % what)
    if bad:
        B.fail(rule, "the %s does not match the recount" % what, bad[:16] + (["and %d more" % (len(bad) - 16)] if len(bad) > 16 else []))
    else:
        B.ok(rule, "%s: %d cells in %d week rows%s match the recount (%s)"
             % (what, checked, len(seen), ", subtotals and the total" if rule.startswith("table") else "", "hooks" if hooked else "found by its headings"))
    if unknown:
        B.warn(rule + "_columns", "%d column(s) of the %s are not checked because the gate cannot name them"
               % (len(unknown), what), ["'%s': add data-sr-col" % u for u in unknown])


def _span(ns):
    return "%d to %d" % (ns[0], ns[-1]) if len(ns) > 1 else (str(ns[0]) if ns else "none")


# ---------------------------------------------------------------------------------------------
# the numbers table: this week, last week, since we listed
# ---------------------------------------------------------------------------------------------
def _scorecards(ctx):
    named = ctx.page.named_table("scorecard")
    if named:
        return named, True
    out = []
    for tb in ctx.page.tables():
        g = grid(tb)
        if g and not tb.name and any(norm(c.text) == "this week" for c in g[0]) and any(
                norm(c.text) in ("last week", "since we listed") for c in g[0]):
            out.append(tb)
    return out, False


def _check_scorecard(B, ctx, m, tb, hooked):
    header, body = grid(tb)
    which = {}
    for c in header:
        t = c.node.get("data-sr-col") or {"this week": "this", "last week": "last", "since we listed": "total"}.get(norm(c.text))
        if t in ("this", "last", "total"):
            which[c.col] = t
    T, W, LW = m["totals"], m["this_week"], m["last_week"]
    bad, checked, unknown, rows = [], 0, [], 0
    for tr, cells in body:
        if len(cells) < 2:
            continue
        label = cells[0].text
        field = row_field(tr, label)
        if field is None or field not in TOTAL_OF and field != "outbound_people":
            unknown.append(label[:50])
            continue
        rows += 1
        for col, t in sorted(which.items()):
            cell = at(cells, col)
            if cell is None:
                continue
            if t == "total":
                src = TOTAL_OF.get(field)
                want = m["extra"]["followup_people"] if field == "outbound_people" else RC.printable(ctx.ledger, src, T[src])
                ses = T["open_house_sessions"]
            else:
                wk = W if t == "this" else LW
                if wk is None:
                    continue
                want = RC.printable(ctx.ledger, field, wk[field], _stored_week(ctx, wk["n"]))
                ses = wk["open_house_sessions"]
            why = cell_problem(field, want, cell.text, ses)
            checked += 1
            if why:
                bad.append("%s, %s: %s" % (field, {"this": "this week", "last": "last week", "total": "since we listed"}[t], why))
            move = re.search(r"\b(up|down) (\d+)\b|\b(same)\b", cell.text)
            if t == "this" and move and not why and LW is not None and isinstance(want, int) and isinstance(LW.get(field), int):
                diff = want - LW[field]
                told = 0 if move.group(3) else int(move.group(2)) * (1 if move.group(1) == "up" else -1)
                if told != diff:
                    bad.append("%s: the change is printed as '%s'; this week %d against last week %d is %+d"
                               % (field, move.group(0), want, LW[field], diff))
        held = re.search(r"\b(\d+) sessions? held\b", label)
        if field == "open_house_groups" and held and W and int(held.group(1)) != W["open_house_sessions"]:
            bad.append("open houses: '%s'; %d session(s) were held this week" % (held.group(0), W["open_house_sessions"]))
    if not which:
        bad.append("the columns 'This week', 'Last week' and 'Since we listed' could not be found")
    have = [row_field(tr, c[0].text) for tr, c in body if len(c) > 1]
    need = [f for f in EVERY_ISSUE if f not in have]
    if need:
        bad.append("no row for %s: showings, disclosure packages, open house traffic, follow-ups, replies and offers "
                   "print in every issue, zero or not" % ", ".join(need))
    if "online_views" in have and T.get("online_views") is None:
        bad.append("an online views row is printed, and no views are recorded for this listing")
    if bad:
        B.fail("table_scorecard", "the numbers table does not match the recount", bad[:14])
    else:
        B.ok("table_scorecard", "the numbers table: %d cells in %d rows match the recount (%s)"
             % (checked, rows, "hooks" if hooked else "found by its headings"))
    if unknown:
        B.warn("table_scorecard_rows", "%d row(s) of the numbers table are not checked because the gate cannot name them"
               % len(unknown), ["'%s': add data-sr-row" % u for u in unknown])


def _stored_week(ctx, n):
    return next((w for w in ctx.ledger.get("weeks") or [] if w.get("n") == n), None)


# ---------------------------------------------------------------------------------------------
# the record at each list price
# ---------------------------------------------------------------------------------------------
def _period_tables(ctx, m):
    named = ctx.page.named_table("periods")
    if named:
        return named, True
    prices = set(p["price"] for p in m["periods"])
    out = []
    for tb in ctx.page.tables():
        g = grid(tb)
        if not g or tb.name:
            continue
        heads = [c for c in g[0] if c.text]
        if heads and all(any(int(x.replace(",", "")) in prices for x in MONEY.findall(c.text)) for c in heads):
            out.append(tb)
    return out, False


def _check_periods(B, ctx, m, tb, hooked):
    header, body = grid(tb)
    cols, used = {}, set()
    for c in header:
        hook = c.node.get("data-sr-col")
        found = [int(hook)] if hook and hook.isdigit() else [int(x.replace(",", "")) for x in MONEY.findall(c.text)]
        for i, p in enumerate(m["periods"]):
            if found and p["price"] == found[0] and i not in used:
                cols[c.col] = p
                used.add(i)
                break
    bad, checked, unknown = [], 0, []
    for tr, cells in body:
        if len(cells) < 2:
            continue
        label = cells[0].text
        field = row_field(tr, label)
        if field == "SKIP":
            continue
        if field is None or field not in m["periods"][0]:
            unknown.append(label[:50])
            continue
        for col, p in sorted(cols.items()):
            cell = at(cells, col)
            if cell is None:
                continue
            want = RC.printable(ctx.ledger, field, p[field])
            why = cell_problem(field, want, cell.text, p["open_house_sessions"])
            nums = numbers_in(cell.text)
            if not why and field.startswith("price_") and len(nums) > 1 and nums[1] != p["conversations_with_feedback"]:
                why = "prints '%s', but %d conversations were logged at that price" % (cell.text, p["conversations_with_feedback"])
            checked += 1
            if why:
                bad.append("at $%s, %s: %s" % ("{:,}".format(p["price"]), field, why))
    if len(cols) != len(m["periods"]):
        bad.append("%d list price column(s) found, the price history has %d periods" % (len(cols), len(m["periods"])))
    if bad:
        B.fail("table_periods", "the record at each list price does not match the recount by event date", bad[:14])
    else:
        B.ok("table_periods", "record at each list price: %d cells match the recount by event date (%s)"
             % (checked, "hooks" if hooked else "found by its headings"))
    if unknown:
        B.warn("table_periods_rows", "%d row(s) of the per-price table are not checked because the gate cannot name them"
               % len(unknown), ["'%s': add data-sr-row" % u for u in unknown])


def check_tables(B, ctx, m):
    tabs, hooked = _scorecards(ctx)
    if not tabs:
        B.fail("table_scorecard", "the numbers table (this week, last week, since we listed) was not found",
               ["mark it data-sr-table=\"scorecard\", or head its columns 'This week', 'Last week', 'Since we listed'"])
    for tb in tabs[:1]:
        _check_scorecard(B, ctx, m, tb, hooked)
    tabs, named, chart = _weeks_tables(ctx)
    if not [1 for _, rule in tabs if rule.startswith("table_weeks")]:
        B.fail("table_weeks", "the table with one row per week since we listed was not found",
               ["mark it data-sr-table=\"weeks\", or head its first column 'Week'"])
    if not chart:
        B.fail("chart_weeks", "the week by week chart (showings and disclosure packages for every week since listing) was not found",
               ["mark it data-sr-table=\"chart\", or head its first column 'Week of'"])
    for tb, rule in tabs:
        _check_weeks(B, ctx, m, tb, bool(tb.name), rule)
        if rule == "chart_weeks":
            fields = set(col_field(c) for c in (grid(tb) or ([], []))[0])
            lost = [f for f in ("showings", "disclosure_contacts_new") if f not in fields]
            if lost:
                B.fail("chart_series", "the week by week chart does not carry both showings and disclosure packages",
                       ["no column for %s" % f for f in lost])
            else:
                B.ok("chart_series", "the week by week chart carries showings and disclosure packages")
    tabs, hooked = _period_tables(ctx, m)
    if not tabs:
        bands = set(w.get("list_price") for w in ctx.ledger.get("weeks") or [])
        if len(m["periods"]) > 1 and len(bands) > 1:
            B.warn("table_periods", "the list price has changed, and no table of the record at each list price was found",
                   ["mark it data-sr-table=\"periods\" so the gate can check it"])
        elif len(m["periods"]) > 1:
            # an earlier price that never held for most of a week has no column of its own in the weekly table,
            # so the page states the price history in a line and prints no per-price table
            B.skip("table_periods", "every week sits at one list price (an earlier price lasted under half a week), "
                   "so there is no per-price table to check")
        else:
            B.skip("table_periods", "one list price so far, so there is no per-price table to check")
    for tb in tabs[:1]:
        _check_periods(B, ctx, m, tb, hooked)


# ---------------------------------------------------------------------------------------------
# each person's follow-up line: days first, touches second
# ---------------------------------------------------------------------------------------------
# "4 days of follow-up (2 calls, 2 texts, 1 email). 3 replies."   "2 days of follow-up (Mar 23, 26): 2 calls, 1 text. 1 reply, ..."
# "3 days of follow-up (2 calls, 1 text, 2 emails). No reply yet."  "4 days of follow-up (6 follow-ups), and 1 day they contacted us. 3 replies."
# "4 days of follow-up (2 calls, 2 texts, 1 email). 3 replies."   "Follow-up: 3 days (2 calls, 1 text): Sept 20 call ..."
FOLLOW = re.compile(r"(?:\b%s days? of follow-up\b|\bFollow-up: %s days?(?= \())([^.:]{0,150})(?:\. (?:%s repl(?:y|ies)\b|(No repl(?:y|ies) yet)))?"
                    % (N, N, N))
PART = re.compile(r"%s (calls?|texts?|emails?|follow-ups?|visits? in person)" % N)


def _line_fits(mt, f):
    """True when one printed follow-up line is this person's record: days, each channel count, replies."""
    if int((mt.group(1) or mt.group(2)).replace(",", "")) != f["days"]:
        return False
    ch = f["by_channel"]
    for num, word in PART.findall(mt.group(3) or ""):
        n = int(num.replace(",", ""))
        w = word.lower()
        have = (ch["in_person"] if "in person" in w else
                {"call": ch["call"], "text": ch["text"], "email": ch["email"], "follow-up": f["touches"]}.get(w.rstrip("s")))
        if have is None or n != have:
            return False
    if mt.group(4) and int(mt.group(4).replace(",", "")) != f["replies"]:
        return False
    if mt.group(5) and f["replies"]:
        return False
    return True


def check_people(B, ctx, m, text):
    facts = m["people"]
    cards = ctx.page.people()
    bad, checked = [], 0
    if cards:
        unknown = sorted(cid for cid in cards if cid not in facts)
        if unknown:
            bad.append("data-sr-person names %s, who %s not in the ledger" % (", ".join(unknown[:6]), "is" if len(unknown) == 1 else "are"))
        for cid, nodes in sorted(cards.items()):
            if cid not in facts:
                continue
            for n in nodes:
                t = ctx.page.flat(root=n)
                for mt in FOLLOW.finditer(t):
                    checked += 1
                    if not _line_fits(mt, facts[cid]):
                        f = facts[cid]
                        bad.append("%s: prints '%s'; the log gives %d days, %d follow-ups, %d replies"
                                   % (cid, mt.group(0)[:80], f["days"], f["touches"], f["replies"]))
        method = "by person card"
    else:
        for mt in FOLLOW.finditer(text):
            checked += 1
            if not any(_line_fits(mt, f) for f in facts.values()):
                bad.append("'%s' matches nobody's record in the ledger" % mt.group(0)[:80])
        method = "against every person, because the cards carry no data-sr-person"
    if bad:
        B.fail("person_lines", "a person's follow-up line does not match their log", bad[:12])
    elif checked:
        B.ok("person_lines", "%d follow-up lines (days first, touches second) match the log, %s" % (checked, method))
    else:
        B.skip("person_lines", "no line of the form 'Follow-up: N days (...)' or 'N days of follow-up (...)' was found to check")
