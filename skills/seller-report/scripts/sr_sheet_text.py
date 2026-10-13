# -*- coding: utf-8 -*-
"""sr_sheet_text: reads what people type into the activity sheet.

Text helpers for intake_sheet.py. Nothing here opens a file, and nothing here writes a word a seller will
read. Each function takes a cell value and returns plain data:

    clean(value)                      a cell as text (or the date it holds), junk characters removed
    DateCtx(list_date, as_of)         places a date typed without a year inside the listing's life
    split_dated(text, ctx)            one running cell -> its dated lines
    parse_when(value, ctx)            a "Date & Time" cell -> [{date, time_text, date_quality, ...}]
    parse_last_touch(value, ctx)      an Email / Call / Text cell -> the dates in it
    count_in_prose(text)              "6 groups", "no one came", "only one group" -> (n, unit, phrase)
    parse_sessions(when, recap, ctx)  one open house row -> one entry per session, each with its count
    read_sheet_tag(kind, value, ctx)  the four columns the team is adding, normalised
    phones_of, emails_of, name_key    contact details and the name key used to propose merges

Standard library only. No real client data belongs in this file.
"""
import datetime
import difflib
import re

import sr_contract as C

# ---------------------------------------------------------------------------------------------
# cells
# ---------------------------------------------------------------------------------------------
# zero-width and direction marks that web tools paste into date cells, and the soft hyphen
_INVISIBLE = dict.fromkeys((0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
                            0x2060, 0x2066, 0x2067, 0x2068, 0x2069, 0xFEFF, 0x00AD), None)
_ODD_SPACES = dict.fromkeys((0x00A0, 0x2002, 0x2003, 0x2007, 0x2009, 0x200A, 0x202F, 0x3000), " ")
_QUOTES = {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"'}
_TABLE = dict(_INVISIBLE)
_TABLE.update(_ODD_SPACES)
_TABLE.update(_QUOTES)


def clean(v):
    """A cell value as it should be read. Dates and datetimes pass through. A whole-number float loses its
    '.0' (phone numbers arrive as floats). Text loses zero-width characters, odd spaces and carriage
    returns, and curly quotes become straight ones. Empty text gives None."""
    if v is None:
        return None
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).translate(_TABLE).replace("\r\n", "\n").replace("\r", "\n")
    s = "\n".join(line.rstrip() for line in s.split("\n")).strip()
    return s or None


def cell_json(v):
    """A cleaned cell as it is stored in raw.json: text, or an ISO date / timestamp."""
    if isinstance(v, datetime.datetime):
        return v.replace(microsecond=0).isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    return v


_PHONE = re.compile(r"(?<![\d.])(?:\+?1[\s.\-]?)?\(?(\d{3})\)?[\s.\-]?(\d{3})[\s.\-]?(\d{4})(?!\d)")
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def phones_of(*values):
    """Ten-digit phone numbers found in the given cells, sorted, each once. Digits inside an email address
    are not a phone number."""
    out = set()
    for v in values:
        if v is None or isinstance(v, (datetime.datetime, datetime.date)):
            continue
        for m in _PHONE.finditer(_EMAIL.sub(" ", str(v))):
            out.add("".join(m.groups()))
    return sorted(out)


def emails_of(*values):
    out = set()
    for v in values:
        if isinstance(v, str):
            out.update(m.group(0).lower().rstrip(".") for m in _EMAIL.finditer(v))
    return sorted(out)


def name_key(raw):
    """'first_last' in lower case, for proposing that two rows are one person. Brackets and a second line
    are dropped. This is a hint, never a key: two people can share it."""
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", str(raw or "")).split("\n")[0]
    s = _EMAIL.sub(" ", _PHONE.sub(" ", s))
    toks = [t for t in re.findall(r"[^\W\d_][^\W\d_'\-]*", s.lower()) if len(t) > 1]
    if not toks:
        return None
    return toks[0] + ("_" + toks[-1] if len(toks) > 1 else "")


