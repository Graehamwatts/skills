---
name: real-estate-carousels
description: Create property listing carousels from photos or video stills, with ready-to-post PNG slides, an editable PDF, and a caption. Use for real estate carousels and swipeable property tours.
---

# Real Estate Carousels

Create a property carousel using the existing video-editor carousel engine. Default to ten 1080x1350 slides: cover, eight feature slides, and recap. Adapt the sequence to the actual property and requested length. Deliver PNGs, a PDF with real text, a caption, and a short upload guide.

## Inputs and choices

Use facts, footage selections, and brand preferences already supplied. Ask only for missing information that affects the result. Default to property-only content without agent name, contact details, or price; add those when requested. Use only confirmed facts and visibly supported features. Research current sources when making market or value comparisons. Do not infer materials, room classifications, or dimensions from appearance alone.

Reuse photo selections, contact sheets, and extracted stills from an existing video edit. Otherwise make a labeled contact sheet, inspect candidate photos, and select clean frames with useful focal points. Check for unwanted signage when agent information is excluded.

## Build efficiently

The existing renderer and PDF exporter are in `C:/Users/Graeham Watts/Documents/Skills LLMS/Claude/Skills/skills/video-editor/scripts/`: `carousel_lib.py`, `make_carousel_pdf.py`, and their dependency `ad_lib.py`. Use these engines rather than reinventing layouts. They share drawing operations for image and PDF output.

Read [the build reference](references/build.md) when producing files. Do not load the full video-editor skill, unrelated video recipes, or renderer source unless needed for adaptation or debugging. Keep layout code stable; change property data and copy. Preserve the existing Poppins, black, gold, and off-white design unless the user specifies another style.

Draft all slide copy together, keeping each feature label and detail brief. Review the overall story and select the final photos before rendering. Render changed slides during revisions; regenerate the PDF when its contents change. Keep output logs compact.

## Check and deliver

Inspect a contact sheet of every finished slide, then check the cover, recap, longest text, and any questionable crop at full resolution. Check text fit, legibility, correct address/city, factual claims, numbering, and photo choices. Extract PDF text to confirm it is real text; render representative PDF pages and compare them with the PNGs. Canva import fidelity requires an actual import check before claiming it is verified.

Deliver `Ready-to-Post-PNG/`, `Editable-PDF/`, `Caption.txt`, and `Carousel-Guide.txt`. Number slides in upload order. Use the current user's file-location rules; on this machine, working files belong under `codex/workspace/tmp/<task>/` and final deliverables under `codex/output/` unless an established business folder is requested. Remove task scratch after delivery.
