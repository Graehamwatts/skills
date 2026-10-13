"""Static inline-SVG charts for the past-client home value updates (no JavaScript, so they render in previews, email and PDF)."""
import math

GOLD, DGOLD, BLACK, GREY, GREEN, RED = '#C5A55A', '#A88B3D', '#1A1A1A', '#666', '#4f9d69', '#E57373'
FONT = 'font-family:Inter,Arial,sans-serif'


def _open(w, h):
    return [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" style="width:100%;height:auto;display:block;{FONT}">']


def money_k(v):
    return f'${v / 1e6:.2f}M' if v >= 1e6 else f'${v / 1e3:.0f}K'


def line(values, labels, tick_fmt, label_fmt, ymin, ymax, step, color=GOLD, dots=None, ref=None, ref_label='', every=6, w=940, h=280):
    """Line chart. values may contain None (gap). labels = one per point; an x tick is drawn every `every` points."""
    L, R, T, B = 70, 22, 18, 38
    n = len(values)
    X = lambda i: L + i * (w - L - R) / max(n - 1, 1)
    Y = lambda v: T + (ymax - min(max(v, ymin), ymax)) * (h - T - B) / (ymax - ymin)
    o = _open(w, h)
    v = ymin
    while v <= ymax + 1e-9:
        y = Y(v)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{w - R}" y2="{y:.1f}" stroke="#ececec"/>')
        o.append(f'<text x="{L - 8}" y="{y + 4:.1f}" font-size="12" fill="{GREY}" text-anchor="end">{tick_fmt(v)}</text>')
        v += step
    for i, lab in enumerate(labels):
        if (n - 1 - i) % every == 0:
            x = X(i)
            o.append(f'<line x1="{x:.1f}" y1="{h - B}" x2="{x:.1f}" y2="{h - B + 4}" stroke="#bbb"/>')
            o.append(f'<text x="{x:.1f}" y="{h - 14}" font-size="12" fill="{GREY}" text-anchor="middle">{lab}</text>')
    if ref is not None:
        y = Y(ref)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{w - R}" y2="{y:.1f}" stroke="{BLACK}" stroke-width="1.4" stroke-dasharray="7 5"/>')
        o.append(f'<text x="{w - R - 4}" y="{y - 6:.1f}" font-size="12" fill="{BLACK}" text-anchor="end">{ref_label}</text>')
    if dots:
        for i, dv in enumerate(dots):
            if dv is not None:
                o.append(f'<circle cx="{X(i):.1f}" cy="{Y(dv):.1f}" r="2.6" fill="#c9c9c9"/>')
    segs, cur = [], []
    for i, val in enumerate(values):
        if val is None:
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append((X(i), Y(val)))
    if cur:
        segs.append(cur)
    for s in segs:
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in s)
        base = Y(ymin)
        o.append(f'<path d="{d} L{s[-1][0]:.1f},{base:.1f} L{s[0][0]:.1f},{base:.1f} Z" fill="{color}" fill-opacity="0.08"/>')
        o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>')
        if len(s) <= 14:
            for x, y in s:
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
    lx, ly = segs[-1][-1]
    last = [x for x in values if x is not None][-1]
    o.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="{color}"/>')
    prev_y = segs[-1][-2][1] if len(segs[-1]) > 1 else ly
    laby = ly + 20 if prev_y < ly - 4 else ly - 10
    o.append(f'<text x="{lx - 8:.1f}" y="{laby:.1f}" font-size="13" font-weight="700" fill="{DGOLD}" text-anchor="end" paint-order="stroke" stroke="#fff" stroke-width="3">{label_fmt(last)}</text>')
    o.append('</svg>')
    return ''.join(o)


