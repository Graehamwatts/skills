#!/usr/bin/env python3
"""
scan_secrets.py -- Secret Leak Scanner: git-tracked secret and config-hygiene sweep.

Scans every file GIT ACTUALLY TRACKS in a repo (never gitignored junk, never
.git internals) for credential-shaped strings, and separately confirms that
known token filenames are gitignored and NOT tracked. This is a read-only
detector, not a fixer -- it reports, a human decides.

Usage:
    python scripts/scan_secrets.py [--history] [--walk] [--json] <path> [<path> ...]

    --history  also scan EVERY blob reachable from ANY ref (all branches, tags,
               PR refs in a --mirror clone). A key that was committed and later
               deleted is still public if the repo is public; HEAD-only scans
               miss it. Office files (.docx/.xlsx/.pptx) are unzipped and their
               XML text is scanned too.
    --walk     accept plain folders that are not git repos (e.g. an Obsidian
               vault) and scan every text-like file under them.
    --json     print machine-readable JSON instead of the text report.

Output never contains a full secret. Each match shows a mask (first 6 / last 4
for values of 20+ chars, last 4 only for 12-19 chars, nothing for shorter),
the value length, and fp = first 12 hex chars of sha256(value), so a finding
can be matched against a rotation worksheet without anyone seeing the value.

Exit code 0 = clean, 1 = findings, 2 = a repo path was invalid.

Why this exists:
    identity.json's blocklist (verify_brand_identity.py) catches stale BRAND
    strings (wrong DRE, old brokerage). It was never meant to catch, and does
    not catch, actual leaked credentials -- an API key, a password, a token
    accidentally committed instead of gitignored. This is that other check.

History:
    2026-09-27  added provider-shaped patterns (Supadata sd_, Anthropic sk-ant-,
                OpenAI sk-proj-, Perplexity pplx-, xAI xai-, Blotato blt_,
                Google GOCSPX-/1//0/ya29./AQ., Cloudflare cfut_/tunnel tokens,
                GitHub github_pat_, GHL pit-, ElevenLabs/HeyGen sk_, Telegram
                and Discord bot tokens, and more) after a Supadata key sat in the
                public skills repo undetected because only generic shapes existed.
                Added --history, --walk, --json, value fingerprints, and
                placeholder detection on the matched value itself.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
# (label, compiled pattern, kind). Patterns are deliberately specific-shaped
# (real key formats) over generic ("password") to keep false positives low
# enough that a human will actually read the output instead of tuning it out.
#
# If a pattern has a named group "v", that group is the secret value used for
# the mask and fingerprint; otherwise the whole match is the value.
#
# kind:
#   "secret"  -> HIGH unless the value or its surroundings look like a placeholder
#   "public"  -> always LOW (public-by-design identifiers, e.g. Mapbox pk.)
#   "generic" -> keyword-driven catch-all; value must also pass looks_random()
PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # --- cloud / infra -------------------------------------------------------
    ("AWS Access Key ID", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "secret"),
    ("AWS Secret Access Key (assignment)", re.compile(
        r"(?i)aws_secret_access_key['\"]?[ \t]*[:=][ \t]*['\"]?(?P<v>[A-Za-z0-9/+=]{40})"), "secret"),
    ("Google API Key (AIza)", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "secret"),
    ("Google AI Studio auth key (AQ.)", re.compile(r"\bAQ\.[A-Za-z0-9_\-]{40,}"), "secret"),
    ("Google OAuth client secret (GOCSPX-)", re.compile(r"\bGOCSPX-[A-Za-z0-9_\-]{20,}"), "secret"),
    ("Google OAuth refresh token (1//0)", re.compile(r"(?<![A-Za-z0-9])1//0[A-Za-z0-9_\-]{30,}"), "secret"),
    ("Google OAuth access token (ya29.)", re.compile(r"\bya29\.[A-Za-z0-9_\-]{30,}"), "secret"),
    ("Cloudflare API token (cfut_/cfat_)", re.compile(r"\bcf[a-z]t_[A-Za-z0-9_\-]{30,}"), "secret"),
    ("Cloudflare tunnel token (eyJhIjoi...)", re.compile(r"\beyJhIjoi[A-Za-z0-9+/]{60,}={0,2}"), "secret"),
    ("Supabase secret key (sb_secret_)", re.compile(r"\bsb_secret_[A-Za-z0-9_\-]{20,}"), "secret"),
    ("Supabase publishable key (public by design)", re.compile(r"\bsb_publishable_[A-Za-z0-9_\-]{20,}"), "public"),
    ("JSON Web Token (check role: anon is public, service_role is secret)", re.compile(
        r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{20,}"), "secret"),
    ("Database URL with inline password", re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:@\s/'\"]+:(?P<v>[^@\s/'\"]{6,})@"), "secret"),
    ("PEM Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP |ENCRYPTED )?PRIVATE KEY-----"), "secret"),
    # --- source control ------------------------------------------------------
    ("GitHub token (ghp_/gho_/ghu_/ghs_/ghr_)", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"), "secret"),
    ("GitHub fine-grained PAT (github_pat_)", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}"), "secret"),
    # --- AI model providers --------------------------------------------------
    ("Anthropic key/token (sk-ant-)", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{32,}"), "secret"),
    ("OpenAI project/service key (sk-proj-/sk-svcacct-/sk-admin-)", re.compile(
        r"\bsk-(?:proj|svcacct|admin)-[A-Za-z0-9_\-]{40,}"), "secret"),
    ("OpenAI legacy key (T3BlbkFJ)", re.compile(r"\bsk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}\b"), "secret"),
    ("Tagged sk- key (sk-kimi-, sk-or-v1-, sk-ws-, ...)", re.compile(
        r"\bsk-(?!ant-|proj-|svcacct-|admin-)[a-z0-9]{2,8}-(?:v\d-)?[A-Za-z0-9_\-]{30,}"), "secret"),
    ("Plain sk- key (DeepSeek, Moonshot, LiteLLM, ...)", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"), "secret"),
    ("Perplexity key (pplx-)", re.compile(r"\bpplx-[A-Za-z0-9]{40,}"), "secret"),
    ("xAI key (xai-)", re.compile(r"\bxai-[A-Za-z0-9]{40,}"), "secret"),
    ("Groq key (gsk_)", re.compile(r"\bgsk_[A-Za-z0-9]{40,}"), "secret"),
    ("Hugging Face token (hf_)", re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"), "secret"),
    ("Replicate token (r8_)", re.compile(r"\br8_[A-Za-z0-9]{30,}\b"), "secret"),
    ("LangSmith key (lsv2_)", re.compile(r"\blsv2_(?:pt|sk)_[a-f0-9]{32}_[a-f0-9]{10}\b"), "secret"),
    ("Z.ai / Zhipu key (hex32.alnum16)", re.compile(r"\b[a-f0-9]{32}\.[A-Za-z0-9]{16}\b"), "secret"),
    # --- media / voice / content tools ---------------------------------------
    ("ElevenLabs key (sk_ + 48 hex)", re.compile(r"\bsk_[a-f0-9]{48}\b"), "secret"),
    ("HeyGen key (sk_V2_)", re.compile(r"\bsk_V\d_[A-Za-z0-9_]{30,}"), "secret"),
    ("Supadata key (sd_)", re.compile(r"\bsd_[A-Za-z0-9]{24,}\b"), "secret"),
    ("Blotato key (blt_)", re.compile(r"\bblt_[A-Za-z0-9+/_\-]{20,}={0,2}"), "secret"),
    ("Composio key (ak_)", re.compile(r"\bak_(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{16,}\b"), "secret"),
    ("Apify token (apify_api_)", re.compile(r"\bapify_api_[A-Za-z0-9]{30,}"), "secret"),
    ("Firecrawl key (fc-)", re.compile(r"\bfc-[a-f0-9]{32}\b"), "secret"),
    ("Tavily key (tvly-)", re.compile(r"\btvly-[A-Za-z0-9_\-]{20,}"), "secret"),
    ("ScrapeGraph key (sgai-)", re.compile(r"\bsgai-[A-Za-z0-9\-]{30,}"), "secret"),
    ("Jina key (jina_)", re.compile(r"\bjina_[A-Za-z0-9]{40,}"), "secret"),
    ("RapidAPI key", re.compile(r"\b[a-f0-9]{10}msh[a-f0-9]{15}p[a-f0-9]{6}jsn[a-f0-9]{12}\b"), "secret"),
    ("Mapbox secret token (sk.eyJ)", re.compile(r"\bsk\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]{10,}"), "secret"),
    ("Mapbox public token (pk.eyJ, public by design)", re.compile(r"\bpk\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]{10,}"), "public"),
    # --- CRM / messaging / email ---------------------------------------------
    ("GoHighLevel Private Integration Token (pit-)", re.compile(
        r"\bpit-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b"), "secret"),
    ("Telegram bot token", re.compile(r"(?<![A-Za-z0-9])\d{8,10}:AA[A-Za-z0-9_\-]{33}(?![A-Za-z0-9_\-])"), "secret"),
    ("Discord bot token", re.compile(
        r"(?<![A-Za-z0-9_\-])[MNO][A-Za-z0-9_\-]{23,27}\.[A-Za-z0-9_\-]{6}\.[A-Za-z0-9_\-]{27,40}(?![A-Za-z0-9_\-])"), "secret"),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,48}"), "secret"),
    ("SendGrid key (SG.)", re.compile(r"\bSG\.[A-Za-z0-9_\-]{20,24}\.[A-Za-z0-9_\-]{40,45}\b"), "secret"),
    ("Resend key (re_)", re.compile(r"\bre_[A-Za-z0-9]{8}_[A-Za-z0-9]{20,}\b"), "secret"),
    ("Nylas key (nyk_)", re.compile(r"\bnyk_[A-Za-z0-9_]{30,}"), "secret"),
    ("Mailchimp key", re.compile(r"\b[a-f0-9]{32}-us\d{1,2}\b"), "secret"),
    ("Notion token (ntn_/secret_)", re.compile(r"\b(?:ntn_[A-Za-z0-9]{40,}|secret_[A-Za-z0-9]{43})\b"), "secret"),
    ("Airtable PAT", re.compile(r"\bpat[A-Za-z0-9]{14}\.[a-f0-9]{64}\b"), "secret"),
    ("Linear key (lin_api_)", re.compile(r"\blin_api_[A-Za-z0-9]{40}\b"), "secret"),
    # --- payments / finance --------------------------------------------------
    ("Stripe live secret/restricted key", re.compile(r"\b(?:sk|rk)_live_[0-9a-zA-Z]{16,}"), "secret"),
    ("Plaid access token", re.compile(
        r"\baccess-(?:sandbox|development|production)-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b"), "secret"),
    # --- generic, keyword-driven ---------------------------------------------
    ("Generic Bearer Token", re.compile(r"Bearer\s+(?P<v>[A-Za-z0-9\-\._~\+/]{24,}={0,2})"), "generic"),
    ("Generic api_key/secret/token assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|apikey|client[_-]?secret|access[_-]?token|auth[_-]?token|refresh[_-]?token"
        r"|secret[_-]?key|private[_-]?key|bearer[_-]?token)['\"]?[ \t]*[:=][ \t]*['\"](?P<v>[A-Za-z0-9_\-\.\+/=]{16,})['\"]"), "generic"),
    ("API key header (x-api-key / apikey / x-goog-api-key)", re.compile(
        r"(?i)\b(?:x-api-key|x-goog-api-key|api-key|apikey)[ \t]*:[ \t]*['\"]?(?P<v>[A-Za-z0-9_\-\.]{20,})"), "generic"),
    ("Env-style secret assignment (UPPER_CASE name)", re.compile(
        r"\b[A-Z][A-Z0-9_]*(?:API_KEY|APIKEY|SECRET|TOKEN|PASSWORD|PASSWD|_PAT|PRIVATE_KEY|ACCESS_KEY|AUTH_KEY)[A-Z0-9_]*"
        r"[ \t]*[:=][ \t]*['\"]?(?P<v>[A-Za-z0-9_\-\.\+/=!@#%^&*~]{16,})"), "generic"),
    ("Hardcoded password assignment", re.compile(
        r"(?i)\b(?:password|passwd|pwd)['\"]?[ \t]*[:=][ \t]*['\"](?P<v>[^'\"\s]{6,})['\"]"), "generic"),
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
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".pdf", ".zip", ".ico", ".woff", ".woff2", ".ttf",
            ".otf", ".mp4", ".mov", ".m4a", ".mp3", ".wav", ".webm", ".gz", ".tgz", ".7z", ".exe", ".dll", ".so",
            ".dylib", ".bin", ".pyc", ".sqlite", ".db"}
# Office formats are zip files of XML: unzip and scan the text instead of skipping.
OFFICE_EXT = {".docx", ".xlsx", ".pptx", ".docm", ".xlsm"}
MAX_BLOB_BYTES = 25 * 1024 * 1024

# Substrings that make a match a known-safe false positive worth silencing
# from the headline count (still listed, just flagged LOW).
BENIGN_HINTS = [
    "example", "placeholder", "your-", "your_", "<your", "xxxx", "sk_live_XXXX", "AKIAIOSFODNN7EXAMPLE",
    "read at send time", "read at runtime", "read at push time", "gitignored", "dummy", "redacted",
    "changeme", "fake",
]
# Markers that, inside the matched VALUE itself, mean it is not a real secret.
PLACEHOLDER_VALUE_HINTS = [
    "xxxx", "your", "example", "placeholder", "dummy", "fake", "redacted", "changeme", "sample", "replace",
    "<", ">", "...", "****", "${", "{{", "process.env", "os.environ", "getenv", "password", "test-", "test_",
    "123456789", "abcdefgh", "0000000000",
]


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def mask(value: str) -> str:
    if len(value) >= 20:
        return value[:6] + "..." + value[-4:]
    if len(value) >= 12:
        return "..." + value[-4:]
    return "..."


def looks_placeholder(value: str) -> bool:
    low = value.lower()
    if any(h in low for h in PLACEHOLDER_VALUE_HINTS):
        return True
    if len(set(value)) < 6:
        return True
    return False


def looks_random(value: str) -> bool:
    """Keyword-driven matches must look like a credential, not a word or code path."""
    if len(value) < 16:
        return False
    # "TOKEN= NEXT_VAR=0": the capture ran into the next assignment
    if "=" in value.rstrip("=") or re.match(r"[A-Z][A-Z0-9_]{3,}(?:=|$)", value):
        return False
    if not re.search(r"\d", value) or not re.search(r"[A-Za-z]", value):
        return False
    if re.fullmatch(r"[a-z_\.]+\d?", value):
        return False
    # dotted code references like self.config.api_key or module.attr
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+", value):
        return False
    return len(set(value)) >= 8


TEST_PATH = re.compile(r"(^|[/\\])(tests?|__tests__|fixtures?|spec|e2e)[/\\]|(^|[/\\])test_[^/\\]*$|\.(test|spec)\.[a-z]+$", re.I)


def scan_text(text: str, path: str = "") -> list[dict]:
    """Return matches in text: label, value metadata, line, severity. Never the raw value.
    Keyword-driven (generic) matches inside test files are LOW: they are fixtures far more
    often than live credentials. Provider-shaped matches stay HIGH everywhere."""
    in_test = bool(path and TEST_PATH.search(path))
    out = []
    seen_spans = []
    for label, pattern, kind in PATTERNS:
        for m in pattern.finditer(text):
            value = m.group("v") if "v" in pattern.groupindex and m.group("v") else m.group(0)
            value = value.strip("'\"")
            if kind == "generic" and not looks_random(value):
                continue
            start, end = (m.start("v"), m.end("v")) if "v" in pattern.groupindex and m.group("v") else (m.start(), m.end())
            # a generic pattern that overlaps a provider-shaped match is a duplicate
            if kind == "generic" and any(s <= start < e or s < end <= e for s, e in seen_spans):
                continue
            seen_spans.append((start, end))
            ctx = text[max(0, m.start() - 60):m.end() + 60].lower()
            if kind == "public" or (kind == "generic" and in_test):
                severity = "LOW"
            elif looks_placeholder(value) or any(h.lower() in ctx for h in BENIGN_HINTS):
                severity = "LOW"
            else:
                severity = "HIGH"
            out.append({
                "label": label,
                "severity": severity,
                "line": text.count("\n", 0, m.start()) + 1,
                "masked": mask(value),
                "last4": value[-4:] if len(value) >= 12 else "",
                "length": len(value),
                "fp": fingerprint(value),
            })
    return out


def office_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            parts = []
            for name in z.namelist():
                if name.endswith(".xml") or name.endswith(".rels"):
                    raw = z.read(name).decode("utf-8", errors="ignore")
                    parts.append(re.sub(r"<[^>]+>", " ", raw))
            return "\n".join(parts)
    except Exception:
        return ""


def bytes_to_text(data: bytes, path: str) -> str | None:
    suffix = Path(path).suffix.lower()
    if suffix in OFFICE_EXT:
        return office_text(data)
    if suffix in SKIP_EXT:
        return None
    if b"\x00" in data[:8000]:
        return None
    return data.decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Working-tree scan (tracked files only)
# ---------------------------------------------------------------------------
def git_tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo_root, capture_output=True
    )
    if result.returncode != 0:
        return []
    names = result.stdout.decode("utf-8", errors="replace").split("\0")
    return [repo_root / n for n in names if n.strip()]


def walk_files(root: Path) -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", ".venv", "__pycache__", ".trash"}]
        for fn in filenames:
            files.append(Path(dirpath) / fn)
    return files


def scan_repo(repo_root: Path, is_git: bool = True) -> dict:
    findings = []
    tracked = git_tracked_files(repo_root) if is_git else walk_files(repo_root)

    # 1. Pattern scan over tracked, non-binary files.
    for f in tracked:
        if f.suffix.lower() in SKIP_EXT or not f.is_file():
            continue
        try:
            if f.stat().st_size > MAX_BLOB_BYTES:
                continue
            text = bytes_to_text(f.read_bytes(), f.name)
        except Exception:
            continue
        if not text:
            continue
        for hit in scan_text(text, str(f)):
            hit.update({"type": "PATTERN_MATCH", "file": str(f.relative_to(repo_root))})
            findings.append(hit)

    if is_git:
        # 2. Sensitive filenames that ARE tracked (should be gitignored instead).
        for f in tracked:
            # committed templates (.env.example, example.env, .env.sample) are expected
            if re.search(r"(example|sample|template|\.dist$)", f.name, re.I):
                continue
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

        # 3. .gitignore sanity: a repo with no .gitignore at all is a standing risk.
        gitignore_path = repo_root / ".gitignore"
        if not gitignore_path.exists():
            findings.append({
                "type": "NO_GITIGNORE",
                "severity": "MEDIUM",
                "label": "No .gitignore found in repo at all (expected to exclude *token*.txt, *.env, *password*.txt)",
                "file": ".gitignore",
                "line": None,
                "masked": None,
            })

    return {
        "repo": str(repo_root),
        "mode": "tracked" if is_git else "walk",
        "tracked_file_count": len(tracked),
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Full-history scan (every blob reachable from every ref)
# ---------------------------------------------------------------------------
def iter_history_blobs(repo_root: Path):
    """Yield (blob_sha, path, text) for every text-like blob reachable from any ref."""
    rl = subprocess.run(["git", "rev-list", "--all", "--objects"], cwd=repo_root, capture_output=True)
    paths: dict[str, str] = {}
    for line in rl.stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[1]:
            paths.setdefault(parts[0], parts[1])
    if not paths:
        return
    check = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=repo_root, input="\n".join(paths).encode(), capture_output=True,
    )
    wanted = []
    for line in check.stdout.decode().splitlines():
        sha, typ, size = line.split(" ")
        if typ != "blob" or int(size) > MAX_BLOB_BYTES:
            continue
        suffix = Path(paths[sha]).suffix.lower()
        if suffix in SKIP_EXT:
            continue
        wanted.append(sha)
    if not wanted:
        return
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=repo_root,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    import threading

    def feed():
        for sha in wanted:
            proc.stdin.write((sha + "\n").encode())
        proc.stdin.close()

    threading.Thread(target=feed, daemon=True).start()
    for _ in wanted:
        header = proc.stdout.readline().decode().strip().split(" ")
        if len(header) < 3:
            break
        sha, _typ, size = header[0], header[1], int(header[2])
        data = proc.stdout.read(size)
        proc.stdout.read(1)  # trailing newline
        text = bytes_to_text(data, paths[sha])
        if text:
            yield sha, paths[sha], text
    proc.wait()


def commits_for_blob(repo_root: Path, blob_sha: str, limit: int = 3) -> list[str]:
    r = subprocess.run(
        ["git", "log", "--all", "--reverse", "--format=%h %ad", "--date=short", f"--find-object={blob_sha}"],
        cwd=repo_root, capture_output=True,
    )
    lines = [l for l in r.stdout.decode("utf-8", errors="replace").splitlines() if l.strip()]
    return lines[:limit] + ([f"... +{len(lines) - limit} more"] if len(lines) > limit else [])


def head_blob_shas(repo_root: Path, ref: str = "HEAD") -> set[str]:
    r = subprocess.run(["git", "ls-tree", "-r", ref], cwd=repo_root, capture_output=True)
    shas = set()
    for line in r.stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1] == "blob":
            shas.add(parts[2])
    return shas


def ref_tip_blobs(repo_root: Path, max_refs: int = 100) -> dict[str, set[str]]:
    """Blob set at the tip of every branch, tag and PR ref. A secret removed from the
    default branch can still sit at the tip of an old branch, tag or PR head."""
    r = subprocess.run(["git", "for-each-ref", "--format=%(refname)"], cwd=repo_root, capture_output=True)
    refs = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()][:max_refs]
    return {ref: head_blob_shas(repo_root, ref) for ref in refs}


def scan_history(repo_root: Path) -> dict:
    by_fp: dict[str, dict] = {}
    blob_count = 0
    for sha, path, text in iter_history_blobs(repo_root):
        blob_count += 1
        for hit in scan_text(text, path):
            entry = by_fp.setdefault(hit["fp"], {**hit, "blobs": []})
            if hit["severity"] == "HIGH":
                entry["severity"] = "HIGH"
            entry["blobs"].append({"blob": sha, "path": path, "line": hit["line"]})
    head = head_blob_shas(repo_root)
    tips = ref_tip_blobs(repo_root) if by_fp else {}
    findings = []
    for fp, e in by_fp.items():
        e["in_head"] = any(b["blob"] in head for b in e["blobs"])
        e["refs_at_tip"] = sorted(ref for ref, blobs in tips.items() if any(b["blob"] in blobs for b in e["blobs"]))
        e["paths"] = sorted({b["path"] for b in e["blobs"]})
        commits: set[str] = set()
        for b in {b["blob"] for b in e["blobs"]}.__iter__():
            commits.update(c for c in commits_for_blob(repo_root, b, limit=50) if not c.startswith("..."))
            if len(commits) > 50:
                break
        ordered = sorted(commits, key=lambda c: c.split(" ")[-1])
        e["first_commit"] = ordered[0] if ordered else ""
        e["commits"] = ordered[:6] + ([f"... +{len(ordered) - 6} more"] if len(ordered) > 6 else [])
        e["blob_count"] = len(e["blobs"])
        e.pop("blobs")
        e.pop("line", None)
        e["type"] = "HISTORY_MATCH"
        findings.append(e)
    findings.sort(key=lambda x: (x["severity"] != "HIGH", x["label"]))
    return {"repo": str(repo_root), "mode": "history", "tracked_file_count": blob_count, "findings": findings}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def is_git_repo(p: Path) -> bool:
    if (p / ".git").exists():
        return True
    r = subprocess.run(["git", "rev-parse", "--is-bare-repository"], cwd=p, capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == "true"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = sys.argv[1:]
    history = "--history" in args
    walk = "--walk" in args
    as_json = "--json" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print("Usage: python scan_secrets.py [--history] [--walk] [--json] <path> [<path> ...]")
        return 2

    any_findings = False
    any_invalid = False
    reports = []
    for arg in paths:
        root = Path(arg).resolve()
        if not root.exists():
            print(f"SKIP (missing): {root}")
            any_invalid = True
            continue
        git_ok = is_git_repo(root)
        if not git_ok and not walk:
            print(f"SKIP (not a git repo; pass --walk to scan it as a plain folder): {root}")
            any_invalid = True
            continue
        if git_ok and (root / ".git").exists():
            reports.append(scan_repo(root, is_git=True))
        elif not git_ok:
            reports.append(scan_repo(root, is_git=False))
        if git_ok and history:
            reports.append(scan_history(root))

    if as_json:
        print(json.dumps(reports, indent=1))
        return 1 if any(r["findings"] for r in reports) else (2 if any_invalid else 0)

    for report in reports:
        print(f"\n=== {report['repo']} [{report['mode']}] ===")
        unit = "unique blobs" if report["mode"] == "history" else "files"
        print(f"  {unit} scanned: {report['tracked_file_count']}")
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
                if f["type"] == "HISTORY_MATCH":
                    where = "; ".join(f["paths"][:3]) + (f" (+{len(f['paths']) - 3} paths)" if len(f["paths"]) > 3 else "")
                    if f["in_head"]:
                        state = "STILL IN HEAD"
                    elif f.get("refs_at_tip"):
                        state = "removed from HEAD but still at the tip of other refs"
                    else:
                        state = "history only"
                    print(f"    - {f['label']} -- {f['masked']} len={f['length']} fp={f['fp']} [{state}]")
                    print(f"        paths: {where}")
                    if f.get("refs_at_tip"):
                        print(f"        refs whose tip still holds it: {', '.join(f['refs_at_tip'][:8])}")
                    print(f"        commits: {', '.join(f['commits'])}")
                else:
                    loc = f"{f['file']}:{f['line']}" if f.get("line") else f["file"]
                    extra = f" ({f['masked']} len={f['length']} fp={f['fp']})" if f.get("masked") else ""
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
