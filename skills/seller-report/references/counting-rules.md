# Counting rules

One definition for every number the seller report prints. A new operator and a new Claude session must count
the same way, so nothing here is left to judgment. The same rules exist as code in
`scripts/sr_contract_counts.py` (`recount`), and `validate_ledger` refuses a ledger whose stored numbers do
not match its rows. If a rule here and the code ever disagree, that is a bug: fix both together.

The report states what happened and what people said. It never recommends a price, never suggests a number,
and never explains what silence on price means, in either direction.

## 1. The week

- A week runs **Monday to Sunday**. The report is issued on a Monday and covers the week that just ended.
  `report.week_start` is that Monday, `report.week_end` the Sunday, `report.report_date` the Monday after.
  Built late (say on a Thursday), it still covers the same week and carries the same Monday date.
- **Week 1 is the week the home was listed**, even if it was listed on a Friday. `days_listed_in_week` says
  how many days of that week the home was on the market, so a short first week is never read as a slow one.
- **Every week since the list week is kept**, with zeros. A quiet week is a row of zeros, not a missing row.
  Weeks are never renumbered. This week is compared with last week, not with the last busy week.
- **The partial current week is never shown as a week.** Anything dated after `week_end` (usually the Monday
  the report is built) goes in `report.since_week_closed` and is printed in its own "Since the week closed"
  box. It is in no weekly count, no total, no tally and no chart. It will be counted next week.
- **Days on market** is the number of calendar days from the list date to the day named: the list date is
  day 0. The masthead uses the report date. Weekly rows use the Sunday.
- A date typed without a year is placed by the listing's life (the first matching date on or after the list
  date), never by today's year.

## 2. Who counts as a contact

- **Contacts** are buyer-side people our team follows up with directly: agents, buyers with no agent, and
  open house visitors who became a lead.
- **An agent and that agent's buyer count once.** A buyer an agent shared the disclosure package with (an
  "Invited by" row) is listed under the agent (`represented_by`), has status `through_agent`, and is in no
  contact count. Follow-up with that buyer is the follow-up with their agent: a call, text or email date typed
  on the buyer's own row is read into the agent's follow-up log and counted there, once.
- **Open house hosts are on our side of the table.** A host who brought no buyer of their own is
  `team_side`: not a contact, their messages are not follow-up, their recap is not a buyer conversation. A
  host who also showed the home to a buyer of their own is counted as an agent like any other.
  `totals.team_side_set_aside` says how many people, messages and reply days were set aside, and the page
  says so.
- An open house visitor nobody can reach except through the host is a contact with
  `reached_through: open_house_host`. A package sent through the host counts as one follow-up, and the page
  says the team has not reached that person directly.
- Open house visitors with no lead are counted only in open house traffic.
- One person is one contact, however many tabs they sit on. Two different agents can shorten to the same
  "First L." label, so people are matched by id, never by label.

## 3. Showings, tours and inquiries: three kinds, never merged

| Kind | What it is | Field |
|---|---|---|
| Key-box showing | A showing with a key-box record: a row on the team's key-box showing log, or a key-box notification | `keybox_showings` |
| Agent-reported tour | A tour we know about only because the agent or buyer told us. No key-box record | `agent_reported_tours` |
| Inquiry | A call, email or showing request with no tour: a question, a cancelled or postponed showing | `inquiries` |

- The three are separate numbers in every week and in the totals. They are **never added into one
  "showings" number**. A printed number always names its kind ("2 key-box showings", "1 tour reported by an
  agent").
- When a listing has no key-box record to read, `keybox_showings` is null and prints as "not recorded". It
  is not zero.
- A key-box entry made by an open house host opening up is not a showing.
- A row with a phone number and no tour is an inquiry, even if it sits on the showing tab.
- A tour listed with no confirmation that it took place still counts and is flagged (`confirmed: false`,
  `totals.tours_unconfirmed`). The page says how many.
- A row on the showing tab with no showing date is read as an inquiry, never a tour, until the notes or the
  operator say a tour took place.
- Tours and inquiries are counted for everyone who is not team side, a buyer listed under an agent included.
  Only the contact counts leave those buyers out.

## 4. Disclosure package: three states

| State | Engagement type | Meaning |
|---|---|---|
| On the list | `disclosure_on_list` | The person is on the disclosure tab. The log does not say whether a link was sent or the package opened |
| Link sent | `disclosure_link_sent` | Our team sent the package link, by the date in the notes |
| Opened | `disclosure_opened` | The disclosure platform shows the person opened it |

- `disclosure_contacts` is the number of contacts tied to the package in any of these ways. Each person
  counts once, in the week of their first dated package entry (`weeks[].disclosure_contacts_new`).
- `disclosure_sent` and `disclosure_opened` are separate numbers. They are never reported as one "have the
  package" figure.
- **When sent or opened is not recorded** (`report.tracking` is false, or a week could not be checked), the
  field is null and the page prints "not recorded". Print the people on the list instead.
- Buyers an agent shared the package with are `totals.disclosure_shared_buyers`. They are a sign of interest
  and are stated on their own line, not added to contacts.
- A host's own view of the package is team side and is not counted.

## 5. Follow-up: days first, touches second

- A **follow-up** is one call, voicemail, text or email our team made to a contact
  (`direction: outbound`). Sending the disclosure link or showing instructions counts.
- **One per channel per day.** A voicemail, a text and an email to one person on one day are three
  follow-ups. A call that went to voicemail is one (the voicemail), not two.
- Every person's follow-up is stated **in days first, then touches**: "6 days of follow-up (6 calls, 6
  texts)". A voicemail is a call in that line. When the log does not give the channel for every touch, the
  bracket says "(8 follow-ups)". Use `sr_contract.fmt_followup`.
