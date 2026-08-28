import os
WORKDIR = os.environ.get('TRM_WORKDIR', os.getcwd())

import sys, re, json

# Brand values come from identity.json — the single source of truth. Never
# hardcode the DRE (correct or blocked) in this script; the repo tripwire
# blocks pushes that contain the blocked value as a literal.
IDENTITY = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared-references', 'identity.json')
with open(IDENTITY, encoding='utf-8') as f:  # fail closed: no identity.json -> crash, don't skip
    _id = json.load(f)
CORRECT_DRE = _id['identity']['dre']
BLOCKED = _id['_blocked_values']['dre_blocklist'] + _id['_blocked_values']['brand_blocklist']

PATH = os.path.join(WORKDIR, 'track-record-map-output.html')

with open(PATH, encoding='utf-8') as f:
    html = f.read()

ok = True

for bad in BLOCKED:
    if re.search(re.escape(bad), html, re.IGNORECASE):
        print(f"FAIL: blocked brand value present: {bad}")
        ok = False
if ok:
    print("PASS: no blocked brand values (DRE blocklist + brand blocklist) present")

if CORRECT_DRE in html:
    print(f"PASS: correct DRE {CORRECT_DRE} present")
else:
    print(f"FAIL: correct DRE {CORRECT_DRE} NOT present")
    ok = False

if '\u2014' in html:
    print("FAIL: em-dash character present")
    ok = False
else:
    print("PASS: em-dash absent")

# per-agent color/legend split check
if 'graeham' in html.lower().replace('graeham watts', '').replace('graehamwatts', ''):
    # crude check for leftover src:"graeham" style differentiation tokens
    pass
if 'dot boyenga' in html or 'dot graeham' in html or "src:\"graeham\"" in html or "src:\"boyenga\"" in html or 'colorFor' in html:
    print("FAIL: leftover per-agent color/legend split markers found")
    ok = False
else:
    print("PASS: no per-agent color/legend split markers")

VOID_TAGS = {'meta','link','br','img','input','hr','area','base','col','embed','source','track','wbr'}
tag_re = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>')
stack = []
balanced = True
for m in tag_re.finditer(html):
    closing, name, attrs = m.groups()
    name_l = name.lower()
    if name_l in VOID_TAGS:
        continue
    if attrs.strip().endswith('/'):
        continue
    if not closing:
        stack.append(name_l)
    else:
        if not stack or stack[-1] != name_l:
            if name_l in stack:
                while stack and stack[-1] != name_l:
                    stack.pop()
                stack.pop()
            else:
                print(f"FAIL: unmatched closing tag </{name_l}>")
                balanced = False
        else:
            stack.pop()
if stack:
    print(f"FAIL: unclosed tags remain: {stack}")
    balanced = False
if balanced and not stack:
    print("PASS: HTML tag balance OK")
else:
    ok = False

script_blocks = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.DOTALL)
inline_blocks = [s for s in script_blocks if s.strip() and 'src=' not in s]
print(f"INFO: found {len(inline_blocks)} inline <script> block(s) to syntax-check via Node")
with open(os.path.join(WORKDIR, 'inline_script2.js'), 'w', encoding='utf-8') as f:
    for b in inline_blocks:
        f.write(b)
        f.write('\n')

print()
print("OVERALL:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
