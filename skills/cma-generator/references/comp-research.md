# Comp Research — finding and verifying comparable sales

Everything about *getting the data right*. For what to do with it once you have it, see `report-build.md`.

---

## Listing status — always pull Active + Pending + Sold

Unless the user explicitly narrows it, every CMA pulls all three, because each answers a different question:

- **Sold** (last 3-6 months) — what the home is actually worth.
- **Pending** — where the market just moved. The freshest read on accepted price, and the single best signal of current buyer behavior.
- **Active** — the live competition this home will be priced against right now.

A Listing CMA must present Active + Pending as "your competition," not just Sold. Pricing strategy is built against the active field, not only closed sales. Past-Client mode may lead with Sold but still notes current Active/Pending context. Never silently drop Active/Pending.

---

## MLS date filters are NOT trustworthy (hard rule, added 2026-08-07 after a real incident)

A CMA for 456 62nd St, Oakland went to a client with every comp dated 2021-2023, presented as "how this pocket is trading right now," because a COE/Sale Date filter set for "last 18 months" silently did not apply. Records from 2014 and 2004 appeared mid-search as visible evidence the filter had failed, and that evidence was not acted on. The client caught it, not the process.

- **Never trust a date-range field just because you typed it in.** Treat every date filter as unverified until proven otherwise. This interface is known to fail silently.
- **Spot-check immediately after setting any date filter.** Open 2-3 returned records and confirm actual close dates fall inside the window. If even one falls outside, the filter did not apply. Stop and rebuild the search (sort by price or distance and verify by hand) rather than continuing.
- **Every comp used in pricing math must have its closing date verified by opening the individual record.** Not inferred from a filter, a grid column, or DOM. (DOM measures time-to-sale, not how long ago the sale happened.)
- **Never blend comps from different rate cycles into one "current market" narrative.** 2021 (near-zero rates, frenzy) and 2023-2026 (6-7% rates) are not the same market. Either restrict pricing math to recent-era comps, or split into clearly separate labeled tables ("Verified Current Comps, Last 18 Months" vs "Older-Cycle Comps, Historical Context Only, Not Used In Pricing").
- **Thin recent data means fewer verified comps, not padded stale ones.** A three-comp report on individually-verified recent sales is more defensible than a nine-comp report where a third are silently 3-5 years old.
- **Final date sanity pass before delivery:** read the sold-comp table and confirm every date matches the window the report's own narrative claims.

### Related trap: assessor records disagree with the MLS listing

County assessor bed/bath counts and square footage frequently disagree with how a home is actually marketed (the county may count non-conforming rooms as bedrooms). **A wrong bedroom count silently produces the wrong comp set.** Precedent: 6656 Dana St, Oakland, 2026-08-13 — the assessor showed 5bd/2,058sf, the live MLS listing showed 3bd/2,105sf. Comps pulled on the assessor's 5bd figure produced a value range roughly 35% too low.

**Before filtering comps by beds or sqft, check whether the subject is currently or recently listed on MLS, and prefer the MLS listing's figures.** Note any material discrepancy in the report rather than silently picking one.

---

## Search criteria

**Radius**
- 1 mile from subject.
- **City boundaries override radius.** Never include a comp from a different city even if it is closer than 1 mile.
- Flag borderline comps near city borders and let Graeham decide.

**Square footage**
- Target subject ±200-300 sqft. Flexible, not a hard cutoff.
- If the market is thin, expand gradually and note why.
- Bed/bath count matters but is not a disqualifier when sqft and condition match.

**Condition categories** (plain language): fully renovated/turnkey, updated/partially renovated, original condition/good bones, fixer-upper/cosmetic, major fixer, tear-down/land value.

**Time frame**
- Preferred: last 3 months. Acceptable: last 6 months.
- Beyond 6 months only if needed, and must be flagged with market context and an adjustment.

**Sample size**
- Note comp count per segment. If only 1-2 comps: "Limited data, use with caution."

---

## Required fields on every sold comp

- **Original list price and List-to-Sale % (sold ÷ original list).** This quantifies how far over or under asking the cohort sold and is what backs the pricing strategy with hard numbers. If original list is genuinely unavailable, note that rather than dropping the column.
- **Price-reduction history:** original list, final list, sold price, number of reductions, DOM. Available on the MLS History tab. Pull for at least the top 8-10 closest comps; at minimum click into the 4-6 closest.

Then write the correlation in plain words: "Homes that priced honestly sold in 8 to 30 days; homes that overpriced sat 90 to 150 days and needed 2+ reductions to clear." This is the single most persuasive data point when talking a seller down from an overpriced list.

---

## Weighting: sold comps lag, actives and pendings lead

Sold comps reflect deals struck 1-3 months ago. Always reconcile against the leading edge and hedge:

