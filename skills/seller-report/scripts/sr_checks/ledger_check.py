# -*- coding: utf-8 -*-
"""sr_checks.ledger_check: is the ledger the page was built from sound?

Three questions, asked before a single number is looked for on the page:
  1. Do the stored totals, weeks and tallies equal what the rows give (this gate's own recount)?
  2. Does each person's stored status follow from their touches?
  3. Does the ledger pass the skill's contract (sr_contract.validate_ledger), when that module is present?

The contract module is the shared data contract, not the renderer. It is imported lazily and the gate
still runs without it.
"""
import os
import sys

from . import core
from . import recount as RC


def check(ctx):
    B = core.Bag("ledger")
    d = ctx.ledger
    try:
        mine = RC.recount(d)
    except (KeyError, TypeError, ValueError, IndexError) as e:
        B.fail("readable", "the ledger cannot be recounted: a required field is missing or malformed",
               ["%s: %s" % (type(e).__name__, e)])
        return B.results
    ctx._cache["recount"] = mine
    B.judge("rows_match",
            ["%s: the ledger says %r, its rows give %r" % x for x in RC.differences(d, mine)],
            "every stored total, weekly row and tally equals a fresh count of the ledger's rows",
            "the ledger's stored numbers do not match its own rows")
    B.judge("status_follows_touches", mine["statuses"],
            "every person's status and price row follow from their touches and conversations",
            "a stored status or price reaction disagrees with the rows")

    T, X = mine["totals"], mine["extra"]
    limits = []
    span = max(1, X["days_on_market_at_week_end"] + 1)
    early = any(t.get("date", "9") < d["listing"]["list_date"] for c in ctx.counted() for t in c.get("touches") or [])
    if T["outbound_distinct_days"] > span and not early:
        limits.append("%d separate follow-up days in %d days on the market" % (T["outbound_distinct_days"], span))
    for w in mine["weeks"]:
        if w["outbound_distinct_days"] > 7:
            limits.append("week %d: %d separate follow-up days in one week" % (w["n"], w["outbound_distinct_days"]))
    pr = mine["pricing"]
    if pr["too_high"] + pr["fair_or_positive"] + pr["not_raised"] != pr["people_with_feedback"]:
        limits.append("the three price rows add to %d, the people who gave feedback number %d"
                      % (pr["too_high"] + pr["fair_or_positive"] + pr["not_raised"], pr["people_with_feedback"]))
    if T["contacted"] > T["contacts"] or T["replied"] + T["awaiting_reply"] + T["not_yet_contacted"] != T["contacts"]:
        limits.append("answered %d + still waiting %d + not yet contacted %d does not equal %d contacts"
                      % (T["replied"], T["awaiting_reply"], T["not_yet_contacted"], T["contacts"]))
    B.judge("counts_add_up", limits, "separate days fit the calendar, the price rows add to the people who gave "
            "feedback, and answered plus waiting plus not yet contacted equals the contacts",
            "a count is impossible on its face")

    # the contract's own validator, when the module sits beside this package
    scripts = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import sr_contract as C
    except Exception as e:                                           # noqa: BLE001
        B.warn("contract", "sr_contract could not be imported, so the contract validator did not run", [str(e)])
        return B.results
    try:
        problems = C.validate_ledger(d, identity=C.load_identity(ctx.identity["path"]))
    except Exception as e:                                           # noqa: BLE001
        B.fail("contract", "sr_contract.validate_ledger stopped with an error", ["%s: %s" % (type(e).__name__, e)])
        return B.results
    B.judge("contract", problems,
            "the ledger passes sr_contract.validate_ledger",
            "the ledger does not pass the contract validator")
    return B.results


def recount_of(ctx):
    """The gate's own recount, computed once per run."""
    if "recount" not in ctx._cache:
        ctx._cache["recount"] = RC.recount(ctx.ledger)
    return ctx._cache["recount"]
