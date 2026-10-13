# -*- coding: utf-8 -*-
"""sr_checks: the ship gate of the seller-report skill. One module per family of checks.

    core           results, the run context, the report
    page           the HTML reader and the data-sr hooks
    recount        every headline number, counted again from the ledger's rows
    ledger_check   the ledger against its own rows and against the contract
    numbers        each number found printed on the page where it belongs
    privacy        nothing private and no other listing on the page
    tone           no quoted comments, no harsh words, every comment labeled
    feedback_only  no recommendation and no reading of silence on price
    brand          name, REALTOR mark, brokerage line, DRE, phone, email, disclaimer, blocklist
    hygiene        dashes, placeholders, links, no working material, the link copy's limits
    email_safety   size and the HTML a mail client will keep
    wrong_file     the right listing, issue, week and file
    layout_probe   optional: true 390, 360 and 320 px renders in Edge

Run it with scripts/check_report.py. The gate never imports the renderer.
"""
from . import core

HOOK_GUIDE = """The hooks the ship gate reads (python check_report.py --hooks prints this).

A hook is a plain attribute on the page. With hooks the gate checks each number exactly where it is printed.
Without them it falls back to finding the number by its sentence or its table heading, which is weaker.
sr_checks/sample_page.py is a small page that carries every hook below.

In <head>
  <meta name="sr:kind" content="email|link|print">     <meta name="sr:slug" content="<slug>">
  <meta name="sr:issue" content="<issue number>">       <meta name="sr:week" content="<week_start>/<week_end>">
  There is one build mode, so a page never names a build kind (a meta sr:build fails the gate).
  <meta name="robots" content="noindex, nofollow">      required on the link copy

Sections: data-sr-section="<name>" on the element (or each of the elements) that makes up the section
  draft_notice  reviewer_panel   must never appear: a page carries no notice and no panel
  brief_override                 a brief Graeham wrote himself (allowed only with --confirm-brief-override)
  masthead  followup  saying  market  next_week          the gate uses these to place numbers and names
  any other name is welcome (brief, conversations, waiting, numbers, weekly_table, price_periods, footer ...)

One value: data-sr="<id>" on the smallest element that holds exactly one printed number
  masthead    issue  address  week  dom  list_price  offers_total
  follow-up   contacted  contacts  answered  waiting  waiting_3plus  not_yet_contacted  through_host
              followups  followup_people  followup_days  replies  shared_buyers  team_side_people
              week_followups  week_followup_people  week_followup_days  week_replies
  saying      feedback_people  price_too_high  price_fair  price_not_raised  price_raised  price_asked
              conversations  theme:<key>  theme:other:<label in lower case>  liked:<key>
  the rest    keybox_showings  agent_tours  inquiries  disclosure_contacts  disclosure_sent  disclosure_opened
              oh_sessions  oh_traffic  oh_no_count  oh_no_visitors  leads_live
  anything    week:<field>  last:<field>  total:<field>   a key of ledger.weeks[] or ledger.totals
  A fact that is not recorded prints 'not recorded' inside its hook, never a number.

Tables: data-sr-table="scorecard|weeks|periods" on the <table>
  scorecard   column heads data-sr-col="this|last|total"; rows data-sr-row="<weeks field>"
  weeks       column heads data-sr-col="<weeks field>" (PRICE_PAIR for 'too high / fair', LABEL for the week column);
              rows data-sr-row="<n>" for week n, "block:<a>-<b>" for weeks folded into one row,
              "sub:<price>" for a list price subtotal, "all" for the total
  periods     column heads data-sr-col="<list price in whole dollars>"; rows data-sr-row="<price_periods field>"
  A column or row without a hook is read by its heading text.

People: data-sr-person="<contact id>" on each person's card (never on a person the link copy must not show)
Comments: data-sr="comment" on the block that holds one comment together with its 'as reported' label
"""

FAMILIES =("ledger", "numbers", "privacy", "tone", "feedback_only", "brand", "hygiene", "email_safety",
            "wrong_file", "layout")
_MODULES = {"ledger": "ledger_check", "numbers": "numbers", "privacy": "privacy", "tone": "tone",
            "feedback_only": "feedback_only", "brand": "brand", "hygiene": "hygiene", "email_safety": "email_safety",
            "wrong_file": "wrong_file", "layout": "layout_probe"}


def run(ctx, families=None, waivers=None):
    """Runs the families in order against one page and returns a core.Report."""
    import importlib
    results = []
    for fam in FAMILIES:
        if families and fam not in families:
            continue
        mod = importlib.import_module("." + _MODULES[fam], __name__)
        try:
            results += mod.check(ctx)
        except Exception as e:                      # a crashed check must never read as a pass
            import traceback
            tb = traceback.format_exc().strip().splitlines()
            results.append(core.Result(fam, "crashed", core.FAIL,
                                       "this family of checks stopped with an error, so nothing in it is verified",
                                       ["%s: %s" % (type(e).__name__, e)] + tb[-4:]))
    refused = core.apply_waivers(results, waivers)
    for rid in refused:
        results.append(core.Result("gate", "waiver_refused", core.FAIL,
                                   "%s cannot be waived (or no reason was given)" % rid))
    return core.Report(ctx, results)
