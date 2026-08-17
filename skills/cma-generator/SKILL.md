---
name: cma-generator
description: "CMA Generator for Graeham Watts — Comparative Market Analysis expert tool for real estate agents. Use this skill ANY time the user mentions: CMA, comps, comparable sales, market analysis, listing presentation, pricing strategy, property valuation, price opinion, broker price opinion, BPO, running comps, pulling comps..."
---

# CMA Generator — Graeham Watts

Produce premium, branded, data-rich CMA reports with real MLS-sourced charts, honest narrative, and a concrete price recommendation.

> **Restructured 2026-08-13.** This skill previously had rules spread across 7 files with 9 direct contradictions (net sheet both banned and required, 3-chart minimum vs 15 mandatory charts, two publishing methods, two URL paths). Rules are now organized by WHEN YOU NEED THEM. Where old rules conflicted, the newer corrective rule won. Do not re-add a rule here without checking it does not contradict one already in the checklist below.

---

## 0. Brand identity — read this before writing any output

**Read `skills/shared-references/identity.json` and copy values from there.** Never type brand details from memory or prior context; cached prompts carry stale values.

- Graeham Watts is the **primary brand** and always leads.
- Brokerage attribution is the supporting line: **"Powered by The Boyenga Team at Compass Real Estate"** (spelling: Boyenga).
- DRE **01466876** is the only valid DRE. One other value is blocklisted in identity.json and has leaked 10+ times; never write it.
- "Intero Real Estate" is the **former** brokerage. It must not appear in new output.

Run the brand validator before every publish (see `references/publishing.md`).

---

## 1. Pick the mode FIRST

Framing and language change by audience. Decide before writing a word.

| Mode | Audience | Framing | Extra reading |
|---|---|---|---|
| **Listing** (default) | Seller about to list | Pricing strategy + list-price recommendation | `references/dashboard_template.html` |
| **Buyer** | Buyer weighing an offer | Offer analysis, what to pay | `references/buyer_mode_template.html` |
| **Past-Client / Home-Value Update** | An owner NOT selling | Warm equity/value update | `references/past_client_mode.md` |

Use Past-Client Mode when the request comes from the past-client follow-up system, or mentions "past client," "home value update," "equity update," an anniversary/CMA cadence, or is clearly addressed to someone who already owns the home and is not selling. When genuinely unsure, ask once.

---

## 2. PRE-FLIGHT CHECKLIST — single source of truth

**Every item must be true before any CMA is published or sent, in every mode and format.** This list replaces the three overlapping "NON-NEGOTIABLE / MANDATORY / REQUIRED" blocks that used to be scattered across this skill. If something is required, it is here. Confirm each out loud before shipping.

**Content**
1. **A concrete dollar recommendation.** Never end on qualitative-only guidance ("price to compete"). At least one explicit $ figure the client can act on. Where a genuine unresolved fact changes the number (unverified sqft, permit status), give multiple labeled dollar scenarios with confidence levels. "It depends" is not a deliverable; "$X to $Y if A, $Z to $W if B" is.
2. **Price recommendations are RANGES, never single numbers.** Single numbers are false precision. Tight cohort (5+ direct comps within 10%): ±2-3%. Wider or unique property: ±4-6%. State the realistic clearing band within each tier.
3. **Prior sale history in the headline stats.** If the subject has any prior recorded sale, its last sold price AND date go in the top stats row, not buried in a table below.
4. **Every material red flag carries a number.** Unverified sqft, permits, or condition claims get a price impact shown, not just a warning.
5. **Charts meet the baseline in §3 below.**
6. **Every comp's closing date individually verified** by opening the record. See the date-filter hard rule in `references/comp-research.md` — this failure has shipped to a client once.

**Voice and omissions**
7. **Second person throughout.** Write as Graeham speaking directly to the client ("you," "your"). Scan for `\bhis\b`, `\bher\b`, `\bthe seller\b`, `\bthe client\b` in prose and rewrite. Exceptions: the factual subject-details table, the footer disclaimer, and the hero subtitle.
8. **Zero em-dashes.** `—` and `&mdash;` are the biggest AI tell. Use commas, periods, parentheses, colons, or "to" for ranges. Scan before publishing.
9. **No net-to-seller sheet** unless Graeham explicitly asks for it in that specific request. Remove on sight if a template carries one.
10. **No "Notes & Caveats" / "About this analysis" / data-source apology section**, in any form. The only disclaimer permitted is one clean line: "Professional opinion of value, not a formal appraisal."
11. **No banned openers.** See the full list in `references/report-build.md`. Never brace the reader ("I want to be straight with you," "Let me be honest").
12. **Humanizer pass run** on all narrative prose. Required, not optional.

**Before publish**
13. **Brand validator passes**, DRE and brokerage correct per §0.
14. **Quality control pass complete** per `references/report-build.md` (comp accuracy, math spot-checks, narrative consistency).

---

## 3. Charts — baseline plus situational

Chart selection is **situational by design**. The old skill demanded a fixed 15-chart set in one place and a 3-chart minimum in another; neither matched how a real CMA gets built.

**Baseline, every CMA (the three that always tell the story):**
1. **Average Sale Price** over time
2. **List-to-Sale Price Ratio** over time
3. **Average Days on Market** over time

**All three come from the MLS Stats module, not hand-plotted from your own comp set.** A line connecting the 3-4 comps you happened to pull is not a market trend. Full pull procedure, screenshot requirement, and caption format are in `references/report-build.md`.

**Then add what supports this specific property's story.** Judgment call, by mode and situation: months of inventory, new listings per month, price journey (original→final→sold), DOM vs price cut, price-vs-DOM scatter, comp price comparison, $/sqft comparison, pricing strategy outcomes, rate trajectory. A listing CMA into a softening market needs the supply and price-cut charts; a quick buyer-side read does not.

