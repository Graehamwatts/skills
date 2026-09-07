# Flight Upgrade Desk — Command Templates

Follow the relevant template exactly. Every command assumes the hard rules in `SKILL.md` section 0 are in force.

---

## `# UPGRADE AUDIT`

The entry point. Run this before any other command.

### Step 1 — Load the wallet

Read `outputs/wallet.md`. If it does not exist, copy `references/wallet-template.md` into it first and say so.

### Step 2 — Get the flight

Needed: airline, confirmation code, date, route, and **fare class letter**. The fare class decides whether anything else is worth doing, so chase it early. It is on the receipt or under booking details.

If Graeham does not know the fare class, note it as unknown and flag every conclusion as provisional until it is confirmed.

### Step 3 — Interview, once

Ask **everything in one batch**, and only what the wallet does not already answer. Do not drip questions one at a time.

Cover, as gaps allow:
- Elite status and current tier, plus any certificates sitting unused and their expiry
- Miles balance in this airline's program
- Bank point balances and which programs they transfer to
- Co-brand card for this airline, if any
- What he paid for the ticket
- The most cash he would pay for a confirmed seat
- Whether an upgrade offer or bid invitation has already appeared

### Step 4 — Research, do not recall

Web-search the current rules for this specific airline's upgrade program. Required, every run, no exceptions. Confirm:
- How this airline prices a miles upgrade today
- Whether it runs bidding
- Which certificates apply and whether space must exist
- How its upgrade list is ordered
- Whether this fare class is eligible at all

If a search result conflicts with `references/programs.md`, trust the search and update the file.

**One-time setup check.** If this is a United flight, ask whether Expert Mode is enabled in his MileagePlus account settings. If not, walk him through it before building the dashboard. It makes the actual upgrade buckets visible on united.com for free, which converts the single most important input from an estimate into a fact. Worth interrupting the flow for, once.

### Step 5 — Rank

Score every door. Confirmed beats waitlist unless cost is unreasonable. Cheap beats expensive at equal certainty. A free waitlist that costs nothing to enter is always worth entering, even at long odds.

### Step 6 — Build the dashboard

Per the spec in `SKILL.md` section 4. Publish as an artifact. Pin the First Move box.

### Step 7 — Say the one thing

Close with a single sentence naming the one action to take now. Not a list. One action.

---

## `# CHASE`

Live browser run. Requires a connected browser with Graeham already logged into the airline.

### Preconditions — verify before starting

1. A dashboard exists from `# UPGRADE AUDIT`. Without it there is nothing to compare live prices against.
2. Browser is connected and the airline tab is logged in. **He logs in himself.**
3. A miles floor is set, defaulting to 1.3 cents.

If any precondition is missing, stop and say which one.

### Procedure

1. **If United: check Expert Mode is on** before anything else. MileagePlus account settings. With it on, united.com renders the actual upgrade buckets inline, and `PZ` is the number that decides whether a PlusPoints or miles upgrade can confirm today. Search a **paid** ticket, not an award ticket, or the classes will not display. This turns a guess into a fact and takes one minute.
2. Open the booking with the confirmation code.
3. Read and report: seats still for sale in the premium cabin, the cash upgrade price, the miles upgrade price, whether a bid option exists on this booking. On United, report the PZ count too, and lead with it.
4. Compare each against the dashboard. Say explicitly where the live number differs from the estimate, and by how much.
5. Take the best path:
   - Miles price clears the floor → apply the miles
   - Airline runs bidding → propose a number using the bid method in `programs.md`, and explain the number before entering it
   - Neither is worth it → join the upgrade list as high as possible and report the position
6. **Stop at the payment step.** Show the exact charge, the exact button, and what happens after the click. Wait for a clear yes.
7. Update the dashboard with what happened and what to check next.

### Narrate as you go

Say what is on screen while working. If the page does not match expectations, stop and describe what is actually there rather than guessing at the next click. Airline sites change layouts often, and a wrong click on a booking page can cancel things.

### If blocked

Airline sites run aggressive bot detection. If the page will not load, a form will not accept input, or a challenge appears: **stop and hand back to Graeham with the exact next click.** Do not attempt to work around a bot challenge. Being useful here means telling him precisely what to press, not defeating a security control.

---

## `# SWEEP`

The re-check. Best run at 72 hours, at check-in, and at the gate. Ideal for scheduling.

```
It's [72 hours / 24 hours / gate day] before the flight, confirmation [CODE].
Check three things and compare each to the dashboard:
  1. Current cash upgrade offer
  2. Current miles upgrade price
  3. Position on the upgrade list
Verdict: buy now, wait for the gate, or stop caring.
```

At the 24-hour mark, also check him in if check-in is open and he has asked for that.

Cash offers usually fall as departure approaches and seats go unsold. A number that was bad at 72 hours can be good at the gate. Compare against the dashboard every time rather than judging the number in isolation.

End with one of exactly three verdicts: **buy now**, **wait**, or **stop caring**. No hedging across all three.

---

## `# TRANSFER MATH`

Run before any bank point transfer. Transfers are one-way and irreversible.

### The ordering rule — this is the guardrail

**Confirm the upgrade is actually available at the quoted price BEFORE transferring anything.**

The failure mode is specific and expensive. Points get transferred to cover a miles upgrade, the transfer completes, and then the upgrade turns out to be unavailable, the price has moved, or the space was never there. The points are now stranded in an airline program that may be worth far less to him than the bank currency he gave up, and there is no way back.

Order of operations, always:

1. Read the live miles price and confirm upgrade space exists
2. Run the math below
3. Only then transfer, and transfer the exact amount needed, not a round number
4. Apply immediately

If the upgrade cannot be confirmed at step 1, the answer is no regardless of how good the math looks. A good rate on a seat that does not exist is not a good deal.

Instant transfers reduce this risk but do not remove it. Transfers taking several days make it severe, and near departure they make the whole path unusable.

### Procedure

1. Web-search current transfer partners, ratios, transfer times and fees. These change and old ratios are actively harmful.
2. Confirm the airline is even a transfer partner of the bank in question. Frequently it is not, which ends the analysis immediately.
3. Compute cents per point:

   ```
   cpp = (cash price of the upgrade) / (points required) × 100
   ```

4. Compare against the floor, 1.3 cents by default.
5. Give a clear yes or no, with the arithmetic shown.

### Also state

- Transfer time. Instant versus several days changes whether this is viable at all near departure.
- What else those points could do. A point returning 0.9 cents on an upgrade might return 2+ cents on an international business award, which makes the transfer a bad trade even when it is affordable.

The answer is often no. Say no clearly when it is.

---

## `# TRACKER`

Multi-flight artifact for several booked trips at once.

Per flight card:
- Route, date, airline, confirmation code, fare class
- The best upgrade path for that airline
- The number to watch (miles price, cash offer, or bid amount), editable
- Checkpoints: booked, 72 hours, 24 hours, gate
- Status, clickable to update
- Days-to-departure countdown

Persist state on the device so updates survive a reopen.

Use this when three or more flights are booked. For one or two, the dashboard alone is enough and a tracker is overhead.

---

## Scheduling

The checkpoints only work if they actually happen. Offer to register a scheduled task for the 72-hour and 24-hour sweeps once a flight is in the tracker.

Recipients and mechanism follow the workspace standing rule: scheduled reports **send**, they do not sit as drafts.
