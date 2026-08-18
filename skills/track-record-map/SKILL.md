---
name: track-record-map
description: "Builds and publishes The Boyenga Team + Graeham Watts's sold-listings track-record map — an interactive two-view Leaflet map of every closed transaction the team has been on either side of, plus a matching Excel export. Use this skill ANY time Graeham wants to show a client proof of the team's real sales volume/experience (a client pushing back on team credentials, a listing presentation, a CMA's 'Staying in Touch' section), or wants to refresh/rebuild the existing map, or wants to spin up a client-specific reference version of it. First shipped 2026-08-17 for the Shree Khare / 3444 Kenyon Drive negotiation, generalized into a skill the same day so it doesn't have to be rebuilt from scratch next time."
metadata:
  type: skill
---

# Track Record Map

Produces an interactive sold-listings map (2 views) + Excel export proving The Boyenga Team's real transaction volume — both sides of the deal, not just listings. Built once live on the fly, generalized here so future runs are a re-run, not a rebuild.

**Live evergreen page:** `https://graehamwatts.github.io/online-content/track-record/Boyenga-Team-Sales-Map.html`
**Live evergreen spreadsheet:** `C:\Users\Graeham Watts\Documents\Agent a list of in local counties\Boyenga Team Sold Track Record.xlsx`

