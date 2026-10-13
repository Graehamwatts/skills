"""Time-adjustment check for a recent buyer: how has price per square foot moved since the purchase?

Run from the WORK folder:
  python <skill>/scripts/time_adjust.py <key> <sqft_lo> <sqft_hi> <then_from> <then_to> [<now_from> <now_to>] [max_miles]
Dates are YYYY-MM-DD. "then" is a window around the purchase; "now" defaults to the last six complete months.
Prints both medians, the percent change and the sales behind each, so the report can state the band and the counts.
Check whether the client's own purchase is in the "then" group and say what the result is without it."""
import sys, statistics, datetime as dt
from mkt import SUBJ, load, miles, WIN, month_add

sys.stdout.reconfigure(encoding='utf-8')
a = sys.argv[1:]
key, lo, hi = a[0], int(a[1]), int(a[2])
t0, t1 = dt.date.fromisoformat(a[3]), dt.date.fromisoformat(a[4])
if len(a) >= 7:
    n0, n1 = dt.date.fromisoformat(a[5]), dt.date.fromisoformat(a[6])
    rest = a[7:]
else:
    ym = month_add(WIN['lm'][0], WIN['lm'][1], -5)
    n0, n1 = dt.date(ym[0], ym[1], 1), WIN['lm_end']
    rest = a[5:]
maxmi = float(rest[0]) if rest else None
S = SUBJ[key]
old, rec, act = load(S['mkt'])
rows = [dict(sd=r['sd'], p=r['p'], sf=r['sf'], a='', mi=None) for r in old]
rows += [dict(sd=r['sd'], p=r['p'], sf=r['sf'], a=r['a'], mi=miles(S['lat'], S['lon'], r['lat'], r['lon'])) for r in rec if r['pt'] == 'SFR']
if maxmi is not None:
    rows = [r for r in rows if r['mi'] is not None and r['mi'] <= maxmi]   # older rows carry no location


def grp(d0, d1):
    return sorted([r for r in rows if r['sf'] and lo <= r['sf'] <= hi and d0 <= r['sd'] <= d1], key=lambda r: r['sd'])


g0, g1 = grp(t0, t1), grp(n0, n1)
for name, g, d0, d1 in [('then', g0, t0, t1), ('now', g1, n0, n1)]:
    psf = [r['p'] / r['sf'] for r in g]
    print(f"{name} {d0} to {d1}: n={len(g)} median $/sqft {statistics.median(psf):.0f} median price {statistics.median([r['p'] for r in g]):,.0f}" if g else f"{name}: no sales")
    for r in g:
        if r['a']:
            print(f"    {r['sd']} {r['a']:<24} {r['p']:>10,} {r['sf']:>5} sf ${r['p'] / r['sf']:.0f}/sf {r['mi']:.2f} mi")
if g0 and g1:
    m0 = statistics.median([r['p'] / r['sf'] for r in g0])
    m1 = statistics.median([r['p'] / r['sf'] for r in g1])
    print(f"change {((m1 / m0) - 1) * 100:+.1f}%")
