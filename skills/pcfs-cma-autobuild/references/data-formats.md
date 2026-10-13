# Data formats and definitions

These are the files the scripts read from `data/` in the WORK folder, and the exact definitions the reports use. Hand this file to the reviewers along with the report and the data files.

## Data files (folder `data/`)

One set per market key. A market is whatever geography the trend charts should describe: a whole city (for example `epa` = East Palo Alto), or a box around the subject filtered by city label, zip or side of Highway 101. Pick it once per subject and state it in the chart captions (`trend_geo`).

- `rec_<mkt>.txt`: one closed sale per line, closed on or after `WIN['rec_from_date']` (the 1st of the month 14 months before the last complete month; `python mkt.py` prints nothing without it, so check `build.py --facts`), pipe separated:
  `id|address|city|sold_date|sold_price|sqft|lot_sqft|beds|baths|year_built|lat|lon|side_of_101(E/W)|list_date|contract_date|orig_list|final_list|n_price_cuts|first_list_date|property_type|county_sqft|county_beds|county_baths`
  - `list_date` = start of the listing period that led to the sale (latest Listed or Relisted event); `first_list_date` = first Listed event of that same listing chain; `contract_date` = first Contingent or Pending event after `list_date`.
  - `orig_list` = first list price of the chain; `final_list` = last list price before the sale; `n_price_cuts` = number of price decreases.
  - Blank `list_date` = the sale has no listing events (private or off-market sale).
  - sqft / beds / baths in columns 6, 8, 9 are the listing's figures; the county figures are the last three columns.
- `act_<mkt>.txt`: homes for sale or in contract on the run date:
  `id|address|city|status|asking_price|sqft|lot|beds|baths|year_built|lat|lon|side|list_date|contract_date|orig_list|final_list|n_price_cuts|first_list_date|property_type`
  - An active with no list event gets its list date from the search record's days on market: put `"<id>": "YYYY-MM-DD"` under `active_list_dates` in run.json.
- `old_<mkt>.txt`: closed sales before that date, semicolon separated, each `yymmdd,sold_price,sqft` (same geography). Used only for the three-year price trend and the $/sqft comparison.
- `rem_<mkt>.txt`: `id|assigned elementary school (blank for epa)|first ~300 characters of the listing remarks` for the comps used.

## Definitions used in the reports

- Distance = straight-line miles from the subject's lat/lon (below).
- DOM in the comp tables = days from first listing to accepted offer: `contract_date - first_list_date` when `first_list_date` is within 120 days before `list_date`, otherwise `contract_date - list_date`.
- List to sale = sold price / original list price. $/SqFt = sold price / listing sqft.
- Trend charts use single-family only (`property_type == SFR` in rec/act; all rows in old).
  - Median sale price: for each month, median of all sales closed in that month and the two before it (shown Dec 2023 to Sep 2026), plus single-month medians as grey dots when a month has 3 or more sales.
  - Sale price as percent of list: median of sold / final_list over the same trailing three months, using only sales that have a list date, a contract date and final_list > 0, and whose list date is not the sold date.
  - Trend "days to contract" in prose = median of `contract_date - list_date` over the same rows; "sold over asking" share = share with sold > final_list.
  - New listings by month: count of `list_date` in that month (closed sales whose list date differs from sold date, plus current actives). Closed sales by month: count of sold dates.
  - Months of inventory at a month end = homes listed on or before that day and not yet in contract (for closed sales with no contract date, contract is taken as sold date minus 25 days; current Active / Coming Soon count if listed by then; current Contingent / Pending count only until their contract date), divided by the average monthly closed sales over that month and the two before it.
- The bubble chart shows SFR sales since the report's "since" date within the stated radius and sqft band, same side of Highway 101, that have a DOM.
