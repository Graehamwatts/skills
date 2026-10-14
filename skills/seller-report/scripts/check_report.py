# -*- coding: utf-8 -*-
r"""check_report: the ship gate of the seller-report skill.

Run it on every build, silently, before anything is put in a Gmail draft. The operator hears about a check
only when it fails, in plain words. It reads the built page and the data it was built from. It never imports
the renderer. There is one build mode, so every page is checked as the report a seller will read.

    Check a whole folder of pages (email.html, email_gmail.html, link.html, print.html with ledger.json, and
    manifest.json when the issue has been kept):

        python check_report.py --issue "<data root>\<slug>\issues\07"
        python check_report.py --issue "<data root>\<slug>\work\build"

    Check one page:

        python check_report.py "<page.html>" --ledger "<ledger.json>" --kind email

Exit code 0: nothing blocking. 1: at least one blocking failure. 2: the gate could not read its inputs.

Families: ledger, numbers, privacy, tone, feedback_only, brand, hygiene, email_safety, wrong_file, layout.
Each rule prints pass, FAIL, warn or skip with the evidence. --json writes the same report as data.
--hooks prints the data-sr attributes the gate reads on the page. --probe adds true phone-width renders in Edge.

Switches a person decides (each is printed in the report):
    --confirm-brief-override     Graeham wrote this issue's brief himself; wording in it is his, not generated
    --brief-override-file PATH   the exact text of that brief
    --waive RULE=REASON          turn one waivable failure into a warning, with the reason on record
    --allow-phone / --allow-email / --allow-name / --allow-term   one more value the page may carry
"""
import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sr_checks                      # noqa: E402
from sr_checks import core            # noqa: E402

# email_gmail.html is the Gmail-safe copy of the email: checked as the email, and against it (sr_checks.email_safety)
PAGES = (("email.html", "email"), ("email_gmail.html", "email"), ("link.html", "link"), ("print.html", "print"))


def parse_args(argv):
    p = argparse.ArgumentParser(prog="check_report.py", description="The ship gate of the seller-report skill.",
                                epilog="Exit 0: nothing blocking. 1: blocked. 2: the gate could not read its inputs.")
    p.add_argument("page", nargs="?", help="one built HTML page")
    p.add_argument("--issue", help="a folder of built pages: ...\\issues\\NN, or the staging folder ...\\work\\build")
    p.add_argument("--ledger", help="ledger.json the page was built from")
    p.add_argument("--listing", help="listing.json of the listing")
    p.add_argument("--raw", help="raw.json of the listing (PRIVATE; used to search the page for what must not be on it)")
    p.add_argument("--events", help="events.json of the listing, when there is one")
    p.add_argument("--manifest", help="manifest.json of the issue")
    p.add_argument("--identity", help="identity.json (default: shared-references\\identity.json)")
    p.add_argument("--data-root", help="the folder that holds one folder per listing")
    p.add_argument("--kind", choices=core.KINDS, help="email, link or print (default: from the file name)")
    p.add_argument("--only", help="comma separated families to run, for example numbers,privacy")
    p.add_argument("--probe", action="store_true", help="also render at 390, 360 and 320 px in Edge")
    p.add_argument("--browser", help="path to Edge or Chrome for --probe")
    p.add_argument("--json", dest="json_out", help="write the report as JSON to this path ('-' for standard output)")
    p.add_argument("-v", "--verbose", action="store_true", help="list the rules that passed as well")
    p.add_argument("--confirm-brief-override", action="store_true",
                   help="the operator confirms Graeham wrote this issue's brief himself")
    p.add_argument("--brief-override-file", help="a text file with the exact brief Graeham wrote")
    p.add_argument("--waive", action="append", default=[], metavar="RULE=REASON",
                   help="turn one waivable failure into a warning, for example privacy.sensitive_terms=\"seller asked about the stairs\"")
    p.add_argument("--allow-phone", action="append", default=[])
    p.add_argument("--allow-email", action="append", default=[])
    p.add_argument("--allow-name", action="append", default=[], help="a full name that may be printed, for example a team member")
    p.add_argument("--allow-term", action="append", default=[], help="a word from the health, family and money list that may be printed")
    p.add_argument("--allow-synthetic", action="store_true", help="let a page built from the synthetic test ledger pass (tests only)")
    p.add_argument("--today", help="today's date as YYYY-MM-DD (default: the computer's date)")
    p.add_argument("--hooks", action="store_true", help="print the data-sr hooks the gate reads, and stop")
    if "--hooks" in argv:
        print(sr_checks.HOOK_GUIDE)
        raise SystemExit(0)
    a = p.parse_args(argv)
    if bool(a.page) == bool(a.issue):
        p.error("give one page, or --issue with an issue folder")
    return a


