---
name: pitch-deck
description: "Builds and reviews startup fundraising pitch decks for first-time founders. Use whenever the user wants a pitch deck, investor deck or investor presentation, a seed or pre-seed deck, a demo day or pitch competition deck, a deck for an accelerator, grant or credit-program application, or a send-ahead (DocSend) deck; wants one reviewed, scored, torn down or roasted; asks 'what goes in a pitch deck'; needs the headlines, competition, market size, pricing or ask slide of such a deck fixed; brings feedback on one; or brings a deck outline another AI wrote. It settles what kind of deck this is (sent ahead, live, or attached to an application), writes headlines that pass a skim test, keeps invented numbers and unchecked 'first' or 'only' claims off slides, builds an honest competition slide, scores decks on a 100-point rubric, and renders and reads every slide. Not for sales or customer decks, listing presentations, board updates, launch or conference talks, or investment-banking pitch books."
---

# Pitch Deck

Build and review startup pitch decks. This is written for a founder who knows their trade and has never made a deck, and for whoever is helping them.

A deck has one job: to earn the next conversation. Nobody invests, admits or funds off a deck alone. The rules below serve that job, and most of them come down to two tests. Can the reader take in the argument at a skim? Would every claim on the page survive the founder being asked about it?

## What this covers

Fundraising decks at pre-seed and seed: building one, reviewing or scoring one, fixing a single slide, cleaning up an outline another AI wrote, and applying feedback someone gave.

Not for sales decks aimed at customers, listing presentations, board updates, launch or conference talks, or investment banking pitch books. Those have different readers and a different job.

**Limits.** This skill checks arithmetic and evidence. It does not advise on valuation, instrument, deal terms or securities rules. Send those to the founder's lawyer or adviser, and say so.

**Private files.** The facts sheet, the claims ledger, the outline, the renders and the review hold a founder's private numbers. Keep them in the founder's own project folder. Never save them inside this skill's folder or in any public repository.

## Pick the mode

| The user has | Mode |
|---|---|
| A company and no deck: notes, documents, a ramble | **Build** |
| A deck, and wants to know how good it is | **Review** |
| A deck, plus feedback someone gave on it | **Review first, then build** the next version |
| An outline or deck prompt from another AI, and no slides yet | **Import** |

Review comes first when a deck and feedback both exist, because the review's first section records what already works. Without it the next draft deletes the good parts along with the bad.

## First, in any mode: what kind of deck is this?

Settle this before anything else. If the material shows it, say which kind and what told you, in one line. If it does not, state your assumption at the top and keep working. Stop to ask only when the material points two ways, such as an investor list and an application deadline.

| | Sent ahead, read alone | Attached to an application | Presented live |
|---|---|---|---|
| Reader | An investor, alone, skimming first | A reviewer working through a stack | A room, listening to the founder |
| Main slides | 10 to 15, plus a short appendix | 6 to 8 | By the slot: about 5 for 3 minutes, 8 to 10 for 7, 12 to 15 for 15 |
| Headline | A claim of 8 to 12 words | The same | A claim of 4 to 8 words |
| Body | Three or four short rows. No paragraphs | The same | One number or one picture |
| It must | Explain itself with nobody there | Show a real product company, fast | Be impossible to follow without the speaker |

A deck built for one of these fails as another. A wordy deck on a stage gets read while the founder is ignored. A stage deck sent by email is a row of pictures nobody explains. When a founder needs more than one, build the sent deck first, because most first reads happen alone, then make the others from the same outline as their own pieces.

## Build mode

Work through these in order. Each step exists because skipping it has cost a founder a version.

1. **Name the deck kind and the reader.** Budgets, slide count and order all follow from it. Writing first and deciding later produces a deck tuned for no room.

2. **Read everything before asking anything.** The site, the product, its documentation, earlier decks, the founder's notes and dictation. A question the documents already answer tells the founder nobody read them.

3. **Find the company's real look.** Its site, its product interface, its design files. A deck in a stock template reads as machine-made, whatever it says. Once a look is approved, reuse its parts in every later version and change only the story.

