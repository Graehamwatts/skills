# Skills "Native Knowledge vs. Hard-Won Specifics" Audit — 2026-07-28

Full sweep of all 66 remaining skills (everything except `remotion-video`/`remotion-rules`, already actioned separately). Six parallel research agents read every SKILL.md in full and classified content against the lens you proposed: **generic content a capable model already knows** (trimmable) vs. **hard-won, non-reconstructable specifics** — bug workarounds, exact IDs/paths, brand locks, compliance rules, discovered vendor quirks (must stay regardless of model capability).

No files have been edited. This is a proposal set.

---

## Part 1 — Actual bugs found (separate from the genericness question, higher priority)

These aren't about trimming — they're incidental discoveries of real inconsistencies/breakage while agents read every file closely. Recommend fixing these regardless of what happens with Part 2.

| # | Skill | Issue |
|---|---|---|
| 1 | `transcript-repurposer` | Repeatedly references `video-script-creation-engine/references/...` paths. That skill was retired 2026-04-29 per the repo's own `CLAUDE.md` in favor of `content-creation-engine`. These are dead pointers today. |
| 2 | `meta-ads` | Its Handoffs table still names `social-media-analyzer`, which was absorbed into `content-calendar`. Stale skill name. |
| 3 | `video-creator` | Hardcodes `"Brokerage": "Compass"` (appears twice) in its Agent Info Defaults. Every other skill in the audit uses "Intero Real Estate," and the repo's `CLAUDE.md` explicitly says brand facts must come from `identity.json`, never be hardcoded. This is the same class of bug the blocklisted-DRE incident was about. |
| 4 | `heygen-video` vs. `heygen-elevenlabs-renderer` | Disagree on Graeham's HeyGen avatar inventory — one documents 6 named looks with a "must ask every time" rule; the other says "70 personal avatar looks" with a single primary ID. These describe the same account and need reconciling. |
| 5 | `newsletter-generator` | Two different gold brand hex values appear in the same file (`#C2A14E` vs. `#C5A258`/`#B8860B`) — looks like drift between an old and new brand pass. |
| 6 | `cinematic-trailer-pipeline` | Built entirely around PAI 2.0/UTOPAI as the video generator, while `higgsfield-video`/`cinematic-hooks` reflect the newer Higgsfield/Seedance/Kling stack. Worth confirming whether PAI 2.0 is still active or this pipeline itself is now the stale one. |
| 7 | `llm-council` | Step 5 says "Do NOT generate an HTML report... user reads it in conversation," but the closing notes contradict this: "The visual report matters... make the HTML output clean." Leftover instruction from an earlier version. |
| 8 | `flow-dictation` | Its "Roadmap (not built yet)" section lists two features (lock mode, AI-polish pass) that the body already describes as shipped. Only "voice commands" is genuinely still pending. |
| 9 | `ai-library` | Cites "45 Personal Claude Skills / 139 total items," clearly stale against the current ~90+ skill directory (the repo's own root `CLAUDE.md` separately claims a stale "39 skills" too). |
| 10 | `cowork-task-shutoff` | Explicitly scoped to a one-time migration dated 2026-06-09/06-12. ~7 weeks later, worth checking whether this is done and the skill itself can retire. |
| 11 | `trackabi-va-payroll` | Bakes a point-in-time loan balance ("as of Jul 1 2026: payment 5 of 10, $522.49 remaining") directly into the SKILL.md prose, duplicating the live loan tracker file. Will read as false every pay period. |
| 12 | `past-client-follow-up-system` | The documented schedule horizon ends "Fri Aug 7 2026" — about 10 days out from this audit. Needs regenerating soon; also has one unconfirmed GHL custom-field ID flagged "confirm before run." |
| 13 | `website-crawler` | Self-flagged "scaffolded 2026-07-18, not yet installed or run end-to-end" — 10 days old as of this audit; worth confirming whether it's since been verified. |
| 14 | `youtube-scraper` | References `mcp__Claude_in_Chrome__*` (underscore/caps) — this session's actual Chrome MCP tools are `mcp__claude-in-chrome__*` (hyphenated). Worth verifying this isn't a dead tool reference. |
| 15 | `travel-hq` | Not actually a bug — it's an almost entirely unfilled placeholder template (every card, loyalty number, and companion profile is still `[PLACEHOLDER]`). Flagging because it can't meaningfully be audited for genericness until you fill in your actual travel profile. |

---

## Part 2 — The genericness/trim question

### Tier A — Strong trim candidates (mostly/entirely reconstructable from general model knowledge)

| Skill | What's generic | What to keep |
|---|---|---|
| `context-engineer` | Nearly the whole file — token-budget categorization, anti-patterns list, pushback FAQ, a hypothetical (not real) `video-creator` example. Ironically the most bloated file relative to how little Graeham-specific content it has. | The two hard numeric constraints and pointers to its own `references/` files. |
| `github-repo-analyzer` | The entire file — ghost-developer reasoning, git/GitHub domain knowledge, generic management-tact advice. Zero Graeham-specific content found anywhere. | Report format/headers if you like the output shape. |
| `job-search-engine` | Most of the explanatory prose (ATS/7-second-scan lecture, negotiation-script rationale) — though the actual prompt templates are more like reusable assets than teaching content and can stay. | The 9 prompt templates themselves; cut the surrounding generic scene-setting. |
| `language-tutor` | Nearly the whole file — CEFR milestones, generic lesson structure, generic tutoring "rules." Zero facts specific to what Graeham's actually learning. | The intake questions (they gather his real answers) and the progression-tracking state model. |
| `consolidate-memory` | Most of it — general "how to maintain a memory system" theory. | The two hard constraints (200 lines/25KB, line format) and the pointer to the system prompt's memory config. |
| `seo-optimizer` | The entire audit rubric (title-tag length, meta description length, keyword density, Flesch score) — standard on-page SEO a model already knows. Isn't even real-estate-localized. | The one genuinely hard-won insight (YouTube/Reddit citation frequency in AI answers, Pantana Feb 2026 field notes) — should be promoted higher, not cut. |
| `copywriter` | The AIDA/PAS/FAB/BAB framework definitions and the psychological-levers list — textbook, and duplicated almost verbatim in `marketing-psychology`. | Framework *selection* guidance, output templates, humanizer-pass instructions, format character limits. |
| `marketing-psychology` | Schwartz awareness-stage definitions, Cialdini principles, the "11 minds" panel bios — canon-level marketing knowledge. | The decision tables (blocking-force matrix, framework tree, failure-mode fixes) and the explicit division-of-labor vs. `copywriter` — that's applied judgment, not facts. |
| `property-underwriter` | The full NOI/cap-rate/DSCR/IRR formula derivations — textbook real estate finance. | The Model-Builder-gets-the-debt-schedule-wrong warning, all CA/Bay-Area tax specifics, the "never fabricate rent" rule, PropertyIQ integration section. |
| `listing-remarks-writer` | The "Nouns Over Pronouns" copywriting lecture and generic vocabulary lists. | Fair Housing/RESPA rules, truth-in-advertising rules, Bay Area neighborhood specifics, the "AI search ignores these words" claim (flag as uncertain — may be calibrated, not generic). |
| `listing-photo-captioner` | Generic caption-style bullets ("lead with room name," "sentence case"). | Fair Housing/RESPA guardrails, ADU naming rule, MLS character limits, Bay Area landmark examples. |
| `disclosure-analyzer` | Generic finding-severity definitions, generic tact advice, most of "Common Pitfalls" (verify with you whether these came from real incidents first). | Seller Credit Request framework, QC failure-mode list, publishing pipeline. |
| `price-reduction-angle-generator` | Generic "don't use fear tactics" tone rules. | Three-Strategy Honesty Rule, banned-word list, Fair Housing specifics, Bay Area DOM thresholds (flag as uncertain — looks generic but may be calibrated). |
| `offer-analyzer` | Generic Tone & Style paragraph. | The entire Default-Output-Mode-Information-Only section — this is the actual differentiator of the skill, a deliberate liability posture, not generic advice. |
| `cma-generator` | Narrative-writing paragraph-count instructions (now redundant with the separate `humanizer` skill). | DRE/brand hard rule, File-Integrity Protocol, exact publishing steps. |
| `contract-estimate-builder` | Excel-formatting-rules bullet list, already duplicated by the `xlsx` skill it references. | Menalto/Minalto misspelling note, disclaimer legal language, Option-Group modeling logic. |
| `website-builder` | Design-philosophy/anti-pattern list — the file itself admits this overlaps with the separately-installed `frontend-design` skill. | Brand-state table (locked vs. placeholder), snippet routing, conflict-priority rule. |
| `transcript-repurposer` | Analysis-axis and angle-option explanatory prose (duplicates ground `comedy-craft`/`marketing-psychology` already cover). | The named rubric as a compact checklist, environment/entry-point logic, GHL keyword list, humanizer inclusion/exclusion list. |
| `video-watcher` | The "why visual analysis matters" reasoning and the "Why this exists (history)" section. | Trigger-boundary table (cost-driven routing vs. video-transcriber), cost tables, maintenance/ownership note. |
| `room-redesign` | Generic prompt-engineering tips ("tell it what to keep," "one change at a time"). | The four pre-tuned prompt templates, exact model IDs, MLS staging-disclosure legal note. |

### Tier B — Uncertain, don't cut without checking with you first

These *look* generic but the agents flagged them as possibly calibrated from real testing/taste, not textbook knowledge:

- `cinematic-hooks`'s "pattern interrupt psychology" and "creative frameworks" sections — did these come from testing what actually stops a scroll, or are they written from general theory?
- `listing-remarks-writer`'s claim about which words "AI search ignores"
- `price-reduction-angle-generator`'s Bay Area DOM velocity thresholds
- `cma-generator`'s chart-type choices (radar vs. table)
- `humanizer`'s 29-pattern taxonomy (may encode Wikipedia-sourced completeness value even if individually recognizable) and its linked `references/voice-calibration.md`/`patterns-catalog.md` (not read yet — could hold real calibration)
- `llm-council`'s five-advisor personas (a deliberate design choice creating three tensions, not random)
- `comedy-craft`'s technique toolkit (illustrated with real-estate-specific examples throughout — leaning toward keep, but flagged since it's presented as generic craft)

