#!/usr/bin/env bash
# purpose: print the Genie state as JSON: branch, ticket key, change folder, next step, last gate result, bootstrapped.
# last_gate is a hint only: it is a file in the repo, so commands re-run gate_check before relying on it.
# Usage: bash scripts/state.sh   (run from anywhere inside the repo)
set -u
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || branch=""
root=$(git rev-parse --show-toplevel 2>/dev/null) || root="$PWD"
change="${branch##*/}"
ticket=$(printf '%s' "$branch" | grep -oE '[A-Z][A-Z0-9]+-[0-9]+' | head -1)
exec python3 -I -B -c '
import glob, json, os, sys
branch, ticket, change, root = sys.argv[1:5]
changes = os.path.join(root, "openspec", "changes")
names = sorted((n for n in (os.listdir(changes) if os.path.isdir(changes) else []) if n in change), key=len)
change = names[-1] if names else change  # a code branch may add a suffix (two PRs per change)
d = os.path.join(changes, change) if change else ""
state = {"branch": branch or None, "ticket": ticket or None, "change": change or None,
         "change_exists": bool(d) and os.path.isdir(d), "next": None, "last_gate": None,
         "bootstrapped": os.path.isfile(os.path.join(root, "docs", "ai", "index.json"))}
status = os.path.join(d, "status.md")
if state["change_exists"] and os.path.isfile(status):
    for line in open(status, encoding="utf-8"):
        if line.startswith("next:"):
            state["next"] = line[5:].strip()
gates = sorted(glob.glob(os.path.join(d, "gates-*.json")), key=os.path.getmtime) if state["change_exists"] else []
if gates:
    with open(gates[-1], encoding="utf-8") as fh:
        g = json.load(fh)
    state["last_gate"] = {"stage": g.get("stage"), "pass": g.get("pass")}
print(json.dumps(state))
' "$branch" "$ticket" "$change" "$root"
