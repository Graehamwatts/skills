# -*- coding: utf-8 -*-
"""sr_build_people: the people of a ledger, built from raw.json and curation.json.

Used by build_ledger.py. One job: turn every curated person into a ledger contact, as of the end of the
report week, without dropping a note on the way.

    People(listing, raw, cur, week_end, through).build()  ->  contacts (ledger shape)

What it applies, in this order, for each person:
  1. every dated note on the person's rows becomes touches and feedback: from curation when the note is
     read into curation.json, by rule when it is a stock phrase (sr_notes), and a hard stop when it is neither;
  2. the Email / Call / Text date columns fill in touches the notes do not cover;
  3. one follow-up per channel per day, the same attempt typed on two tabs counted once;
  4. engagements: from the tab the row sits on, unless curation says what the row really was;
  5. readings: a sheet column beats Claude's reading, the operator's correction beats both;
  6. the hosts rule, the dead-number flag, and the week-end cutoff (later entries go to since_week_closed).

Nothing here counts totals: sr_contract.finish_ledger does that from the rows this module writes.
Standard library only. No real client data belongs in this file.
"""
import collections
import re

import sr_contract as C
import sr_notes as N

TAG_RANK = {"claude": 0, "sheet_column": 1, "corrected_by_operator": 2}
TAG_STATUSES = ("passed", "writing_offer", "offer_submitted")
OWN_TYPES = C.TOUR_TYPES + C.DISCLOSURE_TYPES + ("inquiry",)
SHEET_TAGS = ("price_reaction", "interest", "offer_intent", "next_followup_date")
NO_NAME = {"agent": "Agent, name not recorded", "buyer": "Buyer, name not recorded", "open_house_visitor": "Open house visitor"}
SINCE_TEXT = {
    "keybox_showing": "A key-box showing was logged.", "agent_reported_tour": "A tour was reported to our team.",
    "inquiry": "An inquiry came in.", "open_house_visit": "Came to an open house.",
    "disclosure_on_list": "Was added to the disclosure package list.",
    "disclosure_link_sent": "The disclosure package link was sent.", "disclosure_opened": "Opened the disclosure package.",
    "disclosure_shared_by_agent": "The disclosure package was shared with a buyer.",
}
_OFFER_WORD = re.compile(r"\boffers?\b", re.I)
_PRIVATE = ("_auto", "_src", "_seq")


def weakest(sources):
    sources = [s for s in sources if s]
    return min(sources, key=lambda s: TAG_RANK.get(s, 0)) if sources else "claude"


def public(d):
    return dict((k, v) for k, v in d.items() if not k.startswith("_"))


