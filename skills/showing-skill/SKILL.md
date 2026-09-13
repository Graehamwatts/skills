---
name: showing-skill
description: "Builds a buyer showing tour for Graeham Watts. Trigger ANY time the user mentions: showing tour, tour sheet, showing schedule, properties to show a client, showing order, showing appointments, confirm showings with agents, showing spreadsheet, or pastes/attaches MLS listings (Agent Full / Client Page exports, a routed map PDF, or a screenshot of a map/list of properties) with a request to plan or organize a buyer tour. Also trigger when the user gives a start time and a list of addresses and wants them turned into a timed schedule with agent outreach."
---

# Showing Skill

Turns a set of MLS listings into a timed buyer-tour schedule, figures out which listing agents need to be contacted before showing (and how), sends that outreach, and produces two spreadsheets: one for the client to carry, one working copy for Graeham with agent info and contact status.

Graeham Watts is a REALTOR at Compass (DRE# 01466876). Brand details (name, brokerage, DRE, phone, email) must always come from `../shared-references/identity.json` — never hardcode them. See that file's `_schema` block for the rule and why it exists.

---

## When to Trigger

- "Build a showing tour for [client] — here are the properties"
- A pasted/attached MLS export (Agent Full report, Client Page report) or a screenshot of a Matrix map/list view, plus a request to plan or schedule a tour
- "What time will we be at [property]" type questions about an in-progress tour (answer directly; only re-run the full skill if the underlying schedule actually changed)

## Step 1 — Gather the Inputs

You need, per property:
- Address, city, zip, price, beds/baths, sqft, lot size, DOM, MLS#
- Occupancy (Vacant / Owner Occupied) and any stated notice requirement
- Showing/access instructions (lockbox location or code process, "go and show" vs "text/call/email agent", open house times)
- Listing agent (and co-listing agent if any): name, brokerage, phone, email

**Where this usually comes from:** an MLS Matrix "Agent Full" PDF export (has the private remarks, showing instructions, and agent contact block that the "Client Page" export omits) plus a routed map/directions PDF if the user has one exported from Matrix — that map PDF is often the fastest source of both **the intended showing order** and **real drive times between stops** (look for a "Turn-by-Turn Directions" section with per-leg mileage/minutes). Prefer those real drive times over guessing from a generic city map.

If PDF image rendering fails in this environment (missing `pdftoppm`/poppler), fall back to text extraction with `pypdf` (`PdfReader(...).pages[i].extract_text()`) — the Agent Full text layer reliably contains the showing-instructions and contact-information blocks even when image rendering isn't available.

**Don't over-ask.** If the user hands you the PDFs/screenshot and a start time, that's enough to proceed — confirm only genuine ambiguities (see Step 4).

## Step 2 — Determine the Showing Order

If a routed map export already assigns stop numbers with turn-by-turn directions, that IS the order — use it as-is, don't re-optimize it. Only compute your own order (nearest-neighbor by city/cross-street, confirmed with the user) if no route was given.

## Step 3 — Categorize Each Property (the core judgment call)

For each property, decide: **does the listing agent need to be contacted before this showing, and how?** This is a reading-comprehension task over the private remarks and showing-instructions fields — there's no reliable regex for it. Contact is needed if ANY of:

- **Occupied by Owner** — always needs a real appointment request, not just a courtesy notice
- **A notice period is stated** (e.g., "24-Hour Notice Required") — flag prominently if the tour is happening on shorter notice than that; still send the request, but tell the user this stop may get declined or need to move
- **Instructions explicitly say to contact the agent for access** (e.g., "text agent for lockbox code," "text LA then go") — even if the property is vacant and technically "go and show," a code you don't have is a hard blocker
- **Instructions are incomplete** — e.g., "vacant, go anytime" with no lockbox code or location given anywhere in the listing. Don't assume access will work out; flag it and ask

A property needs **no contact** only when it's vacant, no notice period is stated, and the access method (lockbox code or location) is fully spelled out in the listing.

For each property that needs contact, also decide the **channel** the listing specifies:
- `email` — instructions explicitly say to email, or say nothing more specific than "contact agent" → email is sufficient on its own
- `text` or `call_or_text` — instructions specifically say text or call. **Still send a courtesy email** (redundancy helps when access is time-sensitive and agents don't all check text/email at the same rate), but the real requirement is a text or call, and Claude cannot send SMS or place calls. Flag these clearly to the user rather than treating the email as if it satisfies the requirement.

## Step 4 — Nail Down the Schedule (ask if genuinely ambiguous)

Defaults, unless the user says otherwise:
- **15 minutes per showing**
- **Real drive time between stops** from the map export (fall back to ~15-20 min general estimate only if no map data exists)
- **30-minute arrival windows**, not exact times — this matches how Graeham actually talks to agents ("between 1:30 and 2:00"), not a single promised minute
- Stop 1's window starts at whatever start time the user actually gives for stop 1 — don't re-derive it from a rule of thumb if the user already stated a concrete window or time for the first stop

Chain each later stop's *nominal* start off the *previous stop's rounded nominal start* (not the end of its window) + showing time + drive time, then round to the nearest 5 minutes and widen into a 30-min window. This keeps window width constant across the day instead of compounding.

**Ask the user directly, don't guess, when:**
- The stated start time/date is genuinely ambiguous or self-contradictory (e.g., two different anchor times given in the same breath) — getting this wrong means emailing wrong times to real agents
- It's unclear whether emails should send immediately or be drafted for review first — sending messages on the user's behalf always needs an explicit go-ahead, not an inferred one, even when the rest of the task is fully specified
- Whether to include a callback phone number in the outreach, and which one

## Step 5 — Send the Outreach

Once the user has confirmed send-vs-draft: for every property needing contact, email the right recipient — whoever the listing instructions point to (the co-listing agent if THEY'RE the one named for access, not just whoever is listed first), cc'ing any other listed co-agent. Keep it short and in Graeham's actual voice: casual-professional, a few sentences, signs off "Thanks, Graeham" (check a couple of his real sent emails to agents via the Gmail connector if unsure of tone — don't invent a more formal register than he actually uses). Always:
- Give the specific time **window** for that property, never a single exact time
- Name the buyer relationship generically ("I have a buyer touring homes today") — don't expose the client's name to a third-party agent unless the user says to
- For owner-occupied/notice-required stops: explicitly acknowledge if notice is short, and ask if it's workable
- For vacant-but-need-code stops: ask for the code/access method directly
- Sign with Graeham's real signature pulled from `identity.json` (name, brokerage, DRE, phone if the user wants one included)

For every property whose channel is `text` or `call_or_text`, do **not** stop at the email — compile a short list (property, window, who to contact, phone number, a ready-to-send message) and get it in front of a human two ways: (a) a dedicated "Texts To Send" sheet in the working spreadsheet (the build script does this automatically), and (b) a direct summary email/message to the user (and anyone else they name, e.g. an assistant) so it doesn't get missed inside a spreadsheet they may not open right away.

## Step 6 — Build the Spreadsheets

Write a JSON spec (see `examples/spec-example.json` for the full schema) and run:

```bash
python scripts/build_showing_sheets.py <spec.json> <output_dir>
```

This produces two files in `<output_dir>`:
- **`{client} Showing Schedule - CLIENT.xlsx`** — one sheet, printable. Address (in tour order), time window, occupancy status, price/beds/baths/sqft/lot/DOM, drive-to-next, and a short buyer-relevant note per property. **No agent contact info, no access codes, no showing-instruction detail** — this is what gets handed to or printed for the client.
- **`{client} Showing Schedule - WORKING (agent info).xlsx`** — everything in the client sheet plus full showing/access instructions, listing agent + co-agent name/phone/email, and a "Contact Status" column recording what was actually done (e.g., "Emailed Andrea Morales 9/13 requesting same-day exception (awaiting reply)" — not just "emailed," write what was actually sent and when). Properties with a stated flag (short-notice risk, missing access info) get a bold red **Flag** column entry. If any property's channel is `text`/`call_or_text`, a second sheet **"Texts To Send"** is added automatically.

**Where output goes:** if the source MLS exports/screenshots came from a specific client working folder (e.g. `Documents\delete me\<client>\`), save both spreadsheets there, next to the source files — not into this skill's own folder. Only fall back to a local `outputs/` folder here if there's no obvious client folder. Either way, **never commit real client/property/agent data to this repo** — this skill folder holds the reusable template and script only. See `examples/spec-example.json` for a fictional stand-in; don't replace it with a real run's data.

## Step 7 — Report Back

Tell the user plainly: which stops needed contact and why, which don't need anything (go straight there), what was actually sent (and to whom), which stops are flagged as at-risk (short notice, unclear access) and what if anything to do about it, and roughly what time the tour wraps up (last stop's window end + showing time). Point to both spreadsheet files by path.

## Edge Cases

- **Multiple listing agents on one property, only one named for access** (e.g., a co-listing agent's number is the one actually named in the "text agent for code" instruction): email/flag that person specifically, not just whoever is listed first.
- **Stale-looking remarks** (e.g., an old offer-due-date left in a "Private" remarks field that's clearly passed) — ignore them, don't let old boilerplate override the current showing instructions.
- **Same-day / short-notice tours**: double-check the actual current date against what the user says "today"/"tomorrow" means — voice-dictated requests especially can say one and mean the other. Getting the tour date wrong means every email promises the wrong day.
- **A property with fully clear instructions** (vacant, go and show, lockbox location given, no notice period) needs no outreach at all — don't email an agent just for the sake of completeness when Step 3's criteria aren't met.
