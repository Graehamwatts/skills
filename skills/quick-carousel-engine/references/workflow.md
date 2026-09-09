# Quick Carousel Workflow

The actual step-by-step process. Target: ~15-20 minutes from a real data
point to finished JPGs ready to post.

## Step 1 — Pick a category and a real input

Read `template-categories.md`, pick ONE of the three categories, and gather
its real inputs:

- **Category 1 (Trend/Stat):** one current, dated stat with a named source
  (Zumper, Redfin, Windsor/Search Console pull, a fresh web search). Range
  language is fine for anything perishable ("$X-$Y" rather than a single
  hard number) — same rule `production-hardening.md` already enforces for
  scripts.
- **Category 2 (Price Comparison):** real active/recent comps across the
  sub-markets being compared, from `mls-matrix-scraper` or a quick MLS
  Matrix pull.
- **Category 3 (Listing Snapshot):** this week's real PropCast/MLS listing
  counts, not last week's.

**Data-integrity rule (non-negotiable):** every stat card needs a
`source_note` naming where the number came from and the month. If you don't
have a real, current number for a slot, cut that card rather than invent
one. A carousel with 3 well-sourced cards beats one with 5 cards where 2 are
made up.

## Step 2 — Fair Housing check

Before writing a single word of copy, re-read
`content-creation-engine/CLAUDE.md`'s "FAIR HOUSING AND ETHICS GUARDRAILS"
section. It applies to carousels exactly as it does to scripts: no
demographic framing of neighborhoods, no "safe/good area" language, no
school-quality comparisons. If a Category 2 comparison starts to read like
it's ranking sub-markets by who lives there rather than by price/sqft/beds/
baths/lot size, rewrite it or drop that angle.

## Step 3 — Build

1. Copy `scripts/quick_carousel_build.py` to a scratch location (or just
   edit a copy in place if that's easier — the important thing is never
   editing the checked-in template file directly, same convention as
   `carousel-builder/scripts/template_build_impact.py`).
2. Delete the card calls for the categories you didn't pick.
3. Replace every `[bracketed placeholder]` with real copy and real numbers.
   Keep `CONFIG["contact_line"]` as `"Graeham Watts  .  Compass  .  DRE
   #01466876"` — read `skills/shared-references/identity.json` if you're
   ever unsure of the current brand line; don't hardcode it from memory.
4. Run `python3 build.py`. It needs Pillow (`pip install Pillow` if the
   environment doesn't have it yet).
5. Open the output JPGs and actually look at them — check no text is
   clipped or overlapping (long labels can still overflow if the card type
   wasn't designed for that; shorten the copy rather than shrinking the
   font past legibility).

## Step 4 — Caption + post

Standard IG carousel caption pattern (mirrors the SFGate reference note):
one jaw-dropper opening line, 2-3 sentences of context, a soft CTA that
matches the closing card's `keyword_line`. Cross-post to Facebook as-is;
this format doesn't need TikTok/YouTube derivatives (those are photo/video
formats, not carousel-native).

Post the carousel, or hand the JPGs + suggested caption to Peter/Ellie if
they're the ones publishing.

## Step 5 — Log it

`content-calendar`'s weekly analytics pull (Windsor Instagram data) will
pick this post up automatically in the next weekly performance review —
no separate tracking needed. If this post is part of the format A/B test
(see `content-calendar/references/testing-roadmap.md`), note which topic
it paired with so the comparison is apples-to-apples.

## Common mistakes (from the first build/test pass, 2026-09-09)

- **Long labels overlapping the value below them.** `quick_rank_card` and
  `quick_title_card` measure wrapped-line height dynamically now, but a
  genuinely long label (a full sentence instead of a short name/stat) will
  still crowd the card. Keep `label_text`/`headline_text` short — this is a
  swipeable card, not a paragraph.
- **Shipping a placeholder.** Every `[bracketed]` value in
  `quick_carousel_build.py` must be replaced before the JPGs go anywhere
  near a post. The build script runs fine with placeholders in — that's
  intentional, so you can review layout before the real copy is ready — but
  "it ran" is not the same as "it's postable."
