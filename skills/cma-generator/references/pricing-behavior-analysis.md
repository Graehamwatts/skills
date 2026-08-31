# Market Pricing Behavior & the Days-on-Market Correlation

**Added 2026-06-23 (Graeham request).** A REQUIRED section in every listing/pre-market CMA, and encouraged in past-client mode. It answers, with hard local numbers, the three questions a seller actually has about pricing:

1. **How is this market pricing?** Are sellers listing UNDER market and getting bid up, or listing OVER and cutting?
2. **What actually happens?** Do homes sell over or under their original ask, and by how much?
3. **Is there a correlation between pricing and speed?** Does pricing sharp actually sell faster, in numbers?

This section is the persuasion engine of the CMA. It is how you move a seller off "let's just try a high number" — you show them what that move costs in this exact market, in days and in dollars.

---

## Data to pull (per sold comp, from the MLSListings History tab)

For at least the closest 12–20 sold comps (use the whole cohort if the pull allows):

| Field | Source |
|---|---|
| Original List Price | History tab, first list price recorded |
| Final List Price | History tab, last list price before sale |
| Sold (Close) Price | Sold price |
| Days on Market | DOM |
| # Price Reductions | count of decreases between original and final list |
| Close of Escrow date | for recency weighting |

Market-level cross-check: the MLS **Stats** tool has a **"Sale Price to Org Price Ratio"** statistic — use it to sanity-check the cohort's median against the whole submarket. (Per-comp original list still comes from the History tab.)

If original list is unavailable for some comps, compute the analysis on the subset that has it and SAY the sample size. Never fabricate an original list. Never silently fall back to final list — the whole point is original-vs-sold.

---

## Metrics (compute in Python, never eyeball)

- **LSR = Sold ÷ Original List × 100** — the list-to-sale ratio vs the ORIGINAL ask (not the final list). This is the number that captures the full pricing story.
- **Over / At / Under split:** % of comps with LSR > 101 (sold over), 99–101 (at), < 99 (under).
- **Median LSR** and **median DOM**.
- **Reduction rate:** % of comps with ≥1 price cut (final < original); median $ cut among those.
- **Correlation:** Pearson **r** between each comp's LSR and its DOM. Report the sign and rough strength in plain words ("r = −0.58, a clear negative correlation: the further over asking a home sold, the fewer days it took").
- **Bucketed outcomes** by how each home actually priced/sold:
  - **Priced to sell** = sold over original ask (LSR ≥ 101)
  - **Priced at market** = sold within ±1% (LSR 99–101)
  - **Overpriced** = sold under original ask (LSR < 99) and/or ≥1 reduction
  - For each bucket: count, median original list, median sold, median LSR, median (and avg) DOM.

---

## The four required visuals (Chart.js)

### 1. Over/Under split — the headline
A single horizontal stacked bar split into **Sold OVER / AT / UNDER original ask**, each segment labeled with its %. Green = over, gray = at, coral = under. Pair it with ONE big stat callout, e.g. *"71% of homes sold over their original asking price; the median home closed at 103% of original list."* This is the one-glance answer to "which way is the market going."

### 2. List-to-Sale ratio distribution
Vertical histogram. Buckets: `≤95%`, `95–99%`, `99–101%`, `101–105%`, `105%+` of original list. Count per bucket. Coral for the under-100 buckets, green for the over-100 buckets. Dashed vertical reference line at the median LSR; caption states the median.

### 3. List-to-Sale % vs Days on Market — THE correlation chart (the new one)
Scatter, one dot per sale: **x-axis = LSR % (sold vs original list), y-axis = days on market.** Add a linear trendline and annotate the correlation r in the caption. Color dots by bucket (green over / gray at / coral under). This is the chart that visually proves "homes that sold over asking sold fast; homes that sold under asking sat." It is the single most persuasive chart in the report — never omit it when original-list data exists.

> Chart.js: use a `scatter` type with a second `line` dataset for the trendline (compute slope/intercept in Python via least squares and pass the two endpoints). Tooltip shows address, LSR%, DOM.

