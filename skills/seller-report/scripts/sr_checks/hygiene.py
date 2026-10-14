# -*- coding: utf-8 -*-
"""sr_checks.hygiene: nothing unfinished, internal or out of place ships.

  no_dashes            no em dash or en dash anywhere a reader could see
  no_placeholders      no TBD, lorem, sample wording, PASTE, {{, unrendered template field or stray None
  links                no empty, '#', relative, http or local link or image address
  no_working_material  no notice, no panel, no word about how the report was made: the page is the seller's alone
  internal_notes       no operator note, field name, contact id or tool name in the seller's text
  link_copy_offers     the link copy carries no offer price, terms, offer agent or list of who may write one
  noindex              the link copy is marked noindex
  email_noindex        the email does not lean on a noindex page for privacy
"""
import os
import re

from . import core
from .ledger_check import recount_of
from .privacy import doc_text

DASH_NAMES = {0x2012: "figure dash", 0x2013: "en dash", 0x2014: "em dash", 0x2015: "horizontal bar"}
DASH_ENTITIES = re.compile(r"&(?:mdash|ndash|horbar|#8211|#8212|#8213|#x2013|#x2014|#x2015);", re.I)
PLACEHOLDERS = (
    ("TBD", r"\b(?:TBD|TBC|TODO|FIXME|XXX+)\b", 0),
    ("confirm the", r"\bconfirm the\b", re.I),
    ("lorem", r"\blorem\b|\bipsum\b", re.I),
    ("sample wording", r"\bsample (?:wording|text|copy|data|report)\b|\(sample\)|\bgraeham writes this\b", re.I),
    ("SAMPLE", r"\bSAMPLE\b", 0),
    ("PASTE", r"\bPASTE\b|\bINSERT\b|\bREPLACE ME\b", 0),
    ("{{", r"\{\{|\}\}|\{%|%\}|\[\[|\]\]|<<|>>", 0),
    ("unrendered field", r"%\(\w+\)[sdr]|(?<![\w%])%[sd](?![\w%])|\$\{[^}]{1,40}\}|\{[a-z_][a-z0-9_.]*\}", 0),
    ("placeholder", r"\bplaceholder\b|\byour[- ](?:link|url|name|text)[- ]here\b|\bexample\.(?:com|org)\b", re.I),
    ("program value", r"\bNaN\b|\bnan%|\bundefined\b|\bnull\b|\bTraceback\b|\b[A-Z][a-z]+Error\b|object at 0x|<built-in"
                      r"|(?:\$|#|No\. ?|Day |Week |of )None\b|\bNone(?:%| of \d| days?\b| follow-ups?\b| repl)", 0),
)
# One build mode: every page is ready to send. None of this may ever be on one.
WORKING_HOOKS = ("draft_notice", "reviewer_panel")
WORKING_WORDS = re.compile(r"\bDRAFT\b|\bMOCKUP\b|not for (?:the|a) seller|for the reviewer|\breviewers?\b|\bunreviewed\b"
                           r"|\btags?\b[^.\n]{0,40}\b(?:reviewed|confirmed|confirm|review)\b|\btag review\b|\b(?:un)?tagged\b|\btagging\b"
                           r"|removed before sending|left out of the final build|\bdo not send\b|\bnot yet confirmed\b", re.I)
OFFER_LEAN = re.compile(r"still deciding|weighing (?:an |the |their |making an )?offer|consider(?:ing|s)? (?:an|making an|writing an) offer"
                        r"|(?:may|might|could|will|plans? to|planned to|planning to|wants? to|wanted to|intends? to|expects? to|preparing to|ready to) "
                        r"(?:write|make|submit|put in|send) an offer|prepared an offer|(?:writing|drafting) (?:up )?an offer"
                        r"|offer (?:is|may be|could be) (?:possible|coming|expected|likely)|leaning toward (?:an|making an|writing an) offer"
                        r"|no word yet on an offer|interested in (?:making|writing) an offer|whether they will write an offer", re.I)
LOCAL_PATH = re.compile(r"(?i)\b[a-z]:[\\/](?:users|documents|temp|windows)\b|file://|\\\\Users\\\\|/Users/[\w.-]+/|\bDocuments[\\/]")
SCHEMES = ("https:", "http:", "mailto:", "tel:", "sms:")


