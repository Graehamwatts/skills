#!/usr/bin/env python3
"""
quick_carousel_lib.py -- lightweight, PHOTO-OPTIONAL carousel card templates
for fast "trending data" / "quick take" carousels (the kenny_fast-style
category: "Where People Are Moving," "$X gets you here," ranked data lists).

This is the execution layer for the quick-carousel-engine skill. It does NOT
duplicate the brand engine -- it imports fonts, colors, the gold-gradient
system, the logo compositor, and the pill/badge primitives straight from
carousel-builder's carousel_lib.py, which stays the single source of truth
for Graeham's visual brand. See ../references/workflow.md for the full
process; the short version:

  carousel-builder      -> ONE property, real photos, deep market research,
                            15-asset package, ~1-2 hrs of work.
  quick-carousel-engine  -> ONE data point / trend / ranked list, zero-to-one
                            generic photos, ~15-20 min of work.

Card types here are deliberately photo-free (solid brand-black background)
so Peter/Ellie never get blocked waiting on a photoshoot. If a real local
photo IS on hand (a phone shot of a recognizable landmark, a headshot),
prefer carousel-builder's `impact_hook_card` / `impact_cta_card` /
`impact_static_comparison` instead -- those give a richer look. This library
exists for the case where there is no photo and the post needs to go out
today.

USAGE: don't call this file directly. Copy scripts/quick_carousel_build.py,
fill in its CONFIG + card calls, run that.
"""
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CAROUSEL_BUILDER_SCRIPTS = os.path.normpath(
    os.path.join(_THIS_DIR, "..", "..", "carousel-builder", "scripts")
)
if _CAROUSEL_BUILDER_SCRIPTS not in sys.path:
    sys.path.insert(0, _CAROUSEL_BUILDER_SCRIPTS)

import carousel_lib as lib  # noqa: E402  (path insert must happen first)
from carousel_lib import (  # noqa: E402
    Image, ImageDraw,
    BLACK, WHITE, GOLD, IMPACT_GOLD,
    get_font, save, place_logo, footer_wordmark2, card_number_badge, swipe_cue,
    bold_tag_banner, gradient_text, gradient_rounded_rect, draw_two_tone_headline,
    wrap_text, draw_multiline, _impact_metrics, _ensure_logos_loaded,
    impact_takeover_stat_card,  # re-exported -- already photo-free, use directly
)

# Same configure(src, out) entrypoint as carousel_lib -- src is only needed
# if a driver script mixes in a real carousel-builder photo card.
configure = lib.configure


def _draw_source_note(draw, w, h, margin, source_note, color=(140, 140, 140), align="left",
                       bottom=150, y=None):
    """Wraps the source citation to the card width instead of drawing it as
    one unbroken line -- a long real citation (or, in testing, a long
    placeholder) silently ran off the right edge of the canvas when this was
    a single draw.text call. Every stat/list card routes through this.
    Pass `y` for a top-anchored position (e.g. right after a variable-height
    block above it); omit it for the default bottom-anchored position."""
    if not source_note:
        return None
    f_note = get_font("Inter", 500, 22, opsz=22)
    text = f"SOURCE: {source_note.upper()}"
    max_w = w - 2 * margin
    lines = wrap_text(draw, text, f_note, max_w)
    x = w / 2 if align == "center" else margin
    asc, desc = f_note.getmetrics()
    line_h = int((asc + desc) * 1.25)
    total_h = line_h * len(lines)
    top = y if y is not None else h - bottom - total_h
    draw_multiline(draw, (x, top), lines, f_note, color, align=align, line_spacing=1.25)
    return top + total_h


def _sync_footer(config):
    """Call once per driver script, right after configure(), same as
    template_build_impact.py does with lib.FOOTER_TEXT / lib.CONTACT_LINE."""
    lib.FOOTER_TEXT = config.get("footer_text", "")
    lib.CONTACT_LINE = config.get("contact_line", "Graeham Watts  .  Compass  .  DRE #01466876")


