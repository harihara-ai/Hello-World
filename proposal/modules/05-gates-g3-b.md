purpose: working source for the gates for done components of the kit (tangled into workspace/).

# Gates for done

Deterministic, JSON in and JSON out. Tests: tests/unit and tests/mutation.

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

## gate.flaky

Section 16.1 steps 2 and 8. Trap 5.

````python file=kit/gates/flaky.py
#!/usr/bin/env python3
"""purpose: compare repeated test runs; a test whose result differs between runs is flaky and is quarantined.

Input: {"runs": [{test: "pass"|"fail"}], "policy": {min_flaky_runs}}. Output: gate JSON with flaky and failing lists.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402


def check(p):
    runs = p.get("runs", [])
    need = int(p.get("policy", {}).get("min_flaky_runs", 3))
    if len(runs) < need:
        return [finding("too_few_runs", "%d runs given, %d needed" % (len(runs), need))], {"flaky": [], "failing": []}
    tests = sorted(set().union(*[set(r) for r in runs]))
    flaky, failing = [], []
    for t in tests:
        seen = {r.get(t, "missing") for r in runs}
        if len(seen) > 1:
            flaky.append(t)
        elif seen == {"fail"}:
            failing.append(t)
    f = [finding("flaky", "%s is flaky: quarantine it with a ticket" % t, t) for t in flaky]
    f += [finding("failing", "%s fails every run" % t, t, "warn") for t in failing]
    return f, {"flaky": flaky, "failing": failing}


if __name__ == "__main__":
    sys.exit(run("flaky", check))
````

## gate.red_check

Section 10.4 check 1 (red then green). Round 3 H05: changed tests must fail on base code (story, bug) or pass there (refactor, chore, tests).

````python file=kit/gates/red_check.py
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

ERRORS = {126, 127, -1}  # the runner did not start or timed out: not a test result


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
                with open(f, "wb") as fh:
                    fh.write(git("show", "%s:%s" % (base, f)))
        on_base = run_tests(shlex.split(cmd))
    finally:
        for i, (s, f) in enumerate(prod):
            if s == "D":
                os.remove(f) if os.path.exists(f) else None
            else:
                shutil.copy2(os.path.join(keep, str(i)), f)
        shutil.rmtree(keep, ignore_errors=True)
    if on_base in ERRORS:
        return [finding("runner_error", "the test command could not run (exit %d)" % on_base)], {"tests": tests}
    f = [] if on_base else [finding("tests_pass_on_base", "the changed tests pass without the change: they do not detect it")]
    return f, {"tests": tests, "exit_base": on_base}


if __name__ == "__main__":
    sys.exit(run("red_check", check))
````
