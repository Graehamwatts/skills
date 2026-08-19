# Design Tokens — LOCKED Brand System

These tokens are NEVER negotiable per card. Continuity is the brand.

**CORRECTED 2026-07-27:** The prior version of this file (and the master template it drove) had drifted from Graeham's real mailed house style — a cream back panel and a glossy 3-stop gold gradient with drop-shadow crept in when this skill was built, and were never actually part of his 2025 cards. Graeham flagged the 08/01/26 card as visually off-brand; comparing it against the real mailed 03/01/25, 03/15/25, and 04/15/25 cards confirmed the drift. Corrected below — **flat single-tone gold, no panel, no gradient, no gloss.** Always sanity-check a new card against a real mailed PDF from `Farming Flyers to mail\`, not just against this file, if anything looks uncertain.

## Colors

| Token | Hex | CMYK (approx) | Use |
|---|---|---|---|
| Gold (primary) | `#C2A14E` | C:25 M:35 Y:75 K:5 | Border, headline highlights, CTA color, logo roof accent — the ONLY gold used anywhere on the card, flat, no gradient |
| Dark ink | `#1A1D2E` | C:80 M:75 Y:50 K:60 | Headlines, body text, logo |
| Pattern color | `#E6DABC` (~35% opacity) | n/a | Chevron house pattern overlay |
| White | `#FFFFFF` | 0,0,0,0 | Postcard background — FRONT AND BACK. No panel, no cream box, no fill color changes anywhere. Copy sits directly on the white chevron background exactly like the QR side. |

**Retired tokens (do not use):** Gold-deep `#A88638` and Gold-light `#EAD9A8` were used for a 3-stop gradient effect that never matched Graeham's real mailed cards — removed 2026-07-27. Cream `#FBF7EC` back-panel fill was likewise never part of the real house style — removed the same day. If you see either reappear in a rendered card, it's a bug — flatten to solid `#C2A14E`.

## Typography

| Use | Font | Weight | Size | Source |
|---|---|---|---|---|
| Front headline | Anton | Regular | 38pt | Google Fonts |
| Back headline | Anton | Regular | 26pt | Google Fonts |
| CTA line | Anton | Regular | 14pt | Google Fonts |
| Body | Inter | 400 (italic) | 10pt | Google Fonts |
| Sub / flip prompt | Inter | 600-800 | 14pt | Google Fonts |
| Contact info | Inter | 400/800 | 8-11pt | Google Fonts |
| Disclaimer | Inter | 400 | 6.5pt | Google Fonts |

**Headline rule:** Anton ONLY. Never substitute. Oswald is acceptable backup if Anton fails to load.

## Layout grid (6" × 4" postcard)

- **Gold left border:** 14px wide, full height, color `#C2A14E`, z-index 6
- **Chevron pattern:** SVG repeat, 80x40px tile, 0.35 stroke opacity, 0.55 layer opacity
- **Bleed:** 0.125" each side (total canvas 6.25" × 4.25")
- **Safe zone:** Keep type 0.25" from all edges minimum

**Front headline rule (corrected 2026-07-27):** the headline dominates the top third of the FRONT — full width, sized to nearly fill the safe zone left-to-right, sitting high on the card. Don't leave it clustered small in a top corner with a large empty middle; that empty-space imbalance was the other half of the 08/01/26 drift. **No decorative arrow on the front.** The master template has no arrow element at all — the QR's own black "SCAN ME" pill is the visual anchor, no arrow needed. The 08/01/26 card's front arrow (pointing at empty space) was a one-off addition that shouldn't have been there; it's been removed from the master template.

## LOCKED Bottom Contact Block (NEVER edit)

This block appears identically on every card. Continuity is the brand signature.

```
[COMPASS LOGO]
The Boyenga Team
[gold roof icon]
GRAEHAM WATTS

REALTOR®          650-308-4727
The Boyenga Team   graehamwatts@gmail.com
DRE #01466876     www.graehamwatts.com
```

**HTML structure (drop-in):**

```html
<div class="gw-logo">
  <div class="brokerage">COMPASS</div>
  <div class="brokerage-sub">The Boyenga Team</div>
  <div class="roof"></div>
  <div class="name">GRAEHAM<br>WATTS</div>
</div>
<div class="contact">
  <div class="role">REALTOR®</div>
  <div>The Boyenga Team</div>
  <div>DRE #01466876</div>
  <div class="phone">650-308-4727</div>
  <div>graehamwatts@gmail.com</div>
  <div>www.graehamwatts.com</div>
</div>
```

## LOCKED Disclaimer (legal — never remove)

> "If your home is listed with another broker, please disregard this postcard. Homes not necessarily sold by this broker."

- Placement: Vertical text on right edge of BACK
- Size: 6.5pt Inter
- Color: `#555`
- Rotated -90°

## Gold-highlight treatments

Two variants only — both FLAT, single-tone `#C2A14E`, no gradient, no gloss, no drop-shadow. Choose per word/phrase:

**Variant A — Solid gold box** (for short emphasized phrases, back headline):
```css
background: #C2A14E;
color: #fff;
padding: 0 6px;
```

**Variant B — Gold text fill** (for emphasized words inline with regular front headline):
```css
color: #C2A14E;
```

**Variant C — Gold underline** (for action verbs):
```css
border-bottom: 4px solid #C2A14E;
padding-bottom: 2px;
```

## What's NEGOTIABLE per card

- Headline text + which words get gold highlight (1-3 max)
- Subline / flip prompt copy
- Back headline + body copy
- CTA line text
- QR target URL
- Headshot pose (pointing for front, smiling for back is the default but can flex)
- **Whether the front carries its own QR** (added 2026-07-27, per Graeham). Default is back-only, but a front QR + its own short CTA line is an approved pattern — e.g. the front poses a curiosity hook with its own QR/offer. When used, mint a SEPARATE Switchy link for the front QR (see cta-router.md's Switchy section) — never reuse the back's link for the front.
- **Whether the back carries a QR at all, or a direct call-to-action instead** (settled 2026-07-27, per Graeham, same day as the above — this is now the DEFAULT, not the exception). A back with no QR — just "WANT A [OFFER]? CALL ME TODAY!" + a large phone number + gold arrow — is Graeham's proven real house style (see the Sept 2025 "Is Now The Right Time To Sell?" card). **Default to ONE QR total (front) + a call CTA on the back**, unless the specific offer genuinely needs its own landing page. Only mint a Switchy link for a QR that actually appears on the card.

## What's NEVER negotiable

- Color tokens above
- Font choices
- Bottom contact block
- Disclaimer text + placement
- Gold left border
- Chevron pattern background
- Aspect ratio (6×4 default — can scale to 6×9 for Corefact jumbo but proportions lock)
