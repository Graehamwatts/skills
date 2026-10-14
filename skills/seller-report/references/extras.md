# The optional sections: online views, similar homes nearby, online ads, the masthead photo

Four things a report may carry and never needs. Each is built from a small file in the listing folder. A report
with none of them is a complete report. `run_issue.py` fetches nothing: it reads what is on file.

| Section | File in the listing folder | Tool | Prints |
|---|---|---|---|
| Online views | `online_views.json` | `scripts\online_views.py` | a row in the numbers table, a chart and a column in the weekly table |
| Similar homes nearby | `nearby.json` | `scripts\nearby_update.py` (and `scripts\nearby_from_mls.py` for the MLS route) | what changed this week, then the watch list as one table |
| Online ads and marketing | `marketing.json` | written by hand from a status note | each channel with its status word |
| Masthead photo | `listing.json` (`hero_photo`) | `scripts\hero_photo.py` | the photo under the masthead band |

**When the email is long** these sections give way first, before anything about people (`sr_render\fit.py`,
`extras`): similar homes nearby keeps what changed and says the rest in one sentence ("The other 5 homes did not
change: 3 active, 1 pending and 1 sold."), the chart of online views is left out (its row in the numbers table
stays), and prepared ad channels join the one sentence for channels that are not on. The link copy and the PDF
always carry the full sections. The ship gate counts the short forms again too.

## 1. Token thrift: the rules, and where the code holds them

These are enforced by `scripts\sr_lookups.py`, not left to memory.

1. **Nothing optional is fetched unless the operator asked for it in this session, or the listing's settings say
   to.** `plan` refuses without `--asked` unless `listing.json` has `extras.<source>.every_issue: true`.
2. **A hard cap per issue.** ONE scripted lookup for the similar homes nearby. ONE page per portal for online
   views. A second `plan` for the same issue is refused, whatever became of the first
   (`sr_contract.LIMITS`: `nearby_lookups_per_issue`, `portal_pages_per_issue`).
3. **Scripts do the work and Claude reads compact JSON.** Never a whole web page, never a whole spreadsheet. The
   snippets in `scripts\web\` return a few hundred bytes to a few kilobytes. `store` and `add --result` refuse
   anything over the cap (`nearby_json_max_bytes`, `portal_json_max_bytes`) and anything that is not one JSON object.
4. **A block is a stop.** When a page or a lookup answers 403 or 429, shows a human check (CAPTCHA, "press and
   hold"), or does not load: stop at once, close the lookup with `skip`, and build without that section. Never
   retry, never try another address, another page or another site to get the same thing. The snippets
   themselves stop at the first blocked request and say so.
5. **A skipped lookup is said in the chat reply, never in the report.** The build puts one plain line in
   `notes_for_operator.json` ("Similar homes nearby could not be checked for this report: the site blocked the
   request. That section is left out of this report."). A skipped lookup always keeps a place among the five
   "worth a glance" lines.

Public pages only, read-only, no sign-in, nothing typed into a page. The snippets read; they never click,
submit or send anything anywhere. The one exception is the MLS route for similar homes nearby (section 3): there
Graeham signs in to MLSListings himself, and the snippet still only reads the results grid on the screen. Claude
never types a password, a code or a username anywhere.

## 2. Online views

Views and saves per portal, kept so they build up week by week.

**Two ways in.**

- The operator gives the numbers: `online_views.py add --folder <folder> --portal Zillow --views 812 --saves 31
  --counts since_listing`. No lookup is involved.
- When asked, Claude reads the listing's public page on a portal: `online_views.py plan --portal Zillow --asked`
  (it prints the page address from `extras.online_views.pages` and the three steps), open that one page, run
  `scripts\web\portal_views.js` (call `globalThis.srPortalViews()`), save what it returns, then
  `online_views.py add --result <file>`. The snippet returns only `{portal, views, saves, as_of}`.

**What a figure counts.** Always say which (`--counts` is never guessed):

- `since_listing`: the running count a site shows since the home was listed. This is what every portal page
  shows. The week's own figure is then this reading minus the reading of the week before. A portal's first
  reading gives the "since we listed" number and no weekly figure yet (in week 1 the two are the same). A count
  that went down gives no weekly figure and a line for the operator.
- `week`: a figure for that one week, for example from a portal's weekly email.

**Zillow in practice (Oct 13, 2026).** One page: the listing's own Zillow page shows the views and saves since
the home was listed, so it is read with `--counts since_listing`. A weekly figure needs two readings, a week
apart: the first reading of a portal only gives the "since we listed" number.

A reading belongs to the week the report covers (read on Monday or Tuesday, it closes the week that just ended).
`--week` or `--report-date` says otherwise. One row per week per portal: a later figure replaces the earlier one.

```json
{"schema_version": 1, "slug": "sample-glen", "lookups": [],
 "rows": [{"week_start": "2026-04-06", "portal": "Zillow", "views": 800, "saves": 22,
           "counts": "since_listing", "as_of": "2026-04-13", "source": "portal_page"}]}
