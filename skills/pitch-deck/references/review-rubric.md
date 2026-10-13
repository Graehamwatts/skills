# Review rubric

Read this before reviewing an existing deck, and when scoring your own draft before calling it final.

The rubric measures craft and evidence: whether the deck says what the company is, whether its claims can be checked, and whether its reader can take it in. It does not predict whether anyone will invest. Say so in every review.

## Contents

1. Before scoring
2. The gates
3. The 100 points, by reader
4. What earns the points
5. Reading the score
6. Red flags
7. Questions the deck does not answer
8. The three weakest claims
9. The review, in a fixed order
10. Rules for the reviewer

---

## 1. Before scoring

**Open the real file.** Score the PDF, the slides or the slide images, not a description of them. A generous summary of a thin slide scores well, and the reader will never see the summary.

**When only pasted text is available**, review it, say that the review covers the words and not the rendered slides, and mark the look and legibility line "not scored". Report the score against the points still available (94 on the investor column when line 11 is not scored) and as a percentage. Do not rescale the other lines. The bands in section 5 then apply to the percentage. Gate 6 is "open", because there are no slides to render.

**An outline is not a deck.** For an outline or a deck prompt with no slides yet, use Import mode in `SKILL.md`. Do not score it.

**Inventory every slide first.** Before judging anything, list for each slide: its number, the first line in the file's text order, the headline as it renders, any text set larger than the headline, the visual, and every number on it. Measure the sizes. By eye a headline looks like the largest line even when a figure beside it is twice its size. For a PDF, `scripts/deck_inventory.py` prints the text order and the sizes and writes the page images. The inventory catches what a read-through misses: a small category tag that a text-order reader takes as the title, or a figure three times the size of the claim.

A word count for each slide is not required. The script prints one as a pointer to crowded slides. Text inside a screenshot or a mock screen is part of the visual and does not count against the 40 to 70 word body budget.

Note the file's name and size as well. A sent deck is named with company, stage, month and year, and is small enough to email.

**Name the reader and the stage.** Pick the column: an investor reading a sent deck, a program reviewer, or a live audience. A deck built for one fails as another, so score it for the reader it is going to. If nobody has said, state the assumption at the top.

**Name the main advantage.** Before scoring, say which claim is the deck's main advantage: the one the deck returns to on the most slides, and that answers the two tests in `slide-by-slide.md`, section 6 (why an established company cannot follow, and what grows with every customer). Line 3 scores whether that claim has a slide of its own. When the founder has ranked their top points, use their ranking.

**Say the weighting in one line.** For example: "Scored as a sent seed deck. For software sold to small businesses, the lines that matter most are the price, what it replaces, the proof and the ask."

**Say what the review does not cover.** Valuation, deal terms, legal questions and a later-stage metrics audit go to a person qualified to answer them.

## 2. The gates

Any one of these means the deck is not ready to send, whatever it scores.

| Gate | Tripped when |
|---|---|
| 1. An unsourced number or claim | A number, customer, result or partnership appears with no source line, no time window and no "Estimate" label, or the founder cannot say where it came from. Placeholder text left on a slide trips this gate too |
| 2. An unchecked ranking claim | "First", "only", "best", "leading", a category crown, or a universal claim about rivals ("no other tool", "competitors cannot") appears with no prior-art check behind it |
| 3. Present tense for what does not run | A capability is shown as working that the claims ledger, the product itself or the deck's own Done, Now, Next strip says is not. A "Sample data" label covers a screen. It does not cover a sentence or a tick |
| 4. Arithmetic that does not reconcile | The market sum, the price or the ask fails its own arithmetic, or the slides disagree with each other |
| 5. An unsourced statement about a named competitor | A named company is described with no first-party source and date, or a product is called by a name its owner has retired |
| 6. Not rendered and read | Nobody has looked at every slide as it renders |

