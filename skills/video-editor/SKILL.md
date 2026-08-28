---
name: video-editor
description: >-
  Turn a folder of raw 4K property/listing clips into finished, on-brand marketing: vertical Reels
  (9:16), a wide Walkthrough tour (16:9, 2-3 min), a Just Listed single-image AD KIT (3 hero
  concepts x portrait/square/landscape, ready-to-post PNGs + Canva-editable PDFs), and a 10-slide
  Instagram CAROUSEL. Use ANY time the user wants to edit, cut, or assemble property or listing
  videos, make reels or a walkthrough from raw clips, create Just Listed / New Listing ads or
  flyers, or build an Instagram carousel for a property. Trigger on 'edit these clips', 'make me
  reels', 'cut a walkthrough', 'property video', 'listing video', 'feature video', 'just listed
  ad', 'new listing flyer', 'carousel for this property', 'turn this footage into a video', or
  when the user points at a folder of property MP4s wanting video or image marketing output. Over-
  trigger for any raw-footage-to-social-asset task. Outputs ready-to-post files plus Canva-
  editable PDFs on a black-and-gold brand.
---

# Video Editor — a listing's raw footage to finished marketing

Turn a folder of raw 4K property clips into four deliverables, all on one black-and-gold
brand, all built locally with `ffmpeg` + Pillow + ReportLab:

1. **Reels** — 9:16 (1080x1920) vertical highlight cuts for IG / TikTok / Shorts.
2. **Walkthrough** — 16:9 (1920x1080), a 2-3 min buyer's-journey tour.
3. **Just Listed ad kit** — 3 hero concepts x 3 sizes (1080x1350, 1080x1080, 1200x628);
   ready-to-post PNGs + Canva-editable PDFs + clean hero photos + a usage README.
4. **Instagram carousel** — 10 slides (1080x1350); PNGs + Canva-editable PDF + caption.

`scripts/` holds the engines; `references/` holds the step-by-step for each deliverable.
**Read the matching reference before building a deliverable** — the recipes there are the
result of a full session of trial-and-error, not guesses.

## 0 · The operating reality — read this or you will fail
You're usually in a small sandbox: ~2 CPU cores, ~4 GB RAM, and a **hard ~45-second limit
per shell command**, against **16+ GB of 4K source**. One full-timeline encode WILL time
out and leave a truncated, unplayable file. The entire pipeline exists to dodge this:
- **Decode each 4K clip once** into small graded 1080p segments; assemble from those.
- **Batch <= 4 renders per shell call**; echo elapsed seconds; keep each call under ~35s.
- **Never assemble in one pass.** Build short chunks, then `ffmpeg -f concat -c copy` them
  (instant, no re-encode).
- **Add a silent audio track with an explicit `-t <dur>`.** `-shortest` does NOT stop a
  copied video stream against an infinite `anullsrc` — it runs to the timeout.
- **Don't use `+faststart` on big files** in one call (the moov-relocation second pass
  blows the time budget). Mux without it.
- **Verify by eye every time**: extract frames -> `montage` -> view. A clean exit is not
  proof; check the pixels.
Full failure-mode list and fixes: **`references/sandbox-constraints.md`**.

## 1 · Always review the footage first
Before cutting anything, extract one labeled thumbnail per clip, montage them into contact
sheets, and actually LOOK. Verify what each clip contains (never trust filenames or a prior
edit plan), record real durations, and **clamp every in/out point to the true clip length**.
This is also where you catch deal-breakers — most importantly a **realtor yard sign visible
inside an exterior clip**, which is a blocker if the user asked for no agent info.
Recipe: `references/video-pipeline.md` (section "Review the footage").

## 2 · Brand system (summary)
Black-and-gold, font **Poppins**. Gold `#C7A974`, ink `#0E0C0A`, off-white `#F4EEE3`,
light-gold `#DEC9A2`. Thin gold inset frame, a gold "JUST LISTED" pill (ink pill with gold
outline for "NEW LISTING"), a lower-third dark gradient, and a bold address lockup. Full
tokens + the Pillow/drawtext recipes: **`references/brand-system.md`**.