Default behavior when asked to use this skill: **refresh the same evergreen page/file** (re-run the pipeline to pick up newly closed sales) rather than create a new one. Only branch to a client-specific variant (different output filename, a reference pin for that client's property) if Graeham asks for one.

---

## 0. Brand identity — read this first

Read `skills/shared-references/identity.json` before writing any brand text (DRE, brand line). Never hardcode from memory. Correct DRE is `01466876`; `02015066` is permanently blocklisted.

## 1. Why this exists (the incident that shaped it)

The first build (2026-08-17) searched MLS Matrix by **Listing Agent only**. That produced 301 total records — 211 for Graeham, 90 for "Boyenga" by last-name text search — and Graeham immediately caught that this badly undercounted real volume: a separate research effort had found he personally has 429 closed transactions. The gap was **buyer-side representation** — every deal where the team represented the buyer instead of the seller was invisible to a listing-agent-only search.

**The fix, and the standing rule for every future run:** search BOTH the Listing Agent Lic# field AND the Buyer's Agent Lic# field, for every team member's DRE, then merge and de-duplicate by MLS#. Doing only one side will silently undercount by roughly half. This took the real total from 301 to **625** unique transactions.

A second correction from the same feedback round: the first build color-coded pins by which agent was involved ("Boyenga Team" vs. "Graeham Watts individually") with a split legend. Graeham explicitly rejected this — **"we're all one team... don't differentiate."** Every pin on the map must be a single unified "Boyenga Team" style with one legend entry, regardless of which team member the underlying MLS record shows.

## 2. Team roster — the DRE numbers to search

Confirmed live, working MLS license numbers as of 2026-08-17 (validated by non-empty search results, not assumed):

| Name | DRE / License # |
|---|---|
| Graeham Watts | 01466876 |
| Janelle Boyenga | 01254724 |
| Eric Boyenga | 01254725 |

> **Naming correction:** `shared-references/identity.json` previously said "Eric and Janet Boyenga." MLS records confirm the first name is **Janelle**, not Janet. If you find "Janet" anywhere in this repo going forward, it's the same historical typo — fix it, same as any other blocklisted-value cleanup.

If Graeham adds another team member later, get their DRE from him directly (don't guess) and add it to this table and to `FILES` in `scripts/parse_merge.py`.

## 3. Full pipeline

Run these in order. Each script reads/writes to a working directory controlled by the `TRM_WORKDIR` environment variable (defaults to the current directory if unset) — set it to a scratch folder for this run before starting, e.g. `Skills LLMS\Claude\Skills\skills\track-record-map\outputs\<date>\`.

### Step 1 — Pull raw MLS search results (manual browser step, not scripted)

Using the MLS Matrix session (via `mcp__claude-in-chrome__*`, already logged into Graeham's real Chrome — see `mls-matrix-scraper` skill for connection details), run **6 searches**, one per DRE per side:

1. Status=Sold, **List Agent Lic#** = 01466876
2. Status=Sold, **Buyer's Agent Lic#** = 01466876
3. Status=Sold, **List Agent Lic#** = 01254724
4. Status=Sold, **Buyer's Agent Lic#** = 01254724
5. Status=Sold, **List Agent Lic#** = 01254725
6. Status=Sold, **Buyer's Agent Lic#** = 01254725

Set results-per-page to the max (250 was available) and page through — don't just read page 1. Save each search's raw result-table text to `search1_list_01466876.txt` through `search6_buyer_01254725.txt` in the working directory (plain text dump of the Matrix results grid is fine — that's the exact format `parse_merge.py` expects).

**Matrix gotchas** (confirmed this session, don't relearn them):
- Fm9_Ctrl* field IDs regenerate after every navigation — re-query fresh IDs immediately before each interaction.
- The "Buyer's Agent Lic#" field is a separate criteria field from "List Agent Lic#" — do not assume one search catches both.
- Do NOT attempt to log in yourself if the session is expired — stop and ask Graeham to log in.

### Step 2 — Merge and de-duplicate

```
python scripts/parse_merge.py
```
Reads the 6 raw text dumps, parses each row, merges by MLS# (a transaction appearing in more than one search — e.g. Graeham as buyer's agent AND Janelle as listing agent on the same deal — counts once), writes `merged_listings.json` to the working directory. Prints per-file row counts and the final de-duplicated total — sanity check these numbers before proceeding.

### Step 3 — Geocode

```
python scripts/geocode.py
```
Geocodes every unique address via Nominatim (OpenStreetMap), respecting its 1 request/second rate limit with a descriptive User-Agent. **Caches results in `geocode_cache.json`** in the working directory, keyed by `"<address>|<city>"` — reuse this cache file across runs (copy it forward into the new working directory) so repeat addresses don't re-hit the API. Writes `geocoded_listings.json`. This is the slow step — 625 addresses took several minutes even with most already cached from a prior run. If the process gets cut off partway, just re-run it; it skips anything already in the cache and picks up where it left off.

### Step 4 — Build the HTML page

```
python scripts/build_html.py
```
Reads `geocoded_listings.json`, writes `track-record-map-output.html` to the working directory. **Before running, edit the `SUBJECT` dict near the top of the script** (address, city, lat/lon) if this run is for a specific client's reference property — plus the few hardcoded description strings that mention "3444 Kenyon Drive" / "95051" (search the file for that string; it wasn't fully templated, so these need a manual find-and-replace per client). If there's no specific client this run (just refreshing the evergreen page), leave the existing reference property as-is or ask Graeham what to point it at.

The two views are: (1) a wide South Bay/Peninsula/East Bay footprint auto-fit to all pins, and (2) a **fixed** mid-zoom regional view (Mountain View/Los Altos/Sunnyvale in the northwest, across Santa Clara/San Jose, down to Cupertino/Campbell/Saratoga) — Graeham specifically asked for this framing after an earlier version was cropped so tight to a single city that it only showed 4 pins and looked sparse. Don't shrink this back down to a single-city crop.

### Step 5 — QC

```
python scripts/qc_check.py
```
Checks: wrong DRE (`02015066`) absent, correct DRE (`01466876`) present, "Intero" absent, em-dashes absent, HTML tag-balance, inline `<script>` syntax validity (via Node `new Function()`), and — critically, since this was the recurring defect — **zero occurrences of split-legend text** ("Graeham Watts individually" / "Boyenga Team listing" or similar per-agent labeling). If any of those checks fail, fix before publishing; don't ship with a failing QC.

### Step 6 — Export Excel

```
python scripts/build_xlsx.py
```
Writes an `.xlsx` with one row per unique transaction (same de-duped set that feeds the map — row count must match pin count exactly), columns: MLS#, Address, City, Sale Price, Close Date, Property Type, Beds, Baths, SqFt, Lot Size, Matched DRE/Side(s), Latitude, Longitude. Requires `openpyxl` (confirmed available in this environment). Default output path is `track-record-export.xlsx` in the working directory — override with the `TRM_XLSX_OUT` env var to write directly to the evergreen location: `C:\Users\Graeham Watts\Documents\Agent a list of in local counties\Boyenga Team Sold Track Record.xlsx`.

### Step 7 — Publish

Copy the built HTML to `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\Online Content\track-record\Boyenga-Team-Sales-Map.html` (or a new client-specific filename in the same folder, if this is meant to be a separate page rather than a refresh of the evergreen one). Publish via the standard clone-to-`/tmp` pipeline documented in `cma-generator/references/publishing.md` — clone `online-content` fresh, copy the file in, commit, push with the PAT from `Online Content/github-token.txt`.

**After pushing, fetch the LIVE URL directly and verify it, not your local copy.** This exact map had two rounds where the live page silently stayed on stale content after a "finished" build — always `curl` the actual live URL, extract the pin-array length from the live response, and compare it to your local file's count before calling it done.

## 4. Disclosure requirement

Because the count includes both listing-side and buyer-side transactions, the page must carry a visible caption disclosing this (e.g. *"Includes homes listed and sold by the team, and homes purchased by team-represented buyers"*) near the total-count stat. Don't blend both without disclosure — a client who later asks "how many have you personally listed" deserves an honest, distinguishable answer, and the underlying data (the "Matched DRE/Side(s)" column in the Excel export) supports answering that if asked.

## 5. Numbers as of the 2026-08-17 build (for reference — re-run to get current numbers, don't reuse these as if they're live)

- Total unique, de-duplicated: 625
- Graeham Watts (listing + buyer): 363
- Janelle Boyenga (listing + buyer): 209
- Eric Boyenga (listing + buyer): 53

Note Graeham's own 363 did not fully reconcile with an outside "429" figure he'd been told previously — most likely explanation is that MLS Matrix's earliest record in this system is Feb 2000, so pre-2000 deals, a different MLS board, or unrecorded referral business could account for the gap. Report real, MLS-verified numbers each time rather than forcing a match to a previously-cited figure.
