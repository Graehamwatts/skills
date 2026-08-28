# Long-Form Script Template

Fill-in structure derived from the 8-beat architecture in `production-grammar.md` §2, localized
for Graeham's markets (East Palo Alto, Palo Alto, Menlo Park, Redwood City, San Mateo County,
Santa Clara County / San Jose, San Francisco, East Bay). Target 8-16 min, ~190 wpm (matches the
corpus pacing — see `production-grammar.md` §7).

Two variants below: **Track A (market-data)** is the original Reventure-grammar template.
**Track B (lifestyle)** is a same-day derivative for zero-market-data, zero-doom content — see
`production-grammar.md` §11 for what changed and why, and `SKILL.md` Phase 1 for how a topic gets
sorted into one track or the other.

Every `[BRACKET]` must be filled from the Phase 2 citation table before the script is considered
done — no placeholder survives to production. Every `[CINEMATIC B-ROLL: ...]` tag must trace back
to a category (A-H) in the Phase 2 b-roll opportunity map — see `production-grammar.md` §9. Do
not add a cinematic tag that isn't doing evidentiary or emotional work.

**Tag legend:**
- `[SCREEN: ...]` — real screen-recording (website, dashboard, MLS, portal, event page)
- `[CHART: ...]` — branded data chart, dark "broadcast" or light "product UI" style per
  `production-grammar.md` §4 (Track A only — Track B has no charts)
- `[OVERLAY: ...]` — sparse text overlay (number callout or geo label only — see §4, do not
  invent a lower-third)
- `[CINEMATIC B-ROLL: Xs, category, ...]` — AI-generated cinematic insert via `higgsfield-video`.
  Always state duration (2-6s) and which gap category (A-H) it fills.

## Track A — Market-Data

```
[COLD OPEN — 0:00–0:20]
[No bumper. Cold, direct to camera or straight to a screenshot per production-grammar.md §1.]
The [superlative: biggest/fastest/first] [phenomenon] in [the Bay Area / San Mateo County /
NUMBER years] is happening right now — and [consequence for viewer's money].
According to [AUTHORITY: CAR / Zillow / Redfin / MLS data / Census / Chronicle — must be a real,
named, checkable source], [headline stat with exact number].
[SCREEN or CHART: the named authority's actual report/page — cut within 0-3s of naming them,
per production-grammar.md §5 rule 1]

[MACRO DATA STACK — 0:20–~2:00]
[2-4 stacked chart/data cutaways from independent sources, quick succession, 10-25s each.]
[CHART: source 1] [stat, spoken precisely, restated once in human terms]
[CHART: source 2] [stat]
[CHART: source 3, if available] [stat]

[CASE STUDY / ANECDOTE — one specific, checkable example]
[CINEMATIC B-ROLL: 3-5s, category B — establishing shot for this case study: exterior push-in /
"For Sale" sign / golden-hour light. Runs BEFORE the data, per production-grammar.md §5 rule 3 —
anecdote before abstraction, never the reverse.]
Like this listing in [city]. [SCREEN: real listing/portal screenshot] [Beds/baths, sq ft, list
price, purchase history: "the owner bought for $X in YEAR and is now asking $Y — that's a Z%
swing."]
[If this beat covers a foreclosure/delinquency/loss/consequence angle (category D): CINEMATIC
B-ROLL: 3-5s, category D — mood-appropriate visual (foreclosure notice, moving boxes, sold sign)
instead of leaving this as a bare text card.]

[MECHANISM — "why is this happening"]
[CHART or SCREEN: DTI/delinquency/capture-rate/correlation data — the "why" behind the macro
claim.]
[If this is an abstract statistical claim with no natural visual (category A): CINEMATIC B-ROLL:
2-4s, category A — supplements the chart, does not replace it.]

[CONTRARIAN / BALANCED-VERDICT BEAT]
A lot of people will tell you [conventional wisdom]. But the data says otherwise: [stat]. / OR:
[steelman the other side explicitly, then reconcile against a second source.]

[REGIONAL / BIFURCATION / MULTI-EXAMPLE MONTAGE]
[If this is a verbal list of places (category C): CINEMATIC B-ROLL: 2-3s each, category C —
quick per-location montage, paired with OVERLAY geo-labels per production-grammar.md §4.]
Now let's zoom into [city/zip]. [OVERLAY: geo label] [zip-level number vs. neighboring zip — the
bifurcation]. And the opposite is happening in [contrasting area]. [If this is a direct
comparison with no paired visual (category G): CINEMATIC B-ROLL: 2-4s, category G — a paired/
split visual for the two locations being contrasted.]

[DENSE ANALYSIS / OPINION STRETCH — this runs long, per production-grammar.md §5 rule 6: opinion
doesn't get a chart. Insert cinematic category-E b-roll roughly every 20-30s through this section
specifically — this is where the pacing otherwise goes flat, per production-grammar.md §7.]
[CINEMATIC B-ROLL: 3-5s, category E]
[2-3 paragraphs of uninterrupted analysis/speculation — the presenter carries this alone.]
[CINEMATIC B-ROLL: 3-5s, category E]
[continue analysis]

[ACTIONABLE ADVICE / RECAP]
So what do you actually do with this? If you're a buyer: [action]. If you're a seller: [action].
If you're an owner: [action].

[CTA — final 45-90s, live product demo per production-grammar.md §8]
[SCREEN: live demo of the actual Graeham tool/service, ideally reusing the SAME example shown
earlier as a callback.]
If you want to know what this means for YOUR street — not the Bay Area average, YOUR zip code —
[CTA: matches the education-graeham-videos end-card DM keyword — see that skill's standing brand
rules]. [If this section currently has no closing visual flourish (category H): CINEMATIC
B-ROLL: 3-5s, category H — a genuine cinematic close instead of a plain sign-off.]
[Sign-off per the brand end card — see education-graeham-videos SKILL.md for the exact spec.]
```

