# Sample mode (internal mock up with simulated results)

On 10/6/2026 Graeham asked to see what a full campaign report would look like with results in it, for his own use and as a pattern for future listings, and said clearly it was not going to the seller. The result is a 13 page SAMPLE built from the real report plus simulated ad and website results. Use this mode only for that purpose.

## Rules

- For Graeham only. Never attach it to an email to a seller or any client, never save it in a listing folder, never show it as a record of what happened. If a client needs the same pages, that is the real report built from real exports, not this.
- Every page header carries "Sample report, simulated ad and website results" and the last page carries an explicit note. The marker stays by default so the file cannot later pass as a record. If Graeham asks for it smaller, shrink it, keep one line on every page, and tell him you did.
- The PDF metadata says it is a sample and not for the seller. Name the file with SAMPLE first and "not for the seller" in the name.
- What stays real: the market comparison, the sales, every showing, open house and agent comment, the Keyword Planner volumes, the listing dates and the true ad status. What is simulated: every impression, view, click, visit, like, save and tour request from campaigns that did not run.
- Simulated tour requests are counts only. Never tie a simulated lead to a real person or a real showing.
- Write an assumptions note next to the PDF showing how each simulated number was built.

## Dates in the first sample (dictated by Graeham)

Property page live and creative library ready September 13, posts September 14, first YouTube ad delivered September 13 and Search and YouTube switched on September 15, both ended September 28 after two weeks, new Facebook and Instagram ads October 5 with several more waiting on review, results through October 5. For a new sample, take the dates from Graeham and state them in the assumptions note.

## Method

`builder\sim_data.py` fixes every total first (paid impressions, views, clicks, visits, post impressions and reach, engagements, link clicks, sessions by source, tour requests). It spreads each across the campaign days with weekday and launch effects and a seeded random generator, so a rebuild gives identical numbers, then asserts every sum. Every page that quotes a figure reads it from this one module, so the pages cannot disagree. `make_assumptions.py` writes the assumptions note from the same module, and `sample_checks.py` checks the PDF against it.

Starting points, all benchmark informed and named in the assumptions note:

- Google Search impressions come from the real Keyword Planner volume (monthly volume times days divided by 30.4, times an impression share). Click through sits near the real estate range of about 7.6 to 9.2 percent, with address searches higher.
- YouTube skippable in stream view rate sits somewhat below the cross industry average of about 32 percent when the film is long, and cost per view runs about 0.02 to 0.05 (cost is not shown in the report).
- Organic engagement for a small local agent account ranges from about 0.3 to 3.7 percent on Instagram, with carousels highest.
- Weekend days run 12 to 18 percent above weekdays, the first two days of a campaign run slower, and a few percent of daily noise keeps charts from looking drawn with a ruler.

When the real search volume is thin, the sample says so plainly. A niche listing's honest result is thin.

## Turning it into a real report

When platform exports exist, replace `sim_data.py` with numbers read from them (same names, same structure), keep the pages, remove the sample marker lines and the last page note, keep the dates real, and rerun the checks. Until every figure on the results pages comes from an export, it stays a sample.
