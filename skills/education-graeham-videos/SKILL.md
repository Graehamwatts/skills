---
name: education-graeham-videos
description: "Education Graeham Videos — Reventure-style data-driven real estate educational videos for Graeham Watts, localized to East Palo Alto, Palo Alto, Menlo Park, Redwood City, San Mateo County, San Jose, SF, and the East Bay. Replicates the exact Reventure format: authority-anchored doom-hook packaging, dense sourced data, zip-level bifurcation stories, listing autopsies, myth-busts, labeled speculation, balanced verdicts, hard CTAs — as long-form YouTube scripts AND reels with full production specs. Use ANY time the user says: create an educational video for the day, educational video, daily video, Reventure video, Reventure style, data video, housing market video, make today's video, or asks for trending Bay Area real estate topics to turn into a video. ALWAYS starts by researching trending topics and presenting a Top 5 list for the user to pick — never jump straight to a script."
---

## STANDING BRAND RULES — every video (locked 2026-07-31, from Graeham's reference frame)

**End card (final ~5s of EVERY finished video), composited over a ~60% black wash of the
closing shot:**
1. TOP: white GRAEHAM WATTS logo lockup (gold roof icon + gold divider + REALTOR), from
   `carousel-builder/assets/logo/logo_white.png`, ~860px wide (1080-wide frame), centered.
2. Under logo: `DRE #01466876` letter-spaced Montserrat, white — brokerage name ONLY, no
   default text. Graeham left the former brokerage (first entry in identity.json brand_blocklist) as of 2026-08-09; do not print its name or
   any other brokerage name on the end card unless Graeham explicitly names a new one to use.
   The brand end card DOES show the DRE — on this card it supersedes any "no DRE on screen"
   note elsewhere.
3. MIDDLE: the video's subject line in gold-gradient Great Vibes cursive
   (`carousel-builder/assets/fonts/GreatVibes-Regular.ttf`), auto-sized to fit ≤980px.
4. Gold gradient rounded button (light→dark metallic), black Montserrat ExtraBold:
   `DM "KEYWORD"` — keyword per viral-playbook CTA system, GHL comment-automation compatible.
5. Below button, white Montserrat caps: `OR CALL — NUMBER IN BIO`.
6. The SPOKEN CTA must match the button keyword. One CTA per video. Say it, show it, pin it.

