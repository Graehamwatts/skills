// portal_views.js: online views and saves for one listing, read from its public page on a portal
// (seller-report, references/extras.md).
//
// Open the listing's own public page on Zillow, Redfin or another portal in the in-app browser, then run this.
// Public pages only, read-only, no sign-in, nothing typed into the page. At most ONE page per portal per issue
// (online_views.py plan enforces it). It returns exactly this, as JSON, and nothing else from the page:
//
//   {"portal": "Zillow", "views": 812, "saves": 31, "as_of": "2026-04-13"}
//
// views and saves are the running counts the site shows since the home was listed. A count the page does not
// show is null. If the page is a block page or a human check, it returns {"portal": ..., "blocked": true} or
// {"portal": ..., "captcha": true} and the report is built without that portal. Never work around a block:
// record it with online_views.py skip (or hand this result to online_views.py add --result, which does it).

globalThis.srPortalViews = function (env) {
  env = env || {};
  const host = String(env.host || location.hostname).toLowerCase();
  const text = String(env.text !== undefined ? env.text : (document.body ? document.body.innerText : '')).split(String.fromCharCode(160)).join(' ');
  const title = String(env.title !== undefined ? env.title : document.title);
  const TZ = env.tz || 'America/Los_Angeles';
  const names = [['zillow', 'Zillow'], ['redfin', 'Redfin'], ['realtor', 'Realtor.com'], ['homes.com', 'Homes.com'], ['trulia', 'Trulia'], ['compass', 'Compass']];
  const hit = names.find(n => host.indexOf(n[0]) >= 0);
  const out = { portal: hit ? hit[1] : host.replace(/^www\./, ''), views: null, saves: null,
                as_of: new Date(env.now || Date.now()).toLocaleDateString('en-CA', { timeZone: TZ }) };
  const head = (title + ' ' + text.slice(0, 3000)).toLowerCase();
  if (/press (&|and) hold|verify you are (a )?human|are you a (human|robot)|captcha|unusual (traffic|activity)/.test(head)) return JSON.stringify({ portal: out.portal, captcha: true });
  if (/access (to this page has been )?denied|request (was )?blocked|403 forbidden|error 403/.test(head)) return JSON.stringify({ portal: out.portal, blocked: true });
  const num = s => parseInt(String(s).replace(/,/g, ''), 10);
  // Number first ("1,234 views", "31 saves") or label first ("Views: 1,234", "Favorites 12"). The way the page
  // writes its views decides how its saves are read, so "Views: 240 Favorites 12" is never read as 240 saves.
  const D = '(\\d[\\d,]*)';
  const first = words => new RegExp(D + '\\s*(?:total\\s+)?(?:' + words + ')\\b', 'i').exec(text);
  const after = words => new RegExp('\\b(?:' + words + ')\\s*[:\\-]?\\s*' + D + '\\b', 'i').exec(text);
  const SAVES = 'saves?|favorites?|saved';
  const a = first('views?'), b = after('views?');
  const numberFirst = a && (!b || a.index <= b.index);
  const v = numberFirst ? a : b, sv = numberFirst ? first(SAVES) : (b ? after(SAVES) : (first(SAVES) || after(SAVES)));
  out.views = v ? num(v[1]) : null;
  out.saves = sv ? num(sv[1]) : null;
  return JSON.stringify(out);
};
