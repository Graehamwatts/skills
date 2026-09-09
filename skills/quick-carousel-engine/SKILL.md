---
name: quick-carousel-engine
description: Generates fast, low-effort, no-photo-required Instagram carousel posts (trending market-data carousels, ranked comparison lists, Peninsula listing-snapshot carousels) for Graeham Watts using a PIL-based image engine, so Peter and Ellie always have something quick and engaging to post even in a week when the full weekly video slots eat all their time. Use this skill ANY time the user asks for "easy carousels," "quick posts," "something fast for Peter/Ellie to post," a "trending data carousel," a carousel like a competitor/influencer's account is running (e.g. migration-data or "$X gets you here" style posts), or a low-effort supplement to the main weekly content-calendar slots. Distinct from carousel-builder, which is a heavy, research-intensive pipeline for ONE property's real listing photos — this skill needs zero-to-one photos and ~15-20 minutes, and is never about a single property. Reuses carousel-builder's brand engine (fonts/colors/logo) but ships its own photo-free card templates.
---

# Quick Carousel Engine

Fast carousel posts, additive to the main weekly content-calendar cadence. Built
2026-09-09 after Graeham flagged that other Bay Area agents (e.g. the
`kenny_fast` Instagram account) run a steady stream of quick, data/trend-driven
carousels that Peter and Ellie don't have an easy way to replicate — the two
existing image pipelines (`carousel-builder`, the weekly calendar's derivative
IG Carousel format) both require either real property photos or a fully
researched/scored topic. This skill fills that gap with its own lightweight
lane. No subscription service (Graeham explicitly declined that route,
2026-09-09) — everything here is built from this repo's own data sources and
brand system.

## Where this fits (read this before building anything)

| Pipeline | Input | Effort | Output |
|---|---|---|---|
| `carousel-builder` | ONE property's real photos + market research | ~1-2 hrs | 15-asset branded package for that listing |
| `content-calendar` → `content-creation-engine` | ONE fully-scored weekly topic | Full research pipeline | 14-format package incl. an IG Carousel derivative |
| **`quick-carousel-engine` (this skill)** | ONE trend/stat/ranked list, zero-to-one generic photos | ~15-20 min | 4-6 card carousel, no property or full topic-scoring required |

This is an **additive** lane, not a replacement for the 5 weekly slots in
`content-calendar`'s V6 system. See that skill's "Quick Carousels" section
(added alongside this skill) for the suggested weekly cadence.

## The three template categories

Read `references/template-categories.md` before building — it has the full
reverse-engineered structure for each category, including the two proven
viral references this borrows from (`viral-hook-library`'s notes 13 and 15).
Summary:

1. **Trend/Stat Editorial Carousel** — one public data point as the hook,
   then a short data barrage, a region-wide zoom-out, then CTA. This is the
   direct analog of the "Where People Are Moving" / migration-data style
   posts Graeham pointed to.
2. **Price/Market Comparison Carousel** — "what $X gets you" across
   Graeham's own sub-markets (EPA/RWC/PA/MP/SMC), one ranked card per
   sub-market with identical layout so only the number changes swipe to
   swipe.
3. **PropCast Listing Snapshot** — sourced from Graeham's OWN live
   listing/PropCast intelligence (via `mls-matrix-scraper` or whatever feed
   is current), not public trend data. "N new listings this week" style.

**Never ship a category-1 or category-2 carousel with an invented number.**
Every stat needs a real, dated source (see `references/workflow.md`'s
data-integrity rule) — this is the same non-negotiable rule
`content-creation-engine/references/production-hardening.md` already
enforces for scripted content, applied here to carousels.

## Quick start

1. Read `references/workflow.md` in full — the actual step-by-step process
   Peter/Ellie (or whoever is running this) follows.
2. Pick ONE category above and gather its real inputs (a fresh stat + source
   citation, or this week's real PropCast listing counts). Don't fabricate.
3. Copy `scripts/quick_carousel_build.py` to a scratch location, delete the
   card calls for the categories you didn't pick, fill in every placeholder.
4. Run it: `python3 build.py`. It imports `scripts/quick_carousel_lib.py`
   (photo-free card templates) which in turn imports fonts/colors/logo/pills
   straight from `../carousel-builder/scripts/carousel_lib.py` — that
   dependency is intentional, keep both skills in the repo together.
5. Review the output JPGs, then hand off to Peter/Ellie (or post directly)
   with the caption guidance in `references/workflow.md`.

## Files in this skill

- `scripts/quick_carousel_lib.py` — the photo-free card engine:
  `editorial_rank_list_card` (light-bg, two-column tinted ranked list — the
  direct "Where People Are Moving" analog, usually shippable as ONE
  standalone image, not a carousel — this is the flagship card, reach for
  it first for any ranked/comparison topic), `quick_title_card` (dark-bg
  hook/title, no photo), `quick_rank_card` (one ranked list entry — city,
  stat, whatever), `quick_table_card` (dark-bg label/value table, the
  workhorse for "top N" lists), `quick_cta_card` (closing card with the
  gold button). Also re-exports `impact_takeover_stat_card` from
  carousel-builder directly (already photo-free, no need to duplicate it).
- `scripts/quick_carousel_build.py` — the per-post driver, one worked example
  per category (commented out for categories 2 and 3 — uncomment the one you
  need). Copy this file per post, same convention as carousel-builder's
  `template_build_impact.py`.
- `references/template-categories.md` — the reverse-engineered structure for
  each of the 3 categories, with the source viral references.
- `references/workflow.md` — the actual production process, data-integrity
  rule, and Fair Housing reminder for whoever runs this weekly.

## Scope

Images only, same as `carousel-builder`. If a topic deserves a video too (or
you're running the format A/B test noted in `content-calendar`'s testing
roadmap), that's a separate `content-creation-engine` / `viral-video-engine`
build — mention the handoff, don't try to generate video from this skill.

Not for a single property's listing photos — that's `carousel-builder`. Not
for a fully-scored weekly topic's full 14-format package — that's
`content-creation-engine`.
