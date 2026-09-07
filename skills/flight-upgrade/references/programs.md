# Program Mechanics

> Researched and verified 2026-09-06. Confidence is marked per claim. Airline programs change often, so re-verify anything marked MEDIUM or lower before acting on it, and re-verify HIGH claims when the flight actually matters.
>
> `HIGH` = confirmed against a primary source or multiple strong secondaries.
> `MEDIUM` = single credible source, plausible, not independently corroborated.
> `UNVERIFIED` = do not state to Graeham as fact.

---

## The seam that makes this skill work

Upgrade space is not award space. They live in different booking-class buckets and travel through different channels.

- **Award space** is scraped off consumer sites by every tool in the market. seats.aero's own terms describe cached data retrieved and interpreted from airline sites. `HIGH`
- **Upgrade space** is GDS-published inventory. ExpertFlyer is the only consumer-priced product holding that position, because the moat is a GDS contract rather than code. `HIGH`

**The exploitable seam:** ExpertFlyer covers award and upgrade classes for only **28 airlines**, and **United and Delta are not among them**. `HIGH` United cut ExpertFlyer off from upgrade classes in Nov 2013, Delta in Sept 2014. Those two carriers instead expose some of it on their own websites.

So for the two most likely US carriers, the paid tool cannot help and the airline's own site can. That is the opposite of what intuition suggests, and it is the single most useful fact in this file.

---

## United: turn on Expert Mode

**The highest-value trick available.** United renders raw booking-class inventory directly on united.com once Expert Mode is enabled in MileagePlus account settings. `HIGH`

Displayed classes: `PZ`, `PN`, `RN`, `IN`, `I`, `XN`, `X`, `JN`, `YN`.

| Bucket | Meaning | Confidence |
|---|---|---|
| **PZ** | Confirmed upgrades into business/first using PlusPoints or miles. **The one that matters.** | `HIGH` |
| **RN** | Premium Plus upgrades with PlusPoints or miles | `HIGH` |
| **PN** | Historically instant first-class upgrades for Premiers on full-fare Y and B. **United ended instant upgrades on 21 Aug 2025**, so every request now goes to the priority waitlist against PZ. Treat PN as probably obsolete | class `HIGH`, current relevance `UNCERTAIN` |
| IN / I | Saver business/first award space (IN for some elites and cardholders, I for everyone else and partners) | `HIGH` |
| XN / X | Saver economy award | `HIGH` |
| JN / YN | Everyday business/first and everyday economy award | `HIGH` |

**Catch:** search **paid** tickets, not award tickets, or the award classes will not display. `HIGH`

If Graeham flies United, walking him through enabling Expert Mode once is worth more than everything else in this file combined. After that, `# CHASE` can read PZ directly instead of guessing from the seat map.

---

## Other carriers, bucket by bucket

| Airline | Bucket | Meaning | Confidence |
|---|---|---|---|
| **American** | `C` | What an SWU or confirmed upgrade clears into for Business, and domestic First on two-cabin aircraft | `HIGH` |
| **American** | `A` | Business into Flagship First on three-cabin aircraft | `HIGH` |
| **Delta** | `Z`, `J`, `P` | Global Upgrade Certificate inventory | `MEDIUM` — single specialist source. Delta publishes nothing and ExpertFlyer cannot see it. **Highest-risk claim in this file** |
| **Delta** | `Z`, `G` | Regional Upgrade Certificate inventory | `MEDIUM`, same caveat |
| **Alaska** | `U` | First class upgrade inventory for elite upgrades and certificates | `HIGH` |
| **Air Canada** | `R` | eUpgrade class | `HIGH` |

### Delta `U` is a trap

**`U` is NOT Delta's upgrade bucket.** It is one of the eligible economy source fares you can upgrade *from*. The full source list is B, H, K, L, M, Q, T, U, V, W, X, Y. `HIGH`

The confusion is easy because `U` genuinely is the upgrade inventory bucket **on Alaska**. Do not carry it across to Delta.

---

## What each site shows you

| Airline | Consumer site exposure | Confidence |
|---|---|---|
| **United** | Full. Expert Mode renders every bucket inline | `HIGH` |
| **Air Canada** | Yes. Log in, mock-book the exact flight with the eUpgrade display option on, and R space shows with the co-pay. Caveat: querying against an existing reservation can return a different booking class than the one held, producing wrong answers | `MEDIUM` |
| **Delta** | Partial and unreliable. A certificate-availability display appears under flight details for Delta-operated flights when it exists, but does not always surface. Partner flights require phoning. Seat maps tell you nothing | `MEDIUM` |
| **American** | Mostly no. Only ConciergeKey and Executive Platinum see SWU availability on aa.com. Everyone else calls or uses ExpertFlyer, which does cover AA | `MEDIUM` |
| **Alaska** | Unknown whether alaskaair.com exposes U directly to logged-in members | `UNCERTAIN` |

