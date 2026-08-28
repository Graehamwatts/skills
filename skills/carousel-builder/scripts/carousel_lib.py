#!/usr/bin/env python3
"""
carousel_lib.py -- Graeham Watts branded listing carousel/static image engine.

This is a PIL-based rendering pipeline (no headless browser needed/available).
It draws directly onto property photos: cover-crops, gradient scrims for text
legibility, gold-on-dark pill badges, the logo with a soft alpha-silhouette
drop shadow, and a library of full card templates (hook, stat, arrow-stat,
split-photo, triptych, CTA).

USAGE: don't call this file directly. Copy scripts/template_build.py, edit the
CONFIG block + card calls for the new property, then run that script. This
file is the shared engine underneath.

Brand constants (colors/fonts) are Graeham Watts' fixed brand and should not
be changed per property. FOOTER_TEXT and CONTACT_LINE ARE meant to be
overridden per property (set them right after importing this module).
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ---------------------------------------------------------------------------
# Paths -- set these via configure() before generating anything.
# ---------------------------------------------------------------------------
SRC = None   # folder of source property photos
OUT = None   # folder to write finished JPGs into

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_THIS_DIR)
MONT = os.path.join(_SKILL_DIR, "assets", "fonts", "Montserrat-var.ttf")
INTER = os.path.join(_SKILL_DIR, "assets", "fonts", "Inter-var.ttf")
LOGO_WHITE_PATH = os.path.join(_SKILL_DIR, "assets", "logo", "logo_white.png")
LOGO_BLACK_PATH = os.path.join(_SKILL_DIR, "assets", "logo", "logo_black.png")


def configure(src, out):
    """Point the engine at this property's source photo folder and output folder."""
    global SRC, OUT
    SRC = src
    OUT = out
    os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------------------
# Brand constants -- Graeham Watts REALTOR. Do not improvise other colors.
# ---------------------------------------------------------------------------
BLACK = (26, 26, 26)        # #1A1A1A
GOLD = (197, 165, 90)        # #C5A55A
WHITE = (255, 255, 255)
CREAM = (245, 239, 220)      # #F5EFDC
DARKGOLD = (168, 139, 61)    # #A88B3D
GRAY = (102, 102, 102)
LIGHTGRAY = (229, 229, 229)
SKYBLUE = (110, 168, 224)    # used only for the blueprint/partition graphic

# "Impact" v3 system -- shiny metallic gold gradient, used everywhere gold
# appears (tag banners, headline accent words, CTA buttons, circular inset
# ring, stat numbers). A flat gold fill reads as yellow/amber and cheap;
# the gradient (dark amber edges brightened just enough to stay legible,
# bright highlight sweep through the middle) reads as "shiny metal."
IMPACT_GOLD = (212, 175, 55)   # flat fallback -- small tag-banner text, etc.
BRIGHT_GOLD_STOPS = [
    (0.0, (196, 156, 55)),
    (0.28, (255, 240, 178)),
    (0.50, (222, 182, 72)),
    (0.72, (255, 240, 178)),
    (1.0, (196, 156, 55)),
]
SCRIPT = os.path.join(_SKILL_DIR, "assets", "fonts", "GreatVibes-Regular.ttf")
_script_font_cache = {}


def get_script_font(size):
    if size in _script_font_cache:
        return _script_font_cache[size]
    f = ImageFont.truetype(SCRIPT, size)
    _script_font_cache[size] = f
    return f

# Per-property text -- OVERRIDE these two lines in your template_build.py
# right after `import carousel_lib as lib`, e.g.:
#   lib.FOOTER_TEXT = "123 MAIN ST . REDWOOD CITY"
#   lib.CONTACT_LINE = "Graeham Watts  .  Compass  .  DRE #01466876"
FOOTER_TEXT = "PROPERTY ADDRESS . CITY"
CONTACT_LINE = "Graeham Watts  .  Compass  .  DRE #01466876"

_font_cache = {}


def get_font(family, weight, size, opsz=32):
    key = (family, weight, size, opsz)
    if key in _font_cache:
        return _font_cache[key]
    if family == "Mont":
        f = ImageFont.truetype(MONT, size)
        f.set_variation_by_axes([weight])
    else:
        f = ImageFont.truetype(INTER, size)
        f.set_variation_by_axes([opsz, weight])
    _font_cache[key] = f
    return f


def cover_crop(path, w, h, focus=("center", "center"), zoom=1.0):
    """zoom > 1.0 crops a smaller window (centered per `focus`) before
    scaling up to (w, h) -- i.e. zooms in around the focus point. Use this
    to "raise" a photo that has too much empty sky/ceiling above the real
    subject: a plain cover-crop on a wide aerial or interior shot often
    keeps the full source height (nothing to trim vertically) when the
    source is much wider than the target frame, so the subject ends up
    small and low in frame. zoom cuts out the excess headroom instead of
    just resizing, so the subject reads bigger and sits higher."""
    im = Image.open(path).convert("RGB")
    src_w, src_h = im.size
    target_ratio = w / h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        new_h = src_h
    else:
        new_w = src_w
        new_h = int(src_w / target_ratio)
    if zoom > 1.0:
        new_w = int(new_w / zoom)
        new_h = int(new_h / zoom)
    fx, fy = focus
    if fx == "center":
        x0 = (src_w - new_w) // 2
    elif fx == "left":
        x0 = 0
    else:
        x0 = src_w - new_w
    if fy == "center":
        y0 = (src_h - new_h) // 2
    elif fy == "top":
        y0 = 0
    elif fy == "bottom":
        y0 = src_h - new_h
    else:
        # numeric bias: 0.0 = top of source, 1.0 = bottom of source.
        # Use this (instead of the "top"/"bottom" strings, which are
        # all-or-nothing) to shift the crop window down by a controlled
        # amount -- e.g. 0.7 crops off some sky/ceiling at the top and
        # reveals more of the subject below, without hard-cutting straight
        # to the bottom edge of the source.
        y0 = int((src_h - new_h) * float(fy))
    x0 = max(0, min(x0, src_w - new_w))
    y0 = max(0, min(y0, src_h - new_h))
    im = im.crop((x0, y0, x0 + new_w, y0 + new_h))
    im = im.resize((w, h), Image.LANCZOS)
    return im


def vgradient(w, h, top_alpha, bottom_alpha, color=(0, 0, 0)):
    grad = Image.new("L", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        a = int(top_alpha + (bottom_alpha - top_alpha) * t)
        grad.putpixel((0, y), a)
    grad = grad.resize((w, h))
    layer = Image.new("RGBA", (w, h), color + (0,))
    layer.putalpha(grad)
    return layer


def hgradient(w, h, left_alpha, right_alpha, color=(0, 0, 0)):
    grad = Image.new("L", (w, 1))
    for x in range(w):
        t = x / max(w - 1, 1)
        a = int(left_alpha + (right_alpha - left_alpha) * t)
        grad.putpixel((x, 0), a)
    grad = grad.resize((w, h))
    layer = Image.new("RGBA", (w, h), color + (0,))
    layer.putalpha(grad)
    return layer


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        test = (cur + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_multiline(draw, xy, lines, font, fill, align="left", line_spacing=1.18, anchor_y="top"):
    x, y = xy
    ascent, descent = font.getmetrics()
    line_h = int((ascent + descent) * line_spacing)
    total_h = line_h * len(lines)
    if anchor_y == "bottom":
        y = y - total_h
    cy = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        if align == "center":
            lx = x - lw / 2
        elif align == "right":
            lx = x - lw
        else:
            lx = x
        draw.text((lx, cy), line, font=font, fill=fill)
        cy += line_h
    return total_h


def draw_multiline_accent(draw, xy, lines, font, base_fill, accent_words=None,
                           gradient_accent=True, accent_fill=None,
                           align="left", line_spacing=1.18):
    """Like draw_multiline(), but specific words within the (already
    line-wrapped) sub/body text render in the accent gold -- gradient by
    default, the same treatment draw_two_tone_headline() gives headlines,
    just scaled down for smaller supporting copy. Use this to call out a
    specific number or phrase inside a sentence without it needing to be
    the whole headline -- e.g. 'over $130K below median' inside a longer
    supporting line. accent_words match case-insensitively and ignore
    trailing punctuation, same rule as draw_two_tone_headline()."""
    base = draw._image
    accent_fill = accent_fill or IMPACT_GOLD
    accent_words = accent_words or []
    accent_set = set(w.upper().rstrip(".,") for w in accent_words)
    x, y = xy
    ascent, descent = font.getmetrics()
    line_h = int((ascent + descent) * line_spacing)
    space_w = draw.textbbox((0, 0), " ", font=font)[2]
    cy = y
    for line in lines:
        words = line.split()
        lb = draw.textbbox((0, 0), line, font=font)
        line_w = lb[2] - lb[0]
        if align == "center":
            cx = x - line_w / 2
        elif align == "right":
            cx = x - line_w
        else:
            cx = x
        for word in words:
            is_accent = word.upper().rstrip(".,") in accent_set
            wb = draw.textbbox((0, 0), word, font=font)
            ww = wb[2] - wb[0]
            if is_accent:
                if gradient_accent:
                    gradient_text(base, (cx, cy), word, font, align="left", stops=BRIGHT_GOLD_STOPS)
                else:
                    draw.text((cx, cy), word, font=font, fill=accent_fill)
            else:
                draw.text((cx, cy), word, font=font, fill=base_fill)
            cx += ww + space_w
        cy += line_h
    return line_h * len(lines)


def gold_rule(draw, canvas_w, y, margin=72, width_px=110, thickness=4, center=False):
    if center:
        x0 = (canvas_w - width_px) / 2
    else:
        x0 = margin
    draw.rectangle([x0, y, x0 + width_px, y + thickness], fill=GOLD)
    return y + thickness + 26


def card_number_badge(base, canvas_w, idx, total, margin=56):
    """NOTE: uses anchor='mm' for true vertical centering inside the pill.
    PIL's textbbox top includes ascender space, so a naive y+pad-const offset
    looks off-center. Always center pill/badge text this way, not manually."""
    draw = ImageDraw.Draw(base)
    text = f"{idx}/{total}"
    f = get_font("Mont", 700, 26)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 22, 12
    w = tw + pad_x * 2
    h = th + pad_y * 2 + 6
    x0 = canvas_w - margin - w
    y0 = margin
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=h / 2, fill=(26, 26, 26, 200))
    draw.text((x0 + w / 2, y0 + h / 2), text, font=f, fill=GOLD, anchor="mm")


def swipe_cue(base, w, h, margin=56):
    """Small 'SWIPE ->' pill, bottom-right. Place on every non-final card in a
    carousel (skip the CTA/last card) -- an explicit affordance nudging people
    to keep going instead of dropping off after 2-3 slides."""
    draw = ImageDraw.Draw(base)
    text = "SWIPE"
    arrow = "\u2192"
    f = get_font("Mont", 700, 22)
    f_arrow = get_font("Mont", 700, 24)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ab = draw.textbbox((0, 0), arrow, font=f_arrow)
    aw, ah = ab[2] - ab[0], ab[3] - ab[1]
    gap = 10
    pad_x, pad_y = 18, 10
    pw = tw + gap + aw + pad_x * 2
    ph = max(th, ah) + pad_y * 2 + 4
    x0 = w - margin - pw
    y0 = h - margin - ph
    draw.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=ph / 2, fill=(12, 12, 12, 190))
    cy = y0 + ph / 2
    draw.text((x0 + pad_x, cy), text, font=f, fill=(230, 230, 230), anchor="lm")
    draw.text((x0 + pad_x + tw + gap, cy), arrow, font=f_arrow, fill=GOLD, anchor="lm")


