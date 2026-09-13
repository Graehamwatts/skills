#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compositor_template.py  (CapCut-first version, 2026-09-13)

What it does. Takes the finished CapCut export (9:16, no text on it) and burns on the four
things CapCut must NOT do: the karaoke captions, the frame-1 hook card, and either the
Instagram DM card (MODE "ig") or the YouTube brand end card (MODE "yt").

How to run it (Peter):
    1. Fill the numbered SETTINGS block below. That is the only part you edit.
    2. python compositor_template.py          renders the MODE written in the settings
    3. python compositor_template.py yt       same settings, the other master (or "ig")
The script checks the export first (size, frame rate, sound) and stops with a plain
sentence if something is off. Everything under "END OF SETTINGS" is the locked brand
build: caption size and position, card positions, fonts, colors. Do not edit it.

Word timing. Captions follow the words whisper hears in the export's own sound, the same
method as video-watcher/scripts/hook_check.py. The timing is saved next to the export as
"<name>.words.json" and rebuilt whenever the export is newer, so a re-cut never plays
old captions.

History. Forked from composite_rwc.py v22 via the ROAD Act job. The avatar-era pipeline
(HeyGen 4K render + alpha, punch-in crops, evidence inserts, b-roll folders, stickers,
warm grade, whip-blur) is archived next to this file as
compositor_avatar_era_2026-09-13.py; CapCut owns all of that now.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is missing. Run:  pip install pillow")

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

# =============================================================================
#  SETTINGS  (the only part you edit; one video = one fill of this block)
# =============================================================================

# 1. THE VIDEO. Full path to the CapCut export: 9:16, 1080 x 1920, 30 fps, no text on it,
#    voice + b-roll + SFX + music already mixed in. Keep the r before the quotes so Windows
#    backslashes work. A 4K avatar render (2160 x 3840) is also accepted; it is scaled down
#    to 1080 x 1920 on the way in.
INPUT_VIDEO = r"C:\Users\Peter\Videos\42 to Zero.mp4"

# 2. ITS PIXEL SIZE. Width, height of that file: 1080, 1920 for a CapCut export, 2160, 3840
#    for a 4K avatar render. The script reads the real size from the file and stops if these
#    two numbers disagree with it (a wrong CapCut export preset is the usual cause).
INPUT_WIDTH, INPUT_HEIGHT = 1080, 1920

# 3. FRAME RATE. Must equal the export's frame rate (CapCut default: 30). Every ffmpeg decoder
#    in this script uses this one number, so no frame is dropped or doubled (25 on a 30 fps
#    file drops every sixth frame). The script stops if the file's rate is different.
FPS = 30

# 4. AUDIO. "video" = use the sound already inside the export (normal for CapCut).
#    Or the full path to a separate .wav mix, e.g. r"C:\Videos\42 to Zero mix.wav".
AUDIO = "video"

# 5. WORD TIMING (drives the captions). "whisper" = listen to the audio from setting 4 and
#    time every word; saved next to the video as "<name>.words.json" and reused until the
#    video changes. Or a path to a words.json from hook_check.py, or to an ElevenLabs
#    alignment .json, if you already have one of those.
WORD_TIMING = "whisper"
WHISPER_MODEL = "base"      # "base" is fast; "small" hears names and numbers better

# 6. MODE. "ig" = Instagram master: DM keyword card over the last DM_CARD seconds, no brand end
#    card, the file loops. "yt" = YouTube master: brand end card appended after the last
#    picture, no DM card. Render both, always. (The command line can override this one value:
#    python compositor_template.py yt)
MODE = "ig"

# 7. HOOK CARD (frame 1, both masters). First line = the place, then the number lines. Lines
#    with a digit, $ or % show in gold, the rest in white. On frame 1 at full opacity, no
#    fade, no animation in; hard cuts out at "hold" seconds.
HOOK_CARD = {
    "lines": ["EAST PALO ALTO", "1992: 42 HOMICIDES", "2025: ZERO"],
    "hold": 2.5,
}

