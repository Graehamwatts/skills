---
name: secret-leak-scanner
description: "Hunts for leaked passwords, API keys, and tokens sitting in Graeham's Skills repo, Online Content repo, PropIQ repo, and n8n workflows — the digital version of checking every drawer for a spare key left somewhere it shouldn't be. NOT a content-moderation guardrail and not the brand-name checker (that's verify_brand_identity.py, which catches stale DRE/brokerage strings, not leaked secrets). Use ANY time Graeham asks for a security scan, secret scan, credential leak check, password leak check, or asks whether the skills/PropIQ/CRM setup is leaking anything."
---

# Secret Leak Scanner

Checks Graeham's own AI tooling for the one failure mode that actually matters here: a real password, API key, or token sitting somewhere git will happily commit and GitHub will happily publish to the world. In plain terms — it looks for a spare house key someone left taped under the doormat, then tells you exactly which doormat.

This is NOT an AI "guardrail" in the usual sense (a rule that stops a model from saying or doing something). It also does not scan client-facing content for brand mistakes — that's `verify_brand_identity.py` (see Skills/CLAUDE.md), a completely separate check with a separate blocklist (wrong DRE number, old brokerage name). Run both when doing a real pre-push check; they catch different things.

## When to run this

- Whenever Graeham asks for a security scan, audit, or "is anything leaking."
- Before onboarding a new automation (n8n workflow, scheduled task, MCP connector) that will hold a real credential.
- Periodically as hygiene — there's no cron for it yet; run it by hand until one exists.
- After any session that touched `.gitignore`, added a new token file, or wired up a new integration.

## What it checks

1. **Credential-shaped strings in git-tracked files** (`scripts/scan_secrets.py`) — AWS keys, Google API keys, Slack tokens, GitHub tokens, generic `api_key=`/`password=` assignments, PEM private key headers, Stripe live keys, and the specific 16-character-in-4-groups shape of a Gmail App Password. Scans only what `git ls-files` actually tracks — gitignored junk, `.git` internals, and binaries are never touched, so this runs fast and stays low-noise.
2. **Sensitive filenames that got tracked by mistake** — if `github-token.txt`, `gmail-app-password.txt`, `propcast-token-pat.txt`, a `.pem`, or a `.env` file shows up in `git ls-files`, that's a HIGH finding regardless of its contents. The token infrastructure in this workspace depends entirely on these files staying gitignored and local-only (see the token map in the workspace root `CLAUDE.md`); a tracked one means it's already in git history, not just on disk.
3. **Missing `.gitignore` entirely** — a repo with real local secrets and no `.gitignore` at all is a standing risk even before anything leaks.
4. **n8n workflow credentials (manual step, not the script)** — when n8n is in scope, use the `mcp__n8n-mcp__n8n_list_workflows` / `n8n_get_workflow` tools to check that credential-bearing nodes reference n8n's credential store (an ID) rather than a hardcoded value pasted into a node parameter. This can't be grepped from disk because the workflows live on the n8n server, not in a local repo — it has to be read live via the n8n MCP tools each time.
5. **Overpermissive automation configs (spot-check, not automated)** — skim `.claude/settings.json`, hook scripts, and scheduled-task wrappers for things like a hook that curls to an unfamiliar domain, a `--dangerously-skip-permissions`-style flag, or a scope broader than the task needs. No pattern-matcher for this yet; it's a manual read until a real false-positive/true-positive corpus exists to build one against.

## How to run it

```bash
python scripts/scan_secrets.py "<repo root 1>" "<repo root 2>" ...
```

Pass every git repo in scope in one call — typically the Skills repo, the Online Content repo, and the local PropIQ working copy (paths are in the workspace root `CLAUDE.md` token map). Exit code 0 = clean, 1 = findings to review, 2 = a path wasn't a valid git repo.

**The script never prints a full secret.** Pattern matches are masked (first 6 / last 4 characters); a HIGH finding tells you where to go look and confirm, not what the value is. If something is confirmed real, rotate it — don't just delete the line, since it's already in git history at that point (see the DRE-leak incident log for what a buried-but-unrotated leak costs later).

## Severity and what to do with a finding

- **HIGH** — pattern genuinely looks like a live credential, or a sensitive filename is tracked. Confirm by hand, then rotate the credential and scrub git history if it's already pushed (`git filter-repo` or BFG — this is a real operation, talk to Graeham before rewriting pushed history).
- **MEDIUM** — structural gap (no `.gitignore`) rather than a live leak. Fix the gap.
- **LOW** — matched a pattern but sits next to a benign hint (the word "example," "placeholder," a comment saying the real value is read at runtime from elsewhere). Skim to confirm, usually a non-issue.

## What this explicitly does not do

- Does not touch GoHighLevel's live account settings — there's no API path in from here (see the GHL-auditing-technique memory: the PIT API is Cloudflare-banned). "Scanning the CRM" in practice means scanning the n8n workflows and local files that drive GHL automation, not GHL's own hosted config. A live GHL settings check is a manual browser pass, not this skill.
- Does not fix anything automatically. Every finding is surfaced for a human decision, same posture as the brand tripwire and everything in the PropCast Master Brain's governance model — propose, never auto-apply.
- Does not replace `verify_brand_identity.py`. Run both when doing a real pre-push check; they catch different failure classes.

## Adding a new pattern

Patterns live in `scripts/scan_secrets.py`'s `PATTERNS` list as `(label, compiled regex)` pairs. Favor a specific key SHAPE (like `AKIA[0-9A-Z]{16}`) over a generic keyword — shape-based patterns rarely false-positive, keyword-based ones (like the `password=` catch-all) will, and that's fine as long as they're still rare enough that findings get read rather than ignored.
