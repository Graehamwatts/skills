import os
WORKDIR = os.environ.get('TRM_WORKDIR', os.getcwd())

# -*- coding: utf-8 -*-
import json, re

GEOCODED_PATH = os.path.join(WORKDIR, 'geocoded_listings.json')
OUT_PATH = os.path.join(WORKDIR, 'track-record-map-output.html')

DRE = '01466876'
BRAND_LINE = 'Powered by The Boyenga Team at Compass Real Estate'

SUBJECT = {'lat': 37.334408, 'lon': -121.991415, 'addr': '3444 Kenyon Drive', 'city': 'Santa Clara'}

# Regional (mid-zoom) bounding box: Mountain View / Los Altos / Sunnyvale (NW)
# across Santa Clara / San Jose, down to Cupertino / Campbell / Saratoga (S)
REGIONAL_SW = [37.23, -122.14]
REGIONAL_NE = [37.43, -121.80]

with open(GEOCODED_PATH, encoding='utf-8') as f:
    records = json.load(f)

geocoded = [r for r in records if r.get('lat') is not None and r.get('lon') is not None]
skipped = [r for r in records if r.get('lat') is None]

print(f"Total unique MLS# records (merged, deduped): {len(records)}")
print(f"Geocoded successfully: {len(geocoded)}")
print(f"Failed to geocode: {len(skipped)}")
for r in skipped:
    print(f"  SKIPPED: {r['mls']} {r['address']}, {r['city']}")

def parse_date(d):
    m, day, y = d.split('/')
    return (int(y), int(m), int(day))

dates_sorted = sorted(records, key=lambda r: parse_date(r['date']))
earliest = dates_sorted[0]['date']
latest = dates_sorted[-1]['date']

def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;'))

def fmt_price(p):
    return '${:,.0f}'.format(p)

def fmt_date(d):
    m, day, y = d.split('/')
    months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return f"{months[int(m)]} {int(day)}, {y}"

def marker_js(records_list, varname):
    lines = [f"const {varname} = ["]
    for r in records_list:
        addr = esc(r['address'])
        city = esc(r['city'])
        price = fmt_price(r['price'])
        date_disp = fmt_date(r['date'])
        lines.append(
            '  {lat:%r, lon:%r, addr:"%s", city:"%s", price:"%s", date:"%s", mls:"%s"},' % (
                r['lat'], r['lon'], addr, city, price, date_disp, r['mls']
            )
        )
    lines.append("];")
    return "\n".join(lines)

all_js = marker_js(geocoded, 'ALL_LISTINGS')

