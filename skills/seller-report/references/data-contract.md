# Data contract

One shape for every listing. Every script in this skill reads and writes these files and nothing else. The
code side of the contract is `scripts/sr_contract.py` (enumerations, helpers, `validate_ledger`,
`validate_curation`, `recount`, `finish_ledger`). How each number is counted is in `counting-rules.md`.

Schema version: **1** (`sr_contract.SCHEMA_VERSION`).

**One build mode.** Every build is the report, clean and ready to send. There is no draft and final split, no
review step, no confirm step, and nothing in any file waits on a person confirming anything. The operator
hands over the information, receives the finished report as an unsent Gmail draft, reads it, and says in
plain words what to change. That correction is saved in `curation.json` and holds in every later week.

## 1. Where the data lives

Private working data sits outside every git repo:

```
C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-reports\<slug>\
  listing.json      facts about the home, the numbering, where the sheet lives
  raw.json          PRIVATE parser output: every row and dated note exactly as typed
  curation.json     who is who, the seller-safe paraphrases, what each note says, the operator's corrections
  events.json       optional machine events pulled from emails, only when the operator asks
  market.json       optional: the days-on-market comparison for the short market section
  marketing.json    optional: marketing status for the short marketing section
  ledger.json       the seller-safe dataset the renderer reads
  notes_for_operator.json   at most five plain lines for the chat reply that hands over the draft
  work\             Claude's own working files: todo.json (the work list), build\ (the pages being checked),
                    gate.json (the last check report)
  issues\NN\        issue NN as it would be sent: ledger.json, notes_for_operator.json, email.html, link.html,
                    print.html, report.pdf, manifest.json, previews\
```

`<slug>` is short and human (the street name, for example `sample-glen`). `sr_contract.slugify(address)` gives a default.
`NN` is the issue number, zero padded to two digits.

Nothing with real names, notes or feedback is ever written under `Skills\skills\seller-report`. Tests and
examples there use the synthetic fixtures in `tests/fixtures`.

The pipeline, and which file each step owns:

