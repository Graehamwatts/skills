# Graeham Watts brand spec (for this skill's image engine)

Canonical source: the `website-builder` skill's `realtor-brand-kit.md`. This
file is a condensed version scoped to what `carousel_lib.py` actually uses —
check the canonical file if Graeham's brand ever changes.

## Colors (exact hex — matches `carousel_lib.py` constants)

| Constant | Hex | Usage |
|---|---|---|
| `BLACK` | `#1A1A1A` | scrims, panels, pill backgrounds |
| `GOLD` | `#C5A55A` | headline accent, eyebrow tags, stat numbers, CTA button fill |
| `WHITE` | `#FFFFFF` | primary body/headline text |
| `CREAM` | `#F5EFDC` | rarely used, alternate light background |
| `DARKGOLD` | `#A88B3D` | secondary accent |
| `GRAY` | `#666666` | captions |

Gold is the only accent color. Never introduce blue/green/red except the one
deliberate exception: `SKYBLUE` for the blueprint/partition diagram graphic
on the "conversion potential" static, which is meant to read as technical
drawing annotation, not brand color.

## Fonts

Montserrat (variable weight axis) for headlines/numbers/eyebrows/badges —
bold, geometric, all-caps for tags. Inter (variable optical-size + weight
axes) for body/subhead/notes — quieter, more readable at small sizes.

Both are loaded from `assets/fonts/*.ttf` and accessed via
`carousel_lib.get_font("Mont", weight, size)` or
`get_font("Inter", weight, size, opsz=size)`. Don't hardcode font files
elsewhere — always go through `get_font()` so the variation-axis calls stay
consistent.

## Hard-won layout lessons (don't relearn these the expensive way)

**Gold text needs a dark backing, always.** Gold-on-photo alone reads fine on
a dark, low-contrast patch of a photo and disappears on a bright or busy one.
Every eyebrow tag, badge, and stat number in this library sits on a
semi-opaque black pill or panel (`eyebrow_pill`, `label_chip`,
`backdrop_panel`) for exactly this reason. Don't add new gold text directly
on a raw photo without one of these backings.

**Text vertical-centering inside pills/badges must use `anchor="mm"`.**
`PIL.ImageDraw.textbbox`'s top value includes ascender space, so a manual
`y + pad - const` offset looks visually off-center even though the math
seems right. Every pill/badge function in this library draws its text with
`draw.text((cx, cy), text, font=f, anchor="mm")` at the shape's true
geometric center. If you add a new pill/badge type, use `anchor="mm"` from
the start.

**Logo treatment: soft alpha-silhouette shadow, never a hard plate.** A solid
rounded-rect badge or a blurred rectangular glow behind the logo both read as
a "muddy smudge" in testing. The technique that worked: extract the logo
PNG's own alpha channel, render it as a blurred black silhouette matching the
letterforms exactly, and composite that twice underneath the sharp logo. See
`place_logo()`. This gives a tight halo with no visible border.

**CTA card layout: stack as one block with fixed gaps, not absolute
positions.** Logo → eyebrow tag → gold button → supporting sentence →
contact line, each one positioned relative to the previous element's bottom
edge with a fixed pixel gap (see `cta_card()`). This way, if you increase any
one element's size (e.g. bigger eyebrow font), everything below cascades
down together instead of the layout looking unbalanced. Don't position CTA
elements at absolute height fractions of the canvas — it looks fine for one
card and wrong the moment text length changes.

**No fabricated people.** Never generate images of people (buyers, families,
tenants) who don't exist for a specific listing — it's misleading and a fair
housing risk. Cards about "family" or "multi-gen living" should sell the
idea through real property photography + copy alone (see how Carousel B's
family-facing cards use empty rooms + a "your parents move in" headline
instead of a photo of an invented family).


## v2 engagement patterns (added after competitive research)

Published 2026 engagement data shows carousels beat single photos and reels
on engagement, driven almost entirely by saves and DM shares -- and a DM
share is weighted 3-5x a like in current algorithm guidance. Three concrete
implications for how cards should be written and built, not just decorated:

