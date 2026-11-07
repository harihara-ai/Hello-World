purpose: working source for the gates for done components of the kit (tangled into workspace/).

# Gates for done

Deterministic, JSON in and JSON out. Tests: tests/unit and tests/mutation.

## gate.trace

Section 10.4 check 6. Trap 6. Only test files count; underscore IDs match (round 1 F01, F02).

````python file=kit/gates/trace_check.py
#!/usr/bin/env python3
"""purpose: every REQ ID in the change's spec appears in at least one test file (traceability, G3 check 6).

Input: {"spec_dirs": [change folder], "type": work type}. Requirement IDs come from spec.md and specs/*.md only
(never the fetched ticket). Test files are code or .feature files matching the fixed test globs (kitconst), so
an ID in production code, docs or a text file does not count. REQ-AREA-001, REQ_AREA_001, testReq_Area_001 match.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
from kitconst import NO_REQUIREMENT_TYPES, SKIP_DIRS, TEST_EXT, is_test_file  # noqa: E402

SPEC_ID = re.compile(r"REQ-[A-Z0-9]+-[0-9]+")
TEST_ID = re.compile(r"(?<![0-9])REQ[-_]([A-Za-z0-9]+?)[-_]([0-9]+)(?![0-9])", re.I)


def norm(area, num):
    return "REQ-%s-%03d" % (area.upper(), int(num))


def spec_ids(dirs):
    found = set()
    for d in dirs:
        specs = [os.path.join(d, "spec.md")]
        specs += [os.path.join(r, n) for r, _d, fs in os.walk(os.path.join(d, "specs")) for n in fs if n.endswith(".md")]
        for path in specs:
            if os.path.isfile(path):
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    found |= {norm(*i.split("-")[1:]) for i in SPEC_ID.findall(fh.read())}
    return found


def test_ids():
    found, n = set(), 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), ".").replace(os.sep, "/")
            if not is_test_file(rel) or not rel.lower().endswith(TEST_EXT):
                continue
            n += 1
            with open(rel, encoding="utf-8", errors="ignore") as fh:
                found |= {norm(a, b) for a, b in TEST_ID.findall(fh.read())}
    return found, n


def check(p):
    ids = spec_ids([d for d in p.get("spec_dirs", []) if os.path.isdir(d)])
    if not ids:
        if p.get("type") in NO_REQUIREMENT_TYPES:
            return [finding("nothing_to_check", "no requirements in a %s change" % p["type"], "", "warn")], {}
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

In git: {"reports": [paths], "baseline_total": pct or "baseline_report": path, "base": ref}. gate_check fills
these from its CI flags only, never from the change folder. The gate reads the reports and git diff itself; no
production code changed means nothing to check; added coverage-ignore markers fail; a signed floor of 0 (a
stack with no coverage tool) needs no report. Outside git only
(fixtures): {changed_lines, covered_lines, baseline_total, current_total}.
"""
import subprocess
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
import cov_import  # noqa: E402
from kitconst import CODE_EXT, COVERAGE_IGNORE, is_test_file  # noqa: E402


def in_git():
    p = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    return p.stdout.strip() == "true"


def from_git(p):
    if "base" not in p:
        raise UsageError("need 'base' in a git repo")
    code = {f: l for f, l in cov_import.changed_lines(p["base"]).items()
            if not is_test_file(f) and f.lower().endswith(CODE_EXT)}
    if not code:
        return [finding("nothing_to_check", "no production code changed", "", "warn")], None
    reports = p.get("reports") or []
    if not reports and float(p.get("policy", {}).get("min_changed_line_coverage", 80)) == 0:
        return [finding("not_required", "the signed policy sets no coverage floor (no coverage tool)", "", "warn")], None
    if not reports or ("baseline_total" not in p and "baseline_report" not in p):
        return [finding("report_required", "code changed: CI must pass --coverage-report and a baseline")], None
    f = []
    for path, lines in code.items():
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read().lower().splitlines()
        for n in sorted(lines):
            if n <= len(text) and any(m in text[n - 1] for m in COVERAGE_IGNORE):
                f.append(finding("coverage_exclusion_added", "added line %d hides code from coverage" % n, path))
    rep, changed, covered = cov_import.parse_reports(reports), {}, {}
    measured = {os.path.splitext(k)[1].lower() for k in rep["instrumented"]}
    for path, lines in code.items():
        key = cov_import.match(path, rep["instrumented"])
        if not key and os.path.splitext(path)[1].lower() not in measured:
            f.append(finding("not_measured", "the report does not measure %s files: %s" % (os.path.splitext(path)[1], path), path, "warn"))
            continue
        if not key:
            f.append(finding("unmatched_file", "%s is not in the report; counted as uncovered" % path, path, "warn"))
        changed[path] = sorted(lines & rep["instrumented"][key]) if key else sorted(lines)
        covered[path] = sorted(rep["covered"].get(key, set())) if key else []
    if "baseline_report" in p:
        p["baseline_total"] = cov_import.parse_report(p["baseline_report"])["total"]
    return f, (changed, covered, rep["total"])


