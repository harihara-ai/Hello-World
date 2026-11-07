#!/usr/bin/env python3
"""purpose: changed-line coverage at or above the threshold, and overall coverage not dropping beyond tolerance.

In git: {"report": coverage report path, "base": git ref, "baseline_total": pct, "policy": {...}}. The gate
reads the report and git diff itself; no production code changed means nothing to check. A report older than
the changed code fails. Outside git only (fixtures): {changed_lines, covered_lines, baseline_total, current_total}.
"""
import subprocess
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
import cov_import  # noqa: E402
from kitconst import CODE_EXT, is_test_file  # noqa: E402


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
    if "report" not in p or "baseline_total" not in p:
        return [finding("report_required", "code changed: give a coverage report and baseline_total")], None
    newest = max((os.path.getmtime(f) for f in code if os.path.exists(f)), default=0)
    if os.path.getmtime(p["report"]) < newest:
        return [finding("stale_report", "the coverage report is older than the changed code; re-run the tests")], None
    rep, f, changed, covered = cov_import.parse_report(p["report"]), [], {}, {}
    for path, lines in code.items():
        key = cov_import.match(path, rep["instrumented"])
        if not key:
            f.append(finding("unmatched_file", "%s is not in the report; counted as uncovered" % path, path, "warn"))
        changed[path] = sorted(lines & rep["instrumented"][key]) if key else sorted(lines)
        covered[path] = sorted(rep["covered"].get(key, set())) if key else []
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