def bars2(labels, a, b, name_a, name_b, w=940, h=280):
    L, R, T, B = 46, 18, 30, 38
    n = len(labels)
    top = max(max(a), max(b), 1)
    ymax = int(math.ceil(top / 5.0) * 5)
    step = 5 if ymax <= 30 else 10
    Y = lambda v: T + (ymax - v) * (h - T - B) / ymax
    gw = (w - L - R) / n
    bw = gw * 0.34
    o = _open(w, h)
    v = 0
    while v <= ymax:
        y = Y(v)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{w - R}" y2="{y:.1f}" stroke="#ececec"/>')
        o.append(f'<text x="{L - 8}" y="{y + 4:.1f}" font-size="12" fill="{GREY}" text-anchor="end">{v}</text>')
        v += step
    for i, lab in enumerate(labels):
        x0 = L + i * gw + gw * 0.14
        for j, (val, col) in enumerate(((a[i], GOLD), (b[i], BLACK))):
            x = x0 + j * (bw + 2)
            y = Y(val)
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h - B - y:.1f}" fill="{col}" rx="2"/>')
            o.append(f'<text x="{x + bw / 2:.1f}" y="{y - 4:.1f}" font-size="11" fill="#444" text-anchor="middle">{val}</text>')
        o.append(f'<text x="{L + i * gw + gw / 2:.1f}" y="{h - 14}" font-size="11.5" fill="{GREY}" text-anchor="middle">{lab}</text>')
    o.append(f'<rect x="{L + 6}" y="6" width="12" height="12" fill="{GOLD}" rx="2"/><text x="{L + 24}" y="16" font-size="12" fill="#333">{name_a}</text>')
    o.append(f'<rect x="{L + 150}" y="6" width="12" height="12" fill="{BLACK}" rx="2"/><text x="{L + 168}" y="16" font-size="12" fill="#333">{name_b}</text>')
    o.append('</svg>')
    return ''.join(o)


def hbar(items, fmt, w=940, xmin=0):
    """items: list of (label, value, is_subject). Horizontal bars, subject in black."""
    rowh = 30
    L, R, T, B = 230, 96, 8, 10
    h = T + B + rowh * len(items)
    vmax = max(v for _, v, _ in items) * 1.02
    X = lambda v: L + (v - xmin) * (w - L - R) / (vmax - xmin)
    o = _open(w, h)
    for i, (lab, v, subj) in enumerate(items):
        y = T + i * rowh
        col = BLACK if subj else GOLD
        wt = '800' if subj else '500'
        o.append(f'<text x="{L - 10}" y="{y + 19}" font-size="12.5" font-weight="{wt}" fill="#222" text-anchor="end">{lab}</text>')
        o.append(f'<rect x="{L}" y="{y + 5}" width="{max(X(v) - L, 2):.1f}" height="{rowh - 11}" fill="{col}" rx="3"/>')
        o.append(f'<text x="{X(v) + 7:.1f}" y="{y + 19}" font-size="12.5" font-weight="{wt}" fill="#222">{fmt(v)}</text>')
    o.append('</svg>')
    return ''.join(o)


def bubble(points, subject, xfmt, w=940, h=360):
    """points: (price, dom, sqft, is_similar). subject: (price, dom, sqft)."""
    L, R, T, B = 60, 26, 30, 46
    xs = [p[0] for p in points] + [subject[0]]
    ys = [p[1] for p in points] + [subject[1]]
    x0, x1 = min(xs) * 0.95, max(xs) * 1.04
    ymax = max(max(ys) * 1.12, 30)
    sfs = [p[2] for p in points if p[2]] + [subject[2]]
    s0, s1 = min(sfs), max(sfs)
    X = lambda v: L + (v - x0) * (w - L - R) / (x1 - x0)
    Y = lambda v: T + (ymax - v) * (h - T - B) / ymax
    rad = lambda s: 6 + 10 * ((s - s0) / (s1 - s0) if s1 > s0 else 0.5)
    o = _open(w, h)
    step = 20 if ymax <= 130 else 40
    v = 0
    while v <= ymax:
        y = Y(v)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{w - R}" y2="{y:.1f}" stroke="#ececec"/>')
        o.append(f'<text x="{L - 8}" y="{y + 4:.1f}" font-size="12" fill="{GREY}" text-anchor="end">{v}</text>')
        v += step
    for k in range(6):
        xv = x0 + (x1 - x0) * k / 5.0
        o.append(f'<text x="{X(xv):.1f}" y="{h - 24}" font-size="12" fill="{GREY}" text-anchor="middle">{xfmt(xv)}</text>')
    o.append(f'<text x="{(L + w - R) / 2:.1f}" y="{h - 6}" font-size="12" fill="{GREY}" text-anchor="middle">Sold price</text>')
    o.append(f'<text x="14" y="{(T + h - B) / 2:.1f}" font-size="12" fill="{GREY}" text-anchor="middle" transform="rotate(-90 14 {(T + h - B) / 2:.1f})">Days on market</text>')
    for price, dom, sf, sim in sorted(points, key=lambda p: -p[2]):
        col, op = (DGOLD, 0.85) if sim else (GOLD, 0.38)
        o.append(f'<circle cx="{X(price):.1f}" cy="{Y(dom):.1f}" r="{rad(sf or s0):.1f}" fill="{col}" fill-opacity="{op}" stroke="{DGOLD}" stroke-width="1"/>')
    sx, sy = X(subject[0]), Y(subject[1])
    o.append(f'<path d="M{sx:.1f},{sy - 12:.1f} L{sx + 12:.1f},{sy:.1f} L{sx:.1f},{sy + 12:.1f} L{sx - 12:.1f},{sy:.1f} Z" fill="{BLACK}" stroke="{GOLD}" stroke-width="2.5"/>')
    o.append(f'<text x="{sx:.1f}" y="{sy - 20:.1f}" font-size="12.5" font-weight="800" fill="{BLACK}" text-anchor="middle" paint-order="stroke" stroke="#fff" stroke-width="3.5">Your home</text>')
    o.append(f'<circle cx="{L + 12}" cy="12" r="6" fill="{DGOLD}" fill-opacity="0.85"/><text x="{L + 24}" y="16" font-size="12" fill="#333">Most similar sales</text>')
    o.append(f'<circle cx="{L + 166}" cy="12" r="6" fill="{GOLD}" fill-opacity="0.38" stroke="{DGOLD}"/><text x="{L + 178}" y="16" font-size="12" fill="#333">Other nearby sales</text>')
    o.append('</svg>')
    return ''.join(o)


