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

## 3. Showings, and what is never a showing

| Kind | What it is | Field |
|---|---|---|
| Key-box showing | A showing with a key-box record: a row on the team's key-box showing log, or a key-box notification | `keybox_showings` |
| Agent-reported tour | A tour we know about only because the agent or buyer told us. No key-box record | `agent_reported_tours` |
| **Showing** | Either of the two above. This is the Showings row a seller reads | `showings` |
| Inquiry | A call, email or showing request with no tour: a question, a cancelled or postponed showing | `inquiries` |

- **Showings = key-box showings + tours agents reported.** `showings` is that sum in every week, in every
  list price period and in the totals. It is the one number the top of the report prints ("Showings"), the
  bars of the week by week chart, and the "Shown" column of the weekly table.
- **An inquiry is never a showing.** It is not in `showings`, in any week or total, however the row was typed
  and whichever tab it sits on. The page says so under the numbers table.
- The two kinds of showing are still stored apart, and the page says how many of each make up the total when
  the listing has a key-box record ("Showings count key-box showings (2 since we listed) and tours agents
  told us about (1)").
- When a listing has no key-box record to read, `keybox_showings` is null and prints as "not recorded". It
  is not zero. `showings` is then the tours agents reported, and the page says the listing has no key-box
  record.
- **A combo lockbox leaves no electronic record.** Some listings (one in Oct 2026) have a combination
  lockbox, not an electronic key box, so there is no key-box record at all: `listing.json` has
  `tracking.keybox_showings: false` with a `tracking.lockbox` note saying so. A tab the team keeps by hand for
  showings (even one named after the key-box company) is a log of reported tours, read like any other tour row,
  not a key-box record.
- A key-box entry made by an open house host opening up is not a showing.
- A row with a phone number and no tour is an inquiry, even if it sits on the showing tab.
- A tour listed with no confirmation that it took place still counts and is flagged (`confirmed: false`,
  `totals.tours_unconfirmed`). The page says how many.
- A row on the showing tab with no showing date is read as an inquiry, never a tour, until the notes or the
  operator say a tour took place.
- Showings and inquiries are counted for everyone who is not team side, a buyer listed under an agent included.
  Only the contact counts leave those buyers out.

## 4. Disclosure package: three states

| State | Engagement type | Meaning |
|---|---|---|
| On the list | `disclosure_on_list` | The person is on the disclosure tab. The log does not say whether a link was sent or the package opened |
| Link sent | `disclosure_link_sent` | Our team sent the package link, by the date in the notes |
| Opened | `disclosure_opened` | The disclosure platform shows the person opened it |

- `disclosure_contacts` is the number of contacts tied to the package in any of these ways. Each person
  counts once, in the week of their first dated package entry (`weeks[].disclosure_contacts_new`). That is
  the "Disclosure packages" row: new people this week, last week, and everyone since we listed. It is also the
  count in the heading of the disclosure package list (section 15).
- When the listing records opens, the row carries a second figure, "N opened", under each number. It is never
  added to the first.
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
- **Open question (asked of Adrian, Oct 13, 2026): what a date in the sheet's Email, Call and Text columns
  means.** It may be the day our team made that call, text or email; the day someone typed the row in; or, at
  times, the day the agent called us. Graeham's own reading is that it is the day they called or entered it.
  It is also not known whether Adrian overwrites an earlier date with a later one. Until Adrian answers, keep
  the current reading: a date in those columns is a follow-up our team made on that day, except where the
  row's note says the agent called us, which makes it a reply (one listing, Oct 12, 2026: 15 older Call dates read
  as the agent calling us, so follow-ups since we listed read 290; read as our calls the total would be 305).
  Say which reading was used in "Worth a glance" whenever it moves a count, and change nothing until Adrian's
  answer is in. When it comes, record it here and drop this note.
- **The hand-written reports count differently.** The series the team wrote by hand before this skill counted
  cancelled tours, questions and open house hosts. This report does not (sections 2 and 3), so its totals are
  lower (one listing, Oct 12, 2026: 35 showings against 37, and 44 on the package list against 52 agents). When a
  seller or the operator asks why, that is the answer: the same people, without cancelled tours, questions and
  hosts.

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
  high, said the price is fair or good, gave no view on price. When a person spoke about price more than
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
- A marketing channel is called **running** only if it is on **and was checked for this issue** (on or after
  the last day of the report week). A channel that is on and was last checked earlier is **switched on**, with
  the day it was last checked. The other words are **prepared**, **on hold**, **not launched** and **ended**,
  and a switched-on channel may say when it is **scheduled to end**. No ad spend amount is printed.
