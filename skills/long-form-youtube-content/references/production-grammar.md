# Long-Form Production Grammar — Full Codebook

Source: 8 full @ReventureConsulting long-form videos, downloaded and analyzed frame-by-frame
(scene-change + coverage-floor extraction, ~35-80 frames per video) against a word-level local
Whisper transcript, August 2026. Combined runtime ~2h05m.

Corpus: 01 ABC Foreclosure (15:52) · 02 BofA Creditmaxxing (16:43) · 03 Bloomberg Demographic
(16:55) · 04 D.R. Horton Cancellation (16:06) · 05 Fannie Mae Bankruptcies (15:57) · 06 Meta AI
Bubble (14:44) · 07 The Dam Has Broken (13:55) · 08 WSJ Six-Figure Losses (15:12).

Format split (matters throughout this document): 01, 03, 04, and the front half of 06 are
**studio format** (static webcam talking-head + browser/dashboard screen recordings, home office
backdrop). 02's back half, 05, 07, 08 are **walk-and-talk format** (handheld/gimbal selfie
camera, host physically on location). Where a rule differs by format, both are given.

Full individual video blueprints (400-600+ lines each, full per-scene notes) were archived at
`/home/claude/reventure_research/0{1-8}_*/production-blueprint.md` in the research session —
this document is the distilled, actionable synthesis of all 8, not a replacement for them if
deeper evidence is ever needed. Re-run `video-watcher` on the corpus if that archive is gone and
the underlying evidence needs re-verification.

**Scope note (added 2026-08-12):** everything below was derived from Reventure's market-data
format (Track A in `SKILL.md`). Track B (pure lifestyle, zero market data) is a same-day addition
built by extrapolation, not by analyzing a lifestyle-format reference corpus — see §11.

---

## 1. Hook Formula (0:00–0:10)

No video in the corpus uses a title card, channel bumper, intro music sting, or "hey guys welcome
back." All 8 open cold with the same 3-beat structure:

**Assert → Specify → Prove.**
1. Spoken thesis claim with maximum-stakes framing ("biggest," "warns," "collapse," "depression")
2. A named, checkable authority source (ABC News, Bank of America, Bloomberg, D.R. Horton, Fannie
   Mae, Meta/its CEO, [an unnamed persistent decline], the Wall Street Journal)
3. Within 0–3 seconds of the name being spoken, hard cut to a full-screen screenshot of that exact
   source, visually proving the claim

First-cut timings across the corpus: 01=0:09, 02=0:16, 03=0:11, 04=0:17, 05=~0:06, 06=0:08–0:10,
07=0:05, 08=0:07–0:09. Five of 8 (02, 05, 06, 07, 08) cut to a screenshot/chart BEFORE the host's
face ever appears; only 01, 03, 04 open talking-head-first. Zero videos use a text hook overlay,
a pattern-interrupt zoom, or an SFX stinger in the first 10 seconds — all hook urgency comes from
vocal delivery and word choice, not editing tricks.

**Write it this way:** cold open, no bumper, superlative thesis sentence naming a real checkable
source in the first breath, hard cut to that source's actual screenshot within 0–3s of the name,
host's face on screen within the next 10–20s delivering the specific number behind the claim.

---

## 2. Beat Structure

A consistent macro-structure recurs across all 8, though the middle beats' order/weight shifts by
format (studio = tighter/faster cuts through the skeleton; walk-and-talk = beats stretch across
physical location changes, longer uncut opinion stretches tolerated).

1. **Cold open / hook** (0:00–~0:20) — universal, all 8. See §1.
2. **Macro data establishing severity** (0:20–~2:00) — 2-4 stacked chart/data cutaways from
   multiple sources in quick succession. Universal, compressed in the two shortest videos (07, 08).
3. **Case study / anecdote ("receipts" beat)** — one specific, checkable example: a real listing,
   a physical house walked to, a human-interest quote. Present in 7/8 (06 substitutes
   source-stacking instead of a single anecdote). **Hard rule: the anecdote always precedes the
   chart that generalizes it, never the reverse** — see §5 rule 3.
4. **Mechanism / "why is this happening"** — DTI ratios, delinquency-vs-income, a cited white
   paper, capture-rate data, cost breakdowns, correlation findings. Present in all 8; this is
   where Reventure's own proprietary app data first typically enters.
5. **Contrarian / balanced-verdict beat** — explicit steelmanning or caveats (e.g. inflated
   spending data from a one-off event; a revenue counter-argument to the bubble thesis; two
   sources reconciled against each other). Present in 7/8, weakest in 01 and 05.
