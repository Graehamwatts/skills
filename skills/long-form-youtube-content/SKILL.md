---
name: long-form-youtube-content
description: "Long-form YouTube content creation for Graeham Watts — builds Reventure-grammar long-form videos (8-16 min) with AI avatar production and generated cinematic b-roll, covering both market-data topics (Track A) and positive lifestyle topics (Track B). Use ANY time the user says: create a long-form video, long-form YouTube video, long-form script, make today's long-form video, or asks for a Top 10 list of long-form video topics (market-data or lifestyle). Separate from education-graeham-videos, which owns short-form reels. Always starts with Phase 1 topic research presenting a scored Top 10 across both tracks — never jumps straight to a script."
---

# Long-Form YouTube Content Creation — Graeham Watts

> **One job:** Turn a verified Bay Area real-estate or lifestyle story into a Reventure-grammar
> long-form YouTube video (8–16 min), built entirely with AI production (avatar, voice, generated
> cinematic b-roll) instead of a human host and crew — while fixing the one thing Reventure
> itself does badly: almost never showing you what the script is talking about.

## Why this skill exists (read this before doing anything else)

This skill is the direct output of a dedicated research project: 8 full @ReventureConsulting
long-form videos were downloaded, transcribed word-for-word (local Whisper), and frame-by-frame
vision-analyzed end to end — not sampled, not skimmed. Every rule below traces to that evidence.
Full source material lived at `/home/claude/reventure_research/` in the session that produced
this skill (8 `production-blueprint.md` files + `CROSS_SYNTHESIS.md`) — if that research needs
to be re-verified or extended, re-run it via `video-watcher` rather than re-deriving from scratch.

**This is a deliberate split from `education-graeham-videos`.** That skill still owns short-form
reels and the paired reel+long-form workflow. This skill owns long-form ONLY, and goes deeper on
the long-form-specific grammar than the older skill's Reventure notes did (those were based on 5
videos watched once, not 8 videos analyzed frame-by-frame with transcript alignment). Once this
skill is proven out, its findings should fold back into (or replace) the long-form half of
`education-graeham-videos`. Until then, treat this as the source of truth for long-form.

**The one deliberate divergence from Reventure, stated up front because it drives every
production decision in this skill:** Reventure's videos are ~98–100% screen-recording / static
chart / talking-head. Genuine cinematic motion b-roll is nearly absent from their catalog — well
under one minute of it across 8 videos totaling over 2 hours. Graeham's version keeps Reventure's
pacing, citation discipline, and script-to-footage timing rules, but targets **15–25% of runtime
as real cinematic b-roll** (AI-generated via Higgsfield, per `higgsfield-video` skill), inserted
using Reventure's own proven discipline: short (2–6s), hard-cut, tied to one specific noun/claim/
emotional beat — punctuation, not sustained coverage. See `references/production-grammar.md`
§9–10 for exactly where this footage goes and why.

## Relationship to other skills (compose, don't duplicate)

| This skill needs... | Provided by |
|---|---|
| Trending topic research, citation table, fair-housing/compliance rules, brand end-card spec, TTS/audio QC rules, avatar look-pair build process, HeyGen/Higgsfield production mechanics, full-sweep QC checklist | `education-graeham-videos` — read its `SKILL.md` and `references/production-pipeline.md` before building. This skill does NOT re-document those; it only adds/overrides what's long-form-specific. |
| Cinematic b-roll generation (start frame + animation) | `higgsfield-video` — follow its Realism Rescue Protocol, Anonymization Strategy, and model-routing rules for every cinematic insert this skill calls for. |
| Analyzing a NEW reference video (competitor, viral outlier, format update check) | `video-watcher` — the exact pipeline this skill's research was built on. Re-run it if Reventure's format visibly shifts, or to analyze a channel other than Reventure. |

If any of those three skills conflict with something written here, the conflict is a signal to
resolve explicitly with Graeham — don't silently pick one.

## Trigger

Fires on: "make a long-form video about X", "write the long-form script for X", "build the
YouTube video for X", "create a long-form video for the day", or as the long-form half of the
standard reel+long-form pairing workflow (`education-graeham-videos` Phase 3 onward hands off the
long-form leg here). Short-form-only requests stay in `education-graeham-videos`.

## Workflow

### Phase 1 — Topic (skip if already provided)

