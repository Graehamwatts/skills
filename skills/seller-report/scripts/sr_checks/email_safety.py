# -*- coding: utf-8 -*-
"""sr_checks.email_safety: the email arrives whole and reads the same in Gmail, Apple Mail and Outlook.

Runs on email builds only.
  size            under 95,000 bytes (Gmail clips a message near 102 KB)
  tags            no script, svg, form or other element a mail client strips or blocks
  css             no position, flexbox, grid or background image
  cell_colors     every table cell has a bgcolor, its own or one it sits inside
  images          every image has alt, width and height
  font_size       no text under 12 px
  line_length     no line over 998 characters, or a note that the sender must use quoted-printable
"""
import re

from . import core
from .page import SILENT

MAX_BYTES = 95000
MIN_FONT_PX = 12.0
BAD_TAGS = ("script", "svg", "form", "iframe", "object", "embed", "video", "audio", "canvas", "input", "button",
            "select", "textarea", "base", "frame", "frameset", "applet", "math")
BAD_CSS = (
    ("position", r"(?<![\w-])position\s*:"),
    ("display:flex", r"(?<![\w-])display\s*:\s*(?:inline-)?flex"),
    ("display:grid", r"(?<![\w-])display\s*:\s*(?:inline-)?grid"),
    ("background-image", r"background-image\s*:|background\s*:[^;}]*url\s*\("),
)
KEYWORD_PX = {"xx-small": 9.0, "x-small": 10.0, "small": 13.0, "medium": 16.0, "large": 18.0, "x-large": 24.0, "xx-large": 32.0}
SIZE = re.compile(r"^(\d*\.?\d+)(px|pt|em|rem|%)(?:/.*)?$")


def size_of(style, parent):
    """The font size an element's inline style gives, in px. None when the style does not set one."""
    val = style.get("font-size")
    if val is None and style.get("font"):
        for tok in style["font"].split():
            if SIZE.match(tok) or tok.split("/")[0] in KEYWORD_PX:
                val = tok.split("/")[0]
                break
    if val is None:
        return None
    val = val.strip()
    if val in KEYWORD_PX:
        return KEYWORD_PX[val]
    if val == "smaller":
        return parent * 0.8333
    if val == "larger":
        return parent * 1.2
    mt = SIZE.match(val)
    if not mt:
        return None
    n, unit = float(mt.group(1)), mt.group(2)
    return {"px": n, "pt": n * 4.0 / 3.0, "em": parent * n, "rem": 16.0 * n, "%": parent * n / 100.0}[unit]


def small_text(page, floor=MIN_FONT_PX):
    """[(px, line, text)] for every piece of visible text set under the floor."""
    out = []

    def walk(n, px):
        if n.tag is None:
            t = n.data.replace(core.NBSP, " ").strip()
            if t and px < floor - 0.01:
                out.append((px, n.line, t[:50]))
            return
        if n.tag in SILENT or n.is_hidden():
            return
        own = size_of(n.style, px)
        if own is not None:
            px = own
        elif n.tag in ("small", "sub", "sup"):
            px = px * 0.8333
        for ch in n.children:
            walk(ch, px)

    walk(page.body, 16.0)
    return out


