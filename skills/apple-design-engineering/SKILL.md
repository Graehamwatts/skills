---
name: apple-design-engineering
description: "Apple-grade interface design, animation, and motion-vocabulary skill for any UI work in this workspace - dashboards, landing pages, CMA pages, artifacts, PropIQ product screens. Distilled from Apple's WWDC design talks (via Emil Kowalski's MIT-licensed skills repo, vetted + vendored 2026-08-31). Use ANY time the user mentions: Apple design, premium UI, make it feel premium, fluid interface, animations, motion design, springs, easing, micro-interactions, audit the UI, design review of a page/app, AI-generated looking UI, interruptible animations, gesture-driven UI, or wants precise vocabulary to describe motion to a developer. Also load whenever BUILDING any user-facing HTML page, dashboard, or artifact in this workspace so the output stops looking AI-generated."
---

# Apple Design Engineering

Vendored from Emil Kowalski's `emilkowalski/skills` repo (MIT, 34k+ stars; he built Sonner and Vaul). Full deep scan passed 2026-08-31: pure markdown, no scripts, no secrets, no network calls, no injection patterns. Original license preserved in `LICENSE-emilkowalski-MIT.txt`. To refresh from upstream later: re-clone, RE-SCAN with secret-leak-scanner plus a malicious-pattern grep, then re-copy the reference files.

## What this skill is for

Three jobs, pick by intent:

1. **BUILD** - writing new UI (a dashboard, landing page, artifact, PropIQ screen) that follows Apple's interaction rules instead of guessing what "premium" means.
2. **AUDIT** - pointing the rules at EXISTING UI and returning specific violations. This is the highest-leverage use (per the source author): "audit this page against the apple-design rules" beats "make it look better" every time.
3. **TRANSLATE** - giving Graeham (non-coder) precise animation vocabulary so he can tell Mehmood's team or Sammy exactly what motion he wants, instead of "make it feel smoother."

## How to use (routing)

- Building or restyling UI -> read `references/apple-design.md` FIRST, then write code. Core rules that must survive into any output: interactions respond on press-down (not release), springs over easing curves for interactive motion, every animation interruptible and reversible mid-flight, motion inherits user velocity, respect `prefers-reduced-motion`, restraint (fewer, better animations - see find-animation-opportunities for the over-animation flags).
- Auditing existing UI -> read `references/review-animations.md` + `references/review-standards.md`, walk the target code/page, output a prioritized findings list (violation, where, why it feels wrong, the fix). For "where should we ADD motion" use `references/find-animation-opportunities.md` - it also flags over-animation.
- Graeham describing motion he wants -> read `references/animation-vocabulary.md` and either (a) translate his plain-English description into precise terms for a dev brief, or (b) teach him the term he is reaching for.

## Workspace application notes

- **PropIQ product screens**: audits of the CRM/dashboard UI go to Mehmood's team as prioritized findings, same audit-then-approve pattern as everything else in the Master Brain. This skill is the reviewer, not the builder, there.
- **This workspace's own HTML output** (dashboards, CMA pages, landing pages, artifacts): apply the BUILD rules directly. This is the antidote to AI-generated-looking pages.
- Brand rules still win: identity.json, gold-is-sacred, palette and typography from the brand kit. This skill governs MOTION and INTERACTION FEEL, not brand colors.
- A copy-paste version for ChatGPT lives at `references/chatgpt-portable-version.md` - regenerate it if the reference files are ever updated.

## Files

- `references/apple-design.md` - the core: Apple's fluid-interface principles translated to web (springs, velocity, interruptibility, materials, typography, reduced-motion).
- `references/review-animations.md` + `references/review-standards.md` - the strict audit rubric.
- `references/find-animation-opportunities.md` - where motion helps, and the over-animation flags.
- `references/animation-vocabulary.md` - the shared language for describing motion precisely.
- `references/chatgpt-portable-version.md` - single-file concatenation for pasting into ChatGPT (custom GPT instructions or project files).
- `LICENSE-emilkowalski-MIT.txt` - upstream license, keep with the files.
