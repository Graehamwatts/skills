#!/usr/bin/env python3
"""Build the sample deck PDF used by eval 4.

The company (Gapwren), its founder and every figure are invented. The deck is
six slides and carries three planted problems that only show in a rendered
file, not in pasted text:

  1. A small category tag above the headline on slides 2 to 6. Each tag is
     10 pt, under a 30 pt headline and smaller than the 14 pt body text, so a
     person barely sees it. It is the first line in the text layer, so a model
     or a screening tool reads it as the title.
  2. On slide 4 a figure ("2,400") is set at 96 pt, three times the headline.
     It is the founder's career patient count, not the number the headline is
     about, and it can be mistaken for product usage.
  3. On slide 5 a comparison table holds text in the alternatives' cells and
     blanks where nothing was found, while the company's column is all ticks.

The ask on slide 6 is arithmetic that reconciles, on purpose, so a review has
something sound to record under what already works.

Usage: python make_sample_deck.py [output.pdf]
Needs PyMuPDF (pip install pymupdf).
"""
import sys
from pathlib import Path

import fitz  # PyMuPDF

W, H = 960, 540
INK = (0.10, 0.12, 0.16)
MUTED = (0.42, 0.45, 0.50)
ACCENT = (0.05, 0.40, 0.36)
RULE = (0.80, 0.82, 0.85)
LEFT = 64


def put(page, x, y, text, size, bold=False, color=INK):
    page.insert_text((x, y), text, fontsize=size,
                     fontname="hebo" if bold else "helv", color=color)


def tag(page, text):
    put(page, LEFT, 62, text, 10, bold=True, color=ACCENT)


def headline(page, lines, top=112):
    for n, line in enumerate(lines):
        put(page, LEFT, top + n * 38, line, 30, bold=True)


def rows(page, items, top=230, gap=34):
    for n, (label, line) in enumerate(items):
        y = top + n * gap
        put(page, LEFT, y, label, 14, bold=True)
        put(page, LEFT + 190, y, line, 14)


def source(page, text):
    put(page, LEFT, H - 34, text, 9, color=MUTED)


def tick(page, x, y):
    page.draw_line((x, y), (x + 6, y + 7), color=ACCENT, width=2.6)
    page.draw_line((x + 6, y + 7), (x + 18, y - 9), color=ACCENT, width=2.6)