**Check the claims before marking the gates.** Gates 1, 2, 4 and 5 cannot be marked until the sums are recomputed and the pages read. At the least, check:

- every sum on the deck, and whether the same price and the same counts appear on every slide;
- every outside number that sits in a headline or is set large;
- every ranking word and every universal claim about rivals;
- the two or three competitors whose own pages come closest to what the company claims, and the name each product carries today.

With a search tool, do these yourself. List what was checked and what was not, so the founder knows what each "clear" rests on.

Mark each gate **tripped**, **clear** or **open**. Use "open" when it depends on something the deck cannot show, such as whether a feature really runs, and write the question for the founder.

For each tripped gate give the number of instances, and say whether the fix is wording the reviewer can supply or a fact only the founder has. One appendix row that cites trade press and an invented customer both trip a gate. The founder needs to know which kind they have.

## 3. The 100 points, by reader

| # | What is scored | Investor, sent deck | Program reviewer | Live audience |
|---|---|---|---|---|
| 1 | What the company is, at a glance | 10 | 15 | 12 |
| 2 | The headlines alone carry the argument | 10 | 12 | 6 |
| 3 | Story, order, one point per slide | 10 | 8 | 12 |
| 4 | Evidence | 20 | 20 | 16 |
| 5 | Proof and stage | 8 | 15 | 8 |
| 6 | Business model and price | 8 | 4 | 6 |
| 7 | Market arithmetic | 6 | 0 | 4 |
| 8 | Competition | 6 | 2 | 4 |
| 9 | The ask | 8 | 8 | 6 |
| 10 | Tone and voice | 8 | 8 | 10 |
| 11 | Look and legibility | 6 | 8 | 8 |
| 12 | Fit to being spoken | 0 | 0 | 8 |
| | Total | 100 | 100 | 100 |

The program reviewer column moves points from market and competition to clarity and proof, because that reader is deciding whether this is a real product company. The live column takes points from the headline skim and gives them to how well the deck works behind a speaker.

The weights are this skill's judgment, not a measured standard. Change them when a reader has published what they score, and say that you did.

**Later stages.** The rubric is built for pre-seed and seed, where a deck is written to win a meeting. From Series A on a deck has to survive diligence. Months of history and the cost of winning a customer carry far more weight than these lines give them. Score what the rubric covers and say plainly what it leaves out.

## 4. What earns the points

Points shown are for the investor column. For another column, work out the share of the line earned and multiply by that column's weight. Give partial credit in proportion: if 9 of 13 slides have a claim as their largest line, the first test of line 2 earns 9/13 of its points.

Tie every score to something on a slide. Quote it. A test that depends on an open gate earns 0 and is marked pending, with the points it could earn.

**1. What the company is, at a glance (10)**
- 4: The cover's largest line says what the company makes and for whom, in verbs. No slogan stands in for it. A tagline may sit beneath it, smaller.
- 3: A reader could describe the product to someone else after the first two slides.
- 3: The founder, their standing and the stage are on the cover. The stage is one small, exact label.

**2. The headlines alone carry the argument (10)**
- 5: The largest line on every main slide is a claim. No category label is the title. Take half a point off when most slides carry a category tag above the headline, even a small one.
- 3: Read in order, the headlines give the thesis in under a minute: what it is, why it matters, why it is believable, what is asked.
- 2: Each headline is one sentence, sits in the target range for the deck kind (8 to 12 words sent or application, 4 to 8 live), and is something the founder would say out loud.

A figure set larger than the headline is read first. Count that slide as passing the first test only when the figure is the number the headline is about, with its unit and its kind in the same glance.

**3. Story, order, one point per slide (10)**
- 3: A pitch order, not the order of the company's website.
- 3: The main advantage has a slide where nothing else shares the body, and each of the founder's other top points has a slide of its own. Give 1 of 3 when the advantage is the headline and other points share the slide, and 0 when it is one bullet in a list.
- 2: One point per slide. No two slides make the same point. No topic takes more than three.
- 2: The length fits the deck kind, and likely questions are answered in a short appendix.

