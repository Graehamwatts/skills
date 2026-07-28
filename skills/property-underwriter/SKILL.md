---
name: property-underwriter
description: "Real-estate investment underwriting engine for Graeham Watts — the pro forma brain behind PropertyIQ / PropSearch. Use this skill ANY time the user wants to: underwrite a property, run the numbers, run a pro forma, analyze a deal, screen a deal, decide buy/hold/pass, or asks 'does this pencil', 'is this a good investment', 'what's the cap rate', 'what's the cash-on-cash', 'what's the NOI', 'what's the IRR', 'what's the DSCR', 'will this cash flow', 'rent vs own math', 'what can I make on this', or 'should I buy this as a rental'. Also trigger on: cap rate, NOI, net operating income, cash-on-cash return, internal rate of return, debt service coverage ratio, mortgage constant, gross rent multiplier, BRRRR, ADU upside, value-add, exit cap, hold period, levered returns, equity multiple, MOIC, seller financing analysis, fix-and-flip math, investment property analysis, income property, fourplex / duplex / triplex / multifamily analysis, or an investor client deal. Trigger when the user pastes a listing URL (Zillow, Redfin, Realtor.com, MLSListings) or MLS export and wants the INVESTMENT numbers (not just a CMA — a CMA prices a home for sale; this underwrites it as an income investment). Bay Area / Peninsula localized (CA property-tax reassessment, local transfer taxes, AB 1482 + city rent control, ADU rules). Produces a live formula-driven Excel pro forma plus a one-page buy/hold/pass memo. This is the engine PropSearch calls on a selected property — depth-on-demand, not inline on a whole search page."
---

# Property Underwriter — Graeham Watts | PropertyIQ / PropSearch

This skill turns any property — a listing URL, an MLS export, or a few typed facts — into a full **investment underwrite**: income → NOI → cap-rate value → debt schedule → levered cash flow → cash-on-cash / IRR / equity multiple, with a bear/base/bull sensitivity surface and a plain-English buy/hold/pass call. It outputs a **live, formula-driven Excel model** (change any assumption, the whole thing recalculates) plus a **one-page written memo**.

**Why this exists.** A CMA prices a home for a buyer or seller. It does not tell an investor whether the deal *works*. Underwriting is the other half — the math that says hold/pass before a viewing or a reservation. PropSearch's spec already promises this (cap rate, NOI, ADU potential, cash-on-cash, IRR); this skill is the engine that actually delivers it. It also serves Graeham's investor clients and his own deals directly, run on demand from chat.

---

## Design note — read this once (it's the whole reason this skill exists)

Anthropic's equity-focused **Model Builder** (`financial-analysis` plugin) gets the real-estate debt schedule wrong if pointed at a property listing — it improvises company-stock DCF structure onto a rental deal, so this skill encodes the correct real-estate pro forma instead.

How it uses the Anthropic engine:

- **Excel construction + self-audit:** build the workbook with the local **`xlsx` skill** (formula-over-hardcode, `recalc.py` error sweep). If the `financial-analysis` plugin is installed, you MAY also use its `/lbo` and `/returns` skills for the heavy 75-cell sensitivity grids and the formula audit loop — but the **pro forma structure and assumptions in THIS skill always win**.
- **Data:** Anthropic's finance connectors (FactSet, Daloopa, Morningstar, PitchBook, Moody's) are **equity/credit data — none cover real estate.** Do NOT rely on them for a property. Feed the model real-estate data instead: the listing facts, an AVM value, a market **rent estimate**, and (where available) the Zoneomics ADU/zoning flag from PropSearch.

---

## Inputs — what to collect (pre-fill from PropSearch when called as the engine)

**Required**
- Address (or listing URL / MLS export)
- Purchase price (or asking price)
- Property type + unit mix (SFR, duplex, triplex, fourplex, multifamily) and beds/baths/sqft
- Market rent — per unit. Use PropSearch's rent estimate / RentCast / comps. **Never guess rent; pull it.**

**Financing (use Bay Area defaults if not given — see `references/bay-area-assumptions.md`)**
- Down payment % / LTV, interest rate, amortization term, loan type (fixed/ARM), points/fees
- Strategy: buy-and-hold / BRRRR / house-hack / fix-and-flip / seller-financed

**Assumptions (default, then let the user override)**
- Hold period (default 5 yr), vacancy %, operating expenses, rent growth, appreciation, exit cap, selling costs
- Rehab budget + ARV (for BRRRR/flip), ADU cost + ADU rent (if zoning permits)

**The clarifying-question rule:** ask the 3–5 questions you genuinely cannot infer (financing terms, rehab scope, hold period). The questions the user *can't* answer are the ones they need to research before bidding — surface them, don't paper over them.

---

## The pro forma — methodology (build in this order, verify each block with the user)

Full derivations moved to `references/pro-forma-derivations.md` (standard real-estate finance math) — load it if you need the build-order detail. Quick reference:

