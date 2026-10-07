# Email, links, Drive and filing

## The email (draft only)

About 400 words of plain prose, no dashes, no ad dollar amounts, no placeholder lines (Graeham sends drafts exactly as they are). Short factual paragraphs in this order:

1. The PDF is attached, the property page link, and "We've added everything to a Google Drive link for you."
2. Where you are: days on market against the comparison group, with the same denominators as the PDF.
3. What buyers are saying: tour and agent counts, the agents' feedback as reported, the next follow up.
4. The ads: what is switched on (with the status wording from SKILL.md), what is waiting on review and approval, what has not launched.
5. Only if the seller has a real decision to make (a creative direction, the AI staging disclosure): one short paragraph asking for it. Drop the paragraph otherwise.
6. Close with the next call time.

Rules: use only the real report's facts. Numbers from a SAMPLE never appear in a seller email, and the attachment is checked first: hash against the real build, metadata title, and a text search for "Sample report" (SKILL.md rule 8). Do not claim a call or conversation you cannot source ("as you asked on our last call"). Address the seller as "you" and never narrate the research conversation with Graeham. Run the narrative through the humanizer skill, then scan for every dash like character (em, en, minus, figure dash, horizontal bar) before saving.

## Making the draft in Gmail

The Gmail connector rewrites URLs into google.com/url redirects, drops attachments when a draft is updated, and detaches reply threads, so links and the PDF are added by hand in the Gmail compose window through the Chrome extension.

1. Create the draft with the connector (`create_draft`), body only, to the seller with the client care address on cc.
2. In Chrome, reload Gmail on the draft's URL and expand the compose window.
3. Wrap each anchor phrase ("the property page", "Google Drive link") in an `<a>` with a JS Range, dispatch an input event, and wait about 10 seconds for autosave. Clicking "Save & close" through the DOM forces a save when the tab is hidden.
4. Attach the PDF last: `file_upload` on the hidden file input, with the full long path (the 8.3 short path is rejected) and a fresh `find` ref after any DOM change.
5. Verify with `get_draft` (body and links) and `list_drafts` with `has:attachment`. `get_message` cannot read drafts.
6. Leave it unsent. Do not touch earlier drafts.

If the Chrome tab is hidden, screenshots time out. Use DOM clicks, not coordinate clicks.

## The property page

Before the PDF or email links to a landing page, open it and check for Box links (replace with the Drive link), a retired tagline or any em dash, "REALTOR" without the registered mark, and stale price or status text. Report what you find to Graeham. Edits to a hosted page are his call unless he says to fix them.

## The Drive folder

Copy the creative library into a Google Drive folder named "<address> Content", with a YouTube or cuts subfolder if the library has one. Share it "anyone with the link", viewer only (Graeham's choice on the first report). Verify the file count and byte sizes against the source, and open the link signed out. Chrome file upload is capped at about 10 MB a call, so the first copy used a temporary n8n workflow (download from the Box shared link, then the Google Drive node), deleted afterwards; ask before creating one. Box shared links also download with curl from `https://app.box.com/index.php?rm=box_download_shared_file&shared_name=<hash>&file_id=f_<id>`, and the file list comes from the shared page's `/app-api/enduserapp/shared-folder?folderID=<id>` with the header `X-Box-EndUser-API: sharedName=<hash>`. Keep Box links out of every PDF, email and landing page.

## Filing

- Final PDF: the listing's folder under `Documents\Listings\Active listings\<address>\`, named like its neighbors (for example "<address> Seller report MM DD YY.pdf").
- A report that must not be used any more goes to a `Superseded` subfolder with a note in the name. Compare file hashes before moving, and do not delete.
- Worked examples and builders go under `Documents\Skills LLMS\Claude\reports\`. A sample never goes in a listing folder.
- PDF metadata: title "<address> - Marketing Update - <date>", author "Graeham Watts | Compass".
