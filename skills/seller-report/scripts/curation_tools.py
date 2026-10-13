# -*- coding: utf-8 -*-
"""curation_tools: Claude's own steps between raw.json and the ledger, and the one step that applies a correction.

    python curation_tools.py todo    --folder <listing folder>                          what has not been read yet
    python curation_tools.py apply   --folder <listing folder> --readings readings.json merge Claude's reading of the notes
    python curation_tools.py correct --folder <listing folder> --who "Jordan" --set price_reaction=not_raised
    python curation_tools.py correct --folder <listing folder> --find "neighbour"
    python curation_tools.py correct --folder <listing folder> --who "Jordan" --reword "old words" --to "new words"
    python curation_tools.py correct --folder <listing folder> --who "Jordan" --remove "neighbour"
    python curation_tools.py correct --folder <listing folder> --file corrections.json

todo     lists only what is new since the last run: new people, new or edited notes, open house sessions,
         showing rows with no date, rows whose key changed. Stock-phrase notes are not listed: the rules read them.
         This is Claude's work list. Nobody else is asked to look at it.
apply    merges Claude's reading of the notes into curation.json. Anything the operator corrected is never
         overwritten, and neither is a value that came from one of the sheet's own columns.
correct  applies what the operator said in plain words after reading the report ("Jordan never said it was
         overpriced", "take out the part about the neighbour"): which person, what to change, the new value or
         wording. It is recorded as corrected_by_operator, so it holds in every later week. Then rebuild.

Where a value came from (claude, corrected_by_operator, sheet_column) is kept in curation.json only. Nothing
gates on it and nothing prints it. There is no review step and no confirm step.

Merges are proposals. Nothing here joins two rows into one person unless a readings file or a correction says so.
Everything written here is PRIVATE and is refused inside a git repo.
Standard library only. No real client data belongs in this file.
"""
import argparse
import datetime
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sr_contract as C          # noqa: E402
import sr_files as F             # noqa: E402
import sr_notes as N             # noqa: E402
from sr_correct import (PERSON_FIELDS, index, holders, next_id, blank_person, find_person, person_name,   # noqa: E402,F401
                        printed_texts, parse_value, correct)

READINGS_FILE_HELP = {
    "people": {"<id or proposed id>": {"rows": ["<row key>"], "kind": "agent | buyer | open_house_visitor", "brokerage": None,
                                       "is_open_house_host": False, "represented_by": None,
                                       "tags": {"interest": "hot | warm | cold | passed | unknown", "offer_intent": "yes | maybe | no | unknown",
                                                "themes": ["<theme key>"], "liked": ["<liked key>"]},
                                       "feedback_safe": "the person-level comment, seller-safe", "feedback_softened": False,
                                       "status": "passed | writing_offer | offer_submitted | null",
                                       "unsure": "one plain sentence when Claude could not tell something that changes a count, else leave out",
                                       "engagements": {"<row key>": [{"type": "agent_reported_tour", "date": "YYYY-MM-DD", "date_quality": "approximate"}]}}},
    "entries": {"<entry key>": {"touches": [{"channel": "call", "direction": "outbound", "outcome": "reached", "summary_safe": "..."}],
                                "feedback": {"text_safe": "...", "softened": False, "source": "conversation", "counts_as_conversation": True,
                                             "price_reaction": "too_high | fair_or_positive | not_raised", "price_asked": None,
                                             "themes": [], "liked": []}}},
    "open_houses": {"<session key>": {"recap_safe": "...", "date": "only when none is typed", "date_quality": "approximate"}},
    "ignored_rows": {"<row key>": "why this row is not a buyer-side contact"},
    "relink": {"<old row key>": "<new row key>"},
    "next_week": ["plain sentences"],
}


def blank_curation(slug):
    return {"schema_version": C.SCHEMA_VERSION, "slug": slug, "updated": None, "people": {}, "entries": {},
            "open_houses": {}, "offers": [], "ignored_rows": {}, "date_corrections": {}, "overrides": [], "next_week": []}


def load(folder):
    paths = F.listing_paths(folder)
    listing = F.load_json(paths["listing"], default={})
    raw = F.load_json(paths["raw"])
    cur = F.load_json(paths["curation"], default=blank_curation(listing.get("slug") or raw.get("slug")))
    return paths, listing, raw, cur


def locked_paths(cur):
    return set(o.get("path") for o in cur.get("overrides") or [])


