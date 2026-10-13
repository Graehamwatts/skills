#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Seller report previews: phone and desktop pictures of a built page, a layout check on narrow phones, and
the PDF from the print layout.

    python render_previews.py <page.html> [--name NAME] [--out DIR]     pictures, then the layout check
    python render_previews.py --check <page.html> [<page.html> ...]     layout check only, no pictures
    python render_previews.py --pdf <print.html> <report.pdf>           print the PDF (build the page with --print)

Pictures are written as <out>\<name>_phone_NN.png (390 px wide) and <out>\<name>_desktop_NN.png (680 px), in
tiles 1400 px tall, so a person or Claude can read them one screen at a time. --out defaults to a "previews"
folder beside the page, and --name to the page's file name.

Needs Microsoft Edge. The pictures also need Pillow; the check and the PDF do not. Phone renders come from an
iframe of the exact width, because Edge headless will not open a window narrower than about 500 px. Temporary
files go to the system temp folder.

Layout check, run at 390, 360 and 320 px:
    - the page does not scroll sideways
    - in "Every week in one table": no header is wider than its column, and no week row is taller than its
      two lines (week number over date), which is what a wrapped date looks like
    - every chart bar is its fixed height (a bar that grows with its row means a label wrapped into it)
    - every link is at least 40 px tall
    - no text is under 12 px
A failure at 390 or 360 ends with exit code 1. At 320 it is reported as a warning.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

TMP = os.path.join(tempfile.gettempdir(), "seller-report-previews")
EDGE_PATHS = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")
CHECK_WIDTHS = (390, 360, 320)
PHONE_W, DESKTOP_W, TILE_H = 390, 680, 1400
MIN_TAP, MIN_FONT = 40, 12

# Runs inside the page copy. Everything it finds goes back to the wrapper page as one JSON string.
PROBE = """
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var r = {width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight,
             headers: [], rows: [], bars: [], links: [], minFont: 99, tables: 0};
    document.querySelectorAll('table').forEach(function (t) {
      if ((t.getAttribute('style') || '').indexOf('table-layout:fixed') < 0) { return; }
      r.tables += 1;
      t.querySelectorAll('tr').forEach(function (tr, i) {
        var cells = tr.children;
        if (i === 0) {
          for (var k = 0; k < cells.length; k++) {
            if (cells[k].scrollWidth > cells[k].clientWidth) { r.headers.push(cells[k].textContent.trim() + ' needs ' + cells[k].scrollWidth + ' has ' + cells[k].clientWidth); }
          }
        } else if (cells.length > 1) {
          var lh = parseFloat(getComputedStyle(cells[1]).lineHeight) || 18.2;
          var pad = parseFloat(getComputedStyle(cells[0]).paddingTop) + parseFloat(getComputedStyle(cells[0]).paddingBottom);
          if (tr.offsetHeight > 2 * lh + pad + 3) { r.rows.push(cells[0].textContent.trim() + ' is ' + tr.offsetHeight + ' px tall'); }
        }
      });
    });
    document.querySelectorAll('td[height]').forEach(function (td) {
      var want = parseInt(td.getAttribute('height'), 10);
      if (Math.abs(td.offsetHeight - want) > 1) { r.bars.push('bar is ' + td.offsetHeight + ' px, set to ' + want); }
    });
    document.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getBoundingClientRect().height;
      if (h < MIN_TAP) { r.links.push(a.textContent.trim().slice(0, 40) + ' is ' + Math.round(h) + ' px tall'); }
    });
    document.querySelectorAll('body *').forEach(function (el) {
      var own = false;
      for (var n = el.firstChild; n; n = n.nextSibling) { if (n.nodeType === 3 && n.nodeValue.replace(/[\\s\\u00a0]/g, '')) { own = true; } }
      if (own && el.getBoundingClientRect().height > 0) {
        var fs = parseFloat(getComputedStyle(el).fontSize);
        if (fs > 2 && fs < r.minFont) { r.minFont = fs; }
      }
    });
    window.parent.postMessage(JSON.stringify(r), '*');
  }, 800);
});
</script>
""".replace("MIN_TAP", str(MIN_TAP))
WRAP = ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:#ff00ff}'
        'iframe{display:block;border:0;width:%dpx;height:%dpx;background:#fff}</style></head><body><iframe src="%s"></iframe>'
        '<script>window.addEventListener("message",function(e){var p=document.createElement("pre");p.id="result";'
        'p.textContent="RESULT::"+e.data+"::END";document.body.appendChild(p);});</script></body></html>')