## 3 · Rules that are NOT optional
These came straight from the operator and apply every single time:
- **Never invent facts.** Beds, baths, sq ft, price, "stainless steel", "2-car garage" — if
  you can't see it in the footage and the user didn't give it to you, **leave it off** and
  offer to add it once they confirm. Caption only features visible on screen. (Example from
  the build: the range was black, not stainless — so the caption said "gas range", not
  "stainless".)
- **Honor "no agent info."** No name / phone / website / DRE when asked — and also scrub any
  **yard sign** that appears inside a photo or clip by swapping to a clean shot (an aerial
  works well for a closing slide).
- **Music:** you cannot burn in licensed/commercial music (copyright). Default to a **clean
  (silent) export** so the operator scores it in their own editor, unless they say otherwise.
  Cut to ~2s beats so it syncs to most 120-128 BPM tracks later.
- **"Editable in Canva" = a PDF with REAL text**, never a flattened image. Build it with
  ReportLab as layers: clean photo (replaceable) + separate gradient overlay (`mask='auto'`)
  + vector gold frame + real Poppins text. **Verify with `pdftotext`** — the words must come
  back — before you deliver.
- **Ask before building** with AskUserQuestion: how to handle music, what (if anything) goes
  on the end-card / contact lockup, and how different the two reels should be. Guessing these
  wastes a full render pass.

## 4 · Workflows
Open the matching reference for the deliverable(s) requested:

| Deliverable | Reference | Engines |
|---|---|---|
| Reels (9:16) + Walkthrough (16:9) | `references/video-pipeline.md` | `scripts/video_lib.sh`, `scripts/chunk.py` |
| Just Listed ad kit | `references/ad-kit.md` | `scripts/ad_lib.py`, `scripts/make_ad_pdfs.py` |
| Instagram carousel | `references/carousel.md` | `scripts/carousel_lib.py`, `scripts/make_carousel_pdf.py` |

Shared flow for all of them: **review footage -> confirm choices with the user -> render in
small batches -> QC by viewing frames -> deliver into the user's listing folder with
`present_files` -> offer the obvious next adds** (a text-free cut, other sizes, a stats slide
once numbers exist, etc.).

## 5 · Bundled scripts (how to call)
Every script finds Poppins automatically (or via `VE_FONTDIR`) and defaults output paths to
relative dirs, so set the env vars per session.

- **`video_lib.sh`** — `export VE_SRC="<clips folder>" VE_OUT="<work dir>"; source video_lib.sh`.
  Gives `seg16` (16:9 segment), `seg916c` (vertical center-crop), `seg916p` (vertical
  blurred-pad for wide shots), and `xf` (xfade two segments). Recipe in video-pipeline.md.
- **`chunk.py`** — `python chunk.py OUT FADEIN FADEOUT seg1 [TRANSITION DUR seg2]...` builds
  one xfade chunk with exact offsets. Transitions: `fade fadeblack fadewhite dissolve
  slideleft slideright slideup smoothleft circleopen wiperight ...`.
- **`ad_lib.py`** — edit `CONCEPTS` / `SIZES` / `ADDR1` / `ADDR2` at the top; set
  `VE_HERO="<hero stills dir>"`; call `render(concept, sizekey, mode)` where mode is
  `png` (flat), `plate` (frame+gradient, no text), or `clean` (photo only). See ad-kit.md.
- **`make_ad_pdfs.py`** — builds the 3 Canva-editable ad PDFs with real text. `VE_KIT="<dir>"`.
- **`carousel_lib.py`** — edit `SLIDES`; set `VE_CHEROES="<slide stills dir>"`;
  call `render(i, mode)`. Imports `ad_lib` (keep them in the same folder).
- **`make_carousel_pdf.py`** — builds the 10-page editable carousel PDF. `VE_CAROUSEL_PDF="<out>"`.

**Dependencies:** `ffmpeg` / `ffprobe`, ImageMagick (`montage`), Python `pillow` + `reportlab`,
`poppler-utils` (`pdftoppm`, `pdftotext`), and the **Poppins** font family. Install Poppins or
set `VE_FONTDIR` if `ad_lib` can't find it. The video drawtext labels fall back to DejaVu-Bold
(`VE_FONT`) since it's preinstalled everywhere.
