# jumbo-11x6: printable, photo-free postcard template

Built 2026-09-30 for the Oct 1 card. This is the real mailed size (11 x 6 in trim), unlike `postcard-template.html`, which is a 6 x 4 design mock.

- `card.html`: front + back with the October copy. Copy this folder into the session scratchpad, change the text, keep the structure. Coordinates are in px inside a 1056 x 576 trim box.
- `gw_logo.png`, `bp_compass.png`, `pattern.jpg`: real brand art pulled from the mailed 09/15/26 PDF (transparent PNGs, chevron background).
- `render.py`: writes `card_final.pdf` (11.472 x 6.472 in page, 3 mm bleed, crop marks, Trim/Bleed boxes) and PNG previews. `--qr "SMSTO:+16503084727:KEYWORD"` makes the text-to-me QR (`qr_timeline.png`).
- Lockup follows the Compass handbook: Compass strip wider than the GW logo, DRE at contact size, Eric and Janelle Boyenga DRE lines under the team logo.
- Back keeps the right half clear for the mailing address; the disclaimer runs vertically on the right edge.
- Final print file goes to `Documents\Farming List & mailers & letters\Farming Flyers to mail\Farming Flyers 2026\` as `Farming Postcard EPA MM DD YY.pdf`. Drafts stay in the scratchpad.
- Verify after rendering: decode the QR from the PDF (cv2.QRCodeDetector), check no em dashes, check both DRE numbers present.
