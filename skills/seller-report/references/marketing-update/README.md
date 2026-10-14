# The seller marketing update PDF (10 pages)

A separate deliverable from the weekly report, built only when Graeham asks for it by name ("the marketing update", "the seller marketing report", "the campaign report"). It shows the seller, with real numbers, how the listing compares with similar sales and what the marketing has and has not done. First built Oct 6, 2026; Graeham called it excellent and asked that it become the pattern. Carried over whole from the `seller-marketing-report` skill.

## Contents

1. The worked example and the builder
2. Workflow
3. The pages
4. The 13 page full campaign report
5. Checks that must pass
6. The real-file check
7. The email with the PDF attached
8. The property page and the Drive folder
9. Filing
10. Done means

## 1. The worked example and the builder

Everything lives in `C:\Users\Graeham Watts\Documents\Skills LLMS\Claude\reports\seller-marketing-update-example-2026-10-06\` (outside the repo, because it holds a real listing):

- `README.md`: read first. (It still names the old skill as its home; this file replaces that.)
- the REAL PDF (verified data, went to the seller) and the SAMPLE PDF (internal only, simulated results), with an assumptions note for the sample
- `builder\`: the Python and PowerShell that produced both, which rebuild from that folder as it sits. The pieces: `build_final.py` (constants, asserts and the page functions `p1` to `p10`), `market_data.py` (closed sales, live listings, group stats; the code asserts every printed number), `sources_v2.md` (the facts as read), `assets\` and `prep_assets.py`, `build2.ps1` and `render.ps1` (Edge headless print), `finalize_pdf.py` (metadata), `overflow_check.py`, `final_checks.py`, `check_mls.py` (reads saved MLSListings pages), `redfin_days_on_market.js`, and for the sample `build_sample.py`, `build_sample.ps1`, `sim_data.py`, `make_assumptions.py`, `sample_checks.py`, `overflow_check2.py`.

The builder is a copy-and-edit job: the layout, styles and checks are reusable, the copy and data are per listing. Parameterizing it (one listing config plus page text blocks) was planned and is not done.

## 2. Workflow

1. **Scope.** Collect the subject facts (address, MLS number, list date, full price history, beds, baths, square feet, HOA, status), the comparison group, the activity record, the marketing status with exact times, the creative library, the property page address and the search demand. Sources and methods: `../market-and-marketing.md`. Use the weekly report's own numbers for the activity page, so the two documents never disagree.
2. **Days on market.** Rebuild each closed sale's days from its listing history in Pacific time, with every unit's type and city checked (`../market-and-marketing.md`, section 3).
3. **Creative to Drive** (section 8), only with Graeham's go-ahead.
4. **Build.** Copy `builder\` into the session scratchpad; the example folder stays the reference. Replace `market_data.py`, the constants and asserts at the top of `build_final.py`, the page functions `p1` to `p10`, the images in `assets\` and the expected strings in `final_checks.py`. Run `build2.ps1 -Name <name> -DriveUrl <Drive root> -CutsUrl <cuts folder>`, then `overflow_check.py` and `final_checks.py`, and look at every page picture and the contact sheet it writes.
5. **Independent review.** Send the final text and the source pack to a fresh subagent with none of your reasoning. The first report took three passes; the first two missed a mobile home counted as a condo and a house figure built from the wrong group. Fix, rebuild, recheck.
6. **File** (section 9) and **draft the email** (section 7).
7. **Report back** in plain prose: what changed, what is still unverified, what Graeham has to decide.

## 3. The pages

Letter pages (8.5 by 11 in), one HTML section per page, printed to PDF with Edge headless. Montserrat headings, Source Sans 3 body. Each page has the brand strip (name in gold caps, REALTOR with the registered mark), a running header with the address and page title, and a footer with the page number and "Updated <date>". Content stays above the bottom margin (747 pt of the 792 pt page). Charts are inline SVG so they survive printing.

1. **Cover.** Hero photo, address, "Marketing update", date, price and key facts, DRE and brokerage line from `identity.json`, link to the property page.
2. **Where you stand.** The headline result in one sentence (for example, day 24 against 72 days on average for the other eight sales). A bar chart of days to contract with the subject's day marked. The denominators: how many closed, how many excluded and why, average, median, range, how many were under contract by the subject's day count, and the effect of counting an excluded same-day sale as zero. One sentence on the second group and one on long-running active listings.
3. **The data behind page 2.** Every closed sale in the window (sold date, address, price, square feet, list date, contract date, days), excluded rows marked with the reason, the live competing listings, the cut by bedrooms with price per square foot against the subject, and a two line method note.
4. **What buyers are telling us.** Tours, agents on the disclosure package list, open houses, offers, and agent comments as reported, with what is pending. Same counts and the same gentle paraphrase as the weekly report.
5. **Since you listed.** A dated timeline of marketing events, true dates only.
6. **This week and next.** Channel by channel with status chips (Switched on, Prepared, On hold, Not launched), what happens before the next call, and the accounts-checked paragraph when no delivery rows exist.
7. **The first ads.** The video versions with thumbnails and one line each, plus the Drive folder link.
8. **Prepared posts.** Carousel and post previews, the AI-generated furniture and props disclosure, photo and map credits.
9. **Google Search plan.** The real volumes, prepared ad previews word for word, and a plain statement of how little searching there is when there is little.
10. **What comes next.** Next steps in sentences, the open house, the next call, links.

## 4. The 13 page full campaign report

Pages 1 to 6 as above, then: what the ads delivered, what the posts delivered, property page traffic, the creative (two pages), the Google Search plan with results, and a closing page on what was learned and what comes next. Build it for real only when platform exports exist for every number on the results pages (`../market-and-marketing.md`, section 7). Before then, the only version is the internal SAMPLE: `sample-mode.md`.

## 5. Checks that must pass

Page count; no dash characters of any kind (em, en, minus, figure dash, horizontal bar), in body, alt text, PDF metadata and email; required phrases present; banned phrases absent ("example", "illustrative", "Box", ad budget and dollar amounts, retired brokerage names, the banned openers in `cma-generator/references/report-build.md` Part 3); REALTOR with the registered mark; DRE and the Compass disclaimer from `identity.json`, the disclaimer copied verbatim even where it reads oddly; the link set equals the expected set; nothing past the bottom limit. `final_checks.py` is the model: rewrite its expected strings for each listing, because it checks the exact numbers and phrases of the example. Run the narrative through the `humanizer` skill. Never mention a buyer's disability, health, family or finances.

## 6. The real-file check

A sample was once mistaken for the real file and mailed to a seller. Before a PDF is attached to a seller email or copied into a listing folder, prove it is the real report: its metadata title does not start with SAMPLE, no page carries a "Sample report" line, and its SHA256 equals the real build's. Every number in the email body must appear in that PDF. A sample keeps its SAMPLE name, stays under `reports\`, and is never renamed to look like the real report.

## 7. The email with the PDF attached

An unsent draft only, To the seller with client care on CC, like the weekly report (`../delivery.md`, sections 1 to 5, including what the connector strips and what to do when an update is refused). About 400 words of plain prose, no dashes, no ad dollar amounts, no placeholder lines (Graeham sends drafts exactly as they are), in this order:

1. The PDF is attached, the property page link, and "We've added everything to a Google Drive link for you."
2. Where you are: days on market against the comparison group, with the same denominators as the PDF.
3. What buyers are saying: tour and agent counts, the agents' feedback as reported, the next follow-up.
4. The ads: what is switched on (status wording from `../market-and-marketing.md`, section 5), what is waiting on review, what has not launched.
5. Only if the seller has a real decision to make (a creative direction, the AI staging disclosure): one short paragraph asking for it.
6. Close with the next call time.

Use only the real report's facts. Never claim a call or conversation you cannot source, address the seller as "you", and never narrate the research with Graeham. Attach the PDF in `create_draft` `attachments` (base64), after the real-file check; give it again on any `update_draft`, which otherwise drops it. The connector turns web links into redirects: that is acceptable for the property page and the Drive link. The older method of wrapping links and uploading the PDF by hand in the Gmail compose window through the Chrome extension depended on that browser being on this computer; use it only if Graeham asks and it is. Verify with `get_draft` and `list_drafts` with `has:attachment`. Leave it unsent and do not touch earlier drafts.

## 8. The property page and the Drive folder

**The property page.** Before the PDF or email links to it, open it and check for Box links (replace with the Drive link), a retired tagline or any em dash, "REALTOR" without the registered mark, and stale price or status text. Report what you find. Edits to a hosted page are Graeham's call.

**The Drive folder.** Copy the creative library into a Google Drive folder named "<address> Content", with a YouTube or cuts subfolder if the library has one, shared "anyone with the link", viewer only (Graeham's choice on the first report). Verify the file count and sizes against the source, and open the link signed out. Writing to Drive and sharing are done only on his go-ahead. Chrome file upload is capped near 10 MB a call; the first copy used a temporary n8n workflow (Box shared link download, then the Google Drive node), deleted afterwards: ask before creating one. Box shared links also download from `https://app.box.com/index.php?rm=box_download_shared_file&shared_name=<hash>&file_id=f_<id>`, and the file list comes from the shared page's `/app-api/enduserapp/shared-folder?folderID=<id>` with the header `X-Box-EndUser-API: sharedName=<hash>`. Box links never appear in a PDF, email or landing page.

## 9. Filing

- The final PDF goes in the listing's folder under `Documents\Listings\Active listings\<address>\`, named like its neighbors (for example "<address> Seller report MM DD YY.pdf"), when Graeham asks for it to be filed.
- A report that must not be used any more goes to a `Superseded` subfolder with a note in the name. Compare hashes before moving; never delete.
- Worked examples and builders live under `Documents\Skills LLMS\Claude\reports\`. A sample never goes in a listing folder. Working files stay in the scratchpad.
- PDF metadata: title "<address> - Marketing Update - <date>", author "Graeham Watts | Compass".

## 10. Done means

- Every printed number traces to a source read this session, and the code asserts the computed ones.
- No dashes of any kind, no "example" wording, DRE only from `identity.json`, REALTOR with the registered mark, links resolve and match the expected set, nothing runs past the bottom margin.
- An independent reviewer rechecked the final text against the sources.
- The email is an unsent draft with the real PDF attached (it passed section 6) and no sample numbers anywhere, and every number in the body appears in the PDF.
- Open questions are in the reply: unconfirmed ad delivery, property page issues, disclosures.
