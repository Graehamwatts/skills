---
name: viral-video-engine
description: >-
  Graeham Watts' finished-video production engine — the DEFAULT for all listing videos and
  social video content. Produces completed, post-ready MP4s (not scripts): 9:16 reels with
  3-second hooks, word-timed b-roll cutaways, burned-in captions, music bed, and DM/call CTAs;
  silent cinematic teasers; 16:9 YouTube tours with retention architecture. Trigger on: make a
  video, listing video, viral video, reels for [address], finished video, edit the video,
  video with music, post-ready video, or "like we did for 1030 Bradley Way." Orchestrates
  heygen-video (fresh on-location composited avatars — never digital_twin, never desk),
  Higgsfield MCP (Seedance b-roll, Nano Banana composites), Whisper cut timing, and a
  resumable ffmpeg editor. Encodes the viral playbook: hook formulas, front-loaded cuts,
  caption grammar, 1080p/4K export specs per platform. Over-trigger for any property or
  brand video request.
---

## STANDING BRAND RULES — every video (locked 2026-07-31, from Graeham's reference frame)

**End card (final ~5s of EVERY finished video), composited over a ~60% black wash of the
closing shot:**
1. TOP: white GRAEHAM WATTS logo lockup (gold roof icon + gold divider + REALTOR), from
   `carousel-builder/assets/logo/logo_white.png`, ~860px wide (1080-wide frame), centered.
2. Under logo: `COMPASS · DRE #01466876` letter-spaced Montserrat, white. The brand end card
   DOES show the DRE — on this card it supersedes any "no DRE on screen" note elsewhere.
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
6. Report findings to Graeham WITH the two things frame QC cannot verify (audio feel, motion
   between frames) called out explicitly. Never claim 100% on unverified dimensions.
A video that has not passed the full sweep is NOT delivered. Deliver-then-fix is a rule violation.
 Avatar look must be confirmed by Graeham (current
standing pick: look 4 `fashion_flip` / look 5 `bespectacled` per heygen-video avatars.md).

# Viral Video Engine — finished videos, every time

This skill produces **completed videos**, not scripts. The deliverable is post-ready MP4s in the
listing folder. Scripts, shot plans, and avatar generation are intermediate steps that happen
inside this pipeline without being presented as final output.

## Read first

1. `references/viral-playbook.md` — hooks, retention architecture, CTA system, export specs. Every creative decision traces to this.
2. `references/edit-pipeline.md` — the proven technical pipeline + hard-won gotchas (content-filter retries, resumable encoding, HeyGen avatar API).

## Standard package per listing

| Asset | Spec | Notes |
|---|---|---|
| Reel 1 — price-anchor hook | 9:16, 1080x1920, 30-50s | Walk-up or on-location hook, avatar + timed cutaways |
| Reel 2 — second angle (lot/flaw/story) | 9:16, 15-30s | B-roll heavy, avatar bookends only |
| Silent teaser | 9:16, ~15s | Music + brand text only, mirrors carousel treatment |
| YouTube tour | 16:9, 4-10 min, 4K master when sources allow | Full retention architecture, chapters, numbers section |

## The pipeline (phases — run in order)

### Phase 1 — Facts & angle
Pull verified listing facts (MLS shared link via Chrome if client-rendered). Choose the hook
formula from the playbook (price-anchor default; lot/flaw/story for the second angle). Date-anchor
every stat ("as of [month year]"). Fair Housing check: features/price/commute only — no demographic
proxies, no school rankings, no "safe/family-friendly."

### Phase 2 — Scripts (internal deliverable)
Write VO per playbook structure: hook <=3s (no greetings, no name until ~20s), one open loop,
spoken CTA. Numbers written for TTS ("924,000 dollars", "A.D.U.", "E.P.A.").
**CTA default: "DM me '[KEYWORD]' for the full details and private tour times — or call me
directly, number's in my bio."** Say it + show it + pin it.