4. **Write the facts sheet and the claims ledger.** The facts sheet holds every number with where it came from. The ledger lists each capability the founder describes and its status: runs today, being built, later, or stated and not yet checked. It uses the names in the company's current documents. A founder describes the product in their head. The ledger separates that from the product on the screen before a slide can blur the two. See `references/evidence-rules.md`.

5. **Run the checks that can sink a deck.** A prior-art search on every "first", "only" and "no other tool does this". Competitor statements taken from the competitor's own pages, with the date read and the name the product carries today. The market sum. The price against cost to serve. The ask against its own arithmetic. These are cheap now and expensive after the slides exist.

6. **Interview the founder, briefly.** One message, five questions or fewer, and only what only they can know: their numbers, their dates, decisions they have not made. Put everything else as a statement they can correct. For an undecided price or ask, bring a worked range and let them pick. If the inputs for a range are not on file, ask for the inputs. See `references/founder-interview.md`.
   - If they say "just draft it", draft it: assumptions at the top, a placeholder for each missing fact.
   - If there is nothing to draft from, send one message asking for the material, then wait. Never write a deck from imagination, and never hand back an empty template.

7. **Choose the three to five points to be remembered, then write the headline outline.** One line per slide, in a pitch order and not the order of the company's website. Run `scripts/skim_test.py` on it. Show the founder the outline before building anything. A reader keeps about three things, so decide which three before drawing. Wrong order and wrong emphasis cost a minute to fix in an outline and a day to fix in slides.

8. **Write each slide in the slide format** below, using `references/slide-by-slide.md` for the job of each slide. One point per slide. Each of the founder's top points gets a slide of its own, including the long-term advantage, which is the one most often buried in a list. A missing fact is a placeholder, never a guess.

9. **Show early.** Build the cover and two or three slides in the real look and show them before building the rest. A wrong look, a wrong order and a wrong tone are all visible in the first three slides.

10. **Hand the visual build to the right tool.** For an editable file, use the pptx skill. For a designed PDF in the company's own look, build 16:9 slides in HTML and print them to PDF with a headless browser, one 1920 by 1080 page per slide, with the words kept as text. Either way the outline file stays the source of the words. Keep one visual per slide, and use a real screenshot wherever the product exists.

11. **Render every slide and read it, both ways.** Export each page to an image and open each one. `scripts/deck_inventory.py --images` does this for a PDF, and so do pdftoppm and PyMuPDF. Overflowing text, a stale slide and a figure that swamps the claim show up only in the render. Then read the text layer: the first text line of each page, in order, is the skim a model or a screening tool gets. Fix any page whose first line is a tag, and any word that letter-spacing has split. A report that a deck is "clean" is not evidence, your own included. Then run the final gates in `references/evidence-rules.md` and score the deck with `references/review-rubric.md`.

12. **Deliver, then derive the other versions.** Send a PDF named with company, stage, month and year, small enough to email and readable at half zoom. With a draft goes the **Numbers to find** list. With a final deck go the backup sheet with every number and its source, and written answers to at least five likely objections. Make the application and live versions from the same outline file, so a wording change reaches every version. Render and read the shared slides again after every change, because stale shared slides are the usual way two versions drift apart.

## Review mode

Read `references/review-rubric.md` before step 1. It holds the inventory rules, what to do when only pasted text is available, the gate definitions, the points and the review template.

1. **Open the real file and inventory every slide**: its number, the first line in the file's text order, the headline as it renders, any text set larger than the headline, the visual, every figure. For a PDF, `scripts/deck_inventory.py` prints most of this and writes the page images. Score the deck, not a description of it. A generous summary of a thin slide passes, and the reader never sees the summary.

2. **Name the reader, the deck kind, the stage and the main advantage.** Say in one line which parts carry the most weight for this company. The main advantage is the claim the deck returns to on the most slides and that answers the two tests in `references/slide-by-slide.md`, section 6. The same deck scores differently for an investor, a program reviewer and a room.

