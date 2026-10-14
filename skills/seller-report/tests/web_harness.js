// web_harness.js: runs the browser snippets of scripts/web under Node with a pretend site, for test_web_snippets.py.
// Synthetic data only: the "site" below is invented. Usage: node web_harness.js <scripts/web folder>
// Prints one JSON object: {portal: [...], hero: [...], nearby: {...}}.
const fs = require('fs'), path = require('path');
const dir = process.argv[2];
for (const f of ['portal_views.js', 'hero_photo.js', 'nearby_lookup.js', 'matrix_grid.js']) (0, eval)(fs.readFileSync(path.join(dir, f), 'utf8'));

// a pretend Matrix results page: tables of rows of cells, the way the browser hands them to a page script
const cellOf = (t, o) => { o = o || {}; return { innerText: t, textContent: t, colSpan: o.span || 1, getAttribute: () => null,
                                                 querySelector: s => (s.indexOf('[title]') >= 0 ? o.icon : (o.mark || o.icon)) || null }; };
const rowOf = cells => ({ cells: cells.map(c => (c && typeof c === 'object') ? c : cellOf(c)) });
const tableOf = rows => ({ rows: rows.map(rowOf) });
const MO = cellOf('', { icon: { getAttribute: k => (k === 'title' ? 'Members Only' : null) } });          // the flag drawn as an icon
const MARK = cellOf('', { mark: { className: 'mo-flag', tagName: 'I' } });                               // a flag drawn with a class only
const ICONS = tableOf([
  ['MLS #', 'Status', 'Address', 'Price', 'Change Date', 'Change Type', 'M.O.'],
  ['ML80000201', 'Active', '3 Sample Iris Ln', '$1,150,000', '4/8/2026 2:15 PM', 'New Listing', MARK],
  ['ML80000202', 'Active', '5 Sample Iris Ln', '$1,160,000', '4/8/2026', 'New Listing', '']
]);
const pageOf = (tables, body, display) => ({
  querySelectorAll: s => (s === 'table' ? tables : []),
  querySelector: s => (display && /select/.test(s) ? { options: [{ innerText: display }], selectedIndex: 0 } : null),
  body: { innerText: body || '' }
});
const LAYOUT = tableOf([['Search results', 'Map'], ['', '']]);                                         // a layout table with no grid in it
const CLOSED = tableOf([
  [cellOf('', { span: 2 }), 'MLS #', 'St', 'Address', 'City', 'Price', 'Sale Price', 'Close Date', 'DOM', 'Beds', 'Baths', 'Sq Ft', 'M.O.', 'Photo'],
  ['', '', 'ML80000101', 'Active', '14 Sample Fern Ln', 'Fixture City', '$1,210,000', '', '', '3', '3', '2|1', '1,510', '', 'View'],
  ['', '', 'ML80000102', 'Contingent', '9 Sample Cedar Ct', 'Fixture City', '$1,249,000', '', '', '15', '3', '2', '1,620', '', ''],
  ['', '', 'ML80000103', 'Sold', '52 SAMPLE BIRCH DR', 'Fixture City', '$1,182,000', '$1,190,000', '4/7/2026', '28', '3', '2', '1,390', '', ''],
  ['', '', 'ML80000104', 'Sold', '7 Sample Hidden Way', 'Fixture City', '$999,000', '$1,005,000', '3/30/2026', '12', '3', '2', '1,450', MO, ''],
  ['', '', 'ML80000100', 'Active', '218 Sample Glen Ct', 'Fixture City', '$1,195,000', '', '', '6', '3', '2', '1,480', '', ''],
  ['Totals for 5 listings', '', '', '']                                                           // a summary row of another width
]);
const HOT = tableOf([
  ['MLS #', 'Status', 'Address', 'Price', 'Change Date', 'Change Type', 'M.O.'],
  ['ML80000101', 'Active', '14 Sample Fern Ln', '$1,210,000', '4/10/2026', 'New Listing', ''],
  ['ML80000102', 'Contingent', '9 Sample Cedar Ct', '$1,249,000', '4/9/2026', 'Active > Contingent', ''],
  ['ML80000103', 'Sold', '52 SAMPLE BIRCH DR', '$1,190,000', '4/7/2026', 'Contingent > Sold', ''],
  ['ML80000104', 'Sold', '7 Sample Hidden Way', '$1,005,000', '3/30/2026', 'Pending > Sold', 'Y'],
  ['ML80000100', 'Active', '218 Sample Glen Ct', '$1,195,000', '4/7/2026', 'New Listing', '']
]);

const at = (y, mo, d, h) => Date.UTC(y, mo - 1, d, h || 20);          // 20:00 UTC is 1 pm Pacific: the same calendar day
const V = v => ({ value: v, level: 1 });
const home = (id, street, unit, city, beds, sqft, price, extra) => Object.assign(
  { propertyId: id, streetLine: V(street), unitNumber: unit ? V(unit) : undefined, city: city, beds: beds, baths: 2, sqFt: V(sqft), price: V(price) }, extra || {});

