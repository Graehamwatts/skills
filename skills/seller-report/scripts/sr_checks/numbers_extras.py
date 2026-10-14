# -*- coding: utf-8 -*-
"""sr_checks.numbers_extras: the optional sections, counted again from the ledger.

  similar homes nearby   how many of the watched homes changed, one table row per home with its status, price
                         and days, each change with its date and prices, and the day the list was checked
  online ads, marketing  the status word of every channel (running only when checked for this issue, switched
                         on with the day it was last checked, prepared, on hold, not launched), the scheduled
                         end, no ad spend amount, and no section at all when nothing was on or recorded
  online views           the day the figures were read

The section is found by data-sr-section="nearby" or "marketing". The watch list table is found by
data-sr-table="nearby" (rows data-sr-row="<index in ledger.nearby.homes>", columns status, price, days) or by
its headings; a change line by data-sr-row="change:<index>" or by the home's address.
Standard library only. The gate never imports the renderer.
"""
import re

from . import core
from .page import numbers_in

CHANGED = ("new_listing", "price_change", "went_pending", "sold", "withdrawn", "back_on_market")
CHANGE_SAYS = {"new_listing": r"new listing", "price_change": r"price changed", "went_pending": r"went pending", "sold": r"\bsold\b",
               "withdrawn": r"taken off the market|withdrawn", "back_on_market": r"back on the market"}
STATUS_SAYS = {"active": "active", "pending": "pending", "sold": "sold", "withdrawn": "withdrawn"}
MARKETING_WORDS = {"prepared": "prepared", "on_hold": "on hold", "not_launched": "not launched", "ended": "ended"}
MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d+)")
SPEND = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:dollars|usd)\b|\busd\s?\d[\d,]*", re.I)


def _money(text):
    return [int(m.group(1).replace(",", "")) for m in MONEY.finditer(text or "")]


def _rows(table):
    """[(tr node, [cell text])] of a table, header row included."""
    out = []
    for tr in table.node.iter():
        if tr.tag == "tr" and next((a for a in tr.ancestors() if a.tag == "table"), None) is table.node:
            out.append((tr, [c for c in tr.children if c.tag in ("td", "th")]))
    return out