# ---------------------------------------------------------------------------------------------
# dates typed without a year
# ---------------------------------------------------------------------------------------------
class DateCtx(object):
    """The listing's life: from the list date (less a grace period for pre-launch notes) to the day the
    sheet was exported. A date typed without a year is placed inside it, never by today's year."""

    def __init__(self, list_date, as_of, grace_days=60):
        self.list_date = C.parse_date(list_date)
        self.as_of = C.parse_date(as_of)
        if self.as_of < self.list_date:
            raise ValueError("the export date %s is before the list date %s" % (self.as_of, self.list_date))
        self.lo = self.list_date - datetime.timedelta(days=grace_days)
        self.hi = self.as_of + datetime.timedelta(days=1)

    def place(self, month, day, year=None, prefer_past=False):
        """(date or None, rule). rule: year_typed, listing_life, outside_listing_life or bad_date.
        prefer_past is for notes: a note is about something that happened, so a date that fits nowhere in
        the listing's life is read as the latest such date before the export, not as a date still to come."""
        if not (1 <= month <= 12 and 1 <= day <= 31):
            return None, "bad_date"
        if year is not None:
            y = year + 2000 if year < 100 else year
            try:
                return datetime.date(y, month, day), "year_typed"
            except ValueError:
                return None, "bad_date"
        cands = []
        for y in range(self.list_date.year - 1, self.as_of.year + 2):
            try:
                cands.append(datetime.date(y, month, day))
            except ValueError:
                pass
        if not cands:
            return None, "bad_date"
        inside = [d for d in cands if self.lo <= d <= self.hi]
        if inside:
            after = [d for d in inside if d >= self.list_date]
            return (after[0] if after else inside[-1]), "listing_life"

        past = [d for d in cands if d <= self.hi]
        if prefer_past and past:
            return past[-1], "outside_listing_life"

        def gap(d):
            return (self.lo - d).days if d < self.lo else (d - self.hi).days
        return min(cands, key=lambda d: (gap(d), d)), "outside_listing_life"


# a dated line: an optional opening quote or bullet, M/D or M/D/YY, then any separators
_LINE_DATE = re.compile(
    r"^\s*[\"']?\s*[-*\u2022]?\s*"
    r"(\d{1,2})/0*(\d{1,2})(?:/(\d{4}|\d{2}))?(?![\d/])"
    r"(\s*(?:[-\u2013\u2014:.,;]+\s*)*)")
_FRACTION_WORD = re.compile(r"^(?:baths?|acres?|miles?|inch|hours?|story|stories|car\b|of\b|off\b|price\b|way\b|day\b)", re.I)
_MID_DATE = re.compile(r"(?<=[\w.!?)])\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*-{1,2}\s*(?=[A-Za-z>])")


def _dated_line(line, ctx):
    m = _LINE_DATE.match(line)
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    year = int(m.group(3)) if m.group(3) else None
    rest = line[m.end():].strip()
    if year is None and not m.group(4).strip() and _FRACTION_WORD.match(rest):
        return None                                     # '1/2 bath downstairs' is a fraction, not Jan 2
    d, rule = ctx.place(month, day, year, prefer_past=True)
    if d is None:
        return None
    return d, rule, line[:m.end()].strip(), rest


def split_dated(text, ctx):
    """One running cell -> its dated lines, in order. A line that starts with M/D opens a new entry and the
    lines under it belong to it. Lines above the first dated line are one entry with date None.

    Shapes read as a date: '7/22 - text', '7/27-text', '7/23 --text', '7/27this', '8/3/2026' alone on a
    line with the text underneath, a leading quote mark, a leading bullet, '9/17:text', '10/009'.
    Not a date: '2-3 buyers', '1. When', '1- Any', '24/7', '1/2 bath'.

    Each entry: {date, date_raw, year_rule, text} plus reply_lines (the lines typed with a leading '>',
    which is how the team marks the contact's answer) and mid_line_dates (a second date glued into the
    middle of a line, worth a second look) when there are any."""
    out, cur = [], None
    for raw_line in (text or "").replace("\r", "").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        hit = _dated_line(line, ctx)
        if hit:
            d, rule, date_raw, rest = hit
            cur = {"date": d.isoformat(), "date_raw": date_raw, "year_rule": rule, "_lines": [rest] if rest else []}
            out.append(cur)
        else:
            if cur is None:
                cur = {"date": None, "date_raw": None, "year_rule": None, "_lines": []}
                out.append(cur)
            cur["_lines"].append(line)
    for e in out:
        lines = e.pop("_lines")
        e["text"] = "\n".join(lines)
        replies = [ln.lstrip(">").strip() for ln in lines if ln.startswith(">")]
        if replies:
            e["reply_lines"] = replies
        mids = [m.group(1) for ln in lines for m in _MID_DATE.finditer(ln)]
        if mids:
            e["mid_line_dates"] = mids
    return out