# 8. INSTAGRAM DM CARD ("ig" only). The keyword people DM, the subline that matches what the
#    voice promises, and how many seconds before the end it appears (3.0 is the brand rule).
DM_CARD = {"keyword": "ZERO", "subline": "FOR THE FULL STORY", "seconds": 3.0}

# 9. YOUTUBE END CARD ("yt" only). Subject line (gold cursive), button text, phone line.
#    ENDCARD_SECONDS = how long the card holds. ENDCARD_START = "after" appends it after the
#    last frame of picture (that frame freezes under the card), or a time in seconds such as
#    38.95 to start it over the picture while the voice finishes.
ENDCARD_SUBJECT = "42 TO ZERO"
ENDCARD_BUTTON = "SUBSCRIBE FOR BAY AREA REAL ESTATE HISTORY"
ENDCARD_PHONE = "OR CALL 650-308-4727"
ENDCARD_SECONDS = 4.0
ENDCARD_START = "after"

# 10. CAPTION FIXES. Whisper sometimes mishears a name or a number. Wrong word on the left,
#     right word on the right; the caption shows the right one, the timing stays. One word per
#     entry. Leave {} for none.
CAPTION_FIXES = {}          # e.g. {"Pallo": "Palo", "Ravens": "Ravenswood"}

# 11. OUTPUT. Leave "" to save next to the input as "<name> IG.mp4" or "<name> YT.mp4" (the
#     names the Friday hook check expects). Or give a full path ending in .mp4.
OUTPUT = ""

# =============================================================================
#  END OF SETTINGS. Everything below is the locked brand build. Do not edit.
# =============================================================================

if len(sys.argv) > 1 and sys.argv[1].strip().lower() in ("ig", "yt"):
    MODE = sys.argv[1].strip().lower()


def stop(msg):
    print("\nSTOP: " + msg)
    sys.exit(1)


# ── locked frame + brand constants (re-locked 2026-09-13) ───────────────────
# Instagram covers the top 14% (y<270) and bottom 35% (y>1248) of a 1080x1920 Reel with its
# own UI, so every burned-in element lives inside y 270-1248 and x 90-990.
W, H = 1080, 1920
CAPTION_TOP_Y = 1140    # 60 px caption line -> text bottom ~1210; hook_check must read the band at y 1150-1230
ACCENT = (196, 162, 101)
WHITE = (255, 255, 255)
BROKERAGE_LINE = "C O M P A S S   \u00b7   D R E  # 0 1 4 6 6 8 7 6"

B = os.path.dirname(os.path.abspath(__file__))


def _first_existing(paths, what):
    for p in paths:
        if os.path.exists(p):
            return p
    stop(f"cannot find {what}. Looked in:\n  " + "\n  ".join(paths))


# Caption font: Liberation Sans Bold on Linux (the original), Arial Bold elsewhere (Liberation
# Sans is the metric clone of Arial, so the captions land on the same pixels either way).
BOLD = _first_existing([
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
], "the caption font (Liberation Sans Bold or Arial Bold)")

# Brand fonts + logo live in the carousel-builder skill (same repo, two folders up).
CB = _first_existing([
    os.path.normpath(os.path.join(B, "..", "..", "carousel-builder", "assets")),
    os.path.expanduser("~/.claude/skills/carousel-builder/assets"),
    "/root/.claude/skills/carousel-builder/assets",
], "carousel-builder/assets (Montserrat, Great Vibes, logo_white.png); keep the skills repo folder layout")
_MONT = os.path.join(CB, "fonts", "Montserrat-var.ttf")
_VIBES = os.path.join(CB, "fonts", "GreatVibes-Regular.ttf")
_LOGO = os.path.join(CB, "logo", "logo_white.png")
for _p in (_MONT, _VIBES, _LOGO):
    if not os.path.exists(_p):
        stop(f"missing brand asset {_p}")


