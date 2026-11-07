#!/usr/bin/env python3
"""purpose: run the gates for 'ready' or 'done' (kit floor plus repo list; the work type can only add).

Usage: gate_check.py ready|done|auto --repo DIR --change openspec/changes/<name>|auto [--base REF]
       [--coverage-report PATH ...] [--baseline-report PATH] [--test-cmd "CMD, optionally with {tests}"]
'auto' stage: done when the plan is already in the base commit (code PR), else ready (plan PR, which may change
only its change folder). A code PR records evidence.md; a plan whose evidence.md is already in the base is used.
Gate targets are set here, never by the change folder. In git: policy baseline, sign-off and, at done, the
approved plan (spec, Type, impact scan) come from the base commit; coverage evidence and the test command come
from flags (CI sets them; kit/INSTALL.md). Exit 0 all pass, 1 any fail, 2 bad usage.
"""
import sys
import tempfile

sys.dont_write_bytecode = True
sys.pycache_prefix = PYCACHE = tempfile.mkdtemp(prefix="kit-pycache-")  # before any kit import: no planted .pyc
import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
FLOOR = os.path.join(KIT, "core", "policy.yml")
KNOWN = ["injection", "policy_guard", "spec_lint", "granularity", "trace_check", "coverage", "diff_scope", "flaky",
         "red_check"]
CHANGE = re.compile(r"openspec/changes/[A-Za-z0-9][A-Za-z0-9._-]*")
sys.path.insert(0, HERE)
import policy  # noqa: E402
from changectx import PLAN_FILES, approved_plan, exists_in_base, changed_paths, default_base, from_base, git, texts_under  # noqa: E402
from kitconst import DOCS, PROTECTED, TYPES, is_test_file, matches  # noqa: E402


