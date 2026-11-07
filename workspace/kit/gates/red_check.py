#!/usr/bin/env python3
"""purpose: prove the changed tests detect the change: run them against the base commit's production code.

Input: {"base": git ref, "type": work type, "test_cmd": "command"}. The test command comes from CI (gate_check
--test-cmd). Story, NFR, bug and hotfix: the changed tests must fail on base code and pass on the change (red,
then green; spec 10.4 #1). Chore, refactor and tests: they must pass on both (behaviour kept). Spike and docs:
nothing to check. Runs code, so it belongs in CI's sandbox; outside git it only warns.
"""
import shlex
import shutil
import subprocess
import tempfile
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
from kitconst import RED_TYPES, TEST_EXT, is_test_file  # noqa: E402

SKIP_TYPES = {"spike", "docs"}


def git(*args, cwd=None):
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    if p.returncode != 0:
        raise UsageError("git %s failed: %s" % (args[0], p.stderr.strip()))
    return p.stdout


def changed_tests(base):
    if not re.fullmatch(r"[\w./~^@-]+", base) or base.startswith("-"):
        raise UsageError("bad base ref")
    names = git("diff", "--no-ext-diff", "--name-only", "--no-renames", "--diff-filter=d", base, "--").splitlines()
    names += git("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({n for n in names if is_test_file(n) and n.lower().endswith(TEST_EXT) and os.path.isfile(n)})


def run_tests(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=1800).returncode
    except (OSError, subprocess.TimeoutExpired):
        return -1


def check(p):
    wtype = p.get("type", "story")
    inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if inside.stdout.strip() != "true":
        return [finding("needs_git", "red check runs in a git repo (CI)", "", "warn")], {}
    if wtype in SKIP_TYPES:
        return [finding("nothing_to_check", "no tests to prove for a %s change" % wtype, "", "warn")], {}
    tests = changed_tests(p.get("base", ""))
    if not tests:
        if wtype in RED_TYPES:
            return [finding("no_new_tests", "a %s change needs a changed test that fails without it" % wtype)], {}
        return [finding("nothing_to_check", "no changed tests", "", "warn")], {}
    if not p.get("test_cmd"):
        return [finding("no_test_cmd", "CI must pass --test-cmd")], {"tests": tests}
    cmd = shlex.split(p["test_cmd"]) if isinstance(p["test_cmd"], str) else list(p["test_cmd"])
    tmp = tempfile.mkdtemp(prefix="red-")
    wt = os.path.join(tmp, "base")
    git("worktree", "add", "--detach", "-q", wt, p["base"])
    try:
        for t in tests:
            os.makedirs(os.path.dirname(os.path.join(wt, t)) or wt, exist_ok=True)
            shutil.copy(t, os.path.join(wt, t))
        on_base = run_tests(cmd, wt)
    finally:
        git("worktree", "remove", "--force", wt)
        shutil.rmtree(tmp, ignore_errors=True)
    on_head, f = run_tests(cmd, "."), []
    if on_head != 0:
        f.append(finding("tests_fail_on_head", "the tests fail on the change (exit %d)" % on_head))
    if wtype in RED_TYPES and on_base == 0:
        f.append(finding("tests_pass_on_base", "the changed tests also pass without the change: they do not detect it"))
    if wtype not in RED_TYPES and on_base != 0:
        f.append(finding("behaviour_changed", "a %s change must keep behaviour, but its tests fail on base code" % wtype))
    return f, {"tests": tests, "exit_base": on_base, "exit_head": on_head}


if __name__ == "__main__":
    sys.exit(run("red_check", check))
