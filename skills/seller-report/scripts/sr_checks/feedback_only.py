# -*- coding: utf-8 -*-
"""sr_checks.feedback_only: the report says what people said and what was done. It never advises on price.

Graeham's rule: "The system shouldn't do anything in regards to that. The system should only provide
feedback." So the generated copy holds no recommendation, no suggested number, no "My recommendation"
block, no "From you this week" ask and no decision log. It also adds no line about what silence on price
means, in either direction.

Two things can soften a hit:
  as reported     the wording sits inside a comment or log line from the ledger (a buyer's agent asked
                  about a lower price, say). That is feedback, so it is a warning for a person to read.
  brief override  Graeham wrote his own brief. The operator hands the gate the exact text
                  (--brief-override-file) or the renderer marks it (data-sr-section="brief_override"), and
                  confirms with --confirm-brief-override. Without the confirmation it is still a failure.
"""
import re

from . import core
from . import tone

RECOMMEND = (
    ("recommend", r"recommend\w*"),
    ("should reduce", r"should (?:reduce|lower|drop|cut|adjust|change|revisit|consider|think about|talk about)"),
    ("price reduction", r"price (?:reduction|reductions|drop|drops|cut|cuts|adjustment|adjustments|improvement|correction)"),
    ("reduce the price", r"reduc(?:e|es|ed|ing) (?:the |your |our |list )*price"),
    ("lower the price", r"lower(?:s|ed|ing)? (?:the |your |our |list )*price"),
    ("drop the price", r"drop(?:s|ped|ping)? (?:the |your |our |list )*price"),
    ("adjust the price", r"adjust(?:s|ed|ing)? (?:the |your |our |list )*price"),
    ("reposition", r"re-?position\w*"),
    ("bring the price down", r"(?:bring|bringing|brought|move|moving|take|taking) the (?:list )?price down"
                             r"|com(?:e|ing) down on (?:the )?price|price (?:needs to|has to|should|must) come down"),
    ("talk about price", r"(?:talk|speak|meet|sit down|conversation) (?:with you )?about (?:the |your )?(?:price|pricing)"),
    ("where the price should", r"(?:price|pricing) (?:should|needs to|ought to|has to|must)\b|where the price should"),
    ("priced right or wrong", r"priced (?:right|correctly|well|too high|too low|aggressively|above|below)"),
    ("advice", r"\b(?:my|our) (?:advice|suggestion|opinion|view)\b|\bI (?:suggest|advise|propose|would suggest|would advise|would like to)\b"
               r"|\bwe (?:suggest|advise|propose)\b"),
    ("time to act on price", r"time to (?:revisit|review|rethink|reconsider|look at|talk about) (?:the |your )?(?:price|pricing)"
                             r"|(?:revisit|rethink|reconsider) (?:the |your )?(?:list )?price|pric(?:e|ing) strategy"),
)
BLOCKS = (
    ("My recommendation block", r"\bmy recommendation\b"),
    ("From you ask", r"\bfrom you(?: this week)?\s*:|\bfrom you this week\b|\bwhat (?:I|we) need from you\b"),
    ("decision log", r"\bdecision log\b|\bdecisions? on (?:the )?price\b|\bwhat we decided\b"),
)
SILENCE = (
    r"tells? us nothing", r"says? nothing about (?:the )?price", r"not a view on (?:the )?price",
    r"does not mean (?:that )?(?:buyers|they|anyone|people|the price)", r"doesn't mean (?:that )?(?:buyers|they|anyone|people|the price)",
    r"(?:nobody|no one|none of them) (?:thinks|think|said|says|felt|feels|volunteered|complained|objected)",
    r"silence (?:on|about) (?:the )?price", r"no (?:complaints?|objections?|pushback) (?:about|on|to) (?:the )?price",
    r"price (?:is|was) (?:not|n't) (?:an issue|a concern|a problem|the problem|the issue)",
    r"(?<!said the )(?<!say the )(?<!says the )price (?:is|seems|looks|appears) (?:right|fine|well received|about right)",
    r"(?:which|that) (?:means|suggests|tells us|shows) (?:the price|buyers|price)",
    r"good (?:sign|news) (?:on|for|about) (?:the )?price", r"cannot be read (?:as|either way)",
    r"\bpric(?:e|ing)\b[^.]{0,60}\beither way\b",
)
FORBIDDEN_SECTIONS = ("recommendation", "decision_log", "seller_ask", "from_you")