- The online ads and marketing section prints only when a channel is on or something was checked for this
  issue. Otherwise it is left out.
- **Similar homes nearby** is a watch list of at most 8 homes, chosen once. Each issue prints what changed
  since the last check (new listing, price change, went pending, sold, taken off the market, back on the
  market) and then every watched home with its status, price and days, with the day the list was checked.
  - "N of the M homes we are watching changed" counts the homes whose change is not "none".
  - A change is dated by its own event. When two checks differ and no date explains it, the change is dated the
    day it was seen and printed with "by".
  - Price is the list price, or the sale price for a home that sold. Days run from the list date to the first
    accepted offer, the sale or the day the home left the market, and to the day of the check for a home still
    for sale.
  - The section exists only when the list was checked for this issue. Public street addresses are printed in
    that one section, as in a market analysis. Everywhere else the rule is unchanged: never where a buyer went,
    never another client's home.

## 13. What Claude is unsure about

It is never in the report. It goes in the chat reply that hands over the draft, as "Worth a glance before you
send": at most five short plain lines, most important first (`notes_for_operator.json`). Examples: could not
tell whether a tour took place; a comment was toned down; a count here differs from the team's status email,
and why. An optional lookup that was blocked or failed is always among the five: the report has no such
section and the operator should know why (`extras.md`, section 1). The independent checks (numbers recounted, privacy, tone, feedback only, brand, hygiene, email
safety, wrong file) run silently before anything goes in a draft. The operator hears about a check only
when it fails, in plain words.

## 14. The summary on top: the numbers table, the line under it, the charts

- **One table**, three columns: this week, last week, since we listed. These rows print in every issue, zero
  or not, so one report can be laid beside the next:

  | Row | This week and last week | Since we listed |
  |---|---|---|
  | Showings | `weeks[].showings` | `totals.showings` |
  | Disclosure packages | `weeks[].disclosure_contacts_new` (second figure: `disclosure_opened`) | `totals.disclosure_contacts` (second figure: `disclosure_opened_confirmed`) |
  | Open house visitors, in the host's own unit | `weeks[].open_house_groups` | `totals.open_house_groups` |
  | Follow-ups we made | `weeks[].touches_outbound` | `totals.touches_outbound` |
  | Replies we received | `weeks[].replies_inbound` | `totals.replies_inbound` |
  | Offers | `weeks[].offers` | `totals.offers` |
  | Online views, only when recorded | `weeks[].online_views` (second figure: `online_saves`) | `totals.online_views` |

- **One line directly under the table**: "We contacted X of Y people. Z answered. N still waiting."
  (`totals.contacted`, `contacts`, `replied`, `awaiting_reply`). When someone was reached only through an
  open house host the line says so in full: "We contacted 4 of 5 people directly and 1 through the open house
  host." When someone has not been reached at all, a second short line says how many.
- **The week by week chart** has a row for every week since the list week: showings and new disclosure
  packages. A quiet week keeps its row, this week is marked, and each value is printed beside its bar. When
  online views are recorded they get a chart of their own, and a week with no figure says "not recorded".
- **Online views** for a week are the sum of the portals that gave a figure that week (`ledger.online`). A
  week with no figure from any portal is null, never zero. A site shows a running count since the home was
  listed, so a week's figure is one reading minus the reading of the week before, and a site read for the
  first time gives no weekly figure yet. **Since we listed** is, site by site, the running count when one was
  read, otherwise the weeks added up; it is also the last line of the Views column in the weekly table. The
  page names the sites and the day they were read, and says each site counts views its own way.

## 15. The details: people grouped by what they did

The lists match the numbers on top and the way the team's sheet is kept.

| List (`contacts[].lists`) | Who is in it | The count in its heading |
|---|---|---|
| `showings`: Agents who showed the home | Anyone not team side with a key-box showing or a reported tour | `totals.lists.showings` |
| `disclosure`: People on the disclosure package list | A person we follow up with who is on the list, was sent the package or opened it | `totals.lists.disclosure`, always equal to `totals.disclosure_contacts` |
| `open_house`: Open house visitors we know of | Anyone not team side who came to an open house and left a name | `totals.lists.open_house` |
| `other_inquiries`: Other inquiries | Someone with an inquiry who is in none of the three lists above, and anyone else we follow up with | `totals.lists.other_inquiries` |

- **The count in each heading equals the number of entries beneath it.** Both equal the number of people who
  belong in the list, counted from their rows. The ship gate counts all three again and stops the build when
  they differ.
