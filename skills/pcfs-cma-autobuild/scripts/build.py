"""Past-client Home Value Update page builder.

Run from the WORK folder:  python <skill>/scripts/build.py <key> [--facts]
--facts prints every computed row, tier median and trend figure. Read it BEFORE writing any prose."""
import sys, os, io, base64, json, statistics, importlib, datetime as dt
import charts
from mkt import SUBJ, load, miles, trends, TODAY, RUN, WORK, WIN
from brand import ID

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WORK, 'out')
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
TIERS = {'C': ('tC', 'Custom'), 'R': ('tR', 'Remodel'), 'U': ('tU', 'Updated'), 'D': ('tD', 'Dated'), 'F': ('tF', 'Fixer'), 'P': ('tP', 'Private sale'), 'O': ('tP', 'Other')}
LOGO_SRC = os.path.join(HERE, '..', 'assets', 'boyenga_compass_white.png')

RATES = [tuple(x) for x in RUN['rates']]


def usd(n):
    return '${:,.0f}'.format(n)


def signed(n):
    return ('+' if n >= 0 else '-') + '${:,.0f}'.format(abs(n))


def mdy(d):
    return f'{d.month}/{d.day}/{d.year % 100}'


def ymlab(ym):
    return f"{MON[ym[1] - 1]} {ym[0] % 100}"


def logo_uri():
    return 'data:image/png;base64,' + base64.b64encode(open(LOGO_SRC, 'rb').read()).decode()


def comp_dom(r):
    if not r.get('ld') or not r.get('cd'):
        return None
    start = r['ld']
    if r.get('ld0') and 0 <= (r['ld'] - r['ld0']).days <= 120:
        start = r['ld0']
    return max((r['cd'] - start).days, 0)


def dom_td(v):
    if v is None:
        return '<td></td>'
    col = '#2e7d4f' if v < 15 else ('#A88B3D' if v <= 30 else '#c0392b')
    return f"<td style='color:{col};font-weight:700'>{v}</td>"


def bdba(r):
    return f"{r['bd']:g}/{r['ba']:g}"


def nice_bounds(vals, step):
    lo = min(vals)
    hi = max(vals)
    import math
    return math.floor(lo / step) * step, math.ceil(hi / step) * step


