# Delivery: the Gmail draft, the link copy, the PDF, filing

How a checked issue reaches Graeham's drafts folder, how it is replaced after a correction, and what happens when it went out. `<scripts>` and `<listing>` mean the same folders as in SKILL.md. Everything here was learned putting the first two real issues into drafts on Oct 13, 2026.

## Contents

1. Who it goes to, and the one hard rule
2. What the Gmail connector does to HTML, and the Gmail-safe copy
3. Making the draft
4. Replacing the body after a correction
5. When the connector refuses, and routes that do not work
6. The PDF
7. The link copy
8. When it went out, and filing

## 1. Who it goes to, and the one hard rule

One unsent Gmail draft per issue:

| Field | Value |
|---|---|
| To | The seller's email address. Ask the operator, or take it from a status email thread to the seller that was read this session. Never write it in any file |
| CC | Adrian, client care: graehamwattsclientcare@gmail.com |
| Subject | Exactly the line `run_issue.py` printed after READY: `Weekly Seller Report No. NN · <Month D, YYYY> - <address>` (a middle dot, then a plain hyphen before the address). `draft_check.subject_line` makes it |
| Body | `<listing>\issues\NN\email_gmail.html`, never `email.html` |

**Never send.** Never call `send_message`, never send through any other route. Graeham reads the draft and sends it himself, because it speaks to his client in his name. The workspace rule that internal reports are sent, not drafted, does not apply here: this report goes to a client. Never touch an earlier draft unless asked.

## 2. What the Gmail connector does to HTML, and the Gmail-safe copy

The connector's `create_draft` and `update_draft` clean the HTML they are handed. Seen on both drafts on Oct 13, 2026:

- every `<img>` is removed, so the photo is simply gone
- a `tel:` link becomes `javascript:void(0)`, a dead link, so a call button stops working
- every `background:` style declaration is removed; a table cell keeps its `bgcolor` attribute
- the `<head>`, `<style>` blocks, Outlook conditional comments, and `role`, `class`, `scope` and `data-*` attributes are removed
- a website link becomes a `google.com/url` redirect with a short-lived timestamp, and a domain written as plain text (such as graehamwatts.com in the footer) is turned into such a redirect
- visible text, numbers, tables and `mailto:` links come through intact

So every build also writes `email_gmail.html`, drawn by the renderer from the same data at the same fit level (`sr_render.render_email_pair`), never edited by hand afterwards:

- no photo row
- the phone (footer and call button) and the website are plain text with the look of the links they replace; the email address stays a `mailto:` link
- the website, and any other web address in running text, is split so no single run of text holds a whole address: each dot and the part after it sits in its own span with an explicit color (`htmlkit.no_autolink`). Nothing can turn it into a link, and a reader sees and copies exactly the domain. A zero-width character was rejected because it travels into a copied address
- every status chip sits on a one-cell table whose cell carries `bgcolor`
- `<meta name="sr:copy" content="gmail">` marks it for the checks

The ship gate checks this copy as an email and also for images, `tel:` and web links, backgrounds on anything but a table cell, a linkable address, the 95,000 byte ceiling, and that its words are exactly the words of `email.html` (`data-contract.md`, section 7). If `email_gmail.html` is missing from an issue folder, the issue was built before the copy existed: rebuild it with the run line before drafting. Never draft from `email.html`, and never make a Gmail-safe copy by hand.

