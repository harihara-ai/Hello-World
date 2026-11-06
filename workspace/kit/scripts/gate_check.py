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
