# -*- coding: utf-8 -*-
"""sr_correct: applies what the operator said in plain words after reading the report.

Used by curation_tools.py correct. One job: change curation.json so the correction holds in every later week.

    find_person(cur, raw, who)        ids a plain name could mean (an id, a short name, words from the sheet)
    printed_texts(cur, raw)           every sentence in curation.json that a report can print, with its path
    correct(cur, fix, raw, by, on)    apply one correction; everything it touches is corrected_by_operator

A corrected value, sentence or person is never overwritten by a later automatic pass (curation_tools.py apply
skips it). Nothing here prints to a seller and nothing here gates a build.
Standard library only. No real client data belongs in this file.
"""
import datetime
import re

import sr_contract as C

PERSON_FIELDS = ("name_short", "name_recorded", "kind", "brokerage", "is_open_house_host", "represented_by",
                 "reached_through", "phone_out_of_service", "feedback_safe", "feedback_softened", "feedback_safe_as_of",
                 "status", "status_note_safe", "theme_other", "liked_other", "offer_basis_safe", "offer_basis_date",
                 "tag_notes", "extra", "unsure")


def index(raw):
    rows, kinds, tabs = {}, {}, {}
    for t in raw.get("tabs") or []:
        for r in t["rows"]:
            rows[r["key"]], kinds[r["key"]], tabs[r["key"]] = r, t["kind"], t["title"]
    return rows, kinds, tabs


def holders(cur):
    return dict((k, cid) for cid, p in cur["people"].items() for k in p.get("rows") or [])


def next_id(cur):
    """Ids are assigned once and never reused, including the ids of people merged away."""
    used = [int(k[1:]) for k in cur["people"] if re.match(r"^c\d+$", k)]
    used += [int(m.group(1)) for o in cur.get("overrides") or [] for m in [re.match(r"^people\.c(\d+)$", str(o.get("path")))] if m]
    return "c%03d" % (max(used or [0]) + 1)


def blank_person(rows, kind="agent"):
    return {"rows": list(rows), "name_short": None, "name_recorded": True, "kind": kind, "brokerage": None,
            "is_open_house_host": False, "team_side": None, "represented_by": None, "reached_through": None,
            "phone_out_of_service": None, "tags": {}, "feedback_safe": None, "feedback_softened": False, "status": None,
            "status_note_safe": None, "theme_other": None, "liked_other": None, "offer_basis_safe": None,
            "offer_basis_date": None, "tag_notes": None}


def sheet_value(raw_rows, person, tag):
    vals = [(max([e["date"] or "" for e in raw_rows[k]["entries"]] or [""]), (raw_rows[k].get("sheet_tags") or {}).get(tag))
            for k in person.get("rows") or [] if k in raw_rows]
    vals = [v for v in vals if v[1] is not None]
    return sorted(vals)[-1][1] if vals else None


def person_name(cur, rows, cid):
    """The short name a report prints for this person."""
    p = cur["people"][cid]
    if p.get("name_short"):
        return p["name_short"]
    for k in p.get("rows") or []:
        r = rows.get(k) or {}
        n = C.short_name(r.get("name_raw") or r.get("buyer_raw"))
        if n:
            return n
    return cid


def find_person(cur, raw, who):
    """Ids of the people a plain name could mean: an id, a short name, or words from the name as typed in the sheet."""
    rows, _, _ = index(raw)
    who = (who or "").strip()
    if who in cur["people"]:
        return [who]
    words = [w for w in re.split(r"[^a-z0-9']+", who.lower()) if w]
    hits = []
    for cid, p in sorted(cur["people"].items()):
        names = [p.get("name_short") or ""]
        for k in p.get("rows") or []:
            r = rows.get(k) or {}
            names += [r.get("name_raw") or "", r.get("buyer_raw") or "", C.short_name(r.get("name_raw") or r.get("buyer_raw")) or ""]
        hay = set(w for n in names for w in re.split(r"[^a-z0-9']+", n.lower()) if w)
        if words and all(w in hay for w in words):
            hits.append(cid)
    return hits