| Metric | One-line formula |
|---|---|
| EGI | GPR − vacancy/credit loss + other income |
| NOI | EGI − OpEx (tax, insurance, mgmt, repairs, reserves, HOA/utilities — never mortgage, depreciation, or income tax) |
| Going-in cap rate | NOI (Yr1) / Purchase price |
| Implied value | NOI / market cap rate |
| GRM | Price / GPR (sanity screen only) |
| Monthly P&I | standard amortization (loan, rate, term) |
| Mortgage constant | Annual debt service / Loan amount |
| DSCR | NOI / Annual debt service (lenders want ≥1.20–1.25) |
| CFBT | NOI − Annual debt service |
| Cash-on-cash (Yr1) | CFBT / Total cash invested |
| Exit value | Exit-year NOI / Exit cap rate |
| Levered IRR | IRR(−equity at t0, CFBT each year, + net sale proceeds at exit) |
| Equity multiple / MOIC | (Σ CFBT + net sale proceeds) / equity invested |

Build a real **amortization schedule** (beginning balance → interest → principal → ending balance) — this is the row the equity Model Builder gets wrong.

**Strategy overlays (only when relevant):** BRRRR (rehab to ARV → refi at ARV × refi-LTV → recompute cash-in), ADU (if Zoneomics/PropSearch confirms permitted, add ADU rent/cost as a value-add scenario), Flip (ARV − purchase − rehab − holding − selling = profit, annualized).

**Sensitivity (bear/base/bull):** three live 2-D tables — Appreciation × Rent growth → IRR; Exit cap × Hold period → IRR/equity multiple; Interest rate × LTV → cash-on-cash + DSCR. **Read the bear case first** — if the deal still works when rents fall and the exit cap expands, it's real. The data justifies the call, not the label.

---

## Output

1. **Excel pro forma** (`[Address]_Underwrite_[Date].xlsx`) — built via the `xlsx` skill: Assumptions tab (yellow/blue live inputs), Income→NOI, Amortization, 10-yr cash flow, Returns summary, Sensitivity. Formula-driven; run `recalc.py` until zero errors before delivering.
2. **One-page memo** (`.md`, optional `.pdf` via the `pdf` skill) — headline returns (cap, CoC, IRR, equity multiple, DSCR), what drives the outcome, where the deal is fragile, and a **buy / hold / pass / push-the-seller** call. Stakeholder-ready.

Match Graeham's black-and-gold brand for any client-facing PDF (see `../website-builder/references/realtor-brand-kit.md`).

---

## Workflow

1. Collect inputs (pre-fill from PropSearch when called as the engine; otherwise ask the 3–5 questions you can't infer).
2. Pull market rent (PropSearch estimate / RentCast / comps) — never guess it.
3. Load Bay Area defaults from `references/bay-area-assumptions.md`; let the user override.
4. Build the model block-by-block (Income→NOI → Debt → Returns → Sensitivity), confirming each block before the next.
5. Build the Excel workbook with the `xlsx` skill; run `recalc.py` to zero errors.
6. Write the one-page memo; lead with the bear case.
7. Save to outputs and present both files. Offer the PDF.

---

## Hard rules

- **Not investment advice.** This drafts an analyst's underwrite for the user's own judgment. Every output is staged for human review.
- **Verify the local assumptions** that move the answer most: CA property-tax reassessment at purchase, city transfer tax, and local rent control (see refs). Flag any number you did not verify.
- **Never fabricate rent, comps, or tax figures.** Pull them or mark them as an assumption to verify.
- **Formula-over-hardcode** in Excel — the model must flex when an assumption changes.

---

## PropertyIQ integration (how this plugs into the product)

- **PropSearch calls this on a selected property — depth-on-demand**, not inline on every search row. Search surfaces candidates with the cheap inline rent/return estimate; the user picks one; "Underwrite this deal" fires this skill. PropSearch passes in the listing facts, AVM value, rent estimate, and Zoneomics ADU flag so the model skips half the clarifying questions.
- **Wattson:** register this as a callable Skill so Wattson playbooks (e.g., investor-lead intake) can run an underwrite as a step.
- **Event Ledger:** log each run as `UNDERWRITE_RUN` (content_id / contact_id / property) so an investor's underwrite → pipeline → close stays attributable.
- **Data boundary:** same MLS hard rules as the rest of PropertyIQ — no training on MLS data, no public exposure of raw records; the model surfaces facts for the agent's own use.

---

## References
- `references/bay-area-assumptions.md` — default assumptions + the figures that MUST be verified per deal (CA property tax, transfer taxes, AB 1482 + city rent control, insurance, ADU).
- `references/pro-forma-derivations.md` — full formula derivations (NOI, cap rate, debt schedule, levered returns) with build order and rationale.
- `../xlsx/SKILL.md` — Excel construction + `recalc.py` audit (the model engine).
- `../website-builder/references/realtor-brand-kit.md` — brand for client-facing PDFs.
- Optional: Anthropic `financial-analysis` plugin (`/lbo`, `/returns`) for heavy sensitivity + audit if installed.