def build(out: Path) -> None:
    doc = fitz.open()

    # 1. Cover
    p = doc.new_page(width=W, height=H)
    put(p, LEFT, 70, "Gapwren", 14, bold=True, color=ACCENT)
    put(p, LEFT, 210, "Gapwren refills cancelled physical therapy", 34, bold=True)
    put(p, LEFT, 254, "slots by text, before the hour is lost", 34, bold=True)
    put(p, LEFT, 312, "Built by a physical therapist who owned a four-therapist "
        "clinic for nine years", 14)
    put(p, LEFT, 346, "Pre-launch. In daily use at one clinic since May 2026.", 11,
        color=MUTED)
    put(p, LEFT, H - 34, "founder@gapwren.example", 9, color=MUTED)

    # 2. Problem
    p = doc.new_page(width=W, height=H)
    tag(p, "THE PROBLEM")
    headline(p, ["Our clinic lost 148 visit slots to late", "cancellations in ten weeks"])
    rows(p, [
        ("The call comes late", "Most cancellations arrive the same morning"),
        ("Nobody refills it", "The front desk is busy checking patients in"),
        ("The hour is gone", "The therapist is paid and the room sits empty"),
    ])
    source(p, "Source: the founder's clinic schedule, 148 cancelled slots, May to July 2026")

    # 3. Solution
    p = doc.new_page(width=W, height=H)
    tag(p, "THE SOLUTION")
    headline(p, ["Gapwren texts the waitlist the minute", "a patient cancels"])
    rows(p, [
        ("It texts in order", "Patients who asked for an earlier visit hear first"),
        ("The first yes gets it", "The calendar updates without a phone call"),
        ("The desk sees it", "One line on the day sheet, and nothing to chase"),
    ])
    p.draw_rect(fitz.Rect(640, 214, 896, 420), color=RULE, width=1.2)
    put(p, 656, 240, "A slot opened at 2:30 today.", 11)
    put(p, 656, 260, "Reply YES to take it.", 11)
    put(p, 656, 300, "YES", 11, bold=True)
    put(p, 656, 340, "You are booked for 2:30.", 11)
    put(p, 656, 406, "Sample data", 9, color=MUTED)

    # 4. Proof
    p = doc.new_page(width=W, height=H)
    tag(p, "PROOF")
    headline(p, ["At our own clinic Gapwren refilled 61", "of 148 cancelled slots"])
    put(p, 600, 300, "2,400", 96, bold=True, color=ACCENT)
    put(p, 606, 328, "patients treated", 12)
    put(p, 606, 346, "at the founder's clinic, 2016 to 2025", 9, color=MUTED)
    rows(p, [
        ("Started", "January 2026"),
        ("Built by", "The founder and one contract engineer"),
        ("In daily use", "One clinic since May 2026"),
    ], top=250)
    p.draw_line((LEFT, 392), (W - LEFT, 392), color=RULE, width=1)
    put(p, LEFT, 420, "Done", 12, bold=True)
    put(p, LEFT + 60, 420, "Text refill at one clinic, May 2026", 12)
    put(p, LEFT, 444, "Now", 12, bold=True)
    put(p, LEFT + 60, 444, "A second clinic, October 2026", 12)
    put(p, LEFT, 468, "Next", 12, bold=True)
    put(p, LEFT + 60, 468, "The first paying clinics, January 2027", 12)
    source(p, "Source: clinic schedule, ten weeks from May 2026")

    # 5. Competition
    p = doc.new_page(width=W, height=H)
    tag(p, "THE COMPETITION")
    headline(p, ["Clinics refill slots by phone because", "scheduling tools stop at the calendar"])
    cols = [LEFT, 330, 470, 640, 800]
    heads = ["", "By hand", "The scheduling tool", "A front desk hire", "Gapwren"]
    y = 226
    for x, text in zip(cols, heads):
        put(p, x, y, text, 12, bold=True)
    p.draw_line((LEFT, y + 10), (W - LEFT, y + 10), color=RULE, width=1)
    table = [
        ("Texts the waitlist when a slot opens",
         ["Calls, one by one", "Email reminder only", "Calls, one by one"]),
        ("Fills the slot without a phone call", ["", "", ""]),
        ("Works from the clinic's own calendar", ["On paper", "Yes", ""]),
    ]
    for n, (label, cells) in enumerate(table):
        ry = y + 44 + n * 46
        put(p, LEFT, ry, label, 12)
        for x, text in zip(cols[1:4], cells):
            if text:
                put(p, x, ry, text, 12, color=MUTED)
        tick(p, cols[4] + 14, ry - 4)
        p.draw_line((LEFT, ry + 16), (W - LEFT, ry + 16), color=RULE, width=0.6)
    source(p, "Source: scheduling tool help pages, read October 2026")

    # 6. The ask
    p = doc.new_page(width=W, height=H)
    tag(p, "THE ASK")
    headline(p, ["We are raising $600,000 to reach 120", "paying clinics in 18 months"])
    rows(p, [
        ("Price", "$180 a month for each clinic"),
        ("At 120 clinics", "120 x $180 x 12 = $259,200 a year (Estimate)"),
        ("Use of funds", "Product $280,000, reaching clinics $200,000, running the company $120,000"),
        ("Runway", "18 months at about $33,000 a month"),
        ("Next step", "A 30 minute call to walk through one clinic's schedule"),
    ], gap=32)
    source(p, "Estimate inputs: the price is the founder's own. The clinic count is the milestone.")

    doc.set_metadata({"title": "Gapwren sample deck (invented company, for testing)"})
    doc.save(str(out), garbage=4, deflate=True)
    doc.close()


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name(
        "gapwren-seed-draft.pdf")
    build(target)
    print("wrote %s" % target)
