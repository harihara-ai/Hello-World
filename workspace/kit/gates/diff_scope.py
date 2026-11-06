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
