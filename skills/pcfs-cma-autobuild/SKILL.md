---
name: pcfs-cma-autobuild
description: "Builds the weekly past-client Home Value Update CMAs for Graeham Watts end to end: pulls the PCFS due list, checks each client still owns the home, pulls comps and market trends, builds the branded report page with charts, has it independently reviewed, publishes it, and sends a review email (internal note on top, forward-ready client email below) to Graeham and client care. Nothing is ever sent to a client. Use this skill ANY time the user mentions: PCFS CMA, past client CMA, past-client CMAs due, weekly CMA autobuild, run the past client CMAs, home value update, annual CMA for a past client, equity update, value update for a past client, CMA due list, or asks to build or re-run a home value update for someone who already owns the home and is not selling. Also use it for the scheduled Monday pcfs-cma-autobuild-weekly task."
---

# PCFS CMA Autobuild

Builds past-client **Home Value Updates**: a branded web page per client plus a review email. The page goes to the client only after Graeham or client care reads the review email and forwards the bottom half by hand.

**Three rules that never bend**

1. **Never email a client.** Review emails go only to the addresses in `review_to`. Never to the client, never CC.
2. **Only build on a home the client owns today.** Not the home they sold, not a home that is currently listed for sale.
3. **No number is typed by hand.** Tables and charts come from the scripts; prose numbers are copied from `build.py --facts`.

The scripts in `scripts/` do the mechanical work. Your judgment goes into four things: the ownership check, which comps count and what tier each is, the value range, and the plain-language story.

## What you need on this computer

- Python 3.10 or newer (standard library only).
- The Claude desktop app's built-in browser pane (for MLS, or the public-records route when MLS is signed out).
- The Gmail connector (`send_message`).
- To publish: `git` and a local clone of `Graehamwatts/online-content` with its access token file. Tokens are never emailed or pasted into chat. If this computer cannot publish, stop after the build, say so, and do not send review emails with dead links.
- Optional, they make the ownership check faster: the GoHighLevel token file and the past-client master spreadsheet. Without them, use the public listing record and ask the operator when ownership is unclear.

**Only one computer should run a given week.** The shared log `cma/_autobuild_log.json` in the content repo is what prevents double builds, so pull the repo before step 1 and push the log at the end.

### Model and effort

The heavy lifting is scripted, so this does not need the top model. A Sonnet-class model at **high** effort runs it. Spawn the reviewers with `model: "sonnet"`, `effort: "medium"` and the humanizer pass with `model: "sonnet"`, `effort: "low"`. Keep the independent review no matter which model writes: it is what catches a value that leans high. Step up a tier only when a run hits something unusual, such as conflicting ownership records or a one-of-a-kind property.

## The run

Work in a scratch folder (the session scratchpad), called WORK below. Run every script **from WORK** as `python "<skill>/scripts/<name>.py"`. Write scripts and JSON with the Write tool, not shell heredocs (heredocs mangle quotes and backslashes).

### 0. Start the run file

Create `WORK/run.json` from `references/examples/run.example.json`: today's date, the report month, `review_to`, `live_base`, and empty `subjects`. Then:

```bash
python "<skill>/scripts/mkt.py"
```

It prints the chart windows for this run date, including the date the detailed sale records must start from. Add a market key (`mkt.py epa`) later to print that market's trend figures.

### 1. Due list and dedup

`curl -s "https://n8n.graehamwattsn8n.com/webhook/cma-due-list?days=7"` returns `{count, due_cmas: [{client_name, email, property_address, due_date, contact_id}]}`. Pull the content repo, read `cma/_autobuild_log.json`, and skip any `{client_name + due_date}` already logged (sent or held).

### 2. Ownership gate, for every client

The feed is not reliable about who owns what. It returns the transaction address even after the client sold it, it includes contacts tagged do-not-follow-up, and it cannot know a home is on the market. Check each one:

- **Last recorded sale.** Is the client on the buy side of it? The public listing page shows "Listed by ... Bought with ..." for the last sale. A sale after their purchase date means they sold.
- **Currently listed?** An active or pending listing on the subject means hold.
- **CRM and master sheet,** when available: current mailing address, "current home" notes, do-not-follow-up tags, "PCFS inactive".