- **Separate days** are calendar dates. `totals.outbound_distinct_days` is the number of dates on which the
  team followed up with anyone, and can never pass the days on market. A week's figure can never pass 7.
  `totals.outbound_person_days` adds up each person's days and is not a count of days: never call it "days".
- A touch where the log does not say who called (`direction: unknown`) is not counted as a follow-up. It is
  reported as `touches_direction_not_recorded`.

## 6. Replies, answered, still waiting

- A **reply** is a day on which a contact answered us or got in touch: an inbound call, text or email, or a
  call of ours that reached them. **Once per person per day**, however many messages that day.
- **Contacted**: at least one call, text, email or conversation with that person is on record.
- **Answered** (`totals.replied`): they have answered our latest follow-up, or told us where they stand
  (status `replied`, `passed`, `writing_offer` or `offer_submitted`).
- **Still waiting** (`awaiting_reply`): our latest follow-up day is later than their last answer day, or
  they have never answered. Someone who answered once and has gone quiet since is "still waiting", not
  "never replied" (`awaiting_reply_answered_before` says how many).
- Someone who told us they passed stays passed. Later outreach to them (about a price change, say) is logged
  as follow-up and does not move them back to waiting.
- **3 or more tries** (`awaiting_reply_3plus_attempts`): people still waiting whose separate follow-up days
  **since their last answer** number three or more. It is not their days over the whole record.
- **Calls to a dead number.** A call that did not go through (`outcome: did_not_connect`) counts as a try
  and is shown as one that did not connect. When the number on file is out of service
  (`phone_out_of_service`), that person's calls and texts are shown as going to a number that does not work.
- **Quiet**: no contact in either direction for more than 30 days as of the week end. Exactly 30 is not
  quiet. People still waiting are split into "tried in the last 30 days" and "quiet for more than 30 days".

## 7. Open houses

- One session is one entry. A two-day weekend is two sessions.
- Traffic is printed **in the host's own unit** (`counted_unit`: groups, visitors, guests, parties, people).
  A group is never turned into a number of people. When sessions on one listing used different units, the
  total is labeled as each host counted.
- A session with no count on record prints **"no count kept"** (`groups: null`). A session where nobody came
  prints 0. A week with no session prints "none held". These are three different things.
- `open_house_sessions_no_visitors` is counted from the rows (sessions with a count of 0), never typed.

## 8. What people are saying

- **The denominator is people.** `people_with_feedback` is the number of contacts who told us something
  themselves, at least once. Every count in this section is out of that number.
- A **conversation** is one person on one day. `conversations_with_feedback` may follow the people figure in
  brackets and is always labeled as conversations.
- A host's secondhand description of a visitor is not that visitor's feedback. Price remarks in an open
  house recap are listed on their own (`open_house_price_remarks`) and are outside the tally, because the
  other visitors at that session cannot be counted.
- **Price is always a row**, with three plain counts that add up to the denominator: said the price is too
  high, said the price is fair or good, did not bring up price. When a person spoke about price more than
  once, their latest remark decides their row.
