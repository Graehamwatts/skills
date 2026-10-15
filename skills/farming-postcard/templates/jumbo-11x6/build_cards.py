"""Build printer-spec jumbo postcards (11x6 trim on the 11.667x6.667 UMW template).

Run:  python build_cards.py [card_id ...]   (no args = all cards in CARDS)
Needs in the same folder: gw_logo.png, bp_compass.png, photo_point.png, pattern.jpg, qr_<id>.png
Writes <id>.html, <id>.pdf (Trim/Bleed boxes set) and <id>_front.png / <id>_back.png previews.
"""
import os
import sys

import fitz
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))

GOLD = "#BFAB6D"   # sampled from the mailed 08/01 and 09/15 PDFs
INK = "#231F20"

PHONE = "650-308-4727"

CSS = """
@page { size: 1120px 640px; margin: 0; }
:root { --gold: __GOLD__; --ink: __INK__; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #fff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Montserrat', sans-serif; color: var(--ink); }
.page { position: relative; width: 1120px; height: 640px; overflow: hidden; page-break-after: always; background: #fff; }
.page:last-child { page-break-after: auto; }
.bleed { position: absolute; left: 20px; top: 20px; width: 1080px; height: 600px; background: #fff; overflow: hidden; }
.bleed::before { content: ''; position: absolute; inset: 0; background: url('pattern.jpg') center / cover no-repeat; opacity: .40; }
.bar-l { position: absolute; left: 0; top: 0; bottom: 0; width: 24px; background: var(--gold); }
.bar-b { position: absolute; left: 0; right: 0; bottom: 0; height: 24px; background: var(--gold); }
.t { position: absolute; left: 32px; top: 32px; width: 1056px; height: 576px; }
.mk { position: absolute; background: #000; }

.fl { display: block; width: max-content; font-weight: 900; text-transform: uppercase; white-space: nowrap; line-height: .98; letter-spacing: -1px; }
.fl.g { color: var(--gold); }
.fhead { position: absolute; left: 44px; top: 16px; }
.fsub { position: absolute; left: 46px; font-weight: 800; white-space: nowrap; }
.fsub .g, .g { color: var(--gold); }
.photo { position: absolute; left: 2px; width: auto; display: block; }
.fcta { position: absolute; }
.pill { display: inline-block; background: var(--gold); color: #fff; font-weight: 800; font-size: 38px; letter-spacing: .5px; padding: 8px 28px; border-radius: 14px; text-transform: uppercase; white-space: nowrap; }
.fphone { font-weight: 900; font-size: 80px; line-height: 1; letter-spacing: -1.5px; margin-top: 6px; white-space: nowrap; }
.flock { position: absolute; right: 26px; bottom: 14px; width: 380px; }
.flock .r1 { display: flex; align-items: center; gap: 16px; }
.flock .gw { height: 60px; }
.flock .bp { height: 40px; }
.flock .t1 { margin-top: 4px; font-size: 16px; font-weight: 800; }
.flock .t2 { font-size: 12.5px; line-height: 1.3; }
.flock .t3 { font-size: 11px; line-height: 1.25; margin-top: 1px; }

.bcol { position: absolute; left: 44px; top: 18px; width: 575px; }
.bh { font-family: 'Anton', sans-serif; text-transform: uppercase; line-height: 1.04; letter-spacing: -.2px; }
.bh .ln { display: block; width: max-content; white-space: nowrap; }
.bh .box { background: var(--gold); color: #fff; padding: 0 10px; display: inline-block; margin-left: -10px; }
.bh .box.mid { margin-left: 4px; margin-right: 4px; }
.bbody { font-style: italic; font-weight: 500; font-size: 16px; line-height: 1.42; margin-top: 8px; color: #2a2a2a; }
.bbody b { font-style: normal; font-weight: 800; }
.checks { margin-top: 8px; }
.checks div { font-weight: 700; font-size: 16px; line-height: 1.42; display: flex; align-items: center; gap: 10px; }
.checks svg { width: 19px; height: 19px; flex: none; }
.strip { display: flex; margin-top: 12px; width: 540px; }
.step { flex: 1; height: 38px; background: var(--ink); color: #fff; font-family: 'Anton', sans-serif; font-size: 14.5px; letter-spacing: .6px; display: flex; align-items: center; justify-content: center; text-transform: uppercase; white-space: nowrap;
  clip-path: polygon(0 0, calc(100% - 13px) 0, 100% 50%, calc(100% - 13px) 100%, 0 100%, 13px 50%); margin-left: -8px; padding-left: 8px; }
.step:first-child { margin-left: 0; padding-left: 0; clip-path: polygon(0 0, calc(100% - 13px) 0, 100% 50%, calc(100% - 13px) 100%, 0 100%); }
.step.gold { background: var(--gold); color: var(--ink); }
.chips { display: flex; gap: 8px; margin-top: 12px; }
.chip { background: var(--ink); color: #fff; font-family: 'Anton', sans-serif; font-size: 15px; letter-spacing: .6px; padding: 7px 12px 6px; border-radius: 6px; text-transform: uppercase; white-space: nowrap; }
.chip.gold { background: var(--gold); color: var(--ink); }
.bcta { font-family: 'Anton', sans-serif; font-size: 25px; letter-spacing: .4px; color: var(--gold); text-transform: uppercase; line-height: 1.1; margin-top: 12px; white-space: nowrap; }
.brow { display: flex; align-items: center; gap: 22px; margin-top: 4px; }
.bphone { font-family: 'Anton', sans-serif; font-size: 68px; line-height: 1; margin-left: -2px; white-space: nowrap; }
.bnote { font-style: italic; font-weight: 600; font-size: 13px; margin-top: 2px; color: #333; }
.qr { width: 84px; flex: none; }
.qr img { display: block; width: 84px; height: 84px; background: #fff; }
.qr .scan { background: #111; color: #fff; text-align: center; font-family: 'Anton', sans-serif; font-size: 14px; letter-spacing: 1.2px; padding: 2px 0 1px; }

.block { position: absolute; left: 36px; right: 40px; bottom: 12px; height: 72px; }
.block .gw { position: absolute; left: 0; bottom: 0; height: 72px; }
.block .mid { position: absolute; left: 172px; bottom: 0; }
.block .bp { display: block; height: 40px; margin-bottom: 3px; }
.block .team { font-size: 11px; line-height: 1.25; }
.block .c1 { position: absolute; left: 450px; bottom: 0; }
.block .c2 { position: absolute; left: 620px; bottom: 0; }
.block .role { font-weight: 800; font-size: 18px; letter-spacing: .5px; }
.block .dre { font-size: 14px; }
.block .ph { font-weight: 800; font-size: 22px; }
.block .em { font-size: 14px; line-height: 1.3; }

.indicia { position: absolute; left: 917px; top: 33px; width: 107px; height: 72px; border: 1px solid #000; background: #fff; text-align: center; font-family: Helvetica, Arial, sans-serif; font-size: 10px; line-height: 1.17; padding-top: 4px; z-index: 5; }
.indicia b { font-size: 11.5px; }
.disc { position: absolute; right: 14px; top: 12px; height: 552px; writing-mode: vertical-rl; transform: rotate(180deg); text-align: center; font-size: 9px; font-weight: 700; white-space: nowrap; color: #111; z-index: 8; }
""".replace("__GOLD__", GOLD).replace("__INK__", INK)

