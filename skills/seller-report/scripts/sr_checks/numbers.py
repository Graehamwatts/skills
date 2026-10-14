# -*- coding: utf-8 -*-
"""sr_checks.numbers: every headline number, counted again from the ledger and found on the page.

How a number is looked for, in this order:
  1. A hook. An element with data-sr="<id>" must hold exactly that number (or the honest empty state when
     the fact is not recorded). When the page marks its sections, one of the hooked places must sit in the
     section the number belongs to.
  2. A sentence. When the hook is missing, known sentence shapes are searched in the text a seller reads
     ("Contacted 60 of 62", "on 41 separate days"). Every place the shape occurs must carry the right number.
  3. Not found. For a number every report must print, that is a blocking failure. For the rest it is
     reported as skipped, with the hook that would let the gate check it.

The tables (the numbers table, the week by week charts, every week in one table, the record at each list
price) and the per-person follow-up lines are checked in numbers_tables.py. The lists under "The details"
(heading count equals entries, every person once, in full at most once) are checked in numbers_lists.py.
Dates are checked in numbers_dates.py.

What this family does not prove: that a number the gate has no rule for is right. In a trial on a rendered
email, 8 in 10 printed whole numbers were caught when changed by one. The rest were dates that are still dates
in that person's record, list numbering, and a few counts stated only in prose. Mark those with
data-sr="week:<field>" or "total:<field>" and the gate checks them too.
"""
import re

from . import core
from . import recount as RC
from .ledger_check import recount_of
from .page import numbers_in

N = r"(\d{1,3}(?:,\d{3})+|\d+)"
EMPTY = re.compile(r"not recorded|no count kept|none held|not tracked|not checked|no record", re.I)
MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d+)(?![\d,]*\.\d)")
SECTION_OF = {  # claim id -> the sections it may call home
    "contacted": ("numbers", "followup"), "contacts": ("numbers", "followup"), "answered": ("numbers", "followup"),
    "waiting": ("numbers", "followup"), "waiting_3plus": ("followup", "numbers"),
    "followups": ("followup", "numbers"), "followup_days": ("followup", "numbers"), "replies": ("followup", "numbers"),
    "feedback_people": ("saying",), "price_too_high": ("saying",), "price_fair": ("saying",),
    "price_not_raised": ("saying",), "dom": ("masthead",), "list_price": ("masthead",), "offers_total": ("masthead", "followup", "offers"),
}


def to_int(s):
    return int(str(s).replace(",", ""))


class Claim(object):
    def __init__(self, cid, label, value, shapes=(), required=False, zero_ok=False, money=False, kinds=core.KINDS, scope=None):
        self.id, self.label, self.value, self.shapes = cid, label, value, shapes
        self.required, self.zero_ok, self.money, self.kinds = required, zero_ok, money, kinds
        self.scope = scope            # a section name: the sentence is looked for there only (other homes have beds and square feet too)