### Track A voice rules (unchanged from the corpus — write in this voice)

- Address the viewer: "everyone," "folks," "you guys" — 2-3× per minute, never zero.
- "Take a look at this" before every chart/screen cutaway.
- "Now," to pivot between sections.
- "One has to wonder..." for speculation; "Here's the thing everyone is missing..." for the
  contrarian turn.
- State every number precisely, then restate it once in human terms ("$8,700 a month — that's
  over $100,000 a year just to hold the mortgage").
- Rhetorical question chains for emphasis, 2-3 in a row, then answer them.
- Short sentences at emotional peaks. No corporate hedging. No "in today's video."
- Doom in the packaging, calibration in the verdict — the on-camera analysis stays honest even
  when the thumbnail/title is superlative.
- No em-dashes (TTS rule — see education-graeham-videos SKILL.md 0g; use commas instead).
- Prices as plain decimals without a leading $ sign in the VO script itself (TTS rule, same
  source) — captions restore the $ via the display map.

---

## Track B — Lifestyle (added 2026-08-12)

No macro-data stack, no mechanism/"why" beat, no contrarian/balanced-verdict beat — see
`production-grammar.md` §11 for why those get dropped. Runtime is typically shorter (6-10 min
rather than 8-16). Cinematic b-roll target is higher (25-40% vs. Track A's 15-25%) since there's
no chart to fall back on.

```
[COLD OPEN — 0:00–0:20]
[No bumper. Open on the vivid specific detail, not a doom-stakes claim.]
[CINEMATIC B-ROLL: 3-5s, category B — the single most vivid visual the story has (the themed
playground concept, the new restaurant's dish, the amphitheater at dusk). If the subject isn't
built/open yet, this shot needs the CONCEPT RENDERING label — see "Concept-rendering labeling"
below.]
[The hook is currency + specificity, not superlative fear: "A NUMBER project is breaking ground
two blocks from DOWNTOWN this week — and it's not what you'd expect."]
[SCREEN: a real source — the city press release, the business's own page, the event listing —
still cited even though this is a positive story. Zero negativity does not mean zero rigor.]

[THE SCENE — the bulk of the runtime, category B/F territory]
[CINEMATIC B-ROLL: 3-5s, category B or F — establish the place/thing itself.]
Take a look at this. [Concrete, checkable details: address, cost, capacity, who's behind it,
opening date.]
[Repeat this SCENE + CINEMATIC B-ROLL beat 2-4 times for a multi-part story — e.g. several new
openings in the same neighborhood, or several features of one new amenity — each beat gets its
own establishing cinematic shot per production-grammar.md §11.]

[WHY THIS MATTERS FOR THE VIEWER — replaces the mechanism/contrarian beats]
If you're thinking about [living here / spending a weekend here / moving to the area], this is
exactly the kind of thing that [makes NOW the time to look / most people don't know about yet].
[Curiosity/FOMO/opportunity framing per education-graeham-videos rule 0d — never "get out,"
always "get in before everyone else finds this."]

[CTA — final 30-60s]
[SCREEN or CINEMATIC B-ROLL: 3-5s, category H — a genuine cinematic close, not a plain sign-off.]
[CTA: a specific either/or or debate-style engagement QUESTION tied to the video's own content,
inviting a comment — NOT the DM-keyword system. See "Track B CTA mechanism" below for why.]
[Sign-off per the brand end card — logo + DRE# only, no DM-keyword button treatment.]
```

### Track B CTA mechanism (locked 2026-08-12, standing rule — read before scripting a CTA)

Track B does **not** use the DM-keyword/GHL-comment-automation system that Track A and
`education-graeham-videos` reel content use. Reasoning: the DM-keyword ask is built for
BOFU content where the viewer already has a specific, anxious situation they want a personalized
pull on (their own zip code's forecast, their own listing). A lifestyle video has no transactional
urgency — forcing a DM-keyword ask onto "the county built a fun new playground" reads as
bait-and-switch and likely hurts response rate rather than helping it. Comment engagement is also
a better fit for what this content is actually for: comment volume is a stronger YouTube
algorithmic signal than off-platform DMs, and Track B's whole job is top-of-funnel reach and
goodwill, not lead capture.

**The CTA is a specific either/or or debate-style question tied to the video's own content** —
matching the same "genuine either/or debate question" standard `education-graeham-videos` already
uses for pinned comments (see that skill's `references/script-templates.md` §E). A generic "share
your thoughts below" under-performs; a real, specific question doesn't. Example (Coyote Point
playground video): *"Would you rather have the zipline, or keep [the old playground] the way it's
always been?"* — draws directly on a beat already in the script rather than being bolted on.

End card for Track B: logo + DRE# only, same restraint as Track A — no DM-keyword gold button,
since there's no keyword to display. If a future Track B video's response data suggests adding a
soft, non-DM-keyword brand mention (a handle, a "more like this" pointer) would help without
reintroducing transactional pressure, that's a call to revisit with Graeham, not something to
add unilaterally.

### Concept-rendering labeling (locked 2026-08-12, standing rule — read before generating any
not-yet-built cinematic shot)

Track B pulls disproportionately from category B/F subjects that don't exist yet — a new
playground, a proposed building, a project under construction. Full spec lives in
`production-grammar.md` "Concept-rendering label convention"; the short version: any
`[CINEMATIC B-ROLL: ...]` tag depicting a not-yet-built subject gets an on-screen "CONCEPT
RENDERING" label (bottom-left panel, gold 2px top stroke, status + date subtext) on every shot
of that subject, not just the first one. Confirmed by Graeham via a direct A/B comparison on the
Coyote Point Playground video (generated both a labeled and unlabeled version of the cold-open
hero shot, picked labeled) — the reasoning: this channel's whole differentiator is citation
rigor, and one unlabeled "is this real?" shot undermines that credibility more than the label
costs in polish. When writing a `[CINEMATIC B-ROLL: ...]` tag for a not-yet-built subject, note
in the tag itself that it needs the label (see the Coyote Point script for the pattern) so
Phase 4 production doesn't miss it.

### Track B voice rules

- Same delivery cadence as Track A (viewer address, "take a look at this," "now," precise then
  human-terms numbers) minus anything doom-adjacent: no "biggest crash," no crisis framing, no
  myth-bust-the-skeptics energy.
- Every factual claim (address, cost, date, capacity) still needs a real source — positive
  framing is not a license to loosen citation discipline.
- Close on opportunity/curiosity, never absence/loss — per education-graeham-videos rule 0d,
  zero fear hooks, zero "before it's gone" scarcity-shaming.
- Same TTS rules apply: no em-dashes, prices as plain decimals without a leading $ sign.
- CTA is a comment-engagement question, not a DM keyword — see "Track B CTA mechanism" above.

---

## Cinematic-b-roll density check (run before finalizing either track's script)

Add up every `[CINEMATIC B-ROLL: Xs, ...]` tag's duration, divide by the target total runtime.
Track A should land in the 15-25% band; Track B in the 25-40% band (`production-grammar.md` §10,
§11). If it's under target, check the opportunity map from Phase 2 for missed category-A/B/D/E/F
beats. If it's over target, cut the least evidence-grounded tags first — every surviving tag
should trace to a specific category and a specific claim, not just be "a nice shot."