The phone pictures in `issues\NN\previews\` show `email.html`, photo included. To see exactly what goes into the draft, render the copy into the scratchpad: `python "<scripts>\render_previews.py" "<listing>\issues\NN\email_gmail.html" --name gmail --out "<scratch>\previews"`.

## 3. Making the draft

1. **Read the file into the call exactly.** `email_gmail.html` runs 70 to 95 KB. Read it in line ranges, in order, and join them into `htmlBody` with nothing added, dropped, reflowed or "fixed". A missing line changes what the seller reads and fails the check in step 3.
2. **Create it:** `create_draft` with `to` [the seller], `cc` ["graehamwattsclientcare@gmail.com"], `subject` as printed, `htmlBody` the file's text. No `body`, no attachments unless the PDF was asked for (section 6). Keep the draft id it returns.
3. **Read it back and check it.** `get_draft` with that `draftId` and `messageFormat` `RAW`. The result is large, so the harness saves it to a file and gives you the path. Then:
   ```
   python "<scripts>\draft_check.py" --issue "<listing>\issues\NN" --draft "<the saved get_draft result>"
   ```
   It finds the HTML part (raw MIME, base64url MIME inside JSON, or the decoded part), compares the words with `email_gmail.html` after the clean-up rules in section 2, and fails on an image or a `javascript:void` link (either means `email.html` went in), on words that differ, and on a subject that is not the printed line. It reports whether there is a CC. Exit 0 matches, 1 does not, 2 an input could not be read. On 1, read what it names, fix the cause (usually a dropped line range), replace the body (section 4) and check again.
4. **Record it:**
   ```
   python "<scripts>\snapshot_issue.py" record --folder "<listing>" --issue <N> --gmail-draft-id <id>
   ```
5. **Hand it over** in chat (SKILL.md, step 9): which report, that it is in drafts unsent, To and CC, the "Worth a glance before you send" lines, and an invitation to say what to change.

## 4. Replacing the body after a correction

After a correction and a rebuild, put the new `email_gmail.html` into the **same draft**: `update_draft` with `draftId` and `htmlBody` only. Fields left out keep their values, so To, CC and subject stay. Two traps:

- `update_draft` drops attachments unless they are given again in the same call. If the PDF was attached, attach it again.
- Never create a second draft for the same issue unless the first is gone; two drafts invite sending the wrong one.

Then `get_draft` RAW and `draft_check.py` again, and tell the operator in one or two plain sentences what changed.

## 5. When the connector refuses, and routes that do not work

- **A refused update.** On Oct 13 an `update_draft` that only added the CC was refused by the permission classifier as unrequested, though Graeham had asked for it. When an update is refused, do not retry it in another form and do not look for another way in. Tell Graeham in one plain line what the draft still needs ("Please add Adrian on CC before you send" or "The draft still has last night's wording about Jordan; the corrected copy is ready if you want me to try again"), and leave it with him. `draft_check.py` prints the CC line for exactly this case.
- **Routes that failed and are not tried:** signing in to Gmail from a script with the stored app password (the session's permission rules block it as a real-world transaction), and the Chrome extension's browser (it may be on another computer, so it cannot reach a local file). Do not open the in-app browser to compose a draft either. If the connector is unavailable, stop and say so; the files in the issue folder are ready for whenever it is back.

## 6. The PDF

`report.pdf` is printed from the print layout, carries no offer details and keeps the photo. Attach it only when the operator asks. Before attaching, check it is this issue's real file: the path is `<listing>\issues\NN\report.pdf` and its SHA256 equals the one in that folder's `manifest.json`. Attach it through `create_draft` or `update_draft` `attachments` (`content` base64, `filename` named for the address and date, `mimeType` application/pdf), and give it again on every later `update_draft`.

## 7. The link copy

`link.html` is the forwardable copy: everyone in full, no offer price, terms or offer agent, marked noindex. Publish it only on Graeham's word, in this order:

1. Run the brand tripwire (`python scripts\verify_brand_identity.py` in the Skills repo) and put the page in the `online-content` repo under `emails/<YYYY-MM-DD>-<address-slug>-seller-report.html`, by the direct git push in the workspace CLAUDE.md. It is a public site, which is why the link copy carries no offer details.
2. Open the published address and check the real content is there, not a 404 or a shell page.
3. Rebuild with `--link-url <that https address>` so the email gets the "Open the complete record" button, and record it: `snapshot_issue.py record --folder "<listing>" --issue <N> --link-url <url> --link-published-on <YYYY-MM-DD>`.

In the Gmail-safe copy that button stays a web link and opens through Gmail's redirect; the gate notes it as a warning, not a failure. Without a published copy, the email offers to send the complete record on request.

## 8. When it went out, and filing

When the operator says the issue went to the seller:

```
python "<scripts>\snapshot_issue.py" record --folder "<listing>" --issue <N> --sent-on <YYYY-MM-DD>
```

The issue folder is then the record of what the seller received. A later rebuild for the same Monday stops with exit 3 and needs `--replace-sent`, on Graeham's word only.

Filing: the issue folder is the record. A final PDF goes into the listing's folder under `Documents\Listings\Active listings\<address>\` only when Graeham asks for it there, named like the files around it ("<address> Seller report MM DD YY.pdf"). A report that must not be used any more moves to a `Superseded` subfolder after comparing hashes, never deleted. Drafts and working files never go in his folders.
