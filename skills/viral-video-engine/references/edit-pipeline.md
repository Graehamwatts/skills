# Edit Pipeline — technical reference (proven on 1030 Bradley Way, July 2026)

## Asset flow
1. Listing photos → Higgsfield media_upload (presigned PUT via curl) → media_confirm → media_ids.
2. Environment elements from photos → nano_banana_2 composites of Graeham ON LOCATION
   (character element Graeham-RealPhotos cb7aa460-f6a8-4534-b737-ef9f40e6e23a).
3. Composite image URL → HeyGen photo avatar (avatar create type=photo) → look_id → create.py render at final aspect.
4. Seedance 2.0 image-to-video b-roll from listing photos (start_image role), final aspect, 4-5s.
5. Real 4K clips: build a contact sheet (1 frame per clip) to map rooms BEFORE planning cuts.

## Timing
- faster-whisper tiny.en word timestamps on the avatar render = ground truth for cut points.
- Cut at sentence boundaries: boundary = midpoint between last word end and next word start.
- Front-load: hook segment cuts ~0.5-1s each; body 2-3s; CTA holds longer.

## edit_pipeline.py (scripts/)
JSON plan → resumable build:
- Segments encode one at a time to .tmp then os.rename (NEVER trust a file that wasn't renamed —
  timeouts leave corrupt no-moov MP4s that stall the concat silently).
- Kinds: av (avatar slice), ai (720p AI clip → scale), raw169 (4K 16:9 → scale), raw916 (4K → center crop 1215x2160 → 1080x1920), img (zoompan).
- All segments: fps-normalized, setsar=1, tpad stop_mode=clone + trim to exact duration.
- concat demuxer with -c copy (uniform encodes), then drawtext overlay pass, then audio mux:
  full-length avatar audio + looped music (volume 0.08-0.12) via amix duration=first, afade out.
- Long videos: split overlay pass at a segment boundary, encode halves (shift enable times), concat, mux with -c:v copy.
- Re-run the same command after timeout — completed segments are skipped.

## Music
HeyGen catalog: heygen audio sounds list --query "<mood>" --limit 8 → data[].audio_url presigned WAV.
Moods that worked: "warm minimal cinematic beat" (reels), "elegant cinematic real estate warm ambient" (YT), "calm minimal ambient" (teaser).

## Gotchas (each cost real time — respect them)
- Seedance content filter randomly false-flags yard/aerial frames ("nsfw" status): reword prompt (avoid repeating flagged phrasing), resubmit with declined_preset_id if a preset notice intercepts. 16:9 passing does not mean 9:16 passes.
- "IN THE DARK" preset recommendation intercepts fireplace/glide prompts — always retry literal with declined_preset_id.
- Background processes (nohup/setsid) DIE between bash calls — never rely on them; use resumable sync scripts with timeout + re-run.
- HeyGen status.py download path may not exist in sandbox — fetch video_url from heygen video get and curl.
- Copying >150MB to the mounted folder can silently truncate — chunked dd (bs=4M, skip/seek) then cmp to verify.
- HeyGen photo avatar training is fast (<1 min) — poll avatar looks get until dims/preview populate.
- HeyGen reads scripts ~15-20% faster than natural pace — target runtime accordingly.
- Whisper transcription quirks (e.g. proper nouns) don't matter — only timestamps are used.
- Fonts: download Playfair Display Italic / DM Sans / Inter TTFs from github.com/google/fonts (ofl/ paths) — escape %5B %5D in URLs.
- drawtext: avoid raw apostrophes/colons/commas — use ’ and \\, \\: escapes.

## QC (mandatory)
Frame-sheet each final across the timeline and view it. Frozen/repeated frames across sections = corrupt segment in the concat (find with per-segment ffprobe, delete, re-run). Verify duration matches the avatar render.


### v4.3 — music policy (FINAL, client-locked)
Claude cannot hear a mix — level math ≠ taste. After three balance iterations the standing rule is:
NEVER bake music into finals. Deliver VO-only masters (chain above, minus the music branch) plus
the selected/extended music WAVs as separate files in Video_Renders/Music/ for Graeham to mix in
CapCut. Teaser = silent video. The ducking/pre-normalization chain in v4.2 stays documented for
any future explicit "bake the music" request.