def _claims(ctx, m):
    d, T, X, W = ctx.ledger, m["totals"], m["extra"], m["this_week"] or {}
    pv = lambda name, val: RC.printable(d, name, val)                      # noqa: E731
    host = T["contacted_through_host"]

    def contacted_want(mt):
        return T["contacted"] - host if (mt.group(3) or "").strip().startswith("directly") else T["contacted"]

    line = r"[Cc]ontacted %s of %s(?: (?:people|person|agents and buyers|agents))?( directly)?" % (N, N)
    C = [
        Claim("contacted", "people contacted", T["contacted"], required=True,
              shapes=[(line, 1, contacted_want)]),
        Claim("contacts", "people we follow up with", T["contacts"], required=True,
              shapes=[(line, 2), (r"Out of the %s agents and buyers we follow up with" % N, 1)]),
        Claim("answered", "answered", T["replied"], required=True,
              shapes=[(r"\b%s answered\b(?! (?:an )?earlier)" % N, 1), (r"\b[Oo]f the %s who answered" % N, 1)]),
        Claim("waiting", "still waiting", T["awaiting_reply"], required=True,
              shapes=[(r"[Ss]till waiting on %s\b" % N, 1), (r"\b%s still waiting(?! ha(?:s|ve) been)" % N, 1)]),
        Claim("waiting_3plus", "still waiting after 3 or more tries", T["awaiting_reply_3plus_attempts"],
              required=True, zero_ok=True,
              shapes=[(r"\b%s of them after 3 or more tries" % N, 1),
                      (r"\b%s of the %s still waiting ha(?:s|ve) been tried on 3 or more days" % (N, N), 1),
                      (r"\bAll %s still waiting have been tried on 3 or more days" % N, 1),
                      (r"\bThe %s person still waiting has been tried on 3 or more days" % N, 1)]),
        Claim("not_yet_contacted", "not yet contacted", T["not_yet_contacted"],
              shapes=[(r"\b%s not yet (?:reached|contacted)" % N, 1), (r"\b%s (?:people|person) ha(?:s|ve) not been reached yet" % N, 1)]),
        Claim("through_host", "contacted through the open house host", host,
              shapes=[(r"\band %s through the open house host" % N, 1),
                      (r"\b%s more visitors? (?:was|were) reached only through the open house host" % N, 1)]),
        Claim("followups", "follow-ups since we listed", T["touches_outbound"], required=True,
              shapes=[(r"Since we listed: %s follow-ups? to %s (?:people|person)" % (N, N), 1),
                      (r"\b%s FOLLOW-UPS?\b" % N, 1),
                      (r"\b%s follow-ups? and %s repl(?:y|ies) since we listed" % (N, N), 1)]),
        Claim("followup_people", "people we followed up with", X["followup_people"],
              shapes=[(r"Since we listed: %s follow-ups? to %s (?:people|person)" % (N, N), 2),
                      (r"Our follow-ups went to %s (?:people|person)" % N, 1)]),
        Claim("followup_days", "separate days of follow-up", T["outbound_distinct_days"], required=True,
              shapes=[(r"\bon %s separate days?\b" % N, 1), (r"\b%s SEPARATE DAYS?\b" % N, 1)]),
        Claim("replies", "replies since we listed", T["replies_inbound"], required=True,
              shapes=[(r"separate days?\. %s repl(?:y|ies)\b" % N, 1), (r"SEPARATE DAYS? %s REPL(?:Y|IES)\b" % N, 1),
                      (r"\b%s follow-ups? and %s repl(?:y|ies) since we listed" % (N, N), 2)]),
        Claim("week_followups", "follow-ups this week", W.get("touches_outbound"),
              shapes=[(r"This week: %s follow-ups? to %s (?:people|person) on %s days?\b" % (N, N, N), 1)]),
        Claim("week_followup_people", "people followed up with this week", W.get("outbound_people"),
              shapes=[(r"followed up with %s (?:people|person) on %s days?\b" % (N, N), 1),
                      (r"Follow-ups we made to %s (?:people|person) on %s days?\b" % (N, N), 1),
                      (r"This week: %s follow-ups? to %s (?:people|person) on %s days?\b" % (N, N, N), 2)]),
        Claim("week_followup_days", "separate follow-up days this week", W.get("outbound_distinct_days"),
              shapes=[(r"followed up with %s (?:people|person) on %s days?\b" % (N, N), 2),
                      (r"Follow-ups we made to %s (?:people|person) on %s days?\b" % (N, N), 2),
                      (r"This week: %s follow-ups? to %s (?:people|person) on %s days?\b" % (N, N, N), 3)]),
        Claim("week_replies", "replies this week", W.get("replies_inbound")),
        Claim("shared_buyers", "buyers who got the package from their own agent", T["disclosure_shared_buyers"],
              shapes=[(r"\b%s more buyers? got the (?:disclosure )?package from" % N, 1),
                      (r"\b%s buyers? also got the package from their own agent" % N, 1)]),
        Claim("team_side_people", "open house hosts set aside", T["team_side_people"],
              shapes=[(r"\b%s open house hosts? works? with us" % N, 1), (r"\b%s hosts? works? on our side of the table" % N, 1)]),
        Claim("dom", "days on market on the report date", X["days_on_market"], required=True,
              shapes=[(r"\bDay %s\b" % N, 1), (r"\bis day %s\b" % N, 1), (r"This home: day %s\b" % N, 1)]),
        Claim("list_price", "list price", d["listing"]["list_price"], required=True, money=True,
              shapes=[(r"LIST PRICE \$%s" % N, 1)]),
        Claim("offers_total", "offers to date", T["offers"], required=True,
              shapes=[(r"OFFERS TO DATE %s\b" % N, 1), (r"Offers to date: %s\b" % N, 1)]),
        Claim("showings", "showings since we listed (key-box showings plus tours agents reported)", T["showings"],
              shapes=[(r"\b%s showings? since we listed" % N, 1)]),
        Claim("keybox_showings", "key-box showings since we listed", pv("keybox_showings", T["keybox_showings"]),
              shapes=[(r"\b%s (?:completed )?key[- ]?box showings? since we listed" % N, 1),
                      (r"key-box showings \(%s since we listed\)" % N, 1)]),
        Claim("agent_tours", "tours reported to our team since we listed", T["agent_reported_tours"],
              shapes=[(r"\b%s tours? reported (?:to our team|by agents) since we listed" % N, 1),
                      (r"tours agents told us about \(%s\)" % N, 1)]),
        Claim("inquiries", "inquiries since we listed", T["inquiries"]),
        Claim("disclosure_contacts", "people on the disclosure package list", T["disclosure_contacts"]),
        Claim("disclosure_sent", "disclosure packages sent", pv("disclosure_link_sent", T["disclosure_link_sent"])),
        Claim("disclosure_opened", "disclosure packages opened",
              pv("disclosure_opened_confirmed", T["disclosure_opened_confirmed"])),
        Claim("oh_sessions", "open house sessions since we listed", T["open_house_sessions"],
              shapes=[(r"\b%s sessions? since we listed" % N, 1)]),
        Claim("oh_traffic", "open house traffic counted", T["open_house_groups"],
              shapes=[(r"sessions? since we listed, %s (?:groups?|visitors?|guests?|parties|party|people) counted" % N, 1)]),
        Claim("oh_no_count", "open house sessions with no count kept", T["open_house_sessions_without_count"],
              shapes=[(r"\b%s sessions? (?:with no count kept|kept no count)" % N, 1)]),
        Claim("oh_no_visitors", "open house sessions nobody came to", T["open_house_sessions_no_visitors"]),
        Claim("feedback_people", "people who gave feedback (the denominator)", m["pricing"]["people_with_feedback"],
              required=True,
              shapes=[(r"Counts out of %s (?:people|person)" % N, 1),
                      (r"\bof the %s (?:agents and buyers|agents|buyers|people)[^.]{0,20}who gave us feedback" % N, 1),
                      (r"\b%s (?:people|agents and buyers) (?:have )?(?:gave|given) us feedback" % N, 1)]),
        Claim("price_raised", "people who brought up price", m["pricing"]["raised_price"],
              shapes=[(r"Price came up with %s of the %s" % (N, N), 1)]),
        Claim("conversations", "conversations with feedback", T["conversations_with_feedback"],
              shapes=[(r"who gave us feedback \(%s conversations?\)" % N, 1)]),
        Claim("price_asked", "people asked about price directly", m["pricing"]["asked_directly"],
              shapes=[(r"[Aa]sked directly: %s of %s" % (N, N), 1)]),
        Claim("leads_live", "buyers still deciding", X["leads_live"], kinds=("email",)),
    ]
    return C + _more_claims(ctx, m)


