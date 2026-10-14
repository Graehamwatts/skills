# -*- coding: utf-8 -*-
r"""draft_check: is the Gmail draft the report that was checked?

    python draft_check.py --issue "<listing folder>\issues\07" --draft <the saved get_draft result>

After Claude puts email_gmail.html into an unsent Gmail draft with the Gmail connector, it reads the draft back
with get_draft in the raw view (the harness saves a large result to a file) and runs this on that file. It
finds the HTML part in what was saved (a raw MIME message, the same base64url encoded inside JSON, or the HTML
part already decoded), and compares it with the issue's email_gmail.html after the connector's known clean-up
(references\data-contract.md, section 7: images, tel: links, backgrounds, the head and the style blocks go,
web links become redirects). Text and numbers come through the connector intact, so:

    same_words    the words a reader sees in the draft are exactly those of email_gmail.html
    no_images     the draft has no image (an image means email.html went in, not the Gmail-safe copy)
    no_dead_links no javascript:void(0) link (a dead link means a tel: link went in)
    no_web_links  no web link but the record button (a google.com/url link means the website or a plain-text
                  domain was auto-linked by the connector, which the Gmail-safe copy exists to prevent)
    subject       when the saved result has headers: "Weekly Seller Report No. NN · <Month D, YYYY> - <address>",
                  the address from listing.json subject_address when set. A difference only in the street suffix
                  (Ct / Court) is a note line, not a failure
    to            someone other than the team's own addresses (the seller)
    cc            Adrian (client care) when a CC is present. No CC at all is a note: Graeham adds Adrian himself

It never sends, changes or deletes a draft. It reads two files and prints what it found.
Exit 0 when the draft matches, 1 when it does not, 2 when the inputs cannot be read.
Standard library only. No real client data belongs in this file.
"""
import argparse
import base64
import datetime
import email
import email.policy
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from sr_checks.email_safety import reading_words, first_difference      # noqa: E402
from sr_checks.page import Page                                          # noqa: E402

EXIT_OK, EXIT_DIFFERENT, EXIT_INPUT = 0, 1, 2
GMAIL_FILE = "email_gmail.html"
# Adrian, client care: the CC on every draft (references\delivery.md, section 1, holds the same address)
CLIENT_CARE = "graehamwattsclientcare@gmail.com"
RECORD_BUTTON = "OPEN THE COMPLETE RECORD"
SUFFIXES = {"ct": "court", "rd": "road", "st": "street", "ave": "avenue", "av": "avenue", "dr": "drive", "ln": "lane",
            "ter": "terrace", "terr": "terrace", "pl": "place", "blvd": "boulevard", "wy": "way", "cir": "circle",
            "hwy": "highway", "pkwy": "parkway"}


def subject_address(listing):
    """The address as the seller's series writes it: listing.json subject_address when set, else the address."""
    listing = listing or {}
    return listing.get("subject_address") or listing.get("address") or ""


def subject_line(issue_number, report_date, address):
    """'Weekly Seller Report No. 07 · October 12, 2026 - 1982 Sample Rd #2' (a middle dot and a plain hyphen)."""
    d = datetime.date(*[int(x) for x in str(report_date)[:10].split("-")])
    return "Weekly Seller Report No. %02d · %s %d, %d - %s" % (int(issue_number), d.strftime("%B"), d.day, d.year, address)


def _suffix_free(s):
    """A subject with every street suffix written out in full, for a comparison that ignores Ct / Court."""
    words = re.findall(r"[A-Za-z0-9#]+|[^A-Za-z0-9#\s]", s.lower())
    return " ".join(SUFFIXES.get(w, w) for w in words)


def _addresses(value):
    return [x.lower() for x in re.findall(r"[\w.+'-]+@[\w-]+(?:\.[\w-]+)+", value or "")]


def _agent_email():
    try:
        from sr_contract import load_identity
        return (load_identity().get("email") or "").lower()
    except Exception:                                    # identity.json missing: the To check still runs
        return ""


def _mime_html(raw):
    """(html, headers) from one MIME message as bytes, or (None, None)."""
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    html = None
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html = part.get_content()
            break
    if html is None:
        return None, None
    return html, dict((k, str(v)) for k, v in msg.items() if k.lower() in ("to", "cc", "subject", "from"))


def _b64(s):
    t = re.sub(r"\s+", "", s)
    if len(t) < 40 or not re.fullmatch(r"[A-Za-z0-9_\-+/=]+", t):
        return None
    try:
        return base64.urlsafe_b64decode(t + "=" * (-len(t) % 4))
    except (ValueError, TypeError):
        return None


def find_html(text):
    """(html, headers or None, what was found) from the saved get_draft result."""
    candidates = []
    try:
        data = json.loads(text)
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, str):
                candidates.append(node)
    except ValueError:
        candidates.append(text)
    for s in sorted(candidates, key=len, reverse=True):
        if re.match(r"(?:[\w-]+:[^\n]*\n)+", s) and re.search(r"(?im)^content-type:", s):
            html, head = _mime_html(s.encode("utf-8", "surrogateescape"))
            if html:
                return html, head, "a raw MIME message"
        raw = _b64(s)
        if raw and re.search(rb"(?im)^content-type:", raw[:4000]):
            html, head = _mime_html(raw)
            if html:
                return html, head, "a base64url MIME message"
        if re.search(r"<table\b", s, re.I):
            return s, None, "the HTML part"
    return None, None, None


