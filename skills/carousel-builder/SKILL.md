---
name: carousel-builder
description: Generates Graeham Watts' branded 15-image real estate social media package (two Instagram carousels + 4 standalone static images) for a property listing, using a PIL-based image compositing engine (no browser needed). Use this skill ANY time the user asks to create social media graphics, carousel posts, static images, or a "production package" for a real estate listing, especially when they reference a specific property address with photos already on disk. Also trigger on: "make me a carousel for [address]", "create the social media package for this listing", "generate the investment math / multi-gen carousel", "do the same thing we did for [previous property] but for [new property]", or any request to turn property photos + facts into branded Instagram-ready images. This skill produces IMAGES only (carousels + statics) — for video scripts, HeyGen avatar renders, or B-roll for the same listing, hand off to video-script-creation-engine, heygen-video, and higgsfield-video after this skill's images are done.
---

# Listing Social Carousel Generator

Produces Graeham Watts' proven 15-asset image package for a property listing:
Carousel A "The Investment Math" (5 cards), Carousel B "Multi-Gen Made Easy"
(6 cards), and 4 standalone static images — all in his black/gold brand,
with his logo, built by compositing directly onto the property's real photos.

This was built from scratch for 2247 Menalto Ave (East Palo Alto) across many
rounds of feedback, and this skill packages the resulting engine + the
lessons learned so the next property doesn't have to re-derive any of it.

## Before you touch any code: read `references/workflow.md`

That file is the actual step-by-step process — gathering facts, confirming
the narrative angle, selecting photos, filling in the template, running it,
reviewing output, delivering. Read it before starting. The summary below is
just an orientation.

**The single most important thing to understand:** the *engine* (card
layouts, brand treatment, the specific mix of card types and their order) is
reusable. The *content* — hooks, headlines, dollar figures, which room is
shown where — is never reused verbatim across properties. Every new property
needs its own facts gathered and its own copy written to fit those facts.
Don't copy Menalto's headlines onto a different address.

## Why PIL instead of an HTML/CSS renderer

A headless browser (Playwright/Chromium) is not available in this
environment (missing shared libs, no root to install them). So this whole
pipeline is built as direct PIL/Pillow image compositing: cover-crop photos
to the target aspect ratio, layer gradient scrims for text legibility, draw
gold-on-dark pill/panel shapes behind any text, and place the logo with a
soft alpha-silhouette shadow. `references/brand.md` documents the specific
techniques (and the failed attempts that led to them) in more detail —
skim it if you're adding a new card type or debugging a legibility issue.

## Always research market context before writing price/value copy

Before any card that touches price, value, or "deal" framing gets written,
search for the area's current median price and median $/sqft and compare
them to this property's numbers — a low total price does NOT imply a low
$/sqft (small homes often carry a *higher* $/sqft since land cost is fixed
regardless of structure size). Also search the property's own address to
catch discrepancies between the live MLS listing and third-party sites
(Zillow/Redfin can lag); if you find one, ask the user which figure is
current rather than guessing. See `references/workflow.md` step 2 for the
full reasoning — this is a recurring failure mode, not a one-off check.

## Quick start

1. Read `references/workflow.md` in full.
2. Gather the property's facts (address, price, beds/baths, lot size, rental
   estimates if it has an ADU) from the user, or from a shared MLS Matrix
   link if provided.
3. Research market context (median price/$/sqft, third-party listing
   discrepancies) before proposing any value-based narrative angle.
4. Confirm with the user whether this property fits the ADU/investment +
   multi-gen narrative split, or needs different angles (see workflow.md
   step 3) — ask, don't assume, and ground the options you propose in what
   the research + photos actually show.
5. Get the property's photos into a `src/` folder and assign 11 of them to
   the roles documented in `scripts/template_build.py`.
6. Copy `scripts/template_build_impact.py` (the current default -- v3
   "impact" system), fill in `CONFIG`, rewrite the copy in every card call
   to fit this property, run it. Only reach for the older
   `scripts/template_build.py` if you need its standalone static-image
   templates or are reproducing a pre-v3 property's exact look.
7. Review the 15 output JPGs, then copy them into the user's workspace
   folder and present them.

## Files in this skill

