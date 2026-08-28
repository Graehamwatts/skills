---
name: listing-remarks-writer
description: "MLS listing remarks writer optimized for AI-powered home search (ChatGPT with Zillow, Perplexity, Google AI Overviews) and Bay Area buyers. Writes to a hard character budget (MLSListings public remarks = 1300 characters), never repeats the address or the bed/bath/sqft/lot/year stat line the MLS data card already carries, walks the buyer through the property as if touring it, and adapts framing to condition tier (fixer / mid / move-in / renovated / new). Use this skill ANY time the user asks to: write listing remarks, write MLS description, draft listing copy, write property remarks, rewrite a stale listing, optimize a listing for AI search, write public remarks for a new listing, draft remarks for a fixer or renovated home, or improve an existing listing description. Also use for property flyer, brochure, postcard, and single-property-site body copy. Trigger when the user uploads listing photos and asks for the description, mentions a new listing, or pastes property details and wants the listing copy. Localized for Graeham's Bay Area markets (East Palo Alto, Redwood City, Palo Alto, Menlo Park, San Mateo County) with California-specific framing."
---

# Listing Remarks Writer

Write MLS listing descriptions that fit the field, surface in AI-powered home search, and never repeat what the data card already says.

Buyers increasingly search through ChatGPT (with Zillow integration), Perplexity, and Google AI Overviews. Those platforms read the structured listing fields and the public remarks text. They cannot interpret photos, 3D tours, video tours, or captions. Any feature that lives only in a photo is invisible unless the remarks name it — and the remarks only hold about 1,300 characters, so every one of them has to earn its place.

Two rules govern everything below. Both are hard gates, not preferences.

---

## RULE 1 — The character budget is a hard gate

**Never deliver remarks without mechanically counting them first.** Not estimating. Counting.

### Limits

