---
name: website-builder
description: "Graeham Watts website, landing page, and UI build system. Use ANY time the user mentions building, designing, coding, or improving a website, landing page, marketing site, product UI, web app screen, dashboard UI, PropertyOS UI, PropIQ screen, hero section, nav bar, CTA, feature grid, pricing page, component library, or design tokens."
license: Proprietary - Graeham Watts
---

# Website Builder

Graeham's reusable system for building websites, landing pages, and product UI (PropertyOS / PropIQ and general marketing sites). Use alongside Anthropic's `frontend-design` skill: `frontend-design` gives generic taste; this skill gives tokens, snippets, a review loop, and deployment.

## When to use this skill

Trigger on any UI/web request. If the user says "build me a landing page", "redesign this dashboard", "code this Figma mockup", "push to Vercel", "give it a glassy hero" — this skill applies.

If the task is a short email or Word doc, this skill is not the right tool — use `html-email` or `docx` instead.

## How to use the references

Don't read every file. Start with this SKILL.md for orientation, then pull only the reference that matches the current subtask. Each reference is a focused ~100–300 line document.

| If you're doing... | Read |
|---|---|
| Picking colors / CSS variables | `references/design-tokens.md` |
| Picking fonts / sizing / hierarchy | `references/typography.md` |
| Buttons, cards, badges, tables | `references/component-patterns.md` |
| Navs, heroes, feature grids, footers | `references/layout-patterns.md` |
| Page backgrounds, glass, orbs, noise | `references/backgrounds-and-textures.md` |
| Fade-ins, hover, scroll reveals | `references/motion-and-animation.md` |
| Inputs, forms, CTA cards | `references/forms-and-cta.md` |
| Self-critique via screenshots after building | `references/screenshot-loop.md` |
| Shipping to GitHub + Vercel | `references/deployment.md` |
| Applying Graeham's realtor brand | `references/realtor-brand-kit.md` |
| PropIQ placeholder tokens | `references/propiq-placeholder-tokens.md` |

## Standard build flow

When the user asks for a new page or site, follow this sequence unless they ask for something else.

1. Ask the aesthetic direction in one question (editorial / dark-glass / warm-earthy / minimal / custom). If they already gave you one, skip.
2. Scaffold a single HTML file with a `<style>` block — one file is faster to iterate than multi-file React. Move to React only if the user asks.
3. Paste the `:root` token block from `references/design-tokens.md` and edit brand colors.
4. Build sections in order: nav → hero → features → social proof → CTA → footer. Pull snippets from `assets/snippets/`.
5. Add one background effect (glass, orb, grid, or noise). One is enough — stacking them looks busy.
6. Run the screenshot loop. Fix anything that looks AI-generated (centered text blocks, cookie-cutter card rows, purple-on-white gradients).
7. Ask the user if they want to push to GitHub + Vercel. If yes, follow `references/deployment.md`.

## What lives in `assets/snippets/`

Copy-paste HTML fragments — not generic boilerplate, but the specific patterns that keep appearing across Graeham's PropertyOS and PropIQ screens. Use these verbatim, then swap tokens.

- `nav-glassmorphism.html` — blurred translucent nav with gradient-text logo
- `orb-background.html` — floating animated color orbs with noise overlay
- `hero-editorial.html` — large serif headline + body paragraph + two CTAs
- `cta-card.html` — gradient card with headline, supporting copy, primary button
- `kpi-card.html` — dashboard metric card with label, value, delta
- `feature-grid.html` — three-column icon-headline-blurb row

## Project contexts

| Project | Brand state | Use which reference |
|---|---|---|
| Graeham Watts realtor (listings, CMAs, buyer guides) | Locked — gold/black, Eagle CG Bold + SF Pro Display | `references/realtor-brand-kit.md` |
| PropertyOS / PropIQ | Placeholder — Deep Slate + multi-accent | `references/propiq-placeholder-tokens.md` |
| Other (client sites, one-offs) | Open — invent per-project tokens | `references/design-tokens.md` baseline |

If the user doesn't say which project, ask before picking a palette.

## Relationship with `frontend-design`

Anthropic's `frontend-design` plugin stays installed in parallel. When both apply, follow this priority:

- Graeham's locked realtor brand overrides everything — don't "vary the aesthetic" on realtor deliverables.
- For PropIQ, treat placeholder tokens as locked-for-now; `frontend-design`'s variety guidance applies only to new exploratory pages.
- For open/client projects, `frontend-design`'s "pick a bold direction" guidance is the default.

The two skills never conflict if you remember: `frontend-design` is about taste, this skill is about Graeham's specific tokens, snippets, and ship process.
