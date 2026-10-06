# Report structure

Letter pages (8.5 x 11 in), one HTML section per page, printed to PDF with Edge headless. Montserrat headings, Source Sans 3 body. Each page has the brand strip (name in gold caps, REALTOR with the registered mark), a running header with the address and page title, and a footer with the page number and "Updated <date>". Content must stay above the bottom margin (limit 747 pt of the 792 pt page); `overflow_check.py` and `final_checks.py` enforce it. Charts are inline SVG so they survive printing.

## The real report (10 pages)

1. **Cover.** Hero photo, address, "Marketing update", date, price and key facts, DRE and brokerage line, link to the property page.
2. **Where you stand.** The headline result in one sentence (for example, day 24 against 72 days on average for the other eight sales). A bar chart of days to contract for the comparison sales with the subject's day marked. The denominator statements: how many closed, how many excluded and why, average, median, range, how many were under contract by the subject's day count, and the effect of counting the excluded same day sale as zero. One sentence on the second comparison group and one on long running active listings.
3. **The data behind page 2.** Table of every closed sale in the window (sold date, address, price, sq ft, list date, contract date, days), excluded rows marked with the reason, the live competing listings, the cut by bedrooms with price per square foot against the subject, and a two line method note.
4. **What buyers are telling us.** Counts (tours, agents who received the disclosure package, open houses, offers) and agent comments as reported, with what is pending.
5. **Since you listed.** Dated timeline of marketing events, true dates only.
6. **This week and next.** Channel by channel table with status chips (Switched on, Prepared, On hold, Not launched), what happens before the next call, and the accounts checked paragraph when no delivery rows exist.
7. **The first ads.** The video versions with thumbnails and one line each, plus the Drive folder link.
8. **Prepared posts.** Carousel and post previews, the AI generated furniture and props disclosure, photo and map credits.
9. **Google Search plan.** Real volumes table, prepared ad previews verbatim, and a plain statement of how little condo specific searching there is.
10. **What comes next.** Next steps in sentences, the open house, the next call, links.

## The full campaign report (13 pages)

Pages 1 to 6 as above, then: What the ads delivered, What the posts delivered, Property page traffic, The creative (two pages), Google Search plan with results, and a closing page on what was learned and what comes next. Use it for real only when platform exports exist for every number on the results pages. The internal sample uses simulated figures (see `sample-mode.md`).

## Checks that must pass

Page count, no dash characters of any kind, required phrases present, banned phrases absent (example, illustrative, Box, ad budget and dollar amounts, retired brokerage names), REALTOR with the registered mark, DRE from identity.json, link set equals the expected set, nothing past the bottom limit. `final_checks.py` in the builder is the model; rewrite its expected strings for each listing, because it checks the exact numbers and phrases of the example.