class Ctx:
    def __init__(self, cfg):
        self.c = cfg
        self.S = SUBJ[cfg['key']]
        self.old, self.rec, self.act = load(cfg['mkt'])
        self.byid = {r['id']: r for r in self.rec}
        self.actid = {r['id']: r for r in self.act}
        self.t = trends(cfg['mkt'])
        for r in self.rec + self.act:
            r['mi'] = miles(self.S['lat'], self.S['lon'], r['lat'], r['lon'])
        self.sim = []
        for pid, tier, note in cfg['similar']:
            r = dict(self.byid[pid])
            r.update(cfg.get('fix', {}).get(pid, {}))
            r['tier'], r['note'], r['dom'] = tier, note, comp_dom(r)
            r['psf'] = r['p'] / r['sf']
            r['l2s'] = r['p'] / r['ol'] if r['ol'] else None
            self.sim.append(r)
        self.sim.sort(key=lambda r: -r['p'])
        self.ref = []
        for pid, tier, why in cfg['reference']:
            r = dict(self.byid[pid])
            r.update(cfg.get('fix', {}).get(pid, {}))
            r['tier'], r['why'] = tier, why
            r['psf'] = r['p'] / r['sf'] if r['sf'] else 0
            self.ref.append(r)
        self.actv = []
        for pid, note in cfg['active']:
            r = dict(self.actid[pid])
            r.update(cfg.get('fix', {}).get(pid, {}))
            r['note'] = note
            self.actv.append(r)

    # ---------- facts ----------
    def tier_stats(self):
        out = []
        for code in ['C', 'R', 'U', 'D', 'F']:
            rows = [r for r in self.sim if r['tier'] == code]
            if rows:
                out.append((TIERS[code][1], statistics.median([r['p'] for r in rows]), statistics.median([r['psf'] for r in rows]), len(rows)))
        return out

    def facts(self):
        c = self.c
        print('=== SIMILAR')
        for r in self.sim:
            print(f"{r['tier']} {r['a']:<22} {r['mi']:.2f}mi {bdba(r)} {r['sf']}sf lot{r['lot']} {r['yb']} OL{r['ol']} FL{r['fl']} SOLD{r['p']} cuts{r['nc']} vsOL{r['p'] - r['ol']:+d} {(r['l2s'] or 0) * 100:.1f}% dom{r['dom']} ld{r['ld']} cd{r['cd']} closed{r['sd']} psf{r['psf']:.0f}")
        for name, mp, mpsf, n in self.tier_stats():
            print(f'  tier {name}: median {mp:,.0f} psf {mpsf:.0f} n={n}')
        ls = [r['l2s'] for r in self.sim if r['l2s']]
        dm = [r['dom'] for r in self.sim if r['dom'] is not None]
        print(f"  similar: median l2s {statistics.median(ls) * 100:.1f}% median dom {statistics.median(dm)} n={len(self.sim)} dates {min(r['sd'] for r in self.sim)} .. {max(r['sd'] for r in self.sim)} maxmi {max(r['mi'] for r in self.sim):.2f} sf {min(r['sf'] for r in self.sim)}-{max(r['sf'] for r in self.sim)}")
        print(f"  subject psf at mid {c['val_mid'] / c['subj']['sf']:.0f}; gain {c['val_mid'] - c['paid']:+,d} ({(c['val_mid'] / c['paid'] - 1) * 100:.1f}%), multiple {c['val_mid'] / c['paid']:.2f}")
        print('=== REFERENCE')
        for r in self.ref:
            print(f"{r['tier']} {r['a']:<22} {r['mi']:.2f}mi {bdba(r)} {r['sf']}sf lot{r['lot']} SOLD{r['p']} psf{r['psf']:.0f} closed{r['sd']} OL{r['ol']} FL{r['fl']} cuts{r['nc']} dom{comp_dom(r)}")
        print('=== ACTIVE')
        for r in self.actv:
            days = (TODAY - r['ld']).days if r['ld'] else None
            print(f"{r['st']} {r['a']:<22} {r['mi']:.2f}mi {bdba(r)} {r['sf']}sf lot{r['lot']} {r['yb']} ASK{r['p']} OL{r['ol']} cuts{r['nc']} ld{r['ld']} cd{r['cd']} days{days}")
        t = self.t
        p = [x for x in t['price'] if x['med3']]
        print('=== TRENDS', c['mkt'])
        print('  price med3 latest', ymlab(p[-1]['ym']), p[-1]['med3'], 'n3', p[-1]['n3'], '| min', min(x['med3'] for x in p), 'max', max(x['med3'] for x in p), '| yr ago', [x['med3'] for x in p if x['ym'] == WIN['ls'][0]], '| n sales', t['n_price_sales'])
        for x in t['ls']:
            print('  ls', ymlab(x['ym']), None if x['ls_final'] is None else round(x['ls_final'] * 100, 1), 'dom', x['dom'], 'n', x['n'], 'over', None if x['over'] is None else round(x['over'] * 100))
        print('  new/closed', [(ymlab(x['ym']), x['new'], x['closed']) for x in t['newl']], 'tot new', sum(x['new'] for x in t['newl']), 'tot closed', sum(x['closed'] for x in t['newl']))
        print('  inv', [(ymlab(x['ym']), x['active'], round(x['moi'], 1)) for x in t['inv']])
        pts = self.bubble_points()
        print('  bubble n', len(pts), 'median dom all', statistics.median([q[1] for q in pts]))

    def bubble_points(self):
        c = self.c
        simids = {r['id'] for r in self.sim}
        sside = self.S.get('side')
        pts = []
        for r in self.rec:
            if r['pt'] != 'SFR' or (sside and r['side'] != sside) or r['sd'] < c['since'] or r['mi'] > c['radius']:
                continue
            if not (c['bub_sf'][0] <= r['sf'] <= c['bub_sf'][1]):
                continue
            dm = comp_dom(r)
            if dm is None or r['ld'] == r['sd']:
                continue
            pts.append((r['p'], dm, r['sf'], r['id'] in simids))
        return pts

    # ---------- html pieces ----------
    def similar_table(self):
        c = self.c
        rows = []
        subj_done = False
        sj = c['subj']

        def subj_row():
            return (f"<tr class='subj'><td><span class='tierlbl tS'>Your home</span></td><td class='ad2'><strong>{c['street']}</strong><div class='sn'>{c['subj_note']}</div></td>"
                    f"<td>0.00</td><td>{sj['bdba']}</td><td class='num'>{sj['sf']:,}</td><td class='num'>{sj['lot']:,}</td><td>{sj['yb']}</td>"
                    f"<td colspan='2' style='font-weight:600'>Most likely value today</td><td class='num'>{usd(c['val_mid'])}</td><td colspan='5'></td><td class='num'>{usd(c['val_mid'] / sj['sf'])}</td></tr>")
        for r in self.sim:
            if not subj_done and r['p'] < c['val_mid']:
                rows.append(subj_row())
                subj_done = True
            cls, name = TIERS[r['tier']]
            name = r.get('badge', name)
            l2s = f"{r['l2s'] * 100:.1f}%" if r['l2s'] else ''
            rows.append(
                f"<tr><td><span class=\"tierlbl {cls}\">{name}</span></td><td class='ad2'><strong>{r['a']}</strong><div class='sn'>{r['note']}</div></td>"
                f"<td class='num'>{r['mi']:.2f}</td><td>{bdba(r)}</td><td class='num'>{r['sf']:,}</td><td class='num'>{r['lot']:,}</td><td>{r['yb']}</td>"
                f"<td class='num'>{usd(r['ol'])}</td><td class='num'>{usd(r['fl'])}</td><td class='num'><strong>{usd(r['p'])}</strong></td><td>{r['nc']}</td>"
                f"<td class='num'>{signed(r['p'] - r['ol'])}</td><td class='num'>{l2s}</td>{dom_td(r['dom'])}<td class='num'>{mdy(r['sd'])}</td><td class='num'>{usd(r['psf'])}</td></tr>")
        if not subj_done:
            rows.append(subj_row())
        head = ('<tr><th>Tier</th><th>Address and notes</th><th>Mi</th><th>Bd/Ba</th><th>SqFt</th><th>Lot</th><th>Built</th><th>Orig list</th><th>Final list</th>'
                '<th>Sold</th><th>Cuts</th><th>$ vs orig</th><th>List to sale</th><th>DOM</th><th>Closed</th><th>$/SqFt</th></tr>')
        return f'<div class="tw"><table class="wide"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'

    def similar_note(self):
        c = self.c
        parts = [f"{n} {usd(mp)} median, {usd(mpsf)}/sq ft (n={k})" for n, mp, mpsf, k in self.tier_stats()]
        d0 = min(r['sd'] for r in self.sim)
        d1 = max(r['sd'] for r in self.sim)
        return (f'<div class="tnote">{c["sim_scope"]}, closed {MON[d0.month - 1]} {d0.day} to {MON[d1.month - 1]} {d1.day}, {d1.year}. Tier medians: '
                + '; '.join(parts) + '.' + c.get('sim_note_extra', '') + ' List to sale is sold price divided by original list price. DOM is days from first listing to accepted offer.</div>')

    def reference_table(self):
        rows = []
        for r in sorted(self.ref, key=lambda r: -r['p']):
            cls, name = TIERS[r['tier']]
            name = r.get('badge', name)
            rows.append(f"<tr><td><span class=\"tierlbl {cls}\">{name}</span></td><td>{r['a']}</td><td class='num'>{r['mi']:.2f}</td><td>{bdba(r)}</td><td class='num'>{r['sf']:,}</td>"
                        f"<td class='num'>{r['lot']:,}</td><td class='num'><strong>{usd(r['p'])}</strong></td><td class='num'>{usd(r['psf'])}</td><td class='num'>{mdy(r['sd'])}</td><td class='nt'>{r['why']}</td></tr>")
        head = '<tr><th>Tier</th><th>Address</th><th>Mi</th><th>Bd/Ba</th><th>SqFt</th><th>Lot</th><th>Sold</th><th>$/SqFt</th><th>Closed</th><th>Why it is reference only</th></tr>'
        return f'<div class="tw"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'

    def active_table(self):
        rows = []
        for r in self.actv:
            st = {'Pending Do Not Show': 'Pending'}.get(r['st'], r['st'])
            was = usd(r['ol']) if (r['ol'] and r['ol'] > r['p']) else ''
            days = (TODAY - r['ld']).days if r['ld'] else ''
            rows.append(f"<tr><td><strong>{st}</strong></td><td>{r['a']}</td><td class='num'>{r['mi']:.2f}</td><td>{bdba(r)}</td><td class='num'>{r['sf']:,}</td><td class='num'>{r['lot']:,}</td><td>{r['yb']}</td>"
                        f"<td class='num'><strong>{usd(r['p'])}</strong></td><td class='num'>{was}</td><td class='num'>{days}</td><td class='nt'>{r['note']}</td></tr>")
        head = '<tr><th>Status</th><th>Address</th><th>Mi</th><th>Bd/Ba</th><th>SqFt</th><th>Lot</th><th>Built</th><th>Asking</th><th>Was</th><th>Days listed</th><th>Notes</th></tr>'
        return f'<div class="tw"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'

    def cuts_table(self):
        rows = []
        for r in sorted([r for r in self.sim if r['l2s']], key=lambda r: -r['l2s']):
            rows.append(f"<tr><td>{r['a']}</td><td class='num'>{usd(r['ol'])}</td><td class='num'>{usd(r['fl'])}</td><td>{r['nc']}</td><td class='num'><strong>{usd(r['p'])}</strong></td>"
                        f"<td class='num'>{signed(r['p'] - r['ol'])}</td><td class='num'>{r['l2s'] * 100:.1f}%</td>{dom_td(r['dom'])}</tr>")
        head = '<tr><th>Address</th><th>Original list</th><th>Final list</th><th># Cuts</th><th>Sold</th><th>$ vs original</th><th>List to sale</th><th>DOM</th></tr>'
        return f'<div class="tw"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'

    def closest_table(self):
        c = self.c
        sj = c['subj']
        rows = [f"<tr class='subj'><td>{c['street']} (your home)</td><td>{sj['bdba']}</td><td class='num'>{sj['sf']:,}</td><td class='num'>{sj['lot']:,}</td><td>{sj['yb']}</td><td>{sj['cond']}</td>"
                f"<td class='num'>{usd(c['val_mid'])} (most likely)</td><td class='num'>{usd(c['val_mid'] / sj['sf'])}</td><td>0.00</td></tr>"]
        simid = {r['id']: r for r in self.sim}
        for pid in c['closest']:
            r = simid[pid]
            rows.append(f"<tr><td>{r['a']}</td><td>{bdba(r)}</td><td class='num'>{r['sf']:,}</td><td class='num'>{r['lot']:,}</td><td>{r['yb']}</td><td>{r.get('badge', TIERS[r['tier']][1])}</td>"
                        f"<td class='num'>{usd(r['p'])}</td><td class='num'>{usd(r['psf'])}</td><td class='num'>{r['mi']:.2f}</td></tr>")
        head = '<tr><th>Home</th><th>Bd/Ba</th><th>SqFt</th><th>Lot</th><th>Built</th><th>Condition</th><th>Price</th><th>$/SqFt</th><th>Mi</th></tr>'
        return f'<div class="tw"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'

    def chart_block(self, cid, title, svg, cap):
        return f'<div class="cb" id="{cid}"><h4>{title}</h4><div class="cw">{svg}</div><div class="cap">{cap}</div></div>'

    def trend_charts(self):
        c, t = self.c, self.t
        geo = c['trend_geo']
        out = []
        p = t['price']
        vals = [x['med3'] for x in p]
        dots = [x['med1'] for x in p]
        allv = [v for v in vals if v] + [v for v in dots if v]
        stepv = 100000 if max(allv) < 2000000 else (250000 if max(allv) < 4500000 else 500000)
        lo, hi = nice_bounds(allv, stepv)
        fm = (lambda v: f'${v / 1e6:.2f}M') if hi >= 1500000 else (lambda v: f'${v / 1e3:.0f}K')
        fl = lambda v: usd(v)
        svg = charts.line(vals, [ymlab(x['ym']) for x in p], fm, fl, lo, hi, stepv, dots=dots, every=6)
        out.append(self.chart_block('trendPrice', 'Median sale price', svg,
                                    f"Median sale price, {geo}. Each gold point is the median of all sales in the trailing three months; grey dots are single months. Based on {t['n_price_sales']} closed sales, {WIN['price_from']} to {WIN['lm_long']}."))
        ls = t['ls']
        lv = [None if x['ls_final'] is None else x['ls_final'] * 100 for x in ls]
        vv = [v for v in lv if v is not None]
        import math
        lo2, hi2 = math.floor(min(vv) / 2.0) * 2 - 2, math.ceil(max(vv) / 2.0) * 2 + 2
        svg = charts.line(lv, [ymlab(x['ym']) for x in ls], lambda v: f'{v:.0f}%', lambda v: f'{v:.1f}%', lo2, hi2, 2, every=2, ref=100, ref_label='100% = sold at asking')
        nls = t['n_listed']
        out.append(self.chart_block('trendLS', 'Sale price as a percent of list price', svg,
                                    f"Median of sold price divided by final list price, trailing three months, {geo}. Based on {nls} listed sales closed {WIN['rec_from']} to {WIN['lm_long']}."))
        nl = t['newl']
        svg = charts.bars2([ymlab(x['ym']) for x in nl], [x['new'] for x in nl], [x['closed'] for x in nl], 'New listings', 'Closed sales')
        out.append(self.chart_block('newList', 'New listings vs closed sales, last 12 months', svg,
                                    f"New listings and closed sales by month, {geo}, {WIN['newl_from']} to {WIN['lm_long']}."))
        inv = t['inv']
        iv = [x['moi'] for x in inv]
        hi3 = max(4, math.ceil(max(iv) + 0.5))
        svg = charts.line(iv, [ymlab(x['ym']) for x in inv], lambda v: f'{v:.0f}', lambda v: f'{v:.1f} months', 0, hi3, 1, every=2, ref=3, ref_label='3 months = balanced market')
        out.append(self.chart_block('monthsInv', 'Months of inventory', svg,
                                    f"Homes for sale at month end divided by the average monthly sales pace over the prior three months, {geo}. The dashed line marks 3 months, a balanced market. {WIN['lm_long']}: {inv[-1]['moi']:.1f} months."))
        return ''.join(out)

    def html(self):
        c = self.c
        sj = c['subj']
        logo = logo_uri()
        gain = c['val_mid'] - c['paid']
        nav = ''.join(f'<a class="l" href="https://graehamwatts.com/{u}">{n}</a>' for n, u in [
            ('Home', ''), ('Buy', 'buy-with-graeham'), ('Sell', 'sell-with-graeham'), ('Buying in the Bay', 'buying-in-the-bay'), ('The Bay Market', 'the-bay-real-estate-market'),
            ('Neighborhoods', 'bay-area-homes-for-sale'), ('Blogs', 'blog'), ('About', 'about'), ('Reviews', 'reviews'), ('Contact', 'contact-us')])
        fm = lambda v: f'${v / 1e6:.2f}M' if v >= 1e6 else f'${v / 1e3:.0f}K'
        # charts
        bar_items = [(r['a'], r['p'], False) for r in self.sim] + [(c['street'] + ' (your home)', c['val_mid'], True)]
        bar_items.sort(key=lambda x: -x[1])
        comp_bar = charts.hbar(bar_items, usd)
        psf_items = [(r['a'], r['psf'], False) for r in self.sim] + [(c['street'] + ' (your home)', c['val_mid'] / sj['sf'], True)]
        psf_items.sort(key=lambda x: -x[1])
        psf_bar = charts.hbar(psf_items, usd)
        pts = self.bubble_points()
        med_dom = statistics.median([q[1] for q in pts])
        bub = charts.bubble(pts, (c['val_mid'], med_dom, sj['sf']), fm)
        jr = charts.journey(c['paid_label'] + ' purchase', c['paid'], RUN['report_month'], c['val_mid'], c['r_low'][0], c['r_top'][1], fm, usd)
        rng = lambda t: f"{usd(t[0])} to {usd(t[1])}"
        short = lambda t: f"${t[0] / 1e6:.2f}M to ${t[1] / 1e6:.2f}M" if t[0] >= 1e6 else f"${t[0] / 1e3:.0f}K to ${t[1] / 1e3:.0f}K"
        home_rows = ''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in c['home_rows'])
        story = ''.join(f'<p>{p}</p>' for p in c['story'])
        rates = ''.join(f'<div class="st"><div class="n">{a}</div><div class="l">{b}</div></div>' for a, b in RATES)
        css = open(os.path.join(HERE, 'style.css'), encoding='utf-8').read()
        H = []
        H.append(f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Home Value Update, {c['street']}, {c['city']} | {ID['name']}</title>
<meta name="description" content="Home value update for {c['street']}, {c['city']}, prepared by {ID['name']}, {RUN['report_month']}.">
<meta name="robots" content="noindex">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Montserrat:wght@700;800&display=swap" rel="stylesheet">
<style>
{css}
</style></head><body>
<nav class="nav"><a href="https://graehamwatts.com/"><img src="https://images.leadconnectorhq.com/image/f_webp/q_80/r_1200/u_https://assets.cdn.filesafe.space/6wuU3haUH7uNeT20E3UZ/media/691256870b647e40e3c2e105.png" alt="{ID['name']}"></a>{nav}</nav>
<header class="hero"><div class="wrap"><div class="nm">{ID['name'].upper()}</div><div class="rl">{' '.join(ID['title'].upper())}</div>
<img class="lk" src="{logo}" alt="The Boyenga Team + Compass">
<div class="br">{ID['brand_line']}</div>
<div class="lbl">HOME VALUE UPDATE</div>
<div class="ad">{c['addr_full']}</div>
<div class="dt">Prepared for {c['first']}, {RUN['report_month']}</div>
<div class="cn">{ID['name']} | DRE #{ID['dre']} | {ID['phone']} | {ID['website']}</div></div></header>
<div class="wrap">

<section style="padding-top:28px"><div class="sh">Where You Stand</div>
<p class="lead">{c['lead']}</p>
<div class="stats"><div class="st"><div class="n">{usd(c['val_mid'])}</div><div class="l">Most likely value today</div></div>
<div class="st"><div class="n">{usd(c['paid'])}</div><div class="l">You paid, {c['paid_label']}</div></div>
<div class="st"><div class="n">{c.get('gain_text', signed(gain))}</div><div class="l">{c.get('gain_label', 'Value gained')}</div></div>
<div class="st"><div class="n">{short(c['r_mid'])}</div><div class="l">Most likely range</div></div></div>
</section>

<div class="dv"></div>
<section><div class="sh">Your Home</div>
<div class="tw"><table><tbody>
{home_rows}
</tbody></table></div>
</section>

<div class="dv"></div>
<section><div class="sh">The Market Story</div>{story}</section>

<div class="dv"></div>
<section><div class="sh">Comparable Sales</div>
<p>{c['comps_intro']}</p>
<div class="card"><strong>Most similar sales.</strong> {c['sim_card']}</div>
{self.similar_table()}
{self.similar_note()}
<div class="card" style="margin-top:22px"><strong>Reference only.</strong> {c['ref_card']}</div>
{self.reference_table()}
<div class="tnote">{c['ref_left_out']}</div>
<div class="card" style="margin-top:22px"><strong>For sale and in contract right now.</strong> {c['act_card']}</div>
{self.active_table()}
<div class="tnote">Asking prices and status as of {WIN['today_long']}. Days listed counts from the list date. {c.get('act_left_out', '')}</div>
</section>

<div class="dv"></div>
<section><div class="sh">Market Trends</div>
<p>{c['trend_intro']}</p>
{self.trend_charts()}
</section>

<div class="dv"></div>
<section><div class="sh">Interest Rate Environment</div>
<div class="stats">{rates}</div>
<p>{c['rate_par']}</p>
</section>

<div class="dv"></div>
<section><div class="sh">Price Cuts and Your Equity</div>
<p>{c['cuts_par']}</p>
{self.cuts_table()}
{self.chart_block('priceJourney', 'Your equity journey', jr, c['journey_cap'])}
</section>

<div class="dv"></div>
<section><div class="sh">Where Your Home Lands</div>
{self.chart_block('compBar', 'Most similar sales, with your home', comp_bar, "Sold prices of the most similar sales, with your home's most-likely value in black.")}
{self.chart_block('psfChart', 'Price per square foot', psf_bar, c.get('psf_cap', 'Sold price divided by square feet for the most similar sales. Your home is shown at its most-likely value.'))}
<h4 style="font-family:Montserrat,Inter,sans-serif;margin:22px 0 4px">Your home next to its closest matches</h4>
{self.closest_table()}
{self.chart_block('priceDom', 'Recent sales: price vs days on market', bub, f"Each bubble is a single-family sale since {MON[c['since'].month - 1]} {c['since'].day}, {c['since'].year} {c['bub_scope']}; bubble size reflects square footage and darker gold marks the most similar sales. Your home sits at its most-likely value and the group's median of {med_dom:g} days.")}
</section>

<div class="dv"></div>
<section><div class="sh">What Your Home Is Worth Today</div>
<div class="rng">
<div class="rc" style="border-left:7px solid #4f9d69"><div class="rl">Likely range</div><div class="rp">{rng(c['r_low'])}</div><div class="rd">{c['cards'][0]}</div></div>
<div class="rc" style="border-left:7px solid #C5A55A"><div class="rl">Most likely value today</div><div class="rp">{rng(c['r_mid'])}</div><div class="rd">{c['cards'][1]}</div></div>
<div class="rc" style="border-left:7px solid #E57373"><div class="rl">Top of range in strong condition</div><div class="rp">{rng(c['r_top'])}</div><div class="rd">{c['cards'][2]}</div></div>
</div>
<p style="font-size:12.5px;color:var(--gy)">Professional opinion of value, not a formal appraisal.</p>
<p>{c['equity_par']}</p>
</section>

<div class="dv"></div>
<section><div class="sh">Staying In Touch</div>
<p>{c.get('cta', "One quick ask: if you know anyone thinking about buying or selling, I'd be grateful for the introduction. Just reply with their name, forward them this update, or give me a call. Referrals from past clients mean the world to me.")}</p>
<p>{ID['name']}<br>{ID['phone']} | {ID['email']} | {ID['website']}</p>
</section>
</div>
<footer><div class="fn">{ID['name'].upper()}</div><img class="lk lkf" src="{logo}" alt="The Boyenga Team + Compass"><div class="fb">{ID['title']}. {ID['brand_line']}.</div>
<div class="fl">DRE #{ID['dre']} | {ID['phone']} | {ID['website']}</div>
<div class="ds">Prepared for the owner of {c['street']}, {c['city']}, {RUN['report_month']}. Professional opinion of value, not a formal appraisal.</div></footer>
</body></html>''')
        out = ''.join(H)
        for a, b in c.get('replace', []):
            out = out.replace(a, b)
        return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    key = sys.argv[1]
    cfg = importlib.import_module('cfg_' + key).CFG
    ctx = Ctx(cfg)
    if '--facts' in sys.argv:
        ctx.facts()
    else:
        os.makedirs(OUT, exist_ok=True)
        html = ctx.html()
        path = os.path.join(OUT, cfg['file'])
        open(path, 'w', encoding='utf-8').write(html)
        print('wrote', path, len(html), 'bytes')