### 4. Pricing-approach outcomes — use the SLOPE chart, not dual axes

**Do NOT use a dual-axis bar chart here.** Median-DOM on a left axis and median-LSR% on a right axis was shipped once and Graeham's feedback was direct: he could not follow it. Two different units on two different scales in one chart is a reading puzzle, not a persuasion tool.

**Use a two-point slope chart instead.** X-axis has exactly two categories: `Original list price` and `Final sold price`. Two line datasets, each with two points:

- **Priced to sell** (green, solid): median original list → median sold. Slopes UP.
- **Overpriced** (coral, dashed): median original list → median sold. Slopes DOWN.

Both groups start at nearly the same list price and end far apart, so the chart reads instantly as a single sentence: *same starting point, opposite outcomes.* Put the DOM figures in the legend labels ("Priced to sell (15 homes, sold in 10 days)") rather than on a second axis, and put the dollar gap in the caption.

```js
new Chart(ctx,{type:'line',data:{labels:['Original list price','Final sold price'],datasets:[
  {label:'Priced to sell (N homes, sold in D days)',data:[medOrigOver,medSoldOver],
   borderColor:'#4f9d69',backgroundColor:'#4f9d69',borderWidth:4,pointRadius:8,tension:0},
  {label:'Overpriced (N homes, sold in D days)',data:[medOrigUnder,medSoldUnder],
   borderColor:'#C96A45',backgroundColor:'#C96A45',borderWidth:4,pointRadius:8,borderDash:[7,4],tension:0}
]},options:{scales:{y:{ticks:{callback:v=>'$'+(v/1000000).toFixed(2)+'M'}}}}});
```

**Keep the approach table underneath it** — Graeham specifically called this table out as excellent, do not drop it:

| Approach | # of sales | Median orig list | Median sold | LSR | Median DOM |
|---|---|---|---|---|---|
| Priced to sell (sold over) | … | … | … | …% | … |
| Priced at market (±1%) | … | … | … | …% | … |
| Overpriced (cut / sold under) | … | … | … | …% | … |

---

## Narrative — REQUIRED, and it is NOT optional prose

The charts alone are not enough. Graeham's standing instruction (2026-06-23): every chart in this section must be followed by a **plain-language written summary on the sheet** so a reader gets the whole story without interpreting a graph. Three written pieces are MANDATORY:

### A. "Reading the numbers" block (a readable card directly beneath the charts/table)

**This block gets HEAVIER visual treatment than a normal callout.** Graeham flagged it (2026-08-15) as the part of the report he wants emphasized: it is the section that does the persuading. Give it its own class, not the standard `.key` box:

- Gold 2px border with a 10px gold left edge, soft gold box-shadow, light warm gradient background
- An uppercase Montserrat heading ("READING THE NUMBERS") with a rule under it
- Larger body type than surrounding prose (15px vs 13.5px), generous line-height
- Custom bullets: colored dots keyed to outcome, green for the winners, coral for the losers, gray for the at-market group. No default disc bullets.
- Close it with a bolded one-line kicker under a divider that states the dollar spread between the groups, e.g. *"The spread between those two groups is $325,500. Both started within $45,000 of each other on list price."*

Walk through each group in plain sentences with the counts AND outcomes, as a short bullet list. Use this exact shape:

> Of the [N] [market] homes that sold in the last 12 months:
> - **[a] homes ([x]%) priced it to sell** and sold over their original ask, a median of $[…] (about [+p]% over), in a median of just **[d] days**.
> - **[b] homes ([y]%) priced at market** and sold right at asking, in about [d2] days.
> - **[c] homes ([z]%) overpriced** and sold below their original ask. They started highest (median list $[…]) but sold lowest (median $[…], about [-p]% under), and took **[d3] days**, [k]x as long.
> - **[r] homes ([rr]%) had to cut their price** at least once before selling.

Every number here is a real computed value, not a placeholder. Spell out the counts (24 homes), not just the percentages.