def journey(lab0, p0, lab1, p1, low, high, fmt, pfmt=None, w=940, h=300):
    pfmt = pfmt or fmt
    L, R, T, B = 80, 190, 24, 44
    lo = min(p0, low) * 0.9
    hi = max(p1, high) * 1.06
    Y = lambda v: T + (hi - v) * (h - T - B) / (hi - lo)
    xa, xb = L + 90, w - R
    o = _open(w, h)
    for k in range(5):
        v = lo + (hi - lo) * k / 4.0
        y = Y(v)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{w - 20}" y2="{y:.1f}" stroke="#ececec"/>')
        o.append(f'<text x="{L - 8}" y="{y + 4:.1f}" font-size="12" fill="{GREY}" text-anchor="end">{fmt(v)}</text>')
    o.append(f'<line x1="{xa}" y1="{Y(p0):.1f}" x2="{xb}" y2="{Y(high):.1f}" stroke="{RED}" stroke-width="1.6" stroke-dasharray="6 5"/>')
    o.append(f'<line x1="{xa}" y1="{Y(p0):.1f}" x2="{xb}" y2="{Y(low):.1f}" stroke="{GREEN}" stroke-width="1.6" stroke-dasharray="6 5"/>')
    o.append(f'<line x1="{xa}" y1="{Y(p0):.1f}" x2="{xb}" y2="{Y(p1):.1f}" stroke="{GOLD}" stroke-width="3.2" stroke-linecap="round"/>')
    o.append(f'<circle cx="{xa}" cy="{Y(p0):.1f}" r="6" fill="{BLACK}"/><circle cx="{xb}" cy="{Y(p1):.1f}" r="7" fill="{GOLD}" stroke="{BLACK}" stroke-width="2"/>')
    o.append(f'<text x="{xa}" y="{Y(p0) + 22:.1f}" font-size="12.5" font-weight="700" fill="#222" text-anchor="middle">{pfmt(p0)}</text>')
    o.append(f'<text x="{xb + 12}" y="{Y(p1) + 4:.1f}" font-size="13" font-weight="800" fill="#222">{pfmt(p1)} today</text>')
    if abs(Y(high) - Y(p1)) > 13:
        o.append(f'<text x="{xb + 12}" y="{Y(high) + 4:.1f}" font-size="11.5" fill="{RED}">{fmt(high)} top</text>')
    if abs(Y(low) - Y(p1)) > 13:
        o.append(f'<text x="{xb + 12}" y="{Y(low) + 4:.1f}" font-size="11.5" fill="{GREEN}">{fmt(low)} low</text>')
    o.append(f'<text x="{xa}" y="{h - 14}" font-size="12" fill="{GREY}" text-anchor="middle">{lab0}</text>')
    o.append(f'<text x="{xb}" y="{h - 14}" font-size="12" fill="{GREY}" text-anchor="middle">{lab1}</text>')
    o.append('</svg>')
    return ''.join(o)
