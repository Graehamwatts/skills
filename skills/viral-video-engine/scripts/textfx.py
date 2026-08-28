import sys, os, math, subprocess
sys.path.insert(0, '/sessions/dazzling-upbeat-gauss/mnt/.claude/skills/carousel-builder/scripts')
import carousel_lib as lib
from PIL import Image, ImageDraw, ImageFilter
FPS = 25
W, H = 1080, 1920

def add_shadow(img, blur=10, alpha=200, grow=2):
    """Soft blurred black silhouette under the element (carousel place_logo technique)."""
    a = img.getchannel('A')
    sil = Image.new('RGBA', img.size, (0,0,0,0))
    black = Image.new('RGBA', img.size, (0,0,0,alpha))
    sil.paste(black, (0,0), a)
    for _ in range(grow):
        sil = sil.filter(ImageFilter.MaxFilter(5))
    sil = sil.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new('RGBA', img.size, (0,0,0,0))
    out.alpha_composite(sil)
    out.alpha_composite(sil)
    out.alpha_composite(img)
    return out

def add_panel(img, pad_x=50, pad_y=34, alpha=170, radius=26):
    """Dark translucent rounded panel sized to the element's ink box."""
    bbox = img.getbbox()
    if not bbox: return img
    x0,y0,x1,y1 = bbox
    out = img.copy()
    pnl = Image.new('RGBA', img.size, (0,0,0,0))
    ImageDraw.Draw(pnl).rounded_rectangle(
        [max(x0-pad_x,0), max(y0-pad_y,0), min(x1+pad_x,img.size[0]-1), min(y1+pad_y,img.size[1]-1)],
        radius=radius, fill=(10,10,10,alpha))
    base = Image.new('RGBA', img.size, (0,0,0,0))
    base.alpha_composite(pnl)
    base.alpha_composite(out)
    return base

def ease_out_back(t, s=1.9):
    t -= 1; return t*t*((s+1)*t+s)+1
def ease_out(t): return 1-(1-t)**3

def render_pop(canvas_img, dur, pop=0.28, kind='pop', creep=1.03, out_fade=0.0):
    """canvas_img: RGBA element image. Yields full-anim frames (same size)."""
    n = int(dur*FPS); pn = max(int(pop*FPS),1)
    w,h = canvas_img.size
    for i in range(n):
        t = i/FPS
        fr = Image.new('RGBA',(w,h),(0,0,0,0))
        if i < pn:
            p = (i+1)/pn
            if kind=='slam':
                sc = 2.6 - 1.6*ease_out(p)
                alpha = min(1.0, p*2)
            elif kind=='slide':
                sc = 1.0; alpha = ease_out(p)
            else:
                sc = 0.4 + 0.6*ease_out_back(p); alpha = min(1.0,p*2.5)
        else:
            hold = (t-pop)/max(dur-pop,0.01)
            sc = 1.0 + (creep-1.0)*hold; alpha = 1.0
        if out_fade>0 and t > dur-out_fade:
            alpha *= max(0.0,(dur-t)/out_fade)
        sw,sh = max(int(w*sc),2), max(int(h*sc),2)
        im = canvas_img.resize((sw,sh), Image.LANCZOS)
        ox,oy = (w-sw)//2, (h-sh)//2
        if kind=='slide' and i<pn:
            oy += int(80*(1-ease_out((i+1)/pn)))
        if alpha < 1.0:
            a = im.getchannel('A').point(lambda v: int(v*alpha)); im.putalpha(a)
        fr.alpha_composite(im,(ox,oy))
        yield fr

def save_seq(frames, name):
    d = f'/tmp/edit/fx/{name}'; os.makedirs(d, exist_ok=True)
    for i,f in enumerate(frames): f.save(f'{d}/{i:03d}.png')
    return d

def pad_box(w,h,pad=80): return Image.new('RGBA',(w+pad*2,h+pad*2),(0,0,0,0)), pad

