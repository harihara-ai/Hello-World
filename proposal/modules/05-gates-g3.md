purpose: working source for the gates for done components of the kit (tangled into workspace/).

# Gates for done

Deterministic, JSON in and JSON out. Tests: tests/unit and tests/mutation.

## gate.trace

Section 10.4 check 6. Trap 6. Python port of kit-v0 trace_check.sh, with JSON output.

````python file=kit/gates/trace_check.py
#!/usr/bin/env python3
"""purpose: every REQ ID in the specs appears in at least one test file (traceability, G3 check 6).

Input: {"spec_dirs": [...], "test_dirs": [...]}, paths relative to the working directory. Output: gate JSON.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

ID = re.compile(r"REQ-[A-Z0-9]+-[0-9]+")


def ids_in(dirs, md_only):
    found = set()
    for d in dirs:
        for root, _dirs, files in os.walk(d):
            for name in files:
                if md_only and not name.endswith(".md"):
                    continue
                try:
                    with open(os.path.join(root, name), encoding="utf-8", errors="ignore") as fh:
                        found |= set(ID.findall(fh.read()))
                except OSError:
                    continue
    return found


def check(p):
    spec_dirs = [d for d in p.get("spec_dirs", []) if os.path.isdir(d)]
    test_dirs = [d for d in p.get("test_dirs", ["tests", "test", "spec", "src"]) if os.path.isdir(d)]
    spec_ids = ids_in(spec_dirs, True)
    if not spec_ids:
        return [finding("no_ids", "no REQ IDs found in %s" % p.get("spec_dirs"))], {}
    if not test_dirs:
        return [finding("no_test_dirs", "none of the test dirs exist: %s" % p.get("test_dirs"))], {}
    test_ids = ids_in(test_dirs, False)
    f = [finding("untested", "%s has no test" % i, i) for i in sorted(spec_ids - test_ids)]
    f += [finding("orphan_id", "tests mention %s, which is in no spec here" % i, i, "warn")
          for i in sorted(test_ids - spec_ids)]
    return f, {"requirements": sorted(spec_ids)}


if __name__ == "__main__":
    sys.exit(run("trace_check", check))
````

## gate.coverage

Section 10.4 check 5. Trap 8.

````python file=kit/gates/coverage.py
#!/usr/bin/env python3
"""purpose: changed-line coverage at or above the threshold, and no drop in overall coverage.

Input: {"changed_lines": {file: [n]}, "covered_lines": {file: [n]}, "baseline_total": pct,
        "current_total": pct, "policy": {min_changed_line_coverage}}. Output: gate JSON.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

NEEDED = ("changed_lines", "covered_lines", "baseline_total", "current_total")


def check(p):
    missing = [k for k in NEEDED if k not in p]
    if missing:
        return [finding("missing_input", "no coverage evidence: %s" % ", ".join(missing))], {}
    threshold = float(p.get("policy", {}).get("min_changed_line_coverage", 80))
    total = covered = 0
    for path, lines in p["changed_lines"].items():
        total += len(set(lines))
        covered += len(set(lines) & set(p["covered_lines"].get(path, [])))
    pct = round(100.0 * covered / total, 1) if total else 100.0
    f = []
    if pct < threshold:
        f.append(finding("changed_lines", "changed-line coverage %.1f%% is below %.1f%%" % (pct, threshold)))
    if float(p["current_total"]) < float(p["baseline_total"]):
        f.append(finding("overall_drop", "overall coverage fell from %s to %s" % (p["baseline_total"], p["current_total"])))
    return f, {"changed_line_coverage": pct}


if __name__ == "__main__":
    sys.exit(run("coverage", check))
````

## gate.diff_scope

Sections 10.4 check 9, 16.5. Trap 7. Computes changed files from git when given a base ref.

````python file=kit/gates/diff_scope.py
#!/usr/bin/env python3
"""purpose: flag changed files outside the impact scan; with no_production, flag any production file.

Input: {"changed_files": [...] or "base": "<git ref>", "impact_scan": [globs], "no_production": bool,
        "test_globs": [globs]}. Output: gate JSON.
"""
import fnmatch
import subprocess
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

TEST_GLOBS = ["tests/*", "test/*", "spec/*", "features/*", "*/tests/*", "*/test/*", "*_test.*",
              "*.test.*", "*Test.*", "*Tests.*", "test_*", "safety-net/*", "openspec/*", "docs/*"]


