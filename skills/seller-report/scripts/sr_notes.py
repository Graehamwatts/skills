# -*- coding: utf-8 -*-
"""sr_notes: what a follow-up note says was done, read from its words.

Most notes in the activity sheet are one of a few stock phrases ("no answer, left a vm. sent a text and
email"). Those are classified here by rule, so nobody has to tag them. Any note that says more than the
stock phrases is NOT classified here: it goes to the tagging list (curation_tools.py todo).

    infer_touches(text)        (touches, formulaic) for one dated note
    column_touch(channel)      the touch logged when only the Email / Call / Text date column records it
    is_label(text)             an undated line that is a pointer or a label, not an event
    dead_number(text)          the note says the number on file does not work
    settle_day(touches)        one follow-up per channel per day, the same attempt typed on two tabs counted once

The summaries written here are seller-facing: plain, no first person, no dashes.
Standard library only. No real client data belongs in this file.
"""
import re

P_NOANS = re.compile(r"no answer")
P_VM = re.compile(r"left (a )?vm|left a voicemail|left voicemail|\blvm\b")
P_TEXT = re.compile(r"sent (a |her |him )?(a )?(follow up )?text|text follow up|sent text|text and email|a text instead|call and text")
P_EMAIL = re.compile(r"sent (an |a |her |him )?(a )?(follow up )?email|text and email|sent email")
P_FAIL = re.compile(r"hang up|hung up|call rejected|call disconnect|auto rejected|call doesn'?t work|not in service|"
                    r"bad number|calls? doesn'?t go through|vm full|vm disconnected|no longer in service")
FILLER = re.compile(r"no answer|left (a )?vm|left a voicemail|left voicemail|\blvm\b|sent (an? |her |him )?(an? )?(follow up )?(text|email)|"
                    r"text and email|and email|text follow up|follow up|sent|instead|and|on me|my calls? (are getting|is)?|"
                    r"hang up|hung up|call rejected|call disconnects?( when going to vm)?|auto rejected|"
                    r"call doesn'?t work|number( no longer)? (not )?in service|bad number|vm full|"
                    r"vm disconnected while recording|[\s,.\-/]+")
P_DEAD = re.compile(r"not in service|no longer in service|out of service|number (is |was )?disconnected|disconnected number|wrong number", re.I)
P_LABEL = re.compile(r"^\W*(refer to (the )?showing activity (for|of) updates?|open house (host|house)|see showing (tab|activity))\W*$", re.I)

VOICEMAIL = {"channel": "voicemail", "direction": "outbound", "outcome": "left_voicemail",
             "summary_safe": "Called, no answer. Left a voicemail."}
NO_ANSWER = {"channel": "call", "direction": "outbound", "outcome": "no_answer", "summary_safe": "Called, no answer."}
NOT_CONNECTED = {"channel": "call", "direction": "outbound", "outcome": "did_not_connect",
                 "summary_safe": "Called. The call did not connect."}
TEXT = {"channel": "text", "direction": "outbound", "outcome": "sent", "summary_safe": "Sent a text."}
EMAIL = {"channel": "email", "direction": "outbound", "outcome": "sent", "summary_safe": "Sent an email."}
COLUMN = {
    "call": {"channel": "call", "direction": "outbound", "outcome": "unknown", "summary_safe": "Called. No note was kept."},
    "text": {"channel": "text", "direction": "outbound", "outcome": "sent", "summary_safe": "Sent a text. No note was kept."},
    "email": {"channel": "email", "direction": "outbound", "outcome": "sent", "summary_safe": "Sent an email. No note was kept."},
}
# which of two phone attempts on one day is the one to keep
_PHONE_RANK = {"reached": 5, "left_voicemail": 4, "no_answer": 3, "did_not_connect": 2, "unknown": 1, "sent": 0, "replied": 0}


def family(channel):
    return "call" if channel in ("call", "voicemail") else channel


def infer_touches(text):
    """(touches, formulaic) for one dated note. formulaic is true only when nothing is left over once the
    stock phrases are taken out: then the touches stand on their own and the note needs no tagging."""
    t = (text or "").lower().replace("\u2019", "'")
    touches = []
    if P_NOANS.search(t) or P_FAIL.search(t):
        if P_VM.search(t):
            touches.append(dict(VOICEMAIL))
        else:
            touches.append(dict(NO_ANSWER if P_NOANS.search(t) else NOT_CONNECTED))
    elif P_VM.search(t):
        touches.append(dict(VOICEMAIL))
    if P_TEXT.search(t):
        touches.append(dict(TEXT))
    if P_EMAIL.search(t):
        touches.append(dict(EMAIL))
    residue = FILLER.sub("", t)
    return touches, bool(touches) and len(residue) < 4


def column_touch(channel):
    return dict(COLUMN[channel])


def is_label(text):
    """An undated line that only points somewhere else or labels the row. It is never a touch."""
    lines = [ln for ln in (text or "").split("\n") if ln.strip()]
    return bool(lines) and all(P_LABEL.match(ln) for ln in lines)


def dead_number(text):
    return bool(P_DEAD.search(text or ""))


def settle_day(touches):
    """One follow-up per channel per day (a call that went to voicemail is one, the voicemail). The same
    attempt typed on two tabs is counted once. Returns (kept, dropped). Touches keep their order.

    Each touch may carry private keys starting with '_' (for example _auto). They are left in place."""
    kept, dropped, seen_text, slot = [], 0, set(), {}
    for t in touches:
        if t["direction"] != "outbound" or t["channel"] == "unknown":
            key = (t["date"], t["direction"], t["summary_safe"])
            if key in seen_text:
                dropped += 1
                continue
            seen_text.add(key)
            kept.append(t)
            continue
        key = (t["date"], family(t["channel"]))
        if key not in slot:
            slot[key] = len(kept)
            kept.append(t)
            continue
        old = kept[slot[key]]
        dropped += 1
        better = (_PHONE_RANK.get(t["outcome"], 0), not t.get("_auto")) > (_PHONE_RANK.get(old["outcome"], 0), not old.get("_auto"))
        if better:
            kept[slot[key]] = t
    return kept, dropped