| Step | Script | Reads | Writes |
|---|---|---|---|
| Intake (parse what the operator handed over) | `intake_sheet.py` | the xlsx export | `raw.json` |
| Claude reads the new notes | `curation_tools.py todo`, then `apply` | `raw.json`, `curation.json` | `work\todo.json`, `curation.json` |
| Ledger build | `build_ledger.py` | `listing.json`, `raw.json`, `curation.json`, `events.json`, `market.json`, `marketing.json` | `ledger.json`, `notes_for_operator.json` |
| Render | `render_report.py` | `ledger.json`, `identity.json` | `work\build\` |
| Checks | `check_report.py` | the built pages, `ledger.json`, `listing.json`, `raw.json` | `work\gate.json` |
| Keep the issue | `snapshot_issue.py freeze` | `work\build\` | `issues\NN\` |
| The operator's correction | `curation_tools.py correct` | `curation.json` | `curation.json` |

`run_issue.py` runs every step but the reading and the correction, in order, and stops with a line that starts
`NEXT:` wherever Claude or the operator has to act.

Only the renderer's input, `ledger.json`, has to be seller-safe. `raw.json`, `curation.json`, `events.json` and
`work\todo.json` hold phone numbers, full names and blunt notes and never leave the folder.

## 2. listing.json

```json
{
  "schema_version": 1,
  "slug": "sample-glen",
  "address": "218 Sample Glen Ct", "city": "Fixture City", "state": "CA", "zip": "94000",
  "beds": 3, "baths": 2.0, "sqft": 1480, "property_type": "Single Family",
  "list_date": "2026-03-12",
  "list_price": 1195000,
  "price_history": [{"date": "2026-03-12", "price": 1195000, "event": "listed"}],
  "status": "Active", "status_checked": "2026-04-13",
  "mls": "ML00000218",
  "hero_photo": "https://... or a local path, or null",
  "property_page": null,
  "seller_first_names": ["Pat", "Sam"],
  "numbering": {"first_issue_number": 1, "first_issue_date": "2026-03-16", "note": null},
  "sheet": {"drive_id": "...", "title": "<address> - View Activity"},
  "keybox_number": null,
  "listing_folder": null,
  "tracking": {"keybox_showings": true, "disclosure_sent": true, "disclosure_opened": true},
  "tracking_since": {"disclosure_opened": "2026-03-23"},
  "operator_notes": []
}
```

- `price_history` is oldest first and starts with the `listed` entry. Later entries are `price_change`.
- `list_price` is the price in effect on the report date.
- `numbering` lets issue numbers continue what the seller already received. The number for a run is
  `sr_contract.next_issue_number(first_issue_number, issued, report_date)`, where `issued` comes from the
  manifests of the issues on file. A rebuild for the same report date keeps its number.
- `tracking` says whether each kind of fact is recorded for this listing at all (it becomes
  `ledger.report.tracking`). `tracking_since` gives, per flag, the first day that fact could be checked: weeks
  before it keep a null, never a zero.
- `operator_notes` are plain sentences Claude may show the operator. They feed `notes_for_operator.json` and
  are never printed in a report.
- `sheet`, `keybox_number`, `listing_folder`, `numbering`, `tracking`, `tracking_since`, `operator_notes` and
  `status_checked` stay in this file. They are never copied into `ledger.listing`. `listing_folder` is read
  only: the skill never writes inside `Documents\Listings`.
- `seller_first_names` passes through to the ledger and makes the greeting ("Hi Pat and Sam,"). Without it the
  email has no greeting unless `--seller-greeting` is given.
- Optional facts a listing may carry (`year_built`, `hoa_monthly`, `community`, `hero_photo_note`,
  `status_source`, `facts_checked`) pass through to `ledger.listing` unchanged.

## 3. raw.json (PRIVATE)

Everything the parser read, with nothing interpreted beyond dates.

```json
{
  "schema_version": 1,
  "WARNING": "PRIVATE. Full names, phone numbers, emails and notes as typed. Never commit or share.",
  "slug": "sample-glen",
  "parsed_at": "2026-04-13T09:12:00-07:00",
  "sources": [{"source_id": "s1", "kind": "activity_sheet_live", "title": "...", "drive_id": "...",
               "file_name": "export.xlsx", "modified_utc": "...", "exported_at": "...", "sha256": "..."}],
  "tabs": [{
    "source_id": "s1", "title": "Showing Activity", "kind": "showing", "header_row": 1,
    "headers": {"A": "Agent #", "C": "Agent name"},
    "columns_found": {"name": "C", "feedback": "G", "notes": ["K", "L", "M", "N"], "last_call": "I"},
    "hidden_columns": [], "merged": ["K1:N1"],
    "rows": [{
      "key": "showing:1a2b3c4d5e",
      "row": 2,
      "cells": {"C": "...", "G": "..."},
      "name_raw": "...", "buyer_raw": null, "invited_by_raw": null, "agent_no": null, "buyer_no": null,
      "phones": ["..."], "emails": ["..."],
      "when_raw": "Sept 17, 5-6PM",
      "when": [{"date": "2026-09-17", "time_text": "5 to 6 PM", "date_quality": "exact"}],
      "last_touch": {"email": null, "call": "2026-10-05", "text": "2026-10-05"},
      "sheet_tags": {"price_reaction": null, "interest": null, "offer_intent": null, "next_followup_date": null},
      "visitor_count": null,
      "entries": [{"key": "showing:1a2b3c4d5e/feedback/2026-09-18/9f8e7d6c", "field": "feedback", "col": "G",
                   "date": "2026-09-18", "date_raw": "9/18", "year_rule": "listing_life", "text": "as typed"}]
    }]
  }],
  "stats": {}, "warnings": []
}
```

- Tab `kind` is one of `disclosure`, `showing`, `inquiry`, `open_house`, `offers`, `other`. Tabs are matched
  by pattern, never by exact title.
- **Row keys are stable.** `sr_contract.row_key(tab_kind, name, phones, emails, extra)` is made from who the
  row is about, not from where it sits, so sorting the sheet or inserting a row changes nothing. Two rows
  with the same basis get `~2`, `~3` in sheet order. `row` (the sheet row number) is information only.
- **Entry keys follow the wording.** `sr_contract.entry_key(row_key, field, date, text)` changes when a note
  is edited. That is deliberate: an edited note has to be read again.
- Every Notes spill column is read. Every dated line in the Feedback cell and in each Notes cell is one entry.
- `sheet_tags` holds the four optional columns the team may add (price reaction, interest level, offer intent,
  next follow-up date) and `visitor_count` the optional numeric column on the open house tab. Null when the
  column is absent or blank. The skill reads them when present and works fully without them.
- Intake also writes, for Claude's use only: `as_of` (the day the sheet was exported), per row `last_touch_all`,
  `sheet_tags_raw`, `hints`, and on open house rows `sessions[]` (`key` is `<row key>#<n>`, with `date`,
  `time_text`, `groups`, `counted_unit`, `groups_source`, `text`, `team_note`), `recap_raw` and
  `visitor_count_unit`; at the top `tabs_found`, `tabs_missing`, `merge_candidates`, `inviter_candidates`,
  `skipped_rows` (each with its reason) and `since_last_parse`.
- Where a person came from lives here and in `curation.json` only. The ledger never says which row it was.

## 4. curation.json

Claude's reading of the notes, and the operator's corrections on top of it. It is keyed by row and entry keys,
so it survives a re-parse, and only new or edited notes need reading next week. Check it with
`sr_contract.validate_curation`. Nobody is asked to look at this file: it is internal.

