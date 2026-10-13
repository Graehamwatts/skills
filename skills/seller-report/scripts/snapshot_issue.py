# -*- coding: utf-8 -*-
"""snapshot_issue: keeps one issue of the seller report in the listing's issues folder.

    python snapshot_issue.py next   --folder <listing folder> [--report-date 2026-10-12]
    python snapshot_issue.py freeze --folder <listing folder> --from <folder with the rendered files>
    python snapshot_issue.py record --folder <listing folder> --issue 7 --gmail-draft-id <id>
    python snapshot_issue.py record --folder <listing folder> --issue 7 --sent-on 2026-10-12
    python snapshot_issue.py list   --folder <listing folder>

next    reports the issue number the next report gets. Numbers continue the listing's existing numbering
        (listing.json numbering.first_issue_number, then one more per issue on file). A rebuild for a report
        date that is already on file keeps that issue's number.
freeze  copies ledger.json, notes_for_operator.json and the rendered files into issues\\NN and writes
        manifest.json with the hash of every file. There is one build mode: every issue on file is the report
        as it would be sent. A rebuild after a correction replaces the files. Once the operator says the issue
        went to the seller (record --sent-on), the folder is the record of what was sent and the command
        refuses to replace it (exit status 3) unless --replace-sent is given.
record  notes where an issue went (the Gmail draft id, the published link, the day it was sent) in its
        manifest. The files are not touched.

Nothing here sends an email or publishes a page.
Standard library only. No real client data belongs in this file.
"""
import argparse
import datetime
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sr_contract as C          # noqa: E402
import sr_files as F             # noqa: E402

KNOWN_FILES = ("ledger.json", "email.html", "link.html", "print.html", "report.pdf")
NEVER_COPIED = ("manifest.json", "ledger.json")
EXIT_REFUSED = 3
NO_DELIVERY = {"gmail_draft_id": None, "link_published_url": None, "link_published_on": None, "sent_on": None}


def issues_on_file(folder):
    """[{issue_number, report_date, built_at, sent_on, path}] for every manifest in issues\\NN."""
    out, root = [], os.path.join(os.path.abspath(folder), "issues")
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name, "manifest.json")
        if os.path.exists(path):
            m = F.load_json(path)
            out.append({"issue_number": m.get("issue_number"), "report_date": m.get("report_date"), "built_at": m.get("built_at"),
                        "sent_on": (m.get("delivery") or {}).get("sent_on"), "path": os.path.dirname(path)})
    return out


def next_number(folder, report_date=None):
    """(number, issues on file, report date) for the report dated report_date (default: the Monday after the week just ended)."""
    listing = F.load_json(F.listing_paths(folder)["listing"])
    rd = C.parse_date(report_date) if report_date else C.report_week(datetime.date.today())[2]
    if rd.weekday() != 0:
        raise SystemExit("%s is not a Monday. A report is dated the Monday after the week it covers." % rd)
    on_file = [(i["issue_number"], i["report_date"]) for i in issues_on_file(folder)]
    first = (listing.get("numbering") or {}).get("first_issue_number")
    return C.next_issue_number(first, on_file, rd), on_file, rd


def sections_of(ledger):
    return [k for k in ("market", "marketing") if ledger.get(k)]


def freeze(folder, source=None, ledger_path=None, flags=None, page_checks=0, built_at=None, replace_sent=False, gate=None):
    """Writes the issue folder and its manifest. Returns (exit code, manifest or None, messages)."""
    paths = F.listing_paths(folder)
    ledger_path = ledger_path or (os.path.join(source, "ledger.json") if source and os.path.exists(os.path.join(source, "ledger.json")) else paths["ledger"])
    ledger = F.load_json(ledger_path)
    msgs = []
    problems = C.validate_ledger(ledger, identity=C.load_identity())
    if problems:
        return 2, None, ["the ledger does not pass validation:"] + ["  - " + p for p in problems[:30]]
    R = ledger["report"]
    number = R["issue_number"]
    target = F.issue_dir(folder, number)
    F.refuse_inside_repo(os.path.join(target, "manifest.json"))
    old = F.load_json(os.path.join(target, "manifest.json"), default={})
    sent = (old.get("delivery") or {}).get("sent_on")
    if sent and not replace_sent:
        return EXIT_REFUSED, None, ["issue %02d is recorded as sent to the seller on %s. Its folder is the record of what went out and was not replaced."
                                    % (number, sent),
                                    "If a corrected copy must go out, say so and run this again with --replace-sent."]
    clash = [i for i in issues_on_file(folder) if i["issue_number"] == number and i["report_date"] != R["report_date"]]
    if clash:
        return 2, None, ["issue number %d is already used by the issue for the report dated %s. Rebuild the ledger so the number continues."
                         % (number, clash[0]["report_date"])]
    staged = {}
    if source:
        for name in sorted(os.listdir(source)):
            src = os.path.join(source, name)
            if os.path.isfile(src) and name not in NEVER_COPIED and not name.endswith(".tmp"):
                staged[name] = src
    email_src = staged.get("email.html") or (os.path.join(target, "email.html") if os.path.exists(os.path.join(target, "email.html")) else None)
    if not email_src:
        return 2, None, ["there is no rendered email.html to keep. Render the report first (pass --from <folder with the rendered files>)."]
    limit = C.LIMITS["email_max_bytes"]
    if os.path.getsize(email_src) >= limit:
        return 2, None, ["email.html is %s bytes. The limit is %s (Gmail clips near 102 KB). Nothing was written."
                         % (C.fmt_num(os.path.getsize(email_src)), C.fmt_num(limit))]
    os.makedirs(target, exist_ok=True)
    shutil.copyfile(ledger_path, os.path.join(target, "ledger.json"))
    for name, src in staged.items():
        shutil.copyfile(src, os.path.join(target, name))
    notes = os.path.join(os.path.dirname(os.path.abspath(ledger_path)), "notes_for_operator.json")
    if "notes_for_operator.json" not in staged and os.path.exists(notes):
        shutil.copyfile(notes, os.path.join(target, "notes_for_operator.json"))
    files = []
    for name in sorted(os.listdir(target)):
        p = os.path.join(target, name)
        if os.path.isfile(p) and name != "manifest.json" and not name.endswith(".tmp"):
            files.append({"name": name, "bytes": os.path.getsize(p), "sha256": F.sha256_file(p)})
    missing = [n for n in KNOWN_FILES if n not in [f["name"] for f in files]]
    base = {"webfonts": False, "hero": None, "link_url": None, "sections": sections_of(ledger), "fit_level": 0}
    base.update(flags or {})
    delivery = dict(NO_DELIVERY)
    delivery.update(old.get("delivery") or {})
    if sent and replace_sent:
        msgs.append("note: issue %02d was recorded as sent on %s. This rebuild replaces that record, as asked." % (number, sent))
        delivery.update(sent_on=None, gmail_draft_id=None)
    checks = {"ledger_problems": 0, "page_checks_run": int(page_checks or 0)}
    if gate:
        checks["ship_gate"] = gate
    manifest = {
        "schema_version": C.SCHEMA_VERSION, "slug": ledger["meta"]["slug"], "issue_number": number,
        "report_date": R["report_date"], "week_start": R["week_start"], "week_end": R["week_end"],
        "built_at": built_at or datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "ledger_sha256": F.sha256_file(os.path.join(target, "ledger.json")),
        "files": files, "email_bytes": os.path.getsize(os.path.join(target, "email.html")), "flags": base,
        "checks": checks, "delivery": delivery,
    }
    F.save_json(os.path.join(target, "manifest.json"), manifest)
    msgs.append("issue %02d kept in %s (%d files)" % (number, target, len(files)))
    if missing:
        msgs.append("not rendered: " + ", ".join(missing))
    return 0, manifest, msgs


