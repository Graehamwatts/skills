#!/usr/bin/env python3
"""ROAD Act reel — forked from composite_rwc.py v22 (all locked patterns kept):
- 4K AV pipe, frozen per-interval punch-in crops (sharp, no lag)
- hook native framing (no zoom pumping)
- blur-fill evidence inserts, RED partial ellipses (padded, never touch text)
- RED arrow for congress.gov (dense rows — arrow-only, verified-empty zone)
- landscape wide strip under captions on inserts, gold top stroke
- fixed-line pop-in captions y=1420; caps stacks; whip-blur cuts; endcard DM "EDGE"
"""
import json, subprocess, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 25
AV = f"{B}/avatar_road3_4k.mp4"
AVW, AVH = 2160, 3840
FD = "/usr/share/fonts/truetype/liberation"
BOLD = f"{FD}/LiberationSans-Bold.ttf"
ACCENT = (196, 162, 101); WHITE = (255,255,255)

al = json.load(open(f"{B}/alignment_road2.json"))
chars, t0s, t1s = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
words = []
cur, ws = "", None
for c, a, b_ in zip(chars, t0s, t1s):
    if c == " ":
        if cur: words.append((cur, ws, prev_end))
        cur, ws = "", None
    else:
        if ws is None: ws = a
        cur += c
        prev_end = b_
if cur: words.append((cur, ws, prev_end))
DUR = t1s[-1]

def find(seq_start, phrase):
    for i in range(seq_start, len(words)):
        if words[i][0].strip('.,:;—?!"‘’%').lower() == phrase.lower():
            return i
    raise ValueError(phrase)
def wt(i): return words[i][1]
def we(i): return words[i][2]

i_no    = find(0, "no"); i_buying = find(i_no, "buying")
i_its   = find(0, "It's")
i_inv   = find(i_its, "Investors")
i_that  = find(i_inv, "That")
i_and2  = find(i_that, "And")
i_one   = find(i_and2, "One")
i_31    = find(i_one, "31"); i_office2 = find(i_31, "office")
i_another = find(i_31, "Another")
ENDCARD_START = 38.95   # right after "caught a break." — endcard holds ~5.1s under full CTA

# ── timeline: ROAD Act — buyer-empowerment cut ──────────────────────────────
SEGS = [
    (0.0,            wt(i_its),     'head', 1.6),
    (wt(i_its),      wt(i_inv),     'insert', 'congress'),
    (wt(i_inv),      wt(i_that),    'insert', 'time'),
    (wt(i_that),     wt(i_and2),    'head', 1.6),
    (wt(i_and2),     wt(i_one),     'insert', 'spotlight'),
    (wt(i_one),      wt(i_another), 'head', 1.6),
    (wt(i_another),  ENDCARD_START, 'broll', f"{B}/broll_sj/construction"),
    (ENDCARD_START,  DUR + 1,       'broll', f"{B}/broll_sj/downtown"),
]
CUTS = [s for (s, e, k, a) in SEGS[1:]]

# caps stacks: (words to stack, trigger word idxs, position y)
CAPS_STACKS = [
    (["NO MORE", "BUYING HOMES."], [i_no, i_buying], 260),
    (["31%", "OFFICE VACANCY"], [i_31, i_office2], 220),
]
f_caps = ImageFont.truetype(BOLD, 118)

ins_imgs = {k: Image.open(f"{B}/ins_{k}.png").convert("RGB")
            for k in ["congress","time","spotlight"]}

# ellipses sized by CORNER TEST: every corner of every circled text line at
# <=0.86 normalized ellipse radius, so the stroke NEVER touches the circled
# text anywhere along its curve (verified qc/chk3_time.png, qc/chk4_spotlight.png)
ELL = {"time": (8, 281, 583, 460), "spotlight": (34, 234, 914, 378)}
# congress.gov rows too dense for a clean ellipse -> RED arrow only, aimed at
# "Became Public Law No: 119-101"; tail + path verified empty (qc/chk_congress2.png)
ARROW = {"congress": True, "time": False, "spotlight": False}
ARROW_TAIL = {"congress": (603, 386)}
ARROW_TIP  = {"congress": (471, 479)}

def draw_partial_ellipse(d, box, prog, width=10):
    if prog <= 0: return
    RED_ = (220, 40, 35)
    d.arc(box, start=-80, end=-80 + 360*min(prog,1.0), fill=RED_, width=width)
    d.arc([box[0]+3, box[1]+2, box[2]+3, box[3]+2], start=-80, end=-80+360*min(prog,1.0), fill=RED_, width=width-2)

