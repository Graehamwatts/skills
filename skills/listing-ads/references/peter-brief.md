# Briefing Peter

Peter is the editor. He cuts the videos, thumbnails, carousels and still ads, and Ellie renders and exports the finals. He signs his emails "Jason" and is the same person, so never write Jason as someone else. He works on Philippine time, 15 hours ahead of Pacific until November 1 and 16 after, and his logged day starts around 2 PM Pacific. A brief sent in the Pacific morning is read the next Manila morning, and the first delivery has usually come about a day later. He delivers by Box link.

## Before you write

If the Video Pipeline sheet is open to you (its link arrives in the nightly Video Pipeline email), check it so the ask does not stack on a full queue, and tell Graeham what slips if it does. Brief him only after Graeham has approved the angles. Look in the listing's creative folder first and ask only for what is not there. Ask for the smallest thing that finishes the ad, such as the missing cut, thumbnail or still, never a whole campaign's worth.

## What the email holds

Write as Graeham in the first person, since it goes from his address. Plain short sentences, one ask per thread, numbered deliverables. Use this order, which is how the first brief for the October listing was built:

1. The ask in one sentence, and where the ad will run.
2. Where the existing files are (one link) and which files to use, at original resolution.
3. The exact hook lines for each version, with their letters, spelled the way they must appear.
4. Deliverables by name and format (for example A15 and A30, 16:9 at 1920 x 1080), plus captions or SRT, the editable project, a clean version without music, and a thumbnail per concept.
5. What comes first and when, in both time zones: "by Sunday Oct 4, 9 AM Pacific (midnight Monday in Manila)". If that is not realistic he says the earliest date he can.
6. For a video, the structure by seconds: what shows in 0 to 5, 5 to 10, and so on.
7. The look and the footer: black, warm white and muted gold, the identity line (Graeham Watts, Compass and the DRE) and the phone, both read from identity.json, the real city visible, the call to action wording, and whether the URL is final.
8. The accuracy rules for this listing: what must not be claimed, which comparison is pending and must be labeled "Concept preview, comparison pending", "price" and not "cost", licensed basemap, no invented crossings, travel times or school assignments, AI staging labeled as a visualization, and a list of any AI staged or altered images in his delivery note.
9. "Send previews for review before anything is uploaded or published, and flag missing footage, licensing or production problems early."

Attach a longer brief as a .md or .docx if there is one. Files over about 10 MB go as links. No placeholder lines, because Graeham sends drafts exactly as they are.

## Sending

Default is a Gmail draft from Graeham's own address, since the email is in his voice. It goes To Peter only (the call sheet default of both editor addresses in To does not apply to ad briefs), with Ellie on cc only when she renders or exports. If any other address sends it, put Graeham on cc. Never guess Peter's address: take it from the sender line of his most recent email (the display name starts with Peter and he signs Jason), or ask Graeham. The other editor address in recipients.md is Ellie's. Graeham reviews and sends. If he says "send it" in chat, send it and confirm it is in Sent. The Gmail connector rewrites links and cannot attach files, so for links and attachments use the recipe in `seller-marketing-report/references/email-and-delivery.md`. Never email John. Log the date and thread in the ad log.

## When Peter delivers

Copy the files to the listing's Google Drive folder before anything client facing or ad facing uses them, because Box links stay internal (the Drive folder section of `seller-marketing-report/references/email-and-delivery.md` has the copy method). Check each file against the brief before upload: resolution and length, hook text spelled exactly, the real city on screen in the first five seconds, price and claims matching the approved copy, disclosures present, captions readable, and nothing pending released. If your tool cannot play video, pull frames with ffmpeg (on the user PATH, in `Documents\Skills LLMS\FFmpeg\bin`) at 0, 3 and 5 seconds, for example `ffmpeg -ss 3 -i file.mp4 -frames:v 1 frame3.png`, and read them. If you cannot look at a file at all, say so and leave that check open. If something is wrong, send one consolidated fix list in the same thread rather than a drip. When the creative passes, tell Graeham and move to setup.
