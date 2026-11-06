#!/usr/bin/env bash
# purpose: run the hardening round prompt repeatedly (a Ralph loop) until STOP, a human checkpoint, or the round cap.
# Usage: forge/ralph.sh [MAX_ROUNDS]
# Cost cannot be read reliably from inside the loop. MAX_ROUNDS is the hard stop; watch your usage dashboard too.
set -euo pipefail
cd "$(dirname "$0")/.."
MAX="${1:-6}"
mkdir -p hardening/rounds

for ((i=1; i<=MAX; i++)); do
  [ -f hardening/STOP ] && { echo "STOP file found: stop rules hold."; exit 0; }
  [ -f hardening/HUMAN_CHECK.md ] && { echo "Waiting for human review: see hardening/HUMAN_CHECK.md. Delete it to continue."; exit 0; }
  echo "== round $i of $MAX"
  claude -p "$(cat forge/prompts/round.md)" || { echo "round $i failed"; exit 1; }
done
echo "Round cap reached without STOP. Review hardening/findings.md."
exit 3