**4. Evidence (20)**
- 5: Every number shows its kind: a source line, a time window for the founder's own, or the word "Estimate".
- 3: Sample screens and estimates are labeled as such.
- 4: At least one real case and one real number from the founder's own use. Real screens wherever the product exists.
- 4: No ranking words, no universal claims about rivals, and no picture that ranks.
- 4: Present tense only for what runs.

**5. Proof and stage (8)**
- 3: Progress has a start date, and each number has a time window.
- 2: Who builds the product is stated plainly.
- 2: A dated Done, Now, Next strip. The stage is spelled out there and appears elsewhere only as the short cover label.
- 1: Nothing from the never list: a waitlist alone, pipeline, logos, gains nobody measured.

**6. Business model and price (8)**
- 2: One model, in one sentence.
- 3: A price or a range the founder has set, on the slide. An imported or proposed figure earns 0.
- 2: The price holds against cost to serve, with the working in the appendix or on file.
- 1: The slide shows what the product replaces and whose budget pays.

**7. Market arithmetic (6)**
- 3: Customers times price, with the working shown, using a sourced count and the same price as the business model slide.
- 2: A named first segment, and what follows it.
- 1: No lifted total, no one percent claim, no rings without arithmetic.

**8. Competition (6)**
- 2: Real alternatives by kind, doing nothing included, each with what it leaves undone.
- 2: The established-company question is answered: concede, then claim.
- 1: No tick grid. Any table in which the company's column is all ticks or all filled while every other column has blanks is a tick grid, whatever the other cells say. Any map meets the four conditions in `slide-by-slide.md`.
- 1: Named competitors are in the appendix with source and date.

**9. The ask (8)**
- 3: A definite request: one amount and its instrument, or three specific requests that are not money.
- 2: A countable milestone with a date.
- 2: The arithmetic reconciles with the price and the market slides.
- 1: It ends on a next step the reader can say yes to.

**10. Tone and voice (8)**
- 3: No line about what the product does not do or what the company lacks.
- 2: No consultant words and no unexplained product names.
- 2: It sounds like this founder: the words of their trade, their own cases.
- 1: No hype and no punctuation tics.

**11. Look and legibility (6)**
- 2: It looks like the company, not like a template.
- 2: The headline is the largest text, or the one larger figure passes the test under line 2. Large type, strong contrast, readable at half zoom on a laptop and on a phone.
- 1: Designed rows, not a default bullet list. One visual per slide. Consecutive slides do not share one layout.
- 1: No paragraphs. Nothing clipped or overlapping in the rendered slides.

**12. Fit to being spoken (live only, 8)**
- 3: No slide can be understood without the speaker.
- 2: The spoken opening is a statement about the company, not an introduction.
- 2: The talk fits its slot at an unhurried pace and lands three points.
- 1: There is a note for every slide.

## 5. Reading the score

| Score | Meaning |
|---|---|
| 90 or more, no gate tripped | Ready to send |
| 80 to 89, no gate tripped | Fix the listed lines, then send |
| Under 80 | The weak sections need the founder's input, not better wording |
| Any gate tripped | Not ready, whatever the score |
| For investors: a zero on "a price or a range" (line 6) or on "a definite request" (line 9) | Not ready to send, whatever the total |

The last row exists because the gates test honesty and nothing tests completeness. Price and ask together are 16 points, so a deck with neither could otherwise read "fix the listed lines, then send". A reader cannot respond to a deck that names no price and asks for nothing definite.

When a line is not scored, apply the bands to the percentage of the points still available. A gate marked open is a question the founder must close before sending. Report it as "N gates open" beside the score.

A low score on evidence, proof, price or the ask cannot be written away. Those lines improve only when the founder supplies a real number, a real case, a decision or a screenshot. Say that directly, so nobody spends a day polishing adjectives.

