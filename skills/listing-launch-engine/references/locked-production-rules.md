# Locked Production Rules — Hard Gate

These are Graeham's standing rules, already encoded across his other skills. They are non-negotiable. Run a full scan of the finished Call Sheet against this list before delivering. If any item fails, fix it — do not ship a Call Sheet that violates these.

## 1. Peninsula geographic anchors (required)

Every place reference must anchor to Graeham's real markets: **East Palo Alto** (primary), **Redwood City, Palo Alto, Menlo Park, San Mateo County, the Peninsula** (secondary). Never a generic "California suburb," "a nice neighborhood," or an invented town. AI B-roll prompts that show streets/neighborhoods must describe Peninsula-style settings, not anonymous suburbia.

Fair Housing still applies (inherited from `content-creation-engine`): describe neighborhoods by property features, price, trends, lot size, architecture, transit/walkability facts — never by demographics, and never use "safe/good/family-friendly" as demographic proxy.

## 2. Old-school red/white FOR SALE sign only

Any shot or AI frame showing a for-sale sign uses the **classic red-and-white FOR SALE sign**. No modern, branded, or stylized sign variants. When writing an `AI-BROLL` prompt that includes a sign, quote the text literally and specify the classic red/white style (and route it to GPT Image 2 via `higgsfield-video`, since legible in-frame text is required).

## 3. No DRE number anywhere on screen or in copy

The DRE number must **never** appear in any script line, text overlay, caption, motion graphic, or on-screen text in any asset in the package. DRE belongs in the video description / dashboard / disclosure end-card audio only — never on screen. (Graeham's skills carry conflicting DRE values across files; the safe, correct behavior for this skill is simply: **no DRE number appears in any deliverable, full stop.** The canonical identity lives in `shared-references/identity.json` and is not this skill's concern.)

## 4. ElevenLabs + HeyGen per standing config

- **Voice** = Graeham's ElevenLabs clone, by default, on every asset. Only override if Graeham explicitly says so in Step 0.
- **Avatar look** = the one chosen in Step 0 (never a silent default).
- **Settings/IDs** are owned by `heygen-video` (references/avatars.md). Do **not** hardcode voice/avatar IDs into the Call Sheet — reference that skill so the IDs stay in one place.

## 5. Audio rules on B-roll

- B-roll carries **no competing dialogue** under it. Pair B-roll with **VO or music only**.
- On the **HERO moment** (the one climax beat that gets the Watts Gold treatment), **music drops to silence for ~1.5s**, then fades back — per `watts-motion-graphics`. Flag the HERO beat in the editor packet so the editor knows where to drop the music.
- Avatar-source clips: on-set audio is reference only; the deliverable voice is the ElevenLabs clone.

## 6. Marketing describes the home the way the MLS lists it (Graeham's standing rule, 2026-10-15)

If a property has an unpermitted, unverified or questionable feature (an unpermitted conversion, an unfinished addition, an unknown permit history), **it does not appear in the call sheet at all**: not in a script, hook, caption, ad, graphic, brief, checklist video or "disclosure" asset built around it, and not as a rule or warning inside the sheet either (the sheet should not even name it). Never build a video, an ad or a concept around it.

- **Describe the home as the MLS does** (for example "three-bedroom, two-bath"). Do not call a room or feature permitted, legal or approved unless the record is in hand, and do not invent a name for the space.
- **One small standard disclaimer, only where the numbers are stated.** Wherever a video beat, graphic, caption or ad states bedrooms, baths or square footage: on screen, small, at the bottom of the frame: `Square footage, bedroom and bath counts not verified by agent or others. Buyer to investigate.` In captions and ads, the same idea as the closing sentence: `Square footage, bedroom and bath counts are not verified by the agent or others. Buyer to investigate.` Nothing else about the rooms.
- **Permit status and the history of any room belong in the formal disclosure documents** (seller disclosures, AVID, inspection and permit records). This skill never edits those and never repeats their contents in marketing.
- **"Put it in the disclosures" means those documents, not the marketing.** If Graeham has not said how a feature should be described, ask him once. Never invent a disclosure line and spread it across every asset.
- A generic Disclosure Drop ("here is what I would read first: the seller disclosures, the inspection reports, the natural hazard report, the dates") is fine and must not point at any one feature.
- Live takes already recorded with banned content are marked "audio not used" in the editor packet; never script around a take that says more than the plain description.

## Final scan checklist (run before delivering)

- [ ] Every place reference is a real Peninsula market, no generic suburb.
- [ ] Every for-sale sign is the classic red/white sign.
- [ ] Zero DRE numbers anywhere in any asset (scripts, overlays, captions, on-screen text).
- [ ] Voice = clone; avatar = Step-0 choice; no hardcoded IDs.
- [ ] B-roll has no competing dialogue; HERO music-drop flagged for the editor.
- [ ] Bank shots (≤5) each name a real queued video.
- [ ] Both required Step-0 asks were answered before generation.
- [ ] Launch Content Plan present — all 8 phases instantiated for this listing, CORE assets flagged; every footage-dependent asset has a clip on the shot list (incl. the 4-photo status set).
- [ ] No price/rate/credit in any VIDEO (VO or on-screen); price only in captions/static slides.
- [ ] New keywords (TOUR / DOCS / OPEN) flagged to Graeham to create in GHL or map to existing.
- [ ] Rule 6: no unpermitted, unverified or questionable feature is named, hinted at or built around anywhere in the sheet (scan the finished HTML text, not just the data); every bedroom, bath or square-footage statement carries the small standard disclaimer.