6. **Regional / bifurcation / multi-example montage** — rapid tour of states/cities/zips via a
   map tool or physical walking. Universal, all 8.
7. **Actionable advice / recap** — direct practical guidance or a summarizing thesis line. Present
   in 01, 02, 05, 07; thinner in 03, 04, 06.
8. **CTA / product demo** (final ~5–10% of runtime) — universal, all 8. See §8.

**Universal, never skip:** cold open + citation, macro data stacking, mechanism section, regional/
multi-example beat, CTA close. **Near-universal, include unless there's a specific reason not
to:** case-study anecdote, contrarian beat.

---

## 3. B-Roll & Visual Grammar (the aggregate composition)

| Shot type | Approx. % of runtime | Notes |
|---|---|---|
| Talking-head (studio static OR walk-and-talk selfie) | 26–70%, format-dependent | Studio videos run lower (01 ~36%, 04 ~26%); walk-and-talk runs much higher (05 ~68%, 07 ~65–70%) |
| Screen-recording of real websites/dashboards | 20–40% | Present in all 8 |
| Screen-recording of the proprietary Reventure App | 5–27% | Present in all 8, deliberately withheld early — see §8 |
| Talking-head PIP over screen-recording | large share of studio screen-time (e.g. ~60% in 04) | Studio-only convention; absent from pure walk-and-talk (05, 07, 08) |
| **Genuine cinematic/stock/motion b-roll (not a screen recording)** | **~0–2%, effectively zero in 6 of 8 videos** | **This is the gap this skill exists to fill — see §9–10** |

Across the full ~2h05m corpus, genuine cinematic b-roll totals well under one minute. Every single
instance found, with exact context, because these are the closest things to in-format precedent:

1. **Video 03, ~2:13** — stock aerial of Osaka/Japan skyline, cut precisely on the word "Japan."
2. **Video 03, ~3:18** — stock Shanghai riverfront skyline, cut on "China."
3. **Video 03, ~4:15** — stock Toronto aerial, cut on "Canada." *(Pattern across all three: used
   exclusively when naming a foreign country, a brief flash-cut stinger 1-3s long, immediately
   followed by a return to real data — never sustained, never repeated for the same country.)*
4. **Video 06, 0:08** — aerial drone shot of a real hyperscale data-center campus, opening the
   video before any chart or face appears.
5. **Video 06, 3:41** — interior tracking shot down server racks, timed to the phrase "GPU chips
   in the server."
6. **Video 06, 3:51** — a second aerial data-center shot, looser word-pairing. *(Pattern: reserved
   exclusively for the literal nouns "data center(s)" / "server(s)," clustered in the first 3:51
   of a 14:44 video, never recurring later even though the AI-infrastructure topic continues.)*
7. **Video 07, 5:08** — the one quasi-cinematic beat outside 03/06: a composed low-angle static
   driveway shot (still shot on the host's own phone, not licensed footage) marking a topic pivot.
   Flagged in the source blueprint as "the exception that proves the rule."

Everything else in the corpus — the other 98%+ — is either a real screen-recorded browser/
dashboard (cursor visible, scrollbar visible, browser chrome sometimes left uncropped as a
deliberate authenticity signal) or raw handheld/selfie walking footage with zero color grading or
stabilization polish.

---

## 3b. Talking-Head / Avatar Shot Grammar

**Studio format** (01, 03, 04, 06, front half of 02): static locked-off camera, no pans, no
zooms, no reframing of the host. Centered medium close-up, direct eye contact, consistent
warm-toned home-office backdrop (tan wall, framed US map, an award plaque — implicit authority
branding). Shot-type alternates full-frame (host disappears, visual "is" the content) vs. PIP
bottom-left at ~20-25% frame width (host "using" a visual). No zoom/punch-in on the host himself —
only simulated Ken-Burns pans on static screenshots. Frequent jump-cuts inside a single continuous
take (trimming pauses/breaths), visible via small shirt/lighting shifts between adjacent scenes —
this is a usable authenticity signal, not something to sand out.

**Walk-and-talk format** (02 back half, 05, 07, 08): handheld/gimbal at arm's length, visible
wobble, no true stabilization, occasional fisheye. Continuous walking substitutes for cuts — no
PIP convention exists in this format; graphics are full-screen cutaways with no host inset. Only
2-3 non-face shots in the entire walk-and-talk portion of the corpus, always the same phone camera
swung away, never a separately produced insert.

**Cross-format constant:** max sustained talking-head duration is content-driven, not on a fixed
clock, but studio format caps lower (~45–90s before a cut) than walk-and-talk (up to ~2:14
continuous) — see §5 rule 7 for exactly when the longer stretches are allowed.

---

## 4. On-Screen Text & Graphics System

Extremely sparse and high-signal, never decorative. Video 05 uses only 3 custom overlays across 16
minutes; 07 uses 4; 02 uses 2. **No persistent lower-third/chyron, no caption track, no animated
logo intro/outro anywhere in the corpus.**

Two recurring custom-overlay families:
1. **Big dollar/number callouts** — bold heavy sans-serif, often red or white-outlined, hammering
   a single number the instant it's spoken (e.g. a giant listing price, a CAPE ratio, a loss
   figure).
