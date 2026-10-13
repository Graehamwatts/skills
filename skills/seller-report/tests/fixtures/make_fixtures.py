# -*- coding: utf-8 -*-
"""Regenerates the two synthetic ledgers the tests use.

    python make_fixtures.py

Writes ledger_small.json and ledger_busy.json next to this file. Every name, brokerage, address, date and
comment in them is invented. Nothing here comes from a real listing, and nothing real may be added.

  small: 5 people, 5 weeks, nobody mentions price, market and marketing sections present.
  busy:  98 contact records, 11 weeks, 3 offers, a price change, open house hosts on both sides of the
         table, a phone number that is out of service, quiet people, softened comments.

The generator is deterministic (fixed seed), so a rerun gives the same bytes.
"""
import datetime
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "scripts")))
import sr_contract as C  # noqa: E402


def T(date, channel, direction, outcome, summary, quality="exact"):
    return {"date": date, "date_quality": quality, "channel": channel, "direction": direction, "outcome": outcome,
            "summary_safe": summary}


def VM(d): return T(d, "voicemail", "outbound", "left_voicemail", "Called, no answer. Left a voicemail.")
def NA(d): return T(d, "call", "outbound", "no_answer", "Called, no answer.")
def DEAD(d): return T(d, "call", "outbound", "did_not_connect", "Called. The call did not connect.")
def TX(d): return T(d, "text", "outbound", "sent", "Sent a text.")
def EM(d): return T(d, "email", "outbound", "sent", "Sent an email.")
def REACH(d, s): return T(d, "call", "outbound", "reached", s)
def IN(d, s, ch="unknown"): return T(d, ch, "inbound", "replied", s)


def E(kind, date, quality=None, **extra):
    e = {"type": kind, "date": date, "date_quality": quality or ("exact" if date else "missing"), "confirmed": True}
    e.update(extra)
    return e


def FB(date, text, price="not_raised", themes=(), liked=(), softened=False, asked=None, source="conversation", counts=True):
    return {"date": date, "text_safe": text, "softened": softened, "source": source, "counts_as_conversation": counts,
            "price_reaction": price, "price_asked": asked, "themes": list(themes), "liked": list(liked)}


def OH(date, host, groups, recap, unit="groups", source=None, requests=None, host_id=None, time_text=None):
    return {"date": date, "date_quality": "exact", "host": host, "host_contact_id": host_id, "time_text": time_text,
            "groups": groups, "counted_unit": unit,
            "groups_source": source or ("not_recorded" if groups is None else "parsed_from_prose"),
            "recap_safe": recap, "softened": False, "disclosure_requests": requests}


def save(name, d):
    problems = C.validate_ledger(d)
    if problems:
        raise SystemExit("%s does not satisfy the contract:\n  %s" % (name, "\n  ".join(problems[:40])))
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("%s: %d contact records, %d weeks, clean" % (name, len(d["contacts"]), len(d["weeks"])))


