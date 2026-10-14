---
name: seller-report
description: "Builds Graeham Watts's weekly seller report for one listing: a phone email to the seller (numbers, what people said, everyone followed up with), as an unsent Gmail draft, plus optional extras and the 10 page marketing update PDF. Feedback only, never a price recommendation. Use it ANY time someone mentions a seller report, weekly seller report, weekly listing update, Monday update, Monday seller email, weekly status report for a listing, seller marketing report or update, campaign or ad results report for a listing, 'show the seller what we are doing', showing feedback report, follow-up log, disclosure downloads report, open house recap for a seller, similar homes or comps tracking for a seller's report, or building the record for a price conversation, or hands over a View Activity sheet or report corrections. Not for CMAs or pricing opinions (cma-generator), launch content plans (listing-launch-engine), disclosure analysis (disclosure-analyzer) or price reduction scripts (price-reduction-angle-generator)."
---

# Seller Report

> **Absorbed on 2026-10-13:** `weekly-listing-update` was merged into this skill. All capabilities of `weekly-listing-update` (list: the Monday weekly status report for an active listing; the cumulative activity log rebuilt week by week, with a quiet week kept as a row of zeros; agents as First L.; "Invited by" buyers counted once, under their agent; any offer near the top with received, countered, accepted and pending kept apart; a ranked summary of what buyers said; the wrong-seller check before anything is drafted; no dashes and plain human prose; the unsent Gmail draft to the seller; the hosted copy, now a link copy with no offer details that is published only on Graeham's word; portal view counts, now one page and only when asked; the brand tripwire) now live here. Left out on purpose: the status strip verdict, the Decision Required block, the ranked concern cards and the calendar button (this report gives feedback only), the web-search market context, scraping four portals every week, publishing before anyone read it, and the placeholder template with its two scripts (the pipeline in `scripts/` replaces them). The Monday reminder email is a scheduled task, not part of either skill. The folder `skills/weekly-listing-update/` was deleted in the same commit. If you find any reference to `skills/weekly-listing-update/` anywhere in this repo, that reference is a bug: it should point here.

> **Absorbed on 2026-10-13:** `seller-marketing-report` was merged into this skill. All capabilities of `seller-marketing-report` (list: days on market against comparable closed sales, with the method and every trap; search demand from Google Keyword Planner; ad and creative status wording; platform exports when ads have really delivered; the 10 page seller marketing update PDF and its builder; the 13 page full campaign report; the internal SAMPLE mode with its marker rules; the real-file check before a PDF goes near a seller; the email with the PDF attached; copying creative to Google Drive; filing and the Superseded folder) now live here, in `references/market-and-marketing.md` and `references/marketing-update/`. The folder `skills/seller-marketing-report/` was deleted in the same commit. If you find any reference to `skills/seller-marketing-report/` anywhere in this repo, that reference is a bug: it should point here.

## What this is and who reads it

A weekly letter to the seller of one listing, in Graeham's name. His words: "put together a fully detailed seller report to show the seller that we are doing our job and following up with people and showing them what that feedback is... So it's a lot easier for me when I need to come back and say, Hey, we need a price reduction, look at all the seller reports, this is what everyone's saying."

The reader is a homeowner on a phone, and the draft does go to them. Each issue is numbered, dated a Monday, and covers the Monday to Sunday week that just ended. Top to bottom: a short brief, one numbers table (this week, last week, since we listed), the weekly charts, "What people are saying" with price as plain counts; then "The details", grouped by what people did (offers and likely offers, agents who showed the home, the disclosure package list, open houses, other inquiries), this week's people in full and earlier people one line each; then the optional sections, next week, and the running record since listing. The look is his CMA system: black #1A1A1A, gold #C5A55A, cream #F5EFDC, Montserrat and Inter. `references/report-structure.md` says what each part is for.

One build writes, into `issues\NN\`: `email.html` (the report), `email_gmail.html` (the same words, made safe for the Gmail connector: this is the one that goes into the draft), `link.html` (the forwardable copy with no offer details), `print.html` and `report.pdf`, and phone pictures in `previews\`.

## What the operator does: three steps

1. Hand over the information or say where it is ("run the weekly for Sample Glen, the sheet is up to date").
2. Get the finished report as an **unsent Gmail draft**, To the seller, CC Adrian.
3. Read it like any draft and say in plain words what to change ("Jordan never said it was overpriced", "take out the part about the neighbour"). Claude applies it, rebuilds and replaces the draft body. The correction is saved and holds in every later week.

That is the whole experience. No review table, no confirm step, no sign-off, and nobody is asked to look over how the notes were read. Graeham saw a version with a review step and said: "Don't know what it is or what it does, but I don't know why we need it. This is not what I had in mind." Keep workshop words (tag, tagging, curation, ledger, provenance, validation) out of the report, the operator guide and every chat reply.

## The rules, and why each exists

1. **Draft, never send. One clean build.** It speaks to his client in his name, so Graeham sends it himself. Every build is the finished report: no notice on top, no panel at the end, nothing addressed to anyone but the seller, so no working material can ever go out.
2. **Feedback only.** His words: "The system should only provide feedback." Never recommend a price change, never suggest a number, never say what silence on price means. He makes the pricing case in person with the stack of reports as evidence; a report that argues for him reads as pressure and weakens that evidence.
3. **Tone.** His words: "Friendly, but concise and direct, but should be nuanced to also not offend people... We don't want to be quoting those kinds of terrible things about someone's home. We can just say they provided negative feedback and specifically said that the pricing was too high." The substance stays, the sting goes, every comment is the team's paraphrase "as reported to our team", and nothing is in quote marks.
4. **Privacy.** No phone numbers, emails, lockbox or door codes, buyer health, family or finances, first-person asides from the notes, or the address of any other listing outside the similar homes section. Agents print as "First L." with brokerage. Sellers forward these, and the people in them never agreed to be in them.
5. **Real data only.** No invented numbers, names, quotes or dates; "not recorded" where a fact is missing. Another AI once put invented ad results in a seller report and it could not be sent. One made-up number makes the whole stack worthless as evidence.
6. **Only when asked, only what was asked for.** Nothing runs on a schedule. Read only sources the operator handed over or pointed to in this session. The extras (online views, similar homes, ads, photo) are occasional: "we might not do it all week, every week, every time until we have our PropertyIQ system up and running."
7. **One way to count.** Every number is computed in code by `references/counting-rules.md` and recounted by the checks. Never type or adjust a number. A hand-built report once miscounted empty open houses and double counted agents with their own buyers.
8. **Brand from identity.json.** Name, REALTOR with the registered mark, brokerage line, DRE, phone, email and the Compass disclaimer come from `skills/shared-references/identity.json` at run time. Never write a blocklisted value from that file anywhere: a wrong DRE has leaked into client work before.
9. **No client data in the skills repo.** It syncs to GitHub. Real data lives only in `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-reports\<slug>\`; the sheet export goes in the session scratchpad. Nothing is written inside `Documents\Listings` unless Graeham asks for a final copy filed there. Tests use invented people.
10. **Doubt goes in the chat reply, never in the report.** At most five plain lines under "Worth a glance before you send". The checks run silently; mention one only when it fails and you cannot fix it.

## Workflow

`<scripts>` is `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\Skills\skills\seller-report\scripts`, `<listing>` is the listing's folder under `reports\seller-reports\`, `<scratch>` is the session scratchpad. Quote every path. Needs Python 3 with openpyxl, and Microsoft Edge for the PDF, the phone pictures and the layout check.

1. **Pick the listing.** One listing, one folder, one draft per run. With no `<listing>\listing.json`, set the listing up first (`references/intake.md`, section 2). Under contract or pending: ask whether a report is still wanted.
2. **Get the live sheet** through the Drive connector: `search_files` for `title contains 'View Activity' and title contains '<street>'` (skip it when `listing.json` has `sheet.drive_id`), then `download_file_content` with `exportMimeType` `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, and decode the saved result into `<scratch>` (the one-line decoder is in `references/intake.md`). Never `read_file_content`: it cuts the long feedback cells short.
3. **Numbering and the cross-check.** `python "<scripts>\snapshot_issue.py" next --folder "<listing>"` gives the number. On a listing's first issue, or when the number is in doubt, ask how many reports the seller has had and, with the operator's go-ahead, search Gmail for Adrian's weekly status emails for this address: count what actually reached the seller (sent to them, not drafts), and the series continues from that. When pointed to this week's status email, its counts are a cross-check, never a source (`references/intake.md`, sections 3 and 7).
4. **Run the issue.**
   ```
   python "<scripts>\run_issue.py" --folder "<listing>" --sheet "<scratch>\<slug>-view-activity.xlsx" --as-of <export day> --source "status_email|The team's weekly status email|<its date>" --glance "<a plain line>"
   ```
   `--source` once per extra source used, `--glance` for your own lines. Built late: `--report-date <that Monday>`. `--help` lists the rest. Each stop prints one line starting `NEXT:` with the exact command to run again; use it, because it keeps your switches. Exit codes: 0 READY; 2 an input is missing; 3 that issue was already sent (ask before `--replace-sent`); 10 notes to read (step 5); 11 the numbers could not be built (place the row or give the date it names, never adjust a count); 20 a page did not render (a data or code fault, fix what is named); 30 a check failed (nothing was kept; fix the wording with step 10 and rebuild).
5. **Read the new notes** (exit 10). `<listing>\work\todo.json` lists only what is new. Write the seller-safe wording and what each note says into a readings file in `<listing>\work\` by `references/reading-and-tone.md`, put the open house recaps in plain words in the same pass, then:
   ```
   python "<scripts>\curation_tools.py" apply --folder "<listing>" --readings "<listing>\work\readings.json"
   ```
   and run the NEXT line again. This reading is silent: never show it or ask anyone to confirm it.
6. **Extras, only when asked this session** (or when `listing.json` `extras.<source>.every_issue` is true), before the final run: online views (`online_views.py`), similar homes nearby (`nearby_update.py`, with `--site mls` and `nearby_from_mls.py` when Graeham signs in to MLSListings), the photo (`hero_photo.py`), the ads status (`marketing.json`), time on the market (`market.json`). One lookup each, a block is a stop. Commands and rules: `references/extras.md` and `references/market-and-marketing.md`. Then run the NEXT line again.
7. **Look at it yourself** when it says READY. Read the phone pictures in `<listing>\issues\NN\previews\` (`email_phone_01.png` onward: the first three tiles and anything that changed). Check the address, the greeting and that every name belongs to this listing. Fix a sentence that reads badly now (step 10).
8. **Make the draft** from `issues\NN\email_gmail.html`, never `email.html`. The Gmail connector removes every image, turns call links into dead links, strips background styles, the head, style blocks and class and data attributes, and turns web links and plain-text domains into redirects; the Gmail-safe copy is drawn for exactly that. `references/delivery.md` has the full recipe; in short: `create_draft` with `to` the seller, `cc` graehamwattsclientcare@gmail.com, the `subject` exactly as run_issue printed it (`Weekly Seller Report No. NN · <Month D, YYYY> - <address>`), and `htmlBody` the file's text copied exactly. Then `get_draft` with `messageFormat` RAW, and on the file the harness saves:
   ```
   python "<scripts>\draft_check.py" --issue "<listing>\issues\NN" --draft "<saved get_draft result>"
   python "<scripts>\snapshot_issue.py" record --folder "<listing>" --issue <N> --gmail-draft-id <id>
   ```
   Ask for the seller's address if you do not have it; never store it in a file.
9. **Reply in chat**, short: which report, that it is in drafts unsent, To and CC, then "Worth a glance before you send" with the lines from `<listing>\notes_for_operator.json` `worth_a_glance` (five at most, most important first; leave the heading out when empty), then an invitation to say what to change. No list of checks, no file inventory.
10. **Apply what they say.** Map the plain words to one correction (`references/reading-and-tone.md`, section 12):
    ```
    python "<scripts>\curation_tools.py" correct --folder "<listing>" --find "<words>"
    python "<scripts>\curation_tools.py" correct --folder "<listing>" --who "<name as printed>" --set price_reaction=not_raised --why "<their words>"
    python "<scripts>\curation_tools.py" correct --folder "<listing>" --who "<name>" --reword "<old sentence>" --to "<new sentence>"
    ```
    After `--set`, bring every sentence it prints about that person into line. Rebuild with the run line from step 4 minus `--sheet` and `--as-of` (or the NEXT line), replace the same draft's body with `update_draft` (`draftId`, `htmlBody` only), run `draft_check.py` again, and say in one or two plain sentences what changed. If `update_draft` is refused, tell Graeham what to change in the draft himself, and never work around the refusal.
11. **When they say it went out:** `python "<scripts>\snapshot_issue.py" record --folder "<listing>" --issue <N> --sent-on <YYYY-MM-DD>`. The issue folder is then the record of what the seller received, and a rebuild of it needs `--replace-sent` on Graeham's word.

Use `--waive`, `--allow-name`, `--allow-term`, `--brief-file`, `--issue` and `--replace-sent` only when Graeham says so. Do not pass `--no-pdf` on a rebuild: the older PDF would stay. The link copy is published, and the PDF attached or filed, only on his word (`references/delivery.md`).

## The marketing update PDF

The 10 page seller marketing update (days on market against comparable sales, creative, ad status, search plan) and its internal SAMPLE twin are separate deliverables, built only when Graeham asks for one by name: `references/marketing-update/README.md`.

## Known limits (say so, do not paper over)

- The Gmail connector strips images, call links and background colors, so the draft has no photo and the phone is plain text. The photo shows in the link copy and the PDF.
- No script reads Glide or Supra emails, pasted notes or forwarded emails: they are entered by hand (`references/intake.md`).
- One workbook per run. The live sheet and an attached copy are not merged.
- What a date in the sheet's Email, Call and Text columns means is an open question to Adrian (`references/counting-rules.md`, section 5). Keep the current reading and say in a glance line when it moves a count.
- The hand-written reports counted cancelled tours, questions and open house hosts; this one does not, so its totals run lower. Be ready to say so when asked.
- The MLS grid script has been tested on synthetic pages only. A heading it does not know may need an alias after the first live run.

## Done means

- `run_issue.py` ended READY: every number recounted, every page (email, Gmail-safe copy, link copy, print) passed privacy, tone, feedback only, brand, hygiene, email safety, wrong file and phone layout.
- You read the phone pictures, and the address, greeting and names belong to this one listing.
- There is one unsent draft, To the seller and CC Adrian (or Graeham was told to add the CC), with the printed subject, built from `email_gmail.html`, and `draft_check.py` passed on its RAW read-back. The draft id is recorded.
- The chat reply is short and plain, with at most five glance lines and no workshop words.
- Nothing was sent, published, labeled or filtered without being asked, and nothing private was written in a git repo.

## Reference map

| When you are | Read |
|---|---|
| Setting up a listing, getting a source, deciding which source wins, numbering | `references/intake.md` |
| Reading new notes, seller-safe wording, what a note counts as, applying a correction | `references/reading-and-tone.md` |
| Asked what a section is for, why the email is shorter than the link copy | `references/report-structure.md` |
| Making, checking and replacing the Gmail draft; the link copy, the PDF, filing | `references/delivery.md` |
| Helping Adrian: what to hand over, how to log a follow-up so it reads cleanly | `references/operator-guide.md` |
| Online views, similar homes nearby, the photo | `references/extras.md` |
| Time on the market, ads and marketing status, search demand, platform exports | `references/market-and-marketing.md` |
| Asked for the 10 page marketing update PDF or the SAMPLE | `references/marketing-update/README.md`, `references/marketing-update/sample-mode.md` |
| Unsure how a number is counted | `references/counting-rules.md` |
| Writing or reading any file in a listing folder | `references/data-contract.md` (changes over time: `references/contract-changes.md`) |
