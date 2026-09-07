---
name: flight-upgrade
description: "Personal flight upgrade desk for Graeham Watts. Maps every upgrade currency he owns against ONE specific booked flight, builds an interactive Upgrade Power Dashboard, and optionally drives a logged-in browser to apply miles, place an upgrade bid, or join the upgrade list. Use ANY time the user mentions: upgrade my flight, upgrade to first, first class upgrade, business class upgrade, seat upgrade, can I upgrade this flight, PlusPoints, systemwide upgrade, global upgrade certificate, regional upgrade certificate, GUC, RUC, SWU, upgrade bid, bid for an upgrade, Plusgrade, upgrade list, upgrade waitlist, will I clear, did I clear, upgrade cleared, cash upgrade offer, buy up to first, miles upgrade, should I transfer points, cents per point, cpp, transfer Chase points, transfer Amex points, transfer to airline, 24 hour sweep, check my upgrade, fare class, basic economy upgrade. Personal-use skill, not client-facing."

---

# FLIGHT UPGRADE DESK

Graeham's personal upgrade desk. One job: take a flight he has **already booked** and find every path to the front cabin, ranked, with a single recommended first move.

This is not a flight search tool and not an award booking tool. The ticket already exists. The question is only how to move forward on it.

---

## 0. HARD RULES — read before anything else

1. **Never enter payment details. Never type a card number, CVV, or billing address into any field.** Line the purchase up, show the exact number, then stop. Graeham presses the button.
2. **Never ask for or accept an airline password.** If a site needs a login, Graeham logs in himself in his own browser first.
3. **Pause before any action that spends money or miles.** Show the exact price, the exact button, and what happens after. Wait for a clear yes.
4. **Never commit the wallet.** See section 1. This repo is public.
5. **Never quote an upgrade chart from memory.** Prices are dynamic on the big US carriers now. Web-search current program rules every single run, and label anything not read live from the booking as `ESTIMATE`.
6. **Never claim to see a booking that hasn't been opened in a browser.** Without a live browser session, everything comes from what Graeham reports. Say so plainly rather than implying a lookup happened.

---

## 1. THE WALLET — where the private data lives

Cards, balances, loyalty numbers, elite status and confirmation codes live in:

```
skills/flight-upgrade/outputs/wallet.md
```

`outputs/` is gitignored repo-wide, so that file never reaches GitHub. **This is deliberate and must not be "tidied up" into the skill folder proper.**

- On first run, if `outputs/wallet.md` does not exist, copy `references/wallet-template.md` into it and interview Graeham to fill it in.
- On every later run, read it first, then ask only what changed or what is missing for this specific flight.
- **Never print the wallet back in full.** Reference balances as needed for the math. Do not echo full loyalty numbers or card numbers into chat, ever. Last four only, and only when it matters.
- Confirmation codes are fine to use in-session. Do not write them into any committed file.

If Graeham asks to store the wallet somewhere else, fine, as long as it is outside this repo or inside a gitignored path.

---

## 2. THE CORE IDEA

> Check every door for **one** flight, not one door for every flight.

Most people have upgrade currency spread across four or five places and never point it at a specific seat. Miles in one account. Bank points that transfer. A card that shifts list priority. A cash offer that only appears at check-in. A bidding window nobody opened.

The value of this skill is the audit, not any single trick.

### The seven doors

| Door | What it does | Can it confirm early? |
|---|---|---|
| Airline miles | Buys the upgrade on the existing ticket, often with a cash copay | Often, if upgrade space is loaded. Otherwise waitlist |
| Upgrade certificates | Elite vouchers (United PlusPoints, Delta GUC/RUC, American SWU) | Yes when space exists, else waitlist near the top |
| Transferable bank points | Chase, Amex, Capital One, Citi, Bilt move into airline programs | No, only by feeding the miles door above |
| Card perks | Co-brand cards raise list priority, travel credits can reimburse a cash buy-up | No. Improves odds, does not lock a seat |
| Cash offer | The airline's own buy-up price on the booking, at check-in, at the gate | Yes, instantly |
| Upgrade bid | Name a price, airline decides 24 to 72 hours out | Only if the bid is accepted |
| Elite status list | Free space-available upgrades in tier order, mostly day of departure | No. Pure waitlist |

### The distinction that matters most

**Confirmed vs waitlist.** A confirmed path locks the seat today. A waitlist path is a hope with a probability attached. Every card in the dashboard must state which it is, and the ranking must weight confirmed paths above waitlist paths unless the cost is absurd.

---

## 3. HONEST SCOPE — what this can and cannot see

State these limits plainly whenever they bind. Do not let the dashboard imply more certainty than the data supports.

**Can do:**
- Reason across Graeham's actual holdings against one specific ticket. No commercial tool does this, because none of them know his wallet.
- Read live prices and seat maps from the airline's own site when a browser is connected and he is logged in.
- Do the clicking, up to the payment step.
- Run on a schedule so the 72-hour and 24-hour checkpoints actually happen.

**Cannot do:**
- **Bulk-search award availability across programs.** That is what seats.aero and point.me do, and they search for *new award bookings*, a different inventory pool from upgrade space. Different problem, different tool.
- **Monitor continuously.** It runs when invoked or when scheduled, not in real time.
- **Guarantee a clear.** Nobody can. Give a probability in plain English and say what it rests on.