- `scripts/carousel_lib.py` — the rendering engine. **Default card + static
  templates (use these for any new property):** `impact_hook_card`,
  `impact_photo_card`, `impact_split_content`, `impact_split_silent` (text-free photo-pair
  breather card), `impact_split_silent_bare` (same, but zero logo/badge/footer branding —
  use only when matching a reference that's completely unbranded),
  `news_fact_card` (a distinct "breaking news" fact-card format — bright, no-grade photo,
  the LOCKED `floor_fade_scrim()` bottom treatment (flat fully-opaque black floor across ~1/3
  of the card, then a gentle eased-gradient fade above it into the photo — confirmed final
  after several rounds of client review, do NOT revert to a plain linear scrim or add photo
  color grading to this card type), and text drawn with the exact same left-aligned
  tag-banner + two-tone-headline + sub-text calls as `impact_hook_card` for visual
  consistency across a carousel), `impact_takeover_stat_card`, `impact_cta_card` (carousel cards) and `impact_static_stat_card`,
  `impact_static_blueprint`, `impact_static_landscape`,
  `impact_static_comparison` (the 4 standalone statics) — the "impact" v3
  visual system (bold gradient-gold tag banners, two-tone headlines,
  circular collage inset on the hook card, script-font CTA titles). Plus the
  gradient primitives underneath them (`gradient_text`,
  `gradient_rounded_rect`, `gradient_ring`, `bold_tag_banner`,
  `draw_two_tone_headline`, `circular_inset`, `connector_arrow`,
  `get_script_font`). Older functions (`simple_card2`, `stat_card`,
  `arrow_stat_card`, `takeover_stat_card`, `cta_card`, `triptych`) are kept
  only for backward compatibility with properties shipped before the v3
  redesign — don't use them for new work. `impact_hook_card` and `news_fact_card` share
  a `lift_px`/`lift_main`/`lift` param on their underlying `base_photo_card()` call — use
  this (a pure vertical translate of the already-cropped photo) to reveal more of a subject
  that's sitting low in frame with too much empty sky/ceiling above it. Don't reach for the
  `zoom`/`zoom_main` param for this — zoom changes the crop scale/framing, which is a
  different edit; only use zoom when the subject genuinely needs to be enlarged.
  `impact_hook_card` also accepts `show_connector=False` to drop the gold curved arrow
  linking the main photo to the circular inset, when the inset alone reads cleaner. Shared
  primitives (cropping, plain gradients, text wrapping, `swipe_cue`, the logo compositor) are used by
  both generations. Don't edit this file unless you're fixing a genuine bug
  or adding a reusable new card type — per-property changes belong in the
  copied template script, not here.
- `scripts/template_build_impact.py` — **the default per-property driver**
  (v3 impact system), annotated with a `CONFIG` block and inline comments.
  Copy this file per property; don't run it in place.
- `scripts/template_build.py` — the older v2 driver (kept for
  already-shipped properties and its 4 standalone static-image templates,
  which don't have v3 equivalents yet).
- `assets/fonts/` — Montserrat and Inter variable-weight TTFs (brand fonts),
  plus Great Vibes (`GreatVibes-Regular.ttf`, SIL OFL licensed) — the script
  font used for CTA card titles in the v3 system.
- `assets/logo/` — Graeham's logo, white and black versions, pre-trimmed to
  their bounding box.
- `references/brand.md` — exact brand colors/fonts, the hard-won v2 layout
  lessons (gold-on-dark-backing rule, `anchor="mm"` centering rule, logo
  shadow technique, no-fabricated-people rule), and the full v3 "impact"
  visual system spec (gradient gold everywhere, bold tag banners, two-tone
  headlines, the scrim rules, the CTA title staple). Read the v3 section
  before building a new property's cards.
- `references/workflow.md` — the full step-by-step process.

## Output

15 JPGs at 1080×1350 (carousel cards) except `Static_1` (1080×1080 square)
and `Static_3` (1200×628 landscape) — matching Instagram's portrait/square/
landscape aspect ratios for feed and carousel posts. (Static numbering
differs slightly between the v2 template and `template_build_impact.py`'s
STATICS section — check the actual card call for exact dimensions rather
than assuming from the filename.)

## Scope

This skill covers the carousel + static IMAGES only. Video scripts, HeyGen
avatar renders, and Higgsfield b-roll for the same listing are separate
downstream steps handled by other skills (`video-script-creation-engine`,
`heygen-video`, `higgsfield-video`) — mention this handoff to the user if
they ask for the full production package (images + videos), don't try to
generate video from this skill.
