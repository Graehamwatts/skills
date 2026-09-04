---
name: daily-content-focus-email
description: Weekdays 7:30 AM PT — Monday builds the week's content production calendar and emails the full 5-topic plan to John/Peter/Ellie (cc Graeham); Tuesday-Friday sends a short "Today's Content Focus" email pulling that day's topic off the live calendar. Reactivated 2026-08-07 as the SMTP-based replacement for the retired N8N daily-Peter-email workflow (REVqxrlAb3CHJumM).
---

You are running the daily content-focus email for Graeham Watts (REALTOR, Intero Real Estate, DRE #01466876). This drives the recurring team cadence documented in `skills/content-calendar/SKILL.md` under "Email Delivery — recipients & cadence (LOCKED — do not re-ask)". Read that section before your first run — it is the source of truth for recipients and cadence; do not re-derive or re-ask.

RECIPIENTS (hardcoded — content/video team, NOT Adrian):
- **To:** John (blog/SEO) `graehamwattsmarketing@gmail.com`, Peter (video) `graehamwattsvideo@gmail.com`, Ellie (video) `graehamwattsvideo2@gmail.com`
- **Cc:** Graeham `graehamwatts@gmail.com`

DELIVERY: SEND directly via SMTP using `skills/switchy-engine/scripts/send_email.py` (Gmail app password read at send time from `Documents/Claude/Skills/gmail-app-password.txt`, never printed). Do NOT use the Gmail MCP for this — it only creates drafts, and these are internal team emails meant to land in the inbox, not sit unread in Drafts. Do NOT stand the old N8N workflow (`REVqxrlAb3CHJumM`, instance `n8n.graehamwattsn8n.com`) back up — it's retired; this scheduled task is its replacement.

STEP 0 — Determine today's branch.
Read the system date. Monday → STEP 1 (weekly plan). Tuesday–Friday → STEP 2 (daily focus). Saturday/Sunday → do nothing, exit.

---

STEP 1 — MONDAY: Build and ship the weekly plan.

1a. Run the `content-calendar` skill's weekly planning workflow (performance pull, search demand, Reddit/audience signal, competitor scan, scoring — see `skills/content-calendar/SKILL.md`) to produce this week's calendar JSON. Save it to `skills/content-creation-engine/outputs/calendar-data/calendar-{YYYY-MM-DD}.json` (Monday's date), matching the schema `weekly-calendar-builder.py` validates (`week_of`, `generated_at`, `goal`, `funnel_mix`, `topics[]` with `slug`, `title`, `day`, `scheduled_date`, `primary_format`, `funnel_tier`, `ghl_keyword`, `opportunity_score`, `priority_axes`, `time_decay_band`, `justification_notes`).

1b. **Gate 1 — overlap check (before anything else touches this calendar):**
```
python skills/content-creation-engine/scripts/weekly_overlap_check.py --calendar skills/content-creation-engine/outputs/calendar-data/calendar-{YYYY-MM-DD}.json
```
Exit 1 means a topic overlaps the last 4 weeks (history + in-production). Replace the topic or write a justification into the calendar's `justification_notes` before proceeding — do not ship a HIGH-risk overlap silently.

1c. Render the dashboard:
```
python skills/content-calendar/templates/weekly-calendar-builder.py skills/content-creation-engine/outputs/calendar-data/calendar-{YYYY-MM-DD}.json online-content/dashboards/weekly-calendars/{YYYY-MM-DD}-production-calendar-v6.html
```
Follow `skills/content-creation-engine/references/weekly-dashboard-rules.md` (Rules 9-11: no orphan hrefs, all 10 required sections, single canonical file — no `-all`/`-blogs`/`-videos`/`-research` variants) and `skills/website-builder/references/screenshot-loop.md` (min 1 iteration) before publishing.

1d. **Gate 2 — brand/DRE + truncation check (before sending or publishing):**
```
python skills/content-creation-engine/scripts/verify_output_brand.py online-content/dashboards/weekly-calendars/{YYYY-MM-DD}-production-calendar-v6.html
```
This is a fail-closed gate (mirrors the old N8N "Validate Date + DRE" node): exit 2 means a blocked brand value (the blocklisted DRE in `skills/shared-references/identity.json`) or a truncated file. On failure, STOP — do not publish, do not send. Instead send ONE alert email to `graehamwatts@gmail.com` only, subject `[ALERT] Weekly content calendar failed brand/DRE gate`, body naming the exact failure, and end the run.

1e. Push the HTML (and the calendar JSON alongside it, for Tue-Fri to read) to GitHub Pages per the repo's publish flow, then confirm the live URL loads.

1f. **Gate 3 — topic history (after the calendar ships, not before):**
```
python skills/content-creation-engine/scripts/update_topic_history.py --calendar skills/content-creation-engine/outputs/calendar-data/calendar-{YYYY-MM-DD}.json
```
Skipping this silently breaks next week's freshness/overlap check — do not skip it.

1g. Send the weekly email. To the recipients above, subject `Week of {Mon date}: Content Production Plan`. Body: the full 5-topic plan (day, title, format, funnel tier, GHL keyword, one-line hook per topic) plus the live dashboard link. Attach the rendered HTML (or link only if the attachment is large — link is sufficient since the dashboard is the actual production surface). Send via `send_email.py`:
```
python skills/switchy-engine/scripts/send_email.py \
  --to graehamwattsmarketing@gmail.com --to graehamwattsvideo@gmail.com --to graehamwattsvideo2@gmail.com --to graehamwatts@gmail.com \
  --subject "Week of {Mon date}: Content Production Plan" \
  --html-file <path to composed weekly email HTML>
```

---

STEP 2 — TUESDAY-FRIDAY: Daily focus email.

2a. Locate this week's calendar JSON: the newest `skills/content-creation-engine/outputs/calendar-data/calendar-*.json` whose `week_of` covers today. If none exists (Monday's run failed or was skipped), send the alert email from 1d instead (`[ALERT] No live weekly calendar found for today's focus email`) and stop — do not guess a topic.

2b. From `topics[]`, filter to the entry whose `day` matches today's weekday name. If more than one topic is scheduled for today, include all of them.

2c. **Gate — reuse Gate 2** (`verify_output_brand.py`) against the composed email body before sending. Same fail-closed rule: on failure, alert Graeham only, do not send to the team.

2d. Compose and send a short "Today's Content Focus" email. Subject: `Today's Content Focus — {weekday}, {date}`. Body, per topic: title, primary format, the hook (first 3 seconds / opening line), GHL keyword + CTA, funnel tier, and a deep link to the topic's section on the live dashboard (`{dashboard_url}#topic-{slug}`, per the anchor convention in `skills/content-calendar/references/dashboard-architecture.md`). Keep it short — this is a reminder/trigger, not the production package itself; the linked dashboard and, if it exists, the topic's single-topic production dashboard are where the actual scripts/prompts live. Send the same way as 1g, to the same recipient list, same DRE/date QC rules (`skills/content-creation-engine/references/production-hardening.md` — Date & Year QC block) applied to any stat or date mentioned in the email body.

---

GUARDRAILS:
- Never send to a past-client or external address — this task's only recipients are the four addresses listed above.
- Never skip Gate 2 (brand/DRE) before a send, Monday or daily. It exists because a wrong DRE has leaked into shipped content ten times before (see `shared-references/dre-leak-incident-log.md`) — the gate is what stops the eleventh.
- If the Gmail app password file is missing, `send_email.py` will exit non-zero rather than silently failing to send — treat that as a hard stop, report it to Graeham, do not fall back to a Gmail draft (the whole point of this task is that a draft doesn't get seen).
- Do not modify `pcfs-cma-autobuild-weekly` — unrelated task, same folder tree.

STEP 3 — Report back.
Summarize for Graeham: which branch ran (weekly/daily), which gates passed/failed, who the email went to, and the live dashboard URL if applicable. Keep it concise.
