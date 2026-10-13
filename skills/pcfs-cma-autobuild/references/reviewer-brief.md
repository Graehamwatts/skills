# Brief for the independent reviewer

Spawn one reviewer per report (`model: "sonnet"`, `effort: "medium"` is enough). Fill in the bracketed parts and send the text below. Give the reviewer nothing else: no cfg files, no draft tables, no reasoning.

Before spawning, write `WORK/sources.md`: copy `references/data-formats.md` into it, then add a section per subject with only raw facts (county record, purchase and listing history with dates and prices, the old listing's remarks, assigned schools, lat/lon), the rate figures with their dates, and the brand facts from `brand.py`.

---

You are an independent, read-only quality reviewer for a real estate "Home Value Update" report (a past-client CMA) that is about to be published and emailed. Recompute everything from the raw source data and report what does not match. You do NOT edit the report. Start from the sources, not from the report's own tables.

WORK FOLDER: [WORK]
You may READ only: the finished report `out\[file].html` (subject: [address]; client first name [name]; market key `[mkt]`), `sources.md`, and `data\rec_[mkt].txt`, `data\act_[mkt].txt`, `data\old_[mkt].txt`, `data\rem_[mkt].txt`. Do not open any other file there (the .py files hold the author's draft; reading them defeats the review). Create your own scripts only inside a new subfolder `qc_[key]\`. Write Python to files with the Write tool and run the files. The HTML holds a large base64 image and inline SVG charts: strip `data:image/...base64,...`, and read chart numbers from the `<text>` labels and the `<rect>` / `<circle>` elements.

[One or two lines of context the reviewer needs: which city labels count as the same market, which side of Highway 101, that school assignments are in the rem file.]

CHECK ALL OF THIS and keep counts of what you checked:

1. **Comp selection.** Every comp in all three tables exists in the data files; the stated distance, size, bedroom, school and closing-date bands are true for every row; no comp appears twice; nothing that belongs in the stated "most similar" band was left out without the report saying so.
2. **Data accuracy for every row of every table:** address, beds/baths, size, lot, year, original list, final list, sold, cuts, $ vs original, list to sale, DOM, closed date, $/sq ft, distance (haversine from the subject, 0.01 mi tolerance), asking, was, days listed, status. Use the definitions in sources.md.
3. **Summary statistics:** tier medians and counts by the visible tier label; every number in the lead, the story, the cards, the equity paragraph, the captions and the price-cut paragraph, matched to its row; the gain and its percent; the most-likely value is the midpoint of its own range; the subject's $/sq ft. Recompute any price-per-square-foot comparison the story cites.
4. **Trend claims and chart captions:** latest three-month median and the value a year earlier, the min and max the text cites, sale to list, days to contract, share over asking, months of inventory, sale counts in captions, every bar and point label. The last month plotted must be a complete month.
5. **Subject facts** in the hero, the Your Home table and the story against sources.md. Flag anything stated about the subject that the sources do not support, including inferences presented as fact.
6. **Mortgage rate tiles and paragraph** against sources.md.
7. **Voice and banned content** (each is a Blocker in client-facing text): any em or en dash, "&mdash;", " -- "; third person about the reader (the footer line "Prepared for the owner of ..." is allowed); "no agenda", "no-pressure", "check in"; any mention of the data source or tooling; "estimate only", "N/A"; a notes or caveats section; pricing-strategy advice; the former brokerage name, "Compass Real Estate", or a DRE other than the one in sources.md. The only disclaimer allowed is "Professional opinion of value, not a formal appraisal."
8. **Structure:** ids `trendPrice`, `trendLS`, `newList`, `monthsInv`, `priceJourney`, `compBar`, `psfChart`, `priceDom` each hold a non-empty svg; the ten sections are present in order; the comp table has the nine pricing columns; the page ends on the referral ask; bar counts match table rows plus the subject.
9. **Reasonableness.** Does the most-likely value follow from the evidence shown? Say plainly if a value or range is not supported, by roughly how much, and which comps argue against it. Note anything a careful homeowner or a broker would find wrong, misleading or awkward.

RETURN, as text: (A) a findings table: # | Severity (Blocker / Should fix / Note) | Where | What the source says | What the report says | Suggested fix. Blocker = a wrong number, address, price, date or name, a claim the sources contradict, or banned content. Should fix = a claim the sources do not support, or wording looser than the data. (B) one clean-check line per group saying what was checked and how many items. Quote exact strings. Do not pad. If something cannot be checked from the sources given, say so in one line.

---

## After the review

Fix every Blocker and Should-fix, rebuild, then message the same reviewer with the list of what changed and ask for a re-check of those parts only (Blocker and Should-fix findings only). Tell it about anything you set from information it does not have, such as a tier taken from the full listing remarks. Publish when the re-check has no Blocker.