# ── checks on the settings + the file ───────────────────────────────────────
for tool in ("ffmpeg", "ffprobe"):
    if not shutil.which(tool):
        stop(f"{tool} is not installed or not on PATH. Install ffmpeg (it includes ffprobe) and try again.")

if MODE not in ("ig", "yt"):
    stop(f'MODE is "{MODE}"; it must be "ig" or "yt".')
if not os.path.isfile(INPUT_VIDEO):
    stop(f"INPUT_VIDEO does not exist: {INPUT_VIDEO}\nSetting 1 needs the full path to the CapCut export.")
if not HOOK_CARD.get("lines"):
    stop("HOOK_CARD needs at least one line (the place).")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate:format=duration",
                        "-of", "json", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        j = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        j = {}
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), None)
    has_audio = any(s.get("codec_type") == "audio" for s in j.get("streams", []))
    if v is None:
        stop(f"ffprobe finds no video in {path}")
    num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
    try:
        fps = float(num) / float(den)
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    return {"w": int(v.get("width") or 0), "h": int(v.get("height") or 0), "fps": fps,
            "dur": float((j.get("format") or {}).get("duration") or 0), "audio": has_audio}


info = probe(INPUT_VIDEO)
if (info["w"], info["h"]) != (INPUT_WIDTH, INPUT_HEIGHT):
    stop(f"the file is {info['w']} x {info['h']} but setting 2 says {INPUT_WIDTH} x {INPUT_HEIGHT}. "
         "Fix setting 2, or re-export from CapCut at 1080 x 1920.")
if abs(info["w"] / max(info["h"], 1) - 9 / 16) > 0.01:
    stop(f"the file is {info['w']} x {info['h']}, which is not 9:16. Export a vertical 1080 x 1920 master.")
if abs(info["fps"] - FPS) > 0.1:
    stop(f"the file runs at {info['fps']:.3f} fps but setting 3 says FPS = {FPS}. "
         f"Set FPS = {round(info['fps'])} or re-export from CapCut at {FPS} fps.")
if info["dur"] <= 0:
    stop("ffprobe reports zero length for the export; re-export it.")

if AUDIO == "video":
    if not info["audio"]:
        stop('setting 4 is "video" but the export has no sound. Export with audio, or point AUDIO at a .wav.')
    AUDIO_SRC = INPUT_VIDEO
else:
    if not os.path.isfile(AUDIO):
        stop(f"AUDIO file does not exist: {AUDIO}")
    AUDIO_SRC = AUDIO

VIDEO_DUR = info["dur"]
in_path = Path(INPUT_VIDEO)
if OUTPUT:
    OUT_PATH = Path(OUTPUT)
else:
    OUT_PATH = in_path.with_name(f"{in_path.stem} {MODE.upper()}.mp4")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

print(f"Input : {INPUT_VIDEO}  ({info['w']}x{info['h']}, {info['fps']:.3f} fps, {VIDEO_DUR:.2f} s)")
print(f"Audio : {'inside the export' if AUDIO == 'video' else AUDIO}")
print(f"Mode  : {MODE}")
print(f"Output: {OUT_PATH}")


# ── word timing: whisper on the cut voice, or a json you already have ────────
def _whisper_words(audio_src, model_name):
    """Word-level timing, the hook_check.py way: openai-whisper first, faster-whisper second."""
    wav = in_path.with_name(f"{in_path.stem}.audio16k.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(audio_src), "-vn", "-ac", "1",
                    "-ar", "16000", str(wav)], capture_output=True)
    if not wav.exists():
        stop("could not pull the audio out of the export (ffmpeg wrote no wav).")
    out, engine = [], None
    try:
        import whisper
        engine = f"openai-whisper ({model_name})"
        res = whisper.load_model(model_name).transcribe(str(wav), word_timestamps=True, fp16=False, language="en")
        for s in res["segments"]:
            for w in s.get("words", []):
                out.append([float(w["start"]), float(w["end"]), w["word"].strip()])
    except (ImportError, AttributeError):
        try:
            from faster_whisper import WhisperModel
            engine = f"faster-whisper ({model_name})"
            segments, _ = WhisperModel(model_name, device="cpu", compute_type="int8").transcribe(
                str(wav), word_timestamps=True, language="en")
            for s in segments:
                for w in (s.words or []):
                    out.append([float(w.start), float(w.end), w.word.strip()])
        except ImportError:
            stop("no whisper installed. Run:  pip install faster-whisper   (or: pip install openai-whisper)")
    try:
        wav.unlink()
    except OSError:
        pass
    return out, engine