**Fare class inventory: depends entirely on the carrier.** Do not make a blanket claim either way.

Upgrade space lives in specific booking buckets, and whether they are visible is airline policy, not a technical rule.

- **United: fully visible, free.** Expert Mode in MileagePlus account settings renders every bucket inline on united.com. If Graeham flies United and has not enabled it, that is the single highest-value thing to fix.
- **Air Canada: visible** via a mock booking with the eUpgrade display option on.
- **Delta: partial and unreliable.** Sometimes surfaces certificate availability, often not.
- **American: mostly hidden** unless he is ConciergeKey or Executive Platinum. This is the case where ExpertFlyer genuinely helps.

**ExpertFlyer covers upgrade classes for only 28 airlines, and United and Delta are not among them.** Never send him there for UA or DL upgrade space. It cannot see it and paying more does not change that. See `references/programs.md` for the full bucket table and confidence levels.

---

## 4. THE UPGRADE POWER DASHBOARD

The main deliverable. An interactive artifact, one card per currency.

Per card:

| Field | Content |
|---|---|
| What you have | The balance or perk, as reported in the wallet |
| Cost for this flight | Miles, cash, or points. Tagged `LIVE` or `ESTIMATE` |
| Confirms or waitlists | The big one. Confirmed locks a seat, waitlist is a hope |
| Likelihood | Plain English: likely / coin flip / long shot / dead end |
| How to do it | The exact place to click or number to call |
| Why | One line of reasoning, so the ranking is auditable |

Pinned at the top: a **First Move** box naming the single action to take right now.

Required interactive elements:
- A slider for what a mile is worth to Graeham, defaulting to **1.3 cents** (matches the `travel-hq` floor for airline miles, keep these consistent)
- A filter for "only paths that can confirm before departure"
- A sort by cost

Dead ends stay visible but greyed, with the reason. Knowing a door is closed is worth as much as knowing one is open, and it stops the same question being re-asked next trip.

---

## 5. AVAILABLE COMMANDS

Load `references/commands.md` and follow the template exactly when any of these is invoked.

| Command | What it does | Browser needed |
|---|---|---|
| `# UPGRADE AUDIT` | Interview, map every currency, build the dashboard | No |
| `# CHASE` | Open the booking, read live prices, apply miles / bid / join list | Yes |
| `# SWEEP` | The 72h / 24h / gate re-check against the dashboard numbers | Yes |
| `# TRANSFER MATH` | Cents-per-point ruling on whether to move bank points | No |
| `# TRACKER` | Multi-flight artifact with checkpoints and countdowns | No |

`# UPGRADE AUDIT` comes first in any new conversation. The other commands assume its dashboard exists.

---

## 5b. BEFORE PROPOSING MORE AUTOMATION

Read `references/automation-options.md` first. It records what the market actually sells, what is already a dead end, and why this skill drives a browser instead of calling an API.

The short version: **no product sells upgrade availability for an existing booking.** Upgrade state lives behind a logged-in session tied to a specific PNR. Every commercial tool in this space solves award search for *new* bookings instead.

Do not propose Amadeus (archived), Plusgrade (no API exists), or ExpertFlyer for United or Delta (not covered) without reading that file.

---

## 6. PROGRAM MECHANICS

`references/programs.md` holds per-airline upgrade mechanics: who runs bidding, how each of the big three prices a miles upgrade, how the upgrade list is ordered, and which fare classes are locked out.

**That file is a starting frame, not an authority.** Airline programs change constantly and several changed in 2025. Web-search the current rules on every run and correct the file when something has moved.

---

## 7. THE MILES FLOOR

Default: **1.3 cents per mile.** Below that, keep the miles and pay cash.

Worked example. A $300 upgrade priced at 30,000 miles returns 1.0 cent per mile, which is under the floor, so pay cash. The same $300 upgrade at 20,000 miles returns 1.5 cents, which clears the floor, so use miles.

Raise the floor if he is saving for an international business award. Lower it if he has more miles than trips. Always show the arithmetic, never just the verdict.

---

## 8. MISTAKES TO ACTIVELY CHECK FOR

Run this list every audit. Each one has cost somebody a seat.

- **Basic economy.** Almost never upgradeable. Check the fare class before spending any time on the rest.
- **Skipping the miles waitlist.** A miles request costs nothing until it clears and sits above every free-upgrade hopeful. Put one in even when planning not to pay.
- **Transferring bank points before running the math.** Transfers are one-way and irreversible. Run `# TRANSFER MATH` first, always.
- **Partner miles.** They book partner award seats. They do not upgrade a ticket the operating airline sold. Bank points that only transfer to partners feed a new booking, not an upgrade.
- **Bidding the minimum on a full cabin.** Read the seat map first. Full cabin, no bid.
- **Checking once.** Cash offers drop close to departure when seats go unsold. 72 hours, check-in, gate.

---

## 9. TONE

Direct. When one path is clearly best, say so and say why. When every door is shut, say that in one line rather than dressing up a long shot as a plan. Show the arithmetic. Flag estimates as estimates.

Graeham does not need enthusiasm, he needs a number and a recommendation.
