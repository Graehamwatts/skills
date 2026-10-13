"""Build the review emails: an internal note on top, a forward-ready client email below.

Run from the WORK folder:  python <skill>/scripts/emails.py [key ...]
Reads run.json (review_to, live_base, data_source, common_qc, held_note) and each cfg_<key>.py, whose CFG needs a
`mail` dict: {'subj_line': ..., 'qc': [internal notes], 'body': [client paragraphs]}.
Writes out/email_<key>.txt, out/email_<key>.html and out/email_manifest.json.

Two facts about the Gmail connector shape this template: it strips CSS backgrounds (so contrast comes from borders
and text color) and it wraps every link in a Google redirect (so the clean address is also shown as text)."""
import os, sys, json, statistics, importlib, html
from build import Ctx, usd
from mkt import RUN, WORK
from brand import ID

sys.stdout.reconfigure(encoding='utf-8')
OUT = os.path.join(WORK, 'out')
os.makedirs(OUT, exist_ok=True)
BASE = RUN['live_base']
SOURCE_LINE = {'MLS-FULL': 'MLS-FULL',
               'PUBLIC-FALLBACK': 'PUBLIC-FALLBACK (public records). Recommend a re-run when MLS is logged in.'}[RUN['data_source']]
ASK = ("One quick ask: if you know anyone thinking about buying or selling, I'd be grateful for the introduction. Just reply with their name, forward them this update, or give me a call. "
       "Referrals from past clients mean the world to me.")
LINK_NOTE = ("The page link below goes through a Google redirect because of how this email was sent. Before forwarding, select the link text, press Ctrl+K and paste the clean address shown next to 'Live CMA'.")