def takeover_stat_card(w, h, eyebrow_text, stat_text, note_text, headline_text, sub_text, bg=None):
    """Solid-color, no-photo slide -- a hard visual break from the photo cards
    around it. Photo-only carousels start to blur together after 3-4 slides
    that all use the same dimmed-photo-plus-text-block composition; a flat
    brand-black takeover slide with one giant number resets attention and
    reads as a deliberate 'pay attention to this number' beat rather than
    just another room shot."""
    bg = bg or BLACK
    base = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(base)
    margin = 76
    top_y = 140
    eyebrow_pill(base, w, top_y, eyebrow_text, align="center", size=44)
    draw = ImageDraw.Draw(base)

    cy = h * 0.44
    f_stat = get_font("Mont", 800, 130)
    draw.text((w / 2, cy), stat_text, font=f_stat, fill=GOLD, anchor="mm")

    if note_text:
        f_note = get_font("Inter", 500, 30, opsz=28)
        draw.text((w / 2, cy + 100), note_text, font=f_note, fill=(210, 210, 210), anchor="mm")

    content_block2(base, w, h, margin, None, headline_text, sub_text,
                    headline_size=48, sub_size=28, align="center", bottom_pad=110,
                    sub_color=(210, 210, 210))
    footer_wordmark2(base, w, h, margin=margin)
    return base


def apply_grain(im, amount=6):
    """Subtle film-grain noise overlay -- keeps a bright, ungraded photo from
    looking flat/digital. Amount is the max per-pixel luminance jitter."""
    import random
    w, h = im.size
    noise = Image.effect_noise((w, h), amount * 4).convert("L")
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(im.convert("RGB"), noise_rgb, 0.05).convert("RGB")


def apply_duotone_grade(im, shadow=(20, 24, 34), highlight=(255, 246, 214)):
    """Optional duotone color grade (maps luminance to a two-color ramp).
    Kept for backward compatibility / experimentation -- the 'impact' card
    templates all call base_photo_card with grade=False because a graded
    photo tested as barely perceptible and the brighter, ungraded photo
    plus a bold text treatment tested much better."""
    gray = im.convert("L")
    lut_r = [int(shadow[0] + (highlight[0] - shadow[0]) * i / 255) for i in range(256)]
    lut_g = [int(shadow[1] + (highlight[1] - shadow[1]) * i / 255) for i in range(256)]
    lut_b = [int(shadow[2] + (highlight[2] - shadow[2]) * i / 255) for i in range(256)]
    r = gray.point(lut_r)
    g = gray.point(lut_g)
    b = gray.point(lut_b)
    return Image.merge("RGB", (r, g, b))


def base_photo_card(photo_path, w, h, focus=("center", "center"), dim=0.0, blur=0,
                     grade=False, grain=False, zoom=1.0, lift_px=0):
    im = cover_crop(os.path.join(SRC, photo_path), w, h, focus, zoom=zoom)
    if lift_px:
        # Pure vertical SHIFT, not a re-crop/zoom -- same photo, same scale,
        # just slid up so more of its lower portion is visible and the top
        # portion runs off-canvas. The gap this opens at the very bottom is
        # fine to leave black since floor_fade_scrim's solid floor covers
        # that band anyway. Different from zoom: zoom changes framing/scale,
        # this only changes position.
        shifted = Image.new(im.mode, (w, h), (0, 0, 0) if im.mode == "RGB" else (0, 0, 0, 255))
        shifted.paste(im, (0, -lift_px))
        im = shifted
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if grade:
        im = apply_duotone_grade(im)
    if grain:
        im = apply_grain(im)
    if dim:
        im = ImageEnhance.Brightness(im).enhance(1 - dim)
    return im.convert("RGBA")


def scrim_bottom(base, h_frac=0.5, max_alpha=210):
    w, h = base.size
    gh = int(h * h_frac)
    grad = vgradient(w, gh, 0, max_alpha)
    base.alpha_composite(grad, (0, h - gh))


def scrim_top(base, h_frac=0.28, max_alpha=170):
    w, h = base.size
    gh = int(h * h_frac)
    grad = vgradient(w, gh, max_alpha, 0)
    base.alpha_composite(grad, (0, 0))


def full_scrim(base, alpha=140):
    w, h = base.size
    layer = Image.new("RGBA", (w, h), BLACK + (alpha,))
    base.alpha_composite(layer)


def save(base, name):
    base.convert("RGB").save(os.path.join(OUT, name), quality=94)
    print("saved", name)


