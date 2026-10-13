# -*- coding: utf-8 -*-
"""sr_checks.page: reads a built report page into a small tree the checks can question.

Nothing here knows how the renderer works. It reads HTML the way a mail client would: tags, attributes,
inline styles and text. The stable anchors the renderer is asked to emit are plain attributes:

    data-sr="<id>"            on the smallest element that holds one printed value
    data-sr-section="<name>"  on the element or elements that make up one section
    data-sr-person="<id>"     on a person's card
    data-sr-list="<key>"      on the element that holds the entries of one list under "The details"
    data-sr-entry="<form>:<id>"   on each entry of a list: full, line or pointer, then the contact id
    data-sr-table / -col / -row   on a data table, its column heads and its rows

Standard library only.
"""
import re
from html.parser import HTMLParser

VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
                  "track", "wbr"))
BLOCK = frozenset(("address", "article", "aside", "blockquote", "body", "br", "caption", "center", "dd", "div", "dl",
                   "dt", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav",
                   "ol", "p", "pre", "section", "table", "tbody", "tfoot", "thead", "tr", "ul"))
CELL = frozenset(("td", "th"))
SILENT = frozenset(("style", "script", "title", "head", "template", "noscript"))
# an open tag of the first kind closes an open element of the second kinds (HTML's optional end tags)
IMPLIED_END = {"tr": ("tr", "td", "th"), "td": ("td", "th"), "th": ("td", "th"), "li": ("li",), "p": ("p",),
               "tbody": ("tbody", "thead", "tr", "td", "th"), "thead": ("tbody", "thead", "tr", "td", "th")}
IMPLIED_STOP = frozenset(("table", "ul", "ol", "body", "html"))
NBSP = chr(0xA0)
_WS = re.compile(r"\s+")
_NUM = re.compile(r"(?<![\w.,$#/-])(\d{1,3}(?:,\d{3})+|\d+)(?![\w/]|[.,]\d|%)")


class Node(object):
    __slots__ = ("tag", "attrs", "children", "parent", "line", "data", "_style")

    def __init__(self, tag, attrs=None, parent=None, line=0, data=None):
        self.tag, self.attrs, self.parent, self.line, self.data = tag, attrs or {}, parent, line, data
        self.children, self._style = [], None

    def get(self, name, default=None):
        return self.attrs.get(name, default)

    def has(self, name):
        return name in self.attrs

    @property
    def style(self):
        if self._style is None:
            self._style = parse_style(self.attrs.get("style") or "")
        return self._style

    def iter(self):
        """Every element below this one, in document order."""
        for ch in self.children:
            if ch.tag is not None:
                yield ch
                for x in ch.iter():
                    yield x

    def ancestors(self):
        n = self.parent
        while n is not None:
            yield n
            n = n.parent

    def path(self):
        bits, n = [], self
        while n is not None and n.tag not in (None, "#root"):
            bits.append(n.tag)
            n = n.parent
        return ">".join(reversed(bits[:6]))

    def is_hidden(self):
        st = self.style
        return ("hidden" in self.attrs or st.get("display") == "none" or st.get("visibility") == "hidden"
                or (st.get("max-height") in ("0", "0px") and st.get("overflow") == "hidden"))


def parse_style(text):
    """'color:#333; font-size:12px' -> {'color': '#333', 'font-size': '12px'}. Keys and values in lower case."""
    out = {}
    for part in text.split(";"):
        k, sep, v = part.partition(":")
        if sep and k.strip():
            out[k.strip().lower()] = _WS.sub(" ", v.strip().lower().replace("!important", "").strip())
    return out


class _Builder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]
        self.comments, self.doctype = [], None

    def _open(self, tag, attrs):
        closes = IMPLIED_END.get(tag)
        if closes:
            for i in range(len(self.stack) - 1, 0, -1):
                t = self.stack[i].tag
                if t in closes:
                    del self.stack[i:]
                    break
                if t in IMPLIED_STOP or t in CELL and tag not in CELL and tag != "tr":
                    break
        node = Node(tag, dict((k.lower(), "" if v is None else v) for k, v in attrs), self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)
        return node

    def handle_starttag(self, tag, attrs):
        node = self._open(tag, attrs)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(Node(None, parent=self.stack[-1], line=self.getpos()[0], data=data))

    def handle_comment(self, data):
        self.comments.append((self.getpos()[0], data))

    def handle_decl(self, decl):
        self.doctype = decl


class Cell(object):
    __slots__ = ("node", "text", "span", "col")

    def __init__(self, node, text, span, col):
        self.node, self.text, self.span, self.col = node, text, span, col


class Table(object):
    """One <table>: rows of cells. A cell's text includes any table nested inside it."""

    def __init__(self, node, page):
        self.node, self.rows = node, []
        for tr in _rows_of(node):
            cells, col = [], 0
            for ch in tr.children:
                if ch.tag in CELL:
                    try:
                        span = max(1, int(ch.get("colspan") or 1))
                    except ValueError:
                        span = 1
                    cells.append(Cell(ch, squash(page.text(root=ch)), span, col))
                    col += span
            self.rows.append((tr, cells))

    @property
    def name(self):
        return self.node.get("data-sr-table")

    def width(self):
        return max([c.col + c.span for _, cells in self.rows for c in cells] or [0])


