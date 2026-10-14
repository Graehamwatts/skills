# Report structure: what each part is for

What the seller sees, top to bottom, why each part is there, and how the email differs from the link copy and the PDF. How each number is counted is in `counting-rules.md`; the page code is `scripts\sr_render\` (`assemble.py` `ORDER` fixes the order).

## Contents

1. The reader and the look
2. The files one build writes
3. The page, top to bottom
4. The email against the link copy and the PDF
5. When the email runs long
6. What a page never carries

## 1. The reader and the look

A homeowner reads this on a phone, often between other things, and forwards it to family. So the top must answer "how did this week go" in one screen, and everything under it is there for the reader who wants to check. Graeham's aim: show the seller the team is following up with everyone and what each person said, so the stack of reports is the record he points to in a price conversation. The report never makes that case itself.

The look is Graeham's CMA system (`cma-generator`): black #1A1A1A, gold #C5A55A, cream #F5EFDC, white cards, Montserrat for headings and Inter for body, with system fonts behind them because Gmail does not load web fonts. One column, 680 px at most, 16 px gutters, nothing under 12 px, every link at least 40 px tall. Section headers are gold capitals on a black bar. All of it lives in `sr_render\tokens.py`; brand facts come from `identity.json` at run time.

## 2. The files one build writes

| File | What it is | Who gets it |
|---|---|---|
| `email.html` | The report as designed, with the masthead photo and working call and web links | The checks, the phone pictures, and any mail tool that keeps HTML as it is |
| `email_gmail.html` | The same words, drawn for the Gmail connector: no photo, phone and website as plain text, status chips on table cells (`delivery.md`, section 2) | The body of the Gmail draft |
| `link.html` | The copy that can be forwarded or published: everyone in full, no offer price, terms or offer agent, marked noindex | Published only on Graeham's word |
| `print.html`, `report.pdf` | The link copy laid out for Letter paper, printed by Edge | Attached or filed only when asked |

The email must stay under 95,000 bytes, because Gmail clips a message near 102 KB and hides the rest behind a link the seller will not tap.

## 3. The page, top to bottom

**The summary on top**

| Part | What it says | Why |
|---|---|---|
| Masthead | Wordmark, issue number and date, the address, the photo (never in the Gmail-safe copy) | The seller knows at a glance which report this is in the stack |
| Greeting and "This week in brief" | "Hi Pat and Sam," then a few short sentences: what happened this week, in counts. Graeham may supply his own words for one issue (`--brief-file`, email only) | The one part a busy seller always reads |
| "Since the week closed" | Anything dated after Sunday, one line per person per day, counted next week | Monday's news is not lost, and no week is ever shown half done |
| The numbers table | Showings, disclosure packages, open house visitors, follow-ups we made, replies we received, offers, and online views when recorded; this week, last week, since we listed. Then one line: "We contacted X of Y people. Z answered. N still waiting." | The same rows every week, so one report lays beside the next |
| The weekly charts | Showings and new disclosure packages, every week since listing, this week marked; online views in their own chart when recorded | A quiet stretch and a busy one are both visible, honestly |
| "What people are saying" | Price first, always, as three plain counts (said too high, said fair or good, gave no view) out of the people who gave feedback; then the other points people raised, ranked by people; then what they liked | Price is never hidden and never argued; the seller sees how many people said what |

**The details** (a black band, then the lists)

| Part | What it says | Why |
|---|---|---|
| Offers and likely offers | Every offer with its state (received, countered, accepted and so on), then people who said an offer is possible, while contact is fresh (21 days) | The first thing a seller looks for. Email only |
| Agents who showed the home | Key-box showings plus tours agents told us about. Inquiries are never showings | Matches the Showings row |
| People on the disclosure package list | On the list, sent, opened, kept apart | Matches the Disclosure packages row |
| Open houses | Each session (date, host, count in the host's own unit, recap), then the visitors we know of | Hosts are on our side of the table and are not counted as contacts |
| Other inquiries | Anyone else we follow up with | Printed only when there is someone |

Each person is shown in full once, in their first list; elsewhere they are a one-line pointer. In the email this week's people get a full entry (what they did, "Said:" as reported to our team, "Offer:", "Follow-up:" with every date and channel, "Responded:"), and earlier people one line each under "Earlier". A closing line points to the complete record: a button when a link copy is published, otherwise an offer to send it.

**The optional sections**, each only when its file holds something for this issue (`extras.md`, `market-and-marketing.md`): Similar homes nearby (what changed, then the watch list), Time on the market (this home against recent sales), Online ads and marketing (each channel's status word).

**Next week**: what the team will do, in order. Never a suggestion to the seller, never anything about price.

**The record since we listed** (a black band): follow-up since we listed, "Every week in one table", every price comment on record, the record at each list price, "How we count" (the definitions a seller needs), and the footer with Graeham's contact lines and the Compass disclaimer from `identity.json`.

## 4. The email against the link copy and the PDF

- **Offers.** The email carries offer prices, terms, the offer agent's name, and the "Offer:" line on each entry. The link copy and the PDF carry none of it, and drop any sentence that says who may be weighing an offer, because a link can be forwarded to anyone, another buyer included.
- **People.** The email shows this week's people in full and earlier people in one line. The link copy and the PDF show everyone in full.
- **Brief.** A brief Graeham wrote himself prints in the email only; the link copy and the PDF use the counted brief.
- **Points raised.** "Still deciding" is left out of the link copy.
- **Photo, links.** The Gmail-safe copy has no photo and no call or web links; the other three keep them.

## 5. When the email runs long

The fit ladder (`sr_render\fit.py`) steps detail down until the email fits, in this order: the optional sections shorten first (similar homes keeps only what changed, the views chart moves to the complete record, prepared ad channels join one sentence), then the record half, the pointers, earlier open house sessions and the one-line entries. The numbers table, the three price rows and this week's people go last, and every person keeps an entry in every list they belong to, so heading counts still equal entries. The Gmail-safe copy is drawn at the same level as the email so the two say the same words. `run_issue.py` prints the level used and the manifest keeps it (`flags.fit_level`).

## 6. What a page never carries

A price recommendation, a suggested number, or a sentence about what silence on price means. A comment in quote marks. A phone number, email address or code from the notes. The address of another listing outside the similar homes section. A notice, banner, review table or panel of any kind, or any word about how the report was built. A dollar amount of ad spend. An em or en dash. The checks fail a page that has any of these.