def check(ctx):
    B = core.Bag("email_safety")
    if ctx.kind != "email":
        B.skip("applies", "email checks run on the email build only (this is the %s copy)" % ctx.kind)
        return B.results
    page = ctx.page
    size = len(ctx.raw_bytes)
    if size < MAX_BYTES:
        B.ok("size", "%s bytes, under the %s byte ceiling" % ("{:,}".format(size), "{:,}".format(MAX_BYTES)))
    else:
        B.fail("size", "the email is %s bytes; Gmail clips a message near 102 KB, so the ceiling is %s"
               % ("{:,}".format(size), "{:,}".format(MAX_BYTES)), ["%s bytes over" % "{:,}".format(size - MAX_BYTES + 1)])

    bad = ["<%s> at line %d" % (n.tag, n.line) for n in page.elements if n.tag in BAD_TAGS]
    bad += ["a script inside an HTML comment" for _, c in page.comments if re.search(r"<script\b", c, re.I)]
    bad += ["an on-event attribute (%s) at line %d" % (k, n.line) for n in page.elements for k in n.attrs if k.startswith("on") and len(k) > 3]
    bad += ["a stylesheet or web font link at line %d (%s)" % (n.line, (n.get("href") or "")[:50]) for n in page.elements
            if n.tag == "link" and "stylesheet" in (n.get("rel") or "").lower()]
    B.judge("tags", bad, "no script, svg, form or other element a mail client strips",
            "the email uses an element that mail clients strip or block")

    css = [("style block", page.styles)] + [("line %d" % n.line, n.get("style")) for n in page.elements if n.get("style")]
    css += [("an HTML comment at line %d" % ln, c) for ln, c in page.comments if "<style" in c.lower()]
    bad = []
    for label, pattern in BAD_CSS:
        hits = [where for where, text in css if text and re.search(pattern, text, re.I)]
        if hits:
            bad.append("%s in %d place(s), first at %s" % (label, len(hits), hits[0]))
    if re.search(r"@import|@font-face", page.styles, re.I):
        bad.append("@import or @font-face in the style block (web fonts do not load in Gmail)")
    B.judge("css", bad, "no position, flexbox, grid or background image", "the email uses CSS that mail clients drop")

    bad = []
    for n in page.elements:
        if n.tag in ("td", "th") and not n.get("bgcolor"):
            if not any(a.tag in ("td", "th", "tr", "table") and a.get("bgcolor") for a in n.ancestors()):
                bad.append("<%s> at line %d: '%s'" % (n.tag, n.line, page.flat(root=n)[:40]))
    B.judge("cell_colors", bad, "every table cell has a bgcolor, its own or one it sits inside",
            "a table cell has no background color of its own and none to inherit", limit=8)

    bad = []
    for im in page.images():
        missing = [a for a in ("alt", "width", "height") if not im.has(a)]
        missing += ["%s is not a number of pixels" % a for a in ("width", "height") if im.has(a) and not re.fullmatch(r"\d+", im.get(a).strip())]
        if missing:
            bad.append("the image at line %d: %s" % (im.line, ", ".join("no " + x if " " not in x else x for x in missing)))
    B.judge("images", bad, "every image has alt, width and height (%d image%s)" % (len(page.images()), "" if len(page.images()) == 1 else "s"),
            "an image is missing alt, width or height")

    small = small_text(page)
    bad = ["%.4g px at line %d: '%s'" % x for x in small]
    for mt in re.finditer(r"font(?:-size)?\s*:[^;}]*?(?<![\d.])(\d*\.?\d+)px", page.styles):
        if 1.5 < float(mt.group(1)) < MIN_FONT_PX:
            bad.append("the style block sets %spx: '%s'" % (mt.group(1), core.excerpt(page.styles, mt.start(), mt.end(), 20)))
    B.judge("font_size", bad, "no text under 12 px", "text is set under 12 px", limit=8)

    longest = max([len(ln.rstrip(b"\r")) for ln in ctx.raw_bytes.split(b"\n")] or [0])
    if longest <= 998:
        B.ok("line_length", "the longest line is %d characters (the limit for mail is 998)" % longest)
    else:
        B.warn("line_length", "the longest line is %s characters. Mail allows 998, so the sender must use "
               "quoted-printable or base64 transfer encoding. Never paste this HTML into a raw 7bit or 8bit body"
               % "{:,}".format(longest))
    if not ctx.source.isascii():
        chars = sorted(set(ch for ch in ctx.source if ord(ch) > 127))
        B.info("non_ascii", "the file holds %d kind(s) of non-ASCII character, so it must be sent as UTF-8" % len(chars),
               [", ".join("U+%04X" % ord(c) for c in chars[:12])])
    return B.results
