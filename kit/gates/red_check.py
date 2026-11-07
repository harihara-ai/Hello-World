#!/usr/bin/env python3
"""purpose: prove the changed tests detect the change: run them on the base commit's production code.

Input: {"base": git ref, "type": work type, "test_cmd": "command, optionally with {tests}"}. CI passes the test
command. For story, NFR, bug and hotfix the changed tests must FAIL with the base production code (red; spec
10.4 #1). The base code is put back in this checkout for one run (dependencies stay in place), then restored.
CI's own test step proves green. Other types: nothing to check. Known limit: tests for brand-new code are only
shown to touch it; AI test review and PR review judge what they assert (kit/core/rules.md).
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

ERRORS = {5, 126, 127, -1}  # no tests found (pytest 5), runner did not start, or timed out: not a test result


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True)
    if p.returncode != 0:
        raise UsageError("git %s failed: %s" % (args[0], p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout


def changes(base):
    """[(status, path)] since base, without renames; untracked files count as added."""
    if not re.fullmatch(r"[\w./~^@-]+", base) or base.startswith("-"):
        raise UsageError("bad base ref")
    out = [tuple(line.split("\t", 1)) for line in git("diff", "--no-ext-diff", "--name-status", "--no-renames",
                                                     base, "--").decode().splitlines()]
    out += [("A", p) for p in git("ls-files", "--others", "--exclude-standard").decode().splitlines()]
    return out


def run_tests(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, timeout=1800).returncode
    except (OSError, subprocess.TimeoutExpired):
        return -1


def check(p):
    wtype = p.get("type", "story")
    if wtype not in RED_TYPES:
        return [finding("nothing_to_check", "red check applies to story, nfr, bug and hotfix", "", "warn")], {}
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode != 0:
        return [finding("needs_git", "red check runs in a git repo (CI)", "", "warn")], {}
    base, delta = p.get("base", ""), changes(p.get("base", ""))
    tests = sorted(f for s, f in delta if s != "D" and is_test_file(f) and f.lower().endswith(TEST_EXT))
    if not tests:
        return [finding("no_new_tests", "a %s change needs a changed test that fails without it" % wtype)], {}
    if not p.get("test_cmd"):
        return [finding("no_test_cmd", "CI must pass --test-cmd")], {"tests": tests}
    cmd = p["test_cmd"].replace("{tests}", " ".join(shlex.quote(t) for t in tests))
    prod = [(s, f) for s, f in delta if not is_test_file(f)]
    keep = tempfile.mkdtemp(prefix="red-")
    try:
        for i, (s, f) in enumerate(prod):
            if s != "D":
                shutil.copy2(f, os.path.join(keep, str(i)))
            if s == "A":
                os.remove(f)
            else:
                os.makedirs(os.path.dirname(f) or ".", exist_ok=True)
                with open(f, "wb") as fh:
                    fh.write(git("show", "%s:%s" % (base, f)))
        on_base = run_tests(shlex.split(cmd))
    finally:
        for i, (s, f) in enumerate(prod):
            saved = os.path.join(keep, str(i))
            if s == "D":
                os.remove(f) if os.path.exists(f) else None
            elif os.path.exists(saved):
                os.makedirs(os.path.dirname(f) or ".", exist_ok=True)
                shutil.copy2(saved, f)
        shutil.rmtree(keep, ignore_errors=True)
    if on_base in ERRORS:
        return [finding("runner_error", "the test command could not run (exit %d)" % on_base)], {"tests": tests}
    f = [] if on_base else [finding("tests_pass_on_base", "the changed tests pass without the change: they do not detect it")]
    return f, {"tests": tests, "exit_base": on_base}


if __name__ == "__main__":
    sys.exit(run("red_check", check))