```

`counts` is `week` or `since_listing`; `source` is `operator` or `portal_page`. `online_views.validate_store`
checks the file and a file that fails stops the build.

**In the ledger** (`ledger.online`): `as_of`, `portals`, `weeks[]` (`n`, `views` and `saves` per portal, for that
week only) and, when a running count was read, `since_listing` (`views` and `saves` per portal).
`totals.online_views` is, portal by portal, the running count when one is on file, otherwise that portal's weeks
added up (`sr_contract.online_totals`). A week with no figure is null and prints "not recorded", never zero.

**On the page.** With any figure on file the numbers table gains an "Online views" row (second figure: saved)
and a line saying which sites and which day. With a weekly figure there is also a chart of views by week and a
"Views" column in the weekly table, whose last line is the count since we listed. Each site counts views its
own way and the page says so.

## 3. Similar homes nearby

A watch list of at most 8 comparable homes, chosen once (same property type, similar beds and size, same area),
re-checked once per issue. The report shows what changed that week: new listing, price change, went pending,
sold (price and days on market), taken off the market, back on the market.

**The one lookup**, on the public site (below) or on the MLS ("From the MLS", further down).
`nearby_update.py plan --folder <folder> --asked` checks the rules and writes
`work\nearby_call.js`: the snippet `scripts\web\nearby_lookup.js` plus one line of arguments for this listing.
Open one public redfin.com page (the page for the listing's city is enough), run that text once as it is, save
what it returns, then `nearby_update.py store --result <file>`.

- **First use.** The lookup hands back up to 12 candidates, each with where it stands. `nearby_update.py choose
  --auto` takes the first 8 in ranked order (same building first, homes still for sale or pending before sold
  ones, then closest in size); `choose --ids ...` picks by hand. The same lookup's data becomes the first
  snapshot. No second lookup.
- **Every later issue.** The lookup returns the watched homes only, and `store` prints one sentence ("2 of the 6
  homes we are watching changed: 1 went pending and 1 price change.").
- **Blocked or failed.** `nearby_update.py skip --reason blocked|captcha|failed|pane_unavailable|not_found`. A
  result that itself says `blocked` or `captcha` is closed as skipped by `store`.

The search needs the site's region id for the city. Put it in `listing.json` under `extras.nearby.search`
(`region_id`, `region_type` 6 for a city, `market` when known, `uipt`), or run the snippet on the site's page for
that city, whose address carries the id (`/city/<id>/...`).

**What changed is worked out in Python** (`nearby_update.change_of`), from the dated events of each home. An
event counts when it is dated after the previous check, or, with no previous check, on or after the first day
of the report week. When no dated event explains a difference between two checks (pending last week, active
now), the difference itself is the change, dated the day it was seen and printed with "by", not "on"
(`change_date_approximate`). Days on market run from the list date to the first accepted offer, the sale or the
day the home left the market, and to the day of the check for a home still for sale.

`nearby.json` holds `scope` (the sentence printed above the list), `chosen_on`, `search`, `watch[]` (`id`,
`address`, `beds`, `baths`, `sqft`, `why`: one plain reason it was chosen), `candidates`, `snapshots[]` (one
per issue: `report_date`, `as_of`, `homes[]` with `status`, `list_price`, `list_date`, `pending_date`,
`sold_date`, `sold_price`, `off_date`, `price_change {date, from, to}`) and `lookups[]`.
`nearby_update.validate_store` checks it.

**In the ledger** (`ledger.nearby`) the section exists only when a snapshot was taken for this issue: `as_of`,
`checked_for_this_issue`, `scope`, `source`, `homes[]` (`address`, `beds`, `baths`, `sqft`, `status`,
`list_price`, `sold_price`, `days_on_market`, `change`, `change_date`, and where they apply `price_before`,
`change_date_approximate`). At most 8 homes.

**Privacy.** Public street addresses are printed in this one section, as in a market analysis. Everywhere else
the rule is unchanged: never where a buyer went, never another client's home. The ship gate fails a watched
home's address anywhere outside the section, a unit in the listing's own building included.

**Traps the snippet already handles** (each caused a wrong number once; `market-and-marketing.md`, section 3):

- Event times are turned into Pacific dates first. A UTC date is a day off for an evening MLS event.
- The list date is the earliest copy of the latest "Listed" event; the contract date is the first Pending or
  Contingent event after it.
- The site's property type filter is not reliable (its condo filter has returned a mobile home and a house, and
  homes in another city). Every home's own type and city are read and checked.
- Answers start with `{}&&`, and the search needs `mpt=99` or its filters are ignored.

Tested against a pretend site under Node (`tests\test_web_snippets.py`). **Not yet proven against the live
site from this skill:** on Oct 13, 2026 the first request of a lookup was answered 403 and the lookup was
skipped, as rule 4 says.

### From the MLS: one Matrix search on MLSListings

What worked on Oct 13, 2026 for both listings, when the public site answered 403. It is the same one lookup
per issue (rule 2), planned with `--site mls`, and it is used only when Graeham is there to sign in.

1. `nearby_update.py plan --folder <folder> --asked --site mls`. It writes `work\nearby_call.js`
   (`scripts\web\matrix_grid.js` plus the call `globalThis.srMatrixGrid()`) and prints the steps below with this
   listing's type, beds and city filled in.
2. **Graeham signs in** to MLSListings in the in-app browser himself. A sign-in page is a stop like a block:
   the grid script answers `{"ok": false, "reason": "signed_out"}` and nobody works around it.
3. **The search**, once: Matrix Residential Search
   (`https://search.mlslistings.com/Matrix/Search/Residential/ResidentialSearch`) with
   - Status: Active, Contingent, Pending, Sold
   - Property sub type: the listing's (condominium, townhouse, single family)
   - Beds: the listing's bedroom count
   - City, or the zip code for a tighter area
   - COE Date with a start date and a plus, in the form `6/1/2026+`. The close date applies to sold rows only,
     so active, contingent and pending homes all still come back.
