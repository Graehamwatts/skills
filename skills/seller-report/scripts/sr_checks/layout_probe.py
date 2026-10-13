# -*- coding: utf-8 -*-
"""sr_checks.layout_probe: optional true renders at 390, 360 and 320 px, measured in headless Edge.

Runs only when the operator asks for it (--probe) and Edge (or Chrome) is installed. A private copy of
the page goes into a temporary folder with a small measuring script added, is opened inside an iframe of
the exact width (a headless window will not go narrower than about 500 px), and the folder is removed
afterwards. The page under test is never changed.

  no_sideways_scroll   the page is no wider than the screen at each width
  rendered_font_size   the smallest text the browser actually paints is 12 px or more
  tap_targets          links are at least 40 px tall (a warning)
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

from . import core

WIDTHS = (390, 360, 320)
EDGE_PATHS = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
MEASURE = """
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var r = {width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth, wide: [], links: [], minFont: 99, minFontText: ''};
    document.querySelectorAll('body *').forEach(function (el) {
      var box = el.getBoundingClientRect();
      if (box.width > 0 && box.right > window.innerWidth + 1 && r.wide.length < 6 && el.children.length === 0) {
        r.wide.push(el.tagName.toLowerCase() + ' reaches ' + Math.round(box.right) + ' px: ' + (el.textContent || '').trim().slice(0, 40));
      }
      var own = false;
      for (var n = el.firstChild; n; n = n.nextSibling) { if (n.nodeType === 3 && n.nodeValue.replace(/[\\s\\u00a0]/g, '')) { own = true; } }
      if (own && box.height > 0) {
        var fs = parseFloat(getComputedStyle(el).fontSize);
        if (fs > 2 && fs < r.minFont) { r.minFont = fs; r.minFontText = (el.textContent || '').trim().slice(0, 40); }
      }
    });
    document.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getBoundingClientRect().height;
      if (h > 0 && h < 40 && r.links.length < 6) { r.links.push((a.textContent || '').trim().slice(0, 40) + ' is ' + Math.round(h) + ' px tall'); }
    });
    window.parent.postMessage(JSON.stringify(r), '*');
  }, 600);
});
</script>
"""
WRAP = ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0}'
        'iframe{display:block;border:0;width:%dpx;height:2000px;background:#fff}</style></head><body><iframe src="%s"></iframe>'
        '<script>window.addEventListener("message",function(e){var p=document.createElement("pre");p.id="result";'
        'p.textContent="RESULT::"+e.data+"::END";document.body.appendChild(p);});</script></body></html>')


def find_browser(given=None):
    for p in [given] + list(EDGE_PATHS):
        if p and os.path.exists(p):
            return p
    for name in ("msedge", "microsoft-edge", "chrome", "google-chrome", "chromium"):
        p = shutil.which(name)
        if p:
            return p
    return None


def file_url(path):
    return "file:///" + os.path.abspath(path).replace("\\", "/").replace(" ", "%20").lstrip("/")


def measure(browser, html_path, source, width, tmp, timeout=120):
    """The measurements of one page at one width, or None when the browser gave nothing back."""
    base = '<base href="%s/">' % file_url(os.path.dirname(os.path.abspath(html_path)))
    doc = source
    doc = re.sub(r"(?i)<head[^>]*>", lambda m: m.group(0) + base, doc, count=1) if re.search(r"(?i)<head[^>]*>", doc) else base + doc
    doc = doc.replace("</body>", MEASURE + "</body>") if "</body>" in doc else doc + MEASURE
    copy = os.path.join(tmp, "page_%d.html" % width)
    with open(copy, "w", encoding="utf-8") as f:
        f.write(doc)
    wrap = os.path.join(tmp, "wrap_%d.html" % width)
    with open(wrap, "w", encoding="utf-8") as f:
        f.write(WRAP % (width, file_url(copy)))
    args = [browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--allow-file-access-from-files",
            "--user-data-dir=" + os.path.join(tmp, "profile"), "--virtual-time-budget=15000", "--window-size=900,2200",
            "--dump-dom", file_url(wrap)]
    try:
        out = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    mt = re.search(r'<pre id="result">RESULT::(.*?)::END</pre>', out.decode("utf-8", "replace"), re.S)
    if not mt:
        return None
    raw = mt.group(1).replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    try:
        return json.loads(raw)
    except ValueError:
        return None


def check(ctx):
    B = core.Bag("layout")
    if not ctx.opts.get("probe"):
        B.skip("probe", "the layout probe was not asked for (add --probe to render the page at 390, 360 and 320 px)")
        return B.results
    if ctx.kind == "print":
        B.skip("probe", "the print layout is for paper, so the phone widths do not apply")
        return B.results
    browser = find_browser(ctx.opts.get("browser"))
    if not browser:
        B.skip("probe", "Edge was not found on this computer, so the page was not rendered")
        return B.results
    tmp = tempfile.mkdtemp(prefix="sr-gate-probe-")
    try:
        overflow, fonts, taps, blind = [], [], [], []
        for w in WIDTHS:
            r = measure(browser, ctx.html_path, ctx.source, w, tmp)
            if r is None:
                blind.append("%d px: no measurement came back from the browser" % w)
                continue
            if r.get("width") != w:
                blind.append("%d px: the test frame was %s px wide" % (w, r.get("width")))
                continue
            if r["scrollWidth"] > r["width"]:
                overflow.append("at %d px the content is %d px wide%s" % (w, r["scrollWidth"], (": " + "; ".join(r["wide"][:3])) if r.get("wide") else ""))
            if r.get("minFont", 99) < 12:
                fonts.append("at %d px the smallest painted text is %s px ('%s')" % (w, r["minFont"], r.get("minFontText", "")))
            taps += ["at %d px: %s" % (w, t) for t in r.get("links") or []]
        if blind:
            B.warn("probe", "the layout could not be measured at every width, so it is not verified", blind)
        if len(blind) < len(WIDTHS):
            B.judge("no_sideways_scroll", overflow, "no sideways scroll at %s px" % ", ".join(str(w) for w in WIDTHS),
                    "the page scrolls sideways on a phone")
            B.judge("rendered_font_size", fonts, "the smallest painted text is 12 px or more at every width",
                    "the browser paints text under 12 px")
            if taps:
                B.warn("tap_targets", "%d link(s) are under 40 px tall" % len(taps), sorted(set(taps))[:6])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return B.results