- `price_asked` records whether price was asked directly. The page may state it as a count ("asked directly:
  6 of 9"). It adds no sentence about what an answer or a silence means.
- **Themes can overlap.** One person can raise two topics, so theme rows can add up to more than the
  denominator, and the page says so. Rows are ranked by people. `new_this_week` counts people who raised
  that topic for the first time this week. Price is not a theme.
- **What people liked** is counted the same way (`liked_tally`).
- Comments are the team's paraphrase, labeled "as reported to our team". Harsh wording is never quoted. The
  substance stays ("gave negative feedback and specifically said the price is too high") and the entry is
  flagged `softened`.
- **How a note is counted is decided silently.** Claude reads each note and decides what it says. Nobody is
  shown that reading or asked to confirm it, and it never delays a report. When the operator reads the report
  and says it is wrong ("Jordan never said it was overpriced"), the correction replaces the reading, the counts
  follow, and the correction holds in every later week. A value from one of the sheet's own columns is used
  as typed. Neither is ever overwritten by a later automatic pass.

## 9. Anything per list price

- The record at each list price is **split by the date of each event** against `listing.price_history`:
  tours, inquiries, open house sessions, offers, follow-ups, conversations and price remarks all go to the
  price in effect that day (`price_periods`).
- The weekly table keeps whole weeks. `weeks[].list_price` is the price in effect on most days of that week
  (a tie goes to the later price), and the page says what the price-change week holds at the new price.
- An event dated before the list date belongs to the first price. An undated event is in the totals and in
  no week and no price period, and the page says how many there are.

## 10. Offers

- An offer is counted once, on the date it was received. A counter, an acceptance or a withdrawal changes
  its `state` and is not a new offer. States: received, countered, accepted, declined, withdrawn, expired.
- Percent of list uses the list price on the day of the offer.
- Offer price, terms and the offer agent's name appear in the email only. The link copy carries none of
  them and never says who may be weighing an offer.
- **The 21 day rule.** Someone who said an offer is possible is a live lead only while there has been
  contact in the last 21 days. After that they are shown as earlier interest, never as live
  (`offer_watch[].lead_state`). A person who passed, or whose offer is already in, is not a lead.
- A person is never shown both as passed and as an active lead. Status `passed` and interest `passed` go
  together.

## 11. Dates

- A date read from a note instead of a date cell, or placed by row order, is `approximate` and is printed
  with "about" (`sr_contract.fmt_date(d, approximate=True)`). The page says how many tour dates are
  approximate.
- A missing date is null. The event is in the totals and in no week.
- An entry is dated by when it happened, not by when a later follow-up was logged on the same row.

## 12. Market and marketing (optional sections)

- Every market number carries its window: `as_of`, `data_through`, the scope and the sample. Windows are not
  mixed in one sentence. Days are counted from the list date to the day the sale first went under contract.
- A marketing channel is called running only if it is on **and was checked for this issue**. Anything older
  prints its state with the date last checked.

## 13. What Claude is unsure about

It is never in the report. It goes in the chat reply that hands over the draft, as "Worth a glance before you
send": at most five short plain lines, most important first (`notes_for_operator.json`). Examples: could not
tell whether a tour took place; a comment was toned down; a count here differs from the team's status email,
and why. The independent checks (numbers recounted, privacy, tone, feedback only, brand, hygiene, email
safety, wrong file) run silently before anything goes in a draft. The operator hears about a check only
when it fails, in plain words.

## 14. Do not repeat: five errors caught in a hand-built report

Graeham found these in one hand-compiled weekly report. Each is now impossible or caught by the validator.

1. **Miscounted empty open houses.** The report said three open houses had no visitors. The log had four.
   Counts are computed from the session rows, never typed.
2. **One lead shown two ways.** A buyer who had passed also appeared as an "active warm lead". A person has
   one status. Passed people are never in the offer watch.
3. **A guess stated as fact.** The report said which other unit buyers were comparing the home against,
   which nobody had told the team. Only what was said goes in. When a buyer went elsewhere the report says
   "chose another property" and never names the other listing.
4. **Mixed time windows.** The market section put figures from different date ranges side by side as if
   they were one. Every number names its window.
5. **A headline count that double counted.** "7 people" mixed agents, their own buyers and open house
   visitors. An agent and that agent's buyer count once, hosts are team side, and visitors with no lead
   are only in open house traffic.

Two more from the same review, for the same reason:

- "2 showings" had to become "2 completed key-box showings", and a phone contact had been counted as a tour.
  See section 3.
- "4 agents have the disclosure package" counted two links that were sent and never opened. See section 4.

## 15. Quick reference

| Printed as | Ledger field | Rule |
|---|---|---|
| Contacted X of Y | `totals.contacted`, `totals.contacts` | section 2, section 6 |
| Answered | `totals.replied` | section 6 |
| Still waiting, N after 3 or more tries | `totals.awaiting_reply`, `awaiting_reply_3plus_attempts` | section 6 |
| Follow-ups we made | `totals.touches_outbound`, `weeks[].touches_outbound` | section 5 |
| Separate days | `totals.outbound_distinct_days`, `weeks[].outbound_distinct_days` | section 5 |
| Replies we received | `totals.replies_inbound` | section 6 |
| Key-box showings | `keybox_showings` | section 3 |
| Tours reported to our team | `agent_reported_tours` | section 3 |
| Inquiries | `inquiries` | section 3 |
| New people on the disclosure package list | `weeks[].disclosure_contacts_new` | section 4 |
| Packages sent, packages opened | `disclosure_sent`, `disclosure_opened` | section 4 |
| Open house traffic | `open_house_groups` with `counted_unit` | section 7 |
| Price came up with N of M people | `pricing_tally` | section 8 |
| What people are saying | `themes_tally`, `liked_tally` | section 8 |
| At each list price | `price_periods` | section 9 |
| Offers | `offers`, `totals.offers_by_state` | section 10 |
| Buyers still deciding, earlier interest | `offer_watch` | section 10 |
