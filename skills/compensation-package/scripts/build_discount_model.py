import sys

src = sys.argv[1]
out = sys.argv[2]
html = open(src, encoding="utf-8").read()


def one(old, new, html):
    n = html.count(old)
    if n != 1:
        raise SystemExit(f"Expected exactly 1 match, found {n}, for:\n{old[:200]}")
    return html.replace(old, new, 1)


# 0. unlisted page: keep search engines from indexing it. Standard and Premium are
# public; this one is only ever shared by direct link with clients being offered
# the relationship rate.
html = one(
    '<meta charset="UTF-8">',
    '<meta charset="UTF-8">\n<meta name="robots" content="noindex,nofollow">',
    html,
)

# 1. title
html = one(
    "<title>Marketing & Compensation Package - Standard Rates | Graeham Watts</title>",
    "<title>Marketing & Compensation Package - Discount Model | Graeham Watts</title>",
    html,
)

# 2. CSS: strikethrough classes, right after the :root token line
html = one(
    ":root{--b:#1A1A1A;--g:#C5A55A;--dg:#A88B3D;--cr:#F5EFDC;--gy:#666;--nv:#343955;--red:#c0392b;--grn:#4f9d69;--amb:#C96A45;--gray:#9aa0a6}",
    ":root{--b:#1A1A1A;--g:#C5A55A;--dg:#A88B3D;--cr:#F5EFDC;--gy:#666;--nv:#343955;--red:#c0392b;--grn:#4f9d69;--amb:#C96A45;--gray:#9aa0a6}"
    ".was{text-decoration:line-through;text-decoration-color:var(--red);text-decoration-thickness:2px;color:var(--gray);font-style:normal;font-weight:400}"
    ".now{color:var(--b);font-weight:800;font-style:normal}",
    html,
)

# 3. hero label
html = one(
    '<div class="lbl">MARKETING &amp; COMPENSATION PACKAGE - STANDARD RATES</div>',
    '<div class="lbl">MARKETING &amp; COMPENSATION PACKAGE - DISCOUNT MODEL</div>',
    html,
)

# 4. new explainer section, inserted between "What You're Actually Comparing" and "Marketing Plan Options"
anchor = (
    "</section>\n\n<div class=\"dv\"></div>\n\n"
    '<section id="marketing-plan-options"><div class="sh">Marketing Plan Options</div>'
)
new_section = (
    "</section>\n\n<div class=\"dv\"></div>\n\n"
    '<section id="relationship-discount"><div class="sh">The Relationship Discount</div>\n'
    '<p class="lead">The rates below assume a single transaction. When a client commits to three or more transactions in one relationship, selling and buying together rather than one listing at a time, every tier drops half a point, shown crossed out with the reduced rate beside it. The scope of service does not change: every line on this page still applies in full at the reduced rate.</p>\n'
    "<p>The discount applies once the third transaction is under contract, not before. Each transaction is documented under its own listing or purchase agreement at the full tier rate until then, and if the relationship doesn't reach three, each one stands on its own at the full rate. Where a transaction is brought to us through a referring broker, this rate assumes no separate referral fee is paid out of it.</p>\n"
    "</section>\n\n<div class=\"dv\"></div>\n\n"
    '<section id="marketing-plan-options"><div class="sh">Marketing Plan Options</div>'
)
html = one(anchor, new_section, html)

# 4b. print pagination: give the new section its own forced page break, matching
# the pattern already used for #marketing-plan-options / #compass-concierge / etc.
html = one(
    "#marketing-plan-options{page-break-before:always}",
    "#relationship-discount{page-break-before:always}\n  #marketing-plan-options{page-break-before:always}",
    html,
)

# 5. tier header rates
html = one(
    '<div class="tpkg-tn">SILVER PACKAGE</div><div class="tpkg-tp">COMPENSATION: 2.0%</div>',
    '<div class="tpkg-tn">SILVER PACKAGE</div><div class="tpkg-tp">COMPENSATION: <span class="was">2.0%</span> <span class="now">1.5%</span></div>',
    html,
)
html = one(
    '<div class="tpkg-tn">GOLD PACKAGE</div><div class="tpkg-tp">COMPENSATION: 2.5%</div>',
    '<div class="tpkg-tn">GOLD PACKAGE</div><div class="tpkg-tp">COMPENSATION: <span class="was">2.5%</span> <span class="now">2.0%</span></div>',
    html,
)
html = one(
    '<div class="tpkg-tn">PLATINUM LUXURY PACKAGE</div><div class="tpkg-tp">COMPENSATION: 3.0%–3.5%</div>',
    '<div class="tpkg-tn">PLATINUM LUXURY PACKAGE</div><div class="tpkg-tp">COMPENSATION: <span class="was">3.0%–3.5%</span> <span class="now">2.5%–3.0%</span></div>',
    html,
)

# 6. comparison table row
html = one(
    "<tr><td>Typical listing commission</td><td>1-2%*</td><td>2.5-3%</td><td>2.0% / 2.5% / 3.0%–3.5%, tiered to the plan</td></tr>",
    '<tr><td>Typical listing commission</td><td>1-2%*</td><td>2.5-3%</td><td><span class="was">2.0% / 2.5% / 3.0%–3.5%</span> <span class="now">1.5% / 2.0% / 2.5%–3.0%</span>, tiered to the plan, relationship discount at 3+ transactions</td></tr>',
    html,
)

# 7. "which tier fits" cards
html = one(
    '<div class="card"><div class="lbl">Silver · 2.0%</div>',
    '<div class="card"><div class="lbl">Silver &middot; <span class="was">2.0%</span> <span class="now">1.5%</span></div>',
    html,
)
html = one(
    '<div class="card"><div class="lbl">Gold · 2.5%</div>',
    '<div class="card"><div class="lbl">Gold &middot; <span class="was">2.5%</span> <span class="now">2.0%</span></div>',
    html,
)
html = one(
    '<div class="card"><div class="lbl">Platinum Luxury · 3.0%–3.5%</div>',
    '<div class="card"><div class="lbl">Platinum Luxury &middot; <span class="was">3.0%–3.5%</span> <span class="now">2.5%–3.0%</span></div>',
    html,
)

# 7b. the strikethrough spans add a handful of extra characters to each tier
# header, just enough to push the tier-grid page a hair past the printed page
# height and spawn a blank filler page before the next forced break. Reclaim
# that space by tightening the checklist line spacing a bit further in print.
html = one(
    "  .tpkg-b li{font-size:10px;line-height:1.28;margin-bottom:4px;padding-left:15px}",
    "  .tpkg-b li{font-size:10px;line-height:1.28;margin-bottom:4px;padding-left:15px}\n"
    "  .tpkg-b li{margin-bottom:2px!important;line-height:1.18!important}",
    html,
)

# 8. pagination polish: the "+marks what a tier adds" footnote was riding right at
# the bottom of the (now slightly taller, due to the struck-through rate spans)
# marketing-plan-options page and spilling a single line onto an otherwise-blank
# next page. Tighten its top margin in print so it hugs the grid again.
html = one(
    '<p class="lead" style="margin-top:14px"><span style="color:var(--dg);font-weight:700">+</span> marks what a tier adds beyond the one before it.</p>',
    '<p class="lead" style="margin-top:2px"><span style="color:var(--dg);font-weight:700">+</span> marks what a tier adds beyond the one before it.</p>',
    html,
)

with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", len(html), "chars ->", out)