def first_date(row, cur):
    """The earliest dated record on a sheet row (a note, the date cell, a date column), or None."""
    fixes = cur.get("date_corrections") or {}
    dates = [(fixes.get(e["key"]) or {}).get("date") or e.get("date") for e in row["entries"]]
    dates += [w.get("date") for w in row.get("when") or []] + list((row.get("last_touch") or {}).values())
    dates = [d for d in dates if d]
    return min(dates) if dates else None


def suffix(entry_key):
    return entry_key.split("/", 1)[1] if "/" in entry_key else entry_key


# ---------------------------------------------------------------------------------------------
# todo
# ---------------------------------------------------------------------------------------------
def todo(raw, cur, through=None):
    """The work list: everything in raw.json that has no curation yet. PRIVATE (it quotes the notes as typed)."""
    rows, kinds, tabs = index(raw)
    held, ignored = holders(cur), cur.get("ignored_rows") or {}
    through = C.iso(through) if through else raw.get("as_of")
    out = {"slug": raw.get("slug"), "as_of": raw.get("as_of"), "through": through,
           "WARNING": "PRIVATE. Quotes notes as typed. Never commit or share.",
           "relink_candidates": [], "new_people": [], "rows_to_add": [], "entries": [], "edited_entries": [],
           "showing_rows_without_a_date": [], "open_house_sessions": [], "offer_rows": [], "people_without_a_read": [],
           "stale_rows": [], "readings_file_format": READINGS_FILE_HELP}

    # rows whose key changed (a phone number was added, a name corrected): same notes, new key
    stale = [k for k in held if k not in rows]
    loose = [k for k in rows if k not in held and k not in ignored and kinds[k] in ("disclosure", "showing", "inquiry")]
    # a row whose every dated record is later than this issue waits for the next one (and so does a buyer its agent brought)
    later = set(k for k in loose if first_date(rows[k], cur) and first_date(rows[k], cur) > through)
    for k in loose:
        cands = (raw.get("inviter_candidates") or {}).get(k) or []
        if rows[k].get("invited_by_raw") and cands and all(c in later for c in cands):
            later.add(k)
    out["rows_waiting_for_a_later_issue"] = sorted(later)
    loose = [k for k in loose if k not in later]
    relinked = set()
    for old in stale:
        had = set(suffix(k) for k in cur["entries"] if k.startswith(old + "/"))
        best = None
        for k in loose:
            if kinds[k] != old.split(":")[0]:
                continue
            got = set(suffix(e["key"]) for e in rows[k]["entries"])
            n = len(had & got)
            if n and (best is None or n > best[1]):
                best = (k, n)
        if best:
            out["relink_candidates"].append({"old_row": old, "new_row": best[0], "person": held[old], "notes_in_common": best[1],
                                             "tab": tabs[best[0]], "row": rows[best[0]]["row"]})
            relinked.add(best[0])
        else:
            out["stale_rows"].append({"row": old, "person": held[old]})
    loose = [k for k in loose if k not in relinked]

    # new rows: join a person they may belong to, or become a proposed new person. Proposals only.
    group_of = {}
    for g in raw.get("merge_candidates") or []:
        for k in g["rows"]:
            group_of[k] = g
    nid = int(next_id(cur)[1:])
    proposed, placed = {}, {}
    for k in loose:
        if rows[k].get("invited_by_raw"):
            continue
        g = group_of.get(k)
        owner = next((held[x] for x in (g["rows"] if g else []) if x in held), None)
        if owner:
            out["rows_to_add"].append({"person": owner, "row": k, "tab": tabs[k], "sheet_row": rows[k]["row"],
                                       "basis": g["basis"], "names_differ": g.get("names_differ"), "needs_a_look": True})
            placed[k] = owner
            continue
        gid = id(g) if g else k
        if gid not in proposed:
            proposed[gid] = {"proposed_id": "c%03d" % nid, "rows": [], "basis": g["basis"] if g else "single_row",
                             "needs_a_look": bool(g), "names_differ": bool(g and g.get("names_differ"))}
            nid += 1
        proposed[gid]["rows"].append(k)
        placed[k] = proposed[gid]["proposed_id"]
    for k in loose:
        r = rows[k]
        if not r.get("invited_by_raw"):
            continue
        cands = (raw.get("inviter_candidates") or {}).get(k) or []
        agent = next((held.get(c) or placed.get(c) for c in cands if held.get(c) or placed.get(c)), None)
        proposed[k] = {"proposed_id": "c%03d" % nid, "rows": [k], "basis": "invited_by", "needs_a_look": agent is None,
                       "names_differ": False, "kind_guess": "buyer", "represented_by_guess": agent}
        nid += 1
        placed[k] = proposed[k]["proposed_id"]
    for p in proposed.values():
        first = rows[p["rows"][0]]
        hints = sorted(set(h for k in p["rows"] for h in rows[k]["hints"]))
        p.setdefault("kind_guess", "buyer" if ("buyer_lead" in hints or (not first.get("name_raw") and first.get("buyer_raw"))) else "agent")
        p["name_short_default"] = C.short_name(first.get("name_raw") or first.get("buyer_raw")) or None
        p["hints"] = hints
        p["rows"] = [{"key": k, "tab": tabs[k], "sheet_row": rows[k]["row"], "name_raw": rows[k].get("name_raw"),
                      "buyer_raw": rows[k].get("buyer_raw"), "when": [w.get("date") for w in rows[k].get("when") or []],
                      "sheet_columns": dict((a, b) for a, b in (rows[k].get("sheet_tags") or {}).items() if b is not None)} for k in p["rows"]]
        out["new_people"].append(p)

    # notes not read yet. A stock phrase needs no reading. An edited note has a new key: its old wording is shown beside it.
    gone = {}
    for key, e in cur["entries"].items():
        row_key = key.split("/")[0]
        if row_key in rows and "/last_" not in key and key not in set(x["key"] for x in rows[row_key]["entries"]):
            gone.setdefault(row_key, []).append((key, e))
    for k in sorted(set(list(held) + list(placed)), key=lambda x: (tabs.get(x, ""), rows[x]["row"] if x in rows else 0)):
        if k not in rows or kinds[k] == "open_house":
            continue
        r, person = rows[k], held.get(k) or placed.get(k)
        for e in r["entries"]:
            if e["key"] in cur["entries"]:
                continue
            fix = (cur.get("date_corrections") or {}).get(e["key"])
            date = (fix or {}).get("date") or e["date"]
            if date is None and N.is_label(e["text"]):
                continue
            if date is not None and date > through:
                continue
            stock, formulaic = N.infer_touches(e["text"]) if e["field"] == "note" else ([], False)
            if formulaic and date is not None:
                continue
            item = {"key": e["key"], "person": person, "tab": tabs[k], "sheet_row": r["row"], "field": e["field"], "date": date,
                    "text": e["text"], "undated": date is None, "sensitive_hints": C.sensitive_hints(e["text"]),
                    "stock_phrases_seen": [t["channel"] for t in stock], "says_number_is_dead": N.dead_number(e["text"])}
            if e.get("reply_lines"):
                item["reply_lines"] = e["reply_lines"]
            was = [x for x in gone.get(k, []) if x[0].split("/")[1:3] == e["key"].split("/")[1:3]]
            if was:
                item["edited_from"] = {"old_key": was[0][0], "old_curation": was[0][1]}
                out["edited_entries"].append(e["key"])
            out["entries"].append(item)
        if kinds[k] == "showing" and not [w for w in r.get("when") or [] if w.get("date")]:
            if k not in ((cur["people"].get(person) or {}).get("engagements") or {}):
                out["showing_rows_without_a_date"].append({"row": k, "person": person, "sheet_row": r["row"],
                                                           "question": "Was this a tour or an inquiry? Until someone says, it is read as an inquiry."})
    for t in raw.get("tabs") or []:
        for r in t["rows"]:
            if t["kind"] == "open_house":
                for s in r.get("sessions") or []:
                    if s["key"] in cur["open_houses"]:
                        continue
                    needs = (["date"] if not s["date"] else []) + (["paraphrase"] if (s.get("text") or "").strip() else [])
                    if needs and (s["date"] is None or s["date"] <= through):
                        out["open_house_sessions"].append({"key": s["key"], "sheet_row": r["row"], "date": s["date"], "time_text": s["time_text"],
                                                           "host_default": C.short_name(r.get("name_raw")) or None, "groups": s["groups"],
                                                           "counted_unit": s["counted_unit"], "groups_source": s["groups_source"],
                                                           "text": s.get("text"), "team_note": s.get("team_note"), "needs": needs})
            elif t["kind"] == "offers":
                used = set(o.get("source_row") for o in cur.get("offers") or [])
                if r["key"] not in used and r["key"] not in ignored:
                    out["offer_rows"].append({"row": r["key"], "sheet_row": r["row"], "cells": r["cells"]})
    for cid, p in sorted(cur["people"].items()):
        has_fb = any(k.split("/")[0] in (p.get("rows") or []) and e.get("feedback") for k, e in cur["entries"].items())
        if has_fb and not p.get("represented_by") and not p.get("status") and "interest" not in (p.get("tags") or {}):
            out["people_without_a_read"].append(cid)
    out["counts"] = dict((k, len(v)) for k, v in out.items() if isinstance(v, list))
    return out


