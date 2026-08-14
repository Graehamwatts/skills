#!/usr/bin/env python3
"""verify_references.py - fail on instructions that point at things which do not exist.

WHY THIS EXISTS
---------------
The brand tripwire catches bad VALUES (a wrong DRE, a retired brokerage). Nothing
caught bad REFERENCES, so these all survived in live instructions:

  - Composio was retired workspace-wide 2026-06-09, yet a scheduled task still called
    GITHUB_GET_REPOSITORY_CONTENT every Monday and fell back to re-sending stale output.
    One skill even instructed "COMPOSIO GITHUB TOOLS - never via local git", forbidding
    the correct method.
  - mcp__Claude_in_Chrome__ (wrong case) in 4 skills. Hard-fails on invocation.
  - Routes to skills that have never existed: video-editor, ghl-crm-audit,
    cinematic-video-engine, pipeline-dashboard.
  - references/*.md and scripts/*.py paths naming files that are not on disk.

An agent reading these does the confident thing and fails, or worse, silently skips
the step. This script makes that class of rot fail at push time instead.

USAGE
    python scripts/verify_references.py [--json] [--skill NAME]

EXIT CODES
    0  no broken references
    1  broken references found
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

# Directories whose contents are generated or historical; not live instructions.
SKIP_PARTS = {"outputs", "__pycache__", "node_modules", ".venv", "graphify-out", "library", ".git"}

# Things that are gone. Referencing them operationally is always a bug.
RETIRED = {
    "run_composio_tool":            "Composio retired workspace-wide 2026-06-09; use direct git",
    "GITHUB_COMMIT_MULTIPLE_FILES": "Composio retired; use direct git push",
    "GITHUB_GET_REPOSITORY_CONTENT":"Composio retired; read the local clone instead",
    "COMPOSIO_REMOTE_WORKBENCH":    "Composio retired",
    "mcp__Claude_in_Chrome__":      "wrong case; correct prefix is mcp__claude-in-chrome__",
    "mcp__cowork__":                "no such MCP server in this environment",
    "mcp__workspace__":             "no such MCP server in this environment",
    "ask_user_input_v0":            "no such tool; ask in plain text instead",
    r"C:\\Users\\Admin":            "no such user on this machine; it is C:\\Users\\Graeham Watts",
}

# Skill names confirmed by audit to have NEVER existed in this repo. Listed explicitly
# because the contextual heuristic below is deliberately conservative (to keep the
# false-positive rate near zero), and that conservatism would otherwise let these slip
# when they appear in a table cell or prose without the word "skill" nearby.
PHANTOM_SKILLS = {
    "ghl-crm-audit":          "never existed; meta-ads routes to it twice",
    "pipeline-dashboard":     "never existed; named in shared-references/integrations.md",
    "video-editor":           "never existed; use video-creator",
    "cinematic-video-engine": "never existed; concept-forge ends every path here",
}

# Skills retired with a documented replacement.
DEPRECATED_SKILLS = {
    "html-email":                   "publish HTML to online-content via direct git",
    "github-skill-sync":            "direct git push",
    "video-script-creation-engine": "content-creation-engine",
    "social-media-analyzer":        "content-calendar",
    "video-prompt-builder":         "cinematic-hooks",
}

# Files that legitimately NAME dead things in order to warn about them.
EXEMPT_FILES = {
    "CLAUDE.md", "AGENTS.md", "README.md",
    "skill-deprecation-protocol.md", "dre-leak-incident-log.md",
    "architecture-decision.md", "identity.json",
    "verify_references.py", "verify_brand_identity.py",
    "dashboard-manifest.json", "validate_dashboard.py",
}

# A line that is *explaining* a dead thing rather than instructing its use.
TOMBSTONE = re.compile(
    r"deprecat|retired|do not use|never use|no longer|replaced by|instead of|"
    r"was renamed|absorbed|historical|does not exist|never existed|is void|"
    r"formerly|old approach|superseded", re.I)


# Scheduled tasks live OUTSIDE this repo but are the highest-risk instructions in the
# system: they run unattended, so a broken reference fails with nobody watching. The
# Composio call that broke the Monday content build for two months lived here, not in
# skills/. Scan it whenever it is present.
SCHEDULED = REPO.parent / "Scheduled"


def live_files():
    roots = [SKILLS] + ([SCHEDULED] if SCHEDULED.is_dir() else [])
    for root in roots:
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".md", ".json", ".py"}:
                continue
            if SKIP_PARTS & {q.name for q in p.parents}:
                continue
            if p.name in EXEMPT_FILES:
                continue
            # Correspondence and briefs are documents ABOUT the system, not
            # instructions TO it. A support email describing the zombie-skill
            # problem legitimately names dead skills; flagging it is noise.
            if re.search(r"EMAIL|BRIEF|-for-|POST-?MORTEM|AUDIT|REPORT|NOTES?$",
                         p.stem, re.I):
                continue
            yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skill", help="check only this skill")
    a = ap.parse_args()

    existing = {d.name for d in SKILLS.iterdir() if d.is_dir()}
    findings: list[dict] = []

    for path in live_files():
        try:
            rel = path.relative_to(REPO).as_posix()
        except ValueError:
            rel = "Scheduled/" + path.relative_to(SCHEDULED).as_posix()
        if a.skill and f"skills/{a.skill}/" not in rel:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for i, line in enumerate(lines, 1):
            if TOMBSTONE.search(line):
                continue  # explaining, not instructing

            for token, why in RETIRED.items():
                if re.search(token if token.startswith("C:") else re.escape(token), line):
                    findings.append({"file": rel, "line": i, "kind": "retired",
                                     "ref": token.replace("\\\\", "\\"), "why": why})

            for dead, repl in DEPRECATED_SKILLS.items():
                if re.search(rf"`{re.escape(dead)}`", line):
                    findings.append({"file": rel, "line": i, "kind": "deprecated-skill",
                                     "ref": dead, "why": f"retired; use {repl}"})

            for phantom, why in PHANTOM_SKILLS.items():
                if re.search(rf"`{re.escape(phantom)}`|skills/{re.escape(phantom)}\b", line):
                    findings.append({"file": rel, "line": i, "kind": "missing-skill",
                                     "ref": phantom, "why": why})

            # Backticked skill-like name used in a routing context.
            for m in re.finditer(r"`([a-z][a-z0-9]+(?:-[a-z0-9]+){1,3})`", line):
                name = m.group(1)
                if name in existing or name in DEPRECATED_SKILLS:
                    continue
                # Require an EXPLICIT skill signal. A bare "use the `x-y`" was far too
                # loose: it matched scheduled-task names, output modes, and worked
                # examples, producing enough noise to make the whole check ignorable.
                if not re.search(
                    rf"`{re.escape(name)}`\s*skill|skill\s*`{re.escape(name)}`|"
                    rf"skills/{re.escape(name)}\b|read the\s*`?{re.escape(name)}`?\s*skill|"
                    rf"hands? off to\s*`{re.escape(name)}`|route to\s*`{re.escape(name)}`",
                    line, re.I):
                    continue
                # Scheduled-task names, doc examples, and placeholders are not skills.
                if re.search(r"\btask\b|cron|schedul|example|e\.g\.|placeholder|such as|"
                             r"\bmode\b|variant", line, re.I):
                    continue
                if (SKILLS / name).exists():
                    continue
                findings.append({"file": rel, "line": i, "kind": "missing-skill",
                                 "ref": name, "why": "no such skill directory"})

            # Real client data inside a TEMPLATE or REFERENCE file. Scoped to those
            # directories deliberately: a client's name belongs in their own report,
            # never in the thing every future report is built from. Two cma-generator
            # "templates" were finished client CMAs with zero placeholders, published
            # publicly, and seeding every new report with the original client's
            # identity. weekly-listing-update had the same bug with a seller's data.
            if re.search(r"/(references|templates)/", "/" + rel):
                for pat, kind in (
                    (r"Prepared for\s+[A-Z][a-z]+\s+[A-Z][a-z]+", "client name"),
                    (r"\bAPN[:\s]*\d{3}-\d{3}-\d{3}\b",           "parcel number"),
                    (r"\bML8\d{7}\b",                              "MLS number"),
                ):
                    m = re.search(pat, line)
                    # A placeholder in the same position is the correct state.
                    if m and "{{" not in m.group(0):
                        findings.append({"file": rel, "line": i, "kind": "client-data",
                                         "ref": m.group(0)[:48],
                                         "why": f"real {kind} in a template/reference; "
                                                f"use a {{{{PLACEHOLDER}}}} instead"})

            # Relative pointers to references/ and scripts/ inside the same skill.
            for m in re.finditer(r"`((?:references|scripts|templates|assets)/[A-Za-z0-9_./-]+\.(?:md|py|json|html))`", line):
                target = m.group(1)
                skill_root = path
                while skill_root.parent != SKILLS and skill_root.parent != skill_root:
                    skill_root = skill_root.parent
                # Legitimate homes: this skill, the repo root, or any sibling skill
                # (cross-skill pointers like `scripts/verify_brand_identity.py` are real).
                found = ((skill_root / target).exists()
                         or (REPO / target).exists()
                         or any((d / target).exists() for d in SKILLS.iterdir() if d.is_dir()))
                if not found:
                    findings.append({"file": rel, "line": i, "kind": "missing-file",
                                     "ref": target, "why": "path does not exist in this skill"})

    if a.json:
        print(json.dumps(findings, indent=2)); return 1 if findings else 0

    print(f"Reference integrity check - {len(list(live_files()))} live instruction files\n")
    if not findings:
        print("PASS: every referenced skill, tool, and file exists.")
        return 0

    by_kind: dict[str, list] = {}
    for f in findings:
        by_kind.setdefault(f["kind"], []).append(f)

    print(f"FAIL: {len(findings)} broken reference(s).\n")
    labels = {"retired": "RETIRED TOOL / PATH (will fail at runtime)",
              "deprecated-skill": "DEPRECATED SKILL (has a replacement)",
              "missing-skill": "SKILL DOES NOT EXIST",
              "missing-file": "FILE DOES NOT EXIST",
              "client-data": "REAL CLIENT DATA IN A TEMPLATE (privacy)"}
    for kind, items in sorted(by_kind.items()):
        print(f"  [{labels.get(kind, kind)}]  {len(items)}")
        seen = set()
        for f in items:
            key = (f["ref"], f["file"])
            if key in seen:
                continue
            seen.add(key)
            print(f"    {f['file']}:{f['line']}")
            print(f"      -> {f['ref']}  ({f['why']})")
        print()
    print("Fix each, or add the file to EXEMPT_FILES if it legitimately names a dead")
    print("thing in order to warn about it (a tombstone, not an instruction).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
