# -*- coding: utf-8 -*-
"""sr_lookups: the token rules for the optional sources, in code (references/extras.md).

Online views and similar homes nearby are optional. Each can cost a web lookup, so three rules are enforced
here instead of being left to memory:

  1. Nothing optional is fetched unless the operator asked for it in this session (--asked) or the listing's
     settings say to (listing.json, extras.<source>.every_issue). plan() refuses otherwise.
  2. Every optional source has a hard cap per issue: ONE scripted lookup for the similar homes nearby, ONE page
     per portal for online views. plan() refuses a second one, whatever became of the first.
  3. A lookup hands back compact JSON, never a page. read_result() refuses anything larger than the cap for
     that source, and anything that is not one JSON object.

A lookup that fails, is blocked, or meets a CAPTCHA is closed as skipped (skip()). Nobody works around a block.
The build then leaves that section out, and skipped_notes() gives the plain line for "Worth a glance before
you send".

The log lives inside the source's own store file (online_views.json, nearby.json) under "lookups":

    {"report_date": "2026-04-13", "key": "nearby" | "portal:Zillow", "planned_at": "...", "why": "asked" | "settings",
     "outcome": "planned" | "ok" | "skipped", "reason": null | one of sr_contract.SKIP_REASONS, "detail": null}

Standard library only. No real client data belongs in this file.
"""
import datetime
import json
import os

import sr_contract as C

SKIP_WORDS = {
    "blocked": "the site blocked the request",
    "captcha": "the site asked for a human check",
    "failed": "the lookup failed",
    "pane_unavailable": "the browser pane was not available",
    "not_found": "the listing was not found on the site",
}


class Refused(Exception):
    """A lookup that the token rules do not allow. The message is plain and says what to do instead."""


def now_iso():
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def setting(listing, source):
    """True when listing.json says this optional source is fetched for every issue without being asked."""
    return bool((((listing or {}).get("extras") or {}).get(source) or {}).get("every_issue"))


def log_of(store):
    return store.setdefault("lookups", [])


def for_issue(store, report_date, key=None):
    rd = C.iso(report_date)
    return [x for x in log_of(store) if x.get("report_date") == rd and (key is None or x.get("key") == key)]


def plan(store, key, report_date, cap, asked=False, by_setting=False, what="lookup"):
    """Opens one lookup for this issue, or raises Refused. Call it BEFORE touching the browser."""
    if not asked and not by_setting:
        raise Refused("%s: not asked for. Nothing optional is fetched unless the operator asked for it in this session "
                      "(pass --asked) or listing.json says to (extras, every_issue). Build without it." % what)
    used = for_issue(store, report_date, key)
    if len(used) >= cap:
        last = used[-1]
        raise Refused("%s: the %s allowed for the issue dated %s %s already used (%s%s). Do not run another. %s"
                      % (what, C.fmt_count(cap, "lookup"), C.iso(report_date), "is" if cap == 1 else "are", last.get("outcome"),
                         (", " + last["reason"]) if last.get("reason") else "",
                         "Close it with the result or with skip." if last.get("outcome") == "planned" else
                         "The report is built with what is on file."))
    entry = {"report_date": C.iso(report_date), "key": key, "planned_at": now_iso(), "why": "asked" if asked else "settings",
             "outcome": "planned", "reason": None, "detail": None}
    log_of(store).append(entry)
    return entry


def open_one(store, key, report_date):
    """The planned lookup of this issue that is still open, or None."""
    for x in reversed(for_issue(store, report_date, key)):
        if x.get("outcome") == "planned":
            return x
    return None


def close(store, key, report_date, outcome, reason=None, detail=None):
    """Closes the open lookup as ok or skipped. Raises Refused when none was planned: a result can only be
    stored for a lookup that plan() allowed."""
    if outcome not in ("ok", "skipped"):
        raise ValueError("outcome is ok or skipped")
    if outcome == "skipped" and reason not in C.SKIP_REASONS:
        raise Refused("a skipped lookup needs a reason: %s" % ", ".join(C.SKIP_REASONS))
    x = open_one(store, key, report_date)
    if x is None:
        raise Refused("no lookup is open for %s in the issue dated %s. Run plan first: it checks the cap and whether "
                      "the lookup was asked for." % (key, C.iso(report_date)))
    x.update(outcome=outcome, reason=reason if outcome == "skipped" else None,
             detail=C.strip_dashes(" ".join(str(detail).split()))[:200] if detail else None, closed_at=now_iso())
    return x


def skipped(store, report_date, key=None):
    """The lookups of this issue that ended as skipped."""
    return [x for x in for_issue(store, report_date, key) if x.get("outcome") == "skipped"]


def skipped_note(what, entry, leaves_out):
    """One plain line for 'Worth a glance before you send'."""
    why = SKIP_WORDS.get(entry.get("reason"), "the lookup did not finish")
    return "%s could not be checked for this report: %s. %s" % (what, why, leaves_out)


def read_result(path_or_text, max_bytes, what="lookup"):
    """The compact JSON a lookup snippet handed back, as a dict. A file path or the text itself.
    Refuses a result over the size cap (a page or a dump, not the compact result) and anything that is not one
    JSON object. A result may be a JSON string holding JSON (the browser tool quotes what a snippet returns)."""
    text = path_or_text
    if isinstance(path_or_text, str) and len(path_or_text) < 400 and os.path.exists(path_or_text):
        if os.path.getsize(path_or_text) > max_bytes * 2:
            raise Refused("%s result: the file is %d bytes. The snippet returns compact JSON of at most %d bytes; this is "
                          "something else. Never save a page or a full response." % (what, os.path.getsize(path_or_text), max_bytes))
        with open(path_or_text, encoding="utf-8") as f:
            text = f.read()
    text = (text or "").strip()
    try:
        data = json.loads(text)
        if isinstance(data, str):
            data = json.loads(data)
    except ValueError as e:
        raise Refused("%s result: not JSON (%s). Paste exactly what the snippet returned." % (what, e))
    if not isinstance(data, dict):
        raise Refused("%s result: expected one JSON object." % what)
    size = len(json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    if size > max_bytes:
        raise Refused("%s result: %d bytes, over the %d byte cap for a compact result. Do not trim it by hand: the "
                      "snippet decides what comes back." % (what, size, max_bytes))
    return data


def blocked_reason(data):
    """A skip reason when the snippet itself reports that the site would not answer, else None."""
    if not isinstance(data, dict):
        return "failed"
    if data.get("captcha"):
        return "captcha"
    if data.get("blocked"):
        return "blocked"
    if data.get("ok") is False or data.get("error"):
        return data.get("reason") if data.get("reason") in C.SKIP_REASONS else "failed"
    return None
