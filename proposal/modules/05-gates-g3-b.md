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
````
