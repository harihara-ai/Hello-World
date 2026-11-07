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
