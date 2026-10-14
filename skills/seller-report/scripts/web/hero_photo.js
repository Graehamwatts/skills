// hero_photo.js: the listing's main photo, as a public https address, from a public page that is already open
// (seller-report, references/extras.md).
//
// Run it on the listing's own public page (the property page, or the portal page opened for online views), so it
// costs no extra page. It reads the page's own share image (og:image). When the page names none, it takes the
// first photo on the page that is at least 600 pixels wide. It returns only:
//
//   {"photo_url": "https://...", "width": 1600, "height": 1067, "page": "https://the page it was read from", "from": "share image"}
//
// or {"photo_url": null, "why": "..."} when the page has no usable photo. hero_photo.py set stores the address in
// listing.json. With no photo the report is built without one.

globalThis.srHeroPhoto = async function (env) {
  env = env || {};
  const doc = env.document || document;
  const page = String(env.href || location.href).split('#')[0].split('?')[0];
  const MIN = 600;
  const meta = n => { const m = doc.querySelector('meta[property="' + n + '"], meta[name="' + n + '"]'); return m ? m.getAttribute('content') : null; };
  const abs = u => { try { return new URL(u, page).href; } catch (e) { return null; } };
  const measure = env.measure || (url => new Promise(res => {
    const im = new Image();
    im.onload = () => res({ width: im.naturalWidth, height: im.naturalHeight });
    im.onerror = () => res(null);
    im.src = url;
  }));
  const share = meta('og:image:secure_url') || meta('og:image') || meta('twitter:image');
  let why = 'the page names no share image and shows no photo at least ' + MIN + ' pixels wide';
  if (share) {
    const url = abs(share);
    if (!url) why = 'the share image address is not valid';
    else if (url.slice(0, 8) !== 'https://') why = 'the share image is not at an https address';
    else {
      const size = await measure(url);
      if (size && size.width >= MIN) return JSON.stringify({ photo_url: url, width: size.width, height: size.height, page: page, from: 'share image' });
      why = size ? 'the share image is only ' + size.width + ' pixels wide' : 'the share image did not load';
    }
  }
  const imgs = Array.prototype.slice.call(doc.querySelectorAll ? doc.querySelectorAll('img') : []);
  for (const im of imgs.slice(0, 60)) {
    const url = abs(im.currentSrc || im.src || (im.getAttribute && im.getAttribute('src')) || '');
    if (!url || url.slice(0, 8) !== 'https://' || /\.svg(\?|$)/i.test(url)) continue;
    if ((im.naturalWidth || 0) >= MIN && im.naturalHeight >= 300) {
      return JSON.stringify({ photo_url: url, width: im.naturalWidth, height: im.naturalHeight, page: page, from: 'first large photo on the page' });
    }
  }
  return JSON.stringify({ photo_url: null, why: why });
};
