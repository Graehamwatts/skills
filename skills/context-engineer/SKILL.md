---
name: context-engineer
description: "Context-window diagnostic and optimization engine for Claude sessions and skills. Use ANY time the user mentions context window, context length, token budget, token limit, running out of context, context engineering, optimize my prompt, optimize my skill, my skill is too long, my prompt is too long, context management, context bloat..."
---

# Context Engineer — Diagnose & Optimize the Context Window

You are a context-window architect. Your job: take a messy, bloated, or expensive context and turn it into a lean, tiered system where each piece of information lives at the right level of disclosure.

The premise: Claude's context window is a budget. Every token in that budget either earns its keep by improving the answer, or it steals attention from tokens that would. Context engineering is the discipline of spending that budget well.

---

## Part 1 — Diagnosing an existing context

When the user says "my context is full" or "my prompt is too long", don't guess. Run the diagnostic.

### Step 1: Categorize what's in the window

Break the window down by category (system prompt, conversation history, loaded files, skill bodies, tool results, last response) and produce a table with estimated tokens and % of window per category.

For token-count estimation heuristics and worked examples, see `references/token_estimation.md` — don't re-derive them here.

### Step 2: Identify the offenders

The categories that are over-indexed compared to their value. Common patterns:

- **Runaway tool results** — a single bash call, grep, or web fetch that dumped more than the user needed. Usually the biggest win.
- **Re-read files** — the same file Read multiple times across turns because the model forgot it was already in context.
- **Verbose skill bodies** — a SKILL.md over 500 lines that could be split into SKILL.md + references.
- **Pasted data the user could have linked** — the user pasted a 20,000-word document when a file attachment would have done the same job more efficiently.
- **Repetitive instructions** — user restates rules in every turn ("remember, use TypeScript"). Better to put this in a persistent system instruction or a CLAUDE.md.
- **Accumulated errors** — failed tool calls that returned multi-KB error traces.

### Step 3: Triage

For each offender, make one of these calls:

| Decision | When to use |
|---|---|
| **Keep** | Actively referenced in the current task. Needed in active context. |
| **Move to reference file** | Used occasionally. Load on demand via Read. |
| **Summarize** | Important to remember, but the details don't matter. Replace with a 2–3 sentence summary. |
| **Drop** | No longer relevant. Stale search results, old tool output, abandoned branches. |

Write up the triage like a punch list:

```
Triage — Current context (est. 200k / 200k)
- Tool result from `bash: find /` — DROP (obsolete, no longer needed)
- 40k-char server log — SUMMARIZE to "server returned 500s from 14:32 to 14:47, root cause = DB pool exhausted"
- pdf/SKILL.md fully loaded — MOVE TO REFERENCE (already know the workflow, reload if needed)
- Original user spec doc — KEEP (actively cited in this session)
```

---

## Part 2 — Auditing a SKILL.md for context efficiency

When the user says "audit my skill" or "why is this skill eating so much context", run the skill audit.

### The tiered context model

A well-designed skill has four tiers, each loaded at a different trigger:

| Tier | What | When loaded | Budget |
|---|---|---|---|
| 1. Frontmatter | `name`, `description` | Always, even when skill doesn't trigger | ~200 words |
| 2. SKILL.md body | The core workflow + decision logic | When the skill triggers | <500 lines ideal |
| 3. `references/` | Detailed docs, rubrics, playbooks | On demand, when SKILL.md body tells Claude to Read them | Unbounded |
| 4. `assets/` and `scripts/` | Templates, fonts, images, executables | On demand; scripts can run without loading source | Unbounded |

The key insight: **progressive disclosure**. Information that's used in 10% of invocations should not sit in the 90% of context windows where the skill is loaded.

### Red flags in a SKILL.md

When reviewing a SKILL.md, flag:

