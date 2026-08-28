# Full workflow for generating a new property's carousel/static package

## 1. Gather the property facts

You need, at minimum: address, city, price, bed/bath count, lot size, and —
if this property has an ADU or second unit — the current and post-conversion
estimated rental range. Ask the user for whatever isn't already in the
conversation. If the user gives you an MLS Matrix link, try fetching/browsing
it directly — shared Matrix links (`search.mlslistings.com/matrix/shared/...`)
are often viewable without login and give you price, beds/baths, sqft, lot
size, year built, and the full listing description in one shot. Don't guess
numbers; if a rental estimate isn't provided, either ask for it or clearly
ask the user to confirm before publishing "estimated" figures (these are
marketing claims that go out under Graeham's name and license number).

## 2. Research market context before writing any pricing/value claims

**Always do this — it's not optional groundwork.** Any headline that calls a
property "affordable," "a deal," "priced right," or makes any other value
comparison needs to be checked against real market data first, before it's
written into a card. Two specific traps to check for every time:

- **A lower total price does not mean a lower price-per-square-foot.** Small
  homes on a normal-sized lot often carry a *higher* $/sqft than the area
  median, because land cost is roughly fixed regardless of structure size. A
  "great value" claim built on $/sqft can be flatly wrong even when the
  total price is genuinely low. Check both numbers — total price vs. area
  median, and $/sqft vs. area median $/sqft — they can point in opposite
  directions, and if they do, base the claim on whichever one is actually
  true (usually "lowest total price of entry," not "cheapest per foot").
- **Third-party listing sites can disagree with the live MLS.** Search for
  the property's own listing on Zillow/Redfin/other portals. If a price or
  status there doesn't match the MLS Matrix listing, don't silently pick
  one — surface the discrepancy to the user and ask which figure is
  current. Syndicated sites lag real MLS changes; the user, as the listing
  agent, will know which is right.

To do this, search for things like "[city] median home price per square
foot [current year]", "[city] real estate market trends [current year]",
and the property's own address, before drafting any copy that touches
price or value. A price or value claim in this skill's output goes out
under Graeham's name and DRE license — treat it with the same rigor as any
other stated fact (see step 1's note about rental estimates).

## 3. Confirm the narrative angle BEFORE building anything

The proven template (Carousel A "Investment Math" + Carousel B "Multi-Gen
Made Easy") is built for a property with a main house + a separate
ADU/second unit. If the new property doesn't have that structure, this exact
two-carousel split won't make sense — stop and ask the user what the two
angles should be for this property (e.g. "entry point + room to grow" for an
affordable starter home with a big yard, "turnkey + location" for a
move-in-ready home near major employers, "renovation upside" vs "turnkey
lifestyle", or "school district" vs "commute/location"). Ground the proposed
angles in what you actually found in step 2's research and in the photos —
don't propose a "value" angle before checking whether the numbers support
it. The card *types* (hook, split-photo, stat card, arrow-stat, triptych,
CTA) are reusable for almost any narrative — it's the specific headlines and
structure that need to fit the property.

**Important: the hooks, headlines, and data are never reused verbatim across
properties.** Only the pattern (5-card arc, 6-card arc, 4 standalone statics,
the card templates themselves) carries over. Write fresh copy grounded in
this property's actual facts, verified market context, and photos every
time.

## 4. Select and organize photos

Copy 11 photos for the property into a working `src/` folder, matching the
roles documented in `template_build.py`'s `CONFIG["photos"]` comments
(front facade, main-house interior, ADU exterior x2, ADU bedroom, ADU
office/nook, ADU kitchen, ADU living, backyard, main-house living room,
wide/aerial shot) — relabel/repurpose these roles to fit the property's
actual layout if it doesn't have an ADU (e.g. use "adu_exterior" role for a
second good exterior angle, "adu_bedroom"/"adu_living" roles for the second
bedroom and backyard-focused shots). Actually look at each candidate photo
before assigning it to a role — check for: no people/cars/clutter in hero
shots, and the backyard/wide shot ideally shows the full extent of the lot
if that's part of the story. If a role has no good candidate photo (e.g. no
aerial shot exists), swap in the next-best wide exterior/backyard shot and
adjust the crop `focus` parameter rather than forcing a bad photo into a
hero-image role.

## 5. Copy and fill in `template_build_impact.py`

For any new property, copy `scripts/template_build_impact.py` (the current
default "impact" v3 visual system — see `references/brand.md`) to a scratch
working file, not the older `template_build.py`. Fill in `CONFIG["src_dir"]`,
`CONFIG["out_dir"]`, and the photo filenames. Then rewrite every
tag/headline/sub string in the card calls to fit this property — do not just
change the CONFIG values and leave placeholder copy in place; the whole
point is that the copy is bespoke per property while the *layout code*
(which functions get called, in what order, with what photo-role variables)
stays the same. Only reach for `template_build.py` if you need its 4
standalone static-image templates (no v3 equivalent exists yet) or are
reproducing a pre-v3 property's exact look.

## 6. Run it and review

`python3 build.py` writes the carousel JPGs to `CONFIG["out_dir"]`. Read a
few of them back (especially the CTA cards and any stat cards with real
dollar figures) to sanity-check text wrapping and that gold text isn't
blending into a bright patch of photo — `carousel_lib.py`'s scrim/gradient
backings should prevent this by default, but always double check when a new
photo has very different lighting than what was tested against.

## 7. Deliver

Copy the finished JPGs into the property's folder in the user's workspace
(not just the temporary sandbox) so they're actually visible to the user, and
present them.
