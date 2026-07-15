# Persistent scheduling for the Daily Gmail Triage

This repo runs a daily Gmail triage for Top Tax Pros. The triage logic lives in one
place: **`.claude/commands/daily-triage.md`** (run it any time by typing `/daily-triage`).

This doc explains how to make it run **unattended every morning** and — importantly —
which mechanisms actually reach Gmail and which don't.

> **Note:** the triage is now bundled into the combined **`/daily-brief`** command (Gmail
> triage + GoHighLevel conversation sweep in one report). For the 8:00 AM run, schedule a
> single trigger for `/daily-brief` — see `.claude/GHL-SCHEDULING.md`. Run `/daily-triage`
> standalone any time you want just the email pass.

## The constraint that drives the design

The Gmail connection is an **interactively-authenticated MCP server** tied to the
Claude account. Whether a scheduled run can label your inbox depends entirely on
whether that Gmail auth is present in the run's environment:

| Mechanism | Fires daily unattended? | Reaches Gmail? | Verdict |
|---|---|---|---|
| **Claude Code on the web — scheduled trigger** | ✅ | ✅ (launches a real web session under your account) | **Use this** |
| In-session cron (`CronCreate`) | Only while a session stays alive; auto-expires in 7 days | ✅ | Fallback / proof-of-concept |
| Manual `/daily-triage` | ❌ (you trigger it) | ✅ | Always-works backstop |
| GitHub Action (`schedule:` cron) | ✅ | ❌ — a CI runner has **no Gmail OAuth** | **Do not use for this** |

A GitHub Action *can* run Claude headlessly on a cron, but the runner does not carry
your Gmail MCP credentials, so the triage would fire on time and then be unable to read
or label the inbox. That's why this repo does **not** ship an Actions workflow for the
triage.

## Recommended setup — Claude Code web scheduled trigger

1. Open this repo's environment in Claude Code on the web.
2. Create a **Scheduled trigger** (see
   https://code.claude.com/docs/en/claude-code-on-the-web for the current UI).
3. Configure it to start a session that runs: `/daily-triage`
4. Schedule: **7:30 AM America/Los_Angeles, daily**.

Because the trigger starts a normal web session under your account, the Gmail MCP is
connected exactly as in an interactive session, and the `SessionStart` hook
(`.claude/hooks/session-start.sh`) preps the environment first.

The session's digest output appears **inside that session** — it is not emailed or
pushed anywhere. Open the session to read it (or ask the assistant in a later turn to
summarize the latest run).

## In-session cron fallback

While a session is alive you can arm a same-session daily job:

> "Re-arm the daily triage cron for 7:30 AM Pacific."

This uses `CronCreate` (`32 14 * * *` UTC). Caveats: it is **session-bound** (dies when
the session/container ends) and **auto-expires after 7 days**. Good for a quick test or
a single active day; not a substitute for the scheduled trigger.

## Manual backstop

Any time, in any session for this repo: type **`/daily-triage`**. This is the durable
source of truth and always works because it runs in your authenticated session.
