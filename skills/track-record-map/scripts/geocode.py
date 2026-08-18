import os
WORKDIR = os.environ.get('TRM_WORKDIR', os.getcwd())

import json, time, urllib.request, urllib.parse, sys, re, os

IN_PATH = os.path.join(WORKDIR, 'merged_listings.json')
OUT_PATH = os.path.join(WORKDIR, 'geocoded_listings.json')
CACHE_PATH = os.path.join(WORKDIR, 'geocode_cache.json')

UA = 'GraehamWattsRealEstate-TrackRecordMap/1.1'

def clean_address(addr):
    # normalize unit markers, remove extra spaces
    addr = addr.strip()
    return addr

def query_nominatim(q):
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({'q': q, 'format': 'json', 'limit': 1, 'countrycodes': 'us'})
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"  ERROR for query '{q}': {e}", file=sys.stderr)
    return None

def main():
    with open(IN_PATH, encoding='utf-8') as f:
        records = json.load(f)

    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

    total = len(records)
    success = 0
    failed = []

    for i, r in enumerate(records):
        addr = clean_address(r['address'])
        # strip unit numbers for geocoding (they often confuse Nominatim) - keep street number/name only
        addr_no_unit = re.sub(r',?\s*#\S+$', '', addr).strip()
        city = r['city']
        key = f"{addr_no_unit}|{city}"

        if key in cache and cache[key] is not None:
            r['lat'], r['lon'] = cache[key]
            success += 1
            continue
        if key in cache and cache[key] is None:
            failed.append(r)
            r['lat'], r['lon'] = None, None
            continue

        q1 = f"{addr_no_unit}, {city}, CA"
        result = query_nominatim(q1)
        time.sleep(1.05)

        if result is None:
            # fallback: try without street number's suite/extra tokens, just "City, CA"
            q2 = f"{city}, CA"
            result = query_nominatim(q2)
            time.sleep(1.05)

        if result:
            r['lat'], r['lon'] = result
            cache[key] = [result[0], result[1]]
            success += 1
        else:
            r['lat'], r['lon'] = None, None
            cache[key] = None
            failed.append(r)

        if (i+1) % 10 == 0:
            print(f"  progress: {i+1}/{total} geocoded, {success} success so far", file=sys.stderr)
            # periodically save cache
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f)

    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f)

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    print(f"DONE: {success}/{total} geocoded successfully. {len(failed)} failed.", file=sys.stderr)
    for r in failed:
        print(f"  FAILED: {r['mls']} {r['address']}, {r['city']}", file=sys.stderr)

if __name__ == '__main__':
    main()
