#!/bin/bash
# SessionStart hook: auto-run the live Odds API smoke test in web sessions.
#
# - Only runs in Claude Code on the web (skips local sessions).
# - No-op (exits 0) when ODDS_API_KEY is unset, so sessions without the key
#   stay clean and cost no API quota.
# - When the key is present: installs the package and runs scripts/smoke.sh.
#   NOTE: the scan/train steps of the smoke test consume API quota per run.
set -uo pipefail

# Local sessions: do nothing.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

if [ -z "${ODDS_API_KEY:-}" ]; then
  echo "Live smoke skipped: ODDS_API_KEY not set (no live API calls, no quota used)."
  exit 0
fi

echo "Installing edge (editable)..."
pip install -e . -q 2>&1 | tail -1 || true

echo "Running live smoke test (uses API quota)..."
./scripts/smoke.sh || true

# Always succeed so a failed live check never blocks the session from starting.
exit 0
