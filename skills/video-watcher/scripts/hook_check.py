#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hook_check.py - hook and Instagram safe-zone check for a vertical Short / Reel.

Built from the 42-to-Zero review (Sept 2026). Measures what decides whether a
YouTube Short or Instagram Reel survives its first 3 seconds, and whether its
text survives Instagram's on-screen UI:

  * runtime, spoken word count, words per minute
  * when a place (city / neighborhood) is first SPOKEN, from a word-level transcript
  * cuts: first shot length, cuts in the first 5 seconds, longest hold
  * where caption-style text sits on the frame, flagged against Instagram's
    covered zones (Meta's Reels guidance: keep the top 14% and bottom 35% clear)
  * frame 0, a hook contact sheet (0-6 s every 0.5 s), body sheets (every 3 s)
  * safe-zone overlays for frame 0, 0:01.5 and the last frame

Writes into --out: hook_report.md, transcript.md, words.json, frames/, sheets/,
overlays/. The report is the scorecard. The images are for the visual checks
(does frame 0 name the place, are the title cards inside the safe zone, is the
B-roll real). words.json holds word timings for building a re-cut edit list.

Usage:
  python hook_check.py VIDEO [--out DIR] [--place "East Palo Alto"] [--model base]

  VIDEO: a local file, a direct video URL, a Box share link
         (https://app.box.com/s/...), or anything yt-dlp can download.

Needs ffmpeg + ffprobe on PATH, Pillow, and openai-whisper or faster-whisper
(use --no-transcript to skip the spoken-word checks).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

TOP_ZONE = 0.14      # Instagram's Reels header covers the top 14%
BOTTOM_ZONE = 0.65   # username, caption, audio and buttons cover the bottom 35%

PLACES = [
    "East Palo Alto", "East Menlo Park", "Palo Alto", "Menlo Park", "Redwood City",
    "Atherton", "Woodside", "Portola Valley", "San Carlos", "Belmont", "San Mateo",
    "Foster City", "Burlingame", "Millbrae", "San Bruno", "South San Francisco",
    "Daly City", "Half Moon Bay", "Mountain View", "Los Altos", "Sunnyvale",
    "Santa Clara", "Cupertino", "San Jose", "Fremont", "Oakland", "Berkeley",
    "San Francisco", "Silicon Valley", "Peninsula", "Bay Area", "EPA",
]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def norm(word):
    return re.sub(r"[^a-z0-9]", "", word.lower())


def font(size):
    for f in ("C:/Windows/Fonts/arialbd.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/Library/Fonts/Arial Bold.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def resolve_input(src, out):
    """Return a local video path, downloading links into the output folder."""
    if Path(src).exists():
        return Path(src)
    if not re.match(r"https?://", src):
        sys.exit(f"Not a file or a link: {src}")
    dest = out / "source.mp4"
    box = re.match(r"https?://(?:app\.)?box\.com/s/([A-Za-z0-9]+)", src)
    if box:
        src = f"https://app.box.com/shared/static/{box.group(1)}.mp4"
    if "box.com/shared/static/" in src or re.search(r"\.(mp4|mov|m4v|webm)(\?|$)", src, re.I):
        print("Downloading", src)
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        return dest
    if shutil.which("yt-dlp"):
        print("Downloading with yt-dlp", src)
        r = run(["yt-dlp", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
                 "-o", str(dest), src])
        if dest.exists():
            return dest
        sys.exit("yt-dlp could not download it:\n" + r.stderr[-800:])
    sys.exit("Can't download that link. Install yt-dlp, or download the video and pass the file.")


def probe(video):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(video)])
    try:
        j = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        j = {}
    st = (j.get("streams") or [{}])[0]
    num, _, den = (st.get("r_frame_rate") or "0/1").partition("/")
    try:
        fps = float(num) / float(den)
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    return {"w": int(st.get("width") or 0), "h": int(st.get("height") or 0), "fps": fps,
            "dur": float((j.get("format") or {}).get("duration") or 0)}


def transcribe(video, out, model_name):
    """Word-level transcript. Returns (words, segments, engine or None)."""
    wav = out / "audio16k.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1",
         "-ar", "16000", str(wav)])
    if not wav.exists():
        return [], [], None
    words, segs, engine = [], [], None
    try:
        import whisper
        engine = f"openai-whisper ({model_name})"
        res = whisper.load_model(model_name).transcribe(
            str(wav), word_timestamps=True, fp16=False, language="en")
        for s in res["segments"]:
            segs.append((s["start"], s["end"], s["text"].strip()))
            for w in s.get("words", []):
                words.append((w["start"], w["end"], w["word"].strip()))
    except (ImportError, AttributeError):
        try:
            from faster_whisper import WhisperModel
            engine = f"faster-whisper ({model_name})"
            segments, _ = WhisperModel(model_name, device="cpu", compute_type="int8").transcribe(
                str(wav), word_timestamps=True, language="en")
            for s in segments:
                segs.append((s.start, s.end, s.text.strip()))
                for w in (s.words or []):
                    words.append((w.start, w.end, w.word.strip()))
        except ImportError:
            engine = None
    try:
        wav.unlink()
    except OSError:
        pass
    return words, segs, engine