3. **Run the skim test twice.** Once on the largest lines exactly as they render, which is the skim a person gets. Once on the first text line of each page, which is the skim a model or a screening tool gets. A category label that is first or largest is the title for that reader, whatever sits beneath it.

4. **Check the deck's own claims.** At the least: every sum, every outside number that sits in a headline or is set large, every ranking word and universal claim, and the two or three competitors whose own pages come closest to what the company claims. Use a search tool when one is available. List what was checked and what was not. Whatever cannot be verified goes to the founder as a question and stays out of the findings.

5. **Mark the six gates.** Any one means not ready, whatever the score: an unsourced number, an unchecked ranking claim, present tense for something that does not run, arithmetic that does not reconcile, an unsourced statement about a named competitor, or slides nobody rendered and read. The gates come after the checks because most of them cannot be marked without the checks.

6. **Score the 100 points**, quoting the slide for each line. A number lets the founder see whether the next version is better. An opinion does not. A deck for investors with no price, or with no definite ask, is not ready to send, whatever it totals.

7. **Write the review in the fixed order**: three lines in short, what already works, the score, the gates, the skim read, red flags, the questions the deck does not answer, the three weakest claims, fixes with replacement wording, numbers to find, the one fix that matters most. The slide inventory follows as an appendix. The same order every time makes two versions comparable. Every critique comes with words the founder could paste in, and the review ends on one fix because a founder handed ten equal fixes does none of them well. The review may list everything the deck leaves open. The message that goes to the founder still carries five questions or fewer, and none that the founder has already answered.

8. **Put no invented numbers in the fixes.** A replacement headline that needs a figure the founder has not given carries a placeholder. A made-up figure in a suggested fix tends to end up on the slide.

### When the founder brings outside feedback

Feedback from an investor, a friend or another model is usually right about form and unreliable on specifics. For each point:

1. Check its description against the render and the text layer. A model reviewing a PDF often sees text order and not size, so it can call a small tag a huge title.
2. Keep the advice about form when a rule here agrees with it.
3. Treat every figure, axis and term in it as an illustration. Run the arithmetic and the word list on it, and check any starting count it assumes.
4. Tell the founder which points were taken, which were changed and why, and which were declined. In a review this opens the fixes section.

How some common points come out:

- "Your titles are category labels." If a label is the largest line, it is right as stated. If the labels are small tags above a claim, the description is off and the fix is the same: delete them.
- "Swap the tick grid for a two-by-two." Half right. The grid has to go. A map with the company alone in the best corner is the same mistake, so use the form in the competition section below.
- "Put these price tiers on the slide", "raise this much to reach that many customers". Right that the slide needs a price and an amount. The figures are illustrations. Check their arithmetic, show the founder, and print only what the founder sets.
- "Your biggest advantage is buried." Usually right. Give it a slide of its own, named in plain words.

## Import mode

For an outline or a deck prompt that another AI wrote, with no slides yet. An outline is not a deck, so do not score it. Score the first version that has slides.

1. Name the deck kind and the reader.
2. Sort what the founder has already said into known, assumed and unknown (`references/founder-interview.md`, section 3). Note the tense they use. "Will", "in theory" and "imagine" mean a capability does not run yet, whatever tense the outline uses.
3. Run the procedure in `references/evidence-rules.md`, section 12. It reads the outline against the founder's own words, tags every number and claim, checks that each product and company name is the current one, and runs the arithmetic.
4. Run `scripts/skim_test.py` on the outline's titles.
5. Rewrite the outline as claim headlines in a pitch order, with a placeholder wherever a fact is missing.
6. Send one message of five questions or fewer.

The answer opens with three lines that answer what the founder asked. Then: what was kept, the tagged list with what was removed and why, the arithmetic, the new headline outline, **Numbers to find**, the questions. When the founder replies, carry on in Build mode: put their answers on the facts sheet and the ledger (step 4), then go on from step 7.

## The slide format