- **Body over 500 lines.** Anything over 500 lines pays for itself in every invocation. Hard question: does every line here actually help on a typical run, or is 80% of it edge-case handling that should live in references?
- **Multiple long embedded examples.** Examples are valuable but expensive. Put 1–2 sharp examples in SKILL.md; move the rest to `references/examples.md`.
- **Rules restated multiple times.** If you wrote "ALWAYS use X" in three places, pick one and link to it.
- **Long code blocks.** A 60-line Python function inline in SKILL.md is almost always better placed in `scripts/`.
- **Framework / domain-specific detail for N frameworks.** If the skill handles AWS + GCP + Azure, don't load all three docs; load the one that matches the user's request. Put each in its own reference file.
- **No table of contents on references over 300 lines.** Large reference files should have a TOC up top so Claude (or a reader) can jump to the right section without scanning the whole thing.

### The skill audit output format

```
# Skill Audit — [skill-name]

## Summary
- SKILL.md: XXX lines (target: <500)
- references/: [list of files, sizes]
- Overall context efficiency: Good / Needs work / Bloated

## What to move to references/
| Lines in SKILL.md | What it covers | Move to |
|---|---|---|
| 120-260 | The full Flesch formula walkthrough + examples | references/readability.md |
| 340-420 | Domain-specific playbook for B2B SaaS | references/b2b_saas.md |

## What to cut entirely
- Lines XX-YY: repeated instruction already covered at line ZZ
- Lines AA-BB: example that doesn't add new information beyond the first example

## What to keep as-is
- Core workflow steps
- Decision tree for framework selection
- One or two canonical examples

## Suggested tier structure after the refactor
[show the proposed directory layout]

## Estimated token savings
Before: XXXX tokens on every invocation
After: YYYY tokens on typical invocation (references loaded on demand)
Savings: ZZ% on the 70% of runs that don't need the deep reference
```

---

## Part 3 — Designing context from scratch

When the user is building a new skill or system prompt, design the context tier-first.

### The three questions

Before writing a single line, answer:

1. **What runs on every invocation?** → SKILL.md body. Lean, imperative, includes the decision logic.
2. **What runs only for specific cases?** → references/ files, named by case. Loaded on demand.
3. **What doesn't need to live in context at all?** → scripts/ (executed) or assets/ (templated).

### Progressive disclosure in practice

Example refactor — a hypothetical `video-creator` skill that handles three formats (MP4 slideshow, React-based Remotion, HeyGen avatar):

**Bad (monolithic):**
```
video-creator/
└── SKILL.md  (1,200 lines — all three formats inline)
```

**Good (tiered):**
```
video-creator/
├── SKILL.md  (250 lines — format selection + shared workflow)
└── references/
    ├── mp4_slideshow.md  (400 lines, loaded only for slideshow jobs)
    ├── remotion.md       (600 lines, loaded only for Remotion jobs)
    └── heygen.md         (350 lines, loaded only for HeyGen jobs)
```

Same total information; 70% of invocations pay one-fourth the token cost.

See `references/patterns.md` for more tiered-context patterns (domain-organized, variant-organized, and phase-organized).

---

## Part 4 — Common anti-patterns

See `references/anti_patterns.md` for the seven anti-patterns (kitchen sink, repeat offender, stale tool result, silent re-read, verbose example, unused lookup table, restatement of defaults), each with a diagnostic signature and fix.

---

## Part 5 — When the user pushes back

The goal isn't minimum tokens, it's right-sized context for the task — weigh invocation frequency against the cost of loading something every run before deciding to inline vs. move to a reference.

---

## Reference files

- `references/token_estimation.md` — How to estimate tokens from files, messages, and tool results without running a tokenizer.
- `references/patterns.md` — Tiered context patterns: domain-organized, variant-organized, phase-organized, with examples.
- `references/anti_patterns.md` — The seven anti-patterns with diagnostic signatures and fixes.

Read them on demand. If the user asks for a general context diagnosis, you can usually answer from SKILL.md alone.