> **Trailing-month data artifact (added 2026-08-13, Graeham's catch).** MLS monthly stats for the **current, incomplete month** are commonly wrong, and wrong in a specific direction: partial aggregation makes the last data point show an upswing when the real trend is down (or vice versa). Before publishing any trend chart, check whether the final month is fully aggregated. If it is not, drop that month or mark it explicitly as partial. Never let a partial-month artifact set the direction of the market read.
>
> This rule is about removing **data artifacts that misrepresent reality**, not about removing accurate data that is unfavorable. Adverse but real findings stay in and get explained plainly. That is what earns the client's trust.

---

## 4. Workflow

1. Collect subject property details (template in §5). Ask if missing.
2. Pull comps per `references/comp-research.md` — Active + Pending + Sold by default.
3. **Sort the sold comps into condition tiers and place the subject in one** (`references/pricing-behavior-analysis.md`). Condition drives price far more than size in a mature pocket; skipping this produces a meaningless blended $/sf.
4. Pull the three baseline trend charts from MLS Stats (§3).
5. Compute the pricing-behavior statistics in Python, never by eye.
6. Derive the **expected sales price** off the condition-matched comps, size-adjusted with a within-tier rate. Then set the three list-price strategies from it.
7. Build the **Interactive HTML report** (master format, self-contained, Chart.js via CDN).
8. Run the Pre-Flight Checklist (§2).
9. Publish per `references/publishing.md` and verify the live URL loads.
10. Email-safe HTML or PDF only if requested (see `references/report-build.md`).

> **Reference build.** The 3444 Kenyon Drive listing presentation (August 2026) is the approved standard for this mode. `references/dashboard_template.html` is generated directly from it. When something is ambiguous, match that build.

---

## 5. Subject Property Template

```
Address / City / Zip
List Price Goal (or TBD)
Beds / Baths / SqFt / Lot Size
Year Built
Condition (plain language)
Parking / ADU / Tenant Status
Unpermitted Work (yes/no)
Notable Features
Seller Situation (if known)
```

---

## 6. Report section structure

Section order matters: the client reads the story first, the comps second, the data context third. Never put market statistics at the top where a median could be mistaken for a recommendation. Never open with commission math.

1. **Cover / Hero** — black header, "GRAEHAM WATTS" in gold caps, "R E A L T O R," report type, address, date, contact line.
2. **Subject Property Summary** — branded table plus key-stat callout boxes. Include prior sale price and date here (checklist #3).
3. **The Market Story** — narrative only, no stats boxes or charts. Where the market is, what is selling and for how much, where this property fits, honest expectations.
4. **Comparable Sales** — full comp table (address, sold price, original list, % over/under, sqft, $/sqft, bed/bath, DOM, condition, city). Tier into Most Similar / Somewhat Similar / Use With Caution. Subject-vs-most-similar comparison table. Separate tables per city if the cohort spans cities. No radar charts.
5. **Market Data & Trends** — the baseline trend charts, stats boxes, price distribution, list-to-sale visual, key insight paragraph.
6. **Pricing Strategy Analysis** — lead with market pricing behavior and the DOM correlation (`references/pricing-behavior-analysis.md`), then the three strategies. **Past-Client mode replaces this section entirely** with "What Your Home Is Worth Today" — see `references/past_client_mode.md`.
7. **Recommended Price / Offer** — lead with an **Expected Sales Price** callout, then three LIST-price strategy boxes. See "Expected sales price vs list price" in `references/pricing-behavior-analysis.md`. In Past-Client mode these are relabeled "Likely range / Most-likely value today / Top of range in strong condition."
8. **Special Considerations** — only if applicable: tenant occupancy, unpermitted work, ADU income, lot premium, school district, zoning, environmental, deferred maintenance, market timing. Two to three sentences of price impact each. Omit the section entirely rather than padding it.
9. **Closing** — warm close, referral CTA, contact block, single disclaimer line.

> **Out of scope: tax and legal advice (added 2026-08-17, Shree Khare / step-up-basis question).** A client will sometimes ask a tax or legal question alongside a CMA request, most commonly step-up-in-basis after an inheritance, community-property vs joint-tenancy title questions, or 1031 exchange mechanics. **Never calculate a tax basis or give a legal conclusion.** What is in scope: pulling supporting market data (e.g., comparable sales around a specific date, such as a date of death, to help establish fair market value at that date) and looking up how a property was deeded via Realist/county records (joint tenancy, community property, trust, etc. — a factual lookup, not a legal opinion on its consequences). Always close with a plain recommendation that the client confirm the actual basis and its tax treatment with a CPA or estate attorney. If Graeham has a specific referral, that is his call to offer, not something to invent.
>
> **Revised/objection-handling proposals stay tight.** When responding to a client's specific pushback on an earlier CMA or proposal (pricing, commission, scope), the reply should directly answer each point raised, in plain numbers, and fit in roughly two pages. Do not restate the full original CMA. A sophisticated client (Shree Khare, 2026-08-17: "I work in the industry and I can certainly tell" a proposal is AI-generated fluff) will notice padding and generic restatement faster than most, and it costs trust rather than building it.

---

## 7. Reference map — read by task

| When you are... | Read |
|---|---|
| Finding and verifying comps | `references/comp-research.md` |
| Building charts, writing prose, QC | `references/report-build.md` |
| Publishing | `references/publishing.md` |
| Building a past-client update | `references/past_client_mode.md` |
| Building the pricing-behavior section | `references/pricing-behavior-analysis.md` |
| Matching canonical HTML structure | `references/dashboard_template.html` (listing), `references/buyer_mode_template.html` (buyer) |
| Styling a PDF | `references/branding.md` |
