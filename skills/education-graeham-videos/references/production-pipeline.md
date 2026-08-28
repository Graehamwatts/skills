# Reel Production Pipeline — the ACTUAL build steps (locked 2026-08-05, avatar-look step
simplified 2026-08-12 — see Steps 0-4 note)

This is the pipeline every reel follows after the script is approved. Phase 4 of SKILL.md
points here. Do NOT substitute the old "hand off to heygen-video" flow — this file IS the
production process. All steps run inside the session (curl + python + ffmpeg + Higgsfield MCP).

**2026-08-12 change, per Graeham's explicit standing instruction — read before running
Steps 1-4:** avatar-look generation no longer runs a Seedance animation/training-video step.
Higgsfield produces ONE still image per orientation (Nano Banana Pro compositing the identity
reference into the real environment reference), and that still is uploaded straight to HeyGen
as a photo-based look — HeyGen does the animating, not Seedance. This replaces the old
training-speech-audio + Seedance-video + Topaz-video-upscale chain entirely. Reasoning: it's
the same end result (an HD look of Graeham at a real location) with fewer moving parts and no
lip-sync-training footage to QC before the look even exists.

## Accounts / IDs registry (not secrets — keys are asked from Graeham per process rule)

- HeyGen avatar group (digital twin "Graeham Watts"): `2160746aa659445e9cbfa4c02e5cf39c`
- ElevenLabs voice: `Pa3vOYQHHpLJn1Tf7hnP`, model `eleven_multilingual_v2`,
  voice_settings `{stability 0.38, similarity_boost 0.8, style 0.45, speed 1.08}`,
  endpoint `/v1/text-to-speech/{voice}/with-timestamps` (save alignment JSON).
- Existing trained looks (reusable free — check list before creating new ones):
  `GET /v3/avatars/looks?group_id=...`:
  - `selfie_walk` 48a9a8650bf74c41a8b9241710613b19 (residential street, walking)
  - `rwc_theatre_way` 1be85000c5704390935b916c24bdc157 (+ `_wide` d5dfb97465c744fab193f2363684aea5)
  - `sj_cityhall_hd` 9af7ef6e900b47c4afbd27ebeefc11b0 (+ `_hd_wide` 9aa44d5ed69542d291f791cbd12878b9)
    — HD pair, San Jose City Hall, charcoal jacket (prefer these for SJ)
  - **Note:** these were built under the OLD Seedance-video method and remain valid/reusable
    as-is. Every NEW look built from 2026-08-12 forward uses the still-image method below —
    don't rebuild an existing look just to match the new method.
- Identity reference for Higgsfield: `assets/identity_ref.png` (bundled in this skill).
- SFX: `assets/sfx_whoosh.wav` (airy swept-noise build), `assets/sfx_pop.wav`.
- Compositor: `assets/compositor_template.py` — fork per video, edit the marked config
  (alignment file, SEGS word-finds, CAPS_STACKS, ELL/ARROW, stickers, endcard subject +
  DM keyword, input/output filenames). All locked patterns live in it.

## Step 0 — Location decision (MANDATORY, every video)

If the video is about a specific place, the avatar MUST appear AT that place:
1. Check the looks registry above — if a pair for this location already exists, reuse it
   (fresh outfit is preferred though: a new pair per video is the standing default; reuse
   only when credits/time force it AND Graeham okays it).
2. Otherwise CREATE a new look pair (Steps 1–4). This is not optional and not something to
   silently skip — if Higgsfield credits or keys are missing, STOP and ask Graeham.
3. **No specific place applies to this topic (locked 2026-08-12)** — e.g. a regional/
   market-wide topic with no single location: default to a real, notable, recognizable Bay
   Area street or landmark corridor — East Palo Alto, Menlo Park, Redwood City, San
   Francisco, or elsewhere in the Bay. Pick somewhere the audience would actually recognize
   (a known downtown block, a landmark street, a recognizable waterfront), never a generic
   anonymous suburban block picked just to have *something* in frame. Source a real
   reference image of that location the same way as Step 1 below.

## Step 1 — Environment reference (real place imagery)

Google Street View capture via browser tab + screenshot:
`https://www.google.com/maps?layer=c&cbll={lat},{lng}&cbp=12,{heading},0,0,5}`
(or streetviewpixels-pa.googleapis.com thumbnail URLs). Crop to the landmark. This becomes
the Higgsfield environment reference so the composited still looks like he's really there —
use a REAL captured image here, not an AI-hallucinated approximation of the location, even
though the compositing step itself is AI-generated.

## Steps 2-3 — Higgsfield still-frame generation (per orientation, replaces Seedance training)

For EACH orientation (9:16 portrait, 16:9 landscape), generate ONE 4K Nano Banana Pro still —
follow the `higgsfield-video` skill's Stage 1 process (Realism Rescue Protocol, Anonymization
Strategy where the location is sensitive) with both `identity_ref.png` and the Step 1
environment capture attached as drag-and-drop reference images:
1. Navigate to `https://higgsfield.ai/image/nano-banana-pro`, clear prior prompt/attachments.
2. Drag-and-drop both `identity_ref.png` and the environment capture into the prompt area.
3. Prompt: "the man from the first reference image (same face, same glasses) standing at the
   location from the second reference image, in a NEW outfit (name it), natural candid pose,
   realistic lighting matched to the environment reference" + the Realism Rescue Protocol
   anchor stack for the location shot itself.