```json
{
  "schema_version": 1, "slug": "sample-glen", "updated": "2026-04-13",
  "people": {
    "c001": {
      "rows": ["showing:1a2b3c4d5e", "disclosure:5e4d3c2b1a"],
      "name_short": null, "name_recorded": true, "kind": "agent", "brokerage": null,
      "is_open_house_host": false, "team_side": false, "represented_by": null, "reached_through": null,
      "phone_out_of_service": false,
      "tags": {
        "price_reaction": {"value": "too_high", "provenance": "corrected_by_operator", "corrected_by": "Graeham",
                           "corrected_on": "2026-04-13", "sheet_value_seen": null},
        "interest": {"value": "cold", "provenance": "claude"},
        "themes": {"value": ["size_layout"], "provenance": "claude"}
      },
      "feedback_safe": "Liked the home and said the price is too high.", "feedback_softened": true,
      "status": null, "status_note_safe": null, "theme_other": null, "liked_other": null,
      "offer_basis_safe": null, "offer_basis_date": null,
      "engagements": {"showing:1a2b3c4d5e": [{"type": "agent_reported_tour", "date": "2026-03-14", "date_quality": "approximate"}]},
      "extra": {"touches": [], "feedback": []},
      "feedback_safe_as_of": null,
      "unsure": null,
      "tag_notes": "private: why each value was chosen"
    }
  },
  "entries": {
    "showing:1a2b3c4d5e/note/2026-04-02/0a1b2c3d": {
      "touches": [{"channel": "voicemail", "direction": "outbound", "outcome": "left_voicemail",
                   "summary_safe": "Called, no answer. Left a voicemail."}],
      "feedback": null, "provenance": "claude"
    },
    "showing:1a2b3c4d5e/feedback/2026-04-03/4d3c2b1a": {
      "touches": [{"channel": "unknown", "direction": "inbound", "outcome": "replied", "summary_safe": "..."}],
      "feedback": {"text_safe": "...", "softened": true, "source": "conversation", "counts_as_conversation": true,
                   "price_reaction": "too_high", "price_asked": null, "themes": ["size_layout"], "liked": []},
      "provenance": "corrected_by_operator", "corrected_by": "Graeham", "corrected_on": "2026-04-13"
    }
  },
  "open_houses": {"open_house:9f8e7d6c5b#1": {"recap_safe": "3 groups. One visitor asked for the disclosure package.",
                                              "disclosure_requests": 1}},
  "offers": [],
  "ignored_rows": {"showing:77aa88bb99": "a cancelled showing request, typed as an inquiry on another row"},
  "date_corrections": {"<row or entry key>": {"date": "2026-03-21", "date_quality": "approximate", "reason": "..."}},
  "overrides": [{"path": "people.c001.kind", "value": "buyer", "by": "Graeham", "on": "2026-04-13", "reason": "..."}],
  "next_week": []
}
```

- `people` is the merge: one person, one id, however many rows they sit on. Ids are assigned once and never
  reused. A short name is not a key (two agents can shorten to the same label).
- `name_short` overrides `sr_contract.short_name(name_raw)` when the default is wrong.
- An entry with `"touches": []` is deliberately not a touch (a duplicate or a label).
- **What each note says.** Claude reads every note and decides what it says (price too high, liked the layout,
  passed, and so on) so it can be counted. That is silent and internal. Each value under `tags` is
  `{value, provenance}` and each entry carries `provenance`: `claude`, `corrected_by_operator` or
  `sheet_column` (`sr_contract.PROVENANCE`). **Nothing gates on it and nothing prints it.** It exists for one
  rule: a value the operator corrected, or one that came from a sheet column, is never overwritten by a later
  automatic pass (`curation_tools.py apply` skips it and says so).
- **Precedence at build time.** A sheet column beats Claude's reading. The operator's correction beats both.
  A correction records the sheet value it replaced in `sheet_value_seen`; if the team later types a different
  value in that sheet column, the newer sheet value is used and `notes_for_operator.json` says so.
- **Corrections** (`curation_tools.py correct`, implemented in `sr_correct.py`) change a value
  (`--who "Jordan" --set price_reaction=not_raised`), reword or remove a sentence the report prints
  (`--reword ... --to ...`, `--remove ...`), or apply a corrections file (`people`, `entries`, `open_houses`,
  `merge`, `split`, `ignore_rows`, `next_week`). Everything a correction touches is stamped
  `corrected_by_operator` with `corrected_by` and `corrected_on`; a corrected person-level field is also
  recorded in `overrides` (`path`, `value`, `by`, `on`, `reason`), which is what locks it.
- `people[].engagements` is keyed by row key (`"+"` for one tied to no row) and says what a row really was when
  the tab alone would mislead. A `date` may be `"first_record"`. `people[].extra` holds dated touches and
  feedback that are tied to no sheet note. `feedback_safe_as_of` dates the person-level comment, so a comment
  that quotes an entry made after the week closed is rebuilt from the entries inside the week.
- `people[].unsure`, `entries[].unsure` and `open_houses[].unsure` are one plain sentence each: what Claude could
  not tell (for example whether a tour took place). They go to `notes_for_operator.json` and are cleared when
  the operator corrects that person or entry. They are rejected in a ledger.
- `entries[].offer_related` marks a note that hints at who may be weighing an offer. Touches read from the
  Email, Call and Text date columns have keys of the form
  `sr_contract.entry_key(row_key, "last_call" | "last_text" | "last_email", date, "")`.
- `open_houses` is keyed by session (`<row key>#<n>`): `date`, `date_quality`, `date_note`, `not_before`,
  `ignore`, `host`, `groups`, `counted_unit`, `recap_safe`, `softened`, `disclosure_requests`, `time_text`,
  `price_remark {reaction, remark_safe, softened}`. `offers[]` carry `source_row` (the row on the offers tab).
