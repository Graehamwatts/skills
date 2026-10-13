"""Save data the browser tool returned, without retyping it.

Anything the javascript tool returns as  ##X:<name>## ... ##END##  is in the session transcript. This script finds
those blocks and writes each one to data/<name>.txt in the WORK folder.

Run from the WORK folder:  python <skill>/scripts/extract_from_transcript.py [transcript.jsonl]
With no argument it uses the most recently modified .jsonl under ~/.claude/projects (the running session in Claude
Code). If your app keeps transcripts somewhere else, pass the path, or have the browser return smaller blocks and
write them to data/ with the Write tool."""
import json, sys, os, re, glob

sys.stdout.reconfigure(encoding='utf-8')
WORK = os.getcwd()
if len(sys.argv) > 1:
    T = sys.argv[1]
else:
    cands = glob.glob(os.path.join(os.path.expanduser('~'), '.claude', 'projects', '*', '*.jsonl'))
    if not cands:
        sys.exit('No transcript found under ~/.claude/projects. Pass the transcript path.')
    T = max(cands, key=os.path.getmtime)
print('transcript:', T)
BS = chr(92)
out = {}
with open(T, encoding='utf-8') as f:
    for line in f:
        if '##X:' not in line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get('type') != 'user':
            continue
        c = o.get('message', {}).get('content')
        if not isinstance(c, list):
            continue
        for b in c:
            if b.get('type') != 'tool_result':
                continue
            cc = b.get('content')
            texts = [x.get('text', '') for x in cc] if isinstance(cc, list) else [cc or '']
            for t in texts:
                for m in re.finditer(r'##X:(\w+)##(.*?)##END##', t, flags=re.S):
                    out[m.group(1)] = m.group(2).replace(BS + 'n', chr(10)).replace(BS + '"', '"')
os.makedirs(os.path.join(WORK, 'data'), exist_ok=True)
for k, v in out.items():
    open(os.path.join(WORK, 'data', k + '.txt'), 'w', encoding='utf-8', newline='\n').write(v)
    n = len(v.split(';')) if k.startswith('old_') else len(v.split(chr(10)))
    print(k, len(v), 'chars', n, 'rows')
if not out:
    print('no ##X: blocks found')
