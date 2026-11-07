purpose: working source for the scripts components of the kit (tangled into workspace/).

# Scripts

Helpers used by gates and commands.

## script.gate_check

Section 10.6. Runs floor gates plus repo gates; the type can only add. Sets gate targets, base and sign-off itself (round 1 F03, F08; round 2 G02-G05, G07).

````python file=kit/scripts/gate_check.py
#!/usr/bin/env python3
"""purpose: run the gates for 'ready' or 'done' (kit floor plus repo list; the work type can only add).

Usage: gate_check.py ready|done --repo DIR --change openspec/changes/<name> [--base REF] [--also g1,g2]
Gate targets (spec, change folder, policy, sign-off, git base) are set here; inputs/<gate>.json adds evidence
but cannot redirect a gate. Policy baseline and sign-off come from the base commit. The base defaults to the
remote default branch; CI passes --base (kit/INSTALL.md). Exit 0 all pass, 1 any fail, 2 bad usage.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
FLOOR = os.path.join(KIT, "core", "policy.yml")
KNOWN = ["injection", "policy_guard", "spec_lint", "granularity", "trace_check", "coverage", "diff_scope", "flaky"]
DATA = ("comments/", "fetched/")
PYCACHE = tempfile.mkdtemp(prefix="kit-pycache-")
sys.path.insert(0, HERE)
import policy  # noqa: E402
from kitconst import TYPES  # noqa: E402


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def default_base():
    for ref in ("origin/HEAD", "origin/main", "origin/master"):
        sha = git("merge-base", "HEAD", ref)
        if sha:
            return sha
    return None


def decode(raw):
    for bom, enc in ((b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16"), (b"\xef\xbb\xbf", "utf-8-sig")):
        if raw.startswith(bom):
            return raw.decode(enc, errors="ignore")
    return raw.decode("utf-8", errors="ignore")


def texts_under(ch):
    out, names = [], set()
    for root, _d, files in os.walk(ch):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), ch).replace(os.sep, "/")
            if re.fullmatch(r"gates-\w+\.json", rel):
                continue
            kind = "data" if rel == "ticket.md" or rel.startswith(DATA) else "authored"
            names |= {(seg, kind) for seg in rel.split("/")}
            with open(os.path.join(root, name), "rb") as fh:
                text = decode(fh.read())
            if "\x00" not in text:
                out.append({"source": rel, "text": text, "kind": kind})
    return out + [{"source": "file name %s" % n, "text": n, "kind": k} for n, k in sorted(names)]


def from_base(base, rel):
    """A file as it is in the base commit (written to a temp file), or None."""
    text = git("show", "%s:%s" % (base, rel)) if base else None
    if not text:
        return None
    fd, path = tempfile.mkstemp(suffix=os.path.splitext(rel)[1])
    with os.fdopen(fd, "w") as fh:
        fh.write(text + "\n")
    return path


def payload_for(gate, ctx):
    p, ch = {}, ctx["change"]
    path = os.path.join(ch, "inputs", gate + ".json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            p = json.load(fh)
    p["policy"] = ctx["policy"]
    if gate == "spec_lint":
        p["spec"] = os.path.join(ch, "spec.md")
    elif gate == "injection":
        p["texts"] = texts_under(ch) + list(p.get("texts", []))
    elif gate == "trace_check":
        p = {"spec_dirs": [ch], "type": ctx["type"]}
    elif gate == "policy_guard":
        p = {"old": FLOOR, "baselines": ctx["baselines"], "new": ctx["policy_path"], "signoff": ctx["signoff"]}
    elif gate == "diff_scope":
        p.update(change_dir=ch, no_production=bool(p.get("no_production")) or ctx["no_production"])
        if ctx["base"]:
            p["base"] = ctx["base"]
    elif gate == "coverage" and ctx["base"]:
        p["base"] = ctx["base"]
    return p


def run_gate(gate, payload):
    # pycache_prefix: never load bytecode from a __pycache__ someone planted next to the kit.
    proc = subprocess.run([sys.executable, "-I", "-B", "-X", "pycache_prefix=" + PYCACHE,
                           os.path.join(KIT, "gates", gate + ".py"), "-"],
                          input=json.dumps(payload), capture_output=True, text=True)
    try:
        out = json.loads(proc.stdout)
    except ValueError:
        out = {"gate": gate, "pass": False, "error": (proc.stdout + proc.stderr)[-500:], "findings": []}
    out["pass"] = bool(out.get("pass")) and proc.returncode == 0
    return out


def spec_type(ch):
    try:
        with open(os.path.join(ch, "spec.md"), encoding="utf-8") as fh:
            m = re.search(r"(?m)^Type:\s*(\S+)", fh.read())
    except OSError:
        return "story"
    t = m.group(1).lower() if m else "story"
    return t if t in TYPES else "story"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["ready", "done"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--change", required=True)
    ap.add_argument("--base")
    ap.add_argument("--also", default="")
    a = ap.parse_args()
    also = [g for g in a.also.split(",") if g]
    if any(g not in KNOWN for g in also):
        ap.error("--also accepts only: %s" % ", ".join(KNOWN))
    if not re.fullmatch(r"openspec/changes/[A-Za-z0-9][A-Za-z0-9._-]*/?", a.change) or ".." in a.change:
        ap.error("--change must be openspec/changes/<name>")
    os.chdir(a.repo)
    policy_path = os.path.join("docs", "ai", "policy.yml")
    if not os.path.isfile(policy_path):
        policy_path = FLOOR
    floor, pol = policy.load(FLOOR), policy.load(policy_path)
    wtype = spec_type(a.change)
    rule = TYPES[wtype]
    in_git = git("rev-parse", "--is-inside-work-tree") == "true"
    base = (a.base or default_base()) if in_git else None
    if in_git and not base:
        ap.error("no remote default branch to compare with: pass --base <ref> (CI passes the target branch)")
    signoff = from_base(base, "docs/ai/policy-signoff.json") if in_git else os.path.join("docs", "ai", "policy-signoff.json")
    ctx = {"change": a.change.rstrip("/"), "policy": pol, "policy_path": policy_path, "base": base, "type": wtype,
           "baselines": [b for b in [from_base(base, "docs/ai/policy.yml")] if b], "signoff": signoff,
           "no_production": bool(rule.get("no_production"))}
    key, gates = a.stage + "_gates", []
    extra = rule.get("add", []) if a.stage == "done" else []
    for g in floor.get(key, []) + pol.get(key, []) + also + extra:
        if g in KNOWN and g not in gates:
            gates.append(g)
    results = [run_gate(g, payload_for(g, ctx)) for g in gates]
    report = {"stage": a.stage, "type": wtype, "pass": all(r["pass"] for r in results), "gates": results}
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
d = os.path.join(root, "openspec", "changes", change) if change else ""
state = {"branch": branch or None, "ticket": ticket or None, "change": change or None,
         "change_exists": bool(d) and os.path.isdir(d), "next": None, "last_gate": None,
         "bootstrapped": all(os.path.isfile(os.path.join(root, "docs", "ai", f)) for f in ("index.json", "policy.yml"))}
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