def _load_timing_json(path):
    """Accepts hook_check words.json ([[start, end, word], ...]) or an ElevenLabs alignment json."""
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict) and "characters" in data:
        chars = data["characters"]
        t0s, t1s = data["character_start_times_seconds"], data["character_end_times_seconds"]
        out, cur, ws, prev_end = [], "", None, 0.0
        for c, a, b_ in zip(chars, t0s, t1s):
            if c == " ":
                if cur:
                    out.append([ws, prev_end, cur])
                cur, ws = "", None
            else:
                if ws is None:
                    ws = a
                cur += c
                prev_end = b_
        if cur:
            out.append([ws, prev_end, cur])
        return out
    if isinstance(data, list):
        return [[float(a), float(b_), str(w).strip()] for a, b_, w in data]
    stop(f"{path} is neither a hook_check words.json nor an ElevenLabs alignment json.")


def load_words():
    if WORD_TIMING == "whisper":
        cache = in_path.with_name(f"{in_path.stem}.words.json")
        newest_src = max(os.path.getmtime(INPUT_VIDEO), os.path.getmtime(AUDIO_SRC))
        if cache.exists() and os.path.getmtime(cache) >= newest_src:
            print(f"Timing: reusing {cache.name} (newer than the export)")
            raw = _load_timing_json(cache)
        else:
            print(f"Timing: whisper ({WHISPER_MODEL}) is listening to the audio (the first run downloads the model)...")
            raw, engine = _whisper_words(AUDIO_SRC, WHISPER_MODEL)
            with open(cache, "w", encoding="utf-8") as f:
                json.dump(raw, f)
            print(f"Timing: {len(raw)} words from {engine}, saved as {cache.name}")
    else:
        if not os.path.isfile(WORD_TIMING):
            stop(f"WORD_TIMING file does not exist: {WORD_TIMING}")
        raw = _load_timing_json(WORD_TIMING)
        print(f"Timing: {len(raw)} words from {WORD_TIMING}")
    raw = [(w, a, b_) for a, b_, w in raw if w]
    if not raw:
        stop("no spoken words found. Is the voice in the export? Try WHISPER_MODEL = \"small\".")
    return raw


words = load_words()       # [(word, start, end), ...] in spoken order
print("Heard : " + " ".join(w for w, _, _ in words)[:600])
print("        (a misheard name goes in CAPTION_FIXES, setting 10)")


def wt(i):
    return words[i][1]


def we(i):
    return words[i][2]


_fixes = {k.strip().lower(): v for k, v in CAPTION_FIXES.items()}
_PUNCT = '.,:;!?"\u2018\u2019\u201c\u201d%'


def fix_token(tok):
    core = tok.strip(_PUNCT)
    if core and core.lower() in _fixes:
        head = tok[:len(tok) - len(tok.lstrip(_PUNCT))]
        tail = tok[len(tok.rstrip(_PUNCT)):]
        return head + _fixes[core.lower()] + tail
    return tok


# ── captions: fixed pre-chunked lines, words pop into final positions ───────
phrases = []
curp = []
for idx, (tok, a, b_) in enumerate(words):
    curp.append(idx)
    if tok.rstrip('"\u2019').endswith(('.', '?', '!', '\u2014', ':', ',')):
        phrases.append(curp)
        curp = []
if curp:
    phrases.append(curp)

