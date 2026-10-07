# Area intelligence and keywords

The goal is a one page Area brief that Graeham reads in two minutes and that every ad claim traces back to. Real numbers only, each with a source and a date. A thin or unflattering finding goes in the brief as it is.

## Sources, in order

| Need | Where | Trap |
|---|---|---|
| Listing facts, price history, status | MLS (Matrix, once Graeham signs in inside the app browser), else the MLSListings public page and Redfin | Say "current asking price, listed <date>". The first entry may have been lower, so never write "offered at this price since the list date" |
| Days on market against like for like sales | The method in `seller-marketing-report/references/data-sources.md`. The Redfin side is `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-marketing-update-example-2026-10-06\builder\redfin_days_on_market.js`, run in the app browser | Redfin's property type filter is unreliable, so read each unit's own type and city. Convert times to Pacific. State how many sales, which were excluded and why |
| Competing supply | Redfin active, contingent and pending, same type and price band | Read each unit's own record before calling it long on market |
| Search demand | Google Keyword Planner, below | No volume is a finding, not a gap to fill |
| Local hooks | Parks, trails, transit, employers, restaurants, from official pages and maps. The local-news-scraper skill for news | Facts about the place, never about the people. No schools, safety or demographics. No walk or drive times unless measured |
| What other listings advertise | Meta Ad Library, and a search for the same terms | Use it to avoid the angle everyone runs, not to copy it |
| Seasonality (optional) | Google Trends | A relative index, not volume |

If an ad will quote a market number, compute it the way data-sources.md says and keep the denominators with it.

## Keyword Planner (search volume)

Graeham's Google Ads account is signed in on his Chrome. Open Tools, Planning, Keyword Planner, then "Get search volume and forecasts". Paste the terms, set the location to United States, and read average monthly searches. A term with nothing is reported as "too few to report" and the brief says that plainly. Write volumes as "about N searches a month". Google's forecasts of clicks or leads stay out of anything Graeham or the seller sees. The tool leaves a draft plan in the account, so remove it afterwards (plan menu, Remove plan).

Test four groups, the listing's own words first:

1. The city and property type: "<city> <type> for sale", "<city> <type>", and the bedroom count.
2. The address, the complex or community name, and "<complex> <city> <type>".
3. The bigger neighbor: "<neighbor city> <type> for sale", "<type> near <neighbor city>".
4. The broad terms: "<city> homes for sale", "<city> real estate".

Starter negatives, adjusted per listing: rent, rental, apartments for rent, lease, jobs, salary, foreclosure, free.

On the first run the condo terms showed about 10 searches a month and the address and complex terms showed none, while the broad city term showed hundreds. The plan said so plainly: Search would barely serve, and video and social had to carry the reach.

## From facts to angles

An angle is one claim, one buyer need and one channel. Write each as: the line, the evidence (fact, source, date), the need it speaks to (payment, commute, low maintenance, space, outdoor, yield, and never identity), where it fits, and the risk. Prefer angles built on a gap the research shows. On the first run the gap was price against the pricier neighboring city, which gave three angles: price first, lifestyle first, and a price tag question, each with the true city beside the neighbor's name. A comparison number such as "almost half the price" stays marked pending until a like for like figure is computed, and is worded with "price", not "cost".

When Graeham wants video hook options, give concept-forge the lane, the buyer need and the facts above.

## The Area brief

```
AREA BRIEF: <street and number>, <date>
1. The listing in one line: price, size, status, list date.
2. Where it stands: days on market and price per square foot against like for like sales, and the competing listings. Counts and exclusions stated.
3. Who is searching: the Keyword Planner table and one honest sentence.
4. Five facts that can carry an ad: each with source, date, and when it expires.
5. Angles: three to five in the form above, with the two to start and the two in reserve.
6. What to skip, and why.
```