# ---------------------------------------------------------------------------------------------
# "Date & Time" cells
# ---------------------------------------------------------------------------------------------
_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
           "november", "december")
_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_DAY = r"(mon|tues?|wed(?:nes)?|thu(?:rs?)?|fri|sat(?:ur)?|sun)(?:day)?"
_WEEKDAY = re.compile(r"(?<![A-Za-z])" + _DAY + r"(?![A-Za-z])", re.I)


def month_of(word):
    """1 to 12 for a month name, its short form or a near miss ('Septmber'). None otherwise."""
    w = str(word or "").lower().strip(".,")
    if len(w) < 3:
        return None
    for i, name in enumerate(_MONTHS, 1):
        if w == name or w == name[:3] or (i == 9 and w == "sept"):
            return i
    if len(w) < 4:
        return None
    best, score = None, 0.0
    for i, name in enumerate(_MONTHS, 1):
        r = difflib.SequenceMatcher(None, w, name).ratio()
        if r > score:
            best, score = i, r
    if score >= 0.84 or sorted(w) == sorted(_MONTHS[best - 1]):      # one letter off, or two letters swapped
        return best
    return None


def _day_index(word):
    return [d[:3] for d in _WEEKDAYS].index(word.lower()[:3])


def weekday_of(text):
    """0 (Monday) to 6 for the first weekday named in the text, or None."""
    m = _WEEKDAY.search(text or "")
    return _day_index(m.group(1)) if m else None


_MONTH_DAY = re.compile(r"(?<![A-Za-z])([A-Za-z]{3,9})\.?,?\s+(\d{1,2})(?:st|nd|rd|th)?(?![\d:/])(?:,?\s+(\d{4})(?!\d))?")
_NUM_DATE = re.compile(r"(?<![\d/])(\d{1,2})/0*(\d{1,2})(?:/(\d{4}|\d{2}))?(?![\d/])")
_AP = r"([ap])\.?\s?m\.?"
_RANGE = re.compile(r"(?<![\d/:])(\d{1,2})(?::(\d{2}))?\s*(?:" + _AP + r")?\s*(?:-|\u2013|\u2014|\bto\b|\buntil\b)\s*"
                    r"(\d{1,2})(?::(\d{2}))?\s*" + _AP + r"(?![a-z])", re.I)
_ONE_TIME = re.compile(r"(?<![\d/:])(\d{1,2})(?::(\d{2}))?\s*" + _AP + r"(?![a-z])", re.I)


def _clock(h, mm):
    return "%d%s" % (int(h), (":" + mm) if mm and mm != "00" else "")


def time_text(s):
    """'5-6PM' -> '5 to 6 PM', '11AM-1PM' and '11-1PM' -> '11 AM to 1 PM', 'at 6:45 pm' -> '6:45 PM'.
    None when no time is typed."""
    s = s or ""
    m = _RANGE.search(s)
    if m:
        a, b = _clock(m.group(1), m.group(2)), _clock(m.group(4), m.group(5))
        ap1, ap2 = (m.group(3) or "").upper(), m.group(6).upper()
        if not ap1 and int(m.group(1)) % 12 * 60 + int(m.group(2) or 0) > int(m.group(4)) % 12 * 60 + int(m.group(5) or 0):
            ap1 = "A" if ap2 == "P" else "P"            # '10-12PM' runs across noon: 10 AM to 12 PM
        if ap1 and ap1 != ap2:
            return "%s %sM to %s %sM" % (a, ap1, b, ap2)
        return "%s to %s %sM" % (a, b, ap2)
    m = _ONE_TIME.search(s)
    if m:
        return "%s %sM" % (_clock(m.group(1), m.group(2)), m.group(3).upper())
    return None


def _clock_of(dt):
    if not (dt.hour or dt.minute):
        return None
    h = dt.hour % 12 or 12
    return "%d%s %s" % (h, (":%02d" % dt.minute) if dt.minute else "", "AM" if dt.hour < 12 else "PM")