Then decide:

| Finding | Action |
|---|---|
| Client still owns the address | Build on it |
| Client sold it and a current owned home is on file | Build on the current home. Say in the review email exactly what the ownership rests on, and tell the reader to confirm before forwarding if records do not prove it |
| Client sold and no owned home is known | Hold. Add to `held` in run.json with the reason |
| Home is listed for sale (with anyone) | Hold. A value update must not go out while it is on the market |
| Do-not-follow-up or inactive | Hold |

A hold never stops the run. Keep going with the other clients and report the holds.

### 3. Pull the data

Check MLS first: open `https://search.mlslistings.com/Matrix/Search/Residential/ResidentialSearch?f=` in the built-in browser. A sign-in page means signed out. **Never type MLS credentials.**

Either way the scripts want the same files in `WORK/data/` (layouts in `references/data-formats.md`): `rec_<mkt>.txt` (closed sales with listing history since `rec_from_date`), `act_<mkt>.txt` (for sale and in contract), `old_<mkt>.txt` (older closed sales, date, price, size) and `rem_<mkt>.txt` (remarks and school for the comps you use). A market key is the geography the trend charts describe: a whole city, or a box around the subject filtered by city label, zip or side of Highway 101.

**Signed out (public-records route):** open any redfin.com page in the built-in browser, paste the helpers from `references/redfin_extractor.js` with the javascript tool, and use them to resolve each address, run the sold and active searches, fetch each home's history (`runJob`), and return rows wrapped as `##X:rec_epa##...##END##`. Then run `extract_from_transcript.py` to write them into `data/` without retyping. Rows with no listing events are private sales: keep them out of pricing. If a verification page appears, stop; never solve it.

**Signed in (Matrix):** pull the same fields from Agent Full records and write the same row layouts. Original list price and price changes need the History tab.

Add each subject to `run.json` (`mkt`, `addr`, `lat`, `lon`, and `side` E or W when Highway 101 splits the area, otherwise leave it out).

### 4. Know the subject

County record (beds, baths, size, lot, year, parcel), the purchase date and price, the list price then, and what the last listing said about the home (second units, views, finishes). Note any gap between the county's square footage and the marketed figure. You almost never know today's condition, so every value statement names the condition it assumes.

### 5. Choose comps and tiers

```bash
python "<skill>/scripts/cands.py" <key> 1.0 <since YYYY-MM-DD> <sqft_lo> <sqft_hi>
```

- Same city, same side of any hard boundary (Highway 101, school assignment), about a mile, last six months, size within roughly 250 sq ft. Widen only when thin and say so.
- **Most similar:** the sales that match on size and boundary. **Reference only:** fixers, private sales, bigger homes, the other side of a boundary, older sales on the subject's own street. **For sale and in contract:** state the rule you used to pick them.
- Give each comp a tier from what its **full remarks** say: `R` remodel, `U` updated, `D` dated, `F` fixer, `C` custom, `P` private sale, `O` anything you cannot tier (give it a neutral `badge`). Do not call a neighbor's house dated unless the listing says the kitchen or baths are original.
- If a sale fits the Most similar band but you put it elsewhere, say so on the page.

Write `WORK/comps.py` and `WORK/cfg_<key>.py` from the examples in `references/examples/`. Fill in numbers and comps first, leave the prose for the next step.

### 6. Facts first, then prose

```bash
python "<skill>/scripts/build.py" <key> --facts
```

This prints every table row, tier median, and trend figure. Write the lead, the market story, the cards and the captions **from that output**. For a client who bought within about two years, anchor on their own purchase and run `time_adjust.py` for the move in price per square foot since then.

Setting the value:

- Three ranges that do not overlap: **Likely range** (mostly original condition), **Most likely value today** (state the condition it assumes; its midpoint is the headline number), **Top of range in strong condition**.
- When condition is unknown, a well-kept home sits **just under** the updated tier, not in it.
- A premium for a second unit, a view or a bigger lot needs a comp that shows it.
- If the value is flat or below what they paid, say "roughly even", show it honestly, and flag it at the top of the review email.

Read `references/checklist.md` before writing. It holds the required sections, the banned wording, and the wording mistakes reviewers catch every time.