- `tag_notes` (private reasoning) stays here. It is not allowed in the ledger.
- `validate_curation` scans every seller-facing sentence in this file, the `extra` lines and engagement notes
  included, for phone numbers, emails, access codes, first-person asides and dashes.

## 5. events.json (optional)

Machine events read from notification emails. Written only when the operator asked for that source in this
session. Never create mail filters or labels to collect them.

```json
{
  "schema_version": 1, "slug": "sample-glen",
  "fetched": [{"asked_on": "2026-04-13", "source": "glide_email", "window": ["2026-04-06", "2026-04-13"]}],
  "events": [{
    "id": "e0001", "type": "disclosure_opened", "occurred_at": "2026-03-31T14:13:00-07:00", "date": "2026-03-31",
    "person_raw": "...", "contact_id": "c003", "is_team_side": false,
    "keybox_number": null, "duration_minutes": null,
    "source": "glide_email", "source_message_id": "...", "matched_by": "name"
  }]
}
```

`type` is `disclosure_opened`, `keybox_showing_start` or `keybox_showing_end`. A host opening the key box for
an open house is `is_team_side: true` and is not a showing.

### market.json and marketing.json (optional)

When either file is in the listing folder the builder copies it into `ledger.market` or `ledger.marketing`
(shapes in section 6). For the market block it recomputes `sample`, `days_to_contract` and
`subject_on_report_date` from `sales[]`, so those numbers are never typed.

## 6. ledger.json

The renderer reads this file and `identity.json`, nothing else. It must pass
`sr_contract.validate_ledger(ledger)` with no problems. A ledger that passes is ready to render and send:
there is no second, stricter check. Start from `sr_contract.blank_ledger(slug)` and `sr_contract.blank_contact(id, name_short)`,
fill in the rows, then call `sr_contract.finish_ledger(ledger)`, which computes every derived block.

Rules that hold everywhere in the ledger:

1. **Nothing dated after `report.week_end`** sits in `contacts`, `open_houses` or `offers`. Later entries go
   in `report.since_week_closed.items` and are in no count.
2. **Every count is buyer side.** Team-side hosts and buyers reached through their agent are in the contact
   list but in no count (see `counting-rules.md`). `totals.team_side_set_aside` says what was set aside.
3. **Null means not recorded, never zero.**
4. **Seller-safe text only**: no phone numbers, emails, access codes, first-person asides, other listings'
   addresses, em dashes or en dashes. `validate_ledger` scans every string.
5. **Feedback only.** The keys `recommendation`, `decision_log` and `seller_ask` are rejected anywhere in the
   file.
6. **No working state.** Where a value came from and whether anyone looked at it are not in a ledger. The keys
   `provenance`, `tag_source`, `tag_sources`, `tag_review`, `confirmed_by`, `confirmed_on`, `corrected_by`,
   `corrected_on` and `unsure` are rejected anywhere in the file, along with row keys, phone numbers and the
   other private keys.

### Top level

| Key | Written by | What it is |
|---|---|---|
| `schema_version` | builder | `1` |
| `meta` | builder | `slug`, `built_at`, optional `note`. `synthetic: true` marks test data, which the checks never let through to a seller |
| `listing` | builder | the seller-safe facts from `listing.json` (no Drive ids, no key-box number) |
| `report` | builder | issue number, dates, `tracking`, `since_week_closed`; day counts set by `finish_ledger` |
| `themes_vocabulary` | builder | exactly `sr_contract.themes_vocabulary()` |
| `contacts` | builder | one entry per person |
| `open_houses` | builder | one entry per session |
| `offers` | builder | one entry per offer. Email only, never in the link copy |
| `weeks` | `finish_ledger` | one row per week since the list week |
| `totals` | `finish_ledger` | since-launch numbers |
| `pricing_tally` | `finish_ledger` | the price row, out of people. `open_house_price_remarks` is written by the builder |
| `themes_tally` | `finish_ledger` | what people are saying, ranked |
| `liked_tally` | `finish_ledger` | what people liked |
| `price_periods` | `finish_ledger` | the record at each list price, split by event date |
| `offer_watch` | `finish_ledger` | open offer leads, each `live` or `earlier_interest` |
| `team_side` | builder | the people on our side of the table |
| `market` | builder | optional days on market comparison, or null |
| `marketing` | builder | optional marketing status, or null |
| `next_week` | builder | plain sentences, in order |
| `sources_used` | builder | every source the operator handed over or pointed to |
| `data_quality` | builder | plain build notes for Claude. Never printed to a seller, and the checks fail a page that prints one |

### report

```json
{
  "issue_number": 5, "report_date": "2026-04-13", "week_start": "2026-04-06", "week_end": "2026-04-12",
  "days_on_market": 32, "days_on_market_at_week_end": 31, "weeks_on_market": 5,
  "tracking": {"keybox_showings": true, "disclosure_sent": true, "disclosure_opened": true},
  "since_week_closed": {"through": "2026-04-13", "items": [
    {"date": "2026-04-13", "kind": "touch", "contact_id": "c003", "name_short": "Wilhelmina R.",
     "summary_safe": "Sent a text on Monday morning. No answer yet.", "offer_related": false}]},
  "as_of_note": null
}
```