### v5 — long-form b-roll density (client-locked)
NO talking-head block over ~10s in long-form. Cutaway rule by CONTENT TYPE:
- LITERAL beats (describing rooms/features) → real home footage of that exact subject.
- CONCEPTUAL beats (market context, laws, money, commute) → NON-home visuals:
  (a) brand takeover stat cards (full-frame black, gradient-gold number, tag banner — carousel
      takeover style, img-zoompan segments) for any money/number beat;
  (b) stylized brand map card (gold pins/path) for commute/location;
  (c) AI concept b-roll (Seedance text-to-video, NO trademarks/logos — e.g. "backyard cottage
      under construction" for ADU, "bridge commute over bay toward office campuses" for
      employer-proximity talk).
Face stays on camera for trust beats: "that's not a typo", "verify with the city", the CTA ask.
When takeover cards replace a beat, DROP the matching lower-third overlay (no doubled text).
SYNC GUARD: re-encoded segments MUST use -frames:v round(dur*fps) — frame rounding across ~30
segments accumulates 0.3-0.6s of video/VO desync otherwise. Always ffprobe the concat duration
against the expected total before compositing.

### v6 — watchability rebuild (the big lessons, client-driven)
When feedback says "not watchable", STOP PATCHING and rebuild from the viewer's seat:
1. TIGHTER WINS: cut VO at silence boundaries to 2:30-3:00 (drop-off peaks before 2:00). Splice audio
   spans (atrim+concat), rebuild video timeline against new times (old2new mapping).
2. FRAME-LEVEL CLIP QC before use, not thumbnails: blacklist videographer shadows, blown highlights,
   lens flare. contact-sheet 3 frames/clip minimum and LOOK.
3. GRADE everything real: mild highlight pull + warmth (curves master 0.85->0.8 + colorbalance
   rs=.015:rm=.008 + sat 1.05). NOTE: colorbalance midtone is rm/gm/bm, not "ms".
4. PUNCH-INS: alternate full-frame and crop=iw/1.28 avatar segments per beat — fake multi-cam,
   kills static-angle deadness. Crop from 1080p is invisible at YT compression.
5. TEXT PLATES LEAD the VO by ~0.4s and land on cuts — never trail the word.
6. NUMBERED SECTION HEADERS (gold banner, top-left, 2.2s pop) = progress markers.
7. Micro-payoff every <=30s: plate, card, header, punch-in, or concept clip. Alternate fast
   (hook, montages) and slow (single-subject holds) pacing — don't over-edit every second.
8. Keep the face for trust beats + CTA; conceptual beats get cards/map/concept clips (v5 rule).

### v6.1 — full-script visual coverage audit (client-locked)
Before finishing any long-form cut, walk the ENTIRE transcript beat by beat and ask: "is there a
card/plate/graphic on screen while he says this?" Every concrete claim (specs, features, numbers,
comparisons, open loops) gets one. The spec breakdown ("single-level, detached, built 1947...")
gets a full stat card (headline + spec row). Feature lists get banners. Money claims get gradient
plates. Open loops get teaser lines. Trust beats and pure-story lines stay clean-face — that
contrast is deliberate, not a gap. Target: no uncovered stretch longer than ~8s anywhere.

### v7 — the 15-point client review, codified (FINAL for long-form)
HOOK: never open on a talking head. Text+audio+visual hook: real aerial footage with staggered
gold price-pill pops over rooftops ($1.4M-$2.4M) while VO says "can't buy under a million" —
then the $924K slam. Concept beats footage.
TEXT: shadows OFF panel-backed elements (panel is the separation). ALL CAPS everywhere except the
script-font signature (Great Vibes address = brand exception). Plates enter with the cut and exit
at sentence end — never trail, never vanish mid-claim.
CUTS: every segment boundary snaps to a sentence end (word timestamps). Never return to the
talking head mid-sentence. Never splice VO across two adjacent talking-head segments (face jump
cut) — cover every splice joint with b-roll or a card.
TRANSITIONS: timing-preserving crossfades (encode each segment with +0.4s tail; xfade offset =
original duration; chain in quarters, join resumably). Hard cuts only inside fast montages and
into takeover cards. NOTE: a stalled ffmpeg chain that stops growing = DISK FULL, not a hang.
PUNCH-INS: crop anchored at y=(ih-ih/1.28)*0.18 — center-crop decapitates.
MAP: real geography — OSM tiles (attribution line required), muted grade, gold route animated
point-to-point, pins pop as the route reaches them. 7s @ 25fps PNG seq as a SEGMENT.
LOGO: white variant derived from the black logo (recolor dark px, keep gold). Logo replaces
text-name headers on CTA/end cards.
AUDIO PATCHES: voice-clone TTS isn't direct (starfish engine unsupported) — render a short HeyGen
avatar video and harvest the audio. LEVEL-MATCH the patch to the surrounding VO (volumedetect
means; patches run ~6 dB hot) or loudnorm will clip its onset. Rephrase TTS-fragile words
("DM me" → "Send me"). Cover the patched span with a full-screen card (no lip mismatch).
QC GATE (scripts/qc_gate.py — run on EVERY final before delivery): duration check, silence-gap
scan, whisper transcript diff (base.en MINIMUM — tiny.en garbles and cries wolf), garble flags,
dense frame sheet reviewed by eye. Escalate model size before concluding audio is broken.