**Text treatment (reels/short-form):** Reventure concept in Watts colors — karaoke captions
white extra-bold with black outline, active word on a General-Accent gold (#C4A265) rounded
pill with black text; section labels gold bold-italic with heavy black outline (marker style,
no box); cover hook = white rounded box, dark bold text, exactly ONE emoji; evidence shown as
RAW page screenshots with gold highlighter markings; backgrounds Watts Navy #0A1F44; panels
black with 2px gold top stroke; ONE hero moment per video in protected Watts Gold #B8945A.

**Text sizes (1080×1920 frame — locked after v7):** karaoke captions Bold 96px (shrink-to-fit
floor 72px, max width ~1020px), outline 7px black, baseline y≈1540; active-word pill padding
16/10px radius 18; section labels BoldItalic 64px; CTA overlay BoldItalic 88px; cover-box text
Bold 58px. Text is BIG — it should dominate the lower third like the reference reels.


**Process rules:** ask for all required credentials BEFORE any production work (missing keys =
full stop and ask); NEVER downgrade or substitute the instructed format/avatar/voice/visuals —
if blocked, stop, name the blocker, wait.

**MANDATORY FULL-SWEEP QC — before EVERY video delivery, no exceptions, never wait to be asked:**
1. Frame sweep of the ENTIRE runtime at ≥2 frames/second (0.5s intervals), viewed in grids —
   every segment, not spot samples.
2. Every cut boundary frame checked; consecutive-frame strip on any composited element
   (cutouts, overlays) to catch flicker.
3. Every on-screen number re-verified against the citation table.
4. Caption sync spot-verified on at least 10 sampled words across the runtime.
5. ffprobe container check (resolution, fps, codecs, duration) + volumedetect (peak −1 to −3 dB,
   no clipping).
6. EXPLICIT PASS/FAIL items (added 2026-08-02 after all four failed in one delivery):
   a. Highlighter circle CLEARS the circled content — the stroke must never touch the text/number
      it circles ANYWHERE along its curve, not just at mid-height (2026-08-05: side-padding alone
      still clipped the corner letters of a multi-line headline). Size by the CORNER TEST: for the
      ellipse with center (cx,cy) and semi-axes (a,b), every corner (px,py) of every circled text
      line must satisfy ((px-cx)/a)^2 + ((py-cy)/b)^2 <= 0.86. For a full text block this means a
      near-circumscribing ellipse (~sqrt(2) times the block size); if that overflows the 1080 frame,
      shrink the page scale / shift x0 rather than the ellipse. Furniture (chips, buttons, borders)
      may be grazed; readable body text may not. Verify with a rendered overlay check BEFORE
      compositing AND on final frames.
   b. Cutout bottom-overflow: the cutout's bottom edge must reach/overflow the canvas bottom in
      EVERY frame — no floating-torso gap. Enforce in code (min scale), don't just eyeball.
   c. No hard interior slice edges: body parts touching the source-frame border must fade
      (soft alpha ramp), never end in a visible vertical/horizontal cut inside the canvas.
   d. LIP SYNC: extract a consecutive-frame strip (≥12 fps) of the mouth at the hook + 2 other
      phrases and match closure/opening frames to word onsets from the alignment (P/B closures
      are the easiest anchors). HeyGen renders MUST use the v3 endpoint (POST /v3/videos) —
      the legacy v2 endpoint can fall back to an older animation engine with visibly worse lips.
7. Report findings to Graeham WITH the two things frame QC cannot verify (audio feel, motion
   between frames) called out explicitly. Never claim 100% on unverified dimensions.
A video that has not passed the full sweep is NOT delivered. Deliver-then-fix is a rule violation.
A defect class found by Graeham gets added to THIS checklist the same day — the sweep tests for
every failure mode ever seen, not just the convenient ones.

**FRESH LOOK PER VIDEO (hard workflow step, not a preference):** every video gets a NEW avatar
look with a different outfit; when the video is about a specific place, research and capture
real imagery of that place (Street View) and put Graeham THERE as the look's background —
full steps in `references/production-pipeline.md` Step 0-4. Studio looks (`fashion_flip`,
`bespectacled`) are fallbacks ONLY if Graeham explicitly declines a location look. **No specific
place in this topic (locked 2026-08-12):** default to a real, notable, recognizable Bay Area
street/location — East Palo Alto, Menlo Park, Redwood City, San Francisco, or elsewhere in the
Bay — something the audience would actually recognize, never a generic anonymous block. Studio
looks stay the fallback-of-last-resort, not the default for "no specific place." Full sourcing
logic in `references/production-pipeline.md` Step 0.

**SHORT + LONG FORM PAIR = ONE FRESH AVATAR (added 2026-08-06).** When a topic ships as a
short-form reel AND a companion long-form video (the standard pairing), that pair shares
ONE fresh avatar look — built once per TOPIC, not once per video output. Same outfit, same
location background (if the topic is about a specific place), same digital-twin identity in
both deliverables. The only thing that differs between the two is aspect ratio/orientation:
- Reel / short-form = portrait **9:16**, ALWAYS.
- Long-form YouTube video = landscape **16:9**, ALWAYS.
Do not generate a second "fresh" look for the long-form video just because it's a different
deliverable — that breaks visual continuity between the pair and burns a second one-time look
build for no reason. Build both orientations together in the same Step 0-4 pass (see the
updated LOOK PAIRS bullet under rule 0g).

# Education Graeham Videos

Turn the day's most compelling Bay Area real estate story into a Reventure-style educational
video package: verified research → user-picked topic → long-form YouTube script + reel script +
titles, thumbnail spec, captions, asset list, and production handoffs.

**Read before writing anything:**
- `references/reventure-blueprint.md` — the full style codebook (formats, 11-beat script
  architecture, visual grammar, packaging formulas, reel architecture). This is the ground truth
  for HOW these videos work. Follow it beat-for-beat.
- `references/script-templates.md` — fill-in templates for scripts, titles, thumbnails, captions.

## Non-negotiable rules

0d. **Lifestyle series — attraction, not doom (added 2026-08-02).** A second video track exists
   alongside the market-data videos: LIFESTYLE educational videos ("Moving to East Palo Alto",
   "best-kept secret", "what $1M buys", schools, new parks/restaurants/transit) for Graeham's
   farm areas: East Palo Alto, Redwood City, East Menlo Park, San Francisco, San Jose, Bay Area.
   These videos SELL the areas. Zero negativity: no fear hooks, no "crash/decline/left behind"
   framing, nothing that would push a buyer away from moving there. Keep the Reventure
   production grammar (pacing, receipts, captions, stickers) but flip the emotion: curiosity,
   FOMO, opportunity — "get in before everyone figures it out", never "get out".

0e. **Freshness rule — days old at MOST (added 2026-08-02).** For lifestyle/news videos, the
   news peg the video hangs on must be from within a few days of creation day (same day to a
   few days before/after). Every video day starts with a fresh last-48h/last-7-days search
   BEFORE scripting; the hook anchors to the newest item found. Evergreen facts (distances,
   district boundaries, long-running projects) may support the story, but the hook itself must
   be fresh. An older story may only be used if a NEW milestone (hearing, filing, opening,
   report) re-freshens it — otherwise reframe the video as an evergreen guide, not news.

0f. **Future-projects videos (added 2026-08-02).** Proposed or under-construction developments
   that are big news for a farm area are a wanted lifestyle-track topic: new buildings, housing
   projects, transit (BART/Caltrain), waterfront/downtown plans, campuses, parks. Requirements:
   every claim backed by verifiable sources (city planning pages, CEQA/permit filings, council
   agendas, developer sites, local press) cited in the citation table; clearly label status
   (proposed vs approved vs under construction vs opening) and never present a proposal as a
   done deal; frame as opportunity/growth for the area (per rule 0d). Renderings/site plans used
   as visuals get a source + license note like any other asset.

0g. **Production standards locked 2026-08-04 (from RWC build iterations), aspect-ratio mapping
   updated 2026-08-06:**
   - LOOK PAIRS (simplified 2026-08-12 — Higgsfield generates a STILL, HeyGen does the
     animating): every on-location avatar look is created as a PAIR — portrait 9:16 +
     landscape 16:9 — as a single 4K Higgsfield Nano Banana Pro still per orientation
     (identity ref + real environment ref composited together, no Seedance/video-training
     step), uploaded to HeyGen as a photo-based look. Native 4K Higgsfield output means no
     separate upscale pass is needed before the look is created. Full steps in
     `references/production-pipeline.md` Step 0-4. Built ONCE PER TOPIC
     (not once per video output) — if the topic ships as a short+long-form pair, both
     deliverables reuse this same pair. FIXED mapping, no exceptions: portrait 9:16 is the
     reel/short-form primary (hook, close-ups); landscape 16:9 is the long-form YouTube primary
     (full-frame field format) and also serves split-screen lower strips inside reels. One-time
     cost per topic/location; per-video renders are then HeyGen-only. NEVER outpaint/reframe per
     video (seams mid-sentence + recurring credits).
   - ANNOTATIONS ARE RED (220,40,35): highlighter circles AND arrows. Circles sized by the
     CORNER TEST (QC item 6a — near-circumscribing, stroke never touches circled text anywhere
     on the curve, 2026-08-05); arrows only from verified-empty zones; NO cursor. On pages with
     tightly-stacked rows (e.g. congress.gov bill pages) where no clean ellipse exists, use a
     red arrow from an empty zone INSTEAD of a circle.
   - PRICES IN TTS: plain decimals WITHOUT the $ sign ("10.75 million dollars") — a leading $
     makes ElevenLabs say "ten dollars point seven five". Captions substitute the $ figure
     back via a display map ({"10.75": "$10.75"}). MANDATORY AUDIO QC before any render:
     Whisper-transcribe the generated VO and verify every number/name is spoken correctly;
     use voice_settings.speed (~1.05-1.10) for reference-fast pacing — raising style slows
     delivery down, it does not speed it up.
   - NO EM-DASHES IN VO SCRIPTS (2026-08-05): ElevenLabs holds ~0.9s of dead air on every
     "—", which reads as awkward stalling. Use commas. After generation, run a PAUSE-PROFILE
     check on the alignment: no mid-sentence gap > 0.5s; sentence-boundary gaps <= ~0.8s
     (approved-baseline). Trim longer sentence gaps surgically (cut audio + shift alignment
     times) rather than regenerating and re-rolling the dice. Also verify the Whisper
     transcript has NO extra syllables (TTS sometimes injects an audible breath/vocalization
     in long gaps — mute that window with fades if found).
   - TRANSITION WHOOSH is the airy swept-noise build (sfx_whoosh2: bandpass sweep up-then-
     down, swell envelope + low-air layer) — not the plain noise burst (rejected 2026-08-05).
   - SFX MIX ARCHITECTURE (2026-08-05, replaces the old whole-mix loudnorm): normalize the
     VO ALONE to I=-14 FIRST (single-pass loudnorm on speech is fine), THEN add SFX at true
     relative gains, then final alimiter at mux. NEVER run loudnorm over the finished mix —
     single-pass loudnorm is DYNAMIC and pumps the gain up during VO gaps, which blasts any
     SFX sitting there (this is why the whoosh was 'distracting': it measured as loud as
     speech). Target: whoosh ~9-10dB RMS under speech RMS ("subtle but noticeable"; verify
     with a volumedetect on a VO-silent gap vs a speech window), pop ~0.32 on caps words.
   - Evidence beats: article at 1.15x (per-page centering, no clipped words) over blur-fill,
     full-width landscape strip of the wide look at the bottom, captions above his head.
   - Hook: native framing, NO zoom pumping. Close-up zoom only on mid-video talking beats.

0h. **Sharpness + motion standards (locked 2026-08-04, from "laggy/not HD" fix):**
   - PORTRAIT head renders at 4K (resolution "4k", 2160x3840) so every punch-in DOWNSCALES
     into the 1080x1920 frame — never blow up a 1080p render. Wide/landscape renders stay
     1080p (they're downscaled into the strip anyway).
   - UPSCALE THE TRAINING FOOTAGE BEFORE CREATING LOOKS (2026-08-05, "still low def" fix):
     Seedance outputs 720p; a look trained on 720p stays soft no matter how big the HeyGen
     render is — the 4K render just upscales softness. Topaz-upscale (upscale_video provider
     topaz, 2160p) the concatenated training clips FIRST, then create the digital-twin looks
     from the 4K files. Same one-time cost logic: the HD look pair is reusable forever.
   - FROZEN PUNCH-INS: the close-up crop window is locked per jump-cut interval (~1.8s) —
     computed once from the face-track EMA at interval entry, then held. Per-frame tracking
     drift reads as lag/stutter; never re-track inside an interval.
   - EXAGGERATED JUMP CUTS (2026-08-05): talking-beat zoom levels alternate WIDE half-body
     (~1.15x) <-> TIGHT face (~1.75x). A small delta (e.g. 1.55<->1.70) reads as a subtle
     "pump", not a cut — the two framings must be unmistakably different. Hook stays native.
   - B-ROLL FPS CONFORM (2026-08-05, "laggy" fix): generated b-roll is usually 24fps; forcing
     it to the 25fps timeline with -r duplicates frames and puts visible judder on smooth
     drone pans. ALWAYS conform with minterpolate (mi_mode=mci:mc_mode=aobmc:vsbmc=1) to the
     timeline fps before extracting frames. Check r_frame_rate of every source; never let a
     dup/drop cadence into pans.
   - ALL scaling uses LANCZOS (never BILINEAR for visible content).
   - Master encode: CRF 18. Delivery caps: chat ≤30MiB (encode CRF ~22 to fit — this is the
     POSTING copy), device transfer ≤20MiB (two-pass ~3.2Mbps). Tell Graeham which file is
     the posting copy every time.
   - Footage is 25fps (HeyGen output). If playback still feels non-fluid, the next lever is
     30fps interpolation on head segments — test before promising.
   - FILE NAMING: final file = the hook phrase as a clean title ("Redwood City Just Said
     YES.mp4"). FINAL folder holds exactly ONE file; every prior version goes to old\.

1. **Top-5 first.** On "create an educational video for the day," ALWAYS run Phase 1 research and
   present a scored Top 5 topic list. The user picks. Never skip to scripting.
2. **Every fact verified.** Every statistic in a script must trace to the citation table built in
   Phase 2: one primary source (CAR, MLS, Census, FRED, Zillow/Redfin research, county records) or
   two independent reliable secondary sources. No number without a source. If a stat can't be
   verified, it doesn't go in the script — say so and substitute.
3. **Reventure is invisible.** Reventure/Nick Gerli is an internal style reference ONLY. Never
   mention, cite, show, promote, or allude to Reventure, the Reventure App, or Nick Gerli in any
   script, title, caption, thumbnail, overlay, description, comment, or chart — ever. All data
   credibility comes from OUR sources (MLS, CAR, Zillow/Redfin research, Census, FRED) and all
   CTAs point to Graeham's business. NEVER use Reventure's charts, maps, footage, or branding —
   we replicate the METHOD, not the assets and not the brand. Research materials grabbed for our videos must be: public data we
   re-chart in Graeham's branding, government/public-domain material, brief news-headline
   screenshots used as commentary (fair-use style, shown with source visible), listing screenshots
   from public portals used for market commentary, or licensed/free-to-use footage. Every grabbed
   asset gets a source + license note in the asset list.
4. **Compliance.** Graeham is a licensed agent (DRE# 01466876). No fair-housing violations: never
   characterize neighborhoods by who lives there; talk prices, inventory, DOM, migration counts —
   not people. Forecasts are framed as data commentary, not guarantees ("the data suggests", never
   "will definitely"). Doom packaging is fine; fabricated or misrepresented numbers are not.
5. **Full Reventure energy.** Provocative packaging, superlative hooks, crash arrows — but the
   in-video verdict stays calibrated and sourced, exactly like the source channel does it
   (blueprint §6). The gap between packaging and verdict is the format.

## Phase 1 — Trending topic research → Top 5

Search fresh (last 7 days, prefer last 48h) across:
- News: SF Chronicle, Mercury News, SFGATE, Palo Alto Online, Almanac (Menlo Park), Redwood City
  Pulse, EPA Today, Bloomberg/WSJ/Fortune housing coverage with a Bay Area angle.
- Data drops: CAR monthly report, Zillow Research releases/forecast updates, Redfin Data Center
  news, Case-Shiller SF release dates, FRED updates, Census/ACS migration releases, rate moves.
- Local signals: MLS stats via the `mls-matrix-scraper` skill when available (inventory, DOM,
  price cuts, sales counts for San Mateo + Santa Clara counties), notable listings (big price
  cuts, sales at loss, record sales) on public portals.
- Optional: `instagram-competitor-scraper` / `youtube-scraper` for what's performing in the niche
  this week.

Score each candidate 1–10 on: local relevance (Graeham's markets), data availability (can we get
primary numbers?), hook potential (superlative/flip/authority peg available?), audience value
(does a buyer/seller/owner learn something actionable?). Present as a table:

| # | Topic | Hook angle | Authority peg | Data source | Score |

with a one-line recommendation of which YOU would pick and why. Wait for the user's choice.

## Phase 2 — Deep research + verification + asset grab

For the chosen topic:
1. Pull the primary data (download the actual report/CSV where possible; MLS pull if relevant).
2. Build the **citation table**: every stat → source name, URL, date, exact figure, how retrieved.
3. Cross-check the headline stat against a second independent source. Flag any conflicts to the
   user rather than papering over them.
4. Find the **bifurcation**: where is the OPPOSITE happening nearby? (SF booming while Oakland
   drops; Palo Alto holding while EPA moves). This contrast is a mandatory story beat.
5. Find 1–3 **listing autopsies**: real, current, public listings in Graeham's markets with
   concrete numbers (list price vs purchase history, price cuts, DOM). Note URL + date accessed.
6. Build the **asset grab list** (per rule 3): headline screenshots, report pages, FRED charts,
   public-domain aerials, b-roll needs — each with source + license status.

## Phase 3 — The content package

Produce, using `references/script-templates.md`:
1. **Long-form YouTube script** (8–14 min) following the 11-beat architecture, written in the
   voice (verbal fingerprint in blueprint §2), with inline visual directions
   `[SCREEN: ...]` / `[CHART: ...]` / `[OVERLAY: yellow "..."]` every 20–60 seconds of runtime.
2. **Reel script** (30–60s) + IG caption (CTA-first format) + cover-text spec.
3. **5 title options** (formulas in templates §C) + thumbnail spec (§D).
4. **Description + pinned comment** (§E).
5. **Chart plan**: each chart to build (metric, geography, timeframe, source), styled to
   Graeham's brand — blue=declining / red=rising choropleths, dark chart cards with bold
   callout numbers, yellow highlights. Build with the `dataviz` skill conventions; never
   screenshot Reventure.
6. CTA adapted to Graeham's business: free home-value analysis / CMA (hand off to
   `cma-generator`), "comment your zip", newsletter signup — not an app subscription.

## Phase 4 — Production (BUILD THE VIDEO — follow `references/production-pipeline.md` exactly)

The reel is BUILT in-session, end to end. Read `references/production-pipeline.md` BEFORE
starting production and execute its steps in order. Summary (details + IDs live there):
1. **Step 0 — location look decision (MANDATORY):** new avatar look pair for this video, new
   outfit; if the video is about a specific place, capture real Street View imagery of that
   place and generate the look ON LOCATION; if no specific place applies, use a notable,
   recognizable Bay Area street instead. Never silently reuse or fall back to studio looks.
2. Environment capture → Higgsfield Nano Banana Pro still (identity ref bundled at
   `assets/identity_ref.png` composited into the environment ref, native 4K, one per
   orientation) → **STOP, show Graeham both stills, wait for his "looks like me" approval**
   → upload each approved still to HeyGen via the "Upload look" tile (HD, no separate
   upscale pass needed).
3. VO with timestamps (+ Whisper QC + pause profile) → three HeyGen v3 renders (4K portrait /
   alpha webm / 1080p wide).
4. Evidence inserts (blur-fill, RED corner-test annotations) → fork
   `assets/compositor_template.py` → SFX mix (VO-first, bundled `assets/sfx_*.wav`) →
   composite → full-sweep QC (see checklist above) → master/chat/disk deliverables with the
   hook-phrase filename and one-file FINAL folder.
Long-form YouTube videos still hand off to `heygen-video` / `remotion-video` / `video-editor`
with an edit sheet — the in-session pipeline above is for the daily reel.

## Phase 5 — QC before delivery

- Re-check every number in the final script against the citation table (fix or cut mismatches).
- Compliance pass (rule 4) and copyright pass (rule 3) on the asset list.
- Confirm the package includes: both scripts, titles, thumbnail spec, description + pinned
  comment, chart plan, asset list with licenses, citation table, edit sheet.
- Deliver everything in one organized output folder; offer the next step (render now?).

## Iteration memory

When the user gives feedback during a video build ("more aggressive hooks", "shorter",
"always include a rent angle"), treat it as a standing rule for future runs of this skill and
offer to save it into this SKILL.md so the skill learns.
