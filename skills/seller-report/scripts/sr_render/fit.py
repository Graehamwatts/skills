# -*- coding: utf-8 -*-
"""sr_render.fit: the fit ladder that keeps the email under the size ceiling.

Gmail clips a message near 102 KB, so the email HTML has a hard ceiling of 95,000 bytes. When the email
would pass the target (93,500 bytes), detail steps down one level at a time. The summary on top (the numbers
table, the line under it, the charts, what people are saying) and this week's people are the last things to
shrink: the record half, the pointers, the earlier open house sessions and the one-line entries give way
first. The numbers table and the three price rows are never trimmed, every person keeps an entry in every
list they belong to, and the link copy and the PDF always carry everything.

In the order they give way:

    extras          the optional sections, which give way before anything about people. "full": as built.
                    "short": similar homes nearby keeps what changed and says the rest in one sentence (no
                    table), the chart of online views is left to the complete record (its row in the numbers
                    table stays), and prepared ad channels join the one sentence for channels that are not on
    pointers        "lines": one line per person shown in full under another list. "run": the same people as a
                    run of names in one paragraph
    price_comments  whether every price comment is reprinted in the record (the counts stay on top either way)
    sessions        earlier open house sessions are listed one per line when there are this many or fewer; past
                    it they become one sentence. None lists them all
    table_weeks     latest weeks with a row of their own in "Every week in one table" (older ones in blocks of
                    four, marked data-sr-row="block:a-b"). None gives every week its row
    howcount        "full": every definition. "short": the four a seller needs most, and where the rest are
    line_detail     how much a one-line entry says. 2: the name and brokerage, what they did, where it stands, what
                    they said about price, the last contact. 1: without the brokerage and the last contact.
                    0: the name, where it stands and what they said about price. -1: earlier people as names
                    grouped by where it stands, still one entry each
    weeks           latest weeks with a bar of their own in the week by week chart (older ones in blocks)
    points          rows drawn as bars under "Other points people raised" (the rest become one sentence);
                    half as many, and never fewer than three, under "What people liked"
    days            follow-up days listed in a full entry before the oldest fold into a count
    full            this week's people shown in full in one list; past it they get a one-line entry marked
                    "In touch this week"
"""


def _level(**change):
    base = dict(pointers="lines", price_comments=True, sessions=None, table_weeks=None, howcount="full", line_detail=2,
                weeks=None, points=6, days=10, full=40, extras="short")
    base.update(change)
    return base


FIT_LEVELS = [
    _level(extras="full"),
    _level(pointers="run"),
    _level(pointers="run", price_comments=False),
    _level(pointers="run", price_comments=False, sessions=4),
    _level(pointers="run", price_comments=False, sessions=4, table_weeks=8),
    _level(pointers="run", price_comments=False, sessions=4, table_weeks=8, howcount="short"),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=4, howcount="short"),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=4, howcount="short", line_detail=1),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=4, howcount="short", line_detail=0),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=4, howcount="short", line_detail=-1),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=4, howcount="short", line_detail=-1, weeks=12, points=4, days=6, full=24),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=4, howcount="short", line_detail=-1, weeks=8, points=3, days=4, full=12),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=4, howcount="short", line_detail=-1, weeks=4, points=3, days=3, full=4),
    # A week in which the team reaches nearly everyone on the log (a price change, say) can still be over the
    # ceiling here. These steps let the email finish: fewer of this week's people in full, never fewer entries.
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=2, howcount="short", line_detail=-1, weeks=2, points=3, days=3, full=3),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=2, howcount="short", line_detail=-1, weeks=2, points=3, days=3, full=2),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=2, howcount="short", line_detail=-1, weeks=2, points=3, days=3, full=1),
    _level(pointers="run", price_comments=False, sessions=0, table_weeks=2, howcount="short", line_detail=-1, weeks=2, points=3, days=3, full=0),
]


def size(doc):
    return len(doc.encode("utf-8"))


def fit_email(build, target):
    """Picks the fit level and returns (level, document). build(level) returns the page."""
    level = 0
    doc = build(level)
    while size(doc) > target and level < len(FIT_LEVELS) - 1:
        level += 1
        doc = build(level)
    return level, doc