def check(p):
    if in_git():
        f, data = from_git(p)
        if data is None:
            return f, {}
        changed, covered, current = data
    else:
        missing = [k for k in ("changed_lines", "covered_lines", "baseline_total", "current_total") if k not in p]
        if missing:
            return [finding("missing_input", "no coverage evidence: %s" % ", ".join(missing))], {}
        changed, covered, current = p["changed_lines"], p["covered_lines"], p["current_total"]
        f = [finding("manual_evidence", "coverage numbers were written by hand (outside git only)", "", "warn")]
    pol = p.get("policy", {})
    threshold = float(pol.get("min_changed_line_coverage", 80))
    total = sum(len(set(v)) for v in changed.values())
    hit = sum(len(set(v) & set(covered.get(k, []))) for k, v in changed.items())
    pct = round(100.0 * hit / total, 1) if total else 100.0
    if not total:
        f.append(finding("no_changed_lines", "no changed executable lines were measured", "", "warn"))
    if pct < threshold:
        f.append(finding("changed_lines", "changed-line coverage %.1f%% is below %.1f%%" % (pct, threshold)))
    if float(p["baseline_total"]) - float(current) > float(pol.get("max_total_drop", 0.1)) + 1e-9:
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

Input: {"base": git ref, "impact_scan": [globs], "change_dir": path, "plan_files": [paths], "no_production": bool}
in a git repo; outside git, {"changed_files": [...]} is used instead. In git, listed files are ignored: git is the
truth. Changes to the approved plan files fail (the plan is approved by merging its own PR).
"""
import subprocess
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
from kitconst import PROTECTED, is_production, matches  # noqa: E402


def in_git():
    return subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True).returncode == 0


def git_changed(base):
    if not re.fullmatch(r"[\w./~^@-]+", base) or base.startswith("-"):
        raise UsageError("bad base ref")
    names = set()
    for cmd in (["git", "-c", "core.quotePath=false", "diff", "--no-ext-diff", "--name-only", "--no-renames", base, "--"],
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
    plan = set(p.get("plan_files", []))
    f += [finding("plan_changed", "the approved plan changed after G1; change it in a new plan PR: %s" % c, c)
          for c in changed if c in plan]
    ch = p.get("change_dir", "").rstrip("/")
    f += [finding("bytecode_added", "compiled bytecode cannot be reviewed: %s" % c, c)
          for c in changed if c.endswith((".pyc", ".pyo")) or "__pycache__/" in c]
    changed = [c for c in changed if not (ch and c.startswith(ch + "/"))]
    f += [finding("protected_path", "a human changes this file in its own PR: %s" % c, c) for c in changed if matches(c, PROTECTED)]
    scan = p.get("impact_scan", [])
    if not scan:
        return f + [finding("no_impact_scan", "no impact scan given")], {}
    broad = [g for g in scan if not re.sub(r"[*?./\[\]]", "", g)]
    if broad:
        return f + [finding("scan_too_broad", "impact scan must name files or folders, not %s" % broad)], {}
    f += [finding("outside_scan", "changed but not in the impact scan: %s" % c, c) for c in changed if not matches(c, scan)]
    if p.get("no_production"):
        f += [finding("production_change", "this work item may not change production files: %s" % c, c)
              for c in changed if is_production(c)]
    return f, {"changed_files": changed}


if __name__ == "__main__":
    sys.exit(run("diff_scope", check))
````