def git_changed(base):
    if not re.fullmatch(r"[\w./~^@-]+", base) or base.startswith("-"):
        raise UsageError("bad base ref")
    names = set()
    for cmd in (["git", "diff", "--name-only", base, "--"], ["git", "ls-files", "--others", "--exclude-standard"]):
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode != 0:
            raise UsageError("git failed: %s" % out.stderr.strip())
        names |= {n for n in out.stdout.splitlines() if n}
    return sorted(names)


def matches(path, globs):
    return any(fnmatch.fnmatchcase(path, g) for g in globs)


def check(p):
    changed = p["changed_files"] if "changed_files" in p else git_changed(p.get("base", ""))
    scan = p.get("impact_scan", [])
    if not scan:
        return [finding("no_impact_scan", "no impact scan given")], {}
    f = [finding("outside_scan", "changed but not in the impact scan: %s" % c, c)
         for c in changed if not matches(c, scan)]
    if p.get("no_production"):
        tests = p.get("test_globs", TEST_GLOBS)
        f += [finding("production_change", "this work item may not change production files: %s" % c, c)
              for c in changed if not matches(c, tests)]
    return f, {"changed_files": changed}


if __name__ == "__main__":
    sys.exit(run("diff_scope", check))
````

## gate.policy_guard

Section 10.6. Trap 12. gate_check always compares the repo policy with the kit floor.

````python file=kit/gates/policy_guard.py
#!/usr/bin/env python3
"""purpose: refuse any policy change that loosens the floor unless a human sign-off names that key.

Input: {"old": floor.yml, "new": policy.yml, "signoff": signoff.json}. min_* may only rise, max_* may only
fall, lists may only grow, keys may not be removed. Sign-off JSON: {approved_by, reason, keys: [...]}.
"""
import json
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
import policy  # noqa: E402


def loosened(old, new):
    out = []
    for k, ov in old.items():
        if k not in new:
            out.append((k, "removed"))
            continue
        nv = new[k]
        if k.startswith(("min_", "max_")):
            a = ov if isinstance(ov, list) else [ov]
            b = nv if isinstance(nv, list) else [nv]
            if len(a) != len(b) or not all(isinstance(x, (int, float)) for x in b):
                out.append((k, "changed shape"))
            elif any((y < x) if k.startswith("min_") else (y > x) for x, y in zip(a, b)):
                out.append((k, "%s -> %s" % (ov, nv)))
        elif isinstance(ov, list):
            gone = [x for x in ov if x not in (nv if isinstance(nv, list) else [])]
            if gone:
                out.append((k, "removed %s" % gone))
    return out


def signed_keys(path):
    if not path or not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        s = json.load(fh)
    if not str(s.get("approved_by", "")).strip() or not str(s.get("reason", "")).strip():
        return set()
    return set(s.get("keys", []))


def check(p):
    try:
        old, new = policy.load(p["old"]), policy.load(p["new"])
    except ValueError as e:
        return [finding("unparseable", "policy cannot be parsed: %s" % e)], {}
    signed = signed_keys(p.get("signoff"))
    f = [finding("loosened", "%s loosened (%s) without a human sign-off" % (k, why), k)
         for k, why in loosened(old, new) if k not in signed]
    return f, {}


if __name__ == "__main__":
    sys.exit(run("policy_guard", check))
````

## gate.flaky

Section 16.1 steps 2 and 8. Trap 5.

````python file=kit/gates/flaky.py
#!/usr/bin/env python3
"""purpose: compare repeated test runs; a test whose result differs between runs is flaky and is quarantined.

Input: {"runs": [{test: "pass"|"fail"}], "policy": {min_flaky_runs}}. Output: gate JSON with flaky and failing lists.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402


def check(p):
    runs = p.get("runs", [])
    need = int(p.get("policy", {}).get("min_flaky_runs", 3))
    if len(runs) < need:
        return [finding("too_few_runs", "%d runs given, %d needed" % (len(runs), need))], {"flaky": [], "failing": []}
    tests = sorted(set().union(*[set(r) for r in runs]))
    flaky, failing = [], []
    for t in tests:
        seen = {r.get(t, "missing") for r in runs}
        if len(seen) > 1:
            flaky.append(t)
        elif seen == {"fail"}:
            failing.append(t)
    f = [finding("flaky", "%s is flaky: quarantine it with a ticket" % t, t) for t in flaky]
    f += [finding("failing", "%s fails every run" % t, t, "warn") for t in failing]
    return f, {"flaky": flaky, "failing": failing}


if __name__ == "__main__":
    sys.exit(run("flaky", check))
````
