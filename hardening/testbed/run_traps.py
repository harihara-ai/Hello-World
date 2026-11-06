#!/usr/bin/env python3
"""purpose: run every seeded trap case against a tangled kit and score blocked traps and false alarms.

Usage: run_traps.py [--kit workspace] [--json]
Each case copies its repo to a temp dir, applies overlay/ files and string patches, then runs the real kit.
Exit 0 when every case behaves as expected, 1 otherwise. Writes nothing inside the repo.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PY = [sys.executable, "-I", "-B"]


def prepare(repo, case_dir, case, kit):
    tmp = os.path.join(tempfile.mkdtemp(prefix="trap-"), "repo")
    shutil.copytree(os.path.join(HERE, repo), tmp)
    policy = os.path.join(tmp, "docs", "ai", "policy.yml")
    if not os.path.isfile(policy):
        os.makedirs(os.path.dirname(policy), exist_ok=True)
        shutil.copy(os.path.join(kit, "kit", "core", "policy.yml"), policy)
    overlay = os.path.join(case_dir, "overlay")
    if os.path.isdir(overlay):
        shutil.copytree(overlay, tmp, dirs_exist_ok=True)
    for rel, pairs in case.get("patch", {}).items():
        path = os.path.join(tmp, rel)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for old, new in pairs:
            if text.count(old) != 1:
                raise ValueError("patch target must occur exactly once in %s: %r" % (rel, old[:60]))
            text = text.replace(old, new)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    return tmp


def run_gate_check(tmp, case, kit):
    stages = ["ready", "done"] if case["stage"] == "both" else [case["stage"]]
    failed = []
    for stage in stages:
        p = subprocess.run(PY + [os.path.join(kit, "kit/scripts/gate_check.py"), stage, "--repo", tmp,
                                 "--change", case["change"]], capture_output=True, text=True)
        try:
            out = json.loads(p.stdout)
        except ValueError:
            return False, "gate_check gave no JSON: %s" % (p.stdout + p.stderr)[-300:]
        failed += ["%s:%s" % (stage, g["gate"]) for g in out["gates"] if not g["pass"]]
    names = {f.split(":")[1] for f in failed}
    expected = set(case["expect_fail"])
    if not expected:
        return not failed, "false alarm: %s" % failed if failed else "clean: all gates pass"
    ok = expected <= names
    return ok, "failed gates: %s" % (failed or "none")


def run_probe(tmp, case, kit):
    md = os.path.join(tmp, "docs", "ai", "toolchain.md")
    payload = {"results": case["results"], "capabilities": [case["capability"]]}
    p = subprocess.run(PY + [os.path.join(kit, "kit/scripts/probe.py"), "-", "--out", md],
                       input=json.dumps(payload), capture_output=True, text=True)
    chosen = json.loads(p.stdout)["capabilities"][case["capability"]]["chosen"]
    with open(md, encoding="utf-8") as fh:
        recorded = case["expect_chosen"] in fh.read()
    ok = chosen == case["expect_chosen"] and recorded
    detail = "chosen %s, recorded in toolchain.md: %s" % (chosen, recorded)
    want = case.get("expect_kit_file")
    if want:
        path = os.path.join(kit, want["path"])
        has = os.path.isfile(path) and want["contains"] in open(path, encoding="utf-8").read()
        ok = ok and has
        detail += "; %s mentions %s: %s" % (want["path"], want["contains"], has)
    return ok, detail


def run_repeat(tmp, case, kit):
    runs = []
    for _ in range(case["times"]):
        p = subprocess.run(PY + case["command"], cwd=tmp, capture_output=True, text=True)
        result = {}
        for m in re.finditer(r"^(test\w+) \(.*?\) \.\.\. (ok|FAIL|ERROR)", p.stderr, re.M):
            result[m.group(1)] = "pass" if m.group(2) == "ok" else "fail"
        if not result:
            raise ValueError("could not parse any test result from run output")
        runs.append(result)
    p = subprocess.run(PY + [os.path.join(kit, "kit/gates/flaky.py"), "-"],
                       input=json.dumps({"runs": runs}), capture_output=True, text=True)
    out = json.loads(p.stdout)
    ok = p.returncode == 1 and set(case["expect_flaky"]) <= set(out["flaky"])
    return ok, "flaky: %s over %d runs" % (out["flaky"], len(runs))


def run_tangle(tmp, case, kit):
    case_src = os.path.join(tmp, "..", "doc.md")
    p = subprocess.run(PY + [os.path.join(ROOT, "forge", "tangle.py"), case_src,
                             os.path.join(tmp, "..", "kit.lock"), os.path.join(tmp, "..", "out"), "--pin"],
                       capture_output=True, text=True)
    text = p.stdout + p.stderr
    wrote = os.path.exists(os.path.join(tmp, "..", "out")) or os.path.exists(os.path.join(tmp, "..", "escape.sh"))
    ok = p.returncode == 1 and not wrote and all(s in text for s in case["expect_refused"])
    return ok, "refused: %s; files written: %s" % (p.returncode == 1, wrote)


RUNNERS = {"gate_check": run_gate_check, "probe": run_probe, "repeat": run_repeat, "tangle": run_tangle}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default=os.path.join(ROOT, "workspace"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    kit = os.path.abspath(a.kit)
    cases = []
    for path in sorted(glob.glob(os.path.join(HERE, "cases", "*", "*", "case.json"))):
        case_dir = os.path.dirname(path)
        repo = os.path.basename(os.path.dirname(case_dir))
        with open(path, encoding="utf-8") as fh:
            case = json.load(fh)
        try:
            tmp = prepare(repo, case_dir, case, kit)
            if case["run"] == "tangle":
                shutil.copy(os.path.join(case_dir, case["source"]), os.path.join(tmp, "..", "doc.md"))
            ok, detail = RUNNERS[case["run"]](tmp, case, kit)
        except (OSError, ValueError, KeyError) as e:
            ok, detail = False, "case error: %s" % e
        cases.append({"repo": repo, "case": os.path.basename(case_dir), "trap": case["trap"],
                      "critical": case["critical"], "title": case["title"], "ok": ok, "detail": detail})
    crit = [c for c in cases if c["critical"]]
    other = [c for c in cases if not c["critical"]]
    clean = [c for c in cases if c["trap"] == 13]
    score = {"blocked": sum(c["ok"] for c in cases), "total": len(cases),
             "critical_blocked": sum(c["ok"] for c in crit), "critical_total": len(crit),
             "other_blocked": sum(c["ok"] for c in other), "other_total": len(other),
             "false_alarms": sum(not c["ok"] for c in clean)}
    if a.json:
        print(json.dumps({"score": score, "cases": cases}, indent=1))
    else:
        for c in cases:
            print("%s %-10s %-26s trap %2d  %s" % ("PASS" if c["ok"] else "MISS", c["repo"], c["case"], c["trap"], c["detail"]))
        print("score: %(blocked)d/%(total)d cases; critical %(critical_blocked)d/%(critical_total)d; "
              "other %(other_blocked)d/%(other_total)d; false alarms %(false_alarms)d" % score)
    return 0 if score["blocked"] == score["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
