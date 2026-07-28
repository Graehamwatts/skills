---
name: github-repo-analyzer
description: "GitHub Repository & Developer Activity Analyzer. Use ANY time user mentions: GitHub repo review, code review, developer activity, commit history analysis, PR review, pull request audit, repo health check, code quality audit, developer productivity, sprint review, dev team analysis, GitHub audit, repo analysis, codebase review..."
---

# GitHub Repository & Developer Activity Analyzer

**Before starting, read the reference files:**
- `references/review-criteria.md` — Defines the analysis framework, flag system, and report structure

## Report Format

### Flag System

**🔴 CRITICAL** — Immediate attention needed
**🟡 WARNING** — Needs attention soon
**🟢 WATCH** — Monitor, not urgent

### Report Sections

**Section 0 — Repo Attribution & Verification**
- Repo Attribution Table showing which repos belong to the dev team vs client vs previous team
- External tool development status (detected / confirmed / not detected)
- Migration compliance status (if client has made migration requests)
- Previous developers identified and excluded

**Section 1 — Executive Summary**
- Repository name, analysis period, total contributors active
- Overall health score (Healthy / Needs Attention / At Risk)
- Top 3 findings that need action
- Quick stats: commits, PRs merged, avg merge time, open issues
- External tool workflow status (if applicable)

**Section 2 — Repository Health**
- Activity trends, branch hygiene, CI status, documentation state
- Governance & ownership assessment
- Comparison to previous period if data available

**Section 3 — Developer Scorecards**
For each developer:
- Flag level (Critical/Warning/Watch/Healthy)
- Activity summary (commits, PRs, reviews)
- Push pattern (incremental vs bulk)
- Strengths observed
- Areas for improvement
- Specific recommendations

For ghost developers (billed but no activity):
- Flag as Critical
- Include fairness section with possible explanations
- Specific verification steps the client should take

**Section 4 — Team Dynamics**
- Workload distribution chart/breakdown
- Review network (who reviews whom)
- Collaboration patterns
- Knowledge silo risks
- Billed vs visible developer gap analysis

**Section 5 — Action Items**
Numbered, specific, actionable items prioritized as HIGH / MEDIUM / LOW

**Section 6 — Recommendations**
Process improvements based on patterns observed, including:
- External tool migration plan (if applicable)
- PR/review workflow requirements
- CI/CD setup recommendations
- Governance improvements

## Output Options

Ask the user how they want the report:

1. **In-chat summary** — Quick overview right here in the conversation
2. **HTML report** — Branded, formatted report saved as a file (recommended for sharing)
3. **Markdown report** — Clean markdown file for documentation
4. **Spreadsheet** — Developer metrics in an Excel file for tracking over time

Default to HTML report unless the user specifies otherwise.
