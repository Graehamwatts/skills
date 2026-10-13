"""Pre-publish scan of the built pages (and the review emails when they exist).

Run from the WORK folder:  python <skill>/scripts/final_check.py [key ...]
Checks structure, banned wording, dash characters, third person, brand lines and that the value figures agree with
each other. It does not check comps or math: that is the independent reviewer's job."""
import os, re, sys, importlib, html, unicodedata
from mkt import RUN, WORK
from brand import ID

sys.stdout.reconfigure(encoding='utf-8')
OUT = os.path.join(WORK, 'out')


def usd(n):
    return '${:,.0f}'.format(n)


def visible(h):
    h = re.sub(r'data:image/[a-z]+;base64,[A-Za-z0-9+/=]+', '', h)
    h = re.sub(r'<style.*?</style>', ' ', h, flags=re.S)
    svgtext = ' '.join(re.findall(r'<text[^>]*>(.*?)</text>', h, flags=re.S))
    body = re.sub(r'<svg.*?</svg>', ' ', h, flags=re.S)
    body = re.sub(r'<[^>]+>', ' ', body)
    return html.unescape(re.sub(r'\s+', ' ', body)), html.unescape(svgtext)


# The retired DRE number is assembled here so this file does not itself trip the repo's brand tripwire.
WRONG_DRE = '0201' + '5066'
BANNED = ['no agenda', 'no-pressure', 'check in', 'redfin', 'zillow', 'public data', 'public record', 'mls', 'estimate only', 'n/a', 'intero', 'compass real estate', WRONG_DRE,
          'notes & caveats', 'about this analysis', 'lower-confidence', 'verify these numbers', 'the client', 'the seller', "let's list", 'ready to sell', 'nestled', 'source:']
IDS = ['trendPrice', 'trendLS', 'newList', 'monthsInv', 'priceJourney', 'compBar', 'psfChart', 'priceDom']
SECTIONS = ['Where You Stand', 'Your Home', 'The Market Story', 'Comparable Sales', 'Market Trends', 'Interest Rate Environment', 'Price Cuts and Your Equity', 'Where Your Home Lands',
            'What Your Home Is Worth Today', 'Staying In Touch']
keys = sys.argv[1:] or [k for k in RUN['subjects'] if os.path.exists(os.path.join(WORK, 'cfg_%s.py' % k))]
ok = True
for key in keys:
    cfg = importlib.import_module('cfg_' + key).CFG
    h = open(os.path.join(OUT, cfg['file']), encoding='utf-8').read()
    body, svg = visible(h)
    text = body + ' ' + svg
    low = text.lower()
    probs = []
    for ch in set(text):
        if unicodedata.category(ch) == 'Pd' and ch != '-':
            probs.append('dash char U+%04X' % ord(ch))
    if '&mdash;' in h or '&ndash;' in h or ' -- ' in text:
        probs.append('dash entity')
    for b in BANNED:
        for m in re.finditer(r'(?<![a-z])' + re.escape(b) + r'(?![a-z])', low):
            probs.append('banned: ' + b + ' -> ' + text[max(0, m.start() - 40):m.end() + 30])
    for i in IDS:
        m = re.search(r'id="%s".*?<svg(.*?)</svg>' % i, h, flags=re.S)
        if not m or len(m.group(1)) < 400:
            probs.append('chart missing/empty: ' + i)
    pos = [h.find('<div class="sh">%s</div>' % s) for s in SECTIONS]
    if -1 in pos or pos != sorted(pos):
        probs.append('sections missing or out of order: %s' % pos)
    for need in ['HOME VALUE UPDATE', 'DRE #' + ID['dre'], ID['brand_line'], 'Professional opinion of value, not a formal appraisal.', "I'd be grateful for the introduction",
                 usd(cfg['val_mid']), usd(cfg['paid']), 'Hi %s, here is an update on your home, just keeping you informed.' % cfg['first'],
                 'Prepared for %s, %s' % (cfg['first'], RUN['report_month'])]:
        if need not in text:
            probs.append('missing: ' + need)
    if h.count('DRE #' + ID['dre']) < 2:
        probs.append('DRE not in both hero and footer')
    if not (cfg['r_mid'][0] <= cfg['val_mid'] <= cfg['r_mid'][1]) or (cfg['r_mid'][0] + cfg['r_mid'][1]) / 2 != cfg['val_mid']:
        probs.append('most-likely value is not the midpoint of its range')
    if not (cfg['r_low'][1] <= cfg['r_mid'][0] and cfg['r_mid'][1] <= cfg['r_top'][0]):
        probs.append('ranges overlap')
    for s in [usd(cfg['r_low'][0]), usd(cfg['r_top'][1]), 'Midpoint about ' + usd(cfg['val_mid'])]:
        if s not in text:
            probs.append('range figure not in text: ' + s)
    for w in [r'\bhis\b', r'\bher\b', r'\bshe\b', r'\bhe\b', r'\bhim\b']:
        for m in re.finditer(w, low):
            probs.append('third person: ' + text[max(0, m.start() - 40):m.end() + 30])
    if re.search(r'<script', h):
        probs.append('script tag present')
    for ext in ['txt', 'html']:
        p = os.path.join(OUT, 'email_%s.%s' % (key, ext))
        if not os.path.exists(p):
            continue
        e = open(p, encoding='utf-8').read()
        ev = html.unescape(re.sub(r'<[^>]+>', ' ', e))
        client_part = ev.split('FORWARD-READY CLIENT EMAIL')[-1]
        if any(ch in ev for ch in '—–'):
            probs.append('email dash (%s)' % ext)
        for b in ['no agenda', 'no-pressure', 'public', 'mls', 'redfin', 'intero', WRONG_DRE, 'compass real estate']:
            if b in client_part.lower():
                probs.append('email client section banned: ' + b)
        if usd(cfg['val_mid']) not in client_part or cfg['file'] not in e or cfg['email'] not in e:
            probs.append('email missing value, link or forward address (%s)' % ext)
    print(key, cfg['file'], 'words', len(body.split()), 'bytes', len(h), 'PROBLEMS: %d' % len(probs))
    for p_ in probs:
        ok = False
        print('   -', p_[:220])
print('ALL CLEAN' if ok else 'FIX NEEDED')
