# Reading the notes, and tone

How you turn the team's raw notes into what the report prints and counts, and how a correction is applied. Every name and note in this file is invented.

## Contents

1. What this step is
2. The work list
3. The readings file
4. People: who is who
5. Follow-up lines
6. Comments: the tone rule, with examples
7. What a comment counts as
8. The privacy filter
9. Softened, and unsure
10. Open houses, what a row really was, next week
11. Notes that are not on the sheet
12. Applying a correction
13. What will stop you

## 1. What this step is

The team's notes are shorthand written for themselves: blunt, full of phone numbers, sometimes unkind about the home. A seller reads the report. Between the two sits your reading of each note: a seller-safe sentence, and a decision about what the note says so it can be counted (price too high, liked the layout, passed).

**This reading is silent.** Nobody is shown it, nobody is asked to confirm it, and it never holds up a report. Graeham reads the finished draft. If something is wrong he says so in plain words, and you correct it (section 12).

**How the code and you split the work.** `intake_sheet.py` splits every Feedback and Notes cell into dated entries: a line that starts with a date such as `10/7 -` opens an entry, and a line that starts with `>` is the contact's own answer. Notes made only of stock phrases ("no answer, left a vm. sent a text and email", "LVM") are read by the code and never reach you. Everything else is yours, once: the work list holds only what nobody has read, and an edited note comes back with its old wording beside it.

**The Email, Call and Text columns** hold one date each. Until Adrian answers the open question in `counting-rules.md` section 5, read a date there as a follow-up our team made that day, unless the row's note says the agent called us, which makes it their reply. Say in a glance line when that reading moves a count.

**It is kept.** Your reading is saved in `<listing>\curation.json`, keyed to the note's own wording, so next week only new or edited notes need reading, and a correction the operator made is never overwritten (section 12). In that file and in the readings file the values for a person sit under the key the work list's `readings_file_format` shows. That key is a field name in a data file and nothing more: never use the word with an operator or a seller. If you must say anything, say "how I read the note".

## 2. The work list

`run_issue.py` stops with exit 10 when there is something new to read and writes `<listing>\work\todo.json`. It is private: it quotes notes as typed. What each list in it means:

| List | What it is | What you do |
|---|---|---|
| `new_people` | Rows nobody has placed, grouped into proposed people with a `proposed_id` | Decide who each one is (section 4) and give them their rows |
| `rows_to_add` | A new row that may belong to someone already on file (same phone or name) | Add the row to that person, or make a new person if it is someone else |
| `relink_candidates` | A row whose name or number was edited, so its key changed | Confirm with `"relink": {"<old row key>": "<new row key>"}` |
| `entries` | Notes not read yet, with the text as typed, `sensitive_hints`, and `edited_from` when a note you read before was reworded | Write touches and feedback for each (sections 5 to 7) |
| `open_house_sessions` | Sessions needing a date, a plain recap, or both | Section 10. A session with no date stops the build |
| `offer_rows` | Rows on the offers tab not entered yet | Enter each under `offers` (`intake.md`) |
| `showing_rows_without_a_date` | Showing rows with no date | Section 10. Counted as an inquiry until you or the operator say otherwise |
| `people_without_a_read` | People with feedback but no interest level | Give them one |
| `rows_waiting_for_a_later_issue` | Rows dated after this issue | Nothing. They wait |

Notes made only of stock phrases ("no answer, left a vm. sent a text and email", "LVM") are not on the list. The code reads those.

`readings_file_format` at the end of the work list shows the shape of the file you write.

## 3. The readings file