### B. "Why is the market pricing this way?" — answer the reason, do not just report
Graeham specifically wants the WHY behind the split (e.g., why are most selling under ask). Give a short, honest read of the dynamic, e.g. an anchoring/discipline gap: most sellers anchor to the optimistic end (a top neighbor sale, a Zestimate, the number they want to net) and the market corrects them down over weeks, while the disciplined minority who price at/under true value get bid up. Tie the explanation to the data you just showed (homes still sell fast when priced right → it is not a weak market, it is a pricing-discipline gap).

### C. "What this all means" closing note (end of the section)
A short interpretive wrap-up labeled plainly (e.g. **What this all means.**) that says, in one tight paragraph: which behavior the market punishes vs rewards, and exactly what the subject should do because of it. Connect it to the recommended list price explicitly. This is the "here are the notes, this is what it means" summary Graeham asks for.

Then the recommended list price must follow what the data says the market rewards, and the report must say so out loud.

---

## Expected sales price vs list price (added 2026-08-15, Graeham request)

**These are two different numbers and the report must say both.** In a market where 79% of homes sell over their original ask, the list price is a marketing lever, not a prediction. Reporting only a "recommended price range" conflates them and loses the entire strategic point.

### Required structure for the Pricing Strategy section

**1. Lead with an Expected Sales Price callout.** A single stat block, before any list-price discussion:

> **EXPECTED SALES PRICE**
> **$X to $Y**
> Midpoint $Z, about $N per square foot

**Size it like a stat, not a hero headline.** Real correction, 16 Clarence Court, 2026-08-17: this callout was shipped at 36px in a bold black block and read as oversized and heavy next to the rest of the page. The number in this callout must be the same size and weight as the `.val` price shown on each tier card below it (22px, Montserrat 800), not a large display headline. It is one data point among several on the page, not the page's visual climax.

**2. Show how it was derived**, in a readable block, not just a number. Name the condition-matched comps, state the size adjustment, and show the bracket check.

#### Condition tiering — do this before any pricing math

In a mature single-family pocket, **condition sets price far more than size does.** On the Kenyon build, size alone explained less than 1% of the price variation across the cohort; condition explained most of it. Pricing off a blended $/sf across mixed-condition comps is therefore close to meaningless.

Sort every sold comp into a tier from the listing remarks, photos, and permit history:

| Tier | What it means |
|---|---|
| **fixer** | Explicitly marketed as a project, trust/estate sale, "perfect canvas" |
| **partial** | One system or room touched (appliances, AC added), rest original |
| **dated** | Clean and livable, nothing updated |
| **updated** | Kitchen AND baths genuinely done, no structural work. |
| **remodel** | Gut-level finish throughout, often with a permitted addition |

Then report the median $/sf **per tier** and place the subject in one. Price off the comps in the subject's own tier. The other tiers are the bracket check, not the comparison.

Flag any comp that carries a different school-district assignment and exclude it from the rate math. On the Kenyon build, one full-remodel comp with Cupertino schools sold about $875,000 above an equivalent-size Santa Clara Unified home. Left in, it would have poisoned every number downstream.

Watch for a tier outlier with high DOM: a full remodel that took 78 days and a relist sold at a $/sf well below its tier. That is a marketing or location story, not a condition ceiling. Drop it from the rate regression and say why.

**3. Then the three LIST-price strategies**, renamed. The old Conservative / Competitive / Stretch labels are RETIRED — "Conservative" wrongly implied a low expected outcome when it is actually the strategy most likely to produce a bidding war:

| Tier | Label | What it means |
|---|---|---|
| 1 | **Aggressive list strategy** | List deliberately UNDER value to start a competition. This is what the over-ask majority actually did. Fastest, highest multiple-offer probability. |
| 2 | **Recommended** | List at the value the comps support, still under the market's median winner premium. The default recommendation. |
| 3 | **Stretch** | Tests the top of the range. Carries the overpriced group's risk profile: longer DOM, likely cut. |