- **Active-vs-Sold gap.** If comparable actives are sitting at elevated DOM at prices *below* recent solds, the market softened after those solds closed. Weight toward the active/pending level, not the solds. Isolate **pendings** and weight them most.
- **Do NOT linearly extrapolate $/sqft.** A larger home is not worth (cohort $/sqft × its larger sqft), especially when the matching cohort is small and smaller. Buyers pay for the home, not pure footage. Use comparable sold prices with a modest size adjustment, and flag low confidence when the cohort is under ~5 truly-similar comps.
- **Rate / trend hedge.** In a rising-rate or slowing market, apply and *disclose* a downward hedge (typically 3-6%), and recommend a list that prices slightly ahead of a falling market rather than chasing it down.
- Include a short **Market Conditions** section covering the rate environment, DOM/absorption trend, the active-vs-sold gap, and the explicit hedge applied, so the pricing rationale is transparent.

### Active price-cut tracking — "Which Way the Market Is Moving"

Closed sales lag by 1-2 months; the leading indicator is what active sellers are doing with price right now.

- **Detect cuts** two ways when possible: diff the current active pull against a prior dated snapshot of the same cohort, and open each key active to compare Orig Price vs current List Price (check for delist/relist at a lower number — a new MLS# on the same address is a relaunch; note the prior price).
- **Present as a table:** Address | Was | Now | Cut | DOM | one-line read. Include brand-new listings that launched *below* recent closed prices; that is the same signal wearing a different hat.
- **Write the read:** which tier is cutting, how much, what supply is doing, and what it means for this seller's pricing window.
- **When the subject's tier is cutting, shift the entire pricing architecture below the AVM.** AVMs train on closed sales, so in a softening tier they reflect the market of 1-2 months ago. Precedent (2495 Gloria Way, 2026-06-07): AVM $1,145,800, active tier repricing ~5% down, all three bands moved down $50K to a recommended $1,048,000-$1,099,000, deliberately under both the AVM and the closest sold twin. Framed to the seller as "priced where the market is heading, not where it was." Shift every dependent number consistently; never leave a stale AVM-anchored figure in one section after moving another.

---

## Submarket awareness — required when the cohort crosses a known line

When comps span a known boundary (east-of-101 vs west-of-101 in EPA/Menlo Park/Palo Alto; Belle Haven vs the rest of Menlo Park; original Eichlers vs newer builds; school district lines), the CMA must:

1. Identify which side the subject is on.
2. Flag comps on the other side as a different submarket.
3. **Never use a cross-boundary comp as a price anchor.**

Example: 1030 Bradley Way is east-of-101 in EPA; 2055 Oakwood Drive is west-of-101 and carries the west-side premium. Not a valid anchor. Footnote any such comp so the seller does not anchor on it.

---

## When direct comps don't exist (unique properties)

Some properties have no cleanly matching comps: 2-on-1 dual homes, permitted ADUs, unusual zoning, large-lot teardowns, custom builds, multi-unit on an SFR APN, deed-restricted.

- **Don't fake it.** State plainly that direct comps are unavailable and why. Never present an indirect cohort as if it were direct.
- **Triangulate from three angles, transparently:**
  1. **Adjacent-cohort baseline** — closest "normal" cohort prices, then documented qualitative adjustments for the subject's unique features. State each adjustment.
  2. **Older similar-configuration comps, time-adjusted** — find the closest historical similar-config sale (2-5+ years is fine) and adjust using known area appreciation. Show the math: "sold $X in 2019, +18% to 2022 peak, then −10% to current = adjusted $Y." Use Case-Shiller / Zillow ZHVI / CAR data where available, otherwise document the assumed rate.
  3. **Income approach** — for rentable properties, value against market rents at 5% / 6% / 7% gross cap in a small table.
- **Combine and reconcile.** Present a range all three roughly support; flag divergence.
- **Cite any prior listing as a market test.** DOM, withdrawn vs sold, offer pattern and feedback are real property-specific data and often the strongest single signal.
- **Marketing strategy follows the comp problem.** Investment-style unique homes get marketed as income property with cap-rate framing, reaching the buyer pool that actually fits.
- Be explicit that unique-property confidence bands are wider than standard CMAs.

---

## Re-running a CMA on a property Graeham previously listed

The report goes to the same client. Never write language that retroactively criticizes the prior listing strategy ("mis-positioned for retail," "the marketing approach was wrong") — it reads as Graeham admitting he did not know what he was doing the first time.

Distinguish what the **market** showed (factual: 50 DOM, no acceptable offers, tenant-friction feedback) from what **strategy** changes for the relist (forward-looking). And do not recommend re-spending money already spent: if the home is already staged, do not recommend staging again. Confirm prior spend with Graeham before recommending prep.

---

## Don't ship thin because you are low on context

The full format applies to every mode. "It's just a quick value check" is not a reason to drop the cohort table, the trend charts, or the market story. Chart *selection* is situational (see SKILL.md §3), but the core structure is not. If the session lacks the budget to build a complete report, stop and hand off to a fresh session with a handoff doc rather than shipping something thin.