# ------------------------------------------------------------------------------------------------
# small
# ------------------------------------------------------------------------------------------------
def build_small():
    d = C.blank_ledger("sample-glen")
    d["meta"].update(built_at="2026-04-13", synthetic=True, note="Synthetic test data. Every name and comment is invented.")
    d["listing"].update(
        address="218 Sample Glen Ct", city="Fixture City", state="CA", zip="94000", beds=3, baths=2.0, sqft=1480,
        property_type="Single Family", list_date="2026-03-12", list_price=1195000,
        price_history=[{"date": "2026-03-12", "price": 1195000, "event": "listed"}],
        status="Active", mls="ML00000218", hero_photo=None, seller_first_names=["Pat", "Sam"])
    d["report"].update(
        issue_number=5, report_date="2026-04-13", week_start="2026-04-06", week_end="2026-04-12",
        tracking={"keybox_showings": True, "disclosure_sent": True, "disclosure_opened": True},
        since_week_closed={"through": "2026-04-13", "items": [
            {"date": "2026-04-13", "kind": "touch", "contact_id": "c003", "name_short": "Wilhelmina R.",
             "summary_safe": "Sent a text on Monday morning. No answer yet."}]})

    a = C.blank_contact("c001", "Odalys V.", "agent", "Harborlight Realty")
    a["engagements"] = [E("keybox_showing", "2026-03-14", time_text="2 to 3 PM"), E("disclosure_link_sent", "2026-03-16"),
                        E("disclosure_opened", "2026-03-17")]
    a["touches"] = [
        REACH("2026-03-15", "Asked for feedback the day after the showing. Her clients liked the layout."),
        EM("2026-03-16"), TX("2026-03-24"),
        IN("2026-03-25", "Replied by text. Her clients are still thinking it over.", "text"),
        VM("2026-04-07"), TX("2026-04-07"),
        IN("2026-04-08", "Called back. Her clients liked the yard and are comparing the home with one other.", "call")]
    a["feedback_log"] = [
        FB("2026-03-15", "Her clients liked the layout and the home overall.", liked=("home_overall", "layout_space")),
        FB("2026-03-25", "Her clients are still thinking it over.", themes=("still_deciding",)),
        FB("2026-04-08", "Her clients liked the yard and are comparing the home with one other.",
           themes=("still_deciding",), liked=("outdoor_space",))]
    a["feedback_safe"] = "Her clients liked the layout and the yard. They are comparing the home with one other."
    a.update(interest="warm", offer_intent="maybe", next_followup_date="2026-04-15",
             offer_basis_safe="Comparing the home with one other.", offer_basis_date="2026-04-08")

    b = C.blank_contact("c002", "Thaddeus K.", "agent", "Northgate Homes")
    b["engagements"] = [E("agent_reported_tour", "2026-03-21", "approximate", date_label="week of Mar 16")]
    b["touches"] = [VM("2026-03-23"), TX("2026-03-23"),
                    REACH("2026-03-26", "Reached him by phone. His clients chose another property closer to work.")]
    b["feedback_log"] = [FB("2026-03-26", "His clients chose another property closer to work.",
                            themes=("location", "chose_another_home"))]
    b.update(interest="passed", offer_intent="no", status="passed")

    c = C.blank_contact("c003", "Wilhelmina R.", "agent", None)
    c["engagements"] = [E("disclosure_link_sent", "2026-03-30"), E("disclosure_opened", "2026-03-31")]
    c["touches"] = [EM("2026-03-30"), VM("2026-04-02"), TX("2026-04-02"), VM("2026-04-09"), EM("2026-04-09")]
    c["touches"][0]["summary_safe"] = "Sent the disclosure package link."

    v = C.blank_contact("c004", "Open house visitor, Mar 28", "open_house_visitor", None)
    v.update(name_recorded=False, reached_through="open_house_host", interest="warm")
    v["engagements"] = [E("open_house_visit", "2026-03-28"), E("disclosure_link_sent", "2026-03-29", "approximate")]
    v["touches"] = [T("2026-03-29", "unknown", "outbound", "sent",
                      "Sent the disclosure package to the open house host to pass along.", "approximate")]
    v["feedback_log"] = [FB("2026-03-28", "The host described this visitor as interested. He asked for the disclosure package.",
                            price="unknown", source="open_house_host", counts=False)]

    e = C.blank_contact("c005", "Casimir D.", "agent", "Bluewater Brokers")
    e["engagements"] = [E("inquiry", "2026-04-09")]
    e["touches"] = [IN("2026-04-09", "Called to ask about the HOA dues and the open house times. We answered on the call.", "call")]

    f = C.blank_contact("c006", "Client of Wilhelmina R.", "buyer", None)
    f.update(name_recorded=False, represented_by="c003")
    f["engagements"] = [E("disclosure_shared_by_agent", None)]

    h = C.blank_contact("c007", "Leocadia M.", "agent", "Harborlight Realty")
    h.update(is_open_house_host=True, team_side=True)
    h["touches"] = [TX("2026-03-29"), IN("2026-03-29", "Sent her recap of the weekend.", "text")]
    h["touches"][0]["summary_safe"] = "Asked for a recap of the open house."

    d["contacts"] = [a, b, c, v, e, f, h]
    d["open_houses"] = [
        OH("2026-03-14", "Leocadia M.", 6, "6 groups came through. Two asked about the school boundary.", host_id="c007", time_text="1 to 4 PM"),
        OH("2026-03-15", "Leocadia M.", None, None, host_id="c007"),
        OH("2026-03-28", "Leocadia M.", 3, "3 groups. One visitor with no agent asked for the disclosure package.", requests=1, host_id="c007"),
        OH("2026-04-11", "Leocadia M.", 0, "No visitors.", source="sheet_column", host_id="c007")]
    d["team_side"] = [{"name_short": "Leocadia M.", "role": "open house host", "sessions_hosted": 4, "contact_id": "c007"}]
    days = [9, 14, 21, 30, 44]
    sales = [{"address": "%d Sample Glen Ct" % (200 + i), "sold_date": "2026-0%d-1%d" % (1 + i % 3, i), "sold_price": 1100000 + 25000 * i,
              "sqft": 1400 + 20 * i, "beds_baths": "3/2", "list_date": "2025-1%d-0%d" % (i % 3, i + 1), "list_price": 1090000 + 30000 * i,
              "contract_date": "2026-01-0%d" % (i + 1), "days_to_contract": n, "used_in_average": True} for i, n in enumerate(days)]
    sales.append({"address": "240 Sample Glen Ct", "sold_date": "2026-02-20", "sold_price": 1180000, "sqft": 1500, "beds_baths": "3/2",
                  "list_date": "2026-02-20", "list_price": 1180000, "contract_date": None, "days_to_contract": None, "used_in_average": False})
    d["market"] = {
        "as_of": "2026-04-13", "data_through": "2026-04-12", "refreshed_for_this_issue": True,
        "scope": "Fixture City single family homes that closed in the last six months",
        "source": "Synthetic sales invented for the test fixture.",
        "method": "Days are counted from the list date to the day the listing first went under contract.",
        "sample": {"closed": 6, "used": 5, "excluded": 1, "exclusion_reason": "One sale was listed and closed on the same day."},
        "days_to_contract": {"average": 24, "median": 21, "shortest": 9, "longest": 44, "values_sorted": days, "over_90_days": 0},
        "subject_on_report_date": {"date": "2026-04-13", "days_on_market": 32, "sales_under_contract_by_that_day": 4, "of_sales": 5},
        "sales": sales,
        "statement_safe": "Apr 13 is day 32. 4 of the 5 comparable sales were under contract by that point."}
    d["marketing"] = {"as_of": "2026-04-13", "note": "Checked for this issue.", "channels": [
        {"channel": "MLS and home search sites", "status": "on", "checked": "2026-04-13", "detail": "On the MLS since Mar 12."},
        {"channel": "Open houses", "status": "on", "checked": "2026-04-13", "detail": "Four sessions held. The next is not scheduled yet."},
        {"channel": "Facebook and Instagram ads", "status": "on", "checked": "2026-04-02", "detail": "Two ads were running at the last check."},
        {"channel": "YouTube ads", "status": "prepared", "checked": "2026-04-02", "detail": "The video is uploaded. Nothing has launched."}]}
    d["next_week"] = ["Keep trying Wilhelmina R. She has been followed up on three days since Mar 30 with no answer yet.",
                      "Check back with Odalys V. on Wednesday, Apr 15.",
                      "Ask the open house host where the Mar 28 visitor stands."]
    d["sources_used"] = [{"kind": "activity_sheet_live", "label": "Activity sheet (synthetic)", "as_of": "2026-04-13"},
                         {"kind": "market_data", "label": "Comparable sales (synthetic)", "as_of": "2026-04-13"}]
    d["data_quality"] = ["Synthetic fixture. The Mar 15 open house has no visitor count.",
                         "Thaddeus K. gave no exact tour day. It is placed in the week of Mar 16 and marked approximate."]
    return C.finish_ledger(d)