### 7. Rates

Four sources for the 30-year fixed with their dates: Mortgage News Daily, Freddie Mac PMMS, Bankrate California, and Realtor.com local (use NerdWallet California when Realtor.com will not load, and say so in the internal note). Put them in `run.json` under `rates`.

### 8. Build and look at it

```bash
python "<skill>/scripts/build.py" <key>
python "<skill>/scripts/final_check.py"
```

Then look at the page. Headless Edge from PowerShell renders it to an image, and `tiles.py <name>` cuts that into screens you can read:

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --no-sandbox --user-data-dir="<WORK>\edgeprofile" --hide-scrollbars --window-size=1200,11800 --virtual-time-budget=8000 --screenshot="<WORK>\shots\<name>.png" "file:///<WORK>/out/<file>.html"
```

### 9. Humanizer pass

Copy `cfg_*.py`, `shared.py` and `comps.py` into `WORK/backup`, run the humanizer skill over the prose strings only (a subagent works well), then `numcheck.py` must end with `ALL OK`. No number, address or name may change.

### 10. Independent review (required)

One read-only reviewer subagent per report, using `references/reviewer-brief.md`. Give it only the finished page, `references/data-formats.md`, the data files and a short sheet of raw subject facts. Do not give it your cfg files or your reasoning. It recomputes every row and chart point and returns a findings table.

Fix every Blocker and Should-fix, rebuild, then send the changed parts back to the same reviewer. Publish only when the re-check has no Blocker. If a value changed, say so in the review email.

### 11. Publish

Run the brand check when the toolkit is present (`content-creation-engine/scripts/verify_output_brand.py <file>`, 0 failures). Copy the pages into `cma/` of a fresh clone of the content repo, commit with the noreply identity, push, and wait for each live URL to return 200.

### 12. Review emails

Add a `mail` block to each cfg (subject line, internal QC notes, client paragraphs), then:

```bash
python "<skill>/scripts/emails.py"
```

Send each with the Gmail connector's `send_message` to `review_to` only, passing the `.txt` as `body` and the `.html` as `htmlBody`. Check one with `get_message`: recipients are the review addresses and it carries the INBOX label. The internal note must lead with anything the reader has to decide before forwarding (unconfirmed ownership, a flat value, a sentence they may want removed).

### 13. Log and wrap up

Write `sent.json` (`{"<key>": {"id": "<gmail id>", "sent_at": "<UTC time>"}}`), then:

```bash
python "<skill>/scripts/logappend.py" "<clone>/cma/_autobuild_log.json" sent.json
```

Commit and push the log, and pull the local content folder so it matches. Report back in a few lines: who was built (with links and values), who was held and why, whether MLS or public records was used, and what the reader must check before forwarding.

## Files

| File | Use |
|---|---|
| `scripts/mkt.py` | Loads `data/`, derives the chart windows from today's date, computes trends |
| `scripts/cands.py` | Lists comp candidates by distance |
| `scripts/build.py` | Builds the page; `--facts` prints the verified numbers |
| `scripts/charts.py`, `style.css` | Inline SVG charts and page styling |
| `scripts/time_adjust.py` | Price-per-square-foot change since a recent purchase |
| `scripts/final_check.py` | Structure, banned wording and consistency scan |
| `scripts/numcheck.py` | Proves the humanizer changed no numbers |
| `scripts/emails.py` | Review emails |
| `scripts/logappend.py` | Shared run log |
| `scripts/extract_from_transcript.py` | Saves browser results to `data/` without retyping |
| `scripts/tiles.py` | Cuts a page screenshot into readable tiles |
| `scripts/brand.py`, `assets/` | Brand values and the Boyenga + Compass logo |
| `references/checklist.md` | Required sections, banned wording, lessons from review |
| `references/reviewer-brief.md` | The brief for the independent reviewers |
| `references/data-formats.md` | Row layouts and definitions |
| `references/redfin_extractor.js` | Browser helpers for the public-records route |
| `references/examples/` | Starting points for `run.json`, `comps.py`, `cfg_<key>.py` |

If the `cma-generator` skill is installed, its `references/past_client_mode.md` is the fuller rulebook and wins on any conflict with `references/checklist.md`.
