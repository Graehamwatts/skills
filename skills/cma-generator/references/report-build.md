# Report Build — charts, voice, quality control, output formats

Everything about *turning verified data into a finished report*. For getting the data, see `comp-research.md`. For shipping it, see `publishing.md`.

---

# PART 1 — CHARTS

## The MLS Stats pull (how the baseline charts get made)

The three baseline charts (Average Sale Price, List-to-Sale Ratio, Average Days on Market over time) come from the MLS Stats module. **Not hand-plotted from your own comp set.** A line connecting the 3-4 comps you pulled is a handful of dots, not a market trend, and shipping one has been caught three separate times.

**Procedure, every time:**

1. In MLS Matrix, go to **Search → Stats** (not Residential Search).
2. Click the **Customize** tab. Do NOT use the Presets tab: presets silently reset Chart Type to Column and wipe the criteria form. Customize is the only reliable path.
3. Set the four dropdowns. Their element IDs are stable, so set them directly rather than clicking:

   | Field | Element ID | Value |
   |---|---|---|
   | Time Frame | `m_ucStatsCustomize_m_drPeriod_m_ddlTimePeriod` | `Past 3 Years` (5 for a cycle story) |
   | Statistic | `m_ucStatsCustomize_m_mcPrimaryMeasure_m_ddlMeasures` | see below |
   | Chart Type | `m_ucStatsCustomize_m_mcPrimaryMeasure_m_ddlChartTypes` | `Smooth Line` |
   | Group By | `m_ucStatsCustomize_m_dcDimensions_m_ddlPrimaryDimensions` | `Month` |

   The three baseline statistics are named exactly: `Sale Price, Average` / `Sale Price to List Price Ratio` / `Days to Sell, Average`.

   **Chart Type gotcha, hit twice now:** the dropdown defaults to **Column** and, immediately after switching Statistic, briefly reports only `["Column"]` as its option list. Set Statistic FIRST, then re-read the options, THEN set Smooth Line. Verify `options[selectedIndex].text === 'Smooth Line'` before generating. A Column chart shipped to a client is a caught error, not a style preference.

4. Set the geography on the criteria panel. Zip Code field is `Fm8_Ctrl1107_TextBox`. Set it with `.value` plus dispatched `input` AND `change` events; it does not stick with `.value` alone. **Re-check it right before Generate** — switching Statistic can blank it.
5. Fire `__doPostBack('m_btnGenerate','')`, then `__doPostBack('m_btnChart','')`. Confirm the footer reads the expected time frame, zip, and listing count before capturing.
6. **Capture the chart as a real image.** The chart is a server-rendered PNG at `img[src*="ChartImg"]`, not a canvas.
   - **Preferred:** ask Graeham to snip it and drop it in a folder you can read, then embed the file bytes directly (read the file, base64 it in Node, write the data URI). Lossless.
   - **Never** hand-transcribe base64 out of a `javascript_tool` result into a file. Long base64 strings do not survive being retyped: it silently corrupts, and the "fix" of shrinking the image to make transcription feasible produced blurry, pixelated charts that had to be redone. If you do move bytes through a tool result, **verify with a SHA-256 hash** computed on both sides before trusting it.
   - Downscale-to-fit in CSS, never upscale. Embed at native resolution and constrain with `max-width:560px; display:block; margin:0 auto`. An 910px-wide chart shown in a ~1000px card looks soft; the same image capped at 560px looks crisp.
6. Only rebuild as a styled Chart.js line when the design genuinely needs brand matching, and only after the screenshot exists to check the recreation against. Read the underlying values from the **Data** tab; do not eyeball them off the picture.
7. **Caption every chart** with the criteria shown at the bottom of the MLS Stats page: `Source: MLSListings Matrix Stats, [filter description], [N] listings`. The caption is what makes the chart verifiable instead of decorative.
8. **Do not smooth or invent.** If the real data is a sawtooth, the chart shows a sawtooth. A clean curve that does not match the real MLS chart destroys trust the moment the client looks it up.
9. If MLS Stats is genuinely unreachable for a market (off-MLSListings: Union City, Fremont, Hayward), do not silently hand-plot. Use a clearly-labeled public source (Redfin Data Center publishes months-of-supply and price trends by city), caption it as such, and tell Graeham privately which fields came from where. Do not put a tooling apology in the client report.