4. **Two displays of the same results** (switching the display is not a new search). Show every row on one
   page: a grid that says "1 - 50 of 73" is refused whole.
   - `my:Closed date template`: Price, Sale Price, Close Date and DOM. Run the call text, save exactly what it
     returns to `work\mls_grid_closed.json`.
   - `Agent 1 Line Hotsheet`: Change Date and Change Type. Run the same text again, save it to
     `work\mls_grid_hotsheet.json`.
   The script reads only these columns, from whatever of them the display has, by their headings: status, MLS
   number, address, city, property sub type, list price, previous price, sale price, close date, DOM, beds,
   baths, sq ft, change date, change type, and the M.O. (Members Only) flag. Each row comes back as the cell
   text, nothing worked out.
5. `nearby_from_mls.py --folder <folder> --grid work\mls_grid_closed.json --grid work\mls_grid_hotsheet.json
   [--city "<city>"] [--type <sub type>]` writes `work\nearby_mls_result.json`, then
   `nearby_update.py store --result work\nearby_mls_result.json` keeps it, and on first use `choose` makes the
   watch list from it as usual.

**The rules `nearby_from_mls.py` holds** (`tests\test_nearby_mls.py`):

- **Members only is left out.** A listing flagged in the M.O. column never goes into a seller-facing report.
  A home that only appears in a display without the M.O. column is refused, because nothing says it may be shown.