def edge_path():
    for p in EDGE_PATHS:
        if os.path.exists(p):
            return p
    raise SystemExit("Microsoft Edge was not found. Previews, the layout check and the PDF need it.")


def url(path):
    return "file:///" + os.path.abspath(path).replace("\\", "/").replace(" ", "%20").replace("#", "%23")


def edge(args, timeout=300):
    os.makedirs(TMP, exist_ok=True)
    return subprocess.run([edge_path(), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                           "--user-data-dir=" + os.path.join(TMP, "profile")] + args,
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout)


def shot(page_url, png, w, h):
    if os.path.exists(png):
        os.remove(png)
    edge(["--virtual-time-budget=20000", "--run-all-compositor-stages-before-draw", "--window-size=%d,%d" % (w, h), "--screenshot=" + png, page_url])
    if not os.path.exists(png):
        raise SystemExit("Edge did not write %s" % png)


def tiles(png, prefix, crop=None, tile=TILE_H):
    """Cuts a tall screenshot into tiles. Returns (page height, number of tiles, True when the page was cut off)."""
    import site
    sys.path.append(site.getusersitepackages())      # python -I turns the per-user folder off; Pillow lives there
    try:
        from PIL import Image, ImageChops
    except ImportError:
        raise SystemExit("Pillow is not installed. The pictures need it (python -m pip install --user Pillow). --check and --pdf do not.")
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(png).convert("RGB")
    if crop:
        im = im.crop((0, 0, crop, im.size[1]))
    w, h = im.size
    box = ImageChops.difference(im, Image.new("RGB", im.size, im.getpixel((2, h - 2)))).getbbox()
    bottom = min(h, (box[3] if box else h) + 24)
    y, n = 0, 1
    while y < bottom:
        y2 = min(bottom, y + tile)
        im.crop((0, y, w, y2)).save("%s_%02d.png" % (prefix, n))
        y, n = y2, n + 1
    return bottom, n - 1, bottom >= h - 5


def page_height(html, width):
    r = probe(html, "height", width)
    return int(r["height"]) if r else None


def render(html, name, out_dir):
    """Writes the phone and desktop tiles for one page. Returns the list of files written."""
    html = os.path.abspath(html)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(out_dir):
        if re.match(re.escape(name) + r"_(phone|desktop)_\d+\.png$", f):
            os.remove(os.path.join(out_dir, f))
    written = []
    for kind, width in (("phone", PHONE_W), ("desktop", DESKTOP_W)):
        h = (page_height(html, width) or 30000) + 200         # the true height first, so nothing is cut off
        png = os.path.join(TMP, "%s_%s.png" % (name, kind))
        if kind == "phone":
            wrap = os.path.join(TMP, name + "_wrap.html")
            with open(wrap, "w", encoding="utf-8") as f:
                f.write('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:#ff00ff}'
                        'iframe{display:block;border:0;width:%dpx;height:%dpx;background:#fff}</style></head><body><iframe src="%s"></iframe></body></html>'
                        % (width, h, url(html)))
            shot(url(wrap), png, 600, h)
            bottom, n, cut = tiles(png, os.path.join(out_dir, name + "_phone"), crop=width)
        else:
            shot(url(html), png, width, h)
            bottom, n, cut = tiles(png, os.path.join(out_dir, name + "_desktop"))
        print("%s %s %d: height %d px, %d tiles%s" % (name, kind, width, bottom, n, "  CUT OFF, the page is taller" if cut else ""))
        written += [os.path.join(out_dir, "%s_%s_%02d.png" % (name, kind, i)) for i in range(1, n + 1)]
    return written


