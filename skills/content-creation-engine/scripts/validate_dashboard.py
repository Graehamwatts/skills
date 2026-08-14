#!/usr/bin/env python3
"""validate_dashboard.py - PASS/FAIL check for a built weekly content dashboard.

WHY THIS EXISTS
---------------
The dashboard lost 72% of its content between 2026-05-21 (216KB) and 2026-06-22
(60KB), shedding features one at a time. The chart brush vanished. Three features
that had been REQUIRED BY WRITTEN RULE since June 2026 (cut topics, override
capture, conflict panel) were never built even once. Nobody caught any of it until
the published artifacts were diffed side by side.

Prose rules did not prevent that, and neither did three rule files each claiming to
be canonical. So correctness is no longer a matter of anyone remembering: a build
either satisfies references/dashboard-manifest.json or it fails here.

USAGE
    python scripts/validate_dashboard.py <built-dashboard.html> [--manifest PATH]

EXIT CODES
    0  every required element present
    1  something is missing (each miss is named, with why it matters)
    2  could not run (bad path, unreadable manifest)
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE.parent / "references" / "dashboard-manifest.json"


def check(html: str, sig: str, is_regex: bool) -> bool:
    if is_regex:
        return re.search(sig, html, re.I) is not None
    return sig.lower() in html.lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dashboard")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument(
        "--layout-only",
        action="store_true",
        help="Judge STRUCTURE only (tabs/sections/features/brand), skipping the "
             "content-volume checks. For design previews built with placeholder copy. "
             "NEVER use this on a real weekly build: the volume checks are what catch "
             "silent truncation, which is the failure this tool exists for.",
    )
    a = ap.parse_args()

    path = Path(a.dashboard)
    if not path.exists():
        print(f"FAIL: no such file: {path}")
        return 2
    try:
        m = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: cannot read manifest {a.manifest}: {e}")
        return 2

    html = path.read_text(encoding="utf-8", errors="replace")
    size_kb = len(html.encode("utf-8")) // 1024
    misses: list[tuple[str, str, str]] = []   # (category, name, why)
    notes: list[str] = []

    # --- tabs ---
    for tab in m.get("required_tabs", []):
        if not check(html, tab["signature"], False):
            misses.append(("TAB", tab["label"], "tab is missing from the page"))

    # --- sections ---
    for sec in m.get("required_sections", []):
        if not check(html, sec["signature"], False):
            misses.append(("SECTION", sec["key"], sec.get("why", "")))

    # --- features (the regression-prone ones) ---
    for feat in m.get("required_features", []):
        if not check(html, feat["signature"], feat.get("regex", False)):
            misses.append(("FEATURE", feat["key"], feat.get("why", "")))

    # --- content minimums ---
    mins = m.get("content_minimums", {})
    skipped: list[str] = []
    for kind, label in (("video_topics", "Video Content"), ("blog_topics", "Blog Content")):
        if a.layout_only:
            skipped.append(kind); continue
        want = mins.get(kind)
        if not want:
            continue
        # Count per-topic blocks near the relevant tab heading.
        found = len(re.findall(r'class="[^"]*topic-card|data-topic=', html, re.I))
        if found and found < want:
            misses.append(("CONTENT", kind,
                           f"found ~{found} topic blocks, manifest requires {want}"))

    min_kb = mins.get("min_file_kb")
    if a.layout_only:
        skipped.append("min_file_kb")
    elif min_kb and size_kb < min_kb:
        misses.append(("SIZE", f"{size_kb}KB",
                       f"below the {min_kb}KB floor. High-water mark was 216KB; the last "
                       f"decayed build was 60KB. Small size means silent truncation even "
                       f"when signatures match."))

    # --- brand ---
    brand = m.get("brand", {})
    for bad in brand.get("forbidden", []):
        if bad.lower() in html.lower():
            misses.append(("BRAND", bad, "blocked brand value present in output"))
    dre = brand.get("required_dre")
    if dre and dre not in html:
        notes.append(f"note: DRE {dre} not found (fine if this page carries no contact strip)")

    # --- report ---
    print(f"Dashboard validation: {path.name}  ({size_kb}KB)")
    print(f"  manifest: {Path(a.manifest).name}")
    print()
    if a.layout_only:
        print("  MODE: --layout-only  (structure judged; content-volume checks SKIPPED)")
        print(f"  skipped: {', '.join(skipped)}")
        print()
    if not misses:
        if a.layout_only:
            print("LAYOUT PASS: structure is complete. This is NOT a passing weekly build.")
            print("             Re-run without --layout-only once real content is in.")
        else:
            print("PASS: every required element present.")
        for n in notes:
            print(f"  {n}")
        return 0

    print(f"FAIL: {len(misses)} required element(s) missing.\n")
    by_cat: dict[str, list] = {}
    for cat, name, why in misses:
        by_cat.setdefault(cat, []).append((name, why))
    for cat, items in by_cat.items():
        print(f"  [{cat}]")
        for name, why in items:
            print(f"    - {name}")
            if why:
                print(f"        why it matters: {why}")
        print()
    print("Do not publish until this passes. If a miss is intentional, change the")
    print("manifest deliberately, in its own commit, so the decision is recorded.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