**A seat map showing empty seats is weak evidence about upgrade space.** A cabin can look half empty while the upgrade bucket sits at zero. Treat it as a hint, never an answer.

---

## Bidding vs no bidding

The branch that decides which half of the playbook applies.

**Runs bidding**, mostly through Plusgrade: Air Canada, Lufthansa, Singapore, Virgin Atlantic, Etihad, Aer Lingus, Air New Zealand and many others. Among US carriers, Hawaiian. `MEDIUM — confirm per airline at run time`

**Does not bid:** American, Delta, United. Also British Airways, Emirates, Qatar, Air France, KLM. `MEDIUM`

Plusgrade is strictly B2B with no consumer or developer API, no public documentation, and no open-source footprint whatsoever. `HIGH` The only way to see a bid offer is to be the passenger holding the PNR. So bidding is browser-only, always.

**Never tell Graeham to "place a bid" on a carrier that has no bidding.** That single error makes the whole dashboard look unreliable.

---

## The big three, when there is no bid

Worked in this order.

### 1. Miles upgrade on the booking

The airline shows a miles price, often with a cash copay, beside the cash price. Miles are deducted only when the upgrade clears. Check right after booking and every few days after, because the price moves.

United now prices per flight rather than off a fixed chart. Delta prices off the cash offer, historically near one cent per mile. `MEDIUM — verify at run time`

### 2. Cash upgrade offer

Same screen, in dollars. Often the cheapest path when the cabin is still open close to departure. Falls as departure approaches and seats go unsold. Check at 72 hours, at check-in, and at the gate.

### 3. Certificates

PlusPoints (United), Global and Regional Upgrade Certificates (Delta), systemwide upgrades (American). Confirm instantly when space exists in the relevant bucket, otherwise sit near the top of the waitlist. Apply at booking; the waitlist keeps working after.

### 4. The upgrade list

Free space-available upgrades in status order, processed mostly on the day of departure.

United's ordering as an illustration: top-tier invitation-only members, then anyone with a miles or PlusPoints request already queued, then elite tier, then fare class, then card-based tiebreakers, then who asked first. `MEDIUM`

**The lesson generalizes even where details differ.** A miles or certificate request in the queue costs nothing until it clears and jumps ahead of every free-upgrade hopeful. Put one in even when not expecting to pay.

---

## Bid method, when bidding exists

No published acceptance threshold exists. Anyone quoting an exact winning number is guessing. Give a range with conditions and explain the reasoning.

| Rule | Detail |
|---|---|
| Anchor on the fare gap | Business fare minus what was paid. Winning bids tend to land at 20 to 40 percent of that gap. A $3,200 gap suggests roughly $650 to $1,300 |
| Read the seat map, not the slider | The weak/fair/strong labels are decorative. Empty cabin a week out means the minimum often clears. Three seats left means almost nothing does |
| Beat the round numbers | Most people bid the minimum or a round figure. $850 beats a crowd sitting at $800 |
| Know the ceiling | Above roughly 35 percent of the gap, a check-in cash offer or miles upgrade is usually better |
| Bid per person, per segment | Two travelers means two bids and two charges. Connections bid separately. Adjacent seats are never promised |

**Timeline:** bids typically due at least 72 hours out, adjustable or cancellable until roughly 48 hours out, answer by email 24 to 48 hours before departure. Accepted bids charge then and are generally non-refundable unless the flight cancels. `MEDIUM — varies by airline`

Miles and status credit are earned on the economy fare bought, not the cabin flown.

**Check the seat map twice.** Once when the invitation arrives, once about four days out. Cabin filled in between, lower the bid or pull it. Cabin emptied, the bid can come down.

---

## Hard blockers

Check these first. Each ends the analysis early and saves an hour.

- **Basic economy** is almost never upgradeable with miles or certificates.
- **Partner miles cannot upgrade another airline's ticket.** Virgin Atlantic points book Delta seats but will not upgrade a ticket Delta sold. Bank points that only transfer to partners feed a new booking, not an upgrade.
- **Award tickets** often cannot be upgraded with miles at all.
- **Deeply discounted fare classes** are excluded from certificate upgrades on some carriers even when not basic economy.

---

## When to send him to ExpertFlyer

Worth the money only when the airline is on its 28-carrier upgrade list. American is, and it also does aircraft-change and schedule alerts plus real seat maps.

Pricing verified live 2026-09-06: Basic $5.99/mo annually, Premium $10.99/mo annually, Elite $19.99/mo annually. Elite adds expanded AA systemwide upgrade search. Free tier gives one seat alert a month. `HIGH`

**Do not send him there for United or Delta upgrade space.** It cannot see either, and no amount of money fixes that. `HIGH` For United, Expert Mode on united.com is free and strictly better.