def probe(html, name, width):
    """Measures one page at one width. Returns the dict the probe script posts, or None if Edge gave nothing."""
    os.makedirs(TMP, exist_ok=True)
    with open(html, encoding="utf-8") as f:
        src = f.read()
    # the copy sits beside the page, so the page's relative image paths still resolve
    copy = os.path.join(os.path.dirname(os.path.abspath(html)), "~probe_%s_%d.html" % (re.sub(r"\W+", "_", name), os.getpid()))
    wrap = os.path.join(TMP, "%s_probe_wrap_%d.html" % (re.sub(r"\W+", "_", name), width))
    try:
        with open(copy, "w", encoding="utf-8") as f:
            f.write(src.replace("</body>", PROBE + "</body>"))
        with open(wrap, "w", encoding="utf-8") as f:
            f.write(WRAP % (width, 2000, url(copy)))
        out = edge(["--virtual-time-budget=20000", "--window-size=900,2200", "--dump-dom", url(wrap)]).stdout.decode("utf-8", "replace")
    finally:
        if os.path.exists(copy):
            os.remove(copy)
    mt = re.search(r'<pre id="result">RESULT::(.*?)::END</pre>', out, re.S)
    return json.loads(mt.group(1).replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")) if mt else None


def check(html, name):
    """Runs the layout check at each width. Returns (problems that fail the run, warnings)."""
    fails, warns = [], []
    for w in CHECK_WIDTHS:
        r = probe(html, name, w)
        if r is None:
            fails.append("%s at %d: no measurement came back from Edge" % (name, w))
            continue
        found = []
        if r["width"] != w:
            found.append("the test frame was %d px wide, not %d" % (r["width"], w))
        if r["scrollWidth"] > r["width"]:
            found.append("the page scrolls sideways: content is %d px wide" % r["scrollWidth"])
        if not r["tables"]:
            found.append("the weekly table was not found")
        found += ["weekly table header: " + t for t in r["headers"]]
        found += ["weekly table row: " + t for t in r["rows"]]
        found += sorted(set(r["bars"]))
        found += ["link under %d px: %s" % (MIN_TAP, t) for t in r["links"]]
        if r["minFont"] < MIN_FONT:
            found.append("text at %s px" % r["minFont"])
        print("%-16s %3d px: page %5d px tall, smallest text %s px, %s" % (name, w, r["height"], r["minFont"], "ok" if not found else "; ".join(found)))
        (warns if w < 360 else fails).extend("%s at %d: %s" % (name, w, t) for t in found)
    return fails, warns


def run_checks(files):
    fails, warns = [], []
    for f, n in files:
        a, b = check(os.path.abspath(f), n)
        fails += a
        warns += b
    for t in warns:
        print("WARNING  " + t)
    for t in fails:
        print("FAILED   " + t)
    return 1 if fails else 0


def pdf(print_html, out_pdf):
    """Prints the print layout to PDF with Edge. The page must have been built with render_report.py --print."""
    print_html, out_pdf = os.path.abspath(print_html), os.path.abspath(out_pdf)
    with open(print_html, encoding="utf-8") as f:
        if "zoom:.9" not in f.read():
            print("This page was not built with --print. Build the print layout first.")
            return 1
    if os.path.exists(out_pdf):
        os.remove(out_pdf)
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    edge(["--no-pdf-header-footer", "--virtual-time-budget=20000", "--print-to-pdf=" + out_pdf, url(print_html)])
    if not os.path.exists(out_pdf):
        print("Edge did not write the PDF")
        return 1
    with open(out_pdf, "rb") as f:
        raw = f.read()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))
    print("%s: %d bytes, %d pages" % (out_pdf, len(raw), pages))
    return 0


def name_of(path):
    return re.sub(r"\W+", "_", os.path.splitext(os.path.basename(path))[0])


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 1
    if argv[0] == "--pdf":
        if len(argv) != 3:
            print("usage: render_previews.py --pdf <print.html> <report.pdf>")
            return 1
        return pdf(argv[1], argv[2])
    if argv[0] == "--check":
        return run_checks([(f, name_of(f)) for f in argv[1:]])
    html, name, out = argv[0], None, None
    rest = argv[1:]
    while rest:
        if rest[0] == "--name" and len(rest) > 1:
            name, rest = rest[1], rest[2:]
        elif rest[0] == "--out" and len(rest) > 1:
            out, rest = rest[1], rest[2:]
        else:
            print("unknown argument: %s" % rest[0])
            return 1
    name = name or name_of(html)
    out = out or os.path.join(os.path.dirname(os.path.abspath(html)), "previews")
    render(html, name, out)
    return run_checks([(html, name)])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