```
Headline   One claim in one sentence. 8 to 12 words (4 to 8 live). The largest
           text on the slide and the first text on it.
Rows       Three or four. A label of 2 to 4 words, then one plain line.
Visual     One: a real screenshot, a chart, a before-and-after, a diagram.
Source     A small line under any outside number. "Estimate" or "Sample data" where they apply.
Note       What the founder would say, 50 words at most, ending on the takeaway.
```

Keep the deck's words in one outline file, one block per slide with a `Headline:` line, apart from whatever renders the slides. Wording then changes without touching layout, and the skim test can read the file. A full example is in `references/slide-by-slide.md`.

## The rules, in short

### The skim test

Read only the largest line on each slide, in order. Those lines alone should tell the whole thesis: what the company makes, why it matters, why it is believable, what is being asked. Then read the first text line of each page in the file's text order. A model or a screening tool takes that line as the title.

- A headline is one assertive claim, a single sentence the founder would say out loud.
- "Problem", "Solution", "Market" and "The Ask" are category titles, not headlines. So is "Problem: ..." with a claim after the colon.
- No category tag over the headline, at any size. "The Problem" above a claim adds nothing the slide order has not already said, and in a PDF's text order it comes first, so it is read as the title. A tag that carries something the headline lacks, such as a product name or "Appendix", may stay, smaller than the body text.
- A headline that counts things ("four reasons shops stay") hides its point in a list.

| Category title | Headline (invented company) |
|---|---|
| The Problem | A plumbing shop waits 47 days to collect on a finished job |
| Our Solution | Tallybird sends every reminder so the office manager does not |
| Business Model | One price of $240 a month replaces a part-time collections hire |

### Evidence

- Every number is one of three kinds: the founder's own (with its time window), sourced (with a source line), or an estimate (labeled "Estimate", with its inputs on file). Anything else is a placeholder: `[NEED: what belongs here]`. A placeholder can hold any missing fact: a number, a real case, a reason, a name, a decision.
- "First", "only", "best" and category crowns get a prior-art check. So does the same claim with the ranking word taken out: "no other tool does this", "competitors cannot". Competitors' own pages usually make the same claim. What survives is the narrower thing nobody was found doing. Use that.
- A statement about a named competitor comes from that competitor's own pages, with the date read, under the name the product carries today. A search summary of a page is a lead, not a source.
- Present tense is for what someone has seen run. A capability that the founder or an outline only states is treated as being built until it is checked.
- Market size is arithmetic the founder can say out loud: customers, times what each pays. No rings and no one percent.
- A price is checked against what one customer costs to serve.
- An ask states the amount, the milestone and where that takes the business, and its arithmetic reconciles.
- An outline or prompt from another AI is structure to improve, never a source. So is a figure a reviewer proposes.
- The examples in this skill use invented companies. Never carry an example number into a real deck.

Full rules: `references/evidence-rules.md`.

### Tone

- Say what the product does. Spell the stage out once, in positive and exact words, on a dated Done, Now, Next strip. The cover carries only a short stage label.
- Never spend slide space on what the company lacks or what the product does not do. Those are answers for the question period. Write them out in the appendix and the notes.
- Never claim customers, revenue or results that do not exist. Honesty here means inventing nothing. It does not mean listing gaps.
- Plain words in the founder's voice, from their trade. Their real cases. Their approved tagline, as a small line under the cover's plain line or on the close, never as the largest line.
- Keep consultant words off the slides: leverage, synergy, disrupt, revolutionary, seamless, robust, cutting-edge, world-class, game-changing, autonomous, agentic, closed-loop, attribution, flywheel, paradigm, ecosystem, unlock, empower, end-to-end, full-funnel, product-led, lock-in, AI-powered, unit economics. The list is a sample. Any coined noun phrase for a feature gets the same treatment: say what it does. "Wedge" and "moat" are useful ideas for planning a deck. They stay in the working notes.
- A word on that list stays when it is the customer's own everyday term for the thing: attribution for an ad buyer, autonomous for a robotics buyer. Pass it to the script with `--allow WORD` so the lint agrees.
- A generic deck is cured by the founder's real numbers, real screens, a real price and a real ask. Better adjectives do not help.
- If a humanizer skill is available, run the slide text through its detect mode before the final render.