LINES = []
for p in phrases:
    for i in range(0, len(p), 3):
        LINES.append(p[i:i + 3])
line_windows = []
for li, ln in enumerate(LINES):
    t0 = wt(ln[0])
    t1 = wt(LINES[li + 1][0]) if li + 1 < len(LINES) else we(ln[-1]) + 0.6
    line_windows.append((t0, t1))

f_cap = ImageFont.truetype(BOLD, 60)
f_cap_s = ImageFont.truetype(BOLD, 46)


def draw_outlined(d, xy, text, font, fill=WHITE, ow=4):
    x, y = xy
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            d.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    d.text((x, y), text, font=font, fill=fill)


def draw_captions(frame, t):
    li = None
    for i2, (t0, t1) in enumerate(line_windows):
        if t0 <= t < t1:
            li = i2
            break
    if li is None:
        return
    ln = LINES[li]
    d = ImageDraw.Draw(frame)
    toks = [fix_token(words[i][0]) for i in ln]
    gaps = 16
    f = f_cap
    widths = [d.textlength(tok, font=f) for tok in toks]
    if sum(widths) + gaps * (len(toks) - 1) > 1000:
        f = f_cap_s
        widths = [d.textlength(tok, font=f) for tok in toks]
    total = sum(widths) + gaps * (len(toks) - 1)
    x = (W - total) // 2
    y = CAPTION_TOP_Y
    for i2, w_ in zip(ln, widths):
        tok, a, b_ = words[i2]
        tok = fix_token(tok)
        if t < a - 0.02:
            x += w_ + gaps
            continue
        age = t - a
        if a <= t <= b_ + 0.15:
            fw = f
            if age < 0.10:
                fw = ImageFont.truetype(BOLD, max(30, int(f.size * (0.7 + 0.3 * age / 0.10))))
            ww = d.textlength(tok, font=fw)
            asc, desc = fw.getmetrics()
            ox = x + (w_ - ww) / 2
            d.rounded_rectangle([ox - 12, y - 8, ox + ww + 12, y + asc + desc + 2], radius=14, fill=ACCENT)
            d.text((ox, y), tok, font=fw, fill=(0, 0, 0))
        else:
            draw_outlined(d, (x, y), tok, f)
        x += w_ + gaps


# ── brand fonts + gold gradient ─────────────────────────────────────────────
_logo = Image.open(_LOGO).convert("RGBA")