def _nearby(B, ctx):
    nb = ctx.ledger.get("nearby") if isinstance(ctx.ledger.get("nearby"), dict) else None
    nodes = ctx.page.sections("nearby")
    homes = [h for h in (nb or {}).get("homes") or [] if isinstance(h, dict)]
    if not homes:
        if nodes:
            B.fail("nearby_absent", "a similar homes section is printed, and the ledger holds no watch list for this issue")
        return
    if not nodes:
        return                                              # the section is optional: a page may leave it out
    text = ctx.section_text("nearby") or ""
    low = core.fold(text)
    moved = [(i, h) for i, h in enumerate(homes) if h.get("change") in CHANGED]

    # ---- the count in the heading ---------------------------------------------------------------
    bad = []
    said = re.search(r"\b(\d+) of the (\d+) homes? we are watching changed", text)
    none = re.search(r"\bNo change among the (\d+) homes? we are watching", text)
    if said:
        if (int(said.group(1)), int(said.group(2))) != (len(moved), len(homes)):
            bad.append("'%s'; the ledger has %d changed of %d watched" % (said.group(0), len(moved), len(homes)))
    elif none:
        if moved or int(none.group(1)) != len(homes):
            bad.append("'%s'; the ledger has %d changed of %d watched" % (none.group(0), len(moved), len(homes)))
    else:
        bad.append("the section does not say how many of the %d watched homes changed" % len(homes))
    for name, want in (("nearby_changed", len(moved)), ("nearby_homes", len(homes))):
        for n in ctx.page.hooks(name):
            if numbers_in(ctx.page.flat(root=n)) != [want]:
                bad.append("data-sr=%s prints '%s'; the ledger gives %d" % (name, ctx.page.flat(root=n)[:30], want))
    B.judge("nearby_counts", bad, "similar homes: %d of the %d watched homes changed, as printed" % (len(moved), len(homes)),
            "the similar homes heading does not match the watch list")

    # ---- the watch list, one row per home --------------------------------------------------------
    tables = [t for t in ctx.page.named_table("nearby")]
    if not tables:
        tables = [t for t in ctx.page.tables() if not t.name and ctx.page.within(t.node, "nearby")
                  and re.search(r"\bstatus\b", core.fold(ctx.page.flat(root=t.node))[:200])]
    bad, checked, seen = [], 0, set()
    still = [h for h in homes if h.get("change") not in CHANGED]
    fold = re.search(r"\b(?:The other (\d+) homes? did not change|Where they stand): ([^.]+)\.", text)
    if not tables and ctx.kind == "email" and (fold or not still):
        # a long email says the homes that did not change in one sentence; the link copy and the PDF list each one
        if still:
            said = dict((word, int(k)) for k, word in re.findall(r"(\d+) (active|pending|sold|withdrawn)", fold.group(2)))
            want = dict((st, len([h for h in still if h.get("status") == st])) for st in STATUS_SAYS)
            want = dict((k, v) for k, v in want.items() if v)
            if fold.group(1) and int(fold.group(1)) != len(still):
                bad.append("'%s...'; %d watched homes did not change" % (fold.group(0)[:40], len(still)))
            if said != want:
                bad.append("the homes that did not change are printed as %s; the ledger gives %s" % (
                    ", ".join("%d %s" % (v, k) for k, v in sorted(said.items())) or "nothing",
                    ", ".join("%d %s" % (v, k) for k, v in sorted(want.items()))))
        B.judge("nearby_table", bad, "similar homes: the %d homes that did not change are counted by status as the ledger has them" % len(still),
                "the sentence about the watched homes that did not change does not match the ledger")
        tables, bad = [], None
    elif not tables:
        bad.append("the watch list table was not found (data-sr-table=\"nearby\")")
    for tb in tables[:1]:
        rows = _rows(tb)
        heads = [core.fold(ctx.page.flat(root=c)) for c in (rows[0][1] if rows else [])]
        cols = {}
        for k, cell in enumerate(rows[0][1] if rows else []):
            hook = cell.get("data-sr-col") or {"status": "status", "price": "price", "days": "days"}.get(heads[k])
            if hook in ("status", "price", "days"):
                cols[hook] = k
        for tr, cells in rows[1:]:
            if len(cells) < 2:
                continue
            label = core.fold(ctx.page.flat(root=cells[0]))
            key = tr.get("data-sr-row")
            idx = int(key) if (key or "").isdigit() and int(key) < len(homes) else next(
                (i for i, h in enumerate(homes) if label.startswith(core.fold(h.get("address") or "~"))), None)
            if idx is None:
                bad.append("a row that is no home on the watch list: '%s'" % label[:40])
                continue
            h = homes[idx]
            if idx in seen:
                bad.append("%s is listed twice" % h.get("address"))
            seen.add(idx)
            if core.fold(h.get("address") or "") not in label:
                bad.append("row %d is labeled '%s'; that home is %s" % (idx, label[:40], h.get("address")))
            cell = lambda name: ctx.page.flat(root=cells[cols[name]]) if name in cols and cols[name] < len(cells) else None
            st = cell("status")
            if st is not None:
                checked += 1
                if core.fold(st) != STATUS_SAYS.get(h.get("status")):
                    bad.append("%s: status printed as '%s'; the ledger says %s" % (h.get("address"), st, h.get("status")))
            pr = cell("price")
            if pr is not None:
                checked += 1
                want = h.get("sold_price") if h.get("status") == "sold" else h.get("list_price")
                if _money(pr) != ([want] if want is not None else []):
                    bad.append("%s: price printed as '%s'; the ledger gives %s" % (h.get("address"), pr, "none" if want is None else "${:,}".format(want)))
            dy = cell("days")
            if dy is not None:
                checked += 1
                want = h.get("days_on_market")
                if numbers_in(dy) != ([want] if want is not None else []):
                    bad.append("%s: days printed as '%s'; the ledger gives %s" % (h.get("address"), dy, want))
        missing = [h.get("address") for i, h in enumerate(homes) if i not in seen]
        if missing:
            bad.append("no row for %s: every watched home is listed" % ", ".join(str(a) for a in missing[:4]))
    if bad is not None:
        B.judge("nearby_table", bad, "similar homes: %d rows, %d cells of status, price and days match the ledger" % (len(seen), checked),
                "the watch list table does not match the ledger")

    # ---- what changed, with its date and prices --------------------------------------------------
    bad = []
    for i, h in moved:
        hooked = [n for n in ctx.page.elements if n.get("data-sr-row") == "change:%d" % i]
        addr = core.fold(h.get("address") or "")
        if hooked:
            line = ctx.page.flat(root=hooked[0])
        else:
            at = [mt.start() for mt in re.finditer(re.escape(addr), low)]
            line = next((text[a:a + 220] for a in at if re.search(CHANGE_SAYS[h["change"]], low[a:a + 220])), None)
        if line is None:
            bad.append("%s: its change (%s) is not printed" % (h.get("address"), h["change"].replace("_", " ")))
            continue
        fl = core.fold(line)
        if addr not in fl:
            bad.append("the change line for %s does not name it: '%s'" % (h.get("address"), line[:50]))
        if not re.search(CHANGE_SAYS[h["change"]], fl):
            bad.append("%s: printed as '%s'; the ledger says %s" % (h.get("address"), line[:60], h["change"].replace("_", " ")))
        if h.get("change_date") and core.fold(core.fmt_day(h["change_date"])) not in fl:
            bad.append("%s: the change is dated %s in the ledger, and the line does not say so: '%s'"
                       % (h.get("address"), core.fmt_day(h["change_date"]), line[:70]))
        want = {"price_change": [h.get("price_before"), h.get("list_price")], "sold": [h.get("sold_price")]}.get(h["change"], [])
        got = _money(line)
        for v in want:
            if v is not None and v not in got:
                bad.append("%s: %s is not in its change line ('%s')" % (h.get("address"), "${:,}".format(v), line[:70]))
        allowed = set(v for v in (h.get("price_before"), h.get("list_price"), h.get("sold_price")) if v is not None)
        for v in got:
            if v not in allowed:
                bad.append("%s: its change line prints %s, which is not a price of that home in the ledger" % (h.get("address"), "${:,}".format(v)))
        if h.get("days_on_market") is not None:
            said = re.search(r"after (\d+) days? on the market", line)
            if said and int(said.group(1)) != h["days_on_market"]:
                bad.append("%s: '%s'; the ledger gives %d" % (h.get("address"), said.group(0), h["days_on_market"]))
    if moved:
        B.judge("nearby_changes", bad, "similar homes: the %d changes are printed with their dates and prices" % len(moved),
                "a change among the similar homes does not match the ledger")
    bad = []
    day = core.fmt_day(nb["as_of"]) if nb.get("as_of") else None
    checked_for = bool(nb.get("checked_for_this_issue"))
    said = re.search(r"\b(Last checked|Checked) ([A-Z][a-z]{2,4} \d{1,2})\b", text)
    if not said:
        bad.append("the section does not say when the watch list was checked")
    else:
        if said.group(2) != day:
            bad.append("'%s'; the ledger says the list was checked %s" % (said.group(0), day))
        if (said.group(1) == "Checked") != checked_for:
            bad.append("'%s'; the ledger says the list was %s for this issue" % (said.group(0), "checked" if checked_for else "not checked again"))
    B.judge("nearby_checked", bad, "similar homes: the day the list was checked is printed as the ledger has it",
            "the day the watch list was checked is wrong or missing")