## Trailing-month data artifact — check before publishing

MLS monthly stats for the **current, incomplete month** are commonly wrong in a specific direction: partial aggregation makes the last data point show an upswing when the real trend is down, or the reverse. Before publishing any trend chart, check whether the final month is fully aggregated. If not, drop it or mark it explicitly as partial.

Never let a partial-month artifact set the direction of the market read. This is about removing **artifacts that misrepresent reality**, not about removing accurate data that happens to be unfavorable — real adverse findings stay in and get explained plainly.

## Chart selection

**Baseline, every CMA:** Average Sale Price, List-to-Sale Ratio, Average Days on Market (all MLS Stats, above).

**Situational, add what supports this property's story:**

| Chart | Use when |
|---|---|
| Months of Inventory (line, dashed reference at 3 months = balanced) | Market-health or market-direction story. Under 2-3 months = seller's market; rising = softening. |
| New Listings per month | Supply is part of the story; powers the market-direction read. |
| Price Journey (original→final→sold per comp, green up / coral down) | Talking a seller down from an overpriced list. |
| ~~DOM vs Price Cut (dual-axis bar)~~ | **RETIRED 2026-08-15.** Two units on two axes read as a puzzle. Use the two-point slope chart in `pricing-behavior-analysis.md` section 4 instead, which carries the same argument in one glance. |
| Price vs DOM scatter (bubble: x=price, y=DOM, size=sqft, color=status) | Forecasting what happens at each list price. One of the most persuasive charts in a listing CMA. |
| List-to-Sale vs DOM correlation scatter (with trendline and Pearson r) | The pricing-behavior section. See `pricing-behavior-analysis.md`. |
| Comp price comparison (horizontal bars, subject as reference line) | Almost always useful. |
| $/sqft comparison | Where the subject sits in the range. |
| Over/Under original-list split (stacked bar) | Pricing-behavior section headline. |
| Rate trajectory | Rate environment is material to the story. |
| Geographic heat map | Comps geocode cleanly and spatial spread matters. Otherwise use the price-DOM scatter. |

**Do NOT use radar charts** — too confusing. For subject-vs-comps, use a clean styled comparison table instead.

## Chart implementation notes

- **Interactive HTML (master format):** Chart.js via CDN.

  **Listing mode, the canonical set** (matches `dashboard_template.html`): the three baseline trends are MLS Stats **images**, not canvases. The four Chart.js canvases all live in the pricing-behavior section: `overUnderChart`, `lsrHistChart`, `scatterChart`, `outcomesChart`.

  **Buyer and past-client modes** still use the older named canvases where their templates expect them: `trendPrice`, `trendLS`, `newList`, `monthsInv`, `priceJourney`, `priceDom`.
- **Email-safe HTML / PDF:** matplotlib → PNG → base64 data URI. Brand colors: `BLACK #1A1A1A`, `GOLD #C5A55A`, `DARK_GOLD #A88B3D`, `LIGHT_GOLD #F5EFDC`, `GRAY #666666`, `GREEN #4CAF50`, `RED #E57373`. Hide top/right spines, gray ticks at 8pt, bold 12pt title, `bbox_inches='tight'`, white facecolor.
- **List-to-Sale visual:** use HTML/CSS rows with bars extending left (under asking) or right (over) from a center line at 100%, gold for over and coral for under. Clearer than a Chart.js bar chart. Set `height: auto; overflow: visible;` on the container so rows do not clip.
- **Pricing Strategy Performance chart:** must print the actual numbers on each bar ("20 days", "+7.5%"). Enable datalabels with custom formatters.
- **Positioning bubble chart:** use clearly distinct colors for different cities (gold primary, steel blue secondary). Never similar shades.
- Add a gold divider and spacer between major visual sections so they do not bleed together.

---

# PART 2 — REQUIRED CONTENT SECTIONS

## Interest rate environment — required, multi-source

Every CMA includes a brief rate section showing the current 30-year fixed, **cross-referenced across at least three sources**: Mortgage News Daily (daily national), Freddie Mac PMMS (weekly survey), Bankrate (state level, California for Bay Area), Realtor.com (local market). Include local lender quotes and APR where meaningful.

