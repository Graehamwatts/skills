// matrix_grid.js: one MLSListings Matrix results grid, read as compact rows (seller-report, references/extras.md).
//
// Run it in the in-app browser on a Matrix search results page, after Graeham has signed in to MLSListings
// himself (Claude never types a password or a code). It reads the grid that is on the screen and nothing else:
// no click, no typing, no request, no other page. It returns one JSON string:
//
//   {"ok": true, "site": "mlslistings", "grid": "matrix", "as_of": "2026-10-13", "display": "<the display name>",
//    "columns": ["status", "mls", "address", ...], "rows": [["Active", "ML80000001", "14 Sample Fern Ln", ...], ...],
//    "partial": null | {"shown": 50, "total": 73}, "skipped_columns": [...], "odd_rows": 0}
//
// Each row holds the cell text exactly as the grid prints it, in the order of "columns". Only these columns are
// read, from whatever of them the current display has: status, mls (MLS number), address, city, type (property
// sub type), list_price, previous_price, sale_price, close_date, dom, beds, baths, sqft, change_date,
// change_type, members_only (the M.O. column). Nothing is worked out here: scripts/nearby_from_mls.py reads the
// values, refuses any row it cannot read, leaves out members-only listings and the listing itself, and merges
// the two displays (the closed date template, then the Agent 1 Line Hotsheet) by MLS number.
//
// When the page shows no grid it says why: {"ok": false, "reason": "signed_out"} when it reads like a sign-in
// page (Graeham signs in; nobody works around it), {"ok": false, "reason": "no_grid"} otherwise.

