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
