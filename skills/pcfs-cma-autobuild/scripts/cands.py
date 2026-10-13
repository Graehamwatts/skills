"""Print comp candidates for one subject: closed sales and actives near it.

Run from the WORK folder:  python <skill>/scripts/cands.py <key> [max_miles] [since YYYY-MM-DD] [sqft_lo] [sqft_hi]"""
import sys, datetime as dt
from mkt import SUBJ, load, miles, dom, TODAY
sys.stdout.reconfigure(encoding='utf-8')

key = sys.argv[1]
maxmi = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
since = dt.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else TODAY - dt.timedelta(days=183)
sflo = int(sys.argv[4]) if len(sys.argv) > 4 else 0
sfhi = int(sys.argv[5]) if len(sys.argv) > 5 else 99999
S = SUBJ[key]
old, rec, act = load(S['mkt'])
sside = S.get('side')
rows = []
for r in rec:
    mi = miles(S['lat'], S['lon'], r['lat'], r['lon'])
    if mi <= maxmi and r['sd'] >= since and (not sside or r['side'] == sside) and sflo <= r['sf'] <= sfhi:
        rows.append((mi, r))
rows.sort(key=lambda x: x[0])
print(f"== SOLD near {S['addr']} (<= {maxmi} mi, since {since}, sf {sflo}-{sfhi}): {len(rows)}")
for mi, r in rows:
    dm = dom(r)
    l2s = (r['p'] / r['ol'] * 100) if r['ol'] else 0
    print(f"{r['id']}|{r['a']}|{r['c']}|{mi:.2f}mi|{r['bd']:g}/{r['ba']:g}|{r['sf']}sf|lot{r['lot']}|{r['yb']}|OL{r['ol']}|FL{r['fl']}|SOLD{r['p']}|cuts{r['nc']}|{l2s:.1f}%|dom{dm}|ld{r['ld']}|cd{r['cd']}|sd{r['sd']}|${r['p'] / r['sf'] if r['sf'] else 0:.0f}/sf|{r['pt']}|pr{r['prsf']}sf {r['prbd']:g}/{r['prba']:g}")
arows = []
for r in act:
    mi = miles(S['lat'], S['lon'], r['lat'], r['lon'])
    if mi <= maxmi and (not sside or r['side'] == sside) and sflo <= r['sf'] <= sfhi:
        arows.append((mi, r))
arows.sort(key=lambda x: x[0])
print(f"== ACTIVE/PENDING: {len(arows)}")
for mi, r in arows:
    days = (TODAY - r['ld']).days if r['ld'] else None
    print(f"{r['id']}|{r['a']}|{r['c']}|{mi:.2f}mi|{r['st']}|{r['bd']:g}/{r['ba']:g}|{r['sf']}sf|lot{r['lot']}|{r['yb']}|ASK{r['p']}|OL{r['ol']}|cuts{r['nc']}|ld{r['ld']}|cd{r['cd']}|days{days}|{r['pt']}")