def _rows_of(table):
    for ch in table.children:
        if ch.tag == "tr":
            yield ch
        elif ch.tag in ("tbody", "thead", "tfoot"):
            for g in ch.children:
                if g.tag == "tr":
                    yield g


def squash(s):
    return _WS.sub(" ", (s or "").replace(NBSP, " ")).strip()


def numbers_in(text):
    """Whole numbers printed in a piece of text, as ints. '1,176 sq ft on 3 days' -> [1176, 3].
    A number glued to a letter, a currency sign, a percent sign or a decimal point is not counted."""
    return [int(m.group(1).replace(",", "")) for m in _NUM.finditer(text or "")]


class Page(object):
    def __init__(self, source):
        self.source = source
        b = _Builder()
        b.feed(source)
        b.close()
        self.root, self.comments, self.doctype = b.root, b.comments, b.doctype
        self.elements = list(self.root.iter())
        self.head = next((n for n in self.elements if n.tag == "head"), None)
        self.body = next((n for n in self.elements if n.tag == "body"), None) or self.root
        t = next((n for n in self.elements if n.tag == "title"), None)
        self.title = squash("".join(c.data for c in t.children if c.tag is None)) if t is not None else ""
        self.metas = {}
        for n in self.elements:
            if n.tag == "meta" and (n.get("name") or n.get("property")):
                self.metas.setdefault((n.get("name") or n.get("property")).lower(), n.get("content") or "")
        self.styles = "\n".join("".join(c.data for c in n.children if c.tag is None)
                                for n in self.elements if n.tag == "style")
        self._tables = None

    # -- text ---------------------------------------------------------------------------------
    def text(self, root=None, skip=(), hidden=True, heading_mark=None):
        """Readable text under root (the body by default). Blocks and table rows end with a newline, cells
        are separated by a space. Hidden elements (the preheader) are included unless hidden=False, because an
        inbox preview shows them. Nodes in `skip` are left out with everything under them. heading_mark, when
        given, is written where each h1 to h6 starts."""
        out, skip = [], set(id(n) for n in skip)

        def walk(n):
            if n.tag is None:
                out.append(n.data.replace(NBSP, " "))
                return
            if n.tag in SILENT or id(n) in skip or (not hidden and n.is_hidden()):
                return
            if heading_mark and n.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                out.append(heading_mark)
            if n.tag == "br":
                out.append("\n")
                return
            if n.tag == "img":
                return
            brk = n.tag in BLOCK
            if brk:
                out.append("\n")
            elif n.tag in CELL:
                out.append(" ")
            for ch in n.children:
                walk(ch)
            out.append("\n" if brk else (" " if n.tag in CELL else ""))

        walk(root if root is not None else self.body)
        lines = [_WS.sub(" ", ln).strip() for ln in "".join(out).split("\n")]
        return "\n".join(ln for ln in lines if ln)

    def flat(self, root=None, skip=()):
        return squash(self.text(root=root, skip=skip))

    def hidden_text(self):
        return squash(" ".join(self.text(root=n) for n in self.elements
                               if n.is_hidden() and not any(a.is_hidden() for a in n.ancestors())))

    # -- hooks --------------------------------------------------------------------------------
    def hooks(self, name):
        return [n for n in self.elements if n.get("data-sr") == name]

    def hook_names(self):
        return sorted(set(n.get("data-sr") for n in self.elements if n.has("data-sr")))

    def sections(self, name):
        return [n for n in self.elements if n.get("data-sr-section") == name]

    def section_names(self):
        return sorted(set(n.get("data-sr-section") for n in self.elements if n.has("data-sr-section")))

    def people(self):
        """{contact id: [card nodes]} from data-sr-person, and from data-sr-entry="<form>:<id>"."""
        out = {}
        for n in self.elements:
            if n.has("data-sr-person"):
                out.setdefault(n.get("data-sr-person"), []).append(n)
            elif n.has("data-sr-entry"):
                cid = n.get("data-sr-entry").partition(":")[2]
                if cid:
                    out.setdefault(cid, []).append(n)
        return out

    def entries(self):
        """{list key: [(form, contact id or '', node)]} for every data-sr-entry, in page order. The list key is
        the nearest data-sr-list above the entry (None when an entry sits outside every list)."""
        out = {}
        for n in self.elements:
            if n.has("data-sr-entry"):
                form, _, cid = n.get("data-sr-entry").partition(":")
                key = next((a.get("data-sr-list") for a in n.ancestors() if a.has("data-sr-list")), None)
                out.setdefault(key, []).append((form, cid, n))
        return out

    def within(self, node, name):
        """True when node sits inside a section of that name."""
        return any(a.get("data-sr-section") == name for a in [node] + list(node.ancestors()))

    def section_of(self, node):
        for a in [node] + list(node.ancestors()):
            if a.has("data-sr-section"):
                return a.get("data-sr-section")
        return None

    # -- tables -------------------------------------------------------------------------------
    def tables(self):
        if self._tables is None:
            self._tables = [Table(n, self) for n in self.elements if n.tag == "table"]
        return self._tables

    def named_table(self, name):
        return [t for t in self.tables() if t.name == name]

    # -- attributes ---------------------------------------------------------------------------
    def links(self):
        return [n for n in self.elements if n.tag == "a"]

    def images(self):
        return [n for n in self.elements if n.tag == "img"]
