# Top Tax Pros — Automation Roadmap

Living plan for GoHighLevel/QuickBooks/marketing automations. Each play is built as a
`.claude/commands/*.md` slash command, read-and-report (drafts + digests; sends require
approval), and scheduled via a Claude Code on-the-web trigger. See `GHL-SCHEDULING.md`.

## ✅ Live (PR #4)

Daily Brief (Gmail triage + conversation sweep) · conversation sweep · pipeline sweep ·
doc chase · missed-call rapid response · database reactivation · referral/review flywheel ·
AR collections.

## 🔜 Next wave — approved

Ordered by dependency + timing (off-season = data cleanup + advisory revenue).

1. ✅ **CRM data hygiene sweep** (`/ghl-crm-hygiene`) — suppression gaps, bad emails, unnamed
   callers, duplicates (report-only; merges are manual — no GHL merge API), junk records.
   *Built. Read + propose; writes need approval.*
2. ✅ **Reactivation engine** (`/ghl-reactivation-engine`) — detect abandonment/dormancy from
   pipeline+tag state, apply the empty `cre - *` tags so reactivation has fuel.
   *Built. Read + propose; tagging needs approval.*
3. ✅ **Year-end tax planning outreach** (`/ghl-year-end-planning`) — Q4 advisory-call invites
   to business-interest + Bookkeeping-pipeline + entity clients (targets populated signals,
   since `type - *` tags are empty). *Built. Read + draft; sends need approval.*
4. **Owner's weekly scorecard** — one weekly report: leads in, appts, deals won, revenue +
   AR (QuickBooks), reviews. *Always-on; finally puts QuickBooks to work.*

## 🗂️ Backlog — identified, not yet prioritized

- **Client onboarding kickoff** — deal → Onboarding: create QB customer, engagement tasks, welcome steps.
- **Appointment prep & no-show recovery** — brief tomorrow's consults; rebook `no-show` tags.
- **Monthly bookkeeping close tracker** — Bookkeeping pipeline (Monthly Review→Completed) delivery status.
- **Estimated-tax reminders** — quarterly client nudges (Q3 Sep 15, Q4 Jan 15).
- **Weekly SEO/rank report** — Semrush position changes, competitor moves, site audit.
- **Content/social calendar** — Canva collateral + blog, tax-season-timed.

## Held campaigns

- **Signature-stalled reactivation** — prepared July 2026, send hold until **2027-01-15**
  (reminder trigger set). Regenerate the list fresh at send time. See `GHL-SCHEDULING.md`.
