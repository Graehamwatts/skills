# Brand system — black & gold

One look across every deliverable so videos, ads, and the carousel feel like a set.

## Tokens
- Ink / black `#0E0C0A`  (RGB 14,12,10)
- Gold `#C7A974`  (199,169,116)
- Off-white `#F4EEE3`  (244,238,227)
- Light gold `#DEC9A2`  (222,201,162)
- Muted `#BBAB8E`  (187,171,142)
- Ink pill fill `#12100D` (slightly lifted ink, for the "NEW LISTING" pill)

## Fonts — Poppins
- **Bold** = address / feature labels
- **Medium** = stamp pill, kickers, "now available" lines
- **Light** = city line, sub-lines, body (use ~0.16x letter-spacing/tracking on caps lines)
`ad_lib.py` auto-detects the Poppins dir; video drawtext labels use DejaVu-Bold (preinstalled)
so they work even where Poppins isn't.

## Image grade (stills + video)
`eq=contrast=1.06:saturation=1.10:brightness=0.004:gamma=0.99,unsharp=3:3:0.5:3:3:0` — mild
contrast/sat + a touch of sharpening after the 4K->1080 downscale. For the warmer "hero"
agent clips pull warmth so cuts don't jump: add
`colorbalance=rm=-0.04:rh=-0.03:bm=0.02` (this is `GRADE_HERO` in `video_lib.sh`).

## Layout language
- **Gold inset frame**: thin rectangle inset ~`margin` px from the edge, stroke ~3-4 px.
- **Stamp pill** (top-left): rounded pill. "JUST LISTED" = solid **gold** fill, ink text.
  "NEW LISTING" = **ink** fill, gold outline, off-white text. Uppercase Poppins-Medium, tracked.
- **Lower-third gradient**: dark (`#080706`) ramp from ~50% height to the bottom so white
  text is readable; a faint top gradient helps the stamp.
- **Address lockup** (lower-left): `909 BAINES ST` in Poppins-Bold, a short **gold rule**,
  then `EAST PALO ALTO, CALIFORNIA` in tracked Poppins-Light light-gold. Keep it to the
  **stamp + address only** unless the user asks for more (no tagline by default).

## Video text helpers (in `video_lib.sh`)
- `label16 'TEXT' appear disappear` — bottom-left feature label + gold underline (1920x1080).
- `title16 'BIG' 'small' appear disappear` — centered opening title (e.g. address).
- `capR 'TEXT' appear disappear` — centered reel caption near the upper third (1080x1920),
  with a soft box + gold underline. Captions fade in/out via an alpha expression.

## File-naming conventions
- Videos: `<Addr>-WALKTHROUGH-16x9.mp4`, `<Addr>-REEL-1-9x16.mp4`, `<Addr>-REEL-2-9x16.mp4`.
- Ads: `<Addr>_<Concept>-<Stamp>_<WxH>-<Size>.png` (e.g. `_Exterior-JustListed_1080x1080-Square.png`).
- Carousel: numbered `..._Carousel_01-Cover.png` ... `_10-Recap.png` so they upload in order.
Deliver into the user's listing folder in tidy subfolders: `Ready-to-Post-PNG/`,
`Canva-Editable-PDF/`, `Hero-Photos/`, plus a short `READ-ME` and (carousel) `Caption.txt`.
