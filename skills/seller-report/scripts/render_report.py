#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Weekly Seller Report: render one page from a ledger (email-safe HTML).

    python render_report.py <ledger.json> <out.html> [switches]

What to build (one page per run):
    (nothing)            the email: the full report, for the body of an email. Web fonts off, at most 95,000 bytes.
    --link-copy          the copy that can be forwarded. No offer price, no offer terms, no name of an agent who
                         wrote an offer, nothing that says who may be weighing one. Marked noindex. Holds the
                         complete person by person record.
    --print              the link copy in its print layout (the PDF is printed from this; see render_previews.py).

There is one build mode. Every page is clean and ready to send: nothing on it is addressed to anyone but
the seller.

Other switches:
    --link-url <url>     where the link copy lives (https). The email gets a button to it. Without it, and with
                         --no-link, the email has no button and offers to send the complete record on request.
    --no-link            the email has no button.
    --hero <url>         masthead photo, at an https address. Without it the ledger's hero_photo is used when it
                         is https. A local path is never put on a page: the page is built without a photo.
    --no-hero            no masthead photo.
    --seller-greeting <text>   the line above the brief, for example "Hi Pat and Sam,". Without it the greeting is
                         built from listing.seller_first_names when the ledger has them. Email only.
    --no-greeting        no greeting line.
    --webfonts / --no-webfonts   load Montserrat and Inter from Google Fonts (default: on for the link copy and
                         print, off for the email, because Gmail does not load them).
    --no-market, --no-marketing  leave an optional section out even though the ledger has it.
    --identity <path>    identity.json (name, REALTOR line, brokerage line, DRE, phone, email, disclaimer, blocklist).
    --max-bytes <n>      ceiling for the email (default 95000).
    --info <path>        also write the result JSON to this file.

The ledger must satisfy sr_contract.validate_ledger. report.brief_override, when present, replaces the text of
"This week in brief" in the email. Standard library only. Prints one line of JSON on success. Exit code 2 and a
list of reasons on stderr when the build is refused.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sr_contract as C                      # noqa: E402
from sr_render import render, RenderRefused  # noqa: E402


def parse(argv):
    ap = argparse.ArgumentParser(prog="render_report.py", description="Render one seller report page from a ledger.",
                                 epilog="Run with no arguments to see the full notes.")
    ap.add_argument("ledger")
    ap.add_argument("out")
    what = ap.add_mutually_exclusive_group()
    what.add_argument("--link-copy", action="store_true")
    what.add_argument("--print", dest="print_", action="store_true")
    lk = ap.add_mutually_exclusive_group()
    lk.add_argument("--link-url")
    lk.add_argument("--no-link", action="store_true")
    hr = ap.add_mutually_exclusive_group()
    hr.add_argument("--hero")
    hr.add_argument("--no-hero", action="store_true")
    gr = ap.add_mutually_exclusive_group()
    gr.add_argument("--seller-greeting")
    gr.add_argument("--no-greeting", action="store_true")
    wf = ap.add_mutually_exclusive_group()
    wf.add_argument("--webfonts", dest="webfonts", action="store_true", default=None)
    wf.add_argument("--no-webfonts", dest="webfonts", action="store_false")
    ap.add_argument("--no-market", action="store_true")
    ap.add_argument("--no-marketing", action="store_true")
    ap.add_argument("--identity")
    ap.add_argument("--max-bytes", type=int)
    ap.add_argument("--info")
    return ap.parse_args(argv)


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    a = parse(argv)
    mode = "print" if a.print_ else "link" if a.link_copy else "email"
    try:
        with open(a.ledger, encoding="utf-8") as f:
            ledger = json.load(f)
        identity = C.load_identity(a.identity)
    except (OSError, ValueError, KeyError) as e:
        sys.stderr.write("BUILD REFUSED (input)\n  could not read the ledger or identity.json: %s\n" % e)
        return 2
    try:
        r = render(ledger, identity=identity, mode=mode, hero=a.hero, no_hero=a.no_hero, link_url=a.link_url, no_link=a.no_link,
                   greeting=a.seller_greeting, no_greeting=a.no_greeting, webfonts=a.webfonts, max_bytes=a.max_bytes,
                   market=not a.no_market, marketing=not a.no_marketing)
    except RenderRefused as e:
        sys.stderr.write("BUILD REFUSED (%s)\n  %s\n" % (e.stage, "\n  ".join(e.problems[:60])))
        if len(e.problems) > 60:
            sys.stderr.write("  and %d more\n" % (len(e.problems) - 60))
        return 2
    folder = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(folder, exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(r["html"])
    info = dict(r["info"], out=os.path.abspath(a.out), ledger=os.path.abspath(a.ledger))
    if a.info:
        with open(a.info, "w", encoding="utf-8", newline="\n") as f:
            json.dump(info, f, indent=1)
            f.write("\n")
    print(json.dumps(info))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
