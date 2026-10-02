# Build with the existing carousel engines

Source scripts: `C:/Users/Graeham Watts/Documents/Skills LLMS/Claude/Skills/skills/video-editor/scripts/`.

1. Check the available Python runtime, Pillow, ReportLab, Poppins fonts, and a PDF text extractor. For footage inputs also check ffmpeg/ffprobe. Use the app's bundled document runtime when available. Do not assume the historical Linux paths or 45-second sandbox limits describe the current host.
2. Copy `carousel_lib.py`, `make_carousel_pdf.py`, and `ad_lib.py` together into task scratch. Modify the task copy only; these modules import each other by name. Keep this engine separate from the other `carousel-builder/carousel_lib.py`, which has a different API and design.
3. Set `VE_FONTDIR` to the folder containing Poppins-Bold.ttf, Poppins-Medium.ttf, and Poppins-Light.ttf. Set `VE_CHEROES` to the selected stills folder. Configure `VE_TMP` inside task scratch and `VE_CAROUSEL_PDF` to the intended PDF output path before importing the modules. Obtain licensed fonts if missing, or report that dependency.
4. Replace `ADDR1`, `ADDR2`, and the entire `SLIDES` data in the task copy. Each slide specifies `t` (cover/feat/close), `hero`, `focal`, and `num`; cover adds `hook`, feature adds `label` and `sub`, and close adds `recap`. Do not reuse example property claims.
5. Replace the hardcoded closing-city phrase in `ops_for()` and derive the counter denominator from `len(SLIDES)`. Check both shared modules for leftover example addresses. Cache fonts by filename and size if font loading is a measured bottleneck.
6. Use `render(i, "png").save(path)` for the finished slides. `render(i, "clean")` supplies text-free cropped images; `grad_overlay(spec["t"])` supplies a separate gradient. The PDF exporter uses the same `ops_for(spec)` instructions for real text and vector elements.
7. Run `make_carousel_pdf.py` from the task script directory. Verify text extraction, representative PDF rendering, and PNG readability. Sharing draw operations does not by itself prove pixel-identical outputs or Canva import fidelity. Shorten overlong copy rather than accepting unreadable tiny text.

For new listings, a persistent JSON-driven runner can replace per-task module edits once implemented and validated. Until then, use the documented task copies; do not claim incremental caching or automated layout checks that the existing engine does not implement.
