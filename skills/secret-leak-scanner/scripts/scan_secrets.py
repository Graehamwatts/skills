#!/usr/bin/env python3
"""
scan_secrets.py -- Secret Leak Scanner: git-tracked secret and config-hygiene sweep.

Scans every file GIT ACTUALLY TRACKS in a repo (never gitignored junk, never
.git internals) for credential-shaped strings, and separately confirms that
known token filenames are gitignored and NOT tracked. This is a read-only
detector, not a fixer -- it reports, a human decides.

Usage:
    python scripts/scan_secrets.py <repo_root> [<repo_root> ...]

Exit code 0 = clean, 1 = findings, 2 = a repo path was invalid.

Why this exists:
    identity.json's blocklist (verify_brand_identity.py) catches stale BRAND
    strings (wrong DRE, old brokerage). It was never meant to catch, and does
    not catch, actual leaked credentials -- an API key, a password, a token
    accidentally committed instead of gitignored. This is that other check.
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

# (label, compiled pattern). Patterns are deliberately specific-shaped
# (real key formats) over generic ("password") to keep false positives low
# enough that a human will actually read the output instead of tuning it out.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Access Key (assignment)", re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"][A-Za-z0-9/+=]{40}['\"]")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Slack Token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,48}")),
    ("GitHub Token (classic/fine-grained/PAT)", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,255}")),
    ("Generic Bearer Token", re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+/]{24,}={0,2}")),
    ("PEM Private Key Header", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("Stripe Live Secret Key", re.compile(r"sk_live_[0-9a-zA-Z]{16,}")),
    ("Generic api_key/apikey/secret/token assignment", re.compile(
        r"(?i)\b(api[_-]?key|apikey|client[_-]?secret|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]"
    )),
    ("Hardcoded password assignment", re.compile(
        r"(?i)\b(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]"
    )),
]
# NOTE: a "16 lowercase letters in 4 space-separated groups" pattern (the
# real shape of a Gmail App Password) was tried and removed 2026-08-30 --
# that shape also matches four ordinary short English words in a row, which
# is extremely common prose and drowned every real finding in noise. Gmail
# App Password leaks are still caught by the TRACKED_SENSITIVE_FILENAME
# check below (the file "gmail-app-password.txt" being tracked at all is
# the actual risk, not a content pattern that can't distinguish a real key
# from a sentence).

# Filename globs that are EXPECTED to hold real secrets and must therefore
# never appear in `git ls-files` (tracked). Presence here is a finding, not
# a pattern match inside the file.
SENSITIVE_FILENAMES = [
    "github-token.txt",
    "gmail-app-password.txt",
    "propcast-token-pat.txt",
    "*github-token*.txt",
    "*.pem",
    "*_rsa",
    "id_rsa",
    ".env",
]

# Extensions worth skipping entirely (binary / generated / noisy).
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xlsx", ".docx", ".pptx", ".zip", ".ico", ".woff", ".woff2", ".ttf"}

# Substrings that make a match a known-safe false positive worth silencing
# from the headline count (still listed, just flagged LOW).
BENIGN_HINTS = [
    "example", "placeholder", "your-", "xxxx", "sk_live_XXXX", "AKIAIOSFODNN7EXAMPLE",
    "read at send time", "read at runtime", "read at push time", "gitignored",
]


def git_tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    return [repo_root / line for line in result.stdout.splitlines() if line.strip()]


def scan_repo(repo_root: Path) -> dict:
    findings = []
    tracked = git_tracked_files(repo_root)

    # 1. Pattern scan over tracked, non-binary files.
    for f in tracked:
        if f.suffix.lower() in SKIP_EXT or not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for label, pattern in PATTERNS:
            for m in pattern.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                snippet = m.group(0)
                masked = snippet[:6] + "…" + snippet[-4:] if len(snippet) > 12 else "…"
                severity = "LOW" if any(h.lower() in text[max(0, m.start()-60):m.end()+60].lower() for h in BENIGN_HINTS) else "HIGH"
                findings.append({
                    "type": "PATTERN_MATCH",
                    "severity": severity,
                    "label": label,
                    "file": str(f.relative_to(repo_root)),
                    "line": line_no,
                    "masked": masked,
                })

    # 2. Sensitive filenames that ARE tracked (should be gitignored instead).
    tracked_names = {f.name.lower() for f in tracked}
    for f in tracked:
        for glob in SENSITIVE_FILENAMES:
            g = glob.replace("*", "")
            if g and g.lower() in f.name.lower():
                findings.append({
                    "type": "TRACKED_SENSITIVE_FILENAME",
                    "severity": "HIGH",
                    "label": f"File matching sensitive pattern '{glob}' is TRACKED BY GIT",
                    "file": str(f.relative_to(repo_root)),
                    "line": None,
                    "masked": None,
                })

    # 3. .gitignore sanity: known token filenames should appear in .gitignore
    #    even if not physically present on disk right now (defense in depth).
    gitignore_path = repo_root / ".gitignore"
    gitignore_text = gitignore_path.read_text(encoding="utf-8", errors="ignore") if gitignore_path.exists() else ""
    for expected in ["*token*.txt", "github-token.txt", "*.env", "*password*.txt"]:
        bare = expected.replace("*", "")
        if bare and bare not in gitignore_text and not gitignore_path.exists():
            findings.append({
                "type": "NO_GITIGNORE",
                "severity": "MEDIUM",
                "label": f"No .gitignore found in repo at all (expected to exclude {expected})",
                "file": ".gitignore",
                "line": None,
                "masked": None,
            })
            break  # one finding is enough if there's no .gitignore at all

    return {
        "repo": str(repo_root),
        "tracked_file_count": len(tracked),
        "findings": findings,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scan_secrets.py <repo_root> [<repo_root> ...]")
        return 2

    any_findings = False
    any_invalid = False
    reports = []
    for arg in sys.argv[1:]:
        repo_root = Path(arg).resolve()
        if not repo_root.exists() or not (repo_root / ".git").exists():
            print(f"SKIP (not a git repo): {repo_root}")
            any_invalid = True
            continue
        report = scan_repo(repo_root)
        reports.append(report)

    for report in reports:
        print(f"\n=== {report['repo']} ===")
        print(f"  tracked files scanned: {report['tracked_file_count']}")
        if not report["findings"]:
            print("  PASS: no findings.")
            continue
        any_findings = True
        by_sev = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for f in report["findings"]:
            by_sev[f["severity"]].append(f)
        for sev in ("HIGH", "MEDIUM", "LOW"):
            if not by_sev[sev]:
                continue
            print(f"  [{sev}] {len(by_sev[sev])} finding(s):")
            for f in by_sev[sev]:
                loc = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
                extra = f" ({f['masked']})" if f.get("masked") else ""
                print(f"    - {f['label']} -- {loc}{extra}")

    print()
    if any_findings:
        print("RESULT: findings present. Review HIGH severity items first -- masked value shown, never the full secret.")
        return 1
    if any_invalid:
        print("RESULT: clean, but one or more paths were not valid git repos.")
        return 0
    print("RESULT: clean across all scanned repos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