def backdrop_panel(base, box, alpha=120, radius=28):
    """Semi-opaque black rounded panel behind big stat numbers, so gold text
    never blends into a bright/busy photo background."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=(8, 8, 8, alpha))
    base.alpha_composite(layer)


def split_vertical(photo_top, photo_bottom, w, h, focus_top=("center", "center"), focus_bottom=("center", "center")):
    """Stack two photos top/bottom, equal halves, thin gold divider."""
    base = Image.new("RGBA", (w, h), BLACK + (255,))
    half = h // 2
    top = cover_crop(os.path.join(SRC, photo_top), w, half, focus_top).convert("RGBA")
    bot = cover_crop(os.path.join(SRC, photo_bottom), w, h - half, focus_bottom).convert("RGBA")
    base.paste(top, (0, 0))
    base.paste(bot, (0, half))
    d = ImageDraw.Draw(base)
    d.rectangle([0, half - 3, w, half + 3], fill=GOLD)
    return base


def split_horizontal(photo_left, photo_right, w, h, focus_left=("center", "center"), focus_right=("center", "center")):
    base = Image.new("RGBA", (w, h), BLACK + (255,))
    half = w // 2
    left = cover_crop(os.path.join(SRC, photo_left), half, h, focus_left).convert("RGBA")
    right = cover_crop(os.path.join(SRC, photo_right), w - half, h, focus_right).convert("RGBA")
    base.paste(left, (0, 0))
    base.paste(right, (half, 0))
    d = ImageDraw.Draw(base)
    d.rectangle([half - 3, 0, half + 3, h], fill=GOLD)
    return base


def dim_layer(base, box, alpha=120):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", (x1 - x0, y1 - y0), BLACK + (alpha,))
    base.alpha_composite(layer, (x0, y0))


def label_chip(base, xy, text, align="left", fill=BLACK, text_color=GOLD, size=22):
    draw = ImageDraw.Draw(base)
    f = get_font("Mont", 700, size)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 20, 11
    w = tw + pad_x * 2
    h = th + pad_y * 2 + 4
    x, y = xy
    if align == "center":
        x = x - w / 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h / 2, fill=fill + (215,) if len(fill) == 3 else fill)
    draw.text((x + w / 2, y + h / 2), text, font=f, fill=text_color, anchor="mm")
    return w, h


def triptych(photo1, photo2, w, h, focus1=("center", "center"), focus2=("center", "center")):
    """3 vignettes: photo1, photo2, then a graphic panel the caller draws into.
    Returns (base, third) where `third` = height of each of the top two bands."""
    base = Image.new("RGBA", (w, h), BLACK + (255,))
    third = h // 3
    top = cover_crop(os.path.join(SRC, photo1), w, third, focus1).convert("RGBA")
    mid = cover_crop(os.path.join(SRC, photo2), w, third, focus2).convert("RGBA")
    base.paste(top, (0, 0))
    base.paste(mid, (0, third))
    d = ImageDraw.Draw(base)
    d.rectangle([0, third - 2, w, third + 2], fill=GOLD)
    d.rectangle([0, 2 * third - 2, w, 2 * third + 2], fill=GOLD)
    return base, third


LOGO_WHITE = None
LOGO_BLACK = None


def _ensure_logos_loaded():
    global LOGO_WHITE, LOGO_BLACK
    if LOGO_WHITE is None:
        LOGO_WHITE = Image.open(LOGO_WHITE_PATH).convert("RGBA")
    if LOGO_BLACK is None:
        LOGO_BLACK = Image.open(LOGO_BLACK_PATH).convert("RGBA")


def place_logo(base, w, target_w=270, top_margin=46, logo=None, plate=True):
    """Places the wordmark top-center with a tight drop-shadow hugging the
    letterforms (NOT a rectangular badge/border -- that read as a "muddy
    smudge" in testing). Technique: extract the logo's own alpha channel,
    render it as a blurred black silhouette, composite that twice underneath
    the sharp logo for a soft halo that's just enough contrast to read on any
    photo without ever looking boxy."""
    _ensure_logos_loaded()
    logo = logo if logo is not None else LOGO_WHITE
    lw, lh = logo.size
    scale = target_w / lw
    new_size = (int(lw * scale), int(lh * scale))
    logo_r = logo.resize(new_size, Image.LANCZOS)
    x = int((w - new_size[0]) / 2)
    y = top_margin
    if plate:
        alpha = logo_r.split()[-1]
        silhouette = Image.new("RGBA", logo_r.size, (0, 0, 0, 255))
        silhouette.putalpha(alpha)
        pad = 40
        canvas = Image.new("RGBA", (logo_r.size[0] + pad * 2, logo_r.size[1] + pad * 2), (0, 0, 0, 0))
        canvas.alpha_composite(silhouette, (pad, pad))
        canvas = canvas.filter(ImageFilter.GaussianBlur(9))
        base.alpha_composite(canvas, (x - pad, y - pad))
        base.alpha_composite(canvas, (x - pad, y - pad))
    base.alpha_composite(logo_r, (x, y))
    return y + new_size[1]


def eyebrow_pill(base, w, y, text, align="left", margin=76, size=26):
    """Gold-on-dark-pill eyebrow label -- guarantees contrast regardless of
    the photo behind it. Never render eyebrow/tag text as bare gold-on-photo;
    it disappears against bright or busy backgrounds."""
    draw = ImageDraw.Draw(base)
    f = get_font("Mont", 700, size)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 24, 15
    pw, ph = tw + pad_x * 2, th + pad_y * 2 + 4
    if align == "center":
        x0 = w / 2 - pw / 2
    else:
        x0 = margin
    draw.rounded_rectangle([x0, y, x0 + pw, y + ph], radius=ph / 2, fill=(12, 12, 12, 205))
    draw.text((x0 + pw / 2, y + ph / 2), text, font=f, fill=GOLD, anchor="mm")
    return y + ph + 22


# ===================== METALLIC / GRADIENT GOLD =====================
def _metallic_gradient(w, h, stops=None):
    """Horizontal gradient simulating a brushed-metal gold sheen: dark amber
    edges with a bright highlight band sweeping through the middle."""
    if stops is None:
        stops = BRIGHT_GOLD_STOPS
    grad = Image.new("RGB", (max(w, 1), 1))
    for x in range(grad.width):
        t = x / max(grad.width - 1, 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = (t - t0) / max(t1 - t0, 1e-6)
                r = int(c0[0] + (c1[0] - c0[0]) * f)
                g = int(c0[1] + (c1[1] - c0[1]) * f)
                b = int(c0[2] + (c1[2] - c0[2]) * f)
                grad.putpixel((x, 0), (r, g, b))
                break
    return grad.resize((max(w, 1), max(h, 1)))


def _gradient_fill_mask(base, mask, xy, stops=None):
    """Fills an arbitrary L-mode mask with the metallic gradient and
    composites it onto base at xy (top-left). Shared by gradient_text,
    gradient_rounded_rect, and gradient_ring."""
    w, h = mask.size
    grad = _metallic_gradient(w, h, stops=stops)
    grad_rgba = Image.new("RGBA", (w, h))
    grad_rgba.paste(grad, (0, 0))
    grad_rgba.putalpha(mask)
    base.alpha_composite(grad_rgba, (int(xy[0]), int(xy[1])))


def gradient_text(base, xy, text, font, align="left", stops=None):
    """Draws text filled with the metallic gold gradient instead of a flat
    color -- use for words/labels that should read as 'shiny gold'. Position
    semantics match plain draw.text(xy, text, font) at its default anchor
    ("la"): xy is the same origin you'd pass to draw.text for this same word,
    NOT the tight ink-box top-left -- this keeps gradient words sitting on
    the exact same baseline as flat-color words drawn on the same line."""
    draw = ImageDraw.Draw(base)
    bbox = draw.textbbox((0, 0), text, font=font)
    x0, y0, x1, y1 = bbox
    tw, th = max(x1 - x0, 1), max(y1 - y0, 1)
    mask_img = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask_img).text((-x0, -y0), text, font=font, fill=255)
    tx, ty = xy
    if align == "center":
        tx = tx - (x1 - x0) / 2 - x0
    elif align == "right":
        tx = tx - (x1 - x0) - x0
    _gradient_fill_mask(base, mask_img, (tx + x0, ty + y0), stops=stops)
    return tw, th


def gradient_rounded_rect(base, box, radius, stops=None):
    """Rounded rectangle filled with the metallic gold gradient (for CTA
    buttons / tag banners that should read as shiny gold, not flat gold)."""
    x0, y0, x1, y1 = box
    w, h = int(x1 - x0), int(y1 - y0)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    _gradient_fill_mask(base, mask, (x0, y0), stops=stops)


def gradient_ring(base, center, outer_d, ring_width, stops=None):
    """A ring (annulus) filled with the metallic gradient -- used for the
    circular photo inset's border so it matches the shiny-gold system
    instead of a flat-gold ring."""
    pad = 4
    canvas_d = outer_d + pad * 2
    mask = Image.new("L", (canvas_d, canvas_d), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([pad, pad, pad + outer_d, pad + outer_d], fill=255)
    inner = outer_d - ring_width * 2
    inset = pad + ring_width
    md.ellipse([inset, inset, inset + inner, inset + inner], fill=0)
    x = int(center[0] - canvas_d / 2)
    y = int(center[1] - canvas_d / 2)
    _gradient_fill_mask(base, mask, (x, y), stops=stops)


def bold_tag_banner(base, w, y, text, align="left", margin=76, size=40,
                     fill=IMPACT_GOLD, gradient=True):
    """Bold rectangular tag banner (e.g. 'JUST LISTED') -- a hard-edged,
    high-contrast block rather than eyebrow_pill's soft rounded pill. Filled
    with the shiny gold gradient by default; black bold text sits directly
    on top since gold-on-black-text reads as premium and stays legible
    against any photo (the banner itself is always opaque)."""
    draw = ImageDraw.Draw(base)
    f = get_font("Mont", 800, size)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 30, 16
    pw, ph = tw + pad_x * 2, th + pad_y * 2 + 4
    x0 = margin if align == "left" else (w - pw) / 2
    y0 = y
    if gradient:
        gradient_rounded_rect(base, [x0, y0, x0 + pw, y0 + ph], radius=10)
    else:
        draw.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=10, fill=fill)
    draw = ImageDraw.Draw(base)
    draw.text((x0 + pw / 2, y0 + ph / 2), text, font=f, fill=BLACK, anchor="mm")
    return y0 + ph + 26


def draw_two_tone_headline(draw, xy, text, accent_words, font, base_fill=WHITE,
                            accent_fill=IMPACT_GOLD, max_width=None, align="left",
                            line_spacing=1.14, gradient_accent=True):
    """All-caps headline where specific words render in the accent gold
    (gradient by default) and the rest render in flat base_fill (white).
    accent_words should match the exact (already-uppercased) substrings in
    text. Wraps to max_width like wrap_text, but word-by-word so each word
    can carry its own color."""
    base = draw._image
    x, y = xy
    words = text.split()
    accent_set = set(w.upper() for w in accent_words)
    space_w = draw.textbbox((0, 0), " ", font=font)[2]
    asc, desc = font.getmetrics()
    line_h = int((asc + desc) * line_spacing)

    lines = []
    cur = []
    cur_w = 0
    for word in words:
        wb = draw.textbbox((0, 0), word, font=font)
        ww = wb[2] - wb[0]
        add_w = ww if not cur else ww + space_w
        if max_width and cur and cur_w + add_w > max_width:
            lines.append(cur)
            cur = [word]
            cur_w = ww
        else:
            cur.append(word)
            cur_w += add_w
    if cur:
        lines.append(cur)

    cy = y
    for line_words in lines:
        line_text = " ".join(line_words)
        lb = draw.textbbox((0, 0), line_text, font=font)
        line_w = lb[2] - lb[0]
        if align == "center":
            cx = x - line_w / 2
        elif align == "right":
            cx = x - line_w
        else:
            cx = x
        for word in line_words:
            is_accent = word.upper().rstrip(".,") in accent_set or word.upper() in accent_set
            wb = draw.textbbox((0, 0), word, font=font)
            ww = wb[2] - wb[0]
            if is_accent:
                if gradient_accent:
                    gradient_text(base, (cx, cy), word, font, align="left")
                else:
                    draw.text((cx, cy), word, font=font, fill=accent_fill)
            else:
                draw.text((cx, cy), word, font=font, fill=base_fill)
            cx += ww + space_w
        cy += line_h


def circular_inset(base, photo_path, center, diameter, focus=("center", "center"),
                    border_color=IMPACT_GOLD, ring_width=8, gradient=True):
    """A second photo peeking through a gold-ringed circle -- used on hook
    cards to preview a second room without a second full card."""
    im = cover_crop(os.path.join(SRC, photo_path), diameter, diameter, focus).convert("RGBA")
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, diameter, diameter], fill=255)
    x0 = int(center[0] - diameter / 2)
    y0 = int(center[1] - diameter / 2)
    base.paste(im, (x0, y0), mask)
    if gradient:
        gradient_ring(base, center, diameter, ring_width)
    else:
        draw = ImageDraw.Draw(base)
        draw.ellipse([x0, y0, x0 + diameter, y0 + diameter], outline=border_color, width=ring_width)


def connector_arrow(base, p0, p1, color=IMPACT_GOLD, width=7, curve=0.22):
    """Curved gold line connecting the main photo to the circular inset,
    with a small arrowhead at the inset end -- a visual 'peek inside' cue."""
    import math
    x0, y0 = p0
    x1, y1 = p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    dist = max((dx ** 2 + dy ** 2) ** 0.5, 1)
    nx, ny = -dy / dist, dx / dist
    cx, cy = mx + nx * dist * curve, my + ny * dist * curve

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    steps = 40
    pts = []
    for i in range(steps + 1):
        t = i / steps
        bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
        by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
        pts.append((bx, by))
    ld.line(pts, fill=color + (255,), width=width, joint="curve")
    base.alpha_composite(layer)


def content_block2(base, w, h, margin, eyebrow_text, headline_text, sub_text,
                    headline_size=66, sub_size=30, align="left", bottom_pad=110,
                    headline_weight=800, max_w=None, sub_color=WHITE):
    """Bottom-anchored headline/subhead block with an optional eyebrow pill."""
    draw = ImageDraw.Draw(base)
    f_head = get_font("Mont", headline_weight, headline_size)
    f_sub = get_font("Inter", 500, sub_size, opsz=32)
    mw = max_w if max_w else (w - 2 * margin)

    head_lines = wrap_text(draw, headline_text, f_head, mw) if headline_text else []
    sub_lines = wrap_text(draw, sub_text, f_sub, mw) if sub_text else []

    asc, desc = f_head.getmetrics()
    head_line_h = int((asc + desc) * 1.14)
    asc2, desc2 = f_sub.getmetrics()
    sub_line_h = int((asc2 + desc2) * 1.3)

    eyebrow_h = (26 + 13 * 2 + 4 + 22) if eyebrow_text else 0
    head_h = head_line_h * len(head_lines)
    gap1 = 20 if head_lines and sub_lines else 0
    sub_h = sub_line_h * len(sub_lines)

    total = eyebrow_h + head_h + gap1 + sub_h
    y = h - bottom_pad - total
    x = w / 2 if align == "center" else margin

    if eyebrow_text:
        y = eyebrow_pill(base, w, y, eyebrow_text, align=align, margin=margin)
        draw = ImageDraw.Draw(base)

    if head_lines:
        draw_multiline(draw, (x, y), head_lines, f_head, WHITE, align=align, line_spacing=1.14)
        y += head_h + gap1
    if sub_lines:
        draw_multiline(draw, (x, y), sub_lines, f_sub, sub_color, align=align, line_spacing=1.3)
        y += sub_h
    return y


def footer_wordmark2(base, canvas_w, canvas_h, margin=76):
    """Footer text (property address . city) with a subtle dark backing strip
    for guaranteed contrast. Reads FOOTER_TEXT -- set it per property."""
    draw = ImageDraw.Draw(base)
    f = get_font("Mont", 600, 24)
    text = FOOTER_TEXT
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    y = canvas_h - margin - 24
    pad_x, pad_y = 14, 9
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([margin - pad_x, y - pad_y, margin + tw + pad_x, y + th + pad_y], radius=8, fill=(10, 10, 10, 140))
    base.alpha_composite(layer)
    box_cy = (y - pad_y + y + th + pad_y) / 2
    draw.text((margin + tw / 2, box_cy), text, font=f, fill=GOLD, anchor="mm")


def big_cta_button(base, w, text, cy, sub_contact=None):
    """Larger, centered CTA button for closer/CTA cards."""
    draw = ImageDraw.Draw(base)
    f = get_font("Mont", 800, 50)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 92, 46
    bw, bh = tw + pad_x * 2, th + pad_y * 2
    x0 = w / 2 - bw / 2
    y0 = cy - bh / 2
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x0, y0 + 10, x0 + bw, y0 + bh + 10], radius=bh / 2, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    base.alpha_composite(shadow)
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=bh / 2, fill=GOLD)
    draw.text((x0 + bw / 2, y0 + bh / 2), text, font=f, fill=BLACK, anchor="mm")
    y2 = y0 + bh + 34
    if sub_contact:
        f2 = get_font("Inter", 600, 26, opsz=26)
        b2 = draw.textbbox((0, 0), sub_contact, font=f2)
        draw.text((w / 2 - (b2[2] - b2[0]) / 2, y2), sub_contact, font=f2, fill=(230, 230, 230))
        y2 += 40
    return y2


def partition_overlay(base, w, h, x_frac=0.52, y0_frac=0.30, y1_frac=0.82):
    """Dashed light-blue vertical partition line with tick marks -- simulates
    a conversion/blueprint diagram over a room photo."""
    draw = ImageDraw.Draw(base)
    x = int(w * x_frac)
    y0, y1 = int(h * y0_frac), int(h * y1_frac)
    dash, gap = 22, 14
    y = y0
    while y < y1:
        y2 = min(y + dash, y1)
        draw.line([(x, y), (x, y2)], fill=SKYBLUE + (255,), width=6)
        y = y2 + gap
    for yy in (y0, y1):
        draw.line([(x - 18, yy), (x + 18, yy)], fill=SKYBLUE + (255,), width=6)
    f = get_font("Inter", 600, 24, opsz=24)
    label = "NEW WALL"
    lb = draw.textbbox((0, 0), label, font=f)
    lx = x - (lb[2] - lb[0]) / 2
    draw.rounded_rectangle([lx - 14, y0 - 52, lx + (lb[2] - lb[0]) + 14, y0 - 14], radius=14, fill=(255, 255, 255, 235))
    draw.text((lx, y0 - 48), label, font=f, fill=(20, 60, 110))


# ---------------------------------------------------------------------------
# Full card templates
# ---------------------------------------------------------------------------

def simple_card2(photo, w, h, focus, eyebrow_text, headline, subtext, filename,
                  idx=None, total=None, headline_size=64, sub_size=30, dim=0.05,
                  scrim_frac=0.56, scrim_alpha=235, align="left", margin=76, logo=True):
    """A single full-bleed photo with a bottom scrim and a headline/sub block.
    Used for hook cards and plain photo+copy cards."""
    base = base_photo_card(photo, w, h, focus=focus, dim=dim)
    scrim_bottom(base, h_frac=scrim_frac, max_alpha=scrim_alpha)
    if logo:
        place_logo(base, w)
    content_block2(base, w, h, margin, eyebrow_text, headline, subtext,
                    headline_size=headline_size, sub_size=sub_size, align=align)
    if idx:
        card_number_badge(base, w, idx, total)
        if idx < total:
            swipe_cue(base, w, h)
    footer_wordmark2(base, w, h, margin=margin)
    save(base, filename)
    return base


def stat_card(base_photo, w, h, eyebrow_text, stat_text, note_text, headline_text, sub_text,
              dim=0.35, blur=6, logo=True):
    """Single big number (e.g. rent estimate) over a dimmed/blurred photo,
    with a backdrop panel behind the number so gold never blends into the photo.
    Pass base_photo=None for a solid brand-black background instead (visual
    break card -- see takeover_stat_card for the fully solid variant)."""
    if base_photo:
        base = base_photo_card(base_photo, w, h, dim=dim, blur=blur)
        full_scrim(base, alpha=125)
    else:
        base = Image.new("RGBA", (w, h), BLACK + (255,))
    margin = 76
    top_y = 130
    if logo:
        logo_bottom = place_logo(base, w)
        top_y = logo_bottom + 96
    y = eyebrow_pill(base, w, top_y, eyebrow_text, align="center", size=44)
    draw = ImageDraw.Draw(base)

    cy = h * 0.52
    backdrop_panel(base, (60, cy - 165, w - 60, cy + 150), alpha=115)
    draw = ImageDraw.Draw(base)
    label_chip(base, (w / 2, cy - 140), "ESTIMATED", align="center")

    f_stat = get_font("Mont", 800, 100)
    sbbox = draw.textbbox((0, 0), stat_text, font=f_stat)
    draw.text((w / 2 - (sbbox[2] - sbbox[0]) / 2, cy - 68), stat_text, font=f_stat, fill=GOLD)

    f_note = get_font("Inter", 500, 29, opsz=28)
    nbbox = draw.textbbox((0, 0), note_text, font=f_note)
    draw.text((w / 2 - (nbbox[2] - nbbox[0]) / 2, cy + 58), note_text, font=f_note, fill=(225, 225, 225))

    content_block2(base, w, h, margin, None, headline_text, sub_text,
                    headline_size=48, sub_size=28, align="center", bottom_pad=110)
    footer_wordmark2(base, w, h, margin=margin)
    return base


def arrow_stat_card(base_photo, w, h, eyebrow_text, from_text, to_text, note_text, callout_text,
                     headline_text, sub_text, dim=0.35, blur=8, logo=True):
    """'Before -> after' numbers card, e.g. current rent -> converted rent.
    Pass base_photo=None for a solid brand-black background instead."""
    if base_photo:
        base = base_photo_card(base_photo, w, h, dim=dim, blur=blur)
        full_scrim(base, alpha=100)
    else:
        base = Image.new("RGBA", (w, h), BLACK + (255,))
    top_y = 130
    if logo:
        logo_bottom = place_logo(base, w)
        top_y = logo_bottom + 96
    y = eyebrow_pill(base, w, top_y, eyebrow_text, align="center", size=44)
    draw = ImageDraw.Draw(base)

    cy = h * 0.51
    backdrop_panel(base, (30, cy - 175, w - 30, cy + 150), alpha=115)
    draw = ImageDraw.Draw(base)
    label_chip(base, (w / 2, cy - 150), "ESTIMATED", align="center")

    f_from = get_font("Mont", 500, 52)
    f_arrow = get_font("Mont", 400, 52)
    f_to = get_font("Mont", 800, 92)
    bbox_from = draw.textbbox((0, 0), from_text, font=f_from)
    tw_from = bbox_from[2] - bbox_from[0]
    bbox_arrow = draw.textbbox((0, 0), "   →   ", font=f_arrow)
    tw_arrow = bbox_arrow[2] - bbox_arrow[0]
    bbox_to = draw.textbbox((0, 0), to_text, font=f_to)
    tw_to = bbox_to[2] - bbox_to[0]
    th_to = bbox_to[3] - bbox_to[1]
    total_w = tw_from + tw_arrow + tw_to
    x0 = w / 2 - total_w / 2
    y_base = cy - 58
    draw.text((x0, y_base + (th_to - 52)), from_text, font=f_from, fill=(215, 215, 215))
    draw.text((x0 + tw_from, y_base + (th_to - 52) - 4), "   →   ", font=f_arrow, fill=GOLD)
    draw.text((x0 + tw_from + tw_arrow, y_base), to_text, font=f_to, fill=WHITE)

    f_note = get_font("Inter", 500, 28, opsz=28)
    bboxn = draw.textbbox((0, 0), note_text, font=f_note)
    draw.text((w / 2 - (bboxn[2] - bboxn[0]) / 2, cy + 62), note_text, font=f_note, fill=(215, 215, 215))

    if callout_text:
        label_chip(base, (w / 2, cy + 118), callout_text, align="center", fill=GOLD, text_color=BLACK, size=28)

    content_block2(base, w, h, 76, None, headline_text, sub_text,
                    headline_size=48, sub_size=28, align="center", bottom_pad=120)
    footer_wordmark2(base, w, h, margin=76)
    return base


def cta_card(photo, w, h, focus, eyebrow_text, headline, subtext, filename, idx, total,
             dim=0.25, logo=True, button_text="SCHEDULE A TOUR", save_share_text=None):
    """Closing CTA card: logo -> eyebrow tag -> big gold button -> supporting
    sentence -> contact line, all stacked with a tight fixed gap so the whole
    block moves together instead of drifting apart at different sizes."""
    base = base_photo_card(photo, w, h, focus=focus, dim=dim)
    full_scrim(base, alpha=150)
    top_y = 140
    if logo:
        logo_bottom = place_logo(base, w, target_w=430)
        top_y = logo_bottom + 140
    draw = ImageDraw.Draw(base)
    y = eyebrow_pill(base, w, top_y, eyebrow_text, align="center", size=56)
    draw = ImageDraw.Draw(base)

    f_btn = get_font("Mont", 800, 50)
    btn_bbox = draw.textbbox((0, 0), button_text, font=f_btn)
    btn_h = (btn_bbox[3] - btn_bbox[1]) + 46 * 2
    button_cy = y + 46 + btn_h / 2
    btn_bottom = big_cta_button(base, w, button_text, button_cy, sub_contact=None)
    draw = ImageDraw.Draw(base)

    f_sub = get_font("Inter", 600, 36, opsz=32)
    sub_lines = wrap_text(draw, subtext, f_sub, w - 140)
    sh = draw_multiline(draw, (w / 2, btn_bottom + 8), sub_lines, f_sub, WHITE, align="center", line_spacing=1.3)

    y_contact = btn_bottom + 8 + sh + 34
    f_contact = get_font("Inter", 600, 26, opsz=26)
    contact = CONTACT_LINE
    cb = draw.textbbox((0, 0), contact, font=f_contact)
    contact_h = cb[3] - cb[1]
    draw.text((w / 2 - (cb[2] - cb[0]) / 2, y_contact), contact, font=f_contact, fill=(225, 225, 225))

    if save_share_text:
        f_ss = get_font("Mont", 700, 28)
        y_ss = y_contact + contact_h + 32
        draw.text((w / 2, y_ss), save_share_text, font=f_ss, fill=GOLD, anchor="mm")

    card_number_badge(base, w, idx, total)
    save(base, filename)
    return base


# ===================== "IMPACT" CARD SYSTEM (v3, default) =====================
def _impact_metrics(draw, w, margin, headline_text, sub_text, headline_size, sub_size):
    f_head = get_font("Mont", 800, headline_size)
    f_sub = get_font("Inter", 500, sub_size, opsz=32)
    mw = w - 2 * margin
    head_lines_probe = wrap_text(draw, headline_text, f_head, mw)
    asc, desc = f_head.getmetrics()
    head_line_h = int((asc + desc) * 1.14)
    asc2, desc2 = f_sub.getmetrics()
    sub_lines = wrap_text(draw, sub_text, f_sub, mw)
    sub_line_h = int((asc2 + desc2) * 1.3)
    tag_h = 34 + 16 * 2 + 4 + 26
    head_h = head_line_h * len(head_lines_probe)
    sub_h = sub_line_h * len(sub_lines)
    return f_head, f_sub, mw, head_lines_probe, sub_lines, head_h, sub_h, tag_h


def impact_hook_card(main_photo, inset_photo, w, h, tag_text, headline_text, accent_words,
                      sub_text, filename, idx=None, total=None, headline_size=68, sub_size=30,
                      focus_main=("center", "center"), focus_inset=("center", "center"),
                      inset_diameter=280, inset_pos=("right", 0.30), margin=76, upper=True,
                      sub_accent_words=None, zoom_main=1.0, lift_main=0, show_connector=True):
    """Hook-card v3: full-bleed BRIGHT main photo (no dim, no duotone grade --
    the photo itself should stay vivid/natural, like a real listing photo, not
    toned down) + bold banner tag + two-tone headline (accent_words in a
    brighter accent gold) + one circular collage inset connected by an accent
    arrow. Uses the LOCKED floor_fade_scrim() bottom treatment (flat black
    floor ~1/3 of the card, gentle gradient fade above it) -- confirmed final
    after client review, same as news_fact_card(); do not swap this back to a
    plain linear scrim_bottom(). zoom_main > 1.0 crops in tighter around
    focus_main before the black floor is added, so a photo with a lot of
    empty sky/headroom doesn't end up looking small and buried under the
    floor -- use it to 'raise' the subject when needed."""
    base = base_photo_card(main_photo, w, h, focus=focus_main, dim=0.0, grade=False, grain=True,
                            zoom=zoom_main, lift_px=lift_main)
    floor_fade_scrim(base, floor_frac=0.33, fade_frac=0.35, max_alpha=255, power=1.5)

    if upper:
        headline_text = headline_text.upper()
        tag_text = tag_text.upper()

    draw = ImageDraw.Draw(base)
    f_head, f_sub, mw, head_lines_probe, sub_lines, head_h, sub_h, tag_h = _impact_metrics(
        draw, w, margin, headline_text, sub_text, headline_size, sub_size)

    bottom_pad = 110
    total_block = tag_h + head_h + 20 + sub_h
    y = h - bottom_pad - total_block

    ix = w - 76 - inset_diameter // 2 if inset_pos[0] == "right" else 76 + inset_diameter // 2
    iy = int(h * inset_pos[1]) + inset_diameter // 2 + 40
    main_anchor = (w * 0.30, iy)
    if show_connector:
        connector_arrow(base, main_anchor, (ix, iy), color=IMPACT_GOLD, width=7, curve=0.22)
    circular_inset(base, inset_photo, (ix, iy), inset_diameter, focus=focus_inset, border_color=IMPACT_GOLD)

    place_logo(base, w)

    y = bold_tag_banner(base, w, y, tag_text, align="left", margin=margin, fill=IMPACT_GOLD)
    draw = ImageDraw.Draw(base)
    draw_two_tone_headline(draw, (margin, y), headline_text, accent_words, f_head,
                            base_fill=WHITE, accent_fill=IMPACT_GOLD, max_width=mw, align="left")
    y += head_h + 20
    if sub_accent_words:
        draw_multiline_accent(draw, (margin, y), sub_lines, f_sub, WHITE,
                               accent_words=sub_accent_words, line_spacing=1.3)
    else:
        draw_multiline(draw, (margin, y), sub_lines, f_sub, WHITE, align="left", line_spacing=1.3)

    if idx:
        card_number_badge(base, w, idx, total)
        if idx < total:
            swipe_cue(base, w, h)
    footer_wordmark2(base, w, h, margin=margin)
    save(base, filename)
    return base


def impact_photo_card(photo, w, h, tag_text, headline_text, accent_words, sub_text,
                       filename, idx=None, total=None, headline_size=60, sub_size=30,
                       focus=("center", "center"), margin=76, upper=True,
                       sub_accent_words=None):
    """General-purpose 'impact' style photo card (no collage inset) -- bright
    ungraded photo, bold tag banner, two-tone all-caps headline, scrim
    confined to the bottom text zone. This is the default look for plain
    photo+copy cards (kitchen, living room, location, etc.)."""
    base = base_photo_card(photo, w, h, focus=focus, dim=0.0, grade=False, grain=True)
    scrim_bottom(base, h_frac=0.5, max_alpha=250)
    place_logo(base, w)

    if upper:
        headline_text = headline_text.upper()
        tag_text = tag_text.upper()

    draw = ImageDraw.Draw(base)
    f_head, f_sub, mw, head_lines_probe, sub_lines, head_h, sub_h, tag_h = _impact_metrics(
        draw, w, margin, headline_text, sub_text, headline_size, sub_size)

    bottom_pad = 110
    total_block = tag_h + head_h + 20 + sub_h
    y = h - bottom_pad - total_block

    y = bold_tag_banner(base, w, y, tag_text, align="left", margin=margin, fill=IMPACT_GOLD)
    draw = ImageDraw.Draw(base)
    draw_two_tone_headline(draw, (margin, y), headline_text, accent_words, f_head,
                            base_fill=WHITE, accent_fill=IMPACT_GOLD, max_width=mw, align="left")
    y += head_h + 20
    if sub_accent_words:
        draw_multiline_accent(draw, (margin, y), sub_lines, f_sub, WHITE,
                               accent_words=sub_accent_words, line_spacing=1.3)
    else:
        draw_multiline(draw, (margin, y), sub_lines, f_sub, WHITE, align="left", line_spacing=1.3)

    if idx:
        card_number_badge(base, w, idx, total)
        if idx < total:
            swipe_cue(base, w, h)
    footer_wordmark2(base, w, h, margin=margin)
    save(base, filename)
    return base


def impact_split_content(base, w, h, margin, tag_text, headline_text, accent_words,
                          sub_text, headline_size=54, sub_size=28, upper=True,
                          sub_accent_words=None):
    """Text-block treatment for split-photo cards (impact style) -- bold tag
    banner + two-tone all-caps headline. Caller still owns scrim/logo/footer
    (typically scrim_bottom(base, h_frac=0.5, max_alpha=250) applied right
    after split_vertical()/split_horizontal(), before place_logo)."""
    if upper:
        headline_text = headline_text.upper()
        tag_text = tag_text.upper()
    draw = ImageDraw.Draw(base)
    f_head, f_sub, mw, head_lines_probe, sub_lines, head_h, sub_h, tag_h = _impact_metrics(
        draw, w, margin, headline_text, sub_text, headline_size, sub_size)

    bottom_pad = 110
    total_block = tag_h + head_h + 20 + sub_h
    y = h - bottom_pad - total_block

    y = bold_tag_banner(base, w, y, tag_text, align="left", margin=margin, fill=IMPACT_GOLD)
    draw = ImageDraw.Draw(base)
    draw_two_tone_headline(draw, (margin, y), headline_text, accent_words, f_head,
                            base_fill=WHITE, accent_fill=IMPACT_GOLD, max_width=mw, align="left")
    y += head_h + 20
    if sub_accent_words:
        draw_multiline_accent(draw, (margin, y), sub_lines, f_sub, WHITE,
                               accent_words=sub_accent_words, line_spacing=1.3)
    else:
        draw_multiline(draw, (margin, y), sub_lines, f_sub, WHITE, align="left", line_spacing=1.3)


def impact_split_silent(photo_a, photo_b, w, h, filename, idx=None, total=None,
                        orientation="vertical", focus_a=("center", "center"),
                        focus_b=("center", "center"), margin=76):
    """A pure photo-pair 'breather' card -- split_vertical()/split_horizontal()
    plus the logo, footer, and swipe cue, but deliberately NO tag/headline/sub
    text block at all. Modeled directly on a real high-performing listing
    carousel where 3 of its 5 slides were plain photo pairs between the hook
    and the close -- not every card needs to carry copy. Good photos next to
    each other, with nothing competing for attention, is itself a pacing
    choice: use this between a hook card and a stat/CTA card as a breather,
    not as a wholesale replacement for impact_split_content (which still
    carries the tag+headline+sub when a slide needs to make a specific
    point)."""
    if orientation == "vertical":
        base = split_vertical(photo_a, photo_b, w, h, focus_a, focus_b)
    else:
        base = split_horizontal(photo_a, photo_b, w, h, focus_a, focus_b)
    place_logo(base, w)
    if idx:
        card_number_badge(base, w, idx, total)
        if idx < total:
            swipe_cue(base, w, h)
    footer_wordmark2(base, w, h, margin=margin)
    save(base, filename)
    return base


def impact_takeover_stat_card(w, h, tag_text, stat_text, note_text, headline_text, sub_text, bg=None):
    """Takeover stat card, impact style -- bold tag banner instead of the
    quiet eyebrow pill, and the giant stat number rendered in the shiny
    metallic gold gradient instead of flat gold."""
    bg = bg or BLACK
    base = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(base)
    margin = 76
    top_y = 140
    bold_tag_banner(base, w, top_y, tag_text.upper(), align="center", size=40, fill=IMPACT_GOLD)
    draw = ImageDraw.Draw(base)

    cy = h * 0.44
    f_stat = get_font("Mont", 800, 130)
    stat_bbox = draw.textbbox((0, 0), stat_text, font=f_stat)
    stat_w, stat_h = stat_bbox[2] - stat_bbox[0], stat_bbox[3] - stat_bbox[1]
    gradient_text(base, (w / 2, cy - stat_h / 2 - stat_bbox[1]), stat_text, f_stat,
                  align="center", stops=BRIGHT_GOLD_STOPS)

    if note_text:
        f_note = get_font("Inter", 500, 30, opsz=28)
        draw = ImageDraw.Draw(base)
        draw.text((w / 2, cy + 100), note_text, font=f_note, fill=(210, 210, 210), anchor="mm")

    if headline_text:
        headline_text = headline_text.upper()

    # Center the headline/subtext block within the lower half of the card
    # (between the vertical midpoint and the bottom), rather than anchoring
    # it a fixed distance off the bottom -- keeps it clear of both the stat
    # number above and the footer below regardless of how many lines wrap.
    headline_size, sub_size = 48, 28
    f_head_probe = get_font("Mont", 800, headline_size)
    f_sub_probe = get_font("Inter", 500, sub_size, opsz=32)
    mw_probe = w - 2 * margin
    head_lines_probe = wrap_text(draw, headline_text, f_head_probe, mw_probe) if headline_text else []
    sub_lines_probe = wrap_text(draw, sub_text, f_sub_probe, mw_probe) if sub_text else []
    asc_p, desc_p = f_head_probe.getmetrics()
    head_line_h_probe = int((asc_p + desc_p) * 1.14)
    asc_p2, desc_p2 = f_sub_probe.getmetrics()
    sub_line_h_probe = int((asc_p2 + desc_p2) * 1.3)
    head_h_probe = head_line_h_probe * len(head_lines_probe)
    gap_probe = 20 if head_lines_probe and sub_lines_probe else 0
    sub_h_probe = sub_line_h_probe * len(sub_lines_probe)
    total_probe = head_h_probe + gap_probe + sub_h_probe

    lower_half_top = h / 2
    block_center = lower_half_top + (h - lower_half_top) / 2
    bottom_pad = max(h - (block_center + total_probe / 2), 60)

    content_block2(base, w, h, margin, None, headline_text, sub_text,
                    headline_size=headline_size, sub_size=sub_size, align="center",
                    bottom_pad=bottom_pad, sub_color=(210, 210, 210))
    footer_wordmark2(base, w, h, margin=margin)
    return base


def impact_cta_card(photo, w, h, filename, idx, total, button_text, sub_text,
                     title_line1=None, title_script_line2=None,
                     title_single=None, title_accent_words=None,
                     save_share_text=None, focus=("center", "center"), margin=76,
                     sub_accent_words=None):
    """Closing CTA card, impact style -- bright photo + full translucent
    scrim (legibility needs full coverage here since text fills the whole
    card, unlike the hook cards where only the bottom needs it), a title
    (either the two-line 'YOUR' / script-gradient-noun-phrase treatment, or a
    single two-tone all-caps headline when the copy doesn't split that way),
    a real gold-gradient button (not just colored text) for the one action
    that matters, then supporting line / contact / save-share, all vertically
    grouped and shifted above center so it doesn't float in empty space."""
    base = base_photo_card(photo, w, h, focus=focus, dim=0.0, grade=False, grain=True)
    full_scrim(base, alpha=175)
    logo_bottom = place_logo(base, w, target_w=430)
    draw = ImageDraw.Draw(base)

    button_text = button_text.upper().rstrip(".")

    f_title1 = get_font("Mont", 800, 68)
    f_script = get_script_font(190)
    f_title_single = get_font("Mont", 800, 60)
    f_btn = get_font("Mont", 800, 46)
    f_sub = get_font("Inter", 600, 36, opsz=32)
    f_contact = get_font("Inter", 600, 27, opsz=27)
    f_save = get_font("Mont", 700, 29)

    use_script = bool(title_script_line2)

    if use_script:
        l1_bbox = draw.textbbox((0, 0), title_line1, font=f_title1)
        l1_h = l1_bbox[3] - l1_bbox[1]
        l2_bbox = draw.textbbox((0, 0), title_script_line2, font=f_script)
        l2_h = l2_bbox[3] - l2_bbox[1]
        title_h = l1_h + 10 + l2_h
    else:
        mw = w - 2 * margin
        title_lines = wrap_text(draw, title_single.upper(), f_title_single, mw)
        asc, desc = f_title_single.getmetrics()
        title_line_h = int((asc + desc) * 1.14)
        title_h = title_line_h * len(title_lines)

    btn_bbox = draw.textbbox((0, 0), button_text, font=f_btn)
    btn_pad_x, btn_pad_y = 88, 40
    btn_h = (btn_bbox[3] - btn_bbox[1]) + btn_pad_y * 2

    sub_lines = wrap_text(draw, sub_text, f_sub, w - 140)
    asc2, desc2 = f_sub.getmetrics()
    sub_line_h = int((asc2 + desc2) * 1.3)
    sub_h = sub_line_h * len(sub_lines)

    contact = CONTACT_LINE
    cb = draw.textbbox((0, 0), contact, font=f_contact)
    contact_h = cb[3] - cb[1]

    save_h = 0
    if save_share_text:
        sb = draw.textbbox((0, 0), save_share_text, font=f_save)
        save_h = sb[3] - sb[1] + 26

    # Fixed title zone so the button always lands in the same place whether
    # the title is the two-line script treatment or a single-line headline.
    TITLE_ZONE_H = 260
    gap_title_btn = 46
    gap_btn_sub = 34
    gap_sub_contact = 22

    total_below_title_zone = gap_title_btn + btn_h + gap_btn_sub + sub_h + gap_sub_contact + contact_h + save_h
    block_h = TITLE_ZONE_H + total_below_title_zone
    block_top = (h - block_h) / 2 - 40

    title_zone_top = block_top
    title_zone_bottom = title_zone_top + TITLE_ZONE_H

    if use_script:
        y_title = title_zone_bottom - title_h
        draw.text((margin, y_title), title_line1.upper(), font=f_title1, fill=WHITE)
        y_script = y_title + l1_h + 10
        gradient_text(base, (margin, y_script), title_script_line2, f_script, stops=BRIGHT_GOLD_STOPS)
    else:
        y_title = title_zone_bottom - title_h
        draw_two_tone_headline(draw, (margin, y_title), title_single.upper(),
                                title_accent_words or [], f_title_single,
                                base_fill=WHITE, accent_fill=IMPACT_GOLD,
                                max_width=w - 2 * margin, align="left")

    y_btn = title_zone_bottom + gap_title_btn
    btn_w = (btn_bbox[2] - btn_bbox[0]) + btn_pad_x * 2
    gradient_rounded_rect(base, [margin, y_btn, margin + btn_w, y_btn + btn_h], radius=btn_h / 2,
                          stops=BRIGHT_GOLD_STOPS)
    draw = ImageDraw.Draw(base)
    draw.text((margin + btn_w / 2, y_btn + btn_h / 2), button_text, font=f_btn, fill=BLACK, anchor="mm")

    y_sub = y_btn + btn_h + gap_btn_sub
    if sub_accent_words:
        draw_multiline_accent(draw, (margin, y_sub), sub_lines, f_sub, WHITE,
                               accent_words=sub_accent_words, line_spacing=1.3)
    else:
        draw_multiline(draw, (margin, y_sub), sub_lines, f_sub, WHITE, align="left", line_spacing=1.3)

    y_contact = y_sub + sub_h + gap_sub_contact
    draw.text((margin, y_contact), contact, font=f_contact, fill=(225, 225, 225))

    if save_share_text:
        y_ss = y_contact + contact_h + 26
        gradient_text(base, (margin, y_ss), save_share_text, f_save, stops=BRIGHT_GOLD_STOPS)

    card_number_badge(base, w, idx, total)
    footer_wordmark2(base, w, h, margin=margin)
    save(base, filename)
    return base


# ===================== "IMPACT" STATIC IMAGE TEMPLATES (v3) =====================
def impact_static_stat_card(base_photo, w, h, tag_text, stat_text, note_text,
                             headline_text, sub_text, dim=0.35, blur=6, logo=True):
    """Impact-style standalone stat image (square static, e.g. 'your rental
    offset') -- dimmed/blurred photo as texture, bold gradient tag banner
    instead of the quiet eyebrow pill, and the big number in the shiny gold
    gradient instead of flat gold. Pass base_photo=None for a solid
    brand-black background instead."""
    if base_photo:
        base = base_photo_card(base_photo, w, h, dim=dim, blur=blur)
        full_scrim(base, alpha=125)
    else:
        base = Image.new("RGBA", (w, h), BLACK + (255,))
    margin = 76
    top_y = 130
    if logo:
        logo_bottom = place_logo(base, w)
        top_y = logo_bottom + 96
    bold_tag_banner(base, w, top_y, tag_text.upper(), align="center", size=40, fill=IMPACT_GOLD)
    draw = ImageDraw.Draw(base)

    cy = h * 0.52
    backdrop_panel(base, (60, cy - 165, w - 60, cy + 150), alpha=115)
    draw = ImageDraw.Draw(base)
    gradient_rounded_rect(base, [w / 2 - 90, cy - 168, w / 2 + 90, cy - 128], radius=20)
    draw = ImageDraw.Draw(base)
    draw.text((w / 2, cy - 148), "ESTIMATED", font=get_font("Mont", 700, 22), fill=BLACK, anchor="mm")

    f_stat = get_font("Mont", 800, 100)
    sbbox = draw.textbbox((0, 0), stat_text, font=f_stat)
    gradient_text(base, (w / 2 - (sbbox[2] - sbbox[0]) / 2, cy - 68), stat_text, f_stat,
                  stops=BRIGHT_GOLD_STOPS)

    f_note = get_font("Inter", 500, 29, opsz=28)
    draw = ImageDraw.Draw(base)
    nbbox = draw.textbbox((0, 0), note_text, font=f_note)
    draw.text((w / 2 - (nbbox[2] - nbbox[0]) / 2, cy + 58), note_text, font=f_note, fill=(225, 225, 225))

    if headline_text:
        headline_text = headline_text.upper()
    content_block2(base, w, h, margin, None, headline_text, sub_text,
                    headline_size=48, sub_size=28, align="center", bottom_pad=110)
    footer_wordmark2(base, w, h, margin=margin)
    return base


def impact_static_blueprint(photo, w, h, tag_text, callout_text, headline_text,
                            accent_words, sub_text, dim=0.1, margin=76,
                            partition_kwargs=None, show_partition=True):
    """Impact-style 'conversion blueprint' static -- a lightly dimmed photo
    with the partition_overlay() technical-diagram graphic (unchanged --
    SKYBLUE is a deliberate exception to the gold-only palette, meant to read
    as blueprint annotation, not brand color), a bold gradient tag banner +
    gradient callout chip up top, and a two-tone gradient headline over a
    bottom scrim. Set show_partition=False to reuse this same layout (tag +
    callout chip + headline + sub over a bright photo) for a static that
    doesn't need the diagram line at all -- e.g. a plain 'here's the
    potential' feature static."""
    base = base_photo_card(photo, w, h, dim=dim)
    if show_partition:
        partition_overlay(base, w, h, **(partition_kwargs or {}))
    scrim_bottom(base, h_frac=0.46, max_alpha=235)
    draw = ImageDraw.Draw(base)
    y = bold_tag_banner(base, w, 96, tag_text.upper(), align="left", margin=margin, fill=IMPACT_GOLD)
    if callout_text:
        draw = ImageDraw.Draw(base)
        cb = draw.textbbox((0, 0), callout_text, font=get_font("Mont", 700, 30))
        cw = (cb[2] - cb[0]) + 40
        gradient_rounded_rect(base, [margin, y, margin + cw, y + 52], radius=26)
        draw = ImageDraw.Draw(base)
        draw.text((margin + cw / 2, y + 26), callout_text, font=get_font("Mont", 700, 30),
                  fill=BLACK, anchor="mm")

    headline_text = headline_text.upper()
    f_head = get_font("Mont", 800, 58)
    mw = w - 2 * margin
    head_lines = wrap_text(draw, headline_text, f_head, mw)
    asc, desc = f_head.getmetrics()
    head_line_h = int((asc + desc) * 1.14)
    f_sub = get_font("Inter", 500, 28, opsz=32)
    sub_lines = wrap_text(draw, sub_text, f_sub, mw) if sub_text else []
    asc2, desc2 = f_sub.getmetrics()
    sub_line_h = int((asc2 + desc2) * 1.3)
    head_h = head_line_h * len(head_lines)
    gap = 20 if sub_lines else 0
    sub_h = sub_line_h * len(sub_lines)
    bottom_pad = 100
    ty = h - bottom_pad - head_h - gap - sub_h

    draw_two_tone_headline(draw, (margin, ty), headline_text, accent_words, f_head,
                            base_fill=WHITE, accent_fill=IMPACT_GOLD, max_width=mw, align="left")
    ty += head_h + gap
    if sub_lines:
        draw_multiline(draw, (margin, ty), sub_lines, f_sub, WHITE, align="left", line_spacing=1.3)
    footer_wordmark2(base, w, h, margin=margin)
    return base


def impact_static_landscape(photo_left, photo_right, w, h, headline_text, accent_words,
                            sub_text, footer_override=None,
                            focus_left=("center", "center"), focus_right=("center", "center")):
    """Impact-style landscape static (e.g. 1200x628 for a link-preview-style
    share image) -- split_horizontal() two-photo layout with a bottom bar
    carrying a two-tone gradient headline and a gradient gold sub line."""
    base = split_horizontal(photo_left, photo_right, w, h, focus_left, focus_right)
    draw = ImageDraw.Draw(base)
    bar_h = 170
    layer = Image.new("RGBA", (w, bar_h), BLACK + (235,))
    base.alpha_composite(layer, (0, h - bar_h))
    draw = ImageDraw.Draw(base)

    headline_text = headline_text.upper()
    f_head = get_font("Mont", 800, 40)
    hb = draw.textbbox((0, 0), headline_text, font=f_head)
    hx = w / 2 - (hb[2] - hb[0]) / 2
    hy = h - bar_h + 24
    draw_two_tone_headline(draw, (hx, hy), headline_text, accent_words, f_head,
                           base_fill=WHITE, accent_fill=IMPACT_GOLD, align="left")

    if sub_text:
        f_sub = get_font("Inter", 500, 26, opsz=26)
        sb = draw.textbbox((0, 0), sub_text, font=f_sub)
        gradient_text(base, (w / 2 - (sb[2] - sb[0]) / 2, h - bar_h + 82), sub_text, f_sub,
                      stops=BRIGHT_GOLD_STOPS)
    return base


def impact_static_comparison(photo, w, h, tag_text, rows, headline_text, sub_text,
                             dim=0.45, blur=10, margin=76):
    """Impact-style comparison/checklist static (e.g. 'why investors choose
    this property') -- blurred/dimmed photo, full flat scrim (text fills
    nearly the whole card here, same rule as impact_cta_card: use full_scrim,
    not a gradient, when coverage needs to be even top to bottom), a bold
    gradient tag banner, a label/value row table with gradient-gold values,
    and a centered two-tone headline. `rows` is a list of (label, value)
    tuples."""
    base = base_photo_card(photo, w, h, dim=dim, blur=blur)
    full_scrim(base, alpha=140)
    draw = ImageDraw.Draw(base)
    y = bold_tag_banner(base, w, 180, tag_text.upper(), align="center", size=40, fill=IMPACT_GOLD)
    draw = ImageDraw.Draw(base)

    ry = max(y + 40, 480)
    backdrop_panel(base, (60, ry - 30, w - 60, ry + len(rows) * 130 - 30), alpha=105)
    draw = ImageDraw.Draw(base)
    row_label_w = 260  # approx width label text is given before it must not collide with value
    for label, value in rows:
        f_label = get_font("Inter", 600, 26, opsz=26)
        draw.text((90, ry), label, font=f_label, fill=(220, 220, 220))

        # Long values (e.g. "Minutes to 101 & Dumbarton") can be wider than
        # the big 46px stat-style size leaves room for without colliding
        # with the label -- shrink the value font until it fits rather than
        # relying on every property's copy happening to be short enough.
        value_size = 46
        max_value_w = w - 90 - 90 - row_label_w
        f_value = get_font("Mont", 800, value_size)
        vb = draw.textbbox((0, 0), value, font=f_value)
        while (vb[2] - vb[0]) > max_value_w and value_size > 28:
            value_size -= 2
            f_value = get_font("Mont", 800, value_size)
            vb = draw.textbbox((0, 0), value, font=f_value)

        gradient_text(base, (w - 90 - (vb[2] - vb[0]), ry - 8 + (46 - value_size)), value, f_value,
                      stops=BRIGHT_GOLD_STOPS)
        draw = ImageDraw.Draw(base)
        ry += 62
        draw.rectangle([90, ry, w - 90, ry + 1], fill=(255, 255, 255, 70))
        ry += 68

    headline_text = headline_text.upper()
    content_block2(base, w, h, margin, None, headline_text, sub_text,
                    headline_size=44, sub_size=26, align="center", bottom_pad=110)
    footer_wordmark2(base, w, h, margin=margin)
    return base


def impact_split_silent_bare(photo_a, photo_b, w, h, filename,
                              orientation="vertical",
                              focus_a=("center", "center"),
                              focus_b=("center", "center")):
    """Same photo-pair breather as impact_split_silent(), but with ZERO
    branding overlay -- no logo, no card-number badge, no swipe cue, no
    footer wordmark. Modeled on the actual reference carousel these breather
    cards came from: its silent gallery slides are just two stacked photos,
    nothing else competing for attention. Use this when the goal is to match
    that specific stripped-down pacing; use impact_split_silent (which keeps
    the logo/badge/footer) for Graeham's normal branded carousels."""
    if orientation == "vertical":
        base = split_vertical(photo_a, photo_b, w, h, focus_a, focus_b)
    else:
        base = split_horizontal(photo_a, photo_b, w, h, focus_a, focus_b)
    save(base, filename)
    return base


def floor_fade_scrim(base, floor_frac=0.33, fade_frac=0.35, max_alpha=255, power=1.5):
    """LOCKED-IN 'news card' bottom treatment -- confirmed correct by the
    client after multiple rounds of comparison against a reference post.
    Do not replace this with a plain linear vgradient (scrim_bottom) for
    news_fact_card -- a single linear ramp either crushes to black too
    early (reads as a flat box once cropped near the bottom) or never
    reaches true black at all (reads as translucent everywhere). This is
    two deliberate pieces instead:
      1. A genuinely FLAT, fully-opaque black floor across the bottom
         floor_frac of the card (~1/3 by default) -- true solid black,
         no gradient within that band at all.
      2. A fade zone directly above the floor, easing from opaque down to
         fully clear over the next fade_frac of height, using t**power
         (power>1 keeps it mostly transparent near the top of the zone,
         then accelerates toward the floor) so the photo stays visible
         and the transition feels gentle rather than abrupt.
    Confirmed values: floor_frac=0.33, fade_frac=0.35, power=1.5,
    max_alpha=255. Change the floor_frac/fade_frac args if a specific card
    needs more or less black, but keep the two-piece floor+fade structure --
    it's the structure itself that was confirmed, not just one number."""
    w, h = base.size
    floor_h = int(h * floor_frac)
    fade_h = int(h * fade_frac)
    total_h = floor_h + fade_h
    grad = Image.new("L", (1, total_h))
    for y in range(total_h):
        if y >= fade_h:
            a = max_alpha
        else:
            t = y / max(fade_h - 1, 1)
            a = int(max_alpha * (t ** power))
        grad.putpixel((0, y), a)
    grad = grad.resize((w, total_h))
    layer = Image.new("RGBA", (w, total_h), (0, 0, 0, 0))
    layer.putalpha(grad)
    base.alpha_composite(layer, (0, h - total_h))


def news_fact_card(photo, w, h, tag_text, headline_text, accent_words, sub_text,
                    filename, idx=None, total=None, headline_size=52, sub_size=30,
                    focus=("center", "center"), margin=76, upper=True,
                    sub_accent_words=None, zoom=1.0, lift=0):
    """'Breaking news' fact-card -- CONFIRMED FINAL VERSION. Restyled to
    reuse the exact same text treatment as impact_hook_card() (bold tag
    banner, two-tone headline, plain sub-text, all left-aligned) instead of
    the earlier centered icon+mini-headline layout, per explicit direction
    to make every card's text 'look similar to the text in the hook' for a
    consistent carousel. Sits on the LOCKED floor_fade_scrim() bottom
    treatment: flat black floor across ~1/3 of the card, gentle gradient
    fade above it into the bright, true-color photo (no sepia/duotone --
    that was tried and rejected). zoom > 1.0 crops in tighter so a photo
    with a lot of empty sky/ceiling doesn't look small and buried under the
    floor -- use it to 'raise' the subject the same way impact_hook_card's
    zoom_main does."""
    base = base_photo_card(photo, w, h, focus=focus, dim=0.0, grade=False, grain=True, zoom=zoom, lift_px=lift)
    floor_fade_scrim(base, floor_frac=0.33, fade_frac=0.35, max_alpha=255, power=1.5)

    if upper:
        headline_text = headline_text.upper()
        tag_text = tag_text.upper()

    draw = ImageDraw.Draw(base)
    f_head, f_sub, mw, head_lines_probe, sub_lines, head_h, sub_h, tag_h = _impact_metrics(
        draw, w, margin, headline_text, sub_text, headline_size, sub_size)

    bottom_pad = 110
    total_block = tag_h + head_h + 20 + sub_h
    y = h - bottom_pad - total_block

    y = bold_tag_banner(base, w, y, tag_text, align="left", margin=margin, fill=IMPACT_GOLD)
    draw = ImageDraw.Draw(base)
    draw_two_tone_headline(draw, (margin, y), headline_text, accent_words, f_head,
                            base_fill=WHITE, accent_fill=IMPACT_GOLD, max_width=mw, align="left")
    y += head_h + 20
    if sub_accent_words:
        draw_multiline_accent(draw, (margin, y), sub_lines, f_sub, WHITE,
                               accent_words=sub_accent_words, line_spacing=1.3)
    else:
        draw_multiline(draw, (margin, y), sub_lines, f_sub, WHITE, align="left", line_spacing=1.3)

    if idx is None or (total and idx < total):
        r = 40
        acx, acy = w - 96, h - 90
        draw.ellipse([acx - r, acy - r, acx + r, acy + r], fill=(30, 30, 30, 220))
        f_arrow = get_font("Mont", 700, 32)
        ab = draw.textbbox((0, 0), "→", font=f_arrow)
        draw.text((acx - (ab[2] - ab[0]) / 2, acy - (ab[3] - ab[1]) / 2 - ab[1]),
                   "→", font=f_arrow, fill=WHITE)

    place_logo(base, w, target_w=170, top_margin=40)
    if idx:
        card_number_badge(base, w, idx, total)
    save(base, filename)
    return base
