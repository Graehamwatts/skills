# Dashboard Architecture & Calendar Output Format — moved verbatim from `content-calendar/SKILL.md` (2026-06-09 refactor)

## Calendar Output Format — v5.4 Production Bible

The final deliverable is a **hosted HTML Production Calendar** — a single-page web app that
serves as a complete production bible for the video editor (Jason). It gets pushed to GitHub
Pages at `Graehamwatts/online-content/dashboards/weekly-calendars/YYYY-MM-DD-production-calendar-v6.html`.

The HTML calendar has **three tabs**: Analytics, Production Map, and Copy Bank.

### Tab 1: Analytics Dashboard

Month-over-month performance comparison showing:
- **MoM Metrics Table:** Current 30d vs prior 30d for reach, engagement, followers, video views
- **Content Type Performance Matrix:** Average reach by content category (Discovery, Listing/Promo,
  Data/Market, Engagement, Educational) with sample size and top performer
- **Engagement Details Table:** Per-post breakdown with reach, likes, comments, shares, saves,
  engagement rate, and content type tag
- **Visual Bar Chart:** CSS-only bar chart comparing post reach across the period
- **GSC Query Analysis:** Top search queries by impressions, rising queries, page-2 opportunities,
  and query cluster analysis (e.g., "AB 1482 cluster = X impressions")

### Tab 2: Production Map (Main Calendar)

**Intelligence Stack Panel** at the top showing:
- Every data source used (Windsor IG, Windsor YT, Windsor GSC, Windsor FB, Apify Reddit, Web Search)
- Status of each source (connected/partial/unavailable) with percentage of data coverage
- Which skills were used in generation (content-calendar, content-creation-engine, cinematic-hooks)
- Transparent about what data was NOT available

**Day Cards** — One expandable accordion card per content day (typically 5 content days + 1 email
newsletter day). Each day card shows:

```
[DAY] — [Date]
TOPIC: [Specific topic with angle]
TITLE: [SEO-optimized title, <60 chars]
FORMAT: [Primary format — YouTube Long / Reel / Short / etc.]
PLATFORM: [Primary] → [Cross-post targets]
FUNNEL: [TOFU / MOFU / BOFU]
SEARCH TARGET: [Organic SEO / LLM Search / Both]
SCORE: [X/25] — [Brief justification]
SOURCE BADGE: [Where the idea came from — GSC Query, IG Performance, News Cycle, Reddit, Trend]
HOOK (first 3 sec): "[Specific opening line or visual hook]"
POSTING TIME: [Recommended time based on engagement data]
CTA: [Specific call-to-action + GHL keyword trigger if applicable]
```

**Derivative Format System (CRITICAL v5.4 FEATURE):**
Each day card contains a **horizontal row of clickable format buttons**:
YouTube Long | YT Short | IG Reel #1 | IG Reel #2 | IG Carousel | TikTok | Blog | GMB | FB

Clicking any button reveals a **derivative panel** with the COMPLETE production package for that
specific format, including:
- Full script (with inline shot direction tags)
- Platform-specific specs (duration, aspect ratio, resolution)
- Caption with hashtags
- Description / SEO metadata
- Posting instructions
- GHL keyword CTA

The core asset (usually YouTube Long) panel also includes:
- **Inline Shot Direction Tags:** `[B-ROLL: description]`, `[TALKING HEAD]`, `[TEXT OVERLAY: text]`,
  `[DRONE: description]`, `[SCREEN RECORD: description]` embedded directly in the script
- **Editing Notes for Jason:** Yellow block with B-roll shot list, text overlay timing, pacing notes,
  thumbnail concept, music/SFX direction
- **ElevenLabs SSML Block:** Full `<speak>`, `<prosody>`, `<break>` markup for AI avatar voice
  generation, ready to paste into ElevenLabs
- **AI Video Prompts:** Seedance 2.0 / Kling-ready prompts for hook shots and B-roll sequences,
  with camera movement, lighting, and duration specs
- **Edit Button:** Toggle `contentEditable` on script sections for in-browser editing (local only,
  resets on refresh)

### Tab 3: Copy Bank

Pre-written copy blocks for quick use:
- Email newsletter template for the week
- Social media captions (per platform)
- Blog post outline
- Each block has a **copy-to-clipboard button**

### Visual Design Requirements (Light Theme)

The calendar MUST use a light color scheme matching Graeham's brand:
```
--bg: #f4f5f7 (light gray page background)
--card: #ffffff (white cards)
--navy: #1B2A4A (primary text, headers, nav)
--gold: #C5A258 (accents, badges, active states)
--text: #2d3748 (body text)
--muted: #718096 (secondary text)
```
Fonts: Plus Jakarta Sans (headings) + DM Sans (body) via Google Fonts import.
**DO NOT use dark mode.** The user has explicitly rejected dark themes.

### Source Badges

Every day card gets a source provenance badge showing where the topic idea came from:
- `.src-gsc` — Google Search Console query cluster (blue)
- `.src-reddit` — Reddit audience demand signal (orange)
- `.src-news` — Current news/event cycle (red)
- `.src-perf` — Own performance data showing topic works (green)
- `.src-trend` — Market trend or seasonal hook (purple)

### Key CSS Classes (for consistent rendering)

```css
.dir { /* Inline shot direction tags — blue background */ }
.sm { /* Section markers — bold navy */ }
.edit-notes { /* Yellow editing notes blocks for Jason */ }
.el-block { /* Purple ElevenLabs SSML blocks */ }
.vid-prompt { /* Green AI video prompt blocks */ }
.flow-card / .deriv-panel { /* Clickable derivative format system */ }
.edit-btn { /* In-browser script editing toggle */ }
.src-badge { /* Source provenance badges */ }
.isp / .isp-card { /* Intelligence Stack panel */ }
```