def _more_claims(ctx, m):
    """The supporting numbers a page states in passing. None is required; each is checked where it is printed."""
    d, T, X, W = ctx.ledger, m["totals"], m["extra"], m["this_week"] or {}
    L, S, NF, MK = d["listing"], m["totals"]["by_status"], X["no_final"], X["market"]
    aside = T["team_side_set_aside"]
    dated_new = sum(w["disclosure_contacts_new"] for w in m["weeks"])
    hosts_with_buyers = len([c for c in d.get("contacts") or [] if c.get("is_open_house_host") and not c.get("team_side")])
    dis = r"\b%s dated in the weeks, %s more with no date on file, %s in all" % (N, N, N)
    inq = r"\b%s of the %s inquir(?:y|ies) ha(?:s|ve) no date, so the weeks add to %s" % (N, N, N)
    C = [
        Claim("week_reply_people", "people we heard from this week", X["week_reply_people"],
              shapes=[(r"\bWe heard from %s (?:people|person)" % N, 1), (r"\band heard back from %s\b" % N, 1)]),
        Claim("waiting_answered_before", "still waiting who answered an earlier follow-up", T["awaiting_reply_answered_before"],
              shapes=[(r"\b%s of the %s answered an earlier one" % (N, N), 1)]),
        Claim("approximate_of_tours", "showing dates that are approximate, where restated", T["tours_approximate_date"],
              shapes=[(r"\b%s of the %s (?:tour|showing) dates (?:is|are) approximate" % (N, N), 1)]),
        Claim("disclosure_dated", "disclosure list people dated in the weeks", dated_new, shapes=[(dis, 1)]),
        Claim("disclosure_undated", "disclosure list people with no date", T["disclosure_contacts_undated"], shapes=[(dis, 2)]),
        Claim("disclosure_in_all", "disclosure list people in all", T["disclosure_contacts"], shapes=[(dis, 3)]),
        Claim("inquiries_undated", "inquiries with no date", T["inquiries_undated"], shapes=[(inq, 1)]),
        Claim("inquiries_in_all", "inquiries in all", T["inquiries"], shapes=[(inq, 2)]),
        Claim("inquiries_dated", "inquiries the weeks add to", T["inquiries"] - T["inquiries_undated"], shapes=[(inq, 3)]),
        Claim("hosts_with_buyers", "hosts who also showed the home to their own buyers", hosts_with_buyers,
              shapes=[(r"\b%s more hosts? also showed the home to buyers of their own" % N, 1)]),
        Claim("followup_people_through_host", "people followed up with through the host", X["followup_people_through_host"],
              shapes=[(r"\(%s of them through the open house host\)" % N, 1)]),
        Claim("passed", "people who passed", S["passed"], shapes=[(r"who answered: %s passed" % N, 1)]),
        Claim("no_final_answer", "people who gave no final answer", T["open_no_final_answer"],
              shapes=[(r"\b%s gave no final answer" % N, 1), (r"No final answer \(%s\)" % N, 1)]),
        Claim("no_final_interested", "no final answer, interested", NF["interested"],
              shapes=[(r"No final answer \(%s\): %s interested" % (N, N), 2)]),
        Claim("no_final_undecided", "no final answer, undecided", NF["undecided"],
              shapes=[(r"No final answer \(%s\):[^.]*?\b%s undecided" % (N, N), 2)]),
        Claim("no_final_no_read", "no final answer, no read yet", NF["no_read"],
              shapes=[(r"No final answer \(%s\):[^.]*?\b%s with no read yet" % (N, N), 2)]),
        Claim("no_final_quiet", "no final answer and quiet for 30 days", T["open_no_final_answer_quiet"],
              shapes=[(r"\b%s of them have had no contact with us in the last 30 days" % N, 1)]),
        Claim("week_conversations", "conversations this week", W.get("conversations_with_feedback"),
              shapes=[(r"This week: %s conversations?\b" % N, 1)]),
        Claim("week_oh_sessions", "open houses this week", W.get("open_house_sessions"),
              shapes=[(r"\b%s open houses? this week" % N, 1)]),
        Claim("liked_people", "people who named something they liked", X["liked_people"],
              shapes=[(r"\b%s of the %s people named something they liked" % (N, N), 1)]),
        Claim("weeks_on_market", "weeks on the market", X["weeks_on_market"],
              shapes=[(r"\b%s weeks? on the market, every week" % N, 1)]),
        Claim("week_showings", "showings this week, where restated", W.get("showings"),
              shapes=[(r"\b%s showings? since we listed, %s this week" % (N, N), 2)]),
        Claim("conversations_people", "conversations and the people they come from", T["conversations_with_feedback"],
              shapes=[(r"the %s conversations come from %s different people" % (N, N), 1)]),
        Claim("feedback_people_again", "people who gave feedback, where it is restated", m["pricing"]["people_with_feedback"],
              shapes=[(r"the %s conversations come from %s different people" % (N, N), 2),
                      (r"\bWhat %s (?:agents and buyers|agents?|buyers?|people) ha(?:s|ve) told us" % N, 1),
                      (r"\b%s of the %s people named something they liked" % (N, N), 2)]),
        Claim("aside_messages", "messages to open house hosts, set aside", aside["touches_outbound"],
              shapes=[(r"Not in these totals: %s messages? to %s open house hosts? and %s repl(?:y|ies)" % (N, N, N), 1),
                      (r"\bour %s messages? to them (?:is|are) not counted" % N, 1)]),
        Claim("aside_hosts", "open house hosts set aside", aside["people"],
              shapes=[(r"Not in these totals: %s messages? to %s open house hosts? and %s repl(?:y|ies)" % (N, N, N), 2)]),
        Claim("aside_replies", "replies from open house hosts, set aside", aside["replies_inbound"],
              shapes=[(r"Not in these totals: %s messages? to %s open house hosts? and %s repl(?:y|ies)" % (N, N, N), 3)]),
        Claim("approximate_tour_dates", "tour dates that are approximate", T["tours_approximate_date"],
              shapes=[(r"\b%s dates? of (?:a showing or tour|showings or tours) (?:is|are) approximate" % N, 1)]),
        Claim("beds", "bedrooms", L.get("beds"), shapes=[(r"\b%s bed, [\d.]+ bath, %s sq ft" % (N, N), 1)], scope="masthead"),
        Claim("sqft", "square feet", L.get("sqft"), shapes=[(r"\b%s bed, [\d.]+ bath, %s sq ft" % (N, N), 2)], scope="masthead"),
        Claim("marketing_running", "marketing channels confirmed running for this issue", X["marketing_running"],
              shapes=[(r"\b%s channels? (?:confirmed )?running\b" % N, 1)]),
        Claim("online_views_total", "online views since we listed", T.get("online_views"),
              shapes=[(r"\b%s views? since we listed, as counted by" % N, 1), (r"\b%s views? since we listed on the sites? we read" % N, 1)]),
    ]
    if MK:
        under = r"\b%s of the %s [a-z ]{3,40}? were under contract by that" % (N, N)
        C += [Claim("market_under_contract", "comparable sales under contract by this day", MK["under_contract_by_now"], shapes=[(under, 1)]),
              Claim("market_sales_used", "comparable sales compared", MK["used"], shapes=[(under, 2)]),
              Claim("market_average", "average days to an accepted offer", MK["average"], shapes=[(r"Average %s days, median %s\b" % (N, N), 1)]),
              Claim("market_median", "median days to an accepted offer", MK["median"], shapes=[(r"Average %s days, median %s\b" % (N, N), 2)])]
    return [c for c in C if c.value is not None or c.id in ("beds", "sqft")]


