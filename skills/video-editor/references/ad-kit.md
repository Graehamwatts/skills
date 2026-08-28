# Just Listed ad kit

Engines: `scripts/ad_lib.py` (PNG renderer) + `scripts/make_ad_pdfs.py` (Canva-editable PDFs).
Minimal by design: the only text is the **stamp** (JUST LISTED / NEW LISTING) and the
**address** — no tagline, no agent info, no price (unless the user explicitly adds it).

## Concepts & sizes
3 hero concepts x 3 sizes = 9 ready-to-post PNGs:
- **Exterior** (best 3/4 curb shot) -> stamp `JUST LISTED` (gold pill)
- **Interior** (best bright room) -> stamp `NEW LISTING` (ink pill, gold outline)
- **Detail / lifestyle** (e.g. granite island) -> stamp `JUST LISTED`
Sizes: `1080x1350` (IG/FB portrait, highest impact), `1080x1080` (square),
`1200x628` (landscape — Google Display + FB link ads).

## Build
1. Extract 3 clean, graded 4K hero stills into `VE_HERO` (`hero_exterior.png`, etc.).
2. In `ad_lib.py` edit `CONCEPTS` (hero file, stamp text, style gold/ink, focal point),
   `SIZES` (sizes + per-size font sizes/margins), and `ADDR1`/`ADDR2`.
3. Render: `render(concept, sizekey, mode)` — `mode="png"` (flat, ready-to-post),
   `"plate"` (frame+gradient, no text — background for the PDF), `"clean"` (photo only).
   Drive it from a small loop (see `make_kit` pattern) to emit all 9 PNGs + plates + heroes.
4. `make_ad_pdfs.py` builds the 3 editable PDFs: clean photo layer + gradient overlay
   (`drawImage(..., mask='auto')`) + vector gold frame + **real Poppins text** (pill +
   address). **Verify with `pdftotext`** that the words come back.

## Framing
Center-crop most shots to each aspect with a focal point that keeps the subject and leaves
the busy detail out of the lower third (text zone). For very wide shots in the portrait/
square crops, bias the focal point rather than squashing.

## Deliver
Folder structure in the listing dir:
```
Just Listed Ads/
  Ready-to-Post-PNG/   (9 PNGs)
  Canva-Editable-PDF/  (3 PDFs, one per size, 3 concept pages each)
  Hero-Photos/         (3 clean graded JPGs, no text)
  READ-ME_Ad-Usage-and-Canva-Guide.txt
```
README covers: what's on the ads, where each size is used, how to edit in Canva (import PDF;
text is real Poppins; photo is a replaceable layer; frame+gradient are separate), and the
brand specs. `present_files` a representative set (the 3 portraits + the 3 PDFs).
Offer: IG Story 1080x1920, an "Offered at $___" or contact bar, or alternate hero swaps.
