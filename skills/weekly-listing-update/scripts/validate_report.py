#!/usr/bin/env python3
"""validate_report.py — pre-send gate for the weekly seller status report.

Why this exists
---------------
Until 2026-08-13 `templates/weekly-status-report.html` was not a template: it was a
finished report for 1908 Cooley Ave with that seller's address, price, MLS number and
offer hardcoded, while SKILL.md instructed substituting ~32 variables that did not
exist in the file. Following the documented process literally would have sent one
seller's numbers to a different seller. This report goes to a real seller every week,
so "remember to check" is not a control. This script is the control.

It checks three things and exits non-zero on any failure:

  1. NO UNSUBSTITUTED PLACEHOLDERS  — any surviving {{VAR}} means a field was missed.
  2. NO PRIOR-SELLER BLEED          — the address/seller in the file must be the ONE
                                      you declared, and known prior-seller markers
                                      must be absent.
  3. NO AI TELLS / BRAND ERRORS     — em-dashes (banned in Graeham's published output),
                                      the blocklisted DRE, and the retired brokerage.

Usage
-----
    python scripts/validate_report.py <report.html> --address "742 Example St" \
        --seller "Dana"

Exit codes: 0 = safe to send, 1 = blocking problem found.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

# Markers from reports that have previously shipped. If a new listing's report is
# built by copying an older one, these are what bleeds through. Add to this list
# whenever a report goes out for a new property.
PRIOR_SELLER_MARKERS = [
    "1908 Cooley", "Cooley Ave", "Cooley Avenue", "ML82027334", "SHPCO",
]

BANNED_BRAND = [
    ("02015066", "blocklisted DRE (correct is 01466876)"),
    ("Intero Real Estate", "retired brokerage (now Compass)"),
    ("Berkshire Hathaway", "Intero's affiliate tagline; Compass is not one"),
    ("Martin Team", "stale team name (correct is The Boyenga Team)"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report", help="path to the finished report HTML")
    ap.add_argument("--address", required=True,
                    help="the property address this report is FOR, e.g. '742 Example St'")
    ap.add_argument("--seller", help="seller first name this report is addressed to")
    a = ap.parse_args()

    path = Path(a.report)
    if not path.exists():
        print(f"FAIL: report not found: {path}")
        return 1
    html = path.read_text(encoding="utf-8", errors="replace")

    # Strip HTML comments before checking: the template's own explanatory comment
    # legitimately names the old property, and is never rendered to the seller.
    visible = re.sub(r"<!--.*?-->", "", html, flags=re.S)

    failures: list[str] = []

    # 1 — unsubstituted placeholders
    leftover = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", visible)))
    if leftover:
        failures.append(
            f"{len(leftover)} unsubstituted placeholder(s) still in the report:\n      "
            + ", ".join(leftover)
        )

    # 2 — prior-seller bleed
    bled = [m for m in PRIOR_SELLER_MARKERS
            if m.lower() in visible.lower() and m.lower() not in a.address.lower()]
    if bled:
        failures.append(
            "prior-seller data found in a report for a different property: "
            + ", ".join(repr(b) for b in bled)
            + "\n      This means two sellers' reports have been mixed. Do NOT send."
        )

    # the declared address must actually appear
    if a.address.lower() not in visible.lower():
        failures.append(
            f"the declared address {a.address!r} does not appear in the report at all. "
            "Either the wrong file was passed or the address was never substituted."
        )
    if a.seller and a.seller.lower() not in visible.lower():
        failures.append(f"seller name {a.seller!r} does not appear in the report.")

    # 3 — AI tells and brand errors
    if "—" in visible or "&mdash;" in visible:
        n = visible.count("—") + visible.count("&mdash;")
        failures.append(
            f"{n} em-dash(es) in client-visible text. Em-dashes are banned in Graeham's "
            "published output (the single biggest 'written by AI' tell). Use commas, "
            "periods, colons, or 'to' for ranges."
        )
    for needle, why in BANNED_BRAND:
        if needle.lower() in visible.lower():
            failures.append(f"blocked brand value {needle!r} present: {why}")

    if failures:
        print(f"BLOCKED: {len(failures)} problem(s) in {path.name}\n")
        for i, f in enumerate(failures, 1):
            print(f"  {i}. {f}")
        print("\nDo not send this report until every item above is resolved.")
        return 1

    print(f"PASS: {path.name} is clean.")
    print(f"      Address verified: {a.address}")
    if a.seller:
        print(f"      Addressed to: {a.seller}")
    print("      No leftover placeholders, no prior-seller bleed, no em-dashes, brand OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