- `week_start` is a Monday, `week_end` the Sunday after, `report_date` the Monday after that.
  `sr_contract.report_week(run_date)` gives all three.
- `tracking` says whether each kind of fact is recorded for this listing at all. When a flag is false the
  matching counts are null in `totals` and in every week.
- `since_week_closed.items[].kind` is `touch`, `feedback`, `engagement`, `open_house`, `offer`,
  `price_change` or `note`. An `offer` item carries no price or terms. Set `offer_related: true` on any item
  that hints at who may be weighing an offer: the link copy drops those.
- `as_of_note` is an operator note and is never printed to a seller.
- `brief_override` (optional) is the agent's own words for "This week in brief", for this issue only: plain
  text, blank lines between paragraphs. The email prints it in place of the counted brief; the link copy and
  the PDF always use the counted brief. Set it with `build_ledger.py --brief-file`. The checks let its wording
  through only because the operator supplied it (`check_report.py --confirm-brief-override`).

### contacts[]

```json
{
  "id": "c001", "name_short": "Odalys V.", "name_recorded": true, "brokerage": "Harborlight Realty",
  "kind": "agent",
  "is_open_house_host": false, "team_side": false,
  "represented_by": null, "reached_through": null, "phone_out_of_service": false,
  "engagements": [{"type": "keybox_showing", "date": "2026-03-14", "date_quality": "exact", "confirmed": true,
                   "time_text": "2 to 3 PM"}],
  "touches": [{"date": "2026-03-15", "date_quality": "exact", "channel": "call", "direction": "outbound",
               "outcome": "reached", "summary_safe": "Asked for feedback the day after the showing."}],
  "feedback_log": [{"date": "2026-03-15", "text_safe": "Her clients liked the layout.", "softened": false,
                    "source": "conversation", "counts_as_conversation": true,
                    "price_reaction": "not_raised", "price_asked": null,
                    "themes": [], "liked": ["layout_space"]}],
  "feedback_safe": "Her clients liked the layout and the yard.", "feedback_date": "2026-04-08",
  "price_reaction": "not_raised", "price_asked": null,
  "interest": "warm", "offer_intent": "maybe", "status": "replied", "status_note_safe": null,
  "themes": ["still_deciding"], "theme_other": null, "liked": ["layout_space"], "liked_other": null,
  "softened": false, "next_followup_date": "2026-04-15",
  "offer_basis_safe": null, "offer_basis_date": null,
  "followup": {"outbound_touches": 5, "outbound_days": 4, "replies": 3, "first_touch_date": "2026-03-15",
               "last_touch_date": "2026-04-08", "last_outbound_date": "2026-04-07", "last_reply_date": "2026-04-08",
               "tries_since_last_answer": 0, "days_since_last_touch": 4, "calls_not_connected": 0}
}
```

| Field | Values and meaning |
|---|---|
| `id` | `c001` form. Stable across issues. The only key for a person |
| `name_short` | `First L.` or a single name. With `name_recorded: false` it is a label such as `Agent, name not recorded` |
| `brokerage` | as recorded, or null. Print it through `sr_contract.display_brokerage` |
| `kind` | `agent`, `buyer`, `open_house_visitor` |
| `is_open_house_host` | true for anyone who hosted an open house for us |
| `team_side` | true for a host who brought no buyer of their own. Team-side people are in no count |
| `represented_by` | the id of the agent or host this buyer is reached through, or null. These buyers carry no touches and their status is `through_agent` |
| `reached_through` | `open_house_host` when our only route to the person is the host, else null |
| `phone_out_of_service` | true when the number on file does not work |
| `engagements[].type` | `keybox_showing`, `agent_reported_tour`, `inquiry`, `open_house_visit`, `disclosure_on_list`, `disclosure_link_sent`, `disclosure_opened`, `disclosure_shared_by_agent` |
| `engagements[].date_quality` | `exact`, `approximate`, `missing` (date null). Optional `date_label`, `time_text`, `note` |
| `engagements[].confirmed` | false when the log does not confirm a listed tour took place |
| `touches[].channel` | `call`, `voicemail`, `text`, `email`, `in_person`, `unknown` |
| `touches[].direction` | `outbound`, `inbound`, `unknown` (the log does not say who called) |
| `touches[].outcome` | `sent`, `left_voicemail`, `no_answer`, `did_not_connect`, `reached`, `replied`, `unknown` |
| `feedback_log[]` | dated things the person told us. `source` is `conversation`, `written_reply` or `open_house_host` |
| `feedback_log[].counts_as_conversation` | false for a host's secondhand recap. At most one counted entry per day |
| `feedback_safe`, `feedback_date` | the person-level comment a card prints, and the date of their latest entry |
| `price_reaction` | `too_high`, `fair_or_positive`, `not_raised`, `unknown` (no conversation). Set from the feedback entries |
| `price_asked` | true, false or null: was price asked directly. Null when not recorded |
| `interest` | `hot`, `warm`, `cold`, `passed`, `unknown` |
| `offer_intent` | `yes`, `maybe`, `no`, `unknown` |
| `status` | `not_yet_contacted`, `awaiting_reply`, `replied`, `passed`, `writing_offer`, `offer_submitted`, `through_agent` |
| `themes` | keys from `themes_vocabulary.themes`. `other` goes with a `theme_other` label |
| `liked` | keys from `themes_vocabulary.liked`. `other` goes with a `liked_other` label |
| `softened` | true when the comment or any entry was softened (optional `feedback_softened` marks the comment itself) |
| `next_followup_date` | ISO date or null |
| `followup` | set by `finish_ledger`. The separate-day numbers every card prints |

