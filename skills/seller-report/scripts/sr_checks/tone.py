# -*- coding: utf-8 -*-
"""sr_checks.tone: comments are the team's paraphrase, never a quote, never harsh, always labeled.

Graeham's rule: "We don't want to be quoting those kinds of terrible things about someone's home. We can
just say they provided negative feedback and specifically said that the pricing was too high."

  no_quoted_comments   no quote marks around or inside a comment, and no <q> or <blockquote>
  harsh_words          a list of harsh words never appears in the text a seller reads
  voice_phrases        no opener that braces the reader, no "no agenda" phrasing, no apology for the data or tools
  comment_labeled      every comment sits under an "as reported" label
"""
import re

from . import core

DQUOTES = '"' + "".join(chr(c) for c in (0x201C, 0x201D, 0x201E, 0x00AB, 0x00BB))
SQUOTES = "".join(chr(c) for c in (0x2018, 0x2019))
LABEL = re.compile(r"as reported", re.I)
HARSH = (r"terribl[ey]|horribl[ey]|horrific\w*|horrendous\w*|disgust\w*|awful\w*|dump|dumpy|ugl(?:y|ier|iest)|nast(?:y|ier|iest)"
         r"|filth\w*|smell(?:y|ier|iest)|stink\w*|stank|stench|reek\w*|hideous\w*|appalling\w*|atrocious\w*|dreadful\w*|pathetic\w*"
         r"|garbage|trashy|crap\w*|shit\w*|bullshit|sucks?|sucked|junky|dingy|shabby|run-?down|eyesore|nightmare\w*|disaster\w*"
         r"|ridiculous\w*|insane(?:ly)?|laughable|joke|rip-?off|hate[sd]?|hating|worst|gross(?! (?:living|square|sq|rent|income|area|floor|lot))"
         r"|creepy|sketchy|ghetto|slum\w*|depressing|miserable")
REVIEW = (r"dirty|cheap(?:ly)?|cramped|weird|scary|unsafe|messy|noisy|outdated|overpriced|underpriced|neglected|sloppy"
          r"|trash(?! (?:enclosure|pickup|bins?|cans?|area|room|service|collection|chute))")
HEAD = "<H>"                       # stands where a heading starts, so a label can be tied to its block
# cma-generator references\report-build.md Part 3, for client copy: openers that brace the reader for bad news,
# "no agenda" phrasing, and apologies for the data source or the tools. They take the place of the old weekly
# skill's humanizer pass for the sentences Claude writes (the brief, readings, recaps, next week).
VOICE = (r"first of all|let me be (?:honest|clear|straight)|to be (?:blunt|honest|frank)|i(?:'| wi)ll be (?:direct|honest|blunt)"
         r"|real talk|(?:i|we) want to be (?:straight|honest|upfront|up front) with you|no[ -]agenda|no[ -]pressure"
         r"|(?:i|we) like to check in|mls access|(?:was|were) not signed in|public (?:real estate )?data is"
         r"|less precise than|solid estimate rather than")


def comment_strings(ledger, week_end=None):
    """Every piece of comment text in the ledger: [(where, text)]. These are the team's paraphrases."""
    out = []
    for c in ledger.get("contacts") or []:
        if c.get("feedback_safe"):
            out.append(("contacts[%s].feedback_safe" % c["id"], c["feedback_safe"]))
        for i, e in enumerate(c.get("feedback_log") or []):
            if e.get("text_safe"):
                out.append(("contacts[%s].feedback_log[%d]" % (c["id"], i), e["text_safe"]))
        if c.get("offer_basis_safe"):
            out.append(("contacts[%s].offer_basis_safe" % c["id"], c["offer_basis_safe"]))
    for i, o in enumerate(ledger.get("open_houses") or []):
        if o.get("recap_safe"):
            out.append(("open_houses[%d].recap_safe" % i, o["recap_safe"]))
    for i, r in enumerate((ledger.get("pricing_tally") or {}).get("open_house_price_remarks") or []):
        if r.get("remark_safe"):
            out.append(("open_house_price_remarks[%d]" % i, r["remark_safe"]))
    for w in ledger.get("offer_watch") or []:
        if w.get("basis_safe"):
            out.append(("offer_watch[%s].basis_safe" % w.get("contact_id"), w["basis_safe"]))
    return out


def reported_strings(ledger):
    """Comment text plus the follow-up log lines, which can relay what a person answered."""
    out = comment_strings(ledger)
    for c in ledger.get("contacts") or []:
        for i, t in enumerate(c.get("touches") or []):
            if t.get("summary_safe"):
                out.append(("contacts[%s].touches[%d]" % (c["id"], i), t["summary_safe"]))
        if c.get("status_note_safe"):
            out.append(("contacts[%s].status_note_safe" % c["id"], c["status_note_safe"]))
    for i, it in enumerate(((ledger.get("report") or {}).get("since_week_closed") or {}).get("items") or []):
        if it.get("summary_safe"):
            out.append(("since_week_closed[%d]" % i, it["summary_safe"]))
    for i, o in enumerate(ledger.get("offers") or []):
        for k in ("terms_summary", "note_safe"):
            if o.get(k):
                out.append(("offers[%d].%s" % (i, k), o[k]))
    return out


def spans(flat_folded, strings):
    """Where each ledger string is printed: [(start, end, where)] in the folded text."""
    out = []
    for where, s in strings:
        f = core.fold(s)
        if len(f) < 8:
            continue
        i = flat_folded.find(f)
        while i >= 0:
            out.append((i, i + len(f), where))
            i = flat_folded.find(f, i + len(f))
    return out


