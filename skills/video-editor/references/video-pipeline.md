# Video pipeline — Reels (9:16) + Walkthrough (16:9)

Engines: `scripts/video_lib.sh` (segment + xfade helpers) and `scripts/chunk.py`.
Read `sandbox-constraints.md` first — the batching/timeout rules are what make this work.

## Review the footage
```bash
# one labeled thumbnail per clip, ~45% in, then montage into contact sheets
for f in *.MP4; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  seek=$(echo "$dur*0.45"|bc)
  ffmpeg -ss "$seek" -i "$f" -frames:v 1 -vf "scale=480:270,drawtext=...:text='$f'" thumbs/NN.jpg
done
montage thumbs/*.jpg -tile 4x4 -geometry 480x270+4+4 sheet.jpg   # then copy to a connected folder + Read
```
Confirm each clip's real content, note durations, and **clamp every in/out to clip length**.
Flag any **realtor yard sign** in exterior shots (blocker if "no agent info").

## 1 · Confirm choices (AskUserQuestion)
Music handling (default clean/silent), end-card/branding (default none beyond address), and
how different the two reels should be (recommend genuinely distinct).

## 2 · Render segments (the only 4K decode)
```bash
export VE_SRC="/path/to/clips" VE_OUT="/path/to/work"
source scripts/video_lib.sh
# 16:9 walkthrough segment:  seg16  SRC SS DUR OUT [GRADE] [POSTfilter]
seg16 "C3478.MP4" 0.0 3.9 "wt/wt10.mp4" "$GRADE_STD" "$(label16 'SOARING VAULTED CEILINGS' 0.3 3.5)"
# 9:16 reel, center-crop:    seg916c SRC SS DUR OUT [GRADE] [POST] [XOFF]
seg916c "C3491.MP4" 1.0 2.3 "r1/r1_09.mp4" "$GRADE_STD" "$(capR 'PRIMARY SUITE' 0.3 2.0)"
# 9:16 reel, blurred-pad (use for wides: vaulted, aerials, exterior, sign):
seg916p "C3478.MP4" 0.2 2.6 "r1/r1_03.mp4" "$GRADE_STD" "$(capR 'VAULTED CEILINGS' 0.3 2.3)"
```
Batch <= 4 per call. Use `GRADE_HERO` for the warmer agent clips.

## 3 · Assemble with transitions, in chunks
`chunk.py` joins 2-4 segments with xfades at exact offsets, and can bake a dip (fade) at the
chunk's head/tail for inter-chunk transitions:
```bash
python chunk.py chunks/c01.mp4 0 0.3 wt01.mp4 dissolve 0.7 wt02.mp4 fade 0.6 wt03.mp4
#                ^out         ^fadein ^fadeout  ^seg  ^transition dur ^seg ...
```
Vary transitions with intent, not gimmickry: hard cuts within a section; **slideup** for
going up the stairs; **fadewhite** into a bright bath; **circleopen** into the patio;
**dissolve/smoothleft** for aerials; **dip-to-black** beats around the open and the agent
outro. Then concat-copy the chunks and add silent audio (see sandbox-constraints.md).

## Deliverable specs
- **Walkthrough** 1920x1080, 30 fps, ~2:00-2:45. Buyer's journey: aerial -> approach ->
  sign/title -> curb -> step inside -> living (vaulted) -> kitchen -> stairs/loft ->
  bedrooms -> baths -> patio -> neighborhood -> agent orbit (no contact card if "no agent").
  One feature label per room; resist over-titling. ~30-41 shots.
- **Reels** 1080x1920, 30 fps, ~30-45 s, two **distinct** concepts:
  - Reel 1 = story / face-led: open on the walk-up hook, warmer pace, smooth dissolves.
  - Reel 2 = house-led punch: open on the "wow" (vaulted), snappier ~1.7 s cuts, slides/
    fadewhite, end on a different agent/orbit clip.
  Captions are feature words only (2-4 words), upper-third safe area, no fabricated stats.

## QC then deliver
Probe res/fps/dur/audio; extract ~8 frames across each output, montage, view. Copy finals
into the user's listing folder; `present_files`; offer a text-free cut, a 0:60/0:45
walkthrough, other sizes, or a music pass.