### v8 — audio-splice precision + card etiquette (client-locked)
SPANS FROM WORD *ENDS*: trim spans with end = word.end + 0.25 and start = word.start - 0.28
(the words JSON has 'e' values — USE THEM). Guessing ends from next-word starts clipped word
tails ("here." lost 0.55s) and 0.15s leads clipped onsets ("Verify"). Audit every span edge
against word ends BEFORE cutting.
SHADOWS: none on panel-backed or card elements, ever — panels self-separate. Shadows only on
naked banners/pills over busy footage.
ONE LABEL PER SCREEN: takeover cards must not carry their own tag banner when a corner section
header is on screen (duplicate "THE NUMBERS" bug).
FULL-SCREEN CARDS: encouraged mid-video for comparisons, graphs, bullet lists, stats, maps —
that's the takeover system. The one exception: don't reuse the END-CARD's CTA design mid-video —
a duplicate of the closer reads as "video over" and is redundant with the real CTA. Mid-video CTA
moments = speaker on camera + small DM banner. For patched audio sentences, use the PATCH
RENDER'S OWN AVATAR VIDEO as the segment — same look = matching lips, no cover card needed.
Use the patch's raw audio+video together (level-matched), not the silence-stripped wav (strips
onset consonants).
MONOTONE VO: flagged as AI-tell. Escalation path when client wants more life: re-render VO via
ElevenLabs v3 with audio tags (heygen-elevenlabs-renderer skill) — full re-time required, so
budget it as a version, not a patch.
QC GATE upgrade: transcribe splice-joint windows individually with base.en word timestamps —
full-video transcripts hide joint artifacts; window-edge garble is fuzz, so zoom before concluding.

### v9 — client-edited-audio recut workflow (the round-trip)
Graeham edits the delivered VO WAV externally; the video recuts around it:
1. Transcribe the edited audio (base.en, word timestamps; split >90s audio into halves per call).
2. Align edited words to the delivered-track words (difflib SequenceMatcher on normalized tokens);
   matched pairs become time anchors; t2e() = piecewise-linear track→edited mapping.
3. Read the diff FIRST: distinguish real edits (cuts, stray-word removals) from whisper
   tokenization noise ("810" vs "800-10" etc). Report the edit summary before building.
4. Retime every video segment via boundary-cumulative mapping (derive durations from mapped
   BOUNDARIES, not independent spans — independent rounding drifts ~1.5s across 40+ segments).
5. Talking-head segments compressed >0.18s internally = pause trims → split into runs at the
   trimmed gaps, jump-cut between runs (standard creator style, keeps lips synced per run).
   Segments that got LONGER get tpad freeze (<0.7s imperceptible).
6. Overlays: map both start AND end times (plates end with their compressed sentences).
7. Mux with the client's audio as master (loudnorm+limiter only).
8. QC gate + verify total: video boundaries must sum to mapped VO end exactly.

### v10 — audio-driven avatar re-render (the REAL fix for edited-audio lip sync)
v9's alignment-based retime produced visible lip drift (whisper timestamp error compounds).
The correct architecture when the client edits the VO:
1. Upload the edited audio as a HeyGen asset (heygen asset create --file vo.mp3).
2. Create a NEW avatar video DRIVEN BY THE AUDIO: heygen video create -d
   '{"type":"avatar","title":...,"avatar_id":<look>,"audio_asset_id":<id>,"aspect_ratio":"16:9","resolution":"1080p"}'
   — lips are generated to match the edited audio exactly. Render ≈ 5 min for 3 min audio.
3. Repoint ALL talking-head segments to the new render at their TIMELINE positions
   (source time == timeline time — no alignment needed, sync is by construction).
   Adjacent jump-cut runs from the continuous new source become seamless automatically.
4. B-roll/cards/plates keep the alignment-retimed positions (correct on the edited timeline).
Use v9's alignment mapping ONLY to place visuals; NEVER to retime avatar footage.
RENAME BUG CLASS: when cloning finish scripts via sed s/y9_/y10_/, patterns like 'y9F' without
the underscore survive and silently reuse stale intermediates — grep the clone for old-version
tokens before running. Symptom: final ≠ its own verified halves.
