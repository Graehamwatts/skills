# -*- coding: utf-8 -*-
"""sr_render.htmlkit: small formatters and the email-safe builders (cells, tables, cards, chips, bars, charts).

Everything is tables with inline styles, because that is what mail clients keep. Every cell states its own
background, so dark mode and Outlook have nothing to guess. A cell states its text color whenever that color
is not the ink the page and every card already set: cells on black, on gold, and any cell given its own
color. (The page has about 400 cells; repeating the same ink on each one cost 5 KB of the 95 KB an email may be.)
"""
import datetime
import html as _html
import re

import sr_contract as C
from .tokens import *        # noqa: F401,F403


def esc(s):
    return _html.escape(str(s), quote=False)


def unesc(s):
    return _html.unescape(s)


def pd(s):
    return s if isinstance(s, datetime.date) else C.parse_date(s)


def md(d):
    return C.fmt_date(d)


def wmd(d):
    return C.fmt_date(d, weekday=True)


def long_day(d):
    return C.fmt_date_long(d)


def money(v):
    return C.fmt_money(v)


def num(v):
    return C.fmt_num(v)


def n_(k, one, many=None):
    return C.fmt_count(k, one, many)


def no_(k, one, many=None):
    return ("no " + (many or one + "s")) if k == 0 else n_(k, one, many)


def join_and(items):
    return C.join_and(items)


def cap1(s):
    return s[:1].upper() + s[1:] if s else s


def low1(s):
    """Lower-cases the first letter unless the word is an acronym ('HOA' stays 'HOA')."""
    return (s[0].lower() + s[1:]) if s[1:2].islower() else s


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def first_sentence(s):
    m = re.match(r"(.+?[.!?])(\s|$)", s or "")
    return m.group(1) if m else (s or "")


def sentences(s):
    return [z for z in re.split(r"(?<=[.!?])\s+", (s or "").strip()) if z]


def hf(size, weight=700, lh=1.25):
    """Heading font. 700 keeps the no-web-font fallback at a plain bold; 800 is for the wordmark, the section
    bars and the large callout numbers."""
    return "font:%d %dpx/%s %s" % (weight, size, lh, F["head"])


def fz(size, lh=1.5, weight=None, color=None):
    s = "font-size:%dpx;line-height:%s" % (size, lh)
    if weight:
        s += ";font-weight:%d" % weight
    if color:
        s += ";color:%s" % color
    return s


TBL = 'role="presentation" cellpadding="0" cellspacing="0"'
DATA = 'cellpadding="0" cellspacing="0"'


def short(col):
    """#AABBCC to #ABC for use inside style attributes (bgcolor attributes always keep six digits)."""
    return ("#" + col[1] + col[3] + col[5]) if (len(col) == 7 and col[1] == col[2] and col[3] == col[4] and col[5] == col[6]) else col


def hk(name, inner):
    """Marks one printed value for the ship gate: <span data-sr="contacted">60</span>. The gate (check_report.py)
    counts the number again from the ledger and compares it with what this element prints."""
    return '<span data-sr="%s">%s</span>' % (name, inner)


def mark(name, value):
    """A data-sr-* attribute for an existing element: section, person, table, col or row."""
    return ' data-sr-%s="%s"' % (name, value)


def sp(h):
    """A vertical gap. The line-height sets it; a zero gap prints nothing."""
    return ('<div style="font-size:1px;line-height:%dpx">&nbsp;</div>' % h) if h else ""


def c(inner, sf="card", w=None, al=None, pad=None, line=False, st="", th=False, span=None, va=None,
      scope="col", bg=None, fg=None, at=""):
    """One table cell. Every cell states its own background, and its text color unless that is the ink a light
    surface inherits from the page and the card it sits in. `at` is extra attributes (hooks)."""
    bgc = bg or P[SURF[sf][0]]
    fgc = short(fg or P[SURF[sf][1]])
    inherits = fg is None and sf in LIGHT
    a = at + ' bgcolor="%s"' % bgc
    if w is not None:
        a += ' width="%s"' % w
    if al and not th and "text-align" not in st:        # a th, or a style that already aligns, needs no attribute
        a += ' align="%s"' % al
    if span:
        a += ' colspan="%d"' % span
    if va:
        a += ' valign="%s"' % va
    s = "" if inherits else "color:%s;" % fgc
    if pad:
        s += "padding:%s;" % pad
    if line:
        s += "border-top:1px solid %s;" % P[SURF[sf][2]]
    if th:
        a += ' scope="%s"' % scope
        s += "text-align:%s;" % (al or "left")
        if "font-weight" not in st:
            s += "font-weight:700;"
    s = (s + st).rstrip(";")
    tag = "th" if th else "td"
    return "<%s%s%s>%s</%s>" % (tag, a, (' style="%s"' % s) if s else "", inner, tag)