### Tier C — No changes recommended (dense, hard-won, non-reconstructable)

`mls-matrix-scraper`, `farming-postcard`, `weekly-listing-update`, `chatgpt-ads`, `comedy-craft`, `switchy-engine`, `switchy-qr`, `listing-launch-engine` (core orchestration), `founder-academy`, `finance-watch`, `flow-dictation` (aside from the roadmap fix above), `heygen-video`, `heygen-elevenlabs-renderer`, `higgsfield-video`, `watts-motion-graphics`, `podcast-studio`, `vaibhav-template`, `video-to-obsidian`, `cinematic-trailer-pipeline` (aside from the PAI-2.0 staleness check), `instagram-competitor-scraper`, `local-news-scraper`, `obsidian-vault`, `past-client-follow-up-system`, `schedule`, `setup-cowork`, `trackabi-va-payroll`, `youtube-scraper`, `property-os-sync` (only the Cowork/Windows dual-path branching is worth consolidating), `skill-creator` (its own tripwire/placement-rule block is critical; the generic skill-authoring methodology below it is arguably the actual content this tool-of-tools skill needs to teach, not bloat).

### Anthropic-authored reference skills — different tradeoffs

`docx`, `pdf`, `pptx`, `xlsx` all ship an Anthropic `LICENSE.txt` — they're unmodified public reference skills, not Graeham-custom. Their generic library-API content is intentional design for portability across arbitrary projects, not accumulated bloat. Trimming them loses upgradeability from Anthropic and has different tradeoffs than trimming a bespoke skill. Recommend leaving these alone unless you specifically want a leaner, less-portable fork. `video-transcriber` (no LICENSE.txt, Graeham-custom) is the opposite — almost entirely hard-won, no changes recommended.

---

## What I'd suggest as next steps

Given the scale (66 skills touched by this audit), rather than doing all of Tier A in one giant sweep, sensible slices to approve independently:

1. **Fix the 15 bugs in Part 1** — these are correctness issues, not judgment calls, and mostly small.
2. **Trim Tier A** — 20 skills, all with a clear "cut this / keep this" split above.
3. **Decide Tier B case-by-case** — genuinely needs your judgment on whether each was empirically calibrated or just written generically.
4. **Leave Tier C and the Anthropic reference skills alone.**
