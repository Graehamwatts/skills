"""Market data loader and trend statistics for past-client home value updates.

Run every script from the WORK folder (the run's scratch folder). The WORK folder holds run.json, data/,
the per-client cfg_<key>.py files and out/. See references/data-formats.md for the row layouts."""
import os, sys, json, math, statistics, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.getcwd()
if WORK not in sys.path:
    sys.path.insert(0, WORK)
DATA = os.path.join(WORK, 'data')
MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

RUN = json.load(open(os.path.join(WORK, 'run.json'), encoding='utf-8'))
TODAY = dt.date.fromisoformat(RUN['today'])
SUBJ = {}
for _k, _v in RUN['subjects'].items():
    SUBJ[_k] = dict(_v)
    SUBJ[_k]['key'] = _k
# Actives whose listing history carried no "Listed" event: list date = today minus the search record's days on market.
ACT_LD = {int(k): v for k, v in RUN.get('active_list_dates', {}).items()}


def d(s):
    return dt.date.fromisoformat(s) if s else None


def miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def month_add(y, m, k):
    t = y * 12 + (m - 1) + k
    return t // 12, t % 12 + 1


def month_end(y, m):
    ny, nm = month_add(y, m, 1)
    return dt.date(ny, nm, 1) - dt.timedelta(days=1)


def months(start, end):
    """Inclusive list of (y, m) tuples."""
    out = []
    y, m = start
    while (y, m) <= end:
        out.append((y, m))
        y, m = month_add(y, m, 1)
    return out


def month_long(ym):
    return f"{MONTHS_LONG[ym[1] - 1]} {ym[0]}"


# ---- chart windows, all derived from today's date ----
# LM = last complete month. The current month is never plotted (partial-month artifact rule).
_LM = month_add(TODAY.year, TODAY.month, -1)
_START = TODAY - dt.timedelta(days=1095)          # the search returns three years of closed sales
WIN = dict(
    lm=_LM, lm_end=month_end(*_LM), lm_long=month_long(_LM),
    data_from=(_START.year, _START.month), price_from=month_long((_START.year, _START.month)),
    price=(month_add(_START.year, _START.month, 2), _LM),      # first month with a full trailing three-month window
    ls=(month_add(_LM[0], _LM[1], -12), _LM),                  # 13 points: sale to list, days to contract, inventory
    newl=(month_add(_LM[0], _LM[1], -11), _LM),                # 12 months of new listings vs closed sales
    rec_from_ym=month_add(_LM[0], _LM[1], -14),                # rec_<mkt>.txt must start on the 1st of this month
)
WIN['rec_from'] = month_long(WIN['rec_from_ym'])
WIN['rec_from_date'] = dt.date(WIN['rec_from_ym'][0], WIN['rec_from_ym'][1], 1)
WIN['newl_from'] = month_long(WIN['newl'][0])
WIN['today_long'] = f"{MONTHS_LONG[TODAY.month - 1]} {TODAY.day}, {TODAY.year}"


def load(mkt):
    old = []
    for tok in open(os.path.join(DATA, f'old_{mkt}.txt'), encoding='utf-8').read().split(';'):
        if not tok.strip():
            continue
        s, p, sf = tok.split(',')
        row = dict(sd=dt.date(2000 + int(s[:2]), int(s[2:4]), int(s[4:6])), p=int(p), sf=int(sf))
        if row not in old:
            old.append(row)
    rec = []
    for line in open(os.path.join(DATA, f'rec_{mkt}.txt'), encoding='utf-8').read().split('\n'):
        if not line.strip():
            continue
        f = line.split('|')
        rec.append(dict(id=int(f[0]), a=f[1], c=f[2], sd=d(f[3]), p=int(f[4]), sf=int(f[5] or 0), lot=int(float(f[6] or 0)),
                        bd=float(f[7] or 0), ba=float(f[8] or 0), yb=int(f[9] or 0), lat=float(f[10]), lon=float(f[11]), side=f[12],
                        ld=d(f[13]), cd=d(f[14]), ol=int(f[15]), fl=int(f[16]), nc=int(f[17]), ld0=d(f[18]), pt=f[19],
                        prsf=int(float(f[20] or 0)), prbd=float(f[21] or 0), prba=float(f[22] or 0)))
    act = []
    for line in open(os.path.join(DATA, f'act_{mkt}.txt'), encoding='utf-8').read().split('\n'):
        if not line.strip():
            continue
        f = line.split('|')
        act.append(dict(id=int(f[0]), a=f[1], c=f[2], st=f[3], p=int(f[4]), sf=int(f[5] or 0), lot=int(float(f[6] or 0)),
                        bd=float(f[7] or 0), ba=float(f[8] or 0), yb=int(f[9] or 0), lat=float(f[10]), lon=float(f[11]), side=f[12],
                        ld=d(f[13]), cd=d(f[14]), ol=int(f[15]), fl=int(f[16]), nc=int(f[17]), ld0=d(f[18]), pt=f[19]))
    for r in act:
        if r['id'] in ACT_LD and not r['ld']:
            r['ld'] = d(ACT_LD[r['id']])
    return old, rec, act