// what the pretend search hands back: the property type filter is not to be trusted, so it includes a mobile home
// and a home in another city, exactly as the real one has done
const LIVE = [
  home(9000, '218 Sample Glen Ct', null, 'Fixture City', 3, 1480, 1195000, { mlsStatus: 'Active' }),          // the subject
  home(9001, '14 Sample Fern Ln', null, 'Fixture City', 3, 1510, 1210000, { mlsStatus: 'Active' }),
  home(9003, '9 Sample Cedar Ct', null, 'Fixture City', 3, 1620, 1249000, { mlsStatus: 'Pending' }),
  home(9010, '77 Sample Trailer Park', 'Unit 4', 'Fixture City', 3, 1500, 300000, { mlsStatus: 'Active' }),     // wrong type
  home(9011, '5 Sample Oak St', null, 'Other Town', 3, 1490, 1100000, { mlsStatus: 'Active' }),                // wrong city
  home(9012, '8 Sample Big Rd', null, 'Fixture City', 3, 2600, 1900000, { mlsStatus: 'Active' }),              // too large
  home(9013, '3 Sample Small Rd', null, 'Fixture City', 2, 1450, 990000, { mlsStatus: 'Active' })              // other bed count
];
const SOLD = [home(9004, '52 Sample Birch Dr', null, 'Fixture City', 3, 1390, 1182000, { soldDate: at(2026, 4, 7) })];
const E = (t, d, p) => ({ eventDate: t, eventDescription: d, price: p || null, source: 'MLS' });
const HISTORY = {
  9001: [E(at(2026, 4, 10), 'Listed (Active)', 1210000)],
  // listed in the evening Pacific time: 04:30 UTC on Mar 29 is 9:30 pm on Mar 28 in California. A second copy of the
  // same listing event arrives 10 hours later. Pending on Apr 9, then a later Pending copy that must not win.
  9003: [E(Date.UTC(2026, 2, 29, 4, 30), 'Listed (Active)', 1249000), E(Date.UTC(2026, 2, 29, 14, 30), 'Listed (Active)', 1249000),
         E(at(2026, 4, 9), 'Pending (Pending Sale)'), E(at(2026, 4, 11), 'Pending (Pending Sale)')],
  9004: [E(at(2026, 3, 10), 'Listed (Active)', 1175000), E(at(2026, 3, 19), 'Contingent (Active Under Contract)'),
         E(at(2026, 4, 7), 'Sold (MLS) (Closed)', 1182000)],
  9010: [E(at(2026, 4, 1), 'Listed (Active)', 300000)],
  9020: [E(at(2026, 1, 5), 'Listed (Active)', 1300000), E(at(2026, 2, 1), 'Price Changed', 1250000), E(at(2026, 3, 20), 'Listing Removed')]
};
const TYPE = { 9010: 'Mobile/Manufactured Home' };

function site(opts) {
  const calls = [];
  const fetch = async (url) => {
    calls.push(url);
    const reply = (status, text) => ({ status: status, text: async () => text });
    if (opts.block) return reply(403, '<!DOCTYPE HTML><html><body>Request blocked.</body></html>');
    if (opts.captcha) return reply(200, '<html><body>Press &amp; Hold to confirm you are a human</body></html>');
    if (url.indexOf('/stingray/api/gis') === 0) {
      if (url.indexOf('mpt=99') < 0) return reply(200, '{}&&' + JSON.stringify({ payload: { homes: [] } }));       // without mpt=99 the filters are ignored
      return reply(200, '{}&&' + JSON.stringify({ payload: { homes: url.indexOf('status=9&') >= 0 || /status=9$/.test(url) ? SOLD : LIVE } }));
    }
    const id = +(/propertyId=(\d+)/.exec(url) || [])[1];
    if (url.indexOf('belowTheFold') >= 0) {
      const body = { payload: { propertyHistoryInfo: { events: HISTORY[id] || [] } } };
      if (opts.typeBelow) body.payload.publicRecordsInfo = { basicInfo: { propertyTypeName: TYPE[id] || 'Single Family Residential' } };
      return reply(200, '{}&&' + JSON.stringify(body));
    }
    if (url.indexOf('aboveTheFold') >= 0) return reply(200, '{}&&' + JSON.stringify({ payload: { x: { propertyTypeName: TYPE[id] || 'Single Family Residential' } } }));
    return reply(404, 'not found');
  };
  return { fetch: fetch, calls: calls };
}