def _marketing(B, ctx):
    mk = ctx.ledger.get("marketing") if isinstance(ctx.ledger.get("marketing"), dict) else None
    nodes = ctx.page.sections("marketing")
    if not nodes:
        return
    text = ctx.section_text("marketing") or ""
    R = ctx.ledger.get("report") or {}
    chans = [ch for ch in (mk or {}).get("channels") or [] if isinstance(ch, dict)]
    recorded = any(ch.get("status") == "on" or (ch.get("checked") or "") >= (R.get("week_start") or "") for ch in chans)
    if not recorded:
        B.fail("marketing_recorded", "the online ads and marketing section is printed, and nothing was switched on or checked for this issue",
               ["leave the section out: it prints only when a channel is on or something was recorded for the issue"])
        return
    B.ok("marketing_recorded", "online ads and marketing: a channel is on, or something was checked for this issue")
    spend = [mt.group(0) for mt in SPEND.finditer(text)]
    B.judge("marketing_no_spend", ["an amount of money in the ads section: '%s'" % s for s in spend],
            "online ads and marketing: no ad spend amount is printed", "an ad spend amount is printed", waivable=True)
    bad, checked = [], 0
    we, rd = R.get("week_end") or "", R.get("report_date") or ""
    for i, ch in enumerate(chans):
        hooked = [n for n in ctx.page.elements if n.get("data-sr-row") == "channel:%d" % i]
        if not hooked:
            continue
        row = ctx.page.flat(root=hooked[0])
        name = ch.get("channel") or ""
        after = row[len(name):].strip() if row.startswith(name) else row
        st, running = ch.get("status"), ch.get("status") == "on" and (ch.get("checked") or "") >= we
        want = "running" if running else ("switched on" if st == "on" else MARKETING_WORDS.get(st))
        checked += 1
        if want and not core.fold(after).startswith(want):
            bad.append("%s is shown as '%s'; its status in the ledger reads %s" % (name, after[:24], want.upper()))
        if st == "on" and not running and ch.get("checked") and ("Last checked %s" % core.fmt_day(ch["checked"])) not in row:
            bad.append("%s was last checked %s, and its row does not say so" % (name, core.fmt_day(ch["checked"])))
        ends = re.search(r"\b(Was scheduled to end|Scheduled to end) ([A-Z][a-z]{2,4} \d{1,2})\b", row[:len(name) + 90])
        if ch.get("ends_on"):
            if not ends or ends.group(2) != core.fmt_day(ch["ends_on"]):
                bad.append("%s is scheduled to end %s, and its row does not say so" % (name, core.fmt_day(ch["ends_on"])))
            elif (ends.group(1) == "Scheduled to end") != (ch["ends_on"] >= rd):
                bad.append("%s: '%s' on a report dated %s" % (name, ends.group(0), core.fmt_day(rd)))
        elif ends:
            bad.append("%s: '%s' is printed, and the ledger holds no scheduled end" % (name, ends.group(0)))
    # channels named in one sentence instead of a row each: "Prepared: A and B. On hold: C. Not launched: D."
    for word, names in re.findall(r"\b(Prepared|On hold|Not launched|Ended): ([^.]+)\.", text):
        for ch in chans:
            if ch.get("channel") and re.search(r"(?<![\w])%s(?![\w])" % re.escape(ch["channel"]), names):
                checked += 1
                if MARKETING_WORDS.get(ch.get("status")) != word.lower():
                    bad.append("%s is listed under '%s'; its status in the ledger is %s" % (ch["channel"], word, str(ch.get("status")).replace("_", " ")))
    if checked:
        B.judge("marketing_words", bad, "online ads and marketing: %d channels carry the status word the ledger gives them" % checked,
                "a marketing channel is printed with the wrong status word")


def _online(B, ctx):
    o = ctx.ledger.get("online") if isinstance(ctx.ledger.get("online"), dict) else None
    text = " ".join(t for t in (ctx.section_text("numbers"), ctx.section_text("views_chart"), ctx.section_text("weekly_table")) if t)
    said = re.findall(r"\b(?:Read on|showed on|read on) ([A-Z][a-z]{2,4} \d{1,2})\b", text)
    if not o:
        return
    if said:
        day = core.fmt_day(o["as_of"])
        B.judge("online_as_of", ["'%s' is printed; the ledger says the figures were read %s" % (d, day) for d in said if d != day],
                "online views: the day the figures were read is printed as the ledger has it",
                "the day the online views were read is wrong")


def check_extras(B, ctx):
    _nearby(B, ctx)
    _marketing(B, ctx)
    _online(B, ctx)
