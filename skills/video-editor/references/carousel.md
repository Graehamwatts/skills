# Instagram carousel (10 slides, 1080x1350)

Engines: `scripts/carousel_lib.py` (renderer) + `scripts/make_carousel_pdf.py` (editable PDF).
Property-only by default: **no agent name, phone, website, or price.**

## Slide sequence (a swipeable tour)
1. **Cover** — exterior hero + gold `JUST LISTED` pill + address + a hook line + `SWIPE TO TOUR ›`.
2-9. **Feature slides** — one space each, with a bold LABEL + a one-line honest detail and a
   slide counter (`02 / 10`) top-right + a small address watermark top-left. Typical set:
   vaulted ceilings, open-concept living, granite island kitchen, bright bedrooms, upstairs
   loft, primary suite, spa bath, private patio.
10. **Recap** — gold-dot feature list + `NOW AVAILABLE IN <CITY>` + `‹ Swipe back to tour again`.

## Build
1. Extract ~10 graded 4K stills into `VE_CHEROES` (`s01_cover.png` ... `s10_close.png`).
2. In `carousel_lib.py` edit `SLIDES` (per slide: type cover/feat/close, hero file, focal,
   label, sub, or recap list) and `ADDR1`/`ADDR2`. The renderer is **ops-based**: each slide
   compiles to a list of draw primitives so the PNG and the PDF stay pixel-identical.
3. `render(i, "png")` for all 10 slides.
4. `make_carousel_pdf.py` builds the 10-page editable PDF from the same ops (clean photo +
   gradient overlay + vector frame + real Poppins text). **Verify with `pdftotext`.**

## The closing-slide trap (learned the hard way)
A recap slide wants a calm background, so it's tempting to reuse a front-elevation clip — but
those often contain the **realtor yard sign** = agent info. Use a clean **aerial** for the
closing instead, with a heavier scrim so the recap list reads. Scan every chosen still for
signage before rendering.

## Caption
Write a property-only IG caption (light, IG-native emoji is fine in the deliverable — it's
the product, not chat): a one-line hook, a short "what's inside" feature list (only verified
features), the address, a soft engagement prompt ("which room would you claim first?"), and a
block of local + category hashtags. **No phone, no name, no price.** Save as `Caption.txt`.

## Deliver
```
Instagram Carousel/
  Ready-to-Post-PNG/   (10 slides, numbered 01-10 so they upload in order)
  Canva-Editable-PDF/  (one 10-page PDF, real text)
  Caption.txt
  READ-ME_Carousel-Guide.txt
```
`present_files` a few slides + the PDF + the caption. Note that beds/baths/sq ft/price were
left off (not verifiable from footage) and offer to add a **stats slide** once given numbers —
that's the single highest-impact add.
