---
name: seller-marketing-report
description: "Builds the seller marketing update for one of Graeham Watts's active listings: a branded PDF of about 10 pages that shows the seller where the listing stands against real days on market for comparable sales, what showings, open houses and agents have said, which ads and creative exist and which are switched on, prepared or on hold, and what comes next, plus an unsent Gmail draft with the PDF attached and a Google Drive link to the creative. Use this skill ANY time the user mentions: seller report, seller marketing report, seller marketing update, marketing update for the seller, campaign report, ad results report for a listing, 'show the seller what we are doing', days on market compared with similar condos or homes for a listing, what the ads and posts delivered, or redoing, refreshing or revising one of these reports. Also covers the internal SAMPLE version (simulated results, clearly marked, never for a client) when Graeham asks what a full campaign report would look like. Not for the Monday status email (weekly-listing-update), listing CMAs (cma-generator) or the launch content plan (listing-launch-engine)."
---

# Seller Marketing Report

The report Graeham sends a seller to show, with real numbers, how the listing compares with similar sales and what the marketing has and has not done so far. First built October 6, 2026 for a one bedroom East Palo Alto condo. Graeham called the result excellent and asked that it become the pattern for future listings.

The worked example lives in `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-marketing-update-example-2026-10-06\`: a README, the REAL PDF (goes to a seller), the SAMPLE PDF (internal only), an assumptions note, and `builder\` (the Python and PowerShell that produced both, which rebuild from that folder as it sits). Read the README first, then open the REAL PDF to see the target.

## Where it fits

| Need | Skill |
|---|---|
| Monday status email with showings, disclosure pulls and portal views | weekly-listing-update |
| Pricing opinion, comps, list price recommendation | cma-generator |
| Launch content plan, shot list, call sheet | listing-launch-engine |
| Proof for the seller of how the listing compares with similar sales, what the marketing has done, and what is switched on, prepared or on hold | this skill |

## The rules, and why they exist

1. **Real data only.** The first version of this report (built by another AI) invented "illustrative" ad results, so Graeham could not send it. Every printed number traces to a source read in the current session. No "illustrative", "example", "hypothetical", "projected" or "proposed tracking" wording. A number with no source is left out, even a small or unflattering one. Website traffic appears only when the Analytics export exists.
2. **Never backdate an event or show results for an ad that did not run, in anything a client sees.** Graeham once asked for earlier launch dates and matching ad data. The records contradicted the dates, so the seller report kept the true ones; he then explained he wanted an internal demonstration, which became the SAMPLE (see below). If a client facing request ever needs dates or results the records do not support, ask for platform proof (post dates, YouTube Studio, Google Ads history, Meta insights) and use only that.
3. **Status wording.** "Switched on", "scheduled to end", "no spend or clicks at the first check", "prepared", "on hold", "not launched". Say "running", "active" or "live" only when a platform record confirms delivery. Show prepared ad copy only if it exists verbatim; never reconstruct a description.
4. **No ad dollar amounts** in the PDF or the email unless Graeham says to include them.
5. **Honest denominators.** State how many sales closed, which are excluded and why, and what the average and median become if the excluded sale counts as zero days. Say "halfway between the 51 and 69 day sales" when the median is a midpoint. Quietly dropping the same day sale flatters the story and a careful reader will catch it.
6. **Brand and compliance.** Read `skills/shared-references/identity.json` for the DRE, brokerage line ("Powered by The Boyenga Team at Compass"), contact details and the Compass disclaimer, and copy the disclaimer verbatim even where it reads oddly. REALTOR always carries the registered mark. If creative uses AI generated furniture or props, the report says so, since California requires disclosure of digitally altered listing images.
7. **Voice.** No em or en dashes anywhere: body, image alt text, PDF metadata, email. Follow `cma-generator/references/report-build.md` Part 3 (banned openers, no data source apologies, humanizer pass on narrative prose). Quote agents as they reported. Never mention a buyer's disability, health, family or finances.
8. **Draft, never send.** The email is a Gmail draft for Graeham to review and send. Do not delete, edit or send an earlier draft unless he asks.
9. **Verify before you hand it over.** Numbers are computed and asserted in code (the builder stops if a printed number changes), then at least one independent reviewer rechecks the final text against sources. The first report took three passes, and the first two missed a mobile home counted as a condo.

## Workflow

1. **Scope.** Collect the subject facts (address, MLS number, list date, full price history, beds, baths, sq ft, HOA, status), the comparison group, the activity record (showings, open houses, agent comments), the marketing status with exact times, the creative library, the property page URL and the search demand. `references/data-sources.md` says where each comes from.
2. **Days on market.** Rebuild each closed sale's days from its listing history in Pacific time, with the type and city of every unit checked. `builder\redfin_days_on_market.js` does the Redfin side in the in-app browser pane; cross check against MLSListings pages. The traps are in `references/data-sources.md`.
3. **Creative to Drive.** Copy the creative library from Box to a Google Drive folder shared view only with the link. Keep Box links out of the PDF, email and landing page.
4. **Build.** Copy `builder\` to the session scratchpad (the example folder stays as the reference). Replace `market_data.py`, the constants and asserts at the top of `build_final.py`, the page functions `p1` to `p10`, the images in `assets\` (`prep_assets.py` shows how they were made) and the expected strings in `final_checks.py`. Then run `build2.ps1 -Name <name> -DriveUrl <root> -CutsUrl <cuts folder>`, then `overflow_check.py` and `final_checks.py`, and look at the page PNGs and the contact sheet it writes. `references/report-structure.md` lists what each page must show.
5. **Review.** Send the final text and source pack to an independent reviewer (a fresh subagent with no context from your reasoning). Fix, rebuild, recheck.
6. **File.** Final PDF goes in the listing folder named like its neighbors; superseded versions go in a `Superseded` subfolder, never deleted. Working files stay in the scratchpad.
7. **Email.** Draft only, PDF attached, links added by hand (the Gmail connector rewrites links and drops attachments on update). `references/email-and-delivery.md` has the recipe.
8. **Report back** in plain prose: what changed, what is still unverified, what Graeham has to decide.

The builder is still a copy and edit job: the layout, styles and checks are reusable, the copy and data are per listing. Parameterizing it (one listing config plus page text blocks) is planned and not done yet.

## Sample mode (internal only)

When Graeham asks to see what a full campaign report would look like before any results exist, build a SAMPLE: same pages plus results pages, every simulated figure fixed in one place and marked on every page header and the last page. It is for his eyes only and is never attached to a seller email or saved in a listing folder. Method, benchmarks and the marker rules are in `references/sample-mode.md`.

## Done means

- Every printed number traces to a source read this session, and the code asserts the computed ones.
- No dashes of any kind, no "example" wording, DRE only from identity.json, REALTOR with the registered mark, links resolve and match the expected set.
- Nothing runs past the bottom margin on any page.
- The email is an unsent draft with the PDF attached and working links, and no sample numbers anywhere.
- Open questions for Graeham are listed in the reply (unconfirmed ad delivery, property page issues, disclosures).

## Reference map

| When you are | Read |
|---|---|
| Gathering facts, computing days on market, reading search volumes and activity | `references/data-sources.md` |
| Laying out pages or deciding what a page must show | `references/report-structure.md` |
| Writing the email, adding links and the attachment, copying creative to Drive, filing | `references/email-and-delivery.md` |
| Asked for a mock up with results, or turning real platform exports into results pages | `references/sample-mode.md` |
