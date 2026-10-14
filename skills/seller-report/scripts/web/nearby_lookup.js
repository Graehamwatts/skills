// nearby_lookup.js: ONE lookup for "Similar homes nearby" (seller-report, references/extras.md).
//
// Run it in the in-app browser on a public redfin.com page (the site's listing data only answers from its own
// origin). Public pages only, read-only, no sign-in. It returns compact JSON and nothing else:
//
//   mode "candidates"  first use for a listing: up to `max` comparable homes (same type, similar beds and size,
//                      same city) with where each stands, to choose the watch list from
//   mode "watch"       every later issue: where each watched home stands now
//
// Each home: id, address, city, type, beds, baths, sqft, status (active | pending | sold | withdrawn),
// list_price, list_date, pending_date, sold_date, sold_price, off_date, price_change {date, from, to}.
// The differences against the last issue are worked out in Python (nearby_update.py), not here.
//
// Rules this encodes, each from a real error (seller-marketing-report/references/data-sources.md):
//   - every event time is turned into a Pacific date first: a UTC date is a day off for an evening MLS event
//   - the list date is the earliest copy of the LATEST "Listed" event; the contract date is the FIRST
//     Pending or Contingent event after it
//   - the site's property type filter is not reliable, so every home's own type and city are read and checked
//   - responses start with {}&& and that prefix is removed before parsing
//
// If the site answers 403 or 429, or with a human check, the lookup STOPS and says so
// ({"ok":false,"blocked":true} or {"ok":false,"captcha":true}). Nothing is retried and nothing else is tried.
// Do not add retries. Record the skip with nearby_update.py skip and build the report without the section.
//
// nearby_update.py plan writes the call for one listing (this file plus one line of arguments).