def quick_title_card(w, h, filename, idx, total, tag_text, headline_text,
                      accent_words, sub_text=None, source_note=None,
                      headline_size=72, sub_size=32, margin=76):
    """Photo-free hook/title card. The data point IS the hook -- e.g.
    'RENT IN REDWOOD CITY IS UP 18%' -- so this leads with a bold gradient
    tag banner + a big two-tone headline, top-anchored (there's no photo to
    fill the rest of the frame with, unlike impact_hook_card's bottom
    anchoring). `source_note` renders small and dim near the bottom --
    every stat carousel must cite where the number came from (never ship an
    uncited number; see references/workflow.md's data-integrity rule)."""
    base = Image.new("RGBA", (w, h), BLACK + (255,))
    draw = ImageDraw.Draw(base)
    logo_bottom = place_logo(base, w)

    y = bold_tag_banner(base, w, logo_bottom + 50, tag_text.upper(), align="left",
                         margin=margin, size=38)
    draw = ImageDraw.Draw(base)

    f_head, f_sub, mw, head_lines, sub_lines, head_h, sub_h, _tag_h = _impact_metrics(
        draw, w, margin, headline_text.upper(), sub_text or "", headline_size, sub_size)

    draw_two_tone_headline(draw, (margin, y), headline_text.upper(), accent_words, f_head,
                            base_fill=WHITE, accent_fill=IMPACT_GOLD, max_width=mw, align="left")
    y += head_h + 22

    if sub_text:
        draw_multiline(draw, (margin, y), sub_lines, f_sub, (210, 210, 210), align="left",
                        line_spacing=1.3)

    _draw_source_note(draw, w, h, margin, source_note, align="left")

    footer_wordmark2(base, w, h, margin=margin)
    if idx:
        card_number_badge(base, w, idx, total)
        if idx < total:
            swipe_cue(base, w, h)
    save(base, filename)
    return base


def quick_rank_card(w, h, filename, idx, total, rank_text, label_text, value_text,
                     note_text=None, margin=76):
    """One entry in a ranked list (e.g. '#1 SAN FRANCISCO -- 42% rent increase').
    Big rank number top-left in the gold gradient, the label centered large,
    the value directly under it. Deliberately simple/repetitive across a
    carousel -- consistency is what lets a swiper's eye register only what
    changed between cards, same principle the $2M-comparison carousel note
    documents (see references/template-categories.md)."""
    base = Image.new("RGBA", (w, h), BLACK + (255,))
    draw = ImageDraw.Draw(base)
    place_logo(base, w)

    f_rank = get_font("Mont", 800, 54)
    gradient_text(base, (margin, 210), rank_text.upper(), f_rank, align="left")
    draw = ImageDraw.Draw(base)

    # Top-anchor the label/value/note block and grow downward by MEASURED
    # heights rather than fixed offsets -- a fixed-offset layout silently
    # overlaps the value onto the label the moment label_text wraps to more
    # than one line (this bit us in testing: keep it dynamic).
    y = h * 0.38
    f_label = get_font("Mont", 800, 64)
    label_lines = wrap_text(draw, label_text.upper(), f_label, w - 2 * margin)
    label_h = draw_multiline(draw, (w / 2, y), label_lines, f_label, WHITE, align="center",
                              line_spacing=1.1)
    y += label_h + 50

    f_val = get_font("Mont", 800, 96)
    gradient_text(base, (w / 2, y), value_text, f_val, align="center")
    draw = ImageDraw.Draw(base)
    val_asc, val_desc = f_val.getmetrics()
    y += val_asc + val_desc + 40

    if note_text:
        f_note = get_font("Inter", 500, 28, opsz=28)
        note_lines = wrap_text(draw, note_text, f_note, w - 2 * margin)
        draw_multiline(draw, (w / 2, y), note_lines, f_note, (200, 200, 200), align="center",
                        line_spacing=1.3)

    footer_wordmark2(base, w, h, margin=margin)
    card_number_badge(base, w, idx, total)
    if idx < total:
        swipe_cue(base, w, h)
    save(base, filename)
    return base


def quick_table_card(w, h, filename, idx, total, tag_text, rows, headline_text=None,
                      source_note=None, margin=76):
    """Photo-free ranked/comparison table -- rows of (label, value) drawn as
    a stacked list, gold-gradient values. This is the photo-free sibling of
    carousel-builder's impact_static_comparison (which needs a blurred
    background photo); use this one when there is no photo on hand."""
    base = Image.new("RGBA", (w, h), BLACK + (255,))
    draw = ImageDraw.Draw(base)
    logo_bottom = place_logo(base, w)
    y = bold_tag_banner(base, w, logo_bottom + 40, tag_text.upper(), align="center", size=38)
    draw = ImageDraw.Draw(base)

    row_h = 108
    top = y + 30
    f_label = get_font("Inter", 600, 30, opsz=30)
    f_rank = get_font("Mont", 800, 34)
    f_val = get_font("Mont", 800, 40)
    for i, (label, value) in enumerate(rows):
        ry = top + i * row_h
        draw.line([(margin, ry + row_h - 14), (w - margin, ry + row_h - 14)],
                   fill=(60, 60, 60), width=1)
        gradient_text(base, (margin, ry), f"{i + 1:02d}", f_rank, align="left")
        draw = ImageDraw.Draw(base)
        draw.text((margin + 90, ry + 6), label, font=f_label, fill=WHITE)
        vbbox = draw.textbbox((0, 0), value, font=f_val)
        vw = vbbox[2] - vbbox[0]
        gradient_text(base, (w - margin - vw, ry - 4), value, f_val, align="left")
        draw = ImageDraw.Draw(base)

    bottom_y = top + len(rows) * row_h + 20
    if headline_text:
        f_head = get_font("Mont", 700, 36)
        head_lines = wrap_text(draw, headline_text, f_head, w - 2 * margin)
        draw_multiline(draw, (w / 2, bottom_y), head_lines, f_head, (210, 210, 210),
                        align="center", line_spacing=1.2)

    _draw_source_note(draw, w, h, margin, source_note, align="left")

    footer_wordmark2(base, w, h, margin=margin)
    card_number_badge(base, w, idx, total)
    if idx < total:
        swipe_cue(base, w, h)
    save(base, filename)
    return base


