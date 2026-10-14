# -*- coding: utf-8 -*-
"""sr_render.model: reads a ledger once and answers the questions the sections ask.

The ledger already holds every count (sr_contract.finish_ledger wrote them and validate_ledger proved them).
This module only sorts people into the lists the page prints and reads numbers back out. Before anything is
drawn it cross-checks those lists against the ledger's own totals; a mismatch stops the build.
"""
import datetime

import sr_contract as C
from .htmlkit import pd
from .tokens import LIMITS


class ModelError(Exception):
    """The lists the page would print do not agree with the ledger's totals."""

    def __init__(self, problems):
        Exception.__init__(self, "; ".join(problems))
        self.problems = list(problems)


class Model(object):
    ANSWERED = C.ANSWERED_STATUSES

    def __init__(self, d, identity, link=False):
        self.d, self.ID, self.link = d, identity, link
        self.L, self.R, self.T, self.W = d["listing"], d["report"], d["totals"], d["weeks"]
        self.PT, self.TT, self.LT = d["pricing_tally"], d["themes_tally"], d["liked_tally"]
        self.periods = d["price_periods"]
        self.track = self.R.get("tracking") or {}
        self.WS, self.WE = pd(self.R["week_start"]), pd(self.R["week_end"])
        self.contacts = [dict(x) for x in d["contacts"]]         # copies: the ledger itself is never written to
        self.byid = dict((x["id"], x) for x in self.contacts)
        self.offers = list(d.get("offers") or [])
        self.offer_ids = set(o.get("contact_id") for o in self.offers if o.get("contact_id"))
        # link copy: agents with an offer on file are never named, and nobody is shown as weighing one
        self.masked = set(self.offer_ids) if link else set()
        names = set(self.byid[i]["name_short"] for i in self.masked if i in self.byid)
        names |= set(o.get("agent_short") for o in self.offers if o.get("agent_short")) if link else set()
        self.masked_names = sorted(names, key=len, reverse=True)
        self.offer_people = set(C.offer_people_ids(d))
        for x in self.contacts:
            self._prep(x)
        self.direct = [x for x in self.contacts if C.is_counted(x)]
        self.team = [x for x in self.contacts if x["_team"]]
        self.via = [x for x in self.contacts if x["_via"] and not x["_team"]]
        self.cur = next((w for w in self.W if w.get("is_current")), self.W[-1])
        self.prev = next((w for w in self.W if w["n"] == self.cur["n"] - 1), None)
        # the lists under "The details": who is in each (the heading count), and who is shown in full there
        self.lists = dict((k, [x for x in self.contacts if k in (x.get("lists") or [])]) for k in C.LIST_KEYS)
        self.contacted = [x for x in self.direct if x["_last"]]
        self.via_host = [x for x in self.contacted if x["_via_host"]]
        self.not_reached = [x for x in self.direct if x["status"] == "not_yet_contacted"]
        self.awaiting = [x for x in self.direct if x["status"] == "awaiting_reply"]
        self.replied = [x for x in self.direct if x["status"] in self.ANSWERED]
        self.passed = [x for x in self.replied if x["status"] == "passed"]
        self.offered = [x for x in self.replied if x["status"] in ("offer_submitted", "writing_offer")]
        self.open = [x for x in self.replied if x["status"] == "replied"]
        self.tries3 = [x for x in self.awaiting if x["_tries"] >= LIMITS["tries_flag"]]
        self.answered_before = [x for x in self.awaiting if x["_last_in"]]
        self.fed = [x for x in self.direct if C.counted_feedback(x, self.WE)]      # the people the tallies are out of
        self.active = sorted((x for x in self.direct if x["_wk_t"] or x["_wk_comments"]), key=self._active_key)
        self.fresh_leads, self.stale_leads = [], []
        for w in d.get("offer_watch") or []:
            x = self.byid.get(w["contact_id"])
            if x is None:
                continue
            x["_lead"] = w
            (self.fresh_leads if w.get("lead_state") == "live" else self.stale_leads).append(x)
        self.leaners = self.fresh_leads + self.stale_leads
        self.offers_week = [o for o in self.offers if self.WS <= pd(o["date"]) <= self.WE]
        self.offers_before = [o for o in self.offers if o not in self.offers_week]
        self.oh = list(d.get("open_houses") or [])
        self.oh_week = [o for o in self.oh if self.WS <= pd(o["date"]) <= self.WE]
        self.oh_before = [o for o in self.oh if pd(o["date"]) < self.WS]
        units = set(o.get("counted_unit") for o in self.oh if o.get("groups") is not None)
        # traffic is printed in the host's own unit; when hosts counted differently the total says so
        self.oh_unit = list(units)[0] if len(units) == 1 else None
        self.regimes = self._regimes()
        self.online = d.get("online") if (self.T.get("online_views") is not None or self.T.get("online_saves") is not None) else None
        self.online_weekly = bool(self.online) and any(w.get("online_views") is not None for w in self.W)   # a week by week figure exists
        self.nearby = d.get("nearby") or None
        self.after = list((self.R.get("since_week_closed") or {}).get("items") or [])
        if link:
            self.after = [it for it in self.after if not it.get("offer_related") and it.get("kind") != "offer"
                          and it.get("contact_id") not in self.offer_people]
        self.entries = {}               # list key -> [(contact id, 'full' | 'line' | 'pointer')] as printed in this document
        self.checks_run = 0
        self._verify()

    # ---- per contact: lists for display, numbers from the ledger's own followup block
    def _prep(self, x):
        WS, WE = self.WS, self.WE
        f = x.get("followup") or {}
        day = lambda k: pd(f[k]) if f.get(k) else None
        x["_via"] = bool(x.get("represented_by"))
        x["_team"] = bool(x.get("team_side"))
        x["_via_host"] = x.get("reached_through") == "open_house_host"
        x["_t"] = sorted(x.get("touches") or [], key=lambda t: t["date"])
        x["_out"] = [t for t in x["_t"] if C.is_followup(t)]
        x["_out_days"] = sorted(set(pd(t["date"]) for t in x["_out"]))
        x["_reply_days"] = sorted(set(pd(t["date"]) for t in x["_t"] if C.is_reply(t)))
        x["_n_out"], x["_n_rep"] = f.get("outbound_touches") or 0, f.get("replies") or 0
        x["_last"], x["_last_out"], x["_last_in"] = day("last_touch_date"), day("last_outbound_date"), day("last_reply_date")
        x["_tries"] = f.get("tries_since_last_answer") or 0
        x["_since"] = f.get("days_since_last_touch")
        x["_wk_t"] = [t for t in x["_t"] if WS <= pd(t["date"]) <= WE]
        x["_wk_comments"] = [(e["date"], e["text_safe"]) for e in sorted(x.get("feedback_log") or [], key=lambda e: e["date"])
                             if WS <= pd(e["date"]) <= WE and e.get("text_safe")]
        x["_active"] = bool(x.get("active_this_week"))

    def _active_key(self, x):
        """This week's people: those who said something first, most engaged first, then people still waiting."""
        cm = x["_wk_comments"]
        if x["status"] in ("offer_submitted", "writing_offer"):
            rank = 0
        elif x.get("offer_intent") in ("yes", "maybe"):
            rank = 1
        else:
            rank = {"hot": 2, "warm": 2, "cold": 3}.get(x.get("interest"), 4)
        if x["status"] == "passed":
            rank = 5
        return (0 if cm else 1, rank, -(pd(cm[-1][0]).toordinal()) if cm else 0, -len(x["_wk_t"]), x["name_short"])

    def members(self, key):
        """(this week's people, earlier people, people shown in full under an earlier list) of one list.
        This week's people come most engaged first. Earlier people: still waiting first, then no final answer,
        then passed, each with the latest contact first."""
        mine = [x for x in self.lists[key] if x.get("primary_list") == key]
        ptr = [x for x in self.lists[key] if x.get("primary_list") != key]
        now = sorted((x for x in mine if x["_active"]), key=self._active_key)
        rank = {"awaiting_reply": 0, "writing_offer": 1, "offer_submitted": 1, "replied": 2, "passed": 3, "through_agent": 4,
                "not_yet_contacted": 5}
        last = lambda x: -(x["_last"].toordinal() if x["_last"] else 0)
        earlier = sorted((x for x in mine if not x["_active"]), key=lambda x: (rank.get(x["status"], 9), last(x), x["name_short"]))
        return now, earlier, sorted(ptr, key=lambda x: (C.LIST_KEYS.index(x["primary_list"]), x["name_short"]))

    def quiet(self, x):
        """No contact in either direction for more than 30 days, as of the week end."""
        return (x["_since"] or 0) > LIMITS["quiet_days"]

    def wk(self, x, what):
        WS, WE = self.WS, self.WE
        if what == "out":
            return [t for t in x["_out"] if WS <= pd(t["date"]) <= WE]
        if what == "out_days":
            return [d for d in x["_out_days"] if WS <= d <= WE]
        if what == "rep":
            return [d for d in x["_reply_days"] if WS <= d <= WE]
        raise KeyError(what)

    def heard_how(self, x):
        """How someone we heard from this week came to be in touch: 'this_week' (they answered a follow-up we
        made this week), 'earlier' (they answered one from an earlier week) or 'first' (they contacted us before
        we had followed up with them at all)."""
        first = self.wk(x, "rep")[0]
        if any(d <= first for d in self.wk(x, "out_days")):
            return "this_week"
        return "earlier" if any(d < first for d in x["_out_days"]) else "first"

    def events(self, types):
        """(contact, engagement) for every dated engagement of those types among people who are not team side."""
        return [(x, e) for x in self.contacts if not x["_team"] for e in x.get("engagements") or []
                if e["type"] in types and e.get("date")]

    def _regimes(self):
        """Weeks grouped by the list price the ledger gives each week (the price in effect for most of it).
        A week that holds two list prices is noted on its band: r["straddle"] says which days of which week
        sit at the other price and what is dated on them."""
        out = []
        for w in self.W:
            if not out or out[-1]["price"] != w["list_price"]:
                out.append(dict(price=w["list_price"], weeks=[]))
            out[-1]["weeks"].append(w)
        hist = self.L.get("price_history") or []
        one = datetime.timedelta(days=1)
        for i, r in enumerate(out):
            r["n"] = len(r["weeks"])
            h = next((e for e in hist if e["price"] == r["price"]), None)
            r["change_date"] = h["date"] if (h and i > 0) else None
            r["until"] = None
            r.setdefault("straddle", None)
            if not (i > 0 and r["change_date"]):
                continue
            prev = out[i - 1]
            prev["until"] = r["change_date"]
            cd, last, first = pd(r["change_date"]), prev["weeks"][-1], r["weeks"][0]
            if pd(last["start"]) < cd <= pd(last["end"]):
                # the change fell inside the last week of the earlier band: that week holds days at the new price
                self._straddle(prev, last, cd, pd(last["end"]), r["price"], forward=True)
            elif pd(first["start"]) < cd <= pd(first["end"]):
                # the change fell inside the first week of the new band: that week holds days at the old price
                self._straddle(r, first, max(pd(first["start"]), pd(self.L["list_date"])), cd - one, prev["price"], forward=False)
        return out

    def _straddle(self, band, week, a, b, price, forward):
        inr = lambda day: a <= pd(day) <= b
        ses = [o for o in self.oh if inr(o["date"])]
        band["straddle"] = dict(
            week=week["n"], a=a, b=b, price=price, forward=forward,
            keybox=len([1 for _, e in self.events(("keybox_showing",)) if inr(e["date"])]),
            tours=len([1 for _, e in self.events(("agent_reported_tour",)) if inr(e["date"])]),
            oh_groups=sum(o.get("groups") or 0 for o in ses),
            offers=len([1 for o in self.offers if inr(o["date"])]))

    def price_on(self, day):
        return C.price_on(self.L["price_history"], day)

    def week_of(self, day):
        day = pd(day)
        return next((w for w in self.W if pd(w["start"]) <= day <= pd(w["end"])), None)

    def val(self, key, where=None):
        """A count from the totals (or from one week or period). None means the ledger says 'not recorded'."""
        return (self.T if where is None else where).get(key)

    # ---- the lists above must agree with the ledger's totals, or the build stops
    def _verify(self):
        T, PT, cur = self.T, self.PT, self.cur
        chk = [
            ("people we follow up with", len(self.direct), T["contacts"]),
            ("contacted", len(self.contacted), T["contacted"]),
            ("answered", len(self.replied), T["replied"]),
            ("still waiting", len(self.awaiting), T["awaiting_reply"]),
            ("not yet reached", len(self.not_reached), T["not_yet_contacted"]),
            ("answered splits into passed, open and offer", len(self.passed) + len(self.open) + len(self.offered), len(self.replied)),
            ("waiting after 3 or more tries", len(self.tries3), T["awaiting_reply_3plus_attempts"]),
            ("follow-ups since launch", sum(x["_n_out"] for x in self.direct), T["touches_outbound"]),
            ("follow-ups on the rows", sum(len(x["_out"]) for x in self.direct), T["touches_outbound"]),
            ("replies since launch", sum(x["_n_rep"] for x in self.direct), T["replies_inbound"]),
            ("follow-ups this week", sum(len(self.wk(x, "out")) for x in self.direct), cur["touches_outbound"]),
            ("people followed up this week", len([x for x in self.direct if self.wk(x, "out")]), cur["outbound_people"]),
            ("replies this week", sum(len(self.wk(x, "rep")) for x in self.direct), cur["replies_inbound"]),
            ("people with feedback", len(self.fed), PT["people_with_feedback"]),
            ("the three price rows", PT["too_high"] + PT["fair_or_positive"] + PT["not_raised"], PT["people_with_feedback"]),
            ("themes are out of the same people", self.TT["people_with_feedback"], PT["people_with_feedback"]),
            ("liked points are out of the same people", self.LT["people_with_feedback"], PT["people_with_feedback"]),
            ("offers", len(self.offers), T["offers"]),
            ("offers by list price", sum(p["offers"] for p in self.periods), T["offers"]),
            ("days at each list price", sum(p["days"] for p in self.periods), (self.WE - pd(self.periods[0]["start"])).days + 1),
            ("open house sessions", len(self.oh), T["open_house_sessions"]),
            ("team-side people", len(self.team), T["team_side_set_aside"]["people"]),
            ("showings are key-box showings plus reported tours", T["showings"], (T.get("keybox_showings") or 0) + T["agent_reported_tours"]),
            ("showings this week", cur["showings"], (cur.get("keybox_showings") or 0) + cur["agent_reported_tours"]),
            ("people on the disclosure package list", len(self.lists["disclosure"]), T["disclosure_contacts"]),
            ("everyone we follow up with has one list to be shown in",
             len([x for x in self.direct if x.get("primary_list") in C.LIST_KEYS]), T["contacts"]),
        ]
        for k in C.LIST_KEYS:
            chk.append(("list heading, " + k, len(self.lists[k]), T["lists"][k]))
            chk.append(("this week's people, " + k, len([x for x in self.lists[k] if x.get("primary_list") == k and x["_active"]]),
                        T["lists_active_this_week"][k]))
        for k, lab in (("too_high", "said too high"), ("fair_or_positive", "said fair or good"), ("not_raised", "did not bring up price")):
            chk.append(("price row, " + lab, len([x for x in self.fed if x.get("price_reaction") == k]), PT[k]))
        for i, r in enumerate(self.regimes):
            sd = r["straddle"]
            if sd and sd["forward"] and i + 1 < len(self.regimes):
                # what the price-change week holds at the new price, plus the whole weeks after it, is that price's record
                nxt = self.regimes[i + 1]
                p = next((p for p in self.periods if p["price"] == nxt["price"] and p["start"] == nxt["change_date"]), None)
                if p is not None and nxt is self.regimes[-1]:
                    chk.append(("tours at %s" % nxt["price"], sd["tours"] + sum(w["agent_reported_tours"] for w in nxt["weeks"]), p["agent_reported_tours"]))
                    chk.append(("offers at %s" % nxt["price"], sd["offers"] + sum(w["offers"] for w in nxt["weeks"]), p["offers"]))
        bad = ["%s: the page would print %s, the ledger says %s" % (name, got, want) for name, got, want in chk if got != want]
        # separate days are calendar dates, so they can never pass the 7 days of a week or the days on the market
        if (cur.get("outbound_distinct_days") or 0) > 7:
            bad.append("follow-up days this week (%d) exceed 7" % cur["outbound_distinct_days"])
        if bad:
            raise ModelError(bad)
        self.checks_run = len(chk) + 1
