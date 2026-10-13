---
name: seller-report
description: "Builds the weekly seller report for one of Graeham Watts's active listings: an email a homeowner reads on a phone that shows everyone the team followed up with, what each agent and buyer said (the team's paraphrase, never a harsh quote), a ranked count of what people are saying with price always a row, open houses, the numbers week by week and the running record since launch, plus a link copy with no offer details and an optional PDF. It reports feedback and activity only and never recommends a price. Use this skill ANY time the user mentions: seller report, weekly seller report, weekly listing update, Monday update, Monday seller email, weekly status report for a listing, weekly update for an address, run the weekly for an address, seller marketing report or update, marketing update for the seller, campaign report or ad results report for a listing, 'show the seller what we are doing', showing feedback report, follow-up log, who have we followed up with, disclosure downloads report, open house recap for a seller, days on market against similar sales for a listing, or building the record for a price conversation. Also use it when someone hands over or points to a listing's View Activity sheet, the client care weekly status email, or Glide and Supra notification emails and names an address, and when the user has read a report draft and says what to change. It runs only when a person asks. Not for CMAs or pricing opinions (cma-generator), launch content plans and call sheets (listing-launch-engine), disclosure analysis (disclosure-analyzer) or price reduction scripts (price-reduction-angle-generator)."
---

# Seller Report

