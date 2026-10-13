"""Append this run to cma/_autobuild_log.json (the file next week's run reads to skip what is already done).

Run from the WORK folder:  python <skill>/scripts/logappend.py <path to _autobuild_log.json> <sent.json>
sent.json maps each sent key to its Gmail message id and send time:
  {"abc": {"id": "<gmail message id>", "sent_at": "2026-10-12T18:15:37Z"}}
Clients listed under "held" in run.json are logged with status held_not_sent so they are not rebuilt next week."""
import json, sys, os
from mkt import RUN, WORK

log_path, sent_path = sys.argv[1], sys.argv[2]
log = json.load(open(log_path, encoding='utf-8')) if os.path.exists(log_path) else []
man = json.load(open(os.path.join(WORK, 'out', 'email_manifest.json'), encoding='utf-8'))
sent = json.load(open(sent_path, encoding='utf-8'))
have = {(e.get('client_name'), e.get('due_date')) for e in log}
added = 0
for key, s in sent.items():
    m = man[key]
    if (m['client'], m['due']) in have:
        continue
    log.append({'client_name': m['client'], 'client_email': m['client_email'], 'due_date': m['due'], 'property_address': m['property'], 'live_url': m['url'],
                'value_mid': m['val_mid'], 'value_low': m['low'], 'value_high': m['high'], 'median_psf': m['median_psf'], 'comps_used': m['comps'],
                'sent_at': s['sent_at'], 'data_source': 'mls_full' if RUN['data_source'] == 'MLS-FULL' else 'public_fallback', 'run_id': RUN['run_id'],
                'gmail_message_id': s['id']})
    added += 1
for h in RUN.get('held', []):
    if (h['client_name'], h['due_date']) in have:
        continue
    row = dict(h)
    row.update({'status': 'held_not_sent', 'live_url': None, 'sent_at': None, 'data_source': None, 'run_id': RUN['run_id']})
    log.append(row)
    added += 1
with open(log_path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(log, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('log entries added:', added, 'total', len(log))
