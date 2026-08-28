# THE HOOK & TRANSITION PLAYBOOK
## Reverse-engineered from Graeham's 29-video reference library (July 2026)
### Companion to viral-video-engine — this governs the FIRST 3 SECONDS and every cut after it.

Source: 29 reference reels/carousels watched frame-by-frame (notes in references/notes/).
Engagement spread: 40 likes → 195K likes. The patterns below correlate with the winners.

---

## PART 1 — THE HOOK TAXONOMY (8 families)

Every reference hook fits one of eight families. Pick ONE per video. Never open without one.

### H1. IMPOSSIBLE OBJECT (AI-powered)
Something that can't fly/exist does, and it's headed somewhere.
- Flying keys race through town to the listing door (#1, #2 — the canonical listing version)
- Screen content peels off a laptop like wet film (#27)
- Helicopter-door POV, suited agent about to jump (#24)
RULE: the object must be ON-MESSAGE (keys = home, screen-peel = "beyond the listing photo").
The AI clip buys 3 seconds; REAL footage must take over at the arrival point.

### H2. SINGLE-PROP SURREALISM (zero-AI)
One absurd object in an impossible place, played straight.
- Red rotary phone alone in the street (#3) · keyboard in a ziplock in the rain (#8)
- Bubble machine hidden on a drainpipe (#29)
RULE: color-isolate the prop (one saturated object, desaturated world). $20 prop > $2000 VFX.

### H3. DEADPAN ABSURD COMMITMENT (zero-AI, highest ROI in the library)
A human does something ridiculous with a completely straight face.
- Realtor dances alone in empty flat under billboard type (#4, 14.6K)
- Team stuffs rival realtor into trunk mid-pitch (#7, 30.7K, 615 shares)
- Agent lies "dead" under drone with scattered flyers (#11)
- Firecracker planted in teammate's pocket, then a straight 15s pitch (#23, 85.8K)
RULE: commitment IS the production value. Half-committed = dead. No laughing on camera.

### H4. META / RADICAL HONESTY
Confess the artifice; the one true thing left standing is the product.
- "There's no coffee in this cup... everything here is fake — except this house" (#9, 186K, 5.4K shares)
- Two-phone rig showing its own mechanics (#10) · video-of-a-video recursion (#12, 195K)
RULE: honesty buys trust; spend it on ONE claim ("except this house").

### H5. FORMAT HIJACK
Wear the costume of another media format; brand is the punchline.
- Fake breaking-news CCTV chase → pistachio bakery (#20, AI-generated "news footage")
- Fake IG "Sensitive content / See Reel" gate (#28) — platform-UI hijack
- Mockumentary A24 sitcom listing film "OPEN HOUSE: EP. 2" (#19)
RULE: keep parody legible (fake station name, house icon on the fake gate). Deception converts to a joke, not a scam.

### H6. CANVAS MISBEHAVIOR (pure edit, deterministic)
The frame itself is the effect.
- Video squeezes/reopens/splits into triptych on beats (#5)
- Clone split-screen: "Without me / With me" escalator race (#6)
- Letterboxed billboard type animating on the black bars (#4)
RULE: 100% deterministic in post (CapCut keyframes / Remotion / ffmpeg). No AI needed. Frame moves land ON BEATS.

### H7. NEGATIVE / ROAST HOOK (spoken)
Attack the viewer's status quo, then sell the fix.
- "Does your life actually suck? ... It's not you. It's your zip code." (#21)
RULE: roast the situation (commute, rent, landlord), never a protected class. Flip to the pitch by ~40% mark.

### H8. INSIDER SECRET / CURIOSITY GAP
Promise hidden knowledge with a specific payoff.
- "Secret Bubble Machine 📍 address" (#29) · "$2M around America" comparison (#13)
- Stat hook: "Rent in Alamo Square is up 42%" (#15) · series scaffold "Day 1 of ranking every…" (#26)
RULE: address chip on screen = save/share trigger. Second payoff at ~70% defeats early swipe.

---

## PART 2 — TRANSITION GRAMMAR (what makes their cuts feel expensive)

1. **HIDE THE IMPOSSIBLE IN A HARD CUT.** The helicopter "jump" is never shown — cut at the commit
   moment, brain fills the gap (#24). Flying keys "land" via cut to the agent at the same door (#1).
   The seam is wardrobe/location continuity, not VFX.
2. **SERIAL MATCH CUT.** Same object, same frame position, new world every ~2s (logo side-quests #18,
   key journey #2). The subject is the transition.
3. **WHIP/RADIAL BLUR AS CONNECTIVE TISSUE.** Fast directional blur frames bridge AI scenes (#1) and
   room-to-room jumps (#24). One blurred bridge frame ≈ any two shots cut together.
4. **RECURSIVE PUSH-IN.** Push into a screen-within-screen until it fills frame, repeat (#12). Infinite-zoom
   feel with zero VFX — production sequencing.
5. **CANVAS MOVES ON BEATS.** Squeeze, reopen, split, resize — timed to musical hits (#5).
6. **PHYSICAL MASK WIPES.** Scissors cutting paper layers (#16), napkin wiping a screen (#22) — the
   in-world object performs the wipe.
7. **MEME INSERT SNAP.** Walkthrough → full-screen reaction meme → snap back to the same room (#25).
8. **FAST-HOOK / SLOW-BODY.** Universal shape: hook cuts every 0.7-2s, body relaxes to 3-6s holds,
   one "breath" drone shot mid-video, end card ~3s (#1, #21, #24).

---

## PART 3 — MUSIC & BEAT-SYNC RULES

- Winners use either a LICENSED FEEL-GOOD TRACK (California Honeydrops #29, Madonna #2) or
  ORIGINAL SPOKEN AUDIO (all the skit/meta pieces). Nothing in between.
- Beat-sync where it appears (#2, #5, #18) is CUT-ON-BEAT + FRAME-MOVE-ON-BEAT: shots change every
  1, 2 or 4 beats; alternate fast (1-beat) and slow (4-beat) shots — breathe-in/breathe-out, never
  constant machine-gun.
- HOW WE REPLICATE: onset/beat-detect the chosen track (librosa), snap every cut and every canvas
  move to the beat grid, place the hook's arrival moment on a downbeat, end card on the outro phrase.
- IG POSTING REALITY: for maximum reach the track should be added as IG in-app trending audio when
  possible. Deliver two masters: (a) MUSIC-BAKED beat-synced master for YouTube/FB/direct upload,
  (b) the same edit MUTED (cuts still on the grid) so Graeham adds the trending version in-app and
  the cuts still land. Commercial tracks (Madonna etc.) can only be used via in-app audio — never baked.

## PART 4 — TEXT SYSTEMS (pick exactly one per video)

- T1 EDITORIAL SERIF (magazine): lowercase serif italic + bold mix, upper-third ("vítejte v Třinci" #1,
  gold "ABU DHABI" card #5, address serif card #24). For cinematic/luxury pieces.
- T2 BILLBOARD BARS: huge condensed caps on the letterbox bars, animating on beats (#4).
- T3 KARAOKE CAPS: 1-3 word white extra-bold caps, center, popping with VO (#7, #9, #17, #21).
- T4 DIEGETIC TEXT: the words exist IN the world — phone screens (#10), paper layers (#16), napkin
  (#22), spray paint (#18), news chyrons (#20). The strongest system — use whenever possible.
- T5 PILL CHIPS: black/white rounded pills for specs + 📍address chip (#9 tour, #29). Save-trigger.
- T6 NONE: zero text, caption carries everything (#2, #3, #23). Confidence play for pure-cinema hooks.

## PART 5 — AI / REAL BLEND RULES

**STANDING RULE (Graeham, July 2026): GRAEHAM DOES NOT APPEAR ON CAMERA. Every human presence
is AI: composite him via Nano Banana Pro (Graeham-RealPhotos element + anti-cleft identity block,
wardrobe: white oxford sleeves-rolled + navy chinos as the signature outfit), animate via Seedance,
voice via HeyGen photo-avatar + voice clone. Concepts that required filming him (roast tour, trunk
skit, dance ad, "everything is fake") are executed with avatar composites + Seedance action shots,
or converted to object/canvas concepts. Property footage stays REAL (existing 4K listing clips).**

- AI is for the IMPOSSIBLE 3 SECONDS + THE AVATAR; the listing itself must be real footage (#1, #24
  both hand off at the door). A fully-AI listing video sells nothing — the fully-AI pieces in the
  library are selling prompts (#2, #27), not property.
- Sell the seam with CONTINUITY: same wardrobe (white suit #24), same door, same lighting direction.
- Exception: format-hijack narratives (#20) may be fully AI because the story is the ad.
- Bake handheld drift into AI prompts ("handheld POV, slight camera shake") so generated clips read
  as camera footage next to real gimbal shots (#27's trick).

## PART 6 — ENGAGEMENT ENGINEERING (what the winners do off-screen)

- COMMENT-GATE one asset per video: "Comment TOUR / WILLARD / SEND" (#10: 3.8K comments, #27: 8.7K).
  GHL keyword automation must be armed BEFORE posting.
- SHARE-BAIT: the joke must be self-contained so sharing completes it (#7, #12, #20). Shares > comments
  on every viral outlier in this library.
- LOOP ENGINEERING: last frame = first frame (#22), or payoff lands AT the loop seam (#23) so viewers
  watch twice. Sub-10s loops multiply completed-view rate.
- SERIES SCAFFOLD: "EP. 2" (#19), "Day 1 of ranking…" (#26) manufacture return viewers; comment bait
  = "which one next?"
- CAPTION DOES THE SELLING: on-screen stays entertainment; credentials, specs, open-house times,
  objection-handling live in the caption (#8, #16, #23).

## PART 7 — PRODUCTION TIERS (all-AI cadence — no filming Graeham, ever)

- TIER A (pure AI object/canvas, same-day, no avatar): flying keys, address side-quests, screen-peel-
  to-listing, skywriting, scissor-countdown (AI macro), fake-news open house. → every listing launch.
- TIER B (avatar composite + Seedance action): helicopter arrival, walk-up hooks, "agent on the roof",
  crime-scene drone (avatar lying in frame via composite), escalator clones (two composites masked).
  → 1/week.
- TIER C (avatar + HeyGen VO): talking-head beats, roast-tour VO over AI+real b-roll chain, price-guess
  and contrarian reels (the existing viral-video-engine pipeline). → every listing.
- TIER D (multi-scene AI narrative): mockumentary-style episodic pieces cast entirely with AI
  characters (Seedance multi-shot + HeyGen dialogue). → quarterly brand piece; hardest, highest ceiling.

## PART 8 — THE STANDING FORMULA (every future listing video)

1. Pick ONE hook family (H1-H8). The hook is decided BEFORE the script.
2. Hook occupies 0-3s, arrives ON a downbeat, and hides its seam in a hard cut.
3. Fast-hook/slow-body rhythm; every cut on the beat grid; one breath shot mid-video.
4. One text system only. Diegetic beats digital.
5. AI for the impossible part only; real footage sells the house; continuity sells the seam.
6. Loop-engineer the ending. Comment-gate one asset. Caption carries the specs.
7. Deliver: music-baked master + mute-cut master (for in-app trending audio) + captions + pinned comment.
