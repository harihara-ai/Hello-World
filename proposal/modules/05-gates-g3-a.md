purpose: working source for the gates for done components of the kit (tangled into workspace/).

# Gates for done

Deterministic, JSON in and JSON out. Tests: tests/unit and tests/mutation.

## gate.trace

Section 10.4 check 6. Trap 6. Only test files count; underscore IDs match (round 1 F01, F02).

````python file=kit/gates/trace_check.py
#!/usr/bin/env python3
"""purpose: every REQ ID in the change's spec appears in at least one test file (traceability, G3 check 6).

Input: {"spec_dirs": [change folder]}. Test files are found by the fixed test globs (kitconst), never by input,
so an ID in production code or docs does not count. REQ-AREA-001, REQ_AREA_001 and Req_Area_001 are one ID.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
from kitconst import SKIP_DIRS, is_test_file  # noqa: E402

SPEC_ID = re.compile(r"REQ-[A-Z0-9]+-[0-9]+")
TEST_ID = re.compile(r"(?<![A-Za-z0-9])REQ[-_]([A-Za-z0-9]+?)[-_]([0-9]+)(?![0-9])", re.I)


def norm(area, num):
    return "REQ-%s-%03d" % (area.upper(), int(num))


def spec_ids(dirs):
    found = set()
    for d in dirs:
        for root, _d, files in os.walk(d):
            for name in files:
                if name.endswith(".md"):
                    with open(os.path.join(root, name), encoding="utf-8", errors="ignore") as fh:
                        found |= {norm(*i.split("-")[1:]) for i in SPEC_ID.findall(fh.read())}
    return found


def test_ids():
    found, n = set(), 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), ".").replace(os.sep, "/")
            if not is_test_file(rel):
                continue
            n += 1
            with open(rel, encoding="utf-8", errors="ignore") as fh:
                found |= {norm(a, b) for a, b in TEST_ID.findall(fh.read())}
    return found, n


def check(p):
    ids = spec_ids([d for d in p.get("spec_dirs", []) if os.path.isdir(d)])
    if not ids:
        return [finding("no_ids", "no REQ IDs found in %s" % p.get("spec_dirs"))], {}
    tested, n = test_ids()
    if not n:
        return [finding("no_test_files", "no test files found (see kitconst.TEST_GLOBS)")], {}
    f = [finding("untested", "%s has no test" % i, i) for i in sorted(ids - tested)]
    f += [finding("orphan_id", "tests mention %s, which is in no spec here" % i, i, "warn") for i in sorted(tested - ids)]
    return f, {"requirements": sorted(ids)}


if __name__ == "__main__":
    sys.exit(run("trace_check", check))
````

## gate.coverage

Section 10.4 check 5. Trap 8. Reads the coverage report and git diff itself (round 1 F05).

````python file=kit/gates/coverage.py
#!/usr/bin/env python3
"""purpose: changed-line coverage at or above the threshold, and overall coverage not dropping beyond tolerance.

Preferred input: {"report": coverage report path, "base": git ref, "baseline_total": pct, "policy": {...}}.
The gate reads the report and git diff itself. Manual input {changed_lines, covered_lines, baseline_total,
current_total} is accepted outside git and is flagged as manual evidence.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
import cov_import  # noqa: E402
from kitconst import is_test_file  # noqa: E402

CODE_EXT = (".py", ".php", ".java", ".kt", ".cs", ".vb", ".js", ".ts", ".tsx", ".jsx", ".go", ".rb",
            ".pas", ".dpr", ".c", ".cpp", ".h", ".scala", ".swift", ".rs")


def from_report(p):
    rep = cov_import.parse_report(p["report"])
    changed, covered = {}, {}
    for f, lines in cov_import.changed_lines(p.get("base", "HEAD")).items():
        if is_test_file(f) or not f.endswith(CODE_EXT):
            continue
        key = cov_import.match(f, rep["instrumented"])
        changed[f] = sorted(lines & rep["instrumented"][key]) if key else sorted(lines)
        covered[f] = sorted(rep["covered"].get(key, set())) if key else []
    return changed, covered, rep["total"]