LIGHT = ("page", "card", "cream", "tint")       # surfaces whose text is the ink the page already sets


TH_CAPS = "font-size:12px;letter-spacing:.05em;text-transform:uppercase"


def gth(text, w=None, al="left", pad="8px 6px", st=TH_CAPS, va="bottom", at=""):
    """A column head in a gold header row (the CMA table head: black caps on gold)."""
    return c(text, "gold", w=w, al=al, pad=pad, th=True, va=va, st=st, at=at)


def zebra(i):
    """Alternating white and cream rows."""
    return "cream" if i % 2 else "card"


def table(rows, size=None, lh=1.45, data=False, fixed=False, name=None):
    """A full-width table. Dense tables set their type size once here (class tNN repeats it for Outlook).
    `name` marks a table of numbers for the ship gate (scorecard, weeks, periods)."""
    st = []
    if size:
        st.append("font-size:%dpx;line-height:%s" % (size, lh))
    if fixed:
        st.append("table-layout:fixed")
    return '<table %s width="100%%"%s%s%s>%s</table>' % (
        DATA if data else TBL, mark("table", name) if name else "", (' class="t%d"' % size) if size else "",
        (' style="%s"' % ";".join(st)) if st else "", rows)


def dates_compact(ds):
    out, last = [], None
    for d in ds:
        out.append(("%d" % d.day) if (last and last.month == d.month and last.year == d.year) else md(d))
        last = d
    return ", ".join(out)


def green(s):
    return '<b style="color:%s">%s</b>' % (P["good_fg"], s)


def sec(inner, sf="page", top=34, bot=0, name=None):
    """One section of the page: a full-width row. `name` is the section's name for the ship gate."""
    bg, fg = P[SURF[sf][0]], short(P[SURF[sf][1]])
    return ('<tr><td class="g"%s bgcolor="%s" style="padding:%dpx %dpx %s;color:%s">%s</td></tr>'
            % (mark("section", name) if name else "", bg, top, SIZE["gutter"], ("%dpx" % bot) if bot else "0", fg, inner))


def card(inner, sf="card", pad="16px 16px 16px", top=14, border=None, k=True, edge=False, at=""):
    """A rounded card. edge=True adds the CMA gold left edge (used once, on the brief). `at` is extra attributes
    for the card's cell (a hook for the ship gate)."""
    bg, fg = P[SURF[sf][0]], short(P[SURF[sf][1]])
    if edge:
        return (sp(top) + '<table %s width="100%%"%s><tr><td%s bgcolor="%s" style="padding:%s;color:%s;'
                'border:1px solid %s;border-left:5px solid %s;border-radius:%dpx">%s</td></tr></table>'
                % (TBL, ' class="k"' if (k and OPT.get("keep")) else "", at, bg, pad, fg, border or P[SURF[sf][2]], P["gold"], SIZE["radius"], inner))
    # class k keeps a card on one page in print; the email does not need it. k=False is for a long list that
    # has to be able to run over a page.
    return (sp(top) + '<table %s width="100%%"%s><tr><td%s bgcolor="%s" style="padding:%s;color:%s;'
            'border:1px solid %s;border-radius:%dpx">%s</td></tr></table>'
            % (TBL, ' class="k"' if (k and OPT.get("keep")) else "", at, bg, pad, fg, border or P[SURF[sf][2]], SIZE["radius"], inner))


def sheet(inner, top=12, k=True):
    """A square-cornered frame for a table with a gold header row (the CMA table: no rounded corners)."""
    return (sp(top) + '<table %s width="100%%"%s><tr><td bgcolor="%s" style="padding:0;color:%s;border:1px solid %s">%s</td></tr></table>'
            % (TBL, ' class="k"' if (k and OPT.get("keep")) else "", P["white"], P["ink"], P["line"], inner))


def row_cards(make, n, heading="", pad="4px 16px", top=10, first=3):
    """A card for a list of n rows. make(i, is_first) returns the <tr> for item i.
    In print, the heading and the first few rows hold together and the rest may break between rows, so a long
    list neither leaves its heading alone on a page nor jumps to a new page as one block."""
    if not OPT.get("keep") or n <= first + 3:
        return keep(heading + card(table("".join(make(i, i == 0) for i in range(n))), pad=pad, top=top))
    rest = "".join(make(i, i == first).replace("<tr>", '<tr class="k">', 1) for i in range(first, n))
    return (keep(heading + card(table("".join(make(i, i == 0) for i in range(first))), pad=pad, top=top)) +
            card(table(rest), pad=pad, top=8, k=False))


