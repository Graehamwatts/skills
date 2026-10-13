# -*- coding: utf-8 -*-
"""sr_checks.numbers_lists: the lists under "The details" (counting-rules.md, section 15).

People are grouped by what they did: agents who showed the home, people on the disclosure package list, open
house visitors we know of, other inquiries. The gate decides who belongs in each list from the ledger's rows
(recount.lists_of) and reads the page for:

  list_heading.<key>    the count printed in the heading is the number of people who belong in the list
  list_entries.<key>    the number of entries beneath the heading equals that count, each entry is a person who
                        belongs there, and nobody is entered twice
  list_placement        a person is shown in full or in one line only in the first list they belong to
                        (showings, then disclosure packages, then open house), and as a pointer in the others;
                        nobody is shown in full twice; nobody we follow up with is left out
  list_everyone_in_full the link copy and the PDF show everyone in full, never as a one-line entry
  list_this_week        in the email, a person active in the report week is shown in full (a warning: an
                        email with no room left may fold some of them into one line)

An entry is an element with data-sr-entry="<full|line|pointer>:<contact id>" inside an element with
data-sr-list="<key>". The link copy leaves the id off for an agent with an offer on file. A page with no
entry hooks has only its headings checked, by their text.
"""
import re

from . import core
from . import recount as RC
from .page import numbers_in

TITLES = {
    "showings": ("Agents who showed the home", "Agents and buyers who toured the home"),
    "disclosure": ("People on the disclosure package list",),
    "open_house": ("Open house visitors we know of",),
    "other_inquiries": ("People who asked about the home",),
}
FORMS = ("full", "line", "pointer")


def _heading(ctx, key):
    """The counts the page prints in this list's heading: [(count, where)]."""
    out = [(numbers_in(ctx.page.flat(root=n)), "data-sr=list:%s, line %d" % (key, n.line)) for n in ctx.page.hooks("list:" + key)]
    if out:
        return [(nums[0] if len(nums) == 1 else None, where) for nums, where in out]
    text = ctx.seller_flat()
    for title in TITLES[key]:
        for mt in re.finditer(re.escape(title) + r" \((\d+)\)", text):
            out.append((int(mt.group(1)), "'%s'" % mt.group(0)))
    return out


def check_lists(B, ctx, m):
    members, placed = m["lists"], m["placed"]
    entries = ctx.page.entries()
    hooked = bool(entries)
    link = ctx.kind in ("link", "print")
    hidden = set(m["extra"]["offer_people"]) if link else set()        # the link copy never names an agent with an offer on file
    stray = entries.get(None) or []
    place, in_full, lines_in_link, folded = [], {}, [], []
    shown = {}                                                          # contact id -> entries that are not pointers
    for key in RC.LIST_KEYS:
        want = members[key]
        heads = _heading(ctx, key)
        bad = ["%s prints %s; %d %s in this list" % (where, "no single count" if n is None else n, len(want), "person belongs" if len(want) == 1 else "people belong")
               for n, where in heads if n != len(want)]
        if not heads and want:
            bad.append("the heading '%s (%d)' is not on the page" % (TITLES[key][0], len(want)))
        if heads or want:
            B.judge("list_heading." + key, bad, "'%s': the heading count is %d, the number of people who belong in the list"
                    % (TITLES[key][0], len(want)), "the count in a list heading is not the number of people in that list")
        if not hooked:
            continue
        got = entries.get(key) or []
        bad = []
        if len(got) != len(want):
            bad.append("%d entries beneath the heading; %d %s in this list" % (len(got), len(want), "person belongs" if len(want) == 1 else "people belong"))
        named = [cid for _, cid, _ in got if cid]
        unnamed = len(got) - len(named)
        for cid in sorted(set(named)):
            if cid not in want:
                bad.append("%s has an entry here and does not belong in this list" % cid)
            if named.count(cid) > 1:
                bad.append("%s is entered %d times" % (cid, named.count(cid)))
        missing = [cid for cid in want if cid not in named]
        owed = [cid for cid in missing if cid not in hidden]           # everyone else must have an entry that names them
        if owed:
            bad.append("no entry for %s" % ", ".join(owed[:8]))
        if unnamed > len([cid for cid in missing if cid in hidden]):
            bad.append("%d entries carry no contact id, and only an agent with an offer on file may go unnamed (link copy)" % unnamed)
        B.judge("list_entries." + key, bad, "'%s': %d entries beneath the heading, one for each person who belongs there"
                % (TITLES[key][0], len(got)), "the entries beneath a list heading do not match the people in that list")
        for form, cid, node in got:
            if form not in FORMS:
                place.append("an entry in '%s' has the form '%s' (line %d)" % (key, form, node.line))
                continue
            if link and form == "line":
                lines_in_link.append("%s is a one-line entry in '%s'" % (cid or "an unnamed entry", key))
            if not cid:
                continue
            first = placed[cid]["primary"] if cid in placed else None
            if form == "pointer" and first == key:
                place.append("%s is only a pointer in '%s', the first list they belong to" % (cid, key))
            elif form != "pointer" and first != key:
                place.append("%s is shown in '%s'; the first list they belong to is '%s'" % (cid, key, first))
            if form != "pointer":
                shown[cid] = shown.get(cid, 0) + 1
            if form == "full":
                in_full[cid] = in_full.get(cid, 0) + 1
            if not link and form == "line" and cid in placed and placed[cid]["active"] and first == key:
                folded.append("%s was active this week and has a one-line entry in '%s'" % (cid, key))
    if not hooked:
        B.skip("list_entries", "the page carries no data-sr-entry hooks, so the entries beneath each heading were not counted")
        return
    place += ["an entry sits outside every list (line %d)" % node.line for _, _, node in stray]
    place += ["%s is shown in full %d times" % (cid, k) for cid, k in sorted(in_full.items()) if k > 1]
    place += ["%s is shown %d times outside a pointer" % (cid, k) for cid, k in sorted(shown.items()) if k > 1 and in_full.get(cid, 0) <= 1]
    owed = [cid for cid, p in sorted(placed.items()) if p["primary"] and cid not in shown and cid not in hidden]
    if owed:
        place.append("no entry in full or in one line for %s" % ", ".join(owed[:10]))
    B.judge("list_placement", place, "everyone is shown once, in the first list they belong to, and as a pointer in the others (%d people)"
            % len([1 for p in placed.values() if p["primary"]]), "a person is listed in the wrong place, twice, or not at all")
    if link:
        B.judge("list_everyone_in_full", lines_in_link, "the %s copy shows everyone in full" % ctx.kind,
                "the %s copy must show everyone in full" % ctx.kind)
    elif folded:
        B.warn("list_this_week", "%d of this week's people are not shown in full (an email with no room left folds them into one line)"
               % len(folded), folded[:6])
    else:
        B.ok("list_this_week", "everyone active in the report week is shown in full")
