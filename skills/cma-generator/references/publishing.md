# Publishing a CMA

**One method: direct git push.** Composio was retired workspace-wide 2026-06-09. The GitHub-API-via-browser method described in the old `github_publishing.md` is also retired: it existed because an older sandbox blocked `api.github.com`, which no longer applies. Do not use `run_composio_tool`, `GITHUB_COMMIT_MULTIPLE_FILES`, or `javascript_tool` fetch calls to publish.

---

## Canonical path

**`Online Content/cma/CMA_[street_number]_[street_name].html`** — singular `cma`, underscores for spaces, special characters stripped.

Live URL: `https://graehamwatts.github.io/online-content/cma/CMA_[address].html`

> **Historical note:** `cmas/` and `cma-reports/` also exist in the repo and hold ~100 older reports from when files were triple-mirrored. That mirroring drifted (57 / 53 / 49 files as of 2026-08-13) and is **discontinued**. Do not write to them. They stay in place because their URLs went out in real client emails and deleting them would break those links. `cma/` is the only path for new work.

---

## The push

The Documents folder is a Windows mount where git sometimes cannot unlink its own lock files. The robust pattern is to clone fresh into the sandbox, copy the file in, and push from there:

```bash
# 1. Fresh clone (or reuse an existing sandbox clone and pull)
rm -rf /tmp/oc-push && git clone --quiet https://github.com/Graehamwatts/online-content.git /tmp/oc-push

# 2. Copy the report in
cp "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Online Content/cma/CMA_[address].html" /tmp/oc-push/cma/

# 3. Brand check BEFORE pushing (never skip)
cd /tmp/oc-push && python "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Skills/scripts/verify_brand_identity.py" --path .

# 4. Commit and push
git add cma/CMA_[address].html
git commit -q -m "CMA: [address]"
PAT=$(tr -d '[:space:]' < "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Online Content/github-token.txt")
git push "https://${PAT}@github.com/Graehamwatts/online-content.git" HEAD:main
```

**Never print the PAT.**

Simple `git add / commit / push` directly from the Documents clone also works and is fine when the tree is clean. Use the sandbox-clone pattern when locks or stale-index problems appear.

---

## After pushing

1. **Verify the live URL returns 200** before sending anything to a client. Pages rebuilds in roughly 1-2 minutes; poll rather than assuming.
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" https://graehamwatts.github.io/online-content/cma/CMA_[address].html
   ```
   Add `?v=2` on first load if an old version is cached.
2. **Sync the Documents clone** so it does not drift behind:
   ```bash
   cd "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Online Content" && git add -A && git pull --quiet origin main
   ```
   Note: a `SessionEnd` hook auto-commits and pushes both repos, so a file may already be committed by the time you look. Check `git log` before assuming a push failed.

---

## Brand validation

- **Repo-wide, before any push:** `python scripts/verify_brand_identity.py --path .` from the repo root. Audits everything against the blocklist in `identity.json`.
- **Single output file:** `python skills/content-creation-engine/scripts/verify_output_brand.py <file>` — exit 2 means a blocked value is present. Never ship on exit 2.

Also grep the file itself before publishing:
- Zero em-dashes (`—`, `&mdash;`, ` -- `)
- DRE shows only `01466876`
- Brokerage matches `identity.json` (Compass / The Boyenga Team), never "Intero"

---

## If the file looks truncated or corrupted after a Write

The Cowork VM mount can serve a stale byte-length view of a file immediately after Write/Edit touches it (truncated tail, or NULL padding).

1. **Never run a read-modify-write "fix" through the mount right after Write/Edit.** A script that reads the stale view and writes it back will clobber the good host-side file with the truncated copy.
2. **Recovery:** write the full content to a **fresh filename** via the Write tool (fresh files read clean), verify in bash (size, ends with `</html>`, `node --check` on inline script, zero `\x00`, zero em-dashes, correct DRE), copy the fresh file over the canonical name, publish from it, then fetch the published bytes back from GitHub and assert an exact match.