| MLS / surface | Public remarks limit | Confirmed |
|---|---|---|
| **MLSListings (Graeham's default MLS)** | **1,300 characters** | Yes — 2026-08-25 |
| Any other MLS | **ASK the agent** | — |
| Flyer / brochure / postcard body | Ask, or write to the template's word count | — |
| Social caption | Platform limit, but write far shorter | — |

The 1,300 figure includes spaces and punctuation. Never assume a limit for an MLS you haven't confirmed, and never carry a number over from another board. If the agent doesn't know, write to 1,300 — it's the safest common denominator, and a short remark is always publishable while a long one gets truncated mid-sentence by the field.

> **History:** this skill previously defaulted to 1,500, which put every draft roughly 200 characters over the real field limit. If a draft is ever rejected as too long, the first thing to check is whether the limit in this table is still correct for the board being used.

### Target band: 1,200–1,300 characters

Under 1,200 wastes budget — that's 100+ characters of searchable feature nouns left on the table, and AI search ranks on what the text actually names. Over 1,300 gets truncated by the MLS. Land inside the band.

### The mandatory loop

1. **Reserve first.** Before writing a word, subtract the characters required by any mandatory language — verification hedges, tenant-occupancy disclosure, permit notes. A verification sentence runs 120–180 characters. If the listing needs one, you're writing a 1,120-character body, not a 1,300-character body.
2. **Draft** to the section allocation below.
3. **Count it:**

```bash
python scripts/charcount.py draft.txt 1300
```

   The script collapses whitespace the way the MLS field does, reports over/under, and prints a per-sentence cost table so the trim pass targets the expensive sentences instead of guessing. It exits 1 when over the limit.
4. **If over:** run the trim ladder. **If under 1,200:** run the fill ladder.
5. **Recount.** Repeat until inside the band.
6. **Deliver** with the count stated.

If the counting script isn't available for some reason, count with `python -c "print(len(open('draft.txt').read().strip()))"` or any equivalent. Eyeballing the length is what caused the problem this rule exists to fix.

### Trim ladder — cut in this order

1. **Data-card recitals.** Address, bed/bath count, square footage, lot size, year built, `City, County, ZIP` close. See Rule 2. Usually recovers 150–250 characters on its own.
2. **Zero-information adjectives.** stunning, gorgeous, spacious, welcoming, beautiful, charming, must-see, dream, rare, one-of-a-kind. AI search ignores them and buyers skim past them.
3. **Filler openers and connectives.** "Step inside to," "You'll love," "This home offers," "Located in," "Boasting." Start the sentence at the noun.
4. **Redundant pairs.** "parking and storage" when the garage sentence already said both. "room to gather, work, or set up separate zones" survives; "flexibility" after it does not.
5. **Long lists trimmed to the three strongest items.** Six kitchen features cost 90 characters more than three and rank no better.
6. **Compress, don't delete, the location close.** "Located approximately five minutes by car to Caltrain service at the Palo Alto station" → "Caltrain at the Palo Alto station is roughly five minutes by car." Saves 20+ characters, same facts.

**Never trim these to hit the limit:** material disclosures, verification language, condition honesty on a fixer, or the one feature that makes the listing distinct. If the remarks won't fit with all of those in, cut a whole optional section (secondary bedrooms, systems) instead of shaving the required parts.

### Fill ladder — when under 1,200, add in this order

1. Finish materials by name (quartz, white oak, butcher block, slate).
2. Appliance and system specifics with years (2023 HVAC, five-burner gas range, tankless water heater).
3. Layout and orientation facts (rear-facing primary, ground-floor bedroom, north light).
4. Outdoor use detail (covered patio, raised beds, fenced dog run).
5. Named nearby landmarks, transit, and employers.

### Section allocation for a 1,300-character remark

Rough guide, not a straitjacket. Shift budget toward whatever the condition tier says to emphasize.

| Section | Characters |
|---|---|
| Opening — what it is, where, what's distinct | 120–160 |
| Approach / curb appeal | 100–140 |
| Living, dining, kitchen | 280–340 |
| Primary suite | 120–160 |
| Secondary bedrooms + baths | 80–120 |
| Outdoor space + parking | 150–200 |
| Systems + upgrade years | 80–120 |
| Location close | 140–180 |
| Reserve: disclosures / verification | 0–180 |

---

## RULE 2 — Don't repeat the data card

The MLS already publishes a structured data card next to the remarks: street address, city, ZIP, beds, baths, square footage, lot size, year built, parking, APN, HOA, taxes, school district. Every syndication feed (Zillow, Redfin, Realtor.com, Compass) carries those fields, and every AI search layer built on top of them reads the fields directly. Reciting them in the remarks buys nothing and burns 200–300 characters of a 1,300-character budget.

**Defaults:**

- **No street address in the remarks.** Not in the opening, not in the close.
- **No bed / bath / square-foot / lot-size / year-built recital.** Open with what the home is like, not with its stat line.
- **No `City, County, ZIP` tag line at the end.** Old web-SEO habit. It reads as filler to a buyer and adds nothing an AI engine can't already see in the fields.
- **City and neighborhood may appear once**, naturally, in prose. Subdivision names often aren't in a clean structured field, so they earn their place. Once is enough.

**The exception — when a spec IS the argument.** State a number when the sentence is making a point with it, not listing it:

- Lot size when the pitch is a lot split, an ADU, or an expansion ("a parcel this size may open the door to…")
- Year built when the condition framing depends on it ("original to its 1962 build")
- Square footage when a layout claim needs the scale ("over 3,000 square feet across two wings")
- Bed count when the configuration is the feature, not the count ("two of the four bedrooms sit on the ground floor")

If you cut the number and the sentence still makes the same point, it was a recital. Cut it.

### Other surfaces (flyers, brochures, social, email)

The same rule holds anywhere the piece already prints a spec block. Flyers, brochures, just-listed postcards, and single-property sites all carry the address and stat line in their own template, usually in larger type than the body copy. Repeating it in the paragraph makes the piece read like three people assembled it.

| Surface | Spec block present? | What the body copy does |
|---|---|---|
| MLS public remarks | Yes, structured fields | Features only, ≤1,300 characters |
| Property flyer / brochure | Yes, template header | Features only; write to the template's word count |
| Just-listed postcard | Usually address + beds/baths | Features only; 2–3 sentences |
| Listing web page / single-property site | Yes, spec table | Features only |
| Social caption | No | Stat line once, compressed, then features |
| Text / DM to a buyer | No | Stat line once, compressed |

When the surface has no spec block, give the stat line once in a single compressed clause and move on. Never twice.

---

## Before You Start — Read These

1. **`../shared-references/identity.json`** — Graeham's brand identity. NEVER hardcode contact details, DRE, or brokerage from memory.
2. **`../content-creation-engine/references/market-config.md`** (optional) — full neighborhood list, jurisdiction terms. Use for Graeham's primary markets.
3. **`../comedy-craft/SKILL.md`** (optional) — when a remark calls for one line of dry character. Keep it rare: remarks stay noun-dense first, character second, and wit costs characters.

---

## Fair Housing + RESPA Guardrails (Non-Negotiable)

NEVER write remarks that:

- Reference race, religion, national origin, family status, disability, or sex
- Use coded language: "safe neighborhood," "good area," "family-friendly," "up-and-coming," "exclusive community," "great for families," "perfect for empty nesters"
- **Mention school quality, ratings, rankings, awards, or "improving" / "concerning" framing.** This is the most common Fair Housing trap in real estate marketing. HUD has treated school-quality language as a demographic proxy; NAR Code of Ethics Article 10 prohibits it explicitly.
  - You MAY factually name the district ("Ravenswood City School District") — though it's in the MLS metadata anyway, so it usually isn't worth the characters.
  - You MAY note distance to a named school as a walkability fact ("within 0.4 miles of Costaño Elementary").
  - You may NOT call schools "top-rated," "blue ribbon," "award-winning," "highly rated," or "improving" — no quality assessment at all, positive or negative.
- Promote kickback arrangements with lenders, inspectors, title companies, or other vendors (RESPA)
- Imply preference for or steering toward buyers based on protected characteristics

For location, stick to: property types, price tiers, lot sizes, proximity to amenities (parks, transit, dining, retail, employers), architectural styles, age of housing stock, HOA structure, walkability and commute facts.

---

## Truth-in-Advertising Rules (Non-Negotiable)

**ADU / lot-split language — only when verified, or explicitly hedged.** Never write "ADU potential," "ADU-ready," "buildable lot," "SB 9 eligible," "can add a unit," or "JADU possible" as a flat claim unless the agent has confirmed all three:

1. Local zoning permits it on this lot type, AND
2. The lot meets minimum size / setback requirements for the jurisdiction, AND
3. No HOA / CC&R / easement restriction blocks it

If any answer is unsure, you have two options: omit the language entirely, or write it as possibility plus an explicit buyer-verification sentence in the same remark:

> "A parcel this size may open the door to a lot split under California SB 9, an ADU, or a junior ADU. All development potential, permit history, square footage, and buildability to be verified by the buyer with the City of [jurisdiction] and [county]."

That verification sentence costs about 140 characters. Reserve them before drafting. Bay Area ADU and SB 9 rules differ by city and change yearly — what's allowed in unincorporated San Mateo County may not be allowed in Palo Alto.

**Square footage** — recorded figure from county records or MLS. Never round up, never combine living with garage/basement/sunroom without labeling it.

**Lot size** — recorded figure. Don't estimate from photos or satellite.

**Year built** — recorded figure. "Originally built [year], renovated [year]" is fine; implying newer construction is not.

**Solar / EV / smart home** — only if installed and operational. "Solar-ready" requires pre-wiring; "solar-equipped" requires panels producing.

**Permits** — never call anything "permitted" without confirmation in county records. Many Bay Area additions are unpermitted.

**When the county record and the walkthrough disagree** (a 2-bed record with four bedrooms on the tour, common with unpermitted additions): do not publish either number. Leave bed/bath/sqft out of the remarks entirely — Rule 2 already says to — and flag the discrepancy to the agent so they resolve it before the structured fields go live.

When in doubt, omit. A shorter accurate remark beats a longer one with a claim that can't be defended.

---

## Condition-Aware Framing

Get the condition tier from the agent at intake. Don't guess from photos.

| Condition tier | Spend the budget on | Skip |
|---|---|---|
| **Fixer / contractor special** | Lot, location, bones (foundation, roof structure, layout), footprint, honest condition statement. "Bring your contractor," "value-add," "blank canvas" — only when accurate. | Cosmetic finishes being replaced anyway. Don't name dated materials; just say the home is original. |
| **Mid-range / livable but dated** | Honest condition, layout flow, location, genuine standouts (large lot, recent roof, updated kitchen). Say what's been updated and what hasn't. | "Lovingly maintained" and other signal-free filler. Don't oversell mid as turnkey. |
| **Move-in ready** | Upgrades with year stamps (kitchen 2023, HVAC 2024, roof 2022), finish materials by name, systems. | Rooms untouched since the build. Let photos carry those. |
| **Renovated / fully remodeled** | Full material stack, down-to-the-studs framing if accurate, smart home, EV charging, solar production. | Pretending it isn't a flip if it is. Buyers can tell. |
| **New construction** | Year built, builder name, warranty, energy ratings, pre-wiring, finish package level. | Comparisons to older neighbors. |

**Special cases:**

- **Tenant-occupied:** must disclose. "Currently tenant-occupied at $X/mo, lease terms available." Reserve the characters.
- **Multi-unit / income:** lead with unit mix and current rents, then features.
- **Probate / trust sale:** mention factually if relevant to disclosures.
- **Short sale / REO:** disclose accurately.

---

## The Walkthrough Structure

Write as if walking the buyer through the property, in the order they'd experience it — more readable for humans, scans more naturally for AI search. Adjust for property type; condos skip outdoor sections, multi-units lead with layout.

1. **Opening — what it is and what's distinct.** [Condition modifier] [property type] in the [neighborhood] of [city], plus the single most distinctive thing about the home. No stat recital. AI platforms truncate and summarize, so the first 50 words carry the most weight: spend them on what separates this listing from the eight others in its price band.
2. **Approach + curb appeal.** Street position, exterior style, landscaping, driveway, entry. Physical only. "Quiet residential street with mature trees" is fine; "great neighborhood" is not. **Never itemize individual tree/plant species** ("a Japanese maple, a mature pine, and a towering palm") — nobody searches by tree species and it reads as padding. Use one collective phrase ("mature landscaping," "mature fruit trees") and put the budget toward features buyers actually search on. (Graeham, 2026-08-28: "the info on trees is terrible who cares... listing each tree is dumb.")
3. **Entry + main living areas.** Foyer, then flow through living, dining, kitchen. Kitchen is the hero of most listings: name materials, appliance detail, and layout features.
4. **Primary suite.** Bedroom features plus bathroom features, and where it sits in the home.
5. **Secondary bedrooms + baths.** Count of shared baths, layout, standouts.
6. **Outdoor space.** Yard use, hardscape, landscaping, fencing, garage and parking. ADU or lot-split language only per the Truth-in-Advertising rule.
7. **Systems + recent upgrades, year-stamped.** HVAC, roof, solar, electrical, plumbing, windows.
8. **Location close.** Nearest Caltrain station, freeway access, employers, parks and landmarks. End on a concrete commute or landmark fact — no `City, County, ZIP` tag.

---

## Bay Area Context

Name the Caltrain station, freeway access, and major employers when present. Bay Area buyers prioritize commute facts, and those nouns are what AI search matches on.

**East Palo Alto:** Meta HQ (1 Hacker Way), Stanford Research Park, Cooley Landing, Bay Trail, Ravenswood shopping. Neighborhoods: Woodland Park, Weeks, Gardens, Westside, University Village. Caltrain via Palo Alto or Redwood City. 101 and Dumbarton Bridge.

**Redwood City:** downtown Caltrain, 101, Courthouse Square. Neighborhoods: Mt. Carmel, Stambaugh-Heller, Friendly Acres, Centennial, Roosevelt, Edgewood Park, Emerald Hills. Oracle, Box, Electronic Arts.

**Palo Alto:** Stanford, University Avenue, Caltrain (downtown + California Ave). Neighborhoods: Crescent Park, Old Palo Alto, Professorville, Community Center, Midtown, Barron Park, Greenmeadow.

**Menlo Park:** Sand Hill Road, Stanford, Santa Cruz Avenue, Caltrain. Neighborhoods: West Menlo, Allied Arts, Linfield Oaks, Sharon Heights, Belle Haven, Willows.

**San Mateo County:** 101, 280, Caltrain spine, SFO. San Mateo, Burlingame, Foster City, San Carlos, Belmont, Half Moon Bay.

Eichler and mid-century are worth naming when accurate — Bay Area buyers search those terms directly.

---

## Phase 0 — Address-First Research (Optional)

Use when the property has prior online presence (relist, expired-then-renewed, previously rented or sold) and you want the intake pre-populated from public data. Skip for new construction, pocket listings, or when the agent already gave you the specs.

Triggered by the agent giving only an address, or saying "run Phase 0" / "research the listing first."

1. **Search the address** across Zillow, Redfin, Realtor.com, and Compass (Claude in Chrome MCP if connected, WebFetch otherwise). Pull beds, baths, sqft, lot, year built, tax and sale history, HOA, style, exterior features, noted renovations.
2. **Pull prior remarks verbatim** if previously listed, with dates, list and sold prices, DOM, and outcome (sold / expired / withdrawn).
3. **Summarize prior themes** in 3–5 bullets: what they emphasized, what tone, what they omitted, and any compliance-risky claims (Fair Housing proxies, unverified ADU language, school-quality claims) so we don't repeat them.
4. **Present findings in two labeled sections** — "Specs Found Online" and "Themes from Past Listings" — then ask: are these still accurate, what's the condition tier, what's not in the online data, and should we match or diverge from the prior voice?
5. **Wait for confirmation** before drafting.

**Hard rules:** never fabricate specs; if sources disagree, present both and ask. Never reuse prior remarks verbatim — copyright, plus it re-imports the prior agent's compliance errors. Always flag compliance issues you found. County records trump web sources.

---

## Intake

If Phase 0 ran, items 1–4 are already answered. Collect the rest in one message.

1. **Property address** (street, city, ZIP)
2. **Property type**
3. **Beds / baths / sqft / lot size / year built** — verified, for context and fact-checking even though they won't appear in the remarks
4. **Condition tier**
5. **Recent upgrades with years**
6. **Standout features to emphasize**
7. **Neighborhood / subdivision**
8. **Nearby amenities** (parks, transit, employers — named, not rated)
9. **Output surface + character limit** — MLS remarks (1,300 on MLSListings; ask for any other board), flyer, brochure, postcard, single-property site, social. Confirm whether the surface prints its own spec block.
10. **ADU / lot-split status** — zoning permitted? lot qualifies? HOA/CC&R checked? If any answer is unsure, omit or hedge per the Truth-in-Advertising rule.
11. **Compliance flags** — HOA, Mello-Roos, flood zone, special assessments, easements, tenant occupancy
12. **Photos** (optional) — use them to sequence the walkthrough and catch features the agent didn't mention

Don't proceed without 1–4 and 9. The rest improve quality but aren't blockers.

---

## Example 1 — East Palo Alto, move-in ready

**Input:** 4 bed, 3 bath single-family, 2,400 sqft, 6,500 sqft lot, built 1962 / renovated 2023, Woodland Park, white oak floors, quartz kitchen, gas range, primary suite with walk-in closet, new HVAC + solar, two-car attached garage, near Cooley Landing + Bay Trail. Condition: move-in ready. ADU: not verified (omit). Limit: 1,300.

**Output — 1,239 characters:**

Renovated single-family home in the Woodland Park neighborhood of East Palo Alto, mid-block on a quiet street with mature trees and a new concrete driveway leading to a covered entry. The foyer opens to a main level with white oak hardwood floors throughout. The living room takes oversized front-facing windows and connects to a dining area with contemporary lighting and a sliding door to the patio. The kitchen anchors the space with white quartz counters, a five-burner gas range, stainless appliances, a tiled backsplash, and an island seating four. A walk-in pantry sits just off the kitchen. The primary suite occupies the rear with a vaulted ceiling, walk-in closet, tiled shower, and double vanity. Three additional bedrooms share two full baths in a separate wing. Out back, a fenced yard holds a covered patio, mature fruit trees, and turf landscaping. The attached garage has direct interior access, with a laundry room off the entry. A new HVAC system and roof-mounted solar installed in 2023 cut monthly utility costs. Caltrain at the Palo Alto station is roughly five minutes by car, with Highway 101 and Dumbarton Bridge access nearby. Meta's Menlo Park headquarters, Stanford, and Cooley Landing are all a short drive out.

**What's absent and why:** the bed/bath count, 2,400 sqft, 6,500 sqft lot, garage capacity, and a `City, County, ZIP` close — roughly 190 characters the data card already carries. That budget went into finish and layout detail instead.

---

## Example 2 — Same property, fixer tier

**Output — 1,228 characters:**

Single-family home on an oversized lot in the Woodland Park neighborhood of East Palo Alto, with a flexible single-level floor plan and strong bones for renovation. Original to its 1962 build, the home keeps its mid-century footprint: an open main living area, a separate primary suite, and three additional bedrooms in a secondary wing. Hardwood floors run throughout under existing carpet. The kitchen and baths are original and ready for updating. Outside, the lot carries mature fruit trees, a detached patio area, a long driveway parking three cars, and an attached garage with direct interior access. Lot dimensions may support an expanded footprint or a second unit, to be verified by the buyer with the City of East Palo Alto. Mechanical systems and roof are original, so plan for system upgrades alongside cosmetic work. Caltrain at the Palo Alto station is roughly five minutes by car, with Highway 101 and Dumbarton Bridge access nearby. Meta's Menlo Park headquarters, Stanford, and Cooley Landing are all a short drive out. Ravenswood shopping, Cooley Landing, and the Bay Trail sit within a few minutes. Woodland Park has seen significant renovation activity in recent years. Bring your contractor and your vision.

**The Rule 2 exception in action:** 1962 stays, because the condition argument depends on it. The lot is called "oversized" rather than numbered — the number is in the fields, the judgment is not. The expansion line is hedged, not claimed, because zoning wasn't verified.

---

## Example 3 — Budget-constrained rewrite (430 Garden St, East Palo Alto)

The agent's draft ran 1,428 characters against a 1,300 limit: 128 over. The stat recital and filler carried the overage.

**Output — 1,299 characters:**

Single-level home on a 10,113-square-foot lot. A wide front yard, long driveway, and covered entry lead into a bright living room with large windows and light wood flooring that opens to the dining area. The kitchen offers abundant cabinetry, granite-style counters, stainless appliances, a gas range, recessed lighting, and storage, with access to the side and rear of the home. Multiple living areas give room to gather, work, or set up separate zones. Bedrooms are well sized and take in natural light. The primary retreat holds space for a sitting area or desk, plus an attached bath with dual vanity and shower. Additional baths carry modern tile, refreshed vanities, and neutral tones. Out back, an expansive fenced yard opens to patio areas, mature trees, and open ground for entertaining, gardening, play, or pets. A detached rear garage and extended driveway add parking and storage. A parcel this size may open the door to a lot split under California SB 9, an ADU, or a junior ADU. All development potential, permit history, square footage, and buildability to be verified by the buyer with the City of East Palo Alto and San Mateo County. Close to Palo Alto, Menlo Park, Stanford, Meta, Amazon, Ravenswood shopping, the Bay Trail at Cooley Landing, Highway 101, and the Dumbarton Bridge.

**Where the 129 characters came from:** the `East Palo Alto, California` in the opening and the `East Palo Alto, San Mateo County, 94303` close (Rule 2, ~65), "welcoming" / "spacious" and other zero-information adjectives (~20), "Step inside to" and similar filler openers (~25), "stainless steel" → "stainless" and "independently verified" → "verified" (~19). The lot size stayed — it's carrying the SB 9 argument. Google and one park reference were dropped from the closing list, which already named five employers.

---

## Humanizer Final Pass (Mandatory)

Run the draft through the `humanizer` skill before delivering. Remarks are read by humans on Zillow, Redfin, and Compass, and increasingly quoted by AI search engines. Both penalize obvious AI patterns.

**Humanize:** the walkthrough prose, any variation labels, the location close.

**Do NOT humanize:** any recorded number that survived the Rule 2 cut (a lot size carrying an SB 9 pitch, a year built carrying condition framing), material disclosure flags, and verification language — those stay exact.

**Order matters:** humanize, then recount. The humanizer pass changes length, sometimes by 60+ characters. A draft that passed the count before humanizing can be over after it. Count again, always, as the last step before delivery.

If the humanized version drops below the searchable-noun threshold or cuts a verified fact, redo the pass with an explicit instruction to preserve the named nouns.

---

## Output Format

Deliver the remarks as a single block of plain text — no headers, no bullets, no formatting — so it pastes straight into the public remarks field. If variations are requested (short + long, or A/B), label each block separately and count each one.

After the remarks, always provide:

- **Character count** against the stated limit, from an actual count
- **Top 5 searchable nouns** the description loaded
- **Compliance check** — no school-quality language, no demographic proxies, no unverified ADU/permit claims, no RESPA issues
- **Data-card check** — no street address, no bed/bath/sqft/lot/year recital, no `City, County, ZIP` close; for any number that stayed, name the argument it carries
- **Humanizer confirmation**

### Delivery checklist — all five must be true

1. Counted mechanically, not estimated
2. Inside the 1,200–1,300 band (or the confirmed limit for the board in use)
3. No data-card recital
4. Every claim verified or hedged
5. Humanized, then recounted

---

## Used By

- **Standalone** — writing or rewriting remarks for a new or stale listing.
- **`content-creation-engine`** — pulls the remarks via this skill as the source-of-truth description, then generates downstream blog / social / video copy from it.
- **`listing-launch-engine`** — uses the remarks as the anchor copy for the launch sequence.
