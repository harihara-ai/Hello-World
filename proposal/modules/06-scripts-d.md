purpose: working source for the scripts components of the kit (tangled into workspace/).

# Scripts

Helpers used by gates and commands.

## script.state

Section 17.1.

````bash file=kit/scripts/state.sh
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
````

## script.probe

Sections 4, 5. Trap 10.

````python file=kit/scripts/probe.py
#!/usr/bin/env python3
"""purpose: pick one tool per capability from probe results using the ranked fallbacks (section 4).

Input: {"results": {tool: {"ok": bool, "reason": str}}, "capabilities": [names]}. Tools not probed are skipped.
Usage: probe.py INPUT.json|- [--out docs/ai/toolchain.md]. Exit 1 when a capability has no working tool (ask).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gateio import UsageError, finding, run  # noqa: E402

RANKED = {  # keyed by adapter name in kit.manifest.yml; add a tool by adding its adapter first
    "codenav": ["serena", "ctags"],
    "tracker": ["github", "jira", "azdo", "file"],
}


def choose(cap, results):
    rejected = []
    for tool in RANKED[cap]:
        r = results.get(tool)
        if r is None:
            continue
        if r.get("ok"):
            return tool, rejected
        rejected.append({"tool": tool, "reason": r.get("reason", "probe failed")})
    return None, rejected


def toolchain_md(caps):
    rows = ["purpose: tools chosen by the /bootstrap probe, with the reason for each fallback.", "",
            "| Capability | Chosen | Rejected (reason) |", "| --- | --- | --- |"]
    for cap, c in caps.items():
        rej = "; ".join("%s (%s)" % (r["tool"], r["reason"]) for r in c["rejected"]) or "none"
        rows.append("| %s | %s | %s |" % (cap, c["chosen"] or "ASK THE USER", rej))
    return "\n".join(rows) + "\n"


def main(argv):
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]

    def check(p):
        results = p.get("results", {})
        caps = p.get("capabilities") or [c for c, tools in RANKED.items() if any(t in results for t in tools)]
        unknown = [c for c in caps if c not in RANKED]
        if unknown:
            raise UsageError("unknown capability: %s" % unknown)
        chosen = {}
        for c in caps:
            tool, rejected = choose(c, results)
            chosen[c] = {"chosen": tool, "rejected": rejected}
        if out:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(toolchain_md(chosen))
        f = [finding("no_tool", "no working tool for %s: ask the user and record the answer" % c, c)
             for c, v in chosen.items() if v["chosen"] is None]
        return f, {"capabilities": chosen}

    return run("probe", check, argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
````