def _dashes(B, ctx):
    text = doc_text(ctx)
    bad = []
    for i, ch in enumerate(text):
        if ord(ch) in DASH_NAMES:
            bad.append("%s in '%s'" % (DASH_NAMES[ord(ch)], re.sub("[%s]" % core.DASH_CHARS, "[dash]", core.excerpt(text, i, i + 1, 30))))
    bad += ["the entity %s in the source" % m.group(0) for m in DASH_ENTITIES.finditer(ctx.source)
            if not any(ord(c) in DASH_NAMES for c in text)]
    B.judge("no_dashes", bad, "no em dash or en dash anywhere in the page", "an em dash or en dash is on the page")


def _placeholders(B, ctx):
    flat = ctx.seller_flat()
    attrs = core.squash(" \n ".join(n.get(a) for n in ctx.page.elements for a in ("alt", "title", "aria-label") if n.get(a)))
    scan = flat + " \n " + attrs + " \n " + ctx.page.title
    # an action the team wrote for next week may open with 'Confirm the ...'. That is copy a person approved.
    planned = [core.fold(s) for s in ctx.ledger.get("next_week") or [] if isinstance(s, str)]
    folded = core.fold(scan)
    bad, ours = [], []
    for label, pattern, flags in PLACEHOLDERS:
        for mt in re.finditer(pattern, scan, flags):
            line = "%s: '%s'" % (label, core.excerpt(scan, mt.start(), mt.end(), 35))
            if label == "confirm the" and any(p and folded.find(p) <= mt.start() < folded.find(p) + len(p) for p in planned if p in folded):
                ours.append(line)
            else:
                bad.append(line)
    for tb in ctx.page.tables():
        for _, cells in tb.rows:
            for c in cells:
                if c.text in ("None", "null", "nan", "NaN", "undefined"):
                    bad.append("a table cell prints the program value '%s' (line %d)" % (c.text, c.node.line))
    B.judge("no_placeholders", sorted(set(bad)), "no placeholder, sample wording or unrendered field in the seller's text",
            "unfinished text is on the page")
    if ours:
        B.info("next_week_wording", "%d next-week item(s) from the ledger say 'confirm the'. Read as an action for the team, "
               "not as a note left for the operator" % len(ours), ours[:4])


def _links(B, ctx):
    email = ctx.kind == "email"
    ids = set(n.get("id") for n in ctx.page.elements if n.get("id")) | set(n.get("name") for n in ctx.page.elements if n.tag == "a" and n.get("name"))
    hard, soft = [], []                     # hard: broken on the page itself. soft: will not work for a seller
    for a in ctx.page.links():
        href = (a.get("href") or "").strip()
        label = ctx.page.flat(root=a)[:40] or "(no text)"
        if not a.has("href"):
            if not a.get("name") and not a.get("id"):
                soft.append("a link with no href: '%s' (line %d)" % (label, a.line))
        elif href in ("", "#") or href.lower().startswith("javascript:"):
            soft.append("href=\"%s\" on '%s' (line %d)" % (href, label, a.line))
        elif LOCAL_PATH.search(href):
            soft.append("a link to a file on this computer: '%s' (line %d)" % (label, a.line))
        elif href.startswith("#"):
            if email:
                soft.append("an in-page anchor in an email, which mail clients drop: href=\"%s\" (line %d)" % (href, a.line))
            elif href[1:] not in ids:
                hard.append("href=\"%s\" points at nothing on the page (line %d)" % (href, a.line))
        elif not href.lower().startswith(SCHEMES):
            soft.append("a relative link: href=\"%s\" on '%s' (line %d)" % (href[:60], label, a.line))
        elif href.lower().startswith("http:"):
            soft.append("an http link (use https): '%s' (line %d)" % (href[:60], a.line))
    for im in ctx.page.images():
        src = (im.get("src") or "").strip()
        if not src:
            hard.append("an image with no src (line %d)" % im.line)
        elif LOCAL_PATH.search(src):
            soft.append("an image read from this computer (line %d)" % im.line)
        elif src.lower().startswith("data:"):
            if email:
                soft.append("an image embedded as data, which Gmail does not show (line %d)" % im.line)
        elif not src.lower().startswith("https:"):
            soft.append("an image address that is not https: '%s' (line %d)" % (src[:60], im.line))
    local = sorted(set(m.group(0) for m in LOCAL_PATH.finditer(ctx.source)))
    if local and not any("this computer" in s for s in soft):
        soft.append("a path on this computer is in the source (%s)" % ", ".join(local[:3]))
    if hard:
        B.fail("links", "a link or image is broken", hard[:12])
    B.judge("links_work", soft, "every link and image address is complete and https (or mailto, tel, sms)",
            "a link or image address will not work for a seller")