class People(object):
    def __init__(self, listing, raw, cur, week_end, through):
        self.listing, self.raw, self.cur = listing, raw, cur
        self.we, self.through = C.iso(week_end), C.iso(through)
        self.tour_type = "keybox_showing" if (listing.get("tracking") or {}).get("keybox_showings") else "agent_reported_tour"
        self.rows, self.kind = {}, {}
        for t in raw.get("tabs") or []:
            for r in t["rows"]:
                self.rows[r["key"]] = r
                self.kind[r["key"]] = t["kind"]
        self.problems = []                     # hard stops: the build writes nothing while this list has items
        self.notes = []                        # plain build notes (ledger.data_quality). Never printed to a seller
        self.unsure = []                       # what Claude flagged as unsure while reading the notes: (who, sentence)
        self.provenance = {}                   # person id -> {field: where the value came from}. Never leaves the build
        self.since = []                        # entries after the week closed (report.since_week_closed.items)
        self.stats = collections.Counter()
        self.auto_inquiries = []               # showing rows with no showing date, read as inquiries by default
        self.used_entries = set()
        self.held = {}                         # row key -> person id

    # ----------------------------------------------------------------------------------------- helpers
    def entry_date(self, e):
        fix = (self.cur.get("date_corrections") or {}).get(e["key"])
        if fix:
            return fix["date"], fix.get("date_quality") or "approximate"
        return e.get("date"), "exact"

    def trusted_date(self, e):
        """False for a date the parser could not place inside the listing's life (and nobody has corrected).
        Such a note is still read, but it never dates a tour, an inquiry or a place on the disclosure list."""
        return e.get("year_rule") != "outside_listing_life" or e["key"] in (self.cur.get("date_corrections") or {})

    def sheet_tags(self, rows):
        """{tag: value} from the person's rows. When two rows disagree, the row with the latest note wins."""
        out = {}
        for k in SHEET_TAGS:
            vals = []
            for r in rows:
                v = (r.get("sheet_tags") or {}).get(k)
                if v is not None:
                    vals.append((max([e["date"] or "" for e in r["entries"]] or [""]), v))
            if vals:
                if len(set(v for _, v in vals)) > 1:
                    self.stats["sheet_tag_conflicts"] += 1
                out[k] = sorted(vals)[-1][1]
        return out

    def effective_tag(self, p, key, sheet):
        """(value, provenance) for one reading: a sheet column beats Claude's reading, the operator's correction
        beats both. A correction gives way only when the sheet value has changed since it was made."""
        tag = (p.get("tags") or {}).get(key)
        sv = sheet.get(key)
        if tag and tag.get("provenance") == "corrected_by_operator":
            if sv is not None and sv != tag.get("value") and sv != tag.get("sheet_value_seen"):
                self.stats["corrections_replaced_by_newer_sheet_value"] += 1
                return sv, "sheet_column"
            return tag.get("value"), "corrected_by_operator"
        if sv is not None:
            return sv, "sheet_column"
        if tag:
            return tag.get("value"), tag.get("provenance") or "claude"
        return None, None

    # ----------------------------------------------------------------------------------------- one person
    def build(self):
        people = self.cur.get("people") or {}
        for cid in sorted(people):
            for k in people[cid].get("rows") or []:
                if k in self.held:
                    self.problems.append("row %s is held by both %s and %s" % (k, self.held[k], cid))
                self.held[k] = cid
        self.wards = {}                        # agent id -> the buyers reached through that agent
        for cid in sorted(people):
            if people[cid].get("represented_by"):
                self.wards.setdefault(people[cid]["represented_by"], []).append(cid)
        built = collections.OrderedDict()
        for cid in sorted(people):
            c = self.contact(cid, people[cid])
            if c is not None:
                built[cid] = c
        for cid, c in list(built.items()):                     # a buyer goes where their agent goes
            rb = c.get("represented_by")
            if rb is None:
                continue
            if rb not in people:
                self.problems.append("%s.represented_by: %s is not a person in curation.json" % (cid, rb))
            elif rb not in built:
                self.stats["people_first_seen_after_week_end"] += 1
                del built[cid]
        for item in self.since:
            if item.get("contact_id") not in built:
                item["contact_id"] = None
        return list(built.values())

    def contact(self, cid, p):
        we, kind = self.we, p.get("kind") or "agent"
        rows = [self.rows[k] for k in p.get("rows") or [] if k in self.rows]
        self.stats["rows_stale"] += len(p.get("rows") or []) - len(rows)
        is_host = bool(p.get("is_open_house_host"))
        data_rows = [r for r in rows if self.kind[r["key"]] != "open_house" or is_host]
        named = [r for r in data_rows if self.kind[r["key"]] != "open_house"] + ([r for r in rows if self.kind[r["key"]] == "open_house"] if is_host else [])
        raw_name = next((r.get("name_raw") or r.get("buyer_raw") for r in named if r.get("name_raw") or r.get("buyer_raw")), None)
        name = p.get("name_short") or C.short_name(raw_name) or NO_NAME[kind]
        c = C.blank_contact(cid, name, kind, p.get("brokerage"))
        # a label is not a name: "Client of Yang L." (an Invited by row) and "Agent, name not recorded" are labels
        labelled = not p.get("name_short") and bool(C.invited_by(raw_name))
        c["name_recorded"] = bool(p.get("name_recorded", True)) and bool(C.SHORT_NAME.match(name)) and not labelled
        c["is_open_house_host"] = is_host
        c["represented_by"], c["reached_through"] = p.get("represented_by"), p.get("reached_through")

        # Follow-up with a buyer an agent brought is follow-up with that agent: anything logged on the buyer's
        # row is read into the agent's log, and the buyer carries no touches of their own.
        ward_rows = [self.rows[k] for w in self.wards.get(cid, []) for k in (self.cur["people"][w].get("rows") or [])
                     if k in self.rows and self.kind[k] != "open_house"]
        touch_rows = [] if c["represented_by"] else data_rows + ward_rows
        own = set(r["key"] for r in data_rows)
        touches, feedback, later, all_text, dated = [], [], [], [], []
        seq = 0
        for ri, r in enumerate(touch_rows):
            if r["key"] not in own and (r["entries"] or any((r.get("last_touch") or {}).values())):
                self.stats["buyer_rows_read_into_agent_log"] += 1
            for e in r["entries"]:
                seq += 1
                self.used_entries.add(e["key"])
                all_text.append(e["text"])
                got = self.entry(cid, name, r, e, seq)
                if got is None:
                    continue
                date, ts, fb = got
                if r["key"] in own and self.trusted_date(e):
                    dated.append(date)
                else:
                    for t in ts:
                        t["_ward"] = True
                (touches if date <= we else later).extend(ts)
                if fb is not None and date <= we:
                    feedback.append(fb)
                elif fb is not None and not ts:
                    later.append({"date": date, "_feedback": fb})
        extra = p.get("extra") or {}
        for item in (extra.get("touches") or []) + (extra.get("feedback") or []):
            if not item.get("date"):
                self.problems.append("%s (%s): an extra touch or feedback line in curation has no date" % (cid, name))
        for t in [x for x in extra.get("touches") or [] if x.get("date")]:
            if t["date"] <= self.through:
                seq += 1
                (touches if t["date"] <= we else later).append(self.touch(t, t["date"], t.get("date_quality") or "exact", "curated", seq))
        for fb in [x for x in extra.get("feedback") or [] if x.get("date")]:
            if fb["date"] <= we:
                feedback.append(self.feedback(fb, fb["date"], fb.get("provenance") or "claude"))
        touches, dropped = N.settle_day(touches)
        self.stats["touches_deduped"] += dropped
        self.columns(touch_rows, touches, later, seq, own)
        # inside one day: what the columns alone record, then the notes (our attempts), then the feedback (their answer)
        touches.sort(key=lambda t: (t["date"], 0 if t["_src"] == "column" else 1, t.get("_field") == "feedback", t["_seq"]))

        c["phone_out_of_service"] = p.get("phone_out_of_service")
        if c["phone_out_of_service"] is None:
            c["phone_out_of_service"] = any(N.dead_number(x) for x in all_text)
            if c["phone_out_of_service"]:
                self.notes.append("%s: the notes say the number on file is out of service, so the contact is flagged that way." % name)
        c["phone_out_of_service"] = bool(c["phone_out_of_service"])

        engs, engs_later = self.engagements(p, data_rows, touches, dated, is_host, name)
        own = [e for e in engs if e["type"] in OWN_TYPES]
        c["team_side"] = is_host and not own and not c["represented_by"]
        if isinstance(p.get("team_side"), bool) and p["team_side"] != c["team_side"] and is_host:
            self.notes.append("%s: curation says team_side is %s, but a host is team side exactly when they brought no buyer of their own. The rows decide." % (name, str(p["team_side"]).lower()))
        c["engagements"] = engs

        # nothing on record on or before the week end: this person belongs to a later issue
        anything_later = bool(later or engs_later or [d for d in dated if d > we])
        # someone curation already placed with no date (on the package list, date not recorded) has been on record all along
        placed_undated = any(e.get("date") is None for es in (p.get("engagements") or {}).values() for e in es)
        if not touches and not feedback and not [e for e in engs if e.get("date")] and anything_later and not placed_undated:
            self.stats["people_first_seen_after_week_end"] += 1
            if not c["team_side"]:
                self.push_later(cid, name, later, engs_later, p)
            return None
        if not c["team_side"]:
            self.push_later(cid, name, later, engs_later, p)
        else:
            self.stats["team_side_entries_after_week_end"] += len(later)

        c["touches"] = [public(t) for t in touches]
        self.tags(cid, c, p, rows, feedback)
        return c

    def push_later(self, cid, name, later, engs_later, p):
        for t in later:
            if "_feedback" in t:
                self.since.append({"date": t["date"], "kind": "feedback", "contact_id": cid, "name_short": name,
                                   "summary_safe": t["_feedback"]["text_safe"], "offer_related": bool(_OFFER_WORD.search(t["_feedback"]["text_safe"]))})
            else:
                flag = t.get("_offer_related")
                self.since.append({"date": t["date"], "kind": "touch", "contact_id": cid, "name_short": name,
                                   "summary_safe": t["summary_safe"],
                                   "offer_related": bool(_OFFER_WORD.search(t["summary_safe"])) if flag is None else bool(flag)})
        for e in engs_later:
            self.since.append({"date": e["date"], "kind": "engagement", "contact_id": cid, "name_short": name,
                               "summary_safe": SINCE_TEXT[e["type"]], "offer_related": False})

    # ----------------------------------------------------------------------------------------- notes -> touches
    def touch(self, t, date, quality, src, seq, offer_related=None):
        out = {"date": date, "date_quality": t.get("date_quality") or quality, "channel": t.get("channel"),
               "direction": t.get("direction"), "outcome": t.get("outcome"), "summary_safe": t.get("summary_safe"),
               "_auto": src in ("auto", "column"), "_src": src, "_seq": seq, "_offer_related": offer_related}
        for k in ("purpose", "inferred", "note"):
            if t.get(k) not in (None, "", []):
                out[k] = t[k]
        return out

    def feedback(self, fb, date, prov):
        return {"date": date, "text_safe": fb.get("text_safe"), "softened": bool(fb.get("softened")),
                "source": fb.get("source") or "conversation",
                "counts_as_conversation": bool(fb.get("counts_as_conversation", True)),
                "price_reaction": fb.get("price_reaction") or "not_raised", "price_asked": fb.get("price_asked"),
                "themes": list(fb.get("themes") or []), "liked": list(fb.get("liked") or []), "_prov": prov}

    def entry(self, cid, name, row, e, seq):
        """(date, touches, feedback or None) for one note, or None when it is not an event in this issue."""
        cur_e = (self.cur.get("entries") or {}).get(e["key"])
        date, quality = self.entry_date(e)
        where = "%s (%s), %s dated %s" % (cid, name, "feedback" if e["field"] == "feedback" else "note", e.get("date_raw") or "with no date")
        if date is None:
            if cur_e is None and not N.is_label(e["text"]):
                self.problems.append("%s: an undated line is not accounted for. Give it a date in date_corrections, or record it in curation.json with no touches. Key %s" % (where, e["key"]))
            elif cur_e is not None and (cur_e.get("touches") or cur_e.get("feedback")):
                self.problems.append("%s: curation.json gives it touches or feedback but it has no date. Add a date_corrections entry. Key %s" % (where, e["key"]))
            self.stats["entries_undated_no_event"] += 1
            return None
        if date > self.through:
            self.stats["entries_after_through"] += 1
            return None
        if cur_e is None:
            touches, formulaic = N.infer_touches(e["text"]) if e["field"] == "note" else ([], False)
            if not formulaic:
                self.problems.append("%s: this note has not been read into curation.json yet (curation_tools.py todo lists it). Key %s" % (where, e["key"]))
                return None
            self.stats["entries_by_rule"] += 1
            return date, [dict(self.touch(t, date, quality, "auto", seq), _field=e["field"]) for t in touches], None
        self.stats["entries_curated"] += 1
        if (cur_e.get("unsure") or "").strip() and date <= self.we:
            self.unsure.append((name, cur_e["unsure"].strip()))
        if not cur_e.get("touches") and not cur_e.get("feedback"):
            self.stats["entries_no_event"] += 1
        ts = [dict(self.touch(t, date, quality, "curated", seq, cur_e.get("offer_related")), _field=e["field"]) for t in cur_e.get("touches") or []]
        fb = self.feedback(cur_e["feedback"], date, cur_e.get("provenance")) if cur_e.get("feedback") else None
        if date > self.we:
            self.stats["entries_after_week_end"] += 1
        return date, ts, fb

    def columns(self, data_rows, touches, later, seq, own=()):
        """The Email / Call / Text columns keep one date per channel. A date there with no matching note is a
        touch with no note. A call date with no call note on a day the person answered means they spoke by phone."""
        col = {}
        for r in data_rows:
            for ch in ("call", "email", "text"):
                dates = (r.get("last_touch_all") or {}).get(ch) or ([r["last_touch"][ch]] if (r.get("last_touch") or {}).get(ch) else [])
                for d in dates:
                    col.setdefault(d, {}).setdefault(ch, r["key"])
        for d in sorted(col):
            if d > self.through:
                self.stats["last_touch_cells_after_through"] += len(col[d])
                continue
            target = touches if d <= self.we else later
            for ch in [x for x in ("call", "text", "email") if x in col[d]]:      # the order the stock phrase uses
                seq += 1
                cur_e = (self.cur.get("entries") or {}).get(C.entry_key(col[d][ch], "last_" + ch, d, ""))
                if cur_e is not None:
                    target.extend(self.touch(t, d, "exact", "column", seq, cur_e.get("offer_related")) for t in cur_e.get("touches") or [])
                    self.stats["column_touches_curated"] += len(cur_e.get("touches") or [])
                    continue
                if any(t["date"] == d and "_feedback" not in t and N.family(t["channel"]) == ch for t in target):
                    continue
                answered = [t for t in target if t["date"] == d and "_feedback" not in t and t["direction"] == "inbound" and t["channel"] == "unknown"]
                if ch == "call" and answered:
                    for t in answered:
                        t["channel"] = "call"
                    self.stats["reply_channel_from_column"] += len(answered)
                    continue
                target.append(self.touch(N.column_touch(ch), d, "exact", "column", seq))
                target[-1]["_ward"] = col[d][ch] not in own
                self.stats["touches_from_columns_only"] += 1

    # ----------------------------------------------------------------------------------------- engagements
    def engagements(self, p, data_rows, touches, dated, is_host, name):
        """(on or before the week end, after it). A row's tab says what it was unless curation says otherwise:
        people.<id>.engagements maps a row key to the engagements that row really stands for ([] for none),
        and the key '+' adds engagements no row carries."""
        we, explicit = self.we, p.get("engagements") or {}
        first = min([d for d in dated if d <= we] + [t["date"] for t in touches if not t.get("_ward")] or [None], key=lambda d: d or "9999")
        out = []

        def add(e):
            e = dict(e)
            if e.get("date") == "first_record":
                e.update(date=first, date_quality="approximate" if first else "missing")
            e.setdefault("date_quality", "exact" if e.get("date") else "missing")
            e.setdefault("confirmed", True)
            if not any(x["type"] == e["type"] and x.get("date") == e.get("date") for x in out):
                out.append(e)

        for r in data_rows:
            kind = self.kind[r["key"]]
            if r["key"] in explicit:
                for e in explicit[r["key"]]:
                    add(e)
                continue
            row_dates = sorted(self.entry_date(e)[0] for e in r["entries"] if self.entry_date(e)[0] and self.trusted_date(e))
            if r.get("invited_by_raw"):
                add({"type": "disclosure_shared_by_agent", "date": None, "date_quality": "missing"})
            elif kind == "disclosure":
                if not is_host and not any(x["type"] in C.DISCLOSURE_TYPES for x in out):
                    add({"type": "disclosure_on_list", "date": "first_record"})
            elif kind == "showing":
                whens = [w for w in r.get("when") or [] if w.get("date")]
                for w in whens:
                    e = {"type": self.tour_type, "date": w["date"], "date_quality": "exact"}
                    if w.get("time_text"):
                        e["time_text"] = w["time_text"]
                    add(e)
                if not whens:
                    d = row_dates[0] if row_dates else None
                    add({"type": "inquiry", "date": d, "date_quality": "approximate" if d else "missing"})
                    self.auto_inquiries.append(name)
            elif kind == "inquiry":
                d = row_dates[0] if row_dates else None
                add({"type": "inquiry", "date": d, "date_quality": "approximate" if d else "missing"})
        for e in explicit.get("+") or []:
            add(e)
        keep, later = [], []
        for e in out:
            if e.get("date") and e["date"] > we:
                if e["date"] <= self.through:
                    later.append(e)
                else:
                    self.stats["engagements_after_through"] += 1
            else:
                keep.append(e)
        keep.sort(key=lambda e: e.get("date") or "9999")
        return keep, later

    # ----------------------------------------------------------------------------------------- tags
    def tags(self, cid, c, p, rows, feedback):
        if (p.get("unsure") or "").strip():
            self.unsure.append((c["name_short"], p["unsure"].strip()))
        we, name = self.we, c["name_short"]
        sheet = self.sheet_tags(rows)
        sources = {}
        counted_person = C.is_counted(c)
        feedback.sort(key=lambda f: f["date"])
        if c["team_side"]:
            for f in feedback:                              # a host's recap is not a buyer conversation
                f.update(source="open_house_host", counts_as_conversation=False, price_reaction="unknown", themes=[], liked=[])
        feedback = self.one_conversation_a_day(feedback)
        log = [f for f in feedback if f["counts_as_conversation"]]
        for f in feedback:
            if not f["counts_as_conversation"]:
                f.update(themes=[], liked=[])
                if f["source"] == "open_house_host":
                    f["price_reaction"] = "unknown"
            elif f["price_reaction"] == "unknown":
                f["price_reaction"] = "not_raised"

        # price: lives on the dated conversations. A sheet column or a person's correction overrides the reading.
        pv, ps = self.effective_tag(p, "price_reaction", sheet)
        if pv in C.PRICE_BUCKETS and counted_person and (ps in C.PROVENANCE_KEEPS or not any(f["price_reaction"] in ("too_high", "fair_or_positive") for f in log)):
            if not log:
                if pv != "not_raised":
                    self.notes.append("%s has a price reaction on file (%s) but no dated conversation, so it is not in the tally. Log the dated feedback line." % (name, pv.replace("_", " ")))
            elif pv == "not_raised":
                for f in log:
                    f["price_reaction"] = "not_raised"
                sources["price_reaction"] = ps
            else:
                raised = [f for f in log if f["price_reaction"] in ("too_high", "fair_or_positive")]
                (raised[-1] if raised else log[-1])["price_reaction"] = pv
                if not raised:
                    self.stats["price_tags_placed_on_latest_conversation"] += 1
                sources["price_reaction"] = ps
        elif log:
            sources["price_reaction"] = weakest(f["_prov"] for f in log)
        av, asrc = self.effective_tag(p, "price_asked", sheet)
        if av is not None and log:
            if av:
                log[-1]["price_asked"] = True
            else:
                for f in log:
                    f["price_asked"] = False
            sources["price_asked"] = asrc

        # themes and liked points: the person-level tag is the truth, the conversations carry it
        for field, order, other in (("themes", C.THEME_KEYS, "theme_other"), ("liked", C.LIKED_KEYS, "liked_other")):
            tv, ts = self.effective_tag(p, field, sheet)
            from_entries = set(k for f in log for k in f[field])
            want = set(tv) if tv is not None else from_entries
            if not log or not counted_person:
                if want and counted_person:
                    self.notes.append("%s has %s on file but no dated conversation, so they are not in the tally." % (name, field.replace("liked", "liked points")))
                want = set()
            for f in log:
                f[field] = [k for k in order if k in f[field] and k in want]
            missing = want - set(k for f in log for k in f[field])
            if missing and log:
                log[-1][field] = [k for k in order if k in set(log[-1][field]) | missing]
            c[field] = [k for k in order if k in want]
            label = (p.get(other) or "").strip() or None
            if ("other" in want) != bool(label):
                self.problems.append("%s (%s): the '%s' list has 'other' %s a %s label. They go together." % (cid, name, field, "without" if not label else "missing while there is", other))
            c[other] = label if "other" in want else None
            if want:
                sources[field] = weakest([ts] + [f["_prov"] for f in log]) if tv is not None else weakest(f["_prov"] for f in log)

        for key, default in (("interest", "unknown"), ("offer_intent", "unknown"), ("next_followup_date", None)):
            v, s = self.effective_tag(p, key, sheet)
            c[key] = v if v is not None else default
            if v is not None:
                sources[key] = s
        basis_date = p.get("offer_basis_date")
        if basis_date and basis_date > we:
            if c["offer_intent"] in ("yes", "maybe"):
                self.notes.append("%s spoke about a possible offer on %s, after the week closed. This report does not show that yet. It is in the box for what came in since the week closed." % (name, C.fmt_date(basis_date)))
                c["offer_intent"] = "unknown"
                sources.pop("offer_intent", None)
        else:
            c["offer_basis_safe"], c["offer_basis_date"] = p.get("offer_basis_safe"), basis_date

        status = p.get("status") if p.get("status") in TAG_STATUSES else None
        if c["interest"] == "passed" and status in ("writing_offer", "offer_submitted"):
            self.problems.append("%s (%s): interest is 'passed' while status is '%s'. A person is never shown both ways: fix one." % (cid, name, status))
        if status == "passed" or (c["interest"] == "passed" and status is None):
            status, c["interest"] = "passed", "passed"
        if status and not c["touches"] and counted_person:
            self.notes.append("%s is marked %s, but no dated call, text, email or conversation is logged, so the report cannot show an answer. Add the dated note." % (name, status.replace("_", " ")))
            status = None
            if c["interest"] == "passed":
                c["interest"] = "unknown"
        c["status"] = status or "not_yet_contacted"
        c["status_note_safe"] = p.get("status_note_safe")

        c["feedback_log"] = [public(f) for f in feedback]
        c["feedback_safe"] = p.get("feedback_safe")
        as_of = p.get("feedback_safe_as_of")
        if c["feedback_safe"] and as_of and as_of > we:      # the comment quotes an entry made after the week closed
            c["feedback_safe"] = " ".join(f["text_safe"] for f in feedback) or None
            self.stats["comments_rebuilt_as_of_week_end"] += 1
        c["feedback_softened"] = bool(p.get("feedback_softened"))
        if counted_person and log and not c["feedback_safe"]:
            c["feedback_safe"] = log[-1]["text_safe"]
        self.provenance[cid] = dict((k, v) for k, v in sorted(sources.items()) if v)

    def one_conversation_a_day(self, feedback):
        """A conversation is one person on one day. Two feedback lines logged on one day are one conversation."""
        out, by_day = [], {}
        for f in feedback:
            if not f["counts_as_conversation"] or f["date"] not in by_day:
                if f["counts_as_conversation"]:
                    by_day[f["date"]] = f
                out.append(f)
                continue
            a = by_day[f["date"]]
            self.stats["same_day_feedback_merged"] += 1
            if f["text_safe"] and f["text_safe"] not in (a["text_safe"] or ""):
                a["text_safe"] = ((a["text_safe"] or "") + " " + f["text_safe"]).strip()
            a["softened"] = a["softened"] or f["softened"]
            if f["price_reaction"] in ("too_high", "fair_or_positive"):
                a["price_reaction"] = f["price_reaction"]
            if f["price_asked"] is not None:
                a["price_asked"] = bool(a["price_asked"]) or f["price_asked"]
            if f["source"] == "written_reply":
                a["source"] = "written_reply"
            a["themes"] = a["themes"] + [k for k in f["themes"] if k not in a["themes"]]
            a["liked"] = a["liked"] + [k for k in f["liked"] if k not in a["liked"]]
            a["_prov"] = weakest([a["_prov"], f["_prov"]])
        return out