CHECK_SVG = ('<svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="10" fill="%s"/>'
             '<path d="M5.2 10.4l3.2 3.2 6.4-6.8" fill="none" stroke="#fff" stroke-width="2.4" '
             'stroke-linecap="round" stroke-linejoin="round"/></svg>' % GOLD)

MARKS = "".join(
    '<div class="mk" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"></div>' % m
    for m in [
        (0, 32, 14, 1), (32, 0, 1, 14), (1106, 32, 14, 1), (1088, 0, 1, 14),
        (0, 608, 14, 1), (32, 626, 1, 14), (1106, 608, 14, 1), (1088, 626, 1, 14),
    ]
)

JS = """
const $ = s => document.querySelector(s);
function fit(el, maxW, maxSize) {
  let s = maxSize; el.style.fontSize = s + 'px';
  while (el.getBoundingClientRect().width > maxW && s > 14) { s -= 0.5; el.style.fontSize = s + 'px'; }
}
document.fonts.ready.then(() => {
  document.querySelectorAll('.fhead .fl').forEach(el => fit(el, 972, +el.dataset.size));
  const fh = $('.fhead'), sub = $('.fsub');
  sub.style.top = (fh.offsetTop + fh.offsetHeight + 8) + 'px';
  fit(sub, 972, 27);
  const photo = $('.photo');
  const top = sub.offsetTop + sub.offsetHeight + 12;
  photo.style.top = top + 'px'; photo.style.height = (564 - top) + 'px';
  const cta = $('.fcta');
  cta.style.top = (top + 6) + 'px';
  cta.style.left = Math.max(250, photo.getBoundingClientRect().width + 14) + 'px';
  const lock = $('.flock'), ph = $('.fphone');
  let ps = 80;
  while (cta.getBoundingClientRect().bottom > lock.getBoundingClientRect().top - 8 && ps > 54) { ps -= 2; ph.style.fontSize = ps + 'px'; }
  document.querySelectorAll('.bh .ln').forEach(el => fit(el, 556, +el.dataset.size));
  window.__done = true;
});
"""


