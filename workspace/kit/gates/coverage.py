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
