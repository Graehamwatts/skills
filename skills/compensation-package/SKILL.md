---
name: compensation-package
description: "Generates and publishes Graeham Watts's Marketing & Compensation Package, the branded page that shows sellers what each commission tier (Silver/Gold/Platinum) actually includes, how it compares to Redfin and traditional agents, and what makes The Boyenga Team's marketing different (geofencing retargeting, YouTube in-stream ads, the 3-step Grand Opening launch process). Use this skill ANY time the user mentions: compensation package, compensation flyer, marketing plan options, commission tiers, Silver/Gold/Platinum package, what's included at each commission rate, comp package link for a CMA, Redfin comparison flyer, or updating/rebuilding the commission flyers. Two live pages already exist (Standard and Premium rates) and should be updated in place rather than re-created from scratch unless Graeham asks for a new variant."
---

# Compensation Package — Graeham Watts

Produces the branded, tiered Marketing & Compensation Package page: what a seller's commission buys at each level, how it stacks up against a discount brokerage and a traditional full-service agent, and what makes The Boyenga Team's marketing distinct. Built to be linked from a CMA as a standalone URL, and to print cleanly to PDF as a physical flyer.

---

## 0. Brand identity — read this before writing any output

**Read `skills/shared-references/identity.json` and copy values from there.** Never type brand details from memory.

- Graeham Watts is the primary brand, always leads.
- Brokerage attribution: **"Powered by The Boyenga Team at Compass Real Estate"** (spelling: Boyenga, not Boyanga).
- DRE **01466876** is the only valid DRE.
- "Intero Real Estate" is the former brokerage and must not appear in new output.

Run the brand validator before every publish (see §4).

---

## 1. The two rate models

These replaced the old Intero-branded "Regular" and "Luxury" flyers on 2026-08-15. Both share identical services per tier; only the commission percentage changes. Do not invent a third rate set without Graeham explicitly asking — these two are the approved defaults.

| Tier | Standard variant | Premium variant |
|---|---|---|
| Silver (Discount) | 2.0% | 2.5% |
| Gold (Full-Service) | 2.5% | 3.0% |
| Platinum Luxury (Complete Launch) | 3.0%-3.5% | 3.5% |

**Standard** is the default page to send. **Premium** is what Graeham shows when he believes he can command a stronger fee, e.g. a hot listing, a seller less price-sensitive, a market favoring sellers. Never send Premium as the default without Graeham's direction.

---

## 2. Live pages

| Variant | Live URL |
|---|---|
| Standard | `https://graehamwatts.github.io/online-content/compensation/Compensation-Package-Standard.html` |
| Premium | `https://graehamwatts.github.io/online-content/compensation/Compensation-Package-Premium.html` |

Each page has a toggle link in the hero to the other variant, so whichever one Graeham shares, the recipient can see the other rate set too.

---

## 3. Section structure (do not reorder without reason)

1. **Hero** — name, cobrand lockup (Boyenga + Compass, equal weight), variant badge, DRE/contact, toggle link to the other variant.
2. **What You're Actually Comparing** — framing paragraph, states commission is negotiable.
3. **Marketing Plan Options** — the full checkmark grid, grouped by category (Photography & Film, Home Prep & Staging, Brochure & Signage, Launch Event, Targeted Advertising), Silver/Gold/Platinum columns.
4. **Compass Concierge** — the $0-due-until-closing prep/staging financing callout. This is a real, current Compass-exclusive program (not available at a discount brokerage or most traditional agents); confirm it's still active before reusing this copy in a future year.
5. **How We're Different** — content-capture-to-geofencing explanation, YouTube skippable in-stream ads explanation, buyer-targeting-compared callout.
6. **Our 3-Step Grand Opening Launch Process** — Capture Day → Pre-Launch Amplification → Grand Opening Weekend.
7. **How This Compares** — Discount/Redfin-style vs. Traditional Full-Service vs. Graeham Watts/Boyenga Team table.
8. **Which Tier Fits** — one-line summary per tier.
9. **Staying In Touch** — warm CTA.
10. **Footer** — lockup, DRE/contact, mandatory negotiability + services-subject-to-change disclaimer. Never remove the disclaimer line.

> **Content provenance note.** The "3-Step Grand Opening Launch Process" (§6) was authored from Graeham's own description of the team's workflow (a production day, followed by geofencing/YouTube/social amplification, followed by the Grand Opening event weekend). A web search on 2026-08-15 did not find a Boyenga Team-published document using this exact "3-step" framing, so if Graeham has an actual internal name or sequence for this process, update §6 to match it rather than treating this framing as authoritative.

---

## 4. Workflow — updating or regenerating a page

1. Read `skills/shared-references/identity.json` for current brand values.
2. Start from `references/template.html` (never hand-edit the published output directly, or the two variants will drift apart).
3. Re-encode the cobrand lockup if it has changed:
   ```bash
   base64 -w 0 "C:\Users\Graeham Watts\Documents\Compass\Compass branding\How to use branding\Boyenga And Compass\Boyenga Team + Compass white.png"
   ```
4. Substitute every `{{PLACEHOLDER}}` listed in the template's header comment for both variants (Standard and Premium use the same template, different tier percentages).
5. Grep the output for `\u2014` (em dash) — must be zero. Title/label separators use a plain hyphen `" - "`, matching the convention already used on graehamwatts.com CMA pages.
6. Grep for leftover `{{` — must be zero.
7. Open both pages in a browser and scroll through before publishing; check the tier-header table and the competitor comparison table specifically, they're the two places placeholder substitution most often leaves an awkward string.
8. Run the brand validator (see `references/publishing.md`).
9. Publish per `references/publishing.md`.
10. Verify both live URLs return 200.

---

## 5. Linking from a CMA

When Graeham wants the compensation package included with a CMA, add one line to the CMA's "Staying In Touch" section (or footer) linking to the Standard page by default:

```html
<p>Curious what your commission actually includes? <a href="https://graehamwatts.github.io/online-content/compensation/Compensation-Package-Standard.html">See the full Marketing &amp; Compensation Package</a>.</p>
```

Swap in the Premium URL only if Graeham has specifically said to use the Premium rates for that listing. Do not embed the compensation page's content inline in a CMA; link to it instead, both because it's a general-purpose page (not property-specific) and because the CMA skill's own pre-flight checklist governs what belongs in a CMA directly.

---

## 6. Reference map

| When you are... | Read |
|---|---|
| Regenerating or editing the page | `references/template.html` |
| Publishing to the live site | `references/publishing.md` |
