# -*- coding: utf-8 -*-
r"""run_issue: one command for one issue of the seller report.

    python run_issue.py --folder "<reports>\seller-reports\<slug>" --sheet "<export.xlsx>" --as-of 2026-10-12
    python run_issue.py --folder "<reports>\seller-reports\<slug>"                      (rebuild from raw.json on file)

It runs the steps that need no judgment, in order, and stops where Claude or the operator has to act. Every
stop prints one line that starts with NEXT: and says what to do.

    1. intake      the xlsx export of the activity sheet becomes raw.json (only when --sheet is given)
    2. work list   what Claude has not read yet goes to work\todo.json. If there is any, STOP (exit 10):
                   Claude reads those notes, writes a readings file and runs curation_tools.py apply
    3. ledger      raw + curation + listing become ledger.json and notes_for_operator.json. A row nobody
                   placed, or numbers that do not add up, STOP the run (exit 11)
    4. render      the email, the link copy and the print layout, into work\build (exit 20 when refused)
    5. PDF         printed from the print layout, when Edge is on this computer
    6. checks      the ship gate recounts every number and reads every page: privacy, tone, feedback only,
                   brand, hygiene, email safety, wrong file, phone layout. A failure STOPs the run (exit 30)
    7. keep        the checked files go to issues\NN with a manifest, and phone pictures to issues\NN\previews
                   (exit 3 when that issue was already recorded as sent)

There is one build mode. What comes out is the report, clean and ready to send. Nothing waits for anyone to
confirm anything. When the operator reads it and says what to change, apply it with curation_tools.py correct
and run this again.

This command never sends an email, never drafts one, never publishes a page and never touches a mail filter.
Standard library only (openpyxl for step 1). No real client data belongs in this file.
"""
import argparse
import contextlib
import datetime
import io
import json
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sr_contract as C          # noqa: E402
import sr_files as F             # noqa: E402

EXIT_READY, EXIT_INPUT, EXIT_SENT, EXIT_TO_READ, EXIT_LEDGER, EXIT_RENDER, EXIT_CHECKS = 0, 2, 3, 10, 11, 20, 30
PAGES = (("email", "email.html"), ("link", "link.html"), ("print", "print.html"))
# work list items Claude must settle before a ledger can be built, and how each is said in plain words
MUST_READ = (("relink_candidates", "sheet row(s) whose name or number changed and need joining to the person they were"),
             ("new_people", "new person or people on the sheet"),
             ("rows_to_add", "new row(s) that may belong to someone already on file"),
             ("entries", "note(s) not read yet"),
             ("open_house_sessions_undated", "open house session(s) with no date typed, which need a date before they can be counted"),
             ("offer_rows", "row(s) on the offers tab not entered yet"))


def here(name):
    return os.path.join(_HERE, name)


def stop(code, headline, lines=(), nxt=None):
    F.say("")
    F.say("STOPPED: " + headline)
    for ln in lines:
        F.say("  - " + ln)
    if nxt:
        F.say("NEXT: " + nxt)
    return code


def step(n, text):
    F.say("[%d/7] %s" % (n, text))


def quiet_call(fn, *args, **kw):
    """Runs a step that prints, keeping its printout. Returns (result, printed text)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        out = fn(*args, **kw)
    return out, buf.getvalue()


def gate(folder, json_out, extra=(), only=None):
    """Runs the ship gate on a folder of pages. Returns (exit code, report dict or None, printed text)."""
    import check_report
    argv = ["--issue", folder, "--json", json_out] + list(extra) + (["--only", only] if only else [])
    try:
        code, text = quiet_call(check_report.main, argv)
    except SystemExit as e:                                  # argparse or an unreadable input
        return 2, None, str(e)
    data = None
    if os.path.exists(json_out):
        with open(json_out, encoding="utf-8") as f:
            data = json.load(f)
    return code, data, text


def plain_failures(report):
    """The gate's failures, one plain line each: which page, what is wrong, the evidence."""
    out = []
    for pg in (report or {}).get("pages") or []:
        for r in pg.get("results") or []:
            if r.get("level") == "fail":
                ev = "; ".join(str(x) for x in (r.get("evidence") or [])[:3])
                out.append("%s: %s%s  [%s]" % (os.path.basename(pg.get("file") or ""), r.get("message"), (" (" + ev + ")") if ev else "", r.get("id")))
    return out