def _no_working_material(B, ctx):
    """There is one build mode and no review step. A page never carries a notice on top, a panel at the end,
    or any word about how the report was put together. Text a person reported (it sits in the ledger) is
    left alone."""
    page = ctx.page
    whole = page.text() + " \n " + page.title
    told = core.fold(" \n ".join(s for s in _ledger_strings(ctx.ledger)))
    bad = []
    for hook in WORKING_HOOKS:
        if page.sections(hook):
            bad.append("a block marked data-sr-section=\"%s\" is on the page" % hook)
    if page.metas.get("sr:build"):
        bad.append("the page names a build kind (meta sr:build=%s). There is one build mode" % page.metas.get("sr:build"))
    for mt in WORKING_WORDS.finditer(whole):
        near = core.excerpt(whole, mt.start(), mt.end(), 30)
        if core.fold(mt.group(0)) in told and core.fold(core.excerpt(whole, mt.start(), mt.end(), 12)) in told:
            continue
        bad.append("'%s' in '%s'" % (mt.group(0), near))
    B.judge("no_working_material", sorted(set(bad)), "no notice, no panel and no word about how the report was made",
            "working material is on a page a seller will read")


def _ledger_strings(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k not in ("data_quality", "as_of_note"):
                for x in _ledger_strings(v):
                    yield x
    elif isinstance(node, list):
        for v in node:
            for x in _ledger_strings(v):
                yield x
    elif isinstance(node, str):
        yield node


def _internal(B, ctx):
    flat = ctx.seller_flat()
    folded = core.fold(flat)
    d = ctx.ledger
    notes = [("report.as_of_note", (d.get("report") or {}).get("as_of_note")), ("meta.note", (d.get("meta") or {}).get("note")),
             ("listing.hero_photo_note", (d.get("listing") or {}).get("hero_photo_note")),
             ("listing.status_source", (d.get("listing") or {}).get("status_source"))]
    notes += [("data_quality[%d]" % i, s) for i, s in enumerate(d.get("data_quality") or [])]
    notes += [("price_history[%d].note" % i, e.get("note")) for i, e in enumerate((d.get("listing") or {}).get("price_history") or [])]
    L = ctx.listing or {}
    notes += [("listing.json numbering.note", (L.get("numbering") or {}).get("note")), ("listing.json listing_folder", L.get("listing_folder")),
              ("listing.json sheet.drive_id", (L.get("sheet") or {}).get("drive_id"))]
    bad = []
    for where, note in notes:
        if not note or not isinstance(note, str):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", core.squash(note)):
            f = core.fold(sentence)
            if len(f) >= 24 and f in folded:
                bad.append("%s is printed to the seller: '%s'" % (where, sentence[:70]))
                break
    visible_ids = sorted(set(re.findall(r"(?<![\w/#.])c\d{3,4}(?!\w|\.\w)", flat)))
    if visible_ids:
        bad.append("contact ids are printed: %s" % ", ".join(visible_ids[:6]))
    snake = sorted(set(m.group(0) for m in re.finditer(r"(?<![\w@/.\-])[a-z]{2,}(?:_[a-z0-9]+)+(?![\w@/\-]|\.\w)", flat)))
    if snake:
        bad.append("field names are printed: %s" % ", ".join(snake[:6]))
    # an ad channel can be named after a product ("ChatGPT ads"): its own name, as the ledger has it, is not a tool name
    tools = flat
    for ch in ((ctx.ledger.get("marketing") or {}).get("channels") or []) if isinstance(ctx.ledger.get("marketing"), dict) else []:
        if isinstance(ch, dict) and (ch.get("channel") or "").strip():
            tools = tools.replace(ch["channel"], " " * len(ch["channel"]))
    for mt in re.finditer(r"\bClaude\b|\bChatGPT\b|\bAI[- ]generated\b|\blanguage model\b|\bthe ledger\b|\braw\.json\b|\bledger\.json\b", tools):
        bad.append("'%s' in '%s'" % (mt.group(0), core.excerpt(flat, mt.start(), mt.end(), 30)))
    B.judge("internal_notes", bad, "no operator note, contact id, field name or tool name in the seller's text",
            "internal material is in the text a seller reads")


def _offer_strings(ctx):
    """What the link copy must never carry: [(what, text to look for)]."""
    out = []
    public = set(e.get("price") for e in (ctx.ledger.get("listing") or {}).get("price_history") or [])
    for o in ctx.ledger.get("offers") or []:
        oid = o.get("id") or o.get("date")
        if o.get("price") is not None and o["price"] not in public:      # a full-price offer equals a public list price
            for form in core.money_forms(o["price"]):
                if len(form) >= 6 or form.startswith("$"):
                    out.append(("the price of offer %s" % oid, form))
        if o.get("pct_of_list") is not None:
            for tail in ("of the list price", "of list", "of the asking price", "of asking"):
                out.append(("the percent of list of offer %s" % oid, "%g%% %s" % (o["pct_of_list"], tail)))
        for sentence in re.split(r"(?<=[.;])\s+", core.squash(o.get("terms_summary") or "")):
            if len(sentence) >= 12:
                out.append(("the terms of offer %s" % oid, sentence.rstrip(".;")))
        if o.get("note_safe"):
            out.append(("the note on offer %s" % oid, core.squash(o["note_safe"])))
    return out


def _link_copy(B, ctx):
    if ctx.kind not in ("link", "print"):
        return
    d = ctx.ledger
    m = recount_of(ctx)
    everything = doc_text(ctx)
    low = core.fold(everything)
    flat = ctx.seller_flat()
    bad = []
    # A watched home or a comparable sale can carry the same public price as an offer. Those two sections print
    # public record amounts, each checked against the ledger by its own rule, so an offer price is looked for
    # everywhere else on the page.
    public = ctx.page.sections("nearby") + ctx.page.sections("market")
    low_private = core.fold(ctx.page.text(skip=public)) if public else low
    for what, s in _offer_strings(ctx):
        f = core.fold(s)
        hit = re.search(r"(?<![\w$,.])%s(?![\w,]|\.\d)" % re.escape(f), low_private if what.startswith("the price of offer") else low)
        if hit:
            bad.append("%s is on the page ('%s')" % (what, core.excerpt(low, hit.start(), hit.end(), 20)))
    by_id = dict((c["id"], c) for c in d.get("contacts") or [])
    labels = {}
    for c in d.get("contacts") or []:
        labels.setdefault(c.get("name_short"), []).append(c["id"])
    cards = ctx.page.people()
    writers = set(m["extra"]["offer_people"])
    for o in d.get("offers") or []:
        name = o.get("agent_short") or (by_id.get(o.get("contact_id")) or {}).get("name_short")
        cid = o.get("contact_id")
        if cid and cid in cards:
            bad.append("the agent who wrote offer %s has a card on the page (data-sr-person=%s)" % (o.get("id") or o.get("date"), cid))
        elif name and re.search(r"(?<![\w'])%s(?![\w'])" % re.escape(name), everything):
            twins = [x for x in labels.get(name, []) if x != cid]
            if twins and not cards:
                B.warn("link_copy_offer_agent_twin", "'%s' is printed, and is both an offer agent and another person's label; "
                       "the gate cannot tell which (add data-sr-person)" % name)
            elif not twins or cid in cards:
                bad.append("the agent who wrote offer %s is named on the page" % (o.get("id") or o.get("date")))
    weighing = set(m["extra"]["weighing"]) - writers
    for cid in sorted(weighing):
        c = by_id.get(cid) or {}
        name = c.get("name_short")
        for text in ([ctx.page.flat(root=n) for n in cards.get(cid, [])] if cid in cards else []):
            if re.search(r"\boffers?\b", text, re.I) or OFFER_LEAN.search(text):
                bad.append("the card of a buyer who may be weighing an offer (%s) talks about an offer" % cid)
        if cid not in cards and name and len(labels.get(name, [])) == 1:
            for mt in re.finditer(r"(?<![\w'])%s(?![\w'])" % re.escape(name), flat):
                near = flat[max(0, mt.start() - 120):mt.end() + 220]
                if OFFER_LEAN.search(near):
                    bad.append("offer wording sits beside the name of a buyer who may be weighing one (%s): '%s'"
                               % (cid, core.excerpt(flat, mt.start(), mt.end(), 60)))
                    break
        note = c.get("offer_basis_safe") or ""
        if re.search(r"\boffer", note, re.I) and core.fold(note) in low:
            bad.append("the note on why %s may write an offer is printed" % cid)
    for w in d.get("offer_watch") or []:
        note = w.get("basis_safe") or ""          # a note with no offer wording can also be part of an ordinary comment
        if re.search(r"\boffer", note, re.I) and core.fold(note) in low:
            bad.append("an offer watch note is printed (%s)" % w.get("contact_id"))
    for it in ((d.get("report") or {}).get("since_week_closed") or {}).get("items") or []:
        if (it.get("offer_related") or it.get("kind") == "offer") and it.get("summary_safe") and core.fold(it["summary_safe"]) in low:
            bad.append("a since-the-week-closed note marked offer related is printed (%s)" % it.get("date"))
    for mt in OFFER_LEAN.finditer(flat):
        bad.append("wording about who may write an offer: '%s'" % core.excerpt(flat, mt.start(), mt.end(), 35))
    hidden = [t for t in (d.get("themes_vocabulary") or {}).get("themes") or [] if t.get("hide_in_link_copy")]
    for t in hidden:
        if t["label"].lower() in flat.lower() or ctx.page.hooks("theme:%s" % t["key"]):
            bad.append("the topic row '%s' is printed; it hints at who may write an offer" % t["label"])
    nw = ctx.section_text("next_week")
    if nw is None:                       # no hook: the block under the heading that says 'next week'
        chunks = ctx.page.text(heading_mark="\n<H>").split("<H>")
        nw = core.squash(" ".join(ch for ch in chunks if re.match(r"[^\n]{0,60}\bnext week\b", ch.lstrip(), re.I))) or None
    if nw:
        for cid in sorted(weighing | writers):
            name = (by_id.get(cid) or {}).get("name_short")
            if name and len(labels.get(name, [])) == 1 and re.search(r"(?<![\w'])%s(?![\w'])" % re.escape(name), nw):
                bad.append("the next-week list names %s, who wrote or may write an offer" % cid)
    B.judge("link_copy_offers", sorted(set(bad)),
            "no offer price, percent, terms, offer agent or hint of who may write an offer (%d offers and %d leads in the ledger)"
            % (len(d.get("offers") or []), len(weighing)),
            "the %s copy carries offer details that belong in the email only" % ctx.kind)


def _noindex(B, ctx):
    robots = (ctx.page.metas.get("robots") or "").lower()
    if ctx.kind == "link":
        if "noindex" in robots:
            B.ok("noindex", "the link copy is marked noindex (%s)" % robots)
        else:
            B.fail("noindex", "the link copy has no <meta name=\"robots\" content=\"noindex\">",
                   ["found: %s" % (robots or "no robots meta at all")])
        return
    if ctx.kind != "email":
        return
    flat = ctx.seller_flat()
    bad = ["'%s'" % core.excerpt(flat, mt.start(), mt.end(), 35) for mt in
           re.finditer(r"\bnoindex\b|not indexed|search engines?|\bunlisted\b|private link|hidden from (?:google|search)", flat, re.I)]
    want = ((ctx.manifest or {}).get("flags") or {}).get("link_url")
    record_links = [a for a in ctx.page.links() if re.search(r"complete record|full record|full report|every person", ctx.page.flat(root=a), re.I)]
    for a in record_links:
        href = (a.get("href") or "").strip()
        if want and href != want:
            bad.append("the complete-record link goes to %s, the manifest's link copy is %s" % (href[:70] or "nowhere", want))
    sibling = os.path.join(os.path.dirname(ctx.html_path), "link.html")
    if os.path.isfile(sibling) and os.path.abspath(sibling) != ctx.html_path:
        try:
            with open(sibling, encoding="utf-8", errors="replace") as f:
                head = f.read(6000).lower()
            if not re.search(r"<meta[^>]+name=[\"']robots[\"'][^>]+noindex", head):
                bad.append("the link copy beside this email (link.html) is not marked noindex")
        except OSError:
            pass
    B.judge("email_noindex", bad, "the email does not lean on a noindex page: no wording about search engines, and its "
            "complete-record link (%d found) goes to the link copy" % len(record_links),
            "the email leans on noindex for privacy")


def check(ctx):
    B = core.Bag("hygiene")
    _dashes(B, ctx)
    _placeholders(B, ctx)
    _links(B, ctx)
    _no_working_material(B, ctx)
    _internal(B, ctx)
    _link_copy(B, ctx)
    _noindex(B, ctx)
    return B.results