def _week_channels(B, ctx, m, text):
    """'This week: ... (2 calls, 1 text, 1 email)': each channel count against this week's follow-ups."""
    W = m["this_week"]
    mt = re.search(r"This week:[^().]{0,90}\(([^)]{3,80})\)", text)
    if not W or not mt:
        return
    ch, bad = W["by_channel"], []
    for num, word in re.findall(r"%s (calls?|texts?|emails?|follow-ups?|visits? in person)" % N, mt.group(1)):
        w = word.lower()
        have = ch["in_person"] if "in person" in w else {"call": ch["call"], "text": ch["text"], "email": ch["email"],
                                                         "follow-up": W["touches_outbound"]}.get(w.rstrip("s"))
        if have != to_int(num):
            bad.append("'%s %s' this week; the log gives %s" % (num, word, have))
    B.judge("week_channels", bad, "this week's calls, texts and emails match the log (%s)" % mt.group(1),
            "this week's follow-up by channel does not match the log")


def _generic_hooks(B, ctx, m):
    """Any other number the renderer chooses to mark: data-sr="week:<field>", "last:<field>" or "total:<field>",
    where <field> is a key of the ledger's weeks rows or totals. Each must print the recounted value."""
    T, bad, checked = m["totals"], [], 0
    rows = {"week": m["this_week"], "last": m["last_week"], "total": T}
    for n in ctx.page.elements:
        name = n.get("data-sr") or ""
        scope, _, field = name.partition(":")
        if scope not in rows or not field:
            continue
        row = rows[scope]
        if row is None or field not in row or isinstance(row[field], (dict, list)):
            bad.append("data-sr=%s (line %d) names a number the gate does not count" % (name, n.line))
            continue
        stored = next((w for w in ctx.ledger.get("weeks") or [] if w.get("n") == row.get("n")), None) if scope != "total" else None
        want = RC.printable(ctx.ledger, field, row[field], stored)
        txt = ctx.page.flat(root=n)
        nums = numbers_in(txt)
        checked += 1
        if (want is None and (nums or not EMPTY.search(txt))) or (want is not None and nums != [want]):
            bad.append("data-sr=%s prints '%s' (line %d); the rows give %s" % (name, txt[:50], n.line, "not recorded" if want is None else want))
    if checked or bad:
        B.judge("marked_values", bad, "%d more marked values (week:, last: and total: hooks) match the recount" % checked,
                "a value marked with a week:, last: or total: hook does not match the recount")