> **Absorbed on 2026-10-13:** `weekly-listing-update` was merged into this skill. All capabilities of `weekly-listing-update` (list: the Monday weekly seller status report for an active listing; reading the team's showing, disclosure and open house log; week by week numbers rebuilt from the cumulative log, with a quiet week kept as a row of zeros; agents named as First L.; offers shown near the top with the received, accepted and pending states kept apart; a ranked summary of what buyers said; the wrong-seller check before anything is drafted; no dashes in seller copy; an unsent Gmail draft for Graeham; a hosted copy, now a link copy with no offer details that is published only on his word; portal view counts as an optional input) now live here. Left out on purpose: the status strip verdict, the Decision Required block and the ranked concern cards (this report gives feedback only), publishing before anyone has read it, and the placeholder template with its two scripts (the pipeline in `scripts/` replaces them). The folder `skills/weekly-listing-update/` was deleted in the same commit. If you find any reference to `skills/weekly-listing-update/` anywhere in this repo, that reference is a bug: it should point here.

> **Absorbed on 2026-10-13:** `seller-marketing-report` was merged into this skill. All capabilities of `seller-marketing-report` (list: days on market against comparable closed sales, with the method and every trap; search demand from Google Keyword Planner; ad and creative status wording; platform exports when ads have really delivered; the 10 page seller marketing update PDF and its builder; the 13 page full campaign report; the internal SAMPLE mode with its marker rules; the real-file check before a PDF goes near a seller; the email with the PDF attached; copying creative to Google Drive; filing and the Superseded folder) now live here, in `references/market-and-marketing.md` and `references/marketing-update/`. The folder `skills/seller-marketing-report/` was deleted in the same commit. If you find any reference to `skills/seller-marketing-report/` anywhere in this repo, that reference is a bug: it should point here.

## What this is and who reads it

A weekly letter to the seller of a listing. Graeham's words: "put together a fully detailed seller report to show the seller that we are doing our job and following up with people and showing them what that feedback is... So it's a lot easier for me when I need to come back and say, Hey, we need a price reduction, look at all the seller reports, this is what everyone's saying... they also can't ever complain that I'm not doing my job following up with everyone. I can clearly show them a log of everything and everyone is being followed up with."

The reader is a homeowner on a phone. Feedback and follow-up lead every issue. A market check and a marketing status are short optional sections. Each issue is numbered, is dated a Monday, and covers the Monday to Sunday week that just ended.

Each issue produces three things from one dataset:

| File | What it is |
|---|---|
| `email.html` | The full report, for the body of an email. Under 95,000 bytes, because Gmail clips near 102 KB |
| `link.html` | The copy that can be forwarded. No offer price, no offer terms, no name of an agent who wrote an offer or may be weighing one. Marked noindex. Holds the complete person by person record |
| `report.pdf` | Optional, printed from the print layout of the link copy |

## What the person asking does: three steps

1. They hand over the information or say where it is ("run the weekly for the Sample Glen listing, the sheet is up to date").
2. They get the finished report as an **unsent Gmail draft**.
3. They read it like any draft and say in plain words what to change ("Jordan never said it was overpriced", "take out the part about the neighbour"). You apply it and rebuild. The correction is saved and holds in every later week.

That is the whole experience. There is no review table, no confirm step and no sign-off, and nobody is ever asked to look over how the notes were read. Graeham saw an earlier version with such a step and said: "Don't know what it is or what it does, but I don't know why we need it. This is not what I had in mind." The words tag, tagging, curation, ledger, provenance and validation are workshop words. Keep them out of everything the operator or a seller reads, your chat replies included.

## The rules, and why each exists

1. **Draft, never send. One build.** The email goes into Gmail as a draft and Graeham sends it himself, because it speaks to his client in his name. Every build is the clean report: no notice on top, no panel at the end, nothing addressed to anyone but the seller, so a draft can never go out with working material on it.
2. **Feedback only.** Graeham: "The system shouldn't do anything in regards to that [raising price]. The system should only provide feedback." The report never recommends a price change, never suggests a number, and never says what silence on price means, in either direction. He makes the pricing case himself, in person, with the stack of reports as his evidence. A report that argues for him reads as pressure and weakens that evidence.
3. **Tone.** Graeham: "Friendly, but concise and direct, but should be nuanced to also not offend people that sometimes might be a little sensitive about certain things. You know, whereas a buyer might say, that was absolutely terrible and horrific. We don't want to be quoting those kinds of terrible things about someone's home. We can just say they provided negative feedback and specifically said that the pricing was too high. That's all that needs to be said in that situation." Harsh wording is never quoted. The substance stays. Every comment is the team's paraphrase, labeled "as reported to our team".
4. **Privacy.** Nothing a seller could see carries a phone number, an email address, a lockbox or door code, a buyer's health, disability, family or finances, a first-person aside from the caller's notes, or the address of another listing (say "chose another property"). Agents appear as First L. plus brokerage when known. Sellers forward these reports, and the people in them never agreed to be in them.
5. **Real data only.** No invented numbers, names, quotes or dates. Where a fact is not recorded the report says so ("not recorded", "no count kept"). A report built by another AI once used invented ad results and could not be sent. One made-up number makes every true number in the stack worthless as evidence.
6. **Only when asked, and only what was asked for.** The skill never runs on a schedule. Read only the sources the operator handed over or pointed to in this session. Read, sort or file Glide and Supra emails only when asked. Never create a Gmail filter. It is his inbox and his client relationship.
7. **One way to count.** Every number is computed in code from the log by `references/counting-rules.md`, and the checks recount it. A hand-built report once miscounted empty open houses, showed one buyer as both passed and active, and double counted agents with their own buyers. Never type or adjust a number.
8. **Brand from identity.json.** Name, REALTOR line with the registered mark, the brokerage line, DRE, phone, email and the Compass disclaimer are read from `skills/shared-references/identity.json` at run time. Never type any of them from memory: a wrong DRE has leaked into client work before, and the repo tripwire blocks the push when a blocked value appears.
9. **No client data in this repo.** The skills folder publishes to GitHub. Real names, notes, feedback and reports live only in `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-reports\<slug>\`. The scripts refuse to write private files inside a git repo. Examples and tests here use invented people.
10. **What you are unsure about goes in the chat reply, never in the report.** At most five short plain lines under "Worth a glance before you send". The checks run silently, and the operator hears about one only when it fails and you cannot fix it yourself.

## Workflow

Scripts are in `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\Skills\skills\seller-report\scripts\` (written `<scripts>` below). A listing's private folder is `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-reports\<slug>\` (written `<listing>`). Quote every path: they contain spaces. Python 3 with openpyxl. Microsoft Edge prints the PDF and the phone pictures.

1. **Find the listing.** One listing per run, one folder, one draft. If `<listing>\listing.json` does not exist, set the listing up first (`references/intake.md`, "A new listing"). If the listing is under contract or pending, ask whether a report is still wanted before building one.
2. **Get what was handed over.** Usually the live "<address> - View Activity" Google Sheet, exported to xlsx through the Drive connector and saved in the session scratchpad. `references/intake.md` covers every source, which one wins when two disagree, and what to do when one is missing.
3. **Run the issue.**
   ```
   python "<scripts>\run_issue.py" --folder "<listing>" --sheet "<export.xlsx>" --as-of <YYYY-MM-DD the sheet was exported>
   ```
   Add `--source "KIND|LABEL|YYYY-MM-DD"` once for every other source used this session. For an issue built late, add `--report-date <that Monday>` and `--through <the Sunday before it>`. `python "<scripts>\run_issue.py" --help` lists every switch.
4. **Follow the NEXT line.** Every stop prints one line that starts `NEXT:`.

   | Exit | Meaning | What you do |
   |---|---|---|
   | 0 | READY | Go to step 6 |
   | 2 | An input is missing | Supply it: `listing.json`, the sheet, a readable path |
   | 3 | That issue was already sent | Ask whether a corrected copy should replace it. Only then add `--replace-sent` |
   | 10 | New notes to read | Step 5 |
   | 11 | The numbers could not be built | Fix what is named: a row to place, a date to give. Never adjust a count |
   | 20 | A page did not render | A fault in the data or the code, not the operator's. Fix what is named |
   | 30 | A check failed | Nothing was kept and nothing goes in a draft. Fix the cause, rebuild |
5. **Read the new notes** (exit 10). Open `<listing>\work\todo.json`. It lists only what is new since last week. For each note write the seller-safe wording and what it says, following `references/tagging-and-tone.md`, into a readings file in `<listing>\work\`, then:
   ```
   python "<scripts>\curation_tools.py" apply --folder "<listing>" --readings "<listing>\work\readings.json"
   python "<scripts>\run_issue.py" --folder "<listing>"
   ```
   Put the open house recaps in plain words in the same pass. This reading is silent: do not show it to anyone or ask anyone to confirm it.
6. **Look at it yourself.** Read the phone pictures in `<listing>\issues\NN\previews\` (the first three tiles and anything that changed). If a sentence is wrong or reads badly, fix it now with step 8 and rebuild.
7. **Hand it over.** Put `issues\NN\email.html` in the body of an unsent Gmail draft (`references/delivery.md` has the recipe and what to verify), record the draft, and reply in chat:
   ```
   python "<scripts>\snapshot_issue.py" record --folder "<listing>" --issue <N> --gmail-draft-id <id>
   ```
   The reply is short: which report, that it is in drafts unsent, then "Worth a glance before you send" with the lines from `<listing>\notes_for_operator.json` (`worth_a_glance`), most important first, five at most, in plain words. Leave the heading out when there is nothing. Add your own with `--glance "..."` on `run_issue.py`. `also_noted` is for you. Close by inviting changes in their own words. No list of checks, no file inventory.
8. **Apply what they say.** Map the plain words to one correction and rebuild with the same command:
   ```
   python "<scripts>\curation_tools.py" correct --folder "<listing>" --find "<words>"
   python "<scripts>\curation_tools.py" correct --folder "<listing>" --who "<name as the report prints it>" --set price_reaction=not_raised --why "<their words>"
   python "<scripts>\curation_tools.py" correct --folder "<listing>" --who "<name>" --reword "<old sentence>" --to "<new sentence>"
   python "<scripts>\curation_tools.py" correct --folder "<listing>" --who "<name>" --remove "<words in the sentence to take out>"
   python "<scripts>\run_issue.py" --folder "<listing>"
   ```
   After `--set`, the command prints every sentence the report still prints about that person: bring the wording into line with `--reword`. Then replace the body of the same draft and say in one or two plain sentences what changed.
9. **When they say it went out,** record it. This locks the issue folder as the record of what the seller received:
   ```
   python "<scripts>\snapshot_issue.py" record --folder "<listing>" --issue <N> --sent-on <YYYY-MM-DD>
   ```
   Publishing the link copy, attaching or filing the PDF, and the first-send test in real mail clients are in `references/delivery.md`. Publish only on Graeham's word.

Use `--waive`, `--allow-name`, `--allow-term`, `--brief-file`, `--issue` and `--replace-sent` only when Graeham says so. Do not pass `--no-pdf` on a rebuild: the older PDF would stay in the issue folder.

## Optional sections and the marketing update PDF

- **Market check and marketing status** print only when `<listing>\market.json` or `<listing>\marketing.json` exists. Build or refresh them only when asked, from sources read in this session. A channel is called running only if it was checked for this issue. See `references/market-and-marketing.md`.
- **The 10 page seller marketing update PDF** (days on market against comparable sales, creative, ad status, search plan) is still available when Graeham asks for it by name. It is a separate deliverable with its own builder: `references/marketing-update/README.md`.

## Known limits (say so, do not paper over)

- Nothing has been opened in a real mail client yet. The first real send follows the test in `references/delivery.md`.
- No script reads Glide or Supra emails, pasted notes or forwarded emails. Those are entered by hand (`references/intake.md`).
- One workbook per run. The live sheet and an attached copy are not merged.
- A photo or link that is not https is left off the page. Without a hosted photo the masthead has none, and without a published link copy the email offers to send the record on request.
- The seller's email address is not stored anywhere by this skill. Ask for it, or leave the draft without a recipient.

## Done means

- `run_issue.py` ended with READY, so every number was recounted and every page passed privacy, tone, feedback only, brand, hygiene, email safety, wrong file and phone layout.
- You read the phone pictures, and the address, greeting and recipient all belong to this one listing.
- The email is an unsent Gmail draft whose body matches `issues\NN\email.html`, and the draft id is recorded.
- The chat reply is short and plain, carries at most five glance lines, and uses no workshop words.
- Nothing was sent, published, labeled or filtered without being asked. Nothing private was written inside a git repo or inside `Documents\Listings`.

## Reference map

| When you are | Read |
|---|---|
| Setting up a listing, finding and reading a source, deciding which source wins | `references/intake.md` |
| Reading new notes: seller-safe wording, what a note counts as, tone examples, applying a correction | `references/tagging-and-tone.md` |
| Asked what a section is for, how the page is built, why the email is shorter than the link copy | `references/report-structure.md` |
| Making the Gmail draft, publishing the link copy, the PDF, filing, the first-send test | `references/delivery.md` |
| Explaining to Adrian what to hand over and how to log so it reads cleanly | `references/operator-guide.md` |
| Building the market check or marketing status, or asked for the marketing update PDF | `references/market-and-marketing.md`, then `references/marketing-update/README.md` |
| Unsure how a number is counted | `references/counting-rules.md` |
| Writing or reading any file in a listing folder | `references/data-contract.md` |