`finish_ledger` (through `settle_contact`) sets `followup`, `price_reaction`, `price_asked`, `softened`,
`feedback_date`, `themes` and `liked` (when the entries carry them) and `status`. The builder sets `status`
only for the three a person decides: `passed`, `writing_offer`, `offer_submitted`.

Engagements and open houses may carry `time_text`; an open house may carry `date_note`. A
`since_week_closed` item for a person first seen after the week closed has `contact_id: null` and still
carries `name_short`.

### open_houses[]

```json
{"date": "2026-03-28", "date_quality": "exact", "host": "Leocadia M.", "host_contact_id": "c007",
 "time_text": "1 to 4 PM", "groups": 3, "counted_unit": "groups", "groups_source": "parsed_from_prose",
 "recap_safe": "3 groups. One visitor with no agent asked for the disclosure package.", "softened": false,
 "disclosure_requests": 1}
```

`groups` is the count in the host's own unit, named by `counted_unit` (`groups`, `visitors`, `guests`,
`parties`, `people`). `groups_source` is `sheet_column`, `parsed_from_prose` or `not_recorded` (then
`groups` is null). One entry per session: a two-day weekend is two entries. Each session keeps the host's own
unit, so `counted_unit` can differ from session to session on one listing; the page then labels the total as
each host counted.

### offers[]

```json
{"id": "o1", "date": "2026-01-27", "contact_id": "c001", "agent_short": "Alder A.", "brokerage": "...",
 "price": 1120000, "pct_of_list": 97.4, "terms_summary": "Conventional loan, 20% down, 21 day close.",
 "state": "countered", "note_safe": null}
```

`state` is `received`, `countered`, `accepted`, `declined`, `withdrawn` or `expired`. `pct_of_list` uses the
list price on the day of the offer. `contact_id` ties the offer to the person, which is how the link copy
knows whom to leave unnamed (`sr_contract.offer_people_ids`).

### weeks[], totals, price_periods

Written by `finish_ledger`. Field by field definitions are in `counting-rules.md`. Every week from the list
week to the report week is present, quiet weeks included. `weeks[].label` is the only field a builder may
add. `keybox_showings`, `disclosure_sent`, `disclosure_opened`, `disclosure_link_sent`,
`disclosure_opened_confirmed` and `open_house_groups` can be null. A builder that could not check one week
may set that week's nullable count to null before calling `finish_ledger`, and the null is kept.

### pricing_tally, themes_tally, liked_tally

```json
"pricing_tally": {"people_with_feedback": 58, "too_high": 7, "fair_or_positive": 3, "not_raised": 48,
                  "raised_price": 10, "price_asked_recorded": 10, "asked_directly": 10,
                  "conversations_with_feedback": 58,
                  "open_house_price_remarks": [{"date": "2026-02-14", "reaction": "too_high",
                                                "remark_safe": "...", "softened": true}]},
"themes_tally": {"people_with_feedback": 58, "people_with_no_theme": 14,
                 "rows": [{"key": "size_layout", "label": "Size or layout", "group": "home", "people": 7,
                           "new_this_week": 0, "contact_ids": ["c012"]}]},
"liked_tally": {"people_with_feedback": 58, "people": 27,
                "rows": [{"key": "home_overall", "label": "The home overall", "people": 9, "contact_ids": []}]}
```

The three price rows always print, from `themes_vocabulary.price_rows`. Price is not a theme key.
`open_house_price_remarks[].reaction` is `too_high`, `fair_or_positive` or `raised_no_verdict`.

### offer_watch[], team_side[]

```json
"offer_watch": [{"contact_id": "c004", "lead_state": "live", "last_touch_date": "2026-03-17",
                 "days_since_last_touch": 5, "basis_safe": "...", "basis_date": "2026-03-17"}],
"team_side": [{"name_short": "Leocadia M.", "role": "open house host", "sessions_hosted": 4, "contact_id": "c007"}]
```

`team_side` lists every host who brought no buyer of their own: one with no row of their own on the other
tabs has `contact_id: null`, and a team-side contact who hosted nothing in the period has `sessions_hosted: 0`.

### market, marketing (optional, null when not collected)

`market` needs `as_of`, `data_through`, `refreshed_for_this_issue`, `scope`, `source`, `method`, `sample`
(`closed`, `used`, `excluded`, `exclusion_reason`), `days_to_contract` (`average`, `median`, `shortest`,
`longest`, `values_sorted`, `over_90_days`), `subject_on_report_date` (`date`, `days_on_market`,
`sales_under_contract_by_that_day`, `of_sales`), `sales[]` (`address`, `sold_date`, `sold_price`, `sqft`,
`beds_baths`, `list_date`, `list_price`, `contract_date`, `days_to_contract`, `used_in_average`).
`validate_ledger` recomputes the sample and the day counts from `sales[]`. `statement_safe` is optional and
is never printed: the renderer writes the market sentence from the validated numbers, so it cannot go stale.