def _market_rows(B, ctx, m):
    """The days-to-contract of every comparable sale used, as printed in the market section."""
    mk, text = m["extra"]["market"], ctx.section_text("market")
    if not mk or not text:
        return
    sales = [s["days_to_contract"] for s in (ctx.ledger.get("market") or {}).get("sales") or []
             if s.get("used_in_average") and isinstance(s.get("days_to_contract"), int)]
    printed = numbers_in(text)
    left, missing = list(printed), []
    for v in sales:
        if v in left:
            left.remove(v)
        else:
            missing.append(v)
    if len(missing) > len(sales) / 2.0:
        B.skip("market_rows", "the market section does not list each comparable sale's days, so they were not compared")
    else:
        B.judge("market_rows", ["a sale that took %d days to go under contract is not printed (or is printed with another number)" % v
                                for v in missing],
                "the %d comparable sales are printed with their days to an accepted offer" % len(sales),
                "the market section does not match the ledger's comparable sales")


def _marketing(B, ctx, m, text):
    """A channel is called running only when it is on and was checked for this issue."""
    late = [n for n in m["extra"]["marketing_not_running"] if n]
    bad = []
    for name in late:                                       # "switched on" with the day last checked is the honest word; "running" is not
        for mt in re.finditer(re.escape(name) + r"\s+(RUNNING\b|Running\b|LIVE\b|ACTIVE\b)", text):
            bad.append("'%s' is shown as %s, but it was not confirmed on for this issue" % (name, mt.group(1)))
    if late or m["extra"]["marketing_running"]:
        B.judge("marketing_running_rule", bad, "no channel is called running unless it was checked on for this issue",
                "a marketing channel is called running without a check for this issue")


def _hook_verdict(ctx, cl, nodes):
    """(problems, loose, placed) for the hooked elements of one claim."""
    problems, loose = [], []
    for n in nodes:
        txt = ctx.page.flat(root=n)
        nums = [to_int(x) for x in MONEY.findall(txt)] if cl.money else numbers_in(txt)
        if cl.value is None:
            if nums or not EMPTY.search(txt):
                problems.append("data-sr=%s prints '%s' (line %d); this fact is not recorded, so it must say so"
                                % (cl.id, txt[:70], n.line))
        elif nums == [cl.value]:
            pass
        elif cl.value in nums:
            loose.append("data-sr=%s wraps '%s' (line %d)" % (cl.id, txt[:70], n.line))
        else:
            problems.append("data-sr=%s prints '%s' (line %d); the rows give %s" % (cl.id, txt[:70], n.line, _show(cl)))
    homes = SECTION_OF.get(cl.id)
    placed = True
    if homes and ctx.page.section_names():
        present = [h for h in homes if ctx.page.sections(h)]
        if present and not any(ctx.page.within(n, h) for n in nodes for h in present):
            placed = False
    return problems, loose, placed


def _show(cl):
    if cl.value is None:
        return "not recorded"
    return "${:,}".format(cl.value) if cl.money else str(cl.value)