**ALWAYS present a scored Top 10, never fewer, never jump straight to a script.** (Locked
2026-08-12, per Graeham's explicit standing instruction — this overrides
`education-graeham-videos`' Top 5 default whenever this skill is the one running Phase 1.)

Research across **two parallel tracks**, both in scope every time this phase runs unless Graeham
has already told you which track he wants:

**Track A — Market-data (the original Reventure-grammar track).** Use
`education-graeham-videos` Phase 1 sourcing as-is: news (SF Chronicle, Mercury News, SFGATE, Palo
Alto Online, Almanac, Redwood City Pulse, EPA Today, Bloomberg/WSJ/Fortune with a Bay Area angle),
data drops (CAR, Zillow Research, Redfin Data Center, Case-Shiller SF, FRED, Census/ACS
migration, rate moves), local signals (MLS stats via `mls-matrix-scraper` when available, notable
listings). Doom-hook packaging is fine here; the in-video verdict stays calibrated (per
`education-graeham-videos` rule 5).

**Track B — Lifestyle (added 2026-08-12, standing addition, always run alongside Track A).**
Zero market data, zero doom-adjacent framing of any kind — pure "why you'd want to be here right
now." Search fresh (last 7–14 days, or an evergreen "what's new this summer/season" roundup):
new restaurant/coffee-shop/business openings, new or renovated parks/playgrounds/trails, free
community events (concerts, theater, festivals), new public amenities (libraries, community
centers, accessible/all-abilities features), and anything that gives Graeham's farm areas (East
Palo Alto, Palo Alto, Menlo Park, Redwood City, San Mateo County, Santa Clara County/San Jose,
San Francisco, East Bay) a "get in before everyone figures out how good this is" pull. This is
the same emotional register as `education-graeham-videos` rule 0d (lifestyle series — attraction,
not doom) — apply that rule's zero-negativity standard here too, and route every Track B pick
through it before scripting.

**Scoring.** Score every candidate from both tracks 1–10 on: local relevance (Graeham's farm
areas), data/source availability (can every claim be verified and cited?), hook potential
(superlative/timeliness/authority-peg for Track A; vividness/currency/"wow" specificity for Track
B), and audience value (does a buyer/seller/owner/resident get something real out of it?). Present
all 10 as one table — mixed tracks, ranked by score, with a `Track` column so Graeham can see at a
glance which lane each pick is in:

| # | Track | Topic | Hook angle | Authority/source peg | Score |

Close with a one-line recommendation of which YOU would pick and why, and flag if any pick is
especially well-suited to stress-testing the cinematic-b-roll divergence (§9 categories in
`production-grammar.md`) — some stories are much richer cinematic material than others, and it's
worth saying so before Graeham picks. Wait for his choice.

### Phase 2 — Deep research + citation table + b-roll opportunity map

