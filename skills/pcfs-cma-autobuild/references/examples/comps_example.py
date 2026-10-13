"""Example WORK/comps.py: comp selections, tiers and one-line notes, one block per subject key.

The integers are the row ids from data/rec_<mkt>.txt and data/act_<mkt>.txt. The addresses and numbers in the
tables come from those files, never from this one. Tier codes: R remodel, U updated, D dated, F fixer, C custom,
P private sale, O not tiered (give it a neutral badge under `fix`). Notes are one plain line taken from the
listing remarks."""
import datetime as dt

COMPS = {
 'abc': dict(
  since=dt.date(2026, 4, 12),       # six months back from the run date
  radius=0.75,                      # miles, for the price vs days-on-market bubble chart
  bub_sf=(700, 2100),               # size band for that chart; state it in bub_scope
  similar=[
   (1000001, 'U', 'Your size. Fresh paint, laminate flooring.'),
   (1000002, 'R', 'Remodeled 3/1 on a 6,500 sq ft lot.'),
   (1000003, 'D', 'On your street. Marketed on its potential.'),
  ],
  reference=[
   (1000004, 'R', 'Fully remodeled. Sold the day it was entered, with no time on the open market.'),
   (1000005, 'F', 'Sold as a project, $138,000 under its first asking price.'),
   (1000006, 'P', 'Private sale, never on the open market.'),
  ],
  active=[
   (2000001, 'Updated 3/2 near your size. Cut twice from $1,200,000.'),
   (2000002, '3/2 on a 10,000 sq ft lot. Took an offer in 27 days.'),
  ],
  closest=[1000001, 1000003, 1000002],      # ids from `similar` for the closest-matches table
  fix={1000002: {'a': '123 Corrected Name St'},   # override a field, for example a misspelled address
       1000003: {'badge': 'Big lot'}},            # or give an untiered row a neutral badge
 ),
}
