#!/usr/bin/env python3
"""
template_build.py -- LEGACY v2 per-property driver. For any NEW property,
use scripts/template_build_impact.py instead -- it drives the current
default "impact" visual system (gradient gold, bold tag banners, two-tone
headlines; see references/brand.md's v3 section). This file is kept only so
already-shipped v2 properties (built with simple_card2/content_block2/
takeover_stat_card/cta_card) stay reproducible, and because its 4 standalone
static-image templates don't have v3 equivalents yet.

HOW TO USE THIS FILE (references/workflow.md in the skill has the full
walkthrough -- this is the condensed version):

1. Copy this file to a scratch location for the new property, e.g.
   /tmp/work/<property-slug>/build.py
2. Fill in the CONFIG block below with the property's facts and the 11 chosen
   source photos (see references/photo-selection.md for how to pick them).
3. Edit the copy (headlines/eyebrows/subtext) in the CAROUSEL A / CAROUSEL B /
   STATICS sections below. Keep the section *structure* (card types, order,
   what each card is for) -- that's Graeham's proven format from 2247 Menalto
   Ave. Only the words and numbers should change per property.
4. Run it: `python3 build.py`
5. The 15 finished JPGs land in CONFIG["out_dir"].

This produces the same 15-asset package every time:
  Carousel A "The Investment Math" (5 cards) -- ADU/investment angle
  Carousel B "Multi-Gen Made Easy" (6 cards) -- multi-generational living angle
  4 standalone static images

If the new property does NOT have an ADU / second unit, this template's
"investment math" and "multi-gen" framing won't fit -- talk to the user about
what the two carousel angles should be instead (e.g. "renovation potential"
vs "lifestyle/location") before reusing this structure verbatim. Don't force
an ADU narrative onto a property that doesn't have one.

v2 engagement patterns (see references/brand.md for the full reasoning --
these are DEFAULT behaviors now, not optional extras):
  - Hooks use negation / bold-claim / intrigue framing, not plain description.
    "Everyone says X. This one says otherwise." beats "Nice house in X."
  - The "numbers" card in each carousel uses takeover_stat_card() -- solid
    brand-black, no photo -- instead of keeping a dimmed photo behind the
    stat. It's a deliberate visual break partway through the carousel.
  - Every non-final card gets swipe_cue() -- a small "SWIPE ->" pill,
    bottom-right -- to push swipe-through instead of assuming it.
  - Every cta_card() call fills in save_share_text with something specific
    to the property ("Save this if you're watching this market"), not just
    "Schedule a tour" -- the save/share ask is the actual growth lever.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carousel_lib as lib
from carousel_lib import (
    base_photo_card, scrim_bottom, scrim_top, full_scrim, place_logo,
    content_block2, footer_wordmark2, card_number_badge, save, swipe_cue,
    split_vertical, split_horizontal, dim_layer, label_chip, triptych,
    backdrop_panel, stat_card, arrow_stat_card, simple_card2, cta_card,
    takeover_stat_card, partition_overlay, eyebrow_pill, wrap_text,
    draw_multiline, get_font, GOLD, BLACK, WHITE,
)
from PIL import Image, ImageDraw

# ===========================================================================
# CONFIG -- fill this in per property
# ===========================================================================
CONFIG = {
    "src_dir": "/tmp/work/src",          # folder of source photos for THIS property
    "out_dir": "/tmp/work/out",          # where the 15 finished JPGs get written
    "footer_text": "2247 MENALTO AVE  ·  EAST PALO ALTO",
    "contact_line": "Graeham Watts  ·  Compass  ·  DRE #01466876",

    # Facts used in copy below -- keep these here so they're easy to update
    # in one place instead of hunting through the card calls.
    "price": "$1,098,888",
    "specs_line": "4 bed / 2 bath  ·  $1,098,888  ·  East Palo Alto",
    "config_line": "4 bed / 2 bath + ADU",
    "lot_size": "0.15 acre",
    "adu_rent_current": "$2,500/mo",
    "adu_rent_converted": "$3,500/mo",
    "adu_rent_range": "$3,000–$3,500/mo",

    # Photo roles -- filenames must exist inside src_dir. Pick these by
    # actually looking at the photos (see references/photo-selection.md):
    # front_facade    - clean full exterior shot of the whole property, no cars/people
    # kitchen_front   - best interior shot of the MAIN house (kitchen or living room)
    # adu_exterior    - ADU/second-unit exterior, clearly a separate structure
    # adu_exterior2   - a second, different angle of the ADU exterior
    # adu_bedroom     - ADU bedroom or a room that reads as a bedroom
    # adu_desk_nook   - ADU office/nook/flex space
    # adu_kitchen     - ADU kitchen or kitchenette
    # adu_living      - ADU living area
    # backyard_patio  - backyard/patio, ideally showing both structures or open space
    # living_fireplace- a warm, inviting interior shot of the main house (living room)
    # aerial_both     - wide/aerial shot showing both the main house and the ADU together
    "photos": {
        "front_facade": "front_facade.jpg",
        "kitchen_front": "kitchen_front.jpg",
        "adu_exterior": "adu_exterior.jpg",
        "adu_exterior2": "adu_exterior2.jpg",
        "adu_bedroom": "adu_bedroom.jpg",
        "adu_desk_nook": "adu_desk_nook.jpg",
        "adu_kitchen": "adu_kitchen.jpg",
        "adu_living": "adu_living.jpg",
        "backyard_patio": "backyard_patio.jpg",
        "living_fireplace": "living_fireplace.jpg",
        "aerial_both": "aerial_both.jpg",
    },
}

lib.configure(CONFIG["src_dir"], CONFIG["out_dir"])
lib.FOOTER_TEXT = CONFIG["footer_text"]
lib.CONTACT_LINE = CONFIG["contact_line"]
P = CONFIG["photos"]

W, H = 1080, 1350


# ===========================================================================
# CAROUSEL A -- "The Investment Math" (5 cards, ADU/investor angle)
# ===========================================================================

simple_card2(P["front_facade"], W, H, ("center", "center"),
    "STOP BUYING JUST A HOUSE", "Most buyers see one house. This one pays you to own it.",
    CONFIG["specs_line"],
    "CarouselA_1_Hook.jpg", idx=1, total=5, headline_size=58, sub_size=30, dim=0.0)

simple_card2(P["kitchen_front"], W, H, ("center", "center"),
    "FRONT HOUSE · 3 BED / 1 BATH", "This is just the part you live in.",
    "Updated kitchen. Fireplace. Fenced yard.",
    "CarouselA_2_FrontUnit.jpg", idx=2, total=5, headline_size=62, sub_size=30, dim=0.05)

base = split_vertical(P["adu_exterior"], P["adu_bedroom"], W, H)
scrim_bottom(base, h_frac=0.5, max_alpha=235)
place_logo(base, W)
content_block2(base, W, H, 76, "REAR UNIT · THE ADU",
              "This is the part most buyers miss.",
              "1 bed, 1 bath now. 2 bed with conversion. Either way, it rents.",
              headline_size=52, sub_size=28, align="left")
card_number_badge(base, W, 3, 5)
swipe_cue(base, W, H)
footer_wordmark2(base, W, H)
save(base, "CarouselA_3_RearUnit.jpg")

# "The numbers" card -- solid-black takeover, not another dimmed photo. Lead
# with the single most compelling number (the delta), not a from/to pair --
# it hits harder as one giant figure.
base = takeover_stat_card(W, H, "THE UNLOCK", "+$1,000/MO",
                           "if the ADU converts from a 1-bed to a 2-bed",
                           "Most buyers won't do this math. You just did.", None)
card_number_badge(base, W, 4, 5)
swipe_cue(base, W, H)
save(base, "CarouselA_4_TheNumbers.jpg")

cta_card(P["aerial_both"], W, H, ("center", "center"), "THE UNLOCK", "Schedule a tour.",
         "See why investors are calling this the unlock.",
         "CarouselA_5_CTA.jpg", 5, 5, dim=0.15,
         save_share_text="Save this if you're house-hunting in the area.")


# ===========================================================================
# CAROUSEL B -- "Multi-Gen Made Easy" (6 cards, multi-generational angle)
# ===========================================================================

base = split_horizontal(P["living_fireplace"], P["adu_living"], W, H)
scrim_bottom(base, h_frac=0.46, max_alpha=235)
place_logo(base, W)
content_block2(base, W, H, 76, "MULTI-GEN MADE EASY",
              "Your parents move in. Your mortgage moves out.",
              None, headline_size=56, sub_size=30, align="left")
card_number_badge(base, W, 1, 6)
swipe_cue(base, W, H)
footer_wordmark2(base, W, H)
save(base, "CarouselB_1_Hook.jpg")

simple_card2(P["kitchen_front"], W, H, ("center", "center"),
    "THE MAIN HOUSE", "Plenty of space for the whole family.",
    "3 bedrooms + 1 bath up front.",
    "CarouselB_2_FrontHouse.jpg", idx=2, total=6, headline_size=58, sub_size=30, dim=0.05)

base = split_vertical(P["adu_exterior2"], P["adu_kitchen"], W, H)
scrim_bottom(base, h_frac=0.5, max_alpha=235)
place_logo(base, W)
content_block2(base, W, H, 76, "THE ADU",
              "Their own entrance. Their own space.",
              "Their own independence.", headline_size=52, sub_size=30, align="left")
card_number_badge(base, W, 3, 6)
swipe_cue(base, W, H)
footer_wordmark2(base, W, H)
save(base, "CarouselB_3_TheirSpace.jpg")

# "The family math" card -- solid-black takeover, same reasoning as Carousel
# A's numbers card: one deliberate visual break, one number, no photo.
base = takeover_stat_card(W, H, "THE FAMILY MATH", CONFIG["adu_rent_range"],
                           "estimated ADU rental income",
                           "Now your family's living free.",
                           "Rent the ADU. Everyone keeps their independence.")
card_number_badge(base, W, 4, 6)
swipe_cue(base, W, H)
save(base, "CarouselB_4_FamilyMath.jpg")

# B5 triptych (bespoke 3-panel layout: 2 photos + 1 graphic stat panel)
base, third = triptych(P["adu_bedroom"], P["adu_desk_nook"], W, H)
TITLE_H = 310
title_layer = Image.new("RGBA", (W, TITLE_H), BLACK + (235,))
base.alpha_composite(title_layer, (0, 0))
logo_bottom = place_logo(base, W, top_margin=28, target_w=230, plate=False)
draw = ImageDraw.Draw(base)
f_head = get_font("Mont", 800, 42)
head = "Guest room. Home office. Rental income."
lines = wrap_text(draw, head, f_head, W - 140)
head_y = logo_bottom + 26
draw_multiline(draw, (70, head_y), lines, f_head, WHITE, align="left", line_spacing=1.16)
f_sub = get_font("Inter", 600, 27, opsz=28)
draw.text((70, head_y + 50 * len(lines) + 6), "Pick your move.", font=f_sub, fill=GOLD)

panel3 = Image.new("RGBA", (W, H - 2 * third), BLACK + (255,))
d3 = ImageDraw.Draw(panel3)
f_lbl = get_font("Mont", 700, 26)
lbl = "RENTAL INCOME"
lb = d3.textbbox((0, 0), lbl, font=f_lbl)
d3.text((W / 2 - (lb[2] - lb[0]) / 2, 56), lbl, font=f_lbl, fill=GOLD)
f_big = get_font("Mont", 800, 64)
val = CONFIG["adu_rent_range"]
vb = d3.textbbox((0, 0), val, font=f_big)
d3.text((W / 2 - (vb[2] - vb[0]) / 2, 106), val, font=f_big, fill=WHITE)
f_note = get_font("Inter", 500, 24, opsz=24)
note = "estimated, as a 2-bed conversion"
nb = d3.textbbox((0, 0), note, font=f_note)
d3.text((W / 2 - (nb[2] - nb[0]) / 2, 190), note, font=f_note, fill=(200, 200, 200))
base.paste(panel3, (0, 2 * third), panel3)

dim_layer(base, (0, TITLE_H, W, third), alpha=70)
dim_layer(base, (0, third, W, 2 * third), alpha=70)
label_chip(base, (36, TITLE_H + 30), "GUEST ROOM", align="left")
label_chip(base, (36, third + 30), "HOME OFFICE", align="left")
card_number_badge(base, W, 5, 6)
swipe_cue(base, W, H)
save(base, "CarouselB_5_Flexibility.jpg")

cta_card(P["living_fireplace"], W, H, ("center", "center"), "FAMILY + FINANCE", "Schedule a tour.",
         "See how family and finance meet here.",
         "CarouselB_6_CTA.jpg", 6, 6, dim=0.1,
         save_share_text="Tag someone weighing a multi-gen move.")


# ===========================================================================
# STATICS (4 standalone images, no logo -- keep the gold-legibility fixes)
# ===========================================================================

base = base_photo_card(P["adu_bedroom"], W, H, dim=0.1)
partition_overlay(base, W, H, x_frac=0.56, y0_frac=0.28, y1_frac=0.80)
scrim_bottom(base, h_frac=0.46, max_alpha=235)
draw = ImageDraw.Draw(base)
y = eyebrow_pill(base, W, 96, "CONVERSION POTENTIAL", align="left")
draw = ImageDraw.Draw(base)
label_chip(base, (76, y + 4), "+$1,000/MO", fill=GOLD, text_color=BLACK, size=30)
content_block2(base, W, H, 76, None,
              "Convert to 2-bed.",
              "That rear bedroom is worth an estimated $1,000 more every month as a 2-bed. Simple math. Big outcome.",
              headline_size=58, sub_size=28, align="left", bottom_pad=100)
footer_wordmark2(base, W, H)
save(base, "Static_1_ConversionBlueprint.jpg")

SW, SH = 1080, 1080
base = stat_card(P["adu_exterior"], SW, SH, "YOUR MORTGAGE OFFSET", CONFIG["adu_rent_range"],
                  "per month, renting the ADU", "Your offset starts here.",
                  None, dim=0.3, blur=5, logo=False)
save(base, "Static_2_YourOffset.jpg")

LW, LH = 1200, 628
base = split_horizontal(P["kitchen_front"], P["adu_exterior2"], LW, LH)
draw = ImageDraw.Draw(base)
bar_h = 170
layer = Image.new("RGBA", (LW, bar_h), BLACK + (235,))
base.alpha_composite(layer, (0, LH - bar_h))
f_head = get_font("Mont", 800, 40)
head = "Multi-gen living + rental income."
hb = draw.textbbox((0, 0), head, font=f_head)
draw.text((LW / 2 - (hb[2] - hb[0]) / 2, LH - bar_h + 24), head, font=f_head, fill=WHITE)
f_sub = get_font("Inter", 500, 26, opsz=26)
sub = "The property that pays for itself.  ·  " + CONFIG["footer_text"].replace("  ·  ", ", ")
sb = draw.textbbox((0, 0), sub, font=f_sub)
draw.text((LW / 2 - (sb[2] - sb[0]) / 2, LH - bar_h + 82), sub, font=f_sub, fill=GOLD)
save(base, "Static_3_FamilyUpgrade.jpg")

base = base_photo_card(P["backyard_patio"], W, H, dim=0.45, blur=10)
full_scrim(base, alpha=140)
draw = ImageDraw.Draw(base)
y = eyebrow_pill(base, W, 180, "WHY INVESTORS CHOOSE THIS PROPERTY", align="center", size=44)
draw = ImageDraw.Draw(base)

rows = [
    ("PRICE", CONFIG["price"]),
    ("CONFIGURATION", CONFIG["config_line"]),
    ("EST. RENTAL INCOME", CONFIG["adu_rent_range"]),
    ("LOT SIZE", CONFIG["lot_size"]),
]
ry = 480
backdrop_panel(base, (60, ry - 30, W - 60, ry + 4 * 130 - 30), alpha=105)
draw = ImageDraw.Draw(base)
for label, value in rows:
    f_label = get_font("Inter", 600, 26, opsz=26)
    draw.text((90, ry), label, font=f_label, fill=(220, 220, 220))
    f_value = get_font("Mont", 800, 46)
    vb = draw.textbbox((0, 0), value, font=f_value)
    draw.text((W - 90 - (vb[2] - vb[0]), ry - 8), value, font=f_value, fill=GOLD)
    ry += 62
    draw.rectangle([90, ry, W - 90, ry + 1], fill=(255, 255, 255, 70))
    ry += 68

content_block2(base, W, H, 76, None,
              "Same address. Different dreams.",
              "The property that works for multi-gen families and investors alike.",
              headline_size=44, sub_size=26, align="center", bottom_pad=110)
footer_wordmark2(base, W, H)
save(base, "Static_4_WhyInvestors.jpg")

print("ALL 15 ASSETS DONE ->", CONFIG["out_dir"])
