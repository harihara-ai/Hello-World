purpose: working source for the scripts components of the kit (tangled into workspace/).

# Scripts

Helpers used by gates and commands.

## script.gateio

Shared gate I/O so gates stay one-job files.

````python file=kit/scripts/gateio.py
"""purpose: shared I/O for gates: read JSON input (file or '-'), print JSON result, return the exit code."""
import json
import sys


class UsageError(Exception):
    pass


def read_input(argv):
    if len(argv) != 2:
        raise UsageError("usage: %s INPUT.json|-" % argv[0])
    if argv[1] == "-":
        return json.load(sys.stdin)
    with open(argv[1], encoding="utf-8") as fh:
        return json.load(fh)


def finding(rule, message, where="", severity="fail"):
    return {"rule": rule, "severity": severity, "where": where, "message": message}


def emit(gate, findings, **extra):
    ok = not any(f["severity"] == "fail" for f in findings)
    print(json.dumps(dict({"gate": gate, "pass": ok, "findings": findings}, **extra), indent=1))
    return 0 if ok else 1


def run(gate, check, argv=None):
    """Call check(payload) -> (findings, extra). Exit 0 pass, 1 fail, 2 bad input."""
    argv = argv or sys.argv
    try:
        payload = read_input(argv)
        if not isinstance(payload, dict):
            raise UsageError("input must be a JSON object")
        findings, extra = check(payload)
    except (UsageError, OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"gate": gate, "pass": False, "error": str(e), "findings": []}))
        return 2
    return emit(gate, findings, **extra)
````

## script.policy

Flat YAML parser; no third-party dependency.

````python file=kit/scripts/policy.py
"""purpose: parse the flat policy.yml format (key: number | word | [list]) without third-party YAML."""
import re

KEY = re.compile(r"^([a-z][a-z0-9_]*):\s*(.*)$")


def _scalar(v):
    v = v.strip().strip("'\"")
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def parse(text):
    out = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split(" #")[0].rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = KEY.match(line)
        if not m:
            raise ValueError("line %d: not 'key: value'" % n)
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("["):
            if not v.endswith("]"):
                raise ValueError("line %d: unclosed list" % n)
            inner = v[1:-1].strip()
            out[k] = [_scalar(x) for x in inner.split(",")] if inner else []
        else:
            out[k] = _scalar(v)
    return out


def load(path):
    with open(path, encoding="utf-8") as fh:
        return parse(fh.read())
````

## script.gate_check

Section 10.6. Runs floor gates plus repo gates; a repo cannot drop a floor gate.

````python file=kit/scripts/gate_check.py
#!/usr/bin/env python3
"""purpose: run the gates for 'ready' or 'done' (kit floor list plus repo list) and merge their JSON.

Usage: gate_check.py ready|done --repo DIR --change openspec/changes/<name> [--policy FILE] [--also g1,g2]
Each gate reads <change>/inputs/<gate>.json if present; gate_check adds defaults and the policy.
Writes <change>/gates-<stage>.json. Exit 0 all pass, 1 any fail, 2 bad usage.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
FLOOR = os.path.join(KIT, "core", "policy.yml")
KNOWN = ["injection", "spec_lint", "granularity", "trace_check", "coverage", "diff_scope", "policy_guard", "flaky"]
sys.path.insert(0, HERE)
import policy  # noqa: E402


def texts_under(ch):
    out = []
    for root, _d, files in os.walk(ch):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), ch)
            out.append({"source": "file name %s" % rel, "text": name})
            if name.endswith(".md"):
                with open(os.path.join(root, name), encoding="utf-8", errors="ignore") as fh:
                    out.append({"source": rel, "text": fh.read()})
    return out


def payload_for(gate, a, pol, policy_path):
    p = {}
    path = os.path.join(a.change, "inputs", gate + ".json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            p = json.load(fh)
    p["policy"] = pol
    if gate == "spec_lint":
        p.setdefault("spec", os.path.join(a.change, "spec.md"))
    elif gate == "injection":
        p["texts"] = texts_under(a.change) + p.get("texts", [])
    elif gate == "trace_check":
        p.setdefault("spec_dirs", [a.change])
    elif gate == "policy_guard":
        p = {"old": FLOOR, "new": policy_path, "signoff": os.path.join("docs", "ai", "policy-signoff.json")}
    return p


def run_gate(gate, payload):
    proc = subprocess.run([sys.executable, "-I", "-B", os.path.join(KIT, "gates", gate + ".py"), "-"],
                          input=json.dumps(payload), capture_output=True, text=True)
    try:
        out = json.loads(proc.stdout)
    except ValueError:
        out = {"gate": gate, "pass": False, "error": (proc.stdout + proc.stderr)[-500:], "findings": []}
    out["pass"] = bool(out.get("pass")) and proc.returncode == 0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["ready", "done"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--change", required=True)
    ap.add_argument("--policy")
    ap.add_argument("--also", default="")
    a = ap.parse_args()
    also = [g for g in a.also.split(",") if g]
    if any(g not in KNOWN for g in also):
        ap.error("--also accepts only: %s" % ", ".join(KNOWN))
    if os.path.isabs(a.change) or ".." in a.change.split("/"):
        ap.error("--change must be a path inside the repo")
    os.chdir(a.repo)
    policy_path = a.policy or os.path.join("docs", "ai", "policy.yml")
    if not os.path.isfile(policy_path):
        policy_path = FLOOR
    floor, pol = policy.load(FLOOR), policy.load(policy_path)
    key = a.stage + "_gates"
    gates = []
    for g in floor.get(key, []) + pol.get(key, []) + also:
        if g in KNOWN and g not in gates:
            gates.append(g)
    results = [run_gate(g, payload_for(g, a, pol, policy_path)) for g in gates]
    report = {"stage": a.stage, "pass": all(r["pass"] for r in results), "gates": results}
    with open(os.path.join(a.change, "gates-%s.json" % a.stage), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report, indent=1))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
````

## script.state

Section 17.1.

````bash file=kit/scripts/state.sh
#!/usr/bin/env bash
# purpose: print the Genie state as JSON: branch, ticket key, change folder, next step, last gate result.
# Usage: bash scripts/state.sh   (run from anywhere inside the repo)
set -u
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || branch=""
root=$(git rev-parse --show-toplevel 2>/dev/null) || root="$PWD"
change="${branch##*/}"
ticket=$(printf '%s' "$branch" | grep -oE '[A-Z][A-Z0-9]+-[0-9]+' | head -1)
exec python3 -I -B -c '
import glob, json, os, sys
branch, ticket, change, root = sys.argv[1:5]
d = os.path.join(root, "openspec", "changes", change) if change else ""
state = {"branch": branch or None, "ticket": ticket or None, "change": change or None,
         "change_exists": bool(d) and os.path.isdir(d), "next": None, "last_gate": None}
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
