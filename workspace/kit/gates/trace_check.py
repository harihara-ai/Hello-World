#!/usr/bin/env python3
"""purpose: every REQ ID in the specs appears in at least one test file (traceability, G3 check 6).

Input: {"spec_dirs": [...], "test_dirs": [...]}, paths relative to the working directory. Output: gate JSON.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

ID = re.compile(r"REQ-[A-Z0-9]+-[0-9]+")


def ids_in(dirs, md_only):
    found = set()
    for d in dirs:
        for root, _dirs, files in os.walk(d):
            for name in files:
                if md_only and not name.endswith(".md"):
                    continue
                try:
                    with open(os.path.join(root, name), encoding="utf-8", errors="ignore") as fh:
                        found |= set(ID.findall(fh.read()))
                except OSError:
                    continue
    return found


def check(p):
    spec_dirs = [d for d in p.get("spec_dirs", []) if os.path.isdir(d)]
    test_dirs = [d for d in p.get("test_dirs", ["tests", "test", "spec", "src"]) if os.path.isdir(d)]
    spec_ids = ids_in(spec_dirs, True)
    if not spec_ids:
        return [finding("no_ids", "no REQ IDs found in %s" % p.get("spec_dirs"))], {}
    if not test_dirs:
        return [finding("no_test_dirs", "none of the test dirs exist: %s" % p.get("test_dirs"))], {}
    test_ids = ids_in(test_dirs, False)
    f = [finding("untested", "%s has no test" % i, i) for i in sorted(spec_ids - test_ids)]
    f += [finding("orphan_id", "tests mention %s, which is in no spec here" % i, i, "warn")
          for i in sorted(test_ids - spec_ids)]
    return f, {"requirements": sorted(spec_ids)}


if __name__ == "__main__":
    sys.exit(run("trace_check", check))