# ------------------------------------------------------------------------------------------------
# busy
# ------------------------------------------------------------------------------------------------
FIRST = ("Alder Brisa Corwin Delphine Emrys Fenella Garrick Hespera Ignatius Jessamy Kestrel Leocadia Merrick Nerys Osric "
         "Perpetua Quillon Rosalind Sorrel Tamsin Ulric Verity Wystan Xanthe Yarrow Zephyrine Ambrose Blythe Caspian Dorothea "
         "Evander Florian Greer Hollis Isolde Jorah Kerensa Lucan Maris Niall Ottilie Piers Quenby Rafferty Sunniva Tobiah "
         "Undine Valerian Winsome Xavian Ysolde Zebedee Araminta Barnaby Clemency Dashiell Elowen Fitzroy Gwendolen Horatio "
         "Imogen Jericho Katya Lysander Marigold Nicodemus Ophira Peregrine Rowena Septimus Thisbe").split()
BROKERS = ("Harborlight Realty", "Northgate Homes", "Bluewater Brokers", "Tallgrass Real Estate", "Cedar and Vine Properties", None)
CONCERNS = {
    "location": "The clients wanted a quieter street.",
    "size_layout": "The clients need a larger main bedroom.",
    "floor_level": "The clients would rather not have bedrooms on two levels.",
    "stairs": "The stairs were a concern for the clients.",
    "parking": "The clients wanted a second parking space.",
    "yard_outdoor": "The clients wanted a larger yard.",
    "hoa": "The clients had questions about the HOA dues.",
    "condition_disclosures": "Some items in the disclosures gave the clients pause.",
    "staging": "The clients had trouble picturing their furniture in the living room.",
    "buyer_timing": "The clients decided to wait a few months before buying.",
    "chose_another_home": "The clients chose another property.",
    "no_reason": "The client is not interested and gave no reason.",
}
LIKES = {"home_overall": "They liked the home overall.", "layout_space": "They liked the layout.",
         "condition_updates": "They liked the updated kitchen.", "light_views": "They liked the light.",
         "outdoor_space": "They liked the patio.", "location": "They liked the location."}