def head_front(lines):
    return "".join(
        '<div class="fl%s" data-size="%d">%s</div>' % (" g" if k == "g" else "", size, txt)
        for txt, k, size in lines
    )


def head_back(lines):
    out = []
    for txt, size in lines:
        out.append('<div class="ln" data-size="%d">%s</div>' % (size, txt))
    return "".join(out)


def visual(card):
    v = card["visual"]
    if v["type"] == "checks":
        return '<div class="checks">%s</div>' % "".join(
            "<div>%s<span>%s</span></div>" % (CHECK_SVG, t) for t in v["items"]
        )
    if v["type"] == "strip":
        parts = []
        for i, t in enumerate(v["items"]):
            parts.append('<div class="step%s">%s</div>' % (" gold" if i == 0 or i == len(v["items"]) - 1 else "", t))
        return '<div class="strip">%s</div>' % "".join(parts)
    if v["type"] == "chips":
        return '<div class="chips">%s</div>' % "".join(
            '<div class="chip%s">%s</div>' % (" gold" if i == 0 else "", t) for i, t in enumerate(v["items"])
        )
    return ""


def page_html(card):
    cid = card["id"]
    front = f"""
<div class="page"><div class="bleed"><div class="bar-l"></div><div class="bar-b"></div></div>
 <div class="t">
  <div class="fhead">{head_front(card["front_lines"])}</div>
  <div class="fsub">{card["front_sub"]}</div>
  <img class="photo" src="photo_point.png">
  <div class="fcta"><div class="pill">{card["pill"]}</div><div class="fphone">{PHONE}</div></div>
  <div class="flock">
   <div class="r1"><img class="gw" src="gw_logo.png"><img class="bp" src="bp_compass.png"></div>
   <div class="t1">REALTOR&reg;&nbsp; DRE #01466876</div>
   <div class="t2">graehamwatts@gmail.com &nbsp;|&nbsp; www.graehamwatts.com</div>
   <div class="t3">Eric Boyenga DRE #01254725 &nbsp;|&nbsp; Janelle Boyenga DRE #01254724</div>
  </div>
 </div>{MARKS}</div>"""
    back = f"""
<div class="page"><div class="bleed"><div class="bar-l"></div><div class="bar-b"></div></div>
 <div class="t">
  <div class="bcol">
   <div class="bh">{head_back(card["back_lines"])}</div>
   <div class="bbody" style="font-size:{card.get("body_px", 16.5)}px">{card["back_body"]}</div>
   {visual(card)}
   <div class="bcta">{card["cta"]}</div>
   <div class="brow">
    <div class="bphone">{PHONE}</div>
    <div class="qr"><img src="qr_{cid}.png"><div class="scan">SCAN ME</div></div>
   </div>
  </div>
  <div class="indicia">PRSRT STD<br>US POSTAGE<br><b>PAID</b><br>HUNT. BCH CA<br>PERMIT #608</div>
  <div class="block">
   <img class="gw" src="gw_logo.png">
   <div class="mid"><img class="bp" src="bp_compass.png"><div class="team">Eric Boyenga DRE #01254725<br>Janelle Boyenga DRE #01254724</div></div>
   <div class="c1"><div class="role">REALTOR&reg;</div><div class="dre">DRE #01466876</div></div>
   <div class="c2"><div class="ph">{PHONE}</div><div class="em">graehamwatts@gmail.com<br>www.graehamwatts.com</div></div>
  </div>
  <div class="disc">If your home is listed with another broker, please disregard this postcard. Homes not necessarily sold by this broker.</div>
 </div>{MARKS}</div>"""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{card["title"]}</title>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Montserrat:ital,wght@0,500;0,600;0,700;0,800;0,900;1,500;1,600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>{front}{back}<script>{JS}</script></body></html>"""


CARDS = [
    dict(
        id="1101", mail="11/01/26", title="Farming Postcard 11/01/26 - Year-end statement",
        front_lines=[("YOUR BANK SENT", "k", 78), ("YOU A STATEMENT.", "k", 78), ("YOUR HOME DIDN'T.", "g", 78)],
        front_sub="Your biggest asset never sends one. <span class=g>FLIP OVER.</span>",
        pill="CALL OR TEXT FOR YOURS",
        back_lines=[("GET YOUR HOME'S", 54), ('<span class="box">YEAR-END STATEMENT.</span>', 54)],
        back_body="Your home has likely changed in value since you last checked, and nobody mails you an update. I will. Send me your address and I'll send back your home's number and what nearby homes sold for this year.",
        visual=dict(type="checks", items=["What your home is worth today", "What nearby homes sold for", "Free, about 60 seconds"]),
        cta="SCAN, CALL OR TEXT FOR YOURS TODAY!",
        note="Free. Takes about 60 seconds.",
    ),
    dict(
        id="1115", mail="11/15/26", title="Farming Postcard 11/15/26 - Quiet holiday sale",
        front_lines=[("KEEP THE HOLIDAYS.", "k", 104), ("SELL QUIETLY.", "g", 112)],
        front_sub="No open house. No strangers in your home. <span class=g>FLIP OVER.</span>",
        pill="CALL OR TEXT ME THIS WEEK",
        back_lines=[("A PRIVATE SALE WORKS", 54), ('<span class="box">AROUND YOUR HOLIDAYS.</span>', 54)],
        back_body="Not every sale needs a sign in the yard and a Sunday open house. A private sale puts your home in front of serious buyers on a schedule that works for you. It isn't right for every home, so let's find out if it's right for yours. <b>Free, no obligation.</b>",
        body_px=15.5,
        visual=dict(type="checks", items=["No sign in the yard", "No open houses", "No strangers at your holiday dinner"]),
        cta="SEE IF IT FITS YOU. SCAN, CALL OR TEXT!",
        note="Free, no pressure, no obligation.",
    ),
    dict(
        id="1201", mail="12/01/26", title="Farming Postcard 12/01/26 - Prop 19 (2nd run)",
        front_lines=[("THE TAX BILL THAT", "k", 78), ("KEPT YOU PUT", "k", 78), ("MAY NOT APPLY.", "g", 78)],
        front_sub="Own your home and 55 or older? <span class=g>FLIP OVER.</span>",
        pill="CALL OR TEXT ME THIS WEEK",
        back_lines=[('CALIFORNIA <span class="box mid">CHANGED THE MATH</span>', 52), ("ON MOVING FOR OWNERS 55+", 52)],
        back_body="Since 2021, homeowners 55 and older can carry their current property tax base to a replacement home anywhere in California. Buy the new home within two years of selling. If it costs more, the difference is added to your base. <b>Not tax advice: confirm eligibility with your tax professional.</b>",
        visual=dict(type="chips", items=["Age 55+", "Anywhere in California", "Buy within 2 years"]),
        cta='TEXT &ldquo;PROP19&rdquo; FOR THE 2-MINUTE VERSION!',
        body_px=15.5,
        note="Free, no pressure. Or just call.",
    ),
    dict(
        id="1215", mail="12/15/26", title="Farming Postcard 12/15/26 - Winter window",
        front_lines=[("EVERYONE ELSE IS", "k", 78), ("WAITING FOR SPRING.", "k", 78), ("YOU DON'T HAVE TO.", "g", 78)],
        front_sub="Fewer homes for sale. More eyes on yours. <span class=g>FLIP OVER.</span>",
        pill="CALL OR TEXT ME THIS WEEK",
        back_lines=[("LIST BEFORE", 54), ('<span class="box">THE SPRING RUSH.</span>', 54)],
        back_body="Most owners wait for spring, and then a wave of new listings lands in the same few weeks. A home that comes on in January or February gets seen before that wave. If spring was your plan, the prep starts now. <b>Free, no pressure.</b>",
        visual=dict(type="strip", items=["DEC: PREP", "JAN: LIST", "FEB: OFFERS"]),
        cta="SEE WHAT YOUR HOME WOULD DO. SCAN OR CALL!",
        note="Free, no pressure.",
    ),
    dict(
        id="0101", mail="01/01/27", title="Farming Postcard 01/01/27 - 2026 sold map",
        front_lines=[("SEE WHAT HOMES", "k", 78), ("NEAR YOU SOLD FOR", "k", 78), ("IN 2026.", "g", 78)],
        front_sub="Recent sales on one map you can zoom. <span class=g>FLIP OVER.</span>",
        pill="CALL OR TEXT ME THIS WEEK",
        back_lines=[("SEE RECENT SALES", 54), ('<span class="box">ON ONE MAP.</span>', 54)],
        back_body="Sale prices are public, but nobody puts them in one place. Scan the code to see recent sales in East Palo Alto on a map you can zoom and pan, then call me and I'll tell you what they mean for your home. <b>Free, no pressure.</b>",
        visual=dict(type="strip", items=["SCAN", "SEE THE SALES", "CALL ME"]),
        cta="WHAT DOES IT MEAN FOR YOUR HOME? CALL ME!",
        note="Free home evaluation, no pressure.",
    ),
]


def build(card):
    cid = card["id"]
    html_path = os.path.join(HERE, f"{cid}.html")
    pdf_path = os.path.join(HERE, f"{cid}.pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page_html(card))
    with sync_playwright() as p:
        br = p.chromium.launch(channel='msedge')
        pg = br.new_page(viewport={"width": 1120, "height": 640})
        pg.goto("file:///" + html_path.replace("\\", "/"))
        pg.wait_for_load_state("networkidle")
        pg.wait_for_function("window.__done === true", timeout=20000)
        pg.wait_for_timeout(400)
        pg.pdf(path=pdf_path, width="1120px", height="640px", print_background=True, prefer_css_page_size=False,
               margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        br.close()
    d = fitz.open(pdf_path)
    for pgi in d:
        pgi.set_trimbox(fitz.Rect(24, 24, 816, 456))
        pgi.set_bleedbox(fitz.Rect(15, 15, 825, 465))
    tmp = pdf_path + ".tmp"
    d.save(tmp)
    d.close()
    os.replace(tmp, pdf_path)
    d = fitz.open(pdf_path)
    for i, name in enumerate(["front", "back"]):
        d[i].get_pixmap(dpi=100).save(os.path.join(HERE, f"{cid}_{name}.png"))
    print(cid, "pages", len(d), "size", d[0].rect, "trim", d[0].trimbox)


if __name__ == "__main__":
    want = sys.argv[1:]
    for c in CARDS:
        if not want or c["id"] in want:
            build(c)
