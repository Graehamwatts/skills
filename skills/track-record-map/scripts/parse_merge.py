import os
WORKDIR = os.environ.get('TRM_WORKDIR', os.getcwd())

import re, json, os

BASE = WORKDIR

FILES = [
    'search1_list_01466876.txt',
    'search2_buyer_01466876.txt',
    'search3_list_01254724.txt',
    'search4_buyer_01254724.txt',
    'search5_list_01254725.txt',
    'search6_buyer_01254725.txt',
    'search7_list_70010882.txt',
    'search8_buyer_70010882.txt',
]

# row pattern: N S MLS# ADDRESS $PRICE $SALEPRICE MM/DD/YYYY DOM BEDS BATHS|PARTBATHS SQFT [LOTSIZE] CITY Res. CLASS ...rest
ROW_RE = re.compile(
    r'^\d+\s+S\s+(?P<mls>\S+)\s+(?P<addr>.+?)\s+\$(?P<price>[\d,]+)\s+\$[\d,]+\s+(?P<date>\d{2}/\d{2}/\d{4})\s+.*?\s(?P<city>[A-Za-z][A-Za-z\.\' ]*?)\s+Res\.\s+(?P<cls>Single Family|Condominium|Townhouse|Farm/Ranch|Other)',
)

records = {}  # mls -> record
source_counts = {}

for fname in FILES:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print('MISSING', fname)
        continue
    count = 0
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            m = ROW_RE.match(line.strip())
            if not m:
                continue
            count += 1
            mls = m.group('mls').upper()
            addr = m.group('addr').strip()
            price = int(m.group('price').replace(',', ''))
            date = m.group('date')
            city = m.group('city').strip()
            # strip lot-size unit-label contamination that regex sometimes swallows
            city = re.sub(r'^(?:Lot\s+SqFt\s*|Acres\s*)+', '', city).strip()
            cls = m.group('cls')
            if mls not in records:
                records[mls] = {
                    'mls': mls, 'address': addr, 'price': price,
                    'date': date, 'city': city, 'cls': cls,
                    'sources': []
                }
            records[mls]['sources'].append(fname)
    source_counts[fname] = count

print('Per-file parsed row counts:')
for k, v in source_counts.items():
    print(' ', k, v)

print('Total unique MLS# after dedup:', len(records))

out_path = os.path.join(BASE, 'merged_listings.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(list(records.values()), f, indent=1)
print('Saved to', out_path)