def render_insert(key, t_local, dur_seg):
    img = ins_imgs[key].copy()
    d = ImageDraw.Draw(img)
    prog = t_local / max(dur_seg, 0.01)
    # circle draws over first 0.8s — NO cursor
    if key in ELL:
        draw_partial_ellipse(d, list(ELL[key]), t_local/0.8)
    # RED arrow: slides in from the tail anchor toward its tip target
    if ARROW.get(key) and t_local > 0.9:
        ta = min((t_local - 0.9) / 0.3, 1.0)
        ease = 1 - (1 - ta)**3
        if key in ARROW_TIP:
            tipx, tipy = ARROW_TIP[key]
        else:
            e = ELL[key]
            tipx = e[2] - 14; tipy = (e[1] + e[3])//2 - 20
        tailx, taily = ARROW_TAIL[key]
        sx = tailx + (1-ease)*90; sy = taily - (1-ease)*70
        ang = math.atan2(tipy - sy, tipx - sx)
        L = math.hypot(tipx - sx, tipy - sy)
        bx, by = tipx - 0.32*L*math.cos(ang), tipy - 0.32*L*math.sin(ang)
        px_, py_ = -math.sin(ang), math.cos(ang)
        d.line([(sx, sy), (bx, by)], fill=(220, 40, 35), width=16)
        d.polygon([(tipx, tipy),
                   (bx + px_*26, by + py_*26),
                   (bx - px_*26, by - py_*26)], fill=(220, 40, 35))
    pe = 1 - (1 - min(prog, 1.0))**3
    scale = 1.03 + 0.07*pe
    sw, sh = int(W*scale), int(H*scale)
    z = img.resize((sw, sh), Image.LANCZOS)
    return z.crop(((sw-W)//2, (sh-H)//2, (sw-W)//2+W, (sh-H)//2+H))

# ── captions: fixed pre-chunked lines, words pop into final positions ───────
phrases = []
curp = []
for idx, (tok, a, b_) in enumerate(words):
    curp.append(idx)
    if tok.rstrip('"’').endswith(('.', '?', '!', '—', ':', ',')):
        phrases.append(curp); curp = []
if curp: phrases.append(curp)

LINES = []
for p in phrases:
    for i in range(0, len(p), 3):
        LINES.append(p[i:i+3])
line_windows = []
for li, ln in enumerate(LINES):
    t0 = wt(ln[0])
    t1 = wt(LINES[li+1][0]) if li+1 < len(LINES) else we(ln[-1]) + 0.6
    line_windows.append((t0, t1))

f_cap = ImageFont.truetype(BOLD, 60)
f_cap_s = ImageFont.truetype(BOLD, 46)

def draw_outlined(d, xy, text, font, fill=WHITE, ow=4):
    x, y = xy
    for dx in range(-ow, ow+1, 2):
        for dy in range(-ow, ow+1, 2):
            d.text((x+dx, y+dy), text, font=font, fill=(0,0,0))
    d.text((x, y), text, font=font, fill=fill)

_DISP = {}  # no $-substitutions needed this video (no bare-decimal prices spoken)

def draw_captions(frame, t):
    li = None
    for i2, (t0, t1) in enumerate(line_windows):
        if t0 <= t < t1: li = i2; break
    if li is None: return
    ln = LINES[li]
    d = ImageDraw.Draw(frame)
    toks = [_DISP.get(words[i][0], words[i][0]) for i in ln]
    gaps = 16
    f = f_cap
    widths = [d.textlength(tok, font=f) for tok in toks]
    if sum(widths) + gaps*(len(toks)-1) > 1000:
        f = f_cap_s
        widths = [d.textlength(tok, font=f) for tok in toks]
    total = sum(widths) + gaps*(len(toks)-1)
    x = (W-total)//2; y = 1420
    for i2, w_ in zip(ln, widths):
        tok, a, b_ = words[i2]
        tok = _DISP.get(tok, tok)
        if t < a - 0.02:
            x += w_ + gaps
            continue
        age = t - a
        if a <= t <= b_ + 0.15:
            fw = f
            if age < 0.10:
                fw = ImageFont.truetype(BOLD, max(30, int(f.size * (0.7 + 0.3*age/0.10))))
            ww = d.textlength(tok, font=fw)
            asc, desc = fw.getmetrics()
            ox = x + (w_ - ww)/2
            d.rounded_rectangle([ox-12, y-8, ox+ww+12, y+asc+desc+2], radius=14, fill=ACCENT)
            d.text((ox, y), tok, font=fw, fill=(0,0,0))
        else:
            draw_outlined(d, (x, y), tok, f)
        x += w_ + gaps

def draw_caps_stack(frame, t):
    for stack_words, idxs, y0 in CAPS_STACKS:
        t_start = wt(idxs[0]); t_end = we(idxs[-1]) + 1.4
        for ct in CUTS:
            if t_start < ct < t_end: t_end = ct - 0.04; break
        if not (t_start <= t <= t_end): continue
        d = ImageDraw.Draw(frame)
        yy = y0
        for sw_, idx in zip(stack_words, idxs):
            if t >= wt(idx):
                age = t - wt(idx)
                size = 118 if age > 0.12 else int(118*(0.6+0.4*age/0.12))
                f = ImageFont.truetype(BOLD, size)
                tw = d.textlength(sw_, font=f)
                draw_outlined(d, ((W-tw)/2, yy), sw_, f, ow=8)
            yy += 132

# ── end card ────────────────────────────────────────────────────────────────
CB = "/root/.claude/skills/carousel-builder/assets"
_logo = Image.open(f"{CB}/logo/logo_white.png").convert("RGBA")
_mont = f"{CB}/fonts/Montserrat-var.ttf"; _vibes = f"{CB}/fonts/GreatVibes-Regular.ttf"
def mont(size, weight=800):
    f = ImageFont.truetype(_mont, size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f
def _gold_gradient(w, h, light=(240,212,138), dark=(168,130,62)):
    g = Image.new("RGB", (w, h)); dd = ImageDraw.Draw(g)
    for yy in range(h):
        t_ = yy / max(h-1, 1)
        if t_ < 0.55: k=t_/0.55; c=tuple(int(light[i]+(dark[i]-light[i])*k) for i in range(3))
        else: k=(t_-0.55)/0.45; c=tuple(int(dark[i]+(light[i]-dark[i])*0.35*k) for i in range(3))
        dd.line([(0,yy),(w,yy)], fill=c)
    return g
_ec = None
def build_endcard():
    global _ec
    if _ec is not None: return _ec
    ov = Image.new("RGBA",(W,H),(0,0,0,0)); d = ImageDraw.Draw(ov)
    d.rectangle([0,0,W,H], fill=(0,0,0,150))
    lw=860; lg=_logo.resize((lw,int(_logo.height*lw/_logo.width)),Image.LANCZOS)
    ov.paste(lg,((W-lw)//2,130),lg)
    ya=130+lg.height+30; f_int=mont(38,500)
    txt="I N T E R O   ·   D R E  # 0 1 4 6 6 8 7 6"
    d.text(((W-d.textlength(txt,font=f_int))/2,ya),txt,font=f_int,fill=(235,235,235,255))
    sub="The New Housing Law"; fsz=130
    while fsz>40:
        f_v=ImageFont.truetype(_vibes,fsz); tw=d.textlength(sub,font=f_v)
        if tw<=980: break
        fsz-=4
    mask=Image.new("L",(W,240),0)
    ImageDraw.Draw(mask).text(((W-tw)/2,20),sub,font=f_v,fill=255)
    grad=_gold_gradient(W,240,light=(238,205,130),dark=(178,138,66)).convert("RGBA")
    ov.paste(grad,(0,900),mask)
    bw,bh=760,150; bx,by=(W-bw)//2,1220
    btn=_gold_gradient(bw,bh).convert("RGBA")
    m=Image.new("L",(bw,bh),0); ImageDraw.Draw(m).rounded_rectangle([0,0,bw,bh],radius=34,fill=255)
    btn.putalpha(m); ov.paste(btn,(bx,by),btn)
    f_btn=mont(72,800); bt='DM  "EDGE"'
    d=ImageDraw.Draw(ov)
    d.text(((W-d.textlength(bt,font=f_btn))/2,by+34),bt,font=f_btn,fill=(10,8,4,255))
    f_oc=mont(46,700); oc="OR CALL — NUMBER IN BIO"
    d.text(((W-d.textlength(oc,font=f_oc))/2,by+bh+60),oc,font=f_oc,fill=(255,255,255,255))
    _ec=ov; return ov

_ema = {}

# gold beat stickers on b-roll
STICKERS = {f"{B}/broll_sj/construction": "SAN JOSE, CA"}
_stick_cache = {}
def sticker_img(text):
    if text not in _stick_cache:
        f = ImageFont.truetype(BOLD, 64)
        tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
        tw = int(tmp.textlength(text, font=f))
        w_, h_ = tw + 84, 110
        im = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w_-1, h_-1], radius=20, fill=(196, 162, 101, 255),
                            outline=(0, 0, 0, 255), width=5)
        d.text((42, 20), text, font=f, fill=(10, 8, 4, 255))
        _stick_cache[text] = im.rotate(-2, expand=True, resample=Image.BICUBIC)
    return _stick_cache[text]

def seg_at(t):
    for s in SEGS:
        if s[0] <= t < s[1]: return s
    return SEGS[-1]

dec = subprocess.Popen(["ffmpeg","-v","error","-i",AV,"-f","rawvideo","-pix_fmt","rgb24",
    "-s",f"{AVW}x{AVH}","-r",str(FPS),"-"], stdout=subprocess.PIPE, bufsize=3*10**7)
_crop_lock = {}
ALPHA = f"{B}/avatar_road3_alpha.webm"
dec3 = subprocess.Popen(["ffmpeg","-v","error","-c:v","libvpx-vp9","-i",ALPHA,
    "-f","rawvideo","-pix_fmt","rgba","-s",f"{W}x{H}","-r",str(FPS),"-"],
    stdout=subprocess.PIPE, bufsize=10**7)
WIDE = f"{B}/avatar_road3_wide.mp4"
SW_, SH_ = 1080, 607
dec4 = subprocess.Popen(["ffmpeg","-v","error","-i",WIDE,
    "-f","rawvideo","-pix_fmt","rgb24","-s",f"{SW_}x{SH_}","-r",str(FPS),"-"],
    stdout=subprocess.PIPE, bufsize=10**7)
_wide_current = None

# warm grade LUT + vignette
_lut_r = np.clip(np.arange(256)*1.05 + 6, 0, 255).astype(np.uint8)
_lut_g = np.clip(np.arange(256)*1.02 + 2, 0, 255).astype(np.uint8)
_lut_b = np.clip(np.arange(256)*0.97, 0, 255).astype(np.uint8)
yy_, xx_ = np.mgrid[0:H, 0:W]
_vig = 1.0 - 0.28*(((xx_-W/2)/(W/2))**2 + ((yy_-H/2)/(H/2))**2)/2
_vig = np.clip(_vig, 0.72, 1.0)[..., None].astype(np.float32)
def grade(frame):
    arr = np.array(frame)
    arr[..., 0] = _lut_r[arr[..., 0]]
    arr[..., 1] = _lut_g[arr[..., 1]]
    arr[..., 2] = _lut_b[arr[..., 2]]
    arr = (arr.astype(np.float32) * _vig).astype(np.uint8)
    return Image.fromarray(arr)

enc = subprocess.Popen(["ffmpeg","-v","error","-y",
    "-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-i",f"{B}/vo_mix_road4.wav",
    "-map","0:v","-map","1:a",
    "-c:v","libx264","-pix_fmt","yuv420p","-preset","medium","-crf","18",
    "-c:a","aac","-b:a","192k","-movflags","+faststart",
    f"{B}/../reel_road_v7_raw.mp4"], stdin=subprocess.PIPE)

n = 0
while True:
    buf = dec.stdout.read(AVW*AVH*3)
    if len(buf) < AVW*AVH*3: break
    t = n / FPS
    av_frame = Image.frombytes("RGB", (AVW,AVH), buf)
    abuf = dec3.stdout.read(W*H*4)
    if len(abuf) == W*H*4:
        globals()['_alpha_current'] = Image.frombytes("RGBA", (W,H), abuf)
    wbuf = dec4.stdout.read(SW_*SH_*3)
    if len(wbuf) == SW_*SH_*3:
        globals()['_wide_current'] = Image.frombytes("RGB", (SW_, SH_), wbuf)
    s0, s1, kind, arg = seg_at(t)
    if kind == 'head':
        a = np.array(_alpha_current.getchannel("A"))
        rows = (a > 40).sum(axis=1)
        nz = np.where(rows > 30)[0]
        top = int(nz[0]) if len(nz) else 300
        shl = np.where(rows > 0.55 * W)[0]
        sh = int(shl[0]) if len(shl) else top + 600
        bandm = a[top:max(sh, top + 60), :]
        colsm = (bandm > 40).sum(axis=0)
        fcx = float((colsm * np.arange(W)).sum() / max(colsm.sum(), 1))
        fcy = top + 0.42 * max(sh - top, 260)
        e = _ema.setdefault('face', [fcx, fcy])
        e[0] = 0.90*e[0] + 0.10*fcx; e[1] = 0.90*e[1] + 0.10*fcy
        if s0 < 0.1:
            zj = 1.0   # hook: pure native framing, NO zoom pumping
        else:
            # EXAGGERATED jump cuts (2026-08-05): wide half-body <-> tight face,
            # not a subtle pump — the two framings must read as a real cut
            zj = 1.15 if int((t-s0)/1.8) % 2 == 0 else 1.75
        if zj <= 1.001:
            frame = av_frame.resize((W, H), Image.LANCZOS)
        else:
            ki = (round(s0, 2), int((t - s0) / 1.8))
            if ki not in _crop_lock:
                _crop_lock[ki] = (e[0], e[1])
            fx, fy = _crop_lock[ki]
            cw, ch = int(W/zj), int(H/zj)
            x0 = int(min(max(fx - cw/2, 0), W - cw))
            y0 = int(min(max(fy - ch*0.42, 0), H - ch))
            frame = av_frame.crop((x0*2, y0*2, (x0+cw)*2, (y0+ch)*2)).resize((W, H), Image.LANCZOS)
    elif kind == 'insert':
        frame = render_insert(arg, t - s0, s1 - s0)
        if _wide_current is not None:
            frame.paste(_wide_current, (0, 1385))
            dd = ImageDraw.Draw(frame)
            dd.rectangle([0, 1385, W, 1389], fill=ACCENT)
    else:
        files = sorted(os.listdir(arg))
        idx = min(int((t - s0) * FPS), len(files) - 1)
        frame = Image.open(os.path.join(arg, files[idx])).convert("RGB")
        st = STICKERS.get(arg)
        if st is not None and (t - s0) > 0.1:
            p = min((t - s0 - 0.1) / 0.35, 1.0)
            sc_ = 0.5 + 0.8*p if p <= 0.8 else 1.14 - 0.14*(p-0.8)/0.2
            sim = sticker_img(st)
            sw_, sh_ = int(sim.width*sc_), int(sim.height*sc_)
            sim2 = sim.resize((max(sw_,1), max(sh_,1)), Image.BILINEAR)
            frame.paste(sim2, ((W - sim2.width)//2, 430 - sim2.height//2), sim2)
    # impact settle
    for ct in CUTS:
        dtc = t - ct
        if 0 <= dtc < 0.25:
            k = 1 - (dtc/0.25)
            zi = 1.0 + 0.06*(k**2)
            cw, ch = int(W/zi), int(H/zi)
            frame = frame.crop(((W-cw)//2, (H-ch)//2, (W-cw)//2+cw, (H-ch)//2+ch)).resize((W, H), Image.BILINEAR)
            break
    frame = grade(frame)
    # whip-blur transition
    for ct in CUTS:
        dt = t - ct
        if -0.06 <= dt < 0.10:
            k = 1 - abs(dt)/0.10
            frame = frame.filter(ImageFilter.GaussianBlur(radius=1))
            arr = np.array(frame)
            shift = int(70*k)
            if shift > 0:
                arr = (arr.astype(np.uint16) + np.roll(arr, shift, axis=1) + np.roll(arr, -shift, axis=1))//3
                frame = Image.fromarray(arr.astype(np.uint8))
            break
    if t < ENDCARD_START:
        draw_caps_stack(frame, t)
        draw_captions(frame, t)
    else:
        ov = build_endcard()
        prog = min(1.0, (t-ENDCARD_START)/0.4)
        if prog < 1.0:
            ov = ov.copy(); alpha = ov.getchannel("A").point(lambda a2: int(a2*prog)); ov.putalpha(alpha)
        frame = Image.alpha_composite(frame.convert("RGBA"), ov).convert("RGB")
    enc.stdin.write(frame.tobytes())
    n += 1
    if n % 250 == 0: print("frame", n, flush=True)

dec.stdout.close(); dec3.stdout.close(); enc.stdin.close(); enc.wait()
print("road v1 composited", n, "frames")