def first_places(words, places):
    """First time each place is spoken. Longer names win ('East Palo Alto' over 'Palo Alto')."""
    uniq = {}
    for p in places:
        key = tuple(norm(x) for x in p.split())
        if key and key not in uniq:
            uniq[key] = p
    toks = [(a, norm(w)) for a, _, w in words]
    toks = [x for x in toks if x[1]]
    keys = sorted(uniq, key=len, reverse=True)
    first, i = {}, 0
    while i < len(toks):
        hit = next((k for k in keys if tuple(t for _, t in toks[i:i + len(k)]) == k), None)
        if hit:
            first.setdefault(uniq[hit], toks[i][0])
            i += len(hit)
        else:
            i += 1
    return first


def find_cuts(video, thr):
    r = run(["ffmpeg", "-hide_banner", "-i", str(video), "-an", "-vf",
             f"scale=270:-2,select='gt(scene,{thr})',showinfo", "-f", "null", "-"])
    cuts = []
    for c in (float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)):
        if not cuts or c - cuts[-1] > 0.4:
            cuts.append(c)
    return cuts


def grab(video, t, folder):
    path = folder / f"f_{t:06.1f}.jpg"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video),
         "-frames:v", "1", "-q:v", "3", str(path)])
    return path if path.exists() else None