### Key JavaScript Functions

```javascript
showTab(id)           // switches main tabs (analytics/calendar/copy bank)
toggleDay(id)         // opens/closes day accordion cards
showDeriv(dayId, fmt) // switches between derivative format panels within a day
toggleEdit(btn)       // toggles contentEditable on script boxes
copyText(btn)         // copies text to clipboard from copy bank
toggleCheck(el)       // toggles deliverable checkboxes
```

### Auto-Render Button — retired (2026-07-29)

The "🚀 Full Auto-Render" button, its Flask webhook handler, and the `heygen-elevenlabs-renderer` skill it POSTed to are all retired — that capability is moving into PropertyIQ. **Do not generate the button markup, banner, or webhook prerequisite in new calendars.** For now, each core asset derivative panel should link out to `heygen-video` for manual rendering instead.

**Where renders + voices live (still relevant for manual rendering):**

| What | Where | URL |
|---|---|---|
| Finished video | HeyGen project page | `https://app.heygen.com/videos/<video_id>` |
| All renders | HeyGen projects list | `https://app.heygen.com/projects` |
| Voice generations | ElevenLabs history | `https://elevenlabs.io/app/speech-synthesis/history` |
| Graeham cloned voice | ElevenLabs Voice Library | `https://elevenlabs.io/app/voice-library` |

### GitHub Pages Hosting

After generating the HTML file, push it to the `Graehamwatts/skills` repo under:
`online-content/dashboards/weekly-calendars/YYYY-MM-DD-production-calendar-v6.html`

The hosted URL will be:
`https://graehamwatts.github.io/online-content/dashboards/weekly-calendars/YYYY-MM-DD-production-calendar-v6.html`

### Weekly Email Format (for the Blog Producer) — Three-Tier Topic Options (April 2026)

In addition to the hosted HTML calendar above, content-calendar produces a **Monday email** for the blog producer (the publishing team member who actually posts content) and **daily emails** each weekday morning. The email is the *trigger*; the hosted dashboard is the *action surface*.

**Why this exists:** Blog Track doesn't need the full production calendar (that's for Jason and Peter). Blog Track needs a quick decision surface: "what should I post this week, and where do I grab it?" The email gives him three tiers of topic options, each with a deep-link to the relevant section of the hosted dashboard where the Copy Content button lives.

#### Three-Tier Structure

The Monday email displays the week's topics in three tiers based on the Opportunity Score (25 pts):

| Tier | Score range | Threshold label | Count |
|---|---|---|---|
| **Top tier** | 22-25 | `must_create` | 1-2 topics — the highest-scoring topics this week |
| **Next tier** | 17-21 | `strong` | 2-3 topics — solid alternates if top tier doesn't resonate |
| **Third tier** | 12-16 | `consider` | 1-2 topics — backup options |

Topics scoring below 12 (`skip` threshold) are NOT included in the email. They're excluded entirely.

#### Why Links Instead of In-Email Copy Buttons

**Email clients (Gmail, Outlook, Apple Mail) strip JavaScript from HTML emails for security.** The Copy Content / Copy Script Prompt / Copy Production Prompt buttons documented in `content-creation-engine/references/single-topic-dashboard-rules.md` Rule 3 cannot work inside the email itself — the JS that copies to clipboard would be removed before Blog Track ever opened the email.

Instead, each topic in the email links directly to its section in the hosted dashboard (where the buttons DO work). The flow:

1. Blog Track opens Monday email
2. Picks the topic he wants to post today
3. Clicks "Open in dashboard" link
4. Dashboard opens at that topic's day card
5. Blog Track clicks Copy Content button → content copied → Blog Track pastes into the publishing platform

#### Linking Convention (Deep-Link Anchors)

For the email's links to work, the hosted production calendar must include stable section IDs:

- Each day card: `<section id="day-{day-name}">` (e.g., `id="day-monday"`)
- Each topic within a day: `<div id="topic-{slug}">` (e.g., `id="topic-epa-market-update-april-2026"`)

Email link format: `https://graehamwatts.github.io/online-content/dashboards/weekly-calendars/{YYYY-MM-DD}-production-calendar-v6.html#topic-{slug}`

When the dashboard renders, ALL topics across all three tiers must have stable IDs even if they don't appear in the day-card layout (third-tier topics might live in a "Backup Options" section that's expanded by default but doesn't have its own day slot).

#### Monday Email HTML Template

Email-safe HTML — table-based layout, inline styles, no external CSS, no JS. Tested in Gmail, Outlook, Apple Mail.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Your Content Week — [DATE RANGE]</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f4f5f7;color:#2d3748;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:640px;margin:0 auto;background:#ffffff;">
    <!-- Header -->
    <tr>
      <td style="padding:32px 32px 16px;background:#1B2A4A;color:#ffffff;">
        <h1 style="margin:0;font-size:20px;font-weight:700;letter-spacing:-0.5px;">Your Content Week — [DATE RANGE]</h1>
        <p style="margin:8px 0 0;font-size:13px;color:rgba(255,255,255,0.7);">[N] topics scored. Pick from any tier — top tier is the data's strongest pick this week.</p>
      </td>
    </tr>

    <!-- Top Tier -->
    <tr>
      <td style="padding:24px 32px 8px;">
        <div style="display:inline-block;padding:4px 10px;background:#C5A258;color:#1B2A4A;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;border-radius:4px;">TOP TIER · MUST CREATE</div>
        <p style="margin:8px 0 16px;font-size:13px;color:#718096;">Highest Opportunity Score (22-25). The data's strongest pick.</p>
      </td>
    </tr