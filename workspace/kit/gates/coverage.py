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
