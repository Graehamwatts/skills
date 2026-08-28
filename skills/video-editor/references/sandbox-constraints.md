# Sandbox constraints & the failure modes already hit

The render pipeline looks indirect on purpose. Every choice below was forced by a real
failure during the build. Respect them and the work goes smoothly; ignore them and you get
timeouts and corrupt files.

## The environment
- ~2 CPU cores, ~4 GB RAM.
- A **hard ~45 s limit per shell command** (the wrapper kills the call).
- Source is **16+ GB of 4K (3840x2160) MP4**, mixed frame rates (24 / 30 / 60 fps), some
  clips have no audio (drone), some carry a warmer cinematic grade (agent "hero" shots).
- File tools (Read/Write) and the shell see **different paths** for the same files; to LOOK
  at an image you generate, copy it into one of the user's connected folders and Read it
  from the Windows-style path. The scratch/outputs dir is not Readable directly.

## Why the proxy pipeline
A single straight encode of a 2:40 1080p timeline on 2 cores is ~80 s — over the limit. So:
1. **Decode each 4K clip exactly once** into a short, graded 1080p **segment** (trim with
   `-ss <in> -t <dur>` BEFORE `-i` for fast keyframe seek, so you only decode the window you
   need). 60 fps 4K is the expensive case — keep those segments short.
2. Assemble from the 1080p segments (cheap to decode), never from 4K again.

## Batch sizes & timing
- Render **<= 4 segments per shell call.** Echo `elapsed=$(( $(date +%s)-S ))s` and keep it
  under ~35 s. A batch of 4 plain segments ran ~25 s; 5 with a text overlay ran ~34 s.
- If a call times out, files that were mid-write are **truncated** (no moov atom). Re-render
  just those and **validate every chunk** with `ffprobe` before concatenating.

## Assembly without re-encoding the whole thing
- Build the timeline as short **chunks** (2-4 segments joined by `xfade`), each well under
  45 s, using `scripts/chunk.py`.
- Then join chunks with the concat demuxer **stream-copied** (instant, no quality loss):
  `ffmpeg -f concat -safe 0 -i list.txt -c copy -fflags +genpts out.mp4`.
- All segments/chunks must share identical params (1080p OR vertical, 30 fps, yuv420p,
  SAR 1, `-video_track_timescale 30000`) or concat-copy and xfade break.

## Audio: the `-shortest` trap
The user wants a clean (silent) export they can score. Add a silent stereo track so players
don't choke, but **bound it with `-t`** equal to the video duration:
```
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 video.mp4)
ffmpeg -i video.mp4 -f lavfi -t "$D" -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -map 0:v -map 1:a -c:v copy -c:a aac final.mp4
```
`-shortest` does NOT terminate a `-c:v copy` stream against an infinite `anullsrc`; it ran to
the 45 s kill and left a half-written file. Do not use it here. Do not add `+faststart` in
the same call on a 200 MB+ file — its second pass also blows the budget.

## Verify by eye, always
After any render: extract frames at spread timecodes, `montage` them, copy into a connected
folder, and Read it. Check transitions landed, text is legible, grade is consistent, and
(critical) **no agent signage** snuck in. A 0 exit code is not verification.
