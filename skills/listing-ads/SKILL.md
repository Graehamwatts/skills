---
name: listing-ads
description: "Paid ads for one listing, from an address to campaigns that are set up. Give it a property address plus whatever the team has already made, and it builds the ad set from that, or it first researches the area (days on market against comparable sales, competing listings, Google Keyword Planner search volume, keywords, local hooks) and proposes ad angles. It then writes the copy inside each platform's limits, runs the housing and Compass compliance checks, sets up Facebook and Instagram, YouTube and Google Search campaigns paused until Graeham says go, and briefs Peter by email for any creative that is missing. Use for: generate ads for this listing, ads for [address], ad ideas for this property, what should we advertise for this listing, keyword research or search volume for a listing, set up the listing ads, launch the ads, YouTube ads for a listing, Google Search ads for a listing, Facebook and Instagram ads for a listing, what do we need from Peter for the ads, brief Peter on the ads. Not for the shoot plan or call sheet (listing-launch-engine), the report to the seller (seller-marketing-report), ChatGPT ads (chatgpt-ads), or auditing the Meta account (meta-ads)."
---

# Listing ads

One listing per run. It turns an address into an ad plan Graeham can approve with a yes, then does the setup work. First built in October 2026 on a one bedroom East Palo Alto condo, and each rule below was learned there. Paths such as `shared-references/identity.json` and `seller-marketing-report/references/...` are relative to the skills toolkit, `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\Skills\skills\`, whichever assistant is running this.

## Where it fits

| Need | Skill |
|---|---|
| Shoot plan, call sheet, the full content slate | listing-launch-engine |
| Meta calls (create, edit, report, pixel) and the confirmation gate | meta-ads (this skill calls it) |
| ChatGPT ads | chatgpt-ads |
| Hooks and concept packages | concept-forge |
| Ad copy craft, psychology audit, final polish | copywriter, marketing-psychology, humanizer |
| Comps and pricing | cma-generator |
| The report the seller reads | seller-marketing-report (this skill hands it the status notes) |

## Who does what

Graeham approves the angles, the copy, the budget and end date for each platform, and the switch on. The assistant running this skill (Claude, Codex or Chevy) owns research, plan, copy, setup and status notes. Paid ads were not backfilled when John left, so this is the owner, and spend changes stay in review. Peter (signs his emails Jason) edits video cuts, thumbnails, carousels and still ads. Ellie renders and exports files and posts organic content. Adrian works the leads and owns the seller reports. Wesley shoots new footage. John is off the team: never email him. Crew addresses are in `listing-launch-engine/references/recipients.md`. Do not guess which one is Peter's, `references/peter-brief.md` says how to confirm it.

## The rules, and why they exist

1. **Real evidence only.** Every number and claim in an ad traces to a source read this session, with its date. A market number comes from the method in `references/research.md`, denominators included. Superlatives expire, so date them. Comparisons say "price", never "cost", and a comparison marked pending stays unreleased until it is verified. Never write about results for an ad that did not run, and never backdate a launch. An earlier assistant invented "illustrative" ad results and the report could not be sent.
2. **Money gate.** Never choose a budget or split one. Ask for the total and the end date for each platform and show the daily equivalent. Create every campaign paused and confirm the platform shows Paused, never Scheduled, because a scheduled start spends by itself. Switch on only when Graeham says go for that campaign, one ad account at a time. Uploading a video to YouTube or posting anything publishes it, so ask first. Spend changes need his review (Team Directory, C15). Billing, advertiser verification, passwords and sign in steps are his to do.
3. **Housing rules.** Meta treats listing ads as the Housing special ad category: no age, gender or ZIP targeting, a radius of at least 15 miles, no lookalike or saved audiences. Google's housing policy bars targeting or excluding by gender, age, parental status, marital status or ZIP. Target the housing need and the place, never the household.
4. **Truth in place.** The real city is in the headline and on screen within the first five seconds. A neighboring city's name may sit next to it and never stands in for the address. No claims about schools, safety, family fit, walkability or travel time unless measured and sourced. No financing terms (rate, payment, credit) on any surface.
5. **Identity and disclosure.** Name, Compass and DRE come from `shared-references/identity.json`, never from memory. REALTOR always carries the registered mark and never sits beside a place name. Show the DRE in the ad text and on the closing card, as the Compass handbook requires and the October brief to Peter did. The older rule in `listing-launch-engine/references/locked-production-rules.md` (no DRE on screen) predates the handbook. When two sources disagree, Graeham's latest instruction in chat wins, then the Compass handbook, then older skill files, and you say which one you followed. AI changed images (staging, added props) carry a statement on or next to the image plus a link or QR code to the original, as California AB 723 has required since January 1, 2026.
6. **Not live yet means no listing ad.** If the MLS entry is not live, stop at the Area brief and a plan for neighborhood teasers only, with no address and no price (the Team Directory's pre launch step, the MLS 24 hour rule). Everything else waits for the live entry. Facts about a listing with no MLS record come from Graeham and are marked unverified until the record exists.
7. **Honest demand.** If Keyword Planner shows no volume for the listing's own terms, say so and move the money to channels that reach people. Do not pad a Search campaign to fill a plan.
8. **Status words.** "Switched on", "scheduled to end", "no spend or clicks at the first check", "prepared", "on hold", "not launched". Say running, active or live only when a platform record shows delivery. No ad dollar amounts in anything the seller sees.
9. **One plain ask to Peter.** He is the editor, on Philippine time, with a long queue. Brief him once, in plain language, only after Graeham has approved the angles, as a Gmail draft, and send only when Graeham says send.

## Workflow

1. **Orient.** Read the listing record (MLS, price history, status). Find the creative folder (Drive or Box) from Graeham or the listing's email thread. Find which Meta ad account, Google Ads account and YouTube channel apply by asking him or reading the platform, and ask if more than one shows. Look at what is already live, in the platforms and in any ad log for this listing (see Where files go), before planning anything. List the capabilities you actually have (a browser on Graeham's signed in sessions, Gmail drafts, the Meta connector or Ads Manager), say which steps they block, and do the rest. If the MLS entry is not live, apply rule 6.
2. **Pick the mode and say it in one line.** A: Graeham supplied material (a creative folder, copy, hooks). Inventory it, check every claim in it against a source, and run only the parts of step 3 the ad set needs (Keyword Planner if Search is in scope, days on market if a market claim is used). Write "not researched" on any plan line you skip, then go to step 4. B: he wants ideas, so do step 3 first. C: he only wants Peter briefed. Get the approved angles and hook lines from him, never invent hooks for the brief, then go to step 6.
3. **Area intelligence** (`references/research.md`). Produces a one page Area brief: where the listing stands against like for like sales and competing listings, what people actually search, five facts that can carry an ad, and three to five angles.
4. **The ad set** (`references/ad-specs.md`). Start with two angles and keep two in reserve. Write copy inside each platform's limits, name every ad with its angle letter, note the destination and the creative each one needs, and run the compliance checklist in that file. Use copywriter or concept-forge for craft, then humanizer.
5. **The plan.** Post it in chat in the block below and stop. Work continues only on a clear yes covering the angles and the budget and end date for each platform.
6. **Close the gaps.** For creative that does not exist yet, brief Peter with `references/peter-brief.md`. When he delivers, check it against the brief before anything is uploaded.
7. **Set up paused.** Meta through the meta-ads skill. Google Search and YouTube through Google Ads in the browser on Graeham's signed in Chrome, with his yes before any video is uploaded. Read each setup back from the platform. Run the landing page check in `references/ad-specs.md` before spend starts. If a screen resists automation twice, stop and give Graeham a click by click sheet instead of burning turns.
8. **Switch on and log.** On his explicit go for that campaign, switch it on, check delivery at the first look and again after 24 hours, and append the ad log. Send Graeham the status note so it can go to the seller report.

The plan block:

```
AD PLAN: <street and number>, <date>
Mode: A, B or C
Where it stands: <one sentence, dated numbers, with source, or "not researched">
Demand: <Keyword Planner in one sentence, or "not researched">
Ads: <letter, platform, the line, destination, audience, start and end>
Budget: <total and end date for each platform, blank until Graeham gives them>
Needs from Peter: <list, or none>
Open questions: <only the ones that change what happens next>
```

## Where files go

Drafts and working files stay in your scratch folder. The ad log is one file per listing. Claude writes `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\listing-ads\<street slug>\ad-log.md` and Codex writes `C:\Users\Graeham Watts\Documents\Skills LLMS\codex\output\listing-ads\<street slug>\ad-log.md`. Any other assistant uses its own output folder and tells Graeham the path. Read every log that exists for the listing before you act, and write only your own. A saved copy of the plan goes in the listing's folder only when Graeham asks, named like its neighbors.

## Done means

- Every printed number traces to a source read this session, and nothing describes results that did not happen.
- The compliance checklist in `references/ad-specs.md` passed, with the AI image statement wherever it applies, and every video was actually looked at or the check is marked open.
- Each campaign is either paused with a read back, or switched on with Graeham's go on record, and the log has exact times.
- Any email to Peter is a draft or was sent on Graeham's yes, and its thread is in the log.
- Your reply is plain prose: what is ready, what is switched on, what waits on whom, and what he has to decide.

## Reference map

| When you are | Read |
|---|---|
| Researching the area and the keywords (step 3) | `references/research.md` |
| Writing ads, checking limits, compliance, landing page, the log (steps 4 and 7) | `references/ad-specs.md` |
| Asking Peter for creative, or checking what he delivered (step 6) | `references/peter-brief.md` |
