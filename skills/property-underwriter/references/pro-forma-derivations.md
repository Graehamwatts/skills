# Pro Forma — Full Formula Derivations

Moved out of SKILL.md during a context-trim pass (2026-07-28) — this is standard real-estate finance math, kept here for reference/audit rather than inline. SKILL.md keeps only the compact one-line-per-metric table; load this file if you need the full build order or a refresher on why each block is structured this way.

## 1. Income → NOI
```
Gross Potential Rent (GPR)        = Σ (unit rent × 12)
(−) Vacancy & credit loss          = GPR × vacancy%        (default 5%)
(+) Other income                   = parking, laundry, storage, pet
= Effective Gross Income (EGI)
(−) Operating Expenses (OpEx):
      Property tax  (CA: reassessed to PURCHASE PRICE — see bay-area-assumptions.md)
      Insurance
      Property management  (default 8% of EGI if managed)
      Repairs & maintenance  (default 5–8% of EGI)
      Reserves / CapEx  (default ~$250–300/unit/mo or 5% EGI)
      HOA, utilities owner-paid, landscaping, trash
= Net Operating Income (NOI)
```
**OpEx never includes** the mortgage payment, depreciation, or income tax. NOI is pre-debt.

## 2. Valuation (cap rate)
```
Going-in cap rate  = NOI (Yr 1) / Purchase price
Implied value      = NOI / market cap rate     (cross-check vs price)
GRM                = Price / GPR                (quick sanity screen only)
```

## 3. Debt schedule
```
Loan amount        = Price × LTV
Monthly P&I        = standard amortization (loan, rate, term)
Annual debt service= P&I × 12
Mortgage constant  = Annual debt service / Loan amount
DSCR               = NOI / Annual debt service   (lenders want ≥ 1.20–1.25)
```
Build a real **amortization schedule** (beginning balance → interest → principal → ending balance) so the loan payoff at exit is correct. This is the row the equity Model Builder gets wrong — get it right here.

## 4. Levered returns
```
Cash flow before tax (CFBT) = NOI − Annual debt service
Total cash invested         = Down payment + closing costs + rehab
Cash-on-cash (Yr 1)         = CFBT / Total cash invested
```
Then project the hold (default 5 yr) with rent growth + expense inflation, and compute:
```
Exit value     = Exit-year NOI / Exit cap rate      (or appreciation path)
Net sale proceeds = Exit value − selling costs − loan payoff (from amort schedule)
Levered IRR    = IRR( −equity at t0, CFBT each year, + net sale proceeds at exit )
Equity multiple / MOIC = (Σ CFBT + net sale proceeds) / equity invested
```

## 5. Strategy overlays (only when relevant)
- **BRRRR:** rehab to ARV → refinance at ARV × refi-LTV → capital pulled out → recompute cash-in and infinite-return case.
- **ADU:** if Zoneomics/PropSearch confirms an ADU is permitted, add ADU rent and ADU build cost as a value-add scenario (incremental NOI ÷ cost = ADU yield; show the post-ADU cap rate and value lift).
- **Flip:** ARV − purchase − rehab − holding − selling = profit; annualize.

## 6. Sensitivity (bear / base / bull)
Three 2-D tables, every cell a live recalculation (follow the `dcf-model` 5×5 odd-grid, base-case-centered pattern):
1. **Appreciation × Rent growth** → levered IRR
2. **Exit cap × Hold period** → IRR / equity multiple
3. **Interest rate × LTV** → cash-on-cash + DSCR

**Read the bear case first.** If the deal still works when rents fall and the exit cap expands, it's real. Treat the recommendation as a vote, not a verdict — the data justifies the call, not the label.
