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

## Automated balance sync: blocked by the airlines themselves

AwardWallet has a documented API and it looks like the obvious fix for a manual wallet. **It does not work for the carriers that matter.**

American forced AwardWallet to drop AAdvantage entirely in Dec 2021. Delta, United and Southwest are reduced to email statement forwarding with no login-based tracking at all. The airlines closed this door deliberately.

So automated balance sync covers hotel programs and some smaller airlines, and misses every US major. Their flight award search API also explicitly contains no upgrade inventory.

**Verdict: do not build this.** The manual wallet is not a compromise, it is the only thing that works for United, Delta, American and Southwest. Keep it current by asking at the start of each audit rather than trying to automate around a wall the airlines put up on purpose.

---

## Dead ends, so nobody re-proposes them

- **Amadeus Self-Service. Decommissioned 17 July 2026.** Not deprecated, gone. New registrations paused in March, existing API keys disabled in July, and the registration URLs now 301 to the root. Verified first-hand. The enterprise portal survives but requires a commercial agreement. This was the only self-service API that exposed real booking-class letters, which is why it keeps getting suggested. It no longer exists.
- **Every commercial flight API, for a different reason than you would guess.** Seat maps and order changes bind to an offer the API itself generated or an order the API itself created. Duffel states it plainly: seat maps accept `offer_id` only, and it does not support selecting a seat after an order exists. Travelport PNR retrieval is ownership-scoped and needs claim authority. NDC Order Retrieve is channel-scoped. **No vendor at any price accepts a confirmation code for a booking made somewhere else.** That single fact rules out the entire category, not just the free tiers.
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

## What the airline sites actually do to automation

Measured directly, 2026-09-06. This is why `# CHASE` uses Graeham's own already-open browser instead of launching a fresh one.

| Site | Edge | Bot manager | Plain request result |
|---|---|---|---|
| **united.com** | Akamai | Akamai Bot Manager | **TCP reset, no HTTP response at all.** Blocked below the HTTP layer. The hardest |
| **aa.com** | Akamai | Akamai Bot Manager | **403 Access Denied** before any HTML is served |
| **delta.com** | Akamai | Akamai Bot Manager | 200 shell, but `_abck` carries the `~-1~` "sensor not validated" flag |
| **southwest.com** | Akamai | Akamai Bot Manager | 200, plus a `terms-of-service` header shipped in-band on every response |
| **alaskaair.com** | Fastly + Azure Front Door | **None observed** | 200, no challenge. Analytics cookies only |

**Alaska is the outlier.** No Akamai, no bot-management cookies, no anti-bot script on the pages probed. If a flight happens to be on Alaska, this is materially easier. Their login and shopping POST endpoints were not tested, so do not assume it holds everywhere.

### Why session reuse works and cookie export does not

This is the distinction that decides whether an approach works at all.

Akamai's `_abck` cookie carries a signed prefix describing the browser that earned it. The edge cross-checks it against the presenting connection's TLS fingerprint, HTTP/2 frame ordering and IP reputation. **Move the cookie to a different stack or a different IP and it fails.** The trust window also ages out, so the page's own JS has to keep the sensor alive.

Practical translation: keep driving the same real Chrome profile from the same IP that logged in. Never dump cookies into a script.

### Why low volume helps, but only partly

Two layers, and they behave differently.

- **Volume-insensitive:** TLS fingerprint, HTTP/2 frame ordering, IP reputation, headless-runtime tells. All evaluated on request one. A single badly-fingerprinted request fails exactly as hard as ten thousand, which is why one plain `curl` got a TCP reset from United.
- **Volume-sensitive:** behavioral scoring and account-side velocity locks. Here low volume genuinely helps.

So running real Chrome solves the first layer by not lying, and human pace solves the second. **Residential proxies are counterproductive:** they move him off the IP his account normally logs in from, which is itself a security signal, and solve a problem he does not have at home.

---

## The legal line, and the more likely risk

Air Canada and Aeroplan are suing seats.aero's operator under the CFAA over roughly 265,000 scraped routes. American won a $9.4M jury verdict against Skiplagged in Oct 2024, notably on **copyright** rather than CFAA, now on appeal.

**But the realistic downside here is not a lawsuit.** Those cases target people operating services at scale. For one person checking their own booking, the exposure is account-side: Delta prohibits crawler and scraper access and audits accounts without notice, and United reserves audit rights with termination and mile forfeiture.

The thing to protect is the MileagePlus balance, not a legal position.

**This skill stays clear by design.** It drives Graeham's own logged-in session, on his own booking, at human pace, and collects nothing in bulk. Any future proposal involving automated collection across accounts, routes or users is a different activity, and a legal question before it is an engineering one.

---

## The per-carrier playbook

| Carrier | Best path | Why |
|---|---|---|
| **United** | **Expert Mode on united.com.** Free | `PZ` is airline-internal and not published to the GDS, so no tool can sell it. Expert Mode puts it in his own logged-in page. Their ToS is a flat prohibition on automated access with no commercial carve-out, so read the page, do not crawl the funnel |
| **American** | **Buy ExpertFlyer**, $6.99 to $12.99/mo | AA is covered, showing `C` and `A`. Their ToS clause is scoped to "business or commercial purposes," which a personal subscription sidesteps entirely. Cheaper and safer than automating aa.com, which 403s anything that is not a browser |
| **Delta** | **Check by hand.** No good path exists | No ExpertFlyer coverage, Akamai on the site, and a demonstrated willingness to lock 68,000 accounts at once. Not worth the risk for a domestic upgrade |
| **Alaska** | Easiest. No bot management observed | If the flight is on Alaska, this is the soft case |
| **Air Canada** | Mock booking with the eUpgrade display option | Shows `R` space plus the co-pay |

---

## If more automation is genuinely wanted

In order of value per unit of effort:

1. **Scheduled sweeps.** Zero new dependencies, no new legal surface. Register the 72-hour and 24-hour checks as scheduled tasks so the checkpoints actually happen. **This is where nearly all the real-world value sits**, because the most common failure is not a missing API, it is forgetting to look again.
2. **United Expert Mode.** Turns the most important input from an estimate into a fact, for free.
3. **ExpertFlyer, only if he flies American.** Do not buy it otherwise.
4. **Everything else.** Cost, effort or risk exceeds the benefit for one person's flights.