def band_gap(h=30):
    """Cream space above a black band, so the band never sits against the section before it."""
    return '<tr><td height="%d" bgcolor="%s" style="font-size:0;line-height:0">&nbsp;</td></tr>' % (h, P["cream"])


def kicker(text, color=None):
    """A small caps label. Grey on light surfaces; pass gold for a label on black."""
    return ('<div style="%s;letter-spacing:.12em;color:%s">%s</div>'
            % (hf(SIZE["micro"], 700, 1.4), color or P["grey"], esc(text).upper()))


def bar(text):
    """The CMA section header: a black bar with gold caps and a gold left border."""
    return ('<table %s width="100%%"><tr><td width="6" bgcolor="%s" style="font-size:0;line-height:0">&nbsp;</td>'
            '<td bgcolor="%s" style="padding:11px 12px 10px;background:%s;color:%s;%s;letter-spacing:.12em">%s</td></tr></table>'
            % (TBL, P["gold"], P["ink"], P["ink"], P["gold"], hf(SIZE["bar"], 800, 1.3), esc(text).upper()))


def head(kick, title, lede=None, sf="page"):
    """A section opening: the black bar, then the plain-words headline and an optional lede."""
    s = bar(kick)
    if title:
        s += '<h2 class="h2" style="margin:12px 0 0;%s;color:%s">%s</h2>' % (hf(SIZE["h2"] - 1, 700, 1.25), P["ink"], title)
    if lede:
        s += para(lede, SIZE["text"], top=6)
    return keep(s, sf)


def subhead(text, top=16):
    """A small caps label inside a list: This week, Earlier, Shown in full in another list."""
    return sp(top) + kicker(text, P["ink"])


def h3(title, sub=None, top=24, color=None):
    s = sp(top) + '<h3 style="margin:0;%s;color:%s">%s</h3>' % (hf(SIZE["h3"] - 1, 700, 1.3), color or P["ink"], title)
    if sub:
        s += para(sub, SIZE["small"], top=4, color=P["grey"])
    return s


def para(text, size=None, top=8, color=None, weight=None, lh=1.5, at=""):
    return '<p%s style="margin:%dpx 0 0;%s">%s</p>' % (at, top, fz(size or SIZE["text"], lh, weight, color), text)


CHIP = {"offer": ("ink", "gold"), "lean": ("tint", "ink"), "good": ("good_bg", "good_fg"),
        "wait": ("wait_bg", "wait_fg"), "hold": ("hold_bg", "hold_fg")}


def chip(text, kind):
    bg, fg = CHIP[kind]
    return ('<span style="display:inline-block;padding:3px 9px;border-radius:10px;background:%s;color:%s;'
            'font-size:%dpx;line-height:1.4;font-weight:700;letter-spacing:.06em">%s</span>'
            % (P[bg], P[fg], SIZE["micro"], esc(text).upper().replace(" ", "&nbsp;") if len(text) <= 18 else esc(text).upper()))


def button(href, label, sf="dark"):
    """A full-width link, at least 46 px tall: an inline text link is too small a target on a phone."""
    bg, fg = (P["ink"], P["gold"]) if sf == "dark" else (P["white"], P["ink"])
    edge = P["ink"] if sf == "dark" else P["gold_dark"]
    return ('<table %s width="100%%"><tr><td align="center" bgcolor="%s" style="color:%s;border:1px solid %s;border-radius:4px">'
            '<a href="%s" style="display:block;padding:14px 10px;%s;letter-spacing:.06em;color:%s;text-decoration:none">%s</a>'
            '</td></tr></table>' % (TBL, bg, fg, edge, esc(href), hf(SIZE["small"], 700, 1.4), fg, label))


def bar_td(v, vmax, color, w, bg):
    """A bar in a cell w% wide. The bar is a nested one-row table with a fixed height, so it stays the same
    thickness when the row's label wraps, and no border color is needed to thin it. The longest bar stops at
    92% of its cell, so it never touches the edge of the table."""
    wa = (' width="%d%%"' % w) if w else ""
    if not v:
        return '<td%s bgcolor="%s" style="font-size:0">&nbsp;</td>' % (wa, bg)
    return ('<td%s bgcolor="%s" style="font-size:0"><table %s width="%d%%"><tr>'
            '<td height="%d" bgcolor="%s" style="font-size:0;line-height:0">&nbsp;</td></tr></table></td>'
            % (wa, bg, TBL, max(3, int(round(92.0 * v / vmax))), SIZE["bar_h"], color))


