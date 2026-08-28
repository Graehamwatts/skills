#!/usr/bin/env python3
"""
Split-screen reel compositor — b-roll top half, HeyGen avatar bottom half.

Takes an already-rendered HeyGen avatar clip (with audio) and one or more already-rendered
Higgsfield b-roll clips, and assembles the "bayareawilson-style" split-screen frame:

    ┌─────────────────────┐
    │                      │
    │   B-ROLL (top half)  │  <- cropped/looped to fill the avatar's runtime
    │                      │
    ├──── HEADLINE ────────┤  <- two bold caps lines straddling the seam
    │                      │
    │  AVATAR (bottom half)│  <- avatar's own audio track carries the whole video
    │                      │
    └─────────────────────┘

Both inputs are normalized to a canonical 1080x1920 "cover crop" first (so any source aspect
ratio works), then each contributes its top or bottom 960px band. This means neither the
HeyGen render nor the Higgsfield render needs any special aspect handling upstream — request
them at their normal 9:16 defaults and this script does the rest.

Usage:
    python3 composite_split_screen.py \\
        --avatar /path/to/heygen_render.mp4 \\
        --broll /path/to/broll_clip1.mp4 [/path/to/broll_clip2.mp4 ...] \\
        --headline-line1 "SAFEWAY MARINA ADDS" \\
        --headline-line2 "800 HOMES" \\
        --out /path/to/output_master.mp4

Optional flags: --accent-color, --line2-color, --avatar-anchor-y, --top-anchor-y,
--width, --height, --fps, --posting-copy (writes a second, smaller delivery file).

Requires: ffmpeg, ffprobe, python3-pil (Pillow) on PATH / importable.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

FD = "/usr/share/fonts/truetype/liberation"
BOLD = f"{FD}/LiberationSans-Bold.ttf"


def run(cmd, **kwargs):
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True, **kwargs)


def ffprobe_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", path,
    ])
    return float(json.loads(out)["format"]["duration"])


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def draw_outlined_centered(d, cx, y, text, font, fill, W, ow=7):
    tw = d.textlength(text, font=font)
    x = cx - tw / 2
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            d.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    d.text((x, y), text, font=font, fill=fill)
    return tw


def build_headline_png(width, height, line1, line2, accent_hex, line2_hex, seam_y, out_path,
                        font_size=118, line_gap=136):
    """Transparent overlay with two centered bold-caps lines straddling `seam_y`."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(BOLD, font_size)
    accent = hex_to_rgb(accent_hex)
    white = hex_to_rgb(line2_hex)
    # Block is vertically centered on the seam: line1 sits just above it, line2 just below.
    y1 = seam_y - line_gap
    y2 = seam_y + int(line_gap * 0.12)
    draw_outlined_centered(d, width / 2, y1, line1.upper(), font, accent, width)
    draw_outlined_centered(d, width / 2, y2, line2.upper(), font, white, width)
    img.save(out_path)
    return out_path


def cover_crop_filter(width, height):
    """ffmpeg filter: scale-to-cover then center-crop to exactly width x height."""
    return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"


def normalize_clip(src, width, height, fps, out_path, extra_vf=None):
    vf = cover_crop_filter(width, height) + f",fps={fps}"
    if extra_vf:
        vf += "," + extra_vf
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-an", "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out_path])


def loop_or_trim_to_duration(src, target_dur, out_path, fps):
    src_dur = ffprobe_duration(src)
    if src_dur >= target_dur:
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-t", f"{target_dur:.3f}",
             "-c", "copy", out_path])
    else:
        # loop the clip, then hard-trim to the exact target duration
        run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", src,
             "-t", f"{target_dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "16", "-r", str(fps), out_path])


