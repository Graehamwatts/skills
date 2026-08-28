---
name: split-screen-avatar-reel
description: "Build IG/TikTok/Shorts reels in the split-screen news format — b-roll filling the TOP half of a vertical 9:16 frame, a bold two-line ALL-CAPS headline straddling the seam, and Graeham's HeyGen talking-head avatar filling the BOTTOM half for the whole video. This is the layout used by hyperlocal real-estate-news accounts like @bayareawilson. Use ANY time the user mentions: split screen video, split-screen reel, top-bottom video, half-and-half video, upper b-roll lower talking head, news-anchor-style reel, stacked video layout, b-roll on top avatar on bottom, or references bayareawilson-style reels as a target. Also trigger on 'do another split-screen video', 'same format, new topic', or 'composite the avatar and b-roll into the split screen'. Owns frame layout only — hands off to heygen-video/heygen-elevenlabs-renderer for the avatar half and higgsfield-video for the b-roll half, then composites. Not for full-bleed talking-head videos or the Reventure punch-in format (education-graeham-videos)."
---

# Split-Screen Avatar Reel

Assembles the "b-roll top half / avatar bottom half" split-screen format — see
`references/format-breakdown.md` for the full visual teardown of the three reference reels
this was built from (`@bayareawilson` on Instagram: Safeway Marina, Treasure Island, and
Fisherman's Wharf reels).

**This skill is an orchestrator + compositor, not a third rendering pipeline.** It does not
call HeyGen or Higgsfield directly — it hands off to the two skills that already do that well,
waits for finished clips, then runs the bundled compositor script. Read that reference file
before the first run of this skill so the frame anatomy is fresh in mind.

## When this skill fires

- "Make a split-screen reel about [topic]"
- "Same format as those bayareawilson reels, but for [Graeham's story]"
- "Composite this avatar clip and this b-roll into the split-screen layout"
- "I have a HeyGen render and a Higgsfield clip, stack them"

If the user has a TOPIC but no SCRIPT/headline yet, chain with `content-creation-engine` (or
`education-graeham-videos` if it's Bay Area market/development news — matches this format's
actual content genre most closely) first. That skill's job is finding the story and writing a
tight VO + headline; this skill's job starts once there's a script.

## Workflow

### 1. Get the story and a short VO script

A script for this format should be short — the reference reels read like 20-40 second news
hits, not full explainers. If chaining from `content-creation-engine` / `education-graeham-videos`,
ask for a punchy, single-story script (one development, one number, one hook) rather than a
multi-beat long-form script — this layout doesn't have room for a beat-by-beat structure since
there's no cutting between shot types, just one continuous talking-head take under one
continuous (or slowly-changing) b-roll.

### 2. Ask the required questions in one turn

Before rendering anything, confirm:

1. **Avatar look + voice** — same mandatory ask as `heygen-video`: which look, or default
   voice clone? Don't silently pick one.
2. **Headline text** — two short lines, ALL CAPS reads best (the compositor uppercases
   automatically). If the user doesn't give exact wording, propose one derived from the
   script's hook and confirm before rendering — this is the first thing anyone sees, worth
   getting right.
3. **B-roll subject/scene** — what should fill the top half? One strong establishing shot is
   enough for a ~20s reel; for longer reels, ask if they want a second b-roll clip to cut to
   partway through (the compositor accepts multiple `--broll` clips and concatenates them).
4. **Color scheme** — default is Watts Gold (`#C4A265`) for line 1 / white for line 2, which
   keeps this on-brand with Graeham's other video work. Offer the reference reels' brighter
   yellow (`#F5C518`) as an alternative if they want a closer visual match to the source
   accounts.

### 3. Render the bottom half — avatar

Hand off to `heygen-video` (or `heygen-elevenlabs-renderer` if this is part of an
auto-render chain) with the confirmed script, look, and voice. Request the **normal 9:16
default** — no special aspect handling needed, the compositor crops whatever comes back.
Wait for the finished MP4 per that skill's normal submit-and-check flow; don't block the
conversation on a multi-minute render.

### 4. Render the top half — b-roll

Hand off to `higgsfield-video` with the confirmed scene description. Request 9:16 (matches
the compositor's default crop strategy). Duration: doesn't need to match the avatar's runtime
exactly — the compositor loops/holds the last b-roll frame to fill whatever the avatar clip
runs. A single 10s clip covers most reels in this format fine.

### 5. Composite

Once both MP4s are downloaded:

```bash
python3 scripts/composite_split_screen.py \
  --avatar /path/to/heygen_render.mp4 \
  --broll /path/to/broll_clip.mp4 \
  --headline-line1 "SAFEWAY MARINA ADDS" \
  --headline-line2 "800 HOMES" \
  --accent-color "#C4A265" \
  --out /path/to/output_master.mp4 \
  --posting-copy /path/to/output_posting.mp4
```

What it does (see the script's own docstring for full detail):
1. Normalizes both clips to a canonical 1080x1920 "cover crop" — so it doesn't matter if
   HeyGen or Higgsfield handed back slightly different source dimensions.
2. Crops the top 960px of the b-roll and the bottom 960px of the avatar (loops/holds b-roll
   to cover the avatar's full runtime if it's shorter).
3. Draws the two-line headline as a transparent overlay straddling the seam (y=960), bold
   caps with a heavy black outline for legibility over any background.
4. Stacks top+bottom, overlays the headline, muxes in the avatar clip's own audio as the
   only soundtrack.
5. Outputs a CRF 18 master, and optionally a smaller CRF 23 "posting copy" sized to fit a
   typical ~30 MiB chat-share limit.

**`--avatar-anchor-y` (default 520)** controls where in the normalized 1920px-tall avatar
frame the bottom crop starts. HeyGen's default framing varies a little by look — if the
presenter's chin gets clipped or there's too much headroom, pull a single normalized frame
first (`ffmpeg -i avatar_norm.mp4 -frames:v 1 check.png` after a dry run, or just render once
and look at the composited result) and adjust this value up (crops lower/tighter) or down
(crops higher, more headroom) before re-running — cheap to iterate since it's pure ffmpeg, no
credits spent re-rendering the avatar itself.

**`--top-anchor-y` (default 0)** does the same for the b-roll — 0 keeps the top of the frame,
raise it if the interesting part of the shot is lower in the source composition.

### 6. QC before delivery

- `ffprobe` the output: confirm 1080x1920, audio stream present, duration matches the avatar
  source (±0.5s).
- Pull 2-3 frames across the runtime (`ffmpeg -ss <t> -frames:v 1 ...`) and look at them:
  headline fully on-screen and not clipped at the frame edges, seam is clean (no visible
  crop artifacts), avatar isn't cut off at the chin or missing too much headroom.
- Confirm the posting-copy file (if generated) is under ~30 MiB; if not, bump `--posting-copy`'s
  CRF higher or shorten the reel.

### 7. Deliver

Hand back both the master and posting-copy files (see delivery conventions — master stays
in-session, posting copy is what actually gets shared). If this is part of a recurring
content day (paired with `education-graeham-videos` research), offer to log the finished
reel the same way that pipeline's other outputs are tracked.

## What this skill intentionally does NOT do

- ❌ Does not call the HeyGen or Higgsfield APIs/UI itself — always hands off to those skills.
- ❌ Does not write scripts or find stories — hands off to `content-creation-engine` /
  `education-graeham-videos`.
- ❌ No word-level karaoke captions in v1 — the reference reels didn't show any at the
  captured frame, just the static two-line headline. If a future reel needs them, that's a
  compositor addition, not a redesign.
- ❌ No mid-reel b-roll cutting logic beyond simple concatenation of clips the user provides
  in order — if a reel needs precisely-timed cuts synced to VO beats, treat that as a v2
  ask rather than assuming it here.
- ❌ Does not auto-pick avatar-anchor-y per look — this needs a one-time eyeball check per
  HeyGen look the first time it's used in this format, then it's a known-good value to reuse.

## Files in this skill

- `SKILL.md` — this file
- `scripts/composite_split_screen.py` — the compositor (ffmpeg + Pillow, no other deps)
- `references/format-breakdown.md` — visual teardown of the three reference reels this
  format was built from, including what's confirmed vs. unconfirmed from a single frame each
