#!/usr/bin/env python3
"""
quick_carousel_build.py -- per-post driver for quick-carousel-engine.

HOW TO USE THIS FILE:

1. Copy this file to a scratch location for the new post, e.g.
   /tmp/work/<post-slug>/build.py
2. Pick ONE template category from references/template-categories.md and
   delete the card calls for the other categories below -- don't ship all
   three as one carousel.
3. Fill in every real number/label. Every stat needs a `source_note` (where
   the number came from, e.g. "Zumper, Sept 2026") -- see
   references/workflow.md's data-integrity rule. Never invent a stat.
4. Run it: `python3 build.py`
5. Review the output JPGs, then hand off to Peter/Ellie or post directly.

The card calls below are filled with placeholder copy so the script runs
end-to-end for review -- replace every placeholder before shipping. This
mirrors carousel-builder's template_build_impact.py convention.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quick_carousel_lib import (
    configure, _sync_footer,
    quick_title_card, quick_rank_card, quick_table_card, quick_cta_card,
    editorial_rank_list_card,
    impact_takeover_stat_card,
)
from quick_carousel_lib import card_number_badge, swipe_cue, save  # for the raw stat-card path

# ===========================================================================
# CONFIG
# ===========================================================================
CONFIG = {
    "src_dir": "/tmp/work/src",   # only needed if you mix in a real photo card
    "out_dir": "/tmp/work/out",
    "footer_text": "GRAEHAM WATTS . BAY AREA / PENINSULA",
    "contact_line": "Graeham Watts  .  Compass  .  DRE #01466876",
}
configure(CONFIG["src_dir"], CONFIG["out_dir"])
_sync_footer(CONFIG)

W, H = 1080, 1350

# ===========================================================================
# CATEGORY 1A -- Standalone editorial rank-list post (the direct analog of
# the "Where People Are Moving" reference Graeham pointed to). ONE image,
# not a multi-card carousel -- this is the fastest version of Category 1
# and usually the right default. Light background, black headline, tinted
# two-column ranked list. See references/template-categories.md.
# ===========================================================================

editorial_rank_list_card(
    W, H, "01A_Standalone.jpg", 1, 1,
    headline_text="Where People Are [Moving]",
    accent_word="Moving",
    sub_text="The cities people are leaving the Peninsula for -- and moving in from.",
    left_label="Leaving",
    left_rows=[f"[City {i}, ST]" for i in range(1, 11)],
    right_label="Moving To",
    right_rows=[f"[City {i}, ST]" for i in range(1, 11)],
    source_note="[Cite the real source + month here before posting, e.g. USPS/Redfin migration data]",
)

# ===========================================================================
# CATEGORY 1B -- Multi-card carousel version (optional -- use when the topic
# needs more room than one standalone image: a single hero stat, a data
# barrage, a region zoom-out, then a CTA card). Reverse-engineered from
# viral-hook-library/references/notes/15_sfgate-rent-carousel.md -- "Rent in
# X is up Y%. It signals a larger trend."
# ===========================================================================

quick_title_card(
    W, H, "01_Title.jpg", 1, 6,
    tag_text="Peninsula Trend",
    headline_text="Placeholder: [metric] in [city] is up [X]%.",
    accent_words=["[X]%."],
    sub_text="It signals a larger trend across the Peninsula. Swipe for the numbers.",
    source_note="[Cite the real source + month here before posting]",
)

base = impact_takeover_stat_card(
    W, H, "The Number", "[XX]%",
    "[what this stat measures, e.g. '1BR asking rent, YoY']",
    "Replace with one sentence making the number land.", None,
)
card_number_badge(base, W, 2, 6)
swipe_cue(base, W, H)
save(base, "02_Stat.jpg")

quick_table_card(
    W, H, "03_Table.jpg", 3, 6,
    tag_text="By Neighborhood",
    rows=[
        ("[Neighborhood 1]", "+[X]%"),
        ("[Neighborhood 2]", "+[X]%"),
        ("[Neighborhood 3]", "+[X]%"),
        ("[Neighborhood 4]", "+[X]%"),
    ],
    headline_text="Replace with a closing line tying the rows together.",
    source_note="[Cite the real source + month here before posting]",
)

quick_rank_card(
    W, H, "04_ZoomOut.jpg", 4, 6,
    rank_text="Zoom Out",
    label_text="Replace: the region-wide version of this trend",
    value_text="[X]%",
    note_text="[one supporting sentence]",
)

quick_cta_card(
    W, H, "05_CTA.jpg", 5, 6,
    headline_text="Replace with the payoff headline",
    accent_words=["payoff", "headline"],
    button_text="Get the full breakdown",
    sub_text="One sentence restating why this matters to a buyer/seller.",
    keyword_line="Comment [KEYWORD] and I'll send it over.",
)

print("QUICK CAROUSEL (Category 1 -- Trend/Stat) BUILD DONE ->", CONFIG["out_dir"])

# ===========================================================================
# CATEGORY 2 -- Price/Market Comparison Carousel
# (reverse-engineered from viral-hook-library/references/notes/
#  13_2m-across-america-carousel.md -- "What $X gets you here" -- adapted
#  Peninsula-wide instead of city-vs-city across the country: EPA vs RWC vs
#  PA vs MP vs SMC. Use quick_rank_card once per sub-market with the SAME
#  price point, so only the label/value visibly changes swipe to swipe.)
# ===========================================================================

# Uncomment and fill in real MLS numbers (via mls-matrix-scraper) instead of
# shipping Category 1 and 2 in the same carousel -- pick one.
#
# quick_title_card(
#     W, H, "01_Title.jpg", 1, 6,
#     tag_text="Peninsula Price Check",
#     headline_text="What [$X] gets you across the Peninsula.",
#     accent_words=["[$X]"],
#     sub_text="Same budget, five very different markets. Swipe through.",
# )
# quick_rank_card(W, H, "02_EPA.jpg", 2, 6, "East Palo Alto", "[beds/baths, sqft]", "[$X]")
# quick_rank_card(W, H, "03_RWC.jpg", 3, 6, "Redwood City", "[beds/baths, sqft]", "[$X]")
# quick_rank_card(W, H, "04_PA.jpg", 4, 6, "Palo Alto", "[beds/baths, sqft]", "[$X]")
# quick_rank_card(W, H, "05_MP.jpg", 5, 6, "Menlo Park", "[beds/baths, sqft]", "[$X]")
# quick_cta_card(
#     W, H, "06_CTA.jpg", 6, 6,
#     headline_text="Which one would you pick?",
#     accent_words=["pick?"],
#     button_text="See active listings",
#     keyword_line="Comment your pick below.",
# )

# ===========================================================================
# CATEGORY 3 -- PropCast Listing Snapshot ("This Week on the Peninsula")
# Sourced from Graeham's OWN active/new listing intelligence (PropCast /
# mls-matrix-scraper), not public trend data. Never fabricate counts -- pull
# the real number for the week being posted.
# ===========================================================================

# quick_title_card(
#     W, H, "01_Title.jpg", 1, 4,
#     tag_text="This Week",
#     headline_text="[N] new listings just hit the Peninsula.",
#     accent_words=["[N]"],
#     sub_text="Here's the quick breakdown.",
# )
# quick_table_card(
#     W, H, "02_Breakdown.jpg", 2, 4,
#     tag_text="By Price Band",
#     rows=[
#         ("Under $1M", "[N]"),
#         ("$1M-$2M", "[N]"),
#         ("$2M-$3M", "[N]"),
#         ("$3M+", "[N]"),
#     ],
#     headline_text=None,
#     source_note="Graeham's PropCast listing intelligence, [week of]",
# )
# quick_cta_card(
#     W, H, "03_CTA.jpg", 3, 4,
#     headline_text="Want the full list?",
#     accent_words=["full", "list?"],
#     button_text="Get this week's listings",
#     keyword_line="Comment LISTINGS and I'll send the full sheet.",
# )