Use `education-graeham-videos` Phase 2 (primary/secondary sourcing, bifurcation, listing
autopsies, asset grab list) as-is for Track A topics. For Track B (lifestyle) topics, the
equivalent is: verify every specific detail (address, price, date, capacity, who's behind it)
against at least one primary source (city/county press release, the business itself, an official
event page) plus the news article that surfaced it; skip the citation-table's price/market-data
columns entirely — a lifestyle video's "receipts" are dates, addresses, and named people/
organizations, not $ figures.

**B-roll opportunity map (both tracks).** While researching, tag every fact/claim/beat against
the 8 gap categories in `references/production-grammar.md` §9 (abstract macro claim, case-study/
anecdote, location list, emotional/consequence beat, dense analytical stretch, named-but-unshown
mechanism, comparison/contrast, CTA close). This becomes the shot list input for Phase 3 — you
cannot write accurate `[CINEMATIC B-ROLL: ...]` tags in the script without knowing, up front,
which beats in THIS story fall into which category. Lifestyle topics skew heavily toward category
B (case-study/scene moments) and F (a named-but-unshown place/thing, e.g. a themed playground or
a new restaurant's interior) — expect a HIGHER cinematic-b-roll % than a pure market-data video,
since there's no chart to fall back on and the whole point is "come see this."

### Phase 3 — Script

Use `references/script-template.md`. It is `education-graeham-videos`' long-form template with
the beat structure corrected against the deeper 8-video evidence (see
`references/production-grammar.md` §2 for what changed and why) and a new inline tag,
`[CINEMATIC B-ROLL: ...]`, added alongside the existing `[SCREEN: ...]` / `[CHART: ...]` /
`[OVERLAY: ...]` visual-direction tags. Track B (lifestyle) scripts drop the market-data beats
(macro data stack, mechanism/why, contrarian verdict) and keep only cold open, case-study/scene
beats, and CTA — see the template's Track B variant. **Track B CTA (locked 2026-08-12):** a
specific either/or engagement question inviting a comment, not the DM-keyword system — that stays
reserved for Track A/transactional content. Full reasoning and the end-card spec in
`script-template.md` under "Track B CTA mechanism." **Concept-rendering labeling (locked
2026-08-12):** every `[CINEMATIC B-ROLL: ...]` tag depicting a subject that isn't built/open yet
(common on Track B — a proposed playground, a project under construction) must note that it needs
an on-screen "CONCEPT RENDERING" label. Full spec in `production-grammar.md` "Concept-rendering
label convention" and `script-template.md` "Concept-rendering labeling."

Rules for placing `[CINEMATIC B-ROLL: ...]` tags (full detail in `production-grammar.md` §10):
- Every tag must trace to a specific gap category from Phase 2's opportunity map — no
  decorative inserts with no evidentiary or emotional job to do.
- Track A target: 15–25% of total runtime in cinematic b-roll, concentrated in categories A
  (abstract macro claims), B (case-study opens), D (emotional/consequence beats), and E (long
  opinion/analysis stretches, one insert roughly every 20–30s to prevent avatar monotony).
- Track B target: higher, roughly 25–40% of runtime — a lifestyle video's entire job is showing
  the place/thing, so cinematic coverage of category B and F beats should run generously. Still
  keep individual inserts short (2–6s) and hard-cut per the timing discipline; "more of them," not
  "longer ones."
- A cinematic tag SUPPLEMENTS a citation-triggered data cutaway on Track A, never replaces it.
  Track B has no citation cutaway to protect in the same way, but still needs a real photo/
  screenshot of the actual place/business/event alongside the cinematic shot when one exists (the
  venue's own listing, a city press photo, the business's real signage) — cinematic footage
  dramatizes the real thing, it doesn't invent a generic stand-in for it.
- Keep the tag duration short: write `[CINEMATIC B-ROLL: 3s, ...]` not `[CINEMATIC B-ROLL: 15s,
  ...]`. Sustained cinematic sequences break the format's fast, data-dense rhythm — see
  `production-grammar.md` §5 rule 5.

### Phase 4 — Production

Follow `education-graeham-videos` `references/production-pipeline.md` for everything avatar/VO/
compositing-mechanical (accounts, HeyGen, Higgsfield look pairs, SFX mix architecture, QC). This
skill's only production-specific addition: every `[CINEMATIC B-ROLL: ...]` tag in the approved
script becomes one `higgsfield-video` generation job. Run those generations in the same pass as
the location look-pair build (Step 0–4 of the production pipeline) so nothing gets forgotten
mid-composite. Long-form orientation is always landscape 16:9 (per the standing LOOK PAIRS rule)
— cinematic b-roll generations should be requested in 16:9 to match, not cropped/reframed from a
9:16 asset built for a paired reel.

### Phase 5 — QC

Full-sweep QC per `education-graeham-videos` `SKILL.md` checklist, plus two long-form-specific
additions: **cinematic-b-roll placement audit.** For every `[CINEMATIC B-ROLL: ...]` tag in the
script, verify in the final render that (a) it lands within the timing rules in
`production-grammar.md` §5, (b) it did not delay or crowd out the citation-triggered data cutaway
it was paired with (Track A only), and (c) total cinematic-b-roll runtime falls in the target band
for its track (15–25% Track A, 25–40% Track B) — log the actual % achieved so it can be tracked
video over video. **Concept-rendering label check (locked 2026-08-12):** every cinematic shot of
a not-yet-built subject carries the "CONCEPT RENDERING" label (see `production-grammar.md`
"Concept-rendering label convention") on every frame it appears in, not just its first
appearance — a viewer who skips ahead should never land on an unlabeled frame.

## Reference files

- `references/production-grammar.md` — the full codebook: hook formula, beat structure, b-roll
  grammar (with exact aggregate percentages and every genuine cinematic shot found in the
  8-video corpus), talking-head shot grammar, text/graphics system, script-to-footage timing
  rules, transition style, pacing arc, CTA/branding system, the cinematic-b-roll gap analysis,
  and the adopt-as-is-vs-diverge synthesis. This is the evidence base — read it before writing
  a script, not after.
- `references/script-template.md` — fill-in long-form script template with the corrected beat
  structure and the new `[CINEMATIC B-ROLL: ...]` tag convention, including a Track B (lifestyle)
  variant.

## Open items / what this skill does NOT yet cover

- Only 8 videos were analyzed (the original target was "at least 10"). The patterns are
  consistent enough across all 8 that they're being treated as reliable, but if a 9th/10th video
  analysis surfaces a contradiction, update `production-grammar.md` rather than assuming the
  first 8 were representative.
- No video has yet been produced end-to-end using this skill's `[CINEMATIC B-ROLL: ...]`
  convention. The 15–25% (Track A) / 25–40% (Track B) targets and the "2–6s, hard cut, punctuation
  not coverage" insertion discipline are evidence-grounded predictions of what will work, not yet
  field-tested. Track the first 2–3 productions closely and tighten/loosen the target based on
  actual retention/feedback, the same way `education-graeham-videos` iterated its short-form
  rules.
- Track B (lifestyle) is a 2026-08-12 addition and has zero video-corpus evidence behind its own
  numbers — the 25–40% cinematic target and the "no chart to fall back on" reasoning are a
  reasonable extrapolation from the Track A research, not something separately verified against
  lifestyle-format reference videos. If Graeham wants that verified the same way Track A was,
  it would mean sourcing and analyzing lifestyle-format long-form videos (a different reference
  channel — Reventure doesn't run this track) the same way the original 8 were analyzed.
- Titles, thumbnails, and descriptions for long-form are not re-derived here — use
  `education-graeham-videos` `references/script-templates.md` §C–E as-is; nothing in the 8-video
  research changed those.