Two passes over the same deck can differ by about five points, because several tests bundle more than one condition. Compare versions scored the same way, and read a change of under five as no change. When reviewing a second version, show both scores side by side and say what improved and what got worse.

## 6. Red flags

Scan for these after scoring. Each one that appears goes in the review with the slide number.

**Whole deck**
- A category label is the largest line on a slide.
- A category tag above the headline, at any size.
- The first text line of a page is a category tag, or a word in the text layer is split by letter-spacing.
- Text set larger than the headline that is not the number the headline is about.
- More than 20 slides, or a sent deck under 8.
- The slides follow the website's menu.
- The same deck is being used for email and for the stage.
- An adjective where a number belongs: "strong", "rapid", "massive", "significant".
- A line about what the company does not have.
- A product name or a named "pillar" the reader was never given, or a product called by a retired name.
- Placeholder text left in.
- A file with a generic name such as "deck.pdf", or too large to email.

**Problem and solution**
- A statistic in place of a pain.
- Two problem slides.
- A feature list with no screen.
- Technology before the customer.

**What changed**
- No dates. A trend that applies to every company.

**Example**
- A hypothetical customer. A saving nobody measured. "Up to" before a percentage.

**Proof**
- Adjectives with no numbers. A hand-picked time window. A cumulative chart.
- Signups shown as customers. Pilots or letters of intent worded as usage.
- Large percentage growth on a tiny base. A metric with no date.
- A quote with no name. "Validated" over an estimate.
- A founder's career total set large enough to read as the product's result.

**Market**
- Only a total. One percent reasoning. Data with no year. Neighboring markets added in.

**Competition**
- "No competitors." Only small rivals listed. A tick grid, including one with text in the rivals' cells. A map with the company alone in the best corner.
- A universal negative: "no other tool", "competitors cannot", "nobody else".
- Difference on price alone. No answer for an established company copying the feature.

**Business model**
- No price. Several models at once. Tiers with no cost check. A forecast on the model slide.

**Projections**
- A curve that turns upward with no stated cause. A cost of winning customers that falls for no reason. No assumptions shown.

**The ask**
- No amount, or a range. No milestone. Use of funds that does not add up. Runway under a year with no reason given.
- Ends on "any questions". Asks for the money, not the next conversation.

**Team**
- A wall of logos. Advisors standing in for the team. No tie between the people and this problem.

## 7. Questions the deck does not answer

A reader finishes a deck with questions. List the ones this deck leaves open, most important first. Choose from these, and add any the deck itself raises.

- **What it is.** What exactly would I have to build to copy this? Who uses it on a normal Tuesday?
- **Problem.** How do customers handle this today? What does that cost them, in their own numbers?
- **Demand.** What did the people now using it stop using? Who was the last prospect to say no, and why?
- **Example.** Is this case real? When did it happen, and how was the saving measured?
- **Advantage.** Why can an established company with the same tools not follow? What gets stronger with each customer?
- **Proof.** When did work start? Who builds it? What is in use today, by whom, and do they pay?
- **Market.** How many customers are there, what does each pay, and where does the first one come from?
- **Competition.** What happens when the tool the customer already pays for adds this?
- **Price.** What does it cost, what does one customer cost to serve, and whose budget does it come from?
- **Reach.** How do the first ten outside customers arrive, and who goes and gets them?
- **Ask.** How was the amount arrived at? What exactly will be true when the money is spent? What happens after that?
- **Next step.** What does the company look like in 18 months, and what is the next concrete move?

Each question in the review names the slide where its answer should be.

**Check what the founder has already said before writing a question.** If their notes or dictation answer it, quote the answer and drop the question. If they said they do not know, bring a draft answer for them to correct. Do not ask again.

**The list and the message are different things.** The review may list everything the deck leaves open. The message that goes to the founder carries five questions or fewer, chosen by how much each answer changes the deck (`founder-interview.md`, section 5).

