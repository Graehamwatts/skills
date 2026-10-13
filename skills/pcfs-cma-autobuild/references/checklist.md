# Past-client Home Value Update: what every report must have

The page is a friendly value update for someone who already owns the home and is not selling. It is not a listing presentation. `build.py` produces the structure below; this file is about what you put into it.

## Sections (the builder writes them in this order)

1. Hero: HOME VALUE UPDATE, address, "Prepared for [first name], [month year]", logo, DRE.
2. Where You Stand: the lead paragraph and four tiles (most-likely value, what they paid, change, most-likely range).
3. Your Home: facts table with ownership context.
4. The Market Story: 4 to 6 short paragraphs in second person.
5. Comparable Sales: Most similar (with the subject as a highlighted row), Reference only, For sale and in contract.
6. Market Trends: `trendPrice`, `trendLS`, `newList`, `monthsInv`.
7. Interest Rate Environment: four sources and one plain read on what it means for an owner.
8. Price Cuts and Your Equity: the list-to-sale table and `priceJourney`.
9. Where Your Home Lands: `compBar`, `psfChart`, closest-matches table, `priceDom`.
10. What Your Home Is Worth Today: three range cards and the one disclaimer line.
11. Staying In Touch: the referral ask and contact block.

Comp table columns are fixed: tier, address and note, miles, bed/bath, sq ft, lot, built, original list, final list, sold, cuts, $ vs original, list to sale, DOM, closed, $/sq ft. If a column's data is missing, the cell is blank. Never print N/A.

## Voice

- Open the lead with: "Hi [first name], here is an update on your home, just keeping you informed."
- Second person throughout. Never "the client", "the owner", "the seller", "he", "she" in body text.
- Plain and warm. Short sentences mixed with longer ones. No em dashes or en dashes anywhere: use commas, colons, or "to" for ranges.
- Lead with where they stand and their equity. One soft line is allowed near the end: "If you ever want to talk through what a sale would actually net you, I'm here."
- End on the referral ask. Never end on a caveat.

## Banned in anything the client sees

- "no agenda", "no-pressure", "I like to check in", any sales push ("let's list", "ready to sell").
- Any mention of where the data came from or of MLS access: no vendor names, no "public data", no "Source:", no "estimate only", no "verify these numbers". The data source goes only in the internal note of the review email.
- A notes, caveats or "about this analysis" section in any form. Condition nuance lives inside the three range cards.
- Pricing-strategy or list-price advice.
- The former brokerage name, "Compass Real Estate", or any DRE other than the one `brand.py` supplies.
- The only disclaimer allowed: "Professional opinion of value, not a formal appraisal."

## Wording that reviewers flag every time

Write these correctly the first time.

- **Days on market end at the accepted offer, not the closing.** "Took 62 days to get an offer and closed in July", never "closed in July after 62 days".
- **"Best", "closest", "every", "all" must be literally true** of the rows on the page. If two private sales went higher, say "best open-market price". If one fixer is in the band but shown elsewhere, say so.
- **Counts must match the tables.** "Nine homes" means nine rows a reader can find.
- **State the band a chart uses** (distance, size range, since which date) in its caption, and count captions through the last plotted month only.
- **Say which rows are outside the tier medians** when a row has a neutral badge.
- **Tier words come from the listing remarks.** "Updated" needs the listing to say so. "Dated" needs it to say the kitchen or baths are original. Otherwise use a neutral badge and a factual note.
- **A price raised before sale is not an overbid.** If the list price went up and the home sold at the new price, say that.
- **List what was left out** of each table and why (size, distance, age, school, status).
- **Do not claim "three years"** for a series that starts 34 months back: "nearly three years".
- **Do not say prices held** if the trailing median is lower than a year ago. Say what did hold (the band, price per square foot) or say it is lower.
- **Name the assumption behind the value** in the lead when it rests on one (a working second unit, a condition you cannot see).
- **A home listed for 91 days without a cut, or a seller who cut twice,** is an observation. It becomes advice the moment you add "so price at". Stop at the observation.

## Review email

- Subject: `[REVIEW -> forward] CMA ready: [address] - [client name]` (the builder writes it with the arrow character).
- Top half, internal: forward-to address, client, property, due date, value and range, median $/sq ft and comp count, live link, data source, then QC notes. Lead the notes with whatever the reader must decide before forwarding.
- A red "delete everything above" banner, then the client email: suggested subject, greeting by first name, two or three short paragraphs with the value stated plainly, the link, the referral ask, the signature.
- The connector strips CSS backgrounds and wraps links in a Google redirect. The template already works around both. Tell the reader to re-link before forwarding (the note is added automatically).
- Never invent family or personal details for the greeting. "Hope you're doing well" is enough.