Write one JSON file in `<listing>\work\` (it is private and stays out of git), then apply it:

```
python "<scripts>\curation_tools.py" apply --folder "<listing>" --readings "<listing>\work\readings.json"
```

A small invented example:

```json
{
  "people": {
    "c014": {
      "rows": ["showing:1a2b3c4d5e", "disclosure:5e4d3c2b1a"],
      "kind": "agent",
      "brokerage": "Harborlight Realty",
      "tags": {"interest": "warm", "offer_intent": "maybe"},
      "feedback_safe": "Her clients liked the yard and are still deciding.",
      "offer_basis_safe": "Said her clients may write an offer after a second visit.",
      "offer_basis_date": "2026-04-08"
    }
  },
  "entries": {
    "showing:1a2b3c4d5e/feedback/2026-04-08/0a1b2c3d": {
      "touches": [{"channel": "call", "direction": "outbound", "outcome": "reached",
                   "summary_safe": "Reached her by phone and asked how the second visit went."}],
      "feedback": {"text_safe": "Her clients liked the yard and are still deciding.", "softened": false,
                   "source": "conversation", "counts_as_conversation": true,
                   "price_reaction": "not_raised", "price_asked": null,
                   "themes": ["still_deciding"], "liked": ["outdoor_space"]}
    },
    "showing:1a2b3c4d5e/note/2026-04-09/4d3c2b1a": {
      "touches": [{"channel": "email", "direction": "outbound", "outcome": "sent",
                   "summary_safe": "Emailed the disclosure package link."}]
    }
  },
  "open_houses": {"open_house:9f8e7d6c5b#1": {"recap_safe": "Three groups came through. One asked for the disclosure package.",
                                              "disclosure_requests": 1}},
  "offers": [],
  "ignored_rows": {"showing:77aa88bb99": "A cancelled showing request, already logged as an inquiry on another row."},
  "next_week": ["Check back with Odalys V. after her clients' second visit."]
}
```

Rules of the file:

- Use the row keys and entry keys exactly as the work list gives them.
- An entry with `"touches": []` and no feedback means "this note is a duplicate or a label, not an event".
- A date the note got wrong goes in `"date_corrections": {"<row or entry key>": {"date": "...", "date_quality": "approximate", "reason": "..."}}`.
- `apply` never overwrites anything the operator corrected, and it says what it kept. If it says `rejected`, read the reason, fix the file and apply again.
- Nothing is saved if a sentence breaks a hard rule (section 13).

## 4. People: who is who

One person is one id, however many rows they sit on. Merging is your decision: the work list only proposes.

- **Same person on two tabs** (same phone, or same name and brokerage): one person with both rows. When `names_differ` is true, look before joining: two agents can share an office line.
- **`kind`**: `agent`, `buyer` (no agent of their own), or `open_house_visitor`.
- **An "Invited by" row** is a buyer the agent shared the disclosure package with. Make them a `buyer` with `represented_by` set to the agent's id. They are listed under the agent and are in no contact count. Follow-up with them is follow-up with their agent.
- **An open house host** gets `is_open_house_host: true`. A host who brought no buyer of their own is on our side of the table: not a contact, and their messages are not follow-up. The build works that out. A host who also showed the home to their own buyer is an agent like any other.
- **A visitor nobody can reach except through the host**: `kind` `open_house_visitor`, `reached_through` `open_house_host`.
- **A row with a phone number and no name**: still a person. Leave `name_short` empty and set `name_recorded` false. The report says "Agent, name not recorded". Never print the phone number as a stand-in.
- **A row that is not a buyer-side person at all** (a duplicate, a vendor, a note to self): put it in `ignored_rows` with the reason.
- **`name_short`**: set it only when the default "First L." is wrong.
- **`brokerage`**: as the team recorded it, or null. Do not look one up.

## 5. Follow-up lines

Each note becomes zero or more touches. One per channel per day: a call that went to voicemail is one touch, the voicemail.

| Field | Values |
|---|---|
| `channel` | `call`, `voicemail`, `text`, `email`, `in_person`, `unknown` |
| `direction` | `outbound` (our team made it), `inbound` (they got in touch), `unknown` (the note does not say who called) |
| `outcome` | `sent`, `left_voicemail`, `no_answer`, `did_not_connect`, `reached`, `replied`, `unknown` |
| `summary_safe` | One short plain sentence. No first person, no names of other people, no numbers or codes |

- Do not guess a direction. "Spoke with her" with nothing else is `unknown`, and an `unknown` touch is not counted as follow-up. That is honest: the log does not say who called.
- A call that reached the person, or any inbound message, is a reply.
- A number that does not work: `outcome` `did_not_connect`, and set `phone_out_of_service` true on the person when the note says the number is dead.
- Write what was done, not how it felt. "Called, no answer." Not "tried again, still dodging us".

## 6. Comments: the tone rule, with examples

Graeham's rule, in his words: "Friendly, but concise and direct, but should be nuanced to also not offend people that sometimes might be a little sensitive about certain things. You know, whereas a buyer might say, that was absolutely terrible and horrific. We don't want to be quoting those kinds of terrible things about someone's home. We can just say they provided negative feedback and specifically said that the pricing was too high. That's all that needs to be said in that situation."

So a comment is **the team's paraphrase**, printed under "as reported to our team". The substance always stays: what they thought, why they passed, what they said about price. The sting goes. Never put a comment in quote marks, even a kind one: a quote claims those were the exact words, and the page checks fail it.

How to write one:

- Third person, past tense, plain: "His clients liked the layout." One to three short sentences.
- Say who held the view ("her clients", "the buyer"), not the agent's name again.
- Keep every fact that helps the seller understand: the room, the topic, the reason.
- Name the topic of a criticism without the insult: "gave negative feedback on the kitchen", "had concerns about the street".
- Say price plainly when it was said: "specifically said the price is too high".
- No advice, no "we suggest", no reading between the lines. If they did not say it, it is not in the comment.
- No dashes of any kind. No "I", "me" or "my".

**Example 1: harsh words about the home**

| | |
|---|---|
| As typed | `4/3 - client said kitchen is disgusting and the place is a dump, way overpriced. not interested` |
| Seller-safe | His client is not interested. He gave negative feedback on the kitchen and specifically said the price is too high. |
| Counts as | price `too_high`, point raised `condition_disclosures`, interest `passed`, `softened` true |

**Example 2: private details and another listing**

| | |
|---|---|
| As typed | `4/6 - buyers hated the street, too loud. wife is pregnant so they need to move fast, going with the one on Maple Ave` |
| Seller-safe | Her clients chose another property. They had concerns about noise on the street. |
| Counts as | price `not_raised`, points raised `chose_another_home` and `location`, interest `passed`, `softened` true |
| Left out | The pregnancy (family), the other address, the word "hated" |

**Example 3: a caller's aside and an access code**

| | |
|---|---|
| As typed | `4/7 - LVM, texted. he hung up on me yesterday lol. resent lockbox code 4471` |
| Follow-up lines | Called, no answer. Left a voicemail. / Sent a text with the showing instructions. |
| Counts as | Two follow-ups. No comment: he said nothing about the home |
| Left out | The aside, the code |

**Example 4: a kind written reply**

| | |
|---|---|
| As typed | `>Thanks for checking in! We thought the home showed really well and the price seems fair for the size. Still talking it over.` |
| Seller-safe | Her clients thought the home showed well and said the price seems fair for the size. They are still talking it over. |
| Counts as | price `fair_or_positive`, liked `home_overall`, point raised `still_deciding`, source `written_reply`, `softened` false |

Tidying shorthand, fixing grammar and dropping an exclamation mark is not softening. Softening is taking the sting out.

## 7. What a comment counts as

Count what the person said. When the words do not support a value, do not pick the nearest one.

**Price** (on each comment, `price_reaction`). The report always prints three rows that add up to the people who gave feedback.

| Value | Use when the person |
|---|---|
| `too_high` | Said the price is too high in any words: overpriced, a lot for what it is, not worth it in this market, would only pay well under, walked away over the price |
| `fair_or_positive` | Said the price is fair, good, reasonable or a bargain |
| `not_raised` | Spoke with the team and gave no view on price |

- When a person spoke about price more than once, their latest remark decides their row. You only record each comment as it was.
- **A question or a wish is not a verdict.** "Why is it priced below the one next door?" or "would the seller take less?" does not say the price is too high or fair. Record `not_raised`, keep what they asked in the comment, and write an `unsure` line (section 9) so the operator can decide.
- `price_asked`: true when the note shows the team asked about price directly, false when it shows they did not, null when the note does not say. Mostly null.
- Never write, in a comment or anywhere else, what it means that someone did not bring up price.

**Interest** (on the person, the `interest` value in the example above). The page prints the words in the right column.

| Value | Printed as | Use when |
|---|---|---|
| `hot` | Strong interest | They are preparing or planning an offer, or asked for what they need to write one |
| `warm` | Interested | They liked it and are still considering |
| `cold` | Undecided | Lukewarm, no clear interest either way |
| `passed` | Passed | They said no, chose another home, or are no longer looking |
| `unknown` | (nothing) | No read yet |

Someone who passed also gets `"status": "passed"`. A person is never shown both as passed and as an active lead.

**Offer intent** (on the person, the `offer_intent` value): `yes` when they said they will write or are writing, `maybe` when they said an offer is possible, `no` when they said they will not, `unknown` otherwise. With `yes` or `maybe`, give `offer_basis_safe` (the sentence that supports it) and `offer_basis_date`. After 21 days with no contact the report shows them as earlier interest, not as a live lead. `"status": "writing_offer"` or `"offer_submitted"` only when the notes say exactly that.

**Points people raised** (`themes`, a list). Use the keys. Price is not one of them.

| Key | Printed as |
|---|---|
| `location` | Location or surroundings |
| `size_layout` | Size or layout |
| `floor_level` | Floor level |
| `stairs` | Stairs |
| `parking` | Parking |
| `yard_outdoor` | Yard or outdoor space |
| `hoa` | HOA |
| `condition_disclosures` | Condition or disclosures |
| `staging` | Staging or presentation |
| `buyer_timing` | Buyer's timing |
| `still_deciding` | Still deciding (left out of the link copy) |
| `chose_another_home` | Chose or preferred another property |
| `no_reason` | No reason given (they passed and did not say why) |
| `other` | Other, with a short label in `theme_other` on the person |

**What people liked** (`liked`, a list): `home_overall`, `layout_space`, `condition_updates`, `light_views`, `outdoor_space`, `location`, `community`, `value`, or `other` with `liked_other`.

- One person can raise several points. Do not stretch one remark over three keys.
- `other` always goes with its label, and a label always goes with `other`.
- A host's description of a visitor is not that visitor's feedback: `source` `open_house_host`, `counts_as_conversation` false. It prints, labeled as reported by the host, and is in no tally.
- One conversation per person per day. Two notes on one day are one conversation.

## 8. The privacy filter

Nothing a seller could read may carry any of this, in a comment, a follow-up line, a recap or a next-week line:

- A phone number or an email address.
- A lockbox, door, gate or alarm code, or the instructions that go with one.
- Anything about a buyer's health, disability, family or money: an illness, a pregnancy, a divorce, a death, a job loss, a pre-approval, a down payment. Leave the detail out and keep the plain fact that matters to the seller ("needs to move quickly", "chose another property"). The work list flags likely words under `sensitive_hints`, but the code cannot judge meaning. You can.
- A first-person aside from whoever made the call ("hung up on me", "I think they are stalling").
- The address or unit of any other listing. Say "another property" or "another unit in the building".
- A full name. People print as "First L.", agents with their brokerage when recorded.
- Something nobody said. A report once stated which other unit buyers were comparing against. Nobody had told the team that.

Offer price, terms and the offer agent's name are a separate matter: they print in the email only, and the code keeps them out of the link copy and the PDF.

## 9. Softened, and unsure

**`softened: true`** on a comment when you removed harsh wording or lowered its force. The report does not show the flag. It gives the operator one glance line for the week ("The wording of 1 comment this week was toned down, with the substance kept: Ignatius D.") so he knows the seller is reading the gentle version. Do not set it for ordinary tidying, or the line stops meaning anything.

**`unsure`**: one plain sentence, on a person, an entry or an open house, when you could not tell something that changes a count or what the seller is told. It goes to the glance lines and is cleared when the operator corrects that person.

Good unsure lines say what you could not tell and what you did:

- "Could not tell whether Quentin A. toured on Apr 9 or only called. Counted as an inquiry."
- "Rosalind Y. asked why the price is below the home next door. Counted as not giving a view on price."

Do not use it for doubts that change nothing, for your own unfinished work, or as a way to ask the operator to check your reading in general. Five lines is the limit for the whole reply, most important first.

## 10. Open houses, what a row really was, next week

**Open houses** (`open_houses`, keyed by the session key from the work list):

- `recap_safe`: the host's recap in plain words, same tone rule. Finish these in the same pass as the notes, so no reply ever has to mention recaps waiting.
- Traffic stays in the host's own unit. "6 groups" is 6 groups, never a number of people. Set `groups` and `counted_unit` only when the recap states a count and the parser missed it. A vague recap ("good traffic") has no count, and the report says "no count kept".
- A session with no date needs one before the build can go on: from the operator or the schedule sheet (`intake.md`), with `date_quality` and a `date_note`. Never place one by guesswork.
- A price remark relayed by a host goes in `price_remark` (`reaction` is `too_high`, `fair_or_positive` or `raised_no_verdict`, plus `remark_safe`). It is listed on its own and is outside the tally, because the other visitors cannot be counted.
- `disclosure_requests`: how many visitors asked for the package, when the recap says.

**What a row really was** (`engagements` on the person, keyed by row key). The tab a row sits on is only a first guess:

- A showing row with a phone number and a question, and no tour: `[{"type": "inquiry", "date": "..."}]`.
- A disclosure row whose notes say they toured: add `{"type": "agent_reported_tour", "date": "...", "date_quality": "approximate"}`. A date read from a note is approximate and prints with "about".
- A showing row with no date stays an inquiry unless a note says a tour took place. If you cannot tell, leave it and write an `unsure` line.
- A tour listed with nothing confirming it happened still counts, with `"confirmed": false`.
- Key-box showings and tours reported by agents are different kinds and are never added together. Do not relabel one as the other.

**Next week** (`next_week`): what the team will do, in order, as plain sentences. Follow-ups, check-backs, the next open house. Never a suggestion to the seller, and nothing about changing the price.

## 11. Notes that are not on the sheet

When the operator pastes a note or forwards an email about someone already on the sheet, add it under that person's `extra` in the readings file. Each line needs a date.

```json
"people": {"c014": {"extra": {
  "touches": [{"date": "2026-04-10", "channel": "text", "direction": "inbound", "outcome": "replied",
               "summary_safe": "Texted to say her clients want a second visit."}],
  "feedback": []
}}}
```

`extra` is replaced as a whole, so include the lines already there. For someone who is not on the sheet at all, see `intake.md`: the row belongs in the sheet first.

## 12. Applying a correction

The operator reads the draft and says what is wrong in their own words. Turn that into one correction, rebuild, and tell them what changed in a sentence. Do not ask them for field names.

| They say | You run |
|---|---|
| "Jordan never said it was overpriced" | `correct --who "Jordan" --set price_reaction=not_raised --why "Jordan never said it was overpriced"`, then `--reword` the sentence that still says so |
| "Take out the part about the neighbour" | `correct --find "neighbour"` to see where it is, then `correct --who "<name>" --remove "neighbour"` (or `--everywhere`) |
| "Say she is still interested, not undecided" | `correct --who "<name>" --set interest=warm` |
| "That was a tour, not a call" | `correct --file` with that person's `engagements` |
| "Those two are the same agent" | `correct --file` with `"merge": [{"keep": "c012", "absorb": "c031", "reason": "..."}]` |
| "Change the wording to ..." | `correct --who "<name>" --reword "<old sentence>" --to "<new sentence>"` |
| "I answered him myself on Oct 9" | `correct --file` with that person's `extra` touches, adding the dated outbound or reply line (section 11 shape). Without a date, ask for one |
| "I did not reply to him myself" (or "I don't remember") | Nothing to change: the report already counts only what the log shows. Say so in one line, and leave his entry as it is |
| "That offer expired" | A readings file with that offer under `offers`, the whole entry copied from `curation.json` with the same `id` and `state` set to `expired`, then `apply` (it replaces an offer by id; `correct` has no offers switch) |

All of these are `python "<scripts>\curation_tools.py" correct --folder "<listing>" ...`. `python "<scripts>\curation_tools.py" correct --help` lists the switches.

- `--who` takes the name as the report prints it, a name from the sheet, or an id. If it fits more than one person the command changes nothing and lists them: pick by id.
- `--set` takes `price_reaction`, `price_asked`, `interest`, `offer_intent`, `themes`, `liked` (comma separated), `next_followup_date`, and the person's own fields such as `feedback_safe`, `status`, `brokerage`, `kind`, `name_short`.
- After `--set`, the command prints every sentence the report prints about that person. A changed count with unchanged wording is a contradiction the seller will see: fix the wording too. Rewording the whole sentence is safer than cutting words out of it.
- `--remove` takes out each whole sentence that holds the words. If that would leave an entry empty, it refuses and asks for a `--reword`.
- New wording is held to the same rules as yours (section 8).
- A corrections file for `--file` can hold `people`, `entries`, `open_houses`, `merge`, `split`, `ignore_rows` and `next_week`.

**It is kept.** Everything a correction touches is marked as the operator's, with their words, and no later automatic pass overwrites it: `apply` skips it and says so. It holds every week from then on. One exception, by design: if the team later types a different value into that person's own sheet column, the newer sheet value is used, and a glance line says an earlier correction gave way.

Then rebuild with the issue's run line minus `--sheet` and `--as-of` (the NEXT line run_issue printed keeps every other switch; a bare `--folder` run would drop the photo, the glance lines, the brief and the sources), and replace the body of the same draft as `delivery.md` section 4 says. Tell the operator in one or two plain sentences what changed, never which command ran.

## 13. What will stop you

`apply` and `correct` save nothing, and the build stops, when a sentence a seller could read has a phone number, an email address, an access code, a first-person aside ("I", "I'll", "told me"), another street address, or an em dash or en dash. Reword and run again.

The page checks then fail the build (exit 30) for a harsh word in a comment, a comment in quote marks, a comment with no "as reported" label, a health, family or money word about a buyer, and any wording that recommends a price or says what silence on price means. When one fails, the fix is almost always in your wording: change it with `correct --reword` and rebuild. Do not reach for `--waive` or `--allow-term`. Those are for a case Graeham has looked at and decided.

The code cannot spot a full name hidden in a sentence or judge whether a remark is too personal. That part is on you.
