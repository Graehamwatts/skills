# Intake: sources, a new listing, numbering

How the information for an issue gets from the team to the listing folder. `<scripts>` and `<listing>` mean the same folders as in SKILL.md.

## Contents

1. The rule: only what was handed over
2. A new listing
3. The sources, one by one
4. When two sources disagree
5. When a source is missing
6. What to ask the operator
7. Issue numbering

## 1. The rule: only what was handed over

Graeham: "We'll input the information to you or tell you where to get it. You'll see the emails come through on Glide, we'll log the calls, the follow ups... you should have the ability to get it from Glide and or other places if we ask you to."

So read a source only when the operator gave it to you or pointed to it in this session. "The sheet is up to date" points to the sheet. It does not point to his inbox. Do not go looking in Gmail for Glide or Supra notices, last week's thread or anything else unless asked, and never create a Gmail filter. The mailbox and the Drive are his.

Every source used is recorded with the build so the record shows where the facts came from. The activity sheet records itself. Each other source gets one `--source "KIND|LABEL|YYYY-MM-DD"` on `run_issue.py`:

| KIND | Use for |
|---|---|
| `activity_sheet_live`, `activity_sheet_file` | Set by `--sheet-kind`, not by `--source` |
| `status_email` | The client care weekly status email |
| `open_house_schedule` | The team's open house schedule sheet |
| `offer_summary` | The offers workbook or the offers tab of another file |
| `glide_email`, `supra_email` | Disclosure platform and key-box notices read from Gmail |
| `pasted_notes`, `forwarded_email` | Anything typed or forwarded into the chat |
| `mls_public_page` | The MLS or MLSListings public page read for status or price history |
| `market_data` | Closed sales pulled for the time on the market section |
| `ad_accounts` | Ad platform status or a written status note |
| `portal_page`, `operator_numbers` | Online views read from a portal page, or given by the operator (`online_views.py` records these itself) |
| `nearby_lookup` | The similar homes lookup (`nearby_update.py` records it itself) |
| `other` | Anything else, named in the label |

The label is plain words ("Open house schedule sheet"). No Drive ids, message ids, addresses of other listings or names in a label.

## 2. A new listing

Do this once, before the first issue.

