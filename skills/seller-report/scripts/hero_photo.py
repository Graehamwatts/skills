# -*- coding: utf-8 -*-
r"""hero_photo: the masthead photo of a listing's report, as a stable public https address.

    python hero_photo.py set   --folder "<listing folder>" --result "<what hero_photo.js returned>.json"
    python hero_photo.py set   --folder "<listing folder>" --url https://... --page https://...
    python hero_photo.py clear --folder "<listing folder>"
    python hero_photo.py show  --folder "<listing folder>"

Optional. A mail client can only show a photo it can fetch, so the address must be public and https. Find it
cheaply: run scripts\web\hero_photo.js on a public page of the listing that is already open (its own property
page, or the portal page opened for online views). No extra page is opened for a photo. When none is found the
report is built without a photo, which is a complete report.

"set" writes listing.json: hero_photo (the address) and extras.hero (where it came from, its size, the day).
A photo narrower than 600 pixels is refused: it would be stretched in a 680 pixel masthead. "set" asks the
address for its headers once (no download) to confirm it answers as an image and to learn how heavy the file
is. A photo over 1.5 MB is kept, and the build tells the operator it will load slowly on a phone.
Standard library only. No real client data belongs in this file.
"""
import argparse
import datetime
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sr_contract as C          # noqa: E402
import sr_files as F             # noqa: E402
import sr_lookups as LK          # noqa: E402

MIN_WIDTH = 600
HEAVY_BYTES = 1500000
HTTPS = re.compile(r"^https://[^\s\"'<>]+$")
RESULT_MAX_BYTES = 1200


def check(url, width=None):
    """Why this address cannot be the masthead photo, or None when it can."""
    if not isinstance(url, str) or not HTTPS.match(url):
        return "the photo must be at a public https address"
    if re.search(r"(^https://(localhost|127\.|10\.|192\.168\.))|[?&](token|sig|signature|expires|key)=", url, re.I):
        return "that address is private or expires, so a mail client could not show it later"
    if width is not None and width < MIN_WIDTH:
        return "the photo is %d pixels wide; the masthead needs at least %d" % (width, MIN_WIDTH)
    return None


def probe(url, timeout=20):
    """(content type, bytes or None) from the address's headers. No download. Raises OSError when it does not answer."""
    import urllib.request
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (seller-report photo check)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        size = r.headers.get("Content-Length")
        return (r.headers.get("Content-Type") or "").split(";")[0].strip().lower(), int(size) if (size or "").isdigit() else None


def set_photo(listing, url, page=None, width=None, height=None, on=None, size=None):
    why = check(url, width)
    if why:
        raise SystemExit(why)
    listing["hero_photo"] = url
    listing.setdefault("extras", {})["hero"] = {"page": page, "width": width, "height": height, "bytes": size,
                                                "set_on": C.iso(on or datetime.date.today())}
    return listing


def heavy_note(listing):
    """One plain line for the chat reply when the masthead photo on file is a heavy file, else None."""
    hero = (listing.get("extras") or {}).get("hero") or {}
    url = listing.get("hero_photo")
    if isinstance(url, str) and HTTPS.match(url) and (hero.get("bytes") or 0) > HEAVY_BYTES:
        return ("The masthead photo is a %.1f MB file, so it may load slowly on a phone. A smaller copy of the same photo would be better."
                % (hero["bytes"] / 1000000.0))
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Set or clear the masthead photo of a listing's report (optional).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("set")
    p.add_argument("--folder", required=True)
    p.add_argument("--result", help="a file holding exactly what hero_photo.js returned")
    p.add_argument("--url")
    p.add_argument("--page", help="the public page the photo was found on")
    p.add_argument("--no-check", action="store_true", help="do not ask the address for its headers")
    p = sub.add_parser("clear")
    p.add_argument("--folder", required=True)
    p = sub.add_parser("show")
    p.add_argument("--folder", required=True)
    a = ap.parse_args(argv)
    path = F.listing_paths(a.folder)["listing"]
    listing = F.load_json(path)
    if a.cmd == "show":
        hero = listing.get("hero_photo")
        ok = isinstance(hero, str) and check(hero) is None
        F.say("masthead photo: %s" % (hero if ok else "none the report can use (%s)" % ("not an https address" if hero else "nothing on file")))
        return 0
    if a.cmd == "clear":
        listing["hero_photo"] = None
        (listing.get("extras") or {}).pop("hero", None)
        F.save_json(path, listing)
        F.say("cleared: the report is built without a masthead photo.")
        return 0
    if a.result:
        try:
            data = LK.read_result(a.result, RESULT_MAX_BYTES, "photo")
        except LK.Refused as e:
            F.say("REFUSED: %s" % e)
            return 4
        if not data.get("photo_url"):
            F.say("no photo: %s. The report is built without one." % (data.get("why") or "the page named none"))
            return 0
        url, page, width, height = data["photo_url"], data.get("page"), data.get("width"), data.get("height")
    elif a.url:
        url, page, width, height = a.url, a.page, None, None
    else:
        raise SystemExit("set needs --result <file> or --url https://...")
    size = None
    if not a.no_check and check(url, width) is None:
        try:
            kind, size = probe(url)
        except (OSError, ValueError) as e:
            F.say("no photo: the address did not answer (%s). The report is built without one." % type(e).__name__)
            return 0
        if not kind.startswith("image/"):
            F.say("no photo: the address answers as %s, not as an image. The report is built without one." % (kind or "nothing"))
            return 0
    set_photo(listing, url, page, width, height, size=size)
    F.save_json(path, listing)
    F.say("masthead photo set: %s%s" % (url, (" (%s by %s)" % (width, height)) if width else ""))
    note = heavy_note(listing)
    if note:
        F.say("  note: " + note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