def _sentence_verdict(text, cl):
    """(found, problems) from the known sentence shapes."""
    found, problems = 0, []
    for shape in cl.shapes:
        pattern, group = shape[0], shape[1]
        for mt in re.finditer(pattern, text):
            want = shape[2](mt) if len(shape) > 2 else cl.value
            got = to_int(mt.group(group))
            found += 1
            if want is None:
                problems.append("'%s': a number is printed for a fact that is not recorded" % core.excerpt(text, mt.start(), mt.end(), 25))
            elif got != want:
                problems.append("'%s': prints %d, the rows give %d" % (core.excerpt(text, mt.start(), mt.end(), 25), got, want))
    return found, problems


def _judge_claim(B, ctx, cl, text):
    rule = cl.id
    if cl.scope and ctx.section_text(cl.scope):
        text = ctx.section_text(cl.scope)
    nodes = ctx.page.hooks(cl.id)
    if nodes:
        problems, loose, placed = _hook_verdict(ctx, cl, nodes)
        _, more = _sentence_verdict(text, cl)                      # a hooked page is still read as text
        problems += more
        if problems:
            B.fail(rule, "%s: the page does not print %s" % (cl.label, _show(cl)), problems)
        elif not placed:
            B.fail(rule, "%s is printed, but not in the section it belongs to (%s)"
                   % (cl.label, " or ".join(SECTION_OF[cl.id])), ["found in: %s" % ", ".join(
                       sorted(set(str(ctx.page.section_of(n)) for n in nodes)))])
        elif loose:
            B.warn(rule, "%s = %s found, but the hook wraps more than one number, so the match is loose"
                   % (cl.label, _show(cl)), loose[:4])
        else:
            B.ok(rule, "%s = %s (hook, %d place%s)" % (cl.label, _show(cl), len(nodes), "" if len(nodes) == 1 else "s"))
        return
    found, problems = _sentence_verdict(text, cl)
    if problems:
        B.fail(rule, "%s: the page does not print %s" % (cl.label, _show(cl)), problems)
    elif found:
        B.ok(rule, "%s = %s (sentence, %d place%s; no data-sr hook)" % (cl.label, _show(cl), found, "" if found == 1 else "s"))
    elif cl.required and not (cl.zero_ok and not cl.value):
        B.fail(rule, "%s (%s) was not found on the page" % (cl.label, _show(cl)),
               ["no element carries data-sr=\"%s\" and no known sentence states it" % cl.id])
    else:
        B.skip(rule, "%s (%s): not located. Add data-sr=\"%s\" where it is printed and the gate will check it"
               % (cl.label, _show(cl), cl.id))


# ---------------------------------------------------------------------------------------------
# what people are saying: the three price rows, the theme rows and what people liked
# ---------------------------------------------------------------------------------------------
ROW_TAGS = ("tr", "li", "p", "div", "td", "th", "dd", "dt", "span")


def _blocks(ctx):
    """(node, folded text) for every row-like element a seller reads, computed once. Rows of the three
    number tables are left out: their labels can repeat a tally label ('Said the price is too high' per list
    price), and those tables are checked cell by cell in numbers_tables."""
    if "blocks" not in ctx._cache:
        from . import numbers_tables as NT
        m = recount_of(ctx)
        tables = NT._scorecards(ctx)[0] + [tb for tb, _ in NT._weeks_tables(ctx)[0]] + NT._period_tables(ctx, m)[0]
        skip = set(id(n) for x in [tb.node for tb in tables] for n in [x] + list(x.iter()))
        ctx._cache["blocks"] = [(n, core.fold(ctx.page.flat(root=n))) for n in ctx.page.elements
                                if n.tag in ROW_TAGS and id(n) not in skip]
    return ctx._cache["blocks"]


def _label_rows(ctx, label):
    """The smallest rows that print the label with a count beside it: [(counts in that row, the row's text)].
    A row is one element (a table row, a list item, a line), so a neighbour's count is never read."""
    lab = core.fold(label)
    # The row opens with the label, or with its count and then the label ("51 did not bring up price"), and
    # the label is not the first words of a longer one ("Location" inside "Location or surroundings").
    opens = re.compile(r"(?:\d[\d,]* )?%s\s*(?:$|[\d:(\[|,.;*%s-])" % (re.escape(lab), chr(0xB7)))
    home = ctx.page.sections("saying")              # when the page marks the section, rows outside it are not tally rows
    hits = sorted(((len(t), i, n, t) for i, (n, t) in enumerate(_blocks(ctx)) if opens.match(t) and len(t) <= len(lab) + 170
                   and (not home or ctx.page.within(n, "saying"))),
                  key=lambda h: (h[0], h[1]))
    out, taken = [], []
    for _, _, n, t in hits:
        if any(any(id(a) == id(n) for a in k.ancestors()) for k in taken):
            continue                                    # a row inside this one already answered
        rest = re.sub(r"\b\d+ new this week\b", " ", t.replace(lab, " ", 1))
        nums = numbers_in(rest)
        if nums:
            taken.append(n)
            out.append((nums, t[:90]))
    return out