def _dates_in(line, ctx):
    """[(date, rule)] typed in one line: a month name with a day, or M/D forms (there can be two)."""
    for m in _MONTH_DAY.finditer(line):
        mo = month_of(m.group(1))
        if mo:
            d, rule = ctx.place(mo, int(m.group(2)), int(m.group(3)) if m.group(3) else None)
            if d:
                return [(d, rule)]
    out = []
    for m in _NUM_DATE.finditer(line):
        d, rule = ctx.place(int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
        if d:
            out.append((d, rule))
    return out


def parse_when(v, ctx):
    """A showing 'Date & Time' cell or an open house date cell -> a list, one item per date typed.

    A true date cell is exact. Text is read line by line: 'Sept 17, 5-6PM', 'Tuesday, Jul 28th at 11:35 am',
    '7/30/2026 at 7PM', 'Septmber 26, 1:30-4:30PM', '9/19 and 9/20, 1-4PM' (two items), two lines (two
    items), 'Sat 2-4PM' (no date: date None, date_quality 'missing', the weekday kept).
    Each item: {date, date_quality, time_text, weekday, year_rule, raw}."""
    v = clean(v)
    if v is None:
        return []
    if isinstance(v, datetime.datetime):
        return [{"date": v.date().isoformat(), "date_quality": "exact", "time_text": _clock_of(v),
                 "weekday": v.weekday(), "year_rule": "date_cell", "raw": cell_json(v)}]
    if isinstance(v, datetime.date):
        return [{"date": v.isoformat(), "date_quality": "exact", "time_text": None, "weekday": v.weekday(),
                 "year_rule": "date_cell", "raw": v.isoformat()}]
    out = []
    for line in str(v).split("\n"):
        line = line.strip()
        if not line:
            continue
        tt = time_text(line)
        found = _dates_in(line, ctx)
        if not found:
            out.append({"date": None, "date_quality": "missing", "time_text": tt, "weekday": weekday_of(line),
                        "year_rule": None, "raw": line})
        for d, rule in found:
            out.append({"date": d.isoformat(), "date_quality": "exact", "time_text": tt, "weekday": d.weekday(),
                        "year_rule": rule, "raw": line})
    return out


def parse_last_touch(v, ctx):
    """An Email / Call / Text cell -> (dates oldest first, problem or None). The cell normally holds one date
    cell (the latest touch on that channel). Typed text is read too: '10/009', '4/13, 4/15 LVM'."""
    v = clean(v)
    if v is None:
        return [], None
    if isinstance(v, datetime.datetime):
        return [v.date().isoformat()], None
    if isinstance(v, datetime.date):
        return [v.isoformat()], None
    found = sorted(set(d.isoformat() for d, _ in _dates_in(str(v), ctx)))
    return found, (None if found else "no date could be read from %r" % str(v)[:40])


# ---------------------------------------------------------------------------------------------
# open house traffic, typed as prose
# ---------------------------------------------------------------------------------------------
_NUM_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
              "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
              "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}
_UNIT_WORDS = {"group": "groups", "groups": "groups", "party": "parties", "parties": "parties",
               "visitor": "visitors", "visitors": "visitors", "guest": "guests", "guests": "guests",
               "people": "people", "person": "people", "persons": "people", "family": "groups",
               "families": "groups", "couple": "groups", "couples": "groups", "buyer": "people", "buyers": "people"}
_NUM = r"(\d{1,3}|" + "|".join(sorted(_NUM_WORDS, key=len, reverse=True)) + r")"
_UNIT = r"(" + "|".join(sorted(_UNIT_WORDS, key=len, reverse=True)) + r")"
_COUNT = re.compile(r"(?<![\w/$.:])" + _NUM + r"\s+(?:(?:different|separate|total|new)\s+)?" + _UNIT + r"(?![A-Za-z])", re.I)
_ZERO = re.compile(r"(?<![A-Za-z])(no\s*one|nobody|none|zero|no\s+(?:visitors?|guests?|groups?|parties|people|buyers?|traffic|shows?))"
                   r"(?![A-Za-z])(?!\s+(?:wanted|want|was|were|is|are|made|asked|said|left|had|has|of\s+them|interested|seemed))", re.I)
_DAY_LABEL = re.compile(r"^\s*[-*\u2022]?\s*" + _DAY + r"\s*[:\-\u2013\u2014]\s*", re.I)
_COUNT_THEN_DAY = re.compile(r"(?<![\w/$.:])" + _NUM + r"(?:\s+" + _UNIT + r")?"
                             r"(?:\s+(?:came|stopped|walked|dropped)(?:\s+(?:through|by|in))?)?\s+(?:on\s+)?" + _DAY + r"(?![A-Za-z])", re.I)


def _n(word):
    return int(word) if word.isdigit() else _NUM_WORDS[word.lower()]


def count_in_prose(text):
    """(count, unit, phrase) read from a host's recap, or (None, None, None).
    '6 groups, one serious buyer' -> (6, 'groups', '6 groups'); 'only one group came in' -> (1, 'groups', ...);
    'no one came' -> (0, 'visitors', 'no one'). The unit is the host's own word, never converted to people."""
    t = text or ""
    m = _COUNT.search(t)
    if m:
        return _n(m.group(1)), _UNIT_WORDS[m.group(2).lower()], m.group(0)
    m = _ZERO.search(t)
    if m:
        return 0, "visitors", m.group(0)
    return None, None, None


def _split_by_day(text):
    """Per-day pieces of one recap: {weekday index: {text, groups, unit, phrase}} plus the team's own trailing
    note. Reads 'Saturday: no one came / Sunday: two guests' and '2 visitors on saturday, 1 on sunday'."""
    days, team_note, cur = {}, None, None
    lines = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
    if any(_DAY_LABEL.match(ln) for ln in lines):
        for ln in lines:
            m = _DAY_LABEL.match(ln)
            if m:
                cur = _day_index(m.group(1))
                days.setdefault(cur, []).append(ln[m.end():].strip())
            elif cur is not None and re.match(r"^[-*\u2022]\s*\S", ln):
                team_note = ((team_note + " ") if team_note else "") + ln.lstrip("-*\u2022 ").strip()
            elif cur is not None:
                days[cur].append(ln)
        out = {}
        for k, parts in days.items():
            seg = " ".join(p for p in parts if p)
            n, unit, phrase = count_in_prose(seg)
            out[k] = {"text": seg, "groups": n, "unit": unit, "phrase": phrase}
        return out, team_note
    out, last_unit = {}, None
    for m in _COUNT_THEN_DAY.finditer(text or ""):
        unit = _UNIT_WORDS[m.group(2).lower()] if m.group(2) else last_unit
        last_unit = unit or last_unit
        k = _day_index(m.group(3))
        if k not in out:
            out[k] = {"text": None, "groups": _n(m.group(1)), "unit": unit, "phrase": m.group(0)}
    return out, None


def parse_sessions(when_value, recap, ctx, count_value=None, count_unit=None):
    """One open house row -> (sessions, problems). One session per date typed (two dates in a cell are two
    sessions; no date gives one session with date None).

    Each session: {index, date, date_quality, year_rule, time_text, weekday, groups, counted_unit,
    groups_source, count_phrase, text, team_note}. groups keeps three things apart: a number, 0 when the
    host said nobody came, and None when no count is on record. A numeric count column beats the prose."""
    problems = []
    whens = parse_when(when_value, ctx) or [{"date": None, "date_quality": "missing", "time_text": None,
                                             "weekday": None, "year_rule": None, "raw": None}]
    text = clean(recap)
    text = text if isinstance(text, str) else ""
    by_day, team_note = _split_by_day(text)
    whole = count_in_prose(text)
    sessions = []
    for i, w in enumerate(whens):
        s = {"index": i + 1, "date": w["date"], "date_quality": w["date_quality"], "year_rule": w["year_rule"],
             "time_text": w["time_text"], "weekday": w["weekday"], "groups": None, "counted_unit": None,
             "groups_source": "not_recorded", "count_phrase": None, "text": text or None, "team_note": team_note}
        day = by_day.get(w["weekday"]) if w["weekday"] is not None else None
        if day is None and by_day and len(whens) == len(by_day) and all(x["weekday"] is None for x in whens):
            day = by_day[sorted(by_day)[i]]                       # no weekday typed with the dates: pair them in order
        if len(whens) == 1 and len(by_day) <= 1:
            n, unit, phrase = whole
            if n is not None:
                s.update(groups=n, counted_unit=unit, groups_source="parsed_from_prose", count_phrase=phrase)
        elif day is not None:
            if day["text"] is not None:
                s["text"] = day["text"] or None
            if day["groups"] is not None:
                s.update(groups=day["groups"], counted_unit=day["unit"] or "visitors",
                         groups_source="parsed_from_prose", count_phrase=day["phrase"])
        sessions.append(s)
    if len(whens) == 1 and len(by_day) > 1:
        problems.append("the recap names %d days but the date cell gives one session" % len(by_day))
    if len(whens) > 1 and not by_day and whole[0] is not None:
        problems.append("one count (%s) for %d sessions: it could not be split by day" % (whole[2], len(whens)))
    cv = clean(count_value)
    if cv is not None and not isinstance(cv, (datetime.datetime, datetime.date)):
        nums = [int(x) for x in re.findall(r"(?<![\d.])\d{1,3}(?![\d.])", str(cv))]
        if nums and len(nums) == len(sessions):
            for s, n in zip(sessions, nums):
                s.update(groups=n, groups_source="sheet_column", count_phrase=str(cv),
                         counted_unit=count_unit or s["counted_unit"] or "groups")
        elif nums:
            problems.append("the count column holds %d number(s) for %d session(s): left to the recap" % (len(nums), len(sessions)))
        else:
            problems.append("the count column is not a number: %r" % str(cv)[:30])
    return sessions, problems


# ---------------------------------------------------------------------------------------------
# the columns the team is adding (price reaction, interest level, offer intent, next follow-up date)
# ---------------------------------------------------------------------------------------------
_TAG_WORDS = {
    "price_reaction": (
        ("not_raised", r"not[\s_](?:raised|discussed|mentioned|asked|brought)|did\s?n.?t\s+come\s+up|never\s+came\s+up|no\s+(?:comment|mention)|^n/?a$|^none$|^-+$|silent"),
        ("too_high", r"too[\s_]high|over\s?priced|expensive|\bhigh\b|above\s+market|needs?\s+(?:a\s+)?reduc|price\s+(?:cut|drop)"),
        ("fair_or_positive", r"fair|good|^ok(?:ay)?$|fine|reasonable|priced\s+(?:right|well)|great|positive|under\s?priced|\blow\b"),
        ("unknown", r"^unknown$|^\?+$|not\s+sure"),
    ),
    "interest": (
        ("passed", r"pass(?:ed)?\b|not\s+interested|no\s+longer|^no$|^out$|moved\s+on|dead"),
        ("hot", r"\bhot\b|very\s+interested|high|strong|writing"),
        ("warm", r"\bwarm\b|interested|medium|considering|maybe|likes?"),
        ("cold", r"\bcold\b|\blow\b|luke\s?warm|unlikely|browsing"),
        ("unknown", r"^unknown$|^\?+$|not\s+sure|^n/?a$"),
    ),
    "offer_intent": (
        ("no", r"^n(?:o)?$|\bnot\b|will\s+not|won.?t|\bnone\b|pass"),
        ("yes", r"^y(?:es)?$|will\s+write|writing|submitted|offer\s+(?:coming|in)|likely"),
        ("maybe", r"maybe|possibl|considering|thinking|undecided|might|could"),
        ("unknown", r"^unknown$|^\?+$|^n/?a$"),
    ),
}


def read_sheet_tag(kind, value, ctx):
    """(value, problem). Normalises one cell of a tag column to the contract's words. A cell this function
    does not understand gives (None, a short reason) and is left for a person: nothing is guessed."""
    v = clean(value)
    if v is None:
        return None, None
    if kind == "next_followup_date":
        if isinstance(v, datetime.datetime):
            return v.date().isoformat(), None
        if isinstance(v, datetime.date):
            return v.isoformat(), None
        found = _dates_in(str(v), ctx)
        return (found[0][0].isoformat(), None) if found else (None, "next follow-up date not understood: %r" % str(v)[:30])
    if isinstance(v, (datetime.datetime, datetime.date)):
        return None, "%s holds a date" % kind.replace("_", " ")
    s = " ".join(str(v).lower().replace("_", " ").split())
    exact = s.replace(" ", "_")
    allowed = {"price_reaction": C.PRICE_REACTIONS, "interest": C.INTEREST, "offer_intent": C.OFFER_INTENT}[kind]
    if exact in allowed:
        return exact, None
    for key, rx in _TAG_WORDS[kind]:
        if re.search(rx, s):
            return key, None
    return None, "%s not understood: %r" % (kind.replace("_", " "), str(v)[:30])