def record(folder, issue, gmail_draft_id=None, link_url=None, link_published_on=None, sent_on=None):
    path = os.path.join(F.issue_dir(folder, issue), "manifest.json")
    m = F.load_json(path)
    d = dict(NO_DELIVERY)
    d.update(m.get("delivery") or {})
    if gmail_draft_id:
        d["gmail_draft_id"] = gmail_draft_id
    if link_url:
        if not str(link_url).startswith("https://"):
            raise SystemExit("the published link must be an https address")
        d["link_published_url"] = link_url
        d["link_published_on"] = C.iso(link_published_on or datetime.date.today())
    if sent_on:
        d["sent_on"] = C.iso(sent_on)
    m["delivery"] = d
    F.save_json(path, m)
    return m


def main(argv=None):
    ap = argparse.ArgumentParser(description="Keep an issue of the seller report on file, with a manifest (PRIVATE files).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("next")
    p.add_argument("--folder", required=True)
    p.add_argument("--report-date", help="the Monday the report is dated. Default: the Monday after the week just ended")
    p = sub.add_parser("freeze")
    p.add_argument("--folder", required=True)
    p.add_argument("--from", dest="source", help="the folder holding the rendered files (email.html, link.html, print.html, report.pdf)")
    p.add_argument("--ledger", help="default: ledger.json in the --from folder when there is one, else <folder>\\ledger.json")
    p.add_argument("--flags", help="a JSON file of render flags (webfonts, hero, link_url, fit_level) to record in the manifest")
    p.add_argument("--page-checks", type=int, default=0, help="how many page checks the renderer ran, for the record")
    p.add_argument("--gate", help="the JSON report check_report.py wrote, to record its result in the manifest")
    p.add_argument("--replace-sent", action="store_true", help="replace an issue already recorded as sent to the seller")
    p = sub.add_parser("record")
    p.add_argument("--folder", required=True)
    p.add_argument("--issue", required=True, type=int)
    p.add_argument("--gmail-draft-id")
    p.add_argument("--link-url")
    p.add_argument("--link-published-on")
    p.add_argument("--sent-on", help="the day the operator sent this issue to the seller (YYYY-MM-DD)")
    p = sub.add_parser("list")
    p.add_argument("--folder", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "next":
        n, on_file, rd = next_number(a.folder, a.report_date)
        F.say("next issue number: %d (for the report dated %s)" % (n, rd.isoformat()))
        F.say("issues on file: %s" % (", ".join("No. %02d dated %s" % f for f in on_file) or "none"))
        return 0
    if a.cmd == "freeze":
        gate = None
        if a.gate:
            g = F.load_json(a.gate)
            gate = {"passed": bool(g.get("ok")), "checked_at": g.get("checked_at"), "pages": len(g.get("pages") or []),
                    "blocking": sum(int(pg.get("blocking") or 0) for pg in g.get("pages") or [])}
        code, _, msgs = freeze(a.folder, a.source, a.ledger, F.load_json(a.flags) if a.flags else None, a.page_checks,
                               replace_sent=a.replace_sent, gate=gate)
        for m in msgs:
            (F.shout if code else F.say)(m)
        return code
    if a.cmd == "record":
        m = record(a.folder, a.issue, a.gmail_draft_id, a.link_url, a.link_published_on, a.sent_on)
        F.say("recorded on issue %02d: %s" % (a.issue, m["delivery"]))
        return 0
    for i in issues_on_file(a.folder):
        F.say("No. %02d  report dated %s  built %s  %s  %s" % (i["issue_number"], i["report_date"], i["built_at"],
                                                              ("sent %s" % i["sent_on"]) if i["sent_on"] else "not recorded as sent", i["path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