def printed_texts(cur, raw):
    """Every sentence in curation.json that a report can print: [(owner id or None, path, text)].
    A path is a list of keys from the top of curation.json down to the string."""
    rows, _, _ = index(raw)
    owner = holders(cur)
    out = []
    for cid, p in sorted(cur["people"].items()):
        for k in ("feedback_safe", "status_note_safe", "offer_basis_safe", "theme_other", "liked_other"):
            if isinstance(p.get(k), str) and p[k].strip():
                out.append((cid, ["people", cid, k], p[k]))
        for kind, fld in (("touches", "summary_safe"), ("feedback", "text_safe")):
            for n, it in enumerate((p.get("extra") or {}).get(kind) or []):
                if isinstance(it.get(fld), str) and it[fld].strip():
                    out.append((cid, ["people", cid, "extra", kind, n, fld], it[fld]))
        for rk, engs in sorted((p.get("engagements") or {}).items()):
            for n, e in enumerate(engs or []):
                if isinstance(e.get("note"), str) and e["note"].strip():
                    out.append((cid, ["people", cid, "engagements", rk, n, "note"], e["note"]))
    for key, e in sorted(cur["entries"].items()):
        cid = owner.get(key.split("/")[0])
        for n, t in enumerate(e.get("touches") or []):
            if isinstance(t.get("summary_safe"), str) and t["summary_safe"].strip():
                out.append((cid, ["entries", key, "touches", n, "summary_safe"], t["summary_safe"]))
        fb = e.get("feedback") or {}
        if isinstance(fb.get("text_safe"), str) and fb["text_safe"].strip():
            out.append((cid, ["entries", key, "feedback", "text_safe"], fb["text_safe"]))
    for key, o in sorted(cur["open_houses"].items()):
        if isinstance(o.get("recap_safe"), str) and o["recap_safe"].strip():
            out.append((None, ["open_houses", key, "recap_safe"], o["recap_safe"]))
        pr = o.get("price_remark") or {}
        if isinstance(pr.get("remark_safe"), str) and pr["remark_safe"].strip():
            out.append((None, ["open_houses", key, "price_remark", "remark_safe"], pr["remark_safe"]))
    for n, o in enumerate(cur.get("offers") or []):
        for k in ("terms_summary", "note_safe"):
            if isinstance(o.get(k), str) and o[k].strip():
                out.append((o.get("contact_id"), ["offers", n, k], o[k]))
    for n, line in enumerate(cur.get("next_week") or []):
        if isinstance(line, str) and line.strip():
            out.append((None, ["next_week", n], line))
    return out


def _get(node, path):
    for k in path:
        node = node[k]
    return node


def _put(node, path, value):
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value


def parse_value(key, text):
    """The value of one --set KEY=VALUE, typed the plain way."""
    t = (text or "").strip()
    if t.lower() in ("null", "none", ""):
        return [] if key in ("themes", "liked") else None
    if key in ("themes", "liked"):
        return [x.strip() for x in t.split(",") if x.strip()]
    if key in ("price_asked", "name_recorded", "is_open_house_host", "phone_out_of_service", "feedback_softened"):
        if t.lower() not in ("true", "false", "yes", "no"):
            raise SystemExit("%s takes true or false" % key)
        return t.lower() in ("true", "yes")
    return t