1. **Pick a slug**: short and human, usually the street name in lower case (`sample-glen`). It must not match another folder under `seller-reports\`.
2. **Create the folder** `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-reports\<slug>\`. It is outside every git repo on purpose.
3. **Write `listing.json`** in the shape of `data-contract.md` section 2. The build stops if any of these is missing: `slug`, `address`, `city`, `state`, `beds`, `baths`, `sqft`, `property_type`, `list_date`, `price_history`, `status`, `mls`, `hero_photo` (null is allowed for the photo).

Where each fact comes from, and what to do when you do not have it:

| Field | Source | Notes |
|---|---|---|
| Address, beds, baths, sq ft, type, MLS number, status | The MLS record or the MLSListings public page, read this session | Ask the operator if you were not pointed to one. Do not fill these from memory |
| `list_date`, `price_history` | The listing's own history | Read the whole history before writing "listed at". A listing can enter at one price and change the next morning. The first entry is `listed`, later ones `price_change`, oldest first |
| `seller_first_names` | The operator | Makes the greeting ("Hi Pat and Sam,"). Leave the list empty rather than guess: the email then has no greeting |
| `hero_photo` | An https address of a hosted photo, set with `hero_photo.py` (`extras.md`, section 5) | A local path is never put on a page. With null the masthead has no photo |
| `property_page` | Graeham's own page for the listing, when there is one | Read only to find the photo |
| `extras` | Settings for the optional sections | `extras.md`, section 6 |
| `sheet` | The Drive id and title of the View Activity sheet | Stays in this file. Never copied into the report |
| `keybox_number` | The team's lockbox inventory sheet | Needed only to match Supra notices. Boxes are reused between listings, so read the row for this listing's dates |
| `tracking` | What is truly recorded for this listing | See below |
| `numbering` | Section 7 | |
| `listing_folder` | The listing's folder under `Documents\Listings` | Read only. The scripts never write there |

`tracking` has three flags, and each one decides whether a number prints or the words "not recorded" print:

- `keybox_showings`: true only when there is an electronic key-box record to read for this listing (Supra notices, or a key-box log exported from Supra). With false, tours reported by agents are still counted, as reported tours. A combination lockbox leaves no record at all: set false and say so in `tracking.lockbox` ("combo lockbox, so there is no electronic showing record"). A showing tab the team keeps by hand, even one named after the key-box company, is then a log of reported tours (`counting-rules.md`, section 3).
- `disclosure_sent`: true only when the notes say when a package link was sent.
- `disclosure_opened`: true only when opens can be checked (the disclosure platform's notices). If they can be checked only from some date on, put that date in `tracking_since`: earlier weeks then keep "not recorded", never a zero.

When unsure, set a flag to false. "Not recorded" is honest. A zero that really means "nobody looked" is not.

Nothing else needs creating by hand. The first `run_issue.py` writes `raw.json`, and applying your first readings file creates `curation.json`.

## 3. The sources, one by one

### The live View Activity sheet (the freshest source)

One Google Sheet per listing, titled "<address> - View Activity", kept by hand by client care. It has a disclosure tab (often called Glide View), a showing tab and an open house tab, and sometimes an inquiry tab and an offers tab. Tabs and columns are found by keyword, so a renamed tab or a moved column is fine.

1. Find it with the Drive connector's `search_files`: `title contains 'View Activity' and title contains '<street number and name>'`. Skip this when `listing.json` already has `sheet.drive_id`.
2. Export it with `download_file_content`, `exportMimeType` set to `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. **Do not use `read_file_content` for the report**: it cuts long cells short, and the long cells are the feedback.
3. The result is base64. When it is large the harness saves it to a file and gives you the path. On 2026-10-12 that file was JSON with the workbook under `content`. Decode it into the session scratchpad:
   ```
   python -c "import json,base64,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'wb').write(base64.b64decode(d['content']))" "<saved tool result>" "<scratchpad>\<slug>-view-activity.xlsx"
   ```
   A good file starts with the two letters `PK`. If the keys differ, look at the saved result before decoding.
4. Run the issue with `--sheet "<that file>" --as-of <today>`. `--as-of` is the day of the export. It places dates typed without a year and sets how far "since the week closed" reaches.