2. **Geo/location labels** — bold thick-outlined "meme text" style (yellow/black or gold/olive),
   used ONLY during rapid multi-city montages to keep viewers oriented — never during a
   single-example deep dive.

Occasional single-keyword stinger overlays for a pure emphasis beat ("DISTRESS," "It's officially
law!").

**Chart style — two templates only:**
- **"Broadcast" dark-mode:** near-black background, white gridlines, one bold accent-color line,
  inline data-point labels, small corner "Source: [domain].com" tag. Used for macro/historical
  data pulled from outside sources.
- **"Product UI" light dashboard:** white background, branded wordmark, card-based layout, browser
  chrome left uncropped. Used exclusively for the proprietary app/tool.

Numbers get highlighted via native chart labels, manual highlighter boxes over screenshot figures,
or a big bold number-callout overlay for the single most important figure in a segment — never
more than one of these per beat.

**Recurring motifs to replicate:** a small corner "Source: [domain].com" tag on every external
screenshot, deliberately absent from the channel's own proprietary charts (a "borrowed proof vs.
our analysis" distinction — keep this distinction for Graeham's own MLS/CAR-sourced charts vs.
external ones); brand watermark deliberately withheld until ~55–60% into runtime — credibility
established before brand exposure; cursor-as-narration-tool (live hovering/highlighting/scrolling
functions as the primary "motion graphic" during screen-recordings); pillarboxing for off-aspect
source PDFs.

### Concept-rendering label convention (locked 2026-08-12, standing rule)

Reventure has no precedent for this because every one of its case studies already exists —
Graeham's Track B lifestyle content frequently doesn't have that luxury (a not-yet-built
playground, a proposed development, a project still under construction). Any
`[CINEMATIC B-ROLL: ...]` shot that visualizes a subject that isn't built/open yet — a concept
rendering, an artist's impression, a stylized visualization of a proposal — gets a mandatory
on-screen label. This isn't a style choice; it's the same citation-honesty discipline this whole
skill runs on (§5.1, §10) applied to imagery instead of numbers: never let a generated shot be
mistaken for real footage of a thing that doesn't exist yet.