**Hooks should be provocative, not descriptive.** "The lowest price of entry
into East Palo Alto" states a fact. "Everyone says East Palo Alto is out of
reach. This one says otherwise." picks a fight and creates intrigue.
Negation ("Not a fixer. Not a flip."), bold claims ("Most buyers don't find
this. You just did."), and mild controversy consistently outperform plain
description on the first slide and on hook cards generally. Rewrite every
headline through this lens before shipping -- don't just swap in the
property's facts and call it done.

**The last card should ask for the save/share, not just the tour.** A CTA
card that only says "Schedule a tour" leaves the actual growth mechanism on
the table. `cta_card()` takes an optional `save_share_text` param -- always
fill it in with something specific to the property/angle ("Save this if
you're watching this market," "Tag someone who needs more space"), not a
generic "share this post."

**Break the visual pattern at least once per carousel.** A run of 4-5 cards
that all use the same dimmed-photo-plus-text-block composition starts to
blur together. `takeover_stat_card()` is a solid brand-black, no-photo slide
for exactly one big number -- use it for the "numbers" card in each carousel
instead of always keeping a photo behind the stat. It's a deliberate reset,
not a downgrade.

**Add `swipe_cue()` to every non-final card.** A small "SWIPE ->" pill,
bottom-right, on every card except the last CTA card in each carousel. Small
detail, real completion-rate lever -- explicit affordances outperform
assuming people will keep swiping on their own.

These are default behaviors now, not optional flourishes -- apply them to
every new property, not just the ones where a viral-post analysis happened
to get requested.

## v3 "impact" visual system (default for new properties)

A from-scratch visual redesign, benchmarked directly against real
high-performing Instagram real-estate carousels the user shared, but built
entirely in Graeham's own black/gold/white brand -- never copy a reference
post's actual colors, photos, or copy, only its structural/typographic
patterns. This is now the default look; the plain `simple_card2()` /
`content_block2()` / `takeover_stat_card()` / `cta_card()` functions stay in
the file only for backward compatibility with already-shipped properties.

**Bright, ungraded photo -- legibility comes from the scrim and typography,
never from dimming the photo.** A subtle duotone color-grade was tried and
tested: pixel-diffed against the plain photo, it came out to roughly a 9/255
mean difference with well under 10% of pixels meaningfully changed --
imperceptible, and it didn't move the "this looks boring" feedback at all.
Every `impact_*` card calls `base_photo_card(..., dim=0.0, grade=False,
grain=True)` -- keep the photo vivid and true-to-life like a real listing
photo. `grain=True` adds a very subtle noise texture so a bright, ungraded
photo doesn't look flat/digital; it is not a substitute for a color grade.

**Scrim: `scrim_bottom(base, h_frac=0.5, max_alpha=250)` (hook cards use
`h_frac=0.52, max_alpha=252`) -- dark at the very bottom, fading up to fully
bright by roughly the vertical middle of the card, and staying untouched
above that.** This is tied to the card's own geometry (a fixed fraction of
the card height), NOT to wherever the text happens to start -- a version
that anchored the fade to the exact top of the text block was tried and
explicitly rejected, because it needs to read with the same rhythm across
every card regardless of how long the headline runs. Apply this right after
creating the base photo, before any text is drawn, on `impact_hook_card()`
and `impact_photo_card()`; on split-photo cards, apply the identical
`scrim_bottom()` call yourself right after `split_vertical()` /
`split_horizontal()`, before `place_logo()`, since `impact_split_content()`
only draws the text block and doesn't own the scrim.

**Every gold element is a shiny metallic gradient, never flat gold.** Flat
gold fills (`IMPACT_GOLD`, `(212, 175, 55)`) read as yellow/amber and cheapen
the premium feel the first time you see them next to real gold. Anything
meant to read as "shiny metal" -- tag banners, headline accent words, CTA
buttons, the circular inset's ring, stat numbers, the CTA script line --
uses `gradient_rounded_rect()` / `gradient_text()` / `gradient_ring()` with
`BRIGHT_GOLD_STOPS` (dark amber edges, bright highlight sweep through the
middle). The edge stops were brightened once already after feedback that the
first and last letters of gradient words were too dark to read comfortably
-- don't darken the edge stops back down.

**Bold tag banner, not a soft eyebrow pill.** `bold_tag_banner()` -- a
hard-edged rounded rectangle, gradient-gold fill, black bold all-caps text
-- replaces `eyebrow_pill()`'s quiet rounded pill for every impact card.

**Two-tone all-caps headline.** `draw_two_tone_headline()` -- most of the
headline in flat white, one or two key words in the gradient gold via
`gradient_accent=True` (default). Gradient text is positioned to sit on
the exact same baseline as the flat-white words on the same line -- if you
ever touch `gradient_text()`'s positioning math, verify baseline alignment
against a flat-color word on the same line; a tight-ink-bbox vs.
draw.text-default-anchor mismatch is a real, easy-to-reintroduce bug here.

**Circular collage inset + connector arrow -- hook cards (card 1) only.** A
second photo peeking through a gold-gradient-ringed circle, connected to the
main photo by a curved gold line (`circular_inset()` + `connector_arrow()`).
Using it on every card gets cluttered; reserve it for the highest-stakes
slide.

**CTA card: `full_scrim(alpha=175)`, a flat translucent wash, not a
gradient.** Text fills nearly the entire CTA card, so it needs even coverage
top to bottom -- a bottom-anchored gradient scrim was tried here too and
reverted; the flat wash is correct for this one card type specifically.

**CTA card staple: two-line title, white + cursive gold.** Line 1 in bold
white sans (e.g. "Your" / "Room to"), always `.upper()`-ed like every other
tag/headline in this system, and line 2 in the accent script font
(`get_script_font()`, Great Vibes, `assets/fonts/GreatVibes-Regular.ttf`)
filled with the metallic gradient (e.g. "Entry Point" / "Grow"). Always find
a two-line split for CTA title copy (short lead-in word + a gold noun
phrase) rather than falling back to `title_single` -- that path exists only
for copy that genuinely can't split this way.

**Fixed title zone for CTA cards.** `impact_cta_card()` reserves a constant
height (`TITLE_ZONE_H = 260`) for the title, bottom-aligned within it, so
the button lands in the same position on every CTA card regardless of
whether the title is one line or two. Don't let title length shift the
button -- that breaks the rhythm across a carousel and across properties.

**Stat/takeover card: dynamically centered headline block, not a fixed
offset from the bottom.** `impact_takeover_stat_card()` centers the
headline/sub block in the gap between the card's vertical midpoint and its
bottom edge -- computed from the actual wrapped text height, not a guessed
`bottom_pad` constant -- so it holds up even if the headline text length
changes on a future listing. The giant stat number itself renders in the
gradient gold via `gradient_text(..., stops=BRIGHT_GOLD_STOPS)`.

These come from `impact_hook_card()`, `impact_photo_card()`,
`impact_split_content()`, `impact_takeover_stat_card()`, and
`impact_cta_card()` in `carousel_lib.py` -- use these instead of the older
functions for any new property going forward.


## v3 impact static-image templates

The 4 standalone static images now have impact-system equivalents too --
same rules as the carousel cards (gradient gold everywhere, bold tag
banners, two-tone headlines where a headline has an accent word):

- `impact_static_stat_card()` -- standalone single-number image (e.g. "your
  entry point," "your rental offset"). Dimmed/blurred photo as background
  texture (this one intentionally stays soft-focus -- it's a backdrop for a
  big number, not a hero photo), `backdrop_panel()` behind the number for
  contrast, gradient tag banner + gradient "ESTIMATED" chip + the stat number
  itself in `gradient_text(..., stops=BRIGHT_GOLD_STOPS)`.
- `impact_static_blueprint()` -- a lightly-dimmed room photo with
  `partition_overlay()` (the dashed SKYBLUE diagram line -- unchanged, it's
  a deliberate technical-drawing exception to the gold-only palette) plus a
  gradient tag banner, a gradient callout chip, and a two-tone gradient
  headline over a bottom scrim.
- `impact_static_landscape()` -- two-photo `split_horizontal()` layout with
  a bottom bar carrying a two-tone gradient headline and a gradient gold sub
  line. Sized for link-preview-style landscape posts (e.g. 1200×628).
- `impact_static_comparison()` -- blurred/dimmed photo, `full_scrim()` (flat
  wash, same reasoning as `impact_cta_card()`: text/table fills nearly the
  whole card, so coverage needs to be even, not a bottom gradient), a
  gradient tag banner, and a label/value row table (`rows` param) with each
  value rendered in the gradient gold.

All four are wired into `scripts/template_build_impact.py`'s STATICS
section as the default for new properties.


## v3 additions from competitive research (real high-performing carousels)

Two patterns pulled from directly reviewing real high-performing Instagram
carousels (one civic/news carousel, one real-estate listing case study),
translated into Graeham's own black/gold brand rather than copied verbatim:

- **`impact_split_silent()` -- a text-free photo-pair breather card.** The
  listing case study we reviewed ran 3 of its 5 slides as pure split-photo
  pairs with zero text overlay, between the hook and the close -- letting
  strong renovation/staging photos do all the work instead of cramming copy
  onto every single card. `impact_split_content()` still exists for slides
  that need to make a specific point (tag + headline + sub); reach for
  `impact_split_silent()` as a deliberate pacing beat, not a default --
  don't replace every split card with the silent version, or the carousel
  loses its narrative thread entirely.
- **Inline keyword highlighting in sub/body text.** The news carousel we
  reviewed highlighted specific words *inside* smaller body copy, not just
  in the big headline. `draw_multiline_accent()` brings the same gradient-
  gold word-highlight treatment `draw_two_tone_headline()` gives headlines
  to sub-text -- wired in as an opt-in `sub_accent_words` param on
  `impact_hook_card()`, `impact_photo_card()`, `impact_split_content()`, and
  `impact_cta_card()` (default `None`, falls back to the existing plain
  white sub-text when not given). Use it to call out a specific number or
  phrase inside a supporting sentence ("all updated within the **last two
  years**") without needing to promote it to the headline.


## v4 -- "news card" fact-card format + locked bottom scrim (CONFIRMED FINAL)

A third format, for building a "breaking news" style carousel structurally
modeled on a civic-news account's actual fact-card layout (distinct from
`impact_photo_card()`, which is the normal tag-banner + big-headline
listing card):

- **`news_fact_card()`** -- bright, true-color photo (no sepia/duotone --
  that was tried for a "moodier" feel and explicitly rejected as looking
  muddy/cheap, not intentional). SUPERSEDED TEXT LAYOUT (see v5 section
  below): this card's text block now reuses `impact_hook_card()`'s own
  drawing calls verbatim -- `bold_tag_banner()` + `draw_two_tone_headline()`
  + `draw_multiline()`/`draw_multiline_accent()`, all left-aligned -- instead
  of the original centered icon+headline layout described when this v4
  section was first written. Kept for the round arrow button bottom-right
  (instead of the usual "SWIPE" pill) and the bright/no-grade photo
  treatment, both still current. Icon glyphs, if used elsewhere, must be
  plain ASCII/basic symbols (`$` `■` `K` etc.) -- unicode pictograms (emoji,
  ⬚, ⚑, etc.) silently render as a blank tofu box in this font stack. Verify
  any new icon character with `font.getmask(ch)` before using it.

- **`floor_fade_scrim()` -- the LOCKED bottom treatment, do not change.**
  This took five rounds of client back-and-forth to land on, so preserve it
  exactly rather than reverting to a plain linear `scrim_bottom()`:
  - A single linear gradient (`scrim_bottom`) cannot satisfy "hard black at
    the bottom, gently fading up" -- tuned to reach true black at the
    bottom edge, it crushes to near-solid black too early and reads as a
    flat box in anything but a full-height view; tuned to fade gently, it
    never actually reaches black anywhere and reads as translucent
    everywhere.
  - The fix is two deliberate pieces: a genuinely FLAT, fully-opaque black
    floor across the bottom `floor_frac` of the card (no gradient within
    that band at all), and a fade zone directly above it that eases from
    opaque to fully clear over the next `fade_frac` of height using
    `t ** power` (power > 1, so it stays mostly transparent near the top of
    the zone and accelerates toward the floor).
  - **Confirmed final values: `floor_frac=0.33, fade_frac=0.35,
    power=1.5, max_alpha=255`.** These are the defaults on
    `floor_fade_scrim()` and are baked into `news_fact_card()`. If a
    specific card needs more or less black, adjust `floor_frac`/`fade_frac`
    per-call -- but never drop back to a single continuous linear
    `vgradient` for this card type, and never re-introduce a photo color
    grade (sepia/duotone) here.

- **`impact_split_silent_bare()`** -- the same text-free photo-pair
  breather as `impact_split_silent()`, but with the logo/badge/footer/
  swipe-cue stripped entirely, matching a reference carousel whose gallery
  slides carried zero branding. Use this specific variant when the brief
  is to match that stripped-down pacing exactly; use `impact_split_silent()`
  (which keeps Graeham's branding) for normal branded carousels.

When building a "news style" carousel: hook + CTA still use
`impact_hook_card()` / `impact_cta_card()` (their tag-banner + headline
structure already matches the reference's own hook slide) -- only the
inner fact slides switch to `news_fact_card()`.

## v5 -- hook/fact-card text unification + lift mechanism + optional connector (CONFIRMED FINAL)

Later client review pushed the hook card and fact cards to converge even
further, and corrected a misconception about how to reposition a photo
inside its frame:

- **`news_fact_card()` text now matches `impact_hook_card()` exactly.**
  The original centered icon+headline+body layout (see v4 above) read as
  visually inconsistent against the hook card in an actual carousel swipe.
  `news_fact_card()` was rewritten to call the identical text-drawing
  sequence as `impact_hook_card()`: `bold_tag_banner()` for the tag pill,
  `draw_two_tone_headline()` for the big left-aligned headline with gold
  accent words, then `draw_multiline()` or `draw_multiline_accent()` for
  the sub-text. Both card types now anchor their text block from the
  bottom via a fixed `bottom_pad=110`, computed against `_impact_metrics()`.
  Both also use the exact same `floor_fade_scrim()` call
  (`floor_frac=0.33, fade_frac=0.35, max_alpha=255, power=1.5`) --
  `impact_hook_card()` previously used an older `scrim_bottom(h_frac=0.52,
  max_alpha=252)` which has been fully replaced.

- **`lift_px` on `base_photo_card()` -- pure vertical repositioning,
  distinct from zoom.** When a photo has too much empty sky/ceiling and
  too little subject visible, the fix is NOT to zoom in -- zooming changes
  the crop window and therefore the scale/framing of the subject, which is
  a different edit with different side effects. The correct fix is
  `lift_px`: after `cover_crop()` produces the final same-scale image, it
  gets pasted onto a black canvas offset upward by `lift_px` (`paste(im,
  (0, -lift_px))`), letting the top run off-canvas. The exposed black area
  at the bottom is harmless because `floor_fade_scrim()`'s opaque floor
  already covers that region. `impact_hook_card()` exposes this as
  `lift_main`, `news_fact_card()` as `lift`. Typical working values in this
  set: hook `lift_main=260`, price/fact cards `lift=180-220`. A `zoom`/
  `zoom_main` param also exists on both (crops tighter around the focus
  point before scaling up) -- use it only when the subject genuinely needs
  to be enlarged, not as a substitute for `lift_px`.

- **`show_connector` on `impact_hook_card()` (default `True`).** The gold
  curved connector arrow linking the main photo to the circular inset can
  be dropped entirely by passing `show_connector=False` -- the circular
  inset alone (no line) reads cleaner in some layouts, especially once the
  inset is positioned high/large enough to visually associate with the
  main photo on its own. Client-confirmed final look for the Bradley Way
  hook card uses `show_connector=False` with the inset raised to
  `inset_pos=("right", 0.13)` (near the top of the card, roughly at
  roofline height on a house photo) rather than the original lower/smaller
  placement.