Show the recent trajectory (6-12 months: rising, flat, falling) and a one-line read on what it means for this seller: rates up = thinner retail buyer pool, longer DOM, downward price pressure; rates down = activity warming. Note that investor buyers (cap-rate driven) are less rate-sensitive than retail (monthly-affordability driven) when it affects marketing strategy. Always add "verify day-of before pricing finalization."

## Months of inventory — required metric

Absorption = active listings ÷ monthly closed-sale pace. Include as a metric in every mode. Under roughly 2-3 months = seller's market; rising months = softening. Pair with new-listings and active price-cut data to tell the direction story.

## Past-client CTA — required

Past-client updates end on a warm, low-pressure call to action, never a disclaimer or hedge. Default is a referral plus availability ask, one or two lines: "If you or someone you know is ever thinking about buying or selling, I would love to help, a quick call is always welcome." A softer equity-aware line fits high-equity clients.

---

# PART 3 — VOICE AND BANNED LANGUAGE

## Second person, always

Every CMA gets forwarded to the client. Write all prose as Graeham speaking directly to them ("you," "your"). Never third person ("he," "she," "the client," "the seller") inside client-facing prose.

Acceptable exceptions: the factual subject-details table ("Owner: Li Hu"), the footer disclaimer (use "the owner of [address]"), and the hero subtitle ("Prepared for [Name], [Month Year]").

Before publishing, scan for `\bhis\b`, `\bhim\b`, `\bher\b`, `\bshe\b`, `\bthe client\b`, `\bthe seller\b` in prose context. If advice would feel awkward in second person, the prose is in the wrong voice.

## Whose "you"? Never address Graeham inside the report

"You" and "your" in a CMA always mean the seller reading it. They never mean Graeham, even when the content originated from something Graeham said to Claude while building the report.

**Real incident, 2026-08-17 (16 Clarence Court):** Graeham described a comp to Claude by phone/voice ("Realmar," ~$2M original list, ~$1.275M reduced, sold/pending ~$1.3M). The shipped report included an exception-comp section that read "You asked me to include the recent Ralmar Avenue property... I pulled the exact MLS record. Here is what it actually says, including where your recollection and the verified numbers differ," followed by a two-column table literally titled "What you described" vs. "Verified in MLS." That is a transcript of the Graeham-Claude research conversation, published directly into a document going to the seller. The seller has no idea that conversation happened and must never see it.

**The fix, every time:** treat anything Graeham tells Claude verbally about a comp (a phone call to a listing agent, a recollection of a price, "I think it's around X") purely as a lead to verify, never as report content. Once verified, write the comp into the report using only the confirmed facts, in the same neutral third-person-comp voice as every other comp in the table. Do not narrate the correction. Do not build a "what you said vs. what's true" comparison anywhere in client output; that dialogue happens in chat with Graeham, never in the deliverable.

Scan before publishing for first-person Claude voice and any address to Graeham-as-requester: `\bI \b` outside of quoted remarks, `you (asked|described|told|said|mentioned|recalled)`, `your recollection`, `what you (described|said)`, `I pulled`, `I verified`, `I called`. Any hit is a stop-ship defect, not a style note.

## Banned openers — never brace the reader

BANNED verbatim and paraphrased: "First of all," "I want to be straight with you," "Two things I want to be straight with you about up front," "Let me be honest," "To be blunt," "I'll be direct," "Real talk," or any variant that braces the reader for bad news. They read as aggressive and put the client on the defensive.

Instead, open like you are walking them through what you found: "I reviewed the comparable sales, and here is what the data shows." Lead with facts, let them speak.

## Banned sections and phrases

**Net-to-seller sheet** — never include unless Graeham explicitly asks in that specific request. Remove on sight if a template or draft carries one. If you think it would help, leave it out and offer in chat.

**"Notes & Caveats" / "About this analysis" closing sections** — banned in any form, including "What would sharpen this further" and "Condition matters" cards. Condition nuance belongs inside the value-range card descriptions. Reports end on the warm CTA, then one disclaimer line.

**Data-source and MLS-access apologies** — banned verbatim and paraphrased. Never explain how the data was obtained or apologize for tooling:
- "built from public real estate data because MLS access was not signed in"
- "public data is a good directional guide but less precise than the MLS"
- "treat the numbers here as a solid estimate rather than an exact figure"
- printing "N/A" with an apology attached
- any "About this analysis" paragraph naming the data source as a reason for lower confidence

