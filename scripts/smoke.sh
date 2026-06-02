#!/usr/bin/env bash
#
# Local live smoke test for Edge.
#
# Confirms your Odds API key and network reach the live API, then runs a couple
# of real commands. Run this on your own machine (not a network-restricted
# cloud session).
#
#   export ODDS_API_KEY=your_key
#   ./scripts/smoke.sh                  # defaults to baseball_mlb
#   ./scripts/smoke.sh basketball_nba   # or any sport key from `edge sports`
#
# Exit code is 0 only if every step passes.

set -u

SPORT="${1:-baseball_mlb}"
pass=0
fail=0

# Resolve the edge CLI: prefer an installed `edge`, else run the module.
if command -v edge >/dev/null 2>&1; then
  EDGE=(edge)
else
  EDGE=(python3 -m edge.cli)
fi

step() {
  # step "Description" cmd...
  local desc="$1"; shift
  printf '== %s\n' "$desc"
  if "$@"; then
    printf 'PASS: %s\n\n' "$desc"
    pass=$((pass + 1))
  else
    printf 'FAIL: %s\n\n' "$desc"
    fail=$((fail + 1))
  fi
}

if [ -z "${ODDS_API_KEY:-}" ]; then
  echo "ODDS_API_KEY is not set. Run: export ODDS_API_KEY=your_key" >&2
  exit 2
fi

echo "Using sport: ${SPORT}"
echo "CLI: ${EDGE[*]}"
echo

# 1. Cheapest possible check: lists in-season sports (free, validates the key).
step "list sports (validates key + connectivity)" \
  "${EDGE[@]}" sports

# 2. Real odds + value scan for the chosen sport.
step "live +EV scan for ${SPORT}" \
  "${EDGE[@]}" scan --live --sport "${SPORT}"

# 3. Train a model on real recent results (no-op-safe if none are in window).
step "train team model on live results for ${SPORT}" \
  "${EDGE[@]}" train --model team --live --sport "${SPORT}" --out /tmp/edge-smoke-team.json

echo "----------------------------------------"
echo "Summary: ${pass} passed, ${fail} failed"
[ "${fail}" -eq 0 ] && echo "ALL PASS" || echo "SOME FAILED"
exit "$([ "${fail}" -eq 0 ] && echo 0 || echo 1)"
