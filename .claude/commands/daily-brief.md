---
description: Top Tax Pros morning Daily Brief — runs the Gmail triage and the GoHighLevel conversation sweep, then delivers one combined brief
---

# Top Tax Pros — Daily Brief

You are the operations assistant for Top Tax Pros (tax prep, bookkeeping, entity setup;
Lakewood, CA). This is the single morning brief: it combines two checks into one report so
nothing — inbound email OR client conversation — goes unanswered. **Read + report only.**
No email is sent; no GoHighLevel message is sent. Everything actionable is drafted and
waits for one-click approval.

Run the two parts below, then deliver ONE combined brief. Each part's rules live in its own
command file — follow them as the source of truth so behavior never drifts.

## Part A — Gmail triage

Execute `.claude/commands/daily-triage.md` **Steps 1–6** exactly (setup → fetch untriaged
inbox → classify → safety flags → follow-up sweep → build digest). This still applies the
Gmail labels as described there — that labeling is expected.

**Skip that file's Step 7** (do NOT create a separate "Daily Triage" Gmail draft). Hold the
digest content for the combined delivery below.

## Part B — GoHighLevel conversation sweep

Execute `.claude/commands/ghl-conversation-sweep.md` **Steps 1–3** exactly (pull
"customer spoke last" threads → classify → pre-draft replies for the 🔴 bucket).

**Skip that file's Step 4–5 delivery** — hold the classified results and drafts for the
combined brief below.

## Part C — Build the combined brief

Title: **"Top Tax Pros — Daily Brief [today's date]"**. Lead with the summary, then keep
the two areas clearly separated so each is skimmable:

- **Top line:** one sentence covering both — e.g. "N new emails triaged (X need action, Y
  leads); M conversations where a client spoke last (Z need a reply, W missed calls."

- **💬 Conversations (GoHighLevel)** — from Part B:
  - 🔴 **Needs your reply** — name + channel + the one-line question, then the full draft
    reply in a quote block; note any `[placeholders]` to confirm.
  - ⚠️ **Handle personally** — name + why (no draft).
  - 📵 **Missed calls to return** — name/number list.
  - (⚪ no-reply / 🚫 ignore condensed to a one-line count each.)

- **📬 Email (Gmail)** — from Part A:
  - 🔴 Action: Me — client + what's needed.
  - 🟡 Waiting >5 days — who to nudge.
  - ⚡ Deadlines — what's due and when.
  - 🟢 New / uncontacted leads — name + contact + next step.
  - ⚠️ Verify — anything flagged by the triage safety step.

## Part D — Deliver

1. **In-mailbox copy (always).** Create ONE Gmail **draft** (`create_draft`) with the whole
   combined brief — `to`: `bcook31@toptaxpros.com`, `subject`:
   `Top Tax Pros — Daily Brief [today's date]`, `body`: the full brief from Part C. Note the
   Gmail connector is **draft-only — it cannot send** — so this is the readable copy that sits
   in Drafts; it does not itself notify.

2. **iPhone notification (scheduled/unattended runs).** Fire a push so Brian's phone buzzes:
   call the push-notification tool with a one-line summary, under 200 chars, leading with the
   count that matters — e.g. `Daily Brief ready — 2 conversations need a reply, 1 new lead.
   Full brief in Gmail Drafts.` (Pushes to the phone when the Claude app / remote control is
   connected; it's automatically skipped when Brian is already at the session.)

3. **Optional full-text email to the inbox.** If a real email (not just a draft) is wanted,
   send the brief to Brian via **GoHighLevel email** (GHL can send; Gmail cannot) — a
   **self-send to `bcook31@toptaxpros.com` only**, never to anyone else. Resolve/create the
   self-contact, then `send-a-new-message` with `type: Email`. Caveat: GHL sends are
   approval-gated, so this may not complete on a fully unattended run — the push (step 2) is
   the reliable phone alert.

When run interactively, print the brief and **skip the push** (Brian's already here); ask
which conversation drafts to send. To send an approved client reply, use `send-a-new-message`
(requires approval). **Never send a client message on an unattended run — self-notification only.**