total_count = len(records)
mapped_count = len(geocoded)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Boyenga Team + Graeham Watts Sold Track Record</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<style>
  :root {
    --gold: #b8912f;
    --gold-dark: #8f6f22;
    --navy: #1c2b45;
    --navy-light: #2e4266;
    --ink: #1a1a1a;
    --paper: #faf8f4;
    --card: #ffffff;
    --border: #e3ddd0;
    --muted: #6b6459;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background: var(--paper);
    color: var(--ink);
  }
  header {
    background: linear-gradient(135deg, var(--navy) 0%, var(--navy-light) 100%);
    color: #fff;
    padding: 40px 24px 32px;
    text-align: center;
  }
  header .eyebrow {
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-size: 12px;
    color: var(--gold);
    font-weight: 600;
    margin-bottom: 10px;
  }
  header h1 {
    margin: 0 0 10px;
    font-size: clamp(26px, 4vw, 42px);
    font-weight: 700;
    line-height: 1.15;
  }
  header p.sub {
    margin: 0 auto;
    max-width: 680px;
    font-size: 16px;
    color: #d8dde8;
    line-height: 1.5;
  }
  .stats {
    max-width: 1100px;
    margin: -30px auto 0;
    padding: 0 24px;
    position: relative;
    z-index: 5;
  }
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 14px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 20px;
    box-shadow: 0 10px 30px rgba(28,43,69,0.12);
  }
  .stat {
    text-align: center;
    padding: 6px 8px;
  }
  .stat .num {
    font-size: clamp(20px, 3vw, 30px);
    font-weight: 800;
    color: var(--navy);
  }
  .stat .label {
    font-size: 12.5px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
  }
  .stats-note {
    font-size: 12.5px;
    color: var(--muted);
    text-align: center;
    margin: 10px auto 0;
    max-width: 760px;
    line-height: 1.5;
  }
  main {
    max-width: 1100px;
    margin: 40px auto 60px;
    padding: 0 24px;
  }
  .section {
    margin-bottom: 46px;
  }
  .section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }
  .section-head h2 {
    margin: 0;
    font-size: 22px;
    color: var(--navy);
  }
  .section-head .count-pill {
    background: var(--gold);
    color: #fff;
    font-size: 13px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
  }
  .section p.desc {
    margin: 0 0 14px;
    color: var(--muted);
    font-size: 14.5px;
    max-width: 760px;
  }
  .map-wrap {
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 6px 20px rgba(28,43,69,0.08);
  }
  #map-wide { height: 560px; width: 100%; background: #e9e5da; }
  #map-regional { height: 520px; width: 100%; background: #e9e5da; }
  .legend {
    display: flex;
    gap: 18px;
    flex-wrap: wrap;
    margin-top: 12px;
    font-size: 13px;
    color: var(--muted);
  }
  .legend .dot {
    display: inline-block;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
    border: 1.5px solid rgba(0,0,0,0.25);
  }
  .dot.team { background: var(--gold); }
  .dot.subject { background: #c0392b; }
  .leaflet-popup-content {
    font-size: 13.5px;
    line-height: 1.5;
  }
  .popup-addr { font-weight: 700; color: var(--navy); }
  .popup-row { margin-top: 2px; }
  .popup-price { color: var(--gold-dark); font-weight: 700; }
  footer {
    background: var(--navy);
    color: #cfd6e4;
    text-align: center;
    padding: 30px 20px 34px;
    font-size: 13.5px;
    line-height: 1.7;
  }
  footer .brandline {
    color: #fff;
    font-weight: 700;
    font-size: 15px;
  }
  footer .dre {
    color: #9aa4bb;
  }
  .note {
    font-size: 12.5px;
    color: var(--muted);
    margin-top: 10px;
  }
</style>
</head>
<body>

<header>
  <div class="eyebrow">Sold Track Record</div>
  <h1>The Boyenga Team</h1>
  <p class="sub">Every recorded sold transaction in MLSListings tied to the Boyenga Team - Eric Boyenga, Janelle Boyenga, and Graeham Watts - mapped across the Silicon Valley footprint. Click any pin for address, sale price, and sale date.</p>
</header>

<div class="stats">
  <div class="stats-grid">
    <div class="stat"><div class="num">__TOTAL_COUNT__</div><div class="label">Total Sold Transactions</div></div>
    <div class="stat"><div class="num">__MAPPED_COUNT__</div><div class="label">Pins Mapped</div></div>
    <div class="stat"><div class="num">__EARLIEST_DATE__</div><div class="label">Earliest Close Date</div></div>
    <div class="stat"><div class="num">__LATEST_DATE__</div><div class="label">Most Recent Close Date</div></div>
  </div>
  <p class="stats-note">Includes homes listed and sold by the team, and homes purchased by team-represented buyers. De-duplicated by MLS number across List Agent and Buyer's Agent searches for Eric Boyenga (DRE 01254725), Janelle Boyenga (DRE 01254724), and Graeham Watts (DRE 01466876).</p>
</div>

<main>

  <div class="section">
    <div class="section-head">
      <h2>Wide View - Silicon Valley Footprint</h2>
      <span class="count-pill">__MAPPED_COUNT__ pins mapped</span>
    </div>
    <p class="desc">South Bay, the Peninsula, and into the East Bay - the team's full working territory. Zoom or pan to explore; a handful of sales further afield (referral business outside the core footprint) are also plotted and reachable by zooming out.</p>
    <div class="map-wrap"><div id="map-wide"></div></div>
    <div class="legend">
      <span><span class="dot team"></span>Boyenga Team</span>
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <h2>Regional View - Mountain View to Saratoga</h2>
      <span class="count-pill">__MAPPED_COUNT__ pins mapped</span>
    </div>
    <p class="desc">A mid-level regional view spanning Mountain View, Los Altos, and Sunnyvale in the northwest, across Santa Clara and San Jose, down to Cupertino, Campbell, and Saratoga in the south. The red pin marks 3444 Kenyon Drive (95051) for reference; it is not a Boyenga Team sale. Pan or zoom to see sales outside this window.</p>
    <div class="map-wrap"><div id="map-regional"></div></div>
    <div class="legend">
      <span><span class="dot team"></span>Boyenga Team</span>
      <span><span class="dot subject"></span>3444 Kenyon Drive (client property, reference only)</span>
    </div>
  </div>

</main>

<footer>
  <div class="brandline">__BRAND_LINE__</div>
  <div class="dre">Graeham Watts, REALTOR &middot; DRE #__DRE__</div>
  <div style="margin-top:10px; color:#8b93a8;">Source: MLSListings Matrix, Sold status. Searched by List Agent Lic # and Buyer's Agent Lic # for DRE 01466876 (Graeham Watts), DRE 01254724 (Janelle Boyenga), and DRE 01254725 (Eric Boyenga), plus a Listing Agent Last Name "Boyenga" catch-all, merged and de-duplicated by MLS #. Data compiled and geocoded for informational purposes; deemed reliable but not guaranteed.</div>
</footer>

<script>
__ALL_JS__

const SUBJECT_PROPERTY = {lat: __SUBJECT_LAT__, lon: __SUBJECT_LON__, addr: "3444 Kenyon Drive", city: "Santa Clara"};

function popupHtml(item) {
  return '<div class="popup-addr">' + item.addr + '</div>' +
         '<div class="popup-row">' + item.city + ', CA</div>' +
         '<div class="popup-row popup-price">' + item.price + '</div>' +
         '<div class="popup-row">Sold ' + item.date + '</div>';
}

function addMarkers(map, list) {
  const group = [];
  list.forEach(function(item) {
    const marker = L.circleMarker([item.lat, item.lon], {
      radius: 7,
      fillColor: '#b8912f',
      color: '#ffffff',
      weight: 1.5,
      fillOpacity: 0.9
    }).bindPopup(popupHtml(item));
    marker.addTo(map);
    group.push(marker);
  });
  return group;
}

// Wide map
const mapWide = L.map('map-wide', { scrollWheelZoom: false });
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(mapWide);
addMarkers(mapWide, ALL_LISTINGS);
const wideBounds = L.latLngBounds(ALL_LISTINGS.map(function(i) { return [i.lat, i.lon]; }));
mapWide.fitBounds(wideBounds, {padding: [20, 20]});
mapWide.on('focus', function() { mapWide.scrollWheelZoom.enable(); });
mapWide.on('blur', function() { mapWide.scrollWheelZoom.disable(); });

// Regional map (fixed mid-zoom extent: Mountain View/Los Altos/Sunnyvale NW to Cupertino/Campbell/Saratoga S)
const mapRegional = L.map('map-regional', { scrollWheelZoom: false });
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(mapRegional);
addMarkers(mapRegional, ALL_LISTINGS);
const subjectMarker = L.circleMarker([SUBJECT_PROPERTY.lat, SUBJECT_PROPERTY.lon], {
  radius: 9,
  fillColor: '#c0392b',
  color: '#ffffff',
  weight: 2,
  fillOpacity: 0.95
}).bindPopup('<div class="popup-addr">3444 Kenyon Drive</div><div class="popup-row">Santa Clara, CA 95051</div><div class="popup-row">Client property - reference only</div>');
subjectMarker.addTo(mapRegional);
const regionalBounds = L.latLngBounds([__REGIONAL_SW__, __REGIONAL_NE__]);
mapRegional.fitBounds(regionalBounds, {padding: [10, 10]});
mapRegional.on('focus', function() { mapRegional.scrollWheelZoom.enable(); });
mapRegional.on('blur', function() { mapRegional.scrollWheelZoom.disable(); });
</script>

</body>
</html>
"""

html = TEMPLATE
html = html.replace('__TOTAL_COUNT__', str(total_count))
html = html.replace('__MAPPED_COUNT__', str(mapped_count))
html = html.replace('__EARLIEST_DATE__', fmt_date(earliest))
html = html.replace('__LATEST_DATE__', fmt_date(latest))
html = html.replace('__BRAND_LINE__', BRAND_LINE)
html = html.replace('__DRE__', DRE)
html = html.replace('__ALL_JS__', all_js)
html = html.replace('__SUBJECT_LAT__', str(SUBJECT['lat']))
html = html.replace('__SUBJECT_LON__', str(SUBJECT['lon']))
html = html.replace('__REGIONAL_SW__', str(REGIONAL_SW))
html = html.replace('__REGIONAL_NE__', str(REGIONAL_NE))

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Wrote HTML to {OUT_PATH}")
print(f"File size: {len(html)} bytes")