def quick_cta_card(w, h, filename, idx, total, headline_text, accent_words,
                    button_text, sub_text=None, keyword_line=None, margin=76):
    """Photo-free closing card. Gold-gradient button (the one action that
    matters), headline stating the payoff, optional comment/DM-keyword line.
    No swipe cue -- this is always the last card."""
    base = Image.new("RGBA", (w, h), BLACK + (255,))
    draw = ImageDraw.Draw(base)
    place_logo(base, w, target_w=340)

    cy = h * 0.42
    f_head = get_font("Mont", 800, 60)
    head_lines = wrap_text(draw, headline_text.upper(), f_head, w - 2 * margin)
    head_block_h = 0
    asc, desc = f_head.getmetrics()
    head_line_h = int((asc + desc) * 1.14)
    y0 = cy - (head_line_h * len(head_lines)) / 2
    for line in head_lines:
        draw_two_tone_headline(draw, (w / 2, y0), line, accent_words, f_head,
                                base_fill=WHITE, accent_fill=IMPACT_GOLD, align="center")
        y0 += head_line_h
        head_block_h += head_line_h
    draw = ImageDraw.Draw(base)

    y = cy + head_block_h / 2 + 40
    if sub_text:
        f_sub = get_font("Inter", 500, 32, opsz=32)
        sub_lines = wrap_text(draw, sub_text, f_sub, w - 2 * margin)
        draw_multiline(draw, (w / 2, y), sub_lines, f_sub, (210, 210, 210), align="center",
                        line_spacing=1.3)
        y += int((sum(1 for _ in sub_lines)) * 44) + 40
    else:
        y += 40

    btn_text = button_text.upper()
    f_btn = get_font("Mont", 800, 42)
    bbox = draw.textbbox((0, 0), btn_text, font=f_btn)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 60, 30
    bx0 = w / 2 - (bw + pad_x * 2) / 2
    gradient_rounded_rect(base, [bx0, y, bx0 + bw + pad_x * 2, y + bh + pad_y * 2], radius=(bh + pad_y * 2) / 2)
    draw = ImageDraw.Draw(base)
    draw.text((w / 2, y + (bh + pad_y * 2) / 2), btn_text, font=f_btn, fill=BLACK, anchor="mm")
    y += bh + pad_y * 2 + 36

    if keyword_line:
        f_kw = get_font("Inter", 600, 28, opsz=28)
        draw.text((w / 2, y), keyword_line, font=f_kw, fill=(200, 200, 200), anchor="mm")

    footer_wordmark2(base, w, h, margin=margin)
    card_number_badge(base, w, idx, total)
    save(base, filename)
    return base


# ===========================================================================
# EDITORIAL RANK LIST -- reverse-engineered directly from the reference
# Graeham pointed to (a "Where People Are Moving" style migration-data
# card). Deliberately a different visual register than everything above:
# light background, bold black headline, tinted two-column ranked list.
# Added 2026-09-09 after Graeham's "these are not great, look at Kenny's"
# feedback -- the all-black/gold cards above read as a sales pitch, and
# this specific reference format reads as shareable data journalism, which
# is what TOFU reach content actually needs.
# ===========================================================================

# Muted red/green column tints -- a DELIBERATE, DOCUMENTED exception to the
# gold-only-accent brand rule, same precedent as carousel_lib's SKYBLUE
# (used only for the technical blueprint diagram). These encode DIRECTION
# (leaving vs. arriving) as a chart legend would, not brand decoration.
# Don't reuse red/green anywhere else in this system -- gold stays the only
# decorative accent everywhere but this one functional case.
_LEAVING_TINT = (250, 230, 227)
_LEAVING_TEXT = (176, 68, 56)
_MOVING_TINT = (223, 238, 227)
_MOVING_TEXT = (58, 110, 74)