keys = sys.argv[1:] or [k for k in RUN['subjects'] if os.path.exists(os.path.join(WORK, 'cfg_%s.py' % k))]
manifest = {}
for key in keys:
    cfg = importlib.import_module('cfg_' + key).CFG
    ctx = Ctx(cfg)
    e = cfg['mail']
    url = BASE + cfg['file']
    psf = statistics.median([r['psf'] for r in ctx.sim])
    n = len(ctx.sim)
    low, top = cfg['r_low'][0], cfg['r_top'][1]
    prop = cfg['addr_full']
    subject = f"[REVIEW → forward] CMA ready: {cfg['street']}, {cfg['city']} - {cfg['client']}"
    qc = list(e['qc']) + list(RUN.get('common_qc', [])) + [LINK_NOTE] + ([RUN['held_note']] if RUN.get('held_note') else [])
    sig = [ID['name'], f"{ID['title']}, DRE #{ID['dre']}", ID['brand_line'], ID['phone']]
    # ---------- plain text ----------
    T = ['========== INTERNAL NOTE (delete this whole section before forwarding) ==========', '',
         f"\U0001F4E7 FORWARD TO: {cfg['email']}", f"\U0001F464 Client: {cfg['client']}", f"\U0001F3E1 Property: {prop}", f"\U0001F4C5 CMA due: {cfg['due']}",
         f"\U0001F4B0 Most-likely value: {usd(cfg['val_mid'])}   |   Range: {usd(low)} to {usd(top)}", f"\U0001F4CA Median $/sqft: {usd(psf)} (from {n} comps)",
         f"\U0001F517 Live CMA: {url}", f"\U0001F5C2 Data source: {SOURCE_LINE}", '', 'Quick QC notes:']
    T += [' * ' + q for q in qc]
    T += ['', f"⬇⬇⬇ DELETE EVERYTHING ABOVE THIS LINE BEFORE FORWARDING TO {cfg['email']} ⬇⬇⬇", '=' * 80,
          '⬆⬆⬆ EVERYTHING BELOW IS THE FORWARD-READY CLIENT EMAIL ⬆⬆⬆', '',
          f"Suggested subject: \U0001F525 {e['subj_line']}", '', f"Hi {cfg['first']},", '']
    for p in e['body']:
        T += [p, '']
    T += [f"View your home value update: {url}", '', ASK, ''] + sig
    plain = '\n'.join(T)
    # ---------- html ----------
    esc = html.escape
    rows = [('\U0001F4E7 FORWARD TO', f"<strong>{esc(cfg['email'])}</strong>"), ('\U0001F464 Client', esc(cfg['client'])), ('\U0001F3E1 Property', esc(prop)),
            ('\U0001F4C5 CMA due', esc(cfg['due'])),
            ('\U0001F4B0 Most-likely value', f"<strong>{usd(cfg['val_mid'])}</strong> &nbsp;|&nbsp; Range: {usd(low)} to {usd(top)}"),
            ('\U0001F4CA Median $/sqft', f"{usd(psf)} (from {n} comps)"), ('\U0001F517 Live CMA', f'<a href="{url}">{url}</a>'), ('\U0001F5C2 Data source', esc(SOURCE_LINE))]
    trs = ''.join(f'<tr><td style="padding:4px 12px 4px 0;font-weight:700;white-space:nowrap;vertical-align:top">{a}</td><td style="padding:4px 0">{b}</td></tr>' for a, b in rows)
    lis = ''.join(f'<li style="margin-bottom:6px">{esc(q)}</li>' for q in qc)
    paras = ''.join(f'<p style="margin:0 0 14px">{esc(p)}</p>' for p in e['body'])
    H = f'''<div style="font-family:Arial,Helvetica,sans-serif;font-size:14.5px;color:#1a1a1a;line-height:1.55;max-width:680px">
<div style="border:2px solid #999;padding:14px 16px">
<div style="font-weight:800;letter-spacing:1px;color:#555;font-size:12.5px;margin-bottom:8px">INTERNAL NOTE (delete this whole section before forwarding)</div>
<table cellpadding="0" cellspacing="0" style="font-size:14px;border-collapse:collapse">{trs}</table>
<div style="font-weight:700;margin:12px 0 6px">Quick QC notes</div>
<ul style="margin:0 0 4px 18px;padding:0">{lis}</ul>
</div>
<div style="border:4px solid #cc1f1f;color:#cc1f1f;font-weight:800;text-align:center;padding:12px;margin:18px 0 6px;font-size:15px">⬇⬇⬇ DELETE EVERYTHING ABOVE THIS LINE BEFORE FORWARDING TO {esc(cfg['email'])} ⬇⬇⬇</div>
<hr style="border:0;border-top:4px double #cc1f1f;margin:6px 0">
<div style="border:2px solid #1a7f37;color:#1a7f37;font-weight:800;text-align:center;padding:8px;margin:6px 0 20px;font-size:13.5px">⬆⬆⬆ EVERYTHING BELOW IS THE FORWARD-READY CLIENT EMAIL ⬆⬆⬆</div>
<p style="margin:0 0 16px;color:#555"><strong>Suggested subject:</strong> \U0001F525 {esc(e['subj_line'])}</p>
<p style="margin:0 0 14px">Hi {esc(cfg['first'])},</p>
{paras}
<p style="margin:0 0 18px"><a href="{url}" style="display:inline-block;border:2px solid #C5A55A;color:#1a1a1a;font-weight:700;text-decoration:none;padding:10px 18px;border-radius:6px">View your home value update &rarr;</a></p>
<p style="margin:0 0 14px">{esc(ASK)}</p>
<p style="margin:18px 0 0">{'<br>'.join(esc(x) for x in sig)}</p>
</div>'''
    open(os.path.join(OUT, f'email_{key}.txt'), 'w', encoding='utf-8', newline='\n').write(plain)
    open(os.path.join(OUT, f'email_{key}.html'), 'w', encoding='utf-8', newline='\n').write(H)
    manifest[key] = dict(subject=subject, to=RUN['review_to'], client=cfg['client'], client_email=cfg['email'], due=cfg['due'], property=prop, url=url,
                         val_mid=cfg['val_mid'], low=low, high=top, median_psf=round(psf), comps=n)
    bad = [ch for ch in (plain + H) if ch in '—–']
    print(key, '|', subject, '| plain', len(plain), 'html', len(H), '| em/en dashes:', len(bad))
json.dump(manifest, open(os.path.join(OUT, 'email_manifest.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