def concat_clips(paths, out_path):
    if len(paths) == 1:
        run(["ffmpeg", "-y", "-v", "error", "-i", paths[0], "-c", "copy", out_path])
        return
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
        listfile = f.name
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c", "copy", out_path])
    os.unlink(listfile)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--avatar", required=True, help="HeyGen avatar render (has the VO audio)")
    ap.add_argument("--broll", nargs="+", required=True, help="One or more Higgsfield b-roll clips (top half)")
    ap.add_argument("--headline-line1", required=True)
    ap.add_argument("--headline-line2", required=True)
    ap.add_argument("--accent-color", default="#C4A265", help="Line 1 color (default Watts Gold; use #F5C518 to match the reference reels' brighter yellow)")
    ap.add_argument("--line2-color", default="#FFFFFF")
    ap.add_argument("--top-anchor-y", type=int, default=0,
                     help="Y offset (in the normalized 1080x1920 b-roll) where the top-half crop starts. 0 = top of frame.")
    ap.add_argument("--avatar-anchor-y", type=int, default=520,
                     help="Y offset (in the normalized 1080x1920 avatar) where the bottom-half crop starts. "
                          "Default 520 keeps head+shoulders with headroom in the lower 960px band — "
                          "tune per-avatar-look by eyeballing a normalized frame first.")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--out", required=True, help="Master output path (CRF 18)")
    ap.add_argument("--posting-copy", help="Optional second output path, compressed to fit a ~30MiB chat-share limit")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    W, H, FPS = args.width, args.height, args.fps
    HALF = H // 2

    workdir = args.workdir or tempfile.mkdtemp(prefix="splitscreen_")
    os.makedirs(workdir, exist_ok=True)

    avatar_dur = ffprobe_duration(args.avatar)
    print(f"Avatar clip duration: {avatar_dur:.2f}s — this sets the runtime for the whole reel.", file=sys.stderr)

    # 1. Normalize avatar to canonical 1080x1920, keep its audio for the final mux.
    avatar_norm = os.path.join(workdir, "avatar_norm.mp4")
    normalize_clip(args.avatar, W, H, FPS, avatar_norm)

    # 2. Normalize + concat + loop b-roll to cover the full avatar duration.
    broll_norm_parts = []
    for i, clip in enumerate(args.broll):
        p = os.path.join(workdir, f"broll_norm_{i}.mp4")
        normalize_clip(clip, W, H, FPS, p)
        broll_norm_parts.append(p)
    broll_concat = os.path.join(workdir, "broll_concat.mp4")
    concat_clips(broll_norm_parts, broll_concat)
    broll_full = os.path.join(workdir, "broll_full.mp4")
    loop_or_trim_to_duration(broll_concat, avatar_dur, broll_full, FPS)

    # 3. Crop each to its half of the frame.
    top_crop = os.path.join(workdir, "top_crop.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", broll_full,
         "-vf", f"crop={W}:{HALF}:0:{args.top_anchor_y}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-an", top_crop])

    bottom_crop = os.path.join(workdir, "bottom_crop.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", avatar_norm,
         "-vf", f"crop={W}:{HALF}:0:{args.avatar_anchor_y}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-an", bottom_crop])

    # 4. Headline overlay PNG, centered on the seam (y = HALF).
    headline_png = os.path.join(workdir, "headline.png")
    build_headline_png(W, H, args.headline_line1, args.headline_line2,
                        args.accent_color, args.line2_color, HALF, headline_png)

    # 5. vstack top + bottom, overlay headline, mux avatar's original audio.
    stacked = os.path.join(workdir, "stacked.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", top_crop, "-i", bottom_crop,
         "-filter_complex", "[0:v][1:v]vstack=inputs=2[v]",
         "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", stacked])

    run(["ffmpeg", "-y", "-v", "error",
         "-i", stacked, "-i", headline_png, "-i", args.avatar,
         "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
         "-map", "[v]", "-map", "2:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         "-shortest", args.out])
    print(f"Master written: {args.out}", file=sys.stderr)

    if args.posting_copy:
        run(["ffmpeg", "-y", "-v", "error", "-i", args.out,
             "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
             args.posting_copy])
        size_mb = os.path.getsize(args.posting_copy) / (1024 * 1024)
        print(f"Posting copy written: {args.posting_copy} ({size_mb:.1f} MiB)", file=sys.stderr)
        if size_mb > 30:
            print("WARNING: posting copy still over 30 MiB — bump CRF or shorten the reel.", file=sys.stderr)


if __name__ == "__main__":
    main()