## 8. The three weakest claims

Pick the three claims the deck leans on hardest with the least support. For each, write four follow-ups for the founder:

1. What exactly is being claimed?
2. How do you know?
3. Which customer, case or number shows it?
4. What would a competitor get wrong about this?

A real insight gets more specific under these questions. A borrowed one gets vaguer. In a written review the founder is not there to answer, so the questions go to them. Leave out any follow-up the founder has already answered. Answered claims earn a speaker note or an appendix page. Unanswered claims are cut or softened.

Then count the distinct edges the deck shows across three places: the technology, the read of the market, and the route to customers. Do not count the same edge under three headings, and do not count one that failed its follow-ups. State the count in one line, and name the edge still to be earned.

## 9. The review, in a fixed order

Use this order every time, so two reviews of two versions can be compared.

```
# Deck review: [company], [deck kind], [date]

Reader and stage: [who reads it, at what stage]
Scored from: [the file, or pasted text only]
Weighting: [one line]
Main advantage, as the deck tells it: [one line]

In short: [ready or not ready, the one fix, and what is needed from the
founder. Three lines at most.]

## 1. What already works
[Three to five things, each quoting the slide. This section is required. It
stops the next draft from deleting the parts that are doing their job.]

## 2. Score: [N] of [points available], [N] gates tripped, [N] open
[The twelve lines as a table: points earned, points available, one line of
evidence each. Show the arithmetic.]

## 3. Gates
[Each of the six: tripped, clear or open, with the slide, the number of
instances, and whether the fix is wording or a fact only the founder has.]
Checked today: [the sums, sources and pages checked, and what was not.]

## 4. The skim read
[The largest lines in order, exactly as they render. For a PDF, the first
text line of each page as well. Then one sentence: do they carry the
argument or not.]

## 5. Red flags
[Slide number, the flag, the words on the slide.]

## 6. Questions the deck does not answer
[Most important first. Each names the slide where the answer belongs.]

## 7. The three weakest claims
[Each claim with its follow-ups. Then the edge count in one line.]

## 8. Fixes, with replacement wording
[Ranked by effect. Each one: the slide, what is there now, what to put
instead. A replacement that needs a fact the founder has not given uses a
placeholder: [NEED: ...]. When the founder brought outside feedback, start
this section with each of its points: taken, changed or declined, and why,
with the arithmetic on any figure it proposed.]

## 9. Numbers to find
[Every placeholder used above, and who can supply it.]

## 10. The one fix that matters most
[One. Not a list.]

This review scores craft and evidence. It is a judgment about the deck, not a
forecast of funding. It does not cover valuation, terms or legal questions.

Appendix: slide inventory
[One row per slide: the first text line, the headline as rendered, any larger
text, the visual, the numbers.]
```

The body of the review ends on the one fix. The inventory follows as an appendix, for the record.

For a short deck, or a quick look, the "In short" lines and sections 1, 2, 4, 8 and 10 are the minimum.

## 10. Rules for the reviewer

- **Quote the slide.** Every finding points at words or a picture on a numbered slide.
- **Every critique comes with a fix**, written as replacement wording the founder could paste in.
- **No invented numbers in the fixes.** A replacement headline that needs a figure the founder has not supplied carries a placeholder. Writing "raise $2 million" into a fix is inventing a number.
- **Check the deck's own arithmetic.** Recompute every sum and show the working.
- **Do not make up the company's story.** If the material is missing, ask for it. A judgment you cannot tie to a slide goes to the founder as a question and stays out of the findings.
- **Claim no calibration you do not have.** Do not say the score is benchmarked against funded decks. Do not compare the deck with famous decks from memory.
- **Say what works before what fails.**
- **End on one fix.** A founder with ten equal fixes does none of them well.
- **Keep the persona out.** No investor role-play and no verdict to invest or pass. A model that has read a deck cannot make that call. The founder needs the gaps and the fixes.