def payload_for(gate, ctx):
    p, ch, plan = {}, ctx["change"], ctx["plan"]
    path = os.path.join(plan if gate == "diff_scope" else ch, "inputs", gate + ".json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            p = json.load(fh)
    p["policy"] = ctx["policy"]
    if gate == "spec_lint":
        p["spec"] = os.path.join(ch, "spec.md")
    elif gate == "injection":
        p["texts"] = texts_under(ch) + list(p.get("texts", []))
    elif gate == "trace_check":
        p = {"spec_dirs": [plan], "type": ctx["type"]}
    elif gate == "policy_guard":
        p = {"old": FLOOR, "baselines": ctx["baselines"], "new": ctx["policy_path"], "signoff": ctx["signoff"]}
    elif gate == "diff_scope" and ctx["stage"] == "ready":
        p = {"impact_scan": [ch + "/*"], "change_dir": "", "policy": ctx["policy"]}  # a plan PR holds only its plan
        p.update({"base": ctx["base"]} if ctx["base"] else {"changed_files": []})
    elif gate == "diff_scope":
        p.update(change_dir=ch, no_production=bool(p.get("no_production")) or ctx["no_production"],
                 plan_files=["%s/%s" % (ch, f) for f in PLAN_FILES])
        if ctx["base"]:
            p["base"] = ctx["base"]
    elif gate == "coverage" and ctx["base"]:
        p = dict(ctx["coverage"], base=ctx["base"], policy=ctx["policy"])
    elif gate == "red_check":
        p = {"base": ctx["base"], "type": ctx["type"], "test_cmd": ctx["test_cmd"]}
    return p


def run_gate(gate, payload):
    proc = subprocess.run([sys.executable, "-I", "-B", "-X", "pycache_prefix=" + PYCACHE,
                           os.path.join(KIT, "gates", gate + ".py"), "-"],
                          input=json.dumps(payload), capture_output=True, text=True)
    try:
        out = json.loads(proc.stdout)
    except ValueError:
        out = {"gate": gate, "pass": False, "error": (proc.stdout + proc.stderr)[-500:], "findings": []}
    out["pass"] = bool(out.get("pass")) and proc.returncode == 0
    return out


def spec_type(d):
    try:
        with open(os.path.join(d, "spec.md"), encoding="utf-8") as fh:
            m = re.search(r"(?m)^Type:\s*(\S+)", fh.read())
    except OSError:
        return "story"
    t = m.group(1).lower() if m else "story"
    return t if t in TYPES else "story"


def finish(report, ch):
    if ch:
        with open(os.path.join(ch, "gates-%s.json" % report["stage"]), "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
    print(json.dumps(report, indent=1))
    return 0 if report["pass"] else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["ready", "done", "auto"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--change", required=True)
    ap.add_argument("--base")
    ap.add_argument("--coverage-report", action="append", default=[])
    ap.add_argument("--baseline-report")
    ap.add_argument("--test-cmd")
    a = ap.parse_args()
    if a.change != "auto" and (not CHANGE.fullmatch(a.change.rstrip("/")) or ".." in a.change):
        ap.error("--change must be openspec/changes/<name> or auto")
    reports = [os.path.abspath(r) for r in a.coverage_report]
    baseline_report = os.path.abspath(a.baseline_report) if a.baseline_report else None
    os.chdir(a.repo)
    in_git = git("rev-parse", "--is-inside-work-tree") == "true"
    base = (a.base or default_base()) if in_git else None
    if in_git and not base:
        ap.error("no remote default branch to compare with: pass --base <ref> (CI passes the merge-base)")
    ch = a.change.rstrip("/")
    if ch == "auto":
        if not in_git:
            ap.error("--change auto needs git")
        found = sorted({m.group(0) for p in changed_paths(base) for m in [CHANGE.match(p)] if m and p != m.group(0)})
        if len(found) != 1:
            other = [p for p in changed_paths(base) if is_test_file(p) or not matches(p, PROTECTED + DOCS)]
            ok = not found and not other
            why = ("no change folder: only docs or human-owned files changed" if ok else
                   "one PR holds exactly one change folder; found %s" % (found or "none") +
                   ("" if found else ", but code or tests changed: %s" % other[:5]))
            return finish({"stage": a.stage, "change": None, "pass": ok, "error": why, "gates": []}, None)
        ch = found[0]
    policy_path = os.path.join("docs", "ai", "policy.yml")
    if not os.path.isfile(policy_path):
        policy_path = FLOOR
    floor, pol = policy.load(FLOOR), policy.load(policy_path)
    merged = approved_plan(base, ch) if in_git else None
    if a.stage == "auto":
        a.stage = "done" if merged or not in_git else "ready"
    plan = merged if in_git and a.stage == "done" else ch
    wtype = spec_type(plan or ch)
    rule = TYPES[wtype]
    signoff = from_base(base, "docs/ai/policy-signoff.json") if in_git else os.path.join("docs", "ai", "policy-signoff.json")
    cov = {"reports": reports}
    cov.update({"baseline_report": baseline_report} if baseline_report else {})
    ctx = {"change": ch, "stage": a.stage, "plan": plan or ch, "policy": pol, "policy_path": policy_path,
           "base": base, "type": wtype, "baselines": [b for b in [from_base(base, "docs/ai/policy.yml")] if b],
           "signoff": signoff, "no_production": bool(rule.get("no_production")), "coverage": cov, "test_cmd": a.test_cmd}
    key, gates = a.stage + "_gates", []
    extra = rule.get("add", []) if a.stage == "done" else []
    for g in floor.get(key, []) + pol.get(key, []) + extra:
        if g in KNOWN and g not in gates:
            gates.append(g)
    results = [run_gate(g, payload_for(g, ctx)) for g in gates]
    plan_issue = None
    if a.stage == "done" and in_git:
        if plan is None:
            plan_issue = ("plan_not_approved", "the plan is not in the base commit: merge the plan PR first")
        elif exists_in_base(base, ch + "/evidence.md"):
            plan_issue = ("plan_used", "this plan was already implemented; plan the next change in a new change folder")
        elif not os.path.isfile(os.path.join(ch, "evidence.md")) or not os.path.getsize(os.path.join(ch, "evidence.md")):
            plan_issue = ("no_evidence", "record RED then GREEN in evidence.md (/implement)")
    if plan_issue:
        results.insert(0, {"gate": "plan", "pass": False, "findings": [
            {"rule": plan_issue[0], "severity": "fail", "where": ch, "message": plan_issue[1]}]})
    ran = {r["gate"] for r in results}
    missing = [g for g in floor.get(key, []) if g not in ran]
    report = {"stage": a.stage, "change": ch, "type": wtype, "pass": all(r["pass"] for r in results) and not missing,
              "missing_floor_gates": missing, "gates": results}
    return finish(report, ch)


if __name__ == "__main__":
    sys.exit(main())