### The example that makes it click

Tell it the way a person explains something: let me give you an example. Show one real case of the founder's, the old way beside the new way. Use one to three examples and never four. The product the founder calls the flagship comes first. One exception: when only another product has a real, dated case with a measured result, lead with that case, put the flagship second, tell the founder why, and ask for a real flagship case.

### Competition, done honestly

- The default slide lists alternatives by kind (doing it by hand, the tool the customer already pays for, a hired person, products built for the job), with what each leaves undone.
- A tick grid loses the reader. Every founder draws one where they win every row, so it is discounted on sight, and it is a ranking claim in picture form. Any table in which the company's column is all ticks or all filled while every other column has blanks is a tick grid, whatever the other cells say.
- A two-by-two map works only when the axes are things a customer would name, every placement cites the rival's own page, a rival that describes itself as you do sits where its page puts it, and the product really does stand apart.
- Answer "an established company can build that" in three moves: concede what is true, name the specific thing that is hard for them and why, and say what would have to be true in twelve months for the claim to hold. If the founder does not know the second move yet, leave a placeholder. Do not write the reason for them.
- Named competitors go in the appendix, each with its source and date.

### Look

The headline is the largest text, with one exception. A single figure with its unit may be larger when it is the slide's visual. A skimmer reads that figure first, so it must be the number the headline is about, show its unit and its kind in the same glance, and not be mistakable for a stronger kind of proof. On a price slide the big figure is the price. On a proof slide a founder's career total is labeled as theirs.

Large type and strong contrast, readable at half zoom on a laptop and on a phone. No paragraphs. One visual per slide. Real screenshots over mockups, and "Sample data" on any screen that is not real. Numbers stay as text, not only inside chart images. Charts start at zero.

## The scripts

```
python scripts/skim_test.py deck-outline.md --mode sent
python scripts/deck_inventory.py deck.pdf --first-lines first.txt --largest-lines largest.txt --images renders
```

`skim_test.py` reads the headlines (lines starting with `Headline:` or `#`, a table column named Headline, or one per line) and reports each one's word count, whether it is a bare category title, whether it holds a ranking word, a universal claim about rivals or a consultant word, and whether it reads as a sentence. A placeholder counts as one word. Then it prints the headlines in order as one paragraph, which is the skim read. Exit code 0 means every headline passed. Modes: `sent`, `live`, `application`. Standard library only. Run it with `--help` for the options.

`deck_inventory.py` reads a PDF the two ways its first readers do, by type size and by text order. For each page it prints the first text line, the headline as rendered, any text set larger than the headline, the body size and the word count. It can write the two line files for `skim_test.py` and a PNG of every page. It needs PyMuPDF. With slide images and no PDF, type the largest line of each slide into a text file, one per line, and run the skim test on that.

Both are lints. Neither can tell a true claim from a false one. Read the skim paragraph and the page images yourself, as a stranger would.

## Reference files

| File | Read it when |
|---|---|
| `references/slide-by-slide.md` | Writing the outline or any slide. It has the standard orders (seed investor, application reviewer, live pitch, short variants) and, for each slide type, its job, headline patterns, the proof it needs, the visual, the usual mistakes and what a company with no revenue puts there |
| `references/evidence-rules.md` | Before any number, ranking word, competitor name, price or ask reaches a slide, when handling an outline from another AI (section 12), and before calling a deck final (the final gates) |
| `references/founder-interview.md` | Before asking the founder anything, in any mode, and when working from a long dictated ramble |
| `references/review-rubric.md` | Reviewing a deck or scoring a draft: the inventory, the gates, the 100 points for three kinds of reader, the red flags, the question bank and the review template |
| `references/frameworks-and-credits.md` | A founder asks where a rule comes from or names a framework (YC, Sequoia, Slidebean), and before changing a rule in this skill |
| `evals/evals.json` | Testing a change to this skill. `evals/files/` holds a sample deck PDF with an invented company |
