#!/usr/bin/env python3
"""skim_test.py: check that a deck's headlines carry the argument on their own.

A reader's first pass over a pitch deck is a skim. They read the largest line
on each slide and little else. This script reads a deck outline, pulls out the
headlines, and tests each one the way that skim does.

Where the headlines come from (the first rule that matches wins):
  1. lines that start with "Headline:", if the file has any;
  2. otherwise a markdown table column named Headline;
  3. otherwise markdown heading lines (lines that start with "#"). A single
     top-level heading above other lines is the document title and is skipped;
  4. otherwise every non-empty line. Table rows are skipped.

For each headline it reports:
  - the word count, against the range for the deck kind;
  - whether it is a bare category title ("The Problem", "Market Size") or
    starts with one ("Problem: ...");
  - whether it contains a ranking word ("first", "only", "best") or a category
    crown ("all-in-one"), which need a prior-art check before they are used;
  - whether it makes a universal claim about other companies ("no other
    tool", "competitors cannot"), which needs the same check;
  - whether it contains a listed consultant word ("leverage", "seamless");
  - whether it reads as a sentence (it has a verb, is not a question, and
    does not just count things, as in "three pillars").

A placeholder in square brackets, such as [NEED: monthly price], counts as one
word and as a number, and nothing inside it is checked. It earns a note,
because a headline with a placeholder is still a draft.

It then prints the headlines in order as one paragraph. That paragraph is the
skim read. A person should read it and ask whether it is the whole argument.

To test a rendered deck, put the largest line of each slide in a text file,
one per line, and run the script on that. For a PDF, deck_inventory.py writes
that file, and a second one holding the first text line of each page.

Exit code 0 when every headline passes, 1 when any headline fails, 2 on a
usage error. Notes never change the exit code.

No third-party packages. Python 3.8 or later.

This is a lint, not a judge. It cannot tell a true claim from a false one, and
its verb check is a word list. Read the skim paragraph yourself.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Word-count limits per deck kind. Outside HARD fails. Outside TARGET is a note.
HARD = {"sent": (5, 14), "application": (5, 14), "live": (3, 10)}
TARGET = {"sent": (8, 12), "application": (8, 12), "live": (4, 8)}
# Usual number of main slides per deck kind. Outside this range is a note.
USUAL_SLIDES = {"sent": (10, 15), "application": (6, 8)}

# Built with chr() so this file stays plain ASCII: em dash, en dash, curly quotes.
LONG_DASHES = (chr(0x2014), chr(0x2013))
CURLY_QUOTES = ((chr(0x2019), "'"), (chr(0x2018), "'"), (chr(0x201C), '"'), (chr(0x201D), '"'))

# A placeholder or a pattern slot: [NEED: monthly price], [count]. Each one is
# swapped for a single neutral token before any check runs.
PLACEHOLDER_RE = re.compile(r"\[[^\[\]]*\]")
SLOT = "NEEDSLOT"

# ---------------------------------------------------------------- categories

FILLER = {
    "the", "our", "a", "an", "and", "of", "to", "for", "in", "on", "your",
    "&", "vs", "versus", "with", "by", "at", "us", "we", "it", "its", "or",
}

LABEL_WORDS = {"why", "how", "what", "who", "this", "now", "next"}

CATEGORY_WORDS = {
    "problem", "problems", "pain", "challenge", "challenges",
    "solution", "solutions", "product", "products", "demo", "features",
    "benefits", "technology", "tech", "platform", "architecture",
    "market", "markets", "size", "sizing", "opportunity", "opportunities",
    "tam", "sam", "som", "timing", "trends",
    "competition", "competitors", "competitor", "competitive", "landscape",
    "analysis", "alternatives", "advantage", "advantages", "differentiation",
    "differentiators", "positioning", "moat",
    "business", "model", "models", "revenue", "pricing", "price", "prices",
    "economics", "unit", "monetization",
    "traction", "growth", "metrics", "milestones", "progress", "proof",
    "validation", "customers", "testimonials", "results", "momentum",
    "team", "founders", "founder", "management", "advisors", "board", "people",
    "ask", "raise", "round", "funding", "funds", "use", "investment",
    "financials", "financial", "projections", "forecast", "forecasts",
    "roadmap", "timeline", "plan", "plans", "vision", "mission", "purpose",
    "strategy", "go", "gtm", "sales", "marketing", "distribution", "channels",
    "overview", "introduction", "intro", "summary", "executive", "agenda",
    "background", "about", "company", "value", "proposition", "cover",
    "title", "close", "closing", "conclusion", "key", "highlights",
    "snapshot", "story", "insight", "insights", "secret", "sauce",
    "contact", "questions", "steps", "status", "update", "details",
    "investor", "investors", "capital", "allocation", "case", "cases",
    "study", "studies", "example", "examples", "pillar", "pillars", "wedge",
    "edge", "magic", "moment", "aha", "thesis", "risk", "risks", "exit",
    "operator", "operators", "efficiency", "gains", "appendix",
}

CATEGORY_PHRASES = {
    "why now", "why us", "why we win", "what we do", "who we are",
    "how it works", "what changed", "what's next", "whats next",
    "where we are", "thank you", "thanks", "any questions", "questions",
    "q&a", "q & a", "contact", "contact us", "get in touch", "next steps",
    "the end", "let's talk", "lets talk", "meet the team",
}

# ------------------------------------------------------- ranking and jargon

# Ranking words and category crowns. Each needs a prior-art check on file
# before it goes on a slide, or a rewrite to the narrower true claim.
RANKING_PATTERNS = [
    # "our first 40 shops", "the first paying customers" and "only 12% pay on
    # time" are not ranking claims. A possessive before "first", or a number or
    # a milestone word after it, is let through.
    r"(?<!our\s)(?<!my\s)(?<!your\s)(?<!their\s)(?<!its\s)first"
    r"(?![-\s](?:\d|(?:paying|outside|customers?|segment|market|year|quarter|"
    r"months?|weeks?|days?|hours?|minutes?|seconds?|time|steps?|meeting|call|"
    r"visit|read|pass|round|hire|version|two|three|four|five|six|seven|eight|"
    r"nine|ten|dozen|hundred|thousand)\b))",
    r"only(?!\s(?:\d|\$|(?:when|after|if|once|because|for|to|on|in|with)\b))",
    r"best", r"leading(?!\sto\b)", r"leader", r"#\s?1",
    r"no\.\s?1", r"number\s(?:one|1)", r"world'?s", r"largest", r"biggest",
    r"fastest", r"cheapest", r"smartest",
    r"most\s(?:advanced|powerful|complete|comprehensive|accurate|trusted)",
    r"unrivall?ed", r"unmatched", r"unparalleled", r"unbeatable",
    r"second\sto\snone", r"one\sof\sa\skind", r"best[-\s]in[-\s]class",
    r"top[-\s](?:rated|ranked|tier|performing|producing|selling)",
    r"premier", r"ultimate", r"category[-\s]defining",
    r"category\sleader", r"pioneer(?:ing|s)?", r"all[-\s]in[-\s]one",
    r"one[-\s]stop", r"operating\ssystem", r"the\sfuture\sof",
]

# A universal claim about other companies is a ranking claim with the ranking
# word taken out: "no other tool does this", "competitors cannot". It says
# something about every rival, so it needs the same prior-art check.
# "Company" is left out: in a headline it usually means the customer.
_RIVAL_NOUNS = (r"(?:tools?|products?|platforms?|systems?|software|vendors?|"
                r"apps?|competitors?|rivals?|alternatives?|solutions?)")
UNIVERSAL_PATTERNS = [
    r"no\sother", r"no\sone\selse", r"nobody\selse", r"nothing\selse",
    r"none\s(?:of\sthem\s)?(?:do|does|can|will)",
    r"every\s(?:other\s)?" + _RIVAL_NOUNS,
    r"no\s(?:direct\s|real\s|true\s|serious\s)?(?:" + _RIVAL_NOUNS + r"|competition)",
    r"(?:competitors?|incumbents?|rivals?|alternatives|"
    r"(?:other|existing|legacy)\s" + _RIVAL_NOUNS + r")\s"
    r"(?:cannot|can't|can\snot|do\snot|don't|does\snot|doesn't|never|won't)",
]

# Consultant words. A reader has seen each of these on a hundred slides, so
# they carry no information. Say the plain thing the word was standing in for.
CONSULTANT_PATTERNS = [
    r"leverag\w*", r"synerg\w*", r"autonomous\w*", r"agentic",
    r"attribution", r"closed[-\s]loop", r"wedge", r"moats?", r"flywheel",
    r"paradigm\w*", r"disrupt\w*", r"revolution\w*", r"seamless\w*",
    r"robust", r"cutting[-\s]edge", r"bleeding[-\s]edge",
    r"state[-\s]of[-\s]the[-\s]art", r"next[-\s]gen(?:eration)?",
    r"world[-\s]class", r"game[-\s]chang\w*", r"turnkey", r"holistic\w*",
    r"end[-\s]to[-\s]end", r"ecosystem", r"unlock\w*", r"empower\w*",
    r"frictionless", r"mission[-\s]critical", r"value[-\s]add\w*",
    r"value\sproposition", r"unit\seconomics", r"ai[-\s](?:powered|driven|native)",
    r"innovati\w*", r"transformati\w*", r"supercharg\w*", r"10x",
    r"best[-\s]of[-\s]breed", r"omnichannel", r"scalable", r"streamlin\w*",
    r"democratiz\w*", r"reimagin\w*", r"utiliz\w*",
    # Not every word that starts with "hyper": hypertension and hyperlink are plain words.
    r"hyper[-\s]?(?:growth|scal\w+|personali[sz]\w*|automat\w+|targeted|local)",
    r"full[-\s]funnel", r"product[-\s]led", r"viral\sloops?", r"lock[-\s]in",
    r"sprawl", r"magic(?:al)?",
    r"(?:intelligence|orchestration|executive|agent|ai|trust)\slayer",
]

# A headline that counts things ("three pillars", "5 reasons") hides its point
# inside a list. The point belongs in the headline.
COUNTED_LIST_RE = re.compile(
    r"^(?:the\s+|our\s+)?(?:\d+|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:\w+\s+)?(?:things|pillars|reasons|ways|steps|keys|principles|benefits|"
    r"features|advantages|pieces|parts|layers|engines|modules)\b", re.I)

# Vague words that usually stand where a number belongs. Notes only.
VAGUE_RE = re.compile(
    r"\b(strong|massive|huge|rapid|rapidly|significant|significantly|explosive|"
    r"tremendous|incredible|exciting)\b", re.I)
UP_TO_RE = re.compile(r"\bup\sto\s\$?\d", re.I)

# ------------------------------------------------------------------- verbs

# Words that are mostly nouns in a headline (invoice, email, schedule, report)
# are left out, so a noun phrase is not mistaken for a sentence. Add one for a
# run with --add-verb when it really is the verb.
VERB_BASES = """
accept achieve add adopt afford agree allow answer approve arrive ask assume
attract automate avoid beat become begin belong bet bill bleed book borrow
break bring build burn bury buy call cancel capture carry catch change charge
chase check choose clean clear climb close collect come compare compete
complete confirm connect consider contain continue convert copy cost cover
create cross cut decide deliver deny depend describe detect develop die
discover double drain draw drive drop earn eat enable end enter exist expect
explain fail fall feel fill find finish fit fix follow forget fund gain
gather generate get give go grow halve handle happen hate hear help hire hit
hold ignore improve include increase inspect install join juggle keep kill
know lack land launch lead learn leave lend let lift like live look lose love
make manage match matter mean meet mention miss move need negotiate notice
open operate order own pay pick plan predict prefer prepare prevent produce
protect prove provide publish pull push put qualify quit raise reach read
receive recover reduce refer refuse reject release rely remain remember
remind remove renew repeat replace reply require resolve respond retain
return rise run rush save say scale see seem select sell send serve set
settle ship show shrink sign sink sit skip slip slow solve speak spend spread
stall stand start stay stick stop struggle submit suffer suggest survive swap
switch take teach tell tend think touch track train treat trim triple trust
try turn understand use verify visit wait want warn waste wear weigh win wish
work worry write leverage unlock empower streamline disrupt transform
feed trace sort
""".split()

# Prefixes that turn a known verb into another verb: reorder, overpay, outgrow.
VERB_PREFIXES = ("re", "over", "under", "out", "un", "pre", "mis", "auto")
VERB_ENDINGS = ("ized", "izes", "ize", "ised", "ises", "ifies", "ified", "ify")

IRREGULAR_VERBS = {
    "is", "are", "was", "were", "be", "been", "am", "has", "have",
    "had", "do", "does", "did", "done", "can", "could", "will", "would",
    "should", "must", "may", "might", "cannot", "lost", "built", "bought",
    "sold", "paid", "sent", "spent", "made", "took", "taken", "got", "gotten",
    "grew", "grown", "ran", "won", "knew", "known", "kept", "held", "left",
    "led", "met", "meant", "went", "gone", "came", "became", "began", "begun",
    "broke", "broken", "brought", "caught", "chose", "chosen", "drove",
    "driven", "fell", "fallen", "felt", "found", "gave", "given", "said",
    "saw", "seen", "shrank", "shrunk", "sat", "stood", "told", "thought",
    "understood", "wrote", "written", "rose", "risen", "spoke", "spoken",
    "beaten", "dies", "goes", "taught", "wore", "worn", "stuck",
    "ate", "eaten", "sank", "sunk", "bled", "burnt", "fed", "tied",
}

# A word before a full stop that does not end a sentence.
ABBREVIATIONS = {
    "vs", "inc", "co", "st", "mr", "mrs", "ms", "dr", "no", "jr", "sr", "ltd",
    "corp", "approx", "est", "etc",
}
TWO_SENTENCES_RE = re.compile(r"([A-Za-z0-9]{2,})[.!?]['\")]?\s+[A-Z]")

CONTRACTION_VERBS = {
    "it's", "that's", "there's", "here's", "what's", "who's", "let's",
    "he's", "she's",
}
CONTRACTION_ENDINGS = ("n't", "'re", "'ve", "'ll", "'d")


def _forms(base: str) -> set:
    """Present and past forms of a verb. Over-generating is harmless here.

    The -ing form is left out on purpose. In a headline it is usually a noun
    or a modifier ("faster ordering for nurseries"), and a line whose only
    verb-like word ends in -ing is a fragment, not a sentence.
    """
    forms = {base}
    if base.endswith("e"):
        forms |= {base + "s", base + "d"}
    elif base.endswith("y") and len(base) > 2 and base[-2] not in "aeiou":
        forms |= {base[:-1] + "ies", base[:-1] + "ied"}
    elif base.endswith(("s", "x", "z", "ch", "sh", "o")):
        forms |= {base + "es", base + "ed"}
    else:
        forms |= {base + "s", base + "ed"}
        if (len(base) >= 3 and base[-1] not in "aeiouwxy"
                and base[-2] in "aeiou" and base[-3] not in "aeiou"):
            forms.add(base + base[-1] + "ed")
    return forms


def build_verbs(extra: list) -> set:
    verbs = set(IRREGULAR_VERBS)
    for base in list(VERB_BASES) + [w.lower() for w in extra]:
        verbs |= _forms(base)
    return verbs


# --------------------------------------------------------------- extraction

HEADLINE_RE = re.compile(
    r"^\s*(?:[-*+]\s+)?[*_]{0,2}headline[*_]{0,2}\s*:\s*[*_]{0,2}\s*(.*)$", re.I)
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
APPENDIX_RE = re.compile(r"^(?:the\s+)?appendix\b", re.I)
RULE_RE = re.compile(r"^\s*([-=_*])\1{2,}\s*$")
SLIDE_PREFIX_RE = re.compile(
    r"^(?:slide\s*)?#?\d{1,2}\s*[.):\-]\s+|^slide\s*#?\d{1,2}\s*$", re.I)
LABEL_SPLIT_RE = re.compile(
    r"^(.{1,40}?)\s*(?::\s|\s[-|]\s|\s?[" + "".join(LONG_DASHES) + r"]\s?)\s*(\S.*)$")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_RULE_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")
# Table columns that hold the headlines, in order of preference. A bare
# "Title" column is left out: a team table has one too.
HEADLINE_COLUMNS = ("headline", "headlines", "slide headline", "slide title")


def clean(text: str) -> str:
    """Strip markdown marks, list markers and slide numbers from a headline."""
    t = text.strip()
    for curly, straight in CURLY_QUOTES:
        t = t.replace(curly, straight)
    t = re.sub(r"^[-*+]\s+", "", t)
    t = re.sub(r"\*\*|__|\*|`", "", t)
    t = t.strip()
    # Drop quotes that wrap the whole line. Leave a quoted word inside it alone.
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"' and t.count('"') == 2:
        t = t[1:-1].strip()
    t = SLIDE_PREFIX_RE.sub("", t).strip()
    return t


def table_headlines(lines: list) -> list:
    """Headlines from a markdown table that has a Headline column."""
    items = []
    col = None          # None: not in a table. -1: in a table with no such column.
    in_appendix = False
    for i, ln in enumerate(lines):
        if not TABLE_ROW_RE.match(ln):
            col = None
            h = HEADING_RE.match(ln)
            if h and APPENDIX_RE.match(clean(h.group(2))):
                in_appendix = True
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if col is None:
            names = [clean(c).lower() for c in cells]
            col = next((names.index(w) for w in HEADLINE_COLUMNS if w in names), -1)
            continue
        if col < 0 or TABLE_RULE_RE.match(ln) or col >= len(cells):
            continue
        if any(APPENDIX_RE.match(clean(c)) for c in cells):
            in_appendix = True
            continue
        items.append({"line": i + 1, "text": clean(cells[col]), "appendix": in_appendix})
    return items


def extract(lines: list) -> tuple:
    """Return (headlines, source). Each headline is a dict."""
    has_headline_lines = any(HEADLINE_RE.match(ln) for ln in lines)
    headings = [(i, HEADING_RE.match(ln)) for i, ln in enumerate(lines)]
    headings = [(i, m) for i, m in headings if m]

    items = []
    in_appendix = False

    if has_headline_lines:
        source = '"Headline:" lines'
        for i, ln in enumerate(lines):
            m = HEADLINE_RE.match(ln)
            h = HEADING_RE.match(ln)
            if h and APPENDIX_RE.match(clean(h.group(2))):
                in_appendix = True
                continue
            if not m:
                continue
            text = clean(m.group(1))
            if APPENDIX_RE.match(text):
                in_appendix = True
                continue
            items.append({"line": i + 1, "text": text, "appendix": in_appendix})
        return items, source

    from_table = table_headlines(lines)
    if from_table:
        return from_table, "a table column"

    # A single top-level heading above other lines is the document title, not
    # a headline. Reading it as the only headline would pass a deck unread.
    title_line = None
    if headings:
        levels = [len(m.group(1)) for _, m in headings]
        body_lines = sum(1 for ln in lines if ln.strip())
        if len(levels) == 1 and levels[0] == 1 and body_lines > 1:
            title_line = headings[0][0]

    if headings and title_line is None:
        source = "markdown headings"
        # One top-level heading above deeper ones is the document title.
        skip_title = levels.count(1) == 1 and levels[0] == 1 and len(levels) > 1
        for n, (i, m) in enumerate(headings):
            if skip_title and n == 0:
                continue
            text = clean(m.group(2))
            if APPENDIX_RE.match(text):
                in_appendix = True
                continue
            items.append({"line": i + 1, "text": text, "appendix": in_appendix})
        return items, source

    table_rows = 0
    for i, ln in enumerate(lines):
        if not ln.strip() or RULE_RE.match(ln) or i == title_line:
            continue
        if TABLE_ROW_RE.match(ln):
            table_rows += 1
            continue
        text = clean(ln)
        if APPENDIX_RE.match(text):
            in_appendix = True
            continue
        items.append({"line": i + 1, "text": text, "appendix": in_appendix})
    source = "one headline per line"
    if title_line is not None:
        source += ", document title skipped"
    if table_rows:
        source += ", %d table rows skipped (no Headline column found)" % table_rows
    return items, source


# ------------------------------------------------------------------- checks

def is_category(text: str) -> bool:
    """True when the text is only a category label, with no claim in it."""
    norm = re.sub(r"[^a-z0-9&' ]+", " ", text.lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    if not norm:
        return False
    if norm in CATEGORY_PHRASES:
        return True
    toks = norm.split()
    if len(toks) > 7:
        return False
    empty = all(t in FILLER or t in CATEGORY_WORDS or t in LABEL_WORDS for t in toks)
    named = any(t in CATEGORY_WORDS or t in LABEL_WORDS for t in toks)
    return empty and named


def count_words(text: str) -> int:
    return sum(1 for tok in text.split() if re.search(r"[A-Za-z0-9]", tok))


def find_patterns(text: str, patterns: list, allow: set) -> list:
    found = []
    low = text.lower()
    for pat in patterns:
        for m in re.finditer(r"(?<![a-z0-9])(?:" + pat + r")(?![a-z0-9])", low):
            word = re.sub(r"\s+", " ", m.group(0)).strip()
            if word not in allow and word not in found:
                found.append(word)
    return found


def has_verb(text: str, verbs: set) -> bool:
    """True when the line holds a word that can act as its verb.

    A word list, not a parser. It leans toward saying yes: a fragment that
    holds a word which can be a verb ("lower costs for clinics") slips through.
    """
    for tok in re.findall(r"[a-z]+(?:[-'][a-z]+)*", text.lower()):
        if tok in verbs or tok in CONTRACTION_VERBS:
            return True
        if tok.endswith(CONTRACTION_ENDINGS):
            return True
        if "-" in tok or tok.endswith("ing"):
            continue
        for prefix in VERB_PREFIXES:
            if tok.startswith(prefix) and tok[len(prefix):] in verbs:
                return True
        if len(tok) >= 5 and tok.endswith(VERB_ENDINGS):
            return True
        if len(tok) >= 6 and tok.endswith("ed"):
            return True
    return False


def looks_title_case(text: str) -> bool:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]*", text)][1:]
    long_words = [w for w in words if len(w) >= 4 and not w.isupper()]
    if len(long_words) < 3:
        return False
    capped = sum(1 for w in long_words if w[0].isupper())
    return capped / len(long_words) >= 0.6


def check_headline(item: dict, mode: str, limits: tuple, verbs: set,
                   consultant: list, allow: set) -> dict:
    text = item["text"]
    fails, notes = [], []
    lo, hi = limits
    t_lo, t_hi = TARGET[mode]

    if not text:
        return {**item, "words": 0, "passed": False, "notes": [],
                "fails": ["no headline text: every slide needs a claim as its largest line"]}

    # Every check below reads the line with each placeholder swapped for one
    # neutral token, so the words inside a placeholder are never judged.
    has_slot = bool(PLACEHOLDER_RE.search(text))
    scan = re.sub(r"\s+", " ", PLACEHOLDER_RE.sub(" %s " % SLOT, text)).strip()

    claim = scan
    bare = is_category(scan)
    if bare:
        fails.append("bare category title: say the point of the slide, not its topic")
    else:
        m = LABEL_SPLIT_RE.match(scan)
        if m and is_category(m.group(1)):
            claim = m.group(2).strip()
            fails.append('starts with the category label "%s": drop it so the claim is '
                         "the largest line" % m.group(1).strip())

    words = count_words(claim)
    counted = "%d word%s" % (words, "" if words == 1 else "s")
    if words < lo:
        fails.append("%s: under the %d-word floor for a claim (target %d to %d)"
                     % (counted, lo, t_lo, t_hi))
    elif words > hi:
        fails.append("%s: over the %d-word ceiling (target %d to %d)"
                     % (counted, hi, t_lo, t_hi))
    elif words < t_lo or words > t_hi:
        notes.append("%s: inside the limit, outside the %d to %d target"
                     % (counted, t_lo, t_hi))

    for word in find_patterns(claim, RANKING_PATTERNS, allow):
        fails.append('ranking word "%s": needs a prior-art check on file, or reword to the '
                     "narrower true claim (--allow \"%s\" if it is not a ranking claim)"
                     % (word, word))
    for word in find_patterns(claim, UNIVERSAL_PATTERNS, allow):
        fails.append('universal claim "%s": a statement about every other company needs '
                     "the same prior-art check as a ranking word, or a reword to the "
                     'narrower true claim (--allow "%s" if it is not about rivals)'
                     % (word, word))
    for word in find_patterns(claim, consultant, allow):
        fails.append('consultant word "%s": say the plain thing it stands for' % word)

    if not bare:
        if claim.rstrip().endswith("?"):
            fails.append("a question, not a claim: state the answer")
        elif COUNTED_LIST_RE.match(claim):
            fails.append("counts things instead of making a point: put the point the "
                         "list is hiding in the headline")
        elif not has_verb(claim, verbs):
            fails.append("no verb found: reads as a label or fragment, not a sentence "
                         "(--add-verb WORD if the verb is real)")

    vague = VAGUE_RE.search(claim)
    if vague:
        notes.append('"%s" stands where a number belongs: give the figure and its '
                     "time window" % vague.group(1).lower())
    if UP_TO_RE.search(claim):
        notes.append('"up to" before a number usually means nobody measured it')
    if any(m.group(1).lower() not in ABBREVIATIONS for m in TWO_SENTENCES_RE.finditer(claim)):
        notes.append("two sentences: a headline is one claim, so pick the one the "
                     "slide is about")
    if has_slot:
        notes.append("placeholder present: still a draft, and it belongs on the "
                     "Numbers to find list")

    if any(d in text for d in LONG_DASHES):
        notes.append("contains a long dash: use a comma or a colon")
    letters = re.sub(r"[^A-Za-z]", "", claim.replace(SLOT, ""))
    if len(letters) >= 8 and letters.isupper():
        notes.append("all capitals: harder to read, and it reads as a label")
    elif looks_title_case(claim):
        notes.append("Title Case reads as a label: use sentence case")

    return {**item, "words": words, "passed": not fails, "fails": fails, "notes": notes}


def run(lines: list, mode: str, limits: tuple, verbs: set, consultant: list,
        allow: set, include_appendix: bool) -> dict:
    items, source = extract(lines)
    main = [it for it in items if include_appendix or not it["appendix"]]
    skipped = len(items) - len(main)

    results = [check_headline(it, mode, limits, verbs, consultant, allow) for it in main]

    seen = {}
    for n, res in enumerate(results, start=1):
        res["n"] = n
        key = re.sub(r"[^a-z0-9]+", " ", res["text"].lower()).strip()
        if key and key in seen:
            res["fails"].append("same headline as slide %d: two slides are making one point"
                                % seen[key])
            res["passed"] = False
        elif key:
            seen[key] = n

    def has_figure(res: dict) -> bool:
        return bool(re.search(r"\d", res["text"]) or PLACEHOLDER_RE.search(res["text"]))

    deck_notes = []
    if len(results) < 3:
        deck_notes.append("Fewer than 3 headlines: too few to carry a thesis.")
    if results and not any(has_figure(r) for r in results):
        deck_notes.append("No headline carries a number. The proof, market and ask "
                          "headlines usually should, if the number is real.")
    if mode in USUAL_SLIDES and len(results) >= 3 and not has_figure(results[-1]):
        deck_notes.append("The last headline carries no number. If that slide is the ask, "
                          "it needs the amount and the milestone.")
    drafts = sum(1 for r in results if PLACEHOLDER_RE.search(r["text"]))
    if drafts:
        deck_notes.append("%d headline(s) hold a placeholder. This is a draft until the "
                          "founder supplies what each one names." % drafts)
    if mode in USUAL_SLIDES and results:
        lo, hi = USUAL_SLIDES[mode]
        if not lo <= len(results) <= hi:
            deck_notes.append("%d main slides: %s decks usually run %d to %d."
                              % (len(results), mode, lo, hi))
    if skipped:
        deck_notes.append("%d appendix headline(s) not checked (--include-appendix to check them)."
                          % skipped)

    skim_parts = []
    for r in results:
        line = r["text"].rstrip(" .;:,")
        if line:
            skim_parts.append(line if line.endswith(("?", "!")) else line + ".")
    skim = " ".join(skim_parts)
    passed = sum(1 for r in results if r["passed"])
    return {
        "mode": mode,
        "source": source,
        "word_limits": {"min": limits[0], "max": limits[1],
                        "target_min": TARGET[mode][0], "target_max": TARGET[mode][1]},
        "headlines": results,
        "skim_read": skim,
        "deck_notes": deck_notes,
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "ok": bool(results) and passed == len(results),
    }


# ------------------------------------------------------------------- output

def print_report(report: dict, name: str) -> None:
    print("Skim test: %s" % name)
    print("Deck kind: %s. Headlines read from: %s. Checked: %d."
          % (report["mode"], report["source"], report["total"]))
    print()
    if not report["headlines"]:
        print("No headlines found. Give one headline per line, start each with "
              '"Headline:" or "#", or put them in a table column named Headline.')
        return
    print(" #  words  result  headline")
    for r in report["headlines"]:
        print("%2d  %5d  %-6s  %s" % (r["n"], r["words"],
                                      "PASS" if r["passed"] else "FAIL",
                                      r["text"] or "(empty)"))
        for msg in r["fails"]:
            print("                   - %s" % msg)
        for msg in r["notes"]:
            print("                   ~ note: %s" % msg)
    print()
    print("Skim read (the headlines in order, as a first-pass reader gets them):")
    print("  " + report["skim_read"])
    print()
    print("Read that paragraph as a stranger would. Does it say what the company")
    print("makes, why it matters, why it is believable, and what is being asked?")
    if report["deck_notes"]:
        print()
        print("Notes:")
        for note in report["deck_notes"]:
            print("  - %s" % note)
    print()
    print("Result: %d of %d headlines pass, %d fail."
          % (report["passed"], report["total"], report["failed"]))


def load_words_file(path: str) -> list:
    words = []
    for ln in Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
        ln = ln.split("#", 1)[0].strip().lower()
        if ln:
            words.append(re.escape(ln).replace(r"\ ", r"\s"))
    return words


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="skim_test.py",
        description=("Check that a pitch deck's headlines carry the argument on their own. "
                     "Reads a markdown or text outline: one headline per line, or lines "
                     'that start with "#" or "Headline:", or a table column named '
                     "Headline."),
        epilog=("Exit code 0 when every headline passes, 1 when any fails, 2 on a usage "
                "error. A line that starts with the word Appendix ends the main run. "
                "Example: python skim_test.py deck-outline.md --mode sent"),
    )
    parser.add_argument("outline", help='path to the outline file, or "-" to read standard input')
    parser.add_argument("--mode", choices=sorted(HARD), default="sent",
                        help="deck kind: sent (read alone, default), live (presented), "
                             "or application (attached to a program application)")
    parser.add_argument("--min-words", type=int, help="override the word-count floor")
    parser.add_argument("--max-words", type=int, help="override the word-count ceiling")
    parser.add_argument("--allow", action="append", default=[], metavar="WORD",
                        help="do not flag this ranking or consultant word (repeatable). Use it "
                             "when the word is not a ranking claim, or its prior-art check is on file")
    parser.add_argument("--words-file", metavar="PATH",
                        help="extra consultant words or phrases to flag, one per line")
    parser.add_argument("--add-verb", action="append", default=[], metavar="WORD",
                        help="a verb the built-in list does not know (repeatable)")
    parser.add_argument("--include-appendix", action="store_true",
                        help="check appendix headlines too (skipped by default)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    if args.outline == "-":
        text, name = sys.stdin.read(), "standard input"
    else:
        path = Path(args.outline)
        if not path.is_file():
            print("skim_test.py: file not found: %s" % args.outline, file=sys.stderr)
            return 2
        text, name = path.read_text(encoding="utf-8-sig", errors="replace"), path.name

    lo, hi = HARD[args.mode]
    lo = args.min_words if args.min_words is not None else lo
    hi = args.max_words if args.max_words is not None else hi
    if lo < 1 or hi < lo:
        print("skim_test.py: --min-words must be at least 1 and no more than --max-words",
              file=sys.stderr)
        return 2

    consultant = list(CONSULTANT_PATTERNS)
    if args.words_file:
        if not Path(args.words_file).is_file():
            print("skim_test.py: words file not found: %s" % args.words_file, file=sys.stderr)
            return 2
        consultant += load_words_file(args.words_file)

    report = run(
        lines=text.splitlines(),
        mode=args.mode,
        limits=(lo, hi),
        verbs=build_verbs(args.add_verb),
        consultant=consultant,
        allow={w.lower().strip() for w in args.allow},
        include_appendix=args.include_appendix,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, name)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
