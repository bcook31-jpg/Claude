#!/bin/bash
# SessionStart hook for Claude Code on the web.
# - Installs the repo's Python dependencies so tests / tooling work in web sessions.
# - Injects a reminder that the daily Gmail triage lives at /daily-triage.
# Runs synchronously: the session waits until this finishes (deps guaranteed ready).
set -euo pipefail

# Only run in the remote (Claude Code on the web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Install dependencies (idempotent; cached after first run). Logs go to stderr so
# stdout stays clean for the JSON context payload below.
{
  if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install --quiet -r "$PROJECT_DIR/requirements.txt" || echo "pip install (requirements) failed" >&2
  fi
  pip install --quiet pytest || echo "pip install pytest failed" >&2
} 1>&2

# Add a short reminder to the session context.
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Daily Gmail triage for Top Tax Pros is available as the /daily-triage command (.claude/commands/daily-triage.md). For unattended daily runs at 7:30 AM Pacific, this repo expects a Claude Code on the web *scheduled trigger* that runs /daily-triage — see .claude/SCHEDULING.md. Do NOT auto-run the triage on session start unless asked."}}
JSON