def inside(pos, span_list):
    return next((w for a, b, w in span_list if a <= pos < b), None)


def check(ctx):
    B = core.Bag("tone")
    flat = ctx.seller_flat()
    folded = core.fold(flat)
    comments = comment_strings(ctx.ledger)
    where = spans(folded, comments)

    # ---- no quote marks around comment text ----------------------------------------------------
    bad = []
    for a, b, w in where:
        before, after = flat[max(0, a - 2):a].rstrip()[-1:], flat[b:b + 2].lstrip()[:1]
        if (before and before in DQUOTES + SQUOTES + "'") and (after and after in DQUOTES + SQUOTES + "'"):
            bad.append("%s is printed inside quote marks: '%s'" % (w, core.excerpt(flat, a, a + 40, 6)))
        elif any(ch in flat[a:b] for ch in DQUOTES):
            bad.append("%s carries quote marks inside the comment: '%s'" % (w, core.excerpt(flat, a, a + 60, 0)))
    for n in ctx.page.elements:
        if n.tag in ("q", "blockquote", "cite"):
            bad.append("<%s> at line %d: '%s'" % (n.tag, n.line, ctx.page.flat(root=n)[:60]))
    for n in ctx.page.hooks("comment"):
        t = ctx.page.flat(root=n)
        if any(ch in t for ch in DQUOTES):
            bad.append("a comment block holds quote marks (line %d): '%s'" % (n.line, t[:70]))
    B.judge("no_quoted_comments", sorted(set(bad)),
            "no comment is printed as a quotation (%d comment texts from the ledger found on the page)" % len(where),
            "comment text is printed as a quotation; comments are the team's paraphrase")
    loose = []
    for mt in re.finditer(r"[%s]([^%s]{12,200})[%s]" % (re.escape(DQUOTES), re.escape(DQUOTES), re.escape(DQUOTES)), flat):
        if len(mt.group(1).split()) >= 3 and not inside(mt.start(), where):
            loose.append("'%s'" % core.excerpt(flat, mt.start(), mt.end(), 10))
    if loose:
        B.warn("quoted_passages", "%d passage(s) in quote marks. Check that none is a buyer's or agent's own words" % len(loose), loose[:6])

    # ---- harsh words --------------------------------------------------------------------------
    bad = ["'%s' in '%s'" % (mt.group(0), core.excerpt(flat, mt.start(), mt.end(), 35))
           for mt in re.finditer(r"(?<![\w'\-])(?:%s)(?![\w'\-])" % HARSH, flat, re.I)]
    B.judge("harsh_words", bad, "no harsh word in the text a seller reads",
            "a harsh word is in the text a seller reads (say what the concern was, without the wording)")
    bad = ["'%s' in '%s'" % (mt.group(0), core.excerpt(flat, mt.start(), mt.end(), 35))
           for mt in re.finditer(r"(?<![\w'\-])(?:%s)(?![\w'\-])" % VOICE, flat.replace("’", "'"), re.I)]
    B.judge("voice_phrases", bad, "no bracing opener, no 'no agenda' phrasing and no apology for the data or the tools",
            "the page braces the reader, says it has no agenda, or apologizes for the data source (report-build.md Part 3)")
    soft = sorted(set("'%s' in '%s'" % (mt.group(0), core.excerpt(flat, mt.start(), mt.end(), 30))
                      for mt in re.finditer(r"(?<![\w'\-])(?:%s)(?![\w'\-])" % REVIEW, flat, re.I)))
    if soft:
        B.warn("blunt_words", "%d blunt word(s) worth a second look before a seller reads them" % len(soft), soft[:8])

    # ---- every comment block carries the 'as reported' label -------------------------------------
    hooked = ctx.page.hooks("comment")
    bad = ["a comment block has no 'as reported' label (line %d): '%s'" % (n.line, ctx.page.flat(root=n)[:60])
           for n in hooked if not LABEL.search(ctx.page.flat(root=n))]
    sections = {}
    for name in ctx.page.section_names():
        sections[name] = core.fold(ctx.section_text(name) or "")
    # the same text with a mark where each heading starts: a label under a heading covers the block below it
    marked = core.squash(ctx.page.text(heading_mark=" %s " % HEAD))
    marked_folded = core.fold(marked)
    seen = 0
    for a, b, w in where:
        seen += 1
        if LABEL.search(flat[max(0, a - 400):a]):
            continue
        piece = folded[a:b]
        if any(piece in t and LABEL.search(t[:max(400, t.find(piece))]) for t in sections.values()):
            continue
        at = marked_folded.find(piece)
        under = False
        while at >= 0 and not under:
            under = bool(LABEL.search(marked[marked.rfind(HEAD, 0, at) + 1:at]))
            at = marked_folded.find(piece, at + 1)
        if under:
            continue
        bad.append("%s is printed with no 'as reported' label near it or under its heading: '%s'" % (w, core.excerpt(flat, a, a + 50, 0)))
    if bad:
        B.fail("comment_labeled", "a comment is printed without the 'as reported' label (%d)" % len(bad), sorted(set(bad))[:10])
    elif seen or hooked:
        B.ok("comment_labeled", "all %d comments found on the page sit under an 'as reported' label" % max(seen, len(hooked)))
    elif comments:
        B.warn("comment_labeled", "none of the ledger's %d comment texts was found word for word, so the label rule "
               "could not be checked (mark comment blocks with data-sr=\"comment\")" % len(comments))
    else:
        B.skip("comment_labeled", "the ledger holds no comment text yet")
    return B.results