`marketing` needs `as_of`, optional `note`, and `channels[]` with `channel`, `status`
(`on`, `prepared`, `on_hold`, `not_launched`, `ended`), `checked` and `detail`. A channel is called running
only when `sr_contract.channel_is_running(channel, report)` is true.

### sources_used[], data_quality[]

```json
"sources_used": [{"kind": "activity_sheet_live", "label": "Live activity sheet, exported to xlsx", "as_of": "2026-04-13"}],
"data_quality": ["The Mar 15 open house has no visitor count."]
```

`kind` is one of `sr_contract.SOURCE_KINDS`. Labels are plain words: no Drive ids or message ids here. List
only sources the operator handed over or pointed to in this session.

## 7. notes_for_operator.json and issues\NN\manifest.json

`notes_for_operator.json` is written beside the ledger by `build_ledger.py` and copied into the issue folder.
It is what Claude is honestly unsure about, for the **chat reply** that hands over the Gmail draft, under the
words "Worth a glance before you send". It is never in the report and it is not a table of anything.

```json
{
  "schema_version": 1, "slug": "sample-glen", "issue_number": 5, "report_date": "2026-04-13",
  "week_start": "2026-04-06", "week_end": "2026-04-12",
  "how_to_use": "...",
  "worth_a_glance": ["Could not tell from the notes whether this tour took place: Odalys V. It is counted as a tour.",
                     "The wording of 1 comment this week was toned down, with the substance kept: Ignatius D."],
  "also_noted": ["..."]
}
```

