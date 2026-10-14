# -*- coding: utf-8 -*-
"""sr_render.tokens: every color, font, size, limit and fixed phrase the report uses.

The look is Graeham's CMA system (cma-generator/references/dashboard_template.html and branding.md):
near-black, gold, cream, white cards, Montserrat for headings, Inter for body. Change a value here and
the whole report follows. No brand fact (name, DRE, phone) is typed in this package: those are read
from identity.json at run time.
"""
import re

import sr_contract as C

# The six brand colors, then the supporting tones that sit between them.
P = dict(
    ink="#1A1A1A", gold="#C5A55A", gold_dark="#A88B3D", cream="#F5EFDC", grey="#666666", white="#FFFFFF",
    tint="#EBDCAE",                 # this week's row: gold let down with white, darker than cream
    line="#E2DAC2",                 # hairlines on white and cream
    dark_line="#3A3A3A",            # hairlines on black
    on_dark="#FFFFFF", on_dark_soft="#DDDDDD",
    good_bg="#E3F0E8", good_fg="#225A3C", wait_bg="#F9E3D6", wait_fg="#8A3A12",
    hold_bg="#ECECEC", hold_fg="#4A4A4A",
)
# Web fonts do not load in Gmail, so each stack ends in fonts every phone has.
F = dict(
    head="Montserrat,Arial,sans-serif",        # kept short: this stack is repeated on every heading and label
    body="Inter,-apple-system,'Segoe UI',Roboto,Arial,sans-serif",
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Montserrat:wght@700;800&display=swap",
)
# surface name -> (background token, text token, hairline token)
SURF = {
    "page": ("cream", "ink", "line"), "card": ("white", "ink", "line"), "cream": ("cream", "ink", "line"),
    "tint": ("tint", "ink", "line"), "dark": ("ink", "on_dark", "dark_line"), "gold": ("gold", "ink", "gold_dark"),
}
SIZE = dict(maxw=680, gutter=16, gutter_wide=32, lede=17, body=16, text=15, small=14, sub=13, micro=12,
            h1=27, h2=21, h3=18, radius=8,
            bar=15,                     # section header bar: gold caps on black
            stat=30,                    # the large gold numbers in a black callout
            wordmark=22, issue_no=20,   # the wordmark is the largest text in the masthead band
            hero_h=220, bar_h=12,       # masthead photo slot is 680 x 220; chart bars are a fixed 12 px tall
            point_h=8,                  # the bar under each point in "What people are saying"
            print_maxw=780)             # column width of the print layout (Letter, 11 mm margins, printed at 90%)
# 12 px (micro) is for letter-spaced caps labels, chips and table heads only. Ordinary secondary text is 13 px
# (sub) or larger. Nothing on the page is under 12 px.
LIMITS = dict(
    max_bytes=C.LIMITS["email_max_bytes"],      # hard ceiling for the email HTML (Gmail clips near 102 KB)
    fit_target=93500,        # the fit ladder steps down until the email is at or under this (a photo, a button and a greeting fit in the rest)
    lead_fresh_days=C.LIMITS["offer_lead_fresh_days"],
    quiet_days=C.LIMITS["quiet_days"],
    tries_flag=C.LIMITS["tries_flag"],
    names_behind_count=3,    # the numbers table prints the names behind a count this small
    tap_px=40,               # every link is at least this tall
)
DOT = " · "
WORDS_BANNED = ["delve", "leverage", "seamless", "robust", "it's worth noting", "tapestry", "testament"]
# The report gives feedback only. None of these may appear in copy the generator writes.
FEEDBACK_ONLY_BANNED = ["recommend", "from you:", "tells us nothing", "tell us nothing", "nobody thinks", "no one thinks",
                        "is not the same as buyers agreeing", "we suggest", "should consider", "price reduction",
                        "reduce the price", "lower the price"]

# Link copy: what counts as saying who may be weighing an offer.
#   OFFER_INTENT drops a sentence from anyone's notes. OFFER_ANY is the wider rule for people read as weighing
#   an offer or having written one, and for the next-week list.
OFFER_INTENT = re.compile(
    r"\ban offer\b|\b(his|her|their|another|a second|the buyer's|the client's) offer\b"
    r"|\b(mak\w*|made|writ\w*|wrote|prepar\w*|submit\w*|expect\w*|send\w*|sent)\s+(an?|the|their|his|her|another)\s+offers?\b"
    r"|\boffer\s+(could|would|might|may)\s+include\b|\bweighing\b|\bstill deciding\b|\boriginal list price\b", re.I)
OFFER_ANY = re.compile(r"\boffers?\b|\bcounter(ed|s)?\b", re.I)
OFFER_MASK = "an agent with an offer on file"
BOILER = re.compile(
    r"^(sent an? (follow-up )?(text|email)\.?|called, no answer\.?( left a voicemail\.?)?|called\. the call did not connect\.?"
    r"|called\. no answer, so we left a voicemail\.?|called again\.?|called\.?)( no note was kept\.?)?$", re.I)
ASIDES = [re.compile(r"\s*Our team's read[^.]*\."), re.compile(r"\s*No note was kept\.")]

PRICE_ROWS = [(r["key"], r["label"]) for r in C.themes_vocabulary()["price_rows"]]
PRICE_TAG = dict(PRICE_ROWS)
INTEREST_TAG = {"hot": "Strong interest", "warm": "Interested", "cold": "Undecided", "passed": "Passed"}
OFFER_STATE = {"received": "Received", "countered": "Countered", "accepted": "Accepted", "declined": "Declined",
               "withdrawn": "Withdrawn", "expired": "Expired"}
MARKETING_WORD = dict(C.MARKETING_STATUSES)
# The lists under "The details" and what an entry prints after "Offer"
LIST_TITLE = dict(C.LISTS)
OFFER_WORD = dict(C.OFFER_WORDS)
# how a nearby home's status and this week's change read to a seller
NEARBY_STATUS = {"active": "Active", "pending": "Pending", "sold": "Sold", "withdrawn": "Withdrawn"}
# how each host's own unit of open house traffic reads, one and many
UNIT = {"groups": ("group", "groups"), "visitors": ("visitor", "visitors"), "guests": ("guest", "guests"),
        "parties": ("party", "parties"), "people": ("person", "people")}
# One build mode: every page is ready to send. None of this working wording may ever be on a page.
NEVER_ON_A_PAGE = ["draft for", "do not send", "not for the seller", "for the reviewer", "tag review", "tags not",
                   "unreviewed", "not yet confirmed", "reviewer", "tagged", "untagged"]

# Per-build switches. api.render() fills this before anything is drawn.
OPT = {}