def mont(size, weight=800):
    f = ImageFont.truetype(_MONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def _gold_gradient(w, h, light=(240, 212, 138), dark=(168, 130, 62)):
    g = Image.new("RGB", (w, h))
    dd = ImageDraw.Draw(g)
    for yy in range(h):
        t_ = yy / max(h - 1, 1)
        if t_ < 0.55:
            k = t_ / 0.55
            c = tuple(int(light[i] + (dark[i] - light[i]) * k) for i in range(3))
        else:
            k = (t_ - 0.55) / 0.45
            c = tuple(int(dark[i] + (light[i] - dark[i]) * 0.35 * k) for i in range(3))
        dd.line([(0, yy), (w, yy)], fill=c)
    return g


# ── end card (YouTube master only) ──────────────────────────────────────────
_ec = None


def build_endcard():
    global _ec
    if _ec is not None:
        return _ec
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 150))
    lw = 720
    lg = _logo.resize((lw, int(_logo.height * lw / _logo.width)), Image.LANCZOS)
    ov.paste(lg, ((W - lw) // 2, 300), lg)            # stack lives inside y 300-1240 (Instagram-safe)
    ya = 300 + lg.height + 25
    f_int = mont(38, 500)
    txt = BROKERAGE_LINE
    d.text(((W - d.textlength(txt, font=f_int)) / 2, ya), txt, font=f_int, fill=(235, 235, 235, 255))
    sub = ENDCARD_SUBJECT
    fsz = 130
    while fsz > 40:
        f_v = ImageFont.truetype(_VIBES, fsz)
        tw = d.textlength(sub, font=f_v)
        if tw <= 980:
            break
        fsz -= 4
    mask = Image.new("L", (W, 240), 0)
    ImageDraw.Draw(mask).text(((W - tw) / 2, 20), sub, font=f_v, fill=255)
    grad = _gold_gradient(W, 240, light=(238, 205, 130), dark=(178, 138, 66)).convert("RGBA")
    ov.paste(grad, (0, 720), mask)
    bw, bh = 760, 150
    bx, by = (W - bw) // 2, 990
    btn = _gold_gradient(bw, bh).convert("RGBA")
    m = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, bw, bh], radius=34, fill=255)
    btn.putalpha(m)
    ov.paste(btn, (bx, by), btn)
    bt = ENDCARD_BUTTON
    bsz = 72
    d = ImageDraw.Draw(ov)
    while bsz > 30:                                   # shrink to fit inside the button
        f_btn = mont(bsz, 800)
        if d.textlength(bt, font=f_btn) <= bw - 60:
            break
        bsz -= 4
    asc, desc = f_btn.getmetrics()
    d.text(((W - d.textlength(bt, font=f_btn)) / 2, by + (bh - asc - desc) // 2), bt, font=f_btn, fill=(10, 8, 4, 255))
    f_oc = mont(46, 700)
    oc = ENDCARD_PHONE
    d.text(((W - d.textlength(oc, font=f_oc)) / 2, by + bh + 40), oc, font=f_oc, fill=(255, 255, 255, 255))   # ends ~y 1230
    _ec = ov
    return ov


# ── frame-1 hook card + Instagram DM card (added 2026-09-13) ─────────────────
_hook = None


def build_hook_card():
    """Place + number stack, centered, inside y 430-1150 and x 90-990. No animation: it is simply
    composited at full opacity from the first frame until HOOK_CARD['hold']."""
    global _hook
    if _hook is not None:
        return _hook
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 128))
    lines = HOOK_CARD["lines"]

    def fitf(s, size, weight=800, maxw=900):
        while size > 28:
            f = mont(size, weight)
            if d.textlength(s, font=f) <= maxw:
                return f
            size -= 4
        return mont(size, weight)

    # Every line carries a black outline (same treatment as the DM card subline) so the card
    # reads on any footage and hook_check's "Text on frame 0" sees it whatever sits behind it.
    y = 430
    f0 = fitf(lines[0], 104)
    d.text(((W - d.textlength(lines[0], font=f0)) / 2, y), lines[0], font=f0, fill=(255, 255, 255, 255),
           stroke_width=4, stroke_fill=(0, 0, 0, 255))
    y += 104 + 34
    d.rectangle([(W - 280) // 2, y, (W + 280) // 2, y + 6], fill=ACCENT + (255,))
    y += 36
    for s in lines[1:]:
        big = any(ch.isdigit() for ch in s) or "$" in s or "%" in s
        f = fitf(s, 150 if big else 62)
        d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=(ACCENT + (255,)) if big else (255, 255, 255, 255),
               stroke_width=3, stroke_fill=(0, 0, 0, 255))
        y += f.size + 28
    if y > 1180:
        stop(f"the hook card runs to y {y}, past the Instagram safe zone. Use fewer or shorter HOOK_CARD lines.")
    _hook = ov
    return ov


_dm = None


def build_dm_card():
    """Instagram closing: gold DM button plus one subline, box y 430-640. The brand end card is never
    used on an Instagram master; the file ends where the CapCut cut ends and loops."""
    global _dm
    if _dm is not None:
        return _dm
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    bw, bh = 760, 150
    bx, by = (W - bw) // 2, 430
    btn = _gold_gradient(bw, bh).convert("RGBA")
    m = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, bw, bh], radius=34, fill=255)
    btn.putalpha(m)
    ov.paste(btn, (bx, by), btn)
    bt = f'DM  "{DM_CARD["keyword"]}"'
    f_btn = mont(72, 800)
    asc, desc = f_btn.getmetrics()
    d.text(((W - d.textlength(bt, font=f_btn)) / 2, by + (bh - asc - desc) // 2), bt, font=f_btn, fill=(10, 8, 4, 255))
    f_sub = mont(40, 700)
    sub = DM_CARD["subline"]
    d.text(((W - d.textlength(sub, font=f_sub)) / 2, by + bh + 14), sub, font=f_sub, fill=(255, 255, 255, 255),
           stroke_width=3, stroke_fill=(0, 0, 0, 255))
    _dm = ov
    return ov


# ── decode -> burn -> encode ────────────────────────────────────────────────
# The decoder scales any 9:16 input (1080x1920 export or 2160x3840 avatar render) to the
# 1080x1920 frame with LANCZOS and runs at FPS, the same number the encoder uses.
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", INPUT_VIDEO,
                        "-vf", f"scale={W}:{H}:flags=lanczos", "-r", str(FPS),
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE, bufsize=10 ** 7)

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", str(AUDIO_SRC),
                        "-map", "0:v", "-map", "1:a:0",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                        str(OUT_PATH)], stdin=subprocess.PIPE)

