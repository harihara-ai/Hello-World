#!/usr/bin/env bash
# Traceability check: every REQ ID in the specs must appear in at least one test.
# Usage: scripts/trace_check.sh [change-name]
#   no argument     -> check openspec/specs and all active changes
#   change-name     -> check only openspec/changes/<change-name>
# Env: TEST_DIRS (space separated, default: "test tests spec src")
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 2

ID_RE='REQ-[A-Z0-9]+-[0-9]+'
TEST_DIRS="${TEST_DIRS:-test tests spec src}"

if [ $# -ge 1 ]; then
  SPEC_PATHS="openspec/changes/$1"
else
  SPEC_PATHS="openspec/specs openspec/changes"
fi

spec_ids=""
for p in $SPEC_PATHS; do
  [ -d "$p" ] && spec_ids="$spec_ids
$(grep -rhoE "$ID_RE" "$p" --include='*.md' 2>/dev/null | grep -v '^$')"
done
spec_ids=$(printf '%s\n' "$spec_ids" | grep -E "^$ID_RE\$" | sort -u)

if [ -z "$spec_ids" ]; then
  echo "trace_check: no requirement IDs found in: $SPEC_PATHS"
  exit 2
fi

dirs=""
for d in $TEST_DIRS; do [ -d "$d" ] && dirs="$dirs $d"; done
if [ -z "$dirs" ]; then
  echo "trace_check: none of the test dirs exist: $TEST_DIRS (set TEST_DIRS)"
  exit 2
fi

# shellcheck disable=SC2086
test_ids=$(grep -rhoE "$ID_RE" $dirs 2>/dev/null | sort -u)

missing=$(comm -23 <(printf '%s\n' "$spec_ids") <(printf '%s\n' "$test_ids"))
status=0

if [ -n "$missing" ]; then
  echo "FAIL: requirements with no test:"
  printf '  %s\n' $missing
  status=1
fi

if [ $# -eq 0 ]; then
  all_spec_ids=$(grep -rhoE "$ID_RE" openspec 2>/dev/null | sort -u)
  orphans=$(comm -13 <(printf '%s\n' "$all_spec_ids") <(printf '%s\n' "$test_ids"))
  if [ -n "$orphans" ]; then
    echo "WARN: tests mention IDs that are not in any spec:"
    printf '  %s\n' $orphans
  fi
fi

[ $status -eq 0 ] && echo "OK: every requirement has at least one test"
exit $status
