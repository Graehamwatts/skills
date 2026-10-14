# Time on the market, and the marketing status

Two optional sections of the weekly report, and the methods they share with the 10 page seller marketing update. Everything here was carried over from the `seller-marketing-report` skill (first built Oct 6, 2026, for a one bedroom East Palo Alto condo, which Graeham called excellent) and fitted to this skill's files. Online views, similar homes nearby and the photo are in `extras.md`. The 10 page PDF itself is in `marketing-update/README.md`.

## Contents

1. When to build these, and the rules that hold everywhere
2. The subject listing's own facts
3. Days on market for comparable closed sales: the method and its traps
4. market.json: the time on the market section
5. Ad and creative status: the wording
6. marketing.json: the online ads and marketing section
7. Platform exports, when ads have really delivered
8. Search demand (Google Keyword Planner)
9. Where it fits among Graeham's skills

## 1. When to build these, and the rules that hold everywhere

Build or refresh either file only when the operator asks in this session, from sources read in this session. A section prints only when its file holds something for this issue: the market section when `market.json` exists, the marketing section only when a channel is on or something was checked on or after the first day of the report week. A file that is not refreshed stays on file and says how old it is.

1. **Real data only.** The first version of the marketing report, built by another AI, invented "illustrative" ad results, and Graeham could not send it. Every number traces to a source read this session. No "illustrative", "example", "hypothetical", "projected" or "proposed tracking" wording. A number with no source is left out, even a small or unflattering one.
2. **Never backdate an event or show results for an ad that did not run**, in anything a client sees. Graeham once asked for earlier launch dates and matching ad data; the records contradicted them, so the seller copy kept the true dates, and what he wanted became the internal SAMPLE (`marketing-update/sample-mode.md`). If a client-facing request needs dates or results the records do not support, ask for platform proof (post dates, YouTube Studio, Google Ads history, Meta insights) and use only that.
3. **No ad dollar amounts**, in any file or on any page, unless Graeham says to include them in the marketing update PDF. The weekly report never prints one: `validate_ledger` rejects a dollar amount in a channel's detail.
4. **Honest denominators** (section 3, rule 10).
5. **Feedback only.** Time on the market is stated, never turned into advice about price.

## 2. The subject listing's own facts

Read the MLS record (Matrix works once Graeham signs in himself in the in-app browser; a Chrome extension tab cannot reuse that sign-in) or, without MLS access, the MLSListings public page. Record the list date, the whole price history (every change and relist), beds, baths, square feet, HOA dues, property type and status in `listing.json`. Read the history before writing "listed at": the first report nearly said "offered at this price since the list date" when the home had entered a little lower and been raised the next morning. Say "current asking price, listed <date>".

## 3. Days on market for comparable closed sales: the method and its traps

Days to contract is the number of days from the list date to the day the sale first went Contingent or Pending. Each rule below fixed a real error.

1. **Pacific time first.** Convert every event time to America/Los_Angeles before taking the date. A UTC date is a day off for an evening MLS event.
2. **List date** is the earliest copy (MLSListings, a bridge feed, another MLS) of the latest Listed event before the sale.
3. **Contract date** is the first Contingent or Pending event after that listing. The first pass used the last Pending date, which overstated days after a fall-through.
4. **Days** is contract date minus list date. A sale with no contract event (listed and closed the same day) or no MLS sold event (a private sale) is shown and excluded, never silently dropped.
5. **Check every home's own type and city.** Redfin's property type filter is unreliable: its condo filter returned a mobile home and a single family house, and its house filter returned a Palo Alto address and homes that were not houses. Keep the type and city on every row and filter on those.
6. **Cross-check** the final rows against MLSListings pages: type, city, and "Days on Site" against the list date.
7. **The window** is the 12 months of closings before the report date. Say the sample size, the average, the median, the range, how many were under contract by the subject's current day count, and how many took more than 90 days.
8. **Like with like.** Condos with condos, with a separate cut by bedrooms for a one bedroom subject. A second group (single family homes, say) gets the same filtering and its numbers are computed in code. Name the group exactly ("single family homes with a recorded contract date").
9. **Never quote a portal's market graph.** Redfin's own graphs ran about three times too high against the MLS records. Rebuild trends from records.
10. **Honest denominators.** Say how many sales closed, which are excluded and why, and what the average and median become if the excluded sale counts as zero days. When the median is a midpoint, say "halfway between the 51 and 69 day sales", not "the middle sale took 60". Quietly dropping the same-day sale flatters the story, and a careful reader will catch it.
11. **One sale, one day count.** When a sale is also on the similar homes watch list, that section drops its own day count for the sale if it differs from this one (`extras.md`, section 3).

**Where the records come from.** The Redfin side ran in the in-app browser pane with `builder\redfin_days_on_market.js` (in the example folder named in `marketing-update/README.md`), because Redfin's API only answers from a redfin.com page. Its notes: the `gis` search needs `mpt=99` or its filters are ignored; answers start with `{}&&`; status 9 is sold, 131 is active plus contingent plus pending, 130 is pending; detail comes from `home/details/belowTheFold` and `aboveTheFold`. Live competing listings use status 131: check each one's type and city before counting it, take its days from its own list date, and call a unit long on the market only after reading its own record. On Oct 13, 2026 Redfin answered 403. Then the MLS route is Graeham's MLSListings sign-in and one Matrix search (`extras.md`, section 3), reading each sale's list date and its first Pending or Contingent change. A block is a stop: never retry or try another site for the same thing.

## 4. market.json: the time on the market section