def chart(rows, lab_w, series_w, head_row="", name=None):
    """A whole bar chart as one table, so every bar starts on the same line and each value sits in its own
    number column beside its bar.
        rows: ("bar", label, [(value, max, color), ...], options) or ("note", html, options)
              a fourth item in a bar tuple is text printed in place of the number (a figure that is not recorded)
              options: sf (surface), bold, nowrap, fg, pad, at (attributes for the row, a hook for the ship gate)
        series_w: [(number %, bar %), ...]
        head_row: an optional <tr> of column heads placed first.
        name: marks the table for the ship gate (chart, chart_views)."""
    ncol = 1 + 2 * len(series_w)
    out, sized = head_row, False
    wd = lambda k: "" if sized else ' width="%d%%"' % k        # the first bar row sets the column widths for all
    for r in rows:
        o = r[-1]
        sf = o.get("sf", "card")
        if r[0] == "note":
            out += "<tr>%s</tr>" % c(r[1], sf, span=ncol, pad=o.get("pad", "5px 8px"), fg=o.get("fg"), st=o.get("st", ""))
            continue
        label, bars = r[1], r[2]
        bg, fg = P[SURF[sf][0]], short(P[SURF[sf][1]])
        ink = "" if sf in LIGHT else "color:%s;" % fg
        cells = '<td%s bgcolor="%s" style="%spadding:4px 4px 4px 6px%s%s">%s</td>' % (
            wd(lab_w), bg, ink, ";font-weight:700" if o.get("bold") else "",
            ";white-space:nowrap" if o.get("nowrap") else "", label)
        for one, (nw, bw) in zip(bars, series_w):
            v, vmax, color = one[:3]
            shown = ('<span style="font-size:%dpx">%s</span>' % (SIZE["micro"], one[3])) if len(one) > 3 else ("<b>%s</b>" if v else "%s") % num(v)
            cells += '<td%s bgcolor="%s" align="right" style="%spadding-right:6px">%s</td>' % (wd(nw), bg, ink, shown)
            cells += bar_td(v, vmax, color, None if sized else bw, bg)
        sized = True
        out += "<tr%s>%s</tr>" % (o.get("at", ""), cells)
    return '<table %s width="100%%"%s class="t14" style="font-size:14px;line-height:20px">%s</table>' % (
        TBL, mark("table", name) if name else "", out)


def point_row(label, n, den, sub="", first=False, unit="people", hook=None):
    """One point in a tally: the label, 'N of M people' at the right, and under them a table-cell bar drawn to
    scale (N out of M). The cream cell is the track; the gold bar is a nested table of fixed height.
    Two table rows. `sub` is a small line under the label."""
    pct = max(3, min(100, int(round(100.0 * n / den)))) if (n and den) else 0
    top = "0" if first else "10px"
    lab = esc(label) + (('<br><span style="font-size:%dpx;color:%s">%s</span>' % (SIZE["sub"], P["grey"], sub)) if sub else "")
    cnt = '<b%s style="font-size:17px">%s</b> of %s%s' % ((' data-sr="%s"' % hook) if hook else "", num(n), num(den), (" " + unit) if unit else "")
    h = SIZE["point_h"]
    if pct:
        track = ('<td colspan="2" bgcolor="%s" style="font-size:0"><table %s width="%d%%"><tr>'
                 '<td height="%d" bgcolor="%s" style="font-size:0">&nbsp;</td></tr></table></td>' % (P["cream"], TBL, pct, h, P["gold"]))
    else:
        track = '<td colspan="2" height="%d" bgcolor="%s" style="font-size:0">&nbsp;</td>' % (h, P["cream"])
    return "<tr>%s%s</tr><tr>%s</tr>" % (
        c(lab, "card", pad="%s 8px 4px 0" % top, va="top"),
        c(cnt, "card", al="right", pad="%s 0 4px" % top, va="top", st="white-space:nowrap"), track)


def keep(inner, sf="page"):
    """Print only: holds a heading and the block under it on one page. The email does not carry the wrapper."""
    if not OPT.get("keep"):
        return inner
    bg, fg = P[SURF[sf][0]], short(P[SURF[sf][1]])
    # A card inside the wrapper gives up its own keep-together class. Two nested ones strand the heading on a
    # page by itself when the card is too tall for what is left of the page.
    return '<table %s width="100%%" class="k"><tr><td bgcolor="%s" style="color:%s">%s</td></tr></table>' % (
        TBL, bg, fg, inner.replace(' class="k"', ""))


def strip(parts, h=10):
    """A proportion strip: [(value, color)]. Text beside it carries the numbers."""
    tot = float(sum(v for v, _ in parts)) or 1.0
    cells = "".join('<td width="%d%%" height="%d" bgcolor="%s" style="font-size:0;line-height:0">&nbsp;</td>'
                    % (max(2, int(round(100 * v / tot))), h, col) for v, col in parts if v)
    return '<table %s width="100%%"><tr>%s</tr></table>' % (TBL, cells)