**Tier cards show ONLY the suggested list price, not a restated expected-sale figure or DOM.** Retired 2026-08-17 after direct correction on 16 Clarence Court: cards previously each carried their own "Expected sale: $X to $Y, N days" line, which produced a second, different sale-price figure sitting below the single Expected Sales Price callout already shown at the top of the section. Graeham's words: "we already say what the expected sale is above, and now it's different and you're putting it below. Makes no sense." One Expected Sales Price, stated once, at the top. The tier cards exist to answer "what do I put on the sign," not to re-derive the outcome a second time with slightly different numbers. Leave DOM off the cards entirely by default; it is optional and only goes in when Graeham asks for it on that specific report.

**Every tier card must still state its own pros and cons** (added 2026-08-17, Shree Khare pushback). A list price with no stated tradeoff reads as a number pulled from nowhere. Use this shape for each of the three:

| Tier | List price shown as | Pros | Cons |
|---|---|---|---|
| **Aggressive** | Suggested list price (below Expected Sales Price) | Draws the widest buyer pool, highest odds of multiple offers, typically the fastest sale | If it does not draw competition, the sale can land at or near the low list price, which reads publicly as underperforming |
| **Recommended** | Suggested list price (at the comps-supported value, still under the market's median winner premium) | Balances speed and upside, matches what most of the current market is actually doing | Less dramatic than an aggressive list, so somewhat lower odds of a bidding-war ceiling |
| **Stretch** | Suggested list price (near or above the top of the Expected Sales Price range) | Keeps upside optionality if a premium buyer appears without a bidding war | Longer time on market, weaker negotiating leverage, usually requires one or more price cuts to reach the Expected Sales Price anyway |

**The Suggested List Price is the only number on the tier card.** The Expected Sales Price lives once, in the callout at the top of the section, never repeated or re-derived per card. This is also the block to reuse verbatim when responding to a client's pricing pushback in an email or revised proposal, not just in the CMA report itself.

### Deriving the aggressive list price from market behavior
Do not guess it. Compute it:

```
aggressive_list = expected_sale_midpoint / (median_winner_LSR / 100)
```

Then sanity-check against the priced-to-sell group's actual median original list. If those two numbers disagree badly, the expected sales price is probably wrong, not the formula.

### Size adjustment — do it correctly
When the condition-matched comps are a different size than the subject, adjust before comparing.

**Measure the marginal $/sf WITHIN a single condition tier, never across all tiers.** Across tiers, condition swamps size and the regression is noise. On the 3444 Kenyon build the cross-tier slope was $210/sf at r²=0.007 (meaningless); within the full-remodel tier it was $1,305/sf at r²=0.804 (usable). Using the cross-tier number would have understated the subject by roughly $270,000.

Report the r² alongside any slope you use. If r² is under about 0.4, say so and fall back to bracketing between tiers rather than adjusting.

Always bracket-check the result: it should clear the top of the tier below and stay under the tier above at comparable size. If it does not, re-examine.

## Guardrails
- Small sample (< 8 comps with original-list data): label the read as **directional**, not definitive.
- Never present LSR vs final list as if it were vs original list — they tell different stories.
- No em dashes in output prose. Compute every percentage and median in Python.
- This section sits in the report AFTER the comps and market data, and FEEDS the Pricing Strategy / Recommended List Price sections (it is the evidence behind them).
- **The stated Suggested List Price must actually match the market-behavior narrative it sits next to.** Caught 2026-08-17 (Shree Khare pushback): a report said most competition prices just under a round-number threshold to draw bidders, then recommended a list price ABOVE that threshold in the same breath. If the narrative says "price under $X to draw competition," the Aggressive tier's list price must actually be under $X. Re-read your own narrative paragraph against your own tier numbers before sending anything out; a contradiction here is exactly the kind of thing a sophisticated client will catch and lose trust over.

## Plain-language labeling and honesty rules (added 2026-06-26, Fugu review)

These were flagged when the 2896 Illinois build shipped a confusing/inaccurate label. Apply every time:

- **Never label the correlation "Price vs Days Correlation."** The x-axis is the sale price as a percent of the ORIGINAL list, not "price." That label is wrong and confuses readers. Use a plain-English label such as **"Longer on market = bigger discount"** (for a negative r) and show the number quietly (e.g. `-0.44`).
- **Always caption the scatter in one plain sentence**, e.g. "Homes that took longer to sell generally closed farther below their original asking price (correlation -0.44, a moderate pattern, not a guarantee for any single home)." Define what the dot means (sale as % of original list vs DOM).
- **r is a tendency, not a prediction.** State it is moderate/strong/weak and does not predict any one home.
- **This pricing-behavior section is ADDITIVE, not a replacement.** It does NOT substitute for the required chart set (`trendPrice`, `trendLS`, `newList`, `monthsInv`, `compBar`, `priceDom`, `priceJourney`, `$/sqft`) or the full comp-table columns. A report must contain BOTH the required charts/columns AND this section. Do not drop required charts to make room.
- **Equity vs gross appreciation.** Never call (today's value minus purchase price) "equity." Equity requires subtracting loan payoff and selling costs, which we usually do not have. Label it **"gross appreciation"** or **"value gained since purchase, before payoff and selling costs."** Only say "equity" if you actually have payoff + cost figures.
- **Data source for the comp pricing fields.** Original List, Final List, Sold, DOM, Close Date, Lot, Year all come cleanly from the MLS **"Appraiser Form 1004MC Detailed" export** (Results → select all → Export → that format → CSV). Beds/baths, exact # of price reductions (vs the orig-minus-final approximation), condition notes, and active-inventory counts (for `newList`/`monthsInv`) are NOT in that export and need a separate pull or the MLS Stats tool. If those are unavailable, state it rather than faking them.

## Target Price Reality Check (added 2026-08-30, Graeham request — 37375 California St)

Trigger this whenever a client states a specific target price and the computed value range does not support it. Never treat this as an error case to smooth over or a number to argue against directly. The goal is to hand the client the same data Graeham would use on a call: not "you're wrong," but "here's exactly what it would take."

Three parts, always in this order, always grounded in comps already in the report (never a fresh unrelated pull just for this section):

### 1. Real proof-of-price comp
Find the closest real, non-outlier sale at or near the client's stated target from the comp set already built for this report. "Non-outlier" matters: skip anything already flagged as auction-style, distressed, or deliberately underpriced to draw bids (those inflate the effective $/sf and would overstate what's achievable). Describe what that comp actually was in plain terms: size, condition, remodel scope, DOM. This is "here's what someone got for that money," stated as fact, not as a hypothetical.

### 2. Reverse-engineered gap
Using that comp's real $/sq ft rate, calculate what the subject would need to reach the target:
- `needed_sqft = target_price / comp_rate_per_sqft`
- State the delta plainly: "that's roughly N sq ft more than it has now" (an addition), or if the subject already exceeds that sqft, say so and explain the gap must be closing on condition/remodel instead.
- Only invoke lot size as part of the gap if the underlying comp data in THIS market actually shows a lot-size premium (check whether larger-lot comps command higher $/sf here first — see `comp-research.md`). Do not force a lot-size narrative onto a market where finished square footage and remodel level are what's actually driving price (confirmed to not apply in the Newark small-lot-starter-home segment, 2026-08-30 — verify per-market, don't assume the Hayward-style land-value story applies everywhere).
- State the condition/remodel level required in the same concrete terms the comp used ("a full permitted remodel plus a real addition," not "needs updating").

### 3. Market-velocity delta
Pull the DOM/absorption trend data already required for every CMA (`trendDom` / MLS Stats Days-to-Sell). Compare the current trailing months against the fastest period in the same lookback window, using the real monthly averages, never a client's or agent's remembered anecdote ("it used to sell in a week") taken at face value — check the anecdote against the actual chart data first and correct the specific number if the real data doesn't match it, while keeping the direction of the claim if the data supports it. State plainly whether reaching a stretch number is getting easier or harder right now given that trend.

### Where it goes in the report
Its own section, placed after the Pricing Strategy / value-range section (it references the value range, so it must come after). Do not fold it into the Special Considerations or closing sections. Section heading should name the actual target number, e.g. "Is $1,000,000-$1,100,000 Realistic? Here's What It Would Take" — a real question the client asked, not a generic header.