# ---------------------------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------------------------
def as_tag(v):
    return {"value": v["value"] if isinstance(v, dict) and "value" in v else v, "provenance": "claude"}


def apply_tags(cur, tags, raw, today=None):
    """Merges Claude's reading of the notes into curation (in place). Anything the operator corrected stays as it is.
    Returns a report: {applied: [...], kept: [...], rejected: [...]}."""
    rows, kinds, _ = index(raw)
    rep = {"applied": [], "kept": [], "rejected": []}
    locked = locked_paths(cur)
    for old, new in (tags.get("relink") or {}).items():
        owner = holders(cur).get(old)
        if not owner or new not in rows:
            rep["rejected"].append("relink %s -> %s: the old row is not held by a person, or the new row is not in raw.json" % (old, new))
            continue
        p = cur["people"][owner]
        p["rows"] = [new if k == old else k for k in p["rows"]]
        new_keys = dict((suffix(e["key"]), e["key"]) for e in rows[new]["entries"])
        for key in [k for k in cur["entries"] if k.startswith(old + "/")]:
            target = new_keys.get(suffix(key)) or (new + "/" + suffix(key) if "/last_" in key else None)
            if target:
                cur["entries"][target] = cur["entries"].pop(key)
        if isinstance(p.get("engagements"), dict) and old in p["engagements"]:
            p["engagements"][new] = p["engagements"].pop(old)
        rep["applied"].append("relink %s -> %s (%s)" % (old, new, owner))
    held = holders(cur)
    for cid, patch in sorted((tags.get("people") or {}).items()):
        if not re.match(r"^c\d{3,}$", cid):
            rep["rejected"].append("people.%s: not an id in the form c001" % cid)
            continue
        is_new = cid not in cur["people"]
        clash = [k for k in patch.get("rows") or [] if held.get(k, cid) != cid]
        missing = [k for k in patch.get("rows") or [] if k not in rows]
        if clash or missing or (is_new and not patch.get("rows")):
            rep["rejected"].append("people.%s: %s" % (cid, "row already held by %s" % held[clash[0]] if clash else
                                                      ("row not in raw.json: %s" % missing[0] if missing else "a new person needs rows")))
            continue
        p = cur["people"].setdefault(cid, blank_person([], patch.get("kind") or "agent"))
        for k in patch.get("rows") or []:
            if k not in p["rows"]:
                p["rows"].append(k)
                held[k] = cid
        for k, v in (patch.get("tags") or {}).items():
            have = (p.get("tags") or {}).get(k)
            if have and have.get("provenance") in C.PROVENANCE_KEEPS:
                rep["kept"].append("people.%s.%s (%s)" % (cid, k, have.get("provenance").replace("_", " ")))
                continue
            p.setdefault("tags", {})[k] = as_tag(v)
            rep["applied"].append("people.%s.tags.%s" % (cid, k))
        for k in PERSON_FIELDS:
            if k in patch:
                if "people.%s.%s" % (cid, k) in locked and not is_new:
                    rep["kept"].append("people.%s.%s (corrected by the operator)" % (cid, k))
                elif p.get(k) != patch[k]:
                    p[k] = patch[k]
                    rep["applied"].append("people.%s.%s" % (cid, k))
        if "engagements" in patch:
            if "people.%s.engagements" % cid in locked and not is_new:
                rep["kept"].append("people.%s.engagements (corrected by the operator)" % cid)
            else:
                p.setdefault("engagements", {}).update(patch["engagements"])
                rep["applied"].append("people.%s.engagements" % cid)
    known = set(e["key"] for r in rows.values() for e in r["entries"])
    for key, e in sorted((tags.get("entries") or {}).items()):
        row_key = key.split("/")[0]
        if key not in known and not (row_key in rows and "/last_" in key):
            rep["rejected"].append("entries[%s]: no such note in raw.json (was it edited? run todo again)" % key)
            continue
        have = cur["entries"].get(key)
        if have and have.get("provenance") == "corrected_by_operator":
            rep["kept"].append("entries[%s] (corrected by the operator)" % key)
            continue
        new = dict((k, v) for k, v in e.items() if k not in ("provenance", "corrected_by", "corrected_on"))
        new.setdefault("touches", [])
        new.setdefault("feedback", None)
        new["provenance"] = "claude"
        cur["entries"][key] = new
        rep["applied"].append("entries[%s]" % key)
    for key, patch in sorted((tags.get("open_houses") or {}).items()):
        have = cur["open_houses"].setdefault(key, {})
        for k, v in patch.items():
            if have.get("corrected_by") or "open_houses.%s.%s" % (key, k) in locked:
                rep["kept"].append("open_houses[%s].%s (corrected by the operator)" % (key, k))
            else:
                have[k] = v
        rep["applied"].append("open_houses[%s]" % key)
    for o in tags.get("offers") or []:
        same = [i for i, x in enumerate(cur["offers"]) if x.get("id") and x.get("id") == o.get("id")]
        if same and cur["offers"][same[0]].get("corrected_by"):
            rep["kept"].append("offers[%s] (corrected by the operator)" % o.get("id"))
        elif same:
            cur["offers"][same[0]] = o
            rep["applied"].append("offers[%s]" % o.get("id"))
        else:
            cur["offers"].append(dict(o, id=o.get("id") or "o%d" % (len(cur["offers"]) + 1)))
            rep["applied"].append("offers[%s] added" % cur["offers"][-1]["id"])
    for key, why in (tags.get("ignored_rows") or {}).items():
        if key in held:
            rep["rejected"].append("ignored_rows[%s]: this row is held by %s" % (key, held[key]))
        elif key not in cur["ignored_rows"]:
            cur["ignored_rows"][key] = why
            rep["applied"].append("ignored_rows[%s]" % key)
    for key, fix in (tags.get("date_corrections") or {}).items():
        if (cur["date_corrections"].get(key) or {}).get("by"):
            rep["kept"].append("date_corrections[%s] (set by the operator)" % key)
        else:
            cur["date_corrections"][key] = fix
            rep["applied"].append("date_corrections[%s]" % key)
    if "next_week" in tags:
        if "next_week" in locked:
            rep["kept"].append("next_week (edited by the operator)")
        else:
            cur["next_week"] = [s for s in tags["next_week"] if isinstance(s, str) and s.strip()]
            rep["applied"].append("next_week")
    cur["updated"] = C.iso(today or datetime.date.today())
    return rep