def correct(cur, fix, raw, by=None, on=None):
    """Applies one correction (in place) and records it as corrected_by_operator. Returns a list of what changed."""
    rows, _, _ = index(raw)
    by, on = by or fix.get("by") or "operator", C.iso(on or fix.get("on") or datetime.date.today())
    why = fix.get("why")
    done = []

    def stamp(tag_dict, person, key):
        tag_dict.update(provenance="corrected_by_operator", corrected_by=by, corrected_on=on, sheet_value_seen=sheet_value(rows, person, key))

    def override(path, value, reason):
        cur["overrides"].append({"path": path, "value": value, "by": by, "on": on, "reason": reason or why or "Corrected by the operator."})

    def mark_path(path):
        """Records a text edit so no later automatic pass undoes it."""
        if path[0] == "entries":
            cur["entries"][path[1]].update(provenance="corrected_by_operator", corrected_by=by, corrected_on=on)
            cur["entries"][path[1]].pop("unsure", None)
        elif path[0] == "open_houses":
            cur["open_houses"][path[1]].update(corrected_by=by, corrected_on=on)
            cur["open_houses"][path[1]].pop("unsure", None)
        elif path[0] == "offers":
            cur["offers"][path[1]].update(corrected_by=by, corrected_on=on)
        elif path[0] == "people":
            override(".".join(str(x) for x in path[:3]), _get(cur, path[:3]), None)
            cur["people"][path[1]].pop("unsure", None)
        else:
            override(str(path[0]), cur[path[0]], None)

    for m in fix.get("merge") or []:
        keep, gone = m.get("keep"), m.get("absorb")
        if keep not in cur["people"] or gone not in cur["people"] or keep == gone:
            raise SystemExit("merge: %r and %r must be two people in curation.json" % (keep, gone))
        cur["people"][keep]["rows"] += [k for k in cur["people"][gone]["rows"] if k not in cur["people"][keep]["rows"]]
        for p in cur["people"].values():
            if p.get("represented_by") == gone:
                p["represented_by"] = keep
        del cur["people"][gone]
        override("people.%s" % gone, "merged into %s" % keep, m.get("reason") or "Same person on two rows.")
        done.append("merged %s into %s" % (gone, keep))
    for sp in fix.get("split") or []:
        src, move = sp.get("person"), sp.get("rows") or []
        if src not in cur["people"] or not move or not all(k in cur["people"][src]["rows"] for k in move):
            raise SystemExit("split: the rows must belong to %r" % src)
        if len(move) == len(cur["people"][src]["rows"]):
            raise SystemExit("split: a person keeps at least one row")
        new = next_id(cur)
        cur["people"][src]["rows"] = [k for k in cur["people"][src]["rows"] if k not in move]
        cur["people"][new] = blank_person(move, sp.get("kind") or cur["people"][src].get("kind") or "agent")
        override("people.%s.rows" % new, move, sp.get("reason") or "Two different people were on one record.")
        done.append("split %d row(s) from %s into %s" % (len(move), src, new))
    for cid, patch in sorted((fix.get("people") or {}).items()):
        if cid not in cur["people"]:
            raise SystemExit("the correction names %s, who is not in curation.json" % cid)
        p = cur["people"][cid]
        for k, v in patch.items():
            if k in C.TAG_FIELDS:
                tag = p.setdefault("tags", {}).setdefault(k, {})
                tag["value"] = v
                stamp(tag, p, k)
                done.append("%s.%s = %s" % (cid, k, v))
            elif k in PERSON_FIELDS or k == "engagements":
                p[k] = v
                override("people.%s.%s" % (cid, k), v, patch.get("note"))
                done.append("%s.%s corrected" % (cid, k))
            elif k != "note":
                raise SystemExit("correction for %s: %r is not a field that can be corrected" % (cid, k))
        p.pop("unsure", None)
    for key, patch in sorted((fix.get("entries") or {}).items()):
        if key not in cur["entries"]:
            raise SystemExit("the correction names a note that is not in curation.json: %s" % key)
        e = cur["entries"][key]
        for k, v in patch.items():
            if k == "touches":
                e["touches"] = v
            elif k == "feedback":
                e["feedback"] = v
            elif e.get("feedback") is not None:
                e["feedback"][k] = v
            else:
                raise SystemExit("correction for %s: there is no feedback on this note to set %r on" % (key, k))
        mark_path(["entries", key])
        done.append("note %s corrected" % key)
    for key, patch in sorted((fix.get("open_houses") or {}).items()):
        cur["open_houses"].setdefault(key, {}).update(patch)
        mark_path(["open_houses", key])
        done.append("open house %s corrected" % key)
    for key, reason in (fix.get("ignore_rows") or {}).items():
        owner = holders(cur).get(key)
        if owner:
            raise SystemExit("ignore_rows: %s is held by %s. Split it off first." % (key, owner))
        cur["ignored_rows"][key] = reason
        done.append("row %s set aside" % key)
    if "next_week" in fix:
        cur["next_week"] = list(fix["next_week"])
        override("next_week", cur["next_week"], "Edited by the operator.")
        done.append("next_week edited")

    # wording: reword or remove a phrase in what the report prints, for one person or everywhere
    scope = fix.get("scope")                                 # a person id, or None for everywhere
    for old, new in fix.get("reword") or []:
        hits = [(cid, path, text) for cid, path, text in printed_texts(cur, raw)
                if old.lower() in text.lower() and (scope is None or cid == scope)]
        if not hits:
            raise SystemExit("reword: %r is not in any sentence the report prints%s. Use --find to see the wording on file."
                             % (old, "" if scope is None else " for " + scope))
        for cid, path, text in hits:
            fixed = re.sub(re.escape(old), lambda _m: new, text, flags=re.I)
            fixed = re.sub(r"\s{2,}", " ", fixed).strip()
            bad = C.safe_text_problems(fixed, streets=False)
            if bad or not fixed:
                raise SystemExit("reword: the new wording %s. Nothing was changed." % (", ".join(bad) or "leaves the sentence empty"))
            _put(cur, path, fixed)
            mark_path(path)
            done.append("reworded %s" % "/".join(str(x) for x in path))
    for phrase in fix.get("remove") or []:
        hits = [(cid, path, text) for cid, path, text in printed_texts(cur, raw)
                if phrase.lower() in text.lower() and (scope is None or cid == scope)]
        if not hits:
            raise SystemExit("remove: %r is not in any sentence the report prints%s. Use --find to see the wording on file."
                             % (phrase, "" if scope is None else " for " + scope))
        for cid, path, text in hits:
            kept = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if phrase.lower() not in x.lower()]
            if not kept:
                if path[0] == "people" and len(path) == 3:
                    _put(cur, path, None)                    # a person-level line can simply go
                elif path[0] == "next_week":
                    cur["next_week"][path[1]] = ""
                else:
                    raise SystemExit("remove: taking %r out would leave an entry with no words (%s). Give the new wording with "
                                     "--reword ... --to ... instead. Nothing was changed." % (phrase, "/".join(str(x) for x in path)))
            else:
                _put(cur, path, " ".join(kept))
            mark_path(path)
            done.append("removed the sentence with %r from %s" % (phrase, "/".join(str(x) for x in path)))
    cur["next_week"] = [x for x in cur.get("next_week") or [] if isinstance(x, str) and x.strip()]
    cur["updated"] = on
    return done