**"No agenda" phrasing** — banned in any report or email: "with no agenda attached," "no agenda here," "no-pressure update," "I like to check in with past clients now and then." Too salesy. Say it plainly: "Here is an update on your home, just keeping you informed."

**The only disclaimer permitted in client output:** "Professional opinion of value, not a formal appraisal."

Tooling and source limitations go to Graeham privately, in chat or a GHL contact note. The client sees a clean, confident report.

## Em-dashes — banned

`—` and `&mdash;` are the single biggest AI tell. Use commas, periods, parentheses, colons, or "to" for numeric ranges. En-dashes in numeric ranges are tolerable but "to" reads better in client prose. Scan for `&mdash;`, `—`, and ` -- ` before publishing.

## Humanizer pass — mandatory

Every CMA narrative and every client email runs through the `humanizer` skill before publishing. Required, not optional. Graeham has flagged tone as stiff more than once.

**Gets humanized:** the market story, per-comp explanations, the key-insight paragraph, pricing strategy narratives, the recommendation paragraph, special-considerations notes, the closing.

**Does NOT get humanized:** comp tables and all numeric data, section headers, property template fields, DRE / brokerage / contact / disclaimer text, chart legends and axis labels, hero section text.

Voice note to pass along: *"Graeham Watts CMA narrative, honest, direct, data-backed, human, no hedging, no cliches, preserve all specific numbers and comp citations exactly."*

Afterward, verify no number, address, or price range was altered.

---

# PART 4 — QUALITY CONTROL (mandatory before delivery)

Do a distinct second pass. Do not re-read what you wrote; go back to the source data and cross-check.

**1. Comp selection**
- Every comp meets criteria: radius (or justified expansion), same city, reasonable sqft, appropriate timeframe.
- No cross-city comp included without an explicit flag.
- "Most Similar" tier genuinely is most similar.
- Fewer than 3 primary comps triggers a "limited data" flag.
- **Date sanity check** — every date in the table falls inside the window the narrative claims. See the date-filter hard rule in `comp-research.md`.

**2. Data accuracy**
- Spot-check at least 5 comps against source MLS: sold price, list price, sqft, lot, bed/bath, DOM, sold date.
- Recompute $/sqft on 5 comps (sold ÷ sqft).
- Recompute list-to-sale on 5 comps (sold ÷ original list × 100).
- Recompute every summary statistic from the comp data.
- No comp appears twice.

**3. Pricing recommendation**
- A concrete dollar figure exists. Qualitative-only guidance is a failed report.
- Prior sale price and date appear in the headline stats, not only in a table below.
- Each range is supported by actual comp data; the recommended $/sqft falls inside the comp range.
- Ranges are ranges, not single numbers.
- Any comp cited by address in the narrative has matching numbers.

**4. Charts**
- Baseline three present and sourced from MLS Stats (screenshot exists in this session's tool calls).
- Trailing month checked for partial-aggregation artifact.
- Chart data matches the tables (12 comps in the table = 12 points in the chart).
- Captions carry the MLS Stats source line.
- No broken or empty canvases.

**5. Narrative consistency**
- Every claim in the market story is supported by data appearing later.
- "Most homes sold over asking" is backed by the list-to-sale data.
- Narrative and pricing recommendation tell the same story.

**6. Branding and formatting**
- Colors correct: black #1A1A1A, gold #C5A55A, white #FFFFFF.
- Name, DRE 01466876, brokerage per `identity.json`, contact info correct.
- Renders at multiple widths.
- No typos in addresses or dollar amounts.

Fix everything found. If a range changed or a comp was removed, tell the user so they know the report was refined.

---

# PART 5 — OUTPUT FORMATS

**Interactive HTML (master, default).** Single self-contained file, Chart.js via CDN, Google Fonts (Inter/Montserrat), sticky nav, responsive. This is the format that gets published and linked.

**Email-safe HTML (on request).** All inline styles, no external CSS/JS/CDN, table-based layout, charts as base64 PNGs, 600px max width, system fonts. Condensed: property summary, top 8 comps, pricing strategy, recommendation.

**PDF (on request).** Print-optimized HTML converted via WeasyPrint (preferred) or xhtml2pdf; ReportLab + matplotlib as fallback. Static chart images, `@media print` page breaks, interactive elements removed, premium styling kept. See `branding.md` for PDF-specific font and color mapping.