def _find_issue_parts(path):
    """(listing folder, issue number text) from any path under ...\\<slug>\\issues\\NN, or under a listing folder
    (one that holds listing.json), such as the staging folder ...\\<slug>\\work\\build."""
    parts = os.path.abspath(path).replace("\\", "/").split("/")
    low = [p.lower() for p in parts]
    if "issues" in low:
        i = len(low) - 1 - low[::-1].index("issues")
        slug_dir = "/".join(parts[:i]) or "/"
        number = parts[i + 1] if i + 1 < len(parts) else None
        return os.path.normpath(slug_dir), number
    d = os.path.abspath(path)
    for _ in range(4):
        d = os.path.dirname(d)
        if os.path.isfile(os.path.join(d, "listing.json")) and os.path.isfile(os.path.join(d, "raw.json")):
            return d, None
    return None, None


def _optional(path, what):
    return core.read_json(path, what) if path and os.path.isfile(path) else None


def build_contexts(a):
    """One core.Ctx per page to check."""
    notes = []
    if a.issue:
        folder = os.path.abspath(a.issue)
        if not os.path.isdir(folder):
            raise core.GateInputError("the issue folder does not exist: %s" % folder)
        pages = [(os.path.join(folder, fn), kind) for fn, kind in PAGES if os.path.isfile(os.path.join(folder, fn))]
        if not pages:
            raise core.GateInputError("no email.html, link.html or print.html in %s" % folder)
        ledger_path = a.ledger or os.path.join(folder, "ledger.json")
        manifest_path = a.manifest or (os.path.join(folder, "manifest.json") if os.path.isfile(os.path.join(folder, "manifest.json")) else None)
        anchor = folder
    else:
        if not os.path.isfile(a.page):
            raise core.GateInputError("the page does not exist: %s" % a.page)
        if not a.ledger:
            raise core.GateInputError("say which ledger the page was built from: --ledger <ledger.json>")
        pages = [(os.path.abspath(a.page), a.kind)]
        ledger_path, manifest_path, anchor = a.ledger, a.manifest, os.path.abspath(a.page)
    ledger = core.read_json(ledger_path, "ledger.json")
    if not isinstance(ledger, dict) or "report" not in ledger or "listing" not in ledger:
        raise core.GateInputError("%s is not a seller-report ledger (no 'report' or 'listing' block)" % ledger_path)
    manifest = _optional(manifest_path, "manifest.json")

    slug_dir, issue_text = _find_issue_parts(os.path.join(anchor, "x") if os.path.isdir(anchor) else anchor)
    if slug_dir is None:
        slug_dir, issue_text = _find_issue_parts(ledger_path)
    if slug_dir is None:
        d = os.path.dirname(os.path.abspath(ledger_path))
        if os.path.basename(d) == (ledger.get("meta") or {}).get("slug"):
            slug_dir = d
    listing_path = a.listing or (os.path.join(slug_dir, "listing.json") if slug_dir else None)
    raw_path = a.raw or (os.path.join(slug_dir, "raw.json") if slug_dir else None)
    events_path = a.events or (os.path.join(slug_dir, "events.json") if slug_dir else None)
    listing, raw, events = _optional(listing_path, "listing.json"), _optional(raw_path, "raw.json"), _optional(events_path, "events.json")
    data_root = a.data_root or (os.path.dirname(slug_dir) if slug_dir else None)
    identity = core.load_identity(a.identity or core.default_identity_path())


    brief = []
    if a.brief_override_file:
        try:
            with open(a.brief_override_file, encoding="utf-8") as f:
                brief.append(f.read())
        except OSError as e:
            raise core.GateInputError("cannot read the brief override file: %s" % e)
    waivers = {}
    for w in a.waive:
        rule, _, reason = w.partition("=")
        waivers[rule.strip()] = reason.strip()
    issue_number = None
    if issue_text and re.fullmatch(r"\d+", issue_text or ""):
        issue_number = int(issue_text)
    opts = {
        "probe": a.probe, "browser": a.browser, "confirm_brief_override": a.confirm_brief_override,
        "brief_override_text": brief, "allow_phone": a.allow_phone, "allow_email": a.allow_email,
        "allow_name": a.allow_name, "allow_term": a.allow_term, "allow_synthetic": a.allow_synthetic,
        "events": [events] if events else [], "today": a.today or datetime.date.today().isoformat(),
        "slug_dir_name": os.path.basename(slug_dir) if slug_dir and a.issue else None,
        "issue_dir_number": issue_number if a.issue else None,
    }
    for label, value, path in (("listing.json", listing, listing_path), ("raw.json", raw, raw_path), ("manifest.json", manifest, manifest_path)):
        notes.append("%s: %s" % (label, path if value is not None else "not found"))
    notes.append("data root: %s" % (data_root or "not known"))
    if a.confirm_brief_override:
        notes.append("the operator confirmed a brief override written by Graeham")
    out = []
    for path, kind in pages:
        with open(path, "rb") as f:
            head = f.read(4000).decode("utf-8", "replace").lower()
        if kind is None:
            stem = os.path.splitext(os.path.basename(path))[0].lower()
            said = re.search(r'<meta[^>]+name="sr:kind"[^>]+content="(\w+)"', head)
            if stem in core.KINDS:
                kind = stem
            elif said and said.group(1) in core.KINDS:
                kind = said.group(1)
            elif "link" in stem:
                kind = "link"
            elif "print" in stem:
                kind = "print"
            else:
                kind = "link" if re.search(r'<meta[^>]+name="robots"[^>]+noindex', head) else "email"
            page_notes = notes + ["kind worked out from the file: %s (say --kind to be sure)" % kind]
        else:
            page_notes = notes
        out.append(core.Ctx(path, ledger, identity, kind, listing=listing, raw=raw, manifest=manifest,
                            data_root=data_root, ledger_path=os.path.abspath(ledger_path), manifest_path=manifest_path,
                            opts=opts, notes=page_notes))
    return out, waivers


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    a = parse_args(sys.argv[1:] if argv is None else argv)
    families = [f.strip() for f in (a.only or "").split(",") if f.strip()] or None
    if families:
        unknown = [f for f in families if f not in sr_checks.FAMILIES]
        if unknown:
            print("unknown family: %s (choose from %s)" % (", ".join(unknown), ", ".join(sr_checks.FAMILIES)), file=sys.stderr)
            return 2
    try:
        contexts, waivers = build_contexts(a)
        reports = [sr_checks.run(c, families=families, waivers=waivers) for c in contexts]
    except core.GateInputError as e:
        print("check_report: %s" % e, file=sys.stderr)
        return 2
    blocked = [r for r in reports if not r.ok]
    payload = {"ok": not blocked, "checked_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
               "families": list(families or sr_checks.FAMILIES), "waivers": waivers, "pages": [r.as_dict() for r in reports]}
    if a.json_out == "-":
        print(json.dumps(payload, indent=1, ensure_ascii=True))
    else:
        for r in reports:
            print(r.as_text(verbose=a.verbose))
            print("")
        print("SHIP GATE: %s (%d page%s, %d blocking, %d warnings)"
              % ("passed" if not blocked else "BLOCKED", len(reports), "" if len(reports) == 1 else "s",
                 sum(len(r.blocking) for r in reports), sum(r.count(core.WARN) for r in reports)))
        if a.json_out:
            with open(a.json_out, "w", encoding="utf-8", newline="\n") as f:
                json.dump(payload, f, indent=1, ensure_ascii=True)
            print("report written to %s" % a.json_out)
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
