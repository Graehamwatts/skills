# Data sources and methods

Every printed fact needs a source you read in the current session. This file says where each fact comes from and which mistakes to avoid. Each trap below caused, or nearly caused, a wrong number on the first report.

## Subject listing

Pull the MLS record. Matrix works once Graeham signs in inside the in-app browser pane and opens Matrix from his dashboard (Chrome extension tabs cannot reuse that login). With no MLS access, use the MLSListings public property page and Redfin.

Record the list date, the full price history (every change and relist), beds, baths, sq ft, HOA dues, property type and status. Read the history before writing "listed at": the first report nearly said "offered at this price since the list date" when the listing had first entered a little lower and been raised the next morning. Say "current asking price, listed <date>".

## Days on market for comparable closed sales

Redfin hides days on market on sold records, so rebuild it from each sale's listing history. `builder\redfin_days_on_market.js` in the example folder does this in the in-app browser pane (Redfin's API only answers from a redfin.com origin). The rules, each of which fixed a real error:

1. Convert every event time to America/Los_Angeles before taking the date. A UTC date is a day off for evening MLS events.
2. List date is the earliest copy (MLSListings, bridge, other MLS) of the latest Listed event before the sale.
3. Contract date is the first Contingent or Pending event after that listing. The first pass used the last Pending date, which overstated days after fall throughs.
4. Days is contract date minus list date. A sale with no contract event (listed and closed the same day) or no MLS sold event (private sale) is shown and excluded, never silently dropped.
5. Redfin's property type filter is unreliable. Its condo filter returned a mobile home and a single family house, and its house filter returned a Palo Alto city address and non houses. Keep `propertyTypeName` and city on every row and filter on those.
6. Cross check the final rows against MLSListings public pages: type, city, and "Days on Site" equal to the list date.
7. The window is the 12 months of closings before the report date. Show the sample size, average, median, range, how many were under contract by the subject's current day count, and how many took more than 90 days.
8. Compare like with like: condos with condos, with a separate cut by bedrooms when the subject is a one bedroom. A second group (for example single family homes) gets the same filtering and its statistics are computed in code. Name the group exactly ("single family homes with a recorded contract date").
9. Redfin's own market graphs ran about three times too high against the MLS records. Rebuild trends from records and never quote the graph.

Redfin API notes: the `gis` search needs `mpt=99` or its parameters are ignored, and responses start with `{}&&`. Status 9 is sold, 131 is active plus contingent plus pending, 130 is pending. Detail comes from `home/details/belowTheFold` and `aboveTheFold`.

Live competing listings use status 131. Check each one's type and city before counting it, and take days on market from its list date. Call a unit long on market only after reading its own record.

## Search demand (Google Keyword Planner)

Use Graeham's Google Ads account through the Chrome extension, Keyword Planner, "Get search volume and forecasts". Enter the terms the Search plan would target and read monthly searches. A term that reports no volume is reported as having none. State volumes as "about N searches a month" and never turn them into expected leads or clicks in a real report. Keyword Planner leaves a draft plan in the account, so remove it afterwards (plan menu, Remove plan).

## Activity

Use the live activity sheet the team keeps for the listing (tours, agent feedback, open houses, offers) and the weekly status reports as they were sent to the seller. Count what the sheet counts and quote what the agents wrote. Do not read preferences into a comment, and treat terms like "the unit upstairs" and open house dates as the sheet's words only. Leave out any personal detail about a buyer, such as disability, health, family or finances, even if an agent wrote it.

## Ad and creative status

Ask whoever set the ads up (often another AI session or an assistant) for a written status note with exact times, and quote it. If you cannot see the ad platform, say what you were told ("switched on overnight, scheduled to end at 12:26 am on October 13, no spend or clicks at the first check") and show prepared ad copy labeled as prepared. If the connected ad accounts return no delivery rows for the window, keep a short paragraph saying which accounts were checked and that unrelated campaigns are excluded from this property's results. Graeham asked to keep that paragraph; adapt the account counts to what you actually checked.

The creative library is a Box or Drive folder. List the files and sizes, and use real thumbnails.

## Platform exports (when ads have really delivered)

Pull from the platforms and never estimate:

- Google Ads and YouTube: impressions, clicks, click through rate, views, view rate, unique reach. Cost stays out unless Graeham says to show it.
- Meta: impressions, reach, link clicks and engagements, by post and by ad.
- Google Analytics for the property page: users, new users, sessions, engaged sessions, average engagement time, key events (gallery opens, form starts, tour requests), by source and medium.

State the reporting window and what was excluded. If Analytics is not connected or the real numbers are tiny, leave the traffic page out rather than dressing it up.