4. Set aspect (9:16 or 16:9 to match this orientation), 4K, batch 4/4. Generate, pick the
   hero variant per the usual narrate-and-recommend process, download to Downloads.
5. Repeat for the other orientation using the SAME outfit/identity framing for continuity
   between the pair — only the aspect crop/composition changes.

**MANDATORY approval gate (locked 2026-08-12, per Graeham's explicit standing instruction) —
before either still touches HeyGen:** present both hero stills to Graeham and get an explicit
"yes, that looks like me" before uploading either one as a look. This is a hard stop, not a
courtesy — do not proceed to Step 4 on an assumed approval, and do not upload a still Graeham
hasn't seen. If he says it doesn't look like him, regenerate (adjust the prompt/reference
weighting, try a different variant from the same batch, or re-batch) and show him again before
moving on. This mirrors the same "wait for approval" discipline already used for topic picks
(Phase 1) and script review — a wrong face is a much more expensive mistake to catch after a
full render than before one.

## Step 4 — HeyGen look upload (HD, no separate upscale pass needed, confirmed 2026-08-12)

Higgsfield's Nano Banana Pro output is native 4K, so unlike the old Seedance-video path there
is no Topaz upscale step before creating the look — the still is already HD. Upload mechanism
confirmed directly from Graeham's HeyGen account (screenshot, 2026-08-12): the Photo Avatar /
Looks library has an **"Upload look"** tile right next to "Design with AI" in the look grid —
click it and upload the approved still directly, no separate API call needed. Since this is a
UI action, drive it via Claude in Chrome:
1. Navigate to HeyGen's Avatar/Photo Avatar looks page (under the existing avatar group).
2. Click the **Upload look** tile.
3. Upload the Graeham-approved hero still for this orientation (same file-access pattern as
   Higgsfield uploads — if the native OS file picker blocks Chrome automation, use the
   drag-and-drop-from-Downloads workaround, same as the `higgsfield-video` skill's documented
   fallback).
4. Name the resulting look `<loc>_hd[_wide]` to match the existing naming convention, repeat
   for the other orientation.
Wait for the look to finish processing before moving to Step 5 (VO) / Step 6 (renders). Confirm
the exact processing-time/ready-state indicator on the first live run and note it here once
seen — not yet observed under this flow.

## Step 5 — VO (rules in SKILL.md 0g apply: no em-dashes, decimals not $, speed 1.08)

`/with-timestamps` → save mp3 + alignment JSON. MANDATORY Whisper QC (full track, base
model): transcript must be word-perfect, no extra syllables. Pause-profile check: no
mid-sentence gap > 0.5s, sentence gaps <= ~0.8s (surgically cut longer ones + shift the
alignment times; mute any vocal artifact windows with fades).

## Step 6 — Three HeyGen renders (v3 endpoint ONLY)

Upload VO mp3 as asset, then `POST /v3/videos` three times:
1. Portrait look, resolution `"4k"`, 9:16 (the main AV — punch-ins downscale from it)
2. Portrait look, 1080p, 9:16, `output_format: "webm", remove_background: true` (alpha)
3. Wide look, 1080p, 16:9 (the split-screen lower strip)
4K jobs sometimes fail with a transient INTERNAL_SERVER_ERROR — just resubmit.
Verify every download with `ffmpeg -v error -i X -f null -` (truncated curl at the 2-min
Bash timeout = corrupt NAL units; re-download, use longer timeouts).

## Step 7 — Evidence inserts

Blur-fill background (page scaled to 1920 h, GaussianBlur 34, brightness 0.42), page at
~1.15x with per-page x0 so full headlines fit, paste at y=120. RED annotations per SKILL.md
QC 6a (corner test <= 0.86; arrow-instead-of-circle on dense row pages). Render check
overlays and VIEW them before compositing.

## Step 8 — SFX mix (VO-first architecture — never loudnorm the finished mix)

1. loudnorm the VO ALONE to I=-14 (dynamic ok on speech).
2. Add whoosh at cuts (gain such that gap RMS lands ~9-10 dB under speech RMS — 0.30 with
   the bundled whoosh), pop 0.32 on caps-stack words.
3. Final mux from wav with `alimiter=limit=0.79:level=false` (level=false is critical —
   default level=true normalizes the ceiling right back up). QC peak −1 to −3 dB.

## Step 9 — Composite

Fork `assets/compositor_template.py`. Key locked patterns already inside: 4K AV pipe with
frozen per-interval punch-ins (LANCZOS, crop coords ×2), hook native zj=1.0, EXAGGERATED
jump cuts 1.15 <-> 1.75, insert zoom ease, wide strip paste (0,1385) + gold stroke,
fixed-line pop-in captions y=1420, caps stacks, whip-blur + impact settle at cuts, warm
grade + vignette, endcard (logo/DRE/cursive subject/DM keyword button). B-roll: conform to
25fps with minterpolate (mci/aobmc/vsbmc) BEFORE frame extraction; boomerang-extend if the
segment outruns the clip.

## Step 10 — Full-sweep QC (SKILL.md checklist) → deliver

Master CRF 18 (kept in session) → chat copy CRF ~23 (≤30 MiB) → disk copy two-pass
(≤20 MiB) → `Downloads\<Topic>-<date>\FINAL\<Hook Phrase>.mp4` — FINAL holds exactly ONE
file; prior versions move to `old\`. Skill updates from the day's feedback ship the same day.