globalThis.srNearby = async function (A, env) {
  env = env || {};
  const doFetch = env.fetch || fetch;
  const now = env.now || Date.now();
  const TZ = A.tz || 'America/Los_Angeles';
  const MAX = Math.min(A.max || 12, 12);
  const CAP = 3 + 2 * Math.max(MAX, (A.watch || []).length);       // requests this one lookup may make
  const ymd = ms => new Date(ms).toLocaleDateString('en-CA', { timeZone: TZ });
  const val = x => (x && typeof x === 'object' && 'value' in x) ? x.value : (x === undefined ? null : x);
  const norm = s => String(s || '').toLowerCase().replace(/\b(unit|apt|ste|suite)\b|#/g, ' ').replace(/[^a-z0-9]+/g, ' ').trim();
  const stop = o => { const e = new Error('stop'); e.out = o; return e; };
  let requests = 0;

  const get = async path => {
    if (++requests > CAP) throw stop({ ok: false, reason: 'failed', detail: 'request cap reached' });
    let r, t;
    try { r = await doFetch(path, { credentials: 'include' }); t = await r.text(); }
    catch (e) { throw stop({ ok: false, reason: 'failed', detail: 'no answer from the site' }); }
    if (r.status === 403 || r.status === 429) throw stop({ ok: false, blocked: true, status: r.status });
    const json = t.slice(0, 4) === '{}&&';
    if (!json && /captcha|are you a human|press (&amp;|&|and) hold|unusual traffic|verify you are/i.test(t.slice(0, 6000))) throw stop({ ok: false, captcha: true, status: r.status });
    if (r.status !== 200 || !json) throw stop({ ok: false, reason: 'failed', status: r.status, detail: 'not the expected answer' });
    return t.slice(4);
  };

  const S = A.search || {};
  let regionId = S.region_id, regionType = S.region_type || 6;
  if (!regionId && typeof location !== 'undefined') {                 // on a city page the address bar carries the region
    const m = /\/city\/(\d+)\//.exec(location.pathname || '');
    if (m) regionId = +m[1];
  }
  const uipt = S.uipt || ({ condo: '2', townhouse: '3', house: '1' })[A.family] || '1,2,3';
  const TYPE = ({ condo: /condo|co-op/i, townhouse: /townho/i, house: /single family/i })[A.family] || /./;

  const gis = async extra => {
    const u = '/stingray/api/gis?al=1&num_homes=350&region_id=' + regionId + '&region_type=' + regionType + '&uipt=' + uipt +
      '&v=8&mpt=99&sf=1,2,3,5,6,7' + (S.market ? '&market=' + encodeURIComponent(S.market) : '') + extra;      // mpt=99 or the filters are ignored
    const j = JSON.parse(await get(u));
    return ((j.payload && j.payload.homes) || []).map(h => ({
      id: h.propertyId,
      address: ((val(h.streetLine) || '') + ' ' + String(val(h.unitNumber) || '').replace(/^(unit|apt|ste|suite)\.?\s*/i, '#')).replace(/\s+/g, ' ').trim(),
      street: norm(val(h.streetLine)), city: h.city || null, beds: val(h.beds), baths: val(h.baths), sqft: val(h.sqFt),
      price: val(h.price), sold: h.soldDate ? ymd(val(h.soldDate)) : null, mls: String(val(h.mlsStatus) || '')
    }));
  };

  const detail = async h => {
    const q = '?propertyId=' + h.id + '&accessLevel=1&pageType=3';
    const bt = await get('/stingray/api/home/details/belowTheFold' + q);
    let tm = /"propertyTypeName":"([^"]*)"/.exec(bt);
    if (!tm) tm = /"propertyTypeName":"([^"]*)"/.exec(await get('/stingray/api/home/details/aboveTheFold' + q));
    let ev = [];
    try { ev = JSON.parse(bt).payload.propertyHistoryInfo.events || []; } catch (e) { }
    ev = ev.filter(e => e && e.eventDate).map(e => ({ t: e.eventDate, d: String(e.eventDescription || ''), p: e.price || null })).sort((a, b) => a.t - b.t);
    const out = { id: h.id, address: h.address, city: h.city, type: tm ? tm[1] : null, beds: h.beds, baths: h.baths, sqft: h.sqft };
    const listed = ev.filter(e => /^(Listed|Relisted)/i.test(e.d));
    const lastL = listed[listed.length - 1];
    const tl = lastL ? Math.min(...listed.filter(e => lastL.t - e.t < 36 * 3600 * 1000).map(e => e.t)) : null;
    const after = tl === null ? [] : ev.filter(e => e.t > tl - 60000);
    const sold = after.filter(e => /^Sold/i.test(e.d)).pop();
    const pend = after.filter(e => /Pending|Contingent/i.test(e.d))[0];
    const off = after.filter(e => /Delisted|Listing Removed|Withdrawn|Expired|Cancel/i.test(e.d)).pop();
    const cut = after.filter(e => /^Price Changed/i.test(e.d) && e.p).pop();
    if (tl !== null) out.list_date = ymd(tl);
    if (pend) out.pending_date = ymd(pend.t);
    if (sold) { out.sold_date = ymd(sold.t); if (sold.p) out.sold_price = sold.p; }
    if (off && !sold) out.off_date = ymd(off.t);
    if (cut) {
      const before = ev.filter(e => e.t < cut.t && e.p).pop();
      out.price_change = { date: ymd(cut.t), from: before ? before.p : null, to: cut.p };
    }
    const lp = after.filter(e => e.p && !/^Sold/i.test(e.d)).pop();
    out.list_price = h.live && h.price ? h.price : (lp ? lp.p : null);
    const held = /pending|contingent|under contract/i.test(h.mls);
    if (h.live) out.status = held || (pend && !/active/i.test(h.mls)) ? 'pending' : 'active';
    else if (sold || h.sold) { out.status = 'sold'; if (!out.sold_date && h.sold) out.sold_date = h.sold; if (!out.sold_price && h.price) out.sold_price = h.price; }
    else if (!(h.unseen && !ev.length)) out.status = 'withdrawn';
    // a watched home found in neither search and with no history at all comes back with no status: nothing is
    // known about it (its id may be another site's number), so it is listed as missing, never as taken off the market
    return out;
  };

  const batch = async list => {
    const res = [];
    for (let i = 0; i < list.length; i += 4) res.push(...await Promise.all(list.slice(i, i + 4).map(detail)));
    return res;
  };

  try {
    if (!regionId) throw stop({ ok: false, reason: 'failed', detail: 'no region id: put it in listing.json extras.nearby.search, or run this on the site\'s page for the city' });
    const live = (await gis('&status=131')).map(h => Object.assign(h, { live: true }));          // active, contingent and pending
    const sold = await gis('&status=9&sold_within_days=' + (A.sold_days || 120));
    const all = live.concat(sold.filter(h => !live.some(x => x.id === h.id)));
    const sub = A.subject || {};
    const me = all.find(h => norm(h.address) === norm(sub.address));
    const out = { ok: true, site: 'redfin', mode: A.mode, as_of: ymd(now), search: { region_id: regionId, region_type: regionType, market: S.market || null, uipt: uipt },
                  subject: me ? { id: me.id, found: true } : { found: false } };
    let picked, dropped = {};
    if (A.mode === 'watch') {
      const want = (A.watch || []).map(w => (typeof w === 'object' ? w : { id: w }));
      picked = want.map(w => all.find(h => String(h.id) === String(w.id)) || { id: w.id, address: w.address || null, city: null, beds: null, baths: null, sqft: null, price: null, mls: '', live: false, unseen: true });
    } else {
      const tol = A.size_tol === undefined ? 0.25 : A.size_tol, bt = A.beds_tol || 0;
      const drop = k => { dropped[k] = (dropped[k] || 0) + 1; return false; };
      const pool = all.filter(h => {
        if (me && h.id === me.id || norm(h.address) === norm(sub.address)) return false;
        if (sub.city && norm(h.city) !== norm(sub.city)) return drop('city');
        if (sub.beds != null && h.beds != null && Math.abs(h.beds - sub.beds) > bt) return drop('beds');
        if (sub.sqft && h.sqft && Math.abs(h.sqft - sub.sqft) / sub.sqft > tol) return drop('size');
        return true;
      });
      const street = norm(String(sub.address || '').replace(/(#|\b(unit|apt|ste|suite)\b).*$/i, ''));
      const score = h => (h.street === street ? 0 : 2) + (h.live ? 0 : 1) + (sub.sqft && h.sqft ? Math.abs(h.sqft - sub.sqft) / sub.sqft : 0.5);
      picked = pool.sort((a, b) => score(a) - score(b)).slice(0, MAX);
    }
    let homes = await batch(picked);
    if (A.mode !== 'watch') {                                           // each home's own type decides, never the filter
      const n = homes.length;
      homes = homes.filter(h => h.type && TYPE.test(h.type));
      if (n - homes.length) dropped.type = n - homes.length;
      out.dropped = dropped;
    }
    out.homes = homes.map(h => { const o = {}; for (const k in h) if (h[k] !== null && h[k] !== undefined) o[k] = h[k]; return o; });
    out.requests = requests;
    return out;
  } catch (e) {
    if (e.out) return Object.assign(e.out, { requests: requests });
    return { ok: false, reason: 'failed', detail: String(e && e.message || e).slice(0, 120), requests: requests };
  }
};