(async () => {
  const subject = { address: '218 Sample Glen Ct', city: 'Fixture City', state: 'CA', zip: '94000', beds: 3, baths: 2, sqft: 1480 };
  const base = { family: 'house', subject: subject, search: { region_id: 99001, region_type: 6 }, max: 12, sold_days: 120 };
  const now = at(2026, 4, 13);
  const out = { portal: [], hero: [], nearby: {} };

  let s = site({});
  out.nearby.candidates = await globalThis.srNearby(Object.assign({ mode: 'candidates' }, base), { fetch: s.fetch, now: now });
  out.nearby.candidates_calls = s.calls;
  s = site({ typeBelow: true });
  out.nearby.watch = await globalThis.srNearby(Object.assign({ mode: 'watch', watch: [{ id: '9003' }, { id: 9004 }, { id: 9020, address: '60 Sample Gone Way' }] }, base), { fetch: s.fetch, now: now });
  out.nearby.watch_calls = s.calls.length;
  s = site({});                    // a watch list of MLS numbers sent to the public site: nothing is known about any of them
  out.nearby.watch_mls_ids = await globalThis.srNearby(Object.assign({ mode: 'watch', watch: [{ id: 'ML80000103', address: '52 Sample Birch Dr' }] }, base), { fetch: s.fetch, now: now });
  s = site({ block: true });
  out.nearby.blocked = await globalThis.srNearby(Object.assign({ mode: 'watch', watch: [{ id: 9003 }] }, base), { fetch: s.fetch, now: now });
  out.nearby.blocked_calls = s.calls.length;
  s = site({ captcha: true });
  out.nearby.captcha = await globalThis.srNearby(Object.assign({ mode: 'candidates' }, base), { fetch: s.fetch, now: now });
  s = site({});
  out.nearby.no_region = await globalThis.srNearby({ mode: 'candidates', family: 'house', subject: subject, search: {} }, { fetch: s.fetch, now: now });
  out.nearby.no_region_calls = s.calls.length;

  const pv = o => JSON.parse(globalThis.srPortalViews(Object.assign({ title: 'A home', now: Date.UTC(2026, 3, 14, 3, 0) }, o)));
  out.portal.push(pv({ host: 'www.zillow.com', text: '32 days on Zillow | 1,812 views | 31 saves' }));
  out.portal.push(pv({ host: 'www.redfin.com', text: 'Activity Views: 240 Favorites 12 X-outs 3' }));
  out.portal.push(pv({ host: 'www.zillow.com', title: 'Access to this page has been denied', text: 'Press & Hold to confirm you are a human' }));
  out.portal.push(pv({ host: 'www.realtor.com', text: 'A lovely home with mountain views and a garden.' }));
  out.portal.push(pv({ host: 'www.example-portal.com', title: '403 Forbidden', text: 'Request blocked' }));

  const doc = metas => ({ querySelector: sel => { const k = Object.keys(metas).find(n => sel.indexOf('"' + n + '"') >= 0); return k ? { getAttribute: () => metas[k] } : null; } });
  const hp = async (metas, size) => JSON.parse(await globalThis.srHeroPhoto({ document: doc(metas), href: 'https://example.test/homes/218-sample-glen?utm=x#top', measure: async () => size }));
  out.hero.push(await hp({ 'og:image': 'https://photos.example.test/218/front.jpg' }, { width: 1600, height: 1067 }));
  out.hero.push(await hp({ 'og:image': 'http://photos.example.test/218/front.jpg' }, { width: 1600, height: 1067 }));
  out.hero.push(await hp({}, null));
  out.hero.push(await hp({ 'twitter:image': '/img/front.jpg' }, null));
  // a page with no share image: the first photo at least 600 pixels wide is taken, never a logo or an icon
  const imgs = [{ src: 'https://example.test/logo.svg', naturalWidth: 900, naturalHeight: 300 }, { src: 'https://example.test/agent.jpg', naturalWidth: 240, naturalHeight: 240 },
                { currentSrc: 'https://media.example.test/218/living.jpg', naturalWidth: 2400, naturalHeight: 1600 }, { src: 'https://media.example.test/218/kitchen.jpg', naturalWidth: 2400, naturalHeight: 1600 }];
  out.hero.push(JSON.parse(await globalThis.srHeroPhoto({ document: { querySelector: () => null, querySelectorAll: () => imgs }, href: 'https://example.test/homes/218-sample-glen' })));

  const mg = (tables, body, display) => JSON.parse(globalThis.srMatrixGrid({ document: pageOf(tables, body, display), now: Date.UTC(2026, 3, 14, 3, 0) }));
  out.matrix = {
    closed: mg([LAYOUT, CLOSED], 'Residential results 1 - 5 of 5', 'my:Closed date template'),
    hotsheet: mg([LAYOUT, HOT], 'Residential results 1 - 5 of 5', 'Agent 1 Line Hotsheet'),
    partial: mg([HOT], 'Residential results 1 - 50 of 73', null),
    signed_out: mg([], 'Sign in to continue. Username Password', null),
    no_grid: mg([LAYOUT], 'Nothing here', null),
    icons: mg([ICONS], 'Residential results 1 - 2 of 2', 'Agent 1 Line Hotsheet')
  };
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