def dom(r):
    """Days from the listing start to the accepted offer (contract date)."""
    if r.get('ld') and r.get('cd'):
        return max((r['cd'] - r['ld']).days, 0)
    return None


def trends(mkt, sfr_only=True):
    old, rec, act = load(mkt)
    recs = [r for r in rec if (r['pt'] == 'SFR' or not sfr_only)]
    acts = [r for r in act if (r['pt'] == 'SFR' or not sfr_only)]
    sales = [(r['sd'], r['p']) for r in old] + [(r['sd'], r['p']) for r in recs]
    out = {'n_sales_all': len(sales), 'n_rec': len(recs), 'n_act': len(acts)}

    def in_month(dte, ym):
        return (dte.year, dte.month) == ym

    def in_3mo(dte, ym):
        lo = month_add(ym[0], ym[1], -2)
        return lo <= (dte.year, dte.month) <= ym

    # price trend: trailing three-month median plus the single-month median
    price = []
    for ym in months(*WIN['price']):
        v3 = [p for (s, p) in sales if in_3mo(s, ym)]
        v1 = [p for (s, p) in sales if in_month(s, ym)]
        price.append(dict(ym=ym, med3=statistics.median(v3) if len(v3) >= 3 else None, n3=len(v3),
                          med1=statistics.median(v1) if len(v1) >= 3 else None, n1=len(v1)))
    out['price'] = price
    out['n_price_sales'] = len([1 for (s, p) in sales if WIN['data_from'] <= (s.year, s.month) <= WIN['lm']])

    # sale to list, days to contract, share over asking: trailing three months
    listed = [r for r in recs if r['fl'] > 0 and r['ld'] and r['cd'] and r['ld'] != r['sd']]
    out['n_listed'] = len([r for r in listed if r['sd'] <= WIN['lm_end']])
    lm = months(*WIN['ls'])
    ls = []
    for ym in lm:
        rows = [r for r in listed if in_3mo(r['sd'], ym)]
        if len(rows) >= 3:
            ls.append(dict(ym=ym, n=len(rows),
                           ls_final=statistics.median([r['p'] / r['fl'] for r in rows]),
                           ls_orig=statistics.median([r['p'] / r['ol'] for r in rows if r['ol'] > 0]),
                           dom=statistics.median([dom(r) for r in rows]),
                           over=sum(1 for r in rows if r['p'] > r['fl']) / len(rows)))
        else:
            ls.append(dict(ym=ym, n=len(rows), ls_final=None, ls_orig=None, dom=None, over=None))
    out['ls'] = ls

    # new listings and closed sales by month
    newl = []
    for ym in months(*WIN['newl']):
        nl = sum(1 for r in recs if r['ld'] and in_month(r['ld'], ym) and r['ld'] != r['sd']) + \
             sum(1 for r in acts if r['ld'] and in_month(r['ld'], ym))
        cs = sum(1 for r in recs if in_month(r['sd'], ym))
        newl.append(dict(ym=ym, new=nl, closed=cs))
    out['newl'] = newl

    # month-end actives and months of inventory
    inv = []
    for ym in lm:
        me = month_end(*ym)
        n_act = 0
        for r in recs:
            if not r['ld'] or r['ld'] == r['sd']:
                continue
            c = r['cd'] or (r['sd'] - dt.timedelta(days=25))
            if r['ld'] <= me < c:
                n_act += 1
        for r in acts:
            if not r['ld']:
                continue
            if r['st'] in ('Active', 'Coming Soon'):
                if r['ld'] <= me:
                    n_act += 1
            else:
                if r['cd'] and r['ld'] <= me < r['cd']:
                    n_act += 1
        pace = sum(1 for r in recs if in_3mo(r['sd'], ym)) / 3.0
        inv.append(dict(ym=ym, active=n_act, pace=pace, moi=(n_act / pace) if pace else None))
    out['inv'] = inv
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('run date', TODAY, '| last complete month', WIN['lm_long'], '| detailed sale rows must start', WIN['rec_from_date'],
          '| price chart from', month_long(WIN['price'][0]), '| other charts from', month_long(WIN['ls'][0]))
    for mkt in sys.argv[1:]:
        t = trends(mkt)
        print('=====', mkt, 'sales', t['n_sales_all'], 'rec', t['n_rec'], 'act', t['n_act'], 'price-window sales', t['n_price_sales'])
        print('price med3:', ' '.join(f"{x['ym'][0] % 100}-{x['ym'][1]:02d}:{(x['med3'] or 0) / 1000:.0f}({x['n3']})" for x in t['price']))
        print('ls:', ' '.join(f"{x['ym'][0] % 100}-{x['ym'][1]:02d}:{(x['ls_final'] or 0) * 100:.1f}/dom{x['dom']}/n{x['n']}/over{(x['over'] or 0) * 100:.0f}" for x in t['ls']))
        print('new/closed:', ' '.join(f"{x['ym'][0] % 100}-{x['ym'][1]:02d}:{x['new']}/{x['closed']}" for x in t['newl']))
        print('inv:', ' '.join(f"{x['ym'][0] % 100}-{x['ym'][1]:02d}:{x['active']}/{x['pace']:.1f}={(x['moi'] or 0):.1f}" for x in t['inv']))