# ---------------------------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------------------------
def save_checked(paths, cur):
    problems = C.validate_curation(cur)
    if problems:
        F.shout("curation.json was NOT written. %d problem(s):" % len(problems))
        for p in problems[:40]:
            F.say("  -", p)
        return 2
    F.save_json(paths["curation"], cur)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Claude's work list, its reading of the notes, and the operator's corrections (PRIVATE files).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("todo", "apply", "correct"):
        sp = sub.add_parser(name)
        sp.add_argument("--folder", required=True, help="the listing folder: <reports>\\seller-reports\\<slug>")
        if name == "todo":
            sp.add_argument("--through", help="ignore notes dated after this day. Default: the sheet's export date")
            sp.add_argument("--out", help="default: <folder>\\work\\todo.json")
        if name == "apply":
            sp.add_argument("--readings", required=True, help="the file Claude wrote from the work list (see readings_file_format in the todo output)")
        if name == "correct":
            sp.add_argument("--who", help="the person: a name as the report prints it, a name from the sheet, or an id such as c012")
            sp.add_argument("--set", action="append", default=[], metavar="FIELD=VALUE",
                            help="what to change for that person, for example price_reaction=not_raised, interest=cold, "
                                 "themes=size_layout,parking or feedback_safe='New wording.' (repeatable)")
            sp.add_argument("--find", metavar="WORDS", help="list every sentence the report prints that holds these words, and change nothing")
            sp.add_argument("--reword", metavar="OLD", help="words to replace in what the report prints (for --who, or everywhere with --everywhere)")
            sp.add_argument("--to", metavar="NEW", help="the new words for --reword")
            sp.add_argument("--remove", action="append", default=[], metavar="WORDS", help="take out each sentence holding these words")
            sp.add_argument("--everywhere", action="store_true", help="apply --reword or --remove to every person, not only --who")
            sp.add_argument("--file", help="a corrections file, for anything the switches do not cover (people, entries, open_houses, merge, split, ignore_rows, next_week)")
            sp.add_argument("--by", help="who asked for the correction. Default: operator")
            sp.add_argument("--why", help="the operator's words, kept with the correction")
            sp.add_argument("--on", help="YYYY-MM-DD. Default: today")
    a = ap.parse_args(argv)
    paths, listing, raw, cur = load(a.folder)
    if a.cmd == "todo":
        out = todo(raw, cur, a.through)
        dest = F.save_json(a.out or os.path.join(paths["work"], "todo.json"), out)
        F.say("work list written (PRIVATE):", dest)
        for k, n in sorted(out["counts"].items()):
            if n:
                F.say("  %-30s %d" % (k, n))
        if not any(out["counts"].values()):
            F.say("  nothing new to read")
        return 0
    if a.cmd == "apply":
        rep = apply_tags(cur, F.load_json(a.readings), raw)
        F.say("applied %d, kept %d (corrected by the operator), rejected %d" % (len(rep["applied"]), len(rep["kept"]), len(rep["rejected"])))
        for line in rep["kept"] + rep["rejected"]:
            F.say("  -", line)
        code = save_checked(paths, cur)
        return code or (1 if rep["rejected"] else 0)
    rows, _, _ = index(raw)
    if a.find:
        hits = [(cid, path, text) for cid, path, text in printed_texts(cur, raw) if a.find.lower() in text.lower()]
        F.say("%d sentence(s) the report prints hold %r (PRIVATE):" % (len(hits), a.find))
        for cid, path, text in hits:
            F.say("  - %s [%s] %s" % (("%s (%s)" % (person_name(cur, rows, cid), cid)) if cid in cur["people"] else "no one person",
                                      "/".join(str(x) for x in path), text))
        return 0
    fix = F.load_json(a.file) if a.file else {}
    cid = None
    if a.who:
        hits = find_person(cur, raw, a.who)
        if len(hits) != 1:
            F.shout("%r fits %d people. Nothing was changed." % (a.who, len(hits)))
            for h in hits[:12]:
                F.say("  - %s (%s)" % (person_name(cur, rows, h), h))
            return 2
        cid = hits[0]
    if a.set:
        if not cid:
            raise SystemExit("--set needs --who")
        patch = fix.setdefault("people", {}).setdefault(cid, {})
        for item in a.set:
            k, sep, v = item.partition("=")
            if not sep:
                raise SystemExit("--set takes FIELD=VALUE, got %r" % item)
            patch[k.strip()] = parse_value(k.strip(), v)
    if a.reword or a.remove:
        if not cid and not a.everywhere:
            raise SystemExit("say whose wording to change with --who, or pass --everywhere")
        if a.reword and a.to is None:
            raise SystemExit("--reword needs --to with the new words")
        fix["scope"] = None if a.everywhere else cid
        if a.reword:
            fix.setdefault("reword", []).append([a.reword, a.to])
        fix.setdefault("remove", []).extend(a.remove)
    if a.why:
        fix["why"] = a.why
    if not any(fix.get(k) for k in ("people", "entries", "open_houses", "merge", "split", "ignore_rows", "reword", "remove")) and "next_week" not in fix:
        raise SystemExit("correct needs something to change: --who with --set, --reword or --remove, or --file")
    done = correct(cur, fix, raw, a.by, a.on)
    for line in done:
        F.say("  -", line)
    code = save_checked(paths, cur)
    if code == 0:
        F.say("saved as corrected by the operator. It holds in every later week. Rebuild the report to see it.")
        if cid:
            mine = [(path, text) for owner, path, text in printed_texts(cur, raw) if owner == cid]
            if mine:
                F.say("what the report prints about %s now (check that the wording agrees with the change):" % person_name(cur, rows, cid))
                for path, text in mine:
                    F.say("  - [%s] %s" % ("/".join(str(x) for x in path), text))
    return code


if __name__ == "__main__":
    sys.exit(main())
