"""Render card.html to a printable jumbo postcard PDF (11x6 in trim, 3 mm bleed, crop marks).

Usage:  python render.py [workdir]
Copy this whole folder to the session scratchpad first, edit card.html there, then run.
Optional first step for a text-to-me QR:  python render.py --qr "SMSTO:+16503084727:TIMELINE"
Output: <workdir>/card_final.pdf plus prev_1.png / prev_2.png (front / back previews).
Needs: playwright (chromium), pymupdf (fitz), qrcode, pillow.
"""
import os
import sys

import fitz
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
if args[:1] == ["--qr"]:
    import qrcode

    here = os.path.dirname(os.path.abspath(__file__))
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=16, border=2)
    q.add_data(args[1])
    q.make(fit=True)
    q.make_image(fill_color="#111111", back_color="#ffffff").save(os.path.join(here, "qr_timeline.png"))
    print("qr written (card.html references qr_timeline.png)")
    sys.exit(0)

B = os.path.abspath(args[0]) if args else os.path.dirname(os.path.abspath(__file__))
html = os.path.join(B, "card.html")
raw = os.path.join(B, "card_raw.pdf")
final = os.path.join(B, "card_final.pdf")

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page()
    pg.goto("file:///" + html.replace("\\", "/"))
    pg.wait_for_load_state("networkidle")
    pg.wait_for_timeout(800)
    pg.pdf(path=raw, width="11.472in", height="6.472in", print_background=True, prefer_css_page_size=True,
           margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    br.close()

d = fitz.open(raw)
for pg in d:
    w, h = pg.rect.width, pg.rect.height
    t, b = 0.236 * 72, 0.118 * 72
    pg.set_trimbox(fitz.Rect(t, t, w - t, h - t))
    pg.set_bleedbox(fitz.Rect(b, b, w - b, h - b))
d.save(final)
d.close()

d = fitz.open(final)
for i, pg in enumerate(d):
    pg.get_pixmap(dpi=110).save(os.path.join(B, f"prev_{i + 1}.png"))
print("wrote", final)