if MODE == "yt":
    ec_start = None if ENDCARD_START == "after" else float(ENDCARD_START)
    est_total = max(VIDEO_DUR, (ec_start if ec_start is not None else VIDEO_DUR) + ENDCARD_SECONDS)
else:
    ec_start = None
    est_total = VIDEO_DUR
est_frames = int(round(est_total * FPS))

n = 0
last = None
card_t0 = None        # when the end card first appeared
picture_done = False
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) == W * H * 3:
        frame = Image.frombytes("RGB", (W, H), buf)
        last = frame
    else:
        picture_done = True
        if MODE != "yt" or last is None:
            break
        if card_t0 is not None and n / FPS >= card_t0 + ENDCARD_SECONDS:
            break
        frame = last.copy()                        # the last picture freezes under the appended card
    t = n / FPS
    card_on = MODE == "yt" and (picture_done or (ec_start is not None and t >= ec_start))
    if card_on:
        if card_t0 is None:
            card_t0 = t
        ov = build_endcard()                       # YouTube only: brand card, 0.4 s fade in
        prog = min(1.0, (t - card_t0) / 0.4)
        if prog < 1.0:
            ov = ov.copy()
            alpha = ov.getchannel("A").point(lambda a2: int(a2 * prog))
            ov.putalpha(alpha)
        frame = Image.alpha_composite(frame.convert("RGBA"), ov).convert("RGB")
    else:
        draw_captions(frame, t)
        if t < HOOK_CARD["hold"]:                  # frame 1 onward, full opacity, no fade in, hard out
            frame = Image.alpha_composite(frame.convert("RGBA"), build_hook_card()).convert("RGB")
        if MODE == "ig" and t >= VIDEO_DUR - DM_CARD["seconds"]:
            frame = Image.alpha_composite(frame.convert("RGBA"), build_dm_card()).convert("RGB")
    enc.stdin.write(frame.tobytes())
    n += 1
    if n % 250 == 0:
        print(f"frame {n} of about {est_frames}", flush=True)
    if picture_done and MODE == "yt" and card_t0 is not None and n / FPS >= card_t0 + ENDCARD_SECONDS:
        break

dec.stdout.close()
enc.stdin.close()
enc.wait()
dec.wait()
if enc.returncode != 0 or not OUT_PATH.exists():
    stop("ffmpeg could not write the output file; see the error above.")
print(f"\nDone: {n} frames ({n / FPS:.2f} s) -> {OUT_PATH}")
print('Next: python video-watcher/scripts/hook_check.py "<that file>" --place "East Palo Alto"')
if MODE == "ig":
    print('Then render the YouTube master:  python compositor_template.py yt')
else:
    print('Then render the Instagram master: python compositor_template.py ig')
