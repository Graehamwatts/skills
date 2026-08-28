#!/usr/bin/env python3
"""
template_build_impact.py -- per-property driver for the "impact" v3 visual
system. THIS IS THE DEFAULT TEMPLATE for any new property's carousels --
use this file, not template_build.py (that one is the older v2 system, kept
only so already-shipped properties stay reproducible).

HOW TO USE THIS FILE:

1. Copy this file to a scratch location for the new property, e.g.
   /tmp/work/<property-slug>/build.py
2. Fill in the CONFIG block below with the property's facts and photos.
3. Rewrite every headline/tag/sub -- the card TYPES and ORDER below are the
   proven structure (hook -> photo -> split-content -> stat takeover -> CTA,
   repeated for a second angle), but the words are never reused verbatim
   across properties. Confirm the narrative angle(s) with the user first
   (see references/workflow.md) -- don't assume every property fits a
   5-card + 6-card two-carousel split; adjust card count to fit the story.
4. Run it: `python3 build.py`

Read references/brand.md's "v3 impact system" section before touching any
card call -- it explains WHY each visual choice exists (gradient gold vs.
flat gold, the scrim rule, the CTA title staple, etc.) and which things were
tried and explicitly rejected, so you don't reintroduce a fixed bug.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carousel_lib as lib
from carousel_lib import (
    impact_hook_card, impact_photo_card, impact_split_content, impact_split_silent,
    impact_takeover_stat_card, impact_cta_card,
    impact_static_stat_card, impact_static_blueprint, impact_static_landscape,
    impact_static_comparison,
    scrim_bottom, place_logo, footer_wordmark2, card_number_badge, save,
    swipe_cue, split_vertical, split_horizontal,
)

# ===========================================================================
# CONFIG -- fill this in per property
# ===========================================================================
CONFIG = {
    "src_dir": "/tmp/work/src",
    "out_dir": "/tmp/work/out",
    "footer_text": "PROPERTY ADDRESS  ·  CITY",
    "contact_line": "Graeham Watts  ·  Compass  ·  DRE #01466876",

    # Photo roles -- pick real filenames from the property's photo set by
    # actually looking at them (see references/photo-selection.md). Reuse a
    # photo across roles if the property doesn't have 11 distinct useful
    # shots -- a repeated great photo beats a unique mediocre one.
    "photos": {
        "hook_main": "front1.jpg",       # hero exterior shot for carousel A's hook card
        "hook_inset": "kitchen.jpg",     # second photo peeking through the hook's collage circle
        "photo_2": "kitchen.jpg",        # card 2 -- a standout single room/feature
        "split_top": "bed1.jpg",         # split-content card, top half
        "split_bottom": "bed2.jpg",      # split-content card, bottom half
        "hook_main_b": "backyard1.jpg",  # hero shot for carousel B's hook card (different angle)
        "hook_inset_b": "living1.jpg",
        "photo_b2": "living1.jpg",
        "split_top_b": "bath.jpg",
        "split_bottom_b": "front2.jpg",
        "photo_b5": "backyard2.jpg",
        "cta_photo_a": "aerial1.jpg",
        "cta_photo_b": "front1.jpg",
        "static_stat_bg": "backyard1.jpg",   # blurred/dimmed background for the standalone stat static
        "static_blueprint": "bed1.jpg",      # a room photo for the "convert/reconfigure" diagram static
        "static_landscape_l": "front1.jpg",  # landscape static, left half
        "static_landscape_r": "backyard1.jpg",  # landscape static, right half
        "static_comparison_bg": "backyard2.jpg",  # blurred/dimmed background for the comparison table static
    },
}

lib.configure(CONFIG["src_dir"], CONFIG["out_dir"])
lib.FOOTER_TEXT = CONFIG["footer_text"]
lib.CONTACT_LINE = CONFIG["contact_line"]
P = CONFIG["photos"]

W, H = 1080, 1350

# ===========================================================================
# CAROUSEL A -- pick a provocative angle (negation/bold-claim/intrigue --
# see brand.md's v2 engagement patterns section, still true for v3)
# ===========================================================================

impact_hook_card(
    main_photo=P["hook_main"], inset_photo=P["hook_inset"], w=W, h=H,
    tag_text="Just Listed",
    headline_text="Replace with a provocative headline.",
    accent_words=["one", "or", "two", "gold", "words"],  # must match words in headline_text exactly
    sub_text="One supporting sentence that earns the headline's claim.",
    filename="CarouselA_1_Hook.jpg", idx=1, total=5, inset_pos=("right", 0.32),
)

impact_photo_card(
    P["photo_2"], W, H,
    tag_text="Feature Tag", headline_text="Short, punchy headline.",
    accent_words=["headline."],
    sub_text="One or two supporting details, comma-separated fragments read well.",
    filename="CarouselA_2_Feature.jpg", idx=2, total=5,
)

# Example of the text-free "breather" card (see brand.md) -- swap back to
# the impact_split_content() version below if this slide needs to make a
# specific point instead of just letting two photos breathe.
impact_split_silent(P["split_top"], P["split_bottom"], W, H, "CarouselA_3_Split.jpg",
                     idx=3, total=5)

# The alternative, text-carrying version of the same split card:
# base = split_vertical(P["split_top"], P["split_bottom"], W, H)
# scrim_bottom(base, h_frac=0.5, max_alpha=250)
# place_logo(base, W)
# impact_split_content(base, W, H, 76, "Tag Text", "Headline for the split card.",
#                       ["split."], "Supporting sentence.",
#                       sub_accent_words=["specific", "phrase"])  # optional inline gold highlight
# card_number_badge(base, W, 3, 5)
# swipe_cue(base, W, H)
# footer_wordmark2(base, W, H)
# save(base, "CarouselA_3_Split.jpg")

base = impact_takeover_stat_card(W, H, "The Numbers", "$XXX,XXX",
                                  "what this stat measures, in plain words",
                                  "One sentence making the number land.", None)
card_number_badge(base, W, 4, 5)
swipe_cue(base, W, H)
save(base, "CarouselA_4_Numbers.jpg")

impact_cta_card(
    P["cta_photo_a"], W, H, "CarouselA_5_CTA.jpg", 5, 5,
    button_text="Schedule a tour",
    sub_text="One sentence restating the carousel's core promise.",
    title_line1="A short lead-in word",       # always .upper()'d automatically
    title_script_line2="Gold noun phrase",    # rendered in the script font + gradient
    save_share_text="Save this if you're watching this market.",
)

# ===========================================================================
# CAROUSEL B -- a second, different angle on the same property (don't repeat
# carousel A's framing -- give people a genuinely different reason to save it)
# ===========================================================================

impact_hook_card(
    main_photo=P["hook_main_b"], inset_photo=P["hook_inset_b"], w=W, h=H,
    tag_text="Second Angle Tag",
    headline_text="A different provocative headline.",
    accent_words=["accent", "words"],
    sub_text="Supporting sentence for angle two.",
    filename="CarouselB_1_Hook.jpg", idx=1, total=6, inset_pos=("right", 0.32),
)

impact_photo_card(
    P["photo_b2"], W, H,
    tag_text="Feature Tag", headline_text="Another short headline.",
    accent_words=["headline."],
    sub_text="Supporting details.",
    filename="CarouselB_2_Feature.jpg", idx=2, total=6,
)

base = split_vertical(P["split_top_b"], P["split_bottom_b"], W, H)
scrim_bottom(base, h_frac=0.5, max_alpha=250)
place_logo(base, W)
impact_split_content(base, W, H, 76, "Tag Text", "Headline for the split card.",
                      ["done."], "Supporting sentence.")
card_number_badge(base, W, 3, 6)
swipe_cue(base, W, H)
footer_wordmark2(base, W, H)
save(base, "CarouselB_3_Split.jpg")

base = impact_takeover_stat_card(W, H, "Another Stat", "X,XXX SF",
                                  "what this stat measures",
                                  "One sentence making the number land.",
                                  "Optional second supporting sentence.")
card_number_badge(base, W, 4, 6)
swipe_cue(base, W, H)
save(base, "CarouselB_4_Stat.jpg")

impact_photo_card(
    P["photo_b5"], W, H,
    tag_text="Location / Feature", headline_text="Fifth card headline.",
    accent_words=["headline."],
    sub_text="Supporting detail.",
    filename="CarouselB_5_Feature.jpg", idx=5, total=6,
)

impact_cta_card(
    P["cta_photo_b"], W, H, "CarouselB_6_CTA.jpg", 6, 6,
    button_text="Schedule a tour",
    sub_text="One sentence restating angle two's promise.",
    title_line1="Lead-in",
    title_script_line2="Gold phrase",
    save_share_text="Tag someone this fits.",
)

# ===========================================================================
# STANDALONE STATICS (not part of either carousel -- single feed posts)
# ===========================================================================

base = impact_static_stat_card(
    P["static_stat_bg"], 1080, 1080, "Tag Text", "$XXX,XXX",
    "what this number represents", "One sentence.", "Making the number land.",
)
save(base, "Static_1_Stat.jpg")

base = impact_static_blueprint(
    P["static_blueprint"], W, H, "Tag Text", "CALLOUT STAT",
    "Two-tone headline for the diagram static.", ["headline."],
    "Supporting sentence.",
    partition_kwargs={"x_frac": 0.56, "y0_frac": 0.28, "y1_frac": 0.80},
)
save(base, "Static_2_Blueprint.jpg")

base = impact_static_landscape(
    P["static_landscape_l"], P["static_landscape_r"], 1200, 628,
    "A headline for the landscape/link-preview static.", ["headline."],
    CONFIG["footer_text"].title(),
)
save(base, "Static_3_Landscape.jpg")

base = impact_static_comparison(
    P["static_comparison_bg"], W, H, "Why This One",
    [("PRICE", "$XXX,XXX"), ("LOT SIZE", "X,XXX SF"),
     ("CONFIGURATION", "X BED / X BATH"), ("DAYS ON MARKET", "NEW")],
    "Closing headline for the comparison static.",
    "One supporting sentence.",
)
save(base, "Static_4_Comparison.jpg")

print("CAROUSEL + STATICS BUILD DONE ->", CONFIG["out_dir"])