def _exempt_spans(ctx, folded):
    """Spans of the operator-confirmed brief override. Returns (spans, what was offered, confirmed)."""
    texts = []
    for n in ctx.page.sections("brief_override"):
        texts.append(ctx.page.flat(root=n))
    for t in ctx.opts.get("brief_override_text") or []:
        texts += [p for p in re.split(r"\n\s*\n", t) if p.strip()]
    out = []
    for t in texts:
        f = core.fold(t)
        if len(f) < 8:
            continue
        i = folded.find(f)
        while i >= 0:
            out.append((i, i + len(f), "brief override"))
            i = folded.find(f, i + len(f))
    return out, texts, bool(ctx.opts.get("confirm_brief_override"))


def check(ctx):
    B = core.Bag("feedback_only")
    flat = ctx.seller_flat()
    folded = core.fold(flat)
    reported = tone.spans(folded, tone.reported_strings(ctx.ledger))
    override, offered, confirmed = _exempt_spans(ctx, folded)

    def sort(hits):
        """(blocking, as reported, under the override) for a list of (label, match)."""
        block, rep, ovr = [], [], []
        for label, mt in hits:
            line = "%s: '%s'" % (label, core.excerpt(flat, mt.start(), mt.end(), 40))
            if tone.inside(mt.start(), override):
                (ovr if confirmed else block).append(line + ("" if confirmed else "  [in the brief override, which the operator has not confirmed]"))
            elif tone.inside(mt.start(), reported):
                rep.append(line + "  [inside %s]" % tone.inside(mt.start(), reported))
            else:
                block.append(line)
        return block, rep, ovr

    hits = [(label, mt) for label, pattern in RECOMMEND for mt in re.finditer(r"(?<![\w'])(?:%s)" % pattern, flat, re.I)]
    block, rep, ovr = sort(hits)
    B.judge("no_recommendation", block, "the generated copy holds no recommendation or price advice",
            "recommendation wording in the generated copy (the report gives feedback only)")
    if rep:
        B.warn("price_talk_as_reported", "%d place(s) where a person's reported remark talks about lowering the price. "
               "That is feedback, shown as reported. Read each one" % len(rep), rep[:8])
    if ovr:
        B.info("brief_override", "%d phrase(s) allowed because the operator confirmed Graeham wrote this brief himself"
               % len(ovr), ovr[:8])
    elif offered and confirmed:
        B.info("brief_override", "a brief override was confirmed; it holds no recommendation wording")
    elif offered and not confirmed:
        B.info("brief_override", "the page carries a brief override that the operator has not confirmed "
               "(--confirm-brief-override). Recommendation wording in it counts as a failure")

    hits = [(label, mt) for label, pattern in BLOCKS for mt in re.finditer(pattern, flat, re.I)]
    block, rep, ovr = sort(hits)
    block += ["a section marked data-sr-section=\"%s\"" % s for s in FORBIDDEN_SECTIONS if ctx.page.sections(s)]
    B.judge("no_advice_blocks", block + rep, "no 'My recommendation' block, no 'From you' ask and no decision log",
            "the page carries a block the feedback-only rule removed")

    hits = [("reads meaning into silence on price", mt) for pattern in SILENCE for mt in re.finditer(pattern, flat, re.I)]
    block, rep, ovr = sort(hits)
    B.judge("no_reading_of_silence", block, "no line says what silence on price means, in either direction",
            "a line explains what it means that people did not bring up price (state the counts and stop)")

    number = []
    for mt in re.finditer(r"(?:at|to|around|near|under|below|closer to) \$\d[\d,]*(?:K|k|M)?(?: or (?:less|lower|below))?"
                          r"(?=[^.]{0,60}\b(?:would|could|should|might) (?:sell|move|bring|draw|get|attract|work))", flat, re.I):
        if not tone.inside(mt.start(), reported) and not (confirmed and tone.inside(mt.start(), override)):
            number.append("'%s'" % core.excerpt(flat, mt.start(), mt.end(), 50))
    B.judge("no_suggested_number", number, "no sentence suggests a price",
            "a sentence suggests what price would work")
    return B.results
