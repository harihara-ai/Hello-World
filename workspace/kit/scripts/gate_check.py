#!/usr/bin/env python3
"""purpose: run the gates for 'ready' or 'done' (kit floor plus repo list, adjusted by the fixed type table).

Usage: gate_check.py ready|done --repo DIR --change openspec/changes/<name> [--base REF] [--also g1,g2]
Gate targets (spec, change folder, policy, git base) are set here; inputs/<gate>.json can add evidence but
cannot redirect a gate. Writes <change>/gates-<stage>.json. Exit 0 all pass, 1 any fail, 2 bad usage.
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
sys.path.insert(0, HERE)
import policy  # noqa: E402
from kitconst import TYPES  # noqa: E402


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def default_base():
    for ref in ("origin/HEAD", "origin/main", "origin/master", "main", "master"):
        sha = git("merge-base", "HEAD", ref)
        if sha:
            return sha
    return "HEAD"


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


def base_policy(base):
    text = git("show", "%s:docs/ai/policy.yml" % base) if base else None
    if not text:
        return []
    fd, path = tempfile.mkstemp(suffix=".yml")
    with os.fdopen(fd, "w") as fh:
        fh.write(text + "\n")
    return [path]


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
        p = {"spec_dirs": [ch]}
    elif gate == "policy_guard":
        p = {"old": FLOOR, "baselines": ctx["baselines"], "new": ctx["policy_path"],
             "signoff": os.path.join("docs", "ai", "policy-signoff.json")}
    elif gate == "diff_scope":
        p.update(change_dir=ch, no_production=bool(p.get("no_production")) or ctx["no_production"])
        if ctx["base"]:
            p["base"] = ctx["base"]
    elif gate == "coverage" and ctx["base"] and "report" in p:
        p["base"] = ctx["base"]
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
    if os.path.isabs(a.change) or ".." in a.change.split("/"):
        ap.error("--change must be a path inside the repo")
    os.chdir(a.repo)
    policy_path = os.path.join("docs", "ai", "policy.yml")
    if not os.path.isfile(policy_path):
        policy_path = FLOOR
    floor, pol = policy.load(FLOOR), policy.load(policy_path)
    rule = TYPES[spec_type(a.change)]
    in_git = git("rev-parse", "--is-inside-work-tree") == "true"
    base = (a.base or default_base()) if in_git else None
    ctx = {"change": a.change.rstrip("/"), "policy": pol, "policy_path": policy_path, "base": base,
           "baselines": base_policy(base), "no_production": bool(rule.get("no_production"))}
    key, gates = a.stage + "_gates", []
    extra = rule.get("add", []) if a.stage == "done" else []
    for g in floor.get(key, []) + pol.get(key, []) + also + extra:
        if g in KNOWN and g not in gates and g not in rule.get("drop", []):
            gates.append(g)
    results = [run_gate(g, payload_for(g, ctx)) for g in gates]
    report = {"stage": a.stage, "type": spec_type(a.change), "pass": all(r["pass"] for r in results), "gates": results}
    with open(os.path.join(a.change, "gates-%s.json" % a.stage), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report, indent=1))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
