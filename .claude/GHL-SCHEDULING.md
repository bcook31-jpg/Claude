# Scheduling the GoHighLevel plays

Top Tax Pros runs three read-only GoHighLevel "plays" as slash commands. Each reads the
CRM and produces a digest of what needs attention — none of them send messages or move
deals on their own (writes in GHL require per-action approval, so unattended sends are
intentionally out of scope).

| Command | What it catches | Suggested schedule |
|---|---|---|
| `/daily-brief` | **Morning umbrella** — Gmail triage + conversation sweep in one brief | **Daily, 8:00 AM Pacific** |
| `/ghl-conversation-sweep` | Customer messaged last, no reply yet — pre-drafts responses | (bundled into `/daily-brief`) |
| `/ghl-pipeline-sweep` | Uncontacted leads + deals rotting in a stage | Daily, 8:15 AM Pacific |
| `/ghl-doc-chase` | Tax clients we're waiting on for docs + internal prep bottlenecks | Daily during season (Jan–Apr + extension weeks); 8:00 AM Pacific |
| `/ghl-review-followup` | Completed/filed jobs that never got a review request | Weekly, Monday 9:00 AM Pacific |

## The same auth constraint as the Gmail triage

The GoHighLevel MCP is an **interactively-authenticated connector tied to the Claude
account**. A scheduled run can only reach the CRM if that auth is present in the run's
environment — exactly like Gmail (see `.claude/SCHEDULING.md`).

| Mechanism | Fires unattended? | Reaches GHL? | Verdict |
|---|---|---|---|
| **Claude Code on the web — scheduled trigger** | ✅ | ✅ (real web session under your account) | **Use this** |
| In-session cron (`CronCreate`) | Only while a session stays alive; auto-expires in 7 days | ✅ | Fallback / test |
| Manual `/ghl-…` command | ❌ (you trigger it) | ✅ | Always-works backstop |
| GitHub Action (`schedule:` cron) | ✅ | ❌ — CI runner has no GHL OAuth | **Do not use** |

## Recommended setup

1. Open this repo's environment in Claude Code on the web.
2. Create a **Scheduled trigger** (https://code.claude.com/docs/en/claude-code-on-the-web).
3. Point it at the command + schedule from the table above (one trigger per play).

The digest appears **inside that session** — it is not emailed or pushed. Open the
session to read it, or ask in a later turn to summarize the latest run.

## Manual backstop

Any time, in any session for this repo, type the command (e.g. `/ghl-pipeline-sweep`).
This always works because it runs in your authenticated session.

## Turning digests into action

Every play is read-only by design. When you want to act on a digest, run the command
interactively and say yes when it offers to draft the messages or create GHL follow-up
tasks — each write still asks for your approval before it goes out.