**Spec** (first tested and confirmed on the Coyote Point Playground video, 2026-08-12): bottom-
left panel, semi-transparent dark background with a 2px gold top stroke — the same panel
convention as `education-graeham-videos`' standing brand rules ("panels black with 2px gold top
stroke"), so it reads as an intentional brand element, not a disclaimer bolted on. Bold caps
primary line: `CONCEPT RENDERING`. Smaller subtext line with the real status + date pulled
straight from the citation table: `Not yet built · opening [DATE]` (swap the exact phrase for
"proposed," "under construction," etc. to match the actual project status — never overstate
certainty the citations don't support). Applies to every cinematic shot of the not-yet-built
subject across the whole video, not just the cold open — a viewer who skips ahead should never
land on an unlabeled frame.

This directly extends `education-graeham-videos` rule 0f (future-projects videos must label
status and never present a proposal as a done deal) by giving that rule a concrete on-screen
visual treatment instead of leaving it to the spoken script alone. Applies on both tracks
whenever the b-roll depicts something not yet built — Track B lifestyle content just hits this
case more often (see `script-template.md` "Concept-rendering labeling").

---

## 5. Script-to-Footage Timing Rules (the most important section — read before scripting)

1. **"Name the source → cut to the source" — the strongest, most universal rule in the corpus.**
   The cut lands within 0–3 seconds of the source being named, firing repeatedly per video (8+
   times in 01, 6+ in 03, 6 in 06). One exception exists in the whole corpus (a source named with
   no visual in 05) — strong rule, not an absolute one.
2. **A spoken statistic lands visually within ~1 second** whenever a supporting graphic is already
   active on screen. Confirmed in 01, 02, 03, 04, 06, 07, 08.
3. **Physical/anecdotal proof always precedes the abstract data that generalizes it — never the
   reverse.** Confirmed independently in 01, 04, 05, 07, 08. This is the single rule most relevant
   to placing cinematic b-roll (§9 category B): the cinematic establishing shot for a case study
   goes BEFORE the chart that generalizes it, matching this existing discipline exactly.
4. **Cutaway duration is elastic and content-driven, not a fixed rhythm** — 2-6s for quick
   annotations, up to 60-120+ seconds for data-dense list recitations. Studio format has a soft
   ceiling of ~45-60s before a punch-in or cut back to the host (01, 02, 06).
5. **Cinematic-specific sub-rule (the one to follow for every `[CINEMATIC B-ROLL: ...]` tag):**
   every genuine cinematic/stock cutaway found anywhere in the corpus (§3, all 7 instances) is
   brief (1-6s), tied to exactly one specific noun or claim, then the edit moves on immediately.
   Cinematic b-roll is punctuation, not sustained coverage — never write a cinematic tag longer
   than ~6 seconds, and never let one delay the citation cutaway it's paired with.
6. **Opinion/speculation content almost never gets a chart — only sourced, factual, numeric claims
   trigger graphics.** Confirmed strongly in 01, 03, 04 (2:14 continuous speculation, zero
   graphics), 06 (90+ second monologue, no visual), 08 (the densest analytical stretch in the
   video has the LEAST visual variety of any section). This is exactly where §9 category E
   cinematic inserts belong — not replacing the "no chart during opinion" rule, but filling the
   dead air it creates.
7. **Max continuous talking-head duration differs by format:** studio ~45–90s (01 max ~70s, 04 max
   ~45s, 06 max ~75-90s); walk-and-talk much longer (up to ~2:14 in 05, nearly 2 min in 07) —
   reserved specifically for opinion/speculation content per rule 6.
8. **Source-stacking sequences tighten cut frequency to ~10-25s** when multiple independent
   sources triangulate one claim (three sources in a row in both 01 and 07).
9. **Assets are frequently reused, not replaced, when the argument circles back** — a chart or
   exhibit shown once early can reappear verbatim later without needing a fresh version (02, 05,
   06 all do this).
10. **Brand/product placement and the hardest CTA push are deliberately delayed to the final
    5-15% of runtime** — universal across all 8. See §8.

---

## 6. Transition Style

100% hard cuts, zero exceptions, across all 8 videos. No crossfades, wipes, whip-pans, or
animated transition graphics anywhere in the corpus. The only quasi-transition techniques
observed: a simulated Ken-Burns zoom/pan on a static screenshot; a live cursor zoom/annotation
captured during real screen-recording; and one flagged unintentional artifact (a stray blank
frame). A topic pivot gets exactly the same hard cut as a mid-sentence pause-trim — transitions
are NOT used to signal topic changes. Keep hard cuts as the only transition type; do not introduce
crossfades or wipes even for the new cinematic b-roll inserts — they get hard cuts in and out like
everything else, which is also what keeps them feeling like punctuation rather than a separate
"cinematic mode."

---

## 7. Pacing

Delivery is conversational and measured, with elevated urgency at key claims but not sustained
hype-voice throughout. Shot duration varies sharply by section, and the arc is consistent across
all 8 videos:

- **Hook + early proof-stacking (first 1-2 min):** fastest cutting, new visual every 10-25s.
- **Case-study deep-dives:** moderate, 13-45+ seconds per graphic/location.
- **Interpretive "why"/mechanism sections:** slowest, 45-90+ seconds, occasionally 2+ minutes in
  walk-and-talk format.
- **Multi-city montage sections:** re-accelerates to 8-25s cuts; geo-labels appear because of the
  faster rate (§4).
- **CTA/product-demo section:** tightens again to near-continuous screen-recording; some videos'
  final seconds are the fastest cuts in the entire runtime (a 1-2s flash-cut trust-signal
  montage).

**Overall arc: fast (open) → slow (middle analysis) → fast (montage) → fast (CTA close).** Plan
cinematic-b-roll density against this same arc — most of the §9 category-E inserts belong in the
slow middle section, since that's precisely where the pacing otherwise goes flat.

---

## 8. CTA & Branding System

Every video closes with a hard CTA for the paid product, consistently priced and consistently
structured: (1) brand watermark withheld until ~55-60% of runtime, hardest push compressed into
the final 5-15%; (2) a **live product demo** — the host actually uses the real tool on a real
input, often the SAME example shown earlier as a case study (a deliberate callback, seen in 01 and
07); (3) a personal testimonial when available; (4) price + URL spoken aloud, synced within ~1s to
a pricing-page screenshot; (5) closing beat is either a rapid flash-cut trust-signal montage or a
plain verbal sign-off — no branded animated outro card exists anywhere in the corpus. No animated
intro/outro bumper appears in any of the 8 videos, and no lower-third name/title card is ever
used.

**Adapt for Graeham:** same structure (delayed branding, live demo of a real Graeham
tool/service using the same example shown earlier, testimonial when available, synced price/URL,
compressed final push), same restraint (no animated bumper, no lower-third) — see
`education-graeham-videos` `SKILL.md` for the actual end-card spec (logo lockup, DRE#, gold-
gradient CTA button, spoken CTA matching the button keyword) that supersedes Reventure's specific
pricing-card mechanics while keeping this section's structural discipline.

---

## 9. THE CINEMATIC B-ROLL GAP — opportunity categories

Consolidated from the explicit "Missed Cinematic Opportunities" analysis run against every video
in the corpus. These are the categories every new script's Phase 2 b-roll opportunity map should
be sorted against.

**A — Abstract macro/statistical claims with zero visual representation.** The single most common
gap, recurring in nearly every video that discusses a macro trend. Example: a "migration at a
35-year low" claim shown only as a line chart, never a moving truck or a highway shot; an entire
multi-minute "stock market bubble" section with zero cinematic tension-building despite being
flagged as the single biggest missed opportunity in that video.

**B — Case-study/anecdote moments treated as a screenshot instead of a scene.** Only one genuinely
composed establishing shot exists in the entire 8-video corpus. Every other case study — a short
sale, a specific street, a specific listing — is a pure Zillow/portal screenshot with no mood or
establishing shot ever accompanying it. A cold-open case study built on a static article
screenshot instead of an evocative opener is flagged as the single highest-leverage miss in its
video, precisely because it's the hook.

**C — List-of-locations moments that could be a quick montage.** Multi-city lists recited purely
verbally with zero per-location visual ("Milwaukee... Omaha... Wichita..."; "Atlanta, Nashville,
Georgia, Tennessee") — flagged explicitly as 3-shot-montage opportunities.

**D — Emotional/consequence beats with no visual weight.** Foreclosure, delinquency, and job-loss
beats represented only by text-quote cards or line charts — no dramatization at all. A
delinquency/foreclosure discussion is flagged as needing "a foreclosure notice on a door, moving
boxes on a porch, a bank-owned sign" instead of a bare chart.

**E — Dense analytical/opinion stretches with the least visual variety in each video.** Because
opinion content doesn't trigger graphics (§5 rule 6), the most information-dense passages are
paradoxically the most visually static — one video's longest, most substantive analytical stretch
is explicitly flagged as having the least visual variety of the entire runtime.

**F — Mechanism/process explanations that named a physical thing but showed nothing.** A named but
never-shown factory near a specific city; a "it's officially law!" legislative beat that uses
three consecutive screenshots with no Capitol/gavel visual anywhere.

**G — Comparison/contrast beats that could use split-screen or paired visuals.** City-vs-city and
county-vs-county comparisons rely entirely on sequential charts/numbers with zero paired visual
metaphor.

**H — The CTA/closing section itself lacks polish precisely where cinematic footage would help
most.** One video's own homepage hero image is a licensed stock aerial photo, not original
footage — the clearest single piece of evidence that even Reventure defaults to stock imagery
when the format calls for an establishing aerial shot. Another video's sign-off is a plain
smiling talking-head with zero closing visual flourish.

**Frequency:** Categories A and E are near-universal (present in effectively every video).
Categories B and D appear in 6-7 of 8. Categories C, F, G, H are more situational but recur 3+
times each and are low-cost, high-clarity insertion points.

---

## 10. Adopt-As-Is vs. Diverge — the synthesis

**ADOPT AS-IS (Reventure gets these right — do not "improve" them):**
- Cold open, no bumper, "assert → specify → prove" hook (§1)
- Claim → name-source → cut-to-receipt within 0–3s — non-negotiable citation discipline (§5.1)
- Physical/anecdotal proof always before the abstract data that generalizes it (§5.3)
- Sourced facts get graphics; opinion doesn't — let the presenter run long during pure
  interpretation instead of manufacturing a visual (§5.6)
- Chart style discipline: dark "broadcast" vs. light "product UI," consistent Source tags,
  authentic unstyled screen-recording, no over-designed graphics (§4)
- Sparse, high-signal text overlays only — no persistent lower-thirds, no caption track (§4)
- 100% hard cuts, zero transition effects, including on the new cinematic inserts (§6)
- The fast → slow → fast → fast pacing arc (§7)
- Delayed branding + compressed hard CTA in the final 5-15%, with a live product demo, synced
  price/URL, and restrained closing (no animated bumper) (§8)
- Strict citation rigor — never substitute cinematic/AI footage for a real source screenshot; a
  claim that needs proof still gets its screenshot regardless of what cinematic footage runs
  alongside it

**DIVERGE (the cinematic-b-roll fill, category by category from §9):**
- **A (abstract macro claims):** insert a brief 2-5s cinematic shot alongside/before the existing
  data cutaway — supplementing, never replacing, the citation.
- **B (case-study opens):** a short cinematic establishing shot (exterior push-in, "For Sale"
  sign, golden-hour light, 3-5s) before cutting to the real listing/case data — preserves
  anecdote-before-abstraction (§5.3) while raising production value.
- **C (location lists):** turn verbal lists into quick multi-shot montages, paired with the
  existing geo-label text convention (§4).
- **D (emotional/consequence beats):** give these mood-appropriate visual weight (a foreclosure
  notice, moving boxes, a "sold" sign) instead of leaving them as a bare chart or text card.
- **E (dense opinion/analysis stretches):** one cinematic cutaway roughly every 20-30 seconds
  during these sections specifically, timed to breathe rather than interrupt — this is where
  the format currently goes visually flat (§7).
- **F (named-but-unshown mechanisms) and G (comparisons):** illustrate the named physical thing;
  use paired/split visuals for direct comparisons instead of sequential charts alone.
- **H (CTA close):** a genuine cinematic shot in the closing section instead of a plain sign-off
  or licensed stock photography — a zero-risk upgrade with no format precedent to violate.

**Target allocation:** Reventure runs ~0-2% cinematic b-roll (effectively zero in 6 of 8 videos
studied). Target **15-25% of total runtime** as genuine cinematic/AI-generated b-roll for
Graeham's Track A videos, concentrated in categories A, B, D, and E, using Reventure's own proven
insertion discipline — 2-6 second flash-cut inserts, hard cuts in/out, each tied to one specific
noun/claim/emotional beat — rather than long sustained cinematic sequences that would break the
format's fast, data-dense rhythm. **Cinematic b-roll is punctuation, not sustained coverage: it
must never delay or replace a citation-triggered data cutaway.**

---

## 11. Track B (Lifestyle) — extrapolation note (added 2026-08-12)

Everything above (§1–10) was derived from analyzing Reventure's market-data format. Track B —
pure lifestyle content, zero market data, zero doom-adjacent framing — has no equivalent reference
corpus behind it yet; Reventure doesn't run this format at all. The following adjustments are
reasoned extrapolations from §1–10, not independently verified findings:

- **Keep:** cold open discipline (§1, minus the doom-stakes framing — open on the vivid specific
  detail instead: "a themed playground with a 50-foot zipline is about to break ground two blocks
  from here"), citation discipline for factual claims (dates, costs, addresses still get a real
  source cutaway), 100% hard cuts (§6), the fast→slow→fast→fast pacing arc (§7) compressed to fit
  a likely-shorter runtime, delayed-branding CTA structure (§8) reframed around Graeham's
  services rather than a paid app.
- **Drop:** the macro-data-stack beat, the mechanism/"why" beat, and the contrarian/balanced-
  verdict beat (§2 beats 2, 4, 5) — a lifestyle video has no doom thesis to complicate or balance.
- **Raise:** cinematic-b-roll allocation from the 15-25% Track A target to roughly 25-40% (see
  `SKILL.md` Phase 3) — without a chart to fall back on, categories B and F (§9) carry nearly the
  entire visual load.
- **Verify later, if it matters:** run `video-watcher` against a lifestyle-format reference
  channel (a local-area "hidden gems" or "moving to X" creator) the same frame-by-frame way the
  original 8 were analyzed, and fold the findings back into this section with real evidence
  markers like §1–10 have.