def check(p):
    f = []
    if "report" in p:
        if "baseline_total" not in p:
            return [finding("missing_input", "no baseline_total from the base branch run")], {}
        changed, covered, current = from_report(p)
    else:
        missing = [k for k in ("changed_lines", "covered_lines", "baseline_total", "current_total") if k not in p]
        if missing:
            return [finding("missing_input", "no coverage evidence: %s" % ", ".join(missing))], {}
        changed, covered, current = p["changed_lines"], p["covered_lines"], p["current_total"]
        f.append(finding("manual_evidence", "coverage numbers were written by hand; prefer a report file", "", "warn"))
    pol = p.get("policy", {})
    threshold = float(pol.get("min_changed_line_coverage", 80))
    total = hit = 0
    for path, lines in changed.items():
        total += len(set(lines))
        hit += len(set(lines) & set(covered.get(path, [])))
    pct = round(100.0 * hit / total, 1) if total else 100.0
    if not total:
        f.append(finding("no_changed_lines", "no changed production lines were measured", "", "warn"))
    if pct < threshold:
        f.append(finding("changed_lines", "changed-line coverage %.1f%% is below %.1f%%" % (pct, threshold)))
    drop = float(p["baseline_total"]) - float(current)
    if drop > float(pol.get("max_total_drop", 0.1)) + 1e-9:
        f.append(finding("overall_drop", "overall coverage fell from %s to %s" % (p["baseline_total"], current)))
    return f, {"changed_line_coverage": pct, "current_total": current}


if __name__ == "__main__":
    sys.exit(run("coverage", check))
````

## gate.diff_scope

Sections 10.4 check 9, 16.5. Trap 7. In git, git is the truth; protected paths always fail (round 1 F06, F07).

````python file=kit/gates/diff_scope.py
#!/usr/bin/env python3
"""purpose: flag changed files outside the impact scan, protected files, and production files when forbidden.

Input: {"base": git ref, "impact_scan": [globs], "change_dir": path, "no_production": bool} in a git repo;
outside git, {"changed_files": [...]} is used instead. In git, listed files are ignored: git is the truth.
"""
import subprocess
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
from kitconst import NOT_PRODUCTION, PROTECTED, matches  # noqa: E402


def in_git():
    return subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True).returncode == 0


def git_changed(base):
    if not re.fullmatch(r"[\w./~^@-]+", base) or base.startswith("-"):
        raise UsageError("bad base ref")
    names = set()
    for cmd in (["git", "diff", "--name-only", "--no-renames", base, "--"],
                ["git", "ls-files", "--others", "--exclude-standard"]):
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode != 0:
            raise UsageError("git failed: %s" % out.stderr.strip())
        names |= {n for n in out.stdout.splitlines() if n}
    return sorted(names)


def check(p):
    f = []
    if in_git() and "base" in p:
        changed = git_changed(p["base"])
        if "changed_files" in p:
            f.append(finding("listed_files_ignored", "changed_files ignored; git diff is used", "", "warn"))
    elif "changed_files" in p:
        changed = p["changed_files"]
    else:
        raise UsageError("need 'base' in a git repo, or 'changed_files' outside git")
    ch = p.get("change_dir", "").rstrip("/")
    changed = [c for c in changed if not (ch and c.startswith(ch + "/")) and "__pycache__/" not in c]
    scan = p.get("impact_scan", [])
    if not scan:
        return f + [finding("no_impact_scan", "no impact scan given")], {}
    f += [finding("protected_path", "a human changes this file in its own PR: %s" % c, c) for c in changed if matches(c, PROTECTED)]
    f += [finding("outside_scan", "changed but not in the impact scan: %s" % c, c) for c in changed if not matches(c, scan)]
    if p.get("no_production"):
        f += [finding("production_change", "this work item may not change production files: %s" % c, c)
              for c in changed if not matches(c, NOT_PRODUCTION)]
    return f, {"changed_files": changed}


if __name__ == "__main__":
    sys.exit(run("diff_scope", check))
````

## gate.policy_guard

Section 10.6. Trap 12. gate_check always compares the repo policy with the kit floor.

````python file=kit/gates/policy_guard.py
#!/usr/bin/env python3
"""purpose: refuse any policy change that loosens the floor unless a human sign-off names that key.

Input: {"old": floor.yml, "baselines": [base-commit policy.yml], "new": policy.yml, "signoff": signoff.json}.
min_* may only rise, max_* may only fall, lists may only grow, keys may not be removed, against the floor and
every baseline. Sign-off JSON: {approved_by, reason, keys: {key: approved value}}.
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


def signed(path):
    if not path or not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        s = json.load(fh)
    keys = s.get("keys")
    if not str(s.get("approved_by", "")).strip() or not str(s.get("reason", "")).strip() or not isinstance(keys, dict):
        return {}
    return keys


def check(p):
    try:
        olds = [policy.load(x) for x in [p["old"]] + p.get("baselines", [])]
        new = policy.load(p["new"])
    except ValueError as e:
        return [finding("unparseable", "policy cannot be parsed: %s" % e)], {}
    ok, f = signed(p.get("signoff")), []
    for k, why in sorted({lw for old in olds for lw in loosened(old, new)}):
        if k not in ok or ok[k] != new.get(k):
            f.append(finding("loosened", "%s loosened (%s) without a human sign-off for that value" % (k, why), k))
    return f, {}


if __name__ == "__main__":
    sys.exit(run("policy_guard", check))
````
