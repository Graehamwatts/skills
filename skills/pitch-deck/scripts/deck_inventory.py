#!/usr/bin/env python3
"""deck_inventory.py: read a deck PDF the two ways its first readers do.

A person skims a slide by size: the largest text is what they take in. A model
or a screening tool reads the text layer in file order: the first line on the
page is what it takes as the title. A deck can pass one read and fail the
other. A small category tag above a large claim is the usual case: a person
barely sees it, and the text-order reader sees nothing else.

For each page this prints:
  - the first content line in text order, with its size;
  - the headline as rendered: the largest line that reads as a sentence;
  - any figure or short line set larger than the headline;
  - the body text size, in points and as a share of the page height;
  - the word count, as a pointer to crowded slides;
  - flags: a tag as the first line, text larger than the headline, a word
    that letter-spacing may have split, no text layer.

Then a summary, with notes on the file name and the file size.

Optional outputs:
  --first-lines FILE    the first content line of each page, one per line
  --largest-lines FILE  the rendered headline of each page, one per line
  --images DIR          one PNG per page, for the render-and-read step
  --json                the whole report as JSON

Run skim_test.py on both line files. The largest lines are the skim a person
gets. The first lines are the skim a model gets.

Needs PyMuPDF (pip install pymupdf). Read-only on the PDF. Exit code 0 when
the report was produced, 2 on a usage error or a missing package.

This is an inventory, not a judge. It reports sizes and order. Open the page
images and read them yourself.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True  # leave no __pycache__ folder inside the skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from skim_test import is_category
except ImportError:  # the script still runs alone, without the tag check
    def is_category(text: str) -> bool:
        return False

GENERIC_NAMES = {
    "deck", "pitch", "pitchdeck", "pitch deck", "pitch-deck", "pitch_deck",
    "presentation", "slides", "untitled", "final", "investor deck", "draft",
    "document", "export", "output",
}
LARGE_FILE_MB = 10.0
RUNNING_SHARE = 0.6     # a line on this share of pages is a running header or footer
HEADLINE_RATIO = 1.3    # text this much larger than the body is headline-sized
TAG_MAX_WORDS = 8       # a first line this short, above a larger headline, is a tag
SINGLE_LETTERS_OK = {"a", "i", "x"}
# A word keeps its apostrophe, hyphen or inner full stop: founder's, x-ray, U.S.
# The curly apostrophe is built with chr() so this file stays plain ASCII.
WORD_RE = re.compile(r"[A-Za-z]+(?:['.%s-][A-Za-z]+)*" % chr(0x2019))


def norm_running(text: str) -> str:
    """A key that is the same for 'Page 3 of 15' and 'Page 4 of 15'."""
    return re.sub(r"\d+", "#", re.sub(r"\s+", " ", text.strip().lower()))


def word_count(text: str) -> int:
    return sum(1 for tok in text.split() if re.search(r"[A-Za-z0-9]", tok))


def reads_as_words(text: str) -> bool:
    return len(re.findall(r"[A-Za-z]{2,}", text)) >= 3


def pick_headline(lines: list):
    """The largest line that reads as a sentence, not as a figure or a name.

    A line of five words or more is preferred, so that "12 days" set huge is
    reported as a figure and the claim beside it as the headline.
    """
    for floor in (5, 3):
        found = [ln for ln in lines
                 if word_count(ln["text"]) >= floor and reads_as_words(ln["text"])]
        if found:
            return max(found, key=lambda ln: ln["size"])
    return None


def split_word_suspect(text: str) -> bool:
    """A stray single letter often means letter-spacing split a word.

    This catches "MARKE T SIZE". It cannot catch a split that leaves two
    real-looking pieces, so read the first lines yourself as well.
    """
    toks = WORD_RE.findall(text)
    if len(toks) < 2:
        return False
    return any(len(t) == 1 and t.lower() not in SINGLE_LETTERS_OK for t in toks)


def page_lines(page) -> list:
    """Text lines in file order: dicts with text, size, y0 and y1."""
    out = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
            if not spans:
                continue
            text = re.sub(r"\s+", " ", "".join(s["text"] for s in line["spans"])).strip()
            if not text:
                continue
            bbox = line.get("bbox", (0, 0, 0, 0))
            out.append({"text": text, "size": round(max(s["size"] for s in spans), 1),
                        "y0": bbox[1], "y1": bbox[3]})
    return out


def body_size(lines: list) -> float:
    """The size that carries the most characters on the page."""
    weight = Counter()
    for ln in lines:
        weight[ln["size"]] += len(ln["text"])
    return weight.most_common(1)[0][0] if weight else 0.0


def merge_wrapped(lines: list, body: float) -> list:
    """Join a headline that wraps onto a second line into one entry."""
    merged = []
    for ln in lines:
        prev = merged[-1] if merged else None
        if (prev and body and ln["size"] >= HEADLINE_RATIO * body
                and abs(ln["size"] - prev["size"]) <= 0.3
                and 0 <= ln["y0"] - prev["y0"] <= 1.8 * ln["size"]):
            prev["text"] += " " + ln["text"]
            prev["y1"] = ln["y1"]
        else:
            merged.append(dict(ln))
    return merged


def inventory(path: Path, images_dir: Path = None, width: int = 1600) -> dict:
    import fitz  # PyMuPDF

    doc = fitz.open(str(path))
    raw = [page_lines(page) for page in doc]

    # Lines that repeat on most pages are running headers or footers.
    seen = Counter()
    for lines in raw:
        for key in {norm_running(ln["text"]) for ln in lines}:
            seen[key] += 1
    need = max(3, int(RUNNING_SHARE * len(raw) + 0.999))
    running = {key for key, n in seen.items() if n >= need}

    pages = []
    for number, (page, lines) in enumerate(zip(doc, raw), start=1):
        content = [ln for ln in lines if norm_running(ln["text"]) not in running]
        body = body_size(content)
        merged = merge_wrapped(content, body)
        with_letters = [ln for ln in merged if re.search(r"[A-Za-z]", ln["text"])]
        first = with_letters[0] if with_letters else None
        headline = pick_headline(merged)
        largest = max(merged, key=lambda ln: ln["size"]) if merged else None

        flags = []
        larger = None
        if not merged:
            flags.append("no text layer: a reader of the text gets nothing from this page")
        if first and headline and first is not headline:
            is_tag = (first["size"] < headline["size"]
                      and word_count(first["text"]) <= TAG_MAX_WORDS)
            if is_tag and is_category(first["text"]):
                flags.append("a category tag is the first text line: delete it")
            elif is_tag:
                flags.append("a tag is the first text line: keep it only if it says "
                             "something the headline lacks")
            else:
                flags.append("the first text line is not the headline")
        elif first and is_category(first["text"]):
            flags.append("a category title is the headline")
        if largest and headline and largest["size"] > headline["size"] + 0.3:
            larger = largest
            if re.search(r"\d", largest["text"]):
                flags.append("a figure is set larger than the headline")
            else:
                flags.append("a short line is set larger than the headline")
        if any(split_word_suspect(ln["text"]) for ln in merged):
            flags.append("a word may be split in the text layer")

        height = page.rect.height or 1.0
        pages.append({
            "page": number,
            "words": sum(word_count(ln["text"]) for ln in content),
            "first_line": first["text"] if first else "",
            "first_line_size": first["size"] if first else 0.0,
            "headline": headline["text"] if headline else "",
            "headline_size": headline["size"] if headline else 0.0,
            "big_figure": larger["text"] if larger else "",
            "big_figure_size": larger["size"] if larger else 0.0,
            "body_size": body,
            "body_share_of_height": round(100.0 * body / height, 1),
            "split_suspects": [ln["text"] for ln in merged if split_word_suspect(ln["text"])],
            "flags": flags,
        })

        if images_dir is not None:
            zoom = width / (page.rect.width or 1.0)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            pix.save(str(images_dir / ("page-%02d.png" % number)))
    doc.close()

    file_notes = []
    stem = re.sub(r"[\s_-]*(v\d+|final|copy|\(\d+\))$", "", path.stem.lower()).strip()
    if stem in GENERIC_NAMES or path.stem.lower() in GENERIC_NAMES:
        file_notes.append('The file is named "%s". Name it with the company, the stage, '
                          "the month and the year." % path.name)
    size_mb = path.stat().st_size / (1024.0 * 1024.0)
    if size_mb > LARGE_FILE_MB:
        file_notes.append("The file is %.1f MB. That is large for an email attachment."
                          % size_mb)

    def count(flag_start: str) -> list:
        return [p["page"] for p in pages if any(f.startswith(flag_start) for f in p["flags"])]

    return {
        "file": path.name,
        "size_mb": round(size_mb, 1),
        "page_count": len(pages),
        "running_lines_skipped": len(running),
        "pages": pages,
        "tag_first_pages": sorted(count("a category tag is the first")
                                  + count("a tag is the first")),
        "category_tag_pages": count("a category tag is the first"),
        "category_headline_pages": count("a category title is the headline"),
        "big_figure_pages": sorted(count("a figure is set larger")
                                   + count("a short line is set larger")),
        "split_word_pages": count("a word may be split"),
        "no_text_pages": count("no text layer"),
        "file_notes": file_notes,
    }


def short(text: str, limit: int = 96) -> str:
    return text if len(text) <= limit else text[:limit - 3] + "..."


def print_report(rep: dict) -> None:
    size = "%.1f MB" % rep["size_mb"] if rep["size_mb"] >= 0.1 else "under 0.1 MB"
    print("Deck inventory: %s (%d pages, %s)" % (rep["file"], rep["page_count"], size))
    if rep["running_lines_skipped"]:
        print("Running header or footer lines left out: %d." % rep["running_lines_skipped"])
    print()
    for p in rep["pages"]:
        print("Page %d: %d words, body text %.1f pt (%.1f%% of the page height)"
              % (p["page"], p["words"], p["body_size"], p["body_share_of_height"]))
        print("  first in text order  [%5.1f pt]  %s"
              % (p["first_line_size"], short(p["first_line"]) or "(none)"))
        print("  headline as rendered [%5.1f pt]  %s"
              % (p["headline_size"], short(p["headline"]) or "(none)"))
        if p["big_figure"]:
            print("  largest text         [%5.1f pt]  %s"
                  % (p["big_figure_size"], short(p["big_figure"])))
        for text in p["split_suspects"][:3]:
            print("  check this line: %s" % short(text))
        for flag in p["flags"]:
            print("  ! %s" % flag)
    print()
    print("Summary")
    total = rep["page_count"]

    def line(label: str, pages: list) -> None:
        where = ", ".join(str(n) for n in pages) if pages else "none"
        print("  %-52s %d of %d (pages: %s)" % (label, len(pages), total, where))

    line("A tag comes before the headline in text order:", rep["tag_first_pages"])
    line("  of those, the tag is a category label:", rep["category_tag_pages"])
    line("A category title is the headline:", rep["category_headline_pages"])
    line("Text is set larger than the headline:", rep["big_figure_pages"])
    line("A word may be split in the text layer:", rep["split_word_pages"])
    line("No text layer:", rep["no_text_pages"])
    for note in rep["file_notes"]:
        print("  - %s" % note)
    print()
    print("A reader of the text layer takes the first line of a page as its title.")
    print("Text larger than the headline is read first by eye. Check that it is the")
    print("number the headline is about, with its unit and its kind beside it.")
    print("The word count includes text inside a screenshot or a mock screen.")
    print("Open the page images and read every slide. This report does not replace that.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="deck_inventory.py",
        description=("Inventory a deck PDF by text order and by type size: the first text "
                     "line of each page, the rendered headline, any figure set larger "
                     "than the headline, and the word count."),
        epilog=("Example: python deck_inventory.py deck.pdf --first-lines first.txt "
                "--largest-lines largest.txt --images renders. Then run skim_test.py "
                "on both text files."),
    )
    parser.add_argument("pdf", help="path to the deck PDF")
    parser.add_argument("--first-lines", metavar="FILE",
                        help="write the first content line of each page, one per line")
    parser.add_argument("--largest-lines", metavar="FILE",
                        help="write the rendered headline of each page, one per line")
    parser.add_argument("--images", metavar="DIR",
                        help="write one PNG per page into this folder")
    parser.add_argument("--width", type=int, default=1600,
                        help="pixel width of the page images (default 1600)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    path = Path(args.pdf)
    if not path.is_file():
        print("deck_inventory.py: file not found: %s" % args.pdf, file=sys.stderr)
        return 2
    try:
        import fitz  # noqa: F401
    except ImportError:
        print("deck_inventory.py: this script needs PyMuPDF. Install it with: "
              "pip install pymupdf", file=sys.stderr)
        return 2
    if args.width < 200:
        print("deck_inventory.py: --width must be at least 200", file=sys.stderr)
        return 2

    images_dir = None
    if args.images:
        images_dir = Path(args.images)
        images_dir.mkdir(parents=True, exist_ok=True)

    rep = inventory(path, images_dir, args.width)

    if args.first_lines:
        Path(args.first_lines).write_text(
            "\n".join(p["first_line"] or "(no text)" for p in rep["pages"]) + "\n",
            encoding="utf-8")
    if args.largest_lines:
        Path(args.largest_lines).write_text(
            "\n".join(p["headline"] or "(no text)" for p in rep["pages"]) + "\n",
            encoding="utf-8")

    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print_report(rep)
        if images_dir is not None:
            print("Page images written to: %s" % images_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