def _tally_row(B, ctx, text, rule, hook, label, value, required):
    nodes = ctx.page.hooks(hook)
    if nodes:
        bad = []
        people = recount_of(ctx)["pricing"]["people_with_feedback"]
        for n in nodes:
            nums = numbers_in(ctx.page.flat(root=n))
            if nums != [value]:
                bad.append("data-sr=%s prints '%s' (line %d); the rows give %d" % (hook, ctx.page.flat(root=n)[:60], n.line, value))
                continue
            around = ctx.page.flat(root=n.parent) if n.parent is not None else ""
            said = re.search(r"\b%d (?:out )?of %s\b" % (value, N), around) if len(around) < 200 else None
            if said and to_int(said.group(1)) != people:
                bad.append("'%s' (line %d): printed out of %s, and %d people gave feedback" % (around[:60], n.line, said.group(1), people))
        if bad:
            B.fail(rule, "'%s': the page does not print %d" % (label, value), bad)
        else:
            B.ok(rule, "'%s' = %d (hook)" % (label, value))
        return True
    seen = [row for lab in ([label] if isinstance(label, str) else label) for row in _label_rows(ctx, lab)]
    label = label if isinstance(label, str) else label[0]
    if not seen:
        if required:
            B.fail(rule, "the row '%s' (%d) is not on the page" % (label, value),
                   ["no data-sr=\"%s\" and the label is not printed with a count beside it" % hook])
        return False
    wrong = [(nums, t) for nums, t in seen if nums[0] != value]          # the count is the first number in the row
    people = recount_of(ctx)["pricing"]["people_with_feedback"]
    out_of = [(nums, t) for nums, t in seen if nums[0] == value and len(nums) > 1 and nums[1] != people
              and re.search(r"\b%d (?:out )?of %d\b" % (nums[0], nums[1]), t)]
    if out_of and not wrong:
        B.fail(rule, "'%s': the count is right, but it is printed out of %d and %d people gave feedback" % (label, out_of[0][0][1], people),
               ["'%s'" % t for _, t in out_of[:3]])
    elif not wrong:
        B.ok(rule, "'%s' = %d (label and count in one row, no data-sr hook)" % (label, value))
    else:
        B.fail(rule, "'%s': the row does not print %d" % (label, value),
               ["'%s' (counts read: %s)" % (t, ", ".join(str(x) for x in nums[:3])) for nums, t in wrong[:4]])
    return True


def _saying(B, ctx, m):
    text = ctx.section_text("saying") or ctx.seller_flat()
    vocab = ctx.ledger.get("themes_vocabulary") or {}
    pr = m["pricing"]
    labels = dict((r["key"], r["label"]) for r in vocab.get("price_rows") or [])
    for key, hook in (("too_high", "price_too_high"), ("fair_or_positive", "price_fair"), ("not_raised", "price_not_raised")):
        _tally_row(B, ctx, text, hook, hook, labels.get(key, key), pr[key], required=True)
    link = ctx.kind in ("link", "print")
    found_any, missing = False, []
    for r in m["themes"]:
        if link and r["hide_in_link_copy"]:
            continue                                              # hygiene checks that the link copy leaves it out
        hook = "theme:%s" % r["key"] if r["key"] != "other" else "theme:other:%s" % core.fold(r["label"])
        got = _tally_row(B, ctx, text, "theme." + r["key"], hook, r["label"], r["people"], required=False)
        found_any = found_any or got
        if not got:
            missing.append("%s (%d)" % (r["label"], r["people"]))
    if m["themes"] and not found_any:
        B.fail("themes_printed", "none of the %d topics people raised is on the page" % len(m["themes"]), missing[:8])
    elif missing:
        B.warn("themes_printed", "%d of %d topic rows were not found (a shortened tally is allowed, a wrong one is not)"
               % (len(missing), len(m["themes"])), missing[:8])
    elif m["themes"]:
        B.ok("themes_printed", "all %d topic rows are printed with their counts" % len(m["themes"]))
    theme_labels = set(core.fold(t["label"]) for t in vocab.get("themes") or [])
    for r in m["liked"]:
        hook = "liked:%s" % r["key"]
        twin = core.fold(r["label"]) in theme_labels or any(t.startswith(core.fold(r["label"]) + " ") for t in theme_labels)
        alts = ["Liked: " + r["label"]] + ([] if twin else [r["label"]])
        if not _tally_row(B, ctx, text, "liked." + r["key"], hook, alts if not ctx.page.hooks(hook) else r["label"], r["people"],
                          required=False) and twin:
            B.skip("liked." + r["key"], "'%s' (%d) is also the name of a topic row, so the gate cannot tell the two apart. "
                   "Add data-sr=\"%s\" to the count, or label the row 'Liked: %s'" % (r["label"], r["people"], hook, r["label"]))


