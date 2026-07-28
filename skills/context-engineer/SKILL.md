---
name: context-engineer
description: "Context-window diagnostic and optimization engine for Claude sessions and skills. Use ANY time the user mentions context window, context length, token budget, token limit, running out of context, context engineering, optimize my prompt, optimize my skill, my skill is too long, my prompt is too long, context management, context bloat..."
---

# Context Engineer — Diagnose & Optimize the Context Window

Diagnose bloated/expensive contexts and skills, and design new ones, using the tiered progressive-disclosure model below.

## Hard constraints

| Tier | What | When loaded | Budget |
|---|---|---|---|
| 1. Frontmatter | `name`, `description` | Always, even when skill doesn't trigger | ~200 words (~1% of a 200k context budget) |
| 2. SKILL.md body | Core workflow + decision logic | When the skill triggers | <500 lines ideal — flag anything over |
| 3. `references/` | Detailed docs, rubrics, playbooks | On demand, when SKILL.md body tells Claude to Read them | Unbounded |
| 4. `assets/` and `scripts/` | Templates, fonts, images, executables | On demand; scripts can run without loading source | Unbounded |

## Reference files

- `references/token_estimation.md` — How to estimate tokens from files, messages, and tool results without running a tokenizer.
- `references/patterns.md` — Tiered context patterns: domain-organized, variant-organized, phase-organized, with examples.
- `references/anti_patterns.md` — The seven anti-patterns with diagnostic signatures and fixes.

Read them on demand. If the user asks for a general context diagnosis, audit, or refactor, work from the tier table above and pull in the reference files as needed for the specific case.
