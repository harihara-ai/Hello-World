#!/usr/bin/env python3
"""purpose: changed-line coverage at or above the threshold, and overall coverage not dropping beyond tolerance.

In git: {"reports": [paths], "baseline_total": pct or "baseline_report": path, "base": ref}. gate_check fills
these from its CI flags only, never from the change folder. The gate reads the reports and git diff itself; no
production code changed means nothing to check; added coverage-ignore markers and coverage-tool API calls (in any
changed code, tests too) fail; a signed floor of 0 (a
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
from kitconst import CODE_EXT, COVERAGE_API, COVERAGE_IGNORE, is_test_file  # noqa: E402


def in_git():
    p = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    return p.stdout.strip() == "true"


def from_git(p):
    if "base" not in p:
        raise UsageError("need 'base' in a git repo")
    every = {f: l for f, l in cov_import.changed_lines(p["base"]).items() if f.lower().endswith(CODE_EXT)}
    code = {f: l for f, l in every.items() if not is_test_file(f)}
    if not code:
        return [finding("nothing_to_check", "no production code changed", "", "warn")], None
    reports = p.get("reports") or []
    if not reports and float(p.get("policy", {}).get("min_changed_line_coverage", 80)) == 0:
        return [finding("not_required", "the signed policy sets no coverage floor (no coverage tool)", "", "warn")], None
    if not reports or ("baseline_total" not in p and "baseline_report" not in p):
        return [finding("report_required", "code changed: CI must pass --coverage-report and a baseline")], None
    f = []
    for path, lines in every.items():
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read().splitlines()
        for n in [n for n in sorted(lines) if n <= len(text)]:
            if path in code and any(m in text[n - 1].lower() for m in COVERAGE_IGNORE):
                f.append(finding("coverage_exclusion_added", "added line %d hides code from coverage" % n, path))
            if COVERAGE_API.search(text[n - 1]):
                f.append(finding("coverage_api_in_change", "added line %d calls the coverage tool: code must not write its own coverage" % n, path))
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