# ---------- element builders (carousel v3 impact style) ----------
def el_gradient_headline(text, size, sub=None, sub_size=44, tag=None, panel=False):
    f = lib.get_font('Mont', 900, size)
    d0 = ImageDraw.Draw(Image.new('RGBA',(10,10)))
    bb = d0.textbbox((0,0), text, font=f); tw,th = bb[2]-bb[0], bb[3]-bb[1]
    sub_h = 0
    fsub = lib.get_font('Mont', 700, sub_size) if sub else None
    if sub:
        sb = d0.textbbox((0,0), sub, font=fsub); sw_,sh_ = sb[2]-sb[0], sb[3]-sb[1]
        sub_h = sh_ + 28
    tag_h = 0
    if tag: tag_h = 90
    cw, ch = max(tw, (sw_ if sub else 0))+160, th+sub_h+tag_h+120
    img,pad = Image.new('RGBA',(cw,ch),(0,0,0,0)), 0
    y = 40
    if panel:
        pnl = Image.new('RGBA',(cw,ch),(0,0,0,0))
        ImageDraw.Draw(pnl).rounded_rectangle([20,10,cw-20,ch-10], radius=28, fill=(20,20,20,175))
        pnl = pnl.filter(ImageFilter.GaussianBlur(0.5)); img.alpha_composite(pnl)
    if tag:
        lib.bold_tag_banner(img, cw, y-14, tag, align='center', size=36); y += tag_h - 14
    lib.gradient_text(img, (cw//2, y), text, f, align='center', stops=lib.BRIGHT_GOLD_STOPS)
    desc = f.getmetrics()[1]  # descender clearance
    y += th + desc + 30
    if sub:
        dr = ImageDraw.Draw(img)
        dr.text((cw//2, y+sh_//2), sub, font=fsub, fill=(255,255,255,255), anchor='mm',
                stroke_width=2, stroke_fill=(0,0,0,180))
    return img

def el_banner(text, size=44):
    f = lib.get_font('Mont', 800, size)
    d0 = ImageDraw.Draw(Image.new('RGBA',(10,10)))
    bb = d0.textbbox((0,0), text, font=f); tw,th = bb[2]-bb[0], bb[3]-bb[1]
    cw,ch = tw+140, th+110
    img = Image.new('RGBA',(cw,ch),(0,0,0,0))
    lib.bold_tag_banner(img, cw, 30, text, align='center', size=size)
    return img

def el_two_tone(white_part, gold_part, size=92, stroke=True, max_w=960):
    f = lib.get_font('Mont', 900, size)
    d_ = ImageDraw.Draw(Image.new('RGBA',(10,10)))
    full_ = white_part + (' ' if white_part else '') + gold_part
    while size > 30:
        bb_ = d_.textbbox((0,0), full_, font=lib.get_font('Mont',900,size))
        if bb_[2]-bb_[0] <= max_w: break
        size -= 4
    f = lib.get_font('Mont', 900, size)
    d0 = ImageDraw.Draw(Image.new('RGBA',(10,10)))
    full = white_part + (' ' if white_part else '') + gold_part
    bb = d0.textbbox((0,0), full, font=f); tw,th = bb[2]-bb[0], bb[3]-bb[1]
    wb = d0.textbbox((0,0), white_part+(' ' if white_part else ''), font=f)
    img = Image.new('RGBA',(tw+120,th+80),(0,0,0,0))
    dr = ImageDraw.Draw(img)
    x0,y0 = 60-bb[0], 40-bb[1]
    if white_part:
        dr.text((x0,y0), white_part, font=f, fill=(255,255,255,255), stroke_width=3, stroke_fill=(0,0,0,200))
    lib.gradient_text(img, (x0+(wb[2]-wb[0]), y0), gold_part, f, stops=lib.BRIGHT_GOLD_STOPS)
    return img

def el_cta():
    cw,ch = 900, 420
    img = Image.new('RGBA',(cw,ch),(0,0,0,0))
    ImageDraw.Draw(img).rounded_rectangle([30,20,cw-30,ch-20], radius=34, fill=(15,15,15,190))
    lib.gradient_rounded_rect(img, [90, 70, cw-90, 210], radius=26, stops=lib.BRIGHT_GOLD_STOPS)
    dr = ImageDraw.Draw(img)
    f1 = lib.get_font('Mont', 900, 74)
    dr.text((cw//2, 140), 'DM  "BRADLEY"', font=f1, fill=(10,10,10,255), anchor='mm')
    f2 = lib.get_font('Mont', 700, 44)
    dr.text((cw//2, 265), 'OR CALL ME DIRECTLY', font=f2, fill=(255,255,255,255), anchor='mm')
    fs = lib.get_script_font(64)
    lib.gradient_text(img, (cw//2, 300), 'number in bio', fs, align='center', stops=lib.BRIGHT_GOLD_STOPS)
    return img

def el_endcard():
    img = Image.new('RGBA',(W,H),(8,8,8,168))
    dr = ImageDraw.Draw(img)
    f1 = lib.get_font('Mont', 900, 92)
    dr.text((W//2, 700), 'GRAEHAM WATTS', font=f1, fill=(255,255,255,255), anchor='mm')
    f2 = lib.get_font('Mont', 600, 40)
    dr.text((W//2, 790), 'R E A L T O R ®   ·   I N T E R O', font=f2, fill=(200,200,200,255), anchor='mm')
    fs = lib.get_script_font(120)
    lib.gradient_text(img, (W//2, 880), '1030 Bradley Way', fs, align='center', stops=lib.BRIGHT_GOLD_STOPS)
    lib.gradient_rounded_rect(img, [W//2-330, 1120, W//2+330, 1245], radius=26, stops=lib.BRIGHT_GOLD_STOPS)
    f3 = lib.get_font('Mont', 900, 60)
    dr = ImageDraw.Draw(img)
    dr.text((W//2, 1182), 'DM  "BRADLEY"', font=f3, fill=(10,10,10,255), anchor='mm')
    f4 = lib.get_font('Mont', 700, 42)
    dr.text((W//2, 1320), 'OR CALL — NUMBER IN BIO', font=f4, fill=(255,255,255,255), anchor='mm')
    return img