- `worth_a_glance` holds **at most five** short plain lines, most important first: the sheet was exported
  before the week ended; anything Claude passed with `--glance` (for example a count that differs from the
  team's status email, and why); each `unsure` sentence from `curation.json`; a tour this week nothing
  confirms took place; a row on the showing tab counted as an inquiry because it has no showing date; a
  comment this week that was toned down; an approximate tour date; an open house with no count or no date;
  an earlier correction that gave way to a newer sheet value.
- `also_noted` is the rest, for Claude only. Neither list uses working words: the operator never reads about
  how the notes were read.

### manifest.json

```json
{
  "schema_version": 1, "slug": "sample-glen", "issue_number": 5,
  "report_date": "2026-04-13", "week_start": "2026-04-06", "week_end": "2026-04-12",
  "built_at": "2026-04-13T10:02:00-07:00",
  "ledger_sha256": "...",
  "files": [{"name": "email.html", "bytes": 61234, "sha256": "..."}],
  "email_bytes": 61234,
  "flags": {"webfonts": false, "hero": null, "link_url": null, "sections": ["market", "marketing"], "fit_level": 0},
  "checks": {"ledger_problems": 0, "page_checks_run": 26,
             "ship_gate": {"passed": true, "checked_at": "...", "pages": 3, "blocking": 0, "warnings": 0}},
  "delivery": {"gmail_draft_id": null, "link_published_url": null, "link_published_on": null, "sent_on": null}
}
```

There is one build per issue and it lives in `issues\NN\`. A rebuild after a correction replaces the files.
Once the operator says the issue went to the seller (`snapshot_issue.py record --sent-on`), the folder is the
record of what was sent, and `freeze` refuses to replace it (exit status 3) unless `--replace-sent` is given.
`ledger.json` in the issue folder is the ledger exactly as rendered. `email_bytes` must stay under
`sr_contract.LIMITS["email_max_bytes"]` (95,000): an email at or over the limit is not kept. The manifest is
written by `snapshot_issue.py` only, after the checks pass, and `check_report.py` compares each file's hash
with it. The email's link to the complete record must equal `flags.link_url`.

## 8. Changes against the approved mockup shape

The mockup carried two dialects (the first listing's file and the richer file of the second) and the generator
bridged them. This contract picks one. Every change:

**Removed (feedback only):** `recommendation`, `decision_log`, `seller_ask`, and
`pricing_tally.statement_safe` (it explained what silence on price means).

**Removed after the design review (2026-10-13):** the review step. `meta.tag_review`, `meta.confirmed_by`,
`meta.confirmed_on`, `contacts[].tag_source` and `tag_sources`, the draft folder `issues\NN\draft\`,
`manifest.build_kind` and `manifest.tag_review`, the yellow notice, the reviewer panel, the review table, and
the `--draft`, `--final` and `--allow-unreviewed` switches. One build mode replaces them.

**Added, as asked:** per-contact `themes` from a fixed vocabulary with a free `theme_other`, `liked` with
`liked_other`, `price_asked`, `next_followup_date`; top-level `themes_vocabulary`; first-class
`is_open_house_host`, `phone_out_of_service` and the separate-day fields (`contacts[].followup`,
`totals.outbound_person_days`, `totals.outbound_distinct_days`, `weeks[].outbound_distinct_days`);
`report.since_week_closed`; `sources_used`; `data_quality` (kept as plain sentences). Provenance is in
`raw.json` and `curation.json` only and is rejected in a ledger.

**Unified, because one renderer needs one shape:**

1. `schema_version` and a required `meta` block (`slug`, `built_at`).
2. Counts are buyer side in the ledger. The mockup stored totals with hosts in and subtracted on the page.
   New `contacts[].team_side` and `totals.team_side_set_aside`.
3. `showings` is gone. `keybox_showings` and `agent_reported_tours` are separate everywhere and never
   summed. `showings_undated` and `showings_approximate_date` became `tours_undated`,
   `tours_approximate_date`, plus `tours_unconfirmed`.
4. New engagement type `disclosure_on_list` (on the disclosure tab, no record of sent or opened). The
   Rows the first dialect typed `disclosure_opened` are now this. Buyers an agent shared the package with
   are `disclosure_shared_by_agent`.
5. `disclosure_contacts` counts people we follow up with. Buyers the package was shared with moved to
   `totals.disclosure_shared_buyers`.
6. `report.tracking` plus nulls replaces the implicit "is this recorded" tests.
7. One reply rule. `got_response` is gone: a reply is an inbound touch or a call that reached the person,
   counted once per person per day (`sr_contract.is_reply`). `responses` became `replies_inbound`.
8. `direction` null became `unknown`. New outcome `did_not_connect`.
9. `feedback_log` is required on every contact (the first dialect had one comment per person). Entry-level
   `price_reaction`, `price_asked`, `themes`, `liked`, `source`, `counts_as_conversation`.
10. A conversation is one person on one day. The first dialect counted a person once per week.
11. `pricing_tally.people_with_feedback` is the one denominator (was `conversations_with_feedback` in one
    dialect, `parties_with_a_conversation` in the other). Added `price_asked_recorded`, `asked_directly`.
12. `objection_tally` (first dialect) and top-level `themes` (second dialect) became `themes_tally`. `price` is not a
    theme. New `liked_tally` replaces the keyword match the page did.
13. `price_periods` is in the ledger (the page computed it).
14. `offer_watch` is derived, with `lead_state`. Its `after_week_end` flag is gone because nothing after the
    week end is in the ledger.
15. `since_week_end` moved to `report.since_week_closed`. The per-row flags `in_report_week` and
    `after_week_end` are gone.
16. `represented_by` holds a contact id in every listing (`via_agent_id`, `party_id` and `counts_in_totals`
    are gone). New status `through_agent`.
17. `attempts` became `followup.outbound_days`. `awaiting_reply_3plus_attempts` keeps its name and counts
    days since the last answer.
18. `price_history[].event` is `listed` or `price_change` (was `price change`).
19. Open houses keep `groups` and `groups_source` and gain a required `counted_unit`, `date_quality`,
    `host_contact_id`. `groups_source` gains `sheet_column`.
20. Offers gain `id`, `contact_id`, `note_safe`.
21. Marketing channel `status` is a key (`on`, `prepared`, `on_hold`, `not_launched`, `ended`), not a
    display string.
22. `definitions` is gone. The definitions are `counting-rules.md`.
23. `status_note` became `status_note_safe`. `tag_notes` moved to `curation.json`.
24. New totals: `contact_records`, `team_side_people`, `contacted_through_host`,
    `awaiting_reply_answered_before`, `awaiting_reply_quiet`, `open_no_final_answer`,
    `open_no_final_answer_quiet`, `calls_not_connected`, `people_with_feedback`, `offers_by_state`.
    New per week: `outbound_people`, `outbound_distinct_days`, `open_house_sessions_without_count`.

## 9. What builders must know

- Import one module: `import sr_contract as C`. Put `scripts` on `sys.path` first. The counting and
  validation code sits in `sr_contract_counts.py` and `sr_contract_validate.py` and is reached through `C`.
- Do not compute a total in a renderer. Read it from the ledger. If a number you need is missing, ask for it
  in the contract.
- Read brand facts with `C.load_identity()`. Never type a DRE, phone, brokerage or brand line into code.
- Another agent's brokerage can be a name on the brand blocklist. Keep it in the ledger as recorded and
  print it with `C.display_brokerage(name, identity)`.
- The link copy must leave out `offers`, every person in `C.offer_people_ids(ledger)` as an offer lead,
  every `since_week_closed` item marked `offer_related`, and every theme row whose vocabulary entry has
  `hide_in_link_copy: true`.
- Format with `C.fmt_money`, `C.fmt_date`, `C.fmt_range`, `C.fmt_count`, `C.fmt_followup`. They never emit
  a dash. Run typed text through `C.strip_dashes` when paraphrasing.
- The synthetic fixtures are `tests/fixtures/ledger_small.json` and `ledger_busy.json`. Regenerate them with
  `python tests\fixtures\make_fixtures.py`. `tests/fixtures/make_workbook.py` builds a synthetic activity sheet
  with every awkward shape, for the intake, ledger, curation and run tests.
- Never print the word "tag" in anything an operator or a seller reads, and never ask either of them to look
  over or confirm how the notes were read. What Claude reads from a note is internal. What Claude is unsure about goes in `notes_for_operator.json`, in plain words.
- The page hooks the checks read (`data-sr`, `data-sr-section`, `data-sr-table`, `data-sr-person`) are listed by
  `python scripts\check_report.py --hooks`. A page never carries a `draft_notice` or `reviewer_panel` section
  and never names a build kind.
