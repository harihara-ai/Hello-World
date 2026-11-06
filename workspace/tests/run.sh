#!/usr/bin/env bash
# purpose: run the kit's own tests: T1 unit, T2 contract, T3 mutation.
set -euo pipefail
cd "$(dirname "$0")"
for level in unit contract mutation; do
  echo "== $level"
  python3 -I -B -m unittest discover -s "$level" -p 'test_*.py'
done