def _draw_rank_row(draw, col_x0, cy, rank, label, color, f_num, f_label):
    badge_d = 42
    bx = col_x0 + 32
    draw.ellipse([bx - badge_d / 2, cy - badge_d / 2, bx + badge_d / 2, cy + badge_d / 2], fill=color)
    draw.text((bx, cy), str(rank), font=f_num, fill=WHITE, anchor="mm")
    draw.text((bx + badge_d / 2 + 22, cy), label, font=f_label, fill=BLACK, anchor="lm")


def editorial_rank_list_card(w, h, filename, idx, total, headline_text, accent_word,
                              sub_text, left_label, left_rows, right_label, right_rows,
                              source_note=None, margin=64):
    """Light-background, two-column color-coded ranked list. `left_rows` and
    `right_rows` are plain lists of short strings (e.g. "San Jose, CA"),
    already ordered -- numbering is added automatically. Column heights
    auto-fit to whichever side has more rows; keep both sides the same
    length (the reference uses 10/10) for visual balance.

    This is the flagship Category-1 hook/data card -- use it in place of
    `quick_title_card` + `quick_table_card` when the topic IS a two-sided
    ranked comparison (migration, price movement direction, etc.). For a
    single-column ranked list (no "leaving vs. arriving" split), leave
    `right_rows` empty and use only `left_label`/`left_rows`."""
    base = Image.new("RGBA", (w, h), lib.CREAM + (255,))
    draw = ImageDraw.Draw(base)

    _ensure_logos_loaded()
    logo_bottom = place_logo(base, w, target_w=200, top_margin=44, logo=lib.LOGO_BLACK, plate=False)

    y = logo_bottom + 36
    f_head = get_font("Mont", 800, 56)
    max_w = w - 2 * margin
    head_lines = wrap_text(draw, headline_text.upper(), f_head, max_w)
    asc, desc = f_head.getmetrics()
    head_line_h = int((asc + desc) * 1.12)
    for line in head_lines:
        draw_two_tone_headline(draw, (w / 2, y), line, [accent_word.upper()], f_head,
                                base_fill=BLACK, accent_fill=IMPACT_GOLD, align="center",
                                gradient_accent=True)
        y += head_line_h
    y += 12

    if sub_text:
        f_sub = get_font("Inter", 500, 27, opsz=27)
        sub_lines = wrap_text(draw, sub_text, f_sub, max_w)
        sub_h = draw_multiline(draw, (w / 2, y), sub_lines, f_sub, (100, 100, 100), align="center",
                                line_spacing=1.3)
        y += sub_h + 30
    else:
        y += 20

    col_w = (w - 2 * margin - 32) / 2
    col_left_x0 = margin
    col_right_x0 = margin + col_w + 32
    n_rows = max(len(left_rows), len(right_rows or []))
    row_h = min(72, max(48, int((h - y - 220) / max(n_rows, 1))))
    header_h = 64
    col_top = y
    col_h = header_h + n_rows * row_h + 20

    draw.rounded_rectangle([col_left_x0, col_top, col_left_x0 + col_w, col_top + col_h],
                            radius=18, fill=_LEAVING_TINT)
    if right_rows:
        draw.rounded_rectangle([col_right_x0, col_top, col_right_x0 + col_w, col_top + col_h],
                                radius=18, fill=_MOVING_TINT)
    draw = ImageDraw.Draw(base)

    f_col_head = get_font("Mont", 800, 28)
    draw.text((col_left_x0 + col_w / 2, col_top + header_h / 2), left_label.upper(),
               font=f_col_head, fill=_LEAVING_TEXT, anchor="mm")
    if right_rows:
        draw.text((col_right_x0 + col_w / 2, col_top + header_h / 2), right_label.upper(),
                   font=f_col_head, fill=_MOVING_TEXT, anchor="mm")

    f_num = get_font("Mont", 800, 24)
    f_label = get_font("Inter", 600, 25, opsz=25)
    for i in range(n_rows):
        ry = col_top + header_h + i * row_h + row_h / 2
        if i < len(left_rows):
            _draw_rank_row(draw, col_left_x0, ry, i + 1, left_rows[i], _LEAVING_TEXT, f_num, f_label)
        if right_rows and i < len(right_rows):
            _draw_rank_row(draw, col_right_x0, ry, i + 1, right_rows[i], _MOVING_TEXT, f_num, f_label)

    _draw_source_note(draw, w, h, margin, source_note, align="center", y=col_top + col_h + 34)

    footer_wordmark2(base, w, h, margin=margin)
    card_number_badge(base, w, idx, total)
    if idx < total:
        swipe_cue(base, w, h)
    save(base, filename)
    return base