The export holds phone numbers and blunt notes. Keep it in the session scratchpad and nowhere else: not in the skills folder, not in the listing's folder under `Documents\Listings`, and not in the listing's report folder (`reports\seller-reports\<slug>`), which keeps only what the scripts write. `raw.json` already holds everything the report needs from it. `run_issue.py` prints a warning when `--sheet` points inside the report folder. (The two exports saved under the report folders' `work\` on Oct 13, 2026 predate this line.)

### The client care weekly status email and its Excel attachment

Client care (Adrian, graehamwattsclientcare@gmail.com) has written a weekly status report by hand for some listings, often with a copy of the sheet attached. Read these only when asked, or for the numbering check in section 7, through Gmail search (`subject:"Weekly Status Report" "<street name>"`, add `has:attachment` for the sheet copy). The Gmail connector reads Graeham's own inbox, so a status email shows there when he was on it.

- **The attachment is a copy of the sheet, and it can be old.** Compare its date with the live sheet. When it is used as the workbook, pass `--sheet-kind activity_sheet_file` so the record says a saved copy was read. If the Gmail connector cannot download an attachment, ask the operator to save it and give you the path, or use the live sheet.
- **The email's own counts are a cross-check, not a source.** The report's numbers come from the log by the counting rules. Where the email says something different (it counts "showings" as one number, or counts an agent and that agent's buyer twice), keep the report's number and tell the operator in one glance line: `--glance "The status email counts 2 showings. This report counts 1 key-box showing and 1 inquiry, because one row has no showing date."`
- Add `--source "status_email|The team's weekly status email|<its date>"`.

### Glide and Supra notification emails (only when asked)

These carry the exact times the sheet lacks. They arrive in Graeham's Gmail, he forwards them and trashes them, and Gmail empties Trash after 30 days. So they can only be read for about a month back, and only with Trash included.

| Notice | Gmail search | What it gives |
|---|---|---|
| Disclosure package first view | `from:glide-email.com subject:viewed "<street name>"`, `includeTrash` true | Who opened the package and when |
| Key-box showing start and end | `from:suprasystems.com "<key-box number>"`, `includeTrash` true | Who opened the key box, when, and for how long |

Supra notices name a key-box number, not an address. Match them through `listing.json` `keybox_number`, and only for dates when that box was on this listing.

There is no script for this step. Write `<listing>\events.json` by hand in the shape of `data-contract.md` section 5:

- One event per notice: `disclosure_opened`, `keybox_showing_start` or `keybox_showing_end`, with `occurred_at` in Pacific time and the `date` taken after converting.
- `contact_id` is the person's id in `curation.json`. Match by name, and say how in `matched_by`. An event you cannot match stays unmatched: it is then in no count and a note says so. Never guess a match.
- A host opening the key box for an open house is `is_team_side: true`. It is not a showing.
- Add one `fetched` entry saying what was asked, when, and for which dates. That is what puts the source on record.
- Then set the matching `tracking` flag in `listing.json` to true, with `tracking_since` when the notices only reach back part of the way.

**Sorting and filing them, only when asked.** If the operator asks you to keep these notices from being lost:

1. Say what you would do before doing it: which threads, which label, and that taking a thread out of Trash stops Gmail deleting it.
2. Reuse a label if one exists (`list_labels`). Create one only on a yes. One label per listing, named for the street address.
3. `untrash_thread`, then `label_thread`, for the threads of this listing only.
4. Never create a filter or a forwarding rule, in the connector or through the browser. A standing rule on his mailbox is his decision and his to set up.

### Pasted notes and forwarded emails

There is no script for these either. What to do depends on who the note is about:

- **Someone already on the sheet**: add the dated touch or the dated feedback under that person's `extra` in your readings file (`reading-and-tone.md`, section 11). Every extra line needs a date. Ask for one if it is missing.
- **Someone not on the sheet**: ask the operator to have a row added to the sheet, then export again. The sheet is the team's single log, and a person who exists only in a chat message would vanish from next week's count. If they want the report now, leave the person out and say so in a glance line.

Add `--source "pasted_notes|Notes pasted in by the operator|<today>"` or the `forwarded_email` kind.

### The open house schedule sheet

The team keeps one schedule sheet for all listings: address, host, date, time, cancellations, with a history tab. Use it only when pointed to it, for one job: giving a date to an open house session that has none on the activity sheet. A session with no date stops the build until it has one. Put the date in your readings file under `open_houses` with `date_quality` and a short `date_note`. The count and the recap still come from the activity sheet. Record the source as `open_house_schedule`.

### Offers

Offers come from the sheet's offers tab or from the team's offers summary workbook when the operator hands it over. Each offer goes in your readings file under `offers`: `id`, `date`, `contact_id`, `price`, `state`, `terms_summary` in plain words, and `source_row` when it came from the sheet. A row on the offers tab that has not been entered stops the build.

The states are not interchangeable (carried over from the earlier weekly report, where mixing them up was a standing risk):

| State | Meaning |
|---|---|
| `received` | An offer is in and the seller has a decision to make. It is not pending and not a locked deal |
| `countered` | The seller answered with a counter. Still the same offer, not a new one |
| `accepted` | The seller accepted. Escrow is opening |
| `declined`, `withdrawn`, `expired` | Closed without a deal |

"Pending" or "in contract" is a status of the listing (`listing.json` `status`), reached after an acceptance. Never call a listing pending because an offer was received. Offer price, terms and the offer agent's name print in the email only. The link copy and the PDF carry none of them.

### The optional sources

Online views, similar homes nearby, the masthead photo and the online ads status are read only when asked in this session (or when `listing.json` `extras.<source>.every_issue` is true), one lookup each. Their tools, caps and procedures are in `extras.md`; time on the market and the ads status are in `market-and-marketing.md`. Never estimate a figure, and never open a page only to find one.

## 4. When two sources disagree

Use the freshest record of the team's own log, and say what you did.

1. **The live sheet**, exported this session.
2. **The newest emailed attachment** of the sheet, when the live sheet cannot be read.
3. **A saved local copy** (for example an xlsx in the listing folder under `Documents\Listings`), last and always flagged: local copies have been weeks behind the live sheet. Check the file date, pass `--sheet-kind activity_sheet_file`, and tell the operator it may be stale.

Machine notices (Glide, Supra) beat the sheet on the time of an event, because a person typed the sheet. The sheet beats them on what was said. A status email never overrides the log. When the disagreement changes a number the seller will read, put it in a glance line with the reason.

`run_issue.py` reads one workbook per run. It does not merge the live sheet with an attached copy. Pick one by the order above.

## 5. When a source is missing

- **No sheet can be read**: stop and say so. Do not build from last week's data with this week's date on it.
- **The sheet was exported before the week ended**: the build goes ahead and puts a glance line first saying the last days may be missing. Offer to export again.
- **No key-box record, no disclosure open record**: leave the tracking flag false. The report prints "not recorded".
- **An open house with no visitor count**: the report prints "no count kept". Do not read a count into a vague recap.
- **A showing row with no date**: it is counted as an inquiry until the notes or the operator say a tour took place. The glance lines say so for rows in the report week.
- **No hosted photo**: the masthead has no photo. Do not link a local file.
- **No seller first names**: no greeting line.

## 6. What to ask the operator

Ask only what you cannot find, and ask it once, in plain words:

- Which listing, when the request could mean two.
- Whether the sheet is current through Sunday.
- The sellers' first names and the email address the draft should go to, the first time.
- The date of an open house session the sheet gives none for.
- Whether a row with no showing date was a tour.
- Whether to read Glide or Supra notices this week.
- On a listing's first issue: how many reports the seller has had, and whether to check Gmail for them (section 7).

Do not ask them to confirm how you read a note. Read it, count it, and put real doubt in a glance line.

## 7. Issue numbering

Issue numbers continue what the seller has already received, so the stack reads as one series. On Oct 12, 2026 one listing continued a hand-written series at No. 07 and another at No. 10.

- `listing.json` `numbering.first_issue_number` is the number this skill's first issue carries. If the seller already received No. 04 to No. 06 written by hand, set it to 7, set `first_issue_date` to that Monday, and say so in `note`.
- **When the number is settled, no check is needed.** With `numbering.first_issue_number` in `listing.json` and an issue already on file, `snapshot_issue.py next` gives the number and Gmail is not searched.
- **Count what reached the seller, not what was written.** For a listing's first issue under this skill (no `numbering` yet, no issue on file), or whenever the number is in doubt, ask the operator how many reports the seller has had and offer to check. With their go-ahead (or when they point you there), search Gmail for Adrian's status emails for this address (`subject:"Weekly Status Report" "<street name>"`) and look at the ones that went to the seller. A draft, or a report sent only to Graeham, is not in the series. The highest number that reached the seller, plus one, is this issue. If nothing can be found, ask; never start again at 1 on a listing that has been reported on.
- After the first issue, the number is one more than the highest issue on file. A week with no report does not skip a number. A rebuild for the same report date keeps its number.
- Check what comes next at any time:
  ```
  python "<scripts>\snapshot_issue.py" next --folder "<listing>"
  python "<scripts>\snapshot_issue.py" list --folder "<listing>"
  ```
- `--issue <N>` on `run_issue.py` overrides the number. Use it only when Graeham says the series needs correcting.

The report date is always the Monday after the week covered, whatever day the report is built. Built on a Thursday, it still covers the same week and carries the same Monday.

**Why the counts differ from the hand-written series.** Those reports counted cancelled tours, questions and open house hosts; this one does not (`counting-rules.md`, sections 2, 3 and 5). No code writes that explanation. On a listing's first issue under this skill, pass it yourself as one glance line, with both figures: the totals in the last hand-written status email that reached the seller (the one found for the numbering check above) and this report's totals, for example `--glance "The last hand-written report counted 14 showings; this one counts 11, because cancelled tours, questions and open house hosts are not counted."`. It is also the answer if the seller asks. When no hand-written report is at hand, leave the line out rather than guess a figure.

**A hand-written report for the same week.** Before the first run, check whether a hand-written status email for the same Monday to Sunday week already reached the seller (the same Gmail search). If one did, say so in a glance line, and with Graeham's word open the brief with one sentence saying this report covers the same week as that update (`--brief-file`; on Oct 13, 2026 that was done for one listing).