def sheet(frames, path, cols=4, tw=270):
    ims = [(t, Image.open(p).convert("RGB")) for t, p in frames]
    w0, h0 = ims[0][1].size
    th, lb = round(tw * h0 / w0), 34
    rows = (len(ims) + cols - 1) // cols
    img = Image.new("RGB", (cols * tw, rows * (th + lb)), (18, 18, 18))
    d, f = ImageDraw.Draw(img), font(22)
    for i, (t, im) in enumerate(ims):
        x, y = (i % cols) * tw, (i // cols) * (th + lb)
        d.text((x + 8, y + 5), ts(t), fill=(255, 215, 0), font=f)
        img.paste(im.resize((tw, th)), (x, y + lb))
    img.save(path, quality=82)


def text_bands(path):
    """Rows crossed by outlined, caption-style text (white fill against a dark
    outline or dark box). Returns [(top_px, bottom_px), ...] in full-frame pixels."""
    im = Image.open(path).convert("RGB")
    W, H = im.size
    sm = im.resize((max(1, W // 2), max(1, H // 2)))
    w, h = sm.size
    px = sm.load()
    hits = []
    for y in range(h):
        edges, last, lx = 0, None, -9
        for x in range(w):
            r, g, b = px[x, y]
            if r > 230 and g > 230 and b > 230:
                c = "W"
            elif r < 60 and g < 60 and b < 60:
                c = "D"
            else:
                continue
            if last and last != c and x - lx <= 3:
                edges += 1
            last, lx = c, x
        hits.append(edges >= 10)
    bands, start, gap = [], None, 0
    for y, hit in enumerate(hits + [False] * 6):
        if hit:
            if start is None:
                start = y
            gap = 0
        elif start is not None:
            gap += 1
            if gap > 4:
                end = y - gap
                if 8 <= end - start <= 120:
                    bands.append((start * 2, end * 2))
                start, gap = None, 0
    return bands


def caption_position(band_map, H):
    """The most common text band across frames is where the captions live."""
    buckets, spans = Counter(), {}
    for bands in band_map.values():
        for a, b in bands:
            key = round((a + b) / 2 / H * 50)   # 2% buckets
            buckets[key] += 1
            spans.setdefault(key, []).append((a, b))
    if not buckets:
        return None
    key, count = buckets.most_common(1)[0]
    tops = sorted(a for a, _ in spans[key])
    bots = sorted(b for _, b in spans[key])
    return tops[len(tops) // 2], bots[len(bots) // 2], count


def overlay(src, dst):
    im = Image.open(src).convert("RGBA")
    W, H = im.size
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    top, bot = int(H * TOP_ZONE), int(H * BOTTOM_ZONE)
    d.rectangle([0, 0, W, top], fill=(215, 35, 35, 105))
    d.rectangle([0, bot, W, H], fill=(215, 35, 35, 105))
    d.rectangle([3, top, W - 3, bot], outline=(60, 220, 110, 255), width=max(3, W // 180))
    if H > W:   # the square the Instagram grid keeps on a vertical video
        sq = (H - W) // 2
        d.rectangle([8, sq, W - 8, sq + W], outline=(80, 170, 255, 255), width=max(2, W // 270))
    f = font(max(18, W // 26))
    d.text((20, max(4, top - W // 16)), "Instagram UI", fill="white", font=f)
    d.text((20, bot + 12), "Instagram UI", fill="white", font=f)
    out = Image.alpha_composite(im, ov).convert("RGB")
    out.resize((540, round(540 * H / W))).save(dst, quality=82)


def main():
    ap = argparse.ArgumentParser(description="Hook and Instagram safe-zone check for a vertical Short / Reel.")
    ap.add_argument("video", help="local file, direct video URL, Box share link, or any yt-dlp link")
    ap.add_argument("--out", type=Path, help="output folder (default: hook-check-<name>)")
    ap.add_argument("--place", action="append", default=[],
                    help='place the video is about, e.g. --place "East Palo Alto" (repeatable)')
    ap.add_argument("--model", default="base", help="whisper model size (default: base)")
    ap.add_argument("--no-transcript", action="store_true", help="skip the spoken-word checks")
    ap.add_argument("--threshold", type=float, default=0.18, help="scene-cut sensitivity (default: 0.18)")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found. Install ffmpeg (it includes ffprobe) and try again.")

    name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(args.video).stem)[:40].strip("-") or "video"
    out = args.out or Path(f"hook-check-{name}")
    for sub in ("frames", "sheets", "overlays"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    video = resolve_input(args.video, out)
    info = probe(video)
    if info["dur"] <= 0 or not info["w"]:
        sys.exit("That file isn't a readable video. If it came from Box, set the link to 'People with the link'.")
    W, H, dur = info["w"], info["h"], info["dur"]
    print(f"Video: {W}x{H}, {info['fps']:.0f} fps, {ts(dur)}")

    print("Finding cuts...")
    cuts = find_cuts(video, args.threshold)
    bounds = [0.0] + cuts + [dur]
    shots = [(bounds[i], bounds[i + 1] - bounds[i]) for i in range(len(bounds) - 1)]
    first_shot = shots[0][1]
    early = sum(1 for c in cuts if c < 5.0)
    long_start, long_len = max(shots, key=lambda s: s[1])

    print("Grabbing frames...")
    fd = out / "frames"
    hook = [(round(x * 0.5, 1), grab(video, x * 0.5, fd)) for x in range(13) if x * 0.5 < dur - 0.05]
    body = [(float(t), grab(video, float(t), fd)) for t in range(8, int(dur), 3)]
    hook = [(t, p) for t, p in hook if p]
    body = [(t, p) for t, p in body if p]
    if hook:
        sheet(hook, out / "sheets" / "hook_0-6s.jpg")
    for i in range(0, len(body), 8):
        sheet(body[i:i + 8], out / "sheets" / f"body_{i // 8 + 1}.jpg")
    last_t = max(0.0, dur - 0.5)
    for t, n in ((0.0, "overlay_frame0.jpg"), (min(1.5, last_t), "overlay_0m01.5s.jpg"),
                 (last_t, "overlay_last.jpg")):
        p = grab(video, t, fd)
        if p:
            overlay(p, out / "overlays" / n)

    print("Measuring on-screen text...")
    band_map = {t: text_bands(p) for t, p in hook + body}
    cap = caption_position(band_map, H)
    frame0_bands = band_map.get(0.0, [])

    words, segs, engine = [], [], None
    if not args.no_transcript:
        print("Transcribing (the first run downloads the whisper model)...")
        words, segs, engine = transcribe(video, out, args.model)
    with open(out / "words.json", "w", encoding="utf-8") as f:
        json.dump(words, f)

    spoken = [w for w in words if re.search(r"[A-Za-z0-9]", w[2])]
    n_words = len(spoken)
    speech = (spoken[-1][1] - spoken[0][0]) if spoken else 0
    wpm = round(n_words / speech * 60) if speech > 0 else 0
    places = first_places(words, args.place + PLACES)
    wanted = {tuple(norm(x) for x in p.split()) for p in args.place}
    pool = [(p, t) for p, t in places.items()
            if not wanted or tuple(norm(x) for x in p.split()) in wanted]
    prim = min(pool, key=lambda x: x[1]) if pool else None

    rows = []

    def add(check, result, target, status):
        rows.append((check, result, target, status))

    add("Runtime", ts(dur), "30–60 s",
        "PASS" if 15 <= dur <= 60 else ("CHECK" if dur < 15 else "FLAG"))
    if engine:
        add("Spoken words", f"{n_words} ({wpm} wpm)", "90–160 words",
            "PASS" if 90 <= n_words <= 160 else "FLAG")
        if prim:
            p, t = prim
            add("Place first spoken", f'"{p}" at {ts(t)}', "within the first 3 s",
                "PASS" if t <= 3 else ("CHECK" if t <= 5 else "FLAG"))
        else:
            want = ", ".join(args.place) if args.place else "any city or neighborhood"
            add("Place first spoken", f"never ({want})", "within the first 3 s", "FLAG")
    else:
        add("Spoken-word checks", "skipped (no whisper, or --no-transcript)", "", "CHECK")
    add("First shot", f"{first_shot:.1f} s", "2 s or less",
        "PASS" if first_shot <= 2 else ("CHECK" if first_shot <= 3 else "FLAG"))
    add("Cuts in first 5 s", str(early), "3 or more",
        "PASS" if early >= 3 else ("CHECK" if early == 2 else "FLAG"))
    add("Longest hold", f"{long_len:.1f} s at {ts(long_start)}", "3–6 s holds after the hook",
        "PASS" if long_len <= 8 else "CHECK")
    if cap:
        a, b, k = cap
        inside = a >= H * TOP_ZONE and b <= H * BOTTOM_ZONE
        add("Caption position", f"y {a}–{b} ({a / H:.0%}–{b / H:.0%}), {k} of {len(band_map)} frames",
            f"between y {int(H * TOP_ZONE)} and y {int(H * BOTTOM_ZONE)}", "PASS" if inside else "FLAG")
    else:
        add("Caption position", "no caption-style text found", "", "CHECK")
    if frame0_bands:
        add("Text on frame 0", ", ".join(f"y {a}–{b}" for a, b in frame0_bands),
            "hook text that names the place", "CHECK")
    else:
        add("Text on frame 0", "none detected", "hook text on the very first frame", "FLAG")

    title = Path(args.video).name if Path(args.video).exists() else args.video
    L = [f"# Hook check: {title}", "",
         f"Checked {date.today():%b %d, %Y}. {W}×{H}, {info['fps']:.0f} fps, runtime {ts(dur)}."
         + (f" Transcript: {engine}." if engine else ""), "",
         "## Scorecard", "", "| Check | Result | Target | Status |", "|---|---|---|---|"]
    L += [f"| {c} | {r} | {tg} | **{s}** |" for c, r, tg, s in rows]
    L += ["", "PASS meets the target. FLAG means fix it before posting. CHECK means look at the images and decide."]
    if words:
        L += ["", "## Opening words (first 12 s)", "",
              " ".join(f"{w} `{ts(a)}`" for a, _, w in words if a < 12)]
    if places:
        L += ["", "## Places spoken, first time", ""]
        L += [f"- {p}: {ts(t)}" for p, t in sorted(places.items(), key=lambda x: x[1])]
    L += ["", "## Cuts", "",
          f"{len(cuts)} cuts, {len(shots)} shots, average shot {dur / len(shots):.1f} s. "
          "Fast camera moves can register as cuts and slow dissolves can be missed, so confirm on the sheets.",
          "", ", ".join(ts(c) for c in cuts) or "No cuts detected."]
    L += ["", "## On-screen text bands by frame", "",
          f"Instagram covers everything above y {int(H * TOP_ZONE)} and below y {int(H * BOTTOM_ZONE)}. "
          "Only outlined, caption-style text is measured. Check colored title cards by eye on the overlays.", "",
          "| Time | Text bands (y px), ⚠ = inside Instagram's UI |", "|---|---|"]
    for t in sorted(band_map):
        cells = ", ".join(f"{a}–{b}" + (" ⚠" if a < H * TOP_ZONE or b > H * BOTTOM_ZONE else "")
                          for a, b in band_map[t])
        L.append(f"| {ts(t)} | {cells or '-'} |")
    L += ["", "## Look at these images", "",
          "- `overlays/overlay_frame0.jpg`: is the hook text on frame 0, and does it name the place? No fade-in.",
          "- `sheets/hook_0-6s.jpg`: a new shot every 1–2 s? Is the opening real footage of the place?",
          "- `sheets/body_*.jpg`: when does the place first appear in on-screen text? Is every title card inside "
          "the green box? Any caption typos, or on-screen numbers that don't match the voiceover?",
          "- `overlays/overlay_last.jpg`: one CTA. YouTube gets the end card and a Related video link. "
          "Instagram gets a comment-keyword card, never 'full video on the channel'.",
          "- The blue square is what the Instagram grid keeps. Cover text goes inside it.",
          "- One short, one story. If a second story starts, that's a second short."]
    L += ["", "## Building the re-cut", "",
          "Use `words.json` (start, end, word) for source in and out points, and cut on the waveform, "
          "since word timings can be off by about 0.1 s. Before asking for a reshoot, look for a line "
          "already in the audio that names the place and states the payoff, and move it to 0:00. "
          "End on that same line so the short loops."]
    if segs:
        with open(out / "transcript.md", "w", encoding="utf-8") as f:
            f.write("\n".join(f"[{ts(a)}–{ts(b)}] {t}" for a, b, t in segs) + "\n")
        L += ["", "## Transcript", ""] + [f"- `{ts(a)}` {t}" for a, _, t in segs]

    report = out / "hook_report.md"
    report.write_text("\n".join(L) + "\n", encoding="utf-8")
    print()
    for c, r, _, s in rows:
        print(f"  {s:5s}  {c}: {r}".replace("–", "-"))
    print(f"\nReport: {report.resolve()}")


if __name__ == "__main__":
    main()
