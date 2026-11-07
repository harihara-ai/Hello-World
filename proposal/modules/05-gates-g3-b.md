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