Written by hand, in the listing folder, from the records above. The builder recomputes `sample`, `days_to_contract` and `subject_on_report_date` from `sales[]`, so those numbers are never typed, and the page writes its own sentence from them ("Oct 12 is day 31 on the market. 2 of the 8 comparable sales were under contract by that day.") with a bar chart of every sale's days and this home's day marked. Shape (`data-contract.md`, section 6, "market"), with invented values:

```json
{
  "as_of": "2026-04-13", "data_through": "2026-04-12", "refreshed_for_this_issue": true,
  "scope": "Fixture City condos that closed from Apr 13, 2025 to Apr 12, 2026",
  "source": "MLS records, each checked against its MLSListings page, read Apr 13, 2026",
  "method": "Days are counted from the list date to the day the listing first went Contingent or Pending, in Pacific time.",
  "sales": [
    {"address": "14 Sample Fern Ln #3", "sold_date": "2026-02-20", "sold_price": 655000, "sqft": 720,
     "beds_baths": "1/1", "list_date": "2025-12-01", "list_price": 665000, "contract_date": "2026-01-21",
     "days_to_contract": 51, "used_in_average": true},
    {"address": "9 Sample Fern Ln #12", "sold_date": "2025-11-03", "sold_price": 640000, "sqft": 700,
     "beds_baths": "1/1", "list_date": "2025-11-03", "list_price": 640000, "contract_date": null,
     "days_to_contract": null, "used_in_average": false}
  ]
}
```

A sale left out of the average keeps `used_in_average: false` and the page says how many and why. Public street addresses print in this section and in similar homes nearby only. Set `refreshed_for_this_issue` false when the file was not rebuilt this week: the section then says when it was last checked.

## 5. Ad and creative status: the wording

Ask whoever set the ads up (often another session or an assistant) for a written status note with exact times, and write from it. If you cannot see the ad platform, say what you were told: "switched on overnight, scheduled to end at 12:26 am on Oct 13, no spend or clicks at the first check".

| Word | Use when |
|---|---|
| Running | On, and checked for this issue (on or after the last day of the report week). Only a platform record confirms delivery |
| Switched on | On, but last checked before that. Always with "Last checked <date>" |
| Scheduled to end | A switched-on channel with an end date; "was scheduled to end" once it has passed |
| Prepared | Ad copy or a video exists and nothing has launched |
| On hold, not launched, ended | As they say. One sentence in the email, a row each in the link copy and PDF |

- Never "active" or "live" without a platform record of delivery.
- Show prepared ad copy only if it exists word for word. Never reconstruct a description.
- When the connected ad accounts return no delivery rows for the window, keep one short paragraph saying which accounts were checked and that unrelated campaigns are excluded. Graeham asked to keep it; adapt the counts to what you checked.
- If creative uses AI-generated furniture or props, say so: California requires disclosure of digitally altered listing images.
- The creative library is a Box or Drive folder. Box links stay internal: never in a report, an email or a landing page.

## 6. marketing.json: the online ads and marketing section

`as_of`, optional `note`, and `channels[]` with `channel`, `status` (`on`, `prepared`, `on_hold`, `not_launched`, `ended`), `checked` (the day that status was last seen), `detail` (plain sentences, no dollar amounts) and, for a channel that is on, optionally `ends_on`. The page picks the word from the table above by `sr_contract.channel_is_running(channel, report)`, so never write "running" in a detail. Invented example:

```json
{"as_of": "2026-04-13", "note": null, "channels": [
  {"channel": "MLS and home search sites", "status": "on", "checked": "2026-04-13",
   "detail": "On the MLS since Mar 12. The MLS page showed the home as Active on Apr 13."},
  {"channel": "Facebook and Instagram ads", "status": "on", "checked": "2026-04-06", "ends_on": "2026-04-13",
   "detail": "Two ads were switched on Apr 5. No spend or clicks had been recorded at the first check."},
  {"channel": "YouTube ads", "status": "prepared", "checked": "2026-04-06",
   "detail": "The 15 second video is uploaded. The campaign has not launched."}]}
```

Add `--source "ad_accounts|<plain label>|<date>"` on `run_issue.py` when an ad platform or a status note was read this session.

## 7. Platform exports, when ads have really delivered

Pull from the platforms and never estimate. State the reporting window and what was excluded.

- Google Ads and YouTube: impressions, clicks, click-through rate, views, view rate, unique reach. Cost stays out unless Graeham says to show it.
- Meta: impressions, reach, link clicks and engagements, by post and by ad.
- Google Analytics for the property page: users, new users, sessions, engaged sessions, average engagement time, key events (gallery opens, form starts, tour requests), by source and medium. If Analytics is not connected or the real numbers are tiny, leave the traffic page out rather than dressing it up.

The weekly report has no results section; delivered results go in a channel's `detail` as plain counts with their window, or in the marketing update PDF.

## 8. Search demand (Google Keyword Planner)

For the marketing update PDF's search plan. In Graeham's Google Ads account through the Chrome extension: Keyword Planner, "Get search volume and forecasts", the terms the Search plan would target. Read monthly searches; a term with no volume is reported as having none. Say "about N searches a month" and never turn volumes into expected leads or clicks in a real report. Keyword Planner leaves a draft plan in the account: remove it afterwards (plan menu, Remove plan).

## 9. Where it fits among Graeham's skills

| Need | Skill |
|---|---|
| The weekly report, its time on the market and marketing sections, and the 10 page marketing update | this skill |
| Pricing opinion, comps for a list price | cma-generator |
| Paid ads for a listing, from plan to campaigns set up (it hands this skill the status notes) | listing-ads |
| Launch content plan, shot list, call sheet | listing-launch-engine |
