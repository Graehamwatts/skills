# Format breakdown — the reference reels

Sourced from three reels on `@bayareawilson` (Instagram) that Graeham flagged as the exact
target format:
- instagram.com/reel/DbyCcCVh0w5 — "Safeway Marina Adds 800 Homes"
- instagram.com/reel/Dbo2vozh_oe — "Treasure Island Opens First Condo Homes"
- instagram.com/reel/DbwlJ_rhvgR — "A New Ten-Million-Dollar [Fisherman's Wharf plaza]"

All three are the same account, same presenter, same rig, same edit template — this is a
repeatable format, not a one-off. What follows is what's visually verifiable from the three
reels; anything not directly observable (their VO length distribution, whether the b-roll ever
cuts mid-video) is flagged as unconfirmed.

## Frame anatomy (1080×1920, confirmed)

- **Top half (y 0–~960):** b-roll. In the three examples: a static drone/aerial rendering, a
  Google-Maps satellite pan, and a rendered site-plan/plaza illustration. Not necessarily
  filmed footage — at least one looked like a still or slow-zoom rendering rather than dynamic
  video. Treat "b-roll" loosely: a slow push/zoom on a single strong image reads fine here,
  full motion isn't required.
- **Seam headline (straddles y ~830–960, i.e. bottom of the b-roll half):** two stacked lines,
  bold condensed sans-serif, ALL CAPS, heavy black outline/drop-shadow for legibility over any
  background. Line 1 in a warm gold/yellow, line 2 in white (confirmed consistent across all
  three examples — gold line always comes first). Text is short — 3-5 words per line, reads
  like a headline not a caption ("SAFEWAY MARINA ADDS" / "800 HOMES").
- **Bottom half (y ~960–1920):** the presenter, static medium shot (chest-up), same indoor set
  in all three (warm-lit shelf with plants and framed photos behind him), gesturing while he
  talks. He's centered horizontally, positioned so his eyes/face sit in the upper third of the
  bottom half — there's headroom above him, not a tight crop.

## What's NOT confirmed from a single frame each

- Whether the b-roll cuts to a second shot partway through longer reels (likely yes for
  anything over ~15s, but not verified frame-by-frame).
- Exact runtime / pacing — likely 20-40s based on typical reel length for this content type.
- Whether there's a word-level caption track anywhere else in the video (the captured frames
  show only the static two-line headline, no karaoke captions visible at that timestamp).
- Font family (visually a heavy grotesk/condensed sans — Liberation Sans Bold or similar is a
  reasonable stand-in; doesn't need to match exactly to hit the same read).

## Caption text (for context on tone/topic, not part of the visual format)

Real, hyperlocal SF Bay Area development news — e.g. "The Safeway Marina redevelopment just
updated its plans to 848 units across two towers up to 258 ft at 15 Marina Blvd — and the
grocery store stays open throughout construction." Each caption ends with an engagement
question and a comment-to-DM CTA ("Comment 'update' to get our Bay Area newsletter"). This
maps directly onto Graeham's existing `education-graeham-videos` / `content-creation-engine`
research and CTA conventions — this skill owns the FRAME LAYOUT, not the story-finding or
copywriting, which stay with those skills.

## Why this skill doesn't reinvent the avatar or b-roll pipelines

Graeham already has mature, credit-metered pipelines for both halves:
- `heygen-video` / `heygen-elevenlabs-renderer` render the presenter (9:16, native HeyGen
  framing — a chest-up medium shot is HeyGen's default composition, which is exactly what the
  bottom half needs).
- `higgsfield-video` renders the b-roll (9:16 or 16:9, Nano Banana Pro / GPT Image 2 → Seedance
  / Kling).

This skill's only job is: take those two already-rendered clips and the headline text, and
assemble them into the split-screen frame. It never calls HeyGen or Higgsfield APIs directly —
it hands off to the two skills above and waits for finished MP4s.