- **A person who did two things is listed once in full.** Their first list, in the order showings, then
  disclosure packages, then open house, is where they are shown (`contacts[].primary_list`). In every other
  list they belong to they are a one-line pointer ("Odalys V.: see Agents who showed the home"). A pointer is
  an entry and is in the heading count. Nobody is shown in full twice.
- **Everyone we follow up with has exactly one such place.** The people shown in full or in one line across
  the lists are the `totals.contacts` people, each once.
- **This week in full, earlier people in one line each.** A person is active in the report week when the log
  holds a touch in either direction, something they told us, or something they did, dated inside the week
  (`contacts[].active_this_week`, `totals.lists_active_this_week`). In the email they get a full entry: short
  name and brokerage, what they did and when, "Said:" (as reported to our team), "Offer:", "Follow-up:" with
  every date and its channel, "Responded:". Everyone else gets one line under an "Earlier" subhead: the name,
  what they did, where it stands, the last contact. **The link copy and the PDF show everyone in full.**
- **"Offer:"** is one of: offer received, writing one, possibly, not yet, no, not discussed
  (`contacts[].offer_word`). An offer on file comes first, then what the person said. "Not yet" is someone who
  said no offer for now and has not passed. The link copy prints no "Offer:" line for anyone.
- **"Responded:"** is "Yes" with the date of their last answer, or "No reply yet after N tries" (section 6).
  There is no separate "still waiting" section: waiting is a status on the entry, and the line under the
  numbers carries the count.
- **Not entries:** a buyer whose only tie is a package their own agent shared is stated as one count under
  the disclosure list (`totals.disclosure_shared_buyers`). Open house hosts are on our side of the table and
  are in no list.
- **A list with no entries prints one honest sentence**, never an empty table. "Other inquiries" is printed
  only when there is someone to list.
- **Open houses** list each session (date, host, the count in the host's own unit, the recap) before the
  visitors we know of. In the email, sessions before this week take one line each.
- **When the email runs out of room** (`sr_render/fit.py`) the optional sections give way before anything about
  people: similar homes nearby keeps what changed and says the homes that did not change in one sentence, the
  chart of online views is left to the complete record, and prepared ad channels join the one sentence for
  channels that are not on. Then the record half gives way, the pointers become a run of names, and the
  one-line entries say less. Every person keeps an entry in every list they
  belong to, so the heading count still equals the entries.

## 16. Do not repeat: five errors caught in a hand-built report

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

- A phone contact had been counted as a showing. An inquiry is never a showing, and the page says what the
  Showings number counts. See section 3.
- "4 agents have the disclosure package" counted two links that were sent and never opened. See section 4.

## 17. Quick reference

| Printed as | Ledger field | Rule |
|---|---|---|
| Contacted X of Y | `totals.contacted`, `totals.contacts` | section 2, section 6 |
| Answered | `totals.replied` | section 6 |
| Still waiting, N after 3 or more tries | `totals.awaiting_reply`, `awaiting_reply_3plus_attempts` | section 6 |
| Follow-ups we made | `totals.touches_outbound`, `weeks[].touches_outbound` | section 5 |
| Separate days | `totals.outbound_distinct_days`, `weeks[].outbound_distinct_days` | section 5 |
| Replies we received | `totals.replies_inbound` | section 6 |
| Showings | `showings` (key-box showings plus reported tours) | section 3 |
| Key-box showings, tours agents told us about | `keybox_showings`, `agent_reported_tours` | section 3 |
| Inquiries | `inquiries` (never a showing) | section 3 |
| Disclosure packages (new people) | `weeks[].disclosure_contacts_new` | section 4 |
| Online views, saves | `online_views`, `online_saves` (since listing: `sr_contract.online_totals`) | section 14 |
| N of the M homes we are watching changed | `nearby.homes[].change` | section 12 |
| Running, switched on, scheduled to end | `marketing.channels[]` (`status`, `checked`, `ends_on`) | section 12 |
| The count in a list heading | `totals.lists` | section 15 |
| Offer: | `contacts[].offer_word` | section 15 |
| Packages sent, packages opened | `disclosure_sent`, `disclosure_opened` | section 4 |
| Open house traffic | `open_house_groups` with `counted_unit` | section 7 |
| Price came up with N of M people | `pricing_tally` | section 8 |
| What people are saying | `themes_tally`, `liked_tally` | section 8 |
| At each list price | `price_periods` | section 9 |
| Offers | `offers`, `totals.offers_by_state` | section 10 |
| Buyers still deciding, earlier interest | `offer_watch` | section 10 |
