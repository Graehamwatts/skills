# jumbo-11x6: the printer-template postcard builder (replaced 2026-10-15)

Builds the real mailed card: 11 x 6 in trim on the printer's 11.667 x 6.667 in template (page 840 x 480 pt, TrimBox inset 24 pt, BleedBox inset 15 pt, safe zone 9 pt inside trim). This is the geometry of the Canva-finished 10/01/26 file in `Farming Flyers 2026`, which is the authority if anything here disagrees with it.

## Use
1. Copy this folder to the session scratchpad (never build inside Graeham's folders).
2. Mint one Switchy link per QR: `skills/switchy-engine/scripts/create_postcard_link.py --date YYYY-MM-DD --hook "..." --dest <url> --market epa --archetype <slug> --slug epa-<name>-<mmdd>`. Switchy rejects `.php` destinations (the IDX sold-homes widget): reuse `https://hi.switchy.io/epa-sold-homes-0901`. For text-me cards use a static `SMSTO:+16503084727:KEYWORD` QR, no Switchy.
3. `python make_qr.py qr_<id>.png "<short link or SMSTO string>"` for each card.
4. Edit the `CARDS` list in `build_cards.py` (front lines, subline, back headline, body, visual, CTA), then `python build_cards.py [id ...]`. Writes `<id>.pdf` plus `<id>_front.png` / `<id>_back.png` to look at. Needs Playwright with Edge (`channel='msedge'`; the bundled Chromium may be missing after a Playwright update), pymupdf, qrcode, pillow.
5. Look at every page. Then QA: decode the back QR from the PDF (cv2.QRCodeDetector), no em/en dashes, DRE #01466876 and both Boyenga DRE lines on both pages, indicia present, nothing dark in the 9 pt band inside trim.
6. File ONLY the final PDFs in `Documents\Farming List & mailers & letters\Farming Flyers to mail\Farming Flyers 2026\` as `Farming Postcard EPA MM DD YY.pdf`. Before saving, list the folder: someone may already have a file with that name (on 2026-10-15 an old draft sat under the 11 01 26 name; it was renamed, not overwritten).

## Layout rules baked in
- Front: stacked headline auto-fit to width, subline, gold pill + giant phone, pointing headshot lower left (extracted from the mailed 09/15 PDF), lockup lower right. No front QR by default.
- Back: headline, short body, one visual (checks, chips or step strip), gold CTA line, giant phone + QR, lockup in the bottom band. Right half stays clear for the mailing address; indicia box (PRSRT STD / US POSTAGE PAID / HUNT. BCH CA / PERMIT #608) top right; legal disclaimer runs vertically on the right edge.
- Colors sampled from the mailed PDFs: gold #BFAB6D, ink #231F20. Front headlines use Montserrat 900 as a stand-in for Canva's Eagle Bold (the house font); Peter swaps the font in Canva if he finishes the file there.
- Compass handbook: Compass strip next to the GW logo, DRE at contact size, Eric and Janelle Boyenga DRE lines under the team logo.
- Assets: `gw_logo.png`, `bp_compass.png`, `photo_point.png`, `pattern.jpg` were pulled from `Farming Postcard EPA 09 15 26.pdf`. The finger-up pose is in that PDF too (page 2).
