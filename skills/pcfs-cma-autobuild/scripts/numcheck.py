"""Guard for the humanizer pass: prove that no number changed.

Before the pass, copy cfg_*.py, shared.py and comps.py from the WORK folder into WORK/backup. After it:
  python <skill>/scripts/numcheck.py
Every digit sequence in each file must match its backup exactly, and no banned string may have crept in."""
import re, os, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
WORK = os.getcwd()
ok = True
files = [os.path.basename(p) for p in glob.glob(os.path.join(WORK, 'backup', '*.py'))]
if not files:
    sys.exit('Nothing in backup/. Copy the prose files there before the humanizer pass.')
for f in sorted(files):
    a = open(os.path.join(WORK, 'backup', f), encoding='utf-8').read()
    b = open(os.path.join(WORK, f), encoding='utf-8').read()
    na = collections.Counter(re.findall(r'\d[\d,.]*\d|\d', a))
    nb = collections.Counter(re.findall(r'\d[\d,.]*\d|\d', b))
    if na != nb:
        ok = False
        print(f, 'NUMBERS CHANGED: removed', dict(na - nb), 'added', dict(nb - na))
    else:
        print(f, 'numbers identical', sum(na.values()))
    for bad in ['—', '–', '&mdash;', ' -- ', 'no agenda', 'no-pressure', 'No agenda', 'public data', 'Redfin', 'Zillow', 'MLS unavailable', 'estimate only', 'N/A']:
        if bad in b:
            ok = False
            print('  BANNED STRING in', f, repr(bad))
print('ALL OK' if ok else 'PROBLEMS FOUND')