LIST, WEEK_START, WEEK_END, REPORT = "2026-01-08", "2026-03-16", "2026-03-22", "2026-03-23"
LAST = 73          # day offset of the week end from the list date


def day(n):
    return (C.parse_date(LIST) + datetime.timedelta(days=n)).isoformat()


def followups(rng, days, dead=False):
    out = []
    for n in days:
        combo = rng.choice([(VM, TX), (VM, TX, EM), (NA, TX), (EM,), (TX,), (VM,)])
        for mk in combo:
            out.append(DEAD(day(n)) if (dead and mk in (VM, NA)) else mk(day(n)))
    return out


def build_busy():
    rng = random.Random(20261013)
    d = C.blank_ledger("sample-orchard")
    d["meta"].update(built_at=REPORT, synthetic=True, note="Synthetic test data. Every name and comment is invented.")
    d["listing"].update(
        address="77 Sample Orchard Ln", city="Fixture City", state="CA", zip="94000", beds=4, baths=2.5, sqft=2140,
        property_type="Single Family", list_date=LIST, list_price=1098000,
        price_history=[{"date": LIST, "price": 1150000, "event": "listed"},
                       {"date": "2026-02-07", "price": 1098000, "event": "price_change"}],
        status="Active", mls="ML00000077", hero_photo=None)
    d["report"].update(
        issue_number=11, report_date=REPORT, week_start=WEEK_START, week_end=WEEK_END,
        tracking={"keybox_showings": True, "disclosure_sent": False, "disclosure_opened": False},
        since_week_closed={"through": REPORT, "items": []})

    names, used = [], set()
    for i, first in enumerate(FIRST):
        label = "%s %s." % (first, "ABCDEFGHJKLMNPRSTVWY"[(i * 7) % 20])
        if label not in used:
            used.add(label)
            names.append(label)
    people = []

    def person(kind="agent"):
        c = C.blank_contact("c%03d" % (len(people) + 1), names[len(people)], kind, rng.choice(BROKERS) if kind == "agent" else None)
        people.append(c)
        return c

    def engage(c, n, i):
        kind = ("keybox_showing", "agent_reported_tour", "disclosure_on_list", "agent_reported_tour", "inquiry")[i % 5]
        if kind == "agent_reported_tour" and i % 4 == 1:
            c["engagements"].append(E(kind, day(n), "approximate"))
        elif kind == "disclosure_on_list" and i % 6 == 2:
            c["engagements"].append(E(kind, None))
        else:
            c["engagements"].append(E(kind, day(n)))
        if kind in C.TOUR_TYPES and i % 3 == 0:
            c["engagements"].append(E("disclosure_on_list", day(min(LAST, n + 1)), "approximate"))

    def answer(c, n, text, **fb):
        """They answered on day n: a reached call or a message back, with a feedback entry."""
        if rng.random() < 0.4:
            c["touches"].append(REACH(day(n), "Reached by phone. " + text))
        else:
            c["touches"].append(IN(day(n), text, rng.choice(["unknown", "text", "call", "email"])))
        c["feedback_log"].append(FB(day(n), text, **fb))

    concern_keys = [k for k in C.THEME_KEYS if k in CONCERNS]
    # 3 offers, all written against the first list price
    for i, (n, price, state) in enumerate(((19, 1120000, "countered"), (20, 1105000, "countered"), (24, 1150000, "received"))):
        c = person()
        c["brokerage"] = BROKERS[i]
        c["engagements"].append(E("keybox_showing", day(n - 6)))
        c["touches"] += followups(rng, [n - 5])
        answer(c, n - 4, "The clients liked the home and planned to write an offer.", liked=("home_overall",))
        c["touches"].append(IN(day(n), "Sent an offer.", "email"))
        c.update(interest="hot", offer_intent="yes", status="offer_submitted")
        d["offers"].append({"id": "o%d" % (i + 1), "date": day(n), "contact_id": c["id"], "agent_short": c["name_short"],
                            "brokerage": c["brokerage"], "price": price, "pct_of_list": round(100.0 * price / 1150000, 1),
                            "terms_summary": "Conventional loan, 20% down, 21 day close.", "state": state, "note_safe": None})
    # 2 offer leads: one fresh, one that has gone 21 days without contact
    for n, text in ((LAST - 5, "The clients are interested and are talking about an offer."),
                    (LAST - 40, "The clients said an offer was possible after a second look.")):
        c = person()
        c["engagements"].append(E("keybox_showing", day(n - 3)))
        c["touches"] += followups(rng, [n - 2])
        answer(c, n, text, themes=("still_deciding",), liked=("home_overall",))
        c.update(interest="warm", offer_intent="maybe", offer_basis_safe=text, offer_basis_date=day(n))
    # 32 people who passed. 7 said the price is too high (softened), 3 said it is fair.
    for i in range(32):
        c = person()
        n = (6 + i * 2) if i < 27 else (60 + (i - 27))          # the last five pass during the report week
        engage(c, n, i)
        k = rng.choice([1, 1, 2, 3])
        tries = [n + 1 + 3 * j for j in range(k)]
        c["touches"] += followups(rng, tries)
        when = min(LAST, tries[-1] + rng.choice([1, 2, 3]))
        themes = rng.sample(concern_keys, rng.choice([1, 1, 2]))
        if len(themes) > 1 and "no_reason" in themes:
            themes.remove("no_reason")              # "no reason given" never sits beside a reason
        text = " ".join(CONCERNS[t] for t in themes)
        fb = dict(themes=themes)
        if i < 7:
            fb.update(price="too_high", softened=True, asked=True)
            text = "Gave negative feedback and specifically said the price is too high. " + text
        elif i < 10:
            fb.update(price="fair_or_positive", asked=True, liked=("value",))
            text = "Said the price looks fair for the area. " + text
        elif i % 4 == 0:
            fb.update(liked=(rng.choice(sorted(LIKES)),))
            text = LIKES[fb["liked"][0]] + " " + text
        if i == 11:
            fb["themes"] = list(themes) + ["other"]
            c["theme_other"] = "Street noise"
            text += " Street noise came up as well."
        answer(c, when, text, **fb)
        c.update(interest="passed", offer_intent="no", status="passed")
    # 13 people who answered and have not given a final answer. The early ones have gone quiet.
    for i in range(13):
        c = person("buyer" if i % 5 == 4 else "agent")
        n = 5 + i * 5
        engage(c, n, i + 1)
        c["touches"] += followups(rng, [n + 1])
        liked = (sorted(LIKES)[i % len(LIKES)],)
        answer(c, min(LAST, n + 2), LIKES[liked[0]] + " No decision yet.", liked=liked, themes=("still_deciding",) if i % 2 else ())
        c.update(interest="warm" if i % 3 else "cold", next_followup_date=day(LAST + 3) if i > 10 else None)
    # 11 people still waiting. The first one has a phone number that is out of service.
    for i in range(11):
        c = person()
        n = (10 + i * 6) if i < 8 else (LAST - 9 + i - 8)
        engage(c, n, i + 2)
        if i == 0:
            c["phone_out_of_service"] = True
            c["touches"] += followups(rng, [n + 1, n + 4, n + 8, n + 15], dead=True)
        elif i % 3 == 1:
            answer(c, n + 1, "Said the clients would talk it over and get back to us.")
            c["touches"] += followups(rng, [n + 4, n + 9][: 1 + i % 2])
        else:
            c["touches"] += followups(rng, [min(LAST, n + 1 + 3 * j) for j in range(1 + i % 4)])
    # 2 people nobody has reached yet, and 1 caller whose name was not written down
    for i in range(2):
        c = person("buyer")
        c["engagements"].append(E("disclosure_on_list", None))
    c = C.blank_contact("c%03d" % (len(people) + 1), "Agent, name not recorded", "agent", None)
    names.insert(len(people), None)
    people.append(c)
    c["name_recorded"] = False
    c["engagements"].append(E("inquiry", day(52)))
    c["touches"].append(T(day(52), "call", "unknown", "reached", "Spoke by phone. The client chose another property before touring."))
    c["feedback_log"].append(FB(day(52), "The client chose another property before touring.", themes=("chose_another_home",)))
    c.update(interest="passed", offer_intent="no", status="passed")
    # 2 open house visitors who left their names
    for i in range(2):
        c = person("open_house_visitor")
        c["engagements"] += [E("open_house_visit", day(16 + 7 * i)), E("disclosure_on_list", day(17 + 7 * i), "approximate")]
        c["touches"] += followups(rng, [17 + 7 * i, 21 + 7 * i])
        if i == 0:
            answer(c, 23, "Liked the home and is waiting on a loan approval.", themes=("buyer_timing",), liked=("home_overall",))
            c["interest"] = "cold"
    direct = list(people)
    # 5 open house hosts: 3 on our side of the table, 2 who also brought a buyer of their own
    hosts = []
    for i in range(5):
        c = person()
        c["is_open_house_host"] = True
        hosts.append(c)
        if i < 3:
            c["team_side"] = True
            c["touches"].append(T(day(10 + 7 * i), "text", "outbound", "sent", "Asked for a recap of the open house."))
            if i == 0:
                c["touches"].append(IN(day(11), "Sent a recap of the weekend.", "text"))
        else:
            n = 30 + 7 * i
            c["engagements"].append(E("agent_reported_tour", day(n)))
            c["touches"] += followups(rng, [n + 1])
            answer(c, n + 2, CONCERNS["size_layout"], themes=("size_layout",))
            c.update(interest="passed", offer_intent="no", status="passed")
    # 27 buyers an agent shared the disclosure package with
    for i in range(27):
        agent = direct[(i * 3) % 40]
        c = C.blank_contact("c%03d" % (len(people) + 1), "Client %d of %s" % (i + 1, agent["name_short"]), "buyer", None)
        people.append(c)
        c.update(name_recorded=False, represented_by=agent["id"])
        c["engagements"].append(E("disclosure_shared_by_agent", None))
    for c in people:
        c["touches"].sort(key=lambda t: t["date"])
        c["touches"] = [t for t in c["touches"] if t["date"] <= WEEK_END]
    d["contacts"] = people

    host_names = [h["name_short"] for h in hosts]
    for wk in range(10):
        sat = 2 + 7 * wk
        h = hosts[wk % 5]
        groups = [9, 7, None, 5, 4, 3, None, 2, 0, 1][wk]
        recap = None if groups is None else ("No visitors." if groups == 0 else "%d groups came through." % groups)
        d["open_houses"].append(OH(day(sat), h["name_short"], groups, recap, host_id=h["id"], requests=1 if wk in (0, 3) else None))
        if wk in (0, 1, 4):
            d["open_houses"].append(OH(day(sat + 1), hosts[(wk + 1) % 5]["name_short"], [6, 4, 0, 0, 2][wk],
                                       "%d groups came through." % [6, 4, 0, 0, 2][wk], host_id=hosts[(wk + 1) % 5]["id"]))
    d["team_side"] = [{"name_short": h["name_short"], "role": "open house host", "contact_id": h["id"],
                       "sessions_hosted": len([o for o in d["open_houses"] if o["host_contact_id"] == h["id"]])} for h in hosts[:3]]
    d["pricing_tally"]["open_house_price_remarks"] = [
        {"date": day(30), "reaction": "raised_no_verdict", "remark_safe": "One open house group asked why the price had changed.", "softened": False},
        {"date": day(37), "reaction": "too_high", "remark_safe": "One open house group felt the price was above similar homes nearby.", "softened": True}]
    d["report"]["since_week_closed"]["items"] = [
        {"date": REPORT, "kind": "touch", "contact_id": direct[5]["id"], "name_short": direct[5]["name_short"],
         "summary_safe": "Called on Monday for an update. No decision yet."},
        {"date": REPORT, "kind": "note", "contact_id": None, "name_short": None,
         "summary_safe": "One new showing request came in on Monday. It will be counted next week."}]
    d["next_week"] = ["Keep trying the people who have not answered yet.",
                      "Check back with the buyers who toured during the week of Mar 16.",
                      "Hold the next open house on Saturday, Mar 28."]
    d["sources_used"] = [{"kind": "activity_sheet_live", "label": "Activity sheet (synthetic)", "as_of": REPORT},
                         {"kind": "offer_summary", "label": "Offer summary (synthetic)", "as_of": REPORT}]
    d["data_quality"] = ["Synthetic fixture. Two open house sessions have no visitor count.",
                         "The disclosure tab lists people only. Link sent and package opened are not recorded for this listing.",
                         "Hosts on this listing: %s." % ", ".join(host_names)]
    return C.finish_ledger(d)


if __name__ == "__main__":
    save("ledger_small.json", build_small())
    save("ledger_busy.json", build_busy())