def run(a):
    folder = os.path.abspath(a.folder)
    paths = F.listing_paths(folder)
    F.refuse_inside_repo(os.path.join(folder, "ledger.json"))
    if not os.path.exists(paths["listing"]):
        return stop(EXIT_INPUT, "there is no listing.json in %s" % folder, nxt="write listing.json for this listing (references\\data-contract.md, section 2), then run this again.")
    listing = F.load_json(paths["listing"])
    remake = 'python "%s" %s' % (here("run_issue.py"), " ".join(('"%s"' % x) if (" " in x or "|" in x) else x for x in a.again))

    # ---- 1. intake ----------------------------------------------------------------------------
    if a.sheet:
        import intake_sheet
        step(1, "reading the activity sheet export")
        argv = [a.sheet, "--folder", folder] + (["--as-of", a.as_of] if a.as_of else []) + (["--kind", a.sheet_kind] if a.sheet_kind else [])
        try:
            code, text = quiet_call(intake_sheet.main, argv)
        except SystemExit as e:
            return stop(EXIT_INPUT, "the sheet could not be read: %s" % e, nxt="check the path to the xlsx export and run this again.")
        F.say(text.rstrip())
        if code:
            return stop(EXIT_INPUT, "the sheet was read but a tab is missing or not recognised", nxt="look at the warnings above, then run this again.")
    elif not os.path.exists(paths["raw"]):
        return stop(EXIT_INPUT, "there is no raw.json yet and no sheet was given",
                    nxt="export the listing's View Activity sheet to xlsx and run this again with --sheet <file> --as-of <the day it was exported>.")
    else:
        step(1, "no new sheet given: using raw.json on file")
    raw = F.load_json(paths["raw"])

    # ---- 2. Claude's work list ----------------------------------------------------------------
    import build_ledger
    import curation_tools
    ws, we, rd = [C.iso(d) for d in build_ledger.report_dates(a.report_date, None)]
    through = C.iso(a.through) if a.through else max(we, min(raw.get("as_of") or we, C.iso(datetime.date.today())))
    step(2, "report dated %s, covering %s. Looking for notes not read yet (through %s)" % (rd, C.fmt_range(ws, we), through))
    cur = F.load_json(paths["curation"], default=curation_tools.blank_curation(listing.get("slug") or raw.get("slug")))
    todo = curation_tools.todo(raw, cur, through)
    todo_path = F.save_json(os.path.join(paths["work"], "todo.json"), todo)
    counts = dict(todo["counts"], open_house_sessions_undated=len([s for s in todo["open_house_sessions"] if "date" in s["needs"]]))
    waiting = [(counts.get(k) or 0, words) for k, words in MUST_READ if counts.get(k)]
    recaps = len(todo["open_house_sessions"]) - counts["open_house_sessions_undated"]
    if recaps and not waiting:
        F.say("      note: %d open house recap(s) are not put in plain words yet, so the report shows only their count (work\todo.json lists them)" % recaps)
    if waiting:
        return stop(EXIT_TO_READ, "Claude has reading to do before the report can be built",
                    ["%d %s" % x for x in waiting],
                    "read %s, write a readings file in the shape it shows (readings_file_format), then run:  python \"%s\" apply --folder \"%s\" --readings <readings.json>  and then:  %s"
                    % (todo_path, here("curation_tools.py"), folder, remake))

    # ---- 3. ledger ----------------------------------------------------------------------------
    step(3, "building the ledger")
    brief = None
    if a.brief_file:
        with open(a.brief_file, encoding="utf-8") as f:
            brief = f.read()
    try:
        (ledger, problems, info), text = quiet_call(build_ledger.build, folder, report_date=rd, through=through, issue=a.issue,
                                                    sources=a.source, as_of_note=a.as_of_note, glance=a.glance, brief=brief)
    except SystemExit as e:
        return stop(EXIT_LEDGER, "the ledger could not be built: %s" % e, nxt="fix what the line above names, then run:  " + remake)
    if text.strip():
        F.say(text.rstrip())
    if problems:
        unread = [p for p in problems if "not been read into curation.json" in p or "not accounted for" in p]
        return stop(EXIT_TO_READ if unread and len(unread) == len(problems) else EXIT_LEDGER,
                    "the ledger was not written. %d problem(s)" % len(problems), problems[:40],
                    ("Claude: read the notes named above into curation.json (curation_tools.py todo, then apply). " if unread else
                     "fix what is named above (a row to place, a date to give, or a count that does not add up). ") + "Then run:  " + remake)
    F.save_json(paths["ledger"], ledger)
    notes = info["notes_for_operator"]
    F.save_json(paths["notes_for_operator"], notes)
    R = ledger["report"]
    for k, v in info["headline"].items():
        F.say("      %-34s %s" % (k, v))

    # ---- 4. render ----------------------------------------------------------------------------
    step(4, "rendering issue %02d: the email, the link copy and the print layout" % R["issue_number"])
    from sr_render import render, RenderRefused
    stage = os.path.join(paths["work"], "build")
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    os.makedirs(stage)
    identity = C.load_identity()
    infos = {}
    for mode, name in PAGES:
        kw = dict(mode=mode, hero=a.hero, no_hero=a.no_hero, greeting=a.seller_greeting, no_greeting=a.no_greeting,
                  market=not a.no_market, marketing=not a.no_marketing)
        if mode == "email":
            kw.update(link_url=a.link_url, no_link=a.no_link)
        try:
            r = render(ledger, identity=identity, **kw)
        except RenderRefused as e:
            return stop(EXIT_RENDER, "the %s could not be rendered (%s)" % (name, e.stage), e.problems[:30],
                        "this is a fault in the data or the renderer, not something the operator did. Fix what is named above, then run:  " + remake)
        with open(os.path.join(stage, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(r["html"])
        infos[mode] = r["info"]
        for w in r["info"]["warnings"]:
            F.say("      note (%s): %s" % (name, w))
    shutil.copyfile(paths["ledger"], os.path.join(stage, "ledger.json"))
    F.save_json(os.path.join(stage, "notes_for_operator.json"), notes)
    F.say("      email.html %s bytes of %s allowed (fit level %d). link.html %s bytes. print.html %s bytes."
          % (C.fmt_num(infos["email"]["bytes"]), C.fmt_num(C.LIMITS["email_max_bytes"]), infos["email"]["fit_level"],
             C.fmt_num(infos["link"]["bytes"]), C.fmt_num(infos["print"]["bytes"])))

    # ---- 5. PDF -------------------------------------------------------------------------------
    import render_previews
    have_edge = any(os.path.exists(p) for p in render_previews.EDGE_PATHS)
    if a.no_pdf or not have_edge:
        step(5, "PDF skipped (%s)" % ("--no-pdf" if a.no_pdf else "Microsoft Edge is not on this computer"))
    else:
        step(5, "printing the PDF from the print layout")
        code, text = quiet_call(render_previews.pdf, os.path.join(stage, "print.html"), os.path.join(stage, "report.pdf"))
        F.say("      " + (text.strip().split("\n")[-1] if text.strip() else "done"))
        if code:
            return stop(EXIT_RENDER, "the PDF could not be printed", [text.strip()[-400:]], "run this again, or pass --no-pdf to build without the PDF.")

    # ---- 6. the independent checks, silent unless one fails ------------------------------------
    step(6, "running the checks (numbers recounted, privacy, tone, feedback only, brand, hygiene, email safety, wrong file%s)"
         % (", phone layout" if have_edge and not a.no_probe else ""))
    extra = []
    if have_edge and not a.no_probe:
        extra.append("--probe")
    if brief:
        brief_copy = os.path.join(paths["work"], "brief.txt")
        F.save_text(brief_copy, brief)
        extra += ["--confirm-brief-override", "--brief-override-file", brief_copy]
    for w in a.waive:
        extra += ["--waive", w]
    for flag, values in (("--allow-name", a.allow_name), ("--allow-term", a.allow_term)):
        for v in values:
            extra += [flag, v]
    if (ledger.get("meta") or {}).get("synthetic") and a.allow_synthetic:
        extra.append("--allow-synthetic")
    gate_json = os.path.join(paths["work"], "gate.json")
    code, report, text = gate(stage, gate_json, extra)
    if code == 2 or report is None:
        return stop(EXIT_CHECKS, "the checks could not run", [text.strip()[-600:]], "fix what the line above names, then run:  " + remake)
    warned = sum((pg.get("counts") or {}).get("warn", 0) for pg in report["pages"])
    if code:
        fails = plain_failures(report)
        return stop(EXIT_CHECKS, "a check failed, so nothing was kept and nothing should go in a draft. %d problem(s)" % len(fails), fails[:40],
                    "the full report is in %s. If the report says something wrong, correct it (curation_tools.py correct) and run:  %s"
                    % (gate_json, remake))
    F.say("      all checks passed on %d page(s)%s" % (len(report["pages"]), (", %d note(s) in %s" % (warned, gate_json)) if warned else ""))

    # ---- 7. keep the issue --------------------------------------------------------------------
    step(7, "keeping issue %02d on file" % R["issue_number"])
    import snapshot_issue
    flags = dict(infos["email"]["flags"])
    summary = {"passed": True, "checked_at": report.get("checked_at"), "pages": len(report["pages"]), "blocking": 0, "warnings": warned}
    code, manifest, msgs = snapshot_issue.freeze(folder, stage, os.path.join(stage, "ledger.json"), flags,
                                                 infos["email"]["checks"]["model_checks_run"], replace_sent=a.replace_sent, gate=summary)
    if code:
        if code == snapshot_issue.EXIT_REFUSED:
            return stop(EXIT_SENT, msgs[0], msgs[1:], "the new build is in %s. Ask the operator whether a corrected copy should replace the one that went out; if yes, run:  %s --replace-sent"
                        % (stage, remake))
        return stop(EXIT_LEDGER, "the issue could not be kept", msgs, "fix what is named above, then run:  " + remake)
    issue_dir = F.issue_dir(folder, R["issue_number"])
    code, kept, text = gate(issue_dir, os.path.join(paths["work"], "gate-kept.json"),
                            ["--allow-synthetic"] if "--allow-synthetic" in extra else [], only="wrong_file")
    if code:
        return stop(EXIT_CHECKS, "the files kept in %s are not the ones that were checked" % issue_dir, plain_failures(kept) or [text.strip()[-400:]],
                    "run:  " + remake)
    previews = os.path.join(issue_dir, "previews")
    if a.no_previews or not have_edge:
        F.say("      phone pictures skipped")
    else:
        if os.path.isdir(previews):
            shutil.rmtree(previews)
        _, text = quiet_call(render_previews.render, os.path.join(issue_dir, "email.html"), "email", previews)
        F.say("      phone and desktop pictures of the email: %s" % previews)

    F.say("")
    F.say("READY: Weekly Seller Report No. %02d for %s, dated %s, covering %s."
          % (R["issue_number"], ledger["listing"]["address"], R["report_date"], C.fmt_range(R["week_start"], R["week_end"])))
    F.say("  email (goes in the body of an unsent Gmail draft): %s" % os.path.join(issue_dir, "email.html"))
    F.say("  link copy (published only when the operator says so): %s" % os.path.join(issue_dir, "link.html"))
    if os.path.exists(os.path.join(issue_dir, "report.pdf")):
        F.say("  PDF: %s" % os.path.join(issue_dir, "report.pdf"))
    if notes["worth_a_glance"]:
        F.say("  Worth a glance before you send (for the chat reply, never for the report):")
        for line in notes["worth_a_glance"]:
            F.say("    - " + line)
    F.say("NEXT: put email.html in the body of an unsent Gmail draft for the operator (never send it), then record it:  "
          "python \"%s\" record --folder \"%s\" --issue %d --gmail-draft-id <id>" % (here("snapshot_issue.py"), folder, R["issue_number"]))
    return EXIT_READY


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run one issue of the seller report from the sheet export to the checked files.",
                                 epilog="Exit 0 ready. 2 an input is missing. 3 the issue was already sent. 10 Claude has notes to read. "
                                        "11 the ledger did not build. 20 a page did not render. 30 a check failed.")
    ap.add_argument("--folder", required=True, help="the listing folder: <reports>\\seller-reports\\<slug>")
    ap.add_argument("--sheet", help="the xlsx export of the View Activity sheet. Without it the raw.json on file is used")
    ap.add_argument("--as-of", help="YYYY-MM-DD the sheet was exported. Default: today")
    ap.add_argument("--sheet-kind", choices=("activity_sheet_live", "activity_sheet_file"),
                    help="activity_sheet_live (default) for a fresh export, activity_sheet_file for a copy someone attached")
    ap.add_argument("--report-date", help="the Monday the report is dated. Default: the Monday after the week that just ended")
    ap.add_argument("--through", help="show entries after the week end up to this day as 'since the week closed'. Default: the sheet's export date")
    ap.add_argument("--issue", type=int, help="override the issue number. Default: continue the numbering on file")
    ap.add_argument("--source", action="append", default=[], metavar="KIND|LABEL|YYYY-MM-DD",
                    help="another source the operator handed over in this session (repeatable)")
    ap.add_argument("--glance", action="append", default=[], metavar="SENTENCE",
                    help="one plain line for 'Worth a glance before you send' (repeatable)")
    ap.add_argument("--as-of-note", help="an operator note kept in the ledger. Never printed to a seller")
    ap.add_argument("--brief-file", help="a text file with the agent's own words for 'This week in brief' (this issue only)")
    ap.add_argument("--hero", help="masthead photo at an https address")
    ap.add_argument("--no-hero", action="store_true")
    ap.add_argument("--link-url", help="where the link copy is published (https). The email gets a button to it")
    ap.add_argument("--no-link", action="store_true")
    ap.add_argument("--seller-greeting", help="the line above the brief, for example \"Hi Pat and Sam,\"")
    ap.add_argument("--no-greeting", action="store_true")
    ap.add_argument("--no-market", action="store_true")
    ap.add_argument("--no-marketing", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--no-previews", action="store_true")
    ap.add_argument("--no-probe", action="store_true", help="skip the phone layout check in Edge")
    ap.add_argument("--waive", action="append", default=[], metavar="RULE=REASON", help="passed to the checks, only on the operator's say-so")
    ap.add_argument("--allow-name", action="append", default=[], help="a full name the page may carry, for example a team member")
    ap.add_argument("--allow-term", action="append", default=[], help="a word from the health, family and money list the page may carry")
    ap.add_argument("--allow-synthetic", action="store_true", help="tests only: let the synthetic test listing through the checks")
    ap.add_argument("--replace-sent", action="store_true", help="replace an issue already recorded as sent to the seller")
    argv = list(sys.argv[1:] if argv is None else argv)
    a = ap.parse_args(argv)
    # the same command without the sheet: what to run again after a stop (the sheet is already in raw.json by then)
    a.again, skip = [], 0
    for x in argv:
        if skip:
            skip -= 1
        elif x in ("--sheet", "--as-of", "--sheet-kind"):
            skip = 1
        elif not x.startswith(("--sheet=", "--as-of=", "--sheet-kind=")):
            a.again.append(x)
    try:
        return run(a)
    except SystemExit as e:
        if isinstance(e.code, int):
            return e.code
        return stop(EXIT_INPUT, str(e), nxt="fix what the line above names and run this again.")


if __name__ == "__main__":
    sys.exit(main())