### Phase 3 — On-location avatar (MANDATORY RULES)
- NEVER digital_twin, NEVER desk looks. Every video gets a FRESH avatar composited on location.
- Higgsfield MCP: create environment element from a listing photo (show_reference_elements
  action=create), then generate_image model nano_banana_2 with <<<Graeham-RealPhotos>>>
  (element cb7aa460-f6a8-4534-b737-ef9f40e6e23a) + <<<listing-environment>>>. 9:16 for reels
  (front of house), 16:9 for YouTube (interior). Include the anti-cleft chin block. 2 variants, QC identity.
- Create HeyGen photo avatar: heygen avatar create -d '{"type":"photo","name":"...","file":{"type":"url","url":"<higgsfield CDN url>"}}'
- Render via heygen-video create.py --avatar-id <look> at the FINAL aspect (9:16 reels / 16:9 YT).
  Voice: Graeham Voice Clone default. Submit-and-poll, never --wait.
- Bonus hook shot: animate the front-of-house composite with Seedance ("walks toward camera") — silent b-roll under the hook VO.

### Phase 4 — B-roll
Footage hierarchy: **real 4K listing clips first** (contact-sheet them to map rooms), Seedance
image-to-video from listing photos only for moves that don't exist, photo zoompan last resort.
Generate at final aspect. Upscale AI b-roll (upscale_video) before any 4K timeline.
Content filter false-flags aerials/yards randomly — reword and resubmit (see edit-pipeline.md).

### Phase 5 — The edit (v4 system — see references/edit-pipeline.md "v4 additions")
1. scripts/transcribe_words.py <render.mp4> → word-level timestamps (faster-whisper tiny.en).
2. TRAILER HOOK first 3s: 4-6 rapid cuts under a giant gold slam price element from frame 1.
   Never open static; trim walk clips to mid-stride.
3. Segments: cut on sentence boundaries (edit_pipeline.py or a per-video build script with the
   same tmp-rename resumable pattern); front-load cuts; visual reset <=20s long-form.
4. TEXT = scripts/textfx.py ONLY (animated carousel-brand elements: gradient gold, Montserrat,
   shadows on everything, panels over bright footage, chest-level placement, autofit width).
   Plain drawtext is retired.
5. END CARD: 0.6s xfade from final avatar shot into a drone/aerial clip + end-card block over
   dark wash. CTA overlay ends before the crossfade. Music rises on the card; never fades
   during speech. Video runs ~3s past the last word.
6. AUDIO (STANDING RULE, client-locked): deliver VO-ONLY masters — normalized VO
   (loudnorm I=-16:TP=-2) + volume 1.25 + alimiter=0.89, apad to video length, NO music baked in.
   Graeham mixes music himself in CapCut. Ship candidate tracks as separate WAVs in
   Video_Renders/Music/ (HeyGen catalog 120s tracks, acrossfade-extended for long-form).
   Teaser ships silent. Do not bake a music bed unless Graeham explicitly asks.
   Long-form: extend 120s catalog tracks via chained acrossfade — never butt-loop. See edit-pipeline.md.

### Phase 6 — QC + delivery (never skip)
- Frame-sheet every final (8-16 frames across the timeline) and LOOK at it: check for stalled/frozen
  video (corrupt segment symptom), overlay timing, avatar identity.
- Verify duration + audio present. cmp after copying big files to the mounted folder (copies truncate silently — chunked dd for >150MB).
- Deliver to <listing folder>/Video_Renders/FINAL/. Present files. Captions + posting copy per platform.

## Export specs (lock)

- Reels/TikTok: 1080x1920 H.264 8-10 Mbps, 30fps, AAC 256k/48kHz. Remind Graeham: IG "High-Quality Uploads" ON.
- YouTube: 4K master upload when sources allow (real footage is 4K) — better codec tier even for 1080p viewers.
- Archive master per video kept in FINAL/.

## What this skill supersedes

For listing/social video content, this skill is the entry point — it CALLS heygen-video,
higgsfield-video/Higgsfield MCP, and vaibhav-template internally. Don't freestyle those
individually for listing content. video-script-creation-engine remains the source for
non-video content packages and SSML variants.