def check(issue_dir, draft_text):
    """(exit code, lines)."""
    lines, bad = [], 0
    path = os.path.join(issue_dir, GMAIL_FILE)
    if not os.path.isfile(path):
        return EXIT_INPUT, ["there is no %s in %s. Build the issue with run_issue.py first." % (GMAIL_FILE, issue_dir)]
    html, head, what = find_html(draft_text)
    if html is None:
        return EXIT_INPUT, ["no HTML part was found in the saved draft. Save the whole get_draft result (raw view) and run this again."]
    lines.append("read the draft from %s" % what)
    with open(path, encoding="utf-8") as f:
        mine = reading_words(Page(f.read()))
    theirs = reading_words(Page(html))
    if mine == theirs:
        lines.append("same_words: the draft says exactly what %s says (%s characters)" % (GMAIL_FILE, "{:,}".format(len(mine))))
    else:
        bad += 1
        lines.append("DIFFERENT same_words: the draft does not say what %s says" % GMAIL_FILE)
        lines += ["  " + x.replace("email.html:", GMAIL_FILE + ":").replace("this copy: ", "the draft:  ") for x in first_difference(mine, theirs)]
    imgs = len(re.findall(r"<img\b", html, re.I))
    dead = len(re.findall(r'href="javascript:void', html, re.I))
    if imgs:
        bad += 1
        lines.append("DIFFERENT no_images: the draft has %d image(s), so email.html went in, not %s" % (imgs, GMAIL_FILE))
    if dead:
        bad += 1
        lines.append("DIFFERENT no_dead_links: the draft has %d dead link(s) (a tel: link went in)" % dead)
    if not imgs and not dead:
        lines.append("no_images, no_dead_links: none")
    links = re.findall(r'<a\b[^>]*href="(https?:[^"]*)"[^>]*>(.*?)</a>', html, re.S | re.I)
    button = [h for h, x in links if " ".join(re.sub(r"<[^>]+>", " ", x).split()).upper() == RECORD_BUTTON]
    web = [(h, x) for h, x in links if " ".join(re.sub(r"<[^>]+>", " ", x).split()).upper() != RECORD_BUTTON]
    if web:
        bad += 1
        lines.append("DIFFERENT no_web_links: the draft has %d web link(s) the connector made, e.g. '%s' -> %s"
                     % (len(web), " ".join(re.sub(r"<[^>]+>", "", web[0][1]).split())[:40], web[0][0][:70]))
    else:
        lines.append("no_web_links: none")
    if button:
        lines.append("note: the record button links to %s (a redirect the connector made is fine for a published copy)" % button[0][:70])
    manifest = os.path.join(issue_dir, "manifest.json")
    ledger = os.path.join(issue_dir, "ledger.json")
    if head is None:
        lines.append("subject, to, cc: the saved result has no headers, so they were not checked")
    elif os.path.isfile(manifest) and os.path.isfile(ledger):
        with open(manifest, encoding="utf-8") as f:
            mf = json.load(f)
        with open(ledger, encoding="utf-8") as f:
            addr = subject_address(json.load(f).get("listing"))
        want = subject_line(mf["issue_number"], mf["report_date"], addr)
        got = " ".join((head.get("Subject") or "").split())
        if got == want:
            lines.append("subject: %s" % got)
        elif _suffix_free(got) == _suffix_free(want):
            lines.append("subject: %s" % got)
            lines.append("note: the subject writes the street suffix differently from '%s'. Keep the form the seller's series "
                         "uses (listing.json subject_address holds it once Graeham says which)" % want)
        else:
            bad += 1
            lines.append("DIFFERENT subject: the draft says '%s'; it should be '%s'" % (got, want))
        to, agent = _addresses(head.get("To")), _agent_email()
        lines.append("to: %s" % (", ".join(to) or "(nobody)"))
        if not [x for x in to if x not in (CLIENT_CARE, agent)]:
            bad += 1
            lines.append("DIFFERENT to: the draft is not addressed to the seller (it has %s)" % ("no To" if not to else "only the team's own address"))
        cc = _addresses(head.get("Cc"))
        if not cc:
            lines.append("cc: the draft has no CC. Tell Graeham to add Adrian (client care) himself; never work around a refused update_draft")
        elif CLIENT_CARE not in cc:
            bad += 1
            lines.append("DIFFERENT cc: the draft is copied to %s, not to Adrian (%s)" % (", ".join(cc), CLIENT_CARE))
        else:
            lines.append("cc: %s" % ", ".join(cc))
    return (EXIT_DIFFERENT if bad else EXIT_OK), lines


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Compare a Gmail draft (the saved get_draft result) with the issue's Gmail-safe copy.",
                                 epilog="Exit 0 the draft matches. 1 it does not. 2 an input cannot be read.")
    ap.add_argument("--issue", required=True, help="the issue folder: <listing folder>\\issues\\NN")
    ap.add_argument("--draft", required=True, help="the file the harness saved the get_draft result in (raw view), or the decoded HTML part")
    a = ap.parse_args(argv)
    try:
        with open(a.draft, "rb") as f:
            text = f.read().decode("utf-8", "surrogateescape")
    except OSError as e:
        print("draft_check: cannot read %s: %s" % (a.draft, e))
        return EXIT_INPUT
    code, lines = check(os.path.abspath(a.issue), text)
    for ln in lines:
        print(ln)
    print("DRAFT MATCHES" if code == EXIT_OK else ("DRAFT DOES NOT MATCH" if code == EXIT_DIFFERENT else "NOT CHECKED"))
    return code


if __name__ == "__main__":
    sys.exit(main())