# ---------------------------------------------------------------------------------------------
# what a showing counts, the counts this week in brief states, and offers with the recorded price and percent
# ---------------------------------------------------------------------------------------------
def _showings_defined(B, ctx, text):
    """Showings is one number: key-box showings plus the tours agents reported. The page must say what it
    counts, and that an inquiry is not a showing, wherever it prints the number."""
    says_what = re.search(r"[Ss]howings (?:count|are) [^.]{0,60}(?:key-box showings|tours agents told us about)", text)
    says_not = re.search(r"inquiry(?:, not| and is never counted as) a showing|never (?:counted as )?a showing", text)
    bad = []
    if not says_what:
        bad.append("the page does not say what a showing is (key-box showings plus tours agents told us about)")
    if not says_not:
        bad.append("the page does not say that an inquiry is not a showing")
    B.judge("showings_defined", bad, "the page says what a showing counts, and that an inquiry is never a showing",
            "the Showings number is printed without saying what it counts")


BRIEF_COUNTS = ((r"\b(\d+|no|zero) (?:more |new )?showings?\b", "showings", "showings"),
                (r"\b(\d+|no|zero) (?:more |new )?inquir(?:y|ies)\b", "inquiries", "inquiries"),
                (r"\b(\d+|no|zero) new disclosure packages?\b", "disclosure_contacts_new", "new disclosure packages"),
                (r"\b[Ww]e received (\d+|no|zero) offers?\b", "offers", "offers"))


def _brief(B, ctx, m):
    """This week in brief, and the inbox preview line that repeats its first sentence: the counts they state are
    this week's counts. A brief the operator wrote is theirs."""
    W = m["this_week"]
    nodes = ctx.page.sections("brief")
    if not W or ctx.page.sections("brief_override"):
        return
    skip = ctx.page.sections("since_week_closed")
    text = core.squash(" ".join([ctx.page.text(root=n, skip=skip) for n in nodes] + [ctx.page.hidden_text()]))
    if not text:
        return
    bad, seen = [], 0
    for pattern, field, word in BRIEF_COUNTS:
        for mt in re.finditer(pattern, text):
            seen += 1
            got = 0 if mt.group(1) in ("no", "zero") else to_int(mt.group(1))
            if got != W[field]:
                bad.append("'%s': this week had %d %s" % (core.excerpt(text, mt.start(), mt.end(), 20), W[field], word))
    if bad:
        B.fail("brief_week", "this week in brief states a count that is not this week's", bad)
    elif seen:
        B.ok("brief_week", "the %d counts this week in brief states are this week's" % seen)


def _offers(B, ctx, text):
    offers = ctx.ledger.get("offers") or []
    if ctx.kind != "email" or not offers:
        return
    known = set((int(o["price"]), "%g" % o["pct_of_list"]) for o in offers
                if o.get("price") is not None and o.get("pct_of_list") is not None)
    bad, seen = [], 0
    for mt in re.finditer(r"\$%s, (\d+(?:\.\d+)?)%% of the list price" % N, text):
        seen += 1
        if (to_int(mt.group(1)), "%g" % float(mt.group(2))) not in known:
            bad.append("'%s' matches no offer on record" % core.excerpt(text, mt.start(), mt.end(), 20))
    if bad:
        B.fail("offer_terms", "an offer is printed with a price or percent that is not in the ledger", bad)
    elif seen:
        B.ok("offer_terms", "%d printed offer price and percent pairs match the ledger" % seen)
    else:
        B.skip("offer_terms", "no offer is printed in the form '$price, N% of the list price', so the pairs were not compared")


def check(ctx):
    from . import numbers_tables as NT
    B = core.Bag("numbers")
    try:
        m = recount_of(ctx)
    except (KeyError, TypeError, ValueError, IndexError) as e:
        B.fail("recount", "the numbers cannot be recounted from this ledger", ["%s: %s" % (type(e).__name__, e)])
        return B.results
    text = ctx.seller_flat()
    for cl in _claims(ctx, m):
        if ctx.kind in cl.kinds:
            _judge_claim(B, ctx, cl, text)
    _saying(B, ctx, m)
    _showings_defined(B, ctx, text)
    _brief(B, ctx, m)
    _offers(B, ctx, text)
    _week_channels(B, ctx, m, text)
    _marketing(B, ctx, m, text)
    _market_rows(B, ctx, m)
    _generic_hooks(B, ctx, m)
    NT.check_tables(B, ctx, m)
    NT.check_people(B, ctx, m, text)
    from . import numbers_lists as NL
    NL.check_lists(B, ctx, m)
    from . import numbers_dates as ND
    ND.check_dates(B, ctx)
    from . import numbers_extras as NX
    NX.check_extras(B, ctx)
    hooks = [h for h in ctx.page.hook_names()]
    if not hooks:
        B.info("hooks", "the page carries no data-sr hooks, so every number was looked for by its sentence or its "
               "table heading. That is the weaker test")
    return B.results
