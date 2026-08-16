# Publishing the Compensation Package

**One method: direct git push.** Same pattern as `cma-generator/references/publishing.md`. Composio is retired workspace-wide; do not reach for it.

---

## Canonical paths

```
Online Content/compensation/Compensation-Package-Standard.html
Online Content/compensation/Compensation-Package-Premium.html
```

Live URLs:
```
https://graehamwatts.github.io/online-content/compensation/Compensation-Package-Standard.html
https://graehamwatts.github.io/online-content/compensation/Compensation-Package-Premium.html
```

Unlike CMAs, these two filenames are fixed and evergreen, there is no per-address naming. Update them in place; do not create dated or address-specific copies unless Graeham explicitly asks for a one-off custom version.

---

## The push

The Documents folder is a Windows mount where git sometimes cannot unlink its own lock files. The robust pattern is to clone fresh into the sandbox, copy the files in, and push from there:

```bash
# 1. Fresh clone
rm -rf /tmp/oc-push && git clone --quiet https://github.com/Graehamwatts/online-content.git /tmp/oc-push

# 2. Copy both variants in
mkdir -p /tmp/oc-push/compensation
cp "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Online Content/compensation/Compensation-Package-Standard.html" /tmp/oc-push/compensation/
cp "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Online Content/compensation/Compensation-Package-Premium.html" /tmp/oc-push/compensation/

# 3. Brand check BEFORE pushing (never skip)
cd /tmp/oc-push && python "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Skills/scripts/verify_brand_identity.py" --path .

# 4. Commit and push
git add compensation/Compensation-Package-Standard.html compensation/Compensation-Package-Premium.html
git commit -q -m "Compensation package: [what changed]"
PAT=$(tr -d '[:space:]' < "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Online Content/github-token.txt")
git push "https://${PAT}@github.com/Graehamwatts/online-content.git" HEAD:main
```

**Never print the PAT.**

Simple `git add / commit / push` directly from the Documents clone also works and is fine when the tree is clean. Use the sandbox-clone pattern when locks or stale-index problems appear.

---

## After pushing

1. **Verify both live URLs return 200** before sending anything to a client:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" https://graehamwatts.github.io/online-content/compensation/Compensation-Package-Standard.html
   curl -s -o /dev/null -w "%{http_code}\n" https://graehamwatts.github.io/online-content/compensation/Compensation-Package-Premium.html
   ```
   Pages rebuild in roughly 1-2 minutes; poll rather than assuming. Add `?v=2` on first load if an old version is cached.
2. **Sync the Documents clone**:
   ```bash
   cd "/c/Users/Graeham Watts/Documents/Skills LLMS/Claude/Online Content" && git add -A && git pull --quiet origin main
   ```
   A `SessionEnd` hook auto-commits and pushes both repos, so a file may already be committed by the time you look. Check `git log` before assuming a push failed.

---

## Brand validation

- **Repo-wide, before any push:** `python scripts/verify_brand_identity.py --path .` from the Skills repo root.
- Also grep each file directly before publishing:
  - Zero `—` (em dash)
  - Zero leftover `{{` placeholders
  - DRE shows only `01466876`
  - Brokerage matches `identity.json` (Compass / The Boyenga Team), never "Intero"
  - The negotiability disclaimer line is present in the footer