- **The listing itself is left out**, by its MLS number (`listing.json` `mls`) and by its address.
- **Contingent counts as pending.** Its pending date is the change date, when the change type is a status
  change. When the latest change is something else (a price change after it went under contract), the home has
  no pending date and the operator line says so.
- **Sold:** the close date is the sold date and the Sale Price is the sold price. The Price column of a sold
  home is never read, in either display, because a display may put the list price or the sale price there.
- **The MLS's own DOM** is carried as `dom`, and `nearby_update.days_on_market` takes it at its word.
- **One sale, one day count.** When the same sale is also in the time on the market chart (`market.json`
  `sales[]`, matched by address) with a different `days_to_contract`, the `dom` is dropped from the nearby home,
  so the report never shows one sale with two day counts. When the chart prints the same number, or no number,
  the `dom` stays.
- **Refused, never guessed.** A row with a status, price, date, count or members-only flag in a form the script
  does not know, a sold home without a sale price or close date, an active or pending home without a price, or a
  home the two displays disagree about is left out and listed by MLS number in the output.
- **More than 12 homes** keeps the 12 closest to the listing, ranked as `choose --auto` ranks them.
- **The source line** of the section reads "MLSListings, checked Oct 13, 2026" (the day the grids were read).
  `store` copies it into `nearby.json` `source`; a later result from the public site puts that site's own line
  back.

## 4. Online ads and marketing

`marketing.json`: `as_of`, optional `note`, `channels[]` with `channel`, `status`, `checked` (the day that status
was last seen), `detail`, and for a switched-on channel optionally `ends_on`.

| `status` | Printed as | |
|---|---|---|
| `on`, checked for this issue | RUNNING | "Running" only when the channel was checked on or after the last day of the report week |
| `on`, checked earlier | SWITCHED ON, "Last checked Oct 6." | never called running |
| `on` with `ends_on` | adds "Scheduled to end Oct 13." | "Was scheduled to end" once that day has passed |
| `prepared` | PREPARED | ad copy or a video exists and nothing has launched |
| `on_hold`, `not_launched`, `ended` | one sentence in the email, a row each in the link copy and PDF | |

- The section prints **only when a channel is on, or something was checked for this issue** (on or after the
  first day of the report week). Otherwise the builder leaves it out and notes why for Claude.
- **No ad spend amounts**, in the file or on the page. `validate_ledger` rejects a dollar amount in a channel's
  detail and the gate fails one in the section. "No spend or clicks had been recorded at the first check" is
  fine: it states no amount.
- Write the status from a note by whoever set the ads up, with exact dates. Do not say what an ad did unless a
  platform record was read for this issue.

## 5. The masthead photo

A mail client can only show a photo at a public https address. Find one cheaply: run
`scripts\web\hero_photo.js` (`await globalThis.srHeroPhoto()`) on a public page of the listing that is already
open, such as its own property page. It returns the page's share image, or the first photo at least 600 pixels
wide, with its size. Then `hero_photo.py set --folder <folder> --result <file>` (or `--url`). `set` asks the
address for its headers once to confirm it answers as an image. A photo over 1.5 MB is kept and the chat reply
says it will load slowly on a phone. Anything that is not https is left off the page.

Two places that have worked (Oct 13, 2026):

- Graeham's own property page for the listing, `graehamwatts.com/<address-slug>`: its share image.
- The Compass listing page's `og:image`, with the size part of the address changed to `1360x906`
  (`https://www.compass.com/m/<id>/1360x906.jpg`).

No photo is fine. Never open an extra page only to find one. The photo is in the email only: the Gmail-safe copy
that goes into the draft has no photo row, because the Gmail connector drops every image
(`references\data-contract.md`, section 7).

## 6. Settings in listing.json

```json
"extras": {
  "online_views": {"every_issue": false, "portals": ["Zillow"], "pages": {"Zillow": "https://..."}},
  "nearby": {"every_issue": false, "search": {"region_id": 99001, "region_type": 6, "market": null, "uipt": "2"}},
  "hero": {"page": "https://...", "width": 1360, "height": null, "bytes": 154146, "set_on": "2026-04-13"}
}
```

`every_issue: true` is the listing's standing instruction to make that lookup for each issue without being asked.
`extras` stays in `listing.json` and is never copied into the ledger.
