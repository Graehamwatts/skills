# RETIRED — offer analyses are NOT published (2026-08-13)

**This file previously taught two things that are both now wrong.** It is kept only as a
tombstone so nothing silently follows the old instructions.

## What it used to say, and why each part is retired

1. **"Publish the offer HTML to `online-content/offers/Offer_[address].html`."**
   Retired on Graeham's instruction, 2026-08-13. That is a **public** GitHub Pages path
   whose filename comes straight from the property address, so anyone who knew the
   address could guess the URL and read every competing buyer's price, terms, financing,
   and contingencies. Offer analyses are confidential and stay private.

2. **"Push via the GitHub Contents API using `javascript_tool` from the browser."**
   Retired workspace-wide. That method existed only because an older Cowork sandbox
   blocked `api.github.com`; that constraint no longer applies. Composio
   (`run_composio_tool`, `GITHUB_COMMIT_MULTIPLE_FILES`) is likewise retired (2026-06-09).
   Where publishing IS still appropriate (CMAs, newsletters), the one correct method is a
   direct `git push` — see `cma-generator/references/publishing.md`.

   This file also referenced a token at `outputs/.claude-credentials/github-pat.txt`,
   which does not exist. The real token lives in `github-token.txt` inside each clone.

## What to do instead

**Do not publish. Deliver privately.** Write the HTML to the skill's gitignored
`offer-analyzer/outputs/` folder and send it as an email **attachment** to Graeham and
Adrian. The full rule, including the exact send command, is in
[`mode-1-offer-analysis.md`](mode-1-offer-analysis.md) under
"NEVER PUBLISH OFFER ANALYSES PUBLICLY".

Do not work around this with an obfuscated filename. An unguessable public URL is still
public; it is not access control.
