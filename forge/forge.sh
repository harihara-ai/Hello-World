#!/usr/bin/env bash
# purpose: one entry point for the forge stages (check, tangle, lint, selftest, harden, certify, package).
# Usage: forge/forge.sh <stage|all> [--from STAGE] [--to STAGE]
# Env:   ROUNDS (default 6) caps hardening rounds.
set -euo pipefail
cd "$(dirname "$0")/.."

STAGES=(check tangle lint selftest harden certify package)
SRC="proposal/modules"
LOCK="kit.lock"
WS="workspace"

stage_check() {
  command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
  command -v git >/dev/null || { echo "git missing"; exit 1; }
  command -v claude >/dev/null || echo "WARN: claude CLI not found (needed for harden and certify)"
  [ -f proposal/north-star-v2.md ] || { echo "Missing proposal/north-star-v2.md. Export the doc as Markdown and save it there."; exit 1; }
  echo "check ok"
}

stage_tangle() {
  [ -d "$SRC" ] || { echo "No $SRC yet. Phase 1 (split) creates it."; exit 1; }
  python3 -I forge/tangle.py "$SRC" "$LOCK" "$WS"
}

stage_lint() {
  python3 -I forge/kit_lint.py "$WS" "$WS/kit.manifest.yml"
}

stage_selftest() {
  python3 -I -m unittest discover -s forge/tests
  if [ -f "$WS/tests/run.sh" ]; then bash "$WS/tests/run.sh"; fi
}

stage_harden() {
  bash forge/ralph.sh "${ROUNDS:-6}"
}

stage_certify() {
  command -v claude >/dev/null || { echo "claude CLI needed"; exit 1; }
  claude -p "$(cat forge/prompts/certify.md)"
}

stage_package() {
  mkdir -p dist
  [ -f hardening/evidence/EVIDENCE.md ] || echo "WARN: no evidence pack; package is UNCERTIFIED"
  out="dist/northstar-kit.zip"
  rm -f "$out"
  python3 -I - <<'PY'
import os, zipfile
out = "dist/northstar-kit.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for base in ("workspace", "hardening/evidence", "hardening/findings.md"):
        if os.path.isfile(base):
            z.write(base)
        elif os.path.isdir(base):
            for root, _d, files in os.walk(base):
                for f in files:
                    p = os.path.join(root, f)
                    z.write(p)
    for f in ("kit.lock", "README.md"):
        if os.path.isfile(f):
            z.write(f)
print("built", out)
PY
}

target="${1:-}"; shift || true
from="check"; to="package"
while [ $# -gt 0 ]; do
  case "$1" in
    --from) from="$2"; shift 2 ;;
    --to) to="$2"; shift 2 ;;
    *) echo "unknown flag $1"; exit 2 ;;
  esac
done

idx() { for i in "${!STAGES[@]}"; do [ "${STAGES[$i]}" = "$1" ] && { echo "$i"; return; }; done; echo -1; }

if [ "$target" = "all" ]; then
  a=$(idx "$from"); b=$(idx "$to")
  [ "$a" -ge 0 ] && [ "$b" -ge "$a" ] || { echo "bad --from/--to"; exit 2; }
  for ((i=a; i<=b; i++)); do echo "== ${STAGES[$i]}"; "stage_${STAGES[$i]}"; done
elif [ "$(idx "$target")" -ge 0 ]; then
  "stage_${target}"
else
  echo "usage: forge.sh <check|tangle|lint|selftest|harden|certify|package|all> [--from S] [--to S]"; exit 2
fi
