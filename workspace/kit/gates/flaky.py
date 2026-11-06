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
