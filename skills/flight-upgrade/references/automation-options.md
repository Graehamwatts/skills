# Automation Options — what could be built beyond this skill

Researched 2026-09-06. Read this before proposing any "let's automate it further" work, because most of the obvious ideas are already dead ends and the reasons are not obvious.

---

## The short version

**There is no data product that sells upgrade availability for an existing booking.** Not seats.aero, not point.me, not AwardWallet, not Plusgrade. Upgrade state lives behind a logged-in session on each airline's own site, tied to a specific PNR. That is why this skill drives a browser instead of calling an API. It is not a shortcut, it is the only door.

The commercial tools in this space all solve award **search** for new bookings. Different inventory, different problem.

---

## What the market actually sells

| Product | What it has | Upgrade coverage | Cost |
|---|---|---|---|
| **seats.aero** | Award availability, 24 programs, cached, Partner API | Almost none. One Air Canada eUpgrade finder, web-only | $99.99/yr Pro |
| **point.me** | Award availability, 100+ programs | None | $129/yr Standard, $260 Premium |
| **ExpertFlyer** | GDS fare class inventory | **28 airlines only. Not United, not Delta** | $132/yr Premium |
| **Thrifty Traveler** | Human-curated deal alerts | None. Content product, not data | $129.99/yr |
| **AwardWallet** | Loyalty balances, documented APIs | Its award search API explicitly excludes upgrade inventory | Account Access API free tier exists |
| **Plusgrade** | The bidding platform itself | Strictly B2B. No consumer or developer API at all | Not available |

**Do not buy ExpertFlyer for United or Delta upgrade space.** United cut them off in Nov 2013, Delta in Sept 2014. Neither has been restored. This is the most common expensive mistake in this space.

---

## The one integration genuinely worth considering

**AwardWallet Account Access API.** The only vendor here with a free, documented, self-registrable path to user-consented balance data.

- Endpoint `business.awardwallet.com/api/export/v1`, `X-Authentication` header
- Returns balances, elite level, expiration dates, transaction history
- Free tier real, business account required but free personal accounts can upgrade
- Reads only accounts the user has explicitly shared

**What it would buy:** the wallet stops going stale. Balances and certificate expiry dates update themselves instead of relying on Graeham to remember what he had.

**What it would not buy:** any upgrade data whatsoever. Their own flight award search API explicitly contains no upgrade inventory.

**Verdict:** worth doing only if the manual wallet proves annoying in practice. Balances change slowly and certificate expiry dates are the only genuinely time-sensitive field. Do not build this speculatively. Wait until the manual version has actually failed.

---

## Dead ends, so nobody re-proposes them

- **Amadeus Self-Service.** The entire `amadeus4dev` GitHub org was archived in July 2026 and the portal is being deprecated. Anything built on it has a shelf life. Do not start here.
- **awardwiz**, the canonical open-source award scraper covering AA, Aeroplan, Alaska, Delta, JetBlue, Southwest and United. Archived, last commit Feb 2024. Dead.
- **Any Plusgrade integration.** GitHub search returns 34 repos for "plusgrade" and every one is a job-interview take-home. No API, no docs, no open-source footprint. The only way to see a bid offer is to be the passenger holding the PNR.
- **Open-source loyalty balance aggregation.** AwardWallet's GitHub org has zero public repos. The only client library ever published was archived in 2017. One working project exists, `itswcl/PointsTracker`, with zero stars.
- **Open-source fare class inventory.** Nothing touches live data. `adamf/jetway` is well built but its own docs say it is deliberately not an availability system and it ships simulated carriers.
- **puppeteer-extra-plugin-stealth and undetected-chromedriver.** Both drifting or dead. The author of undetected-chromedriver has publicly moved on. Do not build on either.

---

## borski/travel-hacking-toolkit

MIT, ~650 stars, actively maintained, 48 Claude skills plus third-party MCP servers. The closest thing to a peer project, and the obvious "should we just use this instead" candidate.

**Answer: no, for this problem.** Its entire upgrade-of-a-booked-ticket content is one sentence in its `gardening` skill and a hyperlink to a seats.aero page its own API cannot reach. Grep counts across the whole repo: PlusPoints 0, Plusgrade 0, systemwide 0, GUC/RUC 0, upgrade bidding 0, ExpertFlyer 0, upgrade waitlist 0.

It is an excellent award-search machine. It is not an upgrade tool, and adopting it would mean taking on Docker, a patched Playwright fork, plaintext bank passwords in a dotfile, and roughly $150/yr in subscriptions to acquire two lines of text.

**Worth borrowing if this skill grows:**
- `data/transfer-partners.json` and `data/transfer-bonuses.json`, both carrying `_meta.last_updated`, primary-source URLs and VERIFIED/LIKELY/UNVERIFIED confidence levels
- Its `refresh-data.yml` workflow pattern, which is **fail-closed**: a scrape returning too little writes nothing, so a bad run leaves committed data untouched rather than corrupting it
- The hold-before-transfer rule from its `award-holds` skill, already adopted into `# TRANSFER MATH`

**Explicitly do not copy** its credential handling. It asks for plaintext passwords to chase.com, americanexpress.com, aa.com and southwest.com in a dotfile, passes them to containers as `-e` flags where they land in `docker inspect`, and writes 2FA codes to a `/tmp` file the container mounts. Gitignored is not the same as safe.

---

## The legal line

Air Canada and Aeroplan are suing seats.aero's operator in federal court under the CFAA over roughly 265,000 scraped routes. Settlement talks hit impasse in Feb 2026.

**This skill stays on the safe side by design.** It drives Graeham's own logged-in session, on his own booking, at human pace, and collects nothing in bulk. That is a categorically different activity from operating a scraping service.

Any future proposal involving automated collection across accounts, routes or users is a legal question before it is a technical one. Raise it as such rather than treating it as an engineering decision.

---

## If more automation is genuinely wanted

In order of value per unit of effort:

1. **Scheduled sweeps.** Zero new dependencies. Register the 72-hour and 24-hour checks as scheduled tasks so the checkpoints actually happen. This is where nearly all the real-world value sits, because the most common failure is simply forgetting to look again.
2. **United Expert Mode parsing.** If United is the usual carrier, reading `PZ` from an already-open logged-in page turns the single most important input from an estimate into a fact. No API, no subscription, no new legal surface.
3. **AwardWallet balance sync.** Only after the manual wallet has actually proven annoying.
4. **Everything else.** Cost exceeds benefit for one person's flights.
