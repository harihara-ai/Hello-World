#!/usr/bin/env python3
"""purpose: refuse any policy change that loosens the floor unless a human sign-off names that key.

Input: {"old": floor.yml, "new": policy.yml, "signoff": signoff.json}. min_* may only rise, max_* may only
fall, lists may only grow, keys may not be removed. Sign-off JSON: {approved_by, reason, keys: [...]}.
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


def signed_keys(path):
    if not path or not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        s = json.load(fh)
    if not str(s.get("approved_by", "")).strip() or not str(s.get("reason", "")).strip():
        return set()
    return set(s.get("keys", []))


def check(p):
    try:
        old, new = policy.load(p["old"]), policy.load(p["new"])
    except ValueError as e:
        return [finding("unparseable", "policy cannot be parsed: %s" % e)], {}
    signed = signed_keys(p.get("signoff"))
    f = [finding("loosened", "%s loosened (%s) without a human sign-off" % (k, why), k)
         for k, why in loosened(old, new) if k not in signed]
    return f, {}


if __name__ == "__main__":
    sys.exit(run("policy_guard", check))