globalThis.srMatrixGrid = function (env) {
  env = env || {};
  const doc = env.document || document;
  const TZ = env.tz || 'America/Los_Angeles';
  const NBSP = String.fromCharCode(160);
  const asOf = new Date(env.now || Date.now()).toLocaleDateString('en-CA', { timeZone: TZ });
  const key = s => String(s || '').toLowerCase().replace(/[^a-z0-9#]+/g, '');
  // the header words each column is known by in Matrix displays, after key()
  const FIELDS = [
    ['status', ['status', 'st', 'stat', 'liststatus']],
    ['mls', ['mls#', 'mls', 'mlsnumber', 'mlsno', 'ml#', 'mlnumber', 'listing#', 'listingid', 'listingnumber']],
    ['address', ['address', 'streetaddress', 'addr', 'fulladdress', 'propertyaddress']],
    ['city', ['city']],
    ['type', ['subtype', 'propertysubtype', 'propsubtype', 'propertytype', 'type']],
    ['list_price', ['price', 'listprice', 'lp', 'currentprice', 'askingprice', 'lprice', 'curprice']],
    ['previous_price', ['oldprice', 'previousprice', 'prevprice', 'priorprice']],
    ['sale_price', ['saleprice', 'soldprice', 'sp', 'closeprice', 'closedprice', 'sprice']],
    ['close_date', ['closedate', 'coe', 'coedate', 'closeddate', 'closingdate', 'solddate', 'closedt']],
    ['dom', ['dom', 'daysonmarket']],
    ['beds', ['beds', 'br', 'bd', 'bedrooms', 'bdrms', 'bed', 'bds']],
    ['baths', ['baths', 'ba', 'bth', 'bathrooms', 'bath', 'bths', 'bathsfh', 'fbhb']],
    ['sqft', ['sqft', 'sf', 'squarefeet', 'approxsqft', 'sqftapx', 'livingarea', 'bldgsqft', 'sqfeet', 'sqftsource']],
    ['change_date', ['changedate', 'chgdate', 'statuschangedate', 'statusdate', 'changedt']],
    ['change_type', ['changetype', 'chgtype', 'change']],
    ['members_only', ['mo', 'membersonly', 'memberonly']]
  ];
  const fieldOf = label => { const k = key(label); const hit = FIELDS.find(f => f[1].indexOf(k) >= 0); return hit ? hit[0] : null; };
  const text = el => {
    let t = String((el.innerText !== undefined && el.innerText !== null ? el.innerText : el.textContent) || '').split(NBSP).join(' ').replace(/\s+/g, ' ').trim();
    if (!t && el.querySelector) {                                   // a flag drawn as an icon: its title, alt or label
      const icon = el.querySelector('[title],[alt],[aria-label]');
      if (icon) t = String(icon.getAttribute('title') || icon.getAttribute('alt') || icon.getAttribute('aria-label') || '').trim();
      if (!t) {                                                     // an icon with no words (a class, an svg, a ticked box):
        const mark = el.querySelector('img,svg,i,input[type=checkbox]:checked,span[class]');   // never read as "no"
        if (mark) t = '[icon ' + String((typeof mark.className === 'string' && mark.className) || mark.tagName || 'unnamed').slice(0, 30) + ']';
      }
    }
    return t;
  };
  const span = c => Math.max(1, parseInt(c.colSpan || (c.getAttribute && c.getAttribute('colspan')) || 1, 10) || 1);
  const slots = row => {                                            // each cell at the column it starts in
    const out = []; let at = 0;
    for (const c of Array.from(row.cells || [])) { out.push({ at: at, cell: c }); at += span(c); }
    return { cells: out, width: at };
  };

  let best = null;
  for (const t of Array.from(doc.querySelectorAll('table'))) {
    const rows = Array.from(t.rows || []);
    for (let i = 0; i < Math.min(rows.length, 6); i++) {
      const s = slots(rows[i]);
      const map = s.cells.map(x => ({ at: x.at, label: text(x.cell), field: fieldOf(text(x.cell)) }));
      const got = new Set(map.filter(x => x.field).map(x => x.field));
      if (got.has('mls') && got.has('address') && got.has('status')) {
        if (!best || got.size > best.got.size) best = { rows: rows, head: i, map: map, got: got, width: s.width };
        break;
      }
    }
  }
  if (!best) {
    const words = String((doc.body && (doc.body.innerText || doc.body.textContent)) || '').slice(0, 4000);
    const signIn = /sign in|log ?in|password|single sign|session (has )?expired/i.test(words);
    return JSON.stringify({ ok: false, site: 'mlslistings', reason: signIn ? 'signed_out' : 'no_grid', as_of: asOf });
  }

  const columns = [], at = {}, skipped = [], twice = [];
  for (const f of FIELDS.map(x => x[0])) {
    const hits = best.map.filter(x => x.field === f);
    if (!hits.length) continue;
    columns.push(f); at[f] = hits[0].at;
    if (hits.length > 1) twice.push(f);
  }
  for (const x of best.map) if (!x.field && x.label) skipped.push(x.label.slice(0, 30));
  const rows = []; let odd = 0;
  for (const r of best.rows.slice(best.head + 1)) {
    const s = slots(r);
    if (!s.cells.length) continue;
    const byAt = {};
    for (const x of s.cells) byAt[x.at] = text(x.cell);
    if (s.width !== best.width) { if (s.cells.some(x => text(x.cell))) odd++; continue; }
    const vals = columns.map(f => byAt[at[f]] === undefined ? '' : byAt[at[f]]);
    if (!vals[columns.indexOf('mls')]) { if (vals.some(v => v)) odd++; continue; }
    rows.push(vals);
  }
  let partial = null;
  const page = String((doc.body && (doc.body.innerText || doc.body.textContent)) || '');
  const m = /\b(\d{1,5})\s*-\s*(\d{1,5})\s+of\s+(\d{1,6})\b/.exec(page);
  if (m && (+m[2] - +m[1] + 1) < +m[3]) partial = { shown: +m[2] - +m[1] + 1, total: +m[3] };
  let display = null;
  const pick = doc.querySelector && doc.querySelector('select[id*="Display" i], select[name*="Display" i]');
  if (pick && pick.options && pick.selectedIndex >= 0 && pick.options[pick.selectedIndex]) display = text(pick.options[pick.selectedIndex]).slice(0, 60);
  return JSON.stringify({ ok: true, site: 'mlslistings', grid: 'matrix', as_of: asOf, display: display, columns: columns, rows: rows,
                          partial: partial, skipped_columns: skipped.slice(0, 40), duplicate_columns: twice, odd_rows: odd });
};
